"""Every independent expenditure by the pro-Israel and crypto super PACs, 2022-2026.

Why. Part 11 shows AIPAC's United Democracy Project as the largest opposing spender against insurgent
Democrats and the lead spender in every incumbent defeat, but not how that money is spent or what the
ads say. This pulls the itemized FEC Schedule E record for four committees so spending can be broken
down by target, party, support/oppose, election stage and medium, and so the targeted races can be
matched to the ads coded in `data/coded/superpac_ads_coded.csv`.

Committees. United Democracy Project C00799031 (AIPAC's super PAC), DMFI PAC C00710848 (Democratic
Majority for Israel; hybrid PAC), Fairshake C00835959 (crypto industry) and Protect Progress C00848440
(Fairshake's Democratic-side affiliate; its Republican-side twin, Defend American Jobs, is left out as it
does not spend in Democratic primaries). Fairshake's own cycle list starts in 2024.

Traps.
1. The itemized endpoint pages by keyset (`last_index` + `last_expenditure_date`), not page number, and
   ignores `two_year_transaction_period`, so each committee's full history is pulled once and the cycle
   is taken from the expenditure date. Totals reconcile to `/committee/<id>/totals/` for every cycle.
2. Rows include memo entries and amendments; `memo_code == 'X'` rows are dropped and, where a filing is
   amended, the FEC's processed data already carries the latest version (`is_notice` 24/48-hour notices are
   superseded by the periodic report and dropped when a periodic row exists).
3. `expenditure_description` is free text ("TV AD BUY - OPPOSE X", "DIGITAL", "MAILER - PRINTING") and is
   classified into media with the regexes in MEDIUM, first match wins.

Output: `data/raw/superpac_ads/superpac_ie_itemized.csv`.
"""

from pathlib import Path
import re
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import fec_insurgent_pull as F  # noqa: E402  (reuses the cached, key-safe FEC getter)

OUT = Path("data/raw/superpac_ads")
COMMITTEES = {"C00799031": "UDP", "C00710848": "DMFI", "C00835959": "Fairshake", "C00848440": "Protect Progress"}
MEDIUM = [("tv", r"\btv\b|televis|broadcast|cable|ott|ctv|streaming|media buy|ad buy|airtime|placement"),
          ("digital", r"digital|online|internet|facebook|google|youtube|social|web|programmatic|text messag|sms"),
          ("mail", r"mail|postage|postcard|print"),
          ("radio", r"radio|audio"),
          ("production", r"production|produc|creative|editing|video"),
          ("field", r"canvass|field|door|phone|call|live call|ivr"),
          ("research/polling", r"poll|survey|research|focus group"),
          ("other", r".")]


def medium(desc):
    d = (desc or "").lower()
    return next(m for m, p in MEDIUM if re.search(p, d))


def pull(cid):
    rows, last = [], {}
    while True:
        j = F.get("/schedules/schedule_e/", committee_id=cid, per_page=100, sort="-expenditure_date", **last)
        res = j.get("results", [])
        rows += res
        li = j.get("pagination", {}).get("last_indexes")
        if not res or not li:
            break
        last = {k: v for k, v in li.items() if v is not None}
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for cid, short in COMMITTEES.items():
        rows = pull(cid)
        print(f"  {short:16s} {len(rows)} rows")
        for r in rows:
            recs.append({"spender": short, "date": r.get("expenditure_date") or r.get("dissemination_date"),
                         "amount": r.get("expenditure_amount"), "support_oppose": r.get("support_oppose_indicator"),
                         "candidate": r.get("candidate_name"), "candidate_id": r.get("candidate_id"),
                         "party": r.get("candidate_party"), "office": r.get("candidate_office"),
                         "state": r.get("candidate_office_state"), "district": r.get("candidate_office_district"),
                         "election_type": r.get("election_type"), "description": r.get("expenditure_description"),
                         "payee": r.get("payee_name"), "memo_code": r.get("memo_code"), "is_notice": r.get("is_notice"),
                         "filing_form": r.get("filing_form"), "sub_id": r.get("sub_id")})
    d = pd.DataFrame(recs).drop_duplicates("sub_id")
    d = d[d.memo_code != "X"]
    yr = pd.to_datetime(d.date, errors="coerce").dt.year
    d["cycle"] = yr + yr % 2                      # two-year cycle ending in the even year
    # 24/48-hour notices duplicate periodic-report rows; keep notices only for committee-cycles with no periodic rows
    periodic = d[d.is_notice != True].groupby(["spender", "cycle"]).size()
    d = d[(d.is_notice != True) | ~d.set_index(["spender", "cycle"]).index.isin(periodic.index)]
    d["medium"] = d.description.map(medium)
    d.to_csv(OUT / "superpac_ie_itemized.csv", index=False)
    print(f"wrote {len(d)} rows; ${d.amount.sum()/1e6:,.1f}M")


if __name__ == "__main__":
    main()
