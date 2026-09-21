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

### A.7 CES 2020–2022–2024 Panel Survey

**Source:** Harvard Dataverse `doi:10.7910/DVN/CETPVT` (published January 2026), file `merged_recontact_2024_vv.csv` (56 MB, 6,175 rows × 2,229 columns) and `Recontact_Survey_Guide_2020_2022_2024.pdf`. No guestbook.
**Script:** `src/data_collection/ces_panel_pull.py` → `data/raw/ces_panel/ces_panel_long.csv` (one row per respondent-wave) and `ces_panel_wide.csv` (one row per respondent).

**Design.** 2020 CES respondents re-interviewed in 2022 and 2024 by YouGov; matched to the Catalist voter file for 2020 and the TargetSmart file for 2022 and 2024 (matches performed August 2023 and August 2025). 4,015 completed the 2024 post-election wave.

**Variable naming.** Demographics carry a wave suffix (`pid7_20`, `educ_22`, `countyfips_24`); question items keep their `CCyy_` prefix. **The panel's 2024 economy item is `CC24_302`, not `CC24_301` as in the 2024 common content**; household income is `CC24_303` and prices `CC24_304` (guide p. 27). The 2020 gender item is `gender` with no suffix. Verified against the guide, not assumed from A.5.

**Vote.** `CC20_410` (asked in 2020) and `CC24_410` (asked in 2024), Democrat = 1 and Trump = 2 in both. Weighted two-party Democratic share of reported vote: 52.0% (2020) and 49.0% (2024) against actual 52.3 / 49.25. Recalled 2020 vote (`presvote20post_22`, `presvote20post_24`) is retained but not used; the contemporaneous item replaces it.

**Validated turnout.** `CL_2020gvm` (Catalist; any value = voted, missing = no record), `TS_g2022` and `TS_g2024` (TargetSmart; 1–6 = voted by method, 7 = did not vote, missing = not matched). Recoded to `voted_validated_{year}`: 1 voted, 0 matched but no vote, missing unmatched. 4,835 panelists have a 2024 match.

**Weights.** `commonweight_24` (all 6,175, adults) for perception items; `commonpostweight_24` (4,015, answered both 2024 waves) for anything using the 2024 vote; `vvweight_22` / `vvweight_post_22` for registered-voter targets (guide p. 10).

**Attrition** (guide p. 11, unweighted): relative to the 2020 base, the 2024 panel is older (mean age 55.9 vs 48.4 in 2020), more college-educated (41% vs 37%), more retired (30% vs 21%), and more often a validated 2020 voter (84% vs 71%). Democrat share 47% vs 48%, Republican 37% vs 34% — no meaningful partisan differential.

**Movers.** 741 panelists (12.0%) report a different county in 2024 than in 2020. The 2024 county's economic record is used; movers are flagged, not dropped.

### A.8 USAspending — county obligations under IIJA and ARPA

**Source:** USAspending API, `POST /api/v2/search/spending_by_geography/` with `geo_layer: county`, filtered by Disaster Emergency Fund Code and time period. No key.
**Script:** `src/data_collection/usaspending_pull.py` → `data/raw/usaspending/county_delivery.csv` (3,232 counties).

**Programs.** IIJA (P.L. 117-58) is DEFC `1` (non-emergency) and `Z` (emergency), window 2021-11-15 to 2024-11-05: $319.9B by place of performance. ARPA (P.L. 117-2) is DEFC `V`, window 2021-03-11 to 2024-11-05: $620.7B. The Inflation Reduction Act and CHIPS carry no DEFC (regular appropriations and tax expenditure) and cannot be isolated; the Clean Investment Monitor's facility data requires ClimateDeck registration and confirms only state and congressional-district granularity, so it is not used.

**Place of performance vs. recipient location.** Both scopes are pulled. Place of performance credits formula funds to the state agency's county (the state capital) and DOE laboratory funding to the lab's county; recipient location has the mirror problem. Place of performance is used, per capita, with the top 1% winsorized (IIJA at $17,503 per capita, ARPA at $18,131) and log1p-transformed. Los Alamos ($14.2B IIJA), Anderson County TN ($9.0B), and Loving County TX (64 residents) are the kind of artifact the winsorizing addresses; models are also re-run dropping the top 5% of counties per capita.

**Obligated is not built.** The figures are obligations, not outlays or completed projects.

**Distribution.** IIJA per capita is roughly flat across partisanship (population-weighted mean $1,023 in the most Republican tercile of counties, $861 in the most Democratic; correlation with 2020 Dem share −0.04). ARPA is not ($503 vs $1,843; correlation +0.39, with log population +0.23) — the State and Local Fiscal Recovery formula and other ARPA streams favored dense, high-unemployment counties. Models therefore include county composition, the RUCC rural-urban code, and log population.

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

AME of one step more inflation reported: +1.9pp with the gap held fixed, +5.1pp without. AME of the gap one step worse, prices held fixed: +3.1pp (was +3.9pp before prices entered). Switch rate by prices response (weighted): increased a lot 12.8% (N = 6,292); increased somewhat 3.6% (10,023); same 2.2% (2,957); decreased somewhat 1.0% (1,257); decreased a lot 2.1% (54, too few to read). The "a lot" versus "somewhat" margin that carries the switching effect is also the margin on which the parties differ most, so the reverse-causation caveat in J.9 applies to this result with only modestly less force than to the economy rating.

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

## F. Part 5 — Panel

Notebook `08_panel_analysis.ipynb`. Party identification is fixed at its 2020 value throughout (pre-treatment for everything that follows). Perception items recoded as in E (+2 … −2; prices +2 = rose a lot).

### F.1 Within-person flip

Weighted (`commonweight_24`) mean perceived economy by 2020 party ID (`outputs/tables/panel_partisan_flip.csv`): 2020 D −1.52 / I −0.98 / R +0.08 / all −0.80; 2022 D −0.49 / I −1.18 / R −1.71 / all −1.10; 2024 D +0.34 / I −0.81 / R −1.36 / all −0.54. Mean within-person change 2020→2024: Democrats +1.88, independents +0.22, Republicans −1.43. Share moving ≥ 2 points toward own-party incumbent: Democrats 60.8%, Republicans 45.7%.

