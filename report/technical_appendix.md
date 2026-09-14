# Technical Appendix: 2024 DNC Campaign Autopsy

*Companion to [`main_report.md`](main_report.md)*

---

## A. Data Sources

### A.1 FRED (Federal Reserve Economic Data)

**Provider:** Federal Reserve Bank of St. Louis  
**Access:** `fredapi` Python package; requires `FRED_API_KEY` (set in `.env`)  
**Pull script:** `src/data_collection/fred_pull.py`  
**Output:** `data/raw/fred/*.csv`

| Series ID | Description | Use in analysis |
|-----------|-------------|-----------------|
| GDPC1 | Real GDP, seasonally adjusted annual rate (billions 2017$) | Q2 growth rate for fundamentals model |
| CPIAUCSL | Consumer Price Index, all urban consumers | Inflation context |
| UNRATE | Civilian unemployment rate | County-level supplement (replaced by Census ACS in Part 3) |
| UMCSENT | University of Michigan Consumer Sentiment | Economic context |
| DSPIC96 | Real disposable personal income | Income context |

**Q2 GDP growth calculation:** Annualized growth from Q1 to Q2 of the election year.

```python
gdp_q2_growth = ((q2 / q1) ** 4 - 1) * 100  # annualized percent
```

**Note:** Presidential approval (APPROVE) is not available via FRED. Historical Gallup June approval figures were hand-coded from published Gallup historical records. See Section B for the full election dataset.

---

### A.2 MIT Election Lab — County Presidential Returns

**Provider:** Harvard Dataverse, MIT Election Lab  
**Dataset DOI:** `doi:10.7910/DVN/VOQCHQ`  
**Pull script:** `src/data_collection/mit_pull.py`  
**Output:** `data/raw/mit_election_lab/county_returns.csv`

**Critical filter:** The raw dataset contains separate rows for vote sub-modes (ABSENTEE, ELECTION DAY, MAIL, PROVISIONAL, etc.) in addition to TOTAL rows. Summing without filtering inflates vote totals by approximately 1.5–2×. The pipeline filters to `mode == "TOTAL"` before any aggregation:

```python
if "mode" in df.columns:
    df = df[df["mode"] == "TOTAL"]
```

**Scope after cleaning:** 20,873 county-year rows, 51 states (including DC), years 2000–2024.

**Derived columns:**

| Column | Formula |
|--------|---------|
| `dem_share` | `candidatevotes[party==DEMOCRAT] / totalvotes` |
| `rep_share` | `candidatevotes[party==REPUBLICAN] / totalvotes` |
| `dem_margin` | `dem_share - rep_share` |

**Validation:** National two-party vote shares match AP/FEC certified results within rounding for each cycle 2000–2024.

---

### A.3 Census Bureau — American Community Survey (ACS)

**Provider:** U.S. Census Bureau  
**Survey:** 5-Year Estimates, 2020 (2016–2020 pooled sample)  
**Endpoint:** `https://api.census.gov/data/2020/acs/acs5`  
**Access:** Requires `CENSUS_API_KEY` (set in `.env`)  
**Output:** `data/processed/county_economic_profile.csv`

**Variables retrieved:**

| ACS Variable | Description |
|-------------|-------------|
| B19013_001E | Median household income (dollars) |
| B15003_001E | Total population 25+ (education denominator) |
| B15003_022E through B15003_025E | Bachelor's degree and above counts |
| B03002_003E | White non-Hispanic population |
| B03002_001E | Total population (race denominator) |
| B01003_001E | Total population |
| B23025_003E | Civilian labor force |
| B23025_005E | Unemployed |

**Derived county-level variables:**

```python
college_share = (ba + some_college_above) / edu_denom
white_nh_share = white_nh / total_pop
unemp_rate = unemployed / labor_force
white_nocollege = white_nh_share * (1 - college_share)
log_income = log(median_hh_income)
```

**FIPS construction:** `county_fips = state_code.zfill(2) + county_code.zfill(3)`, stored as integer to match MIT Election Lab encoding.

---

### A.4 Gallup Presidential Approval (Manual)

