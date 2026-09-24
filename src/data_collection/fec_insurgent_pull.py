"""Study A: Justice Democrats-endorsed House candidates 2018-2026 with FEC money for them and their main
Democratic-primary opponent.

Case universe: every House candidate in the Justice Democrats endorsement tables (Wikipedia article
wikitext, parsed to data/raw/insurgent/jd_house_endorsements_raw.csv). For each case:
  - the JD candidate's FEC id (candidate search by name, state, district, cycle);
  - the main opponent: the Democratic incumbent in that district-cycle if the JD candidate is not the
    incumbent, else the best-funded other Democratic candidate in the district-cycle;
  - for both: receipts through the pre-primary report (12P year-to-date + prior year-end year-to-date,
    falling back to the last report before the primary), full-cycle receipts, unitemized (small-dollar)
    share, and Schedule E independent expenditures for/against by committee for the cycle.
FEC API (api.open.fec.gov, DEMO_KEY: 1,000 requests/hour); responses cached as JSON under data/raw/insurgent/fec/.
"""

from pathlib import Path
import json
import re
import time
import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

RAW = Path("data/raw/insurgent"); CACHE = RAW / "fec"
API = "https://api.open.fec.gov/v1"
KEY = os.getenv("FEC_API_KEY") or "DEMO_KEY"   # DEMO_KEY is 40 calls/hour; a personal key (free) is 1,000/hour
STATE_ABBR = {"Arizona": "AZ", "California": "CA", "Colorado": "CO", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
              "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Jersey": "NJ", "New Mexico": "NM",
              "New York": "NY", "North Carolina": "NC", "Ohio": "OH", "Pennsylvania": "PA", "Texas": "TX", "Washington": "WA", "Tennessee": "TN", "Wisconsin": "WI", "Virginia": "VA", "Oregon": "OR",
              "Connecticut": "CT", "Kentucky": "KY", "Louisiana": "LA", "Oklahoma": "OK", "Arkansas": "AR", "South Carolina": "SC", "Alabama": "AL", "Mississippi": "MS", "Utah": "UT", "Vermont": "VT",
              "Maine": "ME", "New Hampshire": "NH", "Rhode Island": "RI", "Delaware": "DE", "West Virginia": "WV", "Idaho": "ID", "Wyoming": "WY", "North Dakota": "ND", "South Dakota": "SD", "Alaska": "AK"}


# Districts where the FEC still lists the prior incumbent for the cycle but the seat was open (retirement,
# resignation, or run for another office); the opponent is then the best-funded other Democrat.
OPEN_SEAT = {(2018, "Rashida Tlaib"), (2018, "Ilhan Omar"), (2018, "Antoinette Sedillo Lopez"), (2018, "Juana Matias"), (2018, "Amy Vilela"), (2018, "Kaniela Ing"),
             (2021, "Nina Turner"), (2026, "Justin Pearson"), (2026, "Chris Rabb"), (2026, "Claire Valdez"), (2026, "Saikat Chakrabarti"), (2026, "Kat Abughazaleh"),
             (2026, "Frederick Haynes III"), (2026, "Junaid Ahmed")}


def get(path, **params):
    params["api_key"] = KEY
    key = re.sub(r"[^A-Za-z0-9]+", "_", path + json.dumps({k: v for k, v in params.items() if k != "api_key"}, sort_keys=True))[:180]
    f = CACHE / f"{key}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    for attempt in range(60):
        r = requests.get(API + path, params=params, timeout=60)
        if r.status_code == 200:
            j = r.json(); f.write_text(json.dumps(j), encoding="utf-8"); time.sleep(0.5); return j
        if r.status_code == 429:
            print("  FEC rate limit; sleeping 120 s", flush=True); time.sleep(120)
        else:
            time.sleep(5)
    shown = {k: v for k, v in params.items() if k != "api_key"}     # never put the key in a traceback
    raise RuntimeError(f"FEC {path} {shown} -> {r.status_code}")


def find_candidate(name, state, district, cycle):
    last = name.split()[-1].strip("()").replace("(inc.)", "").strip()
    last = re.sub(r"[^A-Za-z\-']", "", name.replace(" (inc.)", "").split()[-1])
    j = get("/candidates/search/", q=last, office="H", state=state, district=f"{int(district):02d}", cycle=cycle, party="DEM", per_page=20)
    res = j.get("results", [])
    if not res:
        j = get("/candidates/search/", q=last, office="H", state=state, cycle=cycle, per_page=20); res = j.get("results", [])
    first = name.replace(" (inc.)", "").split()[0].lower()
    for c in res:
        if first[:3] in c["name"].lower():
            return c
    return res[0] if res else None


