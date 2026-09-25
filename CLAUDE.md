# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data-driven autopsy of the 2024 Democratic presidential campaign, in eleven parts. It began as three:

- **Part 1** — Structural fundamentals baseline (incumbency, economy, approval ratings as predicted baseline)
- **Part 2** — Demobilization vs. persuasion decomposition (how much of the loss was dropoff vs. vote-switching)
- **Part 3** — Economic populism premium across comparable campaigns

Part 3 concluded that a populism premium cannot be tested with county returns, which is what drove the expansion: Parts 4–9 take the question to individual voters (perception, panel timing, the bottom quartile and federal delivery, stronghold turnout, what leavers believed, cross-pressure), and Parts 10–11 to actual economic-left campaigns (NYC 2024→2025 at the election-district level; Justice Democrats House primaries 2018–2026). The synthesis at the end of `main_report.md` was re-audited claim by claim against `outputs/tables/` on 2026-09-23; treat it, not earlier drafts, as the current statement of findings.

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
| ANES 2024 Time Series | 5,521 respondents; open-ended most-important-problem (coded), issue importance and party-ownership batteries, anti-elite/populism and culture-war items the CES lacks; pre-election self/Harris/Trump placements on 7-pt economic and abortion scales; 2016–20–24 panel ids | **Site WAF blocks python-requests (403); download the zip in a browser** into `data/raw/anes/`, then `anes_pull.py` extracts and harmonizes. Post weight `V240107b` for anything using post-election items |
| NYC BOE / DCP / Census | Election-district returns for 2020 & 2024 presidential and 2025 mayoral primary (from the ranked-choice cast vote record) and general; ED shapefiles; 2020 census blocks; block-based ED demographics | `nyc_pull.py`. **BOE ED CSVs prefix every row with the header — parse by position.** RCV contests are not published by ED; rebuilt from the CVR zip (slow; cached to `prim25_cvr_by_ed.csv`). 2020 votes crosswalked to current EDs via blocks. Needs `CENSUS_API_KEY`; `pyogrio` engine for shapefiles (fiona 1.10 breaks geopandas 0.13) |
| NYC CFB | Independent expenditures by spender × candidate × support/oppose (2013–2025), candidate committee summaries | No bulk IE file; `nyc_cfb_pull.py` scrapes the ASP.NET summary and spender pages. Office code for Mayor is 1 except 11 in the 2021 financial-analysis CSV |
| FEC API | Candidate search, house-senate reports (pre-primary YTD receipts), Schedule E IE by candidate | `fec_insurgent_pull.py`; set `FEC_API_KEY` (free). **DEMO_KEY is 40 calls/hour.** Cached JSON in `data/raw/insurgent/fec/`; `OPEN_SEAT` override for retired incumbents the FEC still lists |
| GDELT DOC 2.0 API | Daily article volume and tone per query per source domain, 2017+ | `gdelt_nyc_pull.py`. **Stated limit one request per 5 s — never probe by hand while the script runs.** In practice the API 429s about three requests in four regardless of pacing (server load, not a cooldown): 20 s spacing, flat 60 s retry, ~2–3 min per served query, 6–8 h for a full pull; resumable, empty series checkpointed in `empty_series.txt`. Index gaps: no nypost.com in 2021; no articles at all June 15–July 1 2025; nytimes.com recall 82% in 2021 but 5.8% in 2025 (paywall); **washingtonpost.com not indexed at all after 1 July 2024**. Verify a domain with `audit_coverage.py --probe` before trusting its absence |
| NYT Archive API | Every NYT article per month (census, not a crawl sample) with headline, abstract, print page and section | `nyt_archive_pull.py`; set `NYT_API_KEY` (free, developer.nytimes.com, enable Archive API). Monthly JSON 7–25 MB cached in `data/raw/nyt_archive/`. **Scoreable text is headline + abstract only: `lead_paragraph` is 98.7% present in 2021 and 0% in 2025.** Errors are raised without the request URL because it carries the key |
| NYSBOE party enrolment | Enrolment by NYC election district, DEM/REP/CON/WOR/OTH/BLANK × Active/Inactive/Total | `nyc_enrollment_pull.py`. Node URL `elections.ny.gov/<county>-<MMDDYYYY>` returns the XLSX directly. **WAF fingerprints TLS: `requests` gets 403 with byte-identical headers, `curl` gets 200 — the script shells out to curl.** Snapshots 2021-11-01, 2025-02-20, 2025-11-01, 2026-02-20; the February ones fall six days after each year's 14 Feb party-change deadline. **ED lines were edited between Nov 2025 and Feb 2026 (6.9% of EDs moved >25%)** |
| FEC election-results compilations | Official House primary and general votes by district, 2016–2022 | `fec_primary_turnout_pull.py`. `fec.gov/documents/<id>/federalelections<year>.xlsx`; **ids are not derivable** (1890/2706/4228/5676 for 2016/18/20/22). Democratic primary turnout is the `Party Votes:` row with `PARTY == "D"`; the 2016 district column is `D`, later `DISTRICT`. 2024 and 2026 not yet published — the 2026 insurgent cases use state results via `state_primary_2026_extract.py` (Wikipedia election-box templates) |
| NYC 2026 congressional primaries | June 2026 Democratic House primaries by ED | `nyc_2026_primary_pull.py`. **BOE "Crossover" files are exact duplicates of the county files for multi-county districts — read county files only.** Public Counter / Emergency / Absentee / Federal / Affidavit rows are ballot-method tallies, not candidates |
| FEC Schedule E, super PACs | Every itemized independent expenditure by UDP (AIPAC), DMFI PAC, Fairshake and Protect Progress, 2022–2026 | `superpac_ie_pull.py` (reuses the FEC getter). **The itemized endpoint ignores `two_year_transaction_period` and pages by keyset** — pull each committee's history once, take the cycle from the date, reconcile to `/committee/<id>/totals/` |
| Super PAC ad content (hand-coded) | 47 ads in 20 Democratic primaries plus 6 contrast cases, multi-label attack modes, lead mode, disputed claims, sources | `data/coded/superpac_ads_coded.csv` — **tracked in git, unlike `data/raw/`, because it is hand-coded and cannot be regenerated**. Codebook and fixed hypotheses in `src/analysis/attack_modes.py`; UDP publishes a citation page per ad script (its `sitemap.xml` lists them) |
| Super PAC targets and results | 24 Democratic primaries 2022–2026 with an identifiable super PAC target: money on both sides and head-to-head result | `superpac_targets_pull.py`. **Wikipedia (MediaWiki API) throttles bursts with non-JSON pages — cache and retry; some runoff tables reuse the title 'Democratic primary results' (select the nth box) and some are raw HTML (enter by hand).** FEC name search can return a same-surname candidate from another district — every match is checked on first and last name |
| Pop-up committee funding | 2026 spenders in the studied races, their side, itemized receipts (Schedule A) and the network's 2026 disbursements (Schedule B) | `popup_donors_pull.py`. Schedule A/B page by keyset (`last_index` + last date); money passes through intermediaries (UDP → EDW Action Fund → Pro-Choice Majority Action), so trace one level of disbursements, not only direct transfers |
| Candidate ages | Birth dates for Part 11 challengers, their incumbents, and the 2026 incumbent defeats | `candidate_ages_pull.py`, Wikidata P569; matches accepted only for humans described as U.S. politicians; cached |
| Contested Democratic incumbent primaries | Every contested Democratic House incumbent primary 2024 and 2026, with district 18–34 share (ACS) and incumbent age | `incumbent_primaries_pull.py`. **Wikipedia candidate fields use piped links (`[[Article|Display]] (incumbent)`) — a pattern that stops at the first `|` drops those incumbents silently.** 2026 rows exclude the ten states with new maps; Wikidata year-only birth dates come back as YYYY-00-00 |
| NJ and VA 2025 results | NJ governor 2021 and 2025 by municipality, VA governor 2021 and 2025, lt. governor and AG by locality, with 2020 and 2024 presidential | `same_day_2025_pull.py`. **NJ column order follows each county's ballot draw — read D/R from each PDF's header; every county reconciles to its printed total.** VA's historical site is a JS app; CSVs at `va2.elstats.civera.com/api/download_contest/<id>_table.csv` (307 redirect) |
| ICE enforcement (Deportation Data Project) | ICE arrests, detainers, detentions, removals from FOIA (Hausman v. ICE), Oct 2022–Aug 2026 | `github.com/deportationdata/ice/raw/refs/heads/main/data/<dataset>-latest.parquet` (needs `pyarrow`). **No county field; the city field often records the ERO office (Newark, Chantilly, 26 Federal Plaza) or a county jail, not where the arrest happened — unusable for town-level exposure** |
| ACS immigration shares | Non-citizen and Hispanic shares, median income, NJ municipalities and VA localities | `acs_immigration_pull.py` (B05001, B03003, B19013). Census names add the type word ("Jersey City city", "City of Orange township"); matched within county, then on the bare name if unique |
| YouTube | Videos naming 2025–26 candidates, 90 days pre-election, with views and channel class | `youtube_creator_pull.py`; set `YOUTUBE_API_KEY` (free; 10,000 units/day, a search costs 100). **Channel descriptions make regex classification unreliable (streamers say 'news') — the top channels are hand-coded in `HAND`; tiny-subscriber channels with huge views are paid promotion.** Views accrue after the election |
| Public polling | Mamdani job approval and favourability 2026, Siena regional crosstabs | Hand-entered with source URL and a `verified` column in `data/raw/nyc/`; job approval, four-point job rating and favourability are separate constructs and must not be blended |

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

