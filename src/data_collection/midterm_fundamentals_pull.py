"""E4 inputs: national House vote, mean June Gallup approval and Q2 real GDP growth for every midterm 1950-2022, plus 2026.

The 2026 results plan (report/results_2026_analysis_plan.md: Phase 1 step 2, "E4", and "E4. A midterm fundamentals
check") regresses the president's party's two-party national House vote in each midterm from 1950 to 2022 on the mean
June Gallup approval of the president and second-quarter GDP growth, tested leave-one-out, to predict 2026. This script
assembles those inputs. It fits nothing.

Usage, from the repo root (project venv, `python -I`):
    python src/data_collection/midterm_fundamentals_pull.py --download   # save any source file not yet saved, then build
    python src/data_collection/midterm_fundamentals_pull.py              # rebuild the outputs from the saved files only
    ... --download --refresh-fred                                        # also save a new dated FRED vintage (the build
                                                                         # uses the newest saved pull and names it)

Raw files (data/raw/e4/, gitignored; each has a <name>.meta.json sidecar with URL, UTC retrieval time, bytes and SHA-256;
nothing is ever overwritten):
    clerk/       Clerk of the House, "Statistics of the Congressional Election", one PDF per midterm 1950-2022
                 (history.house.gov/Institution/Election-Statistics/<year>election/). The national figures are the
                 "Total" row of the "Recapitulation of Votes Cast for (U.S.) Representatives" table near the end.
                 1998-2022 have a text layer, read with `pdftotext -raw`. 1950-1994 are page scans with no text layer
                 (HP ScanJet, 1998); their total rows were read by eye from the page images, rotated and enlarged, and
                 are transcribed in CLERK_SCANNED below together with the file's SHA-256, the page and every column, so
                 the transcription is tied to the exact saved file and checked by arithmetic.
    app/         American Presidency Project Gallup approval tables (presidency.ucsb.edu/statistics/data/<president>-
                 public-approval), the source notebook 02 uses; plus the "All Data" page (which says when Gallup stopped)
                 and the 2024 election page (party of the 2026 president).
    fred/        FRED GDPC1 (real GDP, the series and definition of notebook 02 and fred_pull.py), raw JSON, date-stamped;
                 and A191RL1Q225SBEA (BEA's own annualized growth rate), used only as a cross-check.
    brookings/   Vital Statistics on Congress (April 2026 release): table 2-2 (popular vote by party, the secondary
                 cross-check) and 2-4 (the president's party in each midterm).
    fec/         FEC "Federal Elections" summary tables for 2006 and 2014, a tie-breaker for the two years in which the
                 Clerk and Brookings differ most.
    house/       House History, "Presidents, Vice Presidents, & Coinciding Sessions of Congress" (who was president when).

Outputs:
    data/raw/e4/midterms_1950_2026.csv     one row per year (1950, 1954, ..., 2022, 2026), a source column per field
    data/raw/e4/house_vote_crosscheck.csv  Clerk vs Brookings (and FEC where saved), two-party Democratic share

Checks run on every build: each Clerk total row's columns must add to its printed total (or to the documented,
re-read source inconsistency); for 1998-2022 the 50 state rows must add to the national D and R; the scanned PDFs
must match the SHA-256 they were transcribed from; the June rule must reproduce notebook 02's own June readings;
the Q2 growth is printed beside BEA's published rate and beside fred_pull.py's earlier GDPC1 pull.

House vote conventions are the Clerk's, used as printed: party-line columns (in New York, Liberal, Conservative,
Working Families etc. lines are not added to the Democratic or Republican candidate's total); states that do not
tabulate unopposed candidates contribute nothing for those seats; in 2002 and 2014 the Clerk's footnotes say Louisiana
is counted from its December runoff where one was held;
some states' totals include blank, void, under- or over-votes, so total_votes is the Clerk's printed total.

Rules copied from notebook 02 (notebooks/02_fundamentals_model.ipynb):
    June approval: "every Gallup reading whose fieldwork ended in June of the election year, in field order", and the
        model uses their mean. So a reading counts if its END date is in June: one spanning May-June counts, one spanning
        June-July does not. One June reading -> its value. No June reading -> no value (notebook 02 has no such year;
        its lookup returns NaN). The rule is verified below against notebook 02's own list for all 20 presidential years.
    Q2 growth: ((Q2 / Q1) ** 4 - 1) * 100 on GDPC1, Q1 and Q2 of the same year.

The 2026 House vote is left empty (Phase 3). No 2026 election result of any kind is downloaded here.
"""
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import ast
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import pandas as pd

RAW = Path("data/raw/e4")
OUT = RAW / "midterms_1950_2026.csv"
OUT_CHECK = RAW / "house_vote_crosscheck.csv"
NB02 = Path("notebooks/02_fundamentals_model.ipynb")
OLD_FRED_GDPC1 = Path("data/raw/fred/GDPC1.csv")  # fred_pull.py's earlier pull, read only, for the vintage comparison

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MIDTERMS = list(range(1950, 2023, 4))  # 1950, 1954, ..., 2022
YEARS = MIDTERMS + [2026]
TEXT_YEARS = [y for y in MIDTERMS if y >= 1998]

