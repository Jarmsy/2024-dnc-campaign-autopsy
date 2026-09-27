"""Export the audited numbers behind the portfolio page as one small JSON file per chart.

Every figure on the page must come from these files, which are built only from the notebook
outputs in outputs/tables/ (and, for the 2024 fundamentals prediction, notebook 02's saved output).
No analysis happens here. Run from the repo root:

    python portfolio/export_data.py

Writes portfolio/data/*.json and prints a check list of headline numbers to compare with the report.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "outputs" / "tables"
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)
checks = {}


def write(name, obj):
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=1, default=float), encoding="utf-8")


def r(x, n=2):
    return None if pd.isna(x) else round(float(x), n)


# 1. Fundamentals: leave-one-out predictions 1948-2020, plus the 2024 out-of-sample prediction
f = pd.read_csv(T / "fundamentals_loocv_predictions.csv")
nb = json.loads((ROOT / "notebooks" / "02_fundamentals_model.ipynb").read_text(encoding="utf-8"))
txt = "".join("".join(o.get("text", "")) for c in nb["cells"] for o in c.get("outputs", []))
pred24 = float(re.search(r"Predicted Harris share:\s+([\d.]+)%", txt).group(1))
rmse = float(np.sqrt((f.residual_dem ** 2).mean()))
write("01_fundamentals", {
    "elections": [{"year": int(y), "incumbent_party": p, "actual": r(a), "predicted": r(pr)} for y, p, a, pr in
                  zip(f.year, f.incumbent_party, f.actual_dem, f.predicted_dem)],
    "harris_2024": {"predicted": pred24, "actual": 49.25, "error_band_pp": r(rmse), "error_band_refit_without_2020_pp": 2.66,
                    "error_band_refit_source": "technical appendix B, robustness table, 'Drop 2020' row (model refit without 2020)"},
    "note": "Two-party Democratic share. 1948-2020 are leave-one-out predictions; 2024 is out of sample (model fit on 1948-2020). "
            "Error band = root-mean-square leave-one-out error; the 2020 pandemic quarter alone inflates it.",
})
checks["Harris predicted / actual"] = f"{pred24} / 49.25 (report: 47.9 / 49.25)"
checks["error band (LOOCV RMSE)"] = f"{rmse:.2f} (report: 3.75); refit without 2020 = 2.66 taken from appendix B"

# 2. Where the votes went: turnout vs share component by county 2020 Democratic share
b = pd.read_csv(T / "stayhome_by_county_bin.csv")
write("02_turnout_vs_share", {
    "bins": [{"bin": x.county_2020_dem_share, "counties": int(x.counties), "turnout_M": r(x.turnout_component_M, 3),
              "share_M": r(x.share_component_M, 3), "total_M": r(x.delta_dem_M, 3), "turnout_change_pct": r(x.turnout_change_pct, 1)}
             for x in b.itertuples()],
    "note": "Change in Democratic votes 2020->2024 (millions), split into the part from fewer/more people voting (turnout) and the part "
            "from voters choosing differently (share). Kitagawa-Blinder decomposition, county level.",
})
stay = pd.read_csv(T / "stayhome_counterfactual_recall_corrected.csv", index_col=0)
write("02b_stayhome_counterfactual", {
    "states": [{"state": s.title(), "margin_2024": r(x.margin_2024, 0), "net_if_stayhomes_voted": r(x.corrected_one, 0),
                "lo": r(x.lo_one, 0), "hi": r(x.hi_one, 0)} for s, x in stay.iterrows()],
    "note": "Net change in the Democratic margin if every 2020 voter who stayed home in 2024 had voted as in 2020 (unweighted CES "
            "stay-home rates, corrected for recalled vote). A state flips only if the net exceeds the (negative) 2024 margin.",
})
checks["strongholds lost (65%+ D counties)"] = f"{b.iloc[-1].delta_dem_M:.2f}M (report: 2.9M)"

# 3. Economic perception follows party
p = pd.read_csv(T / "attribution_partisan_flip.csv")
write("03_perception_by_party", {
    "years": [{"year": int(x.year), "incumbent": {2016: "D", 2020: "R", 2024: "D"}[int(x.year)], "Democrats": r(x.Dem), "Independents": r(x.Ind),
               "Republicans": r(x.Rep)} for x in p.itertuples()],
    "variance_explained": {"county_economic_record": 0.006, "party_identification": 0.34},
    "note": "Mean answer to 'over the past year the nation's economy has...' (+2 much better ... -2 much worse), CES, weighted. "
            "Variance shares from report Part 4 (attribution_stage1).",
})
s1 = pd.read_csv(T / "attribution_stage1.csv", index_col=0)
checks["perception by party 2024 (D, R)"] = f"{p.iloc[-1].Dem:+.2f}, {p.iloc[-1].Rep:+.2f}"

# 4. The 2022 rating predicts the 2024 switch (panel)
t = pd.read_csv(T / "panel_timing_by_rating.csv")
write("04_rating_2022_predicts_switch", {
    "ratings": [{"rating_2022": x.rating_2022, "N": int(x.N), "switched": int(x.switched), "rate_unweighted": r(x.unweighted, 4),
                 "rate_weighted": r(x.weighted, 4)} for x in t.itertuples()],
    "note": "Biden 2020 voters in the CES 2020-22-24 panel: share who voted Trump in 2024, by how they rated the economy in 2022. "
            "Show unweighted (the report's headline); weighted reverses between the two middle categories (13 and 6 switchers).",
})
checks["2022 'much worse' switch rate / improved"] = f"{t.iloc[0].unweighted:.1%} ; {int(t.iloc[3:].N.sum())} saw improvement, {int(t.iloc[3:].switched.sum())} switched (report: 7.9%, 0 of 438)"

# 5. Switchers' issue positions
it = pd.read_csv(T / "issue_items_by_path.csv")
LABEL = {"expand_medicaid": "Expand Medicaid", "keep_ACA": "Keep the Affordable Care Act", "corp_tax_28": "Raise corporate tax to 28%",
         "tax_400k": "Raise taxes on $400k+", "student_loans": "Forgive student loans", "housing_subsidy": "Low-income housing incentives",
         "no_wall": "Oppose the border wall", "allow_asylum": "Allow asylum at the border", "legal_status": "Legal status for long-employed immigrants",
         "abortion_choice": "Abortion as a matter of choice", "samesex_marriage": "Federal recognition of same-sex marriage"}
rows = it[it["item"].isin(LABEL)]
write("05_issue_positions", {
    "items": [{"axis": x["axis"], "item": LABEL[x["item"]], "loyal_democrats": r(x["B->H"], 3), "switchers": r(x["B->T"], 3),
               "loyal_republicans": r(x["T->T"], 3)} for _, x in rows.iterrows()],
    "note": "Share taking the Democratic-aligned position, CES 2024 (weighted). Groups by recalled 2020 vote x 2024 vote; recall adds some "
            "consistent Trump voters to 'switchers', which pushes their immigration numbers up and economic numbers down slightly.",
})
checks["switchers: expand Medicaid / oppose wall"] = f"{it.set_index('item').loc['expand_medicaid','B->T']:.0%} / {it.set_index('item').loc['no_wall','B->T']:.0%} (report: 77% / 23%)"

# 6. Centrepiece: the order of events (CES panel 2020/2022/2024 + ANES 'Trump cares')
ct = pd.read_csv(T / "ces_panel_switch_timing.csv")
series = []
for m in ["approves Biden", "voted Democratic for House, 2022 (of voters)", "supports Medicare for all", "immigration conservatism (0-1)", "economy got worse"]:
    for x in ct[ct.measure == m].itertuples():
        series.append({"measure": m, "wave": int(x.wave), "loyal": r(x.loyal, 3), "switchers": r(x.switch, 3), "switchers_lo": r(x.switch_lo, 3),
                       "switchers_hi": r(x.switch_hi, 3), "N_switchers": int(x.N_switch), "N_loyal": int(x.N_loyal)})
tc = pd.read_csv(T / "anes_panel_trump_cares_share.csv")
for x in tc.itertuples():
    series.append({"measure": "says Trump 'really cares about people like you' (ANES)", "wave": int(x.wave), "loyal": r(x.loyal, 3),
                   "switchers": r(x.switch, 3), "N_switchers": int(x.switch_N), "switchers_count": int(x.switch_count),
                   "switchers_unweighted": r(x.switch_count / x.switch_N, 3),
                   "plot_field": "switchers_unweighted",
                   "why_unweighted": "21 switchers whose survey weights are extreme (three people carry 44% of the weight, effective n about 11), "
                                     "so the weighted share mostly tracks those three; the page text cites counts. Plot the count share and "
                                     "show the weighted share in the tooltip."})
write("06_order_of_events", {
    "series": series,
    "note": "Same people followed over time. CES 2020-22-24 panel: 39 Biden 2020 voters who voted Trump in 2024 ('switchers') vs ~1,640 "
            "who voted Harris ('loyal'). ANES 2016-20-24 panel for the Trump trait item: 21 switchers (weighted share; counts on hover). "
            "Small samples: intervals are wide; show N.",
})
g = lambda m, w: ct[(ct.measure == m) & (ct.wave.astype(str) == str(w))].iloc[0]
checks["switchers approve Biden 2022"] = f"{g('approves Biden', 2022).switch:.0%} (report: 31%)"
checks["switchers Medicare for all 2020/22/24"] = "/".join(f"{g('supports Medicare for all', w).switch:.0%}" for w in (2020, 2022, 2024)) + " (report: 79/87/47%)"
checks["Trump cares, switchers 2020 / 2024 (counts)"] = f"{int(tc.iloc[1].switch_count)} of {int(tc.iloc[1].switch_N)} / {int(tc.iloc[2].switch_count)} of {int(tc.iloc[2].switch_N)} (report: 2 of 21 / 10 of 20)"

# Sidebar: recall correction
rc = pd.read_csv(T / "ces_panel_recall_check.csv", index_col=0).iloc[:, 0]
sd = pd.read_csv(T / "share_decomposition_recall_corrected.csv", index_col=0)
write("sidebar_recall", {
    "panel": {"recalled_switchers": int(rc.recall_switchers), "true_switchers_among_them": int(rc.in_both),
              "reported_trump_in_2020": int(rc.recall_switchers_reported_Trump_2020), "true_switchers": int(rc.true_switchers),
              "trump_voters_misremembering_biden_pct": r(100 * rc.trump_recall_biden, 1)},
    "corrections": {"biden_switch_rate": {"label": "Share of Biden 2020 voters who voted Trump in 2024 (validated voters, one-time 2024 survey)", "before": r(100 * sd.loc["biden_switch_rate", "recall (published)"], 1), "after": r(100 * sd.loc["biden_switch_rate", "corrected: 2020 report"], 1)},
                    "switchers_per_reverse_switcher": {"label": "Biden-to-Trump switchers for every Trump-to-Harris switcher", "before": r(sd.loc["ratio_BT_TH", "recall (published)"], 1), "after": r(sd.loc["ratio_BT_TH", "corrected: 2020 report"], 1)},
                    "switching_share_of_shift_pct": {"label": "Share of Trump's 2024 edge that came from voters switching sides (the rest came mainly from new voters and 2020 third-party voters)", "before": r(100 * sd.loc["switch_share_of_shift", "recall (published)"], 0), "after": r(100 * sd.loc["switch_share_of_shift", "corrected: 2020 report"], 0)},
                    "much_worse_switch_rate_pct": {"label": "Switch rate among Biden voters who, in 2024, rated the economy 'much worse' (one-time 2024 survey, weighted); a different measure from chart 04, which uses the 2022 rating in the panel", "before": 31.6, "after": r(100 * pd.read_csv(T / "attribution_switching_recall_corrected.csv", index_col=0).loc["much worse", "corrected"], 1)}},
    "note": "CES 2020-24 panel: 2024 recall of the 2020 vote checked against what the same people reported in November 2020.",
})
checks["recall: 44 recalled, 34 true, 9 were Trump voters"] = f"{int(rc.recall_switchers)}, {int(rc.in_both)}, {int(rc.recall_switchers_reported_Trump_2020)}"
checks["switch ratio before/after"] = f"{sd.loc['ratio_BT_TH','recall (published)']:.1f} / {sd.loc['ratio_BT_TH','corrected: 2020 report']:.1f} (report: 3.4 / 2.6)"

# 7. NYC 2025: every Democrat on the ballot gained where voters had swung
ny = pd.read_csv(T / "nyc_2025_same_ballot_by_swing_decile.csv")
write("07_nyc_same_ballot", {
    "deciles": [{"decile": int(x.dec), "swing_to_trump_2024": r(x.swing, 1), "mamdani_vs_harris": r(x.mam_vs_H, 1), "levine_vs_harris": r(x.lev_vs_H, 1),
                 "williams_vs_harris": r(x.wil_vs_H, 1)} for x in ny.itertuples()],
    "labels": {"mamdani": "Mamdani (mayor)", "levine": "Levine (comptroller)", "williams": "Williams (public advocate)"},
    "note": "NYC election districts grouped into tenths by their 2020->2024 swing to Trump. Each line: 2025 Democratic share minus Harris's "
            "2024 share (points). All three Democrats gained most where the swing was largest.",
})
checks["NYC top decile: swing / Mamdani, Levine, Williams vs Harris"] = f"{ny.iloc[-1].swing:.1f} / {ny.iloc[-1].mam_vs_H:+.1f}, {ny.iloc[-1].lev_vs_H:+.1f}, {ny.iloc[-1].wil_vs_H:+.1f}"

# 8. Pre-registered Test A: benchmark slopes
bm = pd.read_csv(T / "michigan_testA_benchmark_2022.csv", index_col=[0, 1])
dr = pd.read_csv(T / "michigan_testA_dryrun_2024.csv", index_col=0)
rows = [{"comparison": pair, "sample": sub, "kind": "2022 benchmark: two down-ballot Democrats", "slope": r(x.slope, 3), "lo": r(x.lo, 3), "hi": r(x.hi, 3)}
        for (pair, sub), x in bm.iterrows()]
rows += [{"comparison": "Slotkin (Senate) - Harris (President), 2024", "sample": sub, "kind": "2024 dry run: pipeline check only", "slope": r(x.slope, 3),
          "lo": r(x.lo, 3), "hi": r(x.hi, 3)} for sub, x in dr.iterrows()]
rows += [{"comparison": "El-Sayed (Senate) - Benson (Governor), 2026", "sample": "all", "kind": "the pre-registered test: result after certification (late Nov 2026)",
          "slope": None, "lo": None, "hi": None}]
write("08_testA_benchmark", {
    "rows": rows,
    "note": "Slope of the gap between two Democrats' shares on the 2020->24 swing to Trump, across Michigan municipalities. Ordinary "
            "down-ballot pairs sit near zero (about -0.06 to +0.04); a 2026 slope clearly beyond about +/-0.1 would exceed ordinary "
            "candidate differences. Plan: report/preregistration_2026_general.md; benchmark: addendum 1.",
})
checks["2022 benchmark slope range"] = f"{bm.slope.min():.2f} to {bm.slope.max():.2f} (report: -0.06 to +0.04)"

(OUT / "CHECKS.txt").write_text("\n".join(f"{k}: {v}" for k, v in checks.items()), encoding="utf-8")
print("\n".join(f"{k}: {v}" for k, v in checks.items()))
print(f"\nwrote {len(list(OUT.glob('*.json')))} JSON files to {OUT}")
