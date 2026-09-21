"""Historical NYC mayoral results at election-district level, crosswalked to current (nyed_25d) EDs:
2017 general and Democratic primary, 2021 general and Democratic primary (from the 2021 cast vote
record). 2013 is published by the BOE only as PDF recaps and is not included.

Pre-2022 contests use the 2012 ED lines (nyed_17d, nyed_21d); votes are moved to current EDs
through 2020 census blocks exactly as nyc_pull.crosswalk_2020 does. Reuses nyc_pull helpers.
"""

from pathlib import Path
import glob
import re
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd

import nyc_pull as base

RAW = base.RAW
OUT = RAW / "nyc_ed_history.csv"
FILES = {
    "mayor17g": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2017/20171107General%20Election/00001100000Citywide%20Mayor%20Citywide%20EDLevel.csv", "mayor_2017_general_citywide.csv"),
    "mayor17p": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2017/20170912Primary%20Election/01001100000Citywide%20Democratic%20Mayor%20Citywide%20EDLevel.csv", "mayor_2017_demprimary_citywide.csv"),
    "mayor21g": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2021/20211102General%20Election/00000200000Citywide%20Mayor%20Citywide%20EDLevel.csv", "mayor_2021_general_citywide.csv"),
    "cvr21p": ("https://www.vote.nyc/sites/default/files/pdf/election_results/2021/20210622Primary%20Election/cvr/PE2021_CVR_Final.zip", "PE2021_CVR_Final.zip"),
}
SHAPES = {"nyed_17d": "election-districts/nyed_17d.zip", "nyed_21d": "election-districts/nyed_21d.zip"}


def cvr_2021():
    cache = RAW / "prim21_cvr_by_ed.csv"
    if cache.exists():
        return pd.read_csv(cache, index_col="ElectDist")
    z = zipfile.ZipFile(base.fetch(*FILES["cvr21p"]))
    namefile = next(n for n in z.namelist() if "CandidacyID_To_Name" in n and n.endswith(".xlsx"))
    with z.open(namefile) as f:
        names = pd.read_excel(f)
    id2name = dict(zip(names.iloc[:, 0].astype(str), names.iloc[:, 1]))
    want = {"adams": "Eric L. Adams", "garcia": "Kathryn A. Garcia", "wiley": "Maya D. Wiley", "yang": "Andrew Yang", "stringer": "Scott M. Stringer"}
    cid = {k: next(i for i, n in id2name.items() if str(n) == v) for k, v in want.items()}
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
        frames.append(df); print(f"  {name}: {len(df)} ballots")
    b = pd.concat(frames, ignore_index=True)
    pr = b["Precinct"].str.extract(r"AD:\s*(\d+)\s*ED:\s*(\d+)")
    b["ElectDist"] = pr[0].astype(int) * 1000 + pr[1].astype(int)
    ranks = [c for c in b.columns if re.fullmatch(r"r\d", c)]
    R = b[ranks].where(b[ranks].isin(set(id2name.keys())))
    b["first"] = R.bfill(axis=1).iloc[:, 0]
    b = b[b["first"].notna()].copy(); R = R.loc[b.index]
    def pos(target):
        p = pd.Series(99, index=R.index)
        for i, c in reversed(list(enumerate(ranks))):
            p = p.where(R[c] != target, i)
        return p
    pa, pg, pw = pos(cid["adams"]), pos(cid["garcia"]), pos(cid["wiley"])
    b["h2h_adams_v_garcia"] = (pa < pg).astype(int); b["h2h_garcia_v_adams"] = (pg < pa).astype(int)
    b["h2h_adams_v_wiley"] = (pa < pw).astype(int); b["h2h_wiley_v_adams"] = (pw < pa).astype(int)
    g = b.groupby("ElectDist")
    out = pd.DataFrame({"prim21_ballots": g.size()})
    for c in ["h2h_adams_v_garcia", "h2h_garcia_v_adams", "h2h_adams_v_wiley", "h2h_wiley_v_adams"]:
        out["prim21_" + c] = g[c].sum()
    for k, i in cid.items():
        out[f"prim21_first_{k}"] = (b["first"] == i).groupby(b["ElectDist"]).sum()
    out.index.name = "ElectDist"; out.to_csv(cache)
    return out


