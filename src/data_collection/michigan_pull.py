"""Michigan general-election results by municipality (city / township), for pre-registered Test A.

Source: OpenElections compilation of the Secretary of State's official precinct results
(github.com/openelections/openelections-data-mi), fetched with curl into data/raw/michigan/:
    20201103__mi__general__precinct.csv   9,762,469 bytes
    20241105__mi__general__precinct.csv  14,724,755 bytes
The OpenElections 2020 files are incomplete (the statewide file omits nine counties; the per-county
files misfile precincts), so 2020 comes from the MIT Election Lab precinct file instead (load_2020). The SOS site itself publishes precinct results as PDFs and its data host (mielections.us) did not
respond in September 2026. The 2026 general will be added from the certified SOS/OpenElections
file when it exists (late November 2026).

Cleaning. `votes` is read as text and coerced. Party labels vary by county (DEM / Democrat /
Democratic; REP / Republican) and in some 2020 rows the candidate and party columns are swapped, so
the party is taken from whichever column carries it. Precinct names are "<Municipality>, Precinct N"
(also AVCB / CB counting boards, suffixes such as "15A" or "FHP"); the municipality is the text
before the first comma, normalized (case, "City of", "Charter Township"/"Township"). Totals are
checked against the certified statewide results in main().
"""
from pathlib import Path
import re
import numpy as np
import pandas as pd

RAW = Path("data/raw/michigan")
FILES = {2008: "20081104__mi__general__precinct.csv", 2012: "20121106__mi__general__precinct.csv", 2016: "20161108__mi__general__precinct.csv",
         2018: "20181106__mi__general__precinct.csv", 2020: "20201103__mi__general__precinct.csv", 2022: "20221108__mi__general__precinct.csv", 2024: "20241105__mi__general__precinct.csv"}
CERTIFIED = {  # statewide certified totals (MI Board of State Canvassers)
    (2020, "U.S. Senate"): {"D": 2734568, "R": 2642233},
    (2020, "President"): {"D": 2804040, "R": 2649852},
    (2024, "President"): {"D": 2736533, "R": 2816636},
    (2024, "U.S. Senate"): {"D": 2712686, "R": 2693680},
    (2022, "Governor"): {"D": 2430505, "R": 1960635},
    (2022, "Attorney General"): {"D": 2329195, "R": 1952408},
    (2022, "Secretary of State"): {"D": 2467859, "R": 1852510},
}
OFFICES_2022 = ("Governor", "Attorney General", "Secretary of State")
# Validation years (addendum 2): presidential swings 2008-2016 and the 2018 statewide races
CERTIFIED.update({
    (2008, "President"): {"D": 2872579, "R": 2048639},
    (2012, "President"): {"D": 2564569, "R": 2115256},
    (2016, "President"): {"D": 2268839, "R": 2279543},
    (2018, "U.S. Senate"): {"D": 2214478, "R": 1938818},
    (2018, "Governor"): {"D": 2266193, "R": 1859534},
    (2018, "Attorney General"): {"D": 2031117, "R": 1916117},
    (2018, "Secretary of State"): {"D": 2213243, "R": 1840118},
})
OFFICES_2018 = ("U.S. Senate", "Governor", "Attorney General", "Secretary of State")


# Candidates are identified by surname in either the candidate or party column: labels vary by
# county (DEM / Democrat / D; REP / Republican / R), and some rows swap the two columns.
NAMES = {("President", 2020): {"D": "biden", "R": "trump"}, ("U.S. Senate", 2020): {"D": "peters", "R": "james"},
         ("President", 2024): {"D": "harris", "R": "trump"}, ("U.S. Senate", 2024): {"D": "slotkin", "R": "rogers"},
         ("Governor", 2022): {"D": "whitmer", "R": "dixon"}, ("Attorney General", 2022): {"D": "nessel", "R": "deperno"},
         ("Secretary of State", 2022): {"D": "benson", "R": "karamo"},
         ("President", 2008): {"D": "obama", "R": "mccain"}, ("President", 2012): {"D": "obama", "R": "romney"},
         ("President", 2016): {"D": "clinton", "R": "trump"}, ("U.S. Senate", 2018): {"D": "stabenow", "R": "james"},
         ("Governor", 2018): {"D": "whitmer", "R": "schuette"}, ("Attorney General", 2018): {"D": "nessel", "R": "leonard"},
         ("Secretary of State", 2018): {"D": "benson", "R": "lang"}}
