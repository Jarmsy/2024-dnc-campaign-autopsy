"""Download BLS QCEW county-level private employment by NAICS sector (annual averages)."""

from pathlib import Path
import zipfile
import pandas as pd
import requests

# Annual single-file archives: https://www.bls.gov/cew/downloadable-data-files.htm
QCEW_URL = "https://data.bls.gov/cew/data/files/{year}/csv/{year}_annual_singlefile.zip"
YEARS = [2012, 2016, 2020, 2024]

# agglvl 71 = county x ownership (industry "10" = all industries)
# agglvl 74 = county x NAICS sector x ownership ("31-33" = manufacturing, etc.)
COUNTY_AGGLVLS = {71, 74}
PRIVATE_OWN_CODE = 5

USECOLS = [
    "area_fips", "own_code", "industry_code", "agglvl_code", "year",
    "disclosure_code", "annual_avg_estabs", "annual_avg_emplvl",
    "total_annual_wages", "avg_annual_pay",
]

output_dir = Path("data/raw/bls_qcew")
output_dir.mkdir(parents=True, exist_ok=True)


def download_zip(year):
    """Fetch the annual single-file zip for one year, caching it locally."""
    zip_path = output_dir / f"{year}_annual_singlefile.zip"
    if zip_path.exists():
        print(f"  Found cached {zip_path.name}")
        return zip_path

    url = QCEW_URL.format(year=year)
    print(f"  Downloading {year} ...", end=" ", flush=True)
    r = requests.get(url, headers={"User-Agent": "dnc-autopsy/0.1"}, stream=True, timeout=600)
    if r.status_code == 404:
        print("ERR (404 - annual file not published yet)")
        return None
    r.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1 << 20):
            f.write(chunk)
    print(f"OK ({zip_path.stat().st_size / 1e6:.0f} MB)")
    return zip_path


def parse_county_sectors(zip_path):
    """Stream the ~3.5M-row single file, keeping only county x private-sector rows."""
    print(f"  Parsing {zip_path.name} ...", end=" ", flush=True)
    keep = []
    with zipfile.ZipFile(zip_path) as z:
        member = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(member) as f:
            reader = pd.read_csv(
                f, usecols=USECOLS, chunksize=500_000,
                dtype={"area_fips": str, "industry_code": str, "disclosure_code": str},
            )
            for chunk in reader:
                mask = chunk["agglvl_code"].isin(COUNTY_AGGLVLS) & (chunk["own_code"] == PRIVATE_OWN_CODE)
                keep.append(chunk[mask])

    df = pd.concat(keep, ignore_index=True)

    # Drop non-county areas (US000, statewide, MSAs) and "unknown county" 999 codes
    df = df[df["area_fips"].str.fullmatch(r"\d{5}") & ~df["area_fips"].str.endswith("999")].copy()
    df["county_fips"] = df["area_fips"].astype(int)

    # disclosure_code "N" = suppressed; BLS reports 0 in the value columns, which is not a real zero
    suppressed = df["disclosure_code"].fillna("").str.strip() == "N"
    for col in ["annual_avg_estabs", "annual_avg_emplvl", "total_annual_wages", "avg_annual_pay"]:
        df.loc[suppressed, col] = pd.NA

    df = df.rename(columns={
        "annual_avg_estabs": "estabs",
        "annual_avg_emplvl": "emplvl",
        "total_annual_wages": "total_wages",
    })[["year", "county_fips", "industry_code", "estabs", "emplvl", "total_wages", "avg_annual_pay"]]

    print(f"OK ({len(df):,} county-sector rows, {df['county_fips'].nunique():,} counties)")
    return df


def build_summary(long_df):
    """One row per county: private employment, manufacturing employment/share, avg pay, by year."""
    total = long_df[long_df["industry_code"] == "10"].set_index(["county_fips", "year"])
    mfg = long_df[long_df["industry_code"] == "31-33"].set_index(["county_fips", "year"])

    summary = pd.DataFrame({
        "private_emp": total["emplvl"],
        "private_avg_pay": total["avg_annual_pay"],
        "mfg_emp": mfg["emplvl"],
    })
    summary["mfg_share"] = summary["mfg_emp"] / summary["private_emp"]

    wide = summary.unstack("year")
    wide.columns = [f"{var}_{yr}" for var, yr in wide.columns]
    return wide.reset_index()


def main():
    print("=" * 60)
    print("BLS QCEW County Private Employment by NAICS Sector")
    print("=" * 60)

    frames = []
    for year in YEARS:
        print(f"\n{year}")
        zip_path = download_zip(year)
        if zip_path is None:
            continue
        frames.append(parse_county_sectors(zip_path))

    if not frames:
        print("\nNo data pulled.")
        return

    long_df = pd.concat(frames, ignore_index=True).sort_values(["year", "county_fips", "industry_code"])
    long_path = output_dir / "qcew_county_sectors.csv"
    long_df.to_csv(long_path, index=False)
    print(f"\nSaved to {long_path}")

    summary = build_summary(long_df)
    summary_path = output_dir / "qcew_county_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"Saved to {summary_path}")

    print("\n" + "=" * 60)
    print("National manufacturing share of private employment (sanity check):")
    for year in sorted(long_df["year"].unique()):
        sub = long_df[long_df["year"] == year]
        mfg = sub.loc[sub["industry_code"] == "31-33", "emplvl"].sum()
        tot = sub.loc[sub["industry_code"] == "10", "emplvl"].sum()
        print(f"  {year}: {mfg / tot:.1%}  ({tot / 1e6:.1f}M private jobs)")
    print("Note: avg_annual_pay is nominal - deflate with CPIAUCSL in the notebook.")
    print("=" * 60)


if __name__ == "__main__":
    main()
