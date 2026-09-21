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

### A.9 ANES 2024 Time Series

**Source:** American National Election Studies, 2024 Time Series Study, full release 2026-05-19 (`anes_timeseries_2024_csv_20260519.zip`, 6,516,359 bytes; 5,521 respondents × 1,738 variables). Free registration at electionstudies.org.
**Script:** `src/data_collection/anes_pull.py` → `data/raw/anes/anes_2024_core.csv` (107 harmonized columns).

**Download.** The ANES site's WAF returns 403 to python-requests regardless of headers but serves the file to a browser. The zip was fetched in the in-app browser and transferred as base64 in thirteen chunks, reassembled and verified byte-exact (`zipfile.testzip()` None). The script does not attempt the HTTP fetch; it extracts and harmonizes whatever zip is on disk.

**Sample.** Three components: 2016–20–24 panel (2,171, carrying `V200001` and `V160001_orig` ids into the 2020 and 2016 files), fresh web (2,308), fresh face-to-face (1,042). Weight `V240107b` (post-election, full sample + PAPI) throughout, because every salience item is post-election; 557 respondents without a post interview drop. Post-weighted two-party vote is Harris 54.4 / Trump 45.6 against a certified 49.2 / 50.8; the ANES over-represents the losing side's voters by ~5 points, so group comparisons, not levels, are the object.

**Variables** (codes verified against the codebook PDF in the zip). Vote: `V242096x` (pre-post summary 2024 presidential vote), `V242095x` (turnout), `V241106x` (recalled 2020 vote), `V241107/V241108` (recalled 2016). Most important problem: open-ended, coded by ANES to Appendix B codes, up to three mentions × five ideas (`V242165y1–y5`, `V242167y1–y5`, `V242169y1–y5`); a "single most important" follow-up (`V242171y1`) asked only when more than one problem was given. Analytic MIP = `V242171y1` when present, else `V242165y1`. Family groupings are the script's `MIP_FAMILY` (economy/prices = codes 50, 54, 53, 15, 30; immigration = 41; democracy/govt = 43, 44, 45, 47, 48, 49, 78, 81, 39, 42, 80, 36; culture/moral = 61, 64, 66, 68, 75, 79, 32; etc.). Importance battery `V242172–V242181` (1 extremely – 5 not at all; illegal immigration, cost of living, climate, guns, abortion, crime, Gaza, schools, democracy, racial inequality). Party-better battery `V242182–V242189` (`V242190/V242191`, democracy and racial inequality, were PAPI-only, N ≈ 200, and are not used). Party better on own first-mentioned problem `V242166`. Anti-elite: `V241231` (few big interests), `V241233` (corrupt), `V241229` (trust govt), `V241120` (outraged), `V242200/V242201` (officials don't care / no say), `V242411` (strong leader), `V242413` (business leaders should run), `V242415` (referendums). Economic: `V241239` (services), `V241245` (govt vs private insurance), `V241252` (guaranteed jobs), `V242350` (minimum wage), `V241369x` (paid leave). Immigration: `V241395x` (wall), `V241392x` (Dreamers), `V241389x` (birthright), `V242227` (levels), `V242231x` (crime), `V242234x` (path to citizenship). Cultural: `V241372x` (trans bathrooms), `V241375x` (trans sports ban), `V242364x` (trans military), `V241288` (campus DEI), `V242349x` (diversity), `V241385x` (gay marriage), `V241302` (abortion). Thermometers `V241156/V241157/V241158/V242151`.

**Missing codes.** Negative values (−9 refused, −8 DK, −7/−5 partial, −6 no post interview, −4 error, −2 DK/RF in a component, −1 inapplicable) → NaN; 99 on 7-point scales ("haven't thought") → NaN; thermometer 998/999 → NaN. Post and panel weights are blank strings outside their universe and are coerced.

---

### A.10 New York City election districts, 2020–2025

**Sources.** NYC Board of Elections ED-level CSVs (`vote.nyc/sites/default/files/pdf/election_results/<year>/<date><event>/…EDLevel.csv`): President 2020 (pre-2022 district lines), President 2024, Mayor 2025 general. Ranked-choice contests are published only as round-by-round PDFs and a ballot-level cast vote record (`2025_Primary_CVR_2025-07-17.zip`, 32 spreadsheets, "AD: nn ED: nnn" precinct field, candidacy-id-to-name map); ED first choices and the Mamdani–Cuomo head-to-head are built from it. Department of City Planning election-district shapefiles `nyed_20d`, `24d`, `25b`, `25d` and 2020 census blocks `nycb2020_25d` (`s-media.nyc.gov/…/bytes/`). Census API: 2020 PL P1/P2 at block level; ACS 2023 five-year B19013, B15003, B17021, B25003 at block group.
**Script:** `src/data_collection/nyc_pull.py` → `data/raw/nyc/nyc_ed_panel.csv` (4,326 EDs × 35) with `prim25_cvr_by_ed.csv` cached.

**BOE format.** Every line of an ED-level CSV carries the eleven column headers as a prefix followed by the eleven data fields; parsed by position. Counter rows (Public Counter, Emergency, Absentee/Military, Federal, Affidavit, Scattered, Early Voting) are excluded from candidate totals. EDs whose status is "COMBINED INTO …" report zero and are dropped.

**Cast vote record.** Ranks 1–5 for Mayor; non-candidate codes (undervote/overvote) treated as blank; first valid rank = first choice; head-to-head = Mamdani ranked above Cuomo vs the reverse (ballots ranking neither excluded). ED first choices sum to 469,960 Mamdani / 387,664 Cuomo against certified first-round 469,984 / 387,748.

**2020 crosswalk.** 2020 EDs (5,838 polygons) → 2020 census blocks by block representative point → current EDs (nyed_25d). Each 2020 ED's votes are spread across its blocks in proportion to 2020 block population and summed within the current ED. 2,276,466 Biden / 684,780 Trump carried over, 98.2% / 99.0% of the BOE totals; the remainder sit in 2020 EDs with no populated block.

**Demographics.** Blocks assigned to nyed_25d EDs by representative point; race/Hispanic shares are block-population-weighted; block-group ACS income, BA share, poverty, and renter share are attached to each block and population-weighted to the ED. 4,193 EDs receive demographics.

**Boundary drift.** 2024 results are on nyed_24d lines, 2025 on 25b/25d, matched by AD-ED number; DCP revisions between versions are small, and the ≥ 50-vote filter in each contest removes most affected EDs.

---

### A.11 NYC Campaign Finance Board and historical mayoral returns

**CFB.** Independent expenditures have no bulk file; `src/data_collection/nyc_cfb_pull.py` scrapes the per-cycle summary (`vsapps/WebForm_Finance_Independent.aspx?as_election_cycle=YYYY`) for spender ids and each spender's detail page (`IndependentSpenderSummary.aspx?spender_id=…`) for the candidate × support/oppose/not-determined table and reported contributions; 2013 (50 spenders), 2017 (16), 2021 (41), 2025 (63). Output `data/raw/nyc_cfb/independent_expenditures_by_candidate.csv`. Candidate committees from the Data Library `EC{cycle}_FinancialAnalysis*.csv` (office code 1 = Mayor in 2013/2017/2025, 11 in 2021); `net_expnd`, `net_cntns`, `pubfnd_pmt`, `cntrs_no`, `sml_amt` (contributions ≤ $175 in 2021/2025, ≤ $250 earlier) → `mayor_candidate_finance_summary.csv`. Figures are as filed through the current statement (2025 page dated 2026-09-18).

**Historical returns.** `src/data_collection/nyc_history_pull.py`: 2017 general and Democratic primary (ordinary CSV format, no header prefix), 2021 general (header-prefixed), 2021 Democratic primary from the cast vote record (`PE2021_CVR_Final.zip`, same structure as 2025; first choices and Adams-vs-Garcia / Adams-vs-Wiley head-to-heads). All on the 2012 district lines (`nyed_17d`, `nyed_21d`); crosswalked to `nyed_25d` through 2020 blocks as in A.10. Carried: 2017 general 747k of 760k de Blasio; 2017 primary 449k of 461k; 2021 general 1,097k of 1,118k total; 2021 primary 925k of 944k ballots. 2013 is published only as PDF recaps and is not included. Citywide results 1989–2025 hand-entered from the certified figures on Wikipedia into `nyc_mayoral_generals_1989_2025.csv`.