# ---------------------------------------------------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------------------------------------------------
CLERK_INDEX = "https://history.house.gov/Institution/Election-Statistics/Election-Statistics/"
CLERK_PDF = "https://history.house.gov/Institution/Election-Statistics/{year}election/"
APP_BASE = "https://www.presidency.ucsb.edu/statistics/data/"
APP_ALL = "presidential-job-approval-all-data"
APP_2024 = "https://www.presidency.ucsb.edu/statistics/elections/2024"
HOUSE_PRESIDENTS = "https://history.house.gov/Institution/Presidents-Coinciding/Presidents-Coinciding/"
BROOKINGS = {
    "brookings_vital_statistics_page.html": "https://www.brookings.edu/articles/vital-statistics-on-congress/",
    "2-2.csv": "https://www.brookings.edu/wp-content/uploads/2026/04/2-2.csv",
    "2-2-Full.pdf": "https://www.brookings.edu/wp-content/uploads/2026/04/2-2-Full.pdf",
    "2-4.csv": "https://www.brookings.edu/wp-content/uploads/2026/04/2-4.csv",
    "2-4-Full.pdf": "https://www.brookings.edu/wp-content/uploads/2026/04/2-4-Full.pdf",
}
FEC = {
    "fec_results_index.html": "https://www.fec.gov/introduction-campaign-finance/election-results-and-voting-information/",
    "2006tables.pdf": "https://www.fec.gov/documents/1640/2006tables.pdf",
    "tables2014.pdf": "https://www.fec.gov/documents/1703/tables2014.pdf",
}
FEC_TABLES = {2006: "2006tables.pdf", 2014: "tables2014.pdf"}
FRED_SERIES = ["GDPC1", "A191RL1Q225SBEA"]

# APP table of each president, keyed by the name as the House History page writes it.
APP_SLUG = {
    "Harry S. Truman": "harry-s-truman", "Dwight D. Eisenhower": "dwight-d-eisenhower",
    "John F. Kennedy": "john-f-kennedy", "Lyndon B. Johnson": "lyndon-b-johnson",
    "Richard M. Nixon": "richard-m-nixon", "Gerald R. Ford": "gerald-r-ford",
    "James Earl “Jimmy” Carter": "jimmy-carter", "Ronald Reagan": "ronald-reagan",
    "George H.W. Bush": "george-bush", "William J. Clinton": "william-j-clinton", "George W. Bush": "george-w-bush",
    "Barack Obama": "barack-obama", "Joseph R. Biden Jr.": "joseph-r-biden",
}
APP_SLUGS = sorted(set(APP_SLUG.values()) | {"donald-j-trump", "donald-j-trump-2nd-term"})


def app_slug(name, year):
    if name == "Donald J. Trump":
        return "donald-j-trump" if year < 2025 else "donald-j-trump-2nd-term"
    return APP_SLUG[name]


