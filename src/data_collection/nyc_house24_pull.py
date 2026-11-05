"""2024 U.S. House general election in New York City, by election district (ED), for Test B.

Why. Test B (report/preregistration_2026_general.md) compares, ED by ED, the House Democrat's
two-party share minus the top of the ticket's two-party share (Harris in 2024, Hochul in 2026) in the
three districts with new left nominees in 2026 (NY-7, NY-10, NY-13) against the two where the 2024
nominee ran again (NY-6, NY-15). This script builds the 2024 House half: every candidate's votes by ED,
summed across ballot lines, the per-line votes, and the flags the test's exclusions need.

Source. The Board of Elections' certified ED-level CSVs for the 5 November 2024 general, listed on
`vote.nyc/page/election-results-summary-2024` (saved beside the downloads), one per (county, district),
on the URL pattern of `nyc_pull.FILES["pres24"]`:
    <county code><019><district, 5 digits><County> Representative in Congress <nth> Congressional District EDLevel.csv
with a certified `Recap.pdf` ("Statement and Return Report for Certification", 2-3 Dec 2024) and a
`Recap.csv` beside each. County codes: 000 Crossover, 001 New York, 002 Bronx, 003 Kings, 004 Queens.

Traps, all handled here.

1. **Tallies of 1,000 or more.** BOE writes them with a thousands separator ("1,023"). Until 4 Nov 2026
   `nyc_pull.read_boe_edlevel` turned every such tally into 0 (58 tallies in the five districts' county
   files; 177 in the 2024 presidential file, 36 of them on Harris's Democratic line and 1 on Trump's
   Republican line). This script found the defect. read_boe_edlevel is now fixed and the panel's vote
   columns rebuilt (`nyc_pull.py --votes-only`). `read_edlevel` below still re-reads the raw strings as a
   cross-check: it must now restore 0 tallies, and the panel_* columns agree with the BOE file in every ED.
2. **Crossover files.** NY-7, NY-10 and NY-13 span two counties. As in the June 2026 primaries, BOE also
   publishes a "Crossover" file for each; it is checked to be exactly the union of the county files and
   is not read into the output. Its recap gives the district-wide total.
3. **Ballot-method rows are not candidates.** "Public Counter", "Manually Counted Emergency",
   "Absentee / Military", "Federal" and "Affidavit" count ballots by how they were cast; they are summed
   as `ballots`. "Scattered" (write-ins) is kept as its own column and left out of `total`, as notebook
   17's METHOD set and `nyc_pull.wide_results` (for `pres24_total`) do.
4. **Combined EDs.** Only `EDAD Status == "IN-PLAY"` rows are kept. EDs "COMBINED INTO" another carry zero
   tallies (checked) and are counted in the receiving ED, which is flagged with the number it absorbed.

Candidates. The Democrat is whoever holds the Democratic line and the Republican whoever holds the
Republican line; each is summed over all of that candidate's lines. Anyone else, on any line, is `other`
(in NY-10 the Conservative line carried a different candidate, Paul J. Briscoe, so his votes are
`other`; `oth_con` keeps them). Names and lines are read from the files.

Checks (printed; the script stops if one fails).
- Every Crossover ED-level file equals the union of its county files, row for row.
- Each county file's ED sums equal its certified recap PDF, for every Assembly District and the county
  total, line by line (candidates, write-ins as Scattered, the five ballot-method rows, total ballots,
  total votes, unrecorded); each Crossover recap's county and district totals equal the ED sums; the
  recap CSV equals the PDF.
- Every ED's House ballots equal its presidential ballots in the same election, and the presidential
  ED file (read the same way) equals the certified citywide presidential recap, county by county.
- Every ED with House votes has presidential votes in `nyc_ed_panel.csv`; EDs whose panel values differ
  from the presidential file (the read_boe_edlevel defect) are flagged.

Matching to 2026. Test B matches 2024 EDs to 2026 EDs by ED number and excludes EDs whose lines changed
between the November 2025 and February 2026 enrolment snapshots (`lines_changed`), as
`nyc_2026_primary_pull.py` does. The output is joined to `nyc_2026_congressional_primary_by_ed.csv` (its
`cd` and `lines_changed`), and the same rule is recomputed from the enrolment file for every 2024 ED
(EDs missing from the primary file still get it; the recomputation must agree where both exist).
Not pre-registered and reported only as flags: the area overlap (intersection over union) of each 2024
ED polygon (DCP `nyed_24d`) with the polygon carrying the same number in DCP's November 2025 map
(`nyed_25d`) and its latest 2026 map (`nyed_26c`, published August 2026; a geography file, not results).
The enrolment rule cannot see line edits made between the 2024 election and November 2025, or after
February 2026, or edits that leave an ED's enrolment roughly unchanged; ED numbers were also reassigned
to different places. `geom_same_24_26` uses an arbitrary 0.9 cut-off. Nothing is dropped.

Run from the repo root: python src/data_collection/nyc_house24_pull.py
No 2026 general-election file is read or downloaded.
"""

from pathlib import Path
import csv
import glob
import json
import os
import re
import subprocess
import sys
import urllib.parse
import zipfile

import numpy as np
import pandas as pd
import requests
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).parent))
from nyc_pull import read_boe_edlevel, UA, FILES, DCP, COUNTIES, RAW as NYC_RAW  # noqa: E402  (nyc_pull loads .env)
from nyc_2026_primary_pull import (METHOD_ROWS, ENROLL, LINE_CHANGE_THRESHOLD,  # noqa: E402
                                   OUT as PRIM26)