SHORT = {"President": "pres", "U.S. Senate": "sen", "Governor": "gov", "Attorney General": "ag", "Secretary of State": "sos"}


def party_of(text, office, year):
    t = text.lower()
    hits = [p for p, n in NAMES[(office, year)].items() if n in t]
    return hits[0] if len(hits) == 1 else None


def municipality(precinct):
    m = str(precinct).split(",")[0].strip().lower()
    m = re.sub(r"\s+", " ", m.replace(".", ""))
    m = re.sub(r"\s+(precinct|pct|ward|avcb|cb)\b.*$", "", m)          # 'alamo twp precinct 1'
    m = re.sub(r"\s+\d+[a-z]?(\s+\w+)?$", "", m)                        # 'alamo twp 1', 'ada township 6 fhp'
    kind = "township" if re.search(r"\b(township|twp)\b", m) else ("village" if "village" in m else "city")
    for pat in (r"^(the )?(charter )?(township|twp) of ", r"^(the )?city of ", r"^(the )?village of ",
                r" (charter )?(township|twp)$", r" city$", r" village$"):
        m = re.sub(pat, "", m)
    return f"{m.strip()} {kind}"


def load_2020(offices=("President", "U.S. Senate")):
    """2020 from the MIT Election Lab precinct file (Harvard Dataverse doi:10.7910/DVN/NT66Z3,
    2020-mi-precinct-general.csv, downloaded by hand because Dataverse requires a guestbook). Each
    precinct reports either one TOTAL row or separate ELECTION DAY / ABSENTEE rows, never both, so
    all modes are summed."""
    d = pd.read_csv(RAW / "2020-mi-precinct-general.csv", low_memory=False,
                    usecols=["office", "party_simplified", "mode", "votes", "county_name", "jurisdiction_name"])
    omap = {"US PRESIDENT": "President", "US SENATE": "U.S. Senate"}
    d = d[d.office.isin(omap) & d.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"])].copy()
    d["office"] = d.office.map(omap); d = d[d.office.isin(offices)]
    d["p"] = d.party_simplified.str[0]
    d["county"] = d.county_name.str.title(); d["muni"] = d.jurisdiction_name.map(municipality)
    out = d.pivot_table(index=["county", "muni"], columns=["office", "p"], values="votes", aggfunc="sum", fill_value=0)
    out.columns = [f"{'pres' if o == 'President' else 'sen'}_{p}_2020" for o, p in out.columns]
    return out.reset_index()


def read_raw(year):
    return pd.read_csv(RAW / FILES[year], low_memory=False, dtype=str)


def load(year, offices=("President", "U.S. Senate")):
    if year == 2020:
        return load_2020(offices)
    d = read_raw(year)
    d = d[d.office.isin(offices) & ~d.precinct.fillna("").str.contains(r"\btotal\b", case=False)].copy()
    d["votes"] = pd.to_numeric(d.votes.str.replace(",", ""), errors="coerce").fillna(0)
    d["p"] = [party_of(f"{c} {p}", o, year) for c, p, o in zip(d.candidate.fillna(""), d.party.fillna(""), d.office)]
    d = d[d.p.notna()]
    d["county"] = d.county.str.strip().str.title()
    d["muni"] = d.precinct.map(municipality)
    out = d.pivot_table(index=["county", "muni"], columns=["office", "p"], values="votes", aggfunc="sum", fill_value=0)
    out.columns = [f"{SHORT[o]}_{p}_{year}" for o, p in out.columns]
    return out.reset_index()


def main():
    for (year, office), cert in CERTIFIED.items():
        m = load(year, (office,))
        pre = SHORT[office]
        for p in ("D", "R"):
            got = m[f"{pre}_{p}_{year}"].sum()
            print(f"{year} {office} {p}: {got:,.0f} vs certified {cert[p]:,} ({got / cert[p] - 1:+.3%})")
    a, b = load(2020), load(2024)
    j = match(a, b)
    j.to_csv(RAW / "mi_municipal_2020_2024.csv", index=False)
    print("--- adding 2022")
    j22 = match(j, load(2022, OFFICES_2022), key_cols=("pres_D_2024", "pres_R_2024"), key_cols_b=("gov_D_2022", "gov_R_2022"))
    j22.to_csv(RAW / "mi_municipal_2020_2024_with_2022.csv", index=False)
    print("--- validation file (addendum 2): 2018 statewide races + presidential 2008/2012/2016")
    v = load(2018, OFFICES_2018)
    for yr in (2016, 2012, 2008):
        v = match(v, load(yr, ("President",)), key_cols=("gov_D_2018", "gov_R_2018"), key_cols_b=(f"pres_D_{yr}", f"pres_R_{yr}"))
    v.to_csv(RAW / "mi_municipal_validation_2008_2018.csv", index=False)


UNPLACEABLE = r"^9999|early voting|statistical adjust|^\{|\bev\d*\b|multi-precinct|collection|cumulative"


def _bare(m, keep_kind):
    name, kind = re.match(r"(.*) (city|township|village)$", m).groups()
    name = re.sub(r"\bmount\b", "mt", name)
    name = re.sub(r"\b(charter|twp|prec|precincts)\b", "", name)
    name = re.sub(r"[^a-z]", "", name)
    return name + ("|" + ("township" if kind == "township" else "municipal") if keep_kind else "")


def match(a, b, key_cols=None, key_cols_b=None):
    """Join 2020 and 2024 municipalities in three passes, each only where the key is unique within the
    county on both sides: exact name + type; bare name + township-or-not (type words, 'mount'->'mt',
    spaces and punctuation removed); bare name alone. County-wide early-voting boards (2024) and
    statistical adjustments (2020) cannot be placed and are dropped; their vote share is printed."""
    vcols = lambda x, kc: list(kc) if kc else [c for c in x.columns if c.startswith("pres_")]
    for x, yr, kc in ((a, "A", key_cols), (b, "B", key_cols_b)):
        bad = x.muni.str.contains(UNPLACEABLE, regex=True)
        cols = vcols(x, kc)
        print(f"{yr}: unplaceable presidential votes {x.loc[bad, cols].values.sum():,.0f} "
              f"({x.loc[bad, cols].values.sum() / x[cols].values.sum():.2%})")
    ca, cb = vcols(a, key_cols), vcols(b, key_cols_b)
    tot20, tot24 = a[ca].values.sum(), b[cb].values.sum()
    a = a[~a.muni.str.contains(UNPLACEABLE, regex=True)].copy(); b = b[~b.muni.str.contains(UNPLACEABLE, regex=True)].copy()
    for x in (a, b):
        x["county"] = x.county.str.replace(".", "", regex=False).str.replace(r"(?i)'s$", "", regex=True).str.strip()
        x["bare"] = x.muni.map(lambda m: _bare(m, True)); x["bare0"] = x.muni.map(lambda m: _bare(m, False))
    parts, ra, rb = [], a, b
    for key in ("muni", "bare", "bare0"):
        ua = ra[~ra.duplicated(["county", key], keep=False)]; ub = rb[~rb.duplicated(["county", key], keep=False)]
        m = ua.merge(ub.drop(columns=[c for c in ("muni", "bare", "bare0") if c != key]), on=["county", key], how="inner")
        parts.append(m.drop(columns=[c for c in ("bare", "bare0") if c in m.columns]))
        keyset = set(zip(m.county, m[key]))
        # boolean arrays, not lists: an empty list would be read as a column selection and drop every column
        ra = ra.loc[np.array([k not in keyset for k in zip(ra.county, ra[key])], dtype=bool)]
        rb = rb.loc[np.array([k not in keyset for k in zip(rb.county, rb[key])], dtype=bool)]
        print(f"  pass {key}: {len(m)} matched")
    out = pd.concat(parts, ignore_index=True)
    print(f"matched {len(out)} municipalities; unmatched A {len(ra)}, B {len(rb)}")
    print(f"share of votes in matched municipalities: A {out[ca].values.sum() / tot20:.2%}, B {out[cb].values.sum() / tot24:.2%}")
    print("still unmatched A:", ra[["county", "muni"]].values.tolist()[:30])
    print("still unmatched B:", rb[["county", "muni"]].values.tolist()[:30])
    return out


if __name__ == "__main__":
    main()