# ---------------------------------------------------------------------------------------------------------------------
# Clerk national totals for the scanned years (no text layer). Read by eye from the page images (rotated 90 degrees,
# cropped and enlarged to about 2x); every column of the total row is transcribed so the arithmetic can be checked.
# page = 1-based page of the PDF file; printed = page number printed on it. `excluded`: columns the table's own note
# keeps out of the Total ("Blank and void ballots excluded from all totals"). `check_diff` = printed Total minus the
# sum of the counted columns, as found on the page (non-zero in two years: an inconsistency in the source, re-read at
# higher magnification; the digits are unambiguous).
# ---------------------------------------------------------------------------------------------------------------------
CLERK_SCANNED = {
    1950: dict(sha256="1d08ba968be04e85c3b49ca5df291202cae689a9a6946cc43556d3f80b68023a", page=43, printed=42,
               label="Total, by States", total=40429556, excluded=[], check_diff=0,
               columns=[("Democrat", 19785122), ("Republican", 19750393), ("Independent", 119634),
                        ("Socialist", 4626), ("Progressive", 127715), ("Prohibition", 34761),
                        ("Socialist Workers", 2484), ("Scattering", 1275), ("American Labor", 225368),
                        ("Liberal", 279168), ("Other", 99010)]),
    1954: dict(sha256="0e48e4f7e65fba9e9083f1d07510fad4d7b0214214ff077606ea7acf5c1589dc", page=46, printed=45,
               label="Total, by States", total=42582927, excluded=["Blank", "Void"], check_diff=0,
               columns=[("Democrat", 22177088), ("Republican", 20034763), ("Prohibition", 8591),
                        ("Socialist Labor", 1652), ("Independent", 74486), ("Liberal", 251290), ("Other", 27367),
                        ("Scattering", 7688), ("Blank", 400427), ("Void", 165), ("Write-in", 2)]),
    1958: dict(sha256="8dd37d1af65a82bb74e15e5cb9a8f2fd8c1622b03260025e07d8fc8f94e7a214", page=45, printed=44,
               label="Total, by States", total=45718994, excluded=["Blank"], check_diff=-10,
               columns=[("Democrat", 25365961), ("Republican", 19943882), ("Prohibition", 8816),
                        ("Independent", 30503), ("Liberal", 297650), ("Conservative", 3444),
                        ("Socialist Labor", 8097), ("Blank", 176636), ("Write-in", 36409), ("Others", 15776),
                        ("Scattering", 8466)]),
    1962: dict(sha256="e821448f48e99da3b333e57488242201354fd7a4c0a378f8a53285ce5ca2929f", page=46, printed=45,
               label="Total, by States", total=51242188, excluded=[], check_diff=0,
               columns=[("Democrat", 26694634), ("Republican", 24160387), ("Independent", 79684),
                        ("Liberal", 259758), ("Prohibition", 17171), ("Socialist Labor", 2611),
                        ("Socialist Workers", 730), ("Other", 8074), ("Scattering", 6869), ("Write-in", 12270)]),
    1966: dict(sha256="aec363c37e6d15742f91e3545f99508eda507c8aff57dea923f08ff2c923330c", page=51, printed=50,
               label="Total, by States", total=52901975, excluded=[], check_diff=0,
               columns=[("Democrat", 26712142), ("Republican", 25408798), ("Independent", 85641),
                        ("Conservative", 297110), ("Liberal", 315556), ("Peace and Freedom", 6641),
                        ("American Independent", 14461), ("Other", 41925), ("Scattering", 19114), ("Write-in", 587)]),
    1970: dict(sha256="2f60f275ddca0efea603f4b990f0dcff2064cc6f8df1c22569541540fc7e3fd7", page=42, printed=41,
               label="Total", total=54258885, excluded=[], check_diff=0,
               columns=[("Democrat", 28781048), ("Republican", 24121959), ("American Independent", 130568),
                        ("Peace and Freedom", 40763), ("Socialist Workers", 9675), ("Socialist Labor", 973),
                        ("Liberal", 285071), ("Conservative", 536628), ("Independent", 122430),
                        ("Scattering", 22053), ("Others", 207717)]),
    1974: dict(sha256="5903a8a73acd03f1679bdf92db418488ecf3bb99109b9d143aa3010e59d5d15d", page=46, printed=45,
               label="Total", total=52313457, excluded=[], check_diff=-800,
               columns=[("Democrat", 29872842), ("Republican", 21165583), ("American", 238265),
                        ("Independent", 340501), ("Prohibition", 8387), ("Conservative", 297642),
                        ("United States Labor", 26342), ("Socialist Labor", 10564), ("Socialist Workers", 13982),
                        ("Liberal", 177642), ("Others", 153728), ("Write-in", 8779)]),
    1978: dict(sha256="687bbdf80589978d23d23b99bf4466ac90e88117e1305bb66c3bd0895234bebd", page=44, printed=43,
               label="Total", total=54583922, excluded=[], check_diff=0,
               columns=[("Democrat", 29129007), ("Republican", 24401021), ("American Independent", 74765),
                        ("Socialist Workers", 19530), ("Socialist Labor", 2434), ("Libertarian", 64310),
                        ("American", 34110), ("Independent", 344272), ("Write-in", 2260), ("Scattering", 496),
                        ("Others", 511717)]),
    1982: dict(sha256="eb3a4397ea768e622f5c467c8a456b0ac61448a6d6d2d1c0e755dfab964d4baf", page=50, printed=49,
               label="Total", total=63880844, excluded=[], check_diff=0,
               columns=[("Democrat", 35126406), ("Republican", 27606014), ("Libertarian", 462277),
                        ("Independent", 120476), ("Citizens", 29248), ("Socialist Workers", 14360),
                        ("American", 2138), ("Constitution", 1597), ("Other", 509442), ("Write-in", 8886)]),
    1986: dict(sha256="6f15503186edbc66a1c3f1bca63f4e7d74493c04610ad01d6aaf2579b2909cd2", page=47, printed=46,
               label="Total", total=59758397, excluded=[], check_diff=0,
               columns=[("Democratic", 32338342), ("Republican", 26384083), ("Libertarian", 121076),
                        ("Independent", 157332), ("Citizens", 8386), ("Socialist Workers", 12812),
                        ("American", 19625), ("Other Parties", 433698),
                        ("Other (Scattering, Write-ins, etc.)", 283043)]),
    1990: dict(sha256="7024f5bd47b5109cb3a8bd79ac9344bdfc01f09217fed8ce9049c09cb39c9437", page=49, printed=48,
               label="Total", total=62354853, excluded=[], check_diff=0,
               columns=[("Democratic", 32397732), ("Republican", 27402036), ("Independent", 367603),
                        ("Libertarian", 444750), ("Populist", 51894), ("New Alliance", 14466),
                        ("Socialist Workers", 8433), ("Other Parties", 622242),
                        ("Other (Scattering, Write-ins, etc.)", 1045697)]),
    1994: dict(sha256="0e0337bd4dde9bb656e42633aae2ae8cdbb8ae5895db65e1ef2728746518e2b6", page=49, printed=48,
               label="Total", total=70493648, excluded=[], check_diff=0,
               columns=[("Republican", 36325809), ("Democratic", 31542823), ("Independent", 497403),
                        ("Libertarian", 415944), ("Conservative", 302735), ("Natural Law", 62556),
                        ("Green", 40177), ("Grassroots", 11960), ("Socialist Workers", 3927),
                        ("Other Parties", 538249), ("Other (Scattering, Write-ins, etc.)", 752065)]),
}
# Column order of the text-layer years as read on the page (the Clerk puts the new majority first in some years);
# the parser reads the order from the header and must agree.
CLERK_TEXT_ORDER = {1998: "RD", 2002: "RD", 2006: "DR", 2010: "RD", 2014: "RD", 2018: "DR", 2022: "RD"}
STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida",
          "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine",
          "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska",
          "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
          "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas",
          "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]
