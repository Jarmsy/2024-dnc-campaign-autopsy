"""Extract and harmonize the ANES 2024 Time Series (full release, 2026-05-19).

Download note. The ANES site (electionstudies.org) sits behind a WAF that returns 403 to
python-requests regardless of headers, but serves the file to a real browser. The zip in
data/raw/anes/ was fetched in the in-app browser (fetch -> base64 -> chunked through the
javascript tool -> reassembled and byte-verified: 6,516,359 bytes, zipfile.testzip() None).
If the zip is missing, download it manually from
    https://electionstudies.org/data-center/2024-time-series-study/
(free registration) and drop it in data/raw/anes/. This script does not attempt the HTTP fetch.

Variable codes below were checked against the user guide/codebook PDF shipped in the zip.
Missing-data conventions: negative codes are missing (-9 refused, -8 DK, -7/-5 partial, -6 no
post interview, -4 error, -2 DK/RF in a component, -1 inapplicable); 99 on 7-pt scales =
"haven't thought much about this".
"""

from pathlib import Path
import zipfile
import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw/anes")
ZIP_NAME = "anes_timeseries_2024_csv_20260519.zip"
CSV_NAME = "anes_timeseries_2024_csv_20260519.csv"

# harmonized name -> ANES column
CORE = {
    "caseid":             "V240001",
    "panel_id_2020":      "V200001",       # 2020 Time Series case id for panel respondents
    "panel_id_2016":      "V160001_orig",  # 2016 Time Series case id
    "sample_type":        "V240003",       # 1 panel (2016-20-24) 2 fresh web 3 fresh FTF 4 GSS
    # Weights: 107 = full sample (fresh in-person + fresh web + panel) + PAPI; a = pre, b = post.
    # Anything using a post-election item must use the post weight.
    "weight_pre":         "V240107a",
    "weight_post":        "V240107b",
    "psu":                "V240107c",
    "strata":             "V240107d",
    "weight_panel_post":  "V240106b",      # 2016-2024 panel alone, post
    # Demographics
    "age":                "V241458x",      # 80 = 80+
    "educ":               "V241463",       # 1..16 raw; 13 = bachelor's
    "race_eth":           "V241501x",      # 1 white 2 black 3 hispanic 4 asian/pi 5 native/other 6 multi
    "gender":             "V241551",       # 1 man 2 woman 3 nonbinary 4 other
    "faminc":             "V241566x",      # 1..28 brackets
    # Party
    "pid7":               "V241227x",      # 1 strong D .. 7 strong R
    "pid3":               "V241221",       # 1 D 2 R 3 I 0 none 5 other
    # Vote
    "turnout_2024":       "V242095x",      # 0 did not vote, 1 voted
    "presvote_2024":      "V242096x",      # 1 Harris 2 Trump 3 RFK 4 West 5 Stein 6 other
    "presvote_2020":      "V241106x",      # 1 did not vote 2 Biden 3 Trump 4 other
    "voted_2016":         "V241107",       # 1 voted 2 did not
    "presvote_2016":      "V241108",       # 1 Clinton 2 Trump 5 other
    "primary_voted":      "V241031",
    "primary_choice":     "V241032",
    # Thermometers (0-100)
    "therm_harris":       "V241156",
    "therm_trump":        "V241157",
    "therm_biden":        "V241158",
    "therm_transgender":  "V242151",       # post; 998/999 missing
    "therm_dem_party":    "V241166",       # pre
    "therm_rep_party":    "V241167",       # pre
    "therm_big_business": "V242141",       # post; 998/999 missing
    "therm_unions":       "V242140",       # post
    "therm_congress":     "V242145",       # post
    # Corporate power / economic populism (post)
    "rich_powerful_block": "V242305",      # 1 not at all well .. 5 extremely well ("because of the rich and powerful it's hard to get ahead")
    "millionaire_tax":    "V242316a",      # 1 favor 2 oppose 3 neither
    "campaign_spend_limits": "V242214",    # 1 favor 2 oppose 3 neither
    # CSES party evaluations (post; 0-10; 96/97/98 missing)
    "like_dem_party":     "V242432",
    "like_rep_party":     "V242433",
    "lr_dem_party":       "V242436",       # 0 left .. 10 right
    "lr_rep_party":       "V242437",
    "lr_self":            "V242438",
    # Most important problem (post, open-ended, coded per Appendix B; up to 3 mentions x 5 ideas)
    "mip1_idea1":         "V242165y1",
    "mip1_idea2":         "V242165y2",
    "mip2_idea1":         "V242167y1",
    "mip3_idea1":         "V242169y1",
    "mip_single_idea1":   "V242171y1",     # "single most important" - asked only if >1 mention
    "mip1_party":         "V242166",       # 1 Dems 2 Reps 3 no difference (party better on mention 1)
    # Closed-ended issue importance (post; 1 extremely .. 5 not at all)
    "imp_illegal_immig":  "V242172",
    "imp_cost_living":    "V242173",
    "imp_climate":        "V242174",
    "imp_guns":           "V242175",
    "imp_abortion":       "V242176",
    "imp_crime":          "V242177",
    "imp_gaza":           "V242178",
    "imp_schools":        "V242179",
    "imp_democracy":      "V242180",
    "imp_racial_ineq":    "V242181",
    # Which party better on each (post; 1 Dems 2 Reps 3 no difference), same order
    "own_illegal_immig":  "V242182",
    "own_cost_living":    "V242183",
    "own_climate":        "V242184",
    "own_guns":           "V242185",
    "own_abortion":       "V242186",
    "own_crime":          "V242187",
    "own_gaza":           "V242188",
    "own_schools":        "V242189",
    "own_democracy":      "V242190",       # PAPI instrument only (N~200) - do not use for group comparisons
    "own_racial_ineq":    "V242191",       # PAPI only
    # Anti-elite / populism / trust (pre unless noted)
    "govt_big_interests": "V241231",       # 1 few big interests 2 benefit of all
    "govt_corrupt":       "V241233",
    "trust_govt":         "V241229",
    "trust_media":        "V241335",
    "outraged":           "V241120",       # 1 not at all .. 5 extremely
    "officials_dont_care": "V242200",      # post; 1 agree strongly .. 5 disagree strongly
    "no_say_in_govt":     "V242201",       # post; same coding
    "cses_strong_leader": "V242411",       # post; 1 strongly agree .. 5 strongly disagree
    "cses_business_run":  "V242413",
    "cses_experts_run":   "V242414",
    "cses_referendums":   "V242415",
    "cses_trust_scientists": "V242420",
    "cses_healthcare_guar":  "V242448",    # how well system guarantees healthcare; 1 very well .. 4 not at all
    # Economic policy (pre, 7-pt; 99 = haven't thought)
    "scale_services":     "V241239",       # 1 many fewer services .. 7 many more
    "scale_health_ins":   "V241245",       # 1 govt plan .. 7 private
    "scale_jobs_income":  "V241252",       # 1 govt guarantee .. 7 on own
    "income_gap":         "V241363x",
    "paid_leave":         "V241369x",
    "min_wage":           "V242350",       # post; 1 raised 2 same 3 lowered 4 eliminated
    "econ_retro_12mo":    "V242426",       # post CSES; 1 much better .. 5 much worse
    # Immigration (pre + post)
    "wall":               "V241395x",      # 1 favor great deal .. 7 oppose great deal
    "dreamers":           "V241392x",
    "birthright_end":     "V241389x",
    "immig_levels":       "V242227",       # post; 1 increase a lot .. 5 decrease a lot
    "immig_crime":        "V242231x",      # post; 1 increase a lot .. 7 decrease a lot
    "path_citizenship":   "V242234x",      # post; 1 favor great deal .. 7 oppose great deal
    # Culture-war items (pre unless noted)
    "trans_bathroom":     "V241372x",      # 1 favor great deal .. 7 oppose great deal
    "trans_sports_ban":   "V241375x",      # 1 favor ban great deal .. 7 oppose
    "trans_military":     "V242364x",      # post
    "dei_campus":         "V241288",       # 1 favor 2 oppose 3 neither
    "gay_marriage":       "V241385x",
    "abortion_std":       "V241302",
    "abortion_importance": "V241303",
    "diversity_better":   "V242349x",      # post
    "cses_women_rep_too_far": "V242412",
    # Foreign policy / trade
    "israel_side":        "V241407",
    "ukraine_weapons":    "V241398",
    "import_limits":      "V242226x",      # post
    # Biden
    "biden_dropout_approve": "V242223x",
}

