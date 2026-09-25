"""Who funds the pop-up super PACs in the 2026 Democratic primaries.

Why. Part 11 found the pro-Israel and crypto committees hide their cause in their ads. Money can also be hidden
one level up: newly registered committees with local or progressive-sounding names ("Chicago Progressive
Partnership", "New Yorkers for Lower Costs") that spend in a single race. This traces their itemized receipts.

Steps.
1. Every committee with independent expenditures (FEC Schedule E, by candidate) for or against the candidates in
   the 2026 races studied. `first_file_date` on or after 2025-01-01 marks a pop-up.
2. Side, from spending alone: net help to the left = support(left) + oppose(establishment) - support(est) -
   oppose(left), with the left/establishment labels in SIDES (the same assignments as the rest of Part 11;
   IL-7 and FL-24, crowded races with no single left-vs-establishment contrast, count toward no side).
3. Each pop-up's itemized receipts (Schedule A, keyset-paginated), and the donor lists of UDP, DMFI, Fairshake,
   Protect Progress and Defend American Jobs (all cycles 2022-2026). Individuals are matched to those lists on
   normalised name + ZIP5; committee transfers are matched on committee id.

4. The network committees' own 2026 disbursements (Schedule B), to find money passed through an intermediary:
   UDP -> EDW Action Fund -> Pro-Choice Majority Action; UDP -> Elect Chicago Women -> Chicago Progressive
   Partnership.

Output: `data/raw/superpac_ads/popups_ie.csv`, `popup_receipts.csv`, `network_donors.csv`,
`network_disbursements_2026.csv`.
"""

from pathlib import Path
import re
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import fec_insurgent_pull as F  # noqa: E402

OUT = Path("data/raw/superpac_ads")
NETWORK = {"C00799031": "UDP", "C00710848": "DMFI", "C00835959": "Fairshake", "C00848440": "Protect Progress",
           "C00836221": "Defend American Jobs"}
# race -> (left candidate, establishment candidate, state, district; 0 = Senate)
SIDES = {"2026 MI-SEN": ("Abdul El-Sayed", "Haley Stevens", "MI", 0),
         "2026 IL-SEN": ("Juliana Stratton", "Raja Krishnamoorthi", "IL", 0),
         "2026 MO-1": ("Cori Bush", "Wesley Bell", "MO", 1),
         "2026 NJ-11": ("Analilia Mejia", "Tom Malinowski", "NJ", 11),
         "2026 CA-14": ("Aisha Wahab", "Melissa Hernandez", "CA", 14),
         "2026 TX-18": ("Al Green", "Christian Menefee", "TX", 18),
         "2026 MI-13": ("Donavan McKinney", "Shri Thanedar", "MI", 13),
         "2026 NY-15": ("Michael Blake", "Ritchie Torres", "NY", 15),
         "2026 NY-7": ("Claire Valdez", "Antonio Reynoso", "NY", 7),
         "2026 NY-10": ("Brad Lander", "Dan Goldman", "NY", 10),
         "2026 NY-13": ("Darializa Avila Chevalier", "Adriano Espaillat", "NY", 13),
         "2026 NY-6": ("Chuck Park", "Grace Meng", "NY", 6),
         "2026 CO-1": ("Melat Kiros", "Diana DeGette", "CO", 1),
         "2026 IL-8": ("Junaid Ahmed", "Melissa Bean", "IL", 8),
         "2026 IL-2": ("Robert Peters", None, "IL", 2)}
NO_SIDE = {"2026 IL-7": ("La Shawn Ford", "Melissa Conyears-Ervin", "IL", 7),
           "2026 FL-24": ("Oliver Gilbert", "Shevrin Jones", "FL", 24)}


def cand_id(name, st, dist):
    if dist:
        c = F.find_candidate(name, st, dist, 2026)
        return c["candidate_id"] if c else None
    j = F.get("/candidates/search/", q=name.split()[-1], office="S", state=st, cycle=2026, party="DEM", per_page=20)
    r = [x for x in j.get("results", []) if name.split()[-1].upper() in x["name"]]
    return r[0]["candidate_id"] if r else None


def schedule_a(committee_id, cycle):
    rows, last = [], {}
    for _ in range(400):
        j = F.get("/schedules/schedule_a/", committee_id=committee_id, two_year_transaction_period=cycle,
                  per_page=100, sort="-contribution_receipt_date", **last)
        res = j.get("results", [])
        rows += res
        li = j.get("pagination", {}).get("last_indexes")
        if not res or not li:
            break
        last = {k: v for k, v in li.items() if v is not None}
    return rows


