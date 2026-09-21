# 2024 DNC Campaign Autopsy: A Data-Driven Analysis

*Unit of analysis: national election (Part 1), county (Parts 2–3), survey respondent in county (Part 4), the same respondent across three waves (Part 5) · Elections covered: 1948–2024*
*Data: MIT Election Lab · FRED · Census ACS 2020 · BLS QCEW · Gallup · Cooperative Election Study (2024 cross-section and 2020–2024 panel) · Medill Local News Initiative*

---

## Executive summary

Kamala Harris lost the 2024 presidential election with **49.25% of the two-party popular vote**, down from Biden's 52.27% in 2020. Democrats received 6.25 million fewer votes than in 2020 in an electorate that was 3.3 million votes smaller. This report examines that result through eight lenses: what structural conditions predicted, how the vote loss decomposes geographically, what county economic characteristics explain the shift, whether voters perceived the economy their county actually had, whether — following 6,175 of the same people from 2020 to 2024 — what they believed in 2022 predicted what they did in 2024, who in the poorest counties actually moved and whether federal money that visibly arrived made any difference, how large the turnout collapse in Democratic strongholds was and whether it decided anything, and finally what the voters who left believed about economics and culture.

**Eight findings:**

| | Finding |
|---|---|
| **Part 1** | A fundamentals model fit on 1948–2020 predicted Harris at 47.9%. She received 49.25%. The +1.4pp residual is well inside the model's 3.75pp out-of-sample error — she performed **about as the fundamentals predicted**, not meaningfully better or worse. |
| **Part 2** | The shift was near-universal: 90% of counties and all 51 states moved right. Nationally, **73% of the Democratic vote loss came from share shift and 27% from lower turnout**. But the largest raw losses were in Democratic strongholds, and there the mechanism was turnout. |
| **Part 3** | County income, education, and racial composition explain about 42% of the variance in county swings. The gap between Democratic performance in rich and poor counties, relative to 2012, widened from +5.0pp (2016) to +9.4pp (2020) to +9.9pp (2024). Harris inherited that gradient; she did not create it. Manufacturing exposure and real wage growth over the Biden term explain essentially nothing. |
| **Part 4** | The measured economic record of a respondent's county explains **0.6% of the variance** in how they rate the economy; party identification explains 34%. Independents rated the 2024 economy worse than the 2020 pandemic economy. Among 2020 Biden voters, **31.6% of those who said the economy got "much worse" voted for Trump, against 1.5% of those who said "much better"** — but that association runs in both causal directions. Prices were the least filtered item: 80% of Democrats and 95% of Republicans said they rose, though Republicans were twice as likely to say "a lot," and saying "a lot" rather than "somewhat" predicted switching independently of the economy rating. Media diet, not media environment, is where the remaining signal is. |
| **Part 5** | In a panel of the same voters, **how a Biden 2020 voter rated the economy in 2022 predicted whether they voted for Trump in 2024**: 7.9% of those who said "much worse" switched, 0 of 438 who saw improvement did. A rating given two years before the vote cannot be a rationalization of it. The same 2022 rating predicted not voting at all, by voter-file record. Within the same people, county economic change still explained nothing. |
| **Part 6** | The bottom-quartile shift is not a class story. White low-income counties moved in 2016 and held; **nonwhite low-income counties did the moving in 2024**. At the individual level, income does not predict a Biden voter switching (7.1% under $30k, 6.4% over $200k); ethnicity does (Hispanic 10.5%, White 5.8%, Black 4.7%). Separately, counties that received more Biden-era infrastructure and recovery money **swung less right — about half a point per standard deviation — but their residents did not rate the economy any better.** Delivery moved the vote without moving the perception. |
| **Part 7** | Democratic strongholds lost **2.9 million votes — 47% of the national Democratic loss — and 97% of it was in safe states.** Conditional on demographics, Biden and Trump 2020 voters stayed home at the same rate; in aggregate more Democratic votes went missing because the coalition is built from lower-turnout groups that surged in 2020 and reverted in 2024 while Republican-area surge voters did not. Swing-state Democratic counties held their turnout. Returning every stay-home at their 2020 vote flips no state under the plainest estimate. **The share shift that decided the Blue Wall was 60% Biden voters switching (3:1 over the reverse) and 35% new voters breaking 58–40 for Trump.** |
| **Part 8** | The switchers were **economically available and culturally lost.** 77% wanted Medicaid expanded and majorities wanted the wealthy taxed — but they were indistinguishable from Republicans on the wall, asylum, and border patrol, and cultural conservatism predicted switching at 3.5× the marginal effect of economic views, with immigration carrying most of it. 59% placed Harris as "very liberal," a perception that tracked immigration attitudes. Among low-income Biden voters with left economic views, cultural conservatives defected at 23% against 2% for cultural liberals. |

**What this does not show.** Parts 1–3 are descriptive: they establish where the vote moved and what kinds of places moved most. Part 4 shows that perception is disconnected from local reality and that misperception travels with vote switching, but in a single cross-section cannot separate cause from effect. Part 5 puts the perception two years ahead of the vote, which rules out the specific objection that decided switchers rated the economy badly *because* they had decided. It does not rule out a slower common cause — a voter already leaving Biden in 2022 for other reasons — and it rests on 39 switchers.

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

