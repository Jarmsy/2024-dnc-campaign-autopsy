"""E1 case list: Justice Democrats' and national DSA's 2026 House endorsements, as they stand on the day this runs.

The 2026 results plan (report/results_2026_analysis_plan.md, Phase 1 step 1) fixes E1's set as every 2026
Democratic House nominee on these two lists, saved on the day the plan was committed (4 November 2026).

Sources:
  - Justice Democrats: https://justicedemocrats.com/candidates/ . One card per candidate, in two sections
    ("Upcoming Elections" = challengers and open seats, "Current Congressmembers" = incumbents). Each card
    carries the district as JD writes it and a status class: `won` (labelled "Primary Winner") or `lost`.
  - National DSA: https://electoral.dsausa.org/our-campaigns/ embeds an Airtable shared view, "Wordpress -
    Current Endorsements (DO NOT EDIT)". The embed page stashes a signed readSharedViewData URL; the rows are
    read from it with the headers the page's own script sends. Only rows whose Office Type includes "Federal"
    are kept. The "Past Endorsements" view (/our-campaigns/past-endorsements/) is read too, to confirm that no
    2026 federal endorsement has been moved there.

Writes:
  data/raw/e1_endorsements/<source>_<UTC stamp>.{html,json}   raw responses (gitignored)
  data/coded/e1_endorsements_2026.csv                          the list, tracked in git, with each raw file's SHA-256

Nominee status is NOT decided here. JD's "Primary Winner" label and DSA's listing are recorded as published;
E1 takes nominees from the official primary results in Phase 2. Run from the repo root.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import html as htmllib
import json
import re
import subprocess
import sys

import pandas as pd

RAW = Path("data/raw/e1_endorsements")
OUT = Path("data/coded/e1_endorsements_2026.csv")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
JD_URL = "https://justicedemocrats.com/candidates/"
DSA_PAGES = {"current": "https://electoral.dsausa.org/our-campaigns/",
             "past": "https://electoral.dsausa.org/our-campaigns/past-endorsements/"}
STATES = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"}
STATE_WORDS = {"PA": "PA", "MI": "MI", "Pennsylvania": "PA", "Michigan": "MI"}


def save(name, body, stamp):
    RAW.mkdir(parents=True, exist_ok=True)
    f = RAW / f"{name}_{stamp}"
    f.write_bytes(body)
    return f, hashlib.sha256(body).hexdigest()


class Resp:
    def __init__(self, content):
        self.content = content
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.content.decode("utf-8"))


def get(url, headers=None):
    """GET with curl. electoral.dsausa.org answers python-requests with 403 and curl with 200 (a TLS
    fingerprint, as with the NYSBOE site in nyc_enrollment_pull.py), so every fetch here goes through curl."""
    cmd = ["curl", "-sSL", "--fail", "--max-time", "60"]
    for k, v in {**UA, **(headers or {})}.items():
        cmd += ["-H", f"{k}: {v}"]
    p = subprocess.run(cmd + [url], capture_output=True)
    if p.returncode != 0:
        sys.exit(f"curl failed ({p.returncode}) for {url}: {p.stderr.decode(errors='replace').strip()}")
    return Resp(p.stdout)


def jd_cards(page):
    """Rows from JD's candidates page: section, name, district as written, status class, label, card URL."""
    cut = page.find("cand-card__grid--incumbent")
    if cut < 0 or "cand-card__grid--challenger" not in page:
        sys.exit("JD page layout changed: section grids not found")
    rows = []
    for m in re.finditer(r'<article class="cand-card (\w+) [^"]*"[^>]*>(.*?)</article>', page, re.S):
        status, body = m.group(1), m.group(2)
        name = re.search(r'<h1 class="cand-card__hed">(.*?)</h1>', body, re.S)
        dist = re.search(r'<h2 class="cand-card__sub">(.*?)</h2>', body, re.S)
        link = re.search(r'<a href="([^"]+)" class="cand-card__link"', body)
        label = re.search(r'<p class="cand-card__label[^"]*">(.*?)</p>', body, re.S)
        if not (name and dist):
            sys.exit(f"JD card without name or district near offset {m.start()}")
        rows.append({
            "jd_section": "Current Congressmembers" if m.start() > cut else "Upcoming Elections",
            "candidate_listed": htmllib.unescape(name.group(1)).strip(),
            "district_listed": htmllib.unescape(dist.group(1)).strip(),
            "jd_status_class": status,
            "jd_label": htmllib.unescape(label.group(1)).strip() if label else "",
            "jd_candidate_page": link.group(1) if link else "",
        })
    return rows


def airtable_rows(embed_html, app_id):
    """(view name, columns, rows, raw JSON bytes) for an Airtable shared-view embed page."""
    m = re.search(r'urlWithParams:\s*"([^"]+)"', embed_html)
    if not m:
        sys.exit("Airtable embed layout changed: no urlWithParams")
    url = json.loads('"' + m.group(1) + '"')
    if url.startswith("/"):
        url = "https://airtable.com" + url
    r = get(url, headers={"x-airtable-application-id": app_id, "x-requested-with": "XMLHttpRequest",
                          "x-time-zone": "America/Chicago", "x-user-locale": "en", "Accept": "application/json"})
    j = r.json()
    if j.get("msg") != "SUCCESS":
        sys.exit(f"Airtable returned {j.get('msg')}")
    t = j["data"]["table"]
    return [v.get("name") for v in t["views"]], t["columns"], t["rows"], r.content


