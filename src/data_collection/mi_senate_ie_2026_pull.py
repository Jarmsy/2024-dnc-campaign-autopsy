"""Independent expenditures for and against El-Sayed and Rogers, Michigan Senate 2026 (E6, interim snapshot).

Why. E6 (report/results_2026_analysis_plan.md) describes the spending gap between El-Sayed and Benson,
from filings through 3 December. The 3 December Post-General reports are not out yet, but every 24-hour
notice through election day is. This saves a dated snapshot now, so the late-October and November
notices are on disk, and the same script is rerun after 3 December for the final figures. Each run writes
new timestamped files; nothing is overwritten.

Sources. FEC Schedule E for candidates S6MI00418 (El-Sayed) and S4MI00595 (Rogers), cycle 2026:
  - processed data, /schedules/schedule_e/ (keyset paging);
  - raw electronic filings, /schedules/schedule_e/efile/, which carry notices filed in the last day or two
    that the processed data does not have yet.
Every raw response is saved under data/raw/e6/raw_<stamp>/ with its SHA-256 in the manifest.

De-duplication.
  0. Memo rows (memo_code X) are dropped, and so is every row of a superseded file: one the raw filings mark
     as amended (filing.amended_by set, or most_recent false), whichever source the row came from, and any
     processed row whose own most_recent is false. The
     processed data can still mark a superseded file most_recent (Fighting for Michigan PAC's 1996934,
     amended by 2029348, would otherwise count $1.13M twice). An amendment replaces the whole report; in the
     5 Nov 2026 snapshot about $18K of general-election rows dropped here appear in no kept file (the
     filers' own corrections, plus one $1,837 row whose amending file was not pulled).
  1. Copies of one filing's row in both sources are collapsed, keyed by committee, candidate, file number and
     transaction ID (processed preferred). Transaction IDs are NOT unique across filings: SLF PAC restarts
     them (SE.1, SE.2, ...) in every 24-hour notice, so they are never matched across files on ID alone.
     A notice re-filed in a later 24-hour report with the same ID, date, candidate and whole-dollar amount
     is collapsed to the later file (MoveOn and WFP, for example). Raw-filing amounts are whole dollars (cents
     truncated) while processed amounts have cents, so amounts are compared on their whole-dollar part here
     and within $1 in step 2.
  2. A 24-hour notice (is_notice) is dropped when a periodic row (F3X) of the same committee and candidate
     matches it one-to-one: first on transaction ID and amount (within $1), then on date and amount. Pairs
     whose payees differ are counted and printed (2 of 917 in the 5 Nov 2026 snapshot, both spellings of one
     payee: "PATRIOT CONTRACT"/"PATRIOT CONTACT", "SWITCHBOARD"/"SWITCHBOARD PUBLIC BENEFIT CORP").
  3. Notices still unmatched but dated inside the coverage window of a periodic file that has rows for the
     same committee and candidate are flagged (`in_periodic_window`). They may be in that report under a
     different date or amount, or not in it at all (AFP Action's 1-6 October media notices, $3.8M against
     El-Sayed and $1.9M for Rogers, match no periodic row). So two totals are kept: `total_high` keeps them
     (may double count) and `total_low` drops them (may undercount). All flagged general-election notices in
     the 5 Nov snapshot are dated on or before 14 Oct. AFP's periodic rows are dated 3-15 days after their
     matched notices, so its 1-6 Oct notices may appear in the Post-General report (15 Oct - 23 Nov, due
     3 Dec) under later dates; nothing yet shows where the other flagged notices went.

Stage. General election = election_type G2026 where the FEC gives it; otherwise (raw-only rows) an
expenditure or dissemination date on or after 5 August 2026, the day after the primary. Disagreements
between the two rules are printed.

Checks. (1) UDP's general-election spending against El-Sayed must be at least $763,533.36, the sum of its
itemized 24-hour notices of 7-29 October cited in the plan (UDP has no periodic rows in the general, so this
checks the pull and staging, not the de-duplication). (2) A bound computed separately from the pulled rows
for SLF PAC, which reuses transaction IDs: its general-election periodic rows plus its notices dated after
its last periodic coverage end must lie between its low and high totals against El-Sayed. The first version
of this script, which keyed on committee and transaction ID across files, fails this check (its high was
below the bound). The low total equals the bound by construction when every flagged notice predates the
coverage end, so the check's real tests are the high side and the notices after the coverage end. It
weakens once the Post-General report moves the coverage end to 23 Nov.

Output (gitignored): data/raw/e6/mi_senate_ie_2026_<stamp>_rows.csv (one row per expenditure, every stage)
and ..._by_committee.csv (general-election totals by committee, candidate and support/oppose).
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import sys
import time

import pandas as pd
import requests

API = "https://api.open.fec.gov/v1"
CANDS = {"S6MI00418": "El-Sayed", "S4MI00595": "Rogers"}
GENERAL_START = "2026-08-05"
UDP = "C00799031"
UDP_CHECK = 763533.36
OUT = Path("data/raw/e6")


def _key():
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("FEC"):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no FEC key in .env")


KEY = _key()


FROM_RAW = False


def get(path, raw_dir, tag, **params):
    """GET one page; save the response; never put the key in an error message. With --from-raw, read the
    saved response instead (re-deriving a snapshot without fetching)."""
    if FROM_RAW:
        return json.loads((raw_dir / f"{tag}.json").read_text(encoding="utf-8"))
    for attempt in range(20):
        try:
            r = requests.get(API + path, params={**params, "api_key": KEY}, timeout=90)
        except requests.RequestException as e:
            print(f"  {type(e).__name__}; retrying", flush=True)
            time.sleep(10)
            continue
        if r.status_code == 200:
            body = r.content
            f = raw_dir / f"{tag}.json"
            f.write_bytes(body)
            MANIFEST.append({"file": f.name, "path": path,
                             "params": {k: v for k, v in params.items()},
                             "sha256": hashlib.sha256(body).hexdigest()})
            time.sleep(0.4)
            return json.loads(body)
        time.sleep(60 if r.status_code == 429 else 5)
    raise RuntimeError(f"FEC {path} {params} failed after 20 attempts")


MANIFEST = []


def pull_processed(cid, raw_dir):
    rows, last, n = [], {}, 0
    while True:
        j = get("/schedules/schedule_e/", raw_dir, f"processed_{cid}_{n:03d}",
                candidate_id=cid, cycle=2026, per_page=100, sort="-expenditure_date", **last)
        res = j.get("results", [])
        rows += res
        li = j.get("pagination", {}).get("last_indexes")
        n += 1
        if not res or not li:
            return rows
        last = li


def pull_efile(cid, raw_dir):
    rows, page = [], 1
    while True:
        j = get("/schedules/schedule_e/efile/", raw_dir, f"efile_{cid}_{page:03d}",
                candidate_id=cid, per_page=100, page=page)
        rows += j.get("results", [])
        if page >= j.get("pagination", {}).get("pages", 0):
            return rows
        page += 1


def norm(x, source, cid):
    com = x.get("committee") or {}
    d = (x.get("expenditure_date") or x.get("dissemination_date") or "")[:10]
    return {"source": source, "candidate_id": cid, "candidate": CANDS[cid],
            "committee_id": x.get("committee_id"), "committee_name": com.get("name") if isinstance(com, dict) else None,
            "support_oppose": x.get("support_oppose_indicator"), "amount": float(x.get("expenditure_amount") or 0),
            "date": d or None, "is_notice": bool(x.get("is_notice")),
            "form": x.get("filing_form") or x.get("report_type"), "election_type": x.get("election_type"),
            "transaction_id": x.get("transaction_id"), "file_number": x.get("file_number"),
            "image_number": x.get("image_number"), "memo_code": x.get("memo_code"),
            "most_recent": x.get("most_recent"),
            "amended_by": (x.get("filing") or {}).get("amended_by") if isinstance(x.get("filing"), dict) else None,
            "description": x.get("expenditure_description"),
            "payee": x.get("payee_name"), "pdf_url": x.get("pdf_url")}


def superseded_mask(df):
    """Rows of a file the raw filings mark as amended, from either source (see step 0)."""
    ef = df[df.source == "efile"]
    sup = set(ef.loc[ef.amended_by.notna() | (ef.most_recent == False), "file_number"].dropna().astype(int))  # noqa: E712
    m = df.file_number.isin(sup) | (df.most_recent == False)  # noqa: E712
    print(f"  rows of superseded files dropped: {int(m.sum())} ({len(sup)} files)")
    return m


def collapse_copies(df):
    """Steps 0-1: drop memo rows and superseded files; collapse the processed and raw copies of one filing's row."""
    df = df.copy()
    df["file_number"] = pd.to_numeric(df.file_number, errors="coerce")
    df = df[~superseded_mask(df) & (df.memo_code != "X")].copy()
    df["_processed"] = (df.source == "processed").astype(int)
    has = df.transaction_id.notna() & (df.transaction_id != "") & df.file_number.notna()
    keyed = (df[has].sort_values("_processed", ascending=False)
             .drop_duplicates(["committee_id", "candidate_id", "file_number", "transaction_id"], keep="first"))
    out = pd.concat([keyed, df[~has]], ignore_index=True).drop(columns="_processed")
    # 1b: a notice re-filed in a later 24-hour report (same ID, amount, date and candidate) is one expenditure
    n = out.is_notice & out.transaction_id.notna() & (out.transaction_id != "")
    nn = out[n].sort_values("file_number", ascending=False)
    nn = nn.assign(_dollars=nn.amount.apply(math.floor))
    refiled = nn[nn.duplicated(["committee_id", "candidate_id", "transaction_id", "_dollars", "date"], keep="first")].index
    print(f"  re-filed notices collapsed: {len(refiled)} rows, ${out.loc[refiled, 'amount'].sum():,.0f}")
    return out.drop(index=refiled)