def district_dems(state, district, cycle):
    j = get("/candidates/totals/", office="H", state=state, district=f"{int(district):02d}", cycle=cycle, party="DEM", election_full="false", per_page=50, sort="-receipts")
    return j.get("results", [])


def pre_primary_receipts(cid, cycle, primary_date):
    j = get("/reports/house-senate/", candidate_id=cid, cycle=cycle, per_page=100, sort="coverage_end_date")
    reps = [r for r in j.get("results", []) if r.get("coverage_end_date")]
    if not reps:
        return None, None, None
    pd_ = pd.Timestamp(primary_date) if primary_date else None
    before = [r for r in reps if pd_ is None or pd.Timestamp(r["coverage_end_date"]) <= pd_]
    if not before:
        return None, None, None
    # latest report before the primary; add prior-year year-end YTD if that report is in the election year
    last = max(before, key=lambda r: r["coverage_end_date"])
    num = lambda v: float(v) if v not in (None, "") else 0.0
    ytd = num(last.get("total_receipts_ytd"))
    unit = num(last.get("individual_unitemized_contributions_ytd"))
    yr = pd.Timestamp(last["coverage_end_date"]).year
    prior = [r for r in reps if pd.Timestamp(r["coverage_end_date"]).year == yr - 1]
    if prior:
        p = max(prior, key=lambda r: r["coverage_end_date"])
        ytd += num(p.get("total_receipts_ytd")); unit += num(p.get("individual_unitemized_contributions_ytd"))
    return ytd, unit, last["coverage_end_date"][:10]


def primary_date(state, cycle):
    """Statewide House primary date from the FEC election-dates endpoint (first regular primary in the cycle year)."""
    j = get("/election-dates/", election_state=state, election_year=cycle, election_type_id="P", office_sought="H", per_page=50)
    ds = sorted(r["election_date"][:10] for r in j.get("results", []) if r.get("election_date") and r.get("election_type_id") == "P")
    return ds[0] if ds else None


def ie_pre_primary(cid, cycle, primary_date):
    """Itemized Schedule E for the candidate, summed by support/oppose over expenditures disseminated or
    dated on or before the primary. Keyset-paginated; the server-side date filter is not reliable, so the
    cutoff is applied client-side on min(expenditure_date, dissemination_date)."""
    if not primary_date:
        return None, None
    cutoff = pd.Timestamp(primary_date)
    sup = opp = 0.0
    params = dict(candidate_id=cid, cycle=cycle, is_notice="false", per_page=100, max_expenditure_date=str(cutoff.date()))
    for page in range(30):
        j = get("/schedules/schedule_e/", **params)
        for r in j.get("results", []):
            ds = [d for d in (r.get("expenditure_date"), r.get("dissemination_date")) if d]
            if not ds or min(pd.Timestamp(d) for d in ds) > cutoff:
                continue
            amt = float(r.get("expenditure_amount") or 0)
            if r.get("support_oppose_indicator") == "S": sup += amt
            elif r.get("support_oppose_indicator") == "O": opp += amt
        li = j.get("pagination", {}).get("last_indexes") or {}
        if not li or not j.get("results"):
            break
        params.update({"last_index": li.get("last_index"), "last_expenditure_date": li.get("last_expenditure_date")})
    return sup, opp


