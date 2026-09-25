"""Harmonize the ANES 2016-2020-2024 panel: the 2,171 respondents interviewed in all three
Time Series studies, with the same attitude items in each wave.

Sources (all in data/raw/anes/, fetched from electionstudies.org in the in-app browser because
the site's WAF returns 403 to python-requests and to curl; transferred as base64 and verified
by SHA-256 against the browser's digest):
    anes_timeseries_2024_csv_20260519.zip   (A.9; panel = V240003 == 1)
    anes_timeseries_2020_csv_20220210.zip   7,777,954 bytes  sha256 70450eb6...1bfda
    anes_timeseries_2016_dta.zip           16,643,125 bytes  sha256 12a0a53d...23f033
    plus both user guide/codebook PDFs, whose text is in codebook_2020.txt / codebook_2016.txt.

Linkage. The 2024 file carries each panelist's 2020 case id (V200001) and 2016 Westat id
(V160001_orig); the 2020 file carries V160001_orig too, and the two agree for all 2,171. The
2016 file's own V160001_orig is the join key there (its V160001 is a different, 1..5090 id).

Items were matched across years by the survey-question mnemonic each codebook prints
(e.g. TRUSTGOV_BIGINTRST), then wording and response codes were read side by side. Every item
below is rescaled to 0..1 with 1 = the direction in its name (anti-elite, left, conservative).
Where the format changed between waves the item is flagged in FORMAT_CHANGES and is excluded
from the within-person change analysis:
    trans_bathroom  2016/2020: 6-pt forced choice with strength (1 = must use birth-sex bathroom);
                    2024: 7-pt favor/oppose "use bathroom that matches gender identity".
    gay_marriage    2016/2020: 3 categories (marry / civil unions / no recognition); 2024 asked the
                    same 3-category item of a random half (V241382) and a 7-pt favor/oppose item of
                    the other half (V241385x). gay_marriage_24 uses whichever was asked;
                    gay_marriage3_24 keeps only the identical 3-category version.
Missing codes: negative values; 99 ("haven't thought") on 7-pt scales; >100 on thermometers;
>10 on CSES 0-10 scales; abortion 5 ("other"); child-trait 4 ("neither", volunteered).
"""

from pathlib import Path
import warnings
import numpy as np
import pandas as pd

RAW_DIR = Path("data/raw/anes")
CSV24 = RAW_DIR / "anes_timeseries_2024_csv_20260519.csv"
CSV20 = RAW_DIR / "anes_timeseries_2020_csv_20220210.csv"
DTA16 = RAW_DIR / "anes_timeseries_2016.dta"
OUT = RAW_DIR / "anes_panel_2016_2024.csv"


# --- recoders: raw code -> 0..1, 1 = the named direction -------------------------------------
def lin(lo, hi, reverse=False):
    """Map lo..hi linearly onto 0..1 (reverse: hi -> 0)."""
    def f(s):
        s = s.where((s >= lo) & (s <= hi))
        v = (s - lo) / (hi - lo)
        return 1 - v if reverse else v
    return f


def binary(one, zero=(), half=()):
    def f(s):
        out = pd.Series(np.nan, index=s.index)
        out[s.isin(zero)] = 0.0
        out[s.isin(half)] = 0.5
        out[s.isin([one] if np.isscalar(one) else one)] = 1.0
        return out
    return f


def therm_inv(s):   # 0..100 thermometer -> 1 = coldest
    return 1 - s.where((s >= 0) & (s <= 100)) / 100