### F.2 First differences

`Δperc_2020→2024 ~ county real pay (z) + job growth (z) + unemployment (z)`, WLS with `commonweight_24`, county-clustered, N = 5,766. R² 0.010 (county actual only), 0.421 (+ 2020 party ID). Real pay: −0.199 (0.078) alone, −0.036 (0.061) with party. Within party: Democrats −0.053 (0.065), independents +0.119 (0.150), Republicans −0.114 (0.080); within-party R² 0.006–0.009.

### F.3 Timing

Sample: `presvote_post_party_2020 == "D"` and `presvote_post_party_2024 ∈ {D, R}`, N = 1,684, switchers = 39 (2.3% unweighted, 4.1% weighted with `commonpostweight_24`). By 2022 rating (`outputs/tables/panel_timing_by_rating.csv`):

| 2022 rating | N | Switched | Unweighted | Weighted |
|---|---|---|---|---|
| Much worse | 240 | 19 | 7.9% | 15.9% |
| Somewhat worse | 611 | 13 | 2.1% | 1.5% |
| Same | 337 | 6 | 1.8% | 3.9% |
| Somewhat better | 362 | 0 | 0.0% | 0.0% |
| Much better | 76 | 0 | 0.0% | 0.0% |

By 2020 rating (given under Trump): much worse 1.5% (18/1,175), somewhat worse 3.6% (15/416), same 5.5% (3/55), better 9.1% (2/22) — Biden voters who rated Trump's economy well were marginally more likely to switch, but on 5 events.

**Models** (`outputs/tables/panel_timing_models.csv`; logit via GLM-binomial, `commonpostweight_24` as frequency weights normalized to N, county-clustered; N = 1,602 with complete covariates, 36 events):

| | Bivariate | + `pid7_20` | + college, age | + 2020 rating | 2020→22 change |
|---|---|---|---|---|---|
| `perc_2022` | −1.273 (0.583) | −1.282 (0.576) | −1.401 (0.603) | −1.440 (0.665) | |
| `d_perc_20_22` | | | | | −0.820 (0.321) |
| `perc_2020` | | | | +0.395 (0.431) | |
| `pid7_20` | | −0.071 (0.158) | −0.225 (0.246) | −0.238 (0.239) | −0.194 (0.223) |
| college | | | −1.416 (0.608) | −1.445 (0.556) | −1.379 (0.573) |
| age (z) | | | −1.036 (0.228) | −0.988 (0.225) | −0.904 (0.229) |

Unweighted `perc_2022` coefficients for the first three specifications: −1.16 (0.22), −1.13 (0.23), −1.10 (0.22). AME of one step worse in 2022: +0.083 (bivariate), +0.083 (+ party), +0.080 (+ demographics), +0.082 (net of 2020 rating); AME of one step worse in 2020: −0.012; AME of a one-step fall 2020→2022: +0.040.

**Prices 2022** (cross-tab only): rose a lot 3.2% switched (32/986), rose somewhat 0.3% (2/647), same 8.8% (3/34), fell somewhat 22.2% (2/9), fell a lot 0/1. A weighted logit of this item returns a negative coefficient driven by the 5 switchers in the 44-person tail (weighted switch rate in the "fell somewhat" cell: 85%); not reported as an estimate.

**2022 media** (added to the + demographics model): Fox +2.213 (0.926), on 2 switchers among 38 Biden-voting Fox viewers; MSNBC +0.128 (0.528). Not evidence.

### F.4 Validated turnout

Sample: reported 2020 major-party vote and a 2024 voter-file match. Biden 2020: 2,495 matched, 97 with no validated 2024 vote (3.9% unweighted, 3.1% weighted). Trump 2020: 1,957 matched, 83 (4.2%, 3.3%). Among Biden 2020 voters by 2022 rating: much worse 9.0% (31/345), somewhat worse 3.6% (33/928), same 3.5% (17/481), somewhat better 1.7% (9/536), much better 2.8% (3/108). Logit, no validated 2024 vote ~ `perc_2022 + pid7_20 + college + age_z` (`outputs/tables/panel_validated_nonvoting.csv`): `perc_2022` −0.789 (0.366, p = 0.031).

**Full 2024 outcome** for the 3,064 who reported a Biden vote in 2020 (`data/processed/panel_biden2020_outcomes.csv`): Harris 1,617; no 2024 post-wave response 1,280; no validated 2024 vote 97; other candidate 37; Trump 33. Six respondents self-reported a Trump vote but have no validated 2024 vote on file and are classified as non-voters. Among the 1,784 with a known outcome, weighted: Harris 92.9%, Trump 2.9%, other 1.0%, no vote 3.3%.

---

## G. Part 6 — Bottom quartile and delivery

Notebook `09_bottom_quartile_and_delivery.ipynb`.

### G.1 Bottom quartile by composition

Q1 = poorest quartile of the 3,110-county panel by ACS 2020 median household income (778 counties, 5.5% of 2024 votes; Q2 12.7%, Q3 21.2%, Q4 60.6%). Within Q1, terciles of nonwhite share (1 − `white_nh_share`). Turnout-weighted change in Democratic share versus Obama 2012 (`outputs/tables/q1_by_composition.csv`, `all_by_composition.csv`):

| | Counties | Share of Q1 votes | Nonwhite | White non-college | 2016 | 2020 | 2024 | 2020→24 |
|---|---|---|---|---|---|---|---|---|
| Q1 mostly white | 260 | 26.9% | 0.06 | 0.79 | −9.60 | −9.10 | −10.69 | −1.58 |
| Q1 mixed | 259 | 31.1% | 0.29 | 0.60 | −6.28 | −6.23 | −8.37 | −2.11 |
| Q1 heavily nonwhite | 259 | 42.0% | 0.61 | 0.33 | −3.23 | −4.59 | −8.87 | −4.26 |
| All mostly white | 1,037 | 9.9% of all | 0.06 | 0.75 | −9.64 | −7.24 | −8.28 | −1.08 |
| All mixed | 1,036 | 29.3% | 0.18 | 0.62 | −4.68 | −0.40 | −1.50 | −1.13 |
| All heavily nonwhite | 1,037 | 60.9% | 0.48 | 0.40 | −0.48 | +2.33 | −0.87 | −3.23 |

