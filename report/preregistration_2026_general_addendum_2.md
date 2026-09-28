# Addendum 2 to the pre-analysis plan: validating Test A before the election

*Written 27 September 2026, before the 3 November 2026 election, before any 2026 result exists, and before any of the data named below has been downloaded or analyzed. It changes nothing in [`preregistration_2026_general.md`](preregistration_2026_general.md) or [Addendum 1](preregistration_2026_general_addendum_1.md). The tests, measures and decision rules there stand. This addendum fixes, in advance, a set of checks on past elections that show what Test A can and cannot detect, and how their results will be used to read Test A's result. The commit history of this file is the record of when it was written.*

## The question

Test A asks whether El-Sayed, an economic-left Senate candidate, runs relatively better or worse than Benson, a mainstream governor candidate on the same ballot, in the Michigan towns that swung most to Trump in 2020→2024. It measures this as the slope of the El-Sayed − Benson gap on that swing.

Because the two candidates share a ballot, a shift toward or away from Democrats that affects both equally cancels out, whether it is uniform or concentrated in the Trump-swing towns. The slope can still be non-zero for reasons that have nothing to do with ideology or economic policy, if the two candidates catch a shared movement unequally:

- **familiarity:** a known statewide officeholder against a newcomer;
- **roll-off and straight-ticket voting** that differ between a Senate race and a governor race, and between town types;
- **identity:** reactions to the candidates' religion or ethnicity;
- **opponents** who appeal differently to swing-town voters;
- **wave-year behavior:** 2026 is a midterm under a Republican president, a possible Democratic wave, while the Addendum 1 benchmark (2022) came from a midterm under a Democratic president.

The checks below measure how large these non-ideological slopes are in past elections, and whether the method can detect a candidate-specific swing appeal where one is widely believed to exist.

## Common specification

Every check uses Test A's specification unchanged:

- Gap = candidate A's two-party share − candidate B's two-party share (points).
- WLS of the gap on the swing, weighted by the votes cast in the race being compared, with HC1 errors.
- Units under 200 votes dropped.

**The swing** is the change in the Republican presidential candidate's two-party share between the two presidential elections before the election being tested:

- 2012→2016 for 2018 races;
- 2016→2020 for 2022 races (as 2020→2024 for 2026).

Every check is also reported with the 2012→2016 swing, the Obama-to-Trump movement, as a secondary measure.

## V1. Wave-year benchmark and familiarity: Michigan 2018 (municipalities)

Michigan 2018 is the closest analog to 2026: a midterm under a Republican president, with a Democratic statewide sweep, on the same state's map and units as Test A.

- **V1a, mainstream newcomers (benchmark):**
  - Nessel (Attorney General) − Whitmer (Governor)
  - Benson (Secretary of State) − Whitmer (Governor)
  - Nessel − Benson

  All three were first-time statewide candidates.
- **V1b, familiarity:** Stabenow (U.S. Senate; incumbent since 2001) − Whitmer (Governor, newcomer). This isolates what a known incumbent against a newcomer produces.

**Prediction.** V1a slopes fall within ±0.1, as in the 2022 benchmark. There is no directional prediction for V1b; it is a measurement.

## V2. Positive controls: can the method detect a known populist swing appeal? (counties)

Pairs where one Democrat is widely described as economic-populist and as running unusually well in Obama-to-Trump areas, beside a more conventional Democrat on the same midterm ballot:

- **V2a, Ohio 2018:** Sherrod Brown (Senate) − Richard Cordray (Governor)
- **V2b, Wisconsin 2018:** Tammy Baldwin (Senate) − Tony Evers (Governor)
- **V2c, Pennsylvania 2022:** John Fetterman (Senate) − Josh Shapiro (Governor)

**Unit.** County: 88, 72 and 67 counties respectively. Presidential swings come from the MIT Election Lab county file already used in this project, and Senate and governor results from the states' official county results.