BASE = "https://www.vote.nyc/sites/default/files/pdf/election_results/2024/20241105General%20Election/"
LISTING = "https://www.vote.nyc/page/election-results-summary-2024"
RAW = NYC_RAW / "2024_general_house"
PRES_RAW = NYC_RAW / "2024_general_president"
PRES_RECAP = "00000100000Citywide President Vice President Citywide Recap.pdf"
PRES24 = NYC_RAW / FILES["pres24"][1]
PANEL = NYC_RAW / "nyc_ed_panel.csv"
OUT = NYC_RAW / "nyc_2024_house_by_ed.csv"

COUNTY_CODE = {"Crossover": "000", "New York": "001", "Bronx": "002", "Kings": "003", "Queens": "004", "Richmond": "005"}
DISTRICTS = {6: ["Queens"], 7: ["Kings", "Queens"], 10: ["New York", "Kings"], 13: ["New York", "Bronx"], 15: ["Bronx"]}
ORDINAL = {6: "6th", 7: "7th", 10: "10th", 13: "13th", 15: "15th"}
TREATED = {6: 0, 7: 1, 10: 1, 13: 1, 15: 0}       # Test B: new left nominee in 2026
METHOD = sorted(METHOD_ROWS)                      # the five ballot-method rows
NOT_CANDIDATES = set(METHOD_ROWS) | {"Scattered"}
MIN_HOUSE_VOTES = 50                              # Test B: EDs with < 50 House votes in either year are excluded
GEOM_IOU = 0.9                                    # informational only; not a pre-registered threshold
LINE_ABBR = {"Democratic": "dem", "Republican": "rep", "Conservative": "con", "Working Families": "wfp"}
CAND = re.compile(r"^(?P<cand>.+?) \((?P<line>[^()]+)\)$")
NUM = r"\d{1,3}(?:,\d{3})*"
COUNTY_NAMES = "Kings|Queens|New York|Bronx|Richmond"


# ----------------------------------------------------------------------------- download

def name(cd, county, kind):
    """BOE file name for one (district, county) and kind ('EDLevel.csv', 'Recap.pdf', 'Recap.csv')."""
    return f"{COUNTY_CODE[county]}019{cd:05d}{county} Representative in Congress {ORDINAL[cd]} Congressional District {kind}"


def get(url, dest):
    """Download once and never overwrite: python-requests first, curl if the site refuses it."""
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    try:
        r = requests.get(url, headers=UA, timeout=300)
        r.raise_for_status()
        tmp.write_bytes(r.content)
    except requests.RequestException as e:
        print(f"  requests failed ({type(e).__name__}); trying curl")
        subprocess.run(["curl", "-sS", "-f", "-L", "-A", UA["User-Agent"], "-o", str(tmp), url], check=True)
    tmp.replace(dest)
    print(f"  saved {dest} ({dest.stat().st_size:,} bytes)")
    return dest


def download():
    get(LISTING, RAW / "election-results-summary-2024.html")
    listing = (RAW / "election-results-summary-2024.html").read_text(encoding="utf-8", errors="replace")
    for cd, counties in DISTRICTS.items():
        for county in counties + (["Crossover"] if len(counties) > 1 else []):
            for kind in ("EDLevel.csv", "Recap.pdf", "Recap.csv"):
                fn = name(cd, county, kind)
                if fn not in listing:
                    raise SystemExit(f"{fn!r} is not on the 2024 listing page")
                get(BASE + urllib.parse.quote(fn), RAW / fn)
        if len(counties) == 1 and name(cd, "Crossover", "EDLevel.csv") in listing:
            raise SystemExit(f"NY-{cd} unexpectedly has a Crossover file")
    for kind in ("Recap.pdf", "Recap.csv"):
        fn = PRES_RECAP.replace("Recap.pdf", kind)
        get(BASE + urllib.parse.quote(fn), PRES_RAW / fn)
    # DCP's latest 2026 election-district map (a geography file, not results), same layout as nyc_pull.SHAPES
    zp = get(DCP + "election-districts/nyed_26c.zip", NYC_RAW / "nyed_26c.zip")
    if not (NYC_RAW / "nyed_26c").exists():
        with zipfile.ZipFile(zp) as z:
            if any(Path(n).is_absolute() or ".." in Path(n).parts for n in z.namelist()):
                raise SystemExit("unsafe paths in nyed_26c.zip")
            z.extractall(NYC_RAW / "nyed_26c")


# ----------------------------------------------------------------------------- readers

def read_edlevel(path):
    """`nyc_pull.read_boe_edlevel`, with tallies of 1,000 or more restored.

    read_boe_edlevel turns any tally written with a thousands separator ("1,023") into 0. The raw Tally
    strings are re-read here with read_boe_edlevel's own row filter and order, and parsed with the comma
    removed. Tallies without a separator must equal read_boe_edlevel's exactly.
    Returns (frame, number of tallies read_boe_edlevel got wrong).
    """
    df = read_boe_edlevel(path)
    raw = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for parts in csv.reader(f):
            if len(parts) >= 22:
                raw.append(parts[21])
            elif len(parts) == 11 and parts[0] != "AD":
                raw.append(parts[10])
    if len(raw) != len(df):
        raise SystemExit(f"{path}: {len(raw)} raw tallies for {len(df)} parsed rows")
    raw = pd.Series(raw, index=df.index).str.strip()
    ok = raw.str.fullmatch(NUM + r"|\d+|")
    if not ok.all():
        raise SystemExit(f"{path}: unparseable tallies {raw[~ok].unique()[:5].tolist()}")
    fixed = pd.to_numeric(raw.str.replace(",", "", regex=False).replace("", "0")).astype("int64")
    comma = raw.str.contains(",", regex=False)
    if (fixed[~comma] != df.loc[~comma, "Tally"]).any():
        raise SystemExit(f"{path}: tallies without a thousands separator disagree with read_boe_edlevel")
    wrong = int((fixed != df["Tally"]).sum())
    df["Tally"] = fixed
    return df, wrong