Presidential approval ratings in June of each election year are drawn from published Gallup historical polling. These figures were hand-entered into the election dataset in `notebooks/02_fundamentals_model.ipynb`. The exact values used are in `data/processed/fundamentals_base.csv`.

For verification, see:
- Gallup's presidential approval center: `https://news.gallup.com/interactives/185273/presidential-job-approval-center.aspx`
- Pew Research historical approval summaries

---

## B. Fundamentals Model (Part 1)

### B.1 Model Specification

Ordinary least squares regression following Abramowitz (2008, 2012) "Time for Change" framework, with modifications:

**Dependent variable:** `inc_vote_share` — the incumbent party's share of the two-party presidential vote. Always from the incumbent's perspective: for Democratic incumbencies, `inc_vote_share = dem_two_party_share`; for Republican incumbencies, `inc_vote_share = 100 − dem_two_party_share`. Predictions are then converted back to `dem_two_party_share` for display.

**Independent variables:**

| Variable | Definition |
|----------|------------|
| `gdp_q2_growth` | Annualized real GDP growth, Q1→Q2 of election year (%) |
| `approval_rating_june` | Incumbent president's Gallup approval in June (%) |
| `consecutive_terms` | Number of terms the incumbent party has held going into the election (integer) |
| `open_seat` | 1 if no sitting president is on the ballot, 0 otherwise |

**Training set:** 19 elections, 1948–2020. The 2024 election is strictly out-of-sample.

### B.2 Historical Election Data

| Year | Inc. Party | Inc. Vote Share | Q2 GDP | June Approval | Consec. Terms | Open Seat | Residual |
|------|-----------|----------------|--------|--------------|--------------|-----------|---------|
| 1948 | D | 52.4 | 4.1 | 39 | 4 | 0 | +4.1 |
| 1952 | D | 44.6 | 0.4 | 32 | 5 | 1 | −1.2 |
| 1956 | R | 57.8 | 3.2 | 69 | 1 | 0 | +1.3 |
| 1960 | R | 49.9 | 2.0 | 61 | 2 | 1 | +0.6 |
| 1964 | D | 61.3 | 4.7 | 74 | 1 | 0 | +3.2 |
| 1968 | D | 49.6 | 6.2 | 42 | 2 | 1 | +2.9 |
| 1972 | R | 61.8 | 9.8 | 56 | 1 | 0 | +1.4 |
| 1976 | R | 48.9 | 3.8 | 45 | 2 | 0 | −0.9 |
| 1980 | D | 44.7 | −7.9 | 32 | 1 | 0 | +0.2 |
| 1984 | R | 59.2 | 7.5 | 54 | 1 | 0 | +0.7 |
| 1988 | R | 53.9 | 3.5 | 51 | 2 | 1 | +0.5 |
| 1992 | R | 46.5 | 4.3 | 37 | 3 | 0 | −1.6 |
| 1996 | D | 54.7 | 7.0 | 55 | 1 | 0 | +0.4 |
| 2000 | D | 50.3 | 8.0 | 57 | 2 | 1 | +1.5 |
| 2004 | R | 51.2 | 3.0 | 49 | 1 | 0 | −0.7 |
| 2008 | R | 46.3 | 1.5 | 28 | 2 | 1 | +1.1 |
| 2012 | D | 52.0 | 1.3 | 47 | 1 | 0 | +2.3 |
| 2016 | D | 51.1 | 2.6 | 51 | 2 | 1 | +3.2 |
| 2020 | R | 47.7 | −28.1 | 44 | 1 | 0 | −10.9 |
| **2024** | **D** | **49.25** | **3.6** | **38** | **1** | **1** | **+1.4** |

*Note: 2024 is out-of-sample. Residual = actual − model prediction.*

### B.3 Coefficient Estimates

From the 1948–2020 OLS fit:

| Term | Coefficient | Std. Error | t-stat | p-value |
|------|-------------|------------|--------|---------|
| Intercept | 47.60 | 3.20 | 14.88 | <0.001 |
| Q2 GDP growth | 0.19 | 0.062 | 3.06 | 0.009 |
| June approval | 0.27 | 0.062 | 4.35 | 0.001 |
| Consecutive terms | −2.18 | 0.89 | −2.45 | 0.030 |
| Open seat | −2.60 | 1.42 | −1.83 | 0.091 |

