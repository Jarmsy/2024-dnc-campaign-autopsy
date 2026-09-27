# Addendum 1 to the pre-analysis plan: a dry run and a benchmark for Test A

*Written 26 September 2026, before the 3 November 2026 election and before any 2026 result exists. It changes nothing in [`preregistration_2026_general.md`](preregistration_2026_general.md): the tests, measures, models and decision rules there stand exactly as written. It records two things learned by running Test A's specification on past Michigan ballots, so that the size of the eventual Test A result can be judged against them. The commit history of this file is the record of when it was written.*

## Why an addendum

Test A regresses the gap between El-Sayed's and Benson's two-party shares, municipality by municipality, on the 2020→2024 swing to Trump. A slope different from zero says El-Sayed did relatively better (or worse) where voters swung. But two Democrats on the same ballot can differ in how they track the swing for reasons that have nothing to do with ideology. The plan's secondary tests (Savit and Gilchrist in place of Benson) guard against that for one candidate; they do not say how large ordinary differences are. The two exercises below do.

## 1. Dry run on the 2024 ballot (notebook 27)

The exact Test A specification — Michigan municipalities, WLS weighted by votes, HC1 errors, municipalities under 200 votes dropped, swing = Trump two-party share 2024 − 2020 — with Slotkin (Senate) in El-Sayed's place and Harris (President) in Benson's:

| | Slope | 95% interval | N |
|---|---|---|---|
| All municipalities | +0.24 | 0.20 to 0.28 | 1,464 |
| Excluding Dearborn, Dearborn Heights, Hamtramck | +0.30 | 0.23 to 0.37 | 1,461 |

The pipeline works: 2020 (MIT Election Lab precinct file) and 2024 (OpenElections) both reconcile to certified statewide totals within 0.1%, and 1,526 municipalities hold 99.7–100% of the vote. The steep slope reflects president–Senate ticket-splitting in places that swung to Trump. **2026 has no presidential race; this comparison is not the benchmark for Test A.**

## 2. Benchmark: two mainstream Democrats, both down-ballot, 2022 (notebook 27)

In 2022 three mainstream Democrats won statewide on one Michigan ballot. The same model, on the same 2020→2024 swing, weighted by governor votes (1,436 municipalities; 2022 data reconcile to certified totals within 0.05%):

| Pair | Slope | 95% interval | Excluding the three cities |
|---|---|---|---|
| Nessel (AG) − Whitmer (Governor) | −0.02 | −0.04 to 0.00 | 0.00 (−0.05 to 0.04) |
| Benson (SoS) − Whitmer (Governor) | +0.03 | −0.01 to 0.08 | +0.04 (−0.07 to 0.15) |
| Nessel (AG) − Benson (SoS) | −0.06 | −0.11 to 0.00 | −0.04 (−0.17 to 0.10) |

## How these will be used

When Test A is reported:

- The primary result is still judged exactly as the plan says (sign and p < 0.05).
- Alongside it, the report will say whether the El-Sayed − Benson slope falls **inside or outside the range of the 2022 down-ballot pairs (about −0.06 to +0.04)**. A slope inside that range will be described as indistinguishable from an ordinary difference between down-ballot Democrats, whatever its p-value; a slope clearly outside it — beyond roughly ±0.1 — as larger than ordinary candidate differences.
- The 2024 Slotkin–Harris slope is reported only as the pipeline check, not as a benchmark.

## Limits

2022 was a midterm under a Democratic president; 2026 is a midterm under a Republican one, and the swing measure postdates the 2022 vote. The benchmark describes how much ordinary down-ballot candidates diverge along this swing, not what El-Sayed's slope will be. Data problems found in the 2026 files will be handled as the plan's reporting rules specify.
