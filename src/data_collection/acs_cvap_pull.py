"""County citizen voting-age population (CVAP), ACS, for sizing migration inside Part 7's "turnout" component.

Why. Part 2's decomposition and Part 7's stronghold figures measure turnout as raw votes cast. A county whose
eligible population shrank between 2020 and 2024 loses votes even if nobody who stayed abstained, and the
people who moved away vote somewhere else. CVAP change separates the two.

Variable: B29001_001E, citizen voting-age population (total). Two sources:
  - ACS 1-year, 2019, 2021 and 2024: counties of 65,000+ only. There is no standard 2020 1-year release, so the
    2020 baseline is the mean of 2019 and 2021.
  - ACS 5-year, 2016-2020 and 2020-2024: every county, but each is a five-year average, so the change runs
    between midpoints about four years apart and lags the 1-year figures. Used as a check.
Connecticut's 2022+ releases use planning regions instead of counties; its counties do not match after 2021.

Output: `data/raw/acs_cvap/county_cvap.csv` (one row per county, one column per release).
"""

import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OUT = Path("data/raw/acs_cvap")
RELEASES = [("acs1", 2019), ("acs1", 2021), ("acs1", 2024), ("acs5", 2020), ("acs5", 2024)]


def get(survey, year):
    r = requests.get(f"https://api.census.gov/data/{year}/acs/{survey}", timeout=120,
                     params={"get": "NAME,B29001_001E", "for": "county:*", "in": "state:*", "key": os.getenv("CENSUS_API_KEY")})
    if r.status_code != 200:
        raise SystemExit(f"ACS {survey} {year} request failed: {r.status_code}")   # never print the URL: it carries the key
    j = r.json()
    d = pd.DataFrame(j[1:], columns=j[0])
    d["county_fips"] = (d.state + d.county).astype(int)
    return d.set_index("county_fips")["B29001_001E"].astype(float).rename(f"cvap_{survey}_{year}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cvap = pd.concat([get(s, y) for s, y in RELEASES], axis=1)
    cvap["cvap_2020_1yr"] = cvap[["cvap_acs1_2019", "cvap_acs1_2021"]].mean(axis=1, skipna=False)
    cvap.index.name = "county_fips"
    cvap.to_csv(OUT / "county_cvap.csv")
    print(f"{len(cvap):,} counties; 1-year coverage (2019, 2021 and 2024 all present): "
          f"{cvap[['cvap_acs1_2019', 'cvap_acs1_2021', 'cvap_acs1_2024']].notna().all(axis=1).sum():,}")


if __name__ == "__main__":
    main()