Two things about this table are easy to misread, and Part 6 takes both up. The poorest quartile of counties casts 5.5% of the national vote. And "the poorest quartile" is not one population: it contains rural white Appalachia and the Rio Grande Valley, which moved in different years for different reasons.

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

A multilevel model with respondents nested in counties puts a ceiling on how much any county-level factor — local news availability, media market, anything geographic — could matter. Only 4.7% of the variance in perceived economy is between counties at all, and after accounting for who lives in each county (party, education, age, race) that falls to 0.5%. A county two standard deviations above versus two below the average differs by 0.31 points on a four-point scale.

That ceiling was then tested directly against the Medill Local News Initiative's 2025 county inventory: 213 counties with no local news outlet, 1,526 with one. (Medill's own curated "news desert" label covers 206 counties and agrees with the zero-outlet count on 163 of them; every result below was run under both definitions and does not change.) Linked to the CES, that gives 547 respondents in news deserts and 8,003 in single-outlet counties. The news environment fails every test it was given:

| Test | Result |
|---|---|
| Does scarcity change what people consume? | Net of party, education, and rural status: newspaper −0.03 (SE 0.02), local TV −0.03 (0.02), Fox −0.02 (0.02). Only "no news at all" rises, by 1.8 points. |
| Does it explain between-county variance? | The news variables alone explain 12% of the 0.5% that remains after accounting for who lives in each county. The rural-urban code alone explains 30% of the same quantity; news adds about four points beyond a metro/nonmetro split. County composition explains 80%. |
| Direct effect on perception? | News desert +0.04 (SE 0.05). Watching Fox, for scale: −0.36. |
| Does it widen the partisan gap? | +0.02 (SE 0.02) — null, and the point estimate runs the wrong way. |
| Can it instrument for perception? | First-stage F = 0.6. No. |

Whatever produced the disconnect between perception and reality, it operated on individuals through the sources they chose, not on places through the sources available. The local news environment is not where the 2024 information problem lived.

The one thing county context does modulate is the size of the partisan gap: the distance between strong Republicans and strong Democrats is **−2.09 in counties with the most white non-college residents and −1.56 in counties with the fewest**. The partisan divergence in perception is a third wider in exactly the places Part 3 identified as structurally drifting — and news availability does not move it.

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

**This is the finding that most needs a caveat.** Perception is measured before the election and vote after, but a voter who had already decided to leave Biden's coalition would rate the economy badly *because* of that decision. The association is consistent with misattribution driving the switch and equally consistent with the switch driving the rating. Nothing in the CES design separates the two. The obvious repair — use local news availability as an instrument for perception, on the logic that it shifts what people believe but not how they vote except through belief — was tried and does not work: the news environment barely moves perception at all (first-stage F = 0.6), so there is nothing to instrument with. What the data does establish is that the rating is not coming from the local economy, and that it is coming, in part, from media diet — which narrows the set of explanations without closing it.

### Prices: consensus on direction, partisanship on degree

The 2024 CES also asks whether "the prices of everyday goods and services" increased a lot, somewhat, stayed the same, or decreased. It is closer to a factual report than the economy rating, and it is less partisan — but not un-partisan, and the distinction matters.

| | Said prices rose | Said "a lot" | Of those who said rose, "a lot" |
|---|---|---|---|
| Democrats | 80% | **35%** | 44% |
| Independents | 90% | 62% | 69% |
| Republicans | 95% | **76%** | 80% |

On direction there is near-consensus: four in five Democrats and nineteen in twenty Republicans said prices went up. On degree there is not: Republicans were twice as likely as Democrats to say "a lot." Measured against each item's own spread, the Democrat–Republican gap is 0.74 standard deviations on prices, 1.26 on the economy rating, and 0.54 on the respondent's own household income. Prices sit between the abstract national question and the personal one — less filtered than "the economy," more filtered than "your income."

Price perception feeds the economy rating by the same amount for everyone: within each party, saying prices rose one step more lowers the economy rating by 0.53–0.58, and the party × prices interaction is zero (0.000, SE 0.007). Partisanship sets the level from which each respondent starts; reported price experience moves every group off that level by the same amount. Adding prices to party identification raises the explained variance in the economy rating from 34% to 44%.

Prices also predict switching on their own. Among recalled Biden voters, **12.8% of those who said prices "increased a lot" voted for Trump, against 3.6% of those who said "increased somewhat."** With the economy rating held fixed, one step more inflation reported raises the probability of switching by 1.9 points; without that control, by 5.1 — a bit under half the prices effect is direct, the rest runs through the general economy rating.

This does not resolve the reverse-causation problem and narrows it only somewhat. The margin that predicts switching — "a lot" versus "somewhat," among people who agree prices rose — is exactly the margin on which the parties differ, so a Biden voter who had already moved toward Trump could plausibly report "a lot" for the same reason they rate the economy badly. What the prices item adds is a second, less abstract measure that points the same way, with a partisan filter about 60% the strength of the economy rating's. Like the economy rating, it has no local component: county economic record and composition explain 2% of its variance.

### Reading Part 4 against Parts 1–3