# name: (construct, 2016 var, 2020 var, 2024 var, recoder[, recoder_2024 if different])
ITEMS = {
    # Anti-politician (I.8): trust in government and external efficacy
    "big_interests":    ("anti_pol", "V161216", "V201234", "V241231", binary(1, zero=[2])),
    "corrupt":          ("anti_pol", "V161218", "V201236", "V241233", lin(1, 5, reverse=True)),   # 1 all .. 5 none
    "trust_never":      ("anti_pol", "V161215", "V201233", "V241229", lin(1, 5)),                 # 1 always .. 5 never
    "officials_dont_care": ("anti_pol", "V162215", "V202212", "V242200", lin(1, 5, reverse=True)),  # 1 agree strongly
    "no_say":           ("anti_pol", "V162216", "V202213", "V242201", lin(1, 5, reverse=True)),
    # Strong hand: CSES "strong leader ... even if the leader bends the rules" (CSES5 2016/2020, CSES6 2024; same wording)
    "strong_leader":    ("strong_hand", "V162263", "V202413", "V242411", lin(1, 5, reverse=True)),
    # Anti-corporate (I.8)
    "anti_bigbiz":      ("anti_corp", "V162100", "V202163", "V242141", therm_inv),
    "rich_powerful":    ("anti_corp", None, "V202305", "V242305", lin(1, 5)),                     # 1 not at all well .. 5 extremely
    "millionaire_tax":  ("anti_corp", "V162140", "V202325", "V242316a", binary(1, zero=[2, 3])),
    "spend_limits":     ("anti_corp", "V162234", "V202225", "V242214", binary(1, zero=[2, 3])),
    # Economic left (I.7)
    "services":         ("econ_left", "V161178", "V201246", "V241239", lin(1, 7)),                # 7 = many more services
    "gov_insurance":    ("econ_left", "V161184", "V201252", "V241245", lin(1, 7, reverse=True)),  # 1 = government plan
    "guar_jobs":        ("econ_left", "V161189", "V201255", "V241252", lin(1, 7, reverse=True)),  # 1 = government guarantee
    "min_wage_raise":   ("econ_left", "V162192", "V202377", "V242350", binary(1, zero=[2, 3, 4])),
    "paid_leave":       ("econ_left", "V161226x", "V201405x", "V241369x", lin(1, 7, reverse=True)),
    # Immigration conservative (I.7, plus the CSES crime item asked in all three waves)
    "wall":             ("immig_cons", "V161196x", "V201426x", "V241395x", lin(1, 7, reverse=True)),
    "dreamers_back":    ("immig_cons", "V161195x", "V201423x", "V241392x", lin(1, 6, reverse=True)),  # 1 = send back, great deal
    "end_birthright":   ("immig_cons", "V161194x", "V201420x", "V241389x", lin(1, 7, reverse=True)),
    "immig_decrease":   ("immig_cons", "V162157", "V202232", "V242227", lin(1, 5)),
    "immig_crime_cses": ("immig_cons", "V162270", "V202420", "V242453", lin(1, 5, reverse=True)),  # agree = conservative
    "immig_crime":      ("immig_cons", None, "V202239x", "V242231x", lin(1, 7, reverse=True)),   # 1 = increase a lot
    "path_oppose":      ("immig_cons", None, "V202242x", "V242234x", lin(1, 7)),
    # Cultural conservative
    "abortion":         ("culture_cons", "V161232", "V201336", "V241302", lin(1, 4, reverse=True)),  # 1 never permitted
    "gay_marriage":     ("culture_cons", "V161231", "V201416", None, lin(1, 3)),                     # 2024 handled below
    "gay_jobs_oppose":  ("culture_cons", "V161229x", "V201414x", "V241378x", lin(1, 4)),
    "gay_adopt_no":     ("culture_cons", "V161230", "V201415", "V241379", binary(2, zero=[1])),
    "trans_bathroom":   ("culture_cons", "V161228x", "V201411x", "V241372x", lin(1, 6, reverse=True), lin(1, 7)),
    "trans_military_oppose": ("culture_cons", None, "V202390x", "V242364x", lin(1, 7)),
    "diversity_worse":  ("culture_cons", None, "V202373x", "V242349x", lin(1, 5)),
    "anti_trans_therm": ("culture_cons_extra", "V162111", "V202172", "V242151", therm_inv),
    # Secondary constructs (not in the 2024 indices; fixed before looking at results)
    "auth_respect":     ("authoritarian", "V162239", "V202266", "V242260", binary(2, zero=[1], half=[3])),
    "auth_manners":     ("authoritarian", "V162240", "V202267", "V242261", binary(2, zero=[1], half=[3])),
    "auth_obedience":   ("authoritarian", "V162241", "V202268", "V242262", binary(1, zero=[2], half=[3])),
    "auth_behaved":     ("authoritarian", "V162242", "V202269", "V242263", binary(2, zero=[1], half=[3])),
    "rr_workway":       ("racial_resent", "V162211", "V202300", "V242300", lin(1, 5, reverse=True)),
    "rr_generations":   ("racial_resent", "V162212", "V202301", "V242301", lin(1, 5)),
    "rr_deserve":       ("racial_resent", "V162213", "V202302", "V242302", lin(1, 5)),
    "rr_tryhard":       ("racial_resent", "V162214", "V202303", "V242303", lin(1, 5, reverse=True)),
    # Single items reported alongside
    "insiders":         ("single", None, "V202304", "V242304", lin(1, 5)),   # "system only works for insiders with money and power"
    "anti_unions":      ("single", "V162098", "V202162", "V242140", therm_inv),
}
FORMAT_CHANGES = {"trans_bathroom": "2024", "gay_marriage": "2024 half-sample"}

