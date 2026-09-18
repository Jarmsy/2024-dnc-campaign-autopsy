# Technical Appendix

*Companion to [`main_report.md`](main_report.md). Every number here is taken from the executed notebooks in `notebooks/`; tables are exported to `outputs/tables/`.*

---

## A. Data sources and handling

### A.1 MIT Election Lab county presidential returns

**Source:** Harvard Dataverse, `doi:10.7910/DVN/VOQCHQ`, file `countypres_2000-2024.csv`. Requires a one-time guestbook form; download manually to `data/raw/mit_election_lab/`.
**Script:** `src/data_collection/mit_pull.py` → `data/raw/mit_election_lab/county_returns.csv` (22,082 county-year rows, 2000–2024, 51 states).

**Vote-mode handling.** The raw file has a `mode` column and three reporting patterns that vary by state and year:

| Pattern | 2020 | 2024 |
|---|---|---|
| Single TOTAL row per county | 40 states | 33 states |
| Per-mode rows only (ABSENTEE, ELECTION DAY, EARLY, PROVISIONAL, …), no TOTAL | AZ, AR, GA, IA, KY, MD, NC, OK, SC, VA | ID, NC, RI, UT, WA, WV, WI, WY |
| Both TOTAL and mode rows for the same county | UT | AZ, AR, IA, LA, NM, OK, PA, SC, SD, TX |

Filtering to `mode == "TOTAL"` drops the second group entirely; summing all rows double-counts the third. The pipeline resolves this per county-party: use the TOTAL row when one exists, otherwise sum the mode rows. `totalvotes` is the county total repeated on every row and is taken as a max, not a sum.

**Validation against certified national results:**

| Year | Dem votes (pipeline) | Dem (certified) | Rep (pipeline) | Rep (certified) | Two-party Dem |
|---|---|---|---|---|---|
| 2012 | 65.75M | 65.92M | 60.67M | 60.93M | 52.01% |
| 2016 | 65.84M | 65.85M | 62.98M | 62.98M | 51.11% |
| 2020 | 81.26M | 81.28M | 74.22M | 74.22M | 52.27% |
| 2024 | 75.01M | 75.02M | 77.30M | 77.30M | 49.25% |

**Alaska.** MIT codes Alaska by state house district (`county_fips` 2001–2040), not borough. Districts were redrawn in 2022, so 2020 and 2024 rows with the same code are different geographies; several codes also collide with real borough FIPS (02013, 02016, 02020). Alaska is retained in national and state-level totals and excluded from all county-level panels.

**Derived columns.** `dem_share = dem_votes / total_votes` and `rep_share = rep_votes / total_votes`, where `total_votes` includes third-party votes. `dem_margin = dem_share − rep_share`. Part 1 uses the two-party share `dem / (dem + rep)`; Parts 2–3 use the raw shares as defined here. The distinction is small (third-party vote was 1.9% in both 2020 and 2024) but the two are not interchangeable.

### A.2 FRED

**Script:** `src/data_collection/fred_pull.py`; requires `FRED_API_KEY`. Series pulled: GDPC1 (real GDP), CPIAUCSL (CPI), UNRATE, UMCSENT (consumer sentiment), DSPIC96 (real disposable income). Only GDPC1 and CPIAUCSL are used in the current models.

- **Q2 GDP growth** = `((GDP_Q2 / GDP_Q1)^4 − 1) × 100`, election year.
- **CPI deflators** for QCEW pay: annual mean of monthly CPIAUCSL, base 2024. 2012 → 1.366, 2016 → 1.307, 2020 → 1.212.

FRED has no presidential-approval series. June Gallup approval is hand-coded in notebook 02 from Gallup's Presidential Job Approval Center.

### A.3 Census ACS 2020 five-year estimates

**Endpoint:** `api.census.gov/data/2020/acs/acs5`, `for=county:*`; requires `CENSUS_API_KEY`. 3,220 counties returned.

| Variable | Construction |
|---|---|
| `med_income` | B19013_001E |
| `college_share` | (B15003_022E + 023E + 024E + 025E) / B15003_001E — bachelor's or higher, population 25+ |
| `white_nh_share` | B03002_003E / B03002_001E |
| `unemp_rate` | B23025_005E / B23025_002E — unemployed / civilian labor force |
| `white_nocollege` | `white_nh_share × (1 − college_share)` |
| `log_income` | ln(`med_income`) |

`white_nocollege` is a county-level product of two shares, not a count of white non-college individuals. It is the best available proxy from published ACS tables but it cannot separate a 90%-white / 20%-college county from a 60%-white / 30%-college one on the dimension that matters.

The 2020 five-year file pools 2016–2020 responses. It predates the inflation of 2021–23 and the post-pandemic labor market. It is used because it is the last vintage that is unambiguously "pre-treatment" for the 2020 → 2024 comparison.

### A.4 BLS Quarterly Census of Employment and Wages

**Script:** `src/data_collection/bls_qcew_pull.py`; no key. Downloads `{year}_annual_singlefile.zip` for 2012, 2016, 2020, 2024 (~77 MB each, cached in `data/raw/bls_qcew/`), streams the ~3.5M-row files, and keeps county × private-ownership rows at aggregation levels 71 (all industries) and 74 (NAICS sector).

**Outputs:** `qcew_county_sectors.csv` (long, every sector) and `qcew_county_summary.csv` (wide: `private_emp`, `mfg_emp`, `mfg_share`, `private_avg_pay` by year).

**Suppression.** BLS withholds cells where one or two employers dominate (`disclosure_code = "N"`), reporting the value as 0. The pipeline recodes those to missing. A county with *no* manufacturing row at all has no establishments and is coded as a true zero — 58–60 counties per year. Suppression affects 500 of 3,236 counties (15.5%) in 2016 or 2024; their median private employment is 1,007 versus 7,965 for unsuppressed counties. Notebook 05 fills a suppressed year from the nearest available year (2016 ← 2012 ← 2020; 2024 ← 2020) and carries a flag; 203 (2016) and 267 (2024) remain missing after filling and are excluded from regressions that use them.

`avg_annual_pay` is total wages divided by average employment — a mean, not a median, and per job rather than per worker. It rises when low-wage jobs disappear. Treat `real_pay_pct_chg` as a coarse measure.

### A.5 Cooperative Election Study (CES)

