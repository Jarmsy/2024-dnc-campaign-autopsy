"""YouTube reach of 2025-26 candidates, split into creator channels, news channels and the campaigns' own.

Why. The project's media measures cover newspapers and a news index; 81% of CES respondents report social
media as a news source and the Times credited Mamdani with working the podcast circuit that helped Trump with
young men. This measures the creator side of the attention each candidate got.

Method. YouTube Data API v3 (`YOUTUBE_API_KEY` in .env). For each candidate, two searches over the 90 days
before their election -- order=relevance and order=viewCount, 50 results each -- then `videos.list` for view
counts and `channels.list` for channel metadata. A video is kept only if its title or description names the
candidate in full (common names otherwise sweep in unrelated videos). Channels are classified by the rules in
`classify`, fixed before any result was seen: news organisations, the candidates' own and party channels, and
creators (everything else). That rule failed validation (see HAND) and
now applies only to the channels outside the hand-coded top 104.

Quota: a search costs 100 units of the 10,000 a day; the full run is about 5,000. Responses are cached, and
errors are raised without the request URL because it carries the key.

Output: `data/raw/youtube/videos.csv` (one row per candidate x video).
"""

import json
import os
from pathlib import Path
import re
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
OUT = Path("data/raw/youtube"); CACHE = OUT / "cache"
API = "https://www.googleapis.com/youtube/v3"

# candidate, race, election date, side ('left' / 'establishment' / 'other'), extra search words
CANDIDATES = [
    ("Zohran Mamdani", "2025 NYC mayor primary", "2025-06-24", "left", ""),
    ("Andrew Cuomo", "2025 NYC mayor primary", "2025-06-24", "establishment", "mayor"),
    ("Zohran Mamdani", "2025 NYC mayor general", "2025-11-04", "left", ""),
    ("Andrew Cuomo", "2025 NYC mayor general", "2025-11-04", "establishment", "mayor"),
    ("Curtis Sliwa", "2025 NYC mayor general", "2025-11-04", "other", ""),
    ("Abdul El-Sayed", "2026 MI-SEN", "2026-08-04", "left", ""),
    ("Haley Stevens", "2026 MI-SEN", "2026-08-04", "establishment", ""),
    ("Juliana Stratton", "2026 IL-SEN", "2026-03-17", "left", ""),
    ("Raja Krishnamoorthi", "2026 IL-SEN", "2026-03-17", "establishment", ""),
    ("Claire Valdez", "2026 NY-7", "2026-06-23", "left", "congress"),
    ("Antonio Reynoso", "2026 NY-7", "2026-06-23", "establishment", ""),
    ("Brad Lander", "2026 NY-10", "2026-06-23", "left", ""),
    ("Dan Goldman", "2026 NY-10", "2026-06-23", "establishment", "congress"),
    ("Darializa Avila Chevalier", "2026 NY-13", "2026-06-23", "left", ""),
    ("Adriano Espaillat", "2026 NY-13", "2026-06-23", "establishment", ""),
    ("Chuck Park", "2026 NY-6", "2026-06-23", "left", "congress"),
    ("Grace Meng", "2026 NY-6", "2026-06-23", "establishment", ""),
    ("Michael Blake", "2026 NY-15", "2026-06-23", "left", "congress"),
    ("Ritchie Torres", "2026 NY-15", "2026-06-23", "establishment", ""),
    ("Melat Kiros", "2026 CO-1", "2026-06-30", "left", ""),
    ("Diana DeGette", "2026 CO-1", "2026-06-30", "establishment", ""),
    ("Donavan McKinney", "2026 MI-13", "2026-08-04", "left", ""),
    ("Shri Thanedar", "2026 MI-13", "2026-08-04", "establishment", ""),
    ("Cori Bush", "2026 MO-1", "2026-08-04", "left", ""),
    ("Wesley Bell", "2026 MO-1", "2026-08-04", "establishment", "congress"),
]