def _int(s):
    s = str(s).strip().replace(",", "")
    return int(s) if s else 0


def _records(text):
    """One page of a recap -> list of records ('Assembly District 50', '41,604 PUBLIC COUNTER', ...).

    The NY-6 (Queens) recap was printed through 'Microsoft: Print To PDF': its text is in the Unicode
    Private Use Area (U+F0xx for ASCII xx) and has no line breaks, so it is mapped back and re-broken.
    """
    text = re.sub("[\uf000-\uf0ff]", lambda m: chr(ord(m.group(0)) - 0xF000), text)
    m = re.match(r"^.*?PRINTED AS OF:\s*\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M", text, re.S)
    if not m:
        return []                                                  # cover page
    t = text[m.end():]
    t = re.sub(r"We certify this statement.*$", "", t, flags=re.S)
    t = re.sub(r"Page \d+ of \d+", "", t)
    t = re.sub(rf"\s*(Assembly District \d+|Total for |(?<!- )(?:{COUNTY_NAMES}) County\b|Total Applicable Ballots"
               r"|Total Ballots|Total Votes|Unrecorded|Less - Inapplicable)", r"\n\1", t)
    t = re.sub(rf"(?<=[\s)])({NUM}) (?=[A-Z])", r"\n\1 ", t)
    return [s.strip() for s in t.split("\n") if s.strip()]


def _section(s):
    s = s.strip()
    m = re.fullmatch(r"Assembly District (\d+)", s)
    if m:
        return int(m.group(1))
    m = re.fullmatch(rf"({COUNTY_NAMES}) County", s)
    if m:
        return m.group(1)
    if s.startswith("Total for "):
        return "TOTAL"
    return None


def _finish(rows, path):
    d = pd.DataFrame(rows, columns=["section", "label", "votes"])
    d["label"] = d.label.str.upper().str.replace(r"\s+", " ", regex=True).str.strip()
    wi = d.label.str.endswith("WRITE-IN)")                       # '(WRITE-IN)' and '(OFFICIAL WRITE-IN)'
    fixed = d[~wi].drop_duplicates()
    if fixed.duplicated(["section", "label"]).any():
        raise SystemExit(f"{path}: conflicting values for {fixed[fixed.duplicated(['section', 'label'], keep=False)].head().values.tolist()}")
    w = d[wi].groupby("section", sort=False).votes.sum().reset_index().assign(label="SCATTERED")
    out = pd.concat([fixed, w], ignore_index=True)
    out["section"] = out.section.astype(str)
    return out.set_index(["section", "label"]).votes


def recap_pdf(path):
    """Certified recap PDF -> Series indexed (section, label). Sections: AD number, county, 'TOTAL'.
    Labels: the five ballot-method rows, each candidate line as printed, SCATTERED (all write-in rows),
    TOTAL BALLOTS, TOTAL APPLICABLE BALLOTS, TOTAL VOTES, UNRECORDED."""
    rows, sec = [], None
    for page in PdfReader(str(path)).pages:
        for rec in _records(page.extract_text() or ""):
            s = _section(rec)
            if s is not None:
                sec = s
                continue
            m = re.match(rf"(Total Applicable Ballots|Total Ballots|Total Votes|Unrecorded)\s+({NUM})\b", rec)
            if m and sec is not None:
                rows.append((sec, m.group(1), _int(m.group(2))))
                continue
            m = re.fullmatch(rf"({NUM}) (.+)", rec)
            if m and not rec.startswith("Less - ") and sec is not None:
                rows.append((sec, m.group(2), _int(m.group(1))))
    if not rows:
        raise SystemExit(f"{path}: no figures read")
    return _finish(rows, path)


def recap_csv(path):
    """The recap CSV beside each PDF, read into the same shape (a check on the PDF reading)."""
    rows = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for p in csv.reader(f):
            if len(p) < 6 or _section(p[3]) is None:
                continue
            sec = _section(p[3])
            rows.append((sec, p[4], _int(p[5])))
            for i in range(6, len(p) - 1):
                if p[i] in ("Total Ballots", "Total Applicable Ballots", "Total Votes", "Unrecorded"):
                    rows.append((sec, p[i], _int(p[i + 1])))
    return _finish(rows, path)


def ed_sums(d, by):
    """ED-level rows (IN-PLAY) -> the recap's labels, summed by `by` (a column, or None for the total)."""
    g = d.assign(label=d["Unit Name"].str.upper().str.replace(r"\s+", " ", regex=True))
    keys = [by] if by else []
    s = g.groupby(keys + ["label"]).Tally.sum() if keys else g.groupby("label").Tally.sum()
    meth = {m.upper() for m in METHOD}
    def derived(x):
        x = x.copy()
        b = x[x.index.isin(meth)].sum()
        v = x[~x.index.isin(meth)].sum()
        x["TOTAL BALLOTS"] = b; x["TOTAL APPLICABLE BALLOTS"] = b
        x["TOTAL VOTES"] = v; x["UNRECORDED"] = b - v
        return x
    if keys:
        return pd.concat({str(k): derived(v.droplevel(0)) for k, v in s.groupby(level=0)})
    return derived(s)


def compare(official, ours, what):
    """Every label in either series must agree. Returns a list of mismatches (label, official, ours)."""
    j = pd.concat([official.rename("official"), ours.rename("ours")], axis=1).fillna(0).astype("int64")
    bad = j[j.official != j.ours]
    return [(what, *k, int(r.official), int(r.ours)) if isinstance(k, tuple) else (what, k, int(r.official), int(r.ours))
            for k, r in bad.iterrows()]


# ----------------------------------------------------------------------------- build

