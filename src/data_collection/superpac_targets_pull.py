"""Candidates the pro-Israel and crypto super PACs spent against in Democratic primaries, 2022-2026:
money on both sides and the result.

Why. Part 11's money model says what being outspent costs a Justice Democrats candidate. The question
here is whether the candidates these four committees (UDP, DMFI, Fairshake, Protect Progress) targeted in
2026 beat that arithmetic more than their targets did in 2022-24 -- i.e. whether the money is losing force.

Universe. Every race in `data/coded/superpac_races_for_coding.csv` ($1M+ from the four committees) with a
clearly identifiable target: a candidate the committees opposed directly, or the main rival of the candidate
they backed in a race with no more than three serious candidates. California and Washington top-two
primaries are excluded (their shares include Republicans), as are crowded open seats where the backed
candidate had no single rival (MD-5 2026, GA-13 2026) and specials with no clear rival (VA-11 2025). The
target and rival for each race are fixed in RACES below.

Money (FEC, via the key-safe getter in fec_insurgent_pull): each side's receipts through the last report
before the election plus outside money disseminated by election day -- the target's side is its receipts,
IE supporting it and IE opposing the rival; the rival's side the reverse. `money_ratio` = rival side /
target side, the same construction as Part 11. Runoffs and specials use their own election date.

Votes (Wikipedia election boxes, fetched through the MediaWiki API): the target's head-to-head share,
target / (target + rival), from the Democratic primary, runoff or special table named in RACES.

`left` marks targets running as progressives or democratic socialists on the public record (Justice
Democrats or DSA endorsement, or Congressional Progressive Caucus membership); None where the record does
not place them.

Output: `data/raw/superpac_ads/superpac_targets.csv`.
"""

from pathlib import Path
import re
import sys

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent))
import fec_insurgent_pull as F  # noqa: E402

OUT = Path("data/raw/superpac_ads/superpac_targets.csv")
H = "United States House of Representatives elections in"
# cycle, state, district (0 = Senate), date, target, rival, wiki page, section district, box label, left
RACES = [
    (2022, "MD", 4, "2022-07-19", "Donna Edwards", "Glenn Ivey", f"2022 {H} Maryland", 4, "Democratic primary results", True),
    (2022, "MI", 11, "2022-08-02", "Andy Levin", "Haley Stevens", f"2022 {H} Michigan", 11, "Democratic primary results", True),
    (2022, "MI", 13, "2022-08-02", "Shri Thanedar", "Adam Hollier", f"2022 {H} Michigan", 13, "Democratic primary results", False),
    (2022, "NC", 1, "2022-05-17", "Erica Smith", "Don Davis", f"2022 {H} North Carolina", 1, "Democratic primary results", True),
    (2022, "NC", 4, "2022-05-17", "Nida Allam", "Valerie Foushee", f"2022 {H} North Carolina", 4, "Democratic primary results", True),
    (2022, "PA", 12, "2022-05-17", "Summer Lee", "Steve Irwin", f"2022 {H} Pennsylvania", 12, "Democratic primary results", True),
    (2022, "OH", 11, "2021-08-03", "Nina Turner", "Shontel Brown", "2021 Ohio's 11th congressional district special election", None, "Democratic primary results", True),
    (2022, "TX", 28, "2022-05-24", "Jessica Cisneros", "Henry Cuellar", f"2022 {H} Texas", 28, "Democratic primary results#2", True),
    (2024, "NY", 16, "2024-06-25", "Jamaal Bowman", "George Latimer", f"2024 {H} New York", 16, "Democratic primary results", True),
    (2024, "MO", 1, "2024-08-06", "Cori Bush", "Wesley Bell", f"2024 {H} Missouri", 1, "Democratic primary results", True),
    (2024, "AZ", 3, "2024-07-30", "Raquel Terán", "Yassamin Ansari", f"2024 {H} Arizona", 3, "Democratic primary results", None),
    (2024, "MD", 3, "2024-05-14", "Harry Dunn", "Sarah Elfreth", f"2024 {H} Maryland", 3, "Democratic primary results", None),
    (2024, "VA", 10, "2024-06-18", "Suhas Subramanyam", "Dan Helmer", f"2024 {H} Virginia", 10, "Democratic primary results", False),
    (2024, "AL", 2, "2024-04-16", "Anthony Daniels", "Shomari Figures", f"2024 {H} Alabama", 2, "Democratic primary runoff results", False),
    (2026, "MI", 0, "2026-08-04", "Abdul El-Sayed", "Haley Stevens", "2026 United States Senate election in Michigan", None, "Democratic primary results", True),
    (2026, "IL", 0, "2026-03-17", "Juliana Stratton", "Raja Krishnamoorthi", "2026 United States Senate election in Illinois", None, "Democratic primary results", True),
    (2026, "IL", 7, "2026-03-17", "La Shawn Ford", "Melissa Conyears-Ervin", f"2026 {H} Illinois", 7, "Democratic primary results", None),
    (2026, "MO", 1, "2026-08-04", "Cori Bush", "Wesley Bell", f"2026 {H} Missouri", 1, "Democratic primary results", True),
    (2026, "NJ", 11, "2026-02-05", "Tom Malinowski", "Analilia Mejia", "2026 New Jersey's 11th congressional district special election", None, "Democratic primary results", False),
    (2026, "CA", 14, "2026-08-18", "Aisha Wahab", "Melissa Hernandez", "2026 California's 14th congressional district special election", None, "runoff", True),
    (2026, "FL", 24, "2026-08-18", "Oliver Gilbert", "Shevrin Jones", f"2026 {H} Florida", 24, "Democratic primary results", False),
    (2026, "TX", 18, "2026-05-26", "Al Green", "Christian Menefee", f"2026 {H} Texas", 18, "Democratic primary runoff results", True),
    (2026, "MI", 13, "2026-08-04", "Donavan McKinney", "Shri Thanedar", f"2026 {H} Michigan", 13, "Democratic primary results", True),
    (2026, "NY", 15, "2026-06-23", "Michael Blake", "Ritchie Torres", f"2026 {H} New York", 15, "Democratic primary results", True),
]

