# 2024 DNC Campaign Autopsy: A Data-Driven Analysis

*Elections covered: 1948–2024 | Unit of analysis: county (Parts 2–3), national election (Part 1)*
*Data: FRED API · MIT Election Lab · Census ACS 2020 · Gallup*

---

## Executive Summary

Kamala Harris lost the 2024 presidential election with **49.25% of the two-party popular vote**. This report decomposes that result across three independent analytical lenses.

**The central finding is uncomfortable for simple narratives in either direction.** Harris was not crushed by catastrophically bad structural conditions — she actually *overperformed* what historical fundamentals models predict for an incumbent party with a 38% approval president. Nor was the loss a narrow, fixable messaging failure. It reflects a decade-long structural realignment of working-class voters away from Democrats that is visible in county-level data across every cycle from 2016 onward.

**Three findings, briefly:**

| | Finding |
|---|---|
| **Part 1** | Structural fundamentals predicted Harris at 47.9%. She got 49.25%. She **overperformed her baseline by +1.4pp**. |
| **Part 2** | 90% of counties shifted right (median −3.1pp). By raw vote count, **demobilization explains 44% of the vote loss** vs. 21% for persuasion. |
| **Part 3** | The income gradient in Democratic voting has **widened every cycle since 2012**. Harris did not create this pattern; she inherited and modestly accelerated it. |

---

## Part 1: Structural Fundamentals Baseline

### Model specification

We fit an incumbency-adjusted OLS regression on 19 presidential elections (1948–2020) following Abramowitz's "Time for Change" framework. The dependent variable is the incumbent party's two-party vote share. Predictors:

- **Q2 GDP growth** — annualized real GDP growth, Q1→Q2 of the election year (FRED: GDPC1)
- **June approval** — incumbent president's Gallup approval rating in June (historical Gallup)
- **Consecutive terms** — terms the incumbent party has held going into the election
- **Open seat** — binary: no sitting president on the ballot

The model is fit on 1948–2020 and applied to 2024 strictly out-of-sample.

**Model performance:** In-sample R² = 0.81, leave-one-out RMSE = 3.75pp. The coefficients are economically sensible: each additional point of Q2 GDP growth adds +0.19pp for the incumbent; each point of June approval adds +0.27pp; an open seat costs −2.6pp.

### 2024 prediction

| Input | Value |
|---|---|
| Q2 2024 GDP growth | +3.6% annualized |
| Biden June 2024 approval | 38% |
| Consecutive Democratic terms | 1 |
| Open seat | Yes (Biden withdrew July 2024) |
| **Predicted Harris two-party share** | **47.9%** |
| **Actual Harris two-party share** | **49.25%** |
| **Residual (actual − predicted)** | **+1.4pp** |

Harris overperformed the model. Biden's 38% June approval is the overwhelming driver of the predicted result — only Carter (1980, 32%) and Truman's heir apparent (1952, 32%) faced comparably poor approval, and both their parties lost decisively. The decent Q2 GDP (+3.6%) provided a modest counterweight but could not overcome that approval headwind.

### Notable residuals in historical context

The model's single largest miss is 2020: it predicted 63.2% for Biden given COVID's GDP collapse (−28% Q2 annualized), but he received 52.3% — a −10.9pp underperformance. This reflects both the pandemic distorting the GDP signal and Trump's unusual incumbency dynamics. By contrast, the largest positive residual is 1948 (+4.1pp, Truman) — another candidate who outperformed grim structural expectations.

### Implication

The structural conditions in 2024 — low approval, high incumbent fatigue — warranted a Democratic loss. Harris beat those conditions. This means the question "why did Democrats lose?" is more nuanced than "bad fundamentals." The deeper question is why the long-run structural realignment of the electorate has made the fundamentals themselves increasingly unfavorable regardless of candidate or cycle.

---

## Part 2: Demobilization vs. Persuasion Decomposition

### Framework

