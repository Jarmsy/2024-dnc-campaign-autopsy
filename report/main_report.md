# 2024 DNC Campaign Autopsy: A Data-Driven Analysis

*Unit of analysis: national election (Part 1), county (Parts 2–3), survey respondent in county (Part 4) · Elections covered: 1948–2024*
*Data: MIT Election Lab · FRED · Census ACS 2020 · BLS QCEW · Gallup · Cooperative Election Study*

---

## Executive summary

Kamala Harris lost the 2024 presidential election with **49.25% of the two-party popular vote**, down from Biden's 52.27% in 2020. Democrats received 6.25 million fewer votes than in 2020 in an electorate that was 3.3 million votes smaller. This report examines that result through four lenses: what structural conditions predicted, how the vote loss decomposes geographically, what county economic characteristics explain the shift, and — linking 60,000 survey respondents to their counties — whether voters perceived the economy their county actually had.

**Four findings:**

| | Finding |
|---|---|
| **Part 1** | A fundamentals model fit on 1948–2020 predicted Harris at 47.9%. She received 49.25%. The +1.4pp residual is well inside the model's 3.75pp out-of-sample error — she performed **about as the fundamentals predicted**, not meaningfully better or worse. |
| **Part 2** | The shift was near-universal: 90% of counties and all 51 states moved right. Nationally, **73% of the Democratic vote loss came from share shift and 27% from lower turnout**. But the largest raw losses were in Democratic strongholds, and there the mechanism was turnout. |
| **Part 3** | County income, education, and racial composition explain about 42% of the variance in county swings. The gap between Democratic performance in rich and poor counties, relative to 2012, widened from +5.0pp (2016) to +9.4pp (2020) to +9.9pp (2024). Harris inherited that gradient; she did not create it. Manufacturing exposure and real wage growth over the Biden term explain essentially nothing. |
| **Part 4** | The measured economic record of a respondent's county explains **0.6% of the variance** in how they rate the economy; party identification explains 34%. Independents rated the 2024 economy worse than the 2020 pandemic economy. Among 2020 Biden voters, **31.6% of those who said the economy got "much worse" voted for Trump, against 1.5% of those who said "much better"** — but that association runs in both causal directions. Media diet, not media environment, is where the signal is. |

**What this does not show.** Parts 1–3 are descriptive: they establish where the vote moved and what kinds of places moved most. Part 4 gets closer to mechanism — it shows that perception is disconnected from local reality and that misperception travels with vote switching — but it cannot establish that misperception *caused* switching rather than the reverse. The identification strategy that would settle that is laid out in the technical appendix.

---

## Part 1: Structural fundamentals

### Model

An incumbency-adjusted OLS regression on 19 presidential elections (1948–2020), following Abramowitz's "Time for Change" framework. The dependent variable is the incumbent party's two-party vote share. Predictors: Q2 real GDP growth in the election year (annualized, FRED GDPC1), the president's June Gallup approval, the number of consecutive terms the incumbent party has held, and whether the seat is open. The model is fit on 1948–2020; 2024 is strictly out-of-sample.

**Fit.** In-sample R² = 0.81; leave-one-out RMSE = 3.75pp. Approval (+0.27pp per point, *p* = 0.001) and GDP growth (+0.19pp per point, *p* = 0.04) carry the model. The open-seat penalty (−2.6pp) is marginal (*p* = 0.08) and consecutive terms (−0.4pp) is not distinguishable from zero (*p* = 0.55). An approval-only model achieves R² = 0.68 and predicts 48.1% for 2024. The fundamentals story is, in practice, an approval story.

### 2024

| Input | Value |
|---|---|
| Q2 2024 GDP growth (annualized) | +3.6% |
| Biden June 2024 approval | 38% |
| Consecutive Democratic terms | 1 |
| Open seat | Yes |
| **Predicted Harris two-party share** | **47.9%** |
| **Actual** | **49.25%** |
| **Residual** | **+1.4pp** |

The +1.4pp residual is less than half the model's out-of-sample error. Fourteen of the nineteen training elections have larger absolute residuals. The honest reading is that Harris performed about as a 38%-approval incumbent party should be expected to — not that she beat the fundamentals.