Largest Q1 counties by 2024 votes: Bronx NY (nonwhite 0.91; 2024 vs 2012 −18.1), Hidalgo TX (0.94; −22.3), Orleans LA (0.69; +1.9), Cameron TX (0.91; −18.3), Caddo LA, Hinds MS, Doña Ana NM, Richmond GA.

### G.2 Individual income, county income, and ethnicity

CES 2024 recalled-Biden voters with a 2024 major-party vote, N = 20,608, `commonpostweight` (`outputs/tables/switch_by_individual_income.csv`, `switch_by_county_income.csv`, `switch_by_race.csv`, `switch_by_race_x_income.csv`). `faminc` bands: <$30k = codes 1–3, $30–50k = 4–5, $50–100k = 6–9, $100–200k = 10–12, $200k+ = 13–16; 97 (declined) dropped. Race: `hispanic == 1` → Hispanic, else `race == 1` White, `race == 2` Black, else Other.

| Individual income | N | Switch (wtd) | Perceived economy (wtd) |
|---|---|---|---|
| <$30k | 3,656 | 7.1% | +0.13 |
| $30–50k | 3,266 | 6.0% | +0.30 |
| $50–100k | 6,340 | 6.3% | +0.45 |
| $100–200k | 4,564 | 6.3% | +0.73 |
| $200k+ | 1,377 | 6.4% | +0.86 |

County income quartile: Q1 7.2% (926), Q2 5.7%, Q3 6.7%, Q4 6.4%. Cross-level: county Q1 × individual <$50k 5.3% (N = 512); Q1 × $50k+ 9.9% (414); Q4 × <$50k 6.4% (3,453); Q4 × $50k+ 6.4% (9,001).

| Race/ethnicity | N | Switch (wtd) | Perceived economy |
|---|---|---|---|
| Hispanic | 1,890 | 10.5% | +0.20 |
| Other | 1,314 | 7.1% | +0.41 |
| White | 14,423 | 5.8% | +0.62 |
| Black | 2,981 | 4.7% | +0.15 |

Race × income (weighted switch): Hispanic 13.6% / 6.6% / 10.8% / 11.4% / 6.9% across the five bands (N 368 / 342 / 604 / 377 / 103); White 5.7 / 6.4 / 5.0 / 6.0 / 6.9; Black 4.8 / 4.2 / 6.2 / 3.7 / 5.1.

Logit, county-clustered: income (16-band code) alone −0.013 (0.020); with Hispanic, Black, `pid7c`, college, age: income −0.008 (0.026), Hispanic +0.588 (0.238), Black +0.161 (0.203); adding county Q1 and log county income: income −0.005 (0.026), Hispanic +0.587 (0.239), county Q1 −0.279 (0.452), log county income −0.315 (0.387).

Panel (contemporaneous, unweighted, events in parentheses): by 2020 income <$30k 3.3% (11), $30–50k 2.8% (8), $50–100k 1.7% (9), $100–200k 1.6% (5), $200k+ 4.9% (3); Hispanic 0.0% (0 of 38), White 2.3% (24 of 1,066), Black 2.9% (9 of 311). Uninformative on the ethnic finding.

### G.3 Delivery

`log_iija_pc`, `log_arpa_pc` = log1p of winsorized per-capita obligations, standardized. Composition = `log_income + college_share + white_nocollege + dem_share_2020`; urban = `C(rucc) + log(population)`. Tables in `outputs/tables/delivery_models.csv`.

**(i) County margin swing 2020→24** (WLS, 2020 turnout weights, HC3; notebook 05 M2 controls; N = 2,913; R² 0.434 → 0.451 with delivery):

| Specification | IIJA pp per SD | ARPA pp per SD |
|---|---|---|
| Part 3 controls | +0.548 (0.238) | +0.382 (0.172) |
| + RUCC + log population | +0.501 (0.227) | +0.433 (0.170) |
| + RUCC + log pop, top 5% per capita dropped (N = 2,653) | +0.546 (0.292) | +0.778 (0.301) |

**(ii) Perceived economy, CES 2024** (WLS, `commonweight`, county-clustered, N = 56,631):

| Specification | R² | IIJA | ARPA |
|---|---|---|---|
| County actual + delivery | 0.020 | −0.025 (0.022) | +0.152 (0.015) |
| + party ID | 0.342 | +0.003 (0.014) | +0.044 (0.010) |
| + county composition | 0.345 | +0.015 (0.013) | +0.003 (0.011) |
| + RUCC + log population | 0.346 | +0.013 (0.013) | +0.002 (0.010) |

Within party, full controls: Democrats IIJA +0.037 (0.020), ARPA +0.004 (0.016); independents −0.009 (0.039), −0.045 (0.027); Republicans −0.007 (0.017), +0.016 (0.014).

**(iii) Switching**, notebook 06 full model + delivery + composition + urban (N = 20,608): IIJA −0.089 (0.125), ARPA −0.128 (0.123); gap −0.814 (0.078).

**(iv) Panel within-person change 2020→24** (WLS, `commonweight_24`, county-clustered, N = 5,772): delivery + party: IIJA +0.110 (0.069), ARPA +0.095 (0.041); + composition + urban: IIJA +0.134 (0.076), ARPA +0.019 (0.048).

The ARPA association with perception in the under-controlled specifications is composition; ARPA per capita correlates +0.39 with 2020 Democratic share. The county-swing effect survives the same controls.

**(v) Components** (`outputs/tables/delivery_components.csv`; same specification as the county-swing model with full controls, N = 2,913; components per 100 2020 voters as in D.1; vote changes as % of 2020 votes):