NEWS = re.compile(
    r"\bnews\b|cnn|fox|msnbc|ms now|nbc|abc|cbs|pbs|npr|c-span|cspan|bloomberg|reuters|associated press|\bap\b|"
    r"new york times|nytimes|washington post|wall street journal|\bwsj\b|guardian|politico|the hill|axios|"
    r"newsmax|\bny1\b|pix11|wpix|wabc|wnbc|spectrum|telemundo|univision|bbc|al jazeera|sky news|cbc|"
    r"daily news|new york post|ny post|chicago tribune|sun-times|free press|detroit news|denver post|"
    r"post-dispatch|ksdk|fox 2|wxyz|wdiv|click on detroit|9news|kdvr|wgn|wbez|nj\.com|gothamist|thecity|"
    r"channel \d|\btv\b|television|radio|newspaper|tribune|times|herald|gazette|journal|telegraph|"
    r"forbes|newsweek|time magazine|the atlantic|vox|vice news|huffpost|business insider|yahoo", re.I)
OFFICIAL = re.compile(r"for (congress|mayor|senate|new york|michigan|illinois)|campaign|democrat(ic)? party|"
                      r"\bdsa\b|democratic socialists|house democrats|senate democrats|gop|republican party|"
                      r"official|congressman|congresswoman|senator|mayor's office|city of|state of", re.I)


def get(path, **params):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (re.sub(r"[^A-Za-z0-9]+", "_", path + json.dumps(params, sort_keys=True))[:180] + ".json")
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    for attempt in range(5):
        r = requests.get(f"{API}/{path}", params=dict(key=os.getenv("YOUTUBE_API_KEY"), **params), timeout=60)
        if r.status_code == 200:
            j = r.json(); f.write_text(json.dumps(j), encoding="utf-8"); time.sleep(0.2); return j
        if r.status_code == 403 and "quota" in r.text.lower():
            raise SystemExit("YouTube quota exhausted for today; rerun tomorrow (responses so far are cached)")
        time.sleep(3 * (attempt + 1))
    shown = {k: v for k, v in params.items() if k != "key"}
    raise RuntimeError(f"YouTube {path} {shown} -> {r.status_code}")   # never the URL: it carries the key


def classify(candidate, ch_title, ch_desc):
    t = f"{ch_title} {ch_desc[:300]}"
    last = candidate.split()[-1].lower()
    if last in ch_title.lower() or OFFICIAL.search(ch_title):
        return "campaign"
    if NEWS.search(t):
        return "news"
    return "creator"

# The pre-set regex rule failed validation before any comparison was run: channel descriptions mention "news"
# (HasanAbi, Zeteo, The Majority Report, The Young Turks were scored as news) and legacy entertainment scored
# as creators (Saturday Night Live, Colbert). The 104 channels carrying 95% of views are therefore coded by hand
# under written rules, and the regex applies only to the remaining 5%.
#   news          legacy or professional news organisations, incl. online-only newsrooms (Middle East Eye)
#   entertainment legacy entertainment: network sketch/late-night/talk shows, syndicated radio
#   creator       online-first individuals and shows: podcasts, streams, commentary, clip and street-interview
#                 channels, independent online outlets (Zeteo, More Perfect Union, The Bulwark, The Free Press)
#   political     candidates, parties, PACs, politicians, advocacy organisations and advocacy media
# Paid promotion: a channel under 5,000 subscribers with a video over 100,000 views is coded political.
HAND = {k: "news" for k in [
    "NBC New York", "CNN", "The New Yorker", "Washington Post", "Middle East Eye", "MS NOW", "NBC News",
    "Democracy Now!", "CBS New York", "Al Jazeera English", "DRM News", "The Economist", "FOX 2 Detroit",
    "Forbes Breaking News", "NY1", "Fox News", "Bloomberg News", "POLITICO", "CBS News", "Oneindia News",
    "Newsweek", "TRT World", "WNYC", "Brut India", "The New York Times", "FOX 5 New York", "BrooklynVegan"]}
HAND.update({k: "entertainment" for k in [
    "Saturday Night Live", "The Daily Show", "The View", "The Late Show with Stephen Colbert",
    "Breakfast Club Power 105.1 FM"]})