**GDELT.** `src/data_collection/gdelt_nyc_pull.py`: DOC 2.0 API `timelinevol` and `timelinetone`, daily, per candidate-name phrase per source domain (nypost, foxnews, cnn, msnbc, nytimes, nydailynews, wsj, gothamist, thecity, all English), windows Jan 1–Nov 3 2021 and Jan 1–Nov 5 2025. The API enforces one request per five seconds and imposes a multi-minute penalty on violation; the script spaces requests at 15 s and resumes from its CSV.

---

### A.12 Justice Democrats endorsements and FEC primary finance

**Cases.** The Justice Democrats Wikipedia article's per-cycle endorsement tables (raw wikitext, `data/raw/insurgent/justice_democrats_wiki.txt`, parsed to `jd_house_endorsements_raw.csv`): 144 House rows 2018–2026 with primary date (2018 only), result, and vote share; 133 matched to FEC candidate ids (unmatched: D'Allesandro IA-3 2018, Treviño TX-23 2018, Gómez CA-53 2020; rowspan continuation rows dropped). Result overrides for runoffs and blanks: Cisneros 2022 lost the runoff 49.69%; Collins 2022 lost 45.72%; Newman 2022 lost 29.23%; Burch 2018 won the runoff.

**FEC** (`src/data_collection/fec_insurgent_pull.py`; api.open.fec.gov with a personal key — `DEMO_KEY` is 40 calls/hour). Candidate id by name/state/district/cycle search. Opponent: the Democratic incumbent in the district-cycle from `/candidates/totals/` (`incumbent_challenge == "I"`), else the best-funded other Democrat; for districts where the FEC still lists a retired or otherwise-running incumbent, an `OPEN_SEAT` override (Tlaib and Omar 2018; Sedillo Lopez, Matias, Vilela, Ing 2018; Turner 2021; Pearson, Rabb, Valdez, Chakrabarti, Abughazaleh, Haynes, Ahmed 2026) removes them. Primary date from `/election-dates/` (first House primary in the state-cycle) where the table lacks one. Pre-primary receipts = `total_receipts_ytd` on the last `/reports/house-senate/` filing on or before the primary date plus the prior calendar year's year-end YTD; unitemized likewise. Independent expenditures from `/schedules/schedule_e/by_candidate/` for the cycle, support and oppose summed over committees, top three opposing committees retained. All responses cached under `data/raw/insurgent/fec/`. Output `jd_cases_fec.csv`.

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

### I.6 The 2020 coalition and the reservoir

Notebook `13_coalition_2020_and_reservoir.ipynb`.

**CES 2020** (`CES20_Common_OUTPUT_vv.csv`; `presvote16post` 1 Clinton / 2 Trump / 7 did not vote; `CC20_410` 1 Biden / 2 Trump; `commonpostweight`). Hispanic = `race == 3` or `hispanic == 1` (race-3 respondents were not asked `hispanic`). Immigration index from `CC20_331a` (legal status, oppose), `331b` (border patrol, support), `331d` (cut legal immigration, support), `331e` (wall, support). `CC20_327a` Medicare-for-all, `CC20_350b` $15 minimum wage (1 = support/favor). N with 2020 major-party vote and 2016 status = 43,878. 2020 electorate by 2016 behavior: Clinton 42.0% (Biden 96.2%), Trump 40.3% (Trump 94.9%), other 4.2%, non-voter 13.5% (Biden 59.6%). Biden voters: Clinton 76.1%, non-voter 15.1% (N = 4,077), Trump 3.9% (969). Trump voters: non-voter 11.6%.

Profile by path (`outputs/tables/coalition_2020_by_2016_vote.csv`):

| Path | N | imm_cons | M4A | min wage $15 | abortion cons | econ perception | age | college | white | Hispanic | Black | <$50k | pid7 | validated |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Clinton→Biden | 19,159 | 0.18 | 87% | 92% | 0.15 | −1.54 | 51 | 45% | 58% | 14% | 21% | 42% | 1.76 | 77% |
| non-voter→Biden | 4,077 | 0.21 | 88% | 89% | 0.23 | −1.30 | 36 | 24% | 48% | 17% | 25% | 56% | 2.33 | 61% |
| Trump→Biden | 969 | 0.41 | 76% | 75% | 0.32 | −0.94 | 48 | 36% | 72% | 9% | 12% | 41% | 4.01 | 60% |
| Clinton→Trump | 498 | 0.58 | 56% | 66% | 0.50 | −0.26 | 47 | 34% | 53% | 20% | 18% | 45% | 4.21 | 64% |
| non-voter→Trump | 2,179 | 0.67 | 42% | 45% | 0.71 | −0.12 | 41 | 18% | 74% | 15% | 5% | 58% | 5.66 | 65% |
| Trump→Trump | 14,162 | 0.81 | 19% | 27% | 0.79 | +0.23 | 56 | 31% | 87% | 6% | 2% | 39% | 6.05 | 79% |

Immigration items 2020, conservative share, Clinton→Biden / non-voter→Biden / non-voter→Trump / Trump→Trump: oppose legal status 10 / 13 / 49 / 62; border patrol 35 / 36 / 88 / 96; cut legal immigration 17 / 24 / 56 / 73; wall 9 / 13 / 74 / 91.

Immigration-conservative (index ≥ 0.5) share of Biden 2020 voters by 2016 status (`reservoir_2020.csv`): Clinton 17.1% (M4A among them 83%), non-voter 23.8% (86%), Trump 49.7% (76%). Within the surge cohort, immigration-conservative (N = 910) vs rest (3,167): Black 34% vs 21%, white 36% vs 51%, Hispanic 16% vs 17%, age 40 vs 34, abortion-conservative 0.36 vs 0.19, econ perception −0.99 vs −1.40, M4A 86% vs 89% (`surge_cohort_split.csv`).

**CES 2024** (`presvote16post` recalled in 2024; 2024 immigration index from `CC24_323a/b/c`, `340f`, `323d`, cutoff 0.5). Recalled-Biden-2020 voters with validated 2024 vote and choice: N = 16,807, 334 switchers (`switchers_2024_by_2016_vote.csv`):

| 2016 vote | N | Share of Biden-20 voters | Share of switchers | imm-cons share | Switch rate | Switch if imm-cons | Switch if not |
|---|---|---|---|---|---|---|---|
| Clinton | 13,297 | 70.2% | 36.7% | 17.3% | 2.7% | 13.5% | 0.5% |
| Non-voter | 1,707 | 18.2% | 23.6% | 20.1% | 6.8% | 26.7% | 1.8% |
| Trump | 621 | 4.5% | 27.4% | 48.2% | 32.2% | 56.7% | 9.4% |

Reservoir (`reservoir_2024.csv`): immigration-conservative = 19.4% of Biden-2020 voters; switch rate 22.0% vs 1.2% for the rest; 81% of all switchers. By group: Hispanic (N = 221) 23.6%, Black (607) 15.2%, white (1,775) 23.2%; Medicaid-expansion support 78 / 92 / 84%. Switcher composition vs all Biden-2020 voters: Hispanic 17 vs 12%, Black 17 vs 17%, white 54 vs 63%.

The panel's Trump-2016 share of switchers (I.5: 4% weighted, 8 of 39) is superseded by the cross-section's 27%; recall bias toward the current vote makes 27% an upper bound.

**Robustness** (notebook 13 §3b; `reservoir_cutoffs.csv`, `reservoir_by_pid.csv`, `reservoir_2020_attitudes_panel.csv`). Cutoff: ≥ 0.4 → 42.0% of Biden-2020 voters, switch 11.1% vs 1.0%, 89% of switchers; ≥ 0.5 → 19.4% / 22.0% vs 1.2% / 81%; ≥ 0.6 → 19.3% / 22.1% vs 1.2% / 81%; ≥ 0.8 → 7.4% / 35.9% vs 2.8% / 51%. By party ID (reservoir share; switch reservoir vs rest): strong Democrat 13.8%, 3.7% vs 0.2%; weak/lean Democrat 18.6%, 9.4% vs 0.8%; independent 36.3%, 46.3% vs 3.3%; Republican-identifying Biden voters 63.5%, 74.7% vs 30.1%.