# Run all notebooks in order (02 through 19; there is no 01 -- data collection is the scripts)
for nb in notebooks/[0-9][0-9]_*.ipynb; do
  jupyter nbconvert --to notebook --execute "$nb" \
      --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy --ExecutePreprocessor.timeout=1800
done
```

> **Kernel note:** Always use `--ExecutePreprocessor.kernel_name=dnc-autopsy`. The default `python3` kernel
> points to Anaconda (or system Python) on most machines and will fail to find project dependencies.
> The `dnc-autopsy` kernel is registered from `.venv` via the `ipykernel install` command above.

## Architecture

Notebooks run in sequence, 02 → 19 (there is no 01; data collection is the scripts in `src/data_collection/`). The early notebooks (02–09) write to `data/processed/` for later ones; 10–19 mostly read `data/raw/` directly.

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

`src/data_collection/` modules handle auth, pagination, and local caching. **In practice nearly all analysis lives in the notebooks**: the shared regression and decomposition helpers once planned for `src/analysis/` were never built, and `src/analysis/framing.py` (the headline-framing lexicon used by notebooks 18 and 19) is the only module there. Do not assume a model spec exists in `src/` — find it in the notebook that produced the table.

## Key Analytical Decisions to Track

- **Unit of analysis**: national election (Part 1), county (Parts 2–3, 6–7), survey respondent (Parts 4–9; CES cross-sections, CES 2020–24 panel, ANES 2024), NYC election district (Part 10), House primary race and news article (Parts 10–11)
- **Swing metric**: `dem_share_2024 - dem_share_2020` (two-party share, signed negative = rightward)
- **Decomposition**: Kitagawa-Blinder at county level: `turnout_component + share_component = ΔDem_votes`
- **Multi-cycle baseline (Part 3)**: Obama 2012 as the fixed reference; Clinton/Biden/Harris each compared against it by income quartile
- **Regression weights (Part 3 WLS)**: 2020 county turnout
- **MIT data filter**: always filter `mode == "TOTAL"` before aggregating — raw file includes sub-mode rows that inflate totals by ~1.5–2×
- **Income variable**: log(median household income) — ACS 2020 five-year estimates
