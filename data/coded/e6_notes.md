# Notes on E6 inputs (Michigan Senate: coverage and spending)

E6 is defined in `report/results_2026_analysis_plan.md`. It is descriptive only and does not enter Test A's regressions. These notes record what the Phase 1 pulls could and could not collect, and the interim spending snapshot taken on 5 November 2026 (UTC; 4 November in Chicago). The final spending figures wait for the FEC Post-General reports due 3 December.

## Coverage (GDELT)

**File:** `data/raw/gdelt_general_2026/gdelt_general_2026_daily.csv`, written by `gdelt_general_2026_pull.py` (gitignored). It covers El-Sayed and Benson.

**Missing days are GDELT's outage, not the pull's.**

- Our series has no rows on 22 of the 91 days from 5 August to 3 November 2026: 14–19 September, 26 September, 3–5 October, 7 October, 9 October, 11–14 October and 28 October–2 November. The same days are missing for El-Sayed and Benson and in every outlet series.
- A query for "Trump" across all sources (DOC API, `mode=timelinevolraw`) returns no "Total Monitored Articles" for exactly those 22 days. The saved response is `outage_probe_trump_20261105T054623Z.csv`, SHA-256 `d746a5aa1d3de48e2b23448075464d133e7558faeaba48dc94eda87acaabae7d`. The DOC API returns nothing for those days, so they cannot be re-pulled from it.
- On six more days GDELT monitored less than a tenth of its median of 116,203 articles per day: 6 October (3,958), 8 October (678), 10 October (1,836), 26 October (4,483), 27 October (2,218) and 3 November (5,672).
  - Our pull has rows on those days, but each day's volume share rests on very few articles.
  - On 8 October both candidates' values are 0, and on 10 October Benson's is 0.
  - E6 should drop or flag these six days.

**Most Michigan outlets are not in GDELT.**

- freep.com, detroitnews.com, mlive.com and michiganadvance.com returned no series in our pull. In the probe, freep, detroitnews and Michigan Advance had 0 covered days and mlive had 1. msnbc.com and ms.now were also empty.
- These domains are mostly unindexed, so the empty series are not evidence of zero coverage.
- Bridge Michigan (bridgemi.com) is indexed and has a series.
- Covering the other Michigan papers would need a second news database, checked for coverage first. It would also need a written amendment before any pull, since the plan names only GDELT.

## Spending (FEC independent expenditures), interim snapshot

**Script:** `src/data_collection/mi_senate_ie_2026_pull.py`. It covers every committee's Schedule E for or against El-Sayed (S6MI00418) and Rogers (S4MI00595) in the 2026 cycle, from the FEC's processed data plus the raw electronic filings.

**Snapshot retrieved 2026-11-05T05:41:32Z:**

- **Files:** `data/raw/e6/mi_senate_ie_2026_20261105T054132Z_rows.csv` and `..._by_committee.csv`.
- **Provenance:** every raw response, with its SHA-256, is in `raw_20261105T054132Z/manifest.json`. The CSVs were rebuilt from those saved responses with `--from-raw 20261105T054132Z` after the de-duplication fix below.
- **Coverage:** the latest expenditure date is 3 November.
- **To update:** rerun the script after 3 December. Each live run writes new timestamped files.

**De-duplication is the main trap.**

- **Why it's needed.** A 24-hour notice and the committee's next periodic report list the same expenditure, and the FEC's data keeps both. Raw rows therefore count some spending twice. Summing the FEC's raw-filing (efile) rows, in which an expenditure can appear both as a notice and as a periodic row, puts GLCF's spending since 5 August at $30.2M. De-duplicated, it is $24.3M: $19.4M against El-Sayed and $4.9M for Rogers.
- **Transaction IDs can't be trusted across filings.** SLF PAC restarts its IDs (SE.1, SE.2, …) in every 24-hour notice. A first version of the script keyed on committee and transaction ID, which merged different SLF expenditures. A reviewer caught it. That version was not saved, but its printed output put SLF's general-election totals against El-Sayed at $45.6M (high) and $42.4M (low). Fixed, they are $46.5M and $46.1M.
- **How the script de-duplicates now:**
  1. It drops every row of a file the raw filings mark as amended, whichever source the row came from, and any processed row the FEC marks as superseded. An amendment replaces the whole report, and the processed data sometimes still marks the old file current. Without this, Fighting for Michigan PAC's primary spending (file 1996934, amended by 2029348) would count $1.13M twice. About $18K of general-election rows dropped here appear in no kept file. Most are the filers' own corrections; one $1,837 row's amending file was not pulled.
  2. It collapses copies of the same filing's row, and notices re-filed with the same ID, date, candidate and whole-dollar amount. Raw-filing amounts drop the cents and processed amounts keep them, so amounts are compared on whole dollars here and within $1 below.
  3. It drops a notice only when a periodic row of the same committee and candidate matches it one-to-one, first on ID and amount, then on date and amount. In this snapshot, 915 of the 917 matched pairs have the same payee (ignoring case and punctuation), and the other two are spellings of one payee.
  4. It flags the remaining notices that fall inside a periodic report's coverage window. That report may hold them under another date or amount, or not at all.