def load_files():
    """All county ED-level files (and Crossover files) -> dict keyed (cd, county)."""
    files, wrong = {}, {}
    for cd, counties in DISTRICTS.items():
        for county in counties + (["Crossover"] if len(counties) > 1 else []):
            d, n = read_edlevel(RAW / name(cd, county, "EDLevel.csv"))
            if set(d["Office"]) != {"Representative in Congress"} or set(d["District Key"].astype(int)) != {cd}:
                raise SystemExit(f"NY-{cd} {county}: unexpected office/district {set(d['Office'])} {set(d['District Key'])}")
            if county != "Crossover" and set(d["County"]) != {county}:
                raise SystemExit(f"NY-{cd} {county}: rows from {set(d['County'])}")
            files[(cd, county)] = d
            wrong[(cd, county)] = n
    return files, wrong


def check_crossover(files):
    print("\nCrossover files vs the union of the county files (every row, all statuses)")
    cols = ["AD", "ED", "County", "EDAD Status", "Unit Name", "Tally"]
    for cd, counties in DISTRICTS.items():
        if len(counties) == 1:
            continue
        x = files[(cd, "Crossover")][cols].sort_values(cols).reset_index(drop=True)
        u = pd.concat([files[(cd, c)] for c in counties])[cols].sort_values(cols).reset_index(drop=True)
        same = x.shape == u.shape and (x.values == u.values).all()
        print(f"  NY-{cd}: crossover {len(x):,} rows, county files {len(u):,} rows -> {'identical' if same else 'DIFFERENT'}")
        if not same:
            raise SystemExit(f"NY-{cd}: Crossover file is not the union of its county files")


def reconcile(files):
    """ED sums against the certified recap PDFs (and the recap CSVs against the PDFs)."""
    print("\nReconciliation to the certified recaps (Statement and Return Report for Certification)")
    allbad = []
    for cd, counties in DISTRICTS.items():
        for county in counties:
            d = files[(cd, county)]
            d = d[d["EDAD Status"] == "IN-PLAY"]
            pdf = recap_pdf(RAW / name(cd, county, "Recap.pdf"))
            rcsv = recap_csv(RAW / name(cd, county, "Recap.csv"))
            ours = pd.concat([ed_sums(d, "AD"), pd.concat({"TOTAL": ed_sums(d, None)})])
            bad = compare(pdf, ours, f"NY-{cd} {county} ED sums vs PDF")
            bad += compare(pdf, rcsv, f"NY-{cd} {county} recap CSV vs PDF")
            n_ad = len({s for s, _ in pdf.index if s != "TOTAL"})
            t = pdf.loc["TOTAL"]
            print(f"  NY-{cd:<2d} {county:9s} {n_ad:2d} ADs + total, {len(pdf):4d} recap figures: "
                  f"{'all equal' if not bad else f'{len(bad)} MISMATCHES'}  (recap total votes {t['TOTAL VOTES']:,}, ballots {t['TOTAL BALLOTS']:,})")
            allbad += bad
        if len(counties) > 1:
            xr = recap_pdf(RAW / name(cd, "Crossover", "Recap.pdf"))
            xc = recap_csv(RAW / name(cd, "Crossover", "Recap.csv"))
            parts = {c: files[(cd, c)][files[(cd, c)]["EDAD Status"] == "IN-PLAY"] for c in counties}
            ours = pd.concat({**{c: ed_sums(v, None) for c, v in parts.items()},
                              "TOTAL": ed_sums(pd.concat(parts.values()), None)})
            bad = compare(xr, ours, f"NY-{cd} Crossover recap vs ED sums")
            bad += compare(xr, xc, f"NY-{cd} Crossover recap CSV vs PDF")
            cty = pd.concat([recap_pdf(RAW / name(cd, c, "Recap.pdf")).loc["TOTAL"] for c in counties]).groupby(level=0).sum()
            bad += compare(xr.loc["TOTAL"], cty, f"NY-{cd} Crossover total vs sum of county recaps")
            t = xr.loc["TOTAL"]
            print(f"  NY-{cd:<2d} Crossover recap (district total, {' + '.join(counties)}): "
                  f"{'all equal' if not bad else f'{len(bad)} MISMATCHES'}  (total votes {t['TOTAL VOTES']:,}, ballots {t['TOTAL BALLOTS']:,})")
            allbad += bad
    if allbad:
        for b in allbad[:40]:
            print("   ", b)
        raise SystemExit(f"{len(allbad)} reconciliation mismatches")


def candidates(d, cd):
    """Candidate rows of one district -> roles. The Democrat holds the Democratic line, the Republican
    the Republican line; everyone else is 'oth'."""
    c = d.loc[~d["Unit Name"].isin(NOT_CANDIDATES), "Unit Name"].drop_duplicates()
    parsed = c.str.extract(CAND)
    if parsed.isna().any().any():
        raise SystemExit(f"NY-{cd}: unparsed candidate rows {c[parsed.isna().any(axis=1)].tolist()}")
    parsed["unit"] = c.values
    dem = parsed.loc[parsed.line == "Democratic", "cand"].unique()
    rep = parsed.loc[parsed.line == "Republican", "cand"].unique()
    if len(dem) != 1 or len(rep) != 1:
        raise SystemExit(f"NY-{cd}: expected one Democratic and one Republican candidate, got {dem} / {rep}")
    parsed["role"] = np.select([parsed.cand == dem[0], parsed.cand == rep[0]], ["d", "r"], "oth")
    parsed["col"] = parsed.role + "_" + parsed.line.map(lambda x: LINE_ABBR.get(x, re.sub(r"[^a-z0-9]+", "_", x.lower()).strip("_")))
    return parsed, dem[0], rep[0]


