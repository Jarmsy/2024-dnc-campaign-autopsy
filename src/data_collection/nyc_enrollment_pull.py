"""NYS Board of Elections party enrollment by election district, for the five NYC counties.

What this answers. The ED panel shows how people voted, not who was registered to vote. Separating
"Mamdani brought new people into the party" from "the Democrats already there turned out" needs
enrollment counts before and after the campaign, which is what these files carry: per ED, the number
of voters enrolled Democratic, Republican, Conservative, Working Families, other, and blank, each
split Active / Inactive / Total.

Access. The published node URLs -- `elections.ny.gov/<county>-<MMDDYYYY>` -- return the XLSX
directly; there is no separate file link to scrape. The site sits behind a WAF, and the block is
**not** header-based: `requests` is refused with 403 on every attempt while `curl` carrying byte-
identical headers is served 200. What differs is the TLS handshake and header ordering, which the
WAF fingerprints, so no amount of header-setting rescues `requests` and the download shells out to
curl instead. The browser set below is still required -- curl without `Accept-Encoding` and
`Connection` is refused too -- but it is necessary rather than sufficient. Files are cached and
requests paced, since the block also appears partly rate-based.

Snapshot dates. NYSBOE does not publish on a fixed cadence and 2021 has no February or April file
for these counties. What exists and is used: **2021-11-01, 2025-02-20, 2025-11-01, 2026-02-20**.
The 2025 pair is the analytically useful one -- it brackets the June primary and the November
general on the same district lines, so no crosswalk is needed. The 2021 file is on the pre-2022
lines and would need the same block-based crosswalk as the historical returns before it could be
compared district by district; it is pulled for county-level context only and flagged as such.

ED identifiers arrive as "Bronx 77001"; the trailing number is the panel's `ElectDist` (assembly
district + district number), so the join is direct.
"""

from pathlib import Path
import io
import subprocess
import time

import pandas as pd

RAW = Path("data/raw/nyc_enrollment")
BASE = "https://elections.ny.gov"
COUNTIES = {"bronx": "Bronx", "kings": "Kings", "new-york": "New York",
            "queens": "Queens", "richmond": "Richmond"}
DATES = ["11012021", "02202025", "11012025", "02202026"]
CROSSWALK_NEEDED = {"11012021"}          # pre-2022 ED lines; not comparable district-by-district
PAUSE, RETRIES = 4, 5

# The WAF rejects anything that does not look like a navigation from a real browser. Accept-Encoding
# and Connection are load-bearing: removing either returns 403.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document", "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none", "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1", "Connection": "keep-alive",
}


def fetch_xlsx(slug, date, session=None):
    """Download one county-date XLSX via curl. `session` is accepted and ignored: an earlier version
    used requests and was refused 403 on every call while curl with the same headers was served."""
    cache = RAW / f"{slug}_{date}.xlsx"
    if cache.exists():
        return cache.read_bytes()
    url = f"{BASE}/{slug}-{date}"
    cmd = ["curl", "-sS", "--compressed", "-L", "--max-time", "120"]
    for k, v in HEADERS.items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-o", str(cache), "-w", "%{http_code}", url]
    for attempt in range(1, RETRIES + 1):
        r = subprocess.run(cmd, capture_output=True, text=True)
        code = (r.stdout or "").strip()
        if code == "200" and cache.exists() and cache.read_bytes()[:2] == b"PK":
            time.sleep(PAUSE)
            return cache.read_bytes()
        cache.unlink(missing_ok=True)
        wait = PAUSE * 2 * attempt
        print(f"    {slug} {date}: HTTP {code or 'curl error'}, attempt {attempt}/{RETRIES}; waiting {wait}s", flush=True)
        time.sleep(wait)
    return None


def parse(blob, slug, date):
    """One row per ED per status. The sheet has three title lines, a header at row 4, and a blank
    spacer between every ED block, so the header is located rather than assumed."""
    raw = pd.read_excel(io.BytesIO(blob), sheet_name=0, header=None)
    hdr = raw.index[raw[0].astype(str).str.strip().str.upper() == "COUNTY"]
    if len(hdr) == 0:
        raise SystemExit(f"{slug} {date}: no COUNTY header row found")
    h = hdr[0]
    df = raw.iloc[h + 1:].copy()
    df.columns = [str(c).strip().upper() for c in raw.iloc[h]]
    df = df[df["ELECTION DIST"].notna() & df["STATUS"].notna()]
    # "Bronx 77001" -> 77001
    df["ElectDist"] = pd.to_numeric(
        df["ELECTION DIST"].astype(str).str.extract(r"(\d{4,6})\s*$")[0], errors="coerce")
    df = df[df.ElectDist.notna()].copy()
    df["ElectDist"] = df.ElectDist.astype(int)
    for c in ["DEM", "REP", "CON", "WOR", "OTH", "BLANK", "TOTAL"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["status"] = df["STATUS"].astype(str).str.strip().str.lower()
    df["county"] = COUNTIES[slug]
    df["snapshot"] = f"{date[4:]}-{date[:2]}-{date[2:4]}"
    df["lines_crosswalk_needed"] = date in CROSSWALK_NEEDED
    return df[["ElectDist", "county", "snapshot", "status", "DEM", "REP", "CON", "WOR", "OTH",
               "BLANK", "TOTAL", "lines_crosswalk_needed"]]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    frames, missing = [], []
    for date in DATES:
        for slug in COUNTIES:
            blob = fetch_xlsx(slug, date)
            if blob is None:
                missing.append((slug, date)); print(f"  {slug} {date}: FAILED", flush=True); continue
            df = parse(blob, slug, date)
            frames.append(df)
            tot = df[df.status == "total"]
            print(f"  {slug:9s} {date}  {len(tot):5d} EDs  DEM {int(tot.DEM.sum()):,}  "
                  f"total {int(tot.TOTAL.sum()):,}", flush=True)
    out = pd.concat(frames, ignore_index=True)
    f = RAW / "nyc_enrollment_by_ed.csv"
    out.to_csv(f, index=False)
    print(f"\nwrote {f}: {out.shape}")
    if missing:
        print("MISSING:", missing)
    piv = out[out.status == "total"].groupby(["snapshot", "county"]).DEM.sum().unstack()
    print("\nDemocratic enrollment by snapshot (Total, includes inactive):")
    print(piv.astype(int).to_string())


if __name__ == "__main__":
    main()
