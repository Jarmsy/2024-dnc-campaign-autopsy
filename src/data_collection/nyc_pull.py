"""NYC election-district (ED) panel: 2024 presidential general, 2025 Democratic mayoral primary
(cast vote record), 2025 mayoral general, joined to 2020 Census block demographics and ACS
block-group income/education.

Sources (all public, no key except Census):
  - NYC BOE ED-level CSVs: vote.nyc/sites/default/files/pdf/election_results/<year>/<date><Event>/...EDLevel.csv
    Every row carries the 11-column header as a prefix (BOE quirk); parsed by position.
  - NYC BOE 2025 primary cast vote record zip (ballot-level, with "AD: nn ED: nnn" precinct).
    Ranked-choice contests are not published at ED level, so ED first choices and the
    Mamdani-vs-Cuomo head-to-head are built from the CVR.
  - DCP election district shapefiles nyed_24d (Nov 2024), nyed_25b (Jun 2025), nyed_25d (Nov 2025)
    and DCP 2020 census blocks nycb2020_25d, from s-media.nyc.gov/.../bytes/.
  - Census API: 2020 PL P1/P2 at block level; ACS 2023 5-year B03002/B19013/B15003/B01001 at block group.

Blocks are assigned to EDs by centroid-in-polygon; ED demographics are block-population-weighted.
"""

from pathlib import Path
import glob
import io
import os
import re
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import requests
from dotenv import load_dotenv

load_dotenv()
RAW = Path("data/raw/nyc")
OUT = RAW / "nyc_ed_panel.csv"
COUNTIES = {"005": "Bronx", "047": "Kings", "061": "New York", "081": "Queens", "085": "Richmond"}
BORO_CODE = {"New York": 1, "Bronx": 2, "Kings": 3, "Queens": 4, "Richmond": 5}
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}

FILES = {
    "pres24": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2024/20241105General%20Election/"
               "00000100000Citywide%20President%20Vice%20President%20Citywide%20EDLevel.csv", "pres_2024_general_citywide.csv"),
    "mayor25g": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20251104General%20Election/"
                 "00000100000Citywide%20Mayor%20Citywide%20EDLevel.csv", "mayor_2025_general_citywide.csv"),
    "pres20": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2020/20201103General%20Election/"
               "00000100000Citywide%20President%20Vice%20President%20Citywide%20EDLevel.csv", "pres_2020_general_citywide.csv"),
    "cvr25p": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2025/20250624Primary%20Election/rcv/2025_Primary_CVR_2025-07-17.zip",
               "2025_Primary_CVR.zip"),
}
SHAPES = {"nyed_20d": "election-districts/nyed_20d.zip", "nyed_24d": "election-districts/nyed_24d.zip", "nyed_25b": "election-districts/nyed_25b.zip",
          "nyed_25d": "election-districts/nyed_25d.zip", "nycb2020_25d": "census-blocks/nycb2020_25d.zip"}
DCP = "https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/"


def fetch(url, dest):
    dest = RAW / dest
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def read_boe_edlevel(path):
    """BOE ED-level CSV where every line = 11 header fields + 11 data fields."""
    import csv
    rows = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        for parts in csv.reader(f):
            if len(parts) < 22:
                continue
            rows.append(parts[11:22])
    df = pd.DataFrame(rows, columns=["AD", "ED", "County", "EDAD Status", "Event", "Party", "Office", "District Key", "VoteFor", "Unit Name", "Tally"])
    df["AD"] = df["AD"].astype(int); df["ED"] = df["ED"].astype(int); df["Tally"] = pd.to_numeric(df["Tally"], errors="coerce").fillna(0).astype(int)
    df["ElectDist"] = df["AD"] * 1000 + df["ED"]
    return df


