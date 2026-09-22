"""GDELT DOC 2.0 `artlist`: individual article headlines for the insurgent-primary challengers,
so framing can be measured instead of sentiment.

Why article level. The daily `timelinevol`/`timelinetone` series carry no text, and tone is a
lexicon score over word valence which Part 10 shows to be nearly blind to framing -- it reads *war*
and *criticism* as isolated tokens and cannot see the choice to lead with a candidate's religion or
to label them radical. `artlist` returns one record per article with its **title**, which is where
framing lives, and is the same kind of text the NYT census analysis used.

The 250-record cap. Each query returns at most 250 articles, sorted by date. A low-volume candidate
fits in one call (Kina Collins: 113 articles over 38 days, complete); a busier one silently
truncates to the last day or two (Cori Bush 2020: 250 articles over 11 days of a 90-day window).
Truncation is not random -- it keeps the end of the window, which is the campaign's final days -- so
it would bias any framing rate toward late coverage. `fetch_window` therefore checks for the cap and
recursively bisects the window until each piece comes back under it, which costs one query for a
quiet candidate and a handful for a loud one instead of a fixed grid for everybody.

Window: the 90 days ending on the primary date, matching gdelt_insurgent_pull.py. Challengers only
by default -- the tier comparison (DSA vs Justice-Democrats-only) holds incumbency constant, which
is the cleaner contrast; pass --incumbents to add the opponents as well.

Throttling and pacing are gdelt_nyc_pull.py's, for the reasons documented there.
"""

from pathlib import Path
import argparse
import datetime as dt
import sys
import time
import urllib.parse

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
from gdelt_insurgent_pull import cases, WINDOW_DAYS  # noqa: E402

RAW = Path("data/raw/gdelt_insurgent")
API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
MAXRECORDS = 250
MIN_SPAN_HOURS = 12      # floor on bisection; below this a cap-hit is accepted and flagged
PAUSE, RETRY = 20, 20


def fetch(query, start, end):
    url = (f"{API}?query={urllib.parse.quote(query)}&mode=artlist&maxrecords={MAXRECORDS}"
           f"&sort=datedesc&startdatetime={start}&enddatetime={end}&format=json")
    attempt = 0
    while True:
        t0 = time.time()
        try:
            r = requests.get(url, headers=UA, timeout=900)
        except requests.RequestException as e:
            print(f"      {type(e).__name__} after {time.time()-t0:.0f}s; waiting {RETRY}s", flush=True)
            time.sleep(RETRY); continue
        if r.status_code == 200 and r.text.startswith("{"):
            return r.json().get("articles", [])
        attempt += 1
        print(f"      throttled ({r.status_code}) attempt {attempt}; waiting {RETRY}s", flush=True)
        time.sleep(RETRY)


def fetch_window(query, a, b, depth=0):
    """Articles in [a, b), bisecting whenever the response hits the record cap."""
    arts = fetch(query, a.strftime("%Y%m%d%H%M%S"), b.strftime("%Y%m%d%H%M%S"))
    time.sleep(PAUSE)
    span_h = (b - a).total_seconds() / 3600
    if len(arts) < MAXRECORDS or span_h <= MIN_SPAN_HOURS:
        if len(arts) >= MAXRECORDS:
            print(f"      {'  '*depth}[{a:%Y-%m-%d}..{b:%Y-%m-%d}] {len(arts)} CAPPED at floor span", flush=True)
        return arts, (1, 1 if len(arts) >= MAXRECORDS else 0)
    mid = a + (b - a) / 2
    print(f"      {'  '*depth}[{a:%Y-%m-%d}..{b:%Y-%m-%d}] hit cap, splitting", flush=True)
    l_arts, (lq, lc) = fetch_window(query, a, mid, depth + 1)
    r_arts, (rq, rc) = fetch_window(query, mid, b, depth + 1)
    return l_arts + r_arts, (1 + lq + rq, lc + rc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incumbents", action="store_true", help="also pull each challenger's opponent")
    args = ap.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "gdelt_insurgent_articles.csv"
    done, frames = set(), []
    if out.exists():
        prev = pd.read_csv(out); frames = [prev]
        done = set(zip(prev.case_id, prev.role))

    ch = cases()
    jobs = []
    for _, c in ch.iterrows():
        cid = f"{c.cycle}-{c.state}{c.district}"
        end = c.primary_date; start = end - dt.timedelta(days=WINDOW_DAYS)
        jobs.append((cid, "challenger", c.candidate, start, end, c.tier, c.won))
        if args.incumbents:
            jobs.append((cid, "incumbent", c.opp_display, start, end, c.tier, c.won))

    print(f"{len(jobs)} candidates to pull; {len(done)} already on disk", flush=True)
    for cid, role, name, start, end, tier, won in jobs:
        if (cid, role) in done:
            continue
        print(f"  {cid} {role} {name}", flush=True)
        arts, (nq, ncap) = fetch_window(f'"{name}" sourcelang:english', start, end)
        if not arts:
            print(f"    no articles", flush=True); continue
        df = pd.DataFrame(arts)[["seendate", "title", "domain", "url", "sourcecountry"]]
        df = df.drop_duplicates(subset="url")
        df["case_id"] = cid; df["role"] = role; df["name"] = name; df["tier"] = tier; df["won"] = won
        df["capped_subwindows"] = ncap
        frames.append(df)
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(f"    {len(df)} articles in {nq} queries"
              f"{f' ({ncap} sub-windows still capped)' if ncap else ''}", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
