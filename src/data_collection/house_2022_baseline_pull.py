"""2022 U.S. House baseline for Test C: New Jersey by municipality, Virginia by locality.

Why. Test C (pre-registration, 24 Sep 2026) measures Republican retention as the Republican 2026 Senate vote
as a share of Trump's 2024 vote, against a 2022 baseline: "the total Republican U.S. House vote in each
municipality as a share of Trump's 2020 vote, using only municipalities in districts with both a Democratic
and a Republican House candidate in 2022. Democratic retention defined the same way." This script builds the
2022 House half: Democratic, Republican and all House votes per New Jersey municipality and Virginia
locality, summed across districts where a place is split, on the keys of `same_day_2025_pull.py`'s outputs.

Sources (all 2022; nothing from 2026 is read or downloaded).
- New Jersey: Division of Elections, one PDF per congressional district with one row per municipality,
  grouped in county blocks with a printed total per county and per district
  (`nj.gov/state/elections/assets/pdf/election-results/2022/2022-general-election-results-hor-NN.pdf`; the
  names are the ones listed on `election-information-2022.shtml`, saved with the PDFs). The reconciliation
  source is the Division's "Official List" (`2022-official-general-results-us-house.pdf`), which gives every
  candidate's tally by county. The Division's 2022 "Registered Voters and Ballots Cast" file for each county
  checks every municipality (House votes cannot exceed ballots cast).
- Virginia: the Department of Elections' historical database (elstats), contest CSVs as in
  `same_day_2025_pull.pull_va`. Contest ids were found with the site's own contest search (office "U.S. House",
  2022) and the search response is saved. The reconciliation source is the Department's official results site
  for the 2022 November General (`results.elections.virginia.gov`, pages marked "Official Results", generated
  6 Dec 2022), which publishes each district's results by locality as JSON. ELECT's statewide results CSV
  (`apps.elections.virginia.gov/SBE_CSV/...`) and the FEC's compilation are checked too.

Quirks found (all handled below and reported when the script runs).
- NJ headers wrap candidate names and slogans over several lines ("Tim / Alexander / Democratic", "Progress
  With / Pam"), so the header cannot be read as alternating name and party lines. Columns are read from the
  positions of the header text: each column's text runs downward, and the next column starts higher up.
- NJ rows drop municipal suffixes ("Absecon", "Washington") and misspell some names ("Tavistok", "Mt.
  Ephraim", "Estelle Manor"); one block's total is labelled with the wrong county (NJ-3's Monmouth block ends
  "Ocean Totals").
- NJ-4 prints Point Pleasant Boro's and Point Pleasant Beach Boro's votes under each other's names
  (`NJ_SWAPPED_ROWS`); the labels are swapped back only after the ballots-cast check confirms it.
- NJ federal overseas and court-order rows are not municipalities. They are kept out of the municipal counts
  and enter only the reconciliation, as in `_parse_nj`.
- elstats labels two localities wrongly: Franklin City as "Franklin County" in VA-2 and Richmond City as
  "Richmond County" in VA-4 (the official results give locality codes 620 and 760). Summing by name would
  have merged Richmond City's VA-4 vote into Richmond County.
- elstats's Alexandria row in VA-8 leaves the provisional ballots out of the candidate columns (but not out of
  its total); its own precinct rows and the official results include them, and the official figures are used.
  Other localities' precinct rows are incomplete, so precinct rows are never used.
- elstats write-ins differ from the official results page by a few votes in most localities. All votes are
  elstats's Total Votes Cast, which equals the FEC's district totals in 10 of 11 districts (VA-11: +24).

Output (one row per municipality or locality, on the same-day files' keys): Democratic, Republican and all
House votes summed over the place's districts; the districts and each district part; flags.
`data/raw/same_day_2025/house22_nj_by_municipality.csv` (key, county) and `house22_va_by_locality.csv`
(locality).
"""

from pathlib import Path
import json
import re
import subprocess
import sys
import time

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from same_day_2025_pull import _norm, _align, NUM, NON_GEO, NJ_COUNTIES  # noqa: E402

RAW = Path("data/raw/house_2022")
NJ_DIR, VA_DIR, VA_ENR_DIR, VA_CSV_DIR = RAW / "nj", RAW / "va_elstats", RAW / "va_enr", RAW / "va_elect_csv"
NJ_BALLOTS_DIR = RAW / "nj_ballotscast"
OUT = Path("data/raw/same_day_2025")
FEC_2022 = Path("data/raw/fec_results/federalelections2022.xlsx")   # saved by fec_primary_turnout_pull.py

NJ_PAGE = "https://www.nj.gov/state/elections/election-information-2022.shtml"
NJ_BASE = "https://www.nj.gov/state/elections/assets/pdf/election-results/2022"
NJ_DISTRICTS = range(1, 13)
NJ_DISTRICT_PDF = "2022-general-election-results-hor-{:02d}.pdf"
NJ_SUMMARY_PDF = "2022-official-general-results-us-house.pdf"
NJ_BALLOTS_PDF = "2022-official-general-result-ballotscast-{}.pdf"     # registered voters and ballots cast
# Rows printed under each other's names in a district PDF. NJ-4 prints Point Pleasant Boro's votes (8,119)
# against "Point Pleasant Beach Boro" and Point Pleasant Beach's (1,974) against "Point Pleasant Boro": the
# Division's ballots-cast file has 8,301 ballots in the borough and 2,014 in Point Pleasant Beach, so the
# printed labels give Point Pleasant Beach four times more House votes than ballots. pull_nj swaps the labels
# only after re-checking exactly this against the ballots-cast file, and flags both rows.
NJ_SWAPPED_ROWS = {4: [("ocean", "Point Pleasant Boro", "Point Pleasant Beach Boro")]}

VA_HOUSE22 = {1: 156400, 2: 156315, 3: 156722, 4: 156380, 5: 156345, 6: 156348, 7: 156343, 8: 156358,
              9: 156364, 10: 156422, 11: 156424}
VA_CSV = "https://va2.elstats.civera.com/api/download_contest/{}_table.csv?split_party=false"
VA_CONTEST_PAGE = "https://historical.elections.virginia.gov/contest/{}"
VA_GRAPHQL = "https://historical.elections.virginia.gov/api/graphql_pr"
VA_SEARCH = {"query": "query SearchContests($pagination: Pagination!, $filters: SearchFilters!) { search("
                      "pagination: $pagination, filters: $filters) { meta { totalResults } results { id isSpecial "
                      "eventTypeDisplayName office { id name } division { displayName } event { id startDate } "
                      "candidates { displayName nVotes isWriteIn party { name } } } } }",
             "variables": {"pagination": {"page": 1, "size": 96},
                           "filters": {"global": {"years": {"from": 2022, "to": 2022}}, "ballotQuestions": None,
                                       "contests": {"candidates": [], "divisions": [], "offices": [{"id": 5}]},
                                       "specialElectionsOnly": False, "voterStats": False, "stages": []}}}
