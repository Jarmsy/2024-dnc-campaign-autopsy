"""June 2026 NYC Democratic congressional primaries, by election district.

Why. Part 10's New York finding rests on one candidate in one year: the report's own limitation is
"New York is one city, with a candidate ... that do not generalize." Eight months after Mamdani's
general election, five 2026 Democratic House primaries inside the city pitted a candidate running to
the left against an establishment one -- two of them won by DSA members, one by a sitting mayoral
ally, three against incumbents. They were fought over the same election districts, so the question
Part 10 could not ask becomes answerable: did the coalition that nominated Mamdani turn out again,
for different candidates, in a different kind of race?

Source. NYC Board of Elections ED-level CSVs under
`vote.nyc/sites/default/files/pdf/election_results/2026/20260623Primary Election/`, one per
(county, congressional district). Congressional primaries are not ranked-choice, so -- unlike the
2025 mayoral primary -- they are published at ED level directly, in the same header-prefixed format
`nyc_pull.read_boe_edlevel` already parses.

Two traps, both handled here.

1. **Crossover files duplicate county files.** For districts spanning two counties BOE also publishes
   a "Crossover" file, and each one is exactly the union of that district's county files (checked:
   every crossover ED appears in a county file, none is crossover-only). Only the county files are
   read; reading both would double-count every multi-county district.
2. **Ballot-method rows are not candidates.** "Public Counter", "Manually Counted Emergency",
   "Absentee / Military", "Federal" and "Affidavit" tally ballots by how they were cast and sum to the
   ED's ballots; candidate rows sum to its votes. They are separated, not summed together.

The left candidate in each contest. Classified from the candidates' own positioning, not from the
result: Valdez (NY-7, open, DSA), Lander (NY-10, against incumbent Goldman; Mamdani's cross-endorsed
ally in 2025), Avila Chevalier (NY-13, against Espaillat, DSA), Park (NY-6, against Meng, ran to her
left on AIPAC money and the Mets casino), Blake (NY-15, against Torres, ran on Israel, AIPAC and
affordability). NY-3, 9, 11, 12 and 14 are pulled but have no establishment-versus-left axis of this
kind and are not used in the replication.

District lines. 99.7% of 2026 ED numbers exist in the November 2025 panel, but between the November
2025 and February 2026 enrolment snapshots 6.9% of EDs changed their registered total by more than
25%, in both directions -- the signature of boundary edits, not a list purge, which would only go
down. Those EDs are flagged `lines_changed` so the analysis can exclude them: for them the same number
denotes different streets in 2025 and 2026.
"""

from pathlib import Path
import glob
import re
import subprocess
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from nyc_pull import read_boe_edlevel  # noqa: E402

RAW = Path("data/raw/nyc/2026_primary")
ENROLL = Path("data/raw/nyc_enrollment/nyc_enrollment_by_ed.csv")
OUT = Path("data/raw/nyc/nyc_2026_congressional_primary_by_ed.csv")
METHOD_ROWS = {"Public Counter", "Manually Counted Emergency", "Absentee / Military", "Federal", "Affidavit"}
LEFT = {7: "Claire Valdez", 10: "Brad Lander", 13: "Darializa Avila Chevalier",
        6: "Chuck Park", 15: "Michael Blake"}
ESTABLISHMENT = {7: "Antonio Reynoso", 10: "Dan Goldman", 13: "Adriano Espaillat",
                 6: "Grace Meng", 15: "Ritchie Torres"}
TIER = {7: "DSA", 13: "DSA", 10: "progressive", 6: "progressive", 15: "progressive"}
INCUMBENT_CHALLENGED = {10: True, 13: True, 6: True, 15: True, 7: False}
LINE_CHANGE_THRESHOLD = 0.25


def load():
    files = [f for f in sorted(glob.glob(str(RAW / "*EDLevel.csv"))) if "Crossover" not in f]
    if not files:
        raise SystemExit(f"no ED-level files in {RAW}; download them from the BOE 2026 primary results page")
    frames = []
    for f in files:
        d = read_boe_edlevel(f)
        d["cd"] = int(re.search(r"Congress (\d+)", f).group(1))
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def main():
    a = load()
    a = a[a["EDAD Status"] == "IN-PLAY"]
    ballots = a[a["Unit Name"].isin(METHOD_ROWS)].groupby(["cd", "ElectDist"]).Tally.sum().rename("ballots26")
    votes = a[~a["Unit Name"].isin(METHOD_ROWS)]
    total = votes.groupby(["cd", "ElectDist"]).Tally.sum().rename("votes26")
    rows = []
    for cd in LEFT:
        v = votes[votes.cd == cd]
        left = v[v["Unit Name"] == LEFT[cd]].groupby("ElectDist").Tally.sum()
        est = v[v["Unit Name"] == ESTABLISHMENT[cd]].groupby("ElectDist").Tally.sum()
        df = pd.DataFrame({"left_votes": left, "est_votes": est}).fillna(0)
        df["cd"] = cd; df["left_candidate"] = LEFT[cd]; df["est_candidate"] = ESTABLISHMENT[cd]
        df["tier"] = TIER[cd]; df["challenges_incumbent"] = INCUMBENT_CHALLENGED[cd]
        rows.append(df.reset_index())
    out = pd.concat(rows, ignore_index=True)
    out = out.merge(total.reset_index(), on=["cd", "ElectDist"], how="left")
    out = out.merge(ballots.reset_index(), on=["cd", "ElectDist"], how="left")
    out["left_share"] = out.left_votes / out.votes26
    out["left_h2h"] = out.left_votes / (out.left_votes + out.est_votes)

    # boundary-change flag from the enrolment snapshots either side of the redraw
    en = pd.read_csv(ENROLL)
    t = en[en.status == "total"].pivot_table(index="ElectDist", columns="snapshot", values="TOTAL", aggfunc="sum")
    chg = (t["2026-02-20"] / t["2025-11-01"] - 1).abs()
    dem = en[en.status == "total"].pivot_table(index="ElectDist", columns="snapshot", values="DEM", aggfunc="sum")
    out["dem_enrolled_feb26"] = out.ElectDist.map(dem["2026-02-20"])
    out["lines_changed"] = out.ElectDist.map(chg > LINE_CHANGE_THRESHOLD).fillna(True)
    out.to_csv(OUT, index=False)

    print(f"wrote {OUT}: {out.shape}")
    for cd, g in out.groupby("cd"):
        L, E = g.left_votes.sum(), g.est_votes.sum()
        print(f"  NY-{cd:<2d} {LEFT[cd]:26s} {L:>7,.0f} vs {ESTABLISHMENT[cd]:18s} {E:>7,.0f}   "
              f"left h2h {L/(L+E):.1%}   EDs {len(g)}, lines changed {int(g.lines_changed.sum())}")


if __name__ == "__main__":
    main()
