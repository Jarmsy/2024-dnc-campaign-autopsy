# Notes on `e1_endorsements_2026.csv`

The CSV is the record of Justice Democrats' and national DSA's 2026 House endorsement lists as published on 4 November 2026 (commit 54ad019). It is not edited. Corrections and provenance found later are recorded here instead, and E1 applies them in Phase 2.

## Corrections

| Candidate | Field in the CSV | As published | Use for E1 | Evidence |
|---|---|---|---|---|
| Greg Casar | state / district_num | TX-35 (JD's card, unchanged since 2021) | **TX-37** | The FEC lists his 2026 candidacy (H2TX35144) in district 37: `data/raw/insurgent/fec/_candidates_search_cycle_2026_district_37_..._q_Casar_state_TX_.json`; `data/raw/insurgent/jd_cases_fec.csv` row `2026,Greg Casar,TX,37`, primary won 3 Mar 2026. Texas redrew its map in 2025. |

To check before E1 is run:

- **Oliver Larkin (FL-25, national DSA only).** Is he the Democratic nominee? Florida's primary was 18 August 2026. Florida is on `incumbent_primaries_pull.REDRAWN_2026`, so also confirm the district number on the 2026 lines.
  - *Resolved 5 November 2026:* he is not the nominee, so E1, whose set is nominees, leaves him out. Rep. Jared Moskowitz (FEC H2FL22171) won the 18 August Democratic primary with "more than two thirds of the vote", per WLRN's election-night report; Larkin conceded ([WLRN](https://www.wlrn.org/government-politics/2026-08-18/jared-moskowitz-25-democratic-primary); [CBS Miami](https://www.cbsnews.com/miami/news/florida-primary-district-25-democratic-jared-moskowitz/)). The FEC lists Larkin's candidacy (H6FL23154) in district 25 on the 2026 lines.

## Provenance

The CSV records the SHA-256 of the two raw files its rows come from. The third file read on 4 November is the national DSA "Past Endorsements" Airtable view. It holds 327 rows dated 2016-07-28 to 2025-11-04 and no 2026 federal row, which is the check that no 2026 endorsement had been moved off the current list.

| Raw file (data/raw/e1_endorsements/, gitignored) | SHA-256 |
|---|---|
| jd_candidates_20261104T224450Z.html | 1ac5a155d7d762cdad854dd881ea911f0b73862f036092cdc0162aef54e60815 |
| dsa_current_20261104T224450Z.json | (in the CSV's raw_sha256 column) |
| dsa_past_20261104T224450Z.json | 6f6622ba6400d1e6451de613af3ba4a9358e7c2173dce0aac96636f08fc75c96 |

## For the write-up

National DSA's list does not include Claire Valdez or Darializa Avila Chevalier. Part 11's DSA tier counts them through NYC-DSA's chapter endorsements. Both are on Justice Democrats' list, so E1's set includes them, but a DSA versus JD-only split in E1 would differ from Part 11's.
