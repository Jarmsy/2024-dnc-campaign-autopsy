# Analysis plan for the 3 November 2026 results

*Written on 4 November 2026, the day after the election, and committed before any 2026 result below state level was downloaded for this project.*

*This is not a pre-registration: statewide and district results were already public when it was written (listed below). It changes nothing in [`preregistration_2026_general.md`](preregistration_2026_general.md), its Addenda 1–4 or the [validation results](preregistration_2026_general_validation_results.md), and Tests A–C run exactly as written there. This file adds three things:*

- *the questions each analysis is meant to answer;*
- *the order of the work as official data arrives;*
- *seven exploratory analyses, specified before their data is pulled.*

*The commit history of this file is the record of when it was written.*

## The questions

The report asks why Democrats lost the voters they lost in 2024, and whether running on economics, including from the left, can win them back. Its evidence on the left so far comes from primaries and from New York's 2025 mayoral race, electorates in which most of the voters Democrats lost don't vote. The 2026 general election puts this cycle's left nominees in front of general-election voters, with Trump's occasional voters back on a federal ballot.

**Pre-registered (Tests A–C):**

1. **Michigan (Test A).** Where towns swung hardest to Trump in 2024, did El-Sayed, the economic-left Senate nominee, gain or lose ground against Benson, a mainstream Democrat on the same ballot?
   - The test can show where he did better or worse, not why.
   - E5–E7 add context: how much the campaigns differed in money and coverage, and how far other Democrats on the same ballot diverged along the swing. They don't change how Test A is judged.
2. **New York City (Test B).** Did the three new left House nominees (Valdez, Lander and Avila Chevalier) fall further behind the top of the ticket than their 2024 predecessors did, specifically in the neighborhoods that swung to Trump? Meng's and Torres's districts are the controls.
3. **New Jersey and Virginia (Test C).** Were the 2025 Democratic gains in immigrant towns just Trump's occasional voters skipping an off-year race? When those voters faced a federal ballot again, did Republicans hold them as well as in the last midterm?

**From Part 11:**

4. **CA-14.** Does the super PAC targets' 2026 record stay at 6 of 10, or fall to 5 of 10?
5. **The money.** Part 11 calls the weakening of the money "a signal to watch in November and 2028 rather than a finding". Did the outside money that lost most 2026 primaries (AIPAC's United Democracy Project and the crypto industry's Fairshake network) also lose in November? Where did it go?

**Exploratory (E1–E7 below):**

6. **E1.** Nationally, did left House nominees run behind or ahead of other Democrats, measured against Harris's 2024 vote in their own districts?
7. **E2.** Did New York's 2025 recovery in the neighborhoods that swung to Trump hold on a federal midterm ballot?
8. **E3.** In the swing states, did Republicans keep less of Trump's 2024 vote than Democrats kept of Harris's, compared with the last midterm? Was the difference largest where the 2024 swing had been largest?
   - County totals can't say whether that came from voters staying home or from voters switching. Part 2 notes that separating the two needs individual-level data (question 11).
9. **E4.** Was 2026 an ordinary referendum on the president's approval?

**When the 2026 surveys are released (2027):**

10. With a Republican president, do ratings of the economy flip by party, as Part 4's finding predicts?
11. Did 2024's switchers vote Democratic in 2026, and how do the ones who came back differ from the ones who didn't?

**What none of this answers:** why individual voters chose as they did. The place-level results are ecological. The money analyses are descriptive and cannot show that spending changed an outcome.

## What was known when this was written

**Unofficial results as of about 2 pm ET on 4 November 2026** (AP data via NBC News unless noted):

- **Control:** Democrats won control of the House ([AP][house]) and the Senate ([AP][senate]).
- **Michigan:**

  | Race | Democrat | Republican |
  |---|---|---|
  | U.S. Senate ([NBC][mi-sen]) | El-Sayed 52.5% | Rogers 45.5% |
  | Governor ([NBC][mi-gov]) | Benson 54.5% | James 43.8% |
  | Attorney general ([NBC][mi-ag]) | Savit 52.5% | Lloyd 44.7% |
  | Secretary of state ([NBC][mi-sos-race]) | Gilchrist 53.7% | Forlini 43.6% |

  In two-party terms, El-Sayed ran about 2 points behind Benson statewide. Test A asks how that gap varies with the 2024 swing.