Part 3 found that the local economic outcomes voters should have been rewarding had no effect on the county swing. Part 4 shows why: voters were not perceiving them. The individual-level gap predicts individual switching, but between-county variation in the gap barely exists, so it does not aggregate to a county-level relationship with the swing — the county-level gap has no detectable effect on the county swing (p = 0.8). The economy voters evaluated in 2024 was a national, partisan, and media-mediated object, not the one in their county's employment and wage records. Prices were the part of that object on which the partisan filter was weakest — all sides agreed they had risen, and reported price experience moved the economy rating through the same channel regardless of party — but how much they had risen was still read through a partisan lens.

---

## Part 5: The same voters, 2020 to 2024

### Data

The CES re-interviewed 6,175 of its 2020 respondents in 2022 and again in 2024. Each wave asked the same economy question. The 2020 vote was recorded in 2020 and the 2024 vote in 2024 — no recall. All three waves were matched to voter files, so turnout is validated by record. Retained panelists are older, more educated, and more often validated voters than the 2020 base, with no partisan difference in attrition; the panel under-represents the disengaged.

### The flip, within person

The partisan flip in Part 4 compared different samples in different years. Here it is the same people:

| Perceived economy (+2 … −2), 2020 party ID | 2020 (Trump) | 2022 (Biden, inflation peak) | 2024 (Biden) |
|---|---|---|---|
| Democrats (N = 2,912) | −1.52 | −0.49 | +0.34 |
| Independents (N = 895) | −0.98 | −1.18 | −0.81 |
| Republicans (N = 2,298) | +0.08 | −1.71 | −1.36 |

Sixty-one percent of Democrats moved two or more points toward their incumbent between 2020 and 2024; 46% of Republicans moved two or more points away. Independents barely moved. Composition cannot explain a within-person change. In 2022, at the inflation peak, Democrats rated their own president's economy at −0.49 — negative, but two full points above Republicans.

In first differences — each person's change in rating against their county's change in real pay — the county coefficient is −0.04 (SE 0.06) with party controlled, and within each party it is indistinguishable from zero. Local reality did not register in the cross-section, and it did not register within the same person over four years.

### Timing

Among 1,684 panelists who voted for Biden in 2020 and for Harris or Trump in 2024, 39 switched. By how they had rated the economy in 2022:

| "Over the past year the nation's economy has…" (asked in 2022) | N | Voted Trump in 2024 |
|---|---|---|
| Gotten much worse | 240 | **7.9%** |
| Gotten somewhat worse | 611 | 2.1% |
| Stayed about the same | 337 | 1.8% |
| Gotten somewhat better | 362 | **0.0%** |
| Gotten much better | 76 | **0.0%** |

Not one of the 438 Biden voters who saw improvement in 2022 voted for Trump. The coefficient on the 2022 rating is −1.1 to −1.4 across five specifications — alone, with party identification, with education and age, net of the same person's rating of Trump's economy in 2020, and expressed as the 2020→2022 *change* — and it moves by less than 0.2 between weighted and unweighted estimation. A one-step-worse rating in 2022 raises the probability of switching by about 8 points. The person's 2020 rating, given under Trump, has no independent effect.

This is the result the cross-section could not deliver. A rating given in autumn 2022 cannot be a rationalization of a vote cast in November 2024. The objection that decided switchers rate the economy badly *because* they have decided does not apply to a rating that predates the decision by two years. What survives is a narrower objection: a voter who was already leaving Biden in 2022 for reasons unrelated to the economy might have rated the economy worse for those reasons. That cannot be excluded with this design, and 39 events do not support the subgroup analysis that would probe it.

The 2022 prices item points the same way: among Biden voters who said prices had risen, 3.2% of those who said "a lot" switched against 0.3% of those who said "somewhat." Watching Fox in 2022 is associated with switching, but on 2 switchers among 38 viewers — not evidence.

### Demobilization, by record

The same 2022 rating predicts the other exit from the coalition. Among Biden 2020 voters matched to a voter file, the share with no validated 2024 vote runs from 9.0% ("much worse" in 2022) to 1.7% ("somewhat better"); the logit coefficient is −0.79 (p = 0.03) with party, education, and age controlled. Perception in 2022 predicted both switching and staying home in 2024.

The level of non-voting does not distinguish the coalitions: 3.9% of Biden 2020 voters and 4.2% of Trump 2020 voters had no validated 2024 vote. In this panel there is no differential demobilization — but the panel retained engaged voters, so both figures are floors. Part 7 returns to this with the much larger cross-section and confirms it: conditional on demographics, Biden and Trump 2020 voters stayed home at the same rate.

Among the 1,784 Biden 2020 voters with a known 2024 outcome (weighted): 92.9% voted for Harris, 2.9% for Trump, 1.0% for another candidate, 3.3% did not vote. In this engaged panel, defection to Trump and demobilization were the same size.

### Reading Part 5 against Part 4

Part 4 established the pattern; Part 5 establishes its timing. Perception of the economy — not the economy itself — moved with the vote, and it moved first. The county's economic record did not enter either the level or the change of what people believed. What entered was party, and within party, what people reported about prices and what they watched. By 2022 the Biden coalition's economic perception had already sorted its 2024 leavers from its stayers, on an item that has no local component and a partisan filter, before the campaign began.