**Sensitivity.** 2020 is the model's largest miss by far (−10.9pp): COVID's −28% Q2 GDP predicted a Trump collapse that did not happen. That single observation suppresses the GDP coefficient. Refit without 2020, the GDP coefficient more than doubles (0.19 → 0.47), LOOCV RMSE falls to 2.66pp, and the 2024 prediction rises to 48.4% — residual +0.8pp. The conclusion is the same under either specification.

**Limitation.** Q2 GDP growth was strong in 2024, but real disposable income had only recently recovered from the 2021–23 inflation and consumer sentiment remained depressed. The model has no variable for the accumulated price-level shock, which is the most commonly cited economic grievance of the cycle. FRED consumer-sentiment and real-income series were pulled for this project and are the natural next test.

---

## Part 2: Where the votes went

### Data

County-level presidential returns from MIT Election Lab, 2016–2024. The raw file mixes reporting formats — some counties have a single TOTAL row, some report only by vote mode (absentee, election day, etc.), and some have both. The pipeline uses TOTAL where present and sums modes otherwise; the result matches certified national totals within 0.02M in every cycle. Alaska is excluded from county analyses because MIT codes it by state house district, which was redrawn in 2022. The county panel is 3,111 counties with complete 2016, 2020, and 2024 returns.

### Decomposition

Each county's change in Democratic votes is split into two parts:

```
ΔDem votes = dem_share_2020 × (total_2024 − total_2020)      [turnout component]
           + (dem_share_2024 − dem_share_2020) × total_2024   [share component]
```

The turnout component is the votes Harris would have gained or lost from turnout change alone, holding Biden's share. The share component is the rest. The share component **cannot** distinguish persuasion (voters switching parties) from differential mobilization (Democratic-leaning voters staying home at higher rates than Republican-leaning ones). That separation requires individual-level data.

### National picture

| | 2016 → 2020 | 2020 → 2024 |
|---|---|---|
| Change in Democratic votes | +15.4M | **−6.25M** |
| Turnout component | +10.6M (69%) | −1.7M (27%) |
| Share component | +4.8M (31%) | **−4.6M (73%)** |
| Change in total votes | +22.0M | −3.3M |

Biden's 2020 gain was mostly a turnout surge. Harris's 2024 loss was mostly share: the electorate shrank modestly, but the bigger effect was that the Democratic share of whoever did vote fell from 51.3% to 48.3%.

### Geography

| Metric | 2020 → 2024 | 2016 → 2020 (comparison) |
|---|---|---|
| Counties shifting right | **2,792 / 3,111 (90%)** | 1,594 / 3,111 (51%) |
| Median county swing (margin) | **−3.2pp** | −0.1pp |
| Turnout-weighted mean swing | **−4.9pp** | — |
| States shifting right | **51 / 51** | — |

The 2020 cycle was a wash at the county median with gains concentrated in suburbs; 2024 moved nearly everything. The largest state swings were in New York (−10.3), New Jersey (−10.0), Florida (−9.7), California (−9.0), and Texas (−8.1) — not the Midwest. The largest county swings (Bronx, Queens, Miami-Dade, Hudson NJ, Imperial CA, the Texas border) are heavily Hispanic urban and border counties.

### Strongholds versus everywhere else

Classifying the 2,439 counties that lost Democratic votes by which component dominates:

| Type | Counties | Share of Dem vote loss |
|---|---|---|
| Turnout-dominant (turnout component > 60% of loss) | 381 | **43%** |
| Mixed (both components negative) | 406 | 27% |
| Share-dominant (share component > 60% of loss) | 789 | 23% |
| Offsetting (one component positive) | 863 | 7% |

This looks like it contradicts the national picture, and the reconciliation matters. Share-dominant counties are twice as numerous, but turnout-dominant counties are the big Democratic ones — and 43% of all lost votes came from just 381 of them. The 60% cutoff is arbitrary and the shares move with it (49% at 55%, 19% at 65%), so the table is illustrative rather than a measurement. The regression in Part 3 is the sturdier evidence: a county's 2020 Democratic share strongly predicts its turnout loss (−1.7 votes per 100 per SD) and barely predicts its share loss (−0.2). **Democratic strongholds lost votes because their voters stayed home; everywhere else, the Democratic share fell.**