- **So two totals are kept:**
  - **High:** flagged notices kept; may double count.
  - **Low:** flagged notices dropped; may undercount.
- **How far apart they are.** In the general election they differ by $8.4M, 69% of it AFP Action's.
  - AFP's 1–6 October notices match no row in its September report or its 1–14 October report: $3.8M against El-Sayed and $1.9M for Rogers. They are flagged only because of their dates.
  - AFP's matched periodic rows are dated 3–15 days after their notices (for example, a 15 September notice appears in the report as 25 September). So its 1–6 October notices may be in the Post-General report (15 October–23 November) under later dates. If so, AFP's low totals undercount by about those amounts.
  - All flagged general-election notices are dated on or before 14 October, inside reports already filed. Nothing yet shows where the non-AFP ones went.

**Checks:**

- **UDP:** its general-election spending against El-Sayed is $763,533.36 on both totals. That equals the sum of its 24-hour notices of 7–29 October cited in the plan.
  - UDP has no periodic rows in the general, so this checks the pull and the staging, not the de-duplication.
  - UDP's $64,392.80 of phone calls for Rogers (27 October) is in the pro-Rogers total.
  - UDP's last notice in this snapshot is dated 29 October (filed 30 October). Spending that needed no notice would appear only in the Post-General report.
- **SLF:** a bound computed separately from the pulled rows must fall between SLF's low and high totals against El-Sayed. The bound is SLF's general-election periodic rows (through 14 October) plus its notices dated after that. It is $46.14M, equal to the low total to the cent. That is expected by construction, so the real tests are that the bound does not exceed the high total ($46.52M) and that no notice after 14 October is lost. The first version's high ($45.6M) would have failed this check. The check weakens after the Post-General report is filed, since few notices will then fall after its coverage end.

**One possible double count, unresolved:** America First Action Fund filed two notices to the same payee (KAP Print), for the same date (21 October) and amount ($66,227.68), under different IDs, in files 2040689 and 2041995. Both are in the pro-Rogers total. The filing PDFs would show whether it is one mail drop or two.

**General-election totals** (stage from the FEC's election type, else a date on or after 5 August):

| Side | High | Low |
|---|---|---|
| For Rogers or against El-Sayed | $169.7M | $163.2M |
| For El-Sayed or against Rogers | $92.2M | $90.4M |

**Largest spenders (high / low, $M):**

| Committee | Spending | High | Low |
|---|---|---|---|
| SLF PAC | Against El-Sayed | 46.5 | 46.1 |
| WinSenate | Against Rogers | 34.0 | 34.0 |
| No Going Back PAC | Against El-Sayed | 27.5 | 27.5 |
| GLCF | Against El-Sayed | 19.4 | 19.4 |
| WinSenate | For El-Sayed | 12.6 | 12.5 |
| AFP Action | Against El-Sayed | 11.9 | 8.1 |
| TFM | Against El-Sayed | 11.4 | 11.3 |
| AFP Action | For Rogers | 10.5 | 8.5 |

**Still missing:**

- **The UDP-to-GLCF transfer.** The reported transfer of up to $9M is not in any filing yet. It should appear in both committees' Post-General reports, or in UDP's Year-End report if the money moved after 23 November.
- **Benson and James** (governor) file with Michigan, not the FEC. They are not pulled yet.