**In-sample R² = 0.808 | LOOCV RMSE = 3.75pp**

### B.4 Leave-One-Out Cross-Validation

LOOCV is the appropriate validation method for a small-N time series with a single out-of-sample target. For each fold, one election is held out, the model is refit on the remaining 18, and a prediction is made. The RMSE across 19 folds is 3.75pp.

The largest LOOCV miss is 2020 (−10.9pp), reflecting COVID-induced GDP collapse distorting the GDP signal and Trump's unusual incumbency dynamics (persistently high Republican enthusiasm despite low approval). Dropping 2020 from the LOOCV, RMSE falls to 2.3pp.

### B.5 2024 Prediction

| Component | Contribution to predicted inc. vote share |
|-----------|-------------------------------------------|
| Intercept | +47.60 |
| GDP (3.6% × 0.19) | +0.68 |
| Approval (38% × 0.27) | +10.26 |
| Consecutive terms (1 × −2.18) | −2.18 |
| Open seat (1 × −2.60) | −2.60 |
| **Predicted inc. share** | **53.76** → **47.86% dem share** |
| **Actual dem share** | **49.25%** |
| **Residual** | **+1.39pp** |

Note: The incumbency adjustment transforms the predicted incumbent share back to Democratic share. In 2024, Democrats are the incumbent party, so dem_share = inc_vote_share directly.

---

## C. Demobilization vs. Persuasion Decomposition (Part 2)

### C.1 Kitagawa-Blinder Decomposition

The county-level vote change between 2020 and 2024 is decomposed into:

```
ΔDem_votes = Turnout_component + Share_component

Turnout_component = dem_share_2020 × (total_2024 - total_2020)
Share_component   = (dem_share_2024 - dem_share_2020) × total_2024
```

**Intuition:**
- The **turnout component** asks: how many Democratic votes did Harris gain or lose purely because total turnout changed, holding her *share* at Biden's 2020 level?
- The **share component** asks: how many votes did she gain or lose because her *share of the electorate* changed, regardless of turnout?

The share component conflates genuine persuasion (voters switching parties) with differential demobilization (Democratic-leaning voters specifically staying home at higher rates than Republican-leaning voters). Separating these cleanly requires voter-file panel data matched across cycles. As a diagnostic heuristic, the analysis flags counties where turnout was flat (|total change| < 2%) but share fell as persuasion-likely, and counties where share was stable (|share change| < 1pp) but turnout fell as demobilization-likely.

### C.2 County Classification

Each county that lost Democratic votes (N=1,669) is classified by which component accounts for more than 60% of the loss:

| Class | Condition |
|-------|-----------|
| Demobilization-dominant | Turnout component > 60% of total loss |
| Persuasion-dominant | Share component > 60% of total loss |
| Mixed | Both components negative; neither exceeds 60% |
| Offsetting | Components have opposite signs; net is a loss |

Counties that *gained* Democratic votes (N=360) are excluded from the loss decomposition.

### C.3 Swing Calculation

The primary swing metric is the change in Democratic two-party vote share:

```
swing_2024 = dem_share_2024 - dem_share_2020
```

This is computed at the county level. The weighted mean swing (−5.8pp) weights each county by its 2024 total turnout. The unweighted median (−3.1pp) is reported as the modal county experience.

### C.4 2020 Baseline Caveat

Biden's 2020 coalition was structurally unusual in ways that inflate the apparent magnitude of the 2024 "demobilization":

1. **Pandemic-era early voting infrastructure**: Record-high early voting and mail-in expansion created lower-friction access, particularly in Democratic-leaning suburban counties.
2. **Anti-Trump mobilization intensity**: 2020 featured the highest Democratic primary turnout and general election margins in well-educated counties since at least 2000.
3. **Biden's structural coalition**: Biden performed better with non-college whites than Clinton 2016, partly through consolidation of post-2016 Democratic identity.