### The 2020 baseline

Biden's 2020 coalition was historically unusual: pandemic-era mail voting, the largest turnout surge in modern history, and peak anti-Trump mobilization in high-education suburbs. Some of the 2024 "turnout loss" in strongholds is the unwinding of that surge. The 2016 → 2020 comparison row above is the reminder that the 2020 starting line was itself an outlier.

---

## Part 3: Economic geography of the swing

### Regression

Merging Census ACS 2020 five-year county characteristics onto the county panel (N = 3,110), a WLS regression weighted by 2020 turnout explains **42%** of the variance in the 2020 → 2024 margin swing. The residuals are severely heavy-tailed (kurtosis 32), so the standard errors reported here are HC3 heteroskedasticity-robust, fit on the 2,817 counties with complete BLS data (97.7% of 2020 votes).

**Effect of a one-SD increase in each predictor on the county swing** (positive = toward Democrats):

| Predictor | Effect (pp) | 95% CI | |
|---|---|---|---|
| College share | **+2.4** | [+1.8, +3.1] | more college → smaller rightward swing |
| White non-college share | **+2.6** | [+1.7, +3.6] | more white non-college → smaller rightward swing |
| Log median income | **−0.8** | [−1.3, −0.2] | richer → larger rightward swing |
| Unemployment rate | −0.4 | [−0.8, +0.1] | not significant |
| Dem share 2020 | −0.4 | [−1.1, +0.2] | not significant |
| Manufacturing share 2016 | +0.2 | [0.0, +0.4] | marginal |
| Change in mfg share 2016–24 | 0.0 | [−0.2, +0.1] | null |
| Private job growth 2020–24 | **−0.5** | [−0.9, −0.1] | faster job growth → larger rightward swing |
| Real pay growth 2020–24 | +0.3 | [−0.2, +0.7] | null |

Three things to read carefully:

**The white non-college coefficient is positive.** Counties with more white non-college residents swung *less* to the right in 2024, holding income and education constant. This is the opposite of the 2016 pattern. Those counties had already moved; the 2024 shift was concentrated in diverse, lower-education, urban and border counties.

**The Biden-term economy did not register.** Real private-sector pay growth from 2020 to 2024, deflated by CPI, has no detectable relationship to the county swing. Counties where real pay rose swung the same as counties where it fell. Private job growth actually predicts a *larger* rightward swing — and the component regressions show why: job growth raises the turnout component (+0.8 per SD) and lowers the share component (−0.2). Those are Sunbelt growth counties gaining new, Republican-leaning voters, not existing voters rewarding the economy.

**Manufacturing exposure is not the story of 2024.** The 2016 manufacturing share of employment is marginally positive; its change since 2016 is exactly zero. Whatever the China-shock literature explains about 2016, it was fully priced into the 2020 baseline.

### The income gradient across cycles

Comparing each Democratic nominee's county-level vote share to Obama's 2012 share, by county income quartile, turnout-weighted:

| vs. Obama 2012 | Q1 (poorest) | Q2 | Q3 | Q4 (richest) | Q4 − Q1 |
|---|---|---|---|---|---|
| Clinton 2016 | −5.8 | −6.1 | −4.5 | −0.8 | **+5.0** |
| Biden 2020 | −6.3 | −4.3 | −1.8 | +3.1 | **+9.4** |
| Harris 2024 | −9.2 | −6.4 | −4.1 | +0.7 | **+9.9** |

Every Democrat since Obama has underperformed him in the poorest quartile, by a growing margin: −5.8, −6.3, −9.2. The gradient nearly doubled between 2016 and 2020 and then held. Harris's cycle is Biden's gradient shifted down roughly 2–3pp across all four quartiles. The class realignment is a ten-year trend, not a 2024 event.

### What "populism premium" this does and does not test

