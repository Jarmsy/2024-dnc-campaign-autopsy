"""ACS 2016-2020 five-year place characteristics for pre-registration addendum 3 and Test A's secondary tests.

Michigan county subdivisions (cities and townships) and Ohio, Wisconsin and Pennsylvania counties:
total population (B01003), bachelor's degree or higher among adults 25+ (B15003_022-025 / _001),
median household income (B19013), White non-Hispanic share (B03002_003 / _001). Census API; needs
CENSUS_API_KEY. Writes data/raw/validation/acs_place_controls_{mi_cousub,counties}.csv.

Added 4 November 2026 for Test A's secondary tests 3 and 4 (report/results_2026_analysis_plan.md, Phase 1
step 2). Same ACS vintage, Michigan county subdivisions only, written to a separate file so the file the
validation used is not rewritten (`--extra` pulls only this one):
  - arab_share: people reporting an Arab ancestry (B04006_006, the table's "Arab" subtotal) / total population
    (B01003_001). Assyrian/Chaldean/Syriac (B04006_017) is a separate ACS category and is not included.
  - age18_34: residents aged 18-34 as a share of residents 18 and over, built as nyc_pull._age_shares builds
    it from nyc_pull._AGE_BANDS: B01001 male lines 007-012 plus female lines 031-036, over B01001_001 less
    the under-18 lines 003-006 and 027-030.
Writes data/raw/validation/acs_mi_cousub_ancestry_age.csv.

mi_match() attaches any of these characteristics to Michigan municipalities as michigan_pull writes them,
with the fixes the validation results promised before the 2026 run. `--check` prints the match before and
after the fixes for the 2008-2018 and 2020-2024 municipal files.
"""
import argparse
import os
from pathlib import Path
import sys

import pandas as pd
import requests

OUT = Path("data/raw/validation")
VARS = ["NAME", "B01003_001E", "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E",
        "B19013_001E", "B03002_001E", "B03002_003E"]
# nyc_pull._AGE_BANDS: B01001 male line numbers; the female line is the male line + 24
UNDER18, AGE18_34 = [3, 4, 5, 6], [7, 8, 9, 10, 11, 12]
EXTRA = (["NAME", "B01003_001E", "B04006_001E", "B04006_006E", "B01001_001E"]
         + [f"B01001_{c:03d}E" for band in (UNDER18, AGE18_34) for m in band for c in (m, m + 24)])
EXTRA_FILE = OUT / "acs_mi_cousub_ancestry_age.csv"