**Pre-switch version.** Panel, reservoir on 2020 attitudes (four 2020 items, cutoff 0.5), 2024 outcome; N = 1,684 Biden-2020 voters, 39 switchers: reservoir 16.7% of the coalition (N = 285); switch 13.5% weighted / 8.1% unweighted (23 events) vs 2.2% / 1.1% (16 events); 55.6% of switchers. At cutoff 0.75: 7.6% (N = 98), 19.9% vs 2.8%, 37.3% of switchers. Medicare-for-all support among the 2020-defined reservoir: 85%. The 2024-attitude figures (I.6 above) include concurrent attitude change; the 2020-attitude figures are the predictive estimate.

**2016 primary, all switchers.** Of the 2,121 Obama→Trump respondents (not only primary voters): 67% voted in a primary; Trump primary 30%, Sanders 15%, Clinton 14%, no primary or other 41%.

### I.7 Salience and anti-elite attitudes (ANES 2024)

Notebook `14_anes_salience.ipynb`. Data A.9; post weight `V240107b`; N = 4,964 with a post interview. Groups by recalled 2020 × 2024 vote: Biden→Harris 1,945; Biden→Trump 69; new (2020 non-voter)→Harris 166; new→Trump 198; Trump→Harris 58; Trump→Trump 1,437. Among Biden-2020 voters the weighted switch rate is 3.8% (CES cross-section 5.2%); among Trump-2020 voters 3.9% (CES 2.6%). Tables `anes_*.csv`.

**Most important problem** (single most important, family shares, row %; N with a coded MIP 1,863 / 62 / 158 / 186 / 1,349): economy/prices 17.7 / **34.8** / 21.5 / **34.5** / 31.1; immigration 3.3 / **16.2** / 5.8 / **19.6** / 31.0; democracy/govt 30.2 / 6.2 / 16.0 / 7.5 / 10.4; culture/moral 10.5 / 5.2 / 18.9 / 4.2 / 3.5; economy other 12.0 / 16.8 / 16.2 / 11.3 / 7.9. Top single codes among switchers: 54 inflation 29.1%, 41 immigration 16.2%, 800 other 12.0%, 55 economics (other) 11.5%. Any mention in up to three problems: economy/prices 33.7 / 59.9 / 42.2 / 57.4 / 65.5; immigration 17.2 / 36.4 / 23.2 / 39.2 / 63.3.

**Closed-ended importance** ("extremely important", %): cost of living 53.7 / 64.0 / 65.2 / 73.6 / 71.4; illegal immigration 19.7 / 33.9 / 21.6 / 60.7 / 71.7; democracy 77.1 / 33.3 / 54.2 / 42.9 / 58.2; abortion 48.9 / 29.6 / 47.5 / 30.6 / 27.7; racial inequality 46.3 / 23.4 / 48.8 / 20.1 / 12.5. Within-respondent, immigration rated above cost of living: 6.2 / **4.5** / 7.2 / 14.6 / 13.2; below: 60.5 / 38.3 / 67.7 / 28.5 / 14.0; tied: 33.3 / 57.2 / 25.1 / 56.8 / 72.8.

**Ownership** (Republicans better, %): cost of living 8.6 / **72.7** / 13.9 / **83.1** / 91.1 (Democrats 57.7 / 10.9 / 51.8 / 2.1 / 1.6); illegal immigration 17.8 / 86.8 / 24.1 / 85.7 / 94.5; crime 12.9 / 80.9 / 19.3 / 75.5 / 89.8; abortion 2.4 / 42.6 / 2.7 / 57.4 / 64.4. Party better on own first-mentioned problem: Republicans 4.1 / 69.7 / 5.6 / 83.6 / 90.5.

**Indices** (0–1; component items A.9, each rescaled so 1 = the named direction, mean of available items): anti-elite 0.48 / 0.62 / 0.53 / 0.58 / 0.62; economic-left 0.77 / 0.59 / 0.79 / 0.56 / 0.41; immigration-conservative 0.35 / 0.56 / 0.38 / 0.61 / 0.69; cultural-conservative 0.27 / 0.54 / 0.28 / 0.58 / 0.67. Single items: government run by a few big interests 76 / 95 / 85 / 82 / 92%; strong leader who bends rules (agree, 0–1) 0.24 / 0.58 / 0.32 / 0.53 / 0.59; prefers government insurance plan (scale ≤ 3) 71 / 46 / 76 / 37 / 17%; raise minimum wage 83 / 44 / 87 / 47 / 34%; transgender thermometer 68 / 44 / 69 / 37 / 34. Switcher minus loyal-Democrat gap in pooled SDs: anti-elite +0.87, economic-left −0.67, immigration +0.92, cultural +1.06. Share of switchers immigration-conservative (index ≥ 0.5): 60% (CES five-item index, I.6: 81%); among Biden→Harris 19%.

**Models** (weighted logit, HC1, Biden-2020 voters, indices standardized; `anes_switch_models.csv`). M1 (N = 1,951, 64 events): anti-elite 0.81 (SE 0.16), economic-left −0.39 (0.12), immigration 0.47 (0.15), cultural 0.86 (0.17). M2 adds MIP = immigration 1.23 (0.45) and MIP = prices 1.04 (0.30); attitude coefficients unchanged. M3 adds "Republicans better on prices" 2.52 (0.29); cultural falls to 0.57, MIP-immigration to 0.76 (p = 0.11), the rest hold. M4 (immigration and cultural only): 0.56 vs 1.13. Partition of Biden-2020 voters, immigration-conservative × MIP = immigration: neither 1.8% (N = 1,537, 20 events); position only 12.5% (317, 31); salience only 15.6% (40, 3); both 21.3% (31, 8). New voters, Trump vs Harris (N = 349): anti-elite 0.29 (0.18), economic-left −0.83 (0.20), immigration 0.77 (0.23), cultural 1.74 (0.25); mean age 35 vs 36; weighted Trump share 55% (CES 58%).

**Reading.** Salience and position give different answers, and both are in the report. On salience the switchers were price voters (2:1 over immigration; 4.5% immigration-first) who had adopted the Republican claim on prices (73%). On position they were the culturally conservative, anti-elite, immigration-conservative fifth, and those positions — not the priority given immigration — are what separates them from Democrats who stayed. All items post-election; the ownership items in particular are as much a rationalization of the vote as a cause, and a Trump voter credits Republicans on crime and abortion too.

### I.8 Corporate capture and lost trust (ANES 2024)

Notebook `15_corporate_capture.ipynb`. Sample, weight, and groups as I.7, plus Biden→stay-home (N = 142). Additional items (A.9 script, verified against the codebook): big-business thermometer `V242141`, labor unions `V242140`, "rich and powerful make it difficult to get ahead" `V242305` (1 not at all well – 5 extremely well; agree = 4–5), millionaire tax `V242316a`, campaign-spending limits `V242214`, party thermometers pre-election `V241166/V241167`, CSES like/dislike `V242432/V242433` (0–10), CSES left-right placement of the Democratic Party, Republican Party, and self `V242436/V242437/V242438` (0 left – 10 right; 95–98 missing). Tables `anes_anticorp_*`, `anes_antielite_items_switch.csv`, `anes_party_perception_by_group.csv`, `anes_ownership_shares_by_group.csv`, `anes_leavers_positions_by_selfplacement.csv`, `anes_capture_summary_by_group.csv`.

**Indices** (0–1). Anti-corporate: 1 − big-business thermometer/100, rich-and-powerful (rescaled), millionaire tax (favor), spending limits (favor). Anti-politician: few big interests, corrupt (all = 1), officials don't care, no say, trust government (never = 1). Strong-hand: strong leader who bends rules, business leaders should run things (agree = 1).

