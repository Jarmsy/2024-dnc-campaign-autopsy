"""GDELT DOC 2.0 API: coverage volume and tone for the contested Justice Democrats challenger
cases (Part 11), each challenger and the incumbent they ran against.

Design differs from gdelt_nyc_pull.py in three ways forced by the subject matter:

1. **Window is per case, not per cycle.** For each case the window is the 90 days ending on the
   primary date. Coverage after a primary is mostly a consequence of the result (AOC's volume
   multiplied roughly a hundredfold the week she won), so the post-primary period cannot go into a
   variable meant to predict the result. Even inside the window coverage responds to perceived
   viability -- this measures what was published, not an exogenous treatment.
2. **Phased.** Phase 1 pulls the all-English-sources series for every candidate; a House primary
   challenger is not the mayor of New York, and most of these names have little indexed national
   coverage. Phase 2 pulls the four national outlets only for candidates whose phase-1 series
   clears MIN_DAYS covered days, so domain-restricted requests are spent only where there is
   something to measure. Run with --phase2 after inspecting phase 1.
3. **Names are hand-checked.** FEC opponent names are uppercase "LAST, FIRST MIDDLE SUFFIX" and
   several collide with other public figures; OPP_NAME maps each to the form the press uses.
   Ambiguity that remains (common names) inflates volume and dilutes tone -- flagged, not fixed.

Retry pacing is set from the logs, not from the API's advice. Acceptance is ~21% per attempt and
does not improve with longer waits (23.0% at 120-360 s vs 20.5% at 60 s, z = 0.61), so there is no
cooldown to wait out. Rejections do cluster -- runs of 6+ consecutive refusals are twice as common as
a memoryless process would give -- so some of the wait is a real server-side bad patch that polling
cannot shorten; it can only be detected sooner. Measured elasticity between the two runs: polling
1.85x faster raised the reject count 1.16x and cut total wait 37%. Hence a short flat retry (RETRY s),
which still works out to about one request per 32 s while throttled, well inside the stated 5 s floor.
Progress is checkpointed per series.
"""

from pathlib import Path
import argparse
import datetime as dt
import time
import urllib.parse
import numpy as np
import pandas as pd
import requests

RAW = Path("data/raw/gdelt_insurgent")
CASES_CSV = Path("data/raw/insurgent/jd_cases_fec.csv")
API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
DOMAINS = ["foxnews.com", "cnn.com", "msnbc.com", "nytimes.com"]
WINDOW_DAYS = 90
MIN_DAYS = 10          # phase-1 covered days required before spending phase-2 requests on a candidate
PAUSE, RETRY = 20, 20

# Result and tier definitions are notebook 19's, repeated here so the pull does not depend on it.
OVERRIDE = {(2022, "Jessica Cisneros"): ("Lost", 49.69), (2022, "Kina Collins"): ("Lost", 45.72),
            (2022, "Marie Newman"): ("Lost", 29.23), (2018, "Lorie Burch"): ("Won", 75.04)}
DSA = {"Alexandria Ocasio-Cortez", "Rashida Tlaib", "Cori Bush", "Jamaal Bowman", "Ilhan Omar", "Summer Lee", "Greg Casar",
       "Melat Kiros", "Donavan McKinney", "Chris Rabb", "Claire Valdez", "Darializa Avila Chevalier", "Kaniela Ing", "Sarah Smith"}
# FEC filer name -> the name the press uses.
OPP_NAME = {
    "DEGETTE, DIANA L.": "Diana DeGette", "DEGETTE, DIANA L": "Diana DeGette", "MURPHY, STEPHANIE": "Stephanie Murphy",
    "LIPINSKI, DANIEL WILLIAM WILLIAM": "Daniel Lipinski", "QUIGLEY, MIKE": "Mike Quigley", "DAVIS, DANNY K": "Danny Davis",
    "DAVIS, DANNY K. MR.": "Danny Davis", "CAPUANO, MICHAEL E": "Michael Capuano", "CLAY, WILLIAM LACY JR": "Lacy Clay",
    "CROWLEY, JOSEPH": "Joe Crowley", "NEAL, RICHARD E MR.": "Richard Neal", "ENGEL, ELIOT L.": "Eliot Engel",
    "BEATTY, JOYCE": "Joyce Beatty", "CUELLAR, HENRY": "Henry Cuellar", "THANEDAR, SHRI": "Shri Thanedar",
    "BELL, WESLEY": "Wesley Bell", "ESPAILLAT, ADRIANO": "Adriano Espaillat", "FOUSHEE, VALERIE": "Valerie Foushee",
}