- **New York City** (Board of Elections, unofficial, as of about 00:41 ET on 4 November):

  | Race | Democrat | Share |
  |---|---|---|
  | NY-6 ([BOE][ny6]) | Meng | 68.6% |
  | NY-7 ([BOE][ny7]) | Valdez | 83.3% |
  | NY-10 ([BOE][ny10]) | Lander | 83.2% |
  | NY-13 ([BOE][ny13]) | Avila Chevalier | 87.5% |
  | NY-15 ([BOE][ny15]) | Torres | 76.8% |
  | Governor, within the city ([BOE][nycgov]) | Hochul | 76.1% |
- **New Jersey and Virginia:** in the U.S. Senate races, Booker won 62.1% to Murphy's 35.3% ([NBC][nj-sen]), and Warner 61.1% to Mizusawa's 38.7% ([NBC][va-sen]).
- **CA-14:** uncalled. Wahab led Hernandez 56.5% to 43.5%, with 52.5% of the expected vote counted ([NBC][ca14]).
- **Turnout:** 49.4% of the voting-eligible population, preliminary ([McDonald][turnout]).

**What the project had seen and downloaded.** To find out what data exists, it looked at the layout of unofficial county results sites in Michigan and of the New York City Board of Elections' election-district pages. It downloaded no file below state level and has analyzed no town-, district- or county-level 2026 figure. The newest *modification* time of any file in `data/raw/` is 28 September 2026. The folder was copied into this clone on 2 November, so file *creation* times show that date.

## Rules

1. **Tests A–C are run exactly as written, on certified files.**
   - Data problems may be fixed only as the plan's reporting rules allow, each listed with its effect on the primary estimate.
   - The tests run as each state's certified files arrive, but are reported in the pre-registered order, A, B, C, whatever they show.
   - The pre-registration files are not edited.
   - The work goes where the plan says: notebook 17 (Tests B and C) and a new Michigan notebook, `31_michigan_testA_2026.ipynb` (Test A). The results go into Parts 10 and 11.
2. **Official sub-state data only.** Nothing unofficial below state level is downloaded.
3. **Exploratory analyses are kept apart from the tests.**
   - They live in `32_results_2026_exploratory.ipynb`.
   - Each is labelled exploratory wherever it appears.
   - Each is reported descriptively, with no claim of statistical significance.

## When the official data arrives

| Data | On 4 November | Official version | For |
|---|---|---|---|
| Michigan, by city and township | Unofficial, on county sites only ([SoS][mi-sos]) | Counties certify by 17 Nov ([MCL 168.822][mi-mcl]); the Board of State Canvassers by 23 Nov ([Brennan Center][mi-bsc]). In 2024 the Secretary of State posted certified results on certification day ([SoS][mi-2024]). | Test A, E5 |
| New York City, by election district (ED) | Unofficial ED web pages, no downloads ([example][ny10-ed]) | Certified ED-level CSV on vote.nyc. 2025's certification is dated 2 Dec 2025 ([recap][nyc-2025]). The statutory deadlines are 28 Nov ([§9-214][ny-9214]) and 15 Dec ([§9-216][ny-9216]). | Test B, E2 |
| New Jersey, by municipality | Unofficial, in some counties | Counties certify 18 Nov; the state by 3 Dec ([calendar][nj-chron]). The 2024 official municipal PDFs were created on 17 Dec ([example][nj-2024]). | Test C |
| Virginia, by locality | Unofficial | Local electoral boards certify provisional ballots by 13 Nov. The State Board certifies results on 7 Dec ([ELECT][va-cert]). | Test C |
| CA-14 | Uncalled ([NBC][ca14]) | Counties certify 3 Dec; the Secretary of State 11 Dec ([SoS][ca-dates]) | Part 11 |
| FEC | 24-hour independent-expenditure reports through 1 Nov ([FEC][fec-24h]) | Post-General report, covering 15 Oct–23 Nov, due 3 Dec from every PAC ([FEC][fec-post]); Year-End due 31 Jan 2027 ([FEC][fec-monthly]) | Part 11, E6 |
| Exit polls | AP VoteCast "was conducted from 2017-2024" ([AP-NORC][votecast]). The networks' 2026 Voter Poll by SSRS has 81,290 national interviews and asks 2024 vote ([SSRS][ssrs]). The networks publish results by group ([NBC][nbc-exit]). | No respondent-level release announced | Context only |
| CES 2026 | Fielded October–November ([CES][ces]) | Spring 2027 is likely: the 2022 Common Content went public on 20 Mar 2023 ([Dataverse][ces-2022]). A 2026 re-interview of the 2020–22–24 panel was not found. | Parts 4–9 |
| Pew validated voters; ANES 2026 pilot | — | Pew's 2022 study appeared on 12 Jul 2023 ([Pew][pew-2022]). The ANES pilot ([ANES][anes-pilot]) has no release date. | Parts 5, 7, 8 |
| Precinct files nationally | — | MEDSL's 2022 state files arrived from Dec 2022 to Jun 2023 ([MEDSL][medsl-2022]) | E3, national |