| Outcome | IIJA per SD | ARPA per SD | R² |
|---|---|---|---|
| Margin swing (pp) | +0.501 (0.227) | +0.433 (0.170) | 0.480 |
| Turnout component | −0.199 (0.226) | +0.189 (0.142) | 0.548 |
| Share component | +0.181 (0.107) | +0.204 (0.073) | 0.485 |
| Total votes, % change | −0.398 (0.296) | +0.277 (0.223) | 0.511 |
| Democratic votes, % change | −0.052 (0.412) | +0.557 (0.278) | 0.478 |
| Republican votes, % change | −1.127 (0.410) | −0.229 (0.488) | 0.235 |

Neither program predicts the turnout component or total turnout change. IIJA's swing effect is carried by lower Republican vote growth; ARPA's by higher Democratic vote retention. The individual switching model (iii) cannot detect an effect of this size: a 0.5pp county margin effect corresponds to roughly 0.25pp of individual vote share, well inside the logit's precision at a 6% base rate.

---

## H. Part 7 — Stronghold demobilization

Notebook `10_stronghold_demobilization.ipynb`.

### H.1 County size

From `county_decomposition.csv` (3,111 counties), binned on 2020 Democratic share (`outputs/tables/stayhome_by_county_bin.csv`):

| 2020 Dem share | Counties | Share of 2020 votes | Share of 2020 Dem votes | ΔDem | Turnout comp. | Share comp. | Turnout change | Dem share change |
|---|---|---|---|---|---|---|---|---|
| <35% | 1,903 | 18.7% | 9.6% | −0.16M | +0.17M | −0.32M | +2.1% | −1.1 |
| 35–45% | 539 | 15.6% | 12.2% | −0.29M | +0.11M | −0.40M | +1.2% | −1.6 |
| 45–55% | 322 | 22.6% | 21.9% | −1.20M | −0.27M | −0.93M | −1.4% | −2.7 |
| 55–65% | 197 | 21.9% | 25.8% | −1.68M | −0.80M | −0.88M | −3.9% | −2.7 |
| 65%+ | 150 | 21.2% | 30.5% | −2.90M | −1.72M | −1.19M | −6.9% | −3.8 |
| All | 3,111 | — | — | −6.22M | −2.51M | −3.71M | −2.0% | — |

65%+ counties: Dem votes 24.69M → 21.79M (−11.8%); non-Dem votes 8.84M → 9.43M; 47% of national ΔDem, 68% of national turnout component; −0.10M in the seven swing states, −1.79M in CA+NY+IL. Ten largest losses: Los Angeles −611,776 (turnout −380,665), Cook −278,152, Queens −131,756, Alameda −118,108, Santa Clara −107,223, Kings −102,045, Bronx −93,704, Dallas −87,458, King WA −74,704, New York County −69,258.

### H.2 Partisanship of 2024 non-voters

**Cross-section.** CES 2024, `TS_voterstatus` non-missing (matched to TargetSmart) and `presvote20post ∈ {1, 2}`: N = 34,666 (20,348 recalled Biden, 14,318 recalled Trump). `stay = 1` if `TS_g2024 == 7`. Recalled D/R ratio is 1.42 unweighted against actual 1.09; the CES weights rake on 2020 vote and bring it to 1.08 (`commonweight`) or 1.12 (`vvweight`), so no separate recall adjustment is applied. `outputs/tables/stayhome_partisanship.csv`:

| Weight | Biden voters stayed home | Trump voters stayed home | Stay-homes who voted Biden |
|---|---|---|---|
| Unweighted | 5.7% | 5.6% | 58.9% |
| `commonweight` (adults) | 4.4% | 3.8% | 55.6% |
| `vvweight` (registered voters) | 8.0% | 5.9% | 60.5% |

**Panel.** Validated 2020 voters with a 2024 match and a contemporaneous 2020 major-party vote: N = 3,982, 136 stay-homes; unweighted Biden 3.2%, Trump 3.7%; `commonweight_24` 2.4% / 4.6%.

**By demographic group** (cross-section, unweighted; `outputs/tables/stayhome_by_group.csv`):

| Group | N Biden | Stay, Biden | N Trump | Stay, Trump | Mean `vvweight` Biden / Trump |
|---|---|---|---|---|---|
| Black | 3,228 | 10.4% | 262 | 16.8% | 1.12 / 1.90 |
| Hispanic | 2,161 | 7.5% | 1,057 | 8.5% | 1.08 / 1.20 |
| Under 35 (other) | 1,650 | 7.7% | 516 | 9.3% | 1.73 / 3.15 |
| No degree (other) | 5,012 | 5.3% | 6,313 | 5.6% | 0.75 / 1.17 |
| Other | 8,297 | 3.2% | 6,170 | 4.4% | 0.77 / 1.00 |

Within every group Trump voters stayed home at an equal or higher rate. The weighted aggregate differential arises because Biden voters are concentrated in the high-stay-home groups and the weights up-weight those groups (mean `vvweight` 1.1–1.7 versus 0.75 for the reference group). It is a compositional effect, not a propensity difference.

### H.3 Turnout against 2016

| County 2020 Dem share | Turnout 2016 | 2020 | 2024 | 2016→20 | 2020→24 | 2016→24 |
|---|---|---|---|---|---|---|
| <35% | 25.72M | 29.50M | 30.13M | +14.7% | +2.1% | +17.2% |
| 35–45% | 21.21M | 24.63M | 24.92M | +16.1% | +1.2% | +17.5% |
| 45–55% | 29.98M | 35.76M | 35.25M | +19.3% | −1.4% | +17.6% |
| 55–65% | 29.81M | 34.55M | 33.22M | +15.9% | −3.9% | +11.5% |
| 65%+ | 29.33M | 33.54M | 31.22M | +14.4% | −6.9% | +6.4% |

Democratic votes in 65%+ counties: 21.03M (2016) → 24.69M (2020) → 21.79M (2024), +3.6% over 2016; Democratic share 71.7% → 73.6% → 69.8%.

