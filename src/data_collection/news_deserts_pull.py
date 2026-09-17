"""Pull county-level local news outlet counts from the Medill Local News Initiative (State of Local News 2025)."""

from pathlib import Path
import ssl
import time
import certifi
import pandas as pd
import requests

# Backend that serves https://localnewsinitiative.northwestern.edu/projects/state-of-local-news/explore/
# (host and port read from that page's assets/runtime-config.js). Unauthenticated, no documented terms;
# calls are paced and cached so the pull runs once.
API = "https://northwesternlni.com:9095"
YEAR = 2025
HEADERS = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1", "Referer": "https://localnewsinitiative.northwestern.edu/"}
PAUSE = 0.5

# The server omits its Sectigo intermediate from the TLS chain. Browsers fetch it via AIA; Python does not,
# so verification fails with "unable to get local issuer certificate". Append the intermediate to certifi's
# bundle rather than disabling verification.
INTERMEDIATE_URL = "http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt"

STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
    "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH",
    "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
]

MEDIA_TYPES = {
    "Newspapers": "newspapers",
    "Digital sites": "digital",
    "Ethnic Outlets": "ethnic",
    "Public Broadcasting": "public_broadcasting",
    "Network Sites": "network",
}

output_dir = Path("data/raw/news_deserts")
output_dir.mkdir(parents=True, exist_ok=True)


def ca_bundle():
    path = output_dir / "ca_bundle.pem"
    if not path.exists():
        der = requests.get(INTERMEDIATE_URL, timeout=30).content
        path.write_text(Path(certifi.where()).read_text() + "\n" + ssl.DER_cert_to_PEM_cert(der))
    return str(path)


def get(path, verify):
    r = requests.get(API + path, headers=HEADERS, timeout=120, verify=verify)
    r.raise_for_status()
    time.sleep(PAUSE)
    return r.json()


def pull_outlets(verify):
    print("Outlet inventory ...", end=" ", flush=True)
    rows = get(f"/lni/localnewstable?year={YEAR}", verify)
    df = pd.DataFrame(rows)[["state", "county", "fips", "mediaName", "mediaType", "active", "yearLoaded"]]
    df["county_fips"] = pd.to_numeric(df["fips"], errors="coerce").astype("Int64")
    df["media_type"] = df["mediaType"].map(MEDIA_TYPES).fillna(df["mediaType"])
    print(f"OK ({len(df):,} outlets, {df['county_fips'].nunique():,} counties)")
    return df


def pull_watchlist(verify):
    print("Desert / watchlist classification ...", end=" ", flush=True)
    rows = get(f"/api/watchlistcounties?year={YEAR}", verify)["watchlistCounties"]
    df = pd.DataFrame(rows)[["state", "countyName", "countyfips", "category", "population", "averagePovertyRate"]]
    df["county_fips"] = pd.to_numeric(df["countyfips"], errors="coerce").astype("Int64")
    print(f"OK ({(df['category'] == 'Desert').sum()} deserts, {(df['category'] == 'Watchlist').sum()} watchlist)")
    return df[["county_fips", "category"]].rename(columns={"category": "lni_category"})