**By group** (loyal D / stay-home / Biden→Trump / new→Harris / new→Trump / Trump→Harris / loyal R): big-business thermometer 38.4 / 42.7 / 49.9 / 39.2 / 49.3 / 44.7 / 53.1; unions 70.6 / 59.3 / 55.6 / 68.8 / 52.9 / 64.1 / 50.9; rich-and-powerful agree 49 / 45 / 32 / 55 / 32 / 33 / 18%; millionaire tax 88 / 67 / 70 / 80 / 55 / 71 / 38%; spending limits 79 / 54 / 52 / 64 / 55 / 62 / 67%; business leaders should run 5 / 10 / 25 / 4 / 15 / 3 / 19%; strong leader 14 / 26 / 47 / 16 / 44 / 42 / 55%; never trust government 5 / 13 / 21 / 8 / 22 / 18 / 21%; few big interests 76 / 83 / 95 / 85 / 82 / 85 / 92%. Indices: anti-corporate 0.73 / 0.60 / 0.54 / 0.68 / 0.53 / 0.60 / 0.48; anti-politician 0.61 / 0.71 / 0.71 / 0.67 / 0.67 / 0.66 / 0.71; strong-hand 0.18 / 0.34 / 0.49 / 0.24 / 0.42 / 0.32 / 0.46. Switcher − loyal gap in pooled SD: anti-corporate −0.78, anti-politician +0.54, strong-hand +1.22.

**Models** (Biden-2020 voters, weighted logit, HC1, standardized). M1 (N = 1,937, 62 events): anti-corporate −0.37 (SE 0.12), anti-politician 0.63 (0.14), strong-hand 0.83 (0.12). M2 adds positions: anti-corporate −0.18 (0.14, p = 0.19), anti-politician 0.53 (0.15), strong-hand 0.63 (0.13), economic-left −0.26 (0.14), immigration 0.39 (0.15), cultural 0.84 (0.18). Item by item, each net of the three position indices: big-business thermometer +1.20 per 100 points (0.52); unions −1.27 (0.66); rich-and-powerful −0.22 (0.29); millionaire tax −0.16 (0.31); spending limits −0.67 (0.26); few big interests +2.00 (0.57); corrupt +0.26 (0.30); officials don't care +0.60 (0.34); no say −0.29 (0.27); never trust +1.21 (0.43); strong leader +1.02 (0.26); business leaders run +0.97 (0.30). Terciles of the anti-corporate index: switch 8.0% (N = 694, 45 events) / 2.9% (715, 17) / 1.5% (600, 7); anti-politician terciles 1.5 / 5.3 / 6.5%. Cross-classified, the low-anti-corporate × high-anti-politician cell switches at 14.9% (N = 182, 22 events); the high-anti-corporate × low-anti-politician cell at 0% (N = 145).

**Party perception.** Pre-election Democratic Party thermometer 73.2 / 62.3 / 36.4 / 64.0 / 22.2 / 51.9 / 14.8 (Republican 17.9 / 30.0 / 54.0 / 25.5 / 72.5 / 49.2 / 76.0); switchers at ≤ 30: 42%, 31–60: 46%, > 60: 12% (loyal: 4 / 25 / 71%). CSES left-right: self 3.8 / 5.6 / 5.9 / 4.3 / 7.0 / 5.1 / 7.7; Democratic Party 3.6 / 4.5 / 3.6 / 3.6 / 2.5 / 3.4 / 1.4; Republican Party 7.8 / 5.4 / 6.8 / 7.3 / 7.6 / 7.7 / 8.2; party spread 4.1 / 0.9 / 3.3 / 3.7 / 5.1 / 4.3 / 6.8; self minus Democrats +0.2 / +1.1 / +2.3 / +0.6 / +4.5 / +1.7 / +6.3. Switchers: 57% place the Democrats to their left, 35% at or to their right; 53% closer to Republicans, 18% equidistant, 21% closer to Democrats. Party better on own MIP, "no difference": 27 / 48 / 27 / 40 / 14 / 34 / 8%; mean "no difference" share across eight ownership items 0.25 / 0.41 / 0.23 / 0.29 / 0.22 / 0.27 / 0.16.

**Self-placement.** Left (0–3) / centre (4–6) / right (7–10): loyal Democrats 46 / 43 / 11%; switchers 13 / 48 / 39%; new→Trump 4 / 38 / 58%; loyal Republicans 2 / 22 / 76%. Among centrist leavers and new Trump voters (N = 99): government insurance 38%, raise minimum wage 50%, millionaire tax 63%, rich-and-powerful 44%, big-business thermometer 46; centrist Biden→Harris (N = 770): 58%, 75%, 83%, 38%, 43.

**Reading.** Anti-corporate sentiment is negatively associated with leaving the Democratic coalition and is zero net of positions; the switcher signature is strong-hand and distrust plus cultural conservatism. The switchers saw the Democrats as too far left (pre-election thermometer 36, placement 2.3 points left of self) and transferred rather than lost faith (70% Republicans on own MIP). The "no difference" profile belongs to the stay-home group. The ANES has no party-specific capture item ("the Democrats serve corporate donors"); the test is of general anti-corporate sentiment, which is necessary but not sufficient for the hypothesis.

---

## J. Part 9 — Cross-pressure, perceived difference, and the meaning of "left"

Notebook `16_crosspressure_and_perceived_difference.ipynb`. Tables `crosspressure_2024.csv`, `crosspressure_2016.csv`, `crosspressure_summary.csv`, `trump_share_by_dem_position_2024.csv`, `anes_perceived_candidate_gap.csv`, `anes_perceived_gap_by_group.csv`.

### J.1 Cross-pressure

CES 2024 validated voters with a major-party vote, N = 31,834, `vvweight_post`; indices as I.1; "economically left" = `econ_left` ≥ 0.5, "culturally conservative" = `cult_cons` ≥ 0.5. Cells (share of electorate; Trump share; N): econ-left × cult-lib 43.3%, 3.8%, 15,715; econ-left × cult-cons 20.0%, 67.6%, 5,841; econ-right × cult-cons 35.6%, 98.8%, 9,994; econ-right × cult-lib 1.1%, 44.3%, 284. Economically left: 63.3% of the electorate, Trump 24.0%; 29.8% of Trump voters, of whom 89.2% culturally conservative. **Cutoff sensitivity** (`crosspressure_2024_cutoff_sensitivity.csv`): with strict > 0.5 (a four-four split on the economic items and a 4.5 tie on the cultural items excluded), econ-left × cult-cons 13.0%, Trump 56.9%; econ-left × cult-lib 41.5%, 2.6%; econ-right × cult-cons 42.7%, 97.0%. 31,444 of 31,834 answered all eight economic items. Logit, all voters, standardized: econ_left −2.25 (SE 0.05), immig_cons 1.78 (0.04), social_cons 1.11 (0.03), police_cons 0.23 (0.03). Among economically-left voters (N = 21,555): immig_cons 1.61, social_cons 0.97, police_cons 0.38. Trump share among holders of each Democratic-aligned position (holder share of electorate): expand Medicaid 38.4% (75.8%), keep ACA 23.1% (60.2%), no work requirement 33.2% (45.5%), student loans 16.2% (48.7%), corporate tax 23.2% (57.4%), tax $400k+ 29.2% (62.7%), no 2017 cuts 16.3% (38.3%), housing 36.6% (70.5%), no wall 5.2% (44.3%), asylum 10.2% (34.9%), no more border patrol 8.3% (17.9%), legal status 24.6% (56.1%), Dreamers 32.4% (69.1%), abortion 20.4% (56.8%), marriage 30.9% (65.4%), no more police 19.5% (40.3%), defund 12.4% (24.5%).

CES 2016 (N = 40,850, `commonweight_vv_post`): economically left = keep ACA and/or $12 minimum wage (two items, ≥ 0.5); culturally conservative = mean of the four-item immigration index and the abortion item ≥ 0.5. Cells: econ-left × cult-lib 45.2%, 15.0%; econ-left × cult-cons 25.9%, 58.1%; econ-right × cult-cons 23.7%, 96.4%; econ-right × cult-lib 5.2%, 76.1%. 44.9% of Trump 2016 voters economically left; 68.9% of those culturally conservative. Logit: econ_left −1.59, immig_cons 1.22, social_cons 0.63. **Levels are not comparable across years** (two economic items vs eight), and the 2016 cells are fragile to the cutoff: strict > 0.5 requires both economic items and gives econ-left × cult-cons 5.2%, Trump 26.4%, econ-left × cult-lib 33.7%, 5.9%. The 2016 comparison is reported as a direction only.