Swing-state counties Biden won with 55%+, 2020→2024: Pennsylvania (5) turnout +0.1%, components −3k / −37k; Michigan (5) −0.1%, −2k / −71k; Wisconsin (6) +3.5%, +23k / −9k; Georgia (23) +1.3%, +19k / −3k; Arizona (4) −0.8%, −3k / −19k; North Carolina (16) +1.2%, +19k / −19k; Nevada has none. All are 11–22% above 2016.

### H.4 Stay-home vs. flip

Outcome for 2020 major-party voters with a known 2024 outcome (`outputs/tables/stayhome_vs_flip.csv`, weighted):

| | Cross-section Biden (N = 18,182) | Cross-section Trump (13,517) | Panel Biden (1,391) | Panel Trump (1,345) |
|---|---|---|---|---|
| Same party | 84.4% | 91.8% | 95.7% | 92.0% |
| Flipped | 4.7% | 1.5% | 1.4% | 2.9% |
| Third party | 0.9% | 0.4% | 0.6% | 1.4% |
| Stayed home | 10.0% | 6.3% | 2.4% | 3.7% |
| **Of leavers:** stayed home / flipped / third | 64 / 30 / 6 | 76 / 19 / 5 | 55 / 31 / 13 | 46 / 36 / 18 |

### H.5 Counterfactual

Net margin change if 2020 voters who did not vote in 2024 had voted as in 2020: `Biden_2020(state) × stay_Biden(state) − Trump_2020(state) × stay_Trump(state)`, rates from the cross-section by `inputstate` under each weight; totals from MIT returns; binomial CI on the unweighted net (`outputs/tables/stayhome_counterfactual.csv`, `outputs/figures/stayhome_counterfactual.png`):

| State | 2024 margin | n Biden / Trump | Unweighted net (95% CI) | `commonweight` | `vvweight` | Flips |
|---|---|---|---|---|---|---|
| Pennsylvania | −120,266 | 1,043 / 855 | −22,361 (−76k, +32k) | −17,457 | −17,276 | no |
| Michigan | −80,103 | 736 / 468 | +20,313 (−50k, +91k) | +51,069 | +182,835 | `vvweight` only |
| Wisconsin | −29,397 | 457 / 296 | −11,576 (−52k, +29k) | +6,506 | −10,013 | no |
| Georgia | −115,100 | 656 / 471 | −5,920 (−77k, +65k) | +19,297 | +37,602 | no |
| Arizona | −187,382 | 472 / 433 | +23,917 (−19k, +67k) | +10,933 | +26,544 | no |
| Nevada | −46,008 | 243 / 163 | −9,710 (−37k, +18k) | −13,830 | +7,780 | no |
| North Carolina | −183,048 | 617 / 494 | +58,566 (−6k, +123k) | +113,455 | +127,872 | no |
| National | −2,289,953 | 20,348 / 14,318 | +434,710 (+54k, +816k) | +763,012 | +2,166,665 | no |

Michigan under `vvweight` rests on 41 Biden and 24 Trump stay-homes. An earlier county-level counterfactual (restore stronghold turnout at 2024 shares) gave +11k Pennsylvania and +1k Michigan; it assumed stay-homes mirror 2024 voters and is superseded, though it reaches the same map for a different reason — swing-state strongholds did not lose turnout (H.3).

### H.6 Share decomposition

Notebook `11_share_and_issues.ipynb` §1. Validated 2024 voters (`TS_g2024 ∈ 1–6`) with a 2024 vote (`CC24_410`) and a recalled 2020 status (`presvote20post`): N = 32,531, weighted by `vvweight_post` falling back to `vvweight`. Two-party Democratic share in this sample 49.1% (actual 49.25%). `outputs/tables/share_decomposition.csv`:

| 2020 status | N | Share of 2024 voters | Harris | Trump | Third | Net to Trump (pp of electorate) |
|---|---|---|---|---|---|---|
| Biden | 16,807 | 47.7% | 93.8% | 5.2% | 1.0% | −42.32 |
| Trump | 12,588 | 44.6% | 1.6% | 97.9% | 0.4% | +42.93 |
| Other | 1,193 | 2.1% | 37.2% | 42.1% | 20.7% | +0.10 |
| Non-voter | 1,943 | 5.6% | 40.0% | 57.7% | 2.2% | +0.98 |

Net switching: +2.48 − 0.73 = +1.74pp. New voters: +0.98pp. New voters by group (share of new voters; Trump / Harris): white/other 30+ 48.5%, 70.8 / 27.4; under 30 (other) 30.2%, 44.6 / 51.6; Hispanic 13.8%, 64.5 / 34.4; Black 7.6%, 14.7 / 85.0. Mean age 39 (all voters 53); no degree 71% (all 50%).

---

## I. Part 8 — Issue attitudes of switchers and new voters

Notebook `11_share_and_issues.ipynb` §2–5. Sample as H.6.

### I.1 Items and indices