# Raw-scale variables kept as-is (cleaned of missing codes)
RAW = {
    # CSES 0 (left) .. 10 (right)
    "lr_self":      ("V162289", "V202439", "V242438", 10),
    "lr_dem":       ("V162287", "V202437", "V242436", 10),
    "lr_rep":       ("V162288", "V202438", "V242437", 10),
    # pre-election party thermometers
    "therm_dem":    ("V161095", "V201156", "V241166", 100),
    "therm_rep":    ("V161096", "V201157", "V241167", 100),
    "pid7":         ("V161158x", "V201231x", "V241227x", 7),
}


def clean(s, hi=None):
    s = pd.to_numeric(s, errors="coerce")
    s = s.where(s >= 0)
    return s.where(s <= hi) if hi is not None else s


def load():
    d24 = pd.read_csv(CSV24, low_memory=False)
    d24 = d24[d24["V240003"] == 1].copy()
    d24["id20"] = pd.to_numeric(d24["V200001"], errors="coerce").astype(int)
    d24["id16"] = pd.to_numeric(d24["V160001_orig"], errors="coerce").astype(int)
    d20 = pd.read_csv(CSV20, low_memory=False)
    d20 = d20[d20["V200001"].isin(d24["id20"])].copy()
    with warnings.catch_warnings():   # a few 2016 string fields are latin-1; none are used here
        warnings.simplefilter("ignore", UnicodeWarning)
        d16 = pd.read_stata(DTA16, convert_categoricals=False)
    d16 = d16[d16["V160001_orig"].isin(d24["id16"])].copy()
    assert len(d20) == len(d24) == len(d16), (len(d24), len(d20), len(d16))
    # the 2020 file's own 2016 id must agree with the 2024 file's
    chk = d24[["id20", "id16"]].merge(d20[["V200001", "V160001_orig"]], left_on="id20", right_on="V200001")
    assert (chk["id16"] == chk["V160001_orig"]).all()
    d20 = d20.set_index("V200001").loc[d24["id20"]].reset_index()
    d16 = d16.set_index("V160001_orig").loc[d24["id16"]].reset_index()
    d24 = d24.reset_index(drop=True)
    return d16, d20, d24


def vote_2016(d16):
    """Contemporaneous 2016 vote: pre-election report for early voters (V161027), else post (V162034a)."""
    who = clean(d16["V161027"]).where(clean(d16["V161027"]).notna(), clean(d16["V162034a"]))
    v = who.map({1: "D", 2: "R", 3: "O", 4: "O", 5: "O", 7: "O", 9: "O"})
    turnout = clean(d16["V162031x"])
    v = v.where(~(turnout == 0), "NV")
    return v