### J.2 Perceived candidate difference (ANES)

Pre-election placements of self, Harris, and Trump on `V241245/V241246/V241247` (health insurance), `V241239/V241240/V241241` (services, reversed so 1 = left), `V241252/V241253/V241254` (guaranteed jobs), `V241248/V241250/V241251` (abortion); 99 → NaN. All respondents with a post weight (N = 4,964): placed both candidates 91.8 / 95.8 / 92.3 / 93.0%; Harris left of Trump 71.5 / 70.9 / 72.6 / 77.6% of all; same point 12.3 / 12.4 / 12.0 / 9.3%; reversed 8.0 / 12.4 / 7.6 / 6.1%; mean Trump − Harris gap among placers 2.8 / 2.4 / 2.8 / 3.3. By group (loyal D / stay-home / Biden→Trump / new→Harris / new→Trump / loyal R): health-insurance gap 3.24 / 2.17 / 1.81 / 2.53 / 2.36 / 3.27; services 3.64 / 2.05 / 1.84 / 2.64 / 0.50 / 2.05; jobs 3.36 / 2.64 / 1.38 / 2.86 / 2.16 / 3.24; abortion 4.03 / 3.44 / 2.89 / 3.56 / 2.51 / 3.37; mean economic gap 3.42 / 2.30 / 1.66 / 2.72 / 1.63 / 2.82. Cannot place one or both, health insurance: 5.3 / 11.3 / 11.3 / 6.3 / 12.5 / 7.4%. Harris at ≤ 3 on health insurance: 62 / 50 / 43 / 54 / 60 / 76%; Trump at ≥ 5: 84 / 65 / 54 / 74 / 56 / 69%. Own position closer to Trump than to Harris on the mean of the three economic scales, among those placing self and both candidates on all three (loyal N = 1,555, switchers N = 46, stay-home N = 98): closer to Trump 7 / 67 / 15%, equidistant 1 / 10 / 11%, closer to Harris 92 / 23 / 74%. Mean placements (health insurance / services / jobs, 1 = government pole): loyal self 2.6 / 2.5 / 3.1, Harris 3.0 / 2.5 / 3.0, Trump 6.2 / 6.1 / 6.3; switchers self 3.7 / 3.7 / 4.2, Harris 3.1 / 2.7 / 3.2, Trump 4.9 / 4.4 / 4.6. An earlier draft reported 53% for the switchers; that figure treated respondents missing a placement as not closer to Trump and is superseded. Switching logit among Biden-2020 voters (N = 1,922, 63 events; standardized): econ_gap −0.42 (0.14), abortion_gap −0.12 (0.11), econ_left −0.29 (0.12), immig_cons 0.51 (0.13), culture_cons 0.96 (0.18).

### J.3 What self-placement measures

ANES `V242438` self (0–10) on standardized indices (WLS, HC1, N = 4,644, R² = 0.43): econ_left −0.16 (0.07), immig_cons 0.71 (0.07), culture_cons 1.14 (0.07). Democratic Party placement `V242436` (N = 4,625, R² = 0.09): econ_left +0.54, immig_cons −0.06, culture_cons −0.33. Republican Party `V242437` (R² = 0.02): −0.45 / −0.12 / −0.35. Among Biden-2020 voters, self minus Democratic Party (N = 1,912, R² = 0.12): econ_left −0.44 (0.11), immig_cons −0.08 (0.13), culture_cons +0.65 (0.11). CES 2024 `CC24_330a` self-ideology (N = 31,366, R² = 0.69): econ_left −0.59 (0.02), immig_cons 0.48 (0.02), social_cons 0.56 (0.02), police_cons 0.28 (0.02). Harris placement `CC24_330d` (N = 30,818, R² = 0.41): +0.35 / −0.29 / −0.14 / −0.11.

**Media.** Biden-2020 voters, CES 2024 (N = 16,251): Harris placement on positions, `pid7`, and `CC24_300b_4/5/6` (CNN / Fox / MSNBC watched yesterday): R² = 0.04; Fox −0.14 (SE 0.10, p = 0.17). Share placing Harris "very liberal": Fox 23.8% vs 8.6%; within immigration-conservative Biden voters 40.6% vs 22.2%. Switching logit (299 events): econ_left −0.54, immig_cons 0.75, social_cons 0.41, police_cons −0.20, pid7 0.70, Fox +0.96 (0.17), MSNBC −1.48 (0.23), CNN +0.10 (0.16), Harris placement −0.48 (0.07). The Fox coefficient equals about 1.4 points on the seven-point party scale (0.96 / 0.70); the binary and the scale are not otherwise comparable. Diet, not exposure to any story; association, not effect.

---

## K. Part 10 — New York City precinct overlap

Notebook `17_nyc_precinct_overlap.ipynb`. Data A.10. Usable EDs: ≥ 50 two-party votes in 2020 (crosswalked), 2024, and 2025, not combined, populated: N = 3,870. Citywide on usable EDs: Trump 23.1% (2020) → 31.0% (2024), swing +7.9; Mamdani 51.0% of the mayoral vote, 55.3% of Mamdani + Cuomo, Sliwa 7.0%; primary head-to-head Mamdani 56.6%. Tables `nyc_by_swing_decile.csv`, `nyc_by_trump_decile.csv`, `nyc_by_majority.csv`, `nyc_by_majority_x_income.csv`, `nyc_within_group_models.csv`, `nyc_mamdani_vs_harris_by_swing_decile.csv`, `nyc_mamdani_minus_harris_models.csv`, `nyc_vote_composition_by_majority.csv`; figure `nyc_trump24_vs_mamdani25.png`.

**Correlations** (weighted by 2024 two-party votes): Mamdani share of the mayoral vote with 2024 Trump share −0.80, with the 2020→24 swing −0.10; Mamdani vs Cuomo −0.76 / −0.07; Sliwa +0.74 / +0.14; primary head-to-head −0.31 / −0.05; Mamdani first choices −0.18 / +0.11; corr(swing, 2024 level) +0.36.

**Swing deciles** (1→10; each N = 387): swing −0.3 / 2.6 / 3.6 / 5.1 / 6.9 / 8.2 / 10.3 / 13.0 / 15.9 / 24.0 points; Harris 2024 84.0 / 79.8 / 77.4 / 70.8 / 65.1 / 64.3 / 61.6 / 61.6 / 60.9 / 53.9%; Mamdani Nov 63.8 / 56.3 / 52.6 / 47.9 / 45.4 / 44.4 / 44.0 / 48.0 / 50.0 / 53.5%; Mamdani − Harris −20.2 / −23.5 / −24.7 / −22.8 / −19.6 / −19.9 / −17.6 / −13.6 / −10.9 / −0.4; Cuomo + Sliwa 35.7 / 43.2 / 46.8 / 51.5 / 54.0 / 55.0 / 55.3 / 51.3 / 49.3 / 45.8% against Trump 2024 16.0 / 20.2 / 22.6 / 29.2 / 34.9 / 35.7 / 38.4 / 38.4 / 39.1 / 46.1%; Mamdani vs Cuomo Nov 66.4 / 59.5 / 56.1 / 52.2 / 50.2 / 49.2 / 49.1 / 52.9 / 54.6 / 57.9%; primary head-to-head 67.2 / 59.3 / 55.1 / 53.7 / 55.2 / 52.4 / 50.2 / 52.5 / 51.8 / 57.3%; Nov 2025 votes per 2024 vote 0.90 / 0.85 / 0.82 / 0.81 / 0.80 / 0.79 / 0.77 / 0.75 / 0.71 / 0.88; primary ballots per 2024 vote 0.58 … 0.30 / 0.40. Decile 10 composition: Hispanic 45%, Asian 28%, white 14%, Black 8%; median income $78k; BA 26%. Decile 1: white 53%, Black 19%; $128k; BA 62%.

