"""Same-day benchmarks for the November 2025 New York City result: New Jersey and Virginia.

Why. Part 10 compares Mamdani with Harris's 2024 vote. On the same day, 4 November 2025, New Jersey and
Virginia elected governors, and Virginia's ballot also carried a lieutenant governor and an attorney
general. That gives two things the New York data cannot: a benchmark for how far the 2024 swing reversed
elsewhere under the same national conditions, and a second same-ballot contrast between a progressive
(Hashmi) and a moderate (Spanberger) in front of the same voters.

Sources.
- Virginia: the Department of Elections' historical database (historical.elections.virginia.gov), which
  is now a JavaScript app. Each contest page links a CSV at
  `va2.elstats.civera.com/api/download_contest/<id>_table.csv` (a 307 redirect; curl needs -L). Rows are
  the state, 133 localities and their precincts; this script keeps localities. Contest ids: governor
  164996, lieutenant governor 164997, attorney general 164998, president 2024 161256, president 2020
  144567, governor 2021 147466. Ids are not derivable -- they were read off the candidate pages.
- New Jersey: Division of Elections official results, one PDF per county per contest, with one row per
  municipality (`nj.gov/state/elections/assets/pdf/election-results/<year>/<year>-official-general-
  results-<governor|president>-<county>.pdf`). **Column order follows each county's ballot draw**, so the
  Democratic and Republican columns are located from each file's own header, and every county's parsed
  municipalities are checked against the county total printed in the same file.

Output: `data/raw/same_day_2025/va_localities.csv` and `nj_municipalities.csv`.
"""

from pathlib import Path
import re
import subprocess
import time

import pandas as pd

OUT = Path("data/raw/same_day_2025")
VA_CONTESTS = {"gov25": 164996, "ltgov25": 164997, "ag25": 164998, "pres24": 161256, "pres20": 144567,
               "gov21": 147466}   # 2021 governor (Youngkin v McAuliffe): the off-year baseline
NJ_COUNTIES = ["atlantic", "bergen", "burlington", "camden", "capemay", "cumberland", "essex", "gloucester",
               "hudson", "hunterdon", "mercer", "middlesex", "monmouth", "morris", "ocean", "passaic", "salem",
               "somerset", "sussex", "union", "warren"]
NJ_FILES = {"gov25": "2025/2025-official-general-results-governor",
            "pres24": "2024/2024-official-general-results-president",
            "pres20": "2020/2020-official-general-results-president",
            # 2021 governor (Murphy v Ciattarelli): the off-year baseline for the enforcement test. The 2021
            # files use a different stem and hyphenate Cape May.
            "gov21": "2021/2021-general-election-results-governor"}
SLUG = {("gov21", "capemay"): "cape-may"}
NJ_BASE = "https://www.nj.gov/state/elections/assets/pdf/election-results"
NUM = re.compile(r"^[\d,]+$")
DATE_LINE = re.compile(r"^(January|February|March|April|May|June|July|August|September|October|November|December)"
                       r"\s+\d{1,2},\s+\d{4}$")