def wide_results(df, candidates, prefix):
    """candidates: {label: substring of Unit Name}. Returns ED x label + total votes (excl. counters/blank)."""
    counters = {"Public Counter", "Manually Counted Emergency", "Absentee / Military", "Federal", "Affidavit", "Scattered", "Early Voting"}
    cand = df[~df["Unit Name"].isin(counters) & ~df["Unit Name"].str.contains("Public Counter|Emergency|Absentee|Affidavit|Scattered|Early Voting", regex=True)]
    out = cand.groupby("ElectDist")["Tally"].sum().rename(f"{prefix}_total").to_frame()
    for lab, pat in candidates.items():
        m = cand[cand["Unit Name"].str.contains(pat, case=False, regex=False)]
        out[f"{prefix}_{lab}"] = m.groupby("ElectDist")["Tally"].sum()
    out["county"] = cand.groupby("ElectDist")["County"].first()
    status = df.groupby("ElectDist")["EDAD Status"].first()
    out["combined_into"] = status.str.contains("COMBINED", na=False)
    return out.fillna({c: 0 for c in out.columns if c.startswith(prefix)})


def cvr_first_choices_and_h2h():
    cache = RAW / "prim25_cvr_by_ed.csv"
    if cache.exists():
        return pd.read_csv(cache, index_col="ElectDist")
    zp = fetch(*FILES["cvr25p"])
    z = zipfile.ZipFile(zp)
    with z.open("Primary Election 2025 - 06-24-2025_CandidacyID_To_Name.xlsx") as f:
        names = pd.read_excel(f)
    id2name = dict(zip(names["CandidacyID"].astype(str), names["DefaultBallotName"]))
    want = {"mamdani": "Mamdani", "cuomo": "Cuomo", "lander": "Lander", "adams": "Adrienne", "stringer": "Stringer",
            "myrie": "Myrie", "ramos": "Ramos", "blake": "Blake", "tilson": "Tilson"}
    cid = {k: next(i for i, n in id2name.items() if v in str(n)) for k, v in want.items()}
    frames = []
    for name in z.namelist():
        if not name.endswith(".xlsx") or "CandidacyID" in name:
            continue
        with z.open(name) as f:
            head = pd.read_excel(f, nrows=0)
        mcols = [c for c in head.columns if c.startswith("DEM Mayor Choice")]
        if not mcols:
            continue
        with z.open(name) as f:
            df = pd.read_excel(f, usecols=["Precinct"] + mcols, dtype=str)
        df = df.rename(columns={c: f"r{i+1}" for i, c in enumerate(sorted(mcols))})
        frames.append(df)
        print(f"  {name}: {len(df)} ballots")
    b = pd.concat(frames, ignore_index=True)
    pr = b["Precinct"].str.extract(r"AD:\s*(\d+)\s*ED:\s*(\d+)")
    b["ElectDist"] = pr[0].astype(int) * 1000 + pr[1].astype(int)
    ranks = [c for c in b.columns if re.fullmatch(r"r\d", c)]
    # first valid choice (skip blanks / undervotes / overvotes coded as non-candidate ids)
    valid_ids = set(id2name.keys())
    R = b[ranks].where(b[ranks].isin(valid_ids))          # non-candidate codes (undervote/overvote) -> NaN
    b["first"] = R.bfill(axis=1).iloc[:, 0]
    b = b[b["first"].notna()].copy(); R = R.loc[b.index]
    # head-to-head: position of Mamdani vs Cuomo among the ranks (99 = not ranked)
    def pos(target):
        p = pd.Series(99, index=R.index)
        for i, c in reversed(list(enumerate(ranks))):
            p = p.where(R[c] != target, i)
        return p
    b["pos_m"] = pos(cid["mamdani"]); b["pos_c"] = pos(cid["cuomo"])
    b["h2h_mamdani"] = (b.pos_m < b.pos_c).astype(int)
    b["h2h_cuomo"] = (b.pos_c < b.pos_m).astype(int)
    b["h2h_neither"] = ((b.pos_m == 99) & (b.pos_c == 99)).astype(int)
    g = b.groupby("ElectDist")
    out = pd.DataFrame({"prim25_ballots": g.size(), "prim25_h2h_mamdani": g["h2h_mamdani"].sum(),
                        "prim25_h2h_cuomo": g["h2h_cuomo"].sum(), "prim25_h2h_neither": g["h2h_neither"].sum()})
    for k, i in cid.items():
        out[f"prim25_first_{k}"] = (b["first"] == i).groupby(b["ElectDist"]).sum()
    out.index.name = "ElectDist"; out.to_csv(cache)
    return out


