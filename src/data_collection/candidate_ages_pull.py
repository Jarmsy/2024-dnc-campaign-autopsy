"""Birth dates for the Part 11 challengers, the incumbents they faced, and the 2026 incumbent defeats.

Why. Three of the four 2026 incumbents beaten from the DSA left were beaten by much younger challengers,
and a fourth, older incumbent lost to a younger moderate: ideology and age move together. Putting the age
gap into the challenger model separates them as far as 21 cases can.

Source: Wikidata (date of birth, P569), found through `wbsearchentities` and accepted only if the entity is
a human whose description names a U.S. politician or officeholder -- common names ("Anthony Clark",
"Mike Quigley") otherwise match the wrong person. Unmatched people are left blank, never guessed; `QID`
and `description` are kept so every match can be checked by eye.

Output: `data/raw/insurgent/candidate_ages.csv`.
"""

from pathlib import Path
import re
import time

import pandas as pd
import requests

OUT = Path("data/raw/insurgent/candidate_ages.csv")
# The 21 challenger-vs-incumbent cases of Part 11 (notebook 19, `type == "challenger vs incumbent"`), as
# (cycle, challenger, incumbent's FEC name).
CASES = [
    (2018, "Saira Rao", "DEGETTE, DIANA L."),
    (2018, "Chardo Richardson", "MURPHY, STEPHANIE"),
    (2018, "Marie Newman", "LIPINSKI, DANIEL WILLIAM WILLIAM"),
    (2018, "Sameena Mustafa", "QUIGLEY, MIKE"),
    (2018, "Anthony Clark", "DAVIS, DANNY K"),
    (2018, "Ayanna Pressley", "CAPUANO, MICHAEL E"),
    (2018, "Cori Bush", "CLAY, WILLIAM LACY JR"),
    (2018, "Alexandria Ocasio-Cortez", "CROWLEY, JOSEPH"),
    (2020, "Marie Newman", "LIPINSKI, DANIEL WILLIAM WILLIAM"),
    (2020, "Alex Morse", "NEAL, RICHARD E MR."),
    (2020, "Cori Bush", "CLAY, WILLIAM LACY JR"),
    (2020, "Jamaal Bowman", "ENGEL, ELIOT L."),
    (2020, "Morgan Harper", "BEATTY, JOYCE"),
    (2020, "Jessica Cisneros", "CUELLAR, HENRY"),
    (2022, "Kina Collins", "DAVIS, DANNY K. MR."),
    (2022, "Jessica Cisneros", "CUELLAR, HENRY"),
    (2026, "Melat Kiros", "DEGETTE, DIANA L"),
    (2026, "Donavan McKinney", "THANEDAR, SHRI"),
    (2026, "Cori Bush", "BELL, WESLEY"),
    (2026, "Darializa Avila Chevalier", "ESPAILLAT, ADRIANO"),
    (2026, "Nida Allam", "FOUSHEE, VALERIE"),
]
S = requests.Session()
S.headers["User-Agent"] = "dnc-autopsy-research/1.0 (academic election analysis; python-requests)"
API = "https://www.wikidata.org/w/api.php"
OK = re.compile(r"politic|representative|congress|senator|mayor|legislat|member of|council|activist|candidate|"
                r"assemblywoman|assemblyman|state house|official", re.I)
# The 2026 House Democratic incumbents who lost primaries and who beat them (U.S. News, 16 Sep 2026).
DEFEATS_2026 = [("Diana DeGette", "Melat Kiros", "DSA"), ("Adriano Espaillat", "Darializa Avila Chevalier", "DSA"),
                ("Shri Thanedar", "Donavan McKinney", "DSA"), ("Dan Goldman", "Brad Lander", "ex-DSA"),
                ("John B. Larson", "Luke Bronin", "moderate"), ("Al Green", "Christian Menefee", "redistricting"),
                ("Julie Johnson", "Colin Allred", "redistricting")]
# Wikidata names differ from FEC names for these
ALIAS = {"LIPINSKI, DANIEL WILLIAM WILLIAM": "Dan Lipinski", "CLAY, WILLIAM LACY JR": "Lacy Clay",
         "NEAL, RICHARD E MR.": "Richard Neal", "DAVIS, DANNY K. MR.": "Danny K. Davis", "DAVIS, DANNY K": "Danny K. Davis",
         "ENGEL, ELIOT L.": "Eliot Engel", "DEGETTE, DIANA L.": "Diana DeGette", "DEGETTE, DIANA L": "Diana DeGette",
         "MURPHY, STEPHANIE": "Stephanie Murphy", "QUIGLEY, MIKE": "Mike Quigley", "CAPUANO, MICHAEL E": "Mike Capuano",
         "CROWLEY, JOSEPH": "Joe Crowley", "BEATTY, JOYCE": "Joyce Beatty", "CUELLAR, HENRY": "Henry Cuellar",
         "THANEDAR, SHRI": "Shri Thanedar", "BELL, WESLEY": "Wesley Bell", "ESPAILLAT, ADRIANO": "Adriano Espaillat",
         "FOUSHEE, VALERIE": "Valerie Foushee"}


CACHE = OUT.parent / "wikidata_cache"


def api(**params):
    """Wikidata API call, cached on disk; throttled bursts come back as non-JSON pages, so retry slowly."""
    import json
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", json.dumps(params, sort_keys=True))[:150] + ".json")
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    for attempt in range(8):
        r = S.get(API, params=dict(format="json", **params), timeout=60)
        try:
            j = r.json()
        except ValueError:
            time.sleep(15 * (attempt + 1)); continue
        f.write_text(json.dumps(j), encoding="utf-8"); time.sleep(1.5)
        return j
    raise RuntimeError(f"Wikidata kept refusing {params}")


def birth(name):
    hits = api(action="wbsearchentities", search=name, language="en", type="item", limit=7).get("search", [])
    for h in hits:
        if not OK.search(h.get("description", "")):
            continue
        e = api(action="wbgetentities", ids=h["id"], props="claims")["entities"][h["id"]]["claims"]
        human = any(c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") == "Q5" for c in e.get("P31", []))
        dob = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("time") for c in e.get("P569", [])]
        if human and dob and dob[0]:
            return dob[0][1:11], h["id"], h.get("description", "")
    return None, None, None


def main():
    people = []
    for _, cand, opp in CASES:
        people += [(cand, "challenger"), (ALIAS.get(opp, opp.title()), "incumbent")]
    for inc, win, _ in DEFEATS_2026:
        people += [(inc, "2026 defeated incumbent"), (win, "2026 winner")]
    rows, seen = [], {}
    for name, role in people:
        if name not in seen:
            seen[name] = birth(name)
        dob, qid, desc = seen[name]
        rows.append(dict(name=name, role=role, dob=dob, qid=qid, description=desc))
        print(f"  {name:28s} {role:24s} {dob}  {qid}  {desc[:50] if desc else ''}")
    d = pd.DataFrame(rows).drop_duplicates(["name", "role"])
    d.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {d.dob.notna().sum()} of {len(d)} with a birth date")


if __name__ == "__main__":
    main()