VA_ENR = "https://results.elections.virginia.gov/vaelections/2022%20November%20General"
VA_ENR_JSON = "Member_House_of_Representatives_({:02d}).json"
VA_ELECT_CSV = ("https://apps.elections.virginia.gov/SBE_CSV/ELECTIONS/ELECTIONRESULTS/2022/"
                "2022%20November%20General.csv")


def _fetch(url, dest, magic=None, data=None, headers=()):
    """Download once with curl and never overwrite: -f makes an HTTP error fail instead of saving the
    error page, and the file is checked for its expected leading bytes before it is kept."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    cmd = ["curl", "-s", "-f", "-L", "-A", "Mozilla/5.0", url, "-o", str(tmp)]
    for h in headers:
        cmd += ["-H", h]
    if data is not None:
        cmd += ["-X", "POST", "--data-binary", data]
    subprocess.run(cmd, check=True)
    head = tmp.read_bytes()[:len(magic)] if magic else b""
    if magic and head != magic:
        tmp.unlink()
        raise ValueError(f"{url}: expected a file starting {magic!r}, got {head!r}")
    tmp.rename(dest)
    time.sleep(0.3)
    return dest


def download():
    _fetch(NJ_PAGE, NJ_DIR / "election-information-2022.shtml")
    for n in NJ_DISTRICTS:
        _fetch(f"{NJ_BASE}/{NJ_DISTRICT_PDF.format(n)}", NJ_DIR / NJ_DISTRICT_PDF.format(n), magic=b"%PDF")
    _fetch(f"{NJ_BASE}/{NJ_SUMMARY_PDF}", NJ_DIR / NJ_SUMMARY_PDF, magic=b"%PDF")
    for c in NJ_COUNTIES:
        _fetch(f"{NJ_BASE}/{NJ_BALLOTS_PDF.format(c)}", NJ_BALLOTS_DIR / NJ_BALLOTS_PDF.format(c), magic=b"%PDF")
    _fetch(VA_GRAPHQL, VA_DIR / "contest_search_2022_us_house.json", magic=b'{"data"',
           data=json.dumps(VA_SEARCH), headers=("Content-Type: application/json", "X-Elstats-Tenant: va2"))
    for n, cid in VA_HOUSE22.items():
        _fetch(VA_CSV.format(cid), VA_DIR / f"va_house22_cd{n:02d}_{cid}.csv")
        _fetch(VA_CONTEST_PAGE.format(cid), VA_DIR / f"contest_{cid}.html")
    _fetch(f"{VA_ENR}/Site/Congress.html", VA_ENR_DIR / "Congress.html")
    for n in VA_HOUSE22:
        _fetch(f"{VA_ENR}/Json/{VA_ENR_JSON.format(n)}", VA_ENR_DIR / VA_ENR_JSON.format(n), magic=b"{")
    _fetch(VA_ELECT_CSV, VA_CSV_DIR / "2022 November General.csv")


def _check(label, ok, detail, diagnostic=False):
    """Print one reconciliation check. Diagnostic checks describe a source and do not decide the output
    (they print ok/MISMATCH); the others print PASS/FAIL and must all pass."""
    mark = ("ok" if ok else "MISMATCH") if diagnostic else ("PASS" if ok else "FAIL")
    print(f"  [{mark}] {label}: {detail}")
    return ok


def _parts(g, district_col):
    """'NJ-4: D 1,011 R 442 T 1,475; ...' for each district part of a place."""
    return "; ".join(f"{r[district_col]}: D {r.dem:,.0f} R {r.rep:,.0f} T {r.total:,.0f}" for _, r in g.iterrows())


# =============================================== New Jersey ===============================================

NJ_COUNTY_NAMES = ["Atlantic", "Bergen", "Burlington", "Camden", "Cape May", "Cumberland", "Essex", "Gloucester",
                   "Hudson", "Hunterdon", "Mercer", "Middlesex", "Monmouth", "Morris", "Ocean", "Passaic", "Salem",
                   "Somerset", "Sussex", "Union", "Warren"]
COUNTY_RE = re.compile(rf"^({'|'.join(NJ_COUNTY_NAMES)}) County$")
FOOTER_RE = re.compile(r"^(Page \d+|NJDOE.*|\d{1,2}/\d{1,2}/\d{4}.*)$")
NON_GEO_H = re.compile(NON_GEO.pattern + r"|court order", re.I)      # Atlantic in NJ-2 has a "Court Order" row
DISTRICT_TOTAL_RE = re.compile(r"^District( \d+)? Totals$")
SUFFIXES = ("boro", "twp", "city", "town", "village", "villagetwp")


def _ckey(name):
    return name.lower().replace(" ", "")          # "Cape May" -> "capemay", as NJ_COUNTIES


def _nj_header(page):
    """(district, column labels, column parties) for one page, read from the header text's positions.

    In content order the header runs column by column, each column's lines going down the page, so a line
    printed higher than the one before it starts a new column. The columns' left edges must then run left
    to right; anything else stops the run."""
    items = []
    page.extract_text(visitor_text=lambda t, cm, tm, fd, fs: items.append((tm[4], tm[5], t.strip()))
                      if t.strip() else None)
    i0 = next(i for i, it in enumerate(items) if it[2].startswith("Congressional District"))
    district = int(re.search(r"\d+", items[i0][2]).group())
    i1 = next(i for i, it in enumerate(items) if i > i0 and COUNTY_RE.match(it[2]))
    cols, prev = [], None
    for x, y, t in items[i0 + 1:i1]:
        if prev is None or y > prev + 0.5:
            cols.append([])
        cols[-1].append((x, t))
        prev = y
    lefts = [min(x for x, _ in c) for c in cols]
    if lefts != sorted(lefts):
        raise ValueError(f"NJ-{district}: header columns out of order {lefts}")
    labels = tuple(" ".join(t for _, t in c) for c in cols)
    parties = tuple("D" if any(t == "Democratic" for _, t in c) else "R" if any(t == "Republican" for _, t in c)
                    else "other" for c in cols)
    return district, labels, parties


def parse_nj_district(pdf):
    """Municipality rows of one district PDF, each county block reconciled to its printed county total.

    Returns (rows, blocks, district, labels, parties, district_total). `rows` has one row per municipality
    with every candidate column. Rows that are not municipalities (federal overseas, court order) are set
    aside: complete ones are assigned to their columns, incomplete ones (blank cells omitted) go to an
    unassigned pool, and the county check allows each column a gap no larger than that pool, as `_parse_nj`
    does."""
    from pypdf import PdfReader
    header, blocks, cur, pending, district_total = None, [], None, "", None
    for page in PdfReader(pdf).pages:
        h = _nj_header(page)
        if header is None:
            header = h
        elif h != header:
            raise ValueError(f"{pdf}: header differs between pages: {h} vs {header}")
        k = len(header[1])
        lines = [l.strip() for l in (page.extract_text() or "").split("\n") if l.strip()]
        start = next(i for i, l in enumerate(lines) if COUNTY_RE.match(l))
        for l in lines[start:]:
            m = COUNTY_RE.match(l)
            if m:
                if pending:
                    raise ValueError(f"{pdf}: dangling name {pending!r} before {l!r}")
                cur = {"county": _ckey(m.group(1)), "rows": [], "nongeo": [], "partial": [], "printed": None,
                       "label": None}
                blocks.append(cur)
                continue
            if FOOTER_RE.match(l):
                continue
            toks = l.split()
            nums = []
            while toks and NUM.match(toks[-1]):
                nums.insert(0, int(toks.pop().replace(",", "")))
            own = " ".join(toks)
            if not nums:
                if NON_GEO_H.search(own):         # an empty non-geographic row must not prefix the next name
                    continue
                pending = (pending + " " + own).strip()
                continue
            if own.endswith("Totals"):
                if pending:
                    raise ValueError(f"{pdf}: dangling name {pending!r} before {l!r}")
                if len(nums) != k:
                    raise ValueError(f"{pdf}: {len(nums)} numbers for {k} candidates in {l!r}")
                if DISTRICT_TOTAL_RE.match(own):
                    district_total = nums
                    cur = None
                else:
                    if cur is None or cur["printed"] is not None:
                        raise ValueError(f"{pdf}: county total outside an open county block: {l!r}")
                    cur["printed"], cur["label"] = nums, own[:-len(" Totals")]
                continue
            name = (pending + " " + own).strip()
            pending = ""
            if cur is None or cur["printed"] is not None:
                raise ValueError(f"{pdf}: row outside an open county block: {l!r}")
            if NON_GEO_H.search(name):
                (cur["nongeo"] if len(nums) == k else cur["partial"]).append((name, nums))
                continue
            if len(nums) != k:
                raise ValueError(f"{pdf}: {len(nums)} numbers for {k} candidates in {l!r}")
            cur["rows"].append((name, nums))
    district, labels, parties = header
    if district_total is None:
        raise ValueError(f"{pdf}: no printed district total")
    for b in blocks:
        if b["printed"] is None:
            raise ValueError(f"{pdf}: {b['county']} block has no printed total")
        known = [sum(r[1][j] for r in b["rows"] + b["nongeo"]) for j in range(len(labels))]
        gaps = [p - kn for p, kn in zip(b["printed"], known)]
        b["unassigned"] = sum(sum(n) for _, n in b["partial"])
        b["gaps"] = gaps
        b["ok"] = all(g >= 0 for g in gaps) and sum(gaps) == b["unassigned"]
    rows = []
    for b in blocks:
        for name, nums in b["rows"]:
            rec = {"district": district, "county": b["county"], "municipality": name,
                   "dem": nums[parties.index("D")] if "D" in parties else None,
                   "rep": nums[parties.index("R")] if "R" in parties else None,
                   "total": sum(nums)}
            rows.append(rec)
    return pd.DataFrame(rows), blocks, district, labels, parties, district_total


ORDINALS = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth",
            "Eleventh", "Twelfth"]


def parse_nj_official_list(pdf):
    """The Division's Official List: {district: {"county": {(county, party): votes}, "cand": [(party, total)],
    "total": district total}} for the Democratic and Republican lines (party D/R) and every candidate total."""
    from pypdf import PdfReader
    text = "\n".join(p.extract_text() or "" for p in PdfReader(pdf).pages)
    out, d = {}, None
    county_line = re.compile(rf"^({'|'.join(c.upper() for c in NJ_COUNTY_NAMES)}) (DEMOCRATIC|REPUBLICAN) ([\d,]+)$")
    for l in (x.strip() for x in text.split("\n")):
        m = re.match(rf"^({'|'.join(ORDINALS)}) Congressional District:", l)
        if m:
            d = ORDINALS.index(m.group(1)) + 1
            out.setdefault(d, {"county": {}, "cand": [], "total": None})
            continue
        if d is None:
            continue
        m = county_line.match(l)
        if m:
            key = (_ckey(m.group(1).title()), m.group(2)[0])
            out[d]["county"][key] = out[d]["county"].get(key, 0) + int(m.group(3).replace(",", ""))
            continue
        m = re.match(r"^Total ([\d,]+)$", l)
        if m:
            out[d]["cand"].append(int(m.group(1).replace(",", "")))
            continue
        m = re.match(r"^([\d,]+)Total$", l)
        if m:
            out[d]["total"] = int(m.group(1).replace(",", ""))
    return out


def _alnum(s):
    return re.sub(r"[^a-z0-9]", "", s)


def match_keys(keys, reference):
    """Map 2022 municipality keys onto the same-day file's keys for one county.

    Passes, in order: (1) exact; (2) equal after dropping punctuation ("peapackgladstone" /
    "peapack&gladstoneboro" needs pass 3 as well); (3) the 2022 name plus a municipal suffix
    ("absecon" -> "abseconcity"), taking the single candidate, or if several, the single one no 2022 name
    matched exactly ("clinton" -> "clintontown" because "Clinton Twp" is printed too); (4) `_align`
    (unique stem, then close spelling: "tavistokboro" -> "tavistockboro"); (5) close spelling once a suffix
    is added, if exactly one key qualifies ("estellemanor" -> "estellmanorcity"). Returns {key: (ref, pass)}."""
    import difflib
    ref = list(dict.fromkeys(reference))
    out = {}
    exact = {k for k in keys if k in ref}
    for k in keys:
        if k in exact:
            out[k] = (k, "exact")
    for k in keys:
        if k in out:
            continue
        hit = [r for r in ref if _alnum(r) == _alnum(k)]
        if len(hit) == 1:
            out[k] = (hit[0], "punctuation")
            continue
        hit = [r for r in ref if any(_alnum(k) + s == _alnum(r) for s in SUFFIXES)]
        if len(hit) > 1:
            hit = [r for r in hit if r not in exact]
        if len(hit) == 1:
            out[k] = (hit[0], "name + suffix")
    left = [k for k in keys if k not in out]
    if left:
        used = {v[0] for v in out.values()}
        for k, r in _align(left, [r for r in ref if r not in used]).items():
            out[k] = (r, "stem or close spelling")
    left = [k for k in keys if k not in out]
    if left:
        used = {v[0] for v in out.values()}
        pool = [r for r in ref if r not in used]
        for k in left:
            hits = {h for s in SUFFIXES for h in difflib.get_close_matches(k + s, pool, n=1, cutoff=0.9)}
            if len(hits) == 1:
                out[k] = (hits.pop(), "close spelling + suffix")
                pool.remove(out[k][0])
    return out


BALLOTS_ROW = re.compile(r"^(.*?)\s+([\d,]+)\s+([\d,]+)\s+(\d+)\s*%\s+([\d,]+)\s+([\d,]+)$")


def parse_nj_ballots(pdf):
    """The Division's registered voters and ballots cast by municipality for one county (2022 general).

    Returns (municipal rows, printed county total of ballots cast, ballots in non-municipal rows)."""
    from pypdf import PdfReader
    lines = [l.strip() for p in PdfReader(pdf).pages for l in (p.extract_text() or "").split("\n") if l.strip()]
    rows, total, other = [], None, 0
    for l in lines:
        m = BALLOTS_ROW.match(l)
        if m:
            vals = [int(m.group(i).replace(",", "")) for i in (2, 3, 5, 6)]
            if m.group(1).upper() == "COUNTY TOTAL":
                total = vals[1]
            else:
                rows.append({"municipality": m.group(1), "registered": vals[0], "ballots": vals[1]})
        elif NON_GEO_H.search(l) and NUM.match(l.split()[-1]):
            other += int(l.split()[-1].replace(",", ""))          # "Federal Overseas 76 76": ballots last
    return pd.DataFrame(rows), total, other


def pull_nj():
    print("\n=== New Jersey: 2022 U.S. House by municipality ===")
    page = (NJ_DIR / "election-information-2022.shtml").read_text(encoding="utf-8", errors="replace")
    missing = [NJ_DISTRICT_PDF.format(n) for n in NJ_DISTRICTS if NJ_DISTRICT_PDF.format(n) not in page]
    names_ok = _check("file names listed on nj.gov's 2022 page", not missing and NJ_SUMMARY_PDF in page,
                      f"12 district files + {NJ_SUMMARY_PDF}" + (f"; missing {missing}" if missing else ""))
    official = parse_nj_official_list(NJ_DIR / NJ_SUMMARY_PDF)
    fec = _fec_house("NJ")
    frames, kept, dropped, all_ok, excluded = [], [], [], names_ok, []
    for n in NJ_DISTRICTS:
        rows, blocks, district, labels, parties, dtot = parse_nj_district(NJ_DIR / NJ_DISTRICT_PDF.format(n))
        if district != n:
            raise ValueError(f"{NJ_DISTRICT_PDF.format(n)} is headed District {district}")
        print(f"NJ-{n}: " + " | ".join(f"{lab} [{p}]" for lab, p in zip(labels, parties)))
        has_dr = parties.count("D") == 1 and parties.count("R") == 1
        if not has_dr:
            print(f"  NJ-{n} lacks a Democratic or a Republican candidate: dropped")
            dropped.append(n)
        else:
            kept.append(n)
        d_col, r_col = (parties.index("D"), parties.index("R")) if has_dr else (None, None)
        for b in blocks:
            lab = "" if b["label"] == next(c for c in NJ_COUNTY_NAMES if _ckey(c) == b["county"]) else \
                f" (printed total labelled '{b['label']} Totals')"
            extra = f"; non-municipal rows {[(nm, v) for nm, v in b['nongeo'] + b['partial']]}" \
                if b["nongeo"] or b["partial"] else ""
            all_ok &= _check(f"NJ-{n} {b['county']}: {len(b['rows'])} municipalities + non-municipal rows = "
                             f"printed county total{lab}", b["ok"],
                             f"printed {b['printed']}, gap by column {b['gaps']}, unassigned {b['unassigned']}{extra}")
            if b["nongeo"] or b["partial"]:
                # once the block reconciles, its gap by column is exactly where the incomplete rows' votes went
                excluded.append({"district": n, "county": b["county"],
                                 "dem": sum(v[d_col] for _, v in b["nongeo"]) + b["gaps"][d_col] if has_dr else None,
                                 "rep": sum(v[r_col] for _, v in b["nongeo"]) + b["gaps"][r_col] if has_dr else None,
                                 "unassigned": b["unassigned"],
                                 "total": sum(sum(v) for _, v in b["nongeo"] + b["partial"])})
        csum = [sum(b["printed"][j] for b in blocks) for j in range(len(labels))]
        all_ok &= _check(f"NJ-{n}: county totals sum to the printed district total", csum == dtot,
                         f"sum {csum} vs printed {dtot}")
        o = official.get(n)
        if o is None:
            all_ok &= _check(f"NJ-{n}: in the Official List", False, "district not found")
        else:
            # the Official List orders candidates its own way, so the column totals are compared as a set;
            # which column is D and which is R is checked county by county just below
            all_ok &= _check(f"NJ-{n}: candidate totals equal the Official List's (any order)",
                             sorted(o["cand"]) == sorted(dtot) and o["total"] == sum(dtot),
                             f"PDF {dtot} (sum {sum(dtot):,}) vs official {o['cand']} (district total {o['total']:,})")
            if has_dr:
                bad = []
                for b in blocks:
                    for p, j in (("D", d_col), ("R", r_col)):
                        if o["county"].get((b["county"], p)) != b["printed"][j]:
                            bad.append((b["county"], p, b["printed"][j], o["county"].get((b["county"], p))))
                n_cells = 2 * len(blocks)
                all_ok &= _check(f"NJ-{n}: D and R county totals (columns read from the header) equal the "
                                 f"Official List's county tallies", not bad and len(o["county"]) == n_cells,
                                 f"{n_cells} county x party cells" + (f"; mismatches {bad}" if bad else "")
                                 + ("" if len(o["county"]) == n_cells else f"; official has {len(o['county'])}"))
        if has_dr and fec is not None:
            f = fec[fec.district == n]
            fd, fr, ft = f[f.party == "D"].votes.sum(), f[f.party == "R"].votes.sum(), f.votes.sum()
            all_ok &= _check(f"NJ-{n}: D, R and all votes equal the FEC compilation",
                             (fd, fr, ft) == (dtot[d_col], dtot[r_col], sum(dtot)),
                             f"PDF {dtot[d_col]:,} / {dtot[r_col]:,} / {sum(dtot):,} vs FEC {fd:,} / {fr:,} / {ft:,}")
        rows["district_ok"] = has_dr
        frames.append(rows)
    allrows = pd.concat(frames, ignore_index=True)
    allrows["district_no"] = allrows.district
    allrows["district"] = "NJ-" + allrows.district.astype(str)
    allrows["raw_key"] = allrows.municipality.map(_norm)
    allrows["row_flag"] = ""
    ex = pd.DataFrame(excluded)
    print(f"Non-municipal rows (federal overseas, court order) left out of the municipal counts: "
          f"D {ex.dem.sum():,.0f}, R {ex.rep.sum():,.0f}, all {ex.total.sum():,.0f} votes "
          f"({ex.unassigned.sum():,} of them in rows with blank columns omitted)")

    # ---- match to same_day_2025's municipality keys, county by county ----
    ref = pd.read_csv(OUT / "nj_municipalities.csv", usecols=["key", "county", "gov21_total", "pres20_total"])
    allrows["key"] = None
    allrows["match"] = None
    unmatched = []
    for county, g in allrows.groupby("county"):
        refkeys = ref.loc[ref.county == county, "key"].tolist()
        m = match_keys(list(dict.fromkeys(g.raw_key)), refkeys)
        idx = g.index
        allrows.loc[idx, "key"] = g.raw_key.map(lambda k: m.get(k, (None, None))[0])
        allrows.loc[idx, "match"] = g.raw_key.map(lambda k: m.get(k, (None, None))[1])
        for k, (r, how) in m.items():
            if how not in ("exact", "name + suffix"):
                names = sorted(set(g.loc[g.raw_key == k, "municipality"]))
                print(f"  {county}: {names} -> {r} ({how})")
        unmatched += [(county, k) for k in dict.fromkeys(g.raw_key) if k not in m]
    n_suffix = allrows.match.eq("name + suffix").sum()
    all_ok &= _check("every 2022 municipality row matches a same-day key", not unmatched,
                     f"{allrows.key.notna().sum()} of {len(allrows)} rows ({n_suffix} by adding the municipal "
                     f"suffix the 2022 file drops; the others above)" + (f"; unmatched {unmatched}" if unmatched else ""))
    allrows["key"] = allrows.key.fillna(allrows.raw_key)       # unmatched rows are kept under their own key

    # ---- ballots cast by municipality (the Division's 2022 file), on the same keys ----
    bal, bad_bal = [], []
    for county in NJ_COUNTIES:
        b, printed, other = parse_nj_ballots(NJ_BALLOTS_DIR / NJ_BALLOTS_PDF.format(county))
        # Camden's file spells one name "Voorhees Townsip"
        b["raw_key"] = b.municipality.map(lambda s: _norm(re.sub(r"(?i)\btownsip\b", "Township", s)))
        m = match_keys(list(b.raw_key), ref.loc[ref.county == county, "key"].tolist())
        for k, (r, how) in m.items():
            if how not in ("exact", "name + suffix", "punctuation"):
                print(f"  ballots-cast {county}: {k} -> {r} ({how})")
        b["key"] = b.raw_key.map(lambda k: m.get(k, (None, None))[0])
        b["county"] = county
        if b.key.isna().any() or b.key.duplicated().any() or printed != b.ballots.sum() + other:
            bad_bal.append((county, b.loc[b.key.isna(), "municipality"].tolist(), printed, b.ballots.sum(), other))
        bal.append(b)
    bal = pd.concat(bal, ignore_index=True)
    _check("ballots-cast files: every municipality matched once, and municipalities + federal rows = printed "
           "county total", not bad_bal, f"{bal.key.notna().sum()} municipalities in 21 counties"
           + (f"; problems {bad_bal}" if bad_bal else ""), diagnostic=True)
    ballots = bal.dropna(subset=["key"]).set_index(["county", "key"]).ballots

    # ---- rows printed under each other's names (NJ_SWAPPED_ROWS), confirmed against ballots cast ----
    for n, swaps in NJ_SWAPPED_ROWS.items():
        for county, a, b in swaps:
            ia = allrows.index[(allrows.district_no == n) & (allrows.county == county) & (allrows.municipality == a)]
            ib = allrows.index[(allrows.district_no == n) & (allrows.county == county) & (allrows.municipality == b)]
            if len(ia) != 1 or len(ib) != 1:
                raise ValueError(f"NJ-{n} {county}: rows {a!r} / {b!r} not found once each")
            ia, ib = ia[0], ib[0]
            ka, kb = allrows.at[ia, "key"], allrows.at[ib, "key"]
            other_a = allrows.loc[(allrows.key == ka) & (allrows.county == county) & (allrows.index != ia), "total"].sum()
            other_b = allrows.loc[(allrows.key == kb) & (allrows.county == county) & (allrows.index != ib), "total"].sum()
            ta, tb, ba, bb = allrows.at[ia, "total"], allrows.at[ib, "total"], ballots[(county, ka)], ballots[(county, kb)]
            as_printed = other_a + ta <= ba and other_b + tb <= bb
            swapped = other_a + tb <= ba and other_b + ta <= bb
            ok = _check(f"NJ-{n} {county}: '{a}' and '{b}' printed under each other's names", (not as_printed)
                        and swapped, f"as printed, House votes {ta + other_a:,} vs {ba:,} ballots and "
                        f"{tb + other_b:,} vs {bb:,}; swapped, {tb + other_a:,} vs {ba:,} and {ta + other_b:,} vs {bb:,}")
            if not ok:
                raise ValueError(f"NJ-{n} {county}: the ballots-cast file does not support swapping {a!r} and {b!r}")
            cols3 = ["dem", "rep", "total"]
            va_, vb_ = allrows.loc[ia, cols3].copy(), allrows.loc[ib, cols3].copy()
            allrows.loc[ia, cols3], allrows.loc[ib, cols3] = vb_.values, va_.values
            for i, them, mine in ((ia, b, vb_), (ib, a, va_)):
                allrows.at[i, "row_flag"] = (f"NJ-{n} prints this municipality's votes (D {mine.dem:,}, R {mine.rep:,}, "
                                             f"all {mine.total:,}) against '{them}'; labels swapped after the "
                                             f"ballots-cast check")
            all_ok &= ok

    # ---- sum across districts, flag split places and places touching a dropped district ----
    out = []
    for (county, key), g in allrows.groupby(["county", "key"], sort=False):
        ok = g[g.district_ok]
        bad = g[~g.district_ok]
        flags = [x for x in g.row_flag if x]
        if len(bad) and len(ok):
            flags.append("partly in a district without both a D and an R candidate: " + ", ".join(bad.district))
        elif len(bad):
            flags.append("only in a district without both a D and an R candidate: " + ", ".join(bad.district))
        nonexact = g[~g.match.isin(["exact", "name + suffix"])]
        if len(nonexact):
            flags.append("2022 name " + ", ".join(f"'{nm}'" for nm in sorted(set(nonexact.municipality)))
                         + " matched by " + ", ".join(sorted(set(nonexact.match.fillna("no match")))))
        if (county, key) in [(c, k) for c, k in unmatched]:
            flags.append("no matching key in nj_municipalities.csv")
        out.append({"key": key, "county": county,
                    "municipality_2022": "; ".join(dict.fromkeys(g.municipality)),
                    "house22_dem": ok.dem.sum() if len(ok) else None,
                    "house22_rep": ok.rep.sum() if len(ok) else None,
                    "house22_total": ok.total.sum() if len(ok) else None,
                    "house22_districts": ";".join(dict.fromkeys(g.district)),
                    "house22_split": g.district.nunique() > 1,
                    "house22_parts": _parts(g, "district"),
                    "partly_in_dropped_district": bool(len(bad) and len(ok)),
                    "house22_flags": " | ".join(flags)})
    nj = pd.DataFrame(out)
    split = nj[nj.house22_split]
    print(f"Municipalities split between districts ({len(split)}):")
    for _, r in split.iterrows():
        print(f"  {r.county} {r.key}: {r.house22_parts}")
    print(f"Districts dropped (no D or no R): {dropped or 'none'}; municipalities partly in one: "
          f"{nj.partly_in_dropped_district.sum()}")

    # ---- statewide checks and the join to the same-day file ----
    kept_rows = allrows[allrows.district_ok]
    for c, p in (("dem", "D"), ("rep", "R")):
        off = sum(official[d]["county"].get((cty, p), 0) for d in kept for cty in
                  {k[0] for k in official[d]["county"]})
        mun = kept_rows[c].sum()
        exc = ex.loc[ex.district.isin(kept), c].sum()
        all_ok &= _check(f"statewide {p}: municipal sum + non-municipal rows = Official List",
                         mun + exc == off, f"{mun:,} + {exc:,.0f} = {mun + exc:,.0f} vs official {off:,}")
    j = nj.merge(ref, on=["county", "key"], how="outer", indicator=True)
    only22, only25 = j[j._merge == "left_only"], j[j._merge == "right_only"]
    all_ok &= _check("join to nj_municipalities.csv on (county, key)", only22.empty and only25.empty,
           f"{(j._merge == 'both').sum()} matched; only in 2022 file {only22[['county', 'key']].values.tolist()}; "
           f"only in same-day file {only25[['county', 'key']].values.tolist()}")
    both = j[j._merge == "both"].copy()
    both["ratio_gov21"] = both.house22_total / both.gov21_total
    odd = both[(both.ratio_gov21 < 0.6) | (both.ratio_gov21 > 1.6)]
    print(f"Plausibility: 2022 House votes / 2021 governor votes, median {both.ratio_gov21.median():.3f}, "
          f"range {both.ratio_gov21.min():.3f}-{both.ratio_gov21.max():.3f}; outside 0.6-1.6: "
          f"{odd[['county', 'key', 'house22_total', 'gov21_total']].values.tolist() or 'none'}")
    nj["ballots_cast22"] = [ballots.get((c, k)) for c, k in zip(nj.county, nj.key)]
    share = nj.house22_total / nj.ballots_cast22
    over = nj[share > 1]
    all_ok &= _check("every municipality: 2022 House votes <= ballots cast (Division's ballots-cast file)",
                     over.empty and nj.ballots_cast22.notna().all(),
                     f"House votes / ballots cast: median {share.median():.3f}, range {share.min():.3f}-{share.max():.3f}"
                     + (f"; over 1: {over[['county', 'key', 'house22_total', 'ballots_cast22']].values.tolist()}"
                        if len(over) else "") + (f"; no ballots figure for {nj.loc[nj.ballots_cast22.isna(), 'key'].tolist()}"
                                                 if nj.ballots_cast22.isna().any() else ""))
    low = nj.assign(share=share).nsmallest(5, "share")
    print("  lowest House votes / ballots cast: " + "; ".join(
        f"{r.county} {r.key} {r.share:.3f} ({r.house22_total:,.0f} of {r.ballots_cast22:,.0f})" for _, r in low.iterrows()))
    cols = ["key", "county", "municipality_2022", "house22_dem", "house22_rep", "house22_total", "ballots_cast22",
            "house22_districts", "house22_split", "house22_parts", "partly_in_dropped_district", "house22_flags"]
    nj = nj[cols].sort_values(["county", "key"]).reset_index(drop=True)
    for c in ["house22_dem", "house22_rep", "house22_total"]:
        nj[c] = nj[c].astype("Int64")
    nj.to_csv(OUT / "house22_nj_by_municipality.csv", index=False)
    print(f"NJ: {len(nj)} municipalities written; D {nj.house22_dem.sum():,} R {nj.house22_rep.sum():,} "
          f"all {nj.house22_total.sum():,}; all checks {'passed' if all_ok else 'DID NOT ALL PASS'}")
    return nj, all_ok


# ================================================ Virginia ================================================

def _fec_house(state):
    """FEC compilation of 2022 House general results (federalelections2022.xlsx), one row per candidate."""
    if not FEC_2022.exists():
        print(f"  (FEC file {FEC_2022} not found: FEC check skipped)")
        return None
    f = pd.read_excel(FEC_2022, sheet_name="8. US House Results by State", dtype=str)
    f = f[(f["STATE ABBREVIATION"] == state) & f["GENERAL VOTES "].notna() & f["CANDIDATE NAME"].notna()
          & f["DISTRICT"].str.fullmatch(r"\d+", na=False)].copy()
    f["district"] = f.DISTRICT.astype(int)
    f["votes"] = pd.to_numeric(f["GENERAL VOTES "].str.replace(",", "")).astype(int)
    f["party"] = f.PARTY.str.strip()
    return f[["district", "CANDIDATE NAME", "party", "votes"]]


def _vnorm(name):
    """Locality name as an upper-case key: 'King & Queen County' and 'King and Queen County' agree."""
    return re.sub(r"\s+", " ", name.upper().replace("&", "AND")).strip()


def _elstats(f):
    """One elstats contest CSV: district number, column roles and its Locality rows (as pull_va reads them)."""
    raw = pd.read_csv(f, header=None, dtype=str)
    names, parties = raw.iloc[0].tolist(), raw.iloc[1].tolist()
    roles = {}
    for j, (nm, p) in enumerate(zip(names, parties)):
        if j < 2:
            continue
        roles[j] = ("dem" if p == "Democratic" else "rep" if p == "Republican" else "total" if nm == "Total Votes Cast"
                    else "writein" if nm == "Write-Ins" else "undervotes" if nm == "Undervotes" else f"other:{p}:{nm}")
    num = raw.iloc[2:].copy()
    for j in roles:
        num[j] = num[j].fillna("0").str.replace(",", "").astype(int)
    district = int(num.loc[num[0] == "Congressional District", 1].iloc[0])
    loc = num[num[0] == "Locality"].rename(columns={1: "locality", **roles})
    dist_row = num[num[0] == "Congressional District"].rename(columns=roles)
    return district, names, parties, roles, loc, dist_row, num


def _enr(n):
    """Official results by locality for district n, from the Department of Elections' results site."""
    j = json.loads((VA_ENR_DIR / VA_ENR_JSON.format(n)).read_text(encoding="utf-8-sig"))
    rows = []
    for L in j["Localities"]:
        rec = {"enr_name": L["Locality"]["LocalityName"], "code": L["Locality"]["LocalityCode"]}
        for c in L["Candidates"]:
            p = c["PoliticalParty"]
            key = {"Democratic": "dem", "Republican": "rep", "Write-In": "writein"}.get(p, f"other:{p}")
            rec[key] = rec.get(key, 0) + int(c["Votes"])
        rows.append(rec)
    return j, pd.DataFrame(rows)


