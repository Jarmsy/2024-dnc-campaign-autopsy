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