def match_notices(df):
    """Step 2: one-to-one matching of notices to periodic rows of the same committee and candidate.
    Returns df without the matched notices, plus the (notice, periodic) index pairs."""
    pairs = []
    for (cid, cand), g in df.groupby(["committee_id", "candidate_id"]):
        per = g[~g.is_notice]
        if per.empty:
            continue
        used = set()
        notices = g[g.is_notice]
        for rule in ("id", "date"):
            for i, n in notices.iterrows():
                if i in {p[0] for p in pairs}:
                    continue
                cand_rows = per[(~per.index.isin(used)) & ((per.amount - n.amount).abs() <= 1.0)]
                if rule == "id":
                    cand_rows = cand_rows[cand_rows.transaction_id == n.transaction_id]
                else:
                    cand_rows = cand_rows[cand_rows.date == n.date]
                if len(cand_rows):
                    j = cand_rows.index[0]
                    used.add(j)
                    pairs.append((i, j))
    drop = [i for i, _ in pairs]
    def _p(v):
        return "".join(ch for ch in str(v or "").upper() if ch.isalnum())
    diff = sum(_p(df.at[i, "payee"]) != _p(df.at[j, "payee"]) for i, j in pairs)
    print(f"  matched pairs whose payees differ: {diff} of {len(pairs)}")
    print(f"  notices matched to periodic rows and dropped: {len(drop)} rows, ${df.loc[drop, 'amount'].sum():,.0f}")
    return df.drop(index=drop), pairs