def pull_va():
    print("\n=== Virginia: 2022 U.S. House by locality ===")
    all_ok = True
    # contest ids as the site's own search returns them
    s = json.loads((VA_DIR / "contest_search_2022_us_house.json").read_text(encoding="utf-8"))["data"]["search"]
    gen = {int(r["division"]["displayName"].split()[-1]): int(r["id"]) for r in s["results"]
           if r["eventTypeDisplayName"] == "General Election" and r["event"]["startDate"].startswith("2022-11-08")
           and r["office"]["name"] == "U.S. House" and not r["isSpecial"]}
    all_ok &= _check("elstats contest search: 2022 general-election U.S. House ids", gen == VA_HOUSE22,
                     f"{len(gen)} contests {sorted(gen.items())}")
    for n, cid in VA_HOUSE22.items():
        page = (VA_DIR / f"contest_{cid}.html").read_text(encoding="utf-8", errors="replace")
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', page, re.S)
        c = json.loads(m.group(1))["props"]["pageProps"]["contest"]
        if c.get("publicNote") or not c.get("verifiedAt"):
            print(f"  elstats VA-{n} (contest {cid}): verifiedAt {c.get('verifiedAt')}; note: {c.get('publicNote')}")

    ref = pd.read_csv(OUT / "va_localities.csv", usecols=["locality", "gov21_total", "pres20_total"])
    refmap = {_vnorm(x): x for x in ref.locality}
    fec = _fec_house("VA")
    ecsv = pd.read_csv(VA_CSV_DIR / "2022 November General.csv", dtype=str, encoding="latin-1")
    ecsv = ecsv[ecsv.DistrictType == "Congressional"].copy()
    ecsv["v"] = pd.to_numeric(ecsv.TOTAL_VOTES.str.replace(",", ""), errors="raise").fillna(0).astype(int)  # blanks only
    parts, dropped = [], []
    for n, cid in VA_HOUSE22.items():
        district, names, parties, roles, loc, dist_row, num = _elstats(VA_DIR / f"va_house22_cd{n:02d}_{cid}.csv")
        if district != n:
            raise ValueError(f"contest {cid} is district {district}, expected {n}")
        rv = list(roles.values())
        has_dr = rv.count("dem") == 1 and rv.count("rep") == 1
        cands = [f"{nm} ({p})" for j, (nm, p) in enumerate(zip(names, parties)) if j in roles and isinstance(p, str)]
        print(f"VA-{n} (contest {cid}): {', '.join(cands)}" + ("" if has_dr else " -> dropped (no D or no R)"))
        if not has_dr:
            dropped.append(n)
        vote_cols = [c for c in rv if c not in ("total", "undervotes")]
        # elstats internal checks (diagnostic: the output is reconciled to the official results below)
        diff = {c: int(loc[c].sum() - dist_row[c].iloc[0]) for c in vote_cols + ["total"]}
        _check(f"VA-{n} elstats: localities sum to the district row", not any(diff.values()),
               f"sum minus district row {diff}", diagnostic=True)
        num = num.assign(owner=num[1].where(num[0] == "Locality").ffill())     # each precinct's locality
        prec = (num[num[0] == "Precinct"].rename(columns=roles).groupby("owner")[vote_cols + ["total"]].sum()
                .reindex(loc.locality, fill_value=0))
        pgap = prec.sub(loc.set_index("locality")[vote_cols + ["total"]]).fillna(0)
        pgap = pgap[(pgap != 0).any(axis=1)]
        _check(f"VA-{n} elstats: precinct rows sum to their locality row (precincts are not used)", pgap.empty,
               "; ".join(f"{i}: precincts minus locality, total {int(r.total):+,}, D {int(r.dem):+,}, R {int(r.rep):+,}"
                         for i, r in pgap.iterrows()) or "all localities", diagnostic=True)
        gap = loc.total - loc[vote_cols].sum(axis=1)
        _check(f"VA-{n} elstats: each locality's Total Votes Cast = sum of its candidates", not gap.any(),
               "; ".join(f"{a}: total exceeds candidates by {b:,}" for a, b in zip(loc.locality, gap) if b)
               or "all equal", diagnostic=True)
        # identity and votes against the official results
        jenr, enr = _enr(n)
        loc["k"] = loc.locality.map(_vnorm)
        enr["k"] = enr.enr_name.map(_vnorm)
        lone_e, lone_o = set(loc.k) - set(enr.k), set(enr.k) - set(loc.k)
        relabel = {}
        for k in list(lone_e):        # pair a mislabelled elstats row with the official locality of equal votes
            e = loc[loc.k == k].iloc[0]
            hit = [o for o in lone_o if (enr.loc[enr.k == o, ["dem", "rep"]].values[0] == e[["dem", "rep"]].values).all()]
            if len(hit) == 1:
                relabel[k] = hit[0]
                lone_e.discard(k)
                lone_o.discard(hit[0])
        for k, o in relabel.items():
            code = enr.loc[enr.k == o, "code"].iloc[0]
            print(f"  VA-{n}: elstats '{loc.loc[loc.k == k, 'locality'].iloc[0]}' carries the official votes of "
                  f"{o} (locality code {code}); relabelled")
        all_ok &= _check(f"VA-{n}: every elstats locality is an official locality of the district",
                         not lone_e and not lone_o, f"{len(enr)} official localities" +
                         (f"; unpaired elstats {lone_e}, official {lone_o}" if lone_e or lone_o else ""))
        loc["k"] = loc.k.replace(relabel)
        loc["relabelled_from"] = loc.locality.where(loc.k.isin(relabel.values()))
        m = loc.merge(enr, on="k", how="left", suffixes=("", "_off"))
        m["flags"] = ""
        m.loc[m.relabelled_from.notna(), "flags"] = (f"VA-{n}: elstats labels this locality '" +
                                                    m.relabelled_from.astype(str) + "'; official name and code used")
        for c in ["dem", "rep"]:
            bad = m[m[c] != m[f"{c}_off"]]
            for _, r in bad.iterrows():
                print(f"  VA-{n} {r.enr_name}: elstats {c} {r[c]:,} vs official {r[c + '_off']:,} "
                      f"(difference {r[c] - r[c + '_off']:+,}); official value used")
        other_e = [c for c in vote_cols if c.startswith("other:")]
        other_o = [c for c in enr.columns if c.startswith("other:")]
        m["other_e"] = m[other_e].sum(axis=1) if other_e else 0
        m["other_o"] = m[other_o].sum(axis=1) if other_o else 0
        fix = (m.dem != m.dem_off) | (m.rep != m.rep_off) | (m.other_e != m.other_o)
        for i in m.index[fix]:
            r = m.loc[i]
            note = (f"VA-{n}: elstats candidate votes (D {r.dem:,}, R {r.rep:,}, other {r.other_e:,}) differ from "
                    f"the official results (D {r.dem_off:,}, R {r.rep_off:,}, other {r.other_o:,}); official used")
            m.loc[i, "flags"] = (m.loc[i, "flags"] + " | " + note).strip(" |")
        wi = m.writein - m.writein_off
        print(f"  VA-{n}: write-ins, elstats minus official, by locality: "
              f"{ {a: int(b) for a, b in zip(m.enr_name, wi) if b} or 'none' } (total {int(wi.sum()):+})")
        m["dem_final"], m["rep_final"] = m.dem_off, m.rep_off
        m["other_final"] = m.other_o
        cons = m.total - (m.dem_final + m.rep_final + m.other_final + m.writein)
        all_ok &= _check(f"VA-{n}: all votes (elstats Total Votes Cast) = official D + R + other + elstats "
                         f"write-ins", not cons.any(),
                         "; ".join(f"{a}: {b:+,}" for a, b in zip(m.enr_name, cons) if b) or "every locality")
        # district totals against the official results page, the FEC compilation and ELECT's CSV
        d_off, r_off = int(enr.dem.sum()), int(enr.rep.sum())
        dfin, rfin, tfin = int(m.dem_final.sum()), int(m.rep_final.sum()), int(m.total.sum())
        all_ok &= _check(f"VA-{n}: D and R equal the official results' district totals", (dfin, rfin) == (d_off, r_off),
                         f"D {dfin:,} R {rfin:,} vs official D {d_off:,} R {r_off:,}")
        if fec is not None:
            f = fec[fec.district == n]
            fd, fr, ft = (int(f[f.party == "D"].votes.sum()), int(f[f.party == "R"].votes.sum()), int(f.votes.sum()))
            ok_dr = (dfin, rfin) == (fd, fr)
            all_ok &= _check(f"VA-{n}: D and R equal the FEC compilation", ok_dr, f"FEC D {fd:,} R {fr:,}")
            _check(f"VA-{n}: all votes equal the FEC compilation", tfin == ft,
                   f"elstats Total Votes Cast {tfin:,} vs FEC {ft:,} (difference {tfin - ft:+,})", diagnostic=True)
        e = ecsv[ecsv.DistrictName == f"{n:02d}"]
        ed, er = int(e[e.Party == "Democratic"].v.sum()), int(e[e.Party == "Republican"].v.sum())
        et = int(e.v.sum())
        _check(f"VA-{n}: D, R and all votes equal ELECT's statewide results CSV", (dfin, rfin, tfin) == (ed, er, et),
               f"CSV D {ed:,} R {er:,} all {et:,}" + ("" if (dfin, rfin, tfin) == (ed, er, et) else
                                                    f" (CSV minus output: D {ed - dfin:+,}, R {er - rfin:+,}, "
                                                    f"all {et - tfin:+,})"), diagnostic=True)
        m["locality_out"] = m.k.map(refmap)
        if m.locality_out.isna().any():
            all_ok &= _check(f"VA-{n}: official localities found in va_localities.csv", False,
                             f"not found {m.loc[m.locality_out.isna(), 'enr_name'].tolist()}")
        m["district"] = f"VA-{n}"
        m["district_ok"] = has_dr
        parts.append(m[["locality_out", "code", "district", "district_ok", "dem_final", "rep_final", "total",
                        "flags"]].rename(columns={"locality_out": "locality", "dem_final": "dem", "rep_final": "rep"}))
    allp = pd.concat(parts, ignore_index=True)
    out = []
    for loc_name, g in allp.groupby("locality", sort=False):
        ok, bad = g[g.district_ok], g[~g.district_ok]
        flags = [x for x in g["flags"] if x]
        if len(bad):
            flags.append(("partly" if len(ok) else "only") + " in a district without both a D and an R candidate: "
                         + ", ".join(bad.district))
        out.append({"locality": loc_name, "fips": "51" + g.code.iloc[0],
                    "house22_dem": ok.dem.sum() if len(ok) else None,
                    "house22_rep": ok.rep.sum() if len(ok) else None,
                    "house22_total": ok.total.sum() if len(ok) else None,
                    "house22_districts": ";".join(g.district), "house22_split": len(g) > 1,
                    "house22_parts": _parts(g, "district"),
                    "partly_in_dropped_district": bool(len(bad) and len(ok)),
                    "house22_flags": " | ".join(flags)})
    va = pd.DataFrame(out)
    codes = va.groupby("locality").fips.nunique()
    all_ok &= _check("one locality code per locality across districts", (codes == 1).all(),
                     f"{codes[codes > 1].to_dict() or 'consistent'}")
    split = va[va.house22_split]
    print(f"Localities split between districts ({len(split)}):")
    for _, r in split.iterrows():
        print(f"  {r.locality}: {r.house22_parts}")
    print(f"Districts dropped (no D or no R): {dropped or 'none'}; localities partly in one: "
          f"{va.partly_in_dropped_district.sum()}")
    j = va.merge(ref, on="locality", how="outer", indicator=True)
    only22, only25 = j[j._merge == "left_only"], j[j._merge == "right_only"]
    all_ok &= _check("join to va_localities.csv on locality", only22.empty and only25.empty,
           f"{(j._merge == 'both').sum()} matched; only in 2022 file {only22.locality.tolist()}; "
           f"only in same-day file {only25.locality.tolist()}")
    both = j[j._merge == "both"].copy()
    both["ratio_gov21"] = both.house22_total / both.gov21_total
    odd = both[(both.ratio_gov21 < 0.6) | (both.ratio_gov21 > 1.6)]
    print(f"Plausibility: 2022 House votes / 2021 governor votes, median {both.ratio_gov21.median():.3f}, "
          f"range {both.ratio_gov21.min():.3f}-{both.ratio_gov21.max():.3f}; outside 0.6-1.6: "
          f"{odd[['locality', 'house22_total', 'gov21_total']].values.tolist() or 'none'}")
    va = va.sort_values("locality").reset_index(drop=True)
    for c in ["house22_dem", "house22_rep", "house22_total"]:
        va[c] = va[c].astype("Int64")
    va.to_csv(OUT / "house22_va_by_locality.csv", index=False)
    print(f"VA: {len(va)} localities written; D {va.house22_dem.sum():,} R {va.house22_rep.sum():,} "
          f"all {va.house22_total.sum():,}; all checks {'passed' if all_ok else 'DID NOT ALL PASS'}")
    return va, all_ok


if __name__ == "__main__":
    download()
    nj, ok_nj = pull_nj()
    va, ok_va = pull_va()
    if not (ok_nj and ok_va):
        sys.exit("Some reconciliation checks failed: see FAIL lines above.")