The hypothesis that working-class economic messaging earns votes in low-income counties cannot be tested with county returns alone: there is no measure of what voters heard or believed. What the data shows is that the local economic outcomes voters would be rewarding — real pay, jobs — had no effect, while the structural composition of a county — education, race, income level — had large ones. That is consistent with an attribution failure (voters did not credit the incumbent party for local improvement). It is equally consistent with national inflation swamping local conditions, or with the shift being cultural rather than economic. Part 4 takes this up with survey data linked to the same county records.

---

## Part 4: Did voters see the economy their county had?

### Data

The Cooperative Election Study (CES) surveys about 60,000 Americans each election year and records their county. The 2024 wave asks, before the election, whether "over the past year the nation's economy has" gotten much better through much worse, and, after the election, whom the respondent voted for and whom they recall voting for in 2020. Linking respondents to the county records from Parts 2–3 gives 56,635 people in 2,653 counties with both a measured local economic change and a stated perception of it.

### Local reality does not register

Regressing perceived economic change (−2 to +2) on the respondent's county's real pay growth, job growth, and unemployment over the Biden term:

| Predictors | R² |
|---|---|
| County economic record | **0.006** |
| Party identification (7-point) | **0.338** |
| Both | 0.341 |

The county record explains six-tenths of one percent. Within party the picture is flat: Democrats in counties where real pay fell the most rate the economy +0.34; where it rose the most, +0.36. Republicans, −1.31 and −1.43. A one-standard-deviation better local real-pay record moves perception by −0.02 (Democrats), −0.04 (independents), and −0.04 (Republicans) — tiny, and in the wrong direction; only the Republican estimate is statistically distinct from zero, and it says Republicans in counties where pay grew faster rated the economy slightly *worse*. Whatever voters were evaluating in 2024, it was not the economy of the place they live.

### The partisan flip, and who flipped less

| Perceived economy, mean (+2 … −2) | Democrats | Independents | Republicans |
|---|---|---|---|
| 2016 (Obama, D) | +0.43 | −0.44 | −0.65 |
| 2020 (Trump, R, pandemic) | −1.41 | −0.83 | +0.11 |
| 2024 (Biden, D) | +0.32 | −0.98 | −1.37 |

Out-party respondents rate the economy badly in every year; that is the known result. Two comparisons are specific to 2024. **Independents rated the 2024 economy worse than the 2020 pandemic economy** (−0.98 vs −0.83). And **the in-party did not fail to notice**: Democrats in 2024 rated Biden's economy (+0.32) *higher* than Republicans rated Trump's in 2020 (+0.11) and only modestly below Democrats' rating of Obama's in 2016 (+0.43). The disconnect between the economic record and its perception is not an in-party phenomenon. It sits with independents and with Republicans, whose −1.37 is within rounding of the −1.41 Democrats recorded for the pandemic year — the out-party rated the 2024 economy about as harshly as the out-party of 2020 rated the year of the COVID crash.

### The attribution gap and media diet

The *attribution gap* is how much better or worse a respondent rates the economy than their county's record predicts — the residual from the first regression above. Net of party identification, demographics, and county characteristics, the gap moves with what people watch and read:

| Media use in the past 24 hours | Effect on gap (scale points) |
|---|---|
| Watched MSNBC | **+0.59** |
| Read a newspaper | +0.30 |
| Watched CNN | +0.16 |
| Watched local TV news | +0.03 (n.s.) |
| Used social media | −0.05 |
| No news at all | −0.12 |
| Watched Fox News | **−0.32** |

For reference, one step on the seven-point party scale is −0.30. Fox viewing shifts Democrats who watch it by −0.67 and strong Republicans by −0.15 — either persuasion of the persuadable or a floor effect among those already at the bottom of the scale; the data cannot say which. Media choice is self-selected, so these are associations conditional on party, not effects of exposure.

### Media environment, as opposed to media diet, has almost nothing to explain

A multilevel model with respondents nested in counties puts a ceiling on how much any county-level factor — local news availability, media market, anything geographic — could matter. Only 4.7% of the variance in perceived economy is between counties at all, and after accounting for who lives in each county (party, education, age, race) that falls to 0.5%. A county two standard deviations above versus two below the average differs by 0.31 points on a four-point scale. Whatever produced the disconnect between perception and reality, it operated on individuals through the sources they chose, not on places through the sources available.