**Money already on file.**

- **United Democracy Project ([UDP][udp]), AIPAC's super PAC.** Its 24-hour report of 30 October puts its direct general-election spending in the Michigan Senate race at $827,926 to that date ([report][udp-24h]). Its 29 October report shows $64,393 of that for Rogers ([report][udp-24h-a]). The remaining $763,533 matches the total of its itemized expenditures against El-Sayed from 7 to 29 October, in its 24-hour reports ([filings][udp]).
- **The reported $9 million.** The New York Times reported up to $9 million from UDP to the Great Lakes Conservatives Fund (GLCF, [C00853861][glcf]), sent after the 14 October cutoff ([Newsweek][nyt-9m]). The transfer appears in no filing yet. It should appear in both committees' Post-General reports, or in both committees' Year-End reports if it moved after 23 November.
- **GLCF.** Its 24-hour report of 30 October puts its independent expenditures in the Senate race at $25.6 million to that date ([report][glcf-24h]). It reports $10.14 million received from "Conservative Americans PAC" (C00820308), $8.0 million of it on 7 October ([pre-general report][glcf-pg]). The FEC lists that committee as terminated ([FEC][cap]).

## Order of work

**Phase 1, now to mid-November (no 2026 data below state level):**

1. **Commit this file.** On the same day, save Justice Democrats' and national DSA's 2026 endorsement lists, for E1, to `data/coded/`, which is tracked in git.
2. **Pull the pre-2026 inputs the tests still lack.**
   - **Test B:** the 2024 House results by ED, from vote.nyc on the URL pattern in `nyc_pull.FILES`, read with `nyc_pull.read_boe_edlevel`. They are matched to 2026 EDs by ED number, excluding the `lines_changed` EDs, as `nyc_2026_primary_pull.py` does for the June primaries.
   - **Test C:** the 2022 House baseline.
     - Virginia by locality, from the elstats contest CSVs (`same_day_2025_pull.pull_va`).
     - New Jersey by municipality. Its 2022 House results come as one PDF per district (`…/2022/2022-general-election-results-hor-NN.pdf`), not the county files `_parse_nj` reads. So a reader is added that keeps `_parse_nj`'s checks: party columns read from each header, and municipalities reconciled to each printed county total.
     - Municipalities split between districts are summed across the district files.
     - Both keep only districts with a Democratic and a Republican candidate.
   - **Test A:** the inputs for secondary tests 3 and 4.
     - Arab ancestry (ACS B04006), which no file or notebook in the project has yet.
     - The 18–34 share (ACS B01001, with the age bands in `nyc_pull._AGE_BANDS`).
     - Both are added to `acs_place_controls_pull.py`. The Bay City, Garden City and Traverse City matches are fixed, as the validation results promised before the 2026 run.
   - **E4:** the national House vote in each midterm from 1950 to 2022, and the mean June Gallup approval from the American Presidency Project's tables, the source notebook 02 now uses. FRED's GDP series begins in 1947, so 1946 has no second-quarter growth.
   - **E6:** news coverage from GDELT. `gdelt_insurgent_pull.py` pulls all English-language sources and then, for candidates with at least 10 days of coverage, four national outlets, in 90-day windows ending on each primary. It is adapted to the 90 days of the general-election campaign, 5 August to 3 November 2026, with five Michigan outlets added: freep.com, detroitnews.com, mlive.com, bridgemi.com and michiganadvance.com. The SSRS statement lists the network as "MSNOW", so msnbc.com's coverage is checked before the pull.
