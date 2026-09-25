"""Every contested Democratic House incumbent primary, 2024 and 2026, with district age and incumbent age.

Why. In 2026 three of the four incumbents beaten from the DSA left lost to challengers roughly 40 years younger,
and a fourth older incumbent lost to a younger moderate. Part 11's 21 Justice Democrats challenges are too few to
say whether young districts turned on incumbents regardless of ideology; this covers every incumbent.

Results: Wikipedia's state pages ("<year> United States House of Representatives elections in <State>"), fetched
through the MediaWiki API and cached (the cache and throttling handling are shared with
`superpac_targets_pull.wikitext`). In each "District N" section the first box titled "Democratic primary results"
is read template by template; the incumbent is the candidate marked "(incumbent)". Only contested primaries
(a results box with two or more candidates) are kept. At-large states are skipped.

2026 districts in states with mid-decade maps in force (TX, NC, OH, CA, UT, FL, TN, LA, AL) or in litigation
at primary time (MO) are dropped: the ACS geography is the 2024 (119th Congress) lines.

District age: ACS 2024 5-year, congressional district: share of adults 18+ aged 18-34 (B01001) and median age
(B01002). Incumbent age: Wikidata date of birth for the incumbent's linked English Wikipedia article (exact, via
sitelink -- no name search).

Output: `data/raw/insurgent/incumbent_primaries.csv`.
"""

import os
from pathlib import Path
import re
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from superpac_targets_pull import wikitext  # noqa: E402
from candidate_ages_pull import api  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OUT = Path("data/raw/insurgent/incumbent_primaries.csv")
STATES = {"Alabama": "01", "Arizona": "04", "Arkansas": "05", "California": "06", "Colorado": "08",
          "Connecticut": "09", "Florida": "12", "Georgia": "13", "Hawaii": "15", "Idaho": "16", "Illinois": "17",
          "Indiana": "18", "Iowa": "19", "Kansas": "20", "Kentucky": "21", "Louisiana": "22", "Maine": "23",
          "Maryland": "24", "Massachusetts": "25", "Michigan": "26", "Minnesota": "27", "Mississippi": "28",
          "Missouri": "29", "Montana": "30", "Nebraska": "31", "Nevada": "32", "New Hampshire": "33",
          "New Jersey": "34", "New Mexico": "35", "New York": "36", "North Carolina": "37", "Ohio": "39",
          "Oklahoma": "40", "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45",
          "Tennessee": "47", "Texas": "48", "Utah": "49", "Virginia": "51", "Washington": "53",
          "West Virginia": "54", "Wisconsin": "55"}
REDRAWN_2026 = {"Texas", "North Carolina", "Ohio", "California", "Utah", "Florida", "Tennessee", "Louisiana",
                "Alabama", "Missouri"}
TOP_TWO = {"California", "Washington"}   # all-party primaries: shares include Republicans; skipped


def candidates(box):
    out = []
    for tpl in re.findall(r"\{\{Election box (?:winning )?candidate[^{}]*\}\}", box, re.S):
        c = re.search(r"candidate\s*=\s*((?:\[\[[^\]]*\]\]|[^|}\[])*)", tpl)   # piped links carry a "|" inside
        v = re.search(r"votes\s*=\s*([\d,]+)", tpl)
        if not (c and v):
            continue
        raw = c.group(1)
        link = re.search(r"\[\[([^|\]]+)", raw)
        name = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", raw)
        out.append(dict(name=re.sub(r"\(.*?\)|''.*?''|<.*?>", "", name).strip(),
                        article=link.group(1).strip() if link else None,
                        incumbent="(incumbent)" in raw.lower(), votes=int(v.group(1).replace(",", ""))))
    return out


def races(year, state):
    t = wikitext(f"{year} United States House of Representatives elections in {state}")
    heads = list(re.finditer(r"\n=+\s*District\s+(\d+)\s*=+", t))
    for i, h in enumerate(heads):
        sec = t[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(t)]
        m = re.search(r"\{\{Election box begin[^}]*Democratic primary results", sec)
        if not m:
            continue
        box = sec[m.start(): sec.find("Election box end", m.start())]
        cs = candidates(box)
        inc = [c for c in cs if c["incumbent"]]
        if len(cs) < 2 or len(inc) != 1:
            continue
        tot = sum(c["votes"] for c in cs)
        best_other = max(c["votes"] for c in cs if not c["incumbent"])
        yield dict(year=year, state=state, district=int(h.group(1)), incumbent=inc[0]["name"],
                   article=inc[0]["article"], inc_share=inc[0]["votes"] / tot, n_candidates=len(cs),
                   lost=inc[0]["votes"] < best_other, total_votes=tot)


def dob(article):
    if not article:
        return None
    j = api(action="wbgetentities", sites="enwiki", titles=article, props="claims")
    for e in j.get("entities", {}).values():
        t = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("time") for c in e.get("claims", {}).get("P569", [])]
        if t and t[0]:
            # year-only precision comes back as YYYY-00-00: take mid-year (within six months either way)
            return t[0][1:11].replace("-00-00", "-07-01").replace("-00", "-01")
    return None


def acs():
    male = [f"B01001_{i:03d}E" for i in range(7, 26)]; female = [f"B01001_{i:03d}E" for i in range(31, 50)]
    young = [f"B01001_{i:03d}E" for i in list(range(7, 13)) + list(range(31, 37))]
    cols = sorted(set(male + female + young)) + ["B01002_001E"]
    frames = []
    for i in range(0, len(cols), 45):
        r = requests.get("https://api.census.gov/data/2024/acs/acs5", timeout=120,
                         params={"get": ",".join(cols[i:i + 45]), "for": "congressional district:*", "in": "state:*",
                                 "key": os.getenv("CENSUS_API_KEY")})
        if r.status_code != 200:
            raise SystemExit(f"ACS request failed: {r.status_code}")   # never print the URL: it carries the key
        j = r.json(); f = pd.DataFrame(j[1:], columns=j[0])
        frames.append(f.set_index(["state", "congressional district"]))
    a = pd.concat(frames, axis=1).apply(pd.to_numeric, errors="coerce")
    a["young_share"] = a[young].sum(axis=1) / a[male + female].sum(axis=1)
    a["median_age"] = a.B01002_001E
    return a[["young_share", "median_age"]].reset_index()


def main():
    rows = []
    for year in (2024, 2026):
        for state in STATES:
            if state in TOP_TWO or (year == 2026 and state in REDRAWN_2026):
                continue
            rows += list(races(year, state))
    d = pd.DataFrame(rows)
    d["inc_dob"] = d.article.map(dob)
    a = acs()
    a["state_name"] = a.state.map({v: k for k, v in STATES.items()})
    a["district"] = pd.to_numeric(a["congressional district"], errors="coerce")
    d = d.merge(a[["state_name", "district", "young_share", "median_age"]], left_on=["state", "district"],
                right_on=["state_name", "district"], how="left").drop(columns="state_name")
    d["inc_age"] = (pd.to_datetime(d.year.astype(str) + "-06-30") - pd.to_datetime(d.inc_dob)).dt.days / 365.25
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(d.groupby("year").agg(races=("lost", "size"), lost=("lost", "sum"), with_age=("inc_age", "count"),
                                with_acs=("young_share", "count")))
    print("  losers:", d[d.lost][["year", "state", "district", "incumbent"]].values.tolist())


if __name__ == "__main__":
    main()
