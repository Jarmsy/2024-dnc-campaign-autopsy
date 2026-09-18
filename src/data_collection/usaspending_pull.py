"""Pull county-level federal obligations under Biden-era programs (IIJA, ARPA) from USAspending."""

from pathlib import Path
import time
import pandas as pd
import requests

API = "https://api.usaspending.gov/api/v2"
HEADERS = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1", "Content-Type": "application/json"}

# Disaster Emergency Fund Codes, from /references/def_codes/. IRA and CHIPS carry no DEFC (regular
# appropriations / tax expenditure) and cannot be isolated here.
PROGRAMS = {
    "iija": {"def_codes": ["1", "Z"], "start": "2021-11-15", "label": "Infrastructure Investment and Jobs Act (P.L. 117-58)"},
    "arpa": {"def_codes": ["V"],      "start": "2021-03-11", "label": "American Rescue Plan Act (P.L. 117-2)"},
}
END = "2024-11-05"

output_dir = Path("data/raw/usaspending")
output_dir.mkdir(parents=True, exist_ok=True)


def county_obligations(def_codes, start, scope):
    body = {
        "scope": scope,
        "geo_layer": "county",
        "filters": {"def_codes": def_codes, "time_period": [{"start_date": start, "end_date": END}]},
    }
    r = requests.post(f"{API}/search/spending_by_geography/", headers=HEADERS, json=body, timeout=300)
    r.raise_for_status()
    rows = r.json()["results"]
    df = pd.DataFrame(rows)[["shape_code", "display_name", "aggregated_amount", "population"]]
    df["county_fips"] = pd.to_numeric(df["shape_code"], errors="coerce").astype("Int64")
    return df.dropna(subset=["county_fips"])


def main():
    print("=" * 60)
    print("USAspending - county obligations under Biden-era programs")
    print("=" * 60)
    frames = []
    for key, cfg in PROGRAMS.items():
        for scope in ["place_of_performance", "recipient_location"]:
            print(f"{key} / {scope} ...", end=" ", flush=True)
            df = county_obligations(cfg["def_codes"], cfg["start"], scope)
            col = f"{key}_{'pop' if scope == 'place_of_performance' else 'rec'}"
            frames.append(df.set_index("county_fips")[["aggregated_amount"]].rename(columns={"aggregated_amount": col}))
            print(f"OK ({len(df):,} counties, ${df['aggregated_amount'].sum() / 1e9:.1f}B)")
            time.sleep(1)
    pop = df.set_index("county_fips")[["display_name", "population"]]

    out = pop.join(frames, how="outer").reset_index()
    for c in [c for c in out.columns if c.startswith(("iija_", "arpa_"))]:
        out[c] = out[c].fillna(0.0)
        out[c + "_pc"] = out[c] / out["population"]
    out = out.rename(columns={"display_name": "county_name", "population": "usaspending_population"})

    path = output_dir / "county_delivery.csv"
    out.to_csv(path, index=False)
    print("\n" + "=" * 60)
    print(f"Saved: {path}  ({len(out):,} counties)")
    print()
    print("Per-capita obligations, place of performance (USD):")
    for key in PROGRAMS:
        s = out[f"{key}_pop_pc"].replace([float("inf")], float("nan")).dropna()
        print(f"  {key}: median ${s.median():,.0f}   p90 ${s.quantile(.9):,.0f}   p99 ${s.quantile(.99):,.0f}   max ${s.max():,.0f}")
    top = out.nlargest(8, "iija_pop_pc")[["county_name", "iija_pop_pc", "iija_pop"]]
    print("\nHighest IIJA per capita (pass-through artifacts: federal HQ, state DOTs in capital counties, tiny counties):")
    print(top.to_string(index=False))
    print()
    print("Place of performance credits state-capital counties with formula funds that state agencies spend statewide;")
    print("recipient location has the same problem in reverse. Both are kept; use per-capita, log, and drop the tail.")
    print("=" * 60)


if __name__ == "__main__":
    main()
