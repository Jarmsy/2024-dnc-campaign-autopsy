"""ACS 2016-2020 five-year place characteristics for pre-registration addendum 3.

Michigan county subdivisions (cities and townships) and Ohio, Wisconsin and Pennsylvania counties:
total population (B01003), bachelor's degree or higher among adults 25+ (B15003_022-025 / _001),
median household income (B19013), White non-Hispanic share (B03002_003 / _001). Census API; needs
CENSUS_API_KEY. Writes data/raw/validation/acs_place_controls_{mi_cousub,counties}.csv.
"""
import os
from pathlib import Path
import pandas as pd
import requests

OUT = Path("data/raw/validation")
VARS = ["NAME", "B01003_001E", "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E",
        "B19013_001E", "B03002_001E", "B03002_003E"]


def key():
    k = os.environ.get("CENSUS_API_KEY")
    if not k and Path(".env").exists():
        for line in Path(".env").read_text().splitlines():
            if line.startswith("CENSUS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"')
    return k


def get(geo_for, geo_in):
    r = requests.get("https://api.census.gov/data/2020/acs/acs5",
                     params={"get": ",".join(VARS), "for": geo_for, "in": geo_in, "key": key()}, timeout=120)
    r.raise_for_status()
    rows = r.json()
    d = pd.DataFrame(rows[1:], columns=rows[0])
    for v in VARS[1:]:
        d[v] = pd.to_numeric(d[v], errors="coerce")
    d.loc[d.B19013_001E < 0, "B19013_001E"] = pd.NA          # Census missing-value sentinels are negative
    d["pop"] = d.B01003_001E
    d["ba_share"] = d[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1) / d.B15003_001E
    d["median_income"] = d.B19013_001E
    d["white_nh_share"] = d.B03002_003E / d.B03002_001E
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mi = get("county subdivision:*", "state:26 county:*")
    mi.to_csv(OUT / "acs_place_controls_mi_cousub.csv", index=False)
    print("MI county subdivisions:", len(mi), "population", int(mi["pop"].sum()))
    parts = [get("county:*", f"state:{s}") for s in ("39", "55", "42")]
    c = pd.concat(parts, ignore_index=True)
    c.to_csv(OUT / "acs_place_controls_counties.csv", index=False)
    print("counties:", c.groupby("state").size().to_dict())


if __name__ == "__main__":
    main()
