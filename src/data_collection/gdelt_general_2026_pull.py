"""GDELT DOC 2.0 API: news volume and tone for El-Sayed and Benson in the 2026 general-election campaign (E6).

Specified in report/results_2026_analysis_plan.md (Phase 1 step 2, "E6", and "E6. The size of the disparity"):
gdelt_insurgent_pull.py's design applied to the general election.
  - Window: the 90 days of the campaign, ending on election day. As in gdelt_insurgent_pull, the request runs
    from 5 August 2026 00:00 to 3 November 2026 00:00 UTC, but GDELT returns the whole end day, so a series
    has up to 91 daily bins. The 3 Nov bin ends at 7 pm EST, before Michigan's polls closed (election-day
    coverage, not results). The 5 Aug bin starts at 8 pm EDT on 4 Aug, when the primary polls closed, so it
    carries primary-night coverage. Report totals with and without those two days. (Part 11's series from
    gdelt_insurgent_pull have the same end-day bin.)
  - Index gaps: every query returned 69 of the 91 days. GDELT has no data at all on 14-19 and 26 Sep;
    3-5, 7, 9 and 11-14 Oct; and 28 Oct-2 Nov, the final week. Those are gaps in the index, not days without
    coverage, and E6 must say so.
  - Phase 1: all English-language sources. Phase 2 (`--phase2`): named outlets, for candidates whose phase-1
    series has at least MIN_DAYS covered days. The outlets are gdelt_insurgent_pull's four national ones plus
    five Michigan outlets: freep.com, detroitnews.com, mlive.com, bridgemi.com and michiganadvance.com.
  - Volume and tone use gdelt_insurgent_pull.series (timelinevol and timelinetone, exact-phrase query) and its
    throttle-aware fetch; the same caveats apply (CLAUDE.md, GDELT row): never probe by hand while this runs.

MSNBC became MS NOW; the SSRS statement for the 2026 Voter Poll lists the network as "MSNOW". `--probe` runs
before the pull and counts covered days for a broad query on each outlet (national outlets: "Trump"; Michigan
outlets: "Michigan"), and on ms.now as well as msnbc.com. A domain with no coverage of a broad query is an
absence of crawling, not of coverage. The counts are saved to probe.csv; if ms.now has any coverage in the
window it is pulled in phase 2 beside msnbc.com, and the two are reported separately.

Descriptive only: neither series varies by town, so neither enters Test A's regressions.
Run from the repo root: --probe, then no flag (phase 1), then --phase2.
"""
from pathlib import Path
import argparse
import datetime as dt
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gdelt_insurgent_pull import DOMAINS as NATIONAL, MIN_DAYS, fetch, series  # noqa: E402

RAW = Path("data/raw/gdelt_general_2026")
ELECTION = dt.datetime(2026, 11, 3)
WINDOW_DAYS = 90
START = ELECTION - dt.timedelta(days=WINDOW_DAYS)
W = (START.strftime("%Y%m%d%H%M%S"), ELECTION.strftime("%Y%m%d%H%M%S"))
CANDIDATES = {"El-Sayed": "Abdul El-Sayed", "Benson": "Jocelyn Benson"}
MICHIGAN = ["freep.com", "detroitnews.com", "mlive.com", "bridgemi.com", "michiganadvance.com"]
MSNOW = "ms.now"


def probe():
    rows = []
    for dom, q in [(d, "Trump") for d in NATIONAL + [MSNOW]] + [(d, "Michigan") for d in MICHIGAN]:
        v = fetch(f"{q} domain:{dom}", "timelinevol", *W)
        covered = int((v.value > 0).sum()) if len(v) else 0
        rows.append({"domain": dom, "query": q, "days_returned": len(v), "covered_days": covered,
                     "first_covered": v.date[v.value > 0].min() if covered else "",
                     "last_covered": v.date[v.value > 0].max() if covered else ""})
        print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(RAW / "probe.csv", index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="check which outlets GDELT indexes in the window")
    ap.add_argument("--phase2", action="store_true", help="pull the named outlets for candidates that cleared phase 1")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    print(f"window {W[0]} to {W[1]}", flush=True)
    if args.probe:
        return probe()
    out, empties = RAW / "gdelt_general_2026_daily.csv", RAW / "empty_series.txt"
    frames, done = [], set()
    if out.exists():
        prev = pd.read_csv(out); frames = [prev]
        done = set(zip(prev.candidate, prev.domain))
    if empties.exists():
        done |= {tuple(l.split(",")) for l in empties.read_text().split("\n") if l.strip()}

    jobs = [(c, p, "ALL") for c, p in CANDIDATES.items()]
    if args.phase2:
        pr = pd.read_csv(RAW / "probe.csv")
        domains = NATIONAL + MICHIGAN
        if int(pr.loc[pr.domain == MSNOW, "covered_days"].sum()) > 0:
            domains = NATIONAL + [MSNOW] + MICHIGAN
        prev = pd.read_csv(out)
        cov = prev[prev.domain == "ALL"].groupby("candidate").volume.apply(lambda s: int((s > 0).sum()))
        keep = [c for c, v in cov.items() if v >= MIN_DAYS]
        print(f"phase 2: covered days in phase 1 {cov.to_dict()}; pulling {keep} on {domains}", flush=True)
        jobs = [(c, CANDIDATES[c], d) for c in keep for d in domains]

    print(f"{len(jobs)} series to pull; {len(done)} already on disk", flush=True)
    for cand, phrase, dom in jobs:
        if (cand, dom) in done:
            continue
        df = series(phrase, dom, *W)
        if df.empty:
            with empties.open("a") as f:
                f.write(f"{cand},{dom}\n")
            print(f"{cand:9s} {dom:20s} EMPTY", flush=True)
            continue
        df["candidate"] = cand; df["name"] = phrase; df["domain"] = dom
        frames.append(df)
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(f"{cand:9s} {dom:20s} days={len(df)} covered={int((df.volume > 0).sum())} "
              f"mean_vol={df.volume.mean():.5f} mean_tone={df.tone.mean():+.2f}", flush=True)
    print("wrote", out, flush=True)


if __name__ == "__main__":
    main()