ABBR = dict(zip(STATES, "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
                        "NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()))
RECAP_HEAD = "Recapitulation of Votes Cast for United States Representatives"


# ---------------------------------------------------------------------------------------------------------------------
# Download (only with --download). curl for web pages and PDFs (some of these sites refuse python-requests);
# requests for the FRED API, whose key is never printed, logged or put in an error message.
# ---------------------------------------------------------------------------------------------------------------------
def _sha256(b):
    return hashlib.sha256(b).hexdigest()


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_new(dest, body, meta):
    """Save a raw download and its sidecar metadata. Never overwrites an existing file."""
    if dest.exists():
        raise FileExistsError(f"{dest} already exists; raw files are never overwritten")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    tmp.write_bytes(body)
    tmp.rename(dest)
    meta = dict(meta, file=dest.name, bytes=len(body), sha256=_sha256(body))
    dest.with_name(dest.name + ".meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return meta


def fetch_curl(url, dest):
    if dest.exists():
        print(f"  have {dest}")
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".curl")
    cmd = ["curl", "-sS", "-L", "--compressed", "--retry", "3", "--max-time", "300", "-A", UA,
           "-o", str(tmp), "-w", "%{http_code}\t%{url_effective}\t%{content_type}", url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    code, final, ctype = (r.stdout.split("\t") + ["", "", ""])[:3]
    if r.returncode != 0 or code != "200":
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"download failed: {url} -> HTTP {code or '?'} (curl exit {r.returncode})")
    body = tmp.read_bytes()
    tmp.unlink()
    meta = _write_new(dest, body, {"url": url, "final_url": final, "http_status": int(code), "content_type": ctype,
                                   "retrieved_utc": _now(), "tool": "curl"})
    print(f"  saved {dest} ({meta['bytes']:,} bytes)")
    return meta


def fetch_fred(series_id, refresh=False):
    """Save FRED's raw JSON (series metadata and every observation of the current vintage), stamped with the UTC date.
    An existing pull is kept and reused unless refresh=True (--refresh-fred), which adds a new dated pull beside it."""
    existing = _fred_files(series_id, "observations")
    if existing and not refresh:
        print(f"  have {existing[-1]} (use --refresh-fred for a new vintage)")
        return
    import requests
    from dotenv import dotenv_values
    key = dotenv_values(".env").get("FRED_API_KEY") or os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("FRED_API_KEY is not set in .env")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    for kind, path in [("series", "series"), ("observations", "series/observations")]:
        dest = RAW / "fred" / f"{series_id}_{kind}_{stamp}.json"
        if dest.exists():
            print(f"  have {dest}")
            continue
        public_url = f"https://api.stlouisfed.org/fred/{path}?series_id={series_id}&file_type=json"
        try:
            r = requests.get(f"https://api.stlouisfed.org/fred/{path}",
                             params={"series_id": series_id, "file_type": "json", "api_key": key}, timeout=120)
            status, body, ctype = r.status_code, r.content, r.headers.get("Content-Type", "")
        except Exception as e:  # never echo the exception: its text can contain the request URL, key included
            raise RuntimeError(f"FRED request for {series_id} {kind} failed ({type(e).__name__})") from None
        if status != 200:
            raise RuntimeError(f"FRED request for {series_id} {kind} returned HTTP {status}")
        json.loads(body.decode("utf-8"))
        meta = _write_new(dest, body, {"url": public_url + " (plus api_key, not recorded)", "http_status": status,
                                       "content_type": ctype, "retrieved_utc": _now(), "tool": "requests"})
        print(f"  saved {dest} ({meta['bytes']:,} bytes)")


def download():
    print("Clerk of the House election statistics:")
    fetch_curl(CLERK_INDEX, RAW / "clerk" / "election_statistics_index.html")
    for y in MIDTERMS:
        fetch_curl(CLERK_PDF.format(year=y), RAW / "clerk" / f"{y}election.pdf")
    print("American Presidency Project:")
    fetch_curl(APP_BASE + APP_ALL, RAW / "app" / f"{APP_ALL}.html")
    for s in APP_SLUGS:
        fetch_curl(APP_BASE + s + "-public-approval", RAW / "app" / f"{s}-public-approval.html")
    fetch_curl(APP_2024, RAW / "app" / "elections-2024.html")
    print("House History, presidents and coinciding Congresses:")
    fetch_curl(HOUSE_PRESIDENTS, RAW / "house" / "presidents_coinciding.html")
    print("Brookings Vital Statistics on Congress:")
    for name, url in BROOKINGS.items():
        fetch_curl(url, RAW / "brookings" / name)
    print("FEC Federal Elections tables:")
    for name, url in FEC.items():
        fetch_curl(url, RAW / "fec" / name)
    print("FRED:")
    for s in FRED_SERIES:
        fetch_fred(s, refresh="--refresh-fred" in sys.argv)


# ---------------------------------------------------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------------------------------------------------
def meta(path):
    return json.loads(Path(str(path) + ".meta.json").read_text(encoding="utf-8"))


def sha256_file(path):
    return _sha256(Path(path).read_bytes())


def pdf_pages(path):
    import pypdf
    return len(pypdf.PdfReader(str(path)).pages)


def pdftotext_raw(path, page):
    r = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-raw", str(path), "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"pdftotext failed on {path} p{page}")
    return r.stdout


def _int(s):
    return int(s.replace(",", ""))


class _Tables(HTMLParser):
    """Every <table> as a list of rows of cell text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self._rows, self._row, self._cell, self._depth = [], None, None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._depth += 1
            if self._depth == 1:
                self._rows = []
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th"):
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._rows is not None:
                self._rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._depth -= 1
            if self._depth == 0 and self._rows is not None:
                self.tables.append(self._rows)
                self._rows = None

    def handle_data(self, d):
        if self._cell is not None:
            self._cell.append(d)


def html_tables(path):
    p = _Tables()
    p.feed(Path(path).read_text(encoding="utf-8", errors="replace"))
    return p.tables


def html_text(path):
    t = Path(path).read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    import html as _h
    return re.sub(r"\s+", " ", _h.unescape(t))


# --- Clerk -----------------------------------------------------------------------------------------------------------
def clerk_scanned(year):
    t = CLERK_SCANNED[year]
    f = RAW / "clerk" / f"{year}election.pdf"
    if sha256_file(f) != t["sha256"]:
        raise RuntimeError(f"{f} is not the file the {year} total row was transcribed from (SHA-256 differs)")
    cols = dict(t["columns"])
    if len(cols) != len(t["columns"]):
        raise RuntimeError(f"{year}: duplicate column names in the transcription")
    counted = sum(v for k, v in t["columns"] if k not in t["excluded"])
    diff = t["total"] - counted
    if diff != t["check_diff"]:
        raise RuntimeError(f"{year}: printed total minus counted columns is {diff}, transcription says {t['check_diff']}")
    dem = next(v for k, v in t["columns"] if k.startswith("Democrat"))
    rep = next(v for k, v in t["columns"] if k.startswith("Republican"))
    order = "".join("D" if k.startswith("Democrat") else "R" for k, _ in t["columns"][:2])
    return dict(dem=dem, rep=rep, total=t["total"], page=t["page"], printed=t["printed"], label=t["label"],
                check_diff=diff, n_columns=len(t["columns"]), excluded=t["excluded"], order=order,
                method="page scan without a text layer; total row read by eye from the page image and transcribed")


def _recap_pages(f):
    n = pdf_pages(f)
    return [p for p in range(max(1, n - 12), n + 1) if RECAP_HEAD in pdftotext_raw(f, p)]


def _state_rows(text, order):
    """Democratic and Republican cells of each state row of the national recap (raw text). Blank cells are dot runs;
    a 1-2 digit token followed by a number is a footnote marker (e.g. North Dakota's Democratic-NPL in 1998)."""
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Za-z .]+?)\s*(\d{1,2})?\s*\.{3,}\s*(.*)$", line)
        if not m or m.group(1).strip() not in STATES:
            continue
        toks, cells, i = m.group(3).split(), [], 0
        while i < len(toks) and len(cells) < 2:
            t = toks[i]
            if re.fullmatch(r"\.{3,}", t):
                cells.append(0)
                i += 1
            elif re.fullmatch(r"\d{1,2}", t) and i + 1 < len(toks) and re.fullmatch(r"[\d,]+", toks[i + 1]):
                cells.append(_int(toks[i + 1]))
                i += 2
            elif re.fullmatch(r"[\d,]+", t):
                cells.append(_int(t))
                i += 1
            else:
                raise RuntimeError(f"unreadable state row: {line[:120]}")
        a, b = cells
        out[m.group(1).strip()] = (a, b) if order == "DR" else (b, a)
    return out


