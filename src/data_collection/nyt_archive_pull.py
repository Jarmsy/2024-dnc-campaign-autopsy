"""New York Times Archive API: a census of NYT articles for the 2021 and 2025 mayoral cycles,
with print page and section -- the one prestige measure that is actually observable.

Why this exists alongside the GDELT pull. GDELT samples what it crawls; for nytimes.com in 2025 it
holds 12 covered days out of 292 for Mamdani against 158 for Adams in 2021, which is a crawl
artifact (paywall), not an editorial fact. The Archive API is different in kind: it returns *every*
article the paper published in a month, so it is a census, not a sample. That makes it both the
right source for "how did the Times cover this" and the yardstick for measuring how much GDELT
misses -- see audit_coverage.py, which benchmarks GDELT's nytimes.com recall against this file.

`print_page` and `print_section` are the payload: a story on A1 is a different act of editorial
judgment from the same story on A17, and nothing in GDELT can see that distinction. Web-only
pieces have no print page and are kept with print_page = NaN rather than dropped.

Needs NYT_API_KEY (free, developer.nytimes.com, "Archive API" enabled on the app).
One request per month; the documented limits are 5/minute and 500/day, so requests are spaced 15 s.
Monthly JSON is cached raw under data/raw/nyt_archive/ (7-25 MB each) and never refetched. The API
drops large bodies mid-transfer and returns intermittent 5xx, both of which are retried. Errors are
raised without the request URL: it carries the api-key, and requests' own raise_for_status would
put that key into the traceback and from there into any log.
"""

from pathlib import Path
import json
import os
import re
import time

import pandas as pd
import requests

RAW = Path("data/raw/nyt_archive")
API = "https://api.nytimes.com/svc/archive/v1/{year}/{month}.json"
PAUSE = 15
MONTHS = [(2021, m) for m in range(1, 12)] + [(2025, m) for m in range(1, 12)]

# Word-boundary patterns. Surnames alone would pull in unrelated people (there are many Adamses),
# so each is anchored to the full name or to an unambiguous surname in a mayoral-race context.
CANDIDATES = {
    "mamdani":  r"\bMamdani\b",
    "cuomo":    r"\bAndrew Cuomo\b|\bCuomo\b",
    "adams":    r"\bEric Adams\b",
    "sliwa":    r"\bCurtis Sliwa\b|\bSliwa\b",
    "lander":   r"\bBrad Lander\b",
    "stringer": r"\bScott Stringer\b",
    "garcia":   r"\bKathryn Garcia\b",
    "wiley":    r"\bMaya Wiley\b",
    "yang":     r"\bAndrew Yang\b",
}
# Cuomo needs disambiguating: Mario Cuomo, and Andrew Cuomo's governorship/scandal coverage that
# is not about the mayoral race. Kept but flagged, so the notebook can require a race term too.
RACE_TERMS = r"\bmayor|mayoral|City Hall|primary|ranked[- ]choice\b"


def fetch_month(year, month, key, tries=5):
    """One month of the archive. Responses are 7-25 MB and the connection is dropped mid-body often
    enough to matter, so a truncated read is retried rather than fatal. The cache is written only
    after the body parses, so a partial download can never poison it."""
    cache = RAW / f"{year}-{month:02d}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(API.format(year=year, month=month), params={"api-key": key}, timeout=300)
            if r.status_code == 401:
                raise SystemExit("NYT_API_KEY rejected (401). Check the key and that the app has the Archive API enabled.")
            if r.status_code in (429, 500, 502, 503, 504):
                wait = 30 * attempt
                print(f"    HTTP {r.status_code} on {year}-{month:02d} (attempt {attempt}/{tries}); waiting {wait} s", flush=True)
                time.sleep(wait); continue
            if r.status_code != 200:
                # raise_for_status puts the full URL, and therefore the key, into the traceback
                raise SystemExit(f"{year}-{month:02d}: unexpected HTTP {r.status_code}")
            j = r.json()
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout, json.JSONDecodeError) as e:
            wait = 20 * attempt
            print(f"    {type(e).__name__} on {year}-{month:02d} (attempt {attempt}/{tries}); waiting {wait} s", flush=True)
            time.sleep(wait); continue
        cache.write_text(json.dumps(j), encoding="utf-8")
        time.sleep(PAUSE)
        return j
    raise SystemExit(f"{year}-{month:02d} failed after {tries} attempts")


def main():
    key = os.environ.get("NYT_API_KEY")
    if not key:
        env = Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("NYT_API_KEY"):
                    key = line.split("=", 1)[1].strip()
    if not key:
        raise SystemExit(
            "NYT_API_KEY not set. Get a free key at developer.nytimes.com (create an app, enable\n"
            "the Archive API), then add a line NYT_API_KEY=... to .env"
        )
    RAW.mkdir(parents=True, exist_ok=True)
    rows = []
    for year, month in MONTHS:
        j = fetch_month(year, month, key)
        docs = j.get("response", {}).get("docs", [])
        hits = 0
        for d in docs:
            text = " ".join(filter(None, [
                (d.get("headline") or {}).get("main"), (d.get("headline") or {}).get("print_headline"),
                d.get("abstract"), d.get("lead_paragraph"), d.get("snippet"),
                " ".join(k.get("value", "") for k in (d.get("keywords") or [])),
            ]))
            who = [c for c, pat in CANDIDATES.items() if re.search(pat, text, re.I)]
            if not who:
                continue
            hits += 1
            page = d.get("print_page")
            head = (d.get("headline") or {}).get("main") or ""
            # Scoreable text is headline + abstract ONLY. lead_paragraph is populated for 98.7% of
            # 2021 records and 0% of 2025 ones, so including it would score the two cycles on
            # different amounts of text and make every cross-cycle comparison an artifact.
            rows.append({
                "cycle": year, "date": (d.get("pub_date") or "")[:10],
                "text": (head + ". " + (d.get("abstract") or "")).strip(),
                "candidates": "|".join(who), "n_candidates": len(who),
                "headline": (d.get("headline") or {}).get("main"),
                "print_page": pd.to_numeric(page, errors="coerce"),
                "print_section": d.get("print_section"),
                "section": d.get("section_name"), "subsection": d.get("subsection_name"),
                "doc_type": d.get("document_type"), "material": d.get("type_of_material"),
                "word_count": d.get("word_count"), "url": d.get("web_url"),
                "race_term": bool(re.search(RACE_TERMS, text, re.I)),
            })
        print(f"{year}-{month:02d}: {len(docs):5d} articles, {hits:4d} mention a candidate", flush=True)
    df = pd.DataFrame(rows)
    df["front_page"] = (df.print_page == 1) & (df.print_section == "A")
    out = RAW / "nyt_mayoral_articles.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out}: {len(df)} articles, {int(df.front_page.sum())} on A1")
    print(df.groupby(["cycle", "candidates"]).size().sort_values(ascending=False).head(15).to_string())


if __name__ == "__main__":
    main()
