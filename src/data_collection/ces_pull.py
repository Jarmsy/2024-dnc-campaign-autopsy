"""Download Cooperative Election Study common content (2016, 2020, 2024) and harmonize core variables."""

from pathlib import Path
import re
import pandas as pd
import requests

DATAVERSE_API = "https://dataverse.harvard.edu/api"
HEADERS = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}

# https://dataverse.harvard.edu/dataverse/cces
DATASETS = {
    2016: {"doi": "doi:10.7910/DVN/GDF6Z0", "data_pattern": r"CCES16_Common_OUTPUT.*\.tab$", "sep": "\t"},
    2020: {"doi": "doi:10.7910/DVN/E9N6PH", "data_pattern": r"CES20_Common_OUTPUT.*\.csv$", "sep": ","},
    2024: {"doi": "doi:10.7910/DVN/X11EP6", "data_pattern": r"CCES24_Common_OUTPUT.*\.csv$", "sep": ","},
}

# harmonized name -> source column per year (None = not asked that year)
HARMONIZED = {
    "caseid":            {2016: "V101",                 2020: "caseid",           2024: "caseid"},
    "weight":            {2016: "commonweight",         2020: "commonweight",     2024: "commonweight"},
    "weight_post":       {2016: "commonweight_post",    2020: "commonpostweight", 2024: "commonpostweight"},
    "weight_vv":         {2016: "commonweight_vv",      2020: "vvweight",         2024: "vvweight"},
    "weight_vv_post":    {2016: "commonweight_vv_post", 2020: "vvweight_post",    2024: "vvweight_post"},
    "state_fips":        {2016: "inputstate",           2020: "inputstate",       2024: "inputstate"},
    "county_fips":       {2016: "countyfips",           2020: "countyfips",       2024: "countyfips"},
    "county_name":       {2016: "countyname",           2020: "countyname",       2024: "countyname"},
    "birthyr":           {2016: "birthyr",              2020: "birthyr",          2024: "birthyr"},
    "gender":            {2016: "gender",               2020: "gender",           2024: "gender4"},
    "educ":              {2016: "educ",                 2020: "educ",             2024: "educ"},
    "race":              {2016: "race",                 2020: "race",             2024: "race"},
    "hispanic":          {2016: "hispanic",             2020: "hispanic",         2024: "hispanic"},
    "faminc":            {2016: "faminc",               2020: "faminc_new",       2024: "faminc_new"},
    "pid3":              {2016: "pid3",                 2020: "pid3",             2024: "pid3"},
    "pid7":              {2016: "pid7",                 2020: "pid7",             2024: "pid7"},
    "votereg":           {2016: "votereg",              2020: "votereg",          2024: "votereg"},
    # Retrospective evaluations. Question numbers shifted in 2024 (verified against each year's guide):
    #   nation's economy past year: CC16_302 / CC20_302 / CC24_301   (1 much better .. 5 much worse, 6 not sure)
    #   household income:           CC16_303 / CC20_303 / CC24_302   (1 increased a lot .. 5 decreased a lot)
    #     NB 2016 asks about the past FOUR years; 2020 and 2024 ask about the past year
    #   prices past year:           CC24_303 only                    (1 increased a lot .. 5 decreased a lot)
    "econ_retro":        {2016: "CC16_302",             2020: "CC20_302",         2024: "CC24_301"},
    "hh_income_retro":   {2016: "CC16_303",             2020: "CC20_303",         2024: "CC24_302"},
    "prices_retro":      {2016: None,                   2020: None,               2024: "CC24_303"},
    # Presidential job approval (1 strongly approve .. 4 strongly disapprove, 5 not sure); not in 2024 common content
    "approve_president": {2016: "CC16_320a",            2020: "CC20_320a",        2024: None},
    # Post-election presidential vote (raw codes; candidate order differs by year - see PRES_CODES)
    "presvote_post":     {2016: "CC16_410a",            2020: "CC20_410",         2024: "CC24_410"},
    "presvote_prior":    {2016: None,                   2020: "presvote16post",   2024: "presvote20post"},
    "presvote_2016_recall": {2016: None,                2020: None,               2024: "presvote16post"},
}

# Candidate codes verified against the guides. 2016 lists Trump first; 2020 and 2024 list the Democrat first.
PRES_CODES = {
    "presvote_post":  {2016: {"D": 2, "R": 1}, 2020: {"D": 1, "R": 2}, 2024: {"D": 1, "R": 2}},
    "presvote_prior": {2020: {"D": 1, "R": 2}, 2024: {"D": 1, "R": 2}},
    "presvote_2016_recall": {2024: {"D": 1, "R": 2}},
}

# Passed through with the CCyy_ prefix dropped: media-use block (300*) and congressional district
PASSTHROUGH = [r"^CC\d\d_300", r"^cdid\d+$"]