**Prediction.** Positive slopes for Brown and Baldwin under the 2012→2016 swing. No directional prediction for Fetterman: his populist branding sits beside Shapiro's unusual strength, and the primary 2016→2020 swing for 2022 is small.

**Known confound.** Brown and Baldwin were incumbents and Cordray and Evers were not, so V2a and V2b combine populism with familiarity. V1b's familiarity slope is what separates the two.

## V3. Placebo swing

Rerun V1 and V2 with the 2008→2012 presidential swing, a period unrelated to the Trump realignment. A method picking up appeal to Trump-swing voters in particular should not produce similar slopes on this swing. If it does, the slopes reflect generic place differences rather than swing-voter appeal.

## V4. Media-market check for Test A (applied to the 2026 result)

Test A's primary model is rerun with fixed effects for Michigan's television media markets. Each municipality takes its county's Nielsen designated market area. This removes any effect of advertising bought market by market, including outside spending against El-Sayed, from the slope. It is reported as a secondary result beside the primary one; the primary result and its decision rule are unchanged.

## V5. Direction forecasts for known non-ideological forces in 2026

These are recorded now, so a surprising Test A result cannot be explained after the fact by a force chosen afterwards. Each entry says which direction it would push the El-Sayed − Benson slope, if it varies with the Trump swing at all.

| Force | Expected effect on the slope |
|---|---|
| Statewide attack ads against El-Sayed | Lowers his level everywhere. Affects the slope only if concentrated in particular markets (V4 addresses this) |
| Familiarity: Benson a sitting statewide officeholder, El-Sayed a first-time nominee | Sign and size estimated by V1b |
| Reactions to a Muslim, Arab-American candidate | If negative reactions are stronger in Trump-swing towns, negative. Not measurable directly |
| Arab-American support concentrated in Dearborn, Dearborn Heights and Hamtramck | Positive in those cities; handled by Test A's pre-registered exclusion |
| Different Republican opponents (Senate vs governor) | Either direction; not predicted |

## How the results will be used

When Test A is reported, beside its primary result:

1. **Ordinary-difference band.** The band of slopes counted as "ordinary candidate differences" becomes the wider of Addendum 1's 2022 range (about −0.06 to +0.04) and the V1a range. If V1a slopes fall outside ±0.1, the band widens to include them, and the report says so.
2. **Familiarity allowance.** If V1b's slope is outside the ordinary band, the report states that familiarity alone produces a slope of that size and sign. An El-Sayed − Benson slope of the same sign and similar or smaller size will not be attributed to his economic positioning.
3. **Sensitivity.** If V2a or V2b produces a positive slope outside the ordinary band, the method is shown able to detect a populist swing appeal where one is widely believed to exist. If neither does, the report says the method did not detect the known cases, so a null Test A result is weak evidence of no effect.
4. **Placebo.** If V3 slopes are comparable in size to V1 and V2, the report says the slopes may reflect generic place differences and qualifies all of the above.
5. **Media markets.** If V4's slope differs from the primary slope in sign, or by more than half its size, the report says market-level advertising may account for part of the result.

## Data

To be downloaded after this addendum is committed, with sources and reconciliation to certified statewide totals reported as in Addendum 1:

- **Michigan 2012, 2016 and 2018:** OpenElections precinct files, or the MIT Election Lab files where OpenElections is incomplete; rolled up to municipalities with `michigan_pull.py`.
- **Ohio 2018, Wisconsin 2018 and Pennsylvania 2022:** county Senate and governor results, from OpenElections county files or the states' official results.
- **Presidential county results 2008–2020:** the MIT Election Lab county file already on disk.
- **County-to-media-market assignment for Michigan:** Nielsen's published county list.

## Limits

No design here separates ideology from everything else a candidate brings. The positive controls are candidates *widely believed* to have populist swing appeal, not candidates whose appeal has been measured. V2 is at county level, which is coarser than Test A's municipalities, and differences in resolution can change slope sizes. What the checks can show is how large non-ideological slopes are, whether the method detects the cases it should, and how much of a slope familiarity alone can produce.