**Source:** Harvard Dataverse, CCES dataverse. 2016 `doi:10.7910/DVN/GDF6Z0`, 2020 `doi:10.7910/DVN/E9N6PH`, 2024 `doi:10.7910/DVN/X11EP6`. No guestbook; the common-content CSV/tab files (135–190 MB) and guide PDFs download via the API.
**Script:** `src/data_collection/ces_pull.py` → `data/raw/ces/ces_{year}.csv` and `ces_2016_2024_core.csv`.
**Sample:** 64,600 (2016), 61,000 (2020), 60,000 (2024). YouGov opt-in panel with sample matching; `commonweight` for pre-election items, `commonpostweight` for post-election items (49,432 post-wave respondents in 2024).

**County identifier.** `countyfips` is in the public common-content file for all three waves (99.8–100% non-missing) and matches the integer FIPS used elsewhere in the project. 98.7% of 2024 respondents fall in a county with complete QCEW data. Median respondents per county is 6 (IQR 2–16); 602 counties have 20 or more, 272 have 50 or more.

**Cross-year harmonization.** Two traps, both verified against the guide PDFs:

| Item | 2016 | 2020 | 2024 |
|---|---|---|---|
| Nation's economy past year | `CC16_302` | `CC20_302` | **`CC24_301`** |
| Household income | `CC16_303` (past *four* years) | `CC20_303` | **`CC24_302`** |
| Prices past year | — | — | `CC24_303` (new) |
| Presidential vote (post) | `CC16_410a`: **Trump = 1, Clinton = 2** | `CC20_410`: Biden = 1, Trump = 2 | `CC24_410`: Harris = 1, Trump = 2 |
| Recalled prior vote | — | `presvote16post` | `presvote20post` (Biden = 1, Trump = 2) |

The question numbers shifted in 2024 and the 2016 candidate order is reversed relative to later waves. The pull script emits `presvote_post_party` and `presvote_prior_party` as D/R/other so raw codes never cross years. Weighted two-party Democratic share of reported vote: 51.4% (2016), 53.1% (2020), 49.0% (2024) against actual 51.1 / 52.3 / 49.25 — the standard CES validity check.

**Scales.** Economy item: 1 much better … 5 much worse, 6 not sure → recoded to +2 … −2, not-sure dropped. Household income (`CC24_302`): 1 increased a lot … 5 decreased a lot → +2 … −2. Prices (`CC24_303`): 1 increased a lot … 5 decreased a lot → recoded **+2 = increased a lot, −2 = decreased a lot** — higher means more inflation experienced, the opposite valence to the other two items; the notebook and all tables carry this sign. `pid7`: 1 strong Democrat … 4 independent … 7 strong Republican, 8 not sure (dropped). Media items (`CC24_300_1..5`, past 24 hours, check-all, 1 = yes): social media, TV news, newspaper, radio, none. `CC24_300a` TV type: 1 local, 2 national, 3 both. `CC24_300b_1..8` networks watched: ABC, CBS, NBC, CNN, Fox, MSNBC, PBS, other. `educ`: 1 no HS … 5 four-year, 6 post-grad; college = 5 or 6.

**Recall bias.** In the 2024 wave, recalled 2020 vote is 45% Biden / 32% Trump / 20% did not vote, against an actual 51 / 47. Trump 2020 voters are under-represented among recallers, so switching analyses are run primarily on the recalled-Biden group.

### A.6 Medill Local News Initiative — State of Local News 2025