def pull_demographics(verify):
    print("County spine + RUCC by state ...", end=" ", flush=True)
    frames = []
    for st in STATES:
        rows = get(f"/api/demographics?year={YEAR}&state={st}", verify)["demographics"]
        frames.append(pd.DataFrame(rows))
    df = pd.concat(frames, ignore_index=True)
    df["county_fips"] = pd.to_numeric(df["countyFips"], errors="coerce").astype("Int64")
    out = df[["county_fips", "stateAbbr", "county", "rucc", "ruccDescription",
              "population", "medianIncome", "medianAge", "percentageBelowPoverty"]].rename(columns={
        "stateAbbr": "state", "ruccDescription": "rucc_desc", "population": "lni_population",
        "medianIncome": "lni_median_income", "medianAge": "lni_median_age",
        "percentageBelowPoverty": "lni_poverty_rate"})
    for c in ["rucc", "lni_population", "lni_median_income", "lni_median_age", "lni_poverty_rate"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    print(f"OK ({len(out):,} counties)")
    return out


def pull_compare(verify, spine):
    """2025 vs 2024 outlet counts per county. Keyed by county name within state; joined to FIPS via the spine."""
    print(f"{YEAR} vs {YEAR - 1} counts by state ...", end=" ", flush=True)
    rows = []
    for st in STATES:
        m = get(f"/api/lni/state/county?currentYear={YEAR}&compareYear={YEAR - 1}&state={st}", verify)
        for county, v in m["activePapersCompareResponseMap"].items():
            rows.append({
                "state": st, "county": county,
                f"newspapers_{YEAR}": v["currentYearCountOfNewsPapers"],
                f"newspapers_{YEAR - 1}": v["compareYearCountOfNewsPapers"],
                f"digital_{YEAR}": v["currentYearCountOfDigitalSites"],
                f"digital_{YEAR - 1}": v["compareYearCountOfDigitalSites"],
                f"public_broadcasting_{YEAR}": v["currentYearCountOfPublicBroadCasting"],
                f"public_broadcasting_{YEAR - 1}": v["compareYearCountOfPublicBroadCasting"],
                f"ethnic_{YEAR}": v["currentYearCountOfEthnicity"],
                f"ethnic_{YEAR - 1}": v["compareYearCountOfEthnicity"],
            })
    cmp = pd.DataFrame(rows)
    count_cols = [c for c in cmp.columns if c not in ("state", "county")]

    # Two-pass name match. The 2024 side of the map drops "Parish" (LA) and "city" (VA independent cities),
    # so the same county arrives as two rows ("Acadia Parish" with 2025 counts, "Acadia" with 2024 counts).
    # Pass 1 exact; pass 2 strips the suffixes for rows still unmatched, accepting only spine names that are
    # unique after stripping. A county/city pair like Richmond / Richmond city both match exactly in pass 1
    # and never reach pass 2. Rows for the same FIPS are then summed.
    exact = lambda s: s.str.upper().str.replace(r"[^A-Z]", "", regex=True)
    stripped = lambda s: exact(s.str.upper().str.replace(r"\b(PARISH|CITY|COUNTY|BOROUGH|CENSUS AREA|MUNICIPALITY)\b", "", regex=True))
    cmp["_k1"] = cmp["state"] + exact(cmp["county"])
    cmp["_k2"] = cmp["state"] + stripped(cmp["county"])
    sp = spine.assign(_k1=spine["state"] + exact(spine["county"]), _k2=spine["state"] + stripped(spine["county"]))

    cmp = cmp.merge(sp[["_k1", "county_fips"]], on="_k1", how="left")
    sp2 = sp.drop_duplicates("_k2", keep=False)[["_k2", "county_fips"]]
    second = cmp.loc[cmp["county_fips"].isna(), ["_k2"]].merge(sp2, on="_k2", how="left")
    cmp.loc[cmp["county_fips"].isna(), "county_fips"] = second["county_fips"].values

    unmatched = cmp[cmp["county_fips"].isna()]
    print(f"OK ({len(cmp):,} rows; {len(unmatched)} unmatched: {dict(unmatched['state'].value_counts())})")
    cmp = cmp.dropna(subset=["county_fips"]).groupby("county_fips", as_index=False)[count_cols].sum()
    cmp["county_fips"] = cmp["county_fips"].astype("Int64")
    return cmp


def build_summary(spine, outlets, watch, cmp):
    counts = (outlets.dropna(subset=["county_fips"])
              .pivot_table(index="county_fips", columns="media_type", values="mediaName", aggfunc="count", fill_value=0)
              .reset_index())
    for c in MEDIA_TYPES.values():
        if c not in counts.columns:
            counts[c] = 0
    counts.columns = ["county_fips"] + [f"n_{c}" for c in counts.columns[1:]]

    df = spine.merge(counts, on="county_fips", how="left").merge(watch, on="county_fips", how="left")
    ncols = [f"n_{c}" for c in MEDIA_TYPES.values()]
    df[ncols] = df[ncols].fillna(0).astype(int)
    df["n_outlets"] = df[ncols].sum(axis=1)
    df["n_outlets_excl_network"] = df["n_outlets"] - df["n_network"]
    df["news_desert"] = (df["n_outlets"] == 0).astype(int)
    df["single_outlet"] = (df["n_outlets"] == 1).astype(int)
    df["outlets_per_100k"] = df["n_outlets"] / df["lni_population"] * 1e5
    df["lni_category"] = df["lni_category"].fillna("None")

    # The compare endpoint omits counties with no newspapers in either year; those are zeros, not missing
    df = df.merge(cmp, on="county_fips", how="left")
    df["in_compare_map"] = df[f"newspapers_{YEAR}"].notna().astype(int)
    cmp_cols = [c for c in cmp.columns if c != "county_fips"]
    df[cmp_cols] = df[cmp_cols].fillna(0).astype(int)
    # Connecticut's 2024 counts are by planning region, which has no county mapping; leave them missing
    prior_cols = [c for c in cmp_cols if c.endswith(f"_{YEAR - 1}")]
    df.loc[df["state"] == "CT", prior_cols] = pd.NA
    df[f"newspapers_lost_{YEAR - 1}_{YEAR}"] = df[f"newspapers_{YEAR - 1}"] - df[f"newspapers_{YEAR}"]
    return df


def main():
    print("=" * 60)
    print(f"Medill Local News Initiative - State of Local News {YEAR}")
    print("=" * 60)
    verify = ca_bundle()

    outlets = pull_outlets(verify)
    watch = pull_watchlist(verify)
    spine = pull_demographics(verify)
    cmp = pull_compare(verify, spine)
    summary = build_summary(spine, outlets, watch, cmp)

    outlets.drop(columns=["fips", "mediaType"]).to_csv(output_dir / f"lni_outlets_{YEAR}.csv", index=False)
    summary.to_csv(output_dir / "lni_county_summary.csv", index=False)

    print("\n" + "=" * 60)
    print(f"Saved: data/raw/news_deserts/lni_outlets_{YEAR}.csv")
    print(f"Saved: data/raw/news_deserts/lni_county_summary.csv  ({len(summary):,} counties)")
    print()
    print(f"Counties with no outlets:   {summary['news_desert'].sum():>5}  (report says 213)")
    print(f"Counties with one outlet:   {summary['single_outlet'].sum():>5}")
    print(f"LNI 'Desert' category:      {(summary['lni_category'] == 'Desert').sum():>5}")
    print(f"LNI 'Watchlist' category:   {(summary['lni_category'] == 'Watchlist').sum():>5}")
    print(f"Newspapers {YEAR - 1} -> {YEAR}:  {summary[f'newspapers_{YEAR - 1}'].sum():.0f} -> {summary[f'newspapers_{YEAR}'].sum():.0f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
