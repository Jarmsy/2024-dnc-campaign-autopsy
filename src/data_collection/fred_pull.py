"""Pull economic and political series from FRED API and save as CSVs."""

import os
import time
from pathlib import Path
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

# Load FRED_API_KEY from .env
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

if not API_KEY:
    raise ValueError(
        "FRED_API_KEY not found. Set it in a .env file in the project root:\n"
        "FRED_API_KEY=your_key_here\n"
        "Get a free API key at https://fredaccount.stlouisfed.org/login"
    )

fred = Fred(api_key=API_KEY)
output_dir = Path("data/raw/fred")
output_dir.mkdir(parents=True, exist_ok=True)

# Series to pull with metadata
series_config = {
    "GDPC1": {
        "description": "Real GDP",
        "expected_range": ("1947-01-01", "2024-12-31"),
    },
    "CPIAUCSL": {
        "description": "CPI, All Urban Consumers",
        "expected_range": ("1947-01-01", "2024-12-31"),
    },
    "UMCSENT": {
        "description": "University of Michigan Consumer Sentiment",
        "expected_range": ("1978-01-01", "2024-12-31"),
    },
    "UNRATE": {
        "description": "Unemployment Rate",
        "expected_range": ("1948-01-01", "2024-12-31"),
    },
    "DSPIC96": {
        "description": "Real Disposable Personal Income",
        "expected_range": ("1959-01-01", "2024-12-31"),
    },
    "APPROVE": {
        "description": "Presidential Approval Rating (Gallup)",
        "expected_range": ("1945-01-01", "2024-12-31"),
    },
}

def pull_series(series_id, description):
    """Pull a single series from FRED with rate limit handling."""
    try:
        print(f"Pulling {series_id} ({description})...", end=" ", flush=True)
        data = fred.get_series(series_id)
        filepath = output_dir / f"{series_id}.csv"
        data.to_csv(filepath)
        print(f"OK  {len(data)} observations saved to {filepath.name}")
        return True
    except Exception as e:
        print(f"ERR {e}")
        return False

def main():
    """Pull all configured FRED series."""
    print(f"FRED API pull starting. Output directory: {output_dir}\n")

    successful = []
    failed = []

    for series_id, config in series_config.items():
        success = pull_series(series_id, config["description"])
        if success:
            successful.append(series_id)
        else:
            failed.append(series_id)
        # Rate limit: FRED allows 120 requests per minute, add small delay to be safe
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Summary: {len(successful)} successful, {len(failed)} failed")
    if successful:
        print(f"  OK:  {', '.join(successful)}")
    if failed:
        print(f"  ERR: {', '.join(failed)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