def crosswalk_2020(blocks):
    """2020 presidential votes (pre-2022 ED lines) -> 2025 EDs. Each 2020 ED's votes are spread over its
    blocks in proportion to 2020 block population, then summed within the 2025 ED containing each block."""
    p20 = read_boe_edlevel(fetch(*FILES["pres20"]))
    v20 = wide_results(p20, {"biden": "Biden", "trump": "Trump"}, "pres20")
    bshp = glob.glob(str(RAW / "nycb2020_25d" / "**" / "nycb2020.shp"), recursive=True)[0]
    bg = gpd.read_file(bshp, engine="pyogrio")[["GEOID", "geometry"]]
    bg["GEOID"] = bg["GEOID"].astype(str).str.zfill(15)
    bg["geometry"] = bg.geometry.representative_point()
    e20 = gpd.read_file(glob.glob(str(RAW / "nyed_20d" / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")[["ElectDist", "geometry"]].rename(columns={"ElectDist": "ed20"})
    e25 = gpd.read_file(glob.glob(str(RAW / "nyed_25d" / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")[["ElectDist", "geometry"]].rename(columns={"ElectDist": "ed25"})
    j = gpd.sjoin(bg, e20, how="inner", predicate="within")[["GEOID", "ed20"]]
    j = gpd.sjoin(bg.merge(j, on="GEOID"), e25, how="inner", predicate="within")[["GEOID", "ed20", "ed25"]]
    j = j.merge(blocks[["GEOID", "pop"]], on="GEOID", how="left").fillna({"pop": 0})
    j["w"] = j["pop"] / j.groupby("ed20")["pop"].transform("sum")
    j = j[j["w"].notna()]
    j = j.merge(v20[["pres20_biden", "pres20_trump", "pres20_total"]], left_on="ed20", right_index=True, how="inner")
    for c in ["pres20_biden", "pres20_trump", "pres20_total"]:
        j[c] = j[c] * j["w"]
    out = j.groupby("ed25")[["pres20_biden", "pres20_trump", "pres20_total"]].sum()
    out.index.name = "ElectDist"
    print("2020 crosswalk: Biden %d Trump %d of BOE totals %d / %d" % (out.pres20_biden.sum(), out.pres20_trump.sum(), v20.pres20_biden.sum(), v20.pres20_trump.sum()))
    return out


def census_blocks():
    key = os.getenv("CENSUS_API_KEY")
    pl = []
    for c in COUNTIES:
        r = requests.get("https://api.census.gov/data/2020/dec/pl", timeout=120, params={
            "get": "P1_001N,P2_001N,P2_002N,P2_005N,P2_006N,P2_008N", "for": "block:*", "in": f"state:36 county:{c}", "key": key})
        r.raise_for_status(); j = r.json()
        pl.append(pd.DataFrame(j[1:], columns=j[0]))
    pl = pd.concat(pl)
    pl["GEOID"] = pl["state"] + pl["county"] + pl["tract"] + pl["block"]
    for c in ["P1_001N", "P2_002N", "P2_005N", "P2_006N", "P2_008N"]:
        pl[c] = pl[c].astype(int)
    pl = pl.rename(columns={"P1_001N": "pop", "P2_002N": "hispanic", "P2_005N": "white_nh", "P2_006N": "black_nh", "P2_008N": "asian_nh"})
    acs = []
    for c in COUNTIES:
        r = requests.get("https://api.census.gov/data/2023/acs/acs5", timeout=120, params={
            "get": "B19013_001E,B15003_001E,B15003_022E,B15003_023E,B15003_024E,B15003_025E,B01001_001E,B17021_001E,B17021_002E,B25003_001E,B25003_003E",
            "for": "block group:*", "in": f"state:36 county:{c} tract:*", "key": key})
        r.raise_for_status(); j = r.json()
        acs.append(pd.DataFrame(j[1:], columns=j[0]))
    acs = pd.concat(acs)
    acs["BG"] = acs["state"] + acs["county"] + acs["tract"] + acs["block group"]
    for c in acs.columns:
        if c.startswith("B") and c != "BG":
            acs[c] = pd.to_numeric(acs[c], errors="coerce")
    acs.loc[acs["B19013_001E"] < 0, "B19013_001E"] = np.nan
    acs["bg_med_income"] = acs["B19013_001E"]
    acs["bg_ba_share"] = (acs[["B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"]].sum(axis=1) / acs["B15003_001E"]).where(acs["B15003_001E"] > 0)
    acs["bg_poverty"] = (acs["B17021_002E"] / acs["B17021_001E"]).where(acs["B17021_001E"] > 0)
    acs["bg_renter"] = (acs["B25003_003E"] / acs["B25003_001E"]).where(acs["B25003_001E"] > 0)
    pl["BG"] = pl["GEOID"].str[:12]
    return pl.merge(acs[["BG", "bg_med_income", "bg_ba_share", "bg_poverty", "bg_renter"]], on="BG", how="left")


def ed_demographics(ed_shp_key, blocks):
    shp = glob.glob(str(RAW / ed_shp_key / "**" / "nyed.shp"), recursive=True)[0]
    eds = gpd.read_file(shp, engine="pyogrio")[["ElectDist", "geometry"]]
    bshp = glob.glob(str(RAW / "nycb2020_25d" / "**" / "nycb2020.shp"), recursive=True)[0]
    bg = gpd.read_file(bshp, engine="pyogrio")[["GEOID", "geometry"]]
    bg["GEOID"] = bg["GEOID"].astype(str).str.zfill(15)
    bg["geometry"] = bg.geometry.representative_point()
    j = gpd.sjoin(bg, eds, how="inner", predicate="within")[["GEOID", "ElectDist"]]
    m = j.merge(blocks, on="GEOID", how="left")
    g = m.groupby("ElectDist")
    out = pd.DataFrame({"pop2020": g["pop"].sum()})
    for c in ["hispanic", "white_nh", "black_nh", "asian_nh"]:
        out[f"{c}_share"] = g[c].sum() / out["pop2020"]
    for c in ["bg_med_income", "bg_ba_share", "bg_poverty", "bg_renter"]:
        out[c.replace("bg_", "")] = g.apply(lambda s: np.average(s[c].dropna(), weights=s.loc[s[c].notna(), "pop"]) if s.loc[s[c].notna(), "pop"].sum() > 0 else np.nan)
    return out


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for k, rel in SHAPES.items():
        zp = fetch(DCP + rel, f"{k}.zip")
        if not (RAW / k).exists():
            zipfile.ZipFile(zp).extractall(RAW / k)
    print("2024 presidential ...")
    p24 = read_boe_edlevel(fetch(*FILES["pres24"]))
    print(p24["Unit Name"].value_counts().head(12))
    pres = wide_results(p24, {"harris": "Harris", "trump": "Trump"}, "pres24")
    print("2025 mayoral general ...")
    m25 = read_boe_edlevel(fetch(*FILES["mayor25g"]))
    print(m25["Unit Name"].value_counts().head(12))
    mayor = wide_results(m25, {"mamdani": "Mamdani", "cuomo": "Cuomo", "sliwa": "Sliwa"}, "gen25")
    print("2025 primary CVR ...")
    prim = cvr_first_choices_and_h2h()
    print("census ...")
    blocks = census_blocks()
    demo = ed_demographics("nyed_25d", blocks)
    xw20 = crosswalk_2020(blocks)
    panel = pres.join(mayor, how="outer", rsuffix="_g25").join(prim, how="outer").join(demo, how="outer").join(xw20, how="left")
    panel["county"] = panel["county"].fillna(panel.get("county_g25"))
    panel = panel.drop(columns=[c for c in panel.columns if c.endswith("_g25") and c != "combined_into_g25"])
    panel.index.name = "ElectDist"
    panel.to_csv(OUT)
    print(f"wrote {OUT}: {panel.shape}")
    print("citywide check: Harris %d Trump %d | Mamdani %d Cuomo %d Sliwa %d | primary first choices Mamdani %d Cuomo %d" % (
        panel.pres24_harris.sum(), panel.pres24_trump.sum(), panel.gen25_mamdani.sum(), panel.gen25_cuomo.sum(), panel.gen25_sliwa.sum(),
        panel.prim25_first_mamdani.sum(), panel.prim25_first_cuomo.sum()))


if __name__ == "__main__":
    main()
