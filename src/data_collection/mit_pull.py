"""Download MIT Election Lab county-level presidential returns (2000-2020)."""

from pathlib import Path
import pandas as pd
import requests
import io

# MIT Election Lab dataset on Harvard Dataverse
# https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
DATASET_DOI = "doi:10.7910/DVN/VOQCHQ"
DATAVERSE_API = "https://dataverse.harvard.edu/api"

output_dir = Path("data/raw/mit_election_lab")
output_dir.mkdir(parents=True, exist_ok=True)


def get_csv_file_id(dataset_doi):
    """Query Dataverse API to find the county returns CSV file ID."""
    url = f"{DATAVERSE_API}/datasets/:persistentId/versions/:latest/files"
    response = requests.get(url, params={"persistentId": dataset_doi}, timeout=30)
    response.raise_for_status()

    files = response.json()["data"]
    for f in files:
        filename = f["dataFile"]["filename"]
        if "countypres" in filename.lower() and filename.endswith((".csv", ".tab")):
            file_id = f["dataFile"]["id"]
            print(f"Found: {filename} (id={file_id})")
            return file_id

    # Fallback: list all files so the user can pick
    print("Available files in dataset:")
    for f in files:
        print(f"  {f['dataFile']['id']}  {f['dataFile']['filename']}")
    raise ValueError("Could not find a countypres CSV in the dataset.")


def download_file(file_id):
    """Download a file from Harvard Dataverse by file ID."""
    url = f"{DATAVERSE_API}/access/datafile/{file_id}"
    print(f"Downloading file id={file_id}...", end=" ", flush=True)
    # gbrecs=true bypasses the Dataverse guestbook prompt
    response = requests.get(url, params={"gbrecs": "true"}, timeout=120)
    response.raise_for_status()
    print("OK")
    return response.content


def parse_and_clean(data_bytes):
    """Parse raw CSV and return clean county-year DataFrame."""
    print("Parsing and cleaning...", end=" ", flush=True)

    # .tab files are tab-separated; .csv files use comma
    sep = "\t" if data_bytes[:200].count(b"\t") > data_bytes[:200].count(b",") else ","
    df = pd.read_csv(io.BytesIO(data_bytes), sep=sep)

    # Filter to presidential elections and TOTAL mode only
    # (dataset includes per-mode sub-rows alongside TOTAL; summing all would double-count)
    df = df[df["office"] == "US PRESIDENT"].copy()
    if "mode" in df.columns:
        df = df[df["mode"] == "TOTAL"]

    # Normalize party column (varies by version: 'DEMOCRAT'/'REPUBLICAN' or lower)
    df["party"] = df["party"].str.upper().str.strip()

    dem = (
        df[df["party"] == "DEMOCRAT"][
            ["year", "state", "county_fips", "candidatevotes", "totalvotes"]
        ]
        .copy()
        .rename(columns={"candidatevotes": "dem_votes", "totalvotes": "total_votes"})
    )

    rep = (
        df[df["party"] == "REPUBLICAN"][
            ["year", "state", "county_fips", "candidatevotes"]
        ]
        .copy()
        .rename(columns={"candidatevotes": "rep_votes"})
    )

    result = dem.merge(rep, on=["year", "state", "county_fips"], how="outer")
    result["dem_votes"] = result["dem_votes"].fillna(0).astype(int)
    result["rep_votes"] = result["rep_votes"].fillna(0).astype(int)
    result["total_votes"] = result["total_votes"].fillna(0).astype(int)

    result["dem_share"] = result["dem_votes"] / result["total_votes"]
    result["rep_share"] = result["rep_votes"] / result["total_votes"]
    result["dem_margin"] = result["dem_share"] - result["rep_share"]
    result = result.fillna(0)

    result = result[
        [
            "year", "state", "county_fips",
            "dem_votes", "rep_votes", "total_votes",
            "dem_share", "rep_share", "dem_margin",
        ]
    ].sort_values(["year", "state", "county_fips"]).reset_index(drop=True)

    print(f"OK  ({len(result)} county-year rows)")
    return result


MANUAL_DOWNLOAD_MSG = """
Harvard Dataverse requires a one-time guestbook form for this dataset.

Steps:
  1. Go to: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/VOQCHQ
  2. Click the download icon next to 'countypres_2000-2024.tab'
  3. Fill in the short form (name / email / institution)
  4. Save the file to:
       data/raw/mit_election_lab/countypres_2000-2024.tab
  5. Re-run this script — it will detect the file and skip the download.
"""


def main():
    print("=" * 60)
    print("MIT Election Lab County-Level Presidential Returns")
    print("=" * 60)

    # Check for manually downloaded file first
    local_tab = output_dir / "countypres_2000-2024.tab"
    local_csv = output_dir / "countypres_2000-2024.csv"
    local_file = local_tab if local_tab.exists() else (local_csv if local_csv.exists() else None)

    if local_file:
        print(f"Found local file: {local_file.name}")
        data_bytes = local_file.read_bytes()
    else:
        print("Attempting Dataverse API download...")
        try:
            file_id = get_csv_file_id(DATASET_DOI)
            data_bytes = download_file(file_id)
        except Exception as e:
            if "Guestbook" in str(e) or "400" in str(e):
                print(MANUAL_DOWNLOAD_MSG)
                return
            raise

    df = parse_and_clean(data_bytes)

    output_file = output_dir / "county_returns.csv"
    df.to_csv(output_file, index=False)
    print(f"Saved to {output_file}")

    print("\n" + "=" * 60)
    print(f"Years:    {df['year'].min()}-{df['year'].max()}")
    print(f"States:   {df['state'].nunique()}")
    print(f"Rows:     {len(df)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