def clerk_text(year):
    f = RAW / "clerk" / f"{year}election.pdf"
    pages = _recap_pages(f)
    if not pages:
        raise RuntimeError(f"{year}: national House recapitulation not found")
    text = "\n".join(pdftotext_raw(f, p) for p in pages)
    # column order from the header: whichever of Republican / Democratic comes first after "State"
    hdr = text[text.index("State"):]
    hdr = hdr[:hdr.index("Alabama")]
    ir, idd = hdr.find("Repub"), hdr.find("Demo")
    order = "RD" if ir < idd else "DR"
    if order != CLERK_TEXT_ORDER[year]:
        raise RuntimeError(f"{year}: header order {order} differs from the order read on the page")
    tot = [ln for ln in text.splitlines() if re.match(r"^\s*Total\s*\.{3,}\s*[\d,]", ln)]
    if len(tot) != 1:
        raise RuntimeError(f"{year}: expected one national Total line, found {len(tot)}")
    nums = [_int(x) for x in re.findall(r"\d[\d,]*", tot[0].split("..")[-1])]
    total, parts = nums[-1], nums[:-1]
    if sum(parts) != total:
        raise RuntimeError(f"{year}: columns sum to {sum(parts)}, printed total {total}")
    a, b = parts[0], parts[1]
    dem, rep = (a, b) if order == "DR" else (b, a)
    rows = _state_rows(text, order)
    if len(rows) != 50:
        raise RuntimeError(f"{year}: {len(rows)} state rows read, expected 50")
    sd, sr = sum(v[0] for v in rows.values()), sum(v[1] for v in rows.values())
    head = re.search(r"Election of ([A-Za-z.]+ \d{1,2}, \d{4})", text)
    return dict(dem=dem, rep=rep, total=total, page=pages[-1], printed=None, label="Total", check_diff=0,
                n_columns=len(parts), excluded=[], order=order, state_sum_dem=sd, state_sum_rep=sr, state_rows=rows,
                election=head.group(1) if head else None,
                method="text layer (pdftotext -raw); party columns sum to the printed total")


def clerk(year):
    return clerk_scanned(year) if year in CLERK_SCANNED else clerk_text(year)


# --- American Presidency Project ---------------------------------------------------------------------------------------
_DATE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def _date(s):
    m = _DATE.match(s.strip())
    return date(int(m.group(3)), int(m.group(1)), int(m.group(2))) if m else None


def app_readings(slug):
    """All readings in an APP approval table: start, end, approving and (2nd Trump term only) source."""
    f = RAW / "app" / f"{slug}-public-approval.html"
    for rows in html_tables(f):
        if not rows:
            continue
        hdr = [re.sub(r"[^a-z]", "", c.lower()) for c in rows[0]]
        if "startdate" in hdr and "enddate" in hdr and "approving" in hdr:
            break
    else:
        raise RuntimeError(f"{f}: no approval table")
    i_s, i_e, i_a = hdr.index("startdate"), hdr.index("enddate"), hdr.index("approving")  # first occurrences
    i_src = hdr.index("source") if "source" in hdr else None
    out, bad = [], []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        s, e = (_date(r[i_s]) if len(r) > i_s else None), (_date(r[i_e]) if len(r) > i_e else None)
        a = r[i_a].strip() if len(r) > i_a else ""
        if s is None or e is None or not re.fullmatch(r"\d{1,3}", a):
            bad.append(r)
            continue
        src = r[i_src].strip() if i_src is not None and len(r) > i_src else ""
        out.append(dict(start=s, end=e, approving=int(a), source=src))
    df = pd.DataFrame(out).sort_values(["start", "end"]).reset_index(drop=True)
    return df, bad


def june_readings(df, year, gallup_only):
    """Notebook 02's rule: every reading whose fieldwork ENDED in June of `year`, in field order."""
    j = df[(df["end"].map(lambda d: d.year) == year) & (df["end"].map(lambda d: d.month) == 6)]
    if gallup_only:
        j = j[j["source"].str.strip().str.lower() == "gallup"]
    return j


def nb02_june_readings():
    """notebook 02's own gallup_june_readings dict, read from the notebook (literal_eval only; nothing is executed)."""
    nb = json.loads(NB02.read_text(encoding="utf-8"))
    src = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    m = re.search(r"gallup_june_readings\s*=\s*(\{.*?\})", src, re.S)
    return ast.literal_eval(m.group(1))