def house_by_ed(files):
    frames, linecols = [], []
    for cd, counties in DISTRICTS.items():
        d = pd.concat([files[(cd, c)] for c in counties], ignore_index=True)
        status = d.groupby("ElectDist")["EDAD Status"].first()
        if d.groupby("ElectDist")["EDAD Status"].nunique().max() > 1:
            raise SystemExit(f"NY-{cd}: an ED has more than one status")
        off = d[d["EDAD Status"] != "IN-PLAY"]
        if off.Tally.sum() != 0:
            raise SystemExit(f"NY-{cd}: combined EDs carry {off.Tally.sum()} votes")
        # 'COMBINED INTO 059/76' = ED 59 of AD 76
        into = status[status != "IN-PLAY"].str.extract(r"COMBINED INTO (\d+)/(\d+)").astype(int)
        absorbed = (into[1] * 1000 + into[0]).value_counts()
        d = d[d["EDAD Status"] == "IN-PLAY"]
        outside = sorted(set(absorbed.index) - set(d.ElectDist))
        if outside:
            src = into.assign(to=into[1] * 1000 + into[0])
            print(f"  note: NY-{cd} EDs {src[src.to.isin(outside)].index.tolist()} are 'COMBINED INTO' {outside}, "
                  f"which are not in this district's files (zero tallies; the district still equals its recap)")
        roles, dem, rep = candidates(d, cd)
        g = d.groupby("ElectDist")
        out = pd.DataFrame({"AD": g.AD.first(), "ED": g.ED.first(), "county": g.County.first()})
        out["cd"] = cd
        out["treated"] = TREATED[cd]
        out["district_part"] = out.county + " | NY-" + str(cd)
        out["d_candidate"], out["r_candidate"] = dem, rep
        oth = roles[roles.role == "oth"]
        out["other_candidates"] = "; ".join(f"{a} ({b})" for a, b in zip(oth.cand, oth.line)) or ""
        lines = d.merge(roles[["unit", "role", "col"]], left_on="Unit Name", right_on="unit", how="inner")
        wide = lines.pivot_table(index="ElectDist", columns="col", values="Tally", aggfunc="sum")
        for role in ("d", "r", "oth"):
            out[f"{role}_votes"] = lines[lines.role == role].groupby("ElectDist").Tally.sum()
        out = out.join(wide)
        out["scattered"] = d[d["Unit Name"] == "Scattered"].groupby("ElectDist").Tally.sum()
        out["ballots"] = d[d["Unit Name"].isin(METHOD_ROWS)].groupby("ElectDist").Tally.sum()
        for m in METHOD:
            out[f"ballots_{re.sub(r'[^a-z]+', '_', m.lower()).strip('_')}"] = d[d["Unit Name"] == m].groupby("ElectDist").Tally.sum()
        out["absorbed_eds"] = out.index.map(absorbed).fillna(0).astype(int)
        linecols += [c for c in wide.columns if c not in linecols]
        frames.append(out)
    h = pd.concat(frames)
    if h.index.duplicated().any():
        raise SystemExit(f"EDs in more than one district: {h.index[h.index.duplicated()].tolist()[:10]}")
    fill = ["d_votes", "r_votes", "oth_votes", "scattered", "ballots"] + [c for c in h.columns if c.startswith("ballots_")]
    h[fill] = h[fill].fillna(0).astype("int64")
    h = h.rename(columns={"oth_votes": "other_votes"})
    h["total"] = h.d_votes + h.r_votes + h.other_votes
    h["two_party"] = h.d_votes + h.r_votes
    h["d_2p_share"] = (h.d_votes / h.two_party).where(h.two_party > 0)
    h["unrecorded"] = h.ballots - h.total - h.scattered
    h.index.name = "ElectDist"
    return h, linecols


def president():
    """The 2024 presidential ED file read the same way, reconciled to the certified citywide recap,
    then compared with nyc_ed_panel.csv's pres24 columns."""
    p, wrong = read_edlevel(PRES24)
    pin = p[p["EDAD Status"] == "IN-PLAY"]
    rec = recap_pdf(PRES_RAW / PRES_RECAP)
    ours = pd.concat({**{c: ed_sums(v, None) for c, v in pin.groupby("County")}, "TOTAL": ed_sums(pin, None)})
    bad = compare(rec, ours, "president ED sums vs recap")
    bad += compare(rec, recap_csv(PRES_RAW / PRES_RECAP.replace("Recap.pdf", "Recap.csv")), "president recap CSV vs PDF")
    t = rec.loc["TOTAL"]
    harris_lines = [k for k in t.index if k.startswith("KAMALA D. HARRIS")]
    trump_lines = [k for k in t.index if k.startswith("DONALD J. TRUMP")]
    print(f"\nPresident, ED file (restored tallies: {wrong}) vs certified citywide recap, 5 counties + city total: "
          f"{'all equal' if not bad else f'{len(bad)} MISMATCHES'}")
    print(f"  city: Harris {sum(t[k] for k in harris_lines):,}  Trump {sum(t[k] for k in trump_lines):,}  "
          f"write-ins {t['SCATTERED']:,}  ballots {t['TOTAL BALLOTS']:,}")
    if bad:
        for b in bad[:20]:
            print("   ", b)
        raise SystemExit("presidential file does not reconcile")
    pr = pd.DataFrame({
        "pres24_harris": pin[pin["Unit Name"].str.contains("Harris")].groupby("ElectDist").Tally.sum(),
        "pres24_trump": pin[pin["Unit Name"].str.contains("Trump")].groupby("ElectDist").Tally.sum(),
        "pres24_ballots": pin[pin["Unit Name"].isin(METHOD_ROWS)].groupby("ElectDist").Tally.sum(),
    })
    pr["pres24_total"] = pin[~pin["Unit Name"].isin(NOT_CANDIDATES)].groupby("ElectDist").Tally.sum()
    for m in METHOD:
        pr[f"_pb_{m}"] = pin[pin["Unit Name"] == m].groupby("ElectDist").Tally.sum()
    pr = pr.fillna(0).astype("int64")
    pr["pres24_tally_restored"] = (pin.assign(c=pin.Tally >= 1000).groupby("ElectDist").c.any())
    return pr, wrong