**By majority group** (Hispanic / Asian / Black / mixed / white; N 723 / 226 / 628 / 1,060 / 1,233): swing +13.6 / +14.8 / +4.5 / +8.6 / +4.9; Harris 70.2 / 53.1 / 89.9 / 69.3 / 61.6%; Mamdani Nov 58.4 / 46.5 / 63.6 / 57.7 / 41.3%; Mamdani vs Cuomo Nov 62.6 / 52.3 / 65.9 / 62.5 / 45.3%; primary head-to-head 55.3 / 61.4 / 43.7 / 64.6 / 56.2%; Mamdani first choice 48.3 / 53.5 / 35.4 / 52.9 / 39.2%, Cuomo first 40.3 / 33.8 / 48.8 / 29.9 / 33.7%; Nov 2025 per 2024 vote 0.69 / 0.79 / 0.67 / 0.81 / 0.92; primary per 2024 vote 0.35 / 0.30 / 0.38 / 0.40 / 0.43. Income terciles within group in `nyc_by_majority_x_income.csv`; low-income Hispanic (N = 490): swing +13.7, Mamdani 56.3%, vs Cuomo 60.2%, primary 47.9%; mid-income Hispanic (173): 63.2%, 68.0%, 68.6%; low-income white (120): swing +5.2, Mamdani 21.9%.

**Within-group WLS** (weights 2024 two-party votes; HC1; regressors swing, 2020 Trump share, log income, BA share, Hispanic / Black / Asian shares). Dependent Mamdani vs Cuomo (Nov), coefficient on swing (SE): Hispanic −0.32 (0.10), Asian +0.03 (0.10), Black −0.62 (0.21), mixed −0.33 (0.08), white −0.47 (0.08), all −0.62 (0.06); on 2020 Trump share −1.18 / −1.48 / −1.65 / −1.18 / −0.83 / −0.86. Primary head-to-head: swing −0.40 / +0.26 / −0.21 / −0.21 / −0.16 / −0.40. Dependent Mamdani Nov share − Harris 2024 share, swing coefficient: Hispanic +0.66 (0.10), Asian +1.05 (0.10), Black +0.37 (0.21), mixed +0.66 (0.08), white +0.53 (0.07), all +0.41 (0.05); R² 0.57 / 0.59 / 0.58 / 0.32 / 0.49 / 0.35. Turnout ratio (Nov 2025 / 2024) on swing: white +6.2 (0.5), Black +7.7 (2.3), mixed +3.3 (0.6), Hispanic −0.4 (0.7), Asian +0.6 (0.2).

**Composition of citywide vote** by ED majority (Hispanic / Asian / Black / mixed / white): Harris 2024 15.6 / 3.8 / 20.8 / 26.1 / 33.7%; Trump 2024 14.8 / 7.5 / 5.2 / 25.8 / 46.8%; Mamdani Nov 15.1 / 4.4 / 16.4 / 29.5 / 34.6%; Cuomo Nov 11.1 / 4.9 / 10.5 / 21.9 / 51.6%; Sliwa 11.0 / 7.1 / 4.9 / 26.1 / 51.0%; Mamdani primary first choices 14.7 / 4.6 / 12.4 / 31.5 / 36.7%; Cuomo first choices 15.0 / 3.5 / 21.0 / 21.8 / 38.7%.

**Reading.** The level and the change tell different but compatible stories. In level, the 2024 swing carries a residual against Mamdani within group (−0.3 to −0.6 per unit) and the 2020 Trump level dominates (−0.8 to −1.6). Against the 2024 baseline, the swing predicts recovery in every group (+0.4 to +1.05), and in the tenth swing decile Mamdani's November share equals Harris's while Cuomo + Sliwa equals Trump's. The Mamdani − Harris measure is partly mechanical where Harris was very high (Cuomo drew moderate Democrats in decile 1), which is why the within-group models control for the 2020 level and composition.

### K.2 Money, media, and the 2017–2021 coalitions

Notebook `18_nyc_money_media_history.ipynb`. Data A.11. Tables `nyc_ie_by_candidate.csv`, `nyc_money_sides.csv`, `nyc_history_by_majority.csv`, `nyc_history_by_swing_decile.csv`, `nyc_history_by_income.csv`, `nyc_history_correlations.csv`; figure `nyc_three_mayors_by_swing.png`.

**Independent expenditures on Mayor, support / oppose ($M).** 2013: Thompson 3.08 / 0; Quinn 0.83 / 1.00; Lhota 0.52 / 1.04; de Blasio 0.51 / 0.02. 2021: Adams 8.04 / 0.01; Donovan 6.49 / 0; McGuire 5.75 / 0; Stringer 4.75 / 0; Yang 3.85 / 0.17; Wiley 1.98 / 0. 2025: Cuomo 31.02 / 1.67; Mamdani 4.83 / 21.93; Sliwa 0.79 / 2.82. 2025 spenders: Fix the City 19.30 for Cuomo, 10.63 against Mamdani, 0.89 against Sliwa (contributions reported $35.6M); For Our City 2.51 for Cuomo / 4.85 against Mamdani; Stop the Socialists 1.79 / 2.14 (+1.52 against Sliwa); Defend NYC 2.49 / 2.21; Housing for All 2.50 for Cuomo; New Yorkers for Lower Costs 2.72 for Mamdani; WFP 0.98 against Cuomo. Total mayoral IE: 2013 ≈ 9, 2021 ≈ 27, 2025 ≈ 83.

**Committees ($M spent; contributors; small-dollar share).** 2013 de Blasio 13.5 (12,267; 7%), Quinn 6.9, Thompson 6.5. 2021 Adams 18.3 (15,483; 14%), McGuire 11.9, Yang 10.5, Stringer 10.2, Garcia 8.6, Wiley 7.6. 2025 Mamdani 16.4 (40,835; 55%; public funds 13.2), Cuomo 14.1 (10,400; 14%; public funds 8.1), Lander 8.2, Sliwa 6.9. Sides (committee + IE for + IE against the other): 2013 de Blasio 15.1 vs Quinn 7.7 / Thompson 9.6; 2021 Adams 26.3 vs Garcia 8.6 / Yang 14.3; 2025 Mamdani 22.9 vs Cuomo 67.0 (ratio 2.92).

**Coalitions** (3,790 EDs usable in all of 2017, 2020, 2021, 2024, 2025). By swing decile 1 … 10: de Blasio 2017 general 74.5 / 70.7 / 68.7 / 63.3 / 59.9 / 58.8 / 62.2 / 67.1 / 70.9 / 72.5%; Adams 2021 general 78.3 / 74.2 / 72.7 / 65.5 / 61.2 / 59.3 / 59.6 / 62.7 / 64.9 / 68.5%; Harris 84.4 … 54.2%; Mamdani 64.1 / 56.1 / 52.7 / 47.8 / 45.9 / 43.7 / 44.5 / 47.9 / 49.5 / 53.6%; Adams vs Garcia 2021 primary 33.7 / 45.7 / 49.2 / 53.2 / 51.4 / 53.5 / 59.0 / 60.3 / 62.0 / 51.8%; Adams vs Wiley 40.2 … 57.8%; Wiley first choices 29.3 … 16.4%; Mamdani vs Cuomo 67.5 / 59.1 / 55.1 / 53.5 / 55.2 / 52.5 / 50.2 / 52.5 / 51.6 / 57.1%. By majority (Hispanic / Asian / Black / mixed / white): de Blasio 2017 83.1 / 54.2 / 92.0 / 68.5 / 50.1; Adams 2021 75.8 / 51.6 / 90.9 / 66.9 / 57.8; Mamdani 58.4 / 46.5 / 63.6 / 57.7 / 41.3; Adams vs Garcia 62.4 / 45.7 / 84.1 / 50.0 / 29.4; Adams vs Wiley 59.9 / 56.6 / 71.3 / 50.7 / 45.6; Mamdani vs Cuomo 55.3 / 61.4 / 43.8 / 64.6 / 56.2. ED-level correlations weighted by 2025 votes: Mamdani general with de Blasio 2017 0.80, Harris 0.79, Adams 2021 0.72, Wiley first 0.81; Mamdani primary head-to-head with Wiley first 0.82, with Adams-vs-Wiley −0.84, with Adams-vs-Garcia −0.54, with Harris 0.39. General votes 2025 / 2021: Hispanic 2.10, Asian 2.00, mixed 2.09, white 1.99, Black 1.66. Primary ballots 2025 / 2021: white 1.25, mixed 1.19, Hispanic 1.13, Black 0.97, Asian 0.92; income terciles low 1.02, mid 1.14, high 1.24.