def key():
    k = os.environ.get("CENSUS_API_KEY")
    if not k and Path(".env").exists():
        for line in Path(".env").read_text().splitlines():
            if line.startswith("CENSUS_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"')
    return k


def get_vars(vars_, geo_for, geo_in):
    r = requests.get("https://api.census.gov/data/2020/acs/acs5",
                     params={"get": ",".join(vars_), "for": geo_for, "in": geo_in, "key": key()}, timeout=120)
    if r.status_code != 200:                                   # the request URL carries the key; never show it
        sys.exit(f"Census API returned {r.status_code} for {geo_for} in {geo_in}")
    rows = r.json()
    d = pd.DataFrame(rows[1:], columns=rows[0])
    for v in vars_[1:]:
        d[v] = pd.to_numeric(d[v], errors="coerce")
    return d


def get(geo_for, geo_in):
    d = get_vars(VARS, geo_for, geo_in)
    d.loc[d.B19013_001E < 0, "B19013_001E"] = pd.NA          # Census missing-value sentinels are negative
    d["pop"] = d.B01003_001E
    d["ba_share"] = d[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1) / d.B15003_001E
    d["median_income"] = d.B19013_001E
    d["white_nh_share"] = d.B03002_003E / d.B03002_001E
    return d


def get_mi_extra():
    d = get_vars(EXTRA, "county subdivision:*", "state:26 county:*")
    if (d[EXTRA[1:]] < 0).any().any():
        sys.exit("negative count in the ACS extract (a missing-value sentinel); inspect before using")
    n = lambda lines: sum(d[f"B01001_{c:03d}E"] + d[f"B01001_{c + 24:03d}E"] for c in lines)
    d["adults"] = (d.B01001_001E - n(UNDER18)).where(d.B01001_001E > 0)
    d["age18_34"] = (n(AGE18_34) / d.adults).where(d.adults > 0)
    d["arab_share"] = (d.B04006_006E / d.B01003_001E).where(d.B01003_001E > 0)
    return d


# ---------------------------------------------------------------- matching to Michigan municipalities

def _mp():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import michigan_pull
    return michigan_pull


def _county(s, fixes=True):
    """County key: dots and a possessive dropped, as notebook 29 did. With the fixes, the 2008-2018
    OpenElections files' 'Gd Traverse' is written out as 'Grand Traverse'."""
    s = s.str.replace(".", "", regex=False).str.replace(r"(?i)'s$", "", regex=True).str.strip()
    return s.str.replace(r"^Gd ", "Grand ", regex=True) if fixes else s


def mi_acs_keys(acs, fixes=True):
    """County and municipality keys for the ACS county subdivisions, in michigan_pull's spelling."""
    mp = _mp()
    a = acs.copy()
    a["county_n"] = a.NAME.str.split(", ").str[1].str.replace(" County", "", regex=False).str.replace(".", "", regex=False).str.strip()
    a["muni"] = a.NAME.str.split(", ").str[0].map(mp.municipality)
    if fixes:
        # The election files name a city 'City of Bay City' (or 'Bay City'), which michigan_pull.municipality
        # reduces to 'bay city': both 'city of' and the trailing 'city' go. The Census name 'Bay City city'
        # keeps the place's own 'City' ('bay city city'). Thirteen Michigan cities are named 'X City'
        # (fifteen county parts: Brown City and Traverse City each span two counties).
        a["muni"] = a.muni.str.replace(r"^(.+) city city$", r"\1 city", regex=True)
    return a


def mi_match(m, acs, cols, fixes=True):
    """Attach ACS columns `cols` to municipalities `m` (columns `county`, `muni`, as michigan_pull writes them).

    fixes=False reproduces notebook 29's match, which the validation results report (1,498 of 1,523
    municipalities): county + name and type, then county + bare name where the ACS key is unique.
    fixes=True (the 2026 run) adds what the validation results promised and one more pass:
      - 'Gd Traverse' read as Grand Traverse (Traverse City, Garfield and East Bay townships, ...);
      - the 'X City' cities spelt alike on both sides (Bay City, Garden City, Traverse City and 10 smaller).
        This also corrects five cities that notebook 29's bare-name pass had given their namesake township's
        values (Tawas City, Imlay City, Lake City, Rose City, Rogers City); --check lists them;
      - michigan_pull.match's middle pass, bare name + township-or-not, which places DeWitt city and DeWitt
        township (Clinton County; 'de witt' in the election files), whose bare names collide without the type;
      - every pass requires its key to be unique on both sides, and an ACS row matched in one pass is not
        offered to the next, so no ACS row is given to two municipalities.
    Returns a copy of m with `cols` and `acs_match` (the pass that matched, or NaN).
    """
    mp = _mp()
    a = mi_acs_keys(acs, fixes)
    a = a[a.B01003_001E > 0].copy()
    x = m.copy().reset_index(drop=True)
    x["county_n"] = _county(x.county, fixes)
    for c in cols:
        x[c] = float("nan")
    x["acs_match"] = None
    if not fixes:                                              # notebook 29, verbatim in effect
        e = x[["county_n", "muni"]].merge(a[["county_n", "muni"] + cols], on=["county_n", "muni"], how="left")
        if len(e) != len(x):
            sys.exit("duplicate ACS keys in the exact pass")
        x[cols] = e[cols].values
        x.loc[x[cols[0]].notna(), "acs_match"] = "exact"
        miss = x[cols[0]].isna().values
        a["bare"] = a.muni.map(lambda s: mp._bare(s, False)); x["bare"] = x.muni.map(lambda s: mp._bare(s, False))
        a_u = a[~a.duplicated(["county_n", "bare"], keep=False)]
        f = x.loc[miss, ["county_n", "bare"]].merge(a_u[["county_n", "bare"] + cols], on=["county_n", "bare"], how="left")
        x.loc[miss, cols] = f[cols].values
        x.loc[miss & x[cols[0]].notna().values, "acs_match"] = "bare"
        return x.drop(columns=["bare"])
    a["k_exact"], x["k_exact"] = a.muni, x.muni
    a["k_bare_kind"], x["k_bare_kind"] = a.muni.map(lambda s: mp._bare(s, True)), x.muni.map(lambda s: mp._bare(s, True))
    a["k_bare"], x["k_bare"] = a.muni.map(lambda s: mp._bare(s, False)), x.muni.map(lambda s: mp._bare(s, False))
    a["_aid"] = range(len(a))
    for k in ("k_exact", "k_bare_kind", "k_bare"):
        todo = x[x.acs_match.isna()]
        ux = todo[~todo.duplicated(["county_n", k], keep=False)]
        ua = a[~a.duplicated(["county_n", k], keep=False)]
        j = ux[["county_n", k]].reset_index().merge(ua[["county_n", k, "_aid"] + cols], on=["county_n", k], how="inner").set_index("index")
        x.loc[j.index, cols] = j[cols].values
        x.loc[j.index, "acs_match"] = k[2:]
        a = a[~a._aid.isin(j._aid)]                            # a matched ACS row is not offered again
    assert x.acs_match.notna().sum() == len(set(zip(x.county_n[x.acs_match.notna()], x.muni[x.acs_match.notna()])))
    return x.drop(columns=["k_exact", "k_bare_kind", "k_bare"])


def check():
    """Coverage before and after the fixes, on the municipal files Test A's notebooks use."""
    acs = pd.read_csv(OUT / "acs_place_controls_mi_cousub.csv")
    for f in ("mi_municipal_validation_2008_2018.csv", "mi_municipal_2020_2024.csv"):
        m = pd.read_csv(Path("data/raw/michigan") / f)
        w = next(c for c in ("gov_D_2018", "pres_D_2024") if c in m)
        w2 = w.replace("_D_", "_R_")
        votes = m[w] + m[w2]
        old, new = mi_match(m, acs, ["pop"], fixes=False), mi_match(m, acs, ["pop"], fixes=True)
        print(f"\n{f} ({len(m)} municipalities; votes = {w} + {w2})")
        for lab, r in (("validation match", old), ("fixed match", new)):
            ok = r["pop"].notna()
            print(f"  {lab:16}: {int(ok.sum())} matched, {votes[ok].sum() / votes.sum():.2%} of votes; "
                  f"by pass {r.acs_match.value_counts().to_dict()}")
        gained = new["pop"].notna() & old["pop"].isna()
        lost = old["pop"].notna() & new["pop"].isna()
        changed = old["pop"].notna() & new["pop"].notna() & (old["pop"] != new["pop"])
        show = lambda mask: [(c, mu, int(v)) for c, mu, v in
                             zip(m.county[mask], m.muni[mask], votes[mask])]
        print(f"  gained {int(gained.sum())}: {sorted(show(gained), key=lambda t: -t[2])}")
        print(f"  lost {int(lost.sum())}: {show(lost)} | matched to a different place: {int(changed.sum())} {show(changed)}")
        print(f"  still unmatched {int(new['pop'].isna().sum())}: {sorted(show(new['pop'].isna()), key=lambda t: -t[2])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra", action="store_true", help="pull only the ancestry and age file")
    ap.add_argument("--check", action="store_true", help="print the match before and after the fixes")
    args = ap.parse_args()
    if args.check:
        return check()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.extra:
        mi = get("county subdivision:*", "state:26 county:*")
        mi.to_csv(OUT / "acs_place_controls_mi_cousub.csv", index=False)
        print("MI county subdivisions:", len(mi), "population", int(mi["pop"].sum()))
        parts = [get("county:*", f"state:{s}") for s in ("39", "55", "42")]
        c = pd.concat(parts, ignore_index=True)
        c.to_csv(OUT / "acs_place_controls_counties.csv", index=False)
        print("counties:", c.groupby("state").size().to_dict())
    x = get_mi_extra()
    x.to_csv(EXTRA_FILE, index=False)
    print(f"MI ancestry and age: {len(x)} county subdivisions; population {int(x.B01003_001E.sum()):,}; "
          f"Arab ancestry {int(x.B04006_006E.sum()):,} ({x.B04006_006E.sum() / x.B01003_001E.sum():.2%}); "
          f"18-34 share of adults {(x.age18_34 * x.adults).sum() / x.adults.sum():.2%}")


if __name__ == "__main__":
    main()