# ----------------------------------------------------------------------------- 2026 matching and lines

def enrolment_lines_changed():
    """The `lines_changed` rule of nyc_2026_primary_pull.py, for every ED in the enrolment file."""
    en = pd.read_csv(ENROLL)
    t = en[en.status == "total"].pivot_table(index="ElectDist", columns="snapshot", values="TOTAL", aggfunc="sum")
    return t["2025-11-01"], t["2026-02-20"], (t["2026-02-20"] / t["2025-11-01"] - 1).abs()


def block_population():
    """2020 census block population (PL 94-171 P1_001N) for the five counties, from the Census API.
    The raw responses are saved once to data/raw/nyc/census2020_block_pop/ and read from there after.
    Errors are reported without the request URL, which carries the API key."""
    folder = NYC_RAW / "census2020_block_pop"
    frames = []
    for fips in COUNTIES:
        raw = folder / f"pl2020_P1_001N_blocks_36{fips}.json"
        if not raw.exists():
            folder.mkdir(parents=True, exist_ok=True)
            try:
                r = requests.get("https://api.census.gov/data/2020/dec/pl", timeout=180, params={
                    "get": "P1_001N", "for": "block:*", "in": f"state:36 county:{fips}", "key": os.getenv("CENSUS_API_KEY")})
            except requests.RequestException as e:
                raise SystemExit(f"Census API request for county {fips} failed ({type(e).__name__})") from None
            if r.status_code != 200:
                raise SystemExit(f"Census API returned HTTP {r.status_code} for county {fips}")
            raw.write_text(r.text, encoding="utf-8")
        j = json.loads(raw.read_text(encoding="utf-8"))
        frames.append(pd.DataFrame(j[1:], columns=j[0]))
    b = pd.concat(frames, ignore_index=True)
    b["GEOID"] = b.state + b.county + b.tract + b.block
    b["pop"] = b.P1_001N.astype(int)
    return b[["GEOID", "pop"]]


