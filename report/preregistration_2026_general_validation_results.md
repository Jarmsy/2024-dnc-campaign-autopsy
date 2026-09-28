# Test A validation: results of Addenda 2 and 3

*Recorded 27 September 2026, before the 3 November 2026 election and before any 2026 result exists. This file reports what the checks fixed in advance in [Addendum 2](preregistration_2026_general_addendum_2.md) and [Addendum 3](preregistration_2026_general_addendum_3.md) found. Those addenda were committed before their data was downloaded (Addendum 2) or their models were estimated (Addendum 3). Notebooks: `28_testA_validation.ipynb` and `29_testA_specification_choice.ipynb`. Tables: `outputs/tables/testA_validation_addendum2.csv` and `testA_specification_choice_addendum3.csv`.*

## Data

**Michigan (V1).** 2008, 2012 and 2016 presidential results and the 2018 Senate, governor, attorney general and secretary of state results. All come from OpenElections precinct files, and every contest equals Michigan's certified statewide total exactly. They are rolled up to 1,523 municipalities matched across all four years, covering at least 99.8% of each year's vote.

**Positive controls (V2), by county.**
- Ohio 2018, from the OpenElections precinct file. The Senate Democrat equals the certified total exactly; the Republican and the governor race are within 0.2%.
- Wisconsin 2018, from the OpenElections ward file; exact.
- Pennsylvania 2022, from the OpenElections county file; exact.
- Presidential swings come from the MIT Election Lab county file.

**Place characteristics (Addendum 3).** ACS 2016–2020 five-year estimates, via `acs_place_controls_pull.py`. They matched 1,498 of 1,523 Michigan municipalities, holding 98.0% of the vote, and all counties. The largest unmatched places are Bay City, Garden City and Traverse City, where county-name abbreviations differ between sources. Those will be fixed before the 2026 run.

## Addendum 2, judged by its pre-committed rules

| Rule | Result |
|---|---|
| 1. Ordinary-difference band | Michigan 2018 down-ballot newcomers: Nessel − Whitmer −0.085 (−0.113 to −0.057), Benson − Whitmer 0.000 (−0.013 to 0.014), Nessel − Benson −0.085 (−0.109 to −0.062). All within ±0.1. With Addendum 1's 2022 range, the band is **about −0.09 to +0.04** |
| 2. Familiarity | Stabenow (incumbent) − Whitmer (newcomer): +0.008 (−0.005 to 0.021). **Familiarity alone produces no slope** |
| 3. Sensitivity | Brown − Cordray +0.173 (0.122 to 0.224), outside the band. Baldwin − Evers +0.184 (0.056 to 0.312). **The method detects the expected populist appeal** |
| 4. Placebo | The 2008→12 swing gives slopes as large or larger, also per standard deviation: Nessel − Whitmer −0.300, Brown +0.477, Baldwin +0.521. **Test A's original slope is not specific to Trump-swing voters; it may reflect general differences between places** |
| 5. Media markets | Applies to the 2026 result only |

Pennsylvania (no prediction): Fetterman − Shapiro +0.437 (0.188 to 0.686) on the 2016→20 swing, +0.039 on 2012→16.

## Addendum 3: specification chosen by the pre-committed rule

Target-swing coefficient (95% interval) for each specification, with the target-swing and placebo coefficients per standard deviation:

| Case | S0 original | S1 + earlier swings and level | S2 + place characteristics | S3 + county fixed effects |
|---|---|---|---|---|
| Brown − Cordray (OH 2018) | +0.173 (0.122, 0.224) | **+0.144 (0.100, 0.188)**; per SD 0.86 vs placebo 0.33 | +0.087 (−0.192, 0.367) | — |
| Baldwin − Evers (WI 2018) | +0.184 (0.056, 0.312) | **+0.118 (0.048, 0.187)**; per SD 0.64 vs placebo 0.38 | +0.039 (−0.135, 0.213) | — |
| Nessel − Whitmer (MI 2018) | −0.085 | −0.064 | −0.022 | −0.069 |
| Benson − Whitmer (MI 2018) | 0.000 | +0.008 | +0.037 | +0.001 |
| Nessel − Benson (MI 2018) | −0.085 | −0.071 | −0.059 | −0.070 |
| Stabenow − Whitmer (familiarity) | +0.008 | +0.007 | +0.028 | −0.028 |
| Fetterman − Shapiro (PA 2022; not used in the choice) | +0.437 | +0.191 (−0.045, 0.427) | +0.175 | — |