For each county, we apply a Kitagawa-Blinder decomposition of the 2020→2024 Democratic vote change:

```
ΔDem votes = Turnout component + Share component
```

- **Turnout component** = `dem_share_2020 × (total_votes_2024 − total_votes_2020)`
  Votes Harris gained or lost purely from overall turnout change, holding her share at Biden's 2020 level.

- **Share component** = `(dem_share_2024 − dem_share_2020) × total_votes_2024`
  Votes Harris gained or lost from her share of the electorate shifting.

The share component conflates persuasion (vote-switching) with differential demobilization (Democratic voters specifically not turning out). Separating these cleanly requires individual-level panel data. As a heuristic: counties where turnout was flat but share collapsed point toward persuasion; counties where share was stable but turnout fell point toward differential mobilization.

### Geographic scope

The 2024 rightward shift was nearly universal:

| Metric | Value |
|---|---|
| Counties shifting right | **1,826 / 2,029 (90%)** |
| Median county swing | **−3.1pp** |
| Turnout-weighted mean swing | **−5.8pp** |
| Comparison: 2016→2020 median swing | +2.1pp (toward Dems) |

This is not a story of particular swing states, sunbelt demographics, or coastal metro collapse. The rightward movement was geographically pervasive — the modal county moved right, regardless of region, density, or partisan baseline.

### Vote loss decomposition

Among the 1,669 counties that lost Democratic votes between 2020 and 2024:

| County type | # Counties | % of total Dem vote loss |
|---|---|---|
| Demobilization-dominant (turnout component >60% of loss) | 302 | **44%** |
| Mixed (both components negative) | 308 | **29%** |
| Persuasion-dominant (share component >60% of loss) | 491 | **21%** |
| Offsetting components | 563 | 6% |

**By raw vote count, demobilization explains roughly twice as much of the Democratic vote loss as persuasion.** But persuasion-dominant counties outnumber demobilization-dominant counties (491 vs. 302) — meaning persuasion affected more *places*, while demobilization drove more *votes*.

This reflects coalition geography. The counties that generate Democratic vote totals are large, dense, already highly Democratic — and they primarily lost votes through turnout collapse. The counties that flipped via share shift tend to be smaller exurban and rural counties where there were more persuadable or newly mobile voters.

### Caveats on the 2020 baseline

Biden's 2020 coalition was historically unusual. Pandemic conditions, record early voting infrastructure, and an intensely anti-Trump mobilization environment produced historically high Democratic turnout in high-education suburban counties. Some of the 2024 "demobilization" is the normalization of an exceptional baseline rather than a new collapse. The 2016→2020 comparison (Biden gained across similar counties) should be read alongside the 2020→2024 numbers, not in isolation.

---

## Part 3: Economic Populism Premium

### County-level regression

Merging Census ACS 2020 county-level economic characteristics with the county vote decomposition, a weighted least squares regression (weighted by 2020 county turnout) explains **52% of the variance** in the 2020→2024 county swing. All four economic variables are statistically significant.

**Coefficient estimates (WLS, N=1,990 counties):**

| Variable | Effect on swing | p-value |
|---|---|---|
| Log(median household income) | −3.69 per log unit | <0.001 |
| College education share | +23.9pp per unit | <0.001 |
| White non-college share | +18.4pp per unit | <0.001 |
| Unemployment rate | −13.3pp per unit | 0.043 |
| Prior Dem share (2020) | −2.86pp per unit | <0.001 |

**Marginal effects at the mean county:**

| Change | Effect on swing |
|---|---|
| +$10K median income | −0.61pp (richer counties swung *less* right) |
| +10pp college share | +2.4pp (toward Dem) |
| +10pp white non-college share | −1.8pp (toward R) |

Higher income and education are associated with smaller rightward swings; higher white non-college share is associated with larger rightward swings. The prior partisan lean coefficient (−2.86) reflects mean reversion — counties that were already highly Democratic in 2020 swung somewhat less than their structural economic profile would predict.