output_dir = Path("data/raw/ces")
output_dir.mkdir(parents=True, exist_ok=True)


def list_files(doi):
    url = f"{DATAVERSE_API}/datasets/:persistentId/versions/:latest/files"
    r = requests.get(url, params={"persistentId": doi}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return [f["dataFile"] for f in r.json()["data"]]


def download(file_id, dest):
    if dest.exists():
        print(f"  Found cached {dest.name}")
        return dest
    url = f"{DATAVERSE_API}/access/datafile/{file_id}"
    print(f"  Downloading {dest.name} ...", end=" ", flush=True)
    r = requests.get(url, headers=HEADERS, stream=True, timeout=900)
    r.raise_for_status()
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    print(f"OK ({dest.stat().st_size / 1e6:.0f} MB)")
    return dest


def fetch_year(year, cfg):
    files = list_files(cfg["doi"])
    data = next(f for f in files if re.search(cfg["data_pattern"], f["filename"]))
    data_path = download(data["id"], output_dir / data["filename"])

    for f in files:
        if re.search(r"guide", f["filename"], re.I) and f["filename"].lower().endswith(".pdf"):
            download(f["id"], output_dir / f["filename"])
    return data_path


def harmonize(year, cfg, data_path):
    print(f"  Reading {data_path.name} ...", end=" ", flush=True)
    header = pd.read_csv(data_path, sep=cfg["sep"], nrows=0).columns.tolist()

    rename = {}
    for new, per_year in HARMONIZED.items():
        src = per_year.get(year)
        if src is None:
            continue
        if src not in header:
            print(f"\n  WARNING: {src} not in {year} file; {new} will be missing")
            continue
        rename[src] = new
    prefix = re.compile(rf"^CC{str(year)[2:]}_")
    for col in header:
        if col in rename:
            continue
        if any(re.search(p, col) for p in PASSTHROUGH):
            rename[col] = "q" + prefix.sub("", col) if prefix.match(col) else col

    df = pd.read_csv(data_path, sep=cfg["sep"], usecols=list(rename), low_memory=False)
    df = df.rename(columns=rename)
    df.insert(0, "year", year)

    for new in HARMONIZED:
        if new not in df.columns:
            df[new] = pd.NA
    for col in df.columns:
        if col not in ("county_name",):
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["county_fips"] = df["county_fips"].astype("Int64")

    # Party-coded vote columns so the year-specific candidate order never reaches the analysis
    for var, codes in PRES_CODES.items():
        if year in codes:
            party = pd.Series(pd.NA, index=df.index, dtype="object")
            party[df[var] == codes[year]["D"]] = "D"
            party[df[var] == codes[year]["R"]] = "R"
            party[df[var].notna() & party.isna()] = "other"
            df[f"{var}_party"] = party
        else:
            df[f"{var}_party"] = pd.NA

    print(f"OK ({len(df):,} respondents, {df.shape[1]} columns)")
    return df


def main():
    print("=" * 60)
    print("Cooperative Election Study Common Content")
    print("=" * 60)

    frames = []
    for year, cfg in DATASETS.items():
        print(f"\n{year}  ({cfg['doi']})")
        data_path = fetch_year(year, cfg)
        df = harmonize(year, cfg, data_path)
        df.to_csv(output_dir / f"ces_{year}.csv", index=False)
        frames.append(df)

    core = ["year"] + list(HARMONIZED) + [f"{v}_party" for v in PRES_CODES]
    stacked = pd.concat([f[core] for f in frames], ignore_index=True)
    stacked_path = output_dir / "ces_2016_2024_core.csv"
    stacked.to_csv(stacked_path, index=False)

    print("\n" + "=" * 60)
    print(f"Saved per-year files: data/raw/ces/ces_{{2016,2020,2024}}.csv (core + media block + cdid)")
    print(f"Saved stacked core:   {stacked_path}")
    print()
    for year, df in zip(DATASETS, frames):
        has_cty = df["county_fips"].notna().mean()
        voted = df[df["presvote_post_party"].isin(["D", "R"])]
        w = voted["weight_post"].fillna(voted["weight"])
        dem_2p = w[voted["presvote_post_party"] == "D"].sum() / w.sum()
        print(f"  {year}: N={len(df):>6,}  county FIPS present {has_cty:.1%}  "
              f"counties {df['county_fips'].nunique():,}  "
              f"weighted two-party Dem {dem_2p:.1%}")
    print()
    print("Retrospective and approval items are numeric codes (see HARMONIZED comments for scales).")
    print("Media block (q300*) item order and cable-channel order (q300b_*) differ by year - check each guide.")
    print("=" * 60)


if __name__ == "__main__":
    main()