---

## Part 6: Who moved, and did delivery register?

### The bottom quartile is two populations that moved in different years

Splitting the 778 poorest-quartile counties into terciles by nonwhite share, and tracking each against Obama 2012:

| Q1 counties | 2016 | 2020 | 2024 | Change 2020→24 |
|---|---|---|---|---|
| Mostly white (27% of Q1 votes; 79% white non-college) | −9.6 | −9.1 | −10.7 | −1.6 |
| Mixed (31%) | −6.3 | −6.2 | −8.4 | −2.1 |
| Heavily nonwhite (42%; 61% nonwhite) | −3.2 | −4.6 | −8.9 | **−4.3** |

White low-income counties moved nearly ten points in 2016 and then sat still through two more cycles. Nonwhite low-income counties barely moved in 2016, moved in 2020, and moved hardest in 2024. The largest Q1 counties by votes are the Bronx (−18 versus 2012), Hidalgo, Texas (−22), and Cameron, Texas (−18). The 2024 widening of the class gradient in Part 3 is the Hispanic and Black working class, not the white working class — the white working class had already gone.

### At the individual level, income does not predict defection; ethnicity does

Among 20,608 CES respondents who recall voting for Biden in 2020 and voted for a major-party candidate in 2024:

| Biden 2020 voters by family income | Switched to Trump |
|---|---|
| Under $30k | 7.1% |
| $30–50k | 6.0% |
| $50–100k | 6.3% |
| $100–200k | 6.3% |
| $200k+ | 6.4% |

| By race/ethnicity | Switched to Trump |
|---|---|
| Hispanic | **10.5%** |
| Other | 7.1% |
| White | 5.8% |
| Black | 4.7% |

Flat across income; the same by county income quartile; and inside the poorest counties, the residents under $50k switched *less* (5.3%) than those over (9.9%). Hispanic Biden voters defected at nearly twice the white rate in every income band; Hispanic voters under $30k, at 13.6%. In a model with party identification, education, age, and county income, Hispanic carries +0.59 (SE 0.24) and individual income −0.008 (SE 0.026).

Low-income Biden voters did rate the economy worse — +0.13 for the lowest band against +0.86 for the highest. The perception gradient by income exists. It did not translate into differential defection. The county-level class gradient is composition: the poorest counties are disproportionately Hispanic, and Hispanic voters left at every income level. (The panel has 38 Hispanic Biden voters and cannot check this.)

### Delivery moved the vote but not the perception

County obligations under the Infrastructure Investment and Jobs Act and the American Rescue Plan — the two most visible Biden-era programs traceable to a county in public spending data — per capita, log-scaled, top 1% winsorized, from enactment through Election Day 2024. Median IIJA obligations were $671 per resident; ARPA, $421. IIJA money was spread evenly across partisan lines ($1,023 per capita in Republican-leaning counties, $861 in Democratic); ARPA was not ($503 versus $1,843), so ARPA doubles as a proxy for urban Democratic counties and every model below controls for composition, the rural-urban code, and population.

| Test | IIJA | ARPA |
|---|---|---|
| County swing 2020→24, per SD of log per-capita obligations (Part 3 controls + rural-urban + population) | **+0.50pp** (SE 0.23) | **+0.43pp** (SE 0.17) |
| Same, dropping the top 5% of counties per capita | +0.55 (0.29) | +0.78 (0.30) |
| Residents' economy rating, with party and composition | +0.01 (0.01) | +0.00 (0.01) |
| Within-person change in rating, 2020→24, panel | +0.13 (0.08) | +0.02 (0.05) |
| Biden voter switching to Trump | −0.09 (0.13) | −0.13 (0.12) |

Counties that received more money swung less to the right — about half a point per standard deviation for each program, robust to every control and to dropping the counties where federal labs and state capitals inflate the figures. This is the first county-level economic variable in the project with the expected sign that survives everything.

But the residents of those counties did not rate the economy any better. ARPA per capita has a raw association with perception that is positive within every party; it disappears entirely once county income, education, and Democratic share are controlled, in both the cross-section and the panel. Delivery did not predict individual switching either.

Money that arrived in a county moved that county's vote without moving its residents' economic perception. The decomposition from Part 2 says which part of the vote it moved:

| Per SD of log per-capita obligations | IIJA | ARPA |
|---|---|---|
| Turnout component | −0.20 (0.23) | +0.19 (0.14) |
| Share component | +0.18 (0.11) | **+0.20 (0.07)** |
| Republican votes, % change 2020→24 | **−1.13 (0.41)** | −0.23 (0.49) |
| Democratic votes, % change | −0.05 (0.41) | **+0.56 (0.28)** |

Neither program moved total turnout. IIJA counties swung less right because Republican votes grew less there — Democratic votes were unaffected. ARPA counties swung less because Democratic votes held up better. Both are share-side effects: fewer new or switched Republican votes, not more Democratic mobilization. That rules out the organizing explanation. What is left is a share effect that does not run through belief about the national economy — a perception of *local* conditions that the survey item does not ask about, or something about the counties that received money that the controls miss. Whatever delivery did, it did not do it by making people believe the economy was better, and it did not do it by getting more Democrats to the polls.

---

## Part 7: Stronghold demobilization — how big, and did it matter?