HAND.update({k: "creator" for k in [
    "HasanAbi", "Zeteo", "More Perfect Union", "Nimrod Kamer", "The Rubin Report", "Are You Okay?",
    "The Majority Report w/ Sam Seder", "Channel 5 with Andrew Callaghan", "Elder Ordonez", "Secular Talk",
    "The Brief Exchange", "New York Street", "FLAGRANT", "The Young Turks", "Red Shorts Politics",
    "Breaking Points", "Lukas Arnold", "Lyfe wise", "Stickman Talks", "Megyn Kelly", "The Bulwark",
    "Hasan Reactions", "The Rational National", "Inaam Khan", "I've Had It", "Hadi Rahim", "Town Manager",
    "Jack Cocchiarella", "Vaush", "Brandon Lehman", "FLAGRANT CLIPS", "The Humanist Report", "Gianmarco Soresi",
    "Off The Press", "Rumour Juice", "Todd Bieber", "MeidasTouch", "Bill O'Reilly", "PalPulse",
    "DeFranco News Clips", "Valuetainment", "HasanAbi Archive", "Corey Shawn", "Pod Save America",
    "Lamont Tyson", "Hook Global", "Pop Politic", "Ayyan", "Difficult-ish", "AMANI", "luke attempted",
    "Hasan Minhaj", "The Free Press", "Jemele Hill"]})
HAND.update({k: "political" for k in [
    "Zohran Mamdani for NYC", "Curtis Sliwa", "Andrew Cuomo", "Antonio Reynoso for Congress", "Diana DeGette",
    "Claire Valdez for Congress", "Justice Democrats", "Chuck Park for Queens", "U.S. Democratic Socialists",
    "Bernie Sanders", "Ritchie Torres", "Our Congressmember Grace Meng", "Congressman Dan Goldman",
    "Fuente Latina", "Real Fight NYC", "MAJORITY VOICE HUB", "The Fellowship PAC", "Young People for a New Era"]})


def kind(channel, subs, max_views, fallback):
    if channel in HAND:
        return HAND[channel]
    if subs < 5000 and max_views > 100_000:
        return "political"                      # paid promotion
    return {"campaign": "political"}.get(fallback, fallback)


def main():
    rows = []
    for cand, race, date, side, extra in CANDIDATES:
        end = pd.Timestamp(date) + pd.Timedelta(days=1)
        start = end - pd.Timedelta(days=91)
        ids = {}
        for order in ("relevance", "viewCount"):
            j = get("search", part="snippet", q=f'"{cand}" {extra}'.strip(), type="video", maxResults=50, order=order,
                    publishedAfter=start.strftime("%Y-%m-%dT00:00:00Z"), publishedBefore=end.strftime("%Y-%m-%dT00:00:00Z"))
            for it in j.get("items", []):
                ids[it["id"]["videoId"]] = it["snippet"]
        vids = list(ids)
        stats, chans = {}, {}
        for i in range(0, len(vids), 50):
            j = get("videos", part="statistics,snippet", id=",".join(vids[i:i + 50]), maxResults=50)
            for it in j.get("items", []):
                stats[it["id"]] = it
        cids = sorted({v["snippet"]["channelId"] for v in stats.values()})
        for i in range(0, len(cids), 50):
            j = get("channels", part="snippet,statistics", id=",".join(cids[i:i + 50]), maxResults=50)
            for it in j.get("items", []):
                chans[it["id"]] = it
        full = cand.lower()
        for vid, it in stats.items():
            sn = it["snippet"]
            text = f"{sn.get('title', '')} {sn.get('description', '')}".lower()
            if full not in text and full.replace("-", " ") not in text:
                continue
            ch = chans.get(sn["channelId"], {})
            ch_title = ch.get("snippet", {}).get("title", sn.get("channelTitle", ""))
            ch_desc = ch.get("snippet", {}).get("description", "")
            rows.append(dict(candidate=cand, race=race, election=date, side=side, video_id=vid,
                             published=sn.get("publishedAt", "")[:10], title=sn.get("title", ""),
                             channel_id=sn["channelId"], channel=ch_title,
                             channel_subs=int(ch.get("statistics", {}).get("subscriberCount", 0) or 0),
                             views=int(it.get("statistics", {}).get("viewCount", 0) or 0),
                             kind=classify(cand, ch_title, ch_desc)))
        n = sum(1 for r in rows if r["candidate"] == cand and r["race"] == race)
        print(f"  {race:24s} {cand:26s} {len(vids):3d} found, {n:3d} name the candidate")
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.DataFrame(rows)
    mx = d.groupby("channel").views.transform("max")
    d["kind_rule"] = d.kind
    d["kind"] = [kind(c, s_, m_, k) for c, s_, m_, k in zip(d.channel, d.channel_subs, mx, d.kind_rule)]
    d.to_csv(OUT / "videos.csv", index=False)
    print(f"wrote {OUT / 'videos.csv'}: {len(d)} rows")


if __name__ == "__main__":
    main()