3. **Prepare the 2026 readers without downloading 2026 files.**
   - `michigan_pull.py`: the 2026 offices and the certified-totals check.
   - `nyc_pull.py`: the 2026 House and governor files. Each candidate is summed across ballot lines. In NY-15 the Republican and Conservative lines carry different candidates. The Board of Elections' pages are headed "SPECIAL".
   - `same_day_2025_pull.py`: the New Jersey 2026 Senate files and the Virginia 2026 Senate contest.
4. **CA-14.** When AP calls the race, or at certification on 11 December, update Part 11's record.
   - **If Wahab wins:** it stays 6 of 10, and 4 of 7 among progressives.
   - **If Hernandez wins:** it becomes 5 of 10 and 3 of 7, and notebook 19's money-model residuals are refit.

**Phase 2, as each state certifies:**

5. **Test A** (after 23 November), in notebook 31. It follows the plan, Addenda 1–4, the validation results and appendix K-ter:
   - S0;
   - S1 and the Michigan S3 version, against the −0.09 to +0.04 band, with Brown's +0.14 as the scale for a meaningful effect (that scale is set in K-ter, not in the pre-registration files);
   - a null S3 result read alongside S1, and reported as weak evidence of no effect if S1 shows one (validation results);
   - the Dearborn exclusion and the media-market check (V4);
   - the original plan's secondary tests 1–4;
   - a plain statement of what the validation showed (Addendum 3);
   - the alternative readings named in advance (Addendum 2's table V5 and Addendum 4), stated beside the result.

   El-Sayed is described as economic-left and critical of Israel's war in Gaza (Addendum 4). E5–E7 are reported beside Test A and labelled exploratory. E6's spending figures wait for the 3 December reports.
6. **Test C** (Virginia after 7 December; New Jersey when the municipal PDFs post), in notebook 17.
7. **Test B** (when New York City's certified ED files post), in notebook 17.
8. **The money** (after 3 December). Rerun `superpac_ie_pull.py` and `popup_donors_pull.py` for the general election, covering:
   - UDP;
   - the transfer to GLCF, and GLCF's own funders;
   - Fairshake's network.
9. **E1–E3 and E5–E7** on the certified data, in notebook 32.
10. **Write-up.** The results go into:
    - Parts 10–11;
    - appendix K-ter;
    - the "What comes next" point in the synthesis's "What it adds up to";
    - the executive summary;
    - the website's section 8.

    Each piece is checked by a fresh reviewer, given only the diff and the sources, before it is called done.

**Phase 3, 2027:**

11. **CES 2026:**
    - Part 4's partisan reversal;
    - the 2024 switchers' 2026 House vote and views, with Part 8's recall caveat;
    - Part 7's stronghold turnout.
12. **Pew's validated voters, and MEDSL's precinct files.** They give individual-level and national versions of E3.
13. **E4**, once the national House vote is final.

## Exploratory analyses

None of these is a test.

**E1. Left House nominees against Harris's 2024 vote (Part 11).**

- **The set:** every 2026 Democratic House nominee on the Justice Democrats or national DSA endorsement list saved in step 1. Statewide nominees are left out; El-Sayed's race is Test A.
- **The measure:** the nominee's two-party share minus Harris's 2024 two-party share in the same district, on 2026 lines. It is compared with the same number for every other Democratic House nominee in that state who faced a Republican.
- **Exclusions:** uncontested races are left out. Democrat-against-Democrat races (CA-7, CA-14, CA-34) are listed separately.

**E2. New York City on a federal midterm ballot (Part 10).**

- **The measure:** by ED, Hochul's 2026 two-party share minus Harris's 2024 two-party share. It is set beside Part 10's 2025 measures: Mamdani − Harris, Levine − Harris and Williams − Harris.
- **The breakdown:** by 2024-swing decile and by majority group, as in Part 10's tables, with turnout set against 2024 and 2025.

**E3. Who kept their 2024 vote? (Parts 2, 3 and 7).**

- **Where:** county by county in the seven swing states of Part 7's tables (Arizona, Georgia, Michigan, Nevada, North Carolina, Pennsylvania and Wisconsin), using the U.S. Senate race where the state has one in 2026, and otherwise the governor's race.
- **The measures:**
  - Republican retention is the Republican 2026 vote ÷ Trump's 2024 vote.
  - Democratic retention is the Democratic 2026 vote ÷ Harris's 2024 vote.
  - The baselines are the 2022 vote ÷ the 2020 presidential vote, built the same way.
- **The estimate:** the change in each, set against the county's 2024 swing. It uses WLS weighted by 2024 votes. State fixed effects are included, as in the report's state-fixed-effect refit of its county model (appendix D.3a). A second model adds Part 3's county covariates.
- **Limit:** county ratios can't separate staying home from switching.

**E4. A midterm fundamentals check (Part 1).**

- **The model:** the president's party's two-party House vote in each midterm from 1950 to 2022, on mean June Gallup approval and second-quarter GDP growth, tested leave-one-out.
- **The comparison:** its 2026 prediction against the national House vote, once the count is final.

**E5. Other pairs on the same 2026 ballot (Test A).**

- **The pairs:** Test A's specifications (S0, S1 and the Michigan S3 version) run on Gilchrist − Benson, Savit − Benson and Savit − Gilchrist. They use Test A's towns and weights (2026 Senate votes). This shows how far other Democrats on the 2026 ballot diverged along the swing in the same year.
- **How it relates to the tests:** with the same towns and weights, these slopes are exact differences of Test A's. For example, Savit − Benson = (El-Sayed − Benson) − (El-Sayed − Savit). At S0, where secondary test 1 is pre-registered, E5 therefore adds only intervals; at S1 and S3 its slopes are new.
- **Use:** context only. It doesn't change how Test A is judged (the pre-registered band stands), and it offers no reading of why.

**E6. The size of the disparity (Test A).**

- **Spending:** for and against each candidate, from filings through 3 December. El-Sayed and Rogers from the FEC, as committee totals and independent expenditures. Benson and James from Michigan's campaign-finance filings for the governor's race.
- **Coverage:** news volume and tone for El-Sayed and Benson, from GDELT, as set out in step 2.
- **Use:** descriptive only. Neither series varies by town, so neither enters Test A's regressions. They show how large a gap the same-ballot design is working around.

**E7. Ad spending by television market (Test A).**

- **The data:** if obtainable, ad spending by Michigan media market for and against El-Sayed and Benson, from AdImpact or from the Wesleyan Media Project once it releases 2026 data.
- **Use:** only to read the V4 check, by showing whether the spending against El-Sayed was concentrated in particular markets. If no data can be obtained, the report says so.

## Verification

- **Reconciliation:** every 2026 file is checked against its certified totals:
  - Michigan: the statewide check in `michigan_pull.main()`;
  - New Jersey: each county's printed total;
  - Virginia: the State Board totals;
  - New York City: the citywide and district totals.
- **Pre-registration untouched:** `git log` shows no change to `report/preregistration_2026_general*.md` after the pre-election commits.
- **Timing:** every download of 2026 data below state level comes after this file's commit. Both times are reported in appendix K-ter.
- **Notebooks:** 17, 19, 31 and 32 run clean with the `dnc-autopsy` kernel.

[house]: https://www.pbs.org/newshour/politics/democrats-win-control-of-the-u-s-house
[senate]: https://www.pbs.org/newshour/politics/democrats-take-control-of-the-senate-after-winning-key-midterm-races
[mi-sen]: https://www.nbcnews.com/politics/2026-elections/michigan-senate-results
[mi-gov]: https://www.nbcnews.com/politics/2026-elections/michigan-governor-results
[mi-ag]: https://www.nbcnews.com/politics/2026-elections/michigan-attorney-general-results
[mi-sos-race]: https://www.nbcnews.com/politics/2026-elections/michigan-secretary-of-state-results
[ny6]: https://enr.boenyc.gov/CD273180.html
[ny7]: https://enr.boenyc.gov/CD273200.html
[ny10]: https://enr.boenyc.gov/CD273220.html
[ny10-ed]: https://enr.boenyc.gov/CD27322AD443.html
[ny13]: https://enr.boenyc.gov/CD273230.html
[ny15]: https://enr.boenyc.gov/CD273240.html
[nycgov]: https://enr.boenyc.gov/OF4CY0PY3.html
[nj-sen]: https://www.nbcnews.com/politics/2026-elections/new-jersey-senate-results
[va-sen]: https://www.nbcnews.com/politics/2026-elections/virginia-senate-results
[ca14]: https://www.nbcnews.com/politics/2026-elections/california-us-house-district-14-results
[turnout]: https://michaelmcdonald.substack.com/p/preliminary-2026-turnout-rate
[mi-sos]: https://www.michigan.gov/sos/elections/election-results-and-data
[mi-mcl]: https://legislature.mi.gov/Laws/MCL?objectName=MCL-168-822
[mi-bsc]: https://www.brennancenter.org/our-work/research-reports/michigan-election-certification-processes-and-guardrails
[mi-2024]: https://content.govdelivery.com/accounts/MISOS/bulletins/3c33b14
[nyc-2025]: https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/00000100000Citywide%20Mayor%20Citywide%20Recap.pdf
[ny-9214]: https://www.nysenate.gov/legislation/laws/ELN/9-214
[ny-9216]: https://www.nysenate.gov/legislation/laws/ELN/9-216
[nj-chron]: https://www.nj.gov/state/elections/assets/pdf/chrons/2026-chron-general-election-0109.pdf
[nj-2024]: https://www.nj.gov/state/elections/assets/pdf/election-results/2024/2024-official-general-results-us-senate-atlantic.pdf
[va-cert]: https://www.elections.virginia.gov/news-releases/early-voting-for-2026-november-general-election-begins-sept-18-2.html
[ca-dates]: https://www.sos.ca.gov/elections/upcoming-elections/general-election-november-3-2026/key-dates-deadlines
[fec-24h]: https://www.fec.gov/help-candidates-and-committees/dates-and-deadlines/2026-reporting-dates/24-and-48-hour-reports-independent-expenditures-periods-general-election-2026/
[fec-post]: https://www.fec.gov/help-candidates-and-committees/dates-and-deadlines/2026-reporting-dates/pre-and-post-general-reports-2026/
[fec-monthly]: https://www.fec.gov/help-candidates-and-committees/dates-and-deadlines/2026-reporting-dates/2026-monthly-filers/
[votecast]: https://apnorc.org/projects/ap-votecast-puf/
[ssrs]: https://ssrs.com/wp-content/uploads/2026-Voter-Poll-Methods-Statement-Nov-3-12AM.pdf
[nbc-exit]: https://www.nbcnews.com/politics/2026-elections/exit-polls
[ces]: https://tischcollege.tufts.edu/research-faculty/research-centers/cooperative-election-study/about-methodology
[ces-2022]: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PR4L8P
[pew-2022]: https://www.pewresearch.org/politics/2023/07/12/republican-gains-in-2022-midterms-driven-mostly-by-turnout-advantage/
[anes-pilot]: https://electionstudies.org/anes-announcement-call-for-proposals-for-the-anes-2026-pilot-study/
[medsl-2022]: https://github.com/MEDSL/2022-elections-official
[udp]: https://www.fec.gov/data/committee/C00799031/
[udp-24h]: https://docquery.fec.gov/dcdev/posted/2044441.fec
[udp-24h-a]: https://docquery.fec.gov/dcdev/posted/2043087.fec
[nyt-9m]: https://www.newsweek.com/aipac-dumps-last-minute-9m-behind-mike-rogers-in-rebuke-of-abdul-el-sayed-12607752
[glcf]: https://www.fec.gov/data/committee/C00853861/
[glcf-24h]: https://docquery.fec.gov/dcdev/posted/2044727.fec
[glcf-pg]: https://docquery.fec.gov/dcdev/posted/2039321.fec
[cap]: https://www.fec.gov/data/committee/C00820308/