# Appendix B "most important problem" codes -> analytic families
MIP_FAMILY = {
    "economy_prices": {50, 54, 53, 15, 30},   # economy, inflation, recession, energy prices, income (other)
    "economy_other":  {10, 27, 28, 38, 40, 52, 55, 51, 26, 25, 29},  # US jobs, employment, housing, budget, taxes, inequality, econ (other), stock mkt, poverty, welfare, soc sec
    "immigration":    {41},
    "democracy_govt": {43, 44, 45, 47, 48, 49, 78, 81, 39, 42, 80, 36},  # political corruption, ethics, govt power, partisanship, politicians, govt (other), elections, unity, size of govt, campaign finance, civility, corporate corruption
    "crime_drugs":    {31, 33, 34, 35},
    "culture_moral":  {61, 64, 66, 68, 75, 79, 32},  # abortion, morality, family, LGBT, gender, religion, race relations
    "foreign_war":    {1, 2, 3, 4, 5, 7, 8, 9, 12, 13, 76, 77},
    "health":         {22, 23, 24},
    "environment":    {17, 18, 14, 16},
    "education":      {19, 20, 21},
    "media":          {69},
}
MIP_CODE_TO_FAMILY = {c: fam for fam, codes in MIP_FAMILY.items() for c in codes}


