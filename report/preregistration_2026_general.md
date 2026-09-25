# Pre-analysis plan: three tests on the 3 November 2026 general election

*Written and committed 24 September 2026, forty days before the election and before any 2026 general-election result exists. Nothing in this plan may be changed after results are available; any analysis not specified here will be reported as exploratory. The commit history of this file is the record of what was fixed when.*

## Why these tests

Every result in this report about economic-left candidates comes from primaries or from New York's 2025 mayoral race: electorates in which most of the voters Democrats lost in 2024 do not take part. Part 10 found New York's progressive coalition durable but not expanding; Part 11 found the democratic-socialist tier outrunning its money but not by more in 2026; the enforcement test (Part 10) found the 2025 swing-back in immigrant towns was mostly Trump's occasional voters sitting out an off-year race. The November midterm puts left nominees in front of general-election voters, and brings the occasional voters back to a federal ballot. The three tests below are the ones those findings leave open.

The general rule for all three: the comparison is made **within the same ballot** wherever possible, so that turnout, the national environment and local conditions are held fixed and only the candidate differs; units are places, so the results are ecological; and "the 2024 swing" means the change in Trump's two-party share from 2020 to 2024 in that place, in points.

---

## Test A — Michigan: does an economic-left nominee win back the places that swung to Trump?

**Candidates on the same ballot.** U.S. Senate: Abdul El-Sayed (D) v Mike Rogers (R). Governor: Jocelyn Benson (D) v John James (R) — a two-candidate race after Mike Duggan's withdrawal. Attorney general: Eli Savit (D) v Doug Lloyd (R). Secretary of state: Garlin Gilchrist (D) v Anthony Forlini (R).

**Unit.** Michigan municipality (city or township), from the Secretary of State's official results by jurisdiction; the 2020 and 2024 presidential results by the same jurisdictions. Municipalities with fewer than 200 votes in the 2026 Senate race are excluded.

**Measure.** For each municipality, El-Sayed's two-party share minus Benson's two-party share (points): the *El-Sayed gap*. Two-party means D / (D + R), so minor candidates do not move it.

**Primary test.** WLS of the El-Sayed gap on the 2024 swing, weighted by 2026 Senate votes, HC1 errors.
- A positive slope (p < 0.05): El-Sayed ran further ahead of the Democratic ticket, or less far behind it, where voters had swung to Trump — **evidence that the economic-left candidate reached the defectors better than a mainstream Democrat on the same ballot.**
- A negative slope (p < 0.05): he ran worst where they had swung — **evidence that the left positioning cost votes among exactly those voters.**
- Neither: **no differential appeal** to the places that swung; any level difference is uniform.

**Secondary tests (reported whatever they show).**
1. The same model with Savit and Gilchrist in place of Benson, to check the comparison does not hinge on one candidate.
2. The mean El-Sayed gap statewide (a level difference, not a test of swing voters).
3. The same model adding the municipality's share of residents of Arab ancestry (ACS B04006) and, separately, excluding Dearborn, Dearborn Heights and Hamtramck, where the 2024 Gaza protest vote was concentrated; this separates an Arab-American effect from a swing-voter effect.
4. The same model adding the ACS 18–34 share, to see whether the gradient runs through age.

**Known limits.** El-Sayed and Benson differ in more than ideology (office, name recognition, religion, spending — Part 11 documents $20M of outside money against him in the primary); the test can say whether the left nominee did better or worse *where* the swing was, not *why*.

---

## Test B — New York City: do the new left nominees lose ground where voters swung?

**Races.** The three districts where a left nominee replaced the 2024 Democratic nominee — NY-7 (Nydia Velázquez → Claire Valdez, DSA; open seat), NY-10 (Dan Goldman → Brad Lander), NY-13 (Adriano Espaillat → Darializa Avila Chevalier, DSA) — and, as controls, the two where the 2024 nominee was renominated: NY-6 (Grace Meng) and NY-15 (Ritchie Torres). NY-7 isolates the loss of an incumbent with only a modest ideological change; NY-10 and NY-13 combine both.

