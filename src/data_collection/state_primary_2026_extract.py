# -*- coding: utf-8 -*-
"""Democratic House primary totals for every district in the 2026-case states, 2024 and 2026.

The FEC compilation does not exist for 2024 or 2026, so the national benchmark used for the
2018-2022 cases is unavailable. A within-state benchmark replaces it: every other district in the
same state and cycle pair, which absorbs the state's own turnout environment.
"""
import json, os, re, sys

import pandas as pd

SCR = os.path.dirname(os.path.abspath(__file__))
STATES = {'Colorado': 'CO', 'Michigan': 'MI', 'Missouri': 'MO', 'New_York': 'NY', 'North_Carolina': 'NC'}


def sections(wt):
    """Yield (district_number, section_text) for every District N heading."""
    ms = list(re.finditer(r"\n=+\s*District\s+(\d+)\s*=+", wt))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(wt)
        yield int(m.group(1)), wt[m.end():end]


def dem_total(sec):
    """(total votes, was_the_primary_contested)."""
    for m in re.finditer(r"Democratic primary results", sec):
        tail = sec[m.start(): m.start() + 8000]
        end = tail.find("Election box end")
        blk = tail[:end] if end > 0 else tail
        tot = re.search(r"Election box total[^}]*?\|\s*votes\s*=\s*([\d,]+)", blk, re.S)
        if tot:
            return int(tot.group(1).replace(',', '')), True
        cands = re.findall(r"\|\s*votes\s*=\s*([\d,]+)", blk)
        if cands:
            return sum(int(v.replace(',', '')) for v in cands), True
    # no results box: either uncontested, or the article simply lacks the table
    low = sec.lower()
    uncontested = ('eliminated in primary' not in low) and ('democratic primary' in low)
    return None, not uncontested


rows = []
for state, ab in STATES.items():
    for y in (2024, 2026):
        path = os.path.join(SCR, f"wiki_{state}_{y}.txt")
        if not os.path.exists(path):
            continue
        wt = json.load(open(path, encoding='utf-8'))['parse']['wikitext']
        for dist, sec in sections(wt):
            tot, contested = dem_total(sec)
            rows.append({'state': ab, 'district': dist, 'cycle': y,
                         'dem_primary_votes': tot, 'contested': contested})
df = pd.DataFrame(rows).drop_duplicates(subset=['state', 'district', 'cycle'])
out = os.path.join(SCR, 'wiki_dem_primary_2024_2026.csv')
df.to_csv(out, index=False)
print(f'wrote {out}: {df.shape}')
for ab in STATES.values():
    s = df[df.state == ab]
    for y in (2024, 2026):
        t = s[s.cycle == y]
        print(f'  {ab} {y}: {len(t):2d} districts, {t.dem_primary_votes.notna().sum():2d} with a total')