Part 2 found that Democratic strongholds lost votes through turnout while the rest of the map lost them through share. This part sizes that loss, identifies who the stay-homes were, and asks whether their staying home changed any result.

### How big

| County type (2020 Dem share) | Share of 2020 votes | Dem vote change | Turnout change | Dem share change |
|---|---|---|---|---|
| Republican strongholds (<35%) | 19% | −0.16M | +2.1% | −1.1 |
| 35–45% | 16% | −0.29M | +1.2% | −1.6 |
| Competitive (45–55%) | 23% | −1.20M | −1.4% | −2.7 |
| Lean Democratic (55–65%) | 22% | −1.68M | −3.9% | −2.7 |
| **Democratic strongholds (65%+)** | **21%** | **−2.90M** | **−6.9%** | **−3.8** |

The 150 counties Biden won with 65% or more held 21% of all votes and 30% of Democratic votes. They lost **2.9 million Democratic votes** — from 24.7M to 21.8M, a 12% drop — while Republican votes in the same counties *rose* by 600,000. That is **47% of the entire national Democratic loss** and **68% of the national turnout component**. Turnout rose in Republican counties and fell in Democratic ones, monotonically across every bin.

The losses are where one would guess: Los Angeles (−612k, 380k of it turnout), Cook (−278k), Queens, Alameda, Santa Clara, Brooklyn, the Bronx. **2.81M of the 2.9M was in safe states**; California, New York, and Illinois alone account for 1.79M. The seven swing states together: −0.10M.

### Who stayed home: propensity versus effect

County returns cannot say who the missing voters were. The CES can: 34,666 respondents in 2024 were matched to the TargetSmart voter file, which records whether they voted, and reported their 2020 vote. Two different questions have two different answers, and keeping them apart is the whole finding.

**Propensity.** Conditional on who they are, was a Biden 2020 voter more likely to abstain in 2024 than a Trump 2020 voter? **No.** Unweighted, 5.7% of Biden voters and 5.6% of Trump voters had no validated 2024 vote. Split by demographic group:

| Group | Biden voters stayed home | Trump voters stayed home | Share of Biden voters |
|---|---|---|---|
| Black | 10.4% | 16.8% | 16% |
| Hispanic | 7.5% | 8.5% | 11% |
| Under 35 | 7.7% | 9.3% | 8% |
| No degree | 5.3% | 5.6% | 25% |
| Other | 3.2% | 4.4% | 41% |

Within every group, Trump voters stayed home as much or more. The panel, whose 2020 vote is contemporaneous rather than recalled, says the same: 3.2% of Biden voters and 3.7% of Trump voters. There is no evidence that Democrats who normally vote chose to sit out 2024 at a higher rate than Republicans who normally vote.

**Effect.** Did more 2020 Biden votes go missing than Trump votes? **Yes.** Weighted to the population — using `vvweight`, the CES's registered-voter weight — 8.0% of Biden voters and 5.9% of Trump voters did not vote. The two answers are consistent: the Democratic coalition contains more Black, Hispanic, and young voters, who vote less reliably in any year, and the survey weights turn that composition into an aggregate gap. The gap is a description of who Democrats are, not evidence that Democrats abandoned the party. County aggregates say the same thing from the other side: turnout fell 6.9% in Democratic strongholds and rose 2.1% in Republican ones.

### What 2016 shows

| County type | Turnout 2016→2020 | 2020→2024 | **2016→2024** |
|---|---|---|---|
| Republican strongholds | +14.7% | +2.1% | **+17.2%** |
| Competitive | +19.3% | −1.4% | +17.6% |
| Democratic strongholds | +14.4% | −6.9% | **+6.4%** |

Democratic votes in strongholds: 21.0M in 2016, 24.7M in 2020, 21.8M in 2024. Against 2016 the strongholds are up 3.6%. The "collapse" is the 2020 surge going back — but not symmetrically. Republican areas kept nearly all of their 2020 gain; Democratic areas kept a third. The 2020 surge in Democratic areas was disproportionately low-propensity voters pulled in by mail voting and anti-Trump energy, and in 2024 they reverted to baseline while Republican-area surge voters did not. That asymmetry is the real content of "demobilization."

### Stay home or flip?

Among Biden 2020 voters who did not vote for Harris:

| | Cross-section (N = 1,709) | Panel (N = 112) |
|---|---|---|
| Stayed home | 64% | 55% |
| Flipped to Trump | 30% | 31% |
| Third party | 6% | 13% |

Roughly two stay-homes for every flip, in both sources. Trump 2020 voters who left his column stayed home in even greater proportion — 76% — and flipped less (19%).

### The counterfactual

If every 2020 voter who stayed home in 2024 had voted as in 2020, using CES stay-home rates by state and 2020 vote applied to actual 2020 totals:

| | Trump margin | Unweighted (95% CI) | `commonweight` | `vvweight` |
|---|---|---|---|---|
| Michigan | −80k | +20k (−50k to +91k) | +51k | **+183k** |
| North Carolina | −183k | +59k (−6k to +123k) | +113k | +128k |
| Arizona | −187k | +24k | +11k | +27k |
| Georgia | −115k | −6k | +19k | +38k |
| Pennsylvania | −120k | −22k | −17k | −17k |
| Wisconsin | −29k | −12k | +7k | −10k |
| Nevada | −46k | −10k | −14k | +8k |
| National popular vote | −2.29M | +0.43M | +0.76M | +2.17M |