| | Sensitivity | Placebo specificity | Ordinary pairs | Passes |
|---|---|---|---|---|
| S0 | ✓ | ✗ (Baldwin: placebo 1.24 per SD > target 1.00) | ✓ | no |
| **S1** | ✓ | ✓ | ✓ | **yes** |
| S2 | ✗ (both intervals include 0) | ✗ | ✓ | no |
| S3 (Michigan, criterion 3 only) | not testable | not testable | ✓ | Michigan version |

**Chosen: S1 as the pre-registered secondary version of Test A.** Following the rule as written, the Michigan version is **S3**. It adds the ACS place characteristics and county fixed effects to S1, and passes the one criterion that Michigan's municipal data can test.

**For 2026 this means.** Beside Test A's primary result (S0), the report gives the El-Sayed − Benson coefficient on the 2020→24 swing from a model that also includes:
- the 2008→12, 2012→16 and 2016→20 swings;
- the 2020 Republican share;
- the four ACS place characteristics;
- county fixed effects.

That coefficient is judged against the band of about −0.09 to +0.04. The S1 version, without place characteristics or county effects, is reported alongside it.

## What this settles, and what it doesn't

- **Settled:**
  - The original slope picks up general place differences.
  - Adding the earlier swings and the Republican level separates the known populist cases from the placebo in the county data.
  - Familiarity doesn't manufacture a slope.
- **A tension the rule accepted in advance.** The Michigan version (S3) includes the place characteristics that removed the positive controls' signal in the county data (S2). With about 1,500 towns rather than 70–90 counties, Michigan has far more power, but S3's ability to detect a real populist appeal could not be tested. A null S3 result in 2026 will therefore be read alongside the S1 result, and reported as weak evidence of no effect if S1 shows one.
- **Small basis.** The choice rests on two positive controls and three ordinary pairs.

## Addendum 4: views on Israel and the swing

*Recorded 28 September 2026, before the election. Notebook `30_israel_views_and_swing.ipynb`; tables `outputs/tables/israel_views_by_county_swing.csv` and `israel_views_by_path.csv`.*

**Place level, the pre-registered reading.** Support for providing arms to Israel (CES 2024, 26% overall), per 10 points of county 2020→24 swing to Trump:

| Model | Change (points) | 95% interval |
|---|---|---|
| All respondents | −7.3 | −10.9 to −3.8 |
| Adding party identification (model 2) | −1.9 | −4.8 to +1.1 |
| Michigan only, with party (1,907 respondents in 81 counties) | −17.6 | −40.8 to +5.5 |

"Do not get involved" (22% overall) in model 2: +2.4 (−1.1 to +6.0); in Michigan +25.8 (+3.5 to +48.1).

**Reading, by Addendum 4's rule: no association.** In model 2 the change is under 3 points, with an interval inside ±5. Places that swung to Trump show less support for arming Israel overall, but only because their party mix differs. Among people of the same party, views on arming Israel don't vary with the swing. So El-Sayed's Gaza position is unlikely to drive a Test A slope through the swing towns nationally.

**Michigan is noted, not decisive.** Within Michigan, people in swing counties were more likely to say the U.S. should not get involved, with an interval clear of zero. The sample is small and the model isn't the pre-registered one, so it is reported as a caution: a positive El-Sayed slope in Michigan could partly reflect a stay-out view, rather than economics, among swing-town voters.

**Individual level.**

| Path (2020 → 2024) | Arms to Israel (CES) | Don't get involved (CES) | Sides with Israelis (ANES) |
|---|---|---|---|
| Loyal Democrats | 15.5% | 10.8% | 15.1% |
| Biden → Trump (recalled) | 20.9% | 27.7% | 25.2% |
| New → Trump | 26.2% | 36.4% | 39.7% |
| Loyal Republicans | 50.6% | 21.8% | 60.4% |

The Biden → Trump switchers sat close to loyal Democrats on arming Israel and far from loyal Republicans. What set them apart was wanting the U.S. to stay out: 28% against 11% of loyal Democrats. They were not more pro-Israel. If El-Sayed's position registers as opposition to U.S. involvement, it is closer to the switchers' view than Benson's might be. That is the non-economic reading of any positive slope that the report must state.