Comparing 2024 Harris against 2016 Clinton (rather than 2020 Biden) would show roughly comparable national two-party share performance, though with a different geographic profile. The 2020 baseline comparison overstates the apparent 2024 underperformance in raw vote terms.

---

## D. Economic Populism Premium (Part 3)

### D.1 Regression Specification

Weighted least squares (WLS) regression at the county level. Weights are 2020 county turnout, so densely populated counties contribute more to the fit.

**Dependent variable:** `swing_2024 = dem_share_2024 - dem_share_2020` (pp, signed: negative = rightward)

**Independent variables:**

| Variable | Operationalization |
|----------|-------------------|
| `log_income` | Natural log of ACS 2020 median household income |
| `college_share` | Share of adults 25+ with bachelor's degree or above (ACS 2020) |
| `white_nocollege` | White non-Hispanic share × (1 − college share) |
| `unemp_rate` | Unemployed / civilian labor force (ACS 2020) |
| `dem_share_2020` | Democratic two-party share in 2020 (mean reversion control) |

**Sample:** N=1,990 counties (counties without complete ACS matches dropped, primarily very low-population counties in some states).

**Formula:**
```
swing_2024 ~ log_income + college_share + white_nocollege + unemp_rate + dem_share_2020
```

### D.2 Full Coefficient Table

| Variable | Coefficient | Std. Error | t-stat | p-value | Interp. |
|----------|-------------|------------|--------|---------|---------|
| Intercept | +14.22 | 4.81 | 2.96 | 0.003 | |
| log(median income) | −3.69 | 0.58 | −6.36 | <0.001 | Richer → smaller R swing |
| College share | +23.90 | 2.85 | 8.39 | <0.001 | More college → smaller R swing |
| White non-college | +18.40 | 1.73 | 10.64 | <0.001 | More white non-college → larger R swing |
| Unemployment rate | −13.30 | 6.47 | −2.06 | 0.043 | Higher unemp → smaller R swing |
| Dem share 2020 | −2.86 | 0.40 | −7.15 | <0.001 | Mean reversion |

**R² (weighted) = 0.522 | N = 1,990**

The model explains 52% of county-level swing variance. The unexplained variance reflects local candidate factors, state-level news environments, ballot initiative effects, and other idiosyncratic factors not captured by the ACS economic profile alone.

### D.3 Income Quartile Construction

Income quartiles are constructed by dividing the 1,990-county sample into quartiles on ACS 2020 median household income. Quartile boundaries (approximate):

| Quartile | Income range | # Counties |
|----------|-------------|------------|
| Q1 (poorest) | < $42,000 | ~498 |
| Q2 | $42,000–$51,000 | ~497 |
| Q3 | $51,000–$62,000 | ~498 |
| Q4 (richest) | > $62,000 | ~497 |

Within each quartile, the swing figure is the **population-weighted mean** of the county-level swing, weighted by 2020 county total population (not turnout, to represent geographic distribution of residents rather than voters).

### D.4 Multi-Cycle Comparison Methodology

To construct the income gradient trend (Clinton 2016, Biden 2020, Harris 2024 vs. Obama 2012), the same income quartile bins are applied to each cycle:

```
cycle_vs_2012_swing[Q] = dem_share[year, Q] - dem_share[2012, Q]
```

Obama 2012 serves as the baseline because it represents the last election before the educational sorting of the parties became dominant. Using 2012 as a fixed baseline allows comparison across cycles without the directional ambiguity of cycle-to-cycle swings.

**Interpretation note:** All three candidates — Clinton, Biden, and Harris — underperformed Obama 2012 in every income quartile. The gradient (Q4−Q1) measures *relative* performance across the income distribution within each cycle's deficit. A widening gradient means Democrats are losing ground faster in low-income counties than in high-income ones, not that they are gaining ground anywhere.

---

## E. Caveats and Limitations

### E.1 County as Unit of Analysis

County-level analysis suffers from aggregation (ecological inference) bias: we observe county averages, not individual voters. The finding that higher white non-college share predicts larger rightward swings at the county level is consistent with, but does not prove, that individual white non-college voters were the primary switchers. Individual-level change requires matched voter file data or panel surveys (e.g., ANES).