# --- House History: who was president ----------------------------------------------------------------------------------
_MON = {m: i for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def _hdate(s):
    s = s.strip()
    if s.lower().startswith("present"):
        return date(9999, 12, 31)
    m = re.match(r"([A-Z][a-z]{2})[a-z]*\.?\s+(\d{1,2}),\s*(\d{4})", s)
    return date(int(m.group(3)), _MON[m.group(1)], int(m.group(2)))


def presidents():
    f = RAW / "house" / "presidents_coinciding.html"
    out = []
    for rows in html_tables(f):
        for r in rows:
            if len(r) >= 4 and re.search(r"\d{4}", r[3]) and re.search(r"[A-Za-z]", r[1]):
                parts = re.split(r"\s*[–—-]\s*|\s*�\s*", r[3])
                parts = [p for p in parts if p]
                if len(parts) != 2:
                    continue
                name = re.sub(r"\s*\d+$", "", r[1]).strip()
                out.append(dict(name=name, start=_hdate(parts[0]), end=_hdate(parts[1])))
    return out


def president_on(plist, d):
    hits = {p["name"] for p in plist if p["start"] <= d < p["end"]}
    if len(hits) != 1:
        raise RuntimeError(f"president on {d}: {hits}")
    return hits.pop()


def president_in(plist, year, month):
    """The president for the whole month (first and last day must agree)."""
    first = date(year, month, 1)
    last = date(year, month, 30)
    a, b = president_on(plist, first), president_on(plist, last)
    if a != b:
        raise RuntimeError(f"president changes during {year}-{month:02d}: {a} / {b}")
    return a


# --- FRED -------------------------------------------------------------------------------------------------------------
def _fred_files(series_id, kind):
    return sorted(p for p in (RAW / "fred").glob(f"{series_id}_{kind}_*.json") if not p.name.endswith(".meta.json"))


def fred_latest(series_id):
    obs, ser = _fred_files(series_id, "observations"), _fred_files(series_id, "series")
    if not obs or not ser:
        raise RuntimeError(f"no saved FRED pull of {series_id}; run with --download")
    o, s = obs[-1], ser[-1]
    d = json.loads(o.read_text(encoding="utf-8"))
    info = json.loads(s.read_text(encoding="utf-8"))["seriess"][0]
    vals = {}
    for x in d["observations"]:
        vals[x["date"]] = float(x["value"]) if x["value"] not in (".", "") else math.nan
    return vals, dict(file=o.name, pulled_utc=meta(o)["retrieved_utc"], realtime=f"{d['realtime_start']}..{d['realtime_end']}",
                      last_updated=info["last_updated"], units=info["units"], title=info["title"])


def q2_growth(vals, year):
    """Notebook 02: ((Q2 / Q1) ** 4 - 1) * 100, real GDP, Q1 and Q2 of the same year."""
    q1, q2 = vals.get(f"{year}-01-01"), vals.get(f"{year}-04-01")
    if q1 is None or q2 is None or math.isnan(q1) or math.isnan(q2):
        return None, q1, q2
    return ((q2 / q1) ** 4 - 1) * 100, q1, q2


# --- Brookings, FEC -----------------------------------------------------------------------------------------------------
def brookings(name):
    return pd.read_csv(RAW / "brookings" / name, encoding="utf-8-sig").dropna(subset=["Year"]).astype({"Year": int})


def _fec_table_text(year):
    f = RAW / "fec" / FEC_TABLES[year]
    for p in range(1, pdf_pages(f) + 1):
        t = pdftotext_raw(f, p)
        if f"{year} VOTES CAST FOR THE U.S. HOUSE OF REPRESENTATIVES BY PARTY" in t:
            return t, p, f
    raise RuntimeError(f"{f}: House by-party table not found")


def fec_house_totals(year):
    """General-election Democratic and Republican House votes from the FEC table "<year> VOTES CAST FOR THE U.S. HOUSE OF
    REPRESENTATIVES BY PARTY" (last three numbers of its Total row: general D, R, other). The FEC's totals include the
    delegates of DC and the territories, and (its notes say) same-day unexpired-term elections and December runoffs."""
    t, p, f = _fec_table_text(year)
    tot = [ln for ln in t.splitlines() if ln.startswith("Total:")]
    nums = [_int(x) for x in re.findall(r"\d[\d,]*", tot[0])]
    return dict(dem=nums[-3], rep=nums[-2], other=nums[-1], page=p, file=f.name)


def fec_vs_clerk_states(year, clerk_rows):
    """States whose FEC row does not contain the Clerk's (D, R) pair as its general-election D and R. A row lists primary
    then general numbers and omits empty cells, so the general pair is either the last two or the two before the last."""
    t, _, _ = _fec_table_text(year)
    fec = {}
    for ln in t.splitlines():
        m = re.match(r"^([A-Z]{2})\s+([\d,\s]+)$", ln.strip())
        if m:
            fec[m.group(1)] = [_int(x) for x in m.group(2).split()]
    out = []
    for st, (d, r) in clerk_rows.items():
        nums = fec.get(ABBR[st], [])
        pairs = [tuple(nums[k:k + 2]) for k in (len(nums) - 3, len(nums) - 2) if k >= 0]
        if (d, r) not in pairs:
            out.append((ABBR[st], (d, r), nums))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------------------------------
def pct(a, b):
    return 100.0 * a / (a + b)


def build():
    # Presidents and parties
    plist = presidents()
    party_tbl = brookings("2-4.csv").set_index("Year")["PresidentParty"].to_dict()
    app2024 = html_text(RAW / "app" / "elections-2024.html")
    if not re.search(r"DONALD J\. TRUMP\s+Republican", app2024):
        raise RuntimeError("elections-2024.html does not show Donald J. Trump as the Republican nominee")

    # Gallup tables
    readings, unparsed = {}, {}
    for s in APP_SLUGS:
        readings[s], unparsed[s] = app_readings(s)

    # Rule check against notebook 02 (presidential years)
    nb = nb02_june_readings()
    mismatches = []
    for y, want in sorted(nb.items()):
        slug = app_slug(president_in(plist, y, 6), y)
        got = june_readings(readings[slug], y, gallup_only=False)["approving"].tolist()
        if got != list(want):
            mismatches.append((y, want, got))
    print(f"Notebook 02 June rule reproduced for {len(nb) - len(mismatches)} of {len(nb)} presidential years"
          + (f"; MISMATCHES: {mismatches}" if mismatches else ""))

    # GDP
    gdp, gdp_info = fred_latest("GDPC1")
    bea, bea_info = fred_latest("A191RL1Q225SBEA")

    all_note = html_text(RAW / "app" / f"{APP_ALL}.html")
    gallup_stop = re.search(r"Since Gallup discontinued presidential approval polls[^.]*\.", all_note)

    rows, checks, fec_state_diffs, straddles = [], [], {}, {}
    b22 = brookings("2-2.csv").set_index("Year")
    for y in YEARS:
        pres = president_in(plist, y, 11)  # serving in November, the month of every midterm
        jpres = president_in(plist, y, 6)
        if y in party_tbl:
            party, party_src = party_tbl[y], "Brookings Vital Statistics on Congress table 2-4 (brookings/2-4.csv), PresidentParty"
        elif y == 2026 and pres == "Donald J. Trump":
            party, party_src = "R", "APP 2024 election results page (app/elections-2024.html): Donald J. Trump, Republican"
        else:
            raise RuntimeError(f"no party source for {y}")
        notes = []
        if jpres != pres:
            notes.append(f"June approval is {jpres}'s ({jpres} was president in June; {pres} in November); same party")

        # House vote
        if y in MIDTERMS:
            c = clerk(y)
            dem, rep, total = c["dem"], c["rep"], c["total"]
            f = RAW / "clerk" / f"{y}election.pdf"
            src = (f"Clerk of the House, Statistics of the Congressional Election ({y}), national recapitulation of "
                   f"votes for Representatives, '{c['label']}' row, PDF page {c['page']}"
                   + (f" (printed p. {c['printed']})" if c["printed"] else "")
                   + f"; clerk/{f.name}, {meta(f)['final_url']}; {c['method']}")
            excl = f", excluding {' and '.join(c['excluded'])} as the table's note says" if c["excluded"] else ""
            if c["check_diff"] == 0:
                check = f"the {c['n_columns']} vote columns{excl} sum to the printed total"
            else:
                check = (f"the printed total ({total:,}) is {abs(c['check_diff']):,} "
                         f"{'less' if c['check_diff'] < 0 else 'more'} than the sum of the {c['n_columns']} vote columns"
                         f"{excl} ({total - c['check_diff']:,}): an inconsistency in the source, digits re-read at higher "
                         f"magnification; D and R as printed")
                notes.append(f"Clerk total row does not add up by {abs(c['check_diff']):,} votes (see house_vote_check)")
            if "state_sum_dem" in c:
                ok = (c["state_sum_dem"] == dem and c["state_sum_rep"] == rep)
                check += ("; 50 state rows sum to the national D and R totals" if ok else
                          f"; STATE ROWS SUM TO D {c['state_sum_dem']:,} / R {c['state_sum_rep']:,}")
            d2 = pct(dem, rep)
            pp = d2 if party == "D" else 100 - d2
            b = b22.loc[y]
            bd2 = pct(b["DemPctVotes"], b["RepPctVotes"])
            lo = pct(b["DemPctVotes"] - 0.05, b["RepPctVotes"] + 0.05)
            hi = pct(b["DemPctVotes"] + 0.05, b["RepPctVotes"] - 0.05)
            ck = dict(year=y, clerk_dem=dem, clerk_rep=rep, clerk_dem2=round(d2, 3),
                      brookings_dem_pct=b["DemPctVotes"], brookings_rep_pct=b["RepPctVotes"],
                      brookings_dem2=round(bd2, 3), diff_brookings_minus_clerk=round(bd2 - d2, 3),
                      diff_range_given_rounding=f"{lo - d2:+.3f} to {hi - d2:+.3f}",
                      over_0_1pp=abs(bd2 - d2) > 0.1)
            if y in FEC_TABLES:
                fe = fec_house_totals(y)
                ck.update(fec_dem=fe["dem"], fec_rep=fe["rep"], fec_dem2=round(pct(fe["dem"], fe["rep"]), 3),
                          diff_fec_minus_clerk=round(pct(fe["dem"], fe["rep"]) - d2, 3))
                fec_state_diffs[y] = fec_vs_clerk_states(y, c["state_rows"])
            if ck["over_0_1pp"]:
                notes.append(f"Brookings two-party D {bd2:.3f} vs Clerk {d2:.3f} ({bd2 - d2:+.3f} pp; see "
                             f"house_vote_crosscheck.csv)" + (f"; FEC {ck['fec_dem2']:.3f}" if "fec_dem2" in ck else ""))
            checks.append(ck)
        else:
            dem = rep = total = None
            d2 = pp = None
            src = "empty: the 2026 national House vote comes in Phase 3 (plan step 13)"
            check = ""

        # June Gallup approval
        slug = app_slug(jpres, y)
        jr = june_readings(readings[slug], y, gallup_only=(y == 2026))
        vals = jr["approving"].tolist()
        rd = readings[slug]
        st = rd[(rd["start"].map(lambda d: (d.year, d.month)) != rd["end"].map(lambda d: (d.year, d.month)))
                & (((rd["start"].map(lambda d: d.year) == y) & (rd["start"].map(lambda d: d.month) == 6))
                   | ((rd["end"].map(lambda d: d.year) == y) & (rd["end"].map(lambda d: d.month) == 6)))]
        straddles[y] = [f"{r.start:%m/%d}-{r.end:%m/%d} {r.approving} "
                        f"{'counted' if r.end.month == 6 else 'not counted'}" for r in st.itertuples()]
        appr_src = f"APP Gallup table app/{slug}-public-approval.html ({APP_BASE}{slug}-public-approval); readings ending in June {y}"
        if y == 2026:
            all_june = june_readings(readings[slug], y, gallup_only=False)
            last_g = readings[slug][readings[slug]["source"].str.lower() == "gallup"]["end"].max()
            others = sorted(set(all_june["source"].str.strip()))
            appr_src += (f"; no Gallup reading: the table's last Gallup reading ended {last_g.isoformat()}, its "
                         f"{len(all_june)} June 2026 readings are from other pollsters ({'; '.join(others)}), not used")
            if gallup_stop:
                appr_src += f'; APP all-data page: "{gallup_stop.group(0).strip()}"'
        mean = sum(vals) / len(vals) if vals else None

        # GDP
        g, q1, q2 = q2_growth(gdp, y)
        bea_q2 = bea.get(f"{y}-04-01")
        gdp_src = (f"FRED GDPC1 ({gdp_info['title']}, {gdp_info['units']}), fred/{gdp_info['file']}, pulled "
                   f"{gdp_info['pulled_utc']}, FRED realtime {gdp_info['realtime']}, series last updated "
                   f"{gdp_info['last_updated']}; ((Q2/Q1)^4-1)*100 as in notebook 02. bea_q2_growth_check: FRED "
                   f"A191RL1Q225SBEA (BEA's published annualized Q2 growth, one decimal), fred/{bea_info['file']}")
        if y == 2026 and not vals:
            notes.append("no June 2026 Gallup reading in the APP table, whose all-data page says Gallup discontinued "
                         "presidential approval polls; approval left empty, no other pollster substituted")

        rows.append(dict(
            year=y, president=pres, president_party=party, june_president=jpres,
            president_source=f"House History, Presidents & Coinciding Sessions of Congress (house/presidents_coinciding.html, {HOUSE_PRESIDENTS}): serving in November and in June of {y}",
            party_source=party_src,
            dem_votes=dem, rep_votes=rep, total_votes=total,
            dem_two_party_pct=round(d2, 4) if d2 is not None else None,
            pres_party_two_party_pct=round(pp, 4) if pp is not None else None,
            house_vote_source=src, house_vote_check=check,
            gallup_june_readings=";".join(str(v) for v in vals), gallup_june_n=len(vals),
            gallup_june_mean=round(mean, 4) if mean is not None else None, approval_source=appr_src,
            gdp_q1=q1, gdp_q2=q2, gdp_q2_growth=round(g, 4) if g is not None else None,
            bea_q2_growth_check=bea_q2, gdp_source=gdp_src,
            notes="; ".join(notes)))

    df = pd.DataFrame(rows)
    for col in ["dem_votes", "rep_votes", "total_votes", "gallup_june_n"]:
        df[col] = df[col].astype("Int64")
    ck = pd.DataFrame(checks)
    for col in ["fec_dem", "fec_rep"]:
        if col in ck:
            ck[col] = ck[col].astype("Int64")
    df.to_csv(OUT, index=False)
    ck.to_csv(OUT_CHECK, index=False)

    # --- report --------------------------------------------------------------------------------------------------
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    print(f"\nWrote {OUT} ({len(df)} rows x {df.shape[1]} columns) and {OUT_CHECK}")
    print(df[["year", "president", "president_party", "june_president", "dem_votes", "rep_votes", "total_votes",
              "pres_party_two_party_pct", "gallup_june_readings", "gallup_june_n", "gallup_june_mean",
              "gdp_q2_growth", "bea_q2_growth_check"]].to_string(index=False))
    print("\nCross-check, two-party Democratic share (%):")
    print(ck.to_string(index=False))
    for y, diffs in fec_state_diffs.items():
        print(f"\n{y}: states whose FEC row lacks the Clerk's (D, R) pair [state, Clerk (D, R), FEC row numbers]:")
        for x in diffs:
            print(f"   {x[0]}  Clerk {x[1]}  FEC {x[2]}")
    print("\nReadings spanning a month boundary into or out of June (notebook 02 counts a reading by its end date):")
    for y, s in straddles.items():
        if s:
            print(f"   {y}: {'; '.join(s)}")
    for s, b in unparsed.items():
        if b:
            print(f"\n{s}: {len(b)} table rows not parsed as readings: {b}")
    dd = (df["gdp_q2_growth"] - df["bea_q2_growth_check"])
    print(f"\nGDPC1 growth minus BEA's published growth rate (A191RL1Q225SBEA, {bea_info['file']}, last updated "
          f"{bea_info['last_updated']}): max |diff| {dd.abs().max():.3f} pp over {dd.notna().sum()} years; by year "
          f"{dict(zip(df['year'], dd.round(3)))}")
    if OLD_FRED_GDPC1.exists():
        old = pd.read_csv(OLD_FRED_GDPC1, index_col=0, parse_dates=True).iloc[:, 0]
        oldv = {i.strftime("%Y-%m-%d"): v for i, v in old.items()}
        diffs = []
        for y in YEARS:
            a = q2_growth(oldv, y)[0]
            b = df.loc[df["year"] == y, "gdp_q2_growth"].iloc[0]
            if a is not None and b is not None and not pd.isna(b):
                diffs.append((y, round(b - a, 3)))
        print(f"Vintage check vs {OLD_FRED_GDPC1} (modified {datetime.fromtimestamp(OLD_FRED_GDPC1.stat().st_mtime):%Y-%m-%d}): "
              f"new minus old Q2 growth by year: {diffs}")
    return df, ck


if __name__ == "__main__":
    if "--download" in sys.argv:
        download()
    build()
