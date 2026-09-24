"""Democratic House primary turnout by district, from the FEC's biennial election-results compilation.

Why this rather than registration. The NYC enrollment result cannot be generalised to the insurgent
cases: twelve of the twenty-one are in states that do not register voters by party at all (Illinois,
Missouri, Texas, Michigan, Ohio), so "did Democratic registration grow" is undefined there rather
than merely unmeasured. Primary turnout exists in every state, and it is the direct analogue of the
cleaner half of the NYC finding -- the share of the party's electorate that actually voted.

Source. `fec.gov/documents/<id>/federalelections<year>.xlsx`, sheet "US House Results by State".
Document ids differ per year and are not derivable, so they are listed below; they were read off
each year's results page. The sheet interleaves candidate rows with two kinds of summary row, keyed
by the TOTAL VOTES column: "Party Votes:" gives a party's district primary total, and
"District Votes:" gives the all-party total. The Democratic primary turnout of a district is the
"Party Votes:" row with PARTY == "D".

Coverage. The FEC compilation is published after each general election, so 2024 and 2026 do not yet
exist: the five 2026 cases have neither a case-cycle nor a baseline figure here and are excluded.
The sixteen cases in 2018, 2020 and 2022 have both their own cycle and the preceding one.

Redistricting. A district number does not denote the same territory across a redistricting. The two
2022 cases are compared against 2020 across the 2020-cycle remap, so their ratios mix turnout change
with boundary change; they are flagged `crosses_redistricting` and should not be read as
like-for-like. The 2018-vs-2016 and 2020-vs-2018 comparisons are within one map.

"Unopposed" appears as a literal string where a primary was not contested, and is kept as missing
rather than zero -- an uncontested primary has no turnout to measure, which is different from
nobody voting.
"""

from pathlib import Path
import subprocess

import pandas as pd

RAW = Path("data/raw/fec_results")
DOCS = {2016: 1890, 2018: 2706, 2020: 4228, 2022: 5676}
SHEET_HINT = "House Results by State"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch(year):
    f = RAW / f"federalelections{year}.xlsx"
    if f.exists():
        return f
    url = f"https://www.fec.gov/documents/{DOCS[year]}/federalelections{year}.xlsx"
    subprocess.run(["curl", "-sS", "-L", "--max-time", "300", "-A", UA, "-o", str(f), url], check=True)
    if f.read_bytes()[:2] != b"PK":
        f.unlink(missing_ok=True)
        raise SystemExit(f"{year}: download did not return a workbook")
    return f


def house_sheet(year):
    x = pd.ExcelFile(fetch(year))
    names = [s for s in x.sheet_names if SHEET_HINT.lower() in s.lower()]
    if not names:
        raise SystemExit(f"{year}: no House results sheet in {x.sheet_names}")
    return pd.read_excel(x, sheet_name=names[0])


def dem_primary_by_district(year):
    d = house_sheet(year)
    d.columns = [str(c).strip() for c in d.columns]
    tot = d["TOTAL VOTES"].astype(str).str.strip().str.lower()
    party = d["PARTY"].astype(str).str.strip().str.upper()
    rows = d[(tot == "party votes:") & (party == "D")].copy()
    rows["state"] = rows["STATE ABBREVIATION"].astype(str).str.strip().str.upper()
    # The district column is "DISTRICT" from 2018 on but bare "D" in the 2016 workbook.
    dcol = next((c for c in ("DISTRICT", "D") if c in rows.columns), None)
    if dcol is None:
        raise SystemExit(f"{year}: no district column in {list(rows.columns)[:8]}")
    # districts arrive as "01", "1", or "00"/"AL" for at-large
    rows["district"] = pd.to_numeric(rows[dcol], errors="coerce")
    pv = rows["PRIMARY VOTES"]
    rows["dem_primary_votes"] = pd.to_numeric(pv, errors="coerce")
    rows["uncontested"] = pv.astype(str).str.strip().str.lower().eq("unopposed")
    rows["cycle"] = year
    out = rows[rows.district.notna()][["cycle", "state", "district", "dem_primary_votes", "uncontested"]]
    out["district"] = out.district.astype(int)
    return out.drop_duplicates(subset=["cycle", "state", "district"])


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    frames = []
    for y in sorted(DOCS):
        t = dem_primary_by_district(y)
        frames.append(t)
        print(f"  {y}: {len(t):3d} districts with a Democratic primary row; "
              f"{int(t.uncontested.sum())} uncontested; "
              f"median turnout {t.dem_primary_votes.median():,.0f}", flush=True)
    out = pd.concat(frames, ignore_index=True)
    f = RAW / "dem_house_primary_turnout.csv"
    out.to_csv(f, index=False)
    print(f"\nwrote {f}: {out.shape}")


if __name__ == "__main__":
    main()