def cases():
    d = pd.read_csv(CASES_CSV)
    for (cy, nm), (res, pct) in OVERRIDE.items():
        d.loc[(d.cycle == cy) & (d.candidate == nm), ["prim_result", "prim_pct"]] = [res, f"{pct}%"]
    d["pct"] = pd.to_numeric(d.prim_pct.astype(str).str.rstrip("%"), errors="coerce")
    d["pending"] = (d.prim_result == "Advanced") & (~d.jd_incumbent) & d.state.isin(["CA", "WA"])
    ch = d[(~d.jd_incumbent) & d.opp_is_incumbent & (d.pct < 99) & (~d.pending)].copy()
    ch["tier"] = np.where(ch.candidate.isin(DSA), "DSA", "JD-only")
    ch["won"] = ch.prim_result.isin(["Won", "Advanced"]).astype(int)
    ch["primary_date"] = pd.to_datetime(ch.primary_date, format="mixed")
    ch["opp_display"] = ch.opp_name.map(OPP_NAME)
    missing = ch[ch.opp_display.isna()].opp_name.unique()
    if len(missing):
        raise SystemExit(f"opponent names not in OPP_NAME, add them: {list(missing)}")
    return ch.reset_index(drop=True)


def fetch(query, mode, start, end):
    url = f"{API}?query={urllib.parse.quote(query)}&mode={mode}&startdatetime={start}&enddatetime={end}&format=json"
    attempt = 0
    while True:
        t0 = time.time()
        try:
            r = requests.get(url, headers=UA, timeout=900)
        except requests.RequestException as e:
            print(f"    {type(e).__name__} after {time.time() - t0:.0f} s; waiting {RETRY} s", flush=True)
            time.sleep(RETRY); continue
        if r.status_code == 200 and r.text.startswith("{"):
            s = r.json().get("timeline", [])
            return pd.DataFrame(s[0]["data"]) if s else pd.DataFrame(columns=["date", "value"])
        attempt += 1
        print(f"    throttled ({r.status_code}) attempt {attempt}, {time.time() - t0:.0f} s; waiting {RETRY} s", flush=True)
        time.sleep(RETRY)


def series(phrase, dom, start, end):
    q = f'"{phrase}"' + (f" domain:{dom}" if dom != "ALL" else " sourcelang:english")
    vol = fetch(q, "timelinevol", start, end); time.sleep(PAUSE)
    tone = fetch(q, "timelinetone", start, end); time.sleep(PAUSE)
    if vol.empty and tone.empty:
        return pd.DataFrame()
    return vol.rename(columns={"value": "volume"}).merge(tone.rename(columns={"value": "tone"}), on="date", how="outer")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase2", action="store_true", help="pull the national domains for candidates that cleared phase 1")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "gdelt_insurgent_daily.csv"
    empties = RAW / "empty_series.txt"
    frames, done = [], set()
    if out.exists():
        prev = pd.read_csv(out); frames = [prev]
        done = set(zip(prev.case_id, prev.role, prev.domain))
    if empties.exists():
        done |= {(c, r, d) for c, r, d in (l.split(",") for l in empties.read_text().split("\n") if l.strip())}

    ch = cases()
    jobs = []
    for _, c in ch.iterrows():
        case_id = f"{c.cycle}-{c.state}{c.district}"
        end = c.primary_date; start = end - dt.timedelta(days=WINDOW_DAYS)
        w = (start.strftime("%Y%m%d%H%M%S"), end.strftime("%Y%m%d%H%M%S"))
        for role, phrase in [("challenger", c.candidate), ("incumbent", c.opp_display)]:
            for dom in (DOMAINS if args.phase2 else ["ALL"]):
                jobs.append((case_id, role, phrase, dom, w, c.tier, c.won))

    if args.phase2:
        prev = pd.read_csv(out)
        cov = prev[prev.domain == "ALL"].groupby(["case_id", "role"]).volume.apply(lambda s: (s > 0).sum())
        keep = {k for k, v in cov.items() if v >= MIN_DAYS}
        print(f"phase 2: {len(keep)} of {len(cov)} candidate-series clear {MIN_DAYS} covered days", flush=True)
        jobs = [j for j in jobs if (j[0], j[1]) in keep]

    print(f"{len(jobs)} series to pull; {len(done)} already on disk", flush=True)
    for case_id, role, phrase, dom, (start, end), tier, won in jobs:
        if (case_id, role, dom) in done:
            continue
        df = series(phrase, dom, start, end)
        if df.empty:
            with empties.open("a") as f:
                f.write(f"{case_id},{role},{dom}\n")
            print(f"{case_id:12s} {role:10s} {dom:13s} EMPTY", flush=True)
            continue
        df["case_id"] = case_id; df["role"] = role; df["name"] = phrase; df["domain"] = dom
        df["tier"] = tier; df["won"] = won
        frames.append(df)
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(f"{case_id:12s} {role:10s} {dom:13s} days={len(df)} covered={int((df.volume > 0).sum())} "
              f"mean_vol={df.volume.mean():.5f} mean_tone={df.tone.mean():+.2f}", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