Michigan flips under the registered-voter weight and under nothing else, on 41 Biden and 24 Trump stay-homes in the sample; the unweighted interval spans zero. No other state comes close. The popular vote does not flip under any weighting. The cleanest reason nothing moves is in the county data: Democratic-leaning counties in the swing states did not lose turnout at all.

| Swing-state counties Biden won with 55%+ | Turnout change 2020→24 | Turnout component | Share component |
|---|---|---|---|
| Pennsylvania (5) | +0.1% | −3k | −37k |
| Michigan (5) | −0.1% | −2k | −71k |
| Wisconsin (6) | +3.5% | +23k | −9k |
| Georgia (23) | +1.3% | +19k | −3k |
| Arizona (4) | −0.8% | −3k | −19k |
| North Carolina (16) | +1.2% | +19k | −19k |

Philadelphia, Wayne, Milwaukee, Fulton, Maricopa held their 2020 turnout. The demobilization happened in Los Angeles and Brooklyn. In every swing state the loss came through share.

### How Republicans won the share

Share is a residual, and it bundles two things. Among validated 2024 voters with a known 2020 status:

| Bloc (2020 behavior) | Share of 2024 voters | 2024 vote | Net to Trump |
|---|---|---|---|
| Biden 2020 voters | 47.7% | 93.8% Harris / **5.2% Trump** | −42.3pp |
| Trump 2020 voters | 44.6% | 97.9% Trump / 1.6% Harris | +42.9pp |
| **2020 non-voters, new in 2024** | **5.6%** | **57.7% Trump** / 40.0% Harris | **+1.0pp** |
| 2020 third-party | 2.1% | split | +0.1pp |

Trump's margin among 2024 voters, about 1.8 points, is **+1.7pp from net switching** — Biden→Trump switchers outnumbered Trump→Harris switchers three to one — and **+1.0pp from new voters**, who broke 58–40 for Trump. Persuasion in the strict sense is about 60% of the share shift; Republican mobilization of people who had not voted in 2020 is about 35%.

The new voters are the mirror of the demobilization story. They were young (mean age 39 against 53 for the electorate), 71% without a degree, and their vote split by group:

| New-voter group | Share of new voters | Trump | Harris |
|---|---|---|---|
| White/other, 30 and over | 48% | **71%** | 27% |
| Under 30 | 30% | 45% | 52% |
| Hispanic | 14% | **65%** | 34% |
| Black | 8% | 15% | 85% |

The non-college white and Hispanic marginal voter — the person who does not vote in most years — showed up in 2024 and voted Trump two to one. On the Democratic side the equivalent marginal voter, who had shown up in 2020, reverted to not voting.

### What it means

The low-propensity electorate changed sides. In 2020 the marginal voter was pulled in against Trump; in 2024 the Democratic-leaning marginal voter went home while the Republican-leaning one was pulled in. That is why Republican strongholds kept their 2020 surge and grew 17% over 2016 while Democratic strongholds gave theirs back. Demobilization was large in raw votes, real in effect, compositional in mechanism, and almost entirely in safe states. It was not Democrats who normally vote choosing to abstain. It did not touch the Blue Wall, where Democratic turnout held and the loss was share — voters who showed up and voted for the other side, and new voters who did the same. The popular-vote deficit is largely a demobilization story; the electoral college is not.

---

## Part 8: What the leavers believed

Part 7 identified the two groups that gave Republicans the share: Biden 2020 voters who switched, and 2020 non-voters who entered for Trump. The 2024 CES asks both groups what they think about healthcare, taxes, immigration, abortion, same-sex marriage, and policing, and where they place themselves, Harris, and Trump on a seven-point ideological scale. This part uses those items to test a specific hypothesis: that Harris lost economically-left but culturally-conservative voters by accepting a culture-war framing rather than pivoting to economic populism.

The CES cannot observe what Harris said, so "accepting a framing" is not directly testable. It can observe what the leavers believed, which axis of belief predicts leaving, and how far left they perceived Harris to be. It has no items on transgender policy, "wokeness," minimum wage, Medicare-for-all, or tariffs; the cultural axis here is immigration (five items), abortion and same-sex marriage (two), and policing (two), and the economic axis is Medicaid expansion, ACA repeal, Medicaid work requirements, student-loan forgiveness, corporate tax, tax on $400k+, the 2017 cuts, and low-income housing incentives.

### The leavers were economically available

Share taking the Democratic-aligned position, by path:

| | Loyal Democrats | **Biden→Trump** | **New voters → Trump** | Loyal Republicans |
|---|---|---|---|---|
| Expand Medicaid | 95% | **77%** | **73%** | 55% |
| Keep the ACA | 95% | 62% | 39% | 25% |
| Low-income housing incentives | 91% | 73% | 67% | 48% |
| Raise corporate tax to 28% | 91% | 60% | 41% | 23% |
| Raise taxes on $400k+ | 91% | 57% | 50% | 34% |
| Forgive student loans | 84% | 47% | 25% | 13% |
| *Economic index (0–1)* | *0.84* | ***0.55*** | ***0.44*** | *0.30* |
| Oppose the border wall | 86% | **23%** | **8%** | 3% |
| Allow asylum at the border | 64% | 18% | 9% | 6% |
| Oppose more border patrol | 33% | 8% | 5% | 2% |
| Legal status for long-employed immigrants | 86% | 43% | 41% | 25% |
| Abortion as a matter of choice | 93% | 46% | 29% | 21% |
| Federal recognition of same-sex marriage | 92% | 60% | 48% | 38% |
| *Cultural conservatism index (0–1)* | *0.27* | ***0.65*** | ***0.74*** | *0.83* |

Switchers sit between the parties on economics and close to Republicans on immigration. Three-quarters of Biden→Trump switchers support expanding Medicaid; 62% want to keep the ACA; majorities want higher taxes on corporations and the wealthy. On the wall, asylum, and border patrol they are indistinguishable from Republicans. On abortion and same-sex marriage they are in the middle. New Trump voters are more conservative on both axes but still 73% for Medicaid expansion.

The hypothesis's first premise holds: the people who left agreed with Democratic economic positions, on the items the CES asks, far more than they agreed with Democratic positions on immigration.

### Which axis predicts leaving

Logit on Biden 2020 voters (N = 16,971; 327 switchers), with party identification, education, age, and race controlled:

| Per standard deviation | Coefficient | Marginal effect on P(switch) |
|---|---|---|
| Cultural conservatism | +2.03 (0.21) | **+7.6 points** |
| Economic-left position | −1.15 (0.19) | −2.2 points |

Cultural conservatism predicts switching at three and a half times the marginal effect of economic views. Splitting the cultural index: immigration +1.45 (marginal +4.5 points), abortion and same-sex marriage +0.87 (+2.4), policing −0.02 (nil). Immigration is the axis that moved Biden voters; the social items moved them about half as much; policing did not register.

For new voters, economics and culture weigh nearly equally (economic −1.45, immigration +1.28, social +1.14), and being Black is by far the strongest predictor of not voting Trump (−2.87).

### The voter the hypothesis describes

Restricting to Biden 2020 voters who hold left economic positions (index ≥ 0.6) and splitting by cultural views:

| Biden 2020 voters, economically left | N | Switched to Trump |
|---|---|---|
| Culturally liberal, income under $50k | 4,668 | **1.8%** |
| Culturally conservative, income under $50k | 360 | **23.3%** |
| Culturally liberal, $50k+ | 9,409 | 1.8% |
| Culturally conservative, $50k+ | 369 | 20.7% |

Same economic views, thirteen times the defection rate, depending on cultural views — and the same at every income. The economically-left, culturally-conservative voter is 24% of switchers against 5% of loyal Democrats. That voter exists, was concentrated among leavers, and left.

### Harris was perceived as far left, and the perception tracked immigration

| | Placed themselves at | Placed Harris at | Called Harris "very liberal" | Distance to Harris | Distance to Trump |
|---|---|---|---|---|---|
| Loyal Democrats | 2.6 | 2.8 | 7% | 1.1 | 4.2 |
| **Biden→Trump** | **4.4** | **1.8** | **59%** | **3.0** | **1.6** |
| New voters → Trump | 5.3 | 1.3 | 85% | 4.2 | 1.1 |
| Trump→Harris | 4.3 | 2.5 | 20% | 2.1 | 2.6 |
| Loyal Republicans | 5.9 | 1.1 | 94% | 4.8 | 0.9 |

Switchers placed themselves in the middle of the scale and Harris between "very liberal" and "liberal" — 59% chose "very liberal," against 7% of loyal Democrats and 20% of the mirror-image Trump→Harris switchers. They saw Trump as nearly twice as close to them as Harris. Among switchers, calling Harris "very liberal" tracks immigration views (+0.14 per SD) and, inversely, economic views (−0.11); abortion and same-sex-marriage views do not predict it (+0.04).

### What this says about the hypothesis

Three of its parts are supported, one is complicated, and two are untestable.

**Supported.** The leavers held Democratic-aligned economic views — a majority of switchers wanted Medicaid expanded, the ACA kept, and the wealthy taxed. They held conservative cultural views. And they perceived Harris as very liberal, a perception that tracked immigration attitudes. The economically-left, culturally-conservative low-income voter the hypothesis names is real, was five times over-represented among switchers, and defected at 23%.

**Complicated.** The hypothesis is that an economic pivot would have kept those voters. The data says immigration attitudes were the stronger force on who actually left — three and a half times the marginal effect of economic views. An economic message would have had to overcome, not merely add to, that. Whether it could have is a counterfactual about salience that cross-sectional attitudes cannot resolve.

**Untestable here.** Whether Harris "accepted" a framing — the CES observes voters, not campaigns. And whether the culture-war issue was transgender policy or "wokeness" — the survey does not ask. What it does show is that among the cultural items it *does* ask, immigration carried most of the weight, abortion and marriage about half as much, and policing none. If the framing that stuck was a culture-war framing, on this evidence it was the border.

### Reading Part 8 against Parts 4 and 5