def ie_totals(cid, cycle):
    j = get("/schedules/schedule_e/by_candidate/", candidate_id=cid, cycle=cycle, per_page=100)
    sup = sum(float(r["total"] or 0) for r in j.get("results", []) if r["support_oppose_indicator"] == "S")
    opp = sum(float(r["total"] or 0) for r in j.get("results", []) if r["support_oppose_indicator"] == "O")
    top_opp = sorted([(r["committee_name"], float(r["total"] or 0)) for r in j.get("results", []) if r["support_oppose_indicator"] == "O"], key=lambda x: -x[1])[:3]
    return sup, opp, "; ".join(f"{n} {v/1e6:.2f}M" for n, v in top_opp)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW / "jd_house_endorsements_raw.csv")
    raw.columns = ["cycle", "name", "state", "district", "date", "prim_result", "prim_pct", "gen_result", "gen_pct", "x"]
    raw = raw[raw.name.notna() & raw.district.astype(str).str.contains("congressional")].copy()
    raw["name"] = raw.name.str.replace(r'rowspan="?\d"?\s*\|', "", regex=True).str.strip()
    raw["state"] = raw.state.str.replace(r'rowspan="?\d"?\s*\|', "", regex=True).str.strip()
    raw["district"] = raw.district.str.replace(r'rowspan="?\d"?\s*\|', "", regex=True).str.strip()
    raw["dist_no"] = raw.district.str.extract(r"(\d+)(?:st|nd|rd|th)")[0].fillna("0").astype(int)
    raw["st"] = raw.state.map(STATE_ABBR)
    raw["incumbent_jd"] = raw.name.str.contains(r"\(inc\.\)")
    raw["cand"] = raw.name.str.replace(r"\s*\(inc\.\)", "", regex=True)
    raw["date"] = raw.date.astype(str).str.replace(r"<br>.*", "", regex=True).str.strip().replace("nan", None)
    raw["cycle_fec"] = raw.cycle.where(raw.cycle != 2021, 2022)
    rows = []
    for _, r in raw.iterrows():
        try:
            c = find_candidate(r.cand, r.st, r.dist_no, int(r.cycle_fec))
            if not c:
                print("no FEC match:", r.cycle, r.cand, r.st, r.dist_no); continue
            cid = c["candidate_id"]
            dems = district_dems(r.st, r.dist_no, int(r.cycle_fec))
            others = [d for d in dems if d["candidate_id"] != cid]
            inc = [d for d in others if d.get("incumbent_challenge") == "I"]
            if (int(r.cycle), r.cand) in OPEN_SEAT:
                others = [d for d in others if d.get("incumbent_challenge") != "I"]; inc = []
            opp = inc[0] if inc else (others[0] if others else None)
            pdate = r.date if isinstance(r.date, str) and re.match(r"\d{4}-\d", r.date) else primary_date(r.st, int(r.cycle_fec))
            pre, unit, asof = pre_primary_receipts(cid, int(r.cycle_fec), pdate)
            sup, oppose, top = ie_totals(cid, int(r.cycle_fec))
            sup_pre, opp_pre = ie_pre_primary(cid, int(r.cycle_fec), pdate)
            tot = next((d for d in dems if d["candidate_id"] == cid), {})
            fnum = lambda v: float(v) if v not in (None, "") else None
            row = {"cycle": r.cycle, "candidate": r.cand, "state": r.st, "district": r.dist_no, "jd_incumbent": r.incumbent_jd, "primary_date": pdate, "prim_result": r.prim_result, "prim_pct": r.prim_pct,
                   "fec_id": cid, "cycle_receipts": fnum(tot.get("receipts")), "cycle_unitemized": fnum(tot.get("individual_unitemized_contributions")), "pre_primary_receipts": pre, "pre_primary_unitemized": unit, "pre_primary_asof": asof,
                   "ie_support": sup, "ie_oppose": oppose, "ie_top_opposers": top, "ie_support_pre": sup_pre, "ie_oppose_pre": opp_pre,
                   "opp_name": opp["name"] if opp else None, "opp_fec_id": opp["candidate_id"] if opp else None, "opp_is_incumbent": bool(inc), "opp_type": "incumbent" if inc else ("other_dem" if opp else "none")}
            if opp:
                p2, u2, a2 = pre_primary_receipts(opp["candidate_id"], int(r.cycle_fec), pdate)
                s2, o2, t2 = ie_totals(opp["candidate_id"], int(r.cycle_fec))
                s2p, o2p = ie_pre_primary(opp["candidate_id"], int(r.cycle_fec), pdate)
                row.update({"opp_cycle_receipts": fnum(opp.get("receipts")), "opp_cycle_unitemized": fnum(opp.get("individual_unitemized_contributions")), "opp_pre_primary_receipts": p2, "opp_pre_primary_unitemized": u2,
                            "opp_ie_support": s2, "opp_ie_oppose": o2, "opp_ie_top_opposers": t2, "opp_ie_support_pre": s2p, "opp_ie_oppose_pre": o2p})
            rows.append(row)
            print(f"{r.cycle} {r.cand:28s} {r.st}-{r.dist_no:02d} pre ${(pre or 0)/1e6:.2f}M IE +{sup/1e6:.2f}/-{oppose/1e6:.2f} | opp {row['opp_name']} pre ${(row.get('opp_pre_primary_receipts') or 0)/1e6:.2f}M IE +{row.get('opp_ie_support', 0)/1e6:.2f}/-{row.get('opp_ie_oppose', 0)/1e6:.2f} ({row['opp_type']})")
        except Exception as ex:
            print("ERROR", r.cycle, r.cand, ex)
        pd.DataFrame(rows).to_csv(RAW / "jd_cases_fec.csv", index=False)
    print("wrote", RAW / "jd_cases_fec.csv", len(rows))


if __name__ == "__main__":
    main()