The one thing county context does modulate is the size of the partisan gap: the distance between strong Republicans and strong Democrats is **−2.09 in counties with the most white non-college residents and −1.56 in counties with the fewest**. The partisan divergence in perception is a third wider in exactly the places Part 3 identified as structurally drifting.

### The gap and vote switching

Among 2024 respondents who recall voting for Biden in 2020 and voted for a major-party candidate in 2024 (N = 20,608), 6.4% voted for Trump (weighted; 3.0% unweighted — the panel over-represents consistent Democrats and the weights correct for it, so the level depends on the weights more than most figures in this report). Split by how they rated the economy:

| "Over the past year the nation's economy has…" | N | Switched to Trump |
|---|---|---|
| Gotten much worse | 1,192 | **31.6%** |
| Gotten somewhat worse | 2,580 | 11.1% |
| Stayed about the same | 3,798 | 4.6% |
| Gotten somewhat better | 8,746 | 1.7% |
| Gotten much better | 4,292 | **1.5%** |

The relationship is monotonic across all five levels. Controlling for party identification, education, age, race, media diet, and the county's actual economic record, a one-point-worse attribution gap raises the probability of switching by 3.9 percentage points. The county's real pay growth has no detectable effect (−0.011, SE 0.113). The mirror holds for recalled Trump voters: 2.3% switched to Harris, and the gap predicts it in the expected direction. A multilevel logit with a county random effect gives a similar coefficient (−0.96 vs −0.83).

**This is the finding that most needs a caveat.** Perception is measured before the election and vote after, but a voter who had already decided to leave Biden's coalition would rate the economy badly *because* of that decision. The association is consistent with misattribution driving the switch and equally consistent with the switch driving the rating. Nothing in the CES design separates the two. What the data does establish is that the rating is not coming from the local economy, and that it is coming, in part, from media diet — which narrows the set of explanations without closing it.

### Reading Part 4 against Parts 1–3

Part 3 found that the local economic outcomes voters should have been rewarding had no effect on the county swing. Part 4 shows why: voters were not perceiving them. The individual-level gap predicts individual switching, but between-county variation in the gap barely exists, so it does not aggregate to a county-level relationship with the swing — the county-level gap has no detectable effect on the county swing (p = 0.8). The economy voters evaluated in 2024 was a national, partisan, and media-mediated object, not the one in their county's employment and wage records.

---

## Synthesis

**The structural conditions predicted a narrow loss, and a narrow loss is what happened.** A 38%-approval incumbent party with an open seat is expected to lose. Harris's result sits within the model's error band on either side of the prediction, depending on specification.

**The shift was everywhere, but the mechanism differed by place.** Nationally, three-quarters of the Democratic vote loss was share shift. In the largest Democratic counties it was turnout. The two are not in conflict: strongholds bled turnout while the share fell across the rest of the map.

**The places that moved most were not the places the 2016 narrative would predict.** Diverse, lower-education, urban and border counties swung hardest. White non-college counties, controlling for income and education, swung less than average.

**Local economic performance did not protect the incumbent party, because voters did not perceive it.** Real wage growth and manufacturing exposure explain nothing about the county swing, and the county's economic record explains 0.6% of how its residents rate the economy. What does explain the rating is party identification and media diet. Whether the resulting misperception drove vote switching or was produced by it is the open question, and the one the data cannot yet answer.

**The class gradient is structural and predates the campaign.** Democrats have lost ground in the poorest counties relative to 2012 in every cycle since, at an accelerating rate. No single campaign created it, and the 2024 gradient is the 2020 gradient shifted down.

**The information problem is individual, not geographic.** Only 4.7% of the variance in economic perception is between counties, and almost none of that survives controlling for who lives there. The disconnect between what happened locally and what voters believed was not a function of local news availability or media markets; it tracked the sources people chose within the same county. The partisan divergence in perception is widest in the white non-college counties where the structural drift has been strongest.

---

*Methods, data handling, full regression tables, and known limitations: [`technical_appendix.md`](technical_appendix.md)*
*Notebooks: [`notebooks/`](../notebooks/) · Figures: [`outputs/figures/`](../outputs/figures/) · Tables: [`outputs/tables/`](../outputs/tables/)*