def build():
    d16, d20, d24 = load()
    out = pd.DataFrame({
        "caseid_24": d24["V240001"], "id20": d24["id20"], "id16": d24["id16"],
        "weight": pd.to_numeric(d24["V240106b"], errors="coerce"),     # 2016-2024 panel, post-election
        "weight_pre": pd.to_numeric(d24["V240106a"], errors="coerce"),
        "psu": d24["V240106c"], "stratum": d24["V240106d"],
        "weight_20panel": pd.to_numeric(d20["V200011b"], errors="coerce"),
        "age_24": clean(d24["V241458x"]), "race_24": clean(d24["V241501x"]),
        "educ_24": clean(d24["V241463"]), "gender_24": clean(d24["V241551"]),
    })
    # Votes, contemporaneous in each wave
    out["vote16"] = vote_2016(d16)
    v20 = clean(d20["V202110x"]).map({1: "D", 2: "R", 3: "O", 4: "O", 5: "O"})
    out["vote20"] = v20.where(~(clean(d20["V202109x"]) == 0), "NV")
    v24 = clean(d24["V242096x"]).map({1: "D", 2: "R", 3: "O", 4: "O", 5: "O", 6: "O"})
    out["vote24"] = v24.where(~(clean(d24["V242095x"]) == 0), "NV")
    # Recalled votes, for the recall-accuracy check
    out["recall20_in24"] = clean(d24["V241106x"]).map({1: "NV", 2: "D", 3: "R", 4: "O"})
    r16_24 = clean(d24["V241108"]).map({1: "D", 2: "R", 5: "O"})
    out["recall16_in24"] = r16_24.where(~(clean(d24["V241107"]) == 2), "NV")
    voted16_in20 = clean(d20["V201101"]).where(clean(d20["V201101"]).notna(), clean(d20["V201102"]))
    r16_20 = clean(d20["V201103"]).map({1: "D", 2: "R", 5: "O"})
    out["recall16_in20"] = r16_20.where(~(voted16_in20 == 2), "NV")

    waves = {"16": d16, "20": d20, "24": d24}
    cols = {}
    for name, spec in ITEMS.items():
        construct, v16, v20_, v24_, rec = spec[:5]
        rec24 = spec[5] if len(spec) > 5 else rec
        for suf, var, r in (("16", v16, rec), ("20", v20_, rec), ("24", v24_, rec24)):
            if var is None:
                continue
            cols[f"{name}_{suf}"] = r(clean(waves[suf][var])).values
    # 2024 gay marriage: identical 3-category item for a random half, 7-pt favor/oppose for the other
    gm3 = lin(1, 3)(clean(d24["V241382"]))
    gm7 = lin(1, 7)(clean(d24["V241385x"]))
    cols["gay_marriage3_24"] = gm3.values
    cols["gay_marriage_24"] = gm3.where(gm3.notna(), gm7).values
    for name, (v16, v20_, v24_, hi) in RAW.items():
        for suf, var in (("16", v16), ("20", v20_), ("24", v24_)):
            cols[f"{name}_{suf}"] = clean(waves[suf][var], hi).values
    return pd.concat([out, pd.DataFrame(cols, index=out.index)], axis=1)


def main():
    p = build()
    p.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {p.shape}")
    print("with panel post weight:", (p.weight > 0).sum())
    print("\ncontemporaneous 2020 x 2024 vote (N, post-weighted panelists):")
    w = p[p.weight > 0]
    print(pd.crosstab(w.vote20.fillna("?"), w.vote24.fillna("?")))
    print("\ncontemporaneous 2016 x 2020 vote:")
    print(pd.crosstab(w.vote16.fillna("?"), w.vote20.fillna("?")))
    print("\nitem coverage (share non-missing among post-weighted panelists):")
    cov = w.filter(regex=r"_(16|20|24)$").notna().mean().round(2)
    print(cov.to_string())


if __name__ == "__main__":
    main()