S = requests.Session()
S.headers["User-Agent"] = "dnc-autopsy-research/1.0 (academic election analysis; python-requests)"


WIKI = OUT.parent / "wiki"


def wikitext(title):
    """Page wikitext, cached on disk; Wikipedia answers bursts with non-JSON throttling pages, so retry slowly."""
    import time
    WIKI.mkdir(parents=True, exist_ok=True)
    f = WIKI / (re.sub(r"[^A-Za-z0-9]+", "_", title)[:150] + ".txt")
    if f.exists():
        return f.read_text(encoding="utf-8")
    for attempt in range(6):
        r = S.get("https://en.wikipedia.org/w/api.php", params=dict(action="parse", page=title, prop="wikitext",
                                                                    format="json", redirects=1), timeout=60)
        try:
            j = r.json()
        except ValueError:
            time.sleep(10 * (attempt + 1)); continue
        text = j.get("parse", {}).get("wikitext", {}).get("*", "")
        f.write_text(text, encoding="utf-8"); time.sleep(1)
        return text
    raise RuntimeError(f"Wikipedia kept refusing {title!r}")


def box_votes(text, district, label):
    """Candidate -> votes from the first election box whose title contains `label`, inside the district section."""
    if district is not None:
        m = re.search(rf"\n=+\s*District\s+{district}\s*=+", text)
        if not m:
            return {}
        nxt = re.search(r"\n=+\s*District\s+\d+\s*=+", text[m.end():])
        text = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
    label, _, nth = label.partition("#")          # "label#2": the second box with that title
    seen = 0
    for bm in re.finditer(r"\{\{Election box begin[^\n]*", text):
        head = text[bm.start(): bm.start() + 600]
        if label.lower() not in head.lower():
            continue
        seen += 1
        if nth and seen < int(nth):
            continue
        end = text.find("Election box end", bm.start())
        blk = text[bm.start(): end]
        out = {}
        for c in re.finditer(r"candidate\s*=\s*((?:\[\[[^\]]*\]\]|[^|\n\[])+?)\s*\|[^{}]*?votes\s*=\s*([\d,]+)", blk, re.S):
            name = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", c.group(1))
            name = re.sub(r"''.*?''|\(.*?\)|<.*?>", "", name).strip()
            out[name] = int(c.group(2).replace(",", ""))
        if out:
            return out
    return {}


STATE = {"MD": "Maryland", "MI": "Michigan", "NC": "North Carolina", "PA": "Pennsylvania", "TX": "Texas", "NY": "New York",
         "MO": "Missouri", "AZ": "Arizona", "VA": "Virginia", "AL": "Alabama", "IL": "Illinois", "FL": "Florida",
         "OH": "Ohio", "NJ": "New Jersey", "CA": "California"}


