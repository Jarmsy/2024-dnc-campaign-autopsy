# Addendum 3 to the pre-analysis plan: a more specific version of Test A

*Written 27 September 2026, before the 3 November 2026 election, before any 2026 result exists, and before any of the specifications below has been estimated. It changes nothing in the original plan or in Addenda 1 and 2: Test A's primary test and decision rule stand. This addendum fixes, in advance, a set of candidate specifications and the rule for choosing among them using past elections only. The chosen specification becomes a pre-registered **secondary** version of Test A. The commit history of this file is the record of when it was written.*

## Why

Addendum 2's checks (notebook 28) found that Test A's slope is **sensitive but not specific**:

- It detects the expected populist appeal. Brown − Cordray in Ohio 2018 gives +0.17 (0.12 to 0.22) on the 2012→16 swing, and Baldwin − Evers in Wisconsin 2018 gives +0.18 (0.06 to 0.31).
- Ordinary down-ballot pairs stay within about ±0.09, and familiarity alone produces no slope (Stabenow − Whitmer, +0.008).
- But a placebo swing from an unrelated period, 2008→12, produces slopes as large or larger, also per standard deviation: from −0.30 (Nessel − Whitmer) to +0.52 (Baldwin − Evers). That placebo swing is nearly uncorrelated with the 2012→16 swing.

So candidates' relative strength varies across places in ways that line up with many place measures. A slope on the 2020→24 swing alone cannot show that a candidate appealed to Trump-swing voters *in particular*. An exploratory check found that controlling for the Republican vote level does not remove the problem (Brown +0.15, Baldwin +0.14).

The fix is to ask whether the gap tracks the 2020→24 swing **beyond** other measures of how places differ.

## Candidate specifications

In every specification the gap, the weights, the 200-vote cutoff and the HC1 errors are as in Test A. "Target swing" means the presidential swing Test A is about: 2020→24 for 2026. In the validation cases it is the analogous swing before each election (2012→16 for 2018, 2016→20 for 2022).

- **S0 (the original Test A):** gap on the target swing.
- **S1, earlier swings and level:** S0 plus every earlier presidential swing available back to 2008, plus the Republican two-party share in the election that starts the target swing.
  - 2026: 2008→12, 2012→16 and 2016→20 swings, plus the 2020 Republican share.
  - Michigan 2018: 2008→12, plus the 2012 share.
  - Ohio and Wisconsin 2018: 2008→12, plus the 2012 share.
  - Pennsylvania 2022: 2008→12 and 2012→16, plus the 2016 share.
- **S2, plus place characteristics:** S1 plus, from the Census Bureau's American Community Survey (2016–2020 five-year):
  - log total population;
  - share of adults 25+ with a bachelor's degree or higher;
  - log median household income;
  - share White non-Hispanic.

  These are measured for Michigan cities and townships (county subdivisions) and for counties.
- **S3, plus county fixed effects** (Michigan municipal data only): S2 plus a fixed effect for each county, so towns are compared only with other towns in the same county.

## How one specification will be chosen, using past elections only

The quantity of interest in each specification is the coefficient on the target swing. A specification **passes** if all of the following hold in the validation cases:

1. **Sensitivity:** the target-swing coefficient stays positive, with a 95% interval excluding zero, for Brown − Cordray (Ohio 2018) and Baldwin − Evers (Wisconsin 2018).
2. **Specificity, placebo:** in the same model, the 2008→12 swing's coefficient, scaled by its standard deviation, is smaller in absolute value than the target swing's coefficient scaled by its standard deviation, for Brown and Baldwin.
3. **Specificity, ordinary pairs:** the target-swing coefficient for each Michigan 2018 down-ballot pair (Nessel − Whitmer, Benson − Whitmer, Nessel − Benson) lies within ±0.1.

For Michigan, S3 is judged only on criterion 3, since the county cases can't carry county fixed effects. For Michigan the chosen specification is the S3 version if S3 passes criterion 3; otherwise the S2 or S1 version, whichever the county cases select.

**Choice.** Of the specifications that pass, the simplest (S1 before S2 before S3) becomes the pre-registered secondary version of Test A. If none passes, the report will say that Test A cannot separate appeal to Trump-swing voters from general place differences. The 2026 El-Sayed − Benson result will then be reported descriptively, without a claim about swing-voter appeal.

Pennsylvania 2022 (Fetterman − Shapiro) is reported under every specification but plays no part in the choice, since Addendum 2 made no directional prediction for it.

## Reporting in November

For the 2026 result, the report gives, in this order:

1. Test A's primary result, S0, judged as the original plan specifies.
2. The chosen specification's target-swing coefficient, judged against the ordinary-difference band from Addenda 1 and 2 (about −0.09 to +0.04).
3. A plain statement of what the validation showed: the method's sensitivity (it detects known populist appeal), its specificity problem, and whether the chosen specification resolves it.

## Data

- **ACS 2016–2020 five-year estimates:** Michigan county subdivisions, and Ohio, Wisconsin and Pennsylvania counties, via the Census API (tables B01003, B15003, B19013 and B03002).
- **Michigan cities and townships** are matched to Census county subdivisions by county and name, using `michigan_pull.py`'s normalization, with unmatched places reported.
- Everything else is on disk from Addendum 2.

## Limits

These specifications are chosen on three positive-control cases and three ordinary pairs, a small basis. Controlling for place characteristics can also absorb some genuine swing-voter appeal, when the swing is itself concentrated in places with those characteristics. So a specification that passes may understate a real effect. That is the price of specificity, and the report will say so.
