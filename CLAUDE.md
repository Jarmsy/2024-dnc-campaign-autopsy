# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Three-part data-driven autopsy of the 2024 Democratic presidential campaign:

- **Part 1** — Structural fundamentals baseline (incumbency, economy, approval ratings as predicted baseline)
- **Part 2** — Demobilization vs. persuasion decomposition (how much of the loss was dropoff vs. vote-switching)
- **Part 3** — Economic populism premium across comparable campaigns

Output: narrative in `report/main_report.md` + technical appendix in `report/technical_appendix.md`, figures/tables in `outputs/`

## Stack

- Python 3.11+
- `pandas`, `geopandas` — data wrangling and spatial joins
- `statsmodels` — regression models (OLS, WLS, logit)
- `matplotlib` — figures for the report
- `jupyter` — analysis notebooks

## Data Sources & Access

| Source | What it provides | Access method |
|--------|-----------------|---------------|
| FRED API | Economic indicators (GDP, unemployment, inflation) | `fredapi` package; set `FRED_API_KEY` env var |
| MIT Election Lab | Precinct-level returns | Bulk CSV download |
| FEC.gov | Campaign finance bulk data | FTP bulk files |
| CES (Cooperative Election Study) | Individual survey microdata 2016/2020/2024 with county FIPS (~60k/yr) | Harvard Dataverse, no guestbook; `ces_pull.py` harmonizes core vars. **Question numbers and candidate codes differ by year — see `HARMONIZED`/`PRES_CODES` in the script, never use raw `CCyy_*` codes across years** |
| BLS QCEW | County private employment by NAICS sector (2012/16/20/24) | Annual single-file zips, no key; `bls_qcew_pull.py` caches zips in `data/raw/bls_qcew/` |
| Census ACS | County income, education, race, unemployment (2020 5-yr) | API; set `CENSUS_API_KEY` env var |
| CES 2020–2024 Panel | ~6,175 panelists interviewed in 2020, 2022, 2024 with county FIPS, validated turnout, and contemporaneous 2020 and 2024 vote | Dataverse `doi:10.7910/DVN/CETPVT`, no guestbook; `ces_panel_pull.py`. **Panel numbering differs from common content: economy item is `CC24_302` here (not `_301`); prices is `CC24_304`.** Weights `commonweight_24` / `commonpostweight_24` |
| Medill Local News Initiative | County local-news outlet counts by type (2025), desert/watchlist flags, RUCC, 2024→2025 newspaper change | Undocumented backend API behind the State of Local News explorer; `news_deserts_pull.py`. Server omits its TLS intermediate — script builds a CA bundle rather than disabling verification |
| ANES 2024 Time Series | 5,521 respondents; open-ended most-important-problem (coded), issue importance and party-ownership batteries, anti-elite/populism and culture-war items the CES lacks; 2016–20–24 panel ids | **Site WAF blocks python-requests (403); download the zip in a browser** into `data/raw/anes/`, then `anes_pull.py` extracts and harmonizes. Post weight `V240107b` for anything using post-election items |
| GDELT | Media coverage index | BigQuery or bulk download |

Store raw data under `data/raw/` (gitignored). Processed/cached data under `data/processed/`.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Register the project venv as a named Jupyter kernel (one-time setup, run with venv active)
python -m ipykernel install --user --name dnc-autopsy --display-name "Python (dnc-autopsy)"

# Launch Jupyter
jupyter lab

# Run a single notebook non-interactively — MUST specify kernel explicitly
jupyter nbconvert --to notebook --execute notebooks/02_fundamentals_model.ipynb \
    --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy

# Run all notebooks in order (notebooks 02-04; 01 is data collection, run scripts directly)
for nb in notebooks/02_*.ipynb notebooks/03_*.ipynb notebooks/04_*.ipynb; do
  jupyter nbconvert --to notebook --execute "$nb" \
      --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy
done
```

> **Kernel note:** Always use `--ExecutePreprocessor.kernel_name=dnc-autopsy`. The default `python3` kernel
> points to Anaconda (or system Python) on most machines and will fail to find project dependencies.
> The `dnc-autopsy` kernel is registered from `.venv` via the `ipykernel install` command above.

## Architecture

Notebooks run in sequence (01 → 04); each writes to `data/processed/` for the next to consume.

```
src/
  data_collection/    # fetch + cache logic per source (fred_pull, mit_pull, fec_pull, bls_pull)
  analysis/           # reusable model specs (fundamentals, decomposition, populism_premium)
notebooks/            # orchestration + narrative; import from src/
data/
  raw/                # original downloads, never modified
  processed/          # cleaned/merged CSVs written by notebooks
outputs/
  figures/            # matplotlib exports referenced by the report
  tables/             # CSV/LaTeX table exports
report/
  main_report.md
  technical_appendix.md
```

`src/data_collection/` modules handle auth, pagination, and local caching — notebooks call them and get back clean DataFrames. `src/analysis/` holds regression specs and decomposition helpers so the same model can be run across notebooks without copy-paste. Notebooks own the narrative and parameter choices; `src/` owns the reusable mechanics.

## Key Analytical Decisions to Track

- **Unit of analysis**: county for all three parts (Parts 1–3)
- **Swing metric**: `dem_share_2024 - dem_share_2020` (two-party share, signed negative = rightward)
- **Decomposition**: Kitagawa-Blinder at county level: `turnout_component + share_component = ΔDem_votes`
- **Multi-cycle baseline (Part 3)**: Obama 2012 as the fixed reference; Clinton/Biden/Harris each compared against it by income quartile
- **Regression weights (Part 3 WLS)**: 2020 county turnout
- **MIT data filter**: always filter `mode == "TOTAL"` before aggregating — raw file includes sub-mode rows that inflate totals by ~1.5–2×
- **Income variable**: log(median household income) — ACS 2020 five-year estimates
