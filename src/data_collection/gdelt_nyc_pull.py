"""GDELT DOC 2.0 API: daily coverage volume and tone for NYC mayoral candidates by news source,
2021 and 2025 cycles (the API covers 2017 onward).

Endpoint: https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=timelinevol|timelinetone
Rate limit: one request per 5 seconds (enforced here). Tone is GDELT's document-level score
(positive minus negative word share, roughly -10..+10); volume is the share of all monitored
articles that day matching the query. Both are per candidate-name phrase per source domain.
Outputs one long CSV: cycle, candidate, domain, date, volume, tone.

Retry pacing is set from the logs, not from the API's advice. Acceptance is ~21% per attempt and
does not improve with longer waits (23.0% at 120-360 s vs 20.5% at 60 s, z = 0.61), so there is no
cooldown to wait out. Rejections do cluster -- runs of 6+ consecutive refusals are twice as common as
a memoryless process would give -- so some of the wait is a real server-side bad patch that polling
cannot shorten; it can only be detected sooner. Measured elasticity between the two runs: polling
1.85x faster raised the reject count 1.16x and cut total wait 37%. Hence a short flat retry (RETRY s),
which still works out to about one request per 32 s while throttled, well inside the stated 5 s floor.
Progress is checkpointed per candidate x domain; series the API returns empty (a domain GDELT does
not index) are recorded in empty_series.txt so they are not re-fetched.
"""

from pathlib import Path
import json
import time
import urllib.parse
import pandas as pd
import requests

RAW = Path("data/raw/gdelt_nyc")
API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
WINDOWS = {2021: ("20210101000000", "20211103000000"), 2025: ("20250101000000", "20251105000000")}
# Ordered: the candidates the notebook's tone-gap comparison needs come first so a partial run is usable.
CANDIDATES = [
    (2025, "mamdani", "Mamdani"), (2025, "cuomo", '"Andrew Cuomo"'),
    (2021, "adams", '"Eric Adams"'), (2021, "garcia", '"Kathryn Garcia"'), (2021, "wiley", '"Maya Wiley"'), (2021, "yang", '"Andrew Yang"'),
    (2025, "sliwa", '"Curtis Sliwa"'), (2025, "lander", '"Brad Lander"'), (2021, "sliwa", '"Curtis Sliwa"'), (2021, "stringer", '"Scott Stringer"'),
    (2025, "adams", '"Eric Adams"'), (2025, "stringer", '"Scott Stringer"'),
]
DOMAINS = ["foxnews.com", "cnn.com", "msnbc.com", "nytimes.com", "ALL", "nypost.com", "nydailynews.com",
           "washingtonpost.com", "gothamist.com", "politico.com", "wsj.com", "apnews.com"]
# Domains GDELT may not index at all: checked once with a generic query and skipped if empty.
PROBE_DOMAINS = ["nypost.com", "nydailynews.com", "washingtonpost.com", "gothamist.com", "politico.com", "wsj.com", "apnews.com"]
PAUSE = 20
RETRY = 20


def fetch(query, mode, start, end):
    q = urllib.parse.quote(query)
    url = f"{API}?query={q}&mode={mode}&startdatetime={start}&enddatetime={end}&format=json"
    attempt = 0
    while True:
        t0 = time.time()
        try:
            r = requests.get(url, headers=UA, timeout=900)
        except requests.RequestException as e:
            print(f"    {type(e).__name__} after {time.time() - t0:.0f} s; waiting 120 s", flush=True)
            time.sleep(120); continue
        if r.status_code == 200 and r.text.startswith("{"):
            series = r.json().get("timeline", [])
            if attempt or time.time() - t0 > 30:
                print(f"    ok after {attempt} throttles, {time.time() - t0:.0f} s", flush=True)
            if not series:
                return pd.DataFrame(columns=["date", "value"])
            return pd.DataFrame(series[0]["data"])
        attempt += 1
        body = r.text.strip().replace("\n", " ")[:120]
        print(f"    throttled ({r.status_code}) attempt {attempt}, {time.time() - t0:.0f} s: {body!r}; waiting {RETRY} s", flush=True)
        time.sleep(RETRY)


def probe_domains():
    """One generic query per doubtful domain over the 2025 window; empty means GDELT does not carry the site."""
    cache = RAW / "domain_probe.json"
    dead = json.loads(cache.read_text()) if cache.exists() else {}
    for dom in PROBE_DOMAINS:
        if dom in dead:
            continue
        start, end = WINDOWS[2025]
        df = fetch(f"mayor domain:{dom}", "timelinevol", start, end)
        dead[dom] = bool(df.empty or df.value.sum() == 0)
        print(f"probe {dom}: days={len(df)} total={df.value.sum() if len(df) else 0:.4f} -> {'SKIP' if dead[dom] else 'ok'}", flush=True)
        cache.write_text(json.dumps(dead, indent=1))
        time.sleep(PAUSE)
    return {d for d, v in dead.items() if v}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "gdelt_nyc_daily.csv"
    empties = RAW / "empty_series.txt"
    done = set()
    if out.exists():
        prev = pd.read_csv(out)
        done = set(zip(prev.cycle, prev.candidate, prev.domain))
        frames = [prev]
    else:
        frames = []
    if empties.exists():
        done |= {(int(c), a, d) for c, a, d in (l.split(",") for l in empties.read_text().split("\n") if l.strip())}
    skip = probe_domains()
    for cycle, cand, phrase in CANDIDATES:
        start, end = WINDOWS[cycle]
        for dom in DOMAINS:
            if (cycle, cand, dom) in done or dom in skip:
                continue
            query = phrase + (f" domain:{dom}" if dom != "ALL" else " sourcelang:english")
            vol = fetch(query, "timelinevol", start, end); time.sleep(PAUSE)
            tone = fetch(query, "timelinetone", start, end); time.sleep(PAUSE)
            df = vol.rename(columns={"value": "volume"}).merge(tone.rename(columns={"value": "tone"}), on="date", how="outer")
            if df.empty:
                with empties.open("a") as f:
                    f.write(f"{cycle},{cand},{dom}\n")
                print(f"{cycle} {cand:9s} {dom:16s} EMPTY (recorded)", flush=True)
                continue
            df["cycle"] = cycle; df["candidate"] = cand; df["domain"] = dom
            frames.append(df)
            pd.concat(frames, ignore_index=True).to_csv(out, index=False)
            print(f"{cycle} {cand:9s} {dom:16s} days={len(df)} mean_vol={df.volume.mean():.4f} mean_tone={df.tone.mean():+.2f}", flush=True)
    print("wrote", out)


if __name__ == "__main__":
    main()
