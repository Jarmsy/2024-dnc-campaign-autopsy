"""Download the 2020-2022-2024 CES Panel Survey and harmonize it to long (respondent-wave) and wide formats."""

from pathlib import Path
import re
import pandas as pd
import requests

DATAVERSE_API = "https://dataverse.harvard.edu/api"
HEADERS = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
DOI = "doi:10.7910/DVN/CETPVT"   # 2020 - 2024 Cooperative Election Study Panel Survey
DATA_PATTERN = r"merged_recontact_2024_vv\.csv$"

WAVES = {2020: "20", 2022: "22", 2024: "24"}

# Question items keep their CCyy_ prefix; demographics carry a _yy suffix. Verified against
# Recontact_Survey_Guide_2020_2022_2024.pdf p.27 (economy items) and pp.59-60 (vote items).
# NB: in the panel the 2024 economy item is CC24_302, NOT CC24_301 as in the 2024 common content.
def per_wave(yy):
    return {
        "county_fips":       f"countyfips_{yy}",
        "county_name":       f"countyname_{yy}",
        "state_fips":        f"inputstate_{yy}",
        "pid7":              f"pid7_{yy}",
        "pid3":              f"pid3_{yy}",
        "educ":              f"educ_{yy}",
        "race":              f"race_{yy}",
        "hispanic":          f"hispanic_{yy}",
        "faminc":            f"faminc_new_{yy}",
        "birthyr":           f"birthyr_{yy}",
        "gender":            "gender" if yy == "20" else f"gender4_{yy}",
        "econ_retro":        f"CC{yy}_302",   # 1 much better .. 5 much worse, 6 not sure
        "hh_income_retro":   f"CC{yy}_303",   # 1 increased a lot .. 5 decreased a lot
        "prices_retro":      f"CC{yy}_304" if yy != "20" else None,   # 1 increased a lot .. 5 decreased a lot
        "approve_president": f"CC{yy}_320a",  # 1 strongly approve .. 4 strongly disapprove, 5 not sure
        "presvote_post":     {"20": "CC20_410", "22": None, "24": "CC24_410"}[yy],
        "presvote_prior":    {"20": "presvote16post_20", "22": "presvote20post_22", "24": "presvote20post_24"}[yy],
    }

# Candidate codes: Democrat first in every wave (guide pp.59-60; checked empirically in main()).
PRES_CODES = {
    "presvote_post":  {2020: {"D": 1, "R": 2}, 2024: {"D": 1, "R": 2}},
    "presvote_prior": {2020: {"D": 1, "R": 2}, 2022: {"D": 1, "R": 2}, 2024: {"D": 1, "R": 2}},
}

# Respondent-level (not per wave)
PANEL_ID = "caseid_20"
WEIGHTS = ["commonweight_24", "commonpostweight_24", "commonweight_22", "vvweight_22", "vvweight_post_22"]
VALIDATION = {2020: ("CL_2020gvm", "CL_voter_status_20"), 2022: ("TS_g2022", "TS_voterstatus_22"), 2024: ("TS_g2024", "TS_voterstatus_24")}

output_dir = Path("data/raw/ces_panel")
output_dir.mkdir(parents=True, exist_ok=True)


def download(file_id, dest):
    if dest.exists():
        print(f"  Found cached {dest.name}")
        return dest
    print(f"  Downloading {dest.name} ...", end=" ", flush=True)
    r = requests.get(f"{DATAVERSE_API}/access/datafile/{file_id}", headers=HEADERS, stream=True, timeout=900)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    print(f"OK ({dest.stat().st_size / 1e6:.0f} MB)")
    return dest