def coverage(cid, file_numbers, raw_dir):
    """Coverage window of each periodic file: /committee/<id>/reports/ (processed, amendments included),
    then /efile/filings/ for files not processed yet. Unknown files are left out (their notices are kept)."""
    win, page = {}, 1
    while True:
        j = get(f"/committee/{cid}/reports/", raw_dir, f"reports_{cid}_{page:03d}", cycle=2026, per_page=100, page=page)
        for r in j.get("results", []):
            if r.get("file_number") and r.get("coverage_start_date") and r.get("coverage_end_date"):
                win[int(r["file_number"])] = (r["coverage_start_date"][:10], r["coverage_end_date"][:10])
        if page >= j.get("pagination", {}).get("pages", 0):
            break
        page += 1
    for fn in sorted(set(file_numbers) - set(win)):
        j = get("/efile/filings/", raw_dir, f"efiling_{fn}", file_number=fn, per_page=5)
        for r in j.get("results", []):
            if r.get("coverage_start_date") and r.get("coverage_end_date"):
                win[int(fn)] = (r["coverage_start_date"][:10], r["coverage_end_date"][:10])
    return win


def flag_window_notices(df, raw_dir):
    """Step 3: flag unmatched notices dated inside the coverage window of a periodic file that has rows for
    the same committee and candidate. Returns the flag; see the module docstring for why they are kept."""
    per = df[~df.is_notice & df.file_number.notna()]
    drop = pd.Series(False, index=df.index)
    for cid, grp in per.groupby("committee_id"):
        win = coverage(cid, grp.file_number.astype(int).unique(), raw_dir)
        for cand, g2 in grp.groupby("candidate_id"):
            spans = [win[int(f)] for f in g2.file_number.astype(int).unique() if int(f) in win]
            m = (df.committee_id == cid) & (df.candidate_id == cand) & df.is_notice & df.date.notna()
            for a, b in spans:
                drop |= m & (df.date >= a) & (df.date <= b)
    print(f"  unmatched notices inside a covering periodic report's window: {int(drop.sum())} rows, "
          f"${df.loc[drop, 'amount'].sum():,.0f}")
    return drop


def stage(df):
    by_type = df.election_type.fillna("").str[:1].map({"G": "general", "P": "primary"})
    by_date = df.date.map(lambda d: None if not d else ("general" if d >= GENERAL_START else "primary"))
    clash = by_type.notna() & by_date.notna() & (by_type != by_date)
    if clash.any():
        print(f"  election_type and date disagree on {int(clash.sum())} rows "
              f"(${df.loc[clash, 'amount'].sum():,.0f}); election_type used")
    return by_type.fillna(by_date).fillna("unknown")