---

## K-bis. Part 11 — Insurgent primaries

Notebook `19_insurgent_primaries.ipynb`. Data A.12. Money in $M; "side" = pre-primary receipts + IE for + IE against the other. Contested = JD vote share < 99%. Tables `insurgent_winrate_by_money.csv`, `insurgent_challengers_vs_incumbents.csv`, `insurgent_models.csv`.

**Counts.** 133 cases, 111 contested: JD incumbent 28 (25 won), challenger vs incumbent 24 (11), open/other 59 (21). By cycle (contested N, wins, outspent share): 2018 58 / 18 / 66%; 2020 12 / 9 / 42%; 2021 1 / 0; 2022 11 / 8 / 18%; 2024 7 / 5 / 29%; 2026 22 / 17 / 36%. Win rate by outspent: JD incumbent not outspent 25/25, outspent 0/3 (mean share 38.8%); challenger not outspent 1/5 (mean 48.0%), outspent 10/19 (39.6%); open not outspent 12/26 (36.0%), outspent 9/33 (26.2%). Median opponent:JD money ratio 0.01 / 2.41 / 1.28.

**Challenger cases** (JD pre-primary $M, opponent $M, IE against JD $M, ratio, result): Pressley–Capuano 0.90 / 2.08 / 0 / 2.4 W; Ocasio-Cortez–Crowley 0.37 / 5.54 / 0.63 / 16.0 W; Newman–Lipinski 2018 1.60 / 1.63 / 0.93 / 0.8 L; Bush–Clay 2018 0.09 / 0.66 / 0 / 7.1 L; Rao–DeGette 0.45 / 1.30 / 0 / 2.9 L; S. Smith–A. Smith 0.09 / 0.92 / 0 / 10.3 adv.; Clark–Davis 0.12 / 0.39 / 0 / 3.3 L; Mustafa–Quigley 0.21 / 1.74 / 0 / 8.3 L; Richardson–Murphy 0.06 / 3.87 / 0 / 40 L; Bowman–Engel 1.33 / 3.20 / 0.81 / 2.1 W; Bush–Clay 2020 0.75 / 1.27 / 0.02 / 1.3 W; Cisneros–Cuellar 2020 2.31 / 3.34 / 0.07 / 0.9 L; Newman–Lipinski 2020 2.89 / 2.27 / 0.01 / 0.6 W; Morse–Neal 1.66 / 6.54 / 1.23 / 2.7 L; Harper–Beatty 1.33 / 3.50 / 0 / 2.7 L; Cisneros–Cuellar 2022 2.33 / 3.93 / 1.44 / 0.6 L; Collins–Davis 2022 0.95 / 0.79 / 0 / 0.9 L; Kiros–DeGette 1.30 / 2.42 / 0.68 / 2.5 W; McKinney–Thanedar 2.13 / 3.34 / 0.27 / 1.7 W; Avila Chevalier–Espaillat 1.07 / 3.23 / 1.53 / 2.6 W; Allam–Foushee 0.92 / 0.93 / 0 / 1.1 L; Bush–Bell 2026 5.53 / 4.85 / 3.60 / 1.7 L; Vang–Matsui 1.10 / 3.71 / 0 / 2.1 adv.; Gonzales-Torres–Gomez 0.33 / 1.92 / 0 / 5.7 adv.

**Incumbent losses.** Bowman 2024: IE against 12.04 (UDP 9.87, Fairshake 2.08), side 8.8 vs 24.8; Bush 2024: 7.34 (UDP 5.24, Fairshake 1.41, Mainstream Democrats 0.60), 7.3 vs 17.5; Newman 2022: 0.50 (DMFI), member-vs-member after redistricting.

**Opposing committees** (sum of top-three-per-case tallies, $M): UDP 22.45 (two spellings), Congressional Leadership Fund 6.30, Fairshake 3.49, DMFI 2.97, NRCC 2.66, Americans for Tomorrow's Future 2.42, Chicago Progressive Partnership 1.84, Bold America 1.52. Win rate with > $250k against: 11/21 (52%); without 47/90 (52%).

**Models** (contested, N = 111, HC1). OLS vote share: log(opponent:JD ratio, clipped 0.05–50) −6.85 (SE 1.30); log1p(IE against, $M) +4.85 (3.46); challenger-vs-incumbent +15.2 (3.2); JD incumbent +18.5 (5.0); 2022+ +2.7 (3.2). Logit win: −0.48 (0.19); −0.44 (0.61); +0.75 (0.58); +1.54 (0.76); +0.77 (0.55). Small-dollar (unitemized) share of pre-primary receipts, medians: JD incumbents 0.28 vs opponents 0.05; challengers 0.39 vs 0.02; open 0.35 vs 0.12; winners 0.34 vs losers 0.35; pre-primary receipts winners $2.09M vs losers $0.50M; money ratio 0.35 vs 1.60.

---

## L. Limitations

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
27. **Recalled 2016 vote in the 2024 file favors the current vote.** A 2024 Trump voter is more likely to recall a 2016 Trump vote. The 27% Trump-2016 share of switchers is an upper bound; the panel's 4% (eight people, low weights) is a lower bound. The reservoir result does not depend on 2016 recall.
28. **The ANES salience results rest on 69 switchers.** Every switcher percentage in I.7 carries roughly a ±10-point interval; the logits are indicative. The ANES also over-represents Harris voters by ~5 points and under-recruits the young, weakly attached voters who make up the new-voter groups. Salience, importance, and ownership are all post-election and cannot separate reason from rationalization; the CES panel's timing test (F.3, I.5) does not extend to salience because the CES does not ask it. MIP family assignments are the script's own; reassigning borderline codes (32 race relations, 37 justice, 55 economics-other) does not change the prices-vs-immigration comparison.
29. **The capture test is indirect.** No survey on disk asks whether the *Democrats* are beholden to corporate interests; I.8 tests whether general anti-corporate sentiment predicts leaving them, and finds the opposite sign. A voter could believe both parties are captured and leave for other reasons; the strong-hand and distrust items that do predict leaving are consistent with an anti-system reading that is not specifically anti-corporate. Sixty-two to sixty-nine events across a dozen items; the per-item coefficients in I.8 should be read as a pattern, not individually.
30. **The cross-pressure cells depend on the cutoff and on which items the CES asks.** Counting four-four ties as "left" gives a 20% cross-pressured cell voting 68% Trump; excluding them, 13% voting 57%. The ordering — economically-left cultural liberals near-unanimous for Harris, economically-left cultural conservatives majority Trump — holds under both; the shares are a range, not a point. The 2016 economic index is two items and its cells collapse under a strict cutoff; 2016 is a direction, not a measurement.
31. **Candidate placements are pre-election but not pre-decision.** Most ANES pre-election interviews are in September–October; a switcher who had decided by then may place Trump nearer to themselves as a consequence. The perceived-gap coefficient in J.2 cannot separate "did not see the contrast" from "had already chosen."
32. **The New York comparison is ecological, single-city, and cross-electorate.** ED co-movement does not identify individuals; the 2024 swing in the outer-borough districts was partly Democratic abstention (Part 7), and 2025 could be return rather than conversion. The November 2025 electorate was 78% of the presidential electorate (92% in white-majority districts, 67% in Black); the primary was registered Democrats. Cuomo carried Trump's endorsement, so Cuomo + Sliwa is a Trump-coalition proxy, not a measurement. The 2020 baseline is crosswalked and carries interpolation noise in small EDs; "Mamdani − Harris" is bounded above where Harris was near 90%. Funding and media coverage are not measured here.
33. **Cross-cycle mayoral shares are not like-for-like.** 2017 and 2021 were two-way races against Republicans who drew 27–28%; 2025 was a three-way race in which the Trump-endorsed independent drew 41% and the Republican 7%. The decline in the Democratic nominee's share in the outer-borough districts between 2021 and 2025 is partly the different opponent; the Mamdani-vs-Cuomo two-way share is the closer comparison and shows the same direction. IE totals count only CFB-reported spending; GDELT tone is a lexicon score, not audience exposure.
34. **The insurgent-primary universe is Justice Democrats' endorsement list,** which changed character across cycles (broad 2018 slate, targeted later slates), so the cycle trend in win rate is partly selection. Opponents are identified mechanically; open-seat "opponents" are one of several. Pre-primary receipts are the last filing before the primary (self-funding counts as receipts — Thanedar 2026). IE totals are cycle totals and include general-election spending for incumbents. 2026 FEC data is partial. Twenty-four challenger cases and three incumbent losses are the whole basis of the incumbent-vs-money finding.

