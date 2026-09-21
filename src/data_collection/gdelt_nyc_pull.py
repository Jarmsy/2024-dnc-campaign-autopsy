"""GDELT DOC 2.0 API: daily coverage volume and tone for NYC mayoral candidates by news source,
2021 and 2025 cycles (the API covers 2017 onward).

Endpoint: https://api.gdeltproject.org/api/v2/doc/doc?query=...&mode=timelinevol|timelinetone
Rate limit: one request per 5 seconds (enforced here). Tone is GDELT's document-level score
(positive minus negative word share, roughly -10..+10); volume is the share of all monitored
articles that day matching the query. Both are per candidate-name phrase per source domain.
Outputs one long CSV: cycle, candidate, domain, date, volume, tone.
"""

from pathlib import Path
import time
import urllib.parse
import pandas as pd
import requests

RAW = Path("data/raw/gdelt_nyc")
API = "https://api.gdeltproject.org/api/v2/doc/doc"
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
WINDOWS = {2021: ("20210101000000", "20211103000000"), 2025: ("20250101000000", "20251105000000")}
CANDIDATES = {
    2021: {"adams": '"Eric Adams"', "yang": '"Andrew Yang"', "garcia": '"Kathryn Garcia"', "wiley": '"Maya Wiley"', "stringer": '"Scott Stringer"', "sliwa": '"Curtis Sliwa"'},
    2025: {"mamdani": "Mamdani", "cuomo": '"Andrew Cuomo"', "lander": '"Brad Lander"', "sliwa": '"Curtis Sliwa"', "adams": '"Eric Adams"', "stringer": '"Scott Stringer"'},
}
DOMAINS = ["nypost.com", "foxnews.com", "cnn.com", "msnbc.com", "nytimes.com", "nydailynews.com", "wsj.com", "gothamist.com", "thecity.nyc", "ALL"]


def fetch(query, mode, start, end):
    q = urllib.parse.quote(query)
    url = f"{API}?query={q}&mode={mode}&startdatetime={start}&enddatetime={end}&format=json"
    for attempt in range(8):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code == 200 and r.text.startswith("{"):
            j = r.json()
            series = j.get("timeline", [])
            if not series:
                return pd.DataFrame(columns=["date", "value"])
            return pd.DataFrame(series[0]["data"])
        time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"failed: {url} -> {r.status_code} {r.text[:120]}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "gdelt_nyc_daily.csv"
    done = set()
    if out.exists():
        prev = pd.read_csv(out)
        done = set(zip(prev.cycle, prev.candidate, prev.domain))
        frames = [prev]
    else:
        frames = []
    for cycle, cands in CANDIDATES.items():
        start, end = WINDOWS[cycle]
        for cand, phrase in cands.items():
            for dom in DOMAINS:
                if (cycle, cand, dom) in done:
                    continue
                query = phrase + (f" domain:{dom}" if dom != "ALL" else " sourcelang:english")
                vol = fetch(query, "timelinevol", start, end); time.sleep(15)
                tone = fetch(query, "timelinetone", start, end); time.sleep(15)
                df = vol.rename(columns={"value": "volume"}).merge(tone.rename(columns={"value": "tone"}), on="date", how="outer")
                df["cycle"] = cycle; df["candidate"] = cand; df["domain"] = dom
                frames.append(df)
                pd.concat(frames, ignore_index=True).to_csv(out, index=False)
                print(f"{cycle} {cand:9s} {dom:16s} days={len(df)} mean_vol={df.volume.mean():.4f} mean_tone={df.tone.mean():+.2f}")
    print("wrote", out)


if __name__ == "__main__":
    main()
