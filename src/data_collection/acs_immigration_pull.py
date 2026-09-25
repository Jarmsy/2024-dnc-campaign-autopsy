"""Non-citizen and Hispanic shares for New Jersey municipalities and Virginia localities (ACS 5-year).

Why. The test of whether the November 2025 swing-back was a backlash to immigration enforcement needs a
measure of local exposure. ICE's own arrest records cannot supply one at town level (see
`superpac`-era notes in the appendix: arrests are coded to field offices and county jails), so exposure is
proxied by who is personally at risk -- the non-citizen share of residents.

Variables: B05001_001E total, B05001_006E not a U.S. citizen (citizenship status); B03003_001E/_003E total and
Hispanic or Latino; B19013_001E median household income. NJ at county subdivision (= municipality), VA at
county (independent cities are counties). The newest 5-year release the API serves is used.

Names are matched to `same_day_2025_pull.py`'s municipality keys with its own normaliser; NJ municipalities
are matched within county so same-named towns in different counties stay apart.

Output: `data/raw/same_day_2025/acs_nj_municipalities.csv`, `acs_nj_matched.csv` (one row per election
municipality), `acs_va_localities.csv`.
"""

import os
from pathlib import Path
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from same_day_2025_pull import _norm, NJ_COUNTIES  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OUT = Path("data/raw/same_day_2025")
VARS = "NAME,B05001_001E,B05001_006E,B03003_001E,B03003_003E,B19013_001E"


def get(geo, state):
    key = os.getenv("CENSUS_API_KEY")
    for yr in (2024, 2023):
        r = requests.get(f"https://api.census.gov/data/{yr}/acs/acs5", timeout=120,
                         params={"get": VARS, "for": geo, "in": f"state:{state}", "key": key})
        if r.status_code == 200:
            j = r.json()
            d = pd.DataFrame(j[1:], columns=j[0]); d["acs_year"] = yr
            for c in VARS.split(",")[1:]:
                d[c] = pd.to_numeric(d[c], errors="coerce")
            d["noncitizen_share"] = d.B05001_006E / d.B05001_001E
            d["hispanic_share"] = d.B03003_003E / d.B03003_001E
            d["med_income"] = d.B19013_001E.where(d.B19013_001E > 0)
            return d
    raise SystemExit(f"ACS request failed: {r.status_code}")   # never print the URL: it carries the key


def _bare(key):
    """Key with municipal-type words removed ("jerseycitycity" -> "jersey", "cityoforangetwp" -> "orange")."""
    import re
    k = re.sub(r"^cityof", "", key)
    for _ in range(2):
        k = re.sub(r"(city|twp|boro|town|village)$", "", k)
    return k


def match_nj(elect, acs):
    """Election municipality key -> ACS row: exact key within county, then the bare name if unique on both sides."""
    out = {}
    for county, e in elect.groupby("county"):
        a = acs[acs.county == county]
        for k in e.key:
            hit = a[a.key == k]
            if len(hit) != 1:
                b = a[a.key.map(_bare) == _bare(k)]
                hit = b if len(b) == 1 and (e.key.map(_bare) == _bare(k)).sum() == 1 else hit.iloc[0:0]
            if len(hit) == 1:
                out[(county, k)] = hit.index[0]
    return out


def main():
    nj = get("county subdivision:*", "34")
    parts = nj.NAME.str.split(", ", expand=True)
    nj["key"] = parts[0].map(_norm)
    nj["county"] = parts[1].str.replace(" County", "", regex=False).str.lower().str.replace(" ", "")
    nj = nj[nj.B05001_001E > 0]
    nj.to_csv(OUT / "acs_nj_municipalities.csv", index=False)
    va = get("county:*", "51")
    va["locality"] = va.NAME.str.replace(", Virginia", "", regex=False)
    va.to_csv(OUT / "acs_va_localities.csv", index=False)
    m = pd.read_csv(OUT / "nj_municipalities.csv")
    mp = match_nj(m, nj)
    m["acs_row"] = [mp.get((c, k)) for c, k in zip(m.county, m.key)]
    cols = ["noncitizen_share", "hispanic_share", "med_income", "B05001_001E"]
    m = m.join(nj[cols], on="acs_row")
    m[["county", "key"] + cols].to_csv(OUT / "acs_nj_matched.csv", index=False)
    print(f"ACS {nj.acs_year.iloc[0]}: {m.acs_row.notna().sum()} of {len(m)} election municipalities matched; "
          f"VA {len(va)} localities")
    print("  unmatched:", m[m.acs_row.isna()][["county", "key"]].values.tolist())


if __name__ == "__main__":
    main()