All items coded 1 = the Democratic-aligned / liberal position, from CES support (1) / oppose (2) responses. **Economic** (8): expand Medicaid (`CC24_328e` support), keep ACA (`CC24_328d` oppose repeal), no Medicaid work requirement (`CC24_328c` oppose), forgive student loans (`CC24_323f` support — misnumbered in the file; counts match the guide's student-loan item), corporate tax to 28% (`CC24_341b` support), tax on $400k+ (`CC24_341c` support), do not extend 2017 cuts (`CC24_341a` oppose), low-income housing incentives (`CC24_328b` support). **Immigration** (5): no wall (`CC24_323c` oppose), allow asylum (`CC24_340f` oppose denial), no more border patrol (`CC24_323b` oppose), legal status for long-employed (`CC24_323a` support), Dreamers (`CC24_323d` support). **Social** (2): abortion as choice (`CC24_324a` support), federal recognition of same-sex marriage (`CC24_340c` support). **Policing** (2): no more police (`CC24_321d` oppose), defund (`CC24_321e` support). `econ_left` = mean of economic items; `cult_cons` = 1 − mean of the nine cultural items; sub-indices likewise. Ideological placement `CC24_330a/d/e` (self / Harris / Trump), 1 very liberal – 7 very conservative, 8 not sure dropped.

The 2024 common content has no item on transgender policy, "wokeness," minimum wage, Medicare-for-all, tariffs, or issue salience.

### I.2 Profiles by path

`outputs/tables/issue_profiles_by_path.csv`, `issue_items_by_path.csv`, weighted:

| Path | N | econ_left | immig_cons | social_cons | police_cons | Self | Harris placed | Trump placed | Harris "very lib" | dist. Harris | dist. Trump |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Biden→Harris | 16,473 | 0.84 | 0.19 | 0.07 | 0.45 | 2.56 | 2.83 | 6.34 | 6.9% | 1.13 | 4.20 |
| Biden→Trump | 334 | 0.55 | 0.73 | 0.47 | 0.72 | 4.41 | 1.83 | 5.35 | 58.8% | 3.02 | 1.55 |
| Non-voter→Harris | 1,005 | 0.82 | 0.19 | 0.09 | 0.46 | 2.53 | 2.66 | 6.31 | 13.1% | 1.34 | 4.16 |
| Non-voter→Trump | 854 | 0.44 | 0.79 | 0.62 | 0.81 | 5.30 | 1.29 | 5.73 | 84.8% | 4.22 | 1.12 |
| Trump→Harris | 348 | 0.65 | 0.53 | 0.30 | 0.53 | 4.29 | 2.52 | 5.83 | 19.7% | 2.05 | 2.55 |
| Trump→Trump | 12,240 | 0.30 | 0.85 | 0.70 | 0.91 | 5.86 | 1.11 | 5.66 | 93.7% | 4.83 | 0.85 |

Item-level shares taking the liberal position, Biden→Harris / Biden→Trump / non-voter→Trump / Trump→Trump: expand Medicaid 95 / 77 / 73 / 55; keep ACA 95 / 62 / 39 / 25; no work requirement 62 / 40 / 37 / 29; student loans 84 / 47 / 25 / 13; corporate tax 91 / 60 / 41 / 23; tax $400k+ 91 / 57 / 50 / 34; no 2017 cuts 67 / 21 / 18 / 11; housing 91 / 73 / 67 / 48; no wall 86 / 23 / 8 / 3; allow asylum 64 / 18 / 9 / 6; no more patrol 33 / 8 / 5 / 2; legal status 86 / 43 / 41 / 25; Dreamers 95 / 64 / 53 / 42; abortion choice 93 / 46 / 29 / 21; same-sex marriage 92 / 60 / 48 / 38; no more police 66 / 35 / 28 / 13; defund 44 / 20 / 11 / 5.

### I.3 Models

**Biden 2020 voters → Trump 2024** (`outputs/tables/switch_issue_models.csv`; logit, `vvweight_post`/`vvweight` as normalized frequency weights, county-clustered; N = 16,971, 327 switchers; per-SD coefficients):

| | Issues only | + `pid7`, college, age, Hispanic, Black | Cultural split |
|---|---|---|---|
| `econ_left` | −1.587 (0.156) | −1.146 (0.186) | −1.249 (0.180) |
| `cult_cons` | +1.922 (0.182) | +2.026 (0.210) | |
| `immig_cons` | | | +1.447 (0.174) |
| `social_cons` | | | +0.868 (0.110) |
| `police_cons` | | | −0.021 (0.128) |
| `pid7` | | +0.775 (0.074) | +0.768 (0.078) |
| Hispanic | | +0.357 (0.323) | +0.203 (0.320) |
| Black | | −0.130 (0.309) | −0.323 (0.305) |
| College | | −0.587 (0.220) | −0.560 (0.230) |

AME per +1 SD, controls model: `econ_left` −0.0215, `cult_cons` +0.0757. Split: `econ_left` −0.0221, `immig_cons` +0.0450, `social_cons` +0.0237, `police_cons` −0.0005.

**New voters → Trump** (`outputs/tables/newvoter_issue_model.csv`; N = 1,943, 854 Trump; no party control): `econ_left` −1.451 (0.205), `immig_cons` +1.282 (0.240), `social_cons` +1.138 (0.135), `police_cons` +0.309 (0.169), Hispanic −0.100 (0.315), Black −2.869 (0.438), college −0.587 (0.282).

**Harris "very liberal" among Biden→Trump switchers** (N = 299; LPM, HC3): `econ_left` −0.111 (0.059), `immig_cons` +0.137 (0.054), `social_cons` +0.035 (0.046), `police_cons` +0.028 (0.055). Base rate 58.9%.

### I.4 Quadrants

Quadrant cutoffs: `econ_left ≥ 0.6` = economically left; `cult_cons ≥ 0.6` = culturally conservative. Composition by path (`outputs/tables/quadrant_by_path.csv`), weighted: Biden→Harris 90% left/liberal, 5% left/conservative, 1% right/conservative; Biden→Trump 29 / 24 / 36 (11% mixed); non-voter→Trump 12 / 20 / 58; Trump→Harris 50 / 13 / 13; Trump→Trump 3 / 10 / 80.

Switch rate among Biden 2020 voters by quadrant and income (`outputs/tables/quadrant_switch_rates.csv`): under $50k — left/liberal 1.8% (N = 4,668), left/conservative 23.3% (360), right/conservative 41.4% (100); $50k+ — left/liberal 1.8% (9,409), left/conservative 20.7% (369), right/conservative 69.1% (191).

### I.5 Attitude timing (panel) and the 2016 switch

Notebook `12_attitudes_timing_and_2016.ipynb`.

**Panel immigration trajectory** (`outputs/tables/panel_immigration_trajectory.csv`). Items: `CC20_331a` / `CC22_331a` / `CC24_331a` (legal status; conservative = oppose), `331b` (border patrol; support), `CC20_331d` / `CC22_331c` / `RC24_331c` (cut legal immigration 50%; support), `CC20_331e` / `CC22_331d` / `RC24_331d` ($25B border security incl. wall; support). Index = mean conservative share; `commonpostweight_24` falling back to `commonweight_24`; path from contemporaneous `CC20_410` and `CC24_410`.

| Path | N | 2020 | 2022 | 2024 | Δ | Abortion-cons 2020 / 2022 / 2024 |
|---|---|---|---|---|---|---|
| Biden→Harris | 1,645 | 0.17 | 0.24 | 0.34 | +0.18 | 0.13 / 0.11 / 0.09 |
| Biden→Trump | 39 | 0.50 | 0.55 | 0.74 | +0.24 | 0.59 / 0.68 / 0.47 |
| Trump→Harris | 39 | 0.51 | 0.53 | 0.51 | 0.00 | 0.43 / 0.42 / 0.28 |
| Trump→Trump | 1,643 | 0.81 | 0.82 | 0.85 | +0.04 | 0.81 / 0.83 / 0.80 |

2020 items, conservative share, loyal Dem / Biden→Trump / loyal Rep (`panel_immigration_items_2020.csv`): oppose legal status 10 / 72 / 63; more border patrol 33 / 49 / 98; cut legal immigration 17 / 39 / 74; wall 7 / 40 / 90.

**Recalled 2016 vote** (`presvote16post_20`, asked in 2020; `panel_2016_vote_by_path.csv`), weighted: Biden→Harris Clinton 70.1 / Trump 1.7 / other 7.0 / no vote 21.3; Biden→Trump 42.7 / 3.8 / 0.5 / 53.0 (unweighted 18 / 8 / 2 / 11); Trump→Harris 21.7 / 56.1 / 14.5 / 7.7; Trump→Trump 1.9 / 75.3 / 6.3 / 16.5. The Biden→Trump Trump-2016 share is 4% weighted and 21% unweighted; the eight respondents carry low weights.

**CES 2016** (`CCES16_Common_OUTPUT_Feb2018_VV.tab`; `CC16_326` 2012 vote, `CC16_410a` 2016 vote, `CC16_328` primary; `commonweight_vv_post`). N with both major-party votes = 35,589. Obama→Trump 12.0% of Obama voters (N = 2,121); Romney→Clinton 5.9% (854). Immigration items are select-all (`CC16_331_1` legal status, `_2` border patrol, `_3` Dreamers, `_7` deport all); not-selected is coded as the opposing position, so levels are not comparable to the 2020+ support/oppose format. `CC16_351I` repeal ACA (for = 1), `CC16_351K` $12 minimum wage (for = 1).

Profile (`switchers_2016_profile.csv`):

| Path | N | imm_cons | abortion_cons | repeal ACA | $12 min wage | college | white | Hispanic | pid7 |
|---|---|---|---|---|---|---|---|---|---|
| Obama→Clinton | 18,677 | 0.28 | 0.18 | 0.20 | 0.92 | 0.36 | 0.61 | 0.02 | 1.83 |
| Obama→Trump | 2,121 | 0.62 | 0.42 | 0.72 | 0.73 | 0.23 | 0.80 | 0.02 | 3.82 |
| Romney→Clinton | 854 | 0.43 | 0.35 | 0.55 | 0.66 | 0.42 | 0.82 | 0.02 | 4.18 |
| Romney→Trump | 13,937 | 0.77 | 0.72 | 0.95 | 0.34 | 0.28 | 0.89 | 0.02 | 5.88 |

Immigration items 2016, conservative share, Obama→Clinton / Obama→Trump / Romney→Trump: oppose legal status 24 / 54 / 73; more border patrol 34 / 65 / 82; oppose Dreamers 35 / 66 / 78; deport all 20 / 62 / 74.

Primary vote among Obama-2012 voters who voted in a primary (`switchers_2016_primary.csv`): Obama→Clinton (N = 14,012) Clinton 63 / Sanders 33 / Trump 1 / Cruz 0 / Kasich 2; Obama→Trump (1,322) Clinton 21 / Sanders 23 / Trump 47 / Cruz 4 / Kasich 3. Sanders primary voters (N = 6,288): Clinton 86.1%, Trump 13.9%; of those who voted Obama in 2012 (5,146): Trump 7.7%; those 288 Sanders→Trump switchers: imm_cons 0.56, $12 minimum wage 79%, repeal ACA 72%.

---

## J. Limitations

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
16. **Panel events.** The Part 5 timing result rests on 39 switchers (36 in the models with covariates). The monotonic cross-tab and the stability of the coefficient across specifications and across weighted/unweighted estimation are the evidence; interactions and subgroup splits are not supportable. Post-election weights average roughly 2× for switchers, so any cell with a handful of events can produce an extreme weighted rate (F.3, prices).
17. **Panel attrition and what it hides.** The retained panel is more engaged than the population (A.7). Validated 2024 non-voting of 3–4% among 2020 voters is a floor, and the equality between Biden and Trump 2020 voters on that measure should not be read as evidence against the stronghold turnout loss in Part 2, which the panel cannot see.
18. **Timing is not identification.** A 2022 rating rules out rationalization of a 2024 decision. It does not rule out a common cause already operating in 2022 — a voter leaving Biden for a non-economic reason and rating the economy worse because of it. Distinguishing those would need either a measure of the non-economic cause in 2022 or an exogenous shock to perception between waves.
19. **Delivery is obligations, by place of performance, for two programs.** Obligated money is not built infrastructure; place of performance mis-credits state capitals and federal labs (addressed by winsorizing and tail-dropping, not eliminated); IRA and CHIPS are absent. A perception null could reflect voters not crediting delivery or delivery not yet being visible by November 2024.
20. **A vote effect without a perception effect is only partly explained.** The delivery coefficient on the county swing survives every control tried and loads on the share component, not turnout (G.3 v), which rules out mobilization. Its absence from perception, within-person change, and individual switching means the remaining channel is not one this project measures: a local-conditions perception the "nation's economy" item does not capture, or county-level confounding that composition, RUCC, and population do not remove.
21. **Race categories are coarse.** CES self-identification; "Other" pools Asian, Native, multiracial, and unspecified. The Hispanic switching rate is a single-wave cross-sectional estimate on recalled 2020 vote; the panel cannot corroborate it (38 Hispanic Biden voters).
22. **Stay-home partisanship is a composition effect and its size depends on the weight.** Unweighted, Biden and Trump 2020 voters stayed home at the same rate, and within every demographic group Trump voters stayed home as much or more (H.2). The weighted aggregate gap reflects the Democratic coalition's concentration in low-turnout groups. The counterfactual is reported under three weightings; Michigan flips under one, on 41 stay-homes, with an unweighted CI spanning zero. It holds new 2024 voters fixed.
23. **Panel and cross-section agree on propensity and cannot both speak to effect.** Both show no propensity difference. The panel's stay-home rate is a third of the cross-section's because it retained the engaged; the cross-section's weighted rates are the population estimate. The 2020 vote in the cross-section is recalled.
24. **Attitudes are measured after the vote.** Part 8's issue items are from the 2024 wave. A switcher's 2024 immigration position could follow from the switch as much as precede it. The panel carries the same items in 2020 and 2022 but has 39 switchers.
25. **The cultural axis is what the CES asks, not what the hypothesis names.** No transgender, "wokeness," or salience items exist in the 2024 common content. The finding that immigration dominates among the cultural items measured is not evidence about items not measured.
26. **The 2016 comparison is across surveys and formats.** The 2016 immigration items are select-all (non-selection coded as opposition), the 2012 vote is recalled in 2016, and the 2024 items are support/oppose. Path-to-path comparisons within each survey are sound; cross-year levels are not. The 2024 switchers' 2016 vote rests on 39 panelists with strong weight sensitivity on the eight who reported a Trump 2016 vote.

---

## K. Reproducibility

### K.1 Environment

Python 3.8 virtual environment at `.venv`; dependencies in `requirements.txt`. Register the kernel once:

```bash
python -m ipykernel install --user --name dnc-autopsy --display-name "Python (dnc-autopsy)"
```

### K.2 Pipeline

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
| 13 | `python src/data_collection/ces_panel_pull.py` | Dataverse | `data/raw/ces_panel/ces_panel_long.csv`, `ces_panel_wide.csv`, guide PDF |
| 14 | `08_panel_analysis.ipynb` | steps 8, 13 | `data/processed/panel_biden2020_outcomes.csv`, tables, figure |
| 15 | `python src/data_collection/usaspending_pull.py` | USAspending API | `data/raw/usaspending/county_delivery.csv` |
| 16 | `09_bottom_quartile_and_delivery.ipynb` | steps 7, 8, 9, 11, 13, 15 | `data/processed/county_delivery_clean.csv`, tables, figure |
| 17 | `10_stronghold_demobilization.ipynb` | steps 3, 6, 9, 13 | tables, figure |
| 18 | `11_share_and_issues.ipynb` | step 9 | tables, figure |
| 19 | `12_attitudes_timing_and_2016.ipynb` | steps 9, 13 | tables |

Execute notebooks non-interactively with the project kernel:

```bash
jupyter nbconvert --to notebook --execute notebooks/0N_*.ipynb --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy
```

### K.3 Keys

Copy `.env.example` to `.env` and set `FRED_API_KEY` and `CENSUS_API_KEY`. Never commit `.env`. The CES and BLS pulls need no key.

---

## L. Next steps

Part 4 established that perception is disconnected from local reality and travels with media diet and with vote switching. The news-environment instrument failed (E.9, first-stage F = 0.64). Part 5 then used the panel to put perception two years ahead of the vote, which is as far as the CES can take the timing question. What remains:

1. **The 2022 common cause.** The panel's 2022 wave carries the items needed to probe whether Biden voters who rated the economy badly in 2022 were already moving on non-economic grounds: 2022 presidential approval (`CC22_320a`), 2022 issue items, and the 2022 House vote (`CC22_412`; candidate names are state-specific, so party must be recovered from the candidate-party fields). A Biden voter who rated the economy "much worse" in 2022 but still voted Democratic in the 2022 House election, and then switched in 2024, is a cleaner case than one who had already defected by 2022. With 39 events this is a cross-tab, not a model, but it is the right cross-tab.
2. **A local price measure.** The prices item is the least partisan perception in the survey and predicts switching net of the economy rating in both the cross-section (E.8) and the panel (F.3), but there is nothing to set it against. BEA regional price parities or ACS 1-year rent would allow a prices gap — perceived minus measured.
3. **More panel.** The 2020–2022 panel (`doi:10.7910/DVN/XV7ABM`) is a different, larger recontact of 2020 respondents; whether any of its members also appear in the 2020–2024 file is undetermined. If so, pooling adds 2022 observations but not 2024 outcomes.
4. **The delivery mechanism.** Delivery moved the county vote (G.3) without moving perception, and the component test (G.3 v) shows it is a share effect, not turnout — Republican vote growth was lower where infrastructure money went. Two things would narrow it further: (a) a local-conditions perception — the CES has no "your area's economy" item, but the household-income item (`CC24_302` in the common content) is the closest available and could be tested against delivery the way the national item was; (b) the composition of the Republican vote growth — whether it is new voters or switchers, which the CES cross-section cannot separate but a county-level comparison of validated new registrants (L2 or TargetSmart aggregates) against delivery could.
5. **The Hispanic shift.** Part 6 reframes the 2024 class gradient as ethnic. The CES 2024 has the sample to go further (1,890 Hispanic Biden voters): by nativity and language of interview if available, by 2022 perception in the panel (too few), and by whether the prices item carries the switching effect for Hispanic voters as it does overall.

The reduced-form association between living in a news desert and switching does not survive Medill's desert definition and should not be pursued.

6. **Salience.** The CES does not ask which issue mattered most. The ANES 2024 does, and its state-level file is public. Whether switchers *prioritized* immigration over healthcare, as opposed to merely holding conservative views on it, is the piece that would turn Part 8's "reachable on economics" into a claim about what would have reached them.

CDC WONDER overdose mortality remains a planned Part 3 covariate; nothing in Part 4 depends on it.