def cell(cols, row, name):
    ids = [c["id"] for c in cols if c["name"] == name]
    return row["cellValuesByColumnId"].get(ids[0]) if ids else None


def choice_names(cols, name):
    c = [c for c in cols if c["name"] == name]
    return {k: v["name"] for k, v in c[0]["typeOptions"]["choices"].items()} if c else {}


def district_parts(text):
    """('CA', 7) from 'CA-07', 'IL-9', 'US Congress (CO-1)', 'PA Congressional District 3', 'MI Congressional District 12'."""
    m = re.search(r"\b([A-Z]{2})-(\d{1,2})\b", text)
    if m and m.group(1) in STATES:
        return m.group(1), int(m.group(2))
    m = re.search(r"\b([A-Z]{2}|Pennsylvania|Michigan) Congressional District (\d{1,2})\b", text)
    if m:
        return STATE_WORDS.get(m.group(1), m.group(1)), int(m.group(2))
    return "", None


def main():
    if OUT.exists() and "--overwrite" not in sys.argv:
        sys.exit(f"{OUT} is the plan-day record (4 Nov 2026, commit 54ad019) and is not overwritten; "
                 "corrections go in data/coded/e1_endorsements_2026_notes.md. Pass --overwrite to replace it.")
    now = datetime.now(timezone.utc)
    stamp, retrieved = now.strftime("%Y%m%dT%H%M%SZ"), now.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []

    # Justice Democrats
    r = get(JD_URL)
    f, sha = save("jd_candidates", r.content, stamp + ".html")
    for row in jd_cards(r.text):
        st, num = district_parts(row["district_listed"])
        out.append({"org": "Justice Democrats", **row, "state": st, "district_num": num, "office_listed": "",
                    "dsa_election_date": "", "dsa_chapters": "", "dsa_record_created_utc": "",
                    "source_url": JD_URL, "raw_file": f.name, "raw_sha256": sha, "retrieved_utc": retrieved})

    # National DSA: current view (kept) and past view (checked)
    past_2026_federal = None
    for which, page_url in DSA_PAGES.items():
        page = get(page_url).text
        m = re.search(r'src="(https://airtable\.com/embed/(app\w+)/(shr\w+)[^"]*)"', page)
        if not m:
            sys.exit(f"DSA {which} page has no Airtable embed")
        embed_url, app_id = htmllib.unescape(m.group(1)), m.group(2)
        views, cols, rows, body = airtable_rows(get(embed_url).text, app_id)
        f, sha = save(f"dsa_{which}", body, stamp + ".json")
        types = choice_names(cols, "Office Type")
        fed = [rw for rw in rows if "Federal" in [types.get(x, x) for x in (cell(cols, rw, "Office Type") or [])]]
        print(f"DSA {which}: view {views}, {len(rows)} rows, {len(fed)} federal")
        if which == "past":
            past_2026_federal = [rw for rw in fed if (cell(cols, rw, "Election Date") or "") >= "2025-11-05"]
            continue
        for rw in fed:
            office = (cell(cols, rw, "Office") or "").strip()
            name = (cell(cols, rw, "Campaign") or "").strip()
            st, num = district_parts(office + " " + name)
            out.append({"org": "National DSA", "jd_section": "", "candidate_listed": name, "district_listed": "",
                        "jd_status_class": "", "jd_label": "", "jd_candidate_page": "", "state": st, "district_num": num,
                        "office_listed": office, "dsa_election_date": (cell(cols, rw, "Election Date") or "")[:10],
                        "dsa_chapters": "; ".join(x["foreignRowDisplayName"] for x in (cell(cols, rw, "Endorsing Chapter(s)") or [])),
                        "dsa_record_created_utc": rw["createdTime"], "source_url": page_url, "raw_file": f.name,
                        "raw_sha256": sha, "retrieved_utc": retrieved})
    if past_2026_federal:
        sys.exit(f"{len(past_2026_federal)} 2026 federal rows are in DSA's past view; add them before saving")

    df = pd.DataFrame(out)
    bad = df[df["district_num"].isna()]
    if len(bad):
        sys.exit(f"district not parsed for: {bad[['org', 'candidate_listed', 'district_listed', 'office_listed']].to_dict('records')}")
    df["district_num"] = df["district_num"].astype(int)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {len(df)} rows ({(df.org == 'Justice Democrats').sum()} JD, {(df.org == 'National DSA').sum()} DSA), retrieved {retrieved}")
    print(df[["org", "candidate_listed", "state", "district_num", "jd_section", "jd_status_class", "dsa_election_date"]].to_string(index=False))


if __name__ == "__main__":
    main()
