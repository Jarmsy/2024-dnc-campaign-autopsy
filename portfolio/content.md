---
title: "Why Democrats Lost the Voters They Lost"
subtitle: "An autopsy of the 2024 election from public data: what the swing voters believed, when they broke, and what I'm testing next"
date: 2026-09-27
tags: [data analysis, survey research, panel data, elections, Python]
repo: https://github.com/Jarmsy/2024-dnc-campaign-autopsy
---

> **Status (27 Sept 2026):** the live page text lives in the website repo (`/made/2024-election-autopsy/`) and has been rewritten in John's voice. `content.md` here is the original draft and is **not** the source of truth for the page. The numbers are unchanged; `data/*.json` remains the only source of figures. Send any change to a number or caveat to the website session to fit into its current wording.

<!-- Chart slots are marked {{CHART:<id>}}; each id matches a spec in CHARTS.md and a file in data/.
     Every number in this text comes from data/*.json (see CHECKS.txt). Do not edit numbers by hand. -->

## The short version

**Democrats didn't lose the 2024 swing voters because those voters were afraid of left-wing economics. The swing voters largely agreed with Democrats on the economy. By 2022 they had decided the Biden government wasn't delivering, and only after they switched did their views of Trump, immigration and health care follow. It was a credibility problem, not a platform problem.**

I built this from public data: election returns for every county and several thousand municipalities, and the two large academic surveys that follow the *same people* across elections, one from 2016 and one from 2020, both through 2024. Along the way I found and corrected an error in my own headline numbers (see "The bug in my own numbers"), and I wrote down a test of the argument *before* the November 2026 election, so the result can't be fitted after the fact.

**What this project shows about how I work:** turning messy public data from 10+ sources into reconciled, reproducible tables; designing comparisons that separate cause from coincidence; auditing and correcting my own results; and explaining uncertainty plainly.

---

## 1. The loss was the one the conditions predicted

{{CHART:01_fundamentals}}

**The finding.** Presidential elections since 1948 follow a few conditions closely, mainly economic growth and the sitting president's approval. A model built on those past elections, given 2024's conditions (an incumbent party at 38% approval seeking an open seat), predicted Harris would win **47.9%** of the two-party vote. She won **49.25%**, slightly *better* than predicted.

**How I know.** I fit the model on 1948–2020 and predicted each election with that year left out, which shows how far off the model typically is: about 3.75 points. That margin is inflated by one data point, the 2020 pandemic quarter when GDP fell 28%; refitting without it shrinks the margin to 2.66 points. Harris sits inside the margin either way.

**What it doesn't show.** A good forecast of the total doesn't say which voters moved or why. The rest of this page is about that.

## 2. The election was lost on persuasion, not turnout

{{CHART:02_turnout_vs_share}}

**The finding.** Democrats lost votes two ways: people who didn't show up (*turnout*) and people who voted the other way (*share*). In the most Democratic counties the loss was mostly turnout, **2.9 million votes**. But that was overwhelmingly in states that weren't competitive, such as California and New York. In the swing states, Democratic counties held their turnout, and the loss came from voters changing sides.

**How I know.** I split each county's change in Democratic votes into a turnout part and a share part (a standard decomposition), then checked the obvious "what if": if every 2020 voter who stayed home in 2024 had voted as in 2020, would any state flip? Using survey stay-home rates by state, **none does** under the straightforward estimate.

{{CHART:02b_stayhome_counterfactual}}

**What it doesn't show.** It doesn't mean Democratic turnout didn't matter anywhere; it means it didn't decide the swing states.

## 3. People saw the economy through their party, not their paycheck

{{CHART:03_perception_by_party}}

**The finding.** How someone rated the national economy tracked whether their party held the White House, flipping every time power changed hands. How their *own county's* economy actually did explains **0.6%** of the differences in people's ratings; their party explains **34%**.

**How I know.** I linked each survey respondent (about 60,000 a year) to their county's actual job and wage record from federal labor statistics, then compared how much of the variation in economic ratings each explained.

**What it doesn't show.** Party isn't the only filter. Which news sources people consumed also mattered, while how much *local* news was available made no measurable difference.

## 4. The bad rating came first

{{CHART:04_rating_2022_predicts_switch}}

**The finding.** Among the same Biden voters, how they rated the economy in **2022** predicted whether they voted Trump in **2024**. Of those who said the economy had gotten "much worse," **7.9%** switched. Of the 438 who said it had improved, **none** did.

**How I know.** This uses a panel survey, which re-interviews the same people in 2020, 2022 and 2024. A rating given two years before the vote can't be an excuse invented after deciding.

**What it doesn't show.** Something else might already have been pulling these voters away in 2022, making them rate the economy badly *and* later switch. Section 6 looks at exactly that.

## 5. The switchers agreed with Democrats on economics, not on immigration

{{CHART:05_issue_positions}}

**The finding.** Biden voters who switched to Trump looked like Democrats on economic policy: **77%** wanted Medicaid expanded, and majorities wanted corporations and high earners taxed more. On immigration they sat far closer to Republicans: only **23%** opposed the border wall. They weren't anti-business either; the most anti-corporate Democrats were the *most* loyal.

**How I know.** A national survey of about 60,000 people asks the same policy questions of everyone. I grouped voters by their 2020 and 2024 votes and compared the share taking the Democratic position on each issue.

**What it doesn't show.** Holding a view isn't the same as voting on it. And these are 2024 answers, given after the switch, which is why the next section matters most.

## 6. The order of events

{{CHART:06_order_of_events}}

**The finding.** Following the same people from 2020 to 2024 shows the sequence:

1. **By 2022 they had turned on the Democratic government.** Only **31%** of future switchers approved of Biden, and about four in ten had already voted Republican for Congress.
2. **But they still wanted Democratic economics.** In 2022, **87%** of them supported Medicare for All, *more* than in 2020.
3. **Everything else followed the switch.** Between 2022 and 2024 their support for Medicare for All fell to **47%**, their immigration views hardened, and their picture of Trump changed wholesale. In 2020, **2 of 21** said Trump "really cares about people like you"; by 2024, **10 of 20** did.

**How I know.** Two panel surveys (CES 2020–22–24 and ANES 2016–20–24) followed the same individuals, so this is change *within* people, not a comparison of different groups at different times. The sample of switchers is small (39 in one panel, 21 in the other), so the exact percentages are uncertain; hover to see how many people each point rests on. The *order* of events is the robust part.

**What it means.** These voters judged the incumbent's performance first, largely on prices, which they named as the top problem two to one over immigration. Only then did they switch, and their policy views caught up with their new side. What made them the ones to leave, rather than other disappointed Democrats, was cultural distance: their immigration and social views were already more conservative in 2016 and 2020, while they were still voting Democratic.

### The bug in my own numbers

{{CHART:sidebar_recall}}

Most surveys ask people in 2024 how they voted in 2020. When I checked those memories against what the same people said in November 2020, I found a problem. Of **44** people who "remembered" voting Biden and then voted Trump, only **34** had actually reported voting Biden; **9** had reported voting Trump.

The reason is arithmetic. Fewer than 1% of Trump voters misremember voting Biden, but Trump voters are a huge group and genuine switchers a small one, so a tiny error rate inflates the small group. Correcting it lowered my estimate of how many Biden voters switched from **5.2% to 4.1%**, and the ratio of switchers to reverse-switchers from **3.4 to 1** to **2.6 to 1**. The patterns (who switched and why) survived; the sizes shrank. I corrected every affected figure in the report and noted what changed.

## 7. An economic-left campaign hasn't yet won these voters back

{{CHART:07_nyc_same_ballot}}

**The finding.** New York City's 2025 mayoral race was the clearest real-world test of an explicitly economic-left campaign. In the neighborhoods that had swung hardest to Trump, Zohran Mamdani ran ahead of Harris's 2024 share. But the two other Democrats on the same ballot, for comptroller and public advocate, gained **even more** in those same neighborhoods. The swing voters came back to Democrats, not specifically to the economic-left candidate. (Mamdani's share runs lower overall because he also faced Andrew Cuomo, a Democrat running as an independent who won 41% citywide; what matters is how much each candidate gained where voters had swung.)

**How I know.** I compared candidates on the *same ballot* in the same election districts, which holds constant everything about the place and the year and leaves only the candidate. The same pattern held in New Jersey and Virginia the same day.

**What it doesn't show.** One city, one election, neighborhood totals rather than individuals. It shows Mamdani's appeal didn't reach these voters *better* than other Democrats'; it doesn't show left economics hurt.

## 8. What I'm testing next, written down before the votes are counted

{{CHART:08_testA_benchmark}}

**The test.** In November 2026, Michigan votes on an economic-left Senate candidate (Abdul El-Sayed) and a mainstream Democrat for governor (Jocelyn Benson) on the same ballot. If economic-left politics reaches the voters who swung to Trump, El-Sayed should run relatively better, compared with Benson, in the towns that swung most.

**Why it's credible.** I published the exact test before the election, so the result can't be reinterpreted afterwards. I also measured what "normal" looks like. Among three mainstream Democrats on Michigan's 2022 ballot, the gap between any two barely tracks the swing: slopes between **−0.06 and +0.04**. So El-Sayed's result will count as meaningful only if it lands clearly outside that range. Results come after certification in late November 2026.

**What could confuse it.** Forces that hit El-Sayed harder in some towns than others: concentrated attack ads, prejudice against a Muslim candidate, strong Arab-American support in Dearborn. The plan names each one and controls for what it can.

---

## What a campaign could take from this

- **The voters Democrats lost weren't scared off by left economics.** They agreed with it. Economic views were what *held* other voters in the coalition.
- **The failure was belief, not platform.** These voters concluded, by 2022, that the Democratic government wasn't delivering, especially on prices. More ambitious promises don't fix that on their own; being believed on delivery does.
- **Cultural distance decides who leaves when trust breaks.** The switchers' views on immigration and social issues were already in place in 2016 and 2020, while they were still voting Democratic.

## What this can't tell us

- **Why trust broke between 2020 and 2022.** The panels don't observe it directly; prices are the strongest candidate, not a proven cause.
- **Whether a different 2024 campaign would have won.** The data describe voters, not counterfactual campaigns.
- **Exact sizes for small groups.** The panel findings rest on dozens of switchers; the direction and order are solid, the precise percentages are not.

---

**Go deeper:** [full report and technical appendix](https://github.com/Jarmsy/2024-dnc-campaign-autopsy/tree/master/report) · [pre-registered November 2026 test](https://github.com/Jarmsy/2024-dnc-campaign-autopsy/blob/master/report/preregistration_2026_general.md) · [code and notebooks](https://github.com/Jarmsy/2024-dnc-campaign-autopsy)

**Methods and tools:** Python (pandas, statsmodels), survey weighting, panel analysis, bootstrap intervals, decomposition, pre-registration. Data: Cooperative Election Study (cross-section and 2020–24 panel), American National Election Studies (2016–20–24 panel), MIT Election Lab, OpenElections, FRED, BLS, Census ACS, NYC Board of Elections.
