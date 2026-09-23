"""GDELT DOC 2.0 `artlist` for the 2025 NYC mayoral candidates, per outlet, so framing can be
compared across publishers the way it was for the insurgent primaries.

Why per outlet rather than all-sources. The insurgent framing analysis pulled all English sources
and then classified domains after the fact, which left 89% of articles in an unclassified tail of
local and aggregator sites. Here the question is explicitly about named publishers -- the *Post* and
Fox against CNN and the rest -- so each outlet is queried directly. That also keeps the record cap
manageable: a domain-restricted query returns far fewer articles than an all-sources one, so most
windows come back complete without bisection.

nytimes.com is deliberately absent. GDELT's crawl of it collapses for 2025 (5.8% recall against the
paper's own census, A.11), so its headlines come from `nyt_archive_pull.py` instead, which is a
census rather than a sample and can be scored with the same lexicon.

Cuomo is pulled as the control: he is the candidate Mamdani actually ran against, so any outlet's
house style -- some run loaded language about everyone -- differences out.
"""

from pathlib import Path
import datetime as dt
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from gdelt_artlist_pull import fetch_window  # noqa: E402  (adaptive cap-aware windowing)

RAW = Path("data/raw/gdelt_nyc")
# nytimes.com omitted on purpose: use the Archive census. msnbc.com kept despite thin volume so the
# left-of-centre cable comparison exists even if it ends up too small to read.
DOMAINS = ["nypost.com", "foxnews.com", "cnn.com", "nydailynews.com", "washingtonpost.com", "msnbc.com"]
CANDIDATES = {"mamdani": "Mamdani", "cuomo": "Andrew Cuomo"}
START, END = dt.datetime(2025, 1, 1), dt.datetime(2025, 11, 5)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "gdelt_nyc_articles.csv"
    frames, done = [], set()
    if out.exists():
        prev = pd.read_csv(out); frames = [prev]
        done = set(zip(prev.candidate, prev.domain))

    jobs = [(c, phrase, d) for c, phrase in CANDIDATES.items() for d in DOMAINS]
    print(f"{len(jobs)} candidate x outlet series", flush=True)
    for cand, phrase, dom in jobs:
        if (cand, dom) in done:
            continue
        print(f"  {cand} @ {dom}", flush=True)
        arts, (nq, ncap) = fetch_window(f'"{phrase}" domain:{dom}', START, END)
        if not arts:
            print("    no articles", flush=True)
            continue
        df = pd.DataFrame(arts)[["seendate", "title", "domain", "url"]].drop_duplicates(subset="url")
        df["candidate"] = cand
        df["query_domain"] = dom
        df["capped_subwindows"] = ncap
        frames.append(df)
        pd.concat(frames, ignore_index=True).to_csv(out, index=False)
        print(f"    {len(df)} articles in {nq} queries"
              f"{f' ({ncap} still capped)' if ncap else ''}", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