**Unit.** Election district, NYC Board of Elections ED-level results for the 2026 House and governor races and the 2024 House and presidential races, parsed with `nyc_pull.read_boe_edlevel`. Each candidate's votes are summed across all ballot lines (Democratic, Working Families). EDs whose lines changed between the November 2025 and February 2026 enrolment snapshots (`lines_changed`) are excluded, as in the replication; EDs with fewer than 50 House votes in either year are excluded.

**Measure.** The *House gap*: the House Democrat's two-party share minus the top-of-ticket Democrat's two-party share in the same ED — Hochul (governor) in 2026, Harris in 2024. The outcome is its change, gap(2026) − gap(2024).

**Primary test.** WLS of the change in the House gap on the 2024 swing, with a district fixed effect and the interaction swing × treated (NY-7, NY-10, NY-13 = 1; NY-6, NY-15 = 0), weighted by 2026 House votes, errors clustered by district-part (county × congressional district).
- Interaction < 0 (p < 0.05): the new left nominees lost ground against the top of the ticket specifically where voters had swung to Trump — **a left penalty among defectors.**
- Interaction > 0: they gained there — **a left advantage among defectors.**
- Neither: **no swing-specific effect.**

**Secondary.** The treated-minus-control difference in the mean change in the House gap (a level effect, which includes the loss of incumbency); NY-7 alone, as the incumbency-without-much-ideology case.

**Known limits.** Five districts, deep-blue seats with weak Republican nominees, and low-information House races in which many voters follow the party line; the design detects differences in how much voters split their ticket, which may be small.

---

## Test C — Do Trump's occasional voters come back, and to whom?

The enforcement test found that in New Jersey's most immigrant towns, Republicans kept only 55–57% of Trump's vote in both the 2021 and 2025 governor's races: an ordinary off-year absence of Trump's occasional voters, not an enforcement backlash. November is the first federal race since. If those voters return and vote Republican, the 2025 swing-back was turnout; if they return and vote Democratic, or stay home more than in the last midterm, there was a change of mind after all.

**Unit.** New Jersey municipality (as in `same_day_2025_pull.py`), with the ACS non-citizen share (`acs_immigration_pull.py`). Virginia localities as the second state.

**Measures.** Republican retention: the Republican U.S. Senate vote in 2026 (Justin Murphy against Cory Booker in New Jersey; Bert Mizusawa against Mark Warner in Virginia) as a share of Trump's 2024 vote. Baseline: the 2022 midterm — the total Republican U.S. House vote in each municipality as a share of Trump's 2020 vote, using only municipalities in districts with both a Democratic and a Republican House candidate in 2022. Democratic retention defined the same way.

**Primary test.** Difference in differences, municipality fixed effects, clustered by municipality: Republican retention on non-citizen share × 2026 (against 2022), controlling for Hispanic share × 2026 and the 2024 swing.
- Coefficient < 0 (p < 0.05): Republicans held Trump's voters worse in immigrant towns in 2026 than in the last midterm — **consistent with an enforcement backlash among Trump's own 2024 voters.**
- Coefficient ≈ 0: the midterm pattern is the ordinary one — **the 2025 result was turnout, and the voters are still Trump's.**
- Coefficient > 0: immigrant-town Republicans held better than in 2022 — **the 2024 realignment persisted.**

**Known limits.** The 2022 baseline uses House races (Senate in 2026) and a different national environment; non-citizen share proxies exposure to enforcement, it does not measure it.

---

## Reporting rules

- Every test above is reported, whatever the result, in the order given.
- Coefficients, standard errors and p-values are reported; "significant" means p < 0.05, two-sided.
- Data problems discovered after results are available (a municipality renamed, an ED file malformed) may be fixed; each fix is listed with its effect on the primary estimate.
- Official, certified results are used. Michigan and New Jersey certify in late November; New York City's ED-level results are expected in December. Analyses will be added to notebooks 17 (Tests B and C) and a new Michigan section, with results written into Parts 10 and 11 and this file left unchanged.