**Source:** The county-level data behind `localnewsinitiative.northwestern.edu/projects/state-of-local-news/explore/`. Medill publishes no download; the explorer is an Angular app that reads an unauthenticated backend at `northwesternlni.com:9095` (host and port from the page's `runtime-config.js`). Four endpoints are used: the full 2025 outlet inventory (`/lni/localnewstable?year=2025`, 8,051 outlets with county FIPS and media type), the desert/watchlist classification (`/api/watchlistcounties`), per-state county demographics with USDA Rural-Urban Continuum Codes (`/api/demographics`), and per-state 2025-vs-2024 outlet counts (`/api/lni/state/county`). Calls are paced at 0.5 s and cached.
**Script:** `src/data_collection/news_deserts_pull.py` → `data/raw/news_deserts/lni_outlets_2025.csv`, `lni_county_summary.csv` (3,144 counties).

**Validation.** Counties with zero outlets in the pulled inventory: 213; with exactly one: 1,526. Both match the figures the site itself reports. The 2025 newspaper count from the year-over-year endpoint agrees with the inventory count in 99.9% of counties.

**TLS.** The server omits its Sectigo intermediate certificate from the chain. Browsers fetch it via AIA; Python's `requests` does not and fails verification. The script downloads the intermediate from the AIA URL in the leaf certificate and appends it to certifi's bundle. Verification is not disabled.

**Name matching.** The 2024 side of the year-over-year map names Louisiana parishes without "Parish" and Virginia independent cities without "city," so the same county arrives as two rows. A two-pass match (exact, then suffix-stripped for still-unmatched rows against spine names unique after stripping) resolves this; Richmond / Richmond city and similar pairs both match exactly in pass 1 and never reach pass 2. Connecticut's 2024 counts are by planning region and are left missing. Counties absent from the year-over-year map have no newspapers in either year and are coded zero.

**Two desert definitions.** `news_desert` is the mechanical count: zero outlets of any type in the 2025 inventory (213 counties; this is what the site's map legend reports). `lni_desert` is Medill's curated "Desert" designation from the watchlist endpoint (206 counties). They agree on 163 counties. Of the 43 Medill deserts with an outlet in the inventory, 38 have a newspaper — so the label appears to reflect whether an outlet actually covers the county, not merely whether one is based there. Of the 50 zero-outlet counties without the label, 10 are Virginia independent cities (presumably covered by adjacent-county papers) and 11 carry Medill's "Watchlist" label instead. Part 4 uses the count-based definition in the main models and reports every key result under the Medill label as well (E.9).

**Variables used in Part 4:** `news_desert`, `lni_desert`, `lni_watchlist`, `single_outlet`, `n_outlets`, `outlets_per_100k` (log1p in models), `rucc` and `nonmetro` (RUCC ≥ 4), `newspapers_lost_2024_2025`.

---

## B. Part 1 — Fundamentals model

### B.1 Specification

```
inc_vote_share ~ gdp_q2_growth + approval_rating_june + consecutive_terms + open_seat
```

`inc_vote_share` is the incumbent party's two-party share: `dem_two_party_share` when a Democrat holds the White House, `100 − dem_two_party_share` otherwise. Predictions are mapped back to Democratic share for display. Fit by OLS on 1948–2020 (N = 19); 2024 held out.

### B.2 Data

| Year | Inc. | Dem 2-party | Q2 GDP | June appr. | Terms | Open | LOOCV resid. (Dem) |
|---|---|---|---|---|---|---|---|
| 1948 | D | 52.37 | +6.8 | 39 | 4 | | +4.1 |
| 1952 | D | 44.60 | +0.9 | 32 | 5 | ✓ | +1.2 |
| 1956 | R | 42.25 | +3.3 | 73 | 1 | | +2.8 |
| 1960 | R | 50.08 | −2.1 | 61 | 2 | ✓ | +3.6 |
| 1964 | D | 61.34 | +4.4 | 74 | 1 | | +1.5 |
| 1968 | D | 49.60 | +6.9 | 42 | 2 | ✓ | +0.6 |
| 1972 | R | 38.22 | +9.4 | 62 | 1 | | −4.5 |
| 1976 | R | 51.05 | +3.0 | 45 | 2 | | +3.2 |
| 1980 | D | 44.70 | −8.0 | 32 | 1 | | −2.9 |
| 1984 | R | 40.83 | +7.1 | 54 | 1 | | −4.3 |
| 1988 | R | 46.09 | +5.4 | 51 | 2 | ✓ | −3.2 |
| 1992 | R | 53.45 | +4.4 | 37 | 3 | | +3.8 |
| 1996 | D | 54.74 | +6.8 | 55 | 1 | | −1.1 |
| 2000 | D | 50.27 | +7.5 | 57 | 2 | ✓ | −3.7 |
| 2004 | R | 48.74 | +3.1 | 48 | 1 | | +2.1 |
| 2008 | R | 53.69 | +2.4 | 30 | 2 | ✓ | −1.9 |
| 2012 | D | 51.96 | +1.8 | 47 | 1 | | −0.7 |
| 2016 | D | 51.11 | +1.3 | 51 | 2 | ✓ | +0.8 |
| 2020 | R | 52.27 | −28.0 | 42 | 1 | | **−10.9** |
| **2024** | **D** | **49.25** | **+3.6** | **38** | **1** | **✓** | **+1.4** (out-of-sample) |

Three-way races (1968, 1992, 1996, 2000) use `Dem / (Dem + Rep)`. GDP values are from FRED GDPC1; approval is Gallup June.

### B.3 Coefficients (1948–2020)

| Term | Coef. | SE | t | p |
|---|---|---|---|---|
| Intercept | 40.09 | 3.80 | 10.56 | <0.001 |
| Q2 GDP growth (pp per pp) | 0.191 | 0.082 | 2.32 | 0.036 |
| June approval (pp per pt) | 0.267 | 0.061 | 4.41 | 0.001 |
| Consecutive terms | −0.44 | 0.72 | −0.61 | 0.552 |
| Open seat | −2.60 | 1.36 | −1.92 | 0.075 |

R² = 0.808, adj. R² = 0.753. Leave-one-out RMSE = 3.75pp. Durbin-Watson 1.82; no evidence of residual autocorrelation.

### B.4 2024 prediction

| | Contribution |
|---|---|
| Intercept | 40.09 |
| GDP: 0.191 × 3.59 | +0.69 |
| Approval: 0.267 × 38 | +10.15 |
| Terms: −0.44 × 1 | −0.44 |
| Open seat | −2.60 |
| **Predicted incumbent (Dem) share** | **47.89%** |
| Actual | 49.25% |
| Residual | +1.36pp |

### B.5 Sensitivity

| Specification | N | R² | LOOCV RMSE | GDP coef. | 2024 pred. | Residual |
|---|---|---|---|---|---|---|
| Full, 1948–2020 | 19 | 0.808 | 3.75 | 0.191 | 47.9 | +1.4 |
| Drop 2020 | 18 | 0.852 | 2.66 | 0.469 | 48.4 | +0.8 |
| Approval only | 19 | 0.684 | — | — | 48.1 | +1.2 |

2020's −28% Q2 GDP is 20 points below the next-lowest value (1980, −8.0%) and is the single most influential observation. Without it, GDP growth matters roughly 2.5× as much and the model fits better. The 2024 residual is inside the out-of-sample error under every specification.

---

## C. Part 2 — Decomposition

### C.1 Identity

For any unit (county, state, nation) between elections *a* and *b*:

```
ΔDem = share_a × (total_b − total_a)  +  (share_b − share_a) × total_b
```

The identity is exact. The first term holds the Democratic share fixed and varies turnout; the second holds turnout at its new level and varies share. The order of decomposition is a choice; the alternative (`share_b × Δtotal + Δshare × total_a`) gives slightly different splits. The version used weights the share effect by the *new* electorate.

### C.2 County panel

3,111 counties present in 2016, 2020, and 2024 after excluding Alaska. Swing is defined as the change in **margin**: `(dem_margin_2024 − dem_margin_2020) × 100`, in percentage points, positive toward Democrats. Margin swing is approximately twice the swing in Democratic share.

### C.3 Classification

For the 2,439 counties where `ΔDem < 0`:

| Class | Rule |
|---|---|
| Turnout-dominant | both components ≤ 0 and turnout component ≥ 60% of the loss |
| Share-dominant | both components ≤ 0 and share component ≥ 60% of the loss |
| Mixed | both components ≤ 0, neither ≥ 60% |
| Offsetting | components have opposite signs |

The 672 counties where Democrats gained votes are excluded from the classification. The 60% threshold is arbitrary and the results are sensitive to it:

| Threshold | Turnout-dominant | Share of loss | Share-dominant | Share of loss |
|---|---|---|---|---|
| 55% | 464 | 49% | 903 | 30% |
| 60% | 381 | 43% | 789 | 23% |
| 65% | 294 | 19% | 657 | 16% |

The classification should be read as a description of the distribution of component ratios, not as a point estimate of "how much was demobilization." The component regressions in D.3 are the better-identified version of the same question.

### C.4 Results

**National** (all 51 states, from raw returns):

| | 2016 → 2020 | 2020 → 2024 |
|---|---|---|
| Dem votes | 65.84M → 81.26M | 81.26M → 75.01M |
| Total votes | 136.49M → 158.48M | 158.48M → 155.21M |
| Dem raw share | 48.2% → 51.3% | 51.3% → 48.3% |
| ΔDem | +15.42M | −6.25M |
| Turnout component | +10.61M (69%) | −1.68M (27%) |
| Share component | +4.82M (31%) | −4.58M (73%) |

**County panel** (N = 3,111):

| | 2020 → 2024 | 2016 → 2020 |
|---|---|---|
| Shifted right | 2,792 (89.7%) | 1,594 (51.2%) |
| Median swing | −3.15pp | −0.13pp |
| Turnout-weighted mean swing | −4.94pp | — |

**Classification of 2,439 vote-losing counties:**

| Class | Counties | Dem votes lost | Share of loss |
|---|---|---|---|
| Turnout-dominant | 381 | −2.87M | 42.7% |
| Mixed | 406 | −1.85M | 27.5% |
| Share-dominant | 789 | −1.56M | 23.2% |
| Offsetting | 863 | −0.45M | 6.7% |

**States:** 51 of 51 swung right. Full table: `outputs/tables/state_decomposition_2020_2024.csv`.

### C.5 What the share component contains

The share component bundles (a) voters who switched from Democrat to Republican, (b) 2020 Democratic voters who abstained in 2024 while Republican voters did not, (c) new 2024 voters who leaned Republican, and (d) in-migration. County returns cannot separate these. The classification labels ("turnout-dominant" / "share-dominant") describe which term of the identity is larger, not which behavioral mechanism operated.

---

## D. Part 3 — County economic regression

### D.1 Specifications

All models are WLS weighted by 2020 county total votes. `swing_2024` is the margin swing from C.2.

- **Base (notebook 04):** `swing_2024 ~ log_income + college_share + white_nocollege + unemp_rate + dem_share_2020`, N = 3,110, nonrobust SEs.
- **M1 (notebook 05):** same, HC3 robust SEs, N = 2,817 (counties with complete QCEW covariates; 97.7% of 2020 votes).
- **M2:** M1 + `mfg_share_2016 + mfg_share_chg_2016_2024 + private_emp_pct_chg_2020_2024 + real_pay_pct_chg_2020_2024`.
- **Component models:** M2 right-hand side with `turnout_component / total_votes_2020 × 100` and `share_component / total_votes_2020 × 100` as outcomes (Democratic votes per 100 2020 voters).

### D.2 Why HC3

The base model's residuals have skew −1.6 and kurtosis 32 (Jarque-Bera 112,974). Nonrobust standard errors are unreliable under that distribution. Under HC3, the SEs on `log_income`, `unemp_rate`, and `dem_share_2020` roughly triple, and `dem_share_2020` loses significance (p = 0.03 → 0.44). The condition number (~1,080) indicates collinearity among `log_income`, `college_share`, `white_nocollege`, and `dem_share_2020`; individual coefficients should be read with that in mind, though the signs are stable across specifications.

### D.3 Coefficient tables

**Base and M1/M2** (`outputs/tables/covariates_swing_regression.csv`):

| | Base (N=3,110) | | M1 HC3 (N=2,817) | | M2 HC3 (N=2,817) | |
|---|---|---|---|---|---|---|
| | coef | SE | coef | SE | coef | SE |
| Intercept | 21.86 | 4.20 | 21.61 | 15.16 | 17.07 | 13.64 |
| log_income | −3.44 | 0.38 | −3.42 | 1.24 | −2.89 | 1.13 |
| college_share | 20.53 | 1.06 | 20.64 | 2.99 | 21.45 | 3.04 |
| white_nocollege | 16.41 | 0.59 | 16.48 | 2.75 | 14.91 | 2.64 |
| unemp_rate | −29.65 | 5.44 | −30.39 | 15.59 | −24.04 | 15.04 |
| dem_share_2020 | −1.46 | 0.69 | −1.58 | 2.04 | −2.61 | 1.99 |
| mfg_share_2016 | | | | | 2.70 | 1.37 |
| mfg_share_chg_2016_2024 | | | | | −0.009 | 0.037 |
| private_emp_pct_chg_2020_2024 | | | | | −0.075 | 0.029 |
| real_pay_pct_chg_2020_2024 | | | | | 0.059 | 0.052 |
| R² | 0.418 | | 0.422 | | 0.437 | |

**Standardized effects, M2** (coef × turnout-weighted SD; the table in the main report):

| Predictor | Wtd SD | Effect (pp) | 95% CI |
|---|---|---|---|
| log_income | 0.261 | −0.75 | [−1.33, −0.18] |
| college_share | 0.113 | +2.43 | [+1.75, +3.10] |
| white_nocollege | 0.177 | +2.63 | [+1.72, +3.55] |
| unemp_rate | 0.015 | −0.36 | [−0.79, +0.08] |
| dem_share_2020 | 0.165 | −0.43 | [−1.08, +0.21] |
| mfg_share_2016 | 0.079 | +0.21 | [+0.00, +0.43] |
| mfg_share_chg_2016_2024 | 1.963 | −0.02 | [−0.16, +0.13] |
| private_emp_pct_chg_2020_2024 | 6.706 | −0.50 | [−0.88, −0.13] |
| real_pay_pct_chg_2020_2024 | 4.374 | +0.26 | [−0.19, +0.70] |

**Component models, HC3** (`outputs/tables/covariates_component_regression.csv`), standardized effects in Dem votes per 100 2020 voters:

| Predictor | Turnout component | Share component |
|---|---|---|
| log_income | −0.47 | −0.44 |
| college_share | +1.02 | +1.14 |
| white_nocollege | +0.97 | +1.29 |
| unemp_rate | −0.35 | −0.23 |
| dem_share_2020 | **−1.69** | −0.24 |
| mfg_share_2016 | −0.07 | +0.08 |
| mfg_share_chg_2016_2024 | +0.04 | −0.02 |
| private_emp_pct_chg_2020_2024 | **+0.76** | −0.23 |
| real_pay_pct_chg_2020_2024 | −0.01 | +0.09 |
| R² | 0.510 | 0.445 |
| Weighted mean of outcome | −1.58 | −2.35 |

### D.4 Sign conventions

`swing_2024` is positive toward Democrats, so a positive coefficient means a smaller rightward shift. The main report's white non-college finding — positive coefficient, i.e. whiter non-college counties swung *less* right — follows directly and reverses a common 2016-era assumption. Marginal effects at the mean from the base model: +$10K median income → −0.57pp; +10pp college share → +2.05pp; +10pp white non-college → +1.64pp; +1pp unemployment → −0.30pp.

### D.5 Multi-cycle income gradient

Counties are assigned to quartiles of ACS 2020 median household income (N = 3,110; quartile cutpoints ≈ $45.6K, $52.7K, $61.3K). For each cycle, `swing_YYYY = (dem_share_YYYY − dem_share_2012) × 100` using raw Democratic share, and the quartile mean is weighted by that cycle's total votes.

| vs. Obama 2012 | Q1 | Q2 | Q3 | Q4 | Q4 − Q1 |
|---|---|---|---|---|---|
| Clinton 2016 | −5.8 | −6.1 | −4.5 | −0.8 | +5.0 |
| Biden 2020 | −6.3 | −4.3 | −1.8 | +3.1 | +9.4 |
| Harris 2024 | −9.2 | −6.4 | −4.1 | +0.7 | +9.9 |

No inferential test is applied to the gradient differences; the 2020 → 2024 change (+0.5pp) should be treated as no change. Table: `outputs/tables/county_multiyear_swing.csv`.

---

## E. Part 4 — Attribution gap and multilevel models

Notebooks `06_attribution_gap.ipynb` and `07_multilevel_model.ipynb`. Sample: CES 2024 respondents with a non-missing economy rating, party ID, and county QCEW match (N = 56,635; 2,653 counties; 49 states).

### E.1 Stage 1 — perceived on actual

WLS with `commonweight`, standard errors clustered by county. County "actual" measures are the Part 3 QCEW/ACS variables, standardized with population weights so one SD is a typical resident's experience.

| | County actual only | Party only | Both |
|---|---|---|---|
| real pay growth 2020–24 (z) | −0.104 (0.017) | | −0.027 (0.009) |
| private job growth 2020–24 (z) | +0.016 (0.011) | | +0.007 (0.008) |
| unemployment 2020 (z) | −0.031 (0.014) | | −0.067 (0.009) |
| `pid7c` | | −0.348 (0.004) | −0.348 (0.004) |
| R² | **0.006** | **0.338** | 0.341 |

Within party, the real-pay coefficient is −0.021 (Dem), −0.036 (Ind), −0.044 (Rep) with SEs of 0.012–0.022. Perception by party × county real-pay-growth quartile:

| | Q1 (fell most) | Q2 | Q3 | Q4 (rose most) |
|---|---|---|---|---|
| Democrats | +0.34 | +0.29 | +0.28 | +0.36 |
| Independents | −0.86 | −1.03 | −1.04 | −1.00 |
| Republicans | −1.31 | −1.34 | −1.38 | −1.43 |

### E.2 Partisan flip

Weighted mean of the economy item by party and wave (`outputs/tables/attribution_partisan_flip.csv`): 2016 D +0.43 / I −0.44 / R −0.65 / all −0.13; 2020 D −1.41 / I −0.83 / R +0.11 / all −0.71; 2024 D +0.32 / I −0.98 / R −1.37 / all −0.60.

### E.3 Attribution gap

`gap = perceived_econ − fitted(county actual only)`. Weighted mean zero, SD 1.37. Weighted mean gap by group: Dem +0.90, Ind −0.39, Rep −0.77; college +0.32, no degree −0.18; Fox viewers −0.53, MSNBC +1.15, CNN +0.64, newspaper +0.46, local TV +0.07, social-media-only −0.31, no news −0.30.

**Gap models** (WLS, `commonweight`, county-clustered; `outputs/tables/attribution_gap_models.csv`):

| | Party only | Media only | Party + media + controls |
|---|---|---|---|
| `pid7c` | −0.344 (0.004) | | −0.298 (0.005) |
| Fox | | −0.880 (0.022) | −0.320 (0.022) |
| MSNBC | | +1.022 (0.032) | +0.589 (0.030) |
| CNN | | +0.433 (0.028) | +0.161 (0.027) |
| local TV | | +0.057 (0.019) | +0.032 (0.017) |
| newspaper | | +0.528 (0.019) | +0.298 (0.016) |
| radio | | −0.060 (0.020) | −0.011 (0.017) |
| social media | | −0.094 (0.023) | −0.052 (0.022) |
| no news | | −0.219 (0.060) | −0.124 (0.053) |
| college | | | +0.258 (0.016) |
| white non-Hispanic | | | +0.161 (0.020) |
| county college share (z) | | | +0.500 (0.139) |
| R² | 0.333 | 0.183 | 0.400 |

Controls also include age, county log income, white non-college share, and 2020 Dem share (last two n.s.). Interaction model: `pid7c × Fox` = +0.087 (0.011); implied Fox effect −0.67 for strong Democrats, −0.41 for independents, −0.15 for strong Republicans. `pid7c × MSNBC` = −0.005 (n.s.).

### E.4 Switching models

Sample: 2024 respondents with `presvote_prior_party == "D"` and a 2024 major-party vote (N = 20,608, 1,919 counties). Logit via GLM-binomial with `commonpostweight` as frequency weights (normalized to N), county-clustered SEs. Weighted switch rate 6.4%, unweighted 3.0%: mean post-weight is 1.88 for switchers versus 0.84 for stayers, so the weighted level is sensitive to the weighting model. Switch rate by economy rating (weighted / unweighted): much worse 31.6% / 20.3% (N = 1,192); somewhat worse 11.1% / 7.0% (2,580); same 4.6% / 2.7% (3,798); somewhat better 1.7% / 0.8% (8,746); much better 1.5% / 0.4% (4,292). Terciles of the gap are not reported: with a five-valued item, the bottom tercile spans "much worse" through "about the same."

| | Gap only | + demographics | Full |
|---|---|---|---|
| `gap` | −1.032 (0.070) | −0.815 (0.083) | −0.827 (0.079) |
| `pid7c` | | +0.810 (0.048) | +0.826 (0.048) |
| college | | −0.372 (0.163) | −0.340 (0.167) |
| Fox | | | +1.868 (0.255) |
| MSNBC | | | −0.467 (0.322) |
| social media | | | −0.619 (0.220) |
| county real pay (z) | | | −0.011 (0.113) |
| county job growth (z) | | | +0.143 (0.087) |
| county unemployment (z) | | | +0.192 (0.107) |

Average marginal effects, full model: gap −1 point → +3.9pp on P(switch); gap +1 → −2.5pp; Fox 0→1 → +11.3pp; county real pay +1 SD → 0.000. Recalled-Trump mirror (N = 16,166): 2.3% switched to Harris; gap coefficient +0.849 (0.092), AME +2.1pp.

**Multilevel logit** (`BinomialBayesMixedGLM`, variational Bayes, county random intercept, unweighted): gap −0.956 (0.043), `pid7c` +0.819, Fox +1.637 (0.108), MSNBC −0.527, social −0.349, county real pay −0.104 (0.054); county random-effect SD 0.384 on the logit scale. Being unweighted, its intercept corresponds to the 3.0% unweighted base rate; slopes are comparable to the weighted single-level model, which is the check intended.

### E.5 Variance decomposition

`statsmodels.MixedLM`, REML, county random intercept, unweighted (weighting variables enter as covariates; fixed effects match the weighted notebook 06 estimates within ±0.05).

| Model | County var. | Residual var. | ICC |
|---|---|---|---|
| M0 null | 0.0897 | 1.806 | 0.047 |
| M1a + party, education, age, race | 0.0061 | 1.168 | 0.005 |
| M1 + individual media diet | 0.0047 | 1.095 | 0.004 |
| M2 + county economic record | 0.0038 | 1.095 | 0.003 |
| M3 + county composition + state FE | 0.0002 | 1.095 | 0.0001 |

M1a is the relevant ceiling for a county-level media-environment variable (which would act partly through individual media choice): county-effect SD 0.078 scale points.

### E.6 Cross-level interactions (M3 + `pid7c × county`)

| Term | Coef. | SE | p |
|---|---|---|---|
| `pid7c` | −0.305 | 0.002 | <0.001 |
| `pid7c × county real pay (z)` | −0.005 | 0.002 | 0.014 |
| `pid7c × county white non-college (z)` | −0.022 | 0.003 | <0.001 |
| `pid7c × county college share (z)` | −0.015 | 0.003 | <0.001 |
| `pid7c × county Dem share 2020 (z)` | +0.003 | 0.004 | 0.403 |

Implied strong-Rep-minus-strong-Dem gap (6 × slope): white non-college −2 SD → −1.56, +2 SD → −2.09.

**Random slope for party ID is not identified.** With `pid7` centred at independent, the random-slope model does not converge and the LR statistic against the intercept-only model is negative. At a median of 6 respondents per county there is insufficient within-county variation in party ID. The cross-level interactions are the usable evidence.

### E.7 County empirical-Bayes gap

Random intercepts from M1 (`data/processed/county_attribution_gap.csv`, 2,653 counties). SD 0.017 versus 0.755 for raw county means — heavy shrinkage; for counties with 1–5 respondents the EB SD is 0.007. Regressed on county covariates (respondent-weighted, HC3): R² 0.23, all coefficients |b| < 0.01. Regressed as a predictor of the county margin swing: −3.40 (SE 8.68, p = 0.70) bivariate; +1.52 (6.37, p = 0.81) with Part 3 controls. No detectable county-level relationship.

### E.8 Prices item

Notebook 06 §8. Weighted distribution of `CC24_303`: increased a lot 56.3%, increased somewhat 31.7%, stayed the same 8.5%, decreased somewhat 3.0%, decreased a lot 0.6%.

**Partisanship of the three perception items** (`outputs/tables/attribution_prices_partisan.csv`; all statistics weighted by `commonweight`):

| Item (sign) | N | All | Dem | Ind | Rep | Dem − Rep | SD | Gap in SDs | corr. with `pid7` | R² on `pid7` |
|---|---|---|---|---|---|---|---|---|---|---|
| Nation's economy (+ = better) | 56,635 | −0.59 | +0.32 | −0.98 | −1.37 | +1.69 | 1.33 | **1.27** | −0.58 | 0.338 |
| Prices (+ = rose more) | 56,526 | +1.40 | +1.09 | +1.47 | +1.69 | −0.60 | 0.81 | **0.74** | +0.34 | 0.112 |
| Own household income (+ = better) | 56,561 | −0.13 | +0.16 | −0.32 | −0.36 | +0.51 | 0.95 | **0.54** | −0.25 | 0.062 |

The prices scale is compressed (88% in two of five categories), so the R² ratio across items (0.11 vs 0.34) overstates how much less partisan prices are; the SD-scaled gap (0.74 vs 1.27) is the fairer comparison. Direction versus degree, by party:

| | Rose (any) | Rose "a lot" | Same | P("a lot" \| rose) |
|---|---|---|---|---|
| Dem | 80.1% | 35.2% | 14.3% | 43.9% |
| Ind | 89.6% | 61.5% | 7.1% | 68.6% |
| Rep | 95.4% | 75.9% | 3.1% | 79.5% |

**Prices → economy rating, within party** (WLS, `commonweight`, county-clustered): slope −0.530 (0.020) Dem, −0.543 (0.040) Ind, −0.575 (0.036) Rep; R² 0.14–0.17. Pooled: `pid7c` alone R² 0.338; `pid7c + perceived_prices` 0.439; `pid7c × perceived_prices` interaction +0.000 (0.007).

**Switching with prices** (`outputs/tables/attribution_prices_switching.csv`; recalled-Biden sample with a prices response, N = 20,583; specification as E.4 full model):

| | With economy gap | Without |
|---|---|---|
| `gap` | −0.696 (0.097) | — |
| `perceived_prices` | +0.450 (0.161) | +0.980 (0.143) |

AME of one step more inflation reported: +1.9pp with the gap held fixed, +5.1pp without. AME of the gap one step worse, prices held fixed: +3.1pp (was +3.9pp before prices entered). Switch rate by prices response (weighted): increased a lot 12.8% (N = 6,292); increased somewhat 3.6% (10,023); same 2.2% (2,957); decreased somewhat 1.0% (1,257); decreased a lot 2.1% (54, too few to read). The "a lot" versus "somewhat" margin that carries the switching effect is also the margin on which the parties differ most, so the reverse-causation caveat in F.9 applies to this result with only modestly less force than to the economy rating.

**County component.** Each item on county economic record + composition (cluster SEs): R² 0.048 (economy), 0.021 (prices), 0.012 (household income); real-pay coefficients 0.005, 0.002, −0.004 with SEs of 0.008–0.011.

### E.9 Local news environment

Notebook 07 §1b, §2, §5b. CES 2024 respondents by county news environment: 547 in 112 news deserts, 8,003 in 1,253 single-outlet counties, 48,085 in 1,288 counties with 2+ outlets; 8,188 in nonmetro counties. Among recalled Biden voters: 164 in deserts, 2,073 in single-outlet counties.

**Media diet by environment** (`outputs/tables/multilevel_news_media_diet.csv`, unweighted shares, past 24 h):

| | N | Newspaper | Local TV | Fox | MSNBC | CNN | Social | No news |
|---|---|---|---|---|---|---|---|---|
| Desert | 547 | 0.263 | 0.406 | 0.168 | 0.099 | 0.137 | 0.792 | 0.049 |
| Single outlet | 8,003 | 0.272 | 0.435 | 0.194 | 0.088 | 0.116 | 0.817 | 0.034 |
| 2+ outlets | 48,085 | 0.340 | 0.458 | 0.170 | 0.131 | 0.157 | 0.810 | 0.027 |

Net of `pid7c`, college, age, race, nonmetro, and county composition (LPM, county-clustered), the desert coefficient is −0.027 (0.021) newspaper, −0.026 (0.021) local TV, −0.015 (0.015) Fox, −0.025 (0.020) social, +0.018 (0.008) no news. Single-outlet coefficients are all |b| < 0.01.

**Variance decomposition with news environment** (`outputs/tables/multilevel_news_variance.csv`; MixedLM, county random intercept):

| Model | County var. | ICC | Share of M1a county var. explained |
|---|---|---|---|
| M1a demographics + party | 0.0061 | 0.0052 | — |
| M1a + nonmetro only | 0.0054 | 0.0046 | 12% |
| M1a + RUCC (9 categories) only | 0.0043 | 0.0037 | 30% |
| M1a + news variables only | 0.0054 | 0.0046 | 12% |
| M1a + news + nonmetro | 0.0051 | 0.0044 | 16% |
| M1a + news + composition | 0.0012 | 0.0010 | 81% |
| M3 (composition + state FE) | 0.0002 | 0.0001 | 97% |
| M3 + news environment | 0.0001 | 0.0001 | 98% |

News variables = `news_desert + single_outlet + log_outlets_pc_z`. The news variables and `nonmetro` overlap heavily: each explains ~12% alone, both together 16%. The full rural-urban code explains more (30%) than the news variables, which is the expected pattern if what the news variables are picking up is mostly rurality.

**Direct fixed effects, M3 + news:** `news_desert` +0.041 (0.050), `single_outlet` +0.007 (0.016), `log_outlets_pc_z` +0.001 (0.006), `nonmetro` +0.019 (0.018). For scale, `fox` −0.361, `newspaper` +0.277.

**Cross-level interactions** (added to the E.6 model): `pid7c × news_desert` +0.022 (0.020, p = 0.27), `pid7c × single_outlet` +0.008 (0.006, p = 0.22), `pid7c × nonmetro` −0.004 (0.007, p = 0.51). Implied strong-Rep-minus-strong-Dem gap: −1.83 (2+ outlets, metro), −1.70 (desert, metro), −1.86 (2+ outlets, nonmetro), −1.72 (desert, nonmetro). The white-non-college interaction (−0.022, p < 0.001) is unchanged by the news terms.

**Reduced form, first stage, IV** (`outputs/tables/multilevel_news_switching.csv`, `multilevel_news_iv.csv`; recalled-Biden sample, N = 20,608, unweighted, county-clustered; controls as E.4 full model plus composition and nonmetro):

| | LPM coef. | SE | p | Logit coef. | SE | p |
|---|---|---|---|---|---|---|
| Reduced form: `news_desert` → switch | +0.024 | 0.018 | 0.18 | +0.741 | 0.448 | 0.10 |
| `single_outlet` | +0.001 | 0.004 | 0.90 | +0.066 | 0.183 | 0.72 |
| `log_outlets_pc_z` | +0.002 | 0.002 | 0.27 | +0.123 | 0.068 | 0.07 |

First stage (gap on instruments + controls): `news_desert` −0.078 (0.087), `single_outlet` +0.024 (0.029), `log_outlets_pc_z` +0.002 (0.010). **Cluster-robust F on excluded instruments = 0.64; partial R² = 0.00008.** 2SLS LPM estimate of the gap effect: −0.114 (SE 0.123), against OLS −0.027 (0.0015). The 2SLS estimate is not interpretable; it is reported so the weak-instrument result is on the record rather than omitted.

**Definition robustness** (`outputs/tables/multilevel_news_definition_robustness.csv`; each desert variable entered alone with the same controls):

| Definition | N in switch sample | Direct on perception | `pid7c` × desert | Reduced form (LPM) | First stage |
|---|---|---|---|---|---|
| Count-based (0 outlets) | 164 | +0.009 (0.096) | +0.006 (0.020) | +0.020 (0.017), p = 0.26 | −0.090 (0.083) |
| Medill "Desert" label | 163 | −0.068 (0.093) | +0.027 (0.020) | +0.002 (0.015), p = 0.90 | −0.126 (0.095) |
| Medill "Watchlist" label | 118 | −0.096 (0.100) | +0.014 (0.021) | −0.008 (0.013), p = 0.57 | −0.023 (0.100) |

All null under every definition. The reduced-form desert → switching association, which reaches p = 0.10–0.18 under the count-based definition when entered alongside the other news terms, falls to p = 0.90 under Medill's label; it is definition-dependent noise.

---

## F. Limitations

1. **Ecological inference.** All Part 2–3 findings are about counties. A positive county-level coefficient on `white_nocollege` does not establish that white non-college *individuals* behaved differently; it establishes that counties with more of them did.
2. **No causal identification.** Every regression is descriptive. Nothing here distinguishes economic composition causing the swing from economic composition proxying for culture, media environment, or partisanship.
3. **The share component is a residual.** See C.5. "Persuasion" appears in the report as shorthand for the share component, not as a measured quantity.
4. **The 2020 baseline is an outlier.** Turnout losses in Democratic strongholds are partly the unwinding of the 2020 surge; the 2016 → 2020 rows are provided so the reader can judge how much.
5. **ACS vintage.** County economic characteristics are 2016–2020 averages. Conditions in 2024 differed in ways the 2020 file cannot capture; the QCEW variables partially address this for employment and pay but not for income distribution or education.
6. **Small-N fundamentals model.** Nineteen observations and four predictors. Two predictors are not significant. The model's out-of-sample error (3.75pp) is larger than most of the residuals it is asked to interpret.
7. **Third-party votes.** Parts 2–3 use raw shares over all votes cast. Rightward "swing" therefore includes movement to third parties, not only to the Republican column.
8. **Suppression.** BLS suppression removes 6–9% of counties from the extended regression, disproportionately small single-employer counties.
9. **Reverse causation in the switching model.** The economy rating is pre-election and the vote post-election, but a respondent who had already decided to switch would rate the economy badly because of it. The gap → switching association is consistent with misattribution causing switching and with the reverse. Panel data with perception measured before the decision, or an instrument for perception, is required to separate them.
10. **Media diet is self-selected.** Fox/MSNBC coefficients net of party ID are associations, not exposure effects.
11. **Unweighted mixed models.** MixedLM and BayesMixedGLM take no survey weights. Fixed effects match the weighted single-level estimates closely, but the variance components are model-based.
12. **Few respondents per county.** The random slope for party ID is not identified; EB county effects are heavily shrunk; any county-level test has low power outside the ~600 counties with 20+ respondents.
13. **Opt-in panel.** CES is a matched opt-in sample, not a probability sample. Its reported two-party vote tracks the actual result within 1pp in each wave, but that validates the weights for vote share, not for perception items.
14. **Local news data provenance.** The Medill county inventory comes from an undocumented backend rather than a published file. It reproduces the site's headline counts exactly, but its definitions (what counts as an outlet, how "active" is determined) are Medill's and are documented only in their methodology page. The 2025 inventory is a snapshot taken after the 2024 election; a county's news environment during the campaign is assumed to be the same.
15. **News-desert sample size.** 547 CES respondents live in the 112 news-desert counties with data; 164 of them are recalled Biden voters. The null results in E.9 have point estimates near zero, not merely wide intervals, but a desert-specific effect of a few points on switching would not be detectable.

---

## G. Reproducibility

### G.1 Environment

Python 3.8 virtual environment at `.venv`; dependencies in `requirements.txt`. Register the kernel once:

```bash
python -m ipykernel install --user --name dnc-autopsy --display-name "Python (dnc-autopsy)"
```

### G.2 Pipeline

| Step | Command / notebook | Reads | Writes |
|---|---|---|---|
| 1 | `python src/data_collection/fred_pull.py` | FRED API | `data/raw/fred/*.csv` |
| 2 | manual Dataverse download | — | `data/raw/mit_election_lab/countypres_2000-2024.csv` |
| 3 | `python src/data_collection/mit_pull.py` | step 2 | `data/raw/mit_election_lab/county_returns.csv` |
| 4 | `python src/data_collection/bls_qcew_pull.py` | BLS | `data/raw/bls_qcew/*.csv` |
| 5 | `02_fundamentals_model.ipynb` | step 1 | `data/processed/fundamentals_base.csv`, tables, figure |
| 6 | `03_demobilization_analysis.ipynb` | step 3 | `data/processed/county_decomposition.csv`, state table, figures |
| 7 | `04_populism_premium.ipynb` | step 6, Census API | `data/processed/county_economic_profile.csv`, tables, figures |
| 8 | `05_county_covariates.ipynb` | steps 1, 4, 6, 7 | `data/processed/county_covariates.csv`, tables, figure |
| 9 | `python src/data_collection/ces_pull.py` | Dataverse | `data/raw/ces/ces_{2016,2020,2024}.csv`, `ces_2016_2024_core.csv`, guide PDFs |
| 10 | `06_attribution_gap.ipynb` | steps 8, 9 | `data/processed/ces_2024_attribution.csv`, tables, figures |
| 11 | `python src/data_collection/news_deserts_pull.py` | LNI backend | `data/raw/news_deserts/lni_county_summary.csv`, `lni_outlets_2025.csv`, `ca_bundle.pem` |
| 12 | `07_multilevel_model.ipynb` | steps 10, 11 | `data/processed/county_attribution_gap.csv`, tables, figure (≈10 min; the VB mixed logit dominates) |

Execute notebooks non-interactively with the project kernel:

```bash
jupyter nbconvert --to notebook --execute notebooks/0N_*.ipynb --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy
```

### G.3 Keys

Copy `.env.example` to `.env` and set `FRED_API_KEY` and `CENSUS_API_KEY`. Never commit `.env`. The CES and BLS pulls need no key.

---

## H. Next steps

Part 4 established that perception is disconnected from local reality and travels with media diet and with vote switching; it did not establish direction. The local news environment was the planned instrument and, as E.9 shows, it does not move perception (first-stage F = 0.64) — the variance ceiling in E.5 ruled it out in advance and the data confirmed it. Two things would still move identification:

1. **Panel data.** The CES has a panel component (2020 → 2022 → 2024 re-interviews). Perception measured in 2022, before the 2024 decision, breaks the simultaneity in E.4 directly and is now the only realistic route. Requires the panel file, which is a separate Dataverse release.
2. **A local price measure.** The prices item (E.8) is the least partisan perception in the survey and predicts switching net of the economy rating, but there is nothing to set it against. BLS publishes CPI only for large metro areas; the closest county-level options are the BEA regional price parities (annual, by metro/non-metro portion of state) or rent from ACS 1-year files. Either would allow a prices *gap* — perceived minus measured — and a test of whether that gap, rather than the level, is what moved votes.

The reduced-form association between living in a news desert and switching (+2.4pp, p = 0.18 under the count-based definition) was initially flagged as a loose end; it does not survive Medill's desert definition (p = 0.90) and should not be pursued.

CDC WONDER overdose mortality remains a planned Part 3 covariate; nothing in Part 4 depends on it.