def main():
    global FROM_RAW
    if "--from-raw" in sys.argv:          # e.g. --from-raw 20261105T054132Z: rebuild that snapshot's CSVs
        FROM_RAW = True
        stamp = sys.argv[sys.argv.index("--from-raw") + 1]
        raw_dir = OUT / f"raw_{stamp}"
        if not raw_dir.is_dir():
            raise SystemExit(f"no {raw_dir}")
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        raw_dir = OUT / f"raw_{stamp}"
        raw_dir.mkdir(parents=True, exist_ok=False)
    frames = []
    for cid in CANDS:
        p = pull_processed(cid, raw_dir)
        e = pull_efile(cid, raw_dir)
        print(f"{CANDS[cid]}: {len(p)} processed rows, {len(e)} raw-filing rows")
        frames += [pd.DataFrame([norm(x, "processed", cid) for x in p]),
                   pd.DataFrame([norm(x, "efile", cid) for x in e])]
    allr = pd.concat(frames, ignore_index=True)
    step1 = collapse_copies(allr)
    d, pairs = match_notices(step1)
    d = d.reset_index(drop=True)
    d["in_periodic_window"] = flag_window_notices(d, raw_dir)
    d["stage"] = stage(d)
    names = d.dropna(subset=["committee_name"]).groupby("committee_id").committee_name.first()
    d["committee_name"] = d.committee_id.map(names).fillna(d.committee_name)
    print(f"rows: {len(allr)} pulled -> {len(step1)} after memo/superseded/copy removal -> {len(d)} after notice matching; "
          f"stage counts {d.stage.value_counts().to_dict()}")

    g = d[d.stage == "general"].copy()
    g["amount_low"] = g.amount.where(~g.in_periodic_window, 0.0)
    for col in ["amount", "amount_low"]:
        udp = g[(g.committee_id == UDP) & (g.candidate_id == "S6MI00418") & (g.support_oppose == "O")][col].sum()
        print(f"check ({'high' if col == 'amount' else 'low'}): UDP general vs El-Sayed ${udp:,.2f} "
              f"(expected ${UDP_CHECK:,.2f}, 7-29 Oct; any later notices would add to it)")
        if udp + 0.005 < UDP_CHECK:
            raise SystemExit("UDP check failed: less than the plan's 7-29 October total")
    slf, es = "C00571703", "S6MI00418"
    raw = allr[(allr.committee_id == slf) & (allr.candidate_id == es) & (allr.memo_code != "X")].copy()
    raw["file_number"] = pd.to_numeric(raw.file_number, errors="coerce")
    raw = raw[~superseded_mask(raw)]
    raw = raw.drop_duplicates(["file_number", "transaction_id"])
    raw = raw[stage(raw) == "general"]
    win = coverage(slf, raw.loc[~raw.is_notice, "file_number"].dropna().astype(int).unique(), raw_dir)
    last_end = max(b_ for _, b_ in win.values())
    bound = raw.loc[~raw.is_notice, "amount"].sum() + raw.loc[raw.is_notice & (raw.date > last_end), "amount"].sum()
    sg = g[(g.committee_id == slf) & (g.candidate_id == es)]
    lo, hi = sg.amount_low.sum(), sg.amount.sum()
    print(f"check: SLF vs El-Sayed, general: periodic + notices after {last_end} = ${bound:,.2f}; "
          f"low ${lo:,.2f}, high ${hi:,.2f}")
    if not (lo - 1 <= bound <= hi + 1):
        raise SystemExit("SLF check failed: the bound is outside the low-high range")

    by = (g.groupby(["committee_id", "committee_name", "candidate", "support_oppose"], dropna=False)
          .agg(total_high=("amount", "sum"), total_low=("amount_low", "sum"), n=("amount", "size"),
               first=("date", "min"), last=("date", "max"))
          .reset_index().sort_values("total_high", ascending=False))
    rows_f = OUT / f"mi_senate_ie_2026_{stamp}_rows.csv"
    by_f = OUT / f"mi_senate_ie_2026_{stamp}_by_committee.csv"
    d.to_csv(rows_f, index=False)
    by.to_csv(by_f, index=False)
    if not FROM_RAW:
        (raw_dir / "manifest.json").write_text(json.dumps({"retrieved_utc": stamp, "files": MANIFEST}, indent=1, default=str),
                                               encoding="utf-8")

    side = g.assign(side=g.apply(lambda r: "pro-El-Sayed" if (r.candidate == "El-Sayed") == (r.support_oppose == "S")
                                 else "pro-Rogers", axis=1))
    print("general-election IEs since 5 Aug, by side (high):", side.groupby("side").amount.sum().round(0).to_dict())
    print("general-election IEs since 5 Aug, by side (low): ", side.groupby("side").amount_low.sum().round(0).to_dict())
    print("latest expenditure date:", g.date.max())
    print(by.head(12).to_string(index=False))
    print(f"wrote {rows_f}, {by_f}" + ("" if FROM_RAW else f", {raw_dir}/manifest.json"))


if __name__ == "__main__":
    main()
