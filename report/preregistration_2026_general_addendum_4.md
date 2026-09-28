# Addendum 4 to the pre-analysis plan: El-Sayed's position on Israel and Gaza

*Written 28 September 2026, before the 3 November 2026 election, before any 2026 result exists, and before the survey check below has been run. It changes no test in the original plan or in Addenda 1–3. It adds one non-economic force to Addendum 2's list, and fixes in advance a survey check on whether that force could bias Test A. The commit history of this file is the record of when it was written.*

## Why

Test A reads the El-Sayed − Benson slope as a test of an **economic-left** candidate's appeal to Trump-swing voters. But El-Sayed differs from Benson on more than economics. He has also been an outspoken critic of Israel's war in Gaza, and views on that question do not follow party lines neatly:

- skepticism of U.S. support for Israel has grown on parts of the right, especially among younger and more populist Republicans;
- Arab-American and Muslim voters are concentrated in a few Michigan cities;
- strongly pro-Israel voters, including many evangelical Protestants, live in places that also swung right.

If views on Israel line up with the 2020→24 swing across places, a Test A slope could reflect El-Sayed's Gaza position as well as, or instead of, his economic positions.

## Addition to Addendum 2's forecast table (V5)

| Force | Expected effect on the El-Sayed − Benson slope |
|---|---|
| El-Sayed's criticism of Israel's war in Gaza | **Direction not predicted.** Positive if Israel skepticism is more common among voters in Trump-swing places; negative if pro-Israel views are. The concentrated Arab-American vote is handled by Test A's pre-registered exclusion of Dearborn, Dearborn Heights and Hamtramck. The survey check below estimates the rest. |

When Test A is reported, every conclusion about El-Sayed describes him as **economic-left and critical of Israel's war in Gaza**, and does not credit a slope to his economic positions alone.

## The survey check

**Measures.**
- **CES 2024** (common content, about 60,000 respondents, with county identifiers). From the question on what the U.S. should do about the war between Israel and Hamas (`CC24_308b`, tick all that apply): *supports providing arms to Israel* (that option ticked). Secondary: *do not get involved* ticked.
- **ANES 2024.** From "In the Middle East conflict, do you side more with the Israelis, the Palestinians, both equally, or neither?" (`V241407`): *sides with the Israelis*.

**Place-level question (primary): does support for arming Israel vary with the 2020→24 swing?** In the CES, regress *supports arms to Israel* on the respondent's county 2020→24 swing to Trump, using the MIT county file and the CES weight, with errors clustered by county. There are three models:

1. all respondents;
2. adding party identification, so the question becomes whether people of the same party differ by place;
3. restricted to Michigan respondents, as a descriptive check with low power.

The same models are run for *do not get involved*.

**Individual-level question (secondary): did the voters who swung hold different views?** Shares by 2020 → 2024 path (loyal Democrats, Biden → Trump, new voters for Trump, loyal Republicans):
- in the CES, for *supports arms to Israel*, using recalled 2020 vote (so switcher shares carry the recall caveat from Part 8);
- in the ANES, for *sides with the Israelis*.

**How it will be read.** Here "the swing" means the county's 2020→24 swing to Trump, scaled per 10 points.

- **No association.** If, in model 2, support for arming Israel changes by less than 3 points per 10 points of county swing, with an interval inside ±5, Israel views are unlikely to drive a Test A slope through the swing towns. The report says so.
- **Less support in swing places.** If the association is clearly negative in model 2 (interval excluding zero), a positive El-Sayed slope may partly reflect his Gaza position. The report states that as an alternative explanation.
- **More support in swing places.** If it is clearly positive, his Gaza position would push the slope down. A positive El-Sayed slope would then be despite that position, and a negative one could partly reflect it.

## Limits

Survey views on Israel in 2024 are an imperfect stand-in for how El-Sayed's position registered with voters in 2026. County is coarser than Test A's municipalities. The check can say whether views on Israel line up with the swing across places, not whether they moved any 2026 vote.