def fetch():
    r = requests.get(f"{DATAVERSE_API}/datasets/:persistentId/versions/:latest/files",
                     params={"persistentId": DOI}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    files = [f["dataFile"] for f in r.json()["data"]]
    data = next(f for f in files if re.search(DATA_PATTERN, f["filename"]))
    data_path = download(data["id"], output_dir / data["filename"])
    for f in files:
        if f["filename"].lower().endswith(".pdf"):
            download(f["id"], output_dir / f["filename"])
    return data_path


def validated_turnout(raw, year):
    """1 voted, 0 matched to a registration record but no vote, NaN not matched."""
    vote_col, status_col = VALIDATION[year]
    voted = raw[vote_col]
    matched = raw[status_col].notna() if status_col in raw.columns else voted.notna()
    out = pd.Series(pd.NA, index=raw.index, dtype="Float64")
    out[matched] = 0.0
    out[voted.notna() & (voted != 7)] = 1.0   # TS: 7 = did not vote; CL has no such code, any value = voted
    return out


def to_long(raw):
    frames = []
    for year, yy in WAVES.items():
        m = per_wave(yy)
        cols = {new: src for new, src in m.items() if src is not None and src in raw.columns}
        missing = [src for new, src in m.items() if src is not None and src not in raw.columns]
        if missing:
            print(f"  WARNING {year}: not in file: {missing}")
        df = raw[list(cols.values())].copy()
        df.columns = list(cols.keys())
        for new in m:
            if new not in df.columns:
                df[new] = pd.NA
        # Media block passthrough with the wave prefix stripped
        media = [c for c in raw.columns if re.match(rf"^CC{yy}_300", c)]
        for c in media:
            df["q" + c[len(f"CC{yy}_"):]] = raw[c]
        df.insert(0, "year", year)
        df.insert(0, "panel_id", raw[PANEL_ID])
        df["voted_validated"] = validated_turnout(raw, year)
        for var, codes in PRES_CODES.items():
            party = pd.Series(pd.NA, index=df.index, dtype="object")
            if year in codes and df[var].notna().any():
                party[df[var] == codes[year]["D"]] = "D"
                party[df[var] == codes[year]["R"]] = "R"
                party[df[var].notna() & party.isna()] = "other"
            df[f"{var}_party"] = party
        frames.append(df)
    long = pd.concat(frames, ignore_index=True)
    for c in long.columns:
        if c not in ("panel_id", "year", "county_name") and not c.endswith("_party"):
            long[c] = pd.to_numeric(long[c], errors="coerce")
    long["county_fips"] = long["county_fips"].astype("Int64")
    return long


def to_wide(raw, long):
    keep = ["county_fips", "state_fips", "pid7", "educ", "econ_retro", "hh_income_retro", "prices_retro",
            "approve_president", "presvote_post_party", "presvote_prior_party", "voted_validated",
            "q300_1", "q300_2", "q300_3", "q300_4", "q300_5", "q300b_4", "q300b_5", "q300b_6"]
    keep = [k for k in keep if k in long.columns]
    wide = long.pivot(index="panel_id", columns="year", values=keep)
    wide.columns = [f"{var}_{yr}" for var, yr in wide.columns]
    wide = wide.reset_index()
    resp = raw[[PANEL_ID] + [w for w in WEIGHTS if w in raw.columns] + ["birthyr_20", "race_20", "hispanic_20", "gender"]]
    resp = resp.rename(columns={PANEL_ID: "panel_id", "birthyr_20": "birthyr", "race_20": "race", "hispanic_20": "hispanic"})
    return wide.merge(resp, on="panel_id", how="left")


def main():
    print("=" * 60)
    print("CES 2020-2022-2024 Panel Survey")
    print("=" * 60)
    data_path = fetch()

    print("  Reading ...", end=" ", flush=True)
    raw = pd.read_csv(data_path, low_memory=False)
    print(f"OK ({len(raw):,} panelists, {raw.shape[1]:,} columns)")

    long = to_long(raw)
    wide = to_wide(raw, long)
    long.to_csv(output_dir / "ces_panel_long.csv", index=False)
    wide.to_csv(output_dir / "ces_panel_wide.csv", index=False)

    print("\n" + "=" * 60)
    print("Saved: data/raw/ces_panel/ces_panel_long.csv  (one row per respondent-wave)")
    print("Saved: data/raw/ces_panel/ces_panel_wide.csv  (one row per respondent)")
    print()
    w = wide["commonpostweight_24"].fillna(wide["commonweight_24"])
    for yr in (2020, 2024):
        v = wide[f"presvote_post_party_{yr}"]
        dem = w[v == "D"].sum() / w[v.isin(["D", "R"])].sum()
        print(f"  {yr} vote (reported that year): weighted two-party Dem {dem:.1%}   N answered {v.notna().sum():,}")
    both = wide[wide["presvote_post_party_2020"].isin(["D", "R"]) & wide["presvote_post_party_2024"].isin(["D", "R"])]
    dr = (both["presvote_post_party_2020"] == "D") & (both["presvote_post_party_2024"] == "R")
    rd = (both["presvote_post_party_2020"] == "R") & (both["presvote_post_party_2024"] == "D")
    print(f"  Major-party voters in both 2020 and 2024: {len(both):,}   D->R {dr.sum()}   R->D {rd.sum()}")
    for yr in WAVES:
        e = long.loc[long["year"] == yr, "econ_retro"]
        print(f"  {yr} economy item answered: {e.notna().sum():,}   county FIPS present: {long.loc[long['year'] == yr, 'county_fips'].notna().mean():.1%}")
    print()
    print("Weights: commonweight_24 for pre-election items, commonpostweight_24 for post-election items (guide p.10).")
    print("Attrition favors older, college-educated, retired, and validated voters; no partisan differential (guide p.11).")
    print("=" * 60)


if __name__ == "__main__":
    main()