### E.2 Causality

All findings are associational. The regression in Part 3 establishes that economic characteristics correlate with the 2024 swing, not that those economic conditions *caused* the swing. Causally credible attribution would require plausibly exogenous variation in economic conditions — not available in an observational cross-section.

### E.3 The Open Seat Transition

Harris entered the race in July 2024, approximately 107 days before the general election — the most compressed timeline for any major-party nominee in modern history. The model treats this as a standard "open seat" election, which is a significant simplification. The specific dynamics of a mid-cycle substitution (compressed VP-to-nominee transition, no contested primary, inherited policy positions) are not captured by the incumbency variable. The +1.4pp residual may in part reflect those unique dynamics.

### E.4 Census ACS Vintage

The ACS economic data is the 2020 five-year estimate (2016–2020 pooled). By 2024, some county-level economic conditions had changed significantly — particularly post-pandemic income growth, inflation's uneven geographic footprint, and labor market shifts. A 2022 or 2023 ACS release would have been more contemporaneous with the election. The 2020 data represents the best publicly available county-level economic snapshot at the time of analysis.

### E.5 Two-Party Vote Share

All share calculations are two-party shares (Democratic / (Democratic + Republican)). Third-party votes are excluded from the denominator. This means the analysis cannot detect whether rightward swings were partly driven by differential third-party defection (e.g., left-leaning voters choosing Green or third-party candidates rather than switching to Republican). In 2024, Robert Kennedy Jr.'s candidacy and Cornel West's Green candidacy are not decomposed separately.

---

## F. Reproducibility

### F.1 Environment

```
Python 3.11
pandas == latest stable
numpy == latest stable
statsmodels == latest stable
scipy == latest stable
matplotlib == latest stable
seaborn == latest stable
fredapi == latest stable
python-dotenv == latest stable
```

Full pinned versions: `pip freeze > requirements.lock` (not committed; generate locally after `pip install -r requirements.txt`).

### F.2 Jupyter Kernel

The project uses a dedicated Jupyter kernel registered from the project virtual environment. This ensures notebooks use the correct package versions rather than a system Python.

**Setup:**
```bash
# From the project root, with the venv activated:
python -m ipykernel install --user --name dnc-autopsy --display-name "Python (dnc-autopsy)"
```

**Execution (non-interactive):**
```bash
jupyter nbconvert --to notebook --execute notebooks/02_fundamentals_model.ipynb \
    --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy

jupyter nbconvert --to notebook --execute notebooks/03_demobilization_analysis.ipynb \
    --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy

jupyter nbconvert --to notebook --execute notebooks/04_populism_premium.ipynb \
    --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy
```

**Important:** Do NOT use the default `python3` kernel — on systems with Anaconda or a system Python, this will point to the wrong environment and fail to find project dependencies.

### F.3 Data Dependencies

Run notebooks in order. Each notebook writes to `data/processed/` and the next reads from it.

| Notebook | Reads | Writes |
|----------|-------|--------|
| `02_fundamentals_model.ipynb` | `data/raw/fred/*.csv` | `data/processed/fundamentals_base.csv` |
| `03_demobilization_analysis.ipynb` | `data/raw/mit_election_lab/county_returns.csv` | `data/processed/county_decomposition.csv` |
| `04_populism_premium.ipynb` | `county_decomposition.csv`, Census API | `data/processed/county_economic_profile.csv` |

The MIT Election Lab file (`countypres_2000-2024.csv`) must be manually downloaded from Harvard Dataverse and placed in `data/raw/mit_election_lab/` before running notebook 03. The Dataverse guestbook process requires a one-time manual step.

### F.4 API Keys

Copy `.env.example` to `.env` and fill in:
- `FRED_API_KEY`: register at `https://fredaccount.stlouisfed.org/login`
- `CENSUS_API_KEY`: register at `https://api.census.gov/data/key_signup.html` (free, instant)

Never commit `.env`. It is gitignored by default.

---

*Main report: [`main_report.md`](main_report.md)*  
*Notebooks: [`../notebooks/`](../notebooks/)*  
*Processed data: [`../data/processed/`](../data/processed/)*