def key(name, zipc):
    n = re.sub(r"[^A-Z ]", "", (name or "").upper())
    parts = [p for p in n.split() if p not in {"MR", "MRS", "MS", "DR", "JR", "SR", "II", "III"}]
    return " ".join(sorted(parts[:3])) + "|" + str(zipc or "")[:5]


def main():
    # 1-2. spenders and side
    rows = []
    for race, (left, est, st, dist) in {**SIDES, **NO_SIDE}.items():
        for role, name in (("left", left), ("est", est)):
            if not name:
                continue
            cid = cand_id(name, st, dist)
            if not cid:
                print(f"  no FEC id: {name}"); continue
            j = F.get("/schedules/schedule_e/by_candidate/", candidate_id=cid, cycle=2026, per_page=100)
            for x in j.get("results", []):
                rows.append(dict(race=race, candidate=name, role=role if race in SIDES else "none",
                                 committee_id=x["committee_id"], committee=x["committee_name"],
                                 so=x["support_oppose_indicator"], total=float(x["total"] or 0)))
    ie = pd.DataFrame(rows)
    sign = {("left", "S"): 1, ("est", "O"): 1, ("est", "S"): -1, ("left", "O"): -1}
    ie["net_left"] = [sign.get((r, s), 0) * t for r, s, t in zip(ie.role, ie.so, ie.total)]
    meta = {c: F.get(f"/committee/{c}/", per_page=1)["results"][0] for c in ie.committee_id.unique()}
    ie["first_file"] = ie.committee_id.map(lambda c: meta[c].get("first_file_date"))
    ie["committee_type"] = ie.committee_id.map(lambda c: meta[c].get("committee_type_full"))
    ie.to_csv(OUT / "popups_ie.csv", index=False)
    by = ie.groupby(["committee_id", "committee", "first_file"]).agg(total=("total", "sum"), net_left=("net_left", "sum"),
                                                                     races=("race", lambda s: ", ".join(sorted(set(s))))).reset_index()
    pop = by[(by.first_file >= "2025-01-01") & (by.total >= 100_000)]
    print(f"{len(pop)} pop-up committees with $100k+:")
    print(pop.assign(total=(pop.total / 1e6).round(2), net_left=(pop.net_left / 1e6).round(2)).to_string(index=False))

    # 3. receipts of the pop-ups and of the network
    rec = []
    for cid in pop.committee_id:
        for cyc in (2026,):
            for r in schedule_a(cid, cyc):
                rec.append(dict(popup=cid, date=r.get("contribution_receipt_date"), amount=r.get("contribution_receipt_amount"),
                                name=r.get("contributor_name"), zip=r.get("contributor_zip"), employer=r.get("contributor_employer"),
                                entity=r.get("entity_type"), contributor_committee=r.get("contributor_committee_id") or
                                (r.get("contributor") or {}).get("committee_id"), memo=r.get("memo_code"), sub_id=r.get("sub_id")))
    R = pd.DataFrame(rec).drop_duplicates("sub_id")
    R = R[R.memo != "X"]
    R.to_csv(OUT / "popup_receipts.csv", index=False)
    net = []
    for cid, short in NETWORK.items():
        for cyc in (2022, 2024, 2026):
            for r in schedule_a(cid, cyc):
                net.append(dict(network=short, name=r.get("contributor_name"), zip=r.get("contributor_zip"),
                                entity=r.get("entity_type"), amount=r.get("contribution_receipt_amount"), sub_id=r.get("sub_id")))
    N = pd.DataFrame(net).drop_duplicates("sub_id")
    N.to_csv(OUT / "network_donors.csv", index=False)
    out = []
    for cid, short in NETWORK.items():
        last = {}
        for _ in range(200):
            j = F.get("/schedules/schedule_b/", committee_id=cid, two_year_transaction_period=2026, per_page=100,
                      sort="-disbursement_date", **last)
            res = j.get("results", [])
            out += [dict(network=short, recipient=r.get("recipient_name"), recipient_committee=r.get("recipient_committee_id"),
                         amount=r.get("disbursement_amount"), date=r.get("disbursement_date"),
                         desc=r.get("disbursement_description")) for r in res]
            li = j.get("pagination", {}).get("last_indexes")
            if not res or not li:
                break
            last = {k: v for k, v in li.items() if v is not None}
    pd.DataFrame(out).to_csv(OUT / "network_disbursements_2026.csv", index=False)
    print(f"receipts: {len(R)} pop-up rows; {len(N)} network donor rows; {len(out)} network disbursements")


if __name__ == "__main__":
    main()