---

## M. Reproducibility

### M.1 Environment

Python 3.8 virtual environment at `.venv`; dependencies in `requirements.txt`. Register the kernel once:

```bash
python -m ipykernel install --user --name dnc-autopsy --display-name "Python (dnc-autopsy)"
```

### M.2 Pipeline

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
| 20 | `13_coalition_2020_and_reservoir.ipynb` | step 9 | tables |
| 21 | manual browser download of the ANES 2024 zip (A.9), then `python src/data_collection/anes_pull.py` | `data/raw/anes/*.zip` | `data/raw/anes/anes_2024_core.csv` |
| 22 | `14_anes_salience.ipynb` | step 21 | tables |
| 23 | `15_corporate_capture.ipynb` | step 21 | tables |
| 24 | `16_crosspressure_and_perceived_difference.ipynb` | steps 9, 21 | tables |
| 25 | `python src/data_collection/nyc_pull.py` | BOE, DCP, Census API (≈25 min; the cast vote record is cached after the first run) | `data/raw/nyc/nyc_ed_panel.csv` |
| 26 | `17_nyc_precinct_overlap.ipynb` | step 25 | tables, figure |
| 27 | `python src/data_collection/nyc_cfb_pull.py`; `python src/data_collection/nyc_history_pull.py`; `python src/data_collection/gdelt_nyc_pull.py` | CFB, BOE, DCP, GDELT (history ≈25 min for the 2021 CVR; GDELT ≈1 h at the rate limit) | `data/raw/nyc_cfb/*.csv`, `data/raw/nyc/nyc_ed_history.csv`, `data/raw/gdelt_nyc/gdelt_nyc_daily.csv` |
| 28 | `18_nyc_money_media_history.ipynb` | steps 25, 27 | tables, figures |
| 29 | `python src/data_collection/fec_insurgent_pull.py` (needs `FEC_API_KEY`; JD wikitext fetched by hand from `?action=raw`) | FEC API | `data/raw/insurgent/jd_cases_fec.csv` |
| 30 | `19_insurgent_primaries.ipynb` | step 29 | tables |

Execute notebooks non-interactively with the project kernel:

```bash
jupyter nbconvert --to notebook --execute notebooks/0N_*.ipynb --inplace --ExecutePreprocessor.kernel_name=dnc-autopsy
```

### M.3 Keys

Copy `.env.example` to `.env` and set `FRED_API_KEY` and `CENSUS_API_KEY`. Never commit `.env`. The CES and BLS pulls need no key; the ANES pull needs the zip placed by hand (A.9); the NYC pull needs `CENSUS_API_KEY`; the FEC pull needs `FEC_API_KEY` (free personal key; `DEMO_KEY` is 40 calls/hour).

---

## N. Next steps

Part 4 established that perception is disconnected from local reality and travels with media diet and with vote switching. The news-environment instrument failed (E.9, first-stage F = 0.64). Part 5 then used the panel to put perception two years ahead of the vote, which is as far as the CES can take the timing question. What remains:

1. **The 2022 common cause.** The panel's 2022 wave carries the items needed to probe whether Biden voters who rated the economy badly in 2022 were already moving on non-economic grounds: 2022 presidential approval (`CC22_320a`), 2022 issue items, and the 2022 House vote (`CC22_412`; candidate names are state-specific, so party must be recovered from the candidate-party fields). A Biden voter who rated the economy "much worse" in 2022 but still voted Democratic in the 2022 House election, and then switched in 2024, is a cleaner case than one who had already defected by 2022. With 39 events this is a cross-tab, not a model, but it is the right cross-tab.
2. **A local price measure.** The prices item is the least partisan perception in the survey and predicts switching net of the economy rating in both the cross-section (E.8) and the panel (F.3), but there is nothing to set it against. BEA regional price parities or ACS 1-year rent would allow a prices gap — perceived minus measured.
3. **More panel.** The 2020–2022 panel (`doi:10.7910/DVN/XV7ABM`) is a different, larger recontact of 2020 respondents; whether any of its members also appear in the 2020–2024 file is undetermined. If so, pooling adds 2022 observations but not 2024 outcomes.
4. **The delivery mechanism.** Delivery moved the county vote (G.3) without moving perception, and the component test (G.3 v) shows it is a share effect, not turnout — Republican vote growth was lower where infrastructure money went. Two things would narrow it further: (a) a local-conditions perception — the CES has no "your area's economy" item, but the household-income item (`CC24_302` in the common content) is the closest available and could be tested against delivery the way the national item was; (b) the composition of the Republican vote growth — whether it is new voters or switchers, which the CES cross-section cannot separate but a county-level comparison of validated new registrants (L2 or TargetSmart aggregates) against delivery could.
5. **The Hispanic shift.** Part 6 reframes the 2024 class gradient as ethnic. The CES 2024 has the sample to go further (1,890 Hispanic Biden voters): by nativity and language of interview if available, by 2022 perception in the panel (too few), and by whether the prices item carries the switching effect for Hispanic voters as it does overall.

The reduced-form association between living in a news desert and switching does not survive Medill's desert definition and should not be pursued.

6. **Salience — done (I.7).** The ANES 2024 shows the switchers prioritized prices over immigration two to one and had adopted the Republican claim on prices. What would extend it: the 2016–20–24 ANES panel subsample (2,171 respondents, ids `V200001`/`V160001_orig`) merged to the 2020 and 2016 Time Series files, which would put the anti-elite and cultural items — which the CES does not carry — ahead of the switch the way F.3 does for economic perception.

7. **The corporate-capture hypothesis — tested in I.8; the strong form fails.** Remaining: Working hypothesis: Democrats came to be seen as beholden to corporate elites; that perception, not policy positions, cost them the trust of economically-left, anti-elite voters and left a vacuum Trump filled. I.7 is consistent with it — 95% of switchers say government is run by a few big interests, switchers are +0.87 SD anti-elite, and 73% had transferred the prices issue to Republicans — but it is not yet a test. Done in I.8: item decomposition, `V242166` no-difference, party thermometers and placement. Still open: (d) the 2016–20–24 panel subsample merged to the 2020 and 2016 files, to put the anti-elite items *before* the switch. Outside the ANES: FEC corporate/PAC receipts by candidate and cycle as the "actual" side of the perception gap, and the Pew/Gallup "which party cares about people like me" series for the trend since 2016.

8. **Insurgent primaries — studies A and B.** Part 10 answered the precinct question for New York. Still open: (A) a case dataset of Democratic primaries with a DSA / Justice Democrats-type challenger, 2018–2026, with FEC receipts, small-dollar share, and independent expenditures for and against (AIPAC/UDP, crypto PACs), to test whether insurgents win against a funding deficit and whether outside spending against predicts loss; (B) GDELT coverage volume and tone by source domain (foxnews.com, cnn.com, msnbc.com, nytimes.com) for each insurgent and opponent in the primary window, with establishment-vs-establishment primaries as the control, to test "smeared by all sides." Both need the 2026 primary results, which postdate the analyst's knowledge and must be pulled from the web.

CDC WONDER overdose mortality remains a planned Part 3 covariate; nothing in Part 4 depends on it.