def _curl(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return
    subprocess.run(["curl", "-s", "-L", "-A", "Mozilla/5.0", url, "-o", str(dest)], check=True)
    time.sleep(0.3)


def pull_va():
    frames = {}
    for key, cid in VA_CONTESTS.items():
        f = OUT / f"va_{key}.csv"
        _curl(f"https://va2.elstats.civera.com/api/download_contest/{cid}_table.csv?split_party=false", f)
        raw = pd.read_csv(f, header=None, dtype=str)
        names, parties = raw.iloc[0].tolist(), raw.iloc[1].tolist()
        d = raw[raw[0] == "Locality"].copy()
        cols = {}
        for j, (n, p) in enumerate(zip(names, parties)):
            if p == "Democratic": cols[j] = f"{key}_dem"
            elif p == "Republican": cols[j] = f"{key}_rep"
            elif n == "Total Votes Cast": cols[j] = f"{key}_total"
        d = d[[1] + list(cols)].rename(columns={1: "locality", **cols})
        for c in cols.values():
            d[c] = d[c].str.replace(",", "").astype(float)
        frames[key] = d.set_index("locality")
    va = pd.concat(frames.values(), axis=1).reset_index()
    va.to_csv(OUT / "va_localities.csv", index=False)
    print(f"VA: {len(va)} localities; statewide governor D {va.gov25_dem.sum():,.0f} R {va.gov25_rep.sum():,.0f}")
    return va


NON_GEO = re.compile(r"federal|overseas|oversees|hand count|provisional|emergency|write", re.I)


SUFFIX = r"(boro|twp|city|town|village)"


def _norm(name):
    s = name.lower().replace(".", "").replace("-", " ").replace(",", " ")
    s = re.sub(r"(borough|boro)\b", " boro", s)
    s = re.sub(r"(township|townshp|twp)\b", " twp", s)     # 'Gloucester Townshp' (2024 Senate file, Camden)
    s = re.sub(rf"^{SUFFIX} of (.+)$", r"\2 \1", s.strip())      # "Twp. of Robbinsville" -> "robbinsville twp"
    s = re.sub(rf"^(.+?) {SUFFIX} of$", r"\1 \2", s.strip())     # "Trenton, City of" -> "trenton city"
    return re.sub(r"\s+", "", s).strip()      # spacing is inconsistent across years ("Closterboro")


def _stem(key):
    return re.sub(rf"(villagetwp|{SUFFIX})$", "", key)     # "South Orange Village Twp" / "South Orange"


def _parse_nj(pdf):
    """Municipality rows with Democratic and Republican columns located from the file's own header.

    Non-geographic rows (federal overseas ballots, hand counts) are set aside: some counties print them
    with blank columns omitted, so their numbers cannot be assigned to candidates. The county-total check
    allows a gap no larger than what those rows hold."""
    from pypdf import PdfReader
    rows, check, unassigned = [], {}, 0
    for page in PdfReader(pdf).pages:
        lines = [l.strip() for l in (page.extract_text() or "").split("\n") if l.strip()]
        start = next(i for i, l in enumerate(lines) if l.startswith("MUNICIPALITIES"))
        head, body = [], []
        for i, l in enumerate(lines[start:], start):
            toks = l.split()
            if len(toks) > 1 and NUM.match(toks[-1]) and not l.startswith("MUNICIPALITIES"):
                body = lines[i:]
                break
            head.append(l.replace("MUNICIPALITIES", "").strip())
        head = [h for h in head if h]
        parties = head[1::2]                      # header alternates candidate line, party line
        d_col, r_col = parties.index("Democratic"), parties.index("Republican")
        pending = ""
        for l in body:
            if l.startswith("*"):                 # footnote (Sussex 2020 notes a post-certification amendment)
                continue
            if DATE_LINE.match(l):                # 'November 5, 2024' (2024 Hudson Senate file): NUM accepts '5,'
                continue
            toks = l.split()
            nums = []
            while toks and NUM.match(toks[-1]):
                nums.insert(0, int(toks.pop().replace(",", "")))
            own = " ".join(toks)
            name = own if own.upper().endswith("TOTAL") else (pending + " " + own).strip()
            if not nums:
                # a name with no numbers wraps onto the next line -- unless it is an empty
                # non-geographic row ("Federal Overseas" with no votes), which must not prefix the next
                pending = "" if (l.startswith("NJDOE") or NON_GEO.search(name)) else name
                continue
            pending = ""
            if not name:                          # a bare number: page number or footnote marker
                continue
            if NON_GEO.search(name):
                unassigned += sum(nums)
                continue
            if len(nums) != len(parties):
                raise ValueError(f"{pdf}: {len(nums)} numbers for {len(parties)} candidates in {l!r}")
            rec = {"municipality": name, "dem": nums[d_col], "rep": nums[r_col], "total": sum(nums)}
            if name.upper().endswith("TOTAL"):
                check = rec
            else:
                rows.append(rec)
    d = pd.DataFrame(rows)
    if not check:
        raise ValueError(f"{pdf}: no printed county total to check against")
    for c in ["dem", "rep"]:
        if not 0 <= check[c] - d[c].sum() <= unassigned:
            raise ValueError(f"{pdf}: parsed {c} {d[c].sum()} vs printed {check[c]}, unassigned {unassigned}")
    if check["total"] - d.total.sum() != unassigned:
        raise ValueError(f"{pdf}: parsed total {d.total.sum()} + unassigned {unassigned} != {check['total']}")
    return d


def _align(keys, reference):
    """Map another year's municipality keys onto the 2025 spelling.

    First by name without its suffix, only where that stem is unique on both sides (Essex drops suffixes
    in some years; Warren has both a Washington Boro and a Washington Twp). Then by close spelling, for
    typos such as 'Travistock' / 'Tavistock'."""
    import difflib
    out = {}
    ks, rs = pd.Series(keys, dtype=str), pd.Series(reference, dtype=str)
    kstem, rstem = ks.map(_stem), rs.map(_stem)
    for k, st in zip(ks, kstem):
        if (kstem == st).sum() == 1 and (rstem == st).sum() == 1:
            out[k] = rs[rstem == st].iloc[0]
    left = [k for k in keys if k not in out]
    pool = [r for r in reference if r not in out.values()]
    for k in left:
        hit = difflib.get_close_matches(k, pool, n=1, cutoff=0.88)
        if hit:
            out[k] = hit[0]
            pool.remove(hit[0])
    return out


def pull_nj():
    (OUT / "nj").mkdir(parents=True, exist_ok=True)
    frames = []
    for county in NJ_COUNTIES:
        parts = []
        for key, stem in NJ_FILES.items():
            f = OUT / "nj" / f"{Path(stem).name}-{county}.pdf"
            _curl(f"{NJ_BASE}/{stem}-{SLUG.get((key, county), county)}.pdf", f)
            d = _parse_nj(f).rename(columns={"dem": f"{key}_dem", "rep": f"{key}_rep", "total": f"{key}_total"})
            d["key"] = d.municipality.map(_norm)
            if parts:                                           # align spellings to the 2025 file
                ref = parts[0].index.tolist()
                miss = [k for k in d.key if k not in ref]
                fix = _align(miss, [r for r in ref if r not in set(d.key)])
                if fix:
                    print(f"  {county} {key}: matched spellings {fix}")
                d["key"] = d.key.replace(fix)
            parts.append(d.drop(columns="municipality").set_index("key"))
        m = pd.concat(parts, axis=1, join="outer")
        m["county"] = county
        unmatched = m[m.isna().any(axis=1)].index.tolist()
        if unmatched:
            print(f"  {county}: not in all three years, dropped: {unmatched}")
        frames.append(m.dropna().reset_index())
    nj = pd.concat(frames, ignore_index=True)
    nj.to_csv(OUT / "nj_municipalities.csv", index=False)
    print(f"NJ: {len(nj)} municipalities; governor D {nj.gov25_dem.sum():,.0f} R {nj.gov25_rep.sum():,.0f}")
    return nj


# ---------------------------------------------------------------- 2026 U.S. Senate, for Test C (added 4 Nov 2026)
# Kept out of VA_CONTESTS and NJ_FILES on purpose: pull_va() and pull_nj() iterate those, so a routine rerun
# would fetch 2026 files. pull_2026_nj() and pull_2026_va() run only with --certified-2026 --nj / --va, after
# each state certifies (NJ: counties 18 Nov, state by 3 Dec 2026; VA: State Board 7 Dec 2026), and stop until
# CERTIFIED_2026 (and, for VA, the contest id) is filled in from the official statements.
#   - NJ: 2024's Senate files are 2024-official-general-results-us-senate-<county>.pdf; the 2026 stem below
#     assumes the same pattern and must be confirmed on nj.gov's 2026 results page (the 2021 files used a
#     different stem and hyphenated Cape May). _parse_nj reconciles every county to its printed total.
#   - VA: look up the contest id on elstats after the State Board certifies. Reconcile the locality totals to
#     the official JSON (results.elections.virginia.gov/vaelections/<event>/Json/...), not to elstats alone:
#     for the 2022 House contests elstats mislabelled Franklin City and Richmond City as counties and left
#     Alexandria's provisional ballots out of its candidate columns (house_2022_baseline_pull.py).
NJ_FILES_2026 = {"sen26": "2026/2026-official-general-results-us-senate"}
VA_CONTESTS_2026 = {"sen26": None}


# Certified statewide totals, filled in from each state's official statement before pull_2026 runs. They are
# the independent check of the parse: a D/R column swap or a dropped row cannot match them.
#   NJ: the Division of Elections' 2026 Official List (U.S. Senate), statewide D and R. NJ county PDFs also carry
#       federal overseas rows outside municipalities (2022 House: D 1,032, R 80), so the municipal sum may fall
#       short of the statewide total by at most NJ_NONMUNI_SHARE of it, per party. Tested on the 2024 Senate files:
#       municipal D 2,155,681 vs official 2,161,491 (Kim), short by 0.27%; a D/R swap would be off by ~400,000.
#   VA: the official JSON's statewide D and R for the 2026 U.S. Senate race.
CERTIFIED_2026 = {"NJ": {"D": None, "R": None}, "VA": {"D": None, "R": None}}
NJ_NONMUNI_SHARE = 0.005
VA_N_LOCALITIES = 133


def _curl_strict(url, dest, magic):
    """Download to a .part file, fail on HTTP errors, check the leading bytes, then move into place. An
    existing file is reused only if it starts with the expected bytes."""
    if dest.exists() and dest.read_bytes()[:len(magic)] == magic:
        return
    part = dest.with_suffix(dest.suffix + ".part")
    subprocess.run(["curl", "-s", "-f", "-L", "-A", "Mozilla/5.0", url, "-o", str(part)], check=True)
    if part.read_bytes()[:len(magic)] != magic:
        raise SystemExit(f"{url}: unexpected content (does not start with {magic!r}); kept as {part}")
    part.replace(dest)
    time.sleep(0.3)


def _check_total(state, d_sum, r_sum, share=0.0, require_only=False):
    cert = CERTIFIED_2026[state]
    if cert["D"] is None or cert["R"] is None:
        raise SystemExit(f"fill in CERTIFIED_2026['{state}'] from the official statement before reading {state}")
    if require_only:
        return
    for p, got in (("D", d_sum), ("R", r_sum)):
        short, tol = cert[p] - got, int(share * cert[p])
        print(f"{state} 2026 Senate {p}: parsed {got:,} vs certified {cert[p]:,} (short by {short:,})")
        if not 0 <= short <= tol:
            raise SystemExit(f"{state} {p} does not reconcile (allowed shortfall 0-{tol:,})")


def pull_2026_va():
    """VA locality 2026 Senate results. Checks: 133 unique localities, candidates <= total votes in every
    locality, and the statewide D and R equal to the certified totals (which catches a provisional row left out
    of a locality's candidate columns, as for Alexandria in 2022). City/county mislabels show up as duplicate
    names: compare those rows with the official JSON by FIPS code and relabel only on an exact vote match."""
    if VA_CONTESTS_2026["sen26"] is None:
        raise SystemExit("fill in VA_CONTESTS_2026['sen26'] (elstats contest id) after certification")
    _check_total("VA", None, None, require_only=True)
    out = OUT / "2026"
    out.mkdir(parents=True, exist_ok=True)
    f = out / "va_sen26.csv"
    _curl_strict(f"https://va2.elstats.civera.com/api/download_contest/{VA_CONTESTS_2026['sen26']}_table.csv?split_party=false",
                 f, b'"')
    raw = pd.read_csv(f, header=None, dtype=str)
    names, parties = raw.iloc[0].tolist(), raw.iloc[1].tolist()
    d = raw[raw[0] == "Locality"].copy()
    cols = {j: c for j, (n, p) in enumerate(zip(names, parties))
            for c in [{"Democratic": "sen26_dem", "Republican": "sen26_rep"}.get(p, "sen26_total" if n == "Total Votes Cast" else None)] if c}
    if sorted(cols.values()) != ["sen26_dem", "sen26_rep", "sen26_total"]:
        raise SystemExit(f"VA 2026 Senate columns not as expected: {cols}")
    va = d[[1] + list(cols)].rename(columns={1: "locality", **cols})
    for c in cols.values():
        va[c] = va[c].str.replace(",", "").astype(int)          # commas stripped; a bad value fails loudly
    dup = va.locality[va.locality.duplicated(keep=False)].tolist()
    if dup or len(va) != VA_N_LOCALITIES:
        raise SystemExit(f"VA: {len(va)} locality rows (expected {VA_N_LOCALITIES}); duplicated names {dup} "
                         "(a city labelled as the county of the same name?) - resolve against the official JSON by FIPS")
    over = va[va.sen26_dem + va.sen26_rep > va.sen26_total]
    if len(over):
        raise SystemExit(f"VA: candidates exceed total votes in {over.locality.tolist()}")
    _check_total("VA", int(va.sen26_dem.sum()), int(va.sen26_rep.sum()))
    va.to_csv(out / "va_sen26_localities.csv", index=False)
    return va


def pull_2026_nj():
    """NJ municipal 2026 Senate results, keyed to nj_municipalities.csv. Checks: _parse_nj's per-county printed
    totals; the statewide D and R against the certified totals (the independent check of which column is D,
    since _parse_nj reads the county total row with the same column indexes); every municipality joins."""
    _check_total("NJ", None, None, require_only=True)
    out = OUT / "2026"
    (out / "nj").mkdir(parents=True, exist_ok=True)
    ref = pd.read_csv(OUT / "nj_municipalities.csv")
    frames = []
    for county in NJ_COUNTIES:
        stem = NJ_FILES_2026["sen26"]
        pdf = out / "nj" / f"{Path(stem).name}-{county}.pdf"
        _curl_strict(f"{NJ_BASE}/{stem}-{SLUG.get(('sen26', county), county)}.pdf", pdf, b"%PDF")
        p = _parse_nj(pdf).rename(columns={"dem": "sen26_dem", "rep": "sen26_rep", "total": "sen26_total"})
        p["key"], p["county"] = p.municipality.map(_norm), county
        keys = ref.loc[ref.county == county, "key"].tolist()
        fix = _align([k for k in p.key if k not in keys], [k for k in keys if k not in set(p.key)])
        if fix:
            print(f"  {county}: matched spellings {fix}")
        p["key"] = p.key.replace(fix)
        frames.append(p)
    nj = pd.concat(frames, ignore_index=True)
    j = ref[["county", "key"]].merge(nj, on=["county", "key"], how="outer", indicator=True)
    if (j._merge != "both").any():
        raise SystemExit(f"NJ: municipalities not joined: {j.loc[j._merge != 'both', ['county', 'key', '_merge']].values.tolist()}")
    _check_total("NJ", int(nj.sen26_dem.sum()), int(nj.sen26_rep.sum()), share=NJ_NONMUNI_SHARE)
    nj.to_csv(out / "nj_sen26_municipalities.csv", index=False)
    return nj


if __name__ == "__main__":
    import sys
    OUT.mkdir(parents=True, exist_ok=True)
    if "--certified-2026" in sys.argv:            # each state when its certified files post (NJ first, by 3 Dec)
        if "--nj" in sys.argv:
            pull_2026_nj()
        if "--va" in sys.argv:
            pull_2026_va()
    else:
        pull_va()
        pull_nj()
