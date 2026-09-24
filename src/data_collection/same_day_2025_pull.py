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
  144567. Ids are not derivable -- they were read off the candidate pages.
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
VA_CONTESTS = {"gov25": 164996, "ltgov25": 164997, "ag25": 164998, "pres24": 161256, "pres20": 144567}
NJ_COUNTIES = ["atlantic", "bergen", "burlington", "camden", "capemay", "cumberland", "essex", "gloucester",
               "hudson", "hunterdon", "mercer", "middlesex", "monmouth", "morris", "ocean", "passaic", "salem",
               "somerset", "sussex", "union", "warren"]
NJ_FILES = {"gov25": "2025/2025-official-general-results-governor",
            "pres24": "2024/2024-official-general-results-president",
            "pres20": "2020/2020-official-general-results-president"}
NJ_BASE = "https://www.nj.gov/state/elections/assets/pdf/election-results"
NUM = re.compile(r"^[\d,]+$")


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
    s = re.sub(r"(township|twp)\b", " twp", s)
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
            _curl(f"{NJ_BASE}/{stem}-{county}.pdf", f)
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


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    pull_va()
    pull_nj()