### The populism premium trend: Obama 2012 baseline

Comparing each Democratic candidate's county-level share against the Obama 2012 baseline, stratified by income quartile (population-weighted within quartile):

| Cycle | Q1 (poorest) | Q2 | Q3 | Q4 (richest) | Gradient (Q4−Q1) |
|---|---|---|---|---|---|
| Clinton 2016 vs. Obama 2012 | −7.5pp | −8.4pp | −7.6pp | −5.0pp | **+2.6pp** |
| Biden 2020 vs. Obama 2012 | −7.7pp | −7.0pp | −5.4pp | −1.4pp | **+6.2pp** |
| Harris 2024 vs. Obama 2012 | −10.0pp | −8.5pp | −6.7pp | −2.9pp | **+7.1pp** |

Two patterns are unambiguous:

**1. The income gradient has widened every cycle.** The Q4−Q1 gap grew from 2.6pp (2016) to 6.2pp (2020) to 7.1pp (2024). Democrats have systematically improved their relative standing in wealthy counties while deteriorating in poor ones — the canonical class inversion of American party politics.

**2. Harris did not create this pattern.** The 2024 gradient (+7.1pp) is nearly identical to Biden's (+6.2pp). The difference between the Biden and Harris cycles is that the *entire distribution* shifted ~2–3pp further right across all four income quartiles — not a structural change in the gradient's shape.

### What this means for "populism premium"

The "economic populism premium" — the hypothesis that Democratic candidates who emphasize working-class economic messaging outperform in low-income areas — cannot be confirmed or denied from this data alone. What is visible is a structural trend: Democrats have been steadily ceding low-income counties since at least 2016, regardless of candidate or messaging emphasis. Clinton, Biden, and Harris all show the same pattern at different magnitudes.

This suggests the driver is structural — changes in the educational and cultural sorting of the two parties over a decade — rather than a cycle-specific messaging failure.

---

## Synthesis

### A consistent narrative across three analyses

The three analytical lenses converge on a coherent story:

**The loss was structurally expected but larger than expected.** Historical fundamentals models predicted a Democratic loss given Biden's 38% approval. Harris beat those predictions by 1.4pp. The actual deficit was not "worse than the fundamentals"; it was roughly at the fundamentals, which were already bad.

**The mechanism was diffuse, not concentrated.** A −5.8pp weighted swing across 90% of counties is not a story of a particular state, demographic segment, or campaign failure. It is a broad-based rightward movement with no obvious single cause.

**Demobilization drove more votes; persuasion was more widespread.** The largest absolute vote losses came from already-Democratic strongholds where turnout collapsed — likely reflecting reduced enthusiasm and the unusual nature of Biden-to-Harris as a transition candidate. Persuasion (share shift) was geographically wider but smaller in aggregate magnitude.

**The class realignment is structural and multi-cycle.** Every Democratic candidate since Obama has underperformed his 2012 baseline in low-income counties, and the gap has grown. This is not a 2024-specific phenomenon, and no single campaign is likely to reverse it.

### The honest bottom line

Democrats lost 2024 primarily because:

1. They were the incumbent party with a historically low-approval president, after accumulated inflation, heading into a third Democratic term attempt — all of which structural models weight heavily against.
2. The underlying class realignment of American politics continued its trajectory, with low-income and non-college counties continuing to drift right at a pace that has been consistent for a decade.
3. Demobilization of the unusually high 2020 coalition, combined with modest persuasion losses, produced a near-universal rightward shift that any Democratic candidate would likely have faced in this environment.

Harris beat her structural conditions. The structural conditions themselves were the problem — and those structural conditions reflect changes that predate her candidacy by nearly a decade.

---

*Technical details and reproducible code: see [`notebooks/`](../notebooks/) and [`report/technical_appendix.md`](technical_appendix.md)*
*Figures: [`outputs/figures/`](../outputs/figures/)*
*Processed data: [`data/processed/`](../data/processed/)*
