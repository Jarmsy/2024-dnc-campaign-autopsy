"""Coverage audit: how complete is the news dataset, measured rather than assumed.

Three checks, in increasing order of what they can tell you.

1. **Share of total captured by named outlets.** The `ALL` series is every English-language source
   GDELT monitors; the named-domain series are six outlets. Their ratio says what fraction of the
   coverage we actually resolve to a publisher. It has been ~7-8%, meaning the outlet-level story
   describes a small slice and the rest is wires, aggregators, local and foreign press.

2. **Domain inventory.** Probes every outlet plausibly relevant to a NYC mayoral race -- local
   dailies and digitals, broadcast sites, national papers, partisan outlets, ethnic press -- to
   establish which ones GDELT indexes at all. A domain that returns nothing is not an absence of
   coverage; it is an absence of crawling, and the two must not be confused in the writeup.

3. **Recall against a census.** The NYT Archive API returns every article the paper published, so
   for nytimes.com we can compute GDELT's actual recall: of the days the Times demonstrably ran a
   Mamdani story, on how many did GDELT register any nytimes.com volume? This is the only one of
   the three that yields a real completeness number, and it only works for outlets with a public
   census API. Run nyt_archive_pull.py first.

Check 2 costs GDELT requests and must not run while another pull is active.
"""

from pathlib import Path
import json
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from gdelt_nyc_pull import fetch, WINDOWS  # noqa: E402  (reuses the throttle-aware fetcher)

GDELT_RAW = Path("data/raw/gdelt_nyc")
NYT_RAW = Path("data/raw/nyt_archive")
OUT = Path("outputs/tables")

# The outlet universe for a NYC mayoral race. Probing establishes which of these GDELT carries.
UNIVERSE = {
    "NYC daily": ["nytimes.com", "nypost.com", "nydailynews.com", "newsday.com", "amny.com"],
    "NYC digital": ["gothamist.com", "thecity.nyc", "hellgatenyc.com", "politico.com", "crainsnewyork.com", "cityandstateny.com"],
    "NYC broadcast": ["ny1.com", "abc7ny.com", "nbcnewyork.com", "cbsnews.com", "pix11.com", "fox5ny.com"],
    "national": ["washingtonpost.com", "wsj.com", "cnn.com", "foxnews.com", "msnbc.com", "npr.org", "apnews.com", "reuters.com", "axios.com", "theatlantic.com", "newyorker.com"],
    "partisan": ["breitbart.com", "dailywire.com", "thefp.com", "jacobin.com", "thenation.com", "nationalreview.com"],
    "ethnic / community": ["eldiariony.com", "amsterdamnews.com", "documentedny.com", "norwoodnews.org"],
}


def check_named_share():
    g = pd.read_csv(GDELT_RAW / "gdelt_nyc_daily.csv")
    tot = g[g.domain == "ALL"].groupby(["cycle", "candidate"]).volume.sum()
    nam = g[g.domain != "ALL"].groupby(["cycle", "candidate"]).volume.sum()
    df = pd.DataFrame({"all_sources": tot, "named_outlets": nam})
    df["share_named"] = df.named_outlets / df.all_sources
    print("1. SHARE OF INDEXED COVERAGE RESOLVED TO A NAMED OUTLET")
    print(df.round(4).to_string())
    print(f"   median {df.share_named.median():.1%} -- the outlet-level analysis describes this slice only\n")
    df.to_csv(OUT / "coverage_audit_named_share.csv")
    return df


def check_domain_inventory(window=2025):
    """One volume query per domain over the 2025 window. Costs ~len(UNIVERSE) GDELT requests."""
    cache = GDELT_RAW / "domain_inventory.json"
    known = json.loads(cache.read_text()) if cache.exists() else {}
    start, end = WINDOWS[window]
    rows = []
    for group, doms in UNIVERSE.items():
        for dom in doms:
            if dom not in known:
                df = fetch(f"mayor OR mayoral domain:{dom}", "timelinevol", start, end)
                known[dom] = {"days": len(df), "covered": int((df.value > 0).sum()) if len(df) else 0,
                              "total": float(df.value.sum()) if len(df) else 0.0}
                cache.write_text(json.dumps(known, indent=1))
                time.sleep(20)
            k = known[dom]
            rows.append({"group": group, "domain": dom, **k, "indexed": k["covered"] > 0})
            print(f"  {group:20s} {dom:24s} covered={k['covered']:4d} total={k['total']:.4f} {'OK' if k['covered'] else 'NOT INDEXED'}", flush=True)
    df = pd.DataFrame(rows)
    print(f"\n2. DOMAIN INVENTORY: {int(df.indexed.sum())} of {len(df)} outlets indexed by GDELT")
    print(df.groupby("group").indexed.agg(["sum", "count"]).to_string())
    df.to_csv(OUT / "coverage_audit_domain_inventory.csv", index=False)
    return df


def check_nyt_recall(candidate="mamdani", cycle=2025):
    """GDELT's recall for nytimes.com, benchmarked against the NYT's own census of its articles."""
    f = NYT_RAW / "nyt_mayoral_articles.csv"
    if not f.exists():
        print("3. NYT RECALL: run nyt_archive_pull.py first (needs NYT_API_KEY)\n"); return None
    nyt = pd.read_csv(f)
    nyt = nyt[(nyt.cycle == cycle) & nyt.candidates.str.contains(candidate, na=False)]
    nyt_days = set(pd.to_datetime(nyt.date).dt.date)
    g = pd.read_csv(GDELT_RAW / "gdelt_nyc_daily.csv")
    g["date"] = pd.to_datetime(g.date.astype(str).str[:8])
    gd = g[(g.cycle == cycle) & (g.candidate == candidate) & (g.domain == "nytimes.com") & (g.volume > 0)]
    gdelt_days = set(gd.date.dt.date)
    both = nyt_days & gdelt_days
    print(f"3. NYT RECALL, {candidate} {cycle}")
    print(f"   days the Times demonstrably published on {candidate}: {len(nyt_days)} ({len(nyt)} articles)")
    print(f"   days GDELT registered any nytimes.com volume:        {len(gdelt_days)}")
    print(f"   overlap: {len(both)}  ->  GDELT recall {len(both)/max(len(nyt_days),1):.1%} of publication days")
    print(f"   front-page (A1) articles in the census: {int(nyt.front_page.sum())}\n")
    return {"nyt_days": len(nyt_days), "gdelt_days": len(gdelt_days), "overlap": len(both),
            "recall": len(both) / max(len(nyt_days), 1), "a1": int(nyt.front_page.sum())}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    check_named_share()
    check_nyt_recall()
    if "--probe" in sys.argv:
        check_domain_inventory()
    else:
        print("2. DOMAIN INVENTORY: skipped (pass --probe; costs GDELT requests, do not run during another pull)")