def race_votes(cycle, st, dist, page, sec, label):
    """Votes from the state page's district section; failing that, from the district's own election article."""
    v = box_votes(wikitext(page), sec, label)
    if not v and dist:
        n = f"{dist}th" if dist % 100 in (11, 12, 13) else f"{dist}" + {1: "st", 2: "nd", 3: "rd"}.get(dist % 10, "th")
        yr = int(page[:4])
        v = box_votes(wikitext(f"{yr} {STATE[st]}'s {n} congressional district election"), None, label)
    return v


def find(votes, name):
    last = name.split()[-1].lower().replace("-", " ")
    hits = [v for k, v in votes.items() if last in k.lower().replace("-", " ")]
    return hits[0] if len(hits) == 1 else None


# Where name search picks the wrong person (a same-surname candidate in another district) or misses an
# accented or long name; every other match is checked on first and last name in main().
FEC_ID = {"Glenn Ivey": "H2MD04232", "Raquel Terán": "H4AZ03117", "Raja Krishnamoorthi": "S6IL00482"}  # FEC: "S. Raja"


# Entered by hand where the Wikipedia table is raw HTML rows rather than election-box templates: the TX-28
# 2022 runoff (Cuellar 22,895, Cisneros 22,606 -- Cisneros 49.69%, as in Part 11's OVERRIDE).
VOTES = {(2022, "Jessica Cisneros"): (22606, 22895)}


def fec_id(name, state, district, cycle):
    if name in FEC_ID:
        return FEC_ID[name]
    if district:
        c = F.find_candidate(name, state, district, cycle)
        return c["candidate_id"] if c else None
    j = F.get("/candidates/search/", q=name.split()[-1], office="S", state=state, cycle=cycle, party="DEM", per_page=20)
    res = [r for r in j.get("results", []) if name.split()[0][:3].lower() in r["name"].lower()]
    return res[0]["candidate_id"] if res else None


def side(cid, cycle, date):
    rec, _, _ = F.pre_primary_receipts(cid, cycle, date) if cid else (None, None, None)
    sup, opp = F.ie_pre_primary(cid, cycle, date) if cid else (None, None)
    return rec or 0.0, sup or 0.0, opp or 0.0


def main():
    rows = []
    for cycle, st, dist, date, tgt, riv, page, sec, label, left in RACES:
        if (cycle, tgt) in VOTES:
            tv, rv = VOTES[(cycle, tgt)]
        else:
            votes = race_votes(cycle, st, dist, page, sec, label)
            tv, rv = find(votes, tgt), find(votes, riv)
        tid, rid = fec_id(tgt, st, dist, cycle), fec_id(riv, st, dist, cycle)
        for nm, cid in ((tgt, tid), (riv, rid)):
            fec_name = F.get(f"/candidate/{cid}/", per_page=1)["results"][0]["name"].upper() if cid else ""
            first, last = nm.split()[0].upper()[:3], nm.split()[-1].upper().replace("Á", "A").split("-")[0]
            if not (last in fec_name and first in fec_name):
                print(f"  CHECK FEC match: {nm} -> {cid} {fec_name}")
        t_rec, t_sup, t_opp = side(tid, cycle, date)
        r_rec, r_sup, r_opp = side(rid, cycle, date)
        t_side, r_side = t_rec + t_sup + r_opp, r_rec + r_sup + t_opp
        rows.append(dict(cycle=cycle, race=f"{cycle} {st}-{dist if dist else 'SEN'}", date=date, target=tgt, rival=riv,
                         left=left, target_votes=tv, rival_votes=rv,
                         h2h=tv / (tv + rv) if tv and rv else None, won=(tv > rv) if tv and rv else None,
                         target_fec=tid, rival_fec=rid, target_receipts=t_rec, rival_receipts=r_rec,
                         ie_against_target=t_opp, ie_for_rival=r_sup, ie_for_target=t_sup, ie_against_rival=r_opp,
                         target_side=t_side, rival_side=r_side,
                         money_ratio=r_side / t_side if t_side else None, wiki=page))
        print(f"  {rows[-1]['race']:12s} {tgt:22s} h2h {rows[-1]['h2h'] or float('nan'):.3f}  ratio "
              f"{rows[-1]['money_ratio'] or float('nan'):5.2f}  votes {tv}/{rv}")
    d = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {len(d)} races, {d.h2h.notna().sum()} with votes")


if __name__ == "__main__":
    main()