Parts 4 and 5 found that leavers rated the economy badly, that the rating was set by 2022, and that it did not track local conditions. Part 8 finds that the same leavers held left economic views. Those are compatible: a voter can want Medicaid expanded and believe the economy under Biden was bad. The link between them — an economically-left voter who rates the incumbent's economy badly, sees the incumbent's successor as very liberal, and holds Republican views on immigration — is the profile of the 2024 switcher, and it is the profile of a voter reachable on economics who was not reached.

---

## Synthesis

**The structural conditions predicted a narrow loss, and a narrow loss is what happened.** A 38%-approval incumbent party with an open seat is expected to lose. Harris's result sits within the model's error band on either side of the prediction, depending on specification.

**The shift was everywhere, but the mechanism differed by place — and the stronghold turnout collapse was compositional, not a Democratic decision to abstain.** Nationally, three-quarters of the Democratic vote loss was share shift. In the largest Democratic counties it was turnout — 2.9M votes, half the national loss, 97% in safe states. But conditional on demographics, Biden and Trump 2020 voters stayed home at the same rate; the coalition lost more votes because it is built from low-propensity groups that surged in 2020 and reverted in 2024 while Republican-area surge voters stayed. Swing-state Democratic counties held their turnout. The Blue Wall was lost on share: Biden voters switching three to one over the reverse, and new voters breaking 58–40 for Trump.

**The switchers were reachable on economics and lost on immigration.** They wanted Medicaid expanded, the ACA kept, and the wealthy taxed, at rates far closer to Democrats than Republicans. They wanted the wall, asylum denied, and more border patrol, at rates indistinguishable from Republicans. Cultural conservatism predicted leaving at three and a half times the marginal effect of economic views, and immigration carried most of it; abortion and marriage half as much; policing none. They saw Harris as "very liberal," and that perception tracked immigration, not social issues. Whether an economic message could have overridden that is the counterfactual the data cannot run; that the voters existed, and were not kept, is not in doubt.

**The places that moved most were not the places the 2016 narrative would predict.** Diverse, lower-education, urban and border counties swung hardest. White non-college counties, controlling for income and education, swung less than average.

**Local economic performance did not protect the incumbent party, because voters did not perceive it.** Real wage growth and manufacturing exposure explain nothing about the county swing; the county's economic record explains 0.6% of how its residents rate the economy in a cross-section and nothing about how the same person's rating changed over four years. What does explain the rating is party identification and media diet. The perception preceded the vote: a Biden voter's 2022 rating predicted both switching and staying home in 2024, and none of the 438 who saw improvement in 2022 switched. Whether something else was already moving those voters in 2022 is the question that remains.

**Federal money that visibly arrived moved the county vote, but not through perception and not through turnout.** Counties with more infrastructure and recovery obligations per capita swung about half a point less right per standard deviation, robust to composition, urbanity, and outliers — the one local economic variable that did register in the vote. Their residents rated the economy no better once composition is controlled, and were no less likely to defect. The effect is on the share side — Republican votes grew less where infrastructure money went; Democratic votes held better where recovery money went — with no movement in total turnout. Delivery worked on the margin of who voted Republican, not on belief about the economy and not on mobilization; the data does not say how.

**The class gradient is structural and predates the campaign — and in 2024 it was not about class.** Democrats have lost ground in the poorest counties relative to 2012 in every cycle since. But the white low-income counties did their moving in 2016 and held; the 2024 movement in the bottom quartile was Hispanic and Black low-income counties. At the individual level, a Biden voter's income did not predict whether they left; being Hispanic did, at every income. The 2024 chapter of the class realignment is an ethnic realignment that shows up as a class gradient because of where Hispanic voters live.

**The information problem is individual, not geographic.** Only 4.7% of the variance in economic perception is between counties, and almost none of that survives controlling for who lives there. Tested directly, the local news environment — 213 counties with no outlet, 1,526 with one — changes neither media diet, nor perception, nor the partisan gap, nor switching. The disconnect between what happened locally and what voters believed tracked the sources people chose within the same county, not the sources available to them. The partisan divergence in perception is widest in the white non-college counties where the structural drift has been strongest.

**The Biden coalition's 2024 exits were visible in 2022.** In the panel, how a Biden voter rated the economy at the inflation peak predicted whether they would vote Trump or stay home two years later, and the gradient is monotonic across all five levels of the item. The campaign of 2024 inherited a coalition whose leavers had already sorted themselves on economic perception — a perception that, in the same people, did not track the economy of the county they lived in.

**Prices were the least filtered economic perception, not an unfiltered one.** Democrats, independents, and Republicans agreed that prices had gone up — 80%, 90%, and 95% — and reported price experience lowered the economy rating by the same amount in every party. But whether prices had gone up "a lot" was itself partisan: 35% of Democrats said so against 76% of Republicans. Saying "a lot" predicted leaving Biden's coalition independently of the overall economy rating. The Democratic base recognized the record and reported the inflation; it reported less of it than everyone else.

---

*Methods, data handling, full regression tables, and known limitations: [`technical_appendix.md`](technical_appendix.md)*
*Notebooks: [`notebooks/`](../notebooks/) · Figures: [`outputs/figures/`](../outputs/figures/) · Tables: [`outputs/tables/`](../outputs/tables/)*