def population_overlap(eds):
    """Population version of the overlap: 2020 census blocks (DCP nycb2020, representative points) are
    placed in a 2024 ED (nyed_24d) and a 2026 ED (nyed_26c). For ED number E, pop_iou_24d_26c is the
    population in blocks that are in E on both maps over the population in E on either map."""
    import geopandas as gpd
    blk = gpd.read_file(glob.glob(str(NYC_RAW / "nycb2020_25d" / "**" / "nycb2020.shp"), recursive=True)[0],
                        engine="pyogrio")[["GEOID", "geometry"]]
    blk["GEOID"] = blk.GEOID.astype(str).str.zfill(15)
    blk["geometry"] = blk.geometry.representative_point()
    pop = block_population()
    miss = len(set(blk.GEOID) - set(pop.GEOID))
    blk = blk.merge(pop, on="GEOID", how="left")
    for k in ("nyed_24d", "nyed_26c"):
        e = gpd.read_file(glob.glob(str(NYC_RAW / k / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")[["ElectDist", "geometry"]]
        j = gpd.sjoin(blk[["GEOID", "geometry"]], e, how="left", predicate="within")
        j = j[~j.GEOID.duplicated()]
        blk[k] = blk.GEOID.map(j.set_index("GEOID").ElectDist)
    print(f"  census blocks: {len(blk):,}, population {blk['pop'].sum():,.0f}; blocks without a population record: {miss}; "
          f"population outside every 2024 ED polygon: {blk.loc[blk.nyed_24d.isna(), 'pop'].sum():,.0f}")
    p24 = blk.groupby("nyed_24d")["pop"].sum()
    p26 = blk.groupby("nyed_26c")["pop"].sum()
    same = blk[blk.nyed_24d == blk.nyed_26c].groupby("nyed_24d")["pop"].sum()
    out = pd.DataFrame(index=pd.Index(eds, name="ElectDist"))
    out["pop2020_24d"] = p24.reindex(out.index)
    out["pop2020_26c_same_number"] = p26.reindex(out.index)
    both = same.reindex(out.index).fillna(0)
    out["pop_iou_24d_26c"] = (both / (out.pop2020_24d.fillna(0) + out.pop2020_26c_same_number.fillna(0) - both)).where(
        (out.pop2020_24d.fillna(0) + out.pop2020_26c_same_number.fillna(0)) > 0)
    return out


def polygon_overlap(eds):
    """Intersection over union of each ED's polygon in DCP's 2024 map (nyed_24d: created 25 Oct 2024)
    with the polygon carrying the same number in the November 2025 map (nyed_25d) and the latest 2026 map
    (nyed_26c: created 27 Jul 2026, published 17 Aug 2026). Area-based, so a park or river moved between
    EDs lowers it without moving voters. Not a pre-registered criterion."""
    import geopandas as gpd
    maps = {}
    for k in ("nyed_24d", "nyed_25d", "nyed_26c"):
        g = gpd.read_file(glob.glob(str(NYC_RAW / k / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")
        maps[k] = g.set_index(g.ElectDist.astype(int)).geometry
    out = pd.DataFrame(index=pd.Index(eds, name="ElectDist"))
    a = maps["nyed_24d"]
    out["in_nyed_24d"] = out.index.isin(a.index)
    for k in ("nyed_25d", "nyed_26c"):
        b = maps[k]
        both = a.index.intersection(b.index).intersection(eds)
        inter = a.loc[both].intersection(b.loc[both], align=True).area
        union = a.loc[both].area + b.loc[both].area - inter
        out[f"in_{k}"] = out.index.isin(b.index)
        out[f"iou_24d_{k[-3:]}"] = (inter / union).reindex(out.index)
    return out


# ----------------------------------------------------------------------------- main

def main():
    download()
    files, wrong = load_files()
    print("Tallies of 1,000+ that nyc_pull.read_boe_edlevel reads as 0, restored:")
    for (cd, county), n in wrong.items():
        print(f"  NY-{cd:<2d} {county:9s} {n:3d}")
    check_crossover(files)
    reconcile(files)
    h, linecols = house_by_ed(files)

    # ---- House ballots vs presidential ballots, and the panel
    pr, pwrong = president()
    h = h.join(pr.drop(columns=[c for c in pr.columns if c.startswith("_pb_")]), how="left")
    pb = pr[[c for c in pr.columns if c.startswith("_pb_")]].rename(columns=lambda c: c[4:])
    hb = h[[f"ballots_{re.sub(r'[^a-z]+', '_', m.lower()).strip('_')}" for m in METHOD]].copy()
    hb.columns = METHOD
    h["ballots_match_pres"] = (hb == pb.reindex(h.index)).all(axis=1)
    h["house_tally_restored"] = False
    for (cd, county), d in files.items():
        if county == "Crossover":
            continue
        r = d[(d["EDAD Status"] == "IN-PLAY") & (d.Tally >= 1000)].ElectDist.unique()
        h.loc[h.index.isin(r), "house_tally_restored"] = True

    panel = pd.read_csv(PANEL, index_col="ElectDist")
    cw = pr[["pres24_harris", "pres24_trump"]].join(panel[["pres24_harris", "pres24_trump"]], rsuffix="_panel", how="inner")
    cw = cw[(cw.pres24_harris != cw.pres24_harris_panel) | (cw.pres24_trump != cw.pres24_trump_panel)]
    print(f"  citywide, nyc_ed_panel.csv's pres24_harris/pres24_trump differ from the BOE file in {len(cw)} EDs: "
          f"Harris {cw.pres24_harris_panel.sum():,.0f} in the panel vs {cw.pres24_harris.sum():,} in the file; "
          f"Trump {cw.pres24_trump_panel.sum():,.0f} vs {cw.pres24_trump.sum():,}")
    pcols = {"pres24_harris": "panel_pres24_harris", "pres24_trump": "panel_pres24_trump",
             "pres24_total": "panel_pres24_total", "combined_into": "panel_combined_into"}
    h = h.join(panel[list(pcols)].rename(columns=pcols), how="left")
    h["in_panel"] = h.index.isin(panel.index)
    h["has_house_votes"] = h.total > 0
    h["has_pres_votes_panel"] = (h.panel_pres24_harris.fillna(0) + h.panel_pres24_trump.fillna(0)) > 0
    h["panel_pres24_differs"] = ~((h.panel_pres24_harris == h.pres24_harris) & (h.panel_pres24_trump == h.pres24_trump)
                                  & (h.panel_pres24_total == h.pres24_total))
    h["lt50_house24"] = h.total < MIN_HOUSE_VOTES

    # ---- 2026 ED numbers and lines
    p26 = pd.read_csv(PRIM26)
    if p26.ElectDist.duplicated().any():
        raise SystemExit("ED in more than one 2026 district in the primary file")
    p26 = p26.set_index("ElectDist")
    h["in_prim26"] = h.index.isin(p26.index)
    h["cd26"] = p26.cd.reindex(h.index)
    h["same_cd26"] = h.cd26 == h.cd
    h["lines_changed_prim26"] = p26.lines_changed.reindex(h.index)
    nov25, feb26, chg = enrolment_lines_changed()
    h["enrol_total_nov25"] = nov25.reindex(h.index)
    h["enrol_total_feb26"] = feb26.reindex(h.index)
    h["enrol_change"] = chg.reindex(h.index)
    # exactly nyc_2026_primary_pull.py's rule: `ED.map(chg > threshold).fillna(True)`. An ED missing from one
    # snapshot has chg = NaN, and NaN > threshold is False, so it counts as unchanged; only EDs absent from
    # the enrolment file altogether count as changed. `enrol_snapshot_missing` marks the first group.
    h["lines_changed"] = pd.Series(h.index.map(chg > LINE_CHANGE_THRESHOLD), index=h.index).fillna(True).astype(bool)
    h["enrol_snapshot_missing"] = h.enrol_total_nov25.isna() | h.enrol_total_feb26.isna()
    both = h.lines_changed_prim26.notna()
    if (h.loc[both, "lines_changed"] != h.loc[both, "lines_changed_prim26"].astype(bool)).any():
        raise SystemExit("recomputed lines_changed disagrees with nyc_2026_congressional_primary_by_ed.csv")
    h["usable_match"] = h.in_prim26 & h.same_cd26 & ~h.lines_changed
    h["usable_testB_2024"] = h.usable_match & ~h.lt50_house24
    h = h.join(polygon_overlap(h.index))
    print("\nOverlap of 2024 and 2026 ED polygons (not pre-registered):")
    h = h.join(population_overlap(h.index))
    # Each measure fails in its own way: area overlap drops when unpopulated land (a park, a pier) moves
    # between EDs; population overlap misplaces people when an ED holds only part of a census block, and is
    # empty for EDs that contain no block's representative point. So an ED counts as the same place if
    # either measure reaches the cut-off.
    basis = pd.concat([h.iou_24d_26c, h.pop_iou_24d_26c], axis=1).max(axis=1)
    h["geom_same_24_26"] = basis.fillna(0) >= GEOM_IOU
    h["usable_match_geom"] = h.usable_match & h.geom_same_24_26

    # ---- write
    id_cols = ["AD", "ED", "county", "cd", "treated", "district_part", "d_candidate", "r_candidate", "other_candidates"]
    vote_cols = ["d_votes", "r_votes", "other_votes", "total", "scattered", "two_party", "d_2p_share"]
    order = ["d_dem", "d_wfp", "r_rep", "r_con"]
    linecols = [c for c in order if c in linecols] + sorted(c for c in linecols if c not in order)
    ballot_cols = ["ballots", "unrecorded"] + [c for c in h.columns if c.startswith("ballots_") and c != "ballots_match_pres"]
    pres_cols = ["pres24_harris", "pres24_trump", "pres24_total", "pres24_ballots", "panel_pres24_harris",
                 "panel_pres24_trump", "panel_pres24_total", "panel_combined_into"]
    flag_cols = ["absorbed_eds", "house_tally_restored", "pres24_tally_restored", "ballots_match_pres", "in_panel",
                 "has_house_votes", "has_pres_votes_panel", "panel_pres24_differs", "lt50_house24",
                 "in_prim26", "cd26", "same_cd26", "lines_changed_prim26", "enrol_total_nov25", "enrol_total_feb26",
                 "enrol_change", "enrol_snapshot_missing", "lines_changed", "usable_match", "usable_testB_2024",
                 "in_nyed_24d", "in_nyed_25d", "iou_24d_25d", "in_nyed_26c", "iou_24d_26c",
                 "pop2020_24d", "pop2020_26c_same_number", "pop_iou_24d_26c", "geom_same_24_26", "usable_match_geom"]
    cols = id_cols + vote_cols + linecols + ballot_cols + pres_cols + flag_cols
    h = h[cols].sort_values(["cd", "ElectDist"])
    h.to_csv(OUT)
    print(f"\nwrote {OUT}: {h.shape[0]} EDs x {h.shape[1] + 1} columns")

    # ---- report
    print("\nCandidates (from the files) and NYC totals, reconciled:")
    for cd, g in h.groupby("cd"):
        print(f"  NY-{cd:<2d} D {g.d_candidate.iloc[0]} {g.d_votes.sum():,} | R {g.r_candidate.iloc[0]} {g.r_votes.sum():,} | "
              f"other {g.other_votes.sum():,} [{g.other_candidates.iloc[0] or '-'}] | write-ins {g.scattered.sum():,} | "
              f"ballots {g.ballots.sum():,}")
    print("\nPresidential votes for the House EDs:")
    print(f"  EDs with House votes: {int(h.has_house_votes.sum())}; in nyc_ed_panel.csv: {int((h.has_house_votes & h.in_panel).sum())}; "
          f"with panel Harris+Trump > 0: {int((h.has_house_votes & h.has_pres_votes_panel).sum())}")
    miss = h[h.has_house_votes & ~h.has_pres_votes_panel]
    print(f"  EDs with House votes but no panel presidential votes: {len(miss)} {miss.index.tolist()[:20]}")
    print(f"  House ballots equal presidential ballots (all five methods) in {int(h.ballots_match_pres.sum())} of {len(h)} EDs")
    dif = h[h.panel_pres24_differs]
    print(f"  panel pres24 differs from the BOE file in {len(dif)} House EDs (read_boe_edlevel defect): "
          f"panel Harris {dif.panel_pres24_harris.sum():,.0f} vs {dif.pres24_harris.sum():,}; "
          f"Trump {dif.panel_pres24_trump.sum():,.0f} vs {dif.pres24_trump.sum():,}")
    print("\nMatching to 2026 ED numbers (nyc_2026_congressional_primary_by_ed.csv) and lines:")
    rows = []
    for cd, g in h.groupby("cd"):
        hv = g[g.has_house_votes]
        rows.append({"cd": cd, "EDs_with_votes": len(hv), "matched_2026_number": int(hv.in_prim26.sum()),
                     "matched_same_cd": int((hv.in_prim26 & hv.same_cd26).sum()),
                     "lines_changed_among_matched": int((hv.in_prim26 & hv.lines_changed).sum()),
                     "lines_changed_all": int(hv.lines_changed.sum()),
                     "usable_EDs": int(hv.usable_match.sum()),
                     "votes_share_usable": hv.loc[hv.usable_match, "total"].sum() / hv.total.sum(),
                     "usable_and_50plus": int(hv.usable_testB_2024.sum()),
                     "votes_share_usable_50plus": hv.loc[hv.usable_testB_2024, "total"].sum() / hv.total.sum(),
                     "number_in_nyed_26c": int(hv.in_nyed_26c.sum()),
                     "usable_area_iou26_le_0.5": int((hv.usable_match & (hv.iou_24d_26c.fillna(0) <= 0.5)).sum()),
                     "usable_area_iou26_lt_0.9": int((hv.usable_match & (hv.iou_24d_26c.fillna(0) < GEOM_IOU)).sum()),
                     "usable_pop_iou26_le_0.5": int((hv.usable_match & (hv.pop_iou_24d_26c.fillna(0) <= 0.5)).sum()),
                     "usable_both_iou26_le_0.5": int((hv.usable_match & (hv.iou_24d_26c.fillna(0) <= 0.5)
                                                      & (hv.pop_iou_24d_26c.fillna(0) <= 0.5)).sum()),
                     "usable_not_geom_same": int((hv.usable_match & ~hv.geom_same_24_26).sum()),
                     "usable_and_geom_same": int(hv.usable_match_geom.sum()),
                     "votes_share_usable_geom_same": hv.loc[hv.usable_match_geom, "total"].sum() / hv.total.sum()})
    R = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(R.T.to_string(header=[f"NY-{c}" for c in R.cd], float_format=lambda x: f"{x:.3f}"))


if __name__ == "__main__":
    main()