def crosswalk(votes, ed_key, blocks, prefix):
    """votes: DataFrame indexed by old ElectDist with count columns -> current EDs via blocks."""
    bshp = glob.glob(str(RAW / "nycb2020_25d" / "**" / "nycb2020.shp"), recursive=True)[0]
    bg = gpd.read_file(bshp, engine="pyogrio")[["GEOID", "geometry"]]
    bg["GEOID"] = bg["GEOID"].astype(str).str.zfill(15)
    bg["geometry"] = bg.geometry.representative_point()
    old = gpd.read_file(glob.glob(str(RAW / ed_key / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")[["ElectDist", "geometry"]].rename(columns={"ElectDist": "ed_old"})
    new = gpd.read_file(glob.glob(str(RAW / "nyed_25d" / "**" / "nyed.shp"), recursive=True)[0], engine="pyogrio")[["ElectDist", "geometry"]].rename(columns={"ElectDist": "ed25"})
    j = gpd.sjoin(bg, old, how="inner", predicate="within")[["GEOID", "ed_old"]]
    j = gpd.sjoin(bg.merge(j, on="GEOID"), new, how="inner", predicate="within")[["GEOID", "ed_old", "ed25"]]
    j = j.merge(blocks[["GEOID", "pop"]], on="GEOID", how="left").fillna({"pop": 0})
    j["w"] = j["pop"] / j.groupby("ed_old")["pop"].transform("sum")
    j = j[j["w"].notna()].merge(votes, left_on="ed_old", right_index=True, how="inner")
    cols = list(votes.columns)
    for c in cols:
        j[c] = j[c] * j["w"]
    out = j.groupby("ed25")[cols].sum(); out.index.name = "ElectDist"
    print(f"{prefix}: carried {out[cols[0]].sum():.0f} of {votes[cols[0]].sum():.0f} in first column")
    return out


def main():
    for k, rel in SHAPES.items():
        zp = base.fetch(base.DCP + rel, f"{k}.zip")
        if not (RAW / k).exists():
            zipfile.ZipFile(zp).extractall(RAW / k)
    blocks = base.census_blocks()
    g17 = base.read_boe_edlevel(base.fetch(*FILES["mayor17g"]))
    print(g17["Unit Name"].value_counts().head(8))
    v17g = base.wide_results(g17, {"deblasio": "de Blasio", "malliotakis": "Malliotakis"}, "gen17")
    p17 = base.read_boe_edlevel(base.fetch(*FILES["mayor17p"]))
    print(p17["Unit Name"].value_counts().head(8))
    v17p = base.wide_results(p17, {"deblasio": "de Blasio", "albanese": "Albanese"}, "prim17")
    g21 = base.read_boe_edlevel(base.fetch(*FILES["mayor21g"]))
    print(g21["Unit Name"].value_counts().head(8))
    v21g = base.wide_results(g21, {"adams": "Adams", "sliwa": "Sliwa"}, "gen21")
    p21 = cvr_2021()
    num = lambda df, pre: df[[c for c in df.columns if c.startswith(pre)]].astype(float)
    parts = [crosswalk(num(v17g, "gen17"), "nyed_17d", blocks, "gen17"), crosswalk(num(v17p, "prim17"), "nyed_17d", blocks, "prim17"),
             crosswalk(num(v21g, "gen21"), "nyed_21d", blocks, "gen21"), crosswalk(p21.astype(float), "nyed_21d", blocks, "prim21")]
    hist = pd.concat(parts, axis=1)
    hist.to_csv(OUT)
    print("wrote", OUT, hist.shape)
    print("citywide: de Blasio 2017 %d Malliotakis %d | dB primary %d | Adams 2021 %d Sliwa %d | 2021 primary first: Adams %d Garcia %d Wiley %d Yang %d" % (
        hist.gen17_deblasio.sum(), hist.gen17_malliotakis.sum(), hist.prim17_deblasio.sum(), hist.gen21_adams.sum(), hist.gen21_sliwa.sum(),
        hist.prim21_first_adams.sum(), hist.prim21_first_garcia.sum(), hist.prim21_first_wiley.sum(), hist.prim21_first_yang.sum()))


if __name__ == "__main__":
    main()