def ensure_extracted():
    csv = RAW_DIR / CSV_NAME
    if csv.exists():
        return csv
    zp = RAW_DIR / ZIP_NAME
    if not zp.exists():
        raise FileNotFoundError(f"{zp} missing - see module docstring for the manual download")
    with zipfile.ZipFile(zp) as z:
        assert z.testzip() is None
        z.extractall(RAW_DIR)
    return csv


def clean_missing(s):
    """ANES negative codes -> NaN."""
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s >= 0)


def harmonize(df):
    missing = [v for v in CORE.values() if v not in df.columns]
    if missing:
        raise KeyError(f"columns not in ANES csv: {missing}")
    out = pd.DataFrame({k: df[v] for k, v in CORE.items()})

    keep_raw = {"caseid", "panel_id_2020", "panel_id_2016", "sample_type",
                "weight_pre", "weight_post", "psu", "strata", "weight_panel_post"}
    for c in out.columns:
        if c not in keep_raw:
            out[c] = clean_missing(out[c])
    # post/panel weights are blank (" ") for respondents outside that weight's universe
    for c in ("weight_pre", "weight_post", "weight_panel_post"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    for c in ("scale_services", "scale_health_ins", "scale_jobs_income"):
        out[c] = out[c].where(out[c] <= 7)
    for c in ("therm_transgender", "therm_big_business", "therm_unions", "therm_congress"):
        out[c] = out[c].where(out[c] <= 100)
    for c in ("like_dem_party", "like_rep_party", "lr_dem_party", "lr_rep_party", "lr_self"):
        out[c] = out[c].where(out[c] <= 10)

    # Vote flags
    out["vote24"] = out["presvote_2024"].map({1: "D", 2: "R", 3: "O", 4: "O", 5: "O", 6: "O"})
    out.loc[out["turnout_2024"] == 0, "vote24"] = "NV"
    out["vote20"] = out["presvote_2020"].map({1: "NV", 2: "D", 3: "R", 4: "O"})
    out["vote16"] = out["presvote_2016"].map({1: "D", 2: "R", 5: "O"})
    out.loc[out["voted_2016"] == 2, "vote16"] = "NV"

    both = out["vote20"].notna() & out["vote24"].notna()
    out["switcher_D_to_R"] = np.where(both, ((out["vote20"] == "D") & (out["vote24"] == "R")).astype(float), np.nan)
    out["new_voter_2024"] = np.where(both, ((out["vote20"] == "NV") & out["vote24"].isin(["D", "R"])).astype(float), np.nan)

    # Most important problem: the "single most important" follow-up is asked only when the
    # respondent gave more than one problem, so the analytic MIP is that item when present,
    # otherwise the first mention.
    mip = out["mip_single_idea1"].where(out["mip_single_idea1"].notna(), out["mip1_idea1"])
    out["mip_code"] = mip
    out["mip_family"] = mip.map(MIP_CODE_TO_FAMILY)
    out.loc[mip.notna() & out["mip_family"].isna(), "mip_family"] = "other"
    # any-mention flags across the three mentions
    mention_cols = ["mip1_idea1", "mip1_idea2", "mip2_idea1", "mip3_idea1"]
    for fam in ("economy_prices", "economy_other", "immigration", "democracy_govt", "culture_moral"):
        flag = out[mention_cols].isin(MIP_FAMILY[fam]).any(axis=1).astype(float)
        out[f"mip_any_{fam}"] = flag.where(out["mip1_idea1"].notna())

    # Convenience recodes (higher = more of the named thing)
    # +1 if illegal immigration rated more important than cost of living, -1 if less, 0 tie
    out["imp_immig_gt_cost"] = np.sign(out["imp_cost_living"] - out["imp_illegal_immig"])
    out["big_interests"] = out["govt_big_interests"].map({1: 1.0, 2: 0.0})
    out["strong_leader_agree"] = (5 - out["cses_strong_leader"]) / 4   # 1 = strongly agree, 0 = strongly disagree
    return out


def main():
    csv = ensure_extracted()
    df = pd.read_csv(csv, low_memory=False)
    print(f"raw: {df.shape}")
    core = harmonize(df)
    dest = RAW_DIR / "anes_2024_core.csv"
    core.to_csv(dest, index=False)
    print(f"wrote {dest}: {core.shape}")

    v = core.loc[core["vote24"].isin(["D", "R", "O"]) & (core["weight_post"] > 0)]
    print("post-weighted 2024 vote among voters:",
          (v.groupby("vote24")["weight_post"].sum() / v["weight_post"].sum()).round(3).to_dict())
    print("2020 -> 2024 (N):")
    print(pd.crosstab(core["vote20"], core["vote24"]))
    m = core.loc[core["mip_family"].notna() & core["vote24"].isin(["D", "R"]) & (core["weight_post"] > 0)]
    print("mip_family among major-party voters (post-weighted):")
    print((m.groupby("mip_family")["weight_post"].sum() / m["weight_post"].sum()).sort_values(ascending=False).round(3))


if __name__ == "__main__":
    main()
