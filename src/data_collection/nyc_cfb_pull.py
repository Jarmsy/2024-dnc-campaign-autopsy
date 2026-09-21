"""NYC Campaign Finance Board: independent expenditures by spender and candidate (2013-2025) and
candidate-committee financial summaries.

Independent expenditures have no bulk file; the CFB publishes an ASP.NET summary page per cycle
(WebForm_Finance_Independent.aspx?as_election_cycle=YYYY) listing spenders, and a detail page per
spender (IndependentSpenderSummary.aspx?spender_id=Znnn) with a candidate x support/oppose table and
the spender's reported contributions. Both are scraped here. Candidate committees come from the
Data Library CSVs (EC{cycle}_FinancialAnalysis*.csv).
"""

from pathlib import Path
import html
import re
import time
import pandas as pd
import requests

RAW = Path("data/raw/nyc_cfb")
BASE = "https://www.nyccfb.info/vsapps/"
UA = {"User-Agent": "Mozilla/5.0 dnc-autopsy/0.1"}
CYCLES = [2013, 2017, 2021, 2025]
FIN = {2013: "/DataLibrary/EC2013_FinancialAnalysis_2013_stmt16_20160104.csv", 2017: "/DataLibrary/EC2017_FinancialAnalysis_2017_stmt16.csv",
       2021: "/DataLibrary/EC2021_FinancialAnalysis.csv", 2025: "/datalibrary/EC2025_FinancialAnalysis.csv"}


def get(url, dest):
    dest = RAW / dest
    if dest.exists() and dest.stat().st_size > 500:
        return dest.read_text(encoding="utf-8", errors="replace")
    r = requests.get(url, headers=UA, timeout=120)
    r.raise_for_status()
    dest.write_text(r.text, encoding="utf-8")
    time.sleep(0.3)
    return r.text


def strip(t):
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t).replace("‎", "").replace("‏", "").replace("\xa0", " ")
    return re.sub(r"\s+", " ", t)


def spenders_for_cycle(cycle):
    t = get(BASE + f"WebForm_Finance_Independent.aspx?as_election_cycle={cycle}", f"ie_summary_{cycle}.html")
    ids = re.findall(r'IndependentSpenderSummary\.aspx\?spender_id=([A-Z0-9]+)&amp;as_election_cycle=\d+&amp;cand_name=([^"]*)"', t)
    seen, out = set(), []
    for sid, name in ids:
        if sid not in seen:
            seen.add(sid); out.append((sid, html.unescape(name)))
    return out


def parse_spender(cycle, sid, name):
    t = get(BASE + f"IndependentSpenderSummary.aspx?spender_id={sid}&as_election_cycle={cycle}", f"spender_{cycle}_{sid}.html")
    txt = strip(t)
    m = re.search(r"has reported ([\d, .]+?) in contributions", txt)
    contrib = float(m.group(1).replace(",", "").replace(" ", "")) if m else None
    rows = []
    i = txt.find("Candidate/Proposal office total spending support oppose not determined")
    if i < 0:
        return contrib, rows
    body = txt[i + len("Candidate/Proposal office total spending support oppose not determined"):]
    body = body[: body.find(" total :")] if " total :" in body else body
    # rows look like: "Cuomo, Andrew M Mayor 19,302,958 19,302,958 - -"
    pat = re.compile(r"(.+?)\s+(Mayor|Public Advocate|Comptroller|Borough President|Boro President|City Council|Council Member|Ballot Proposal[^0-9-]*|Undeclared)\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+|-)")
    for m in pat.finditer(body):
        num = lambda s: 0.0 if s.strip() == "-" else float(s.replace(",", ""))
        rows.append({"cycle": cycle, "spender_id": sid, "spender": name, "candidate": m.group(1).strip(), "office": m.group(2).strip(),
                     "total": num(m.group(3)), "support": num(m.group(4)), "oppose": num(m.group(5)), "not_determined": num(m.group(6))})
    return contrib, rows


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    allrows, spenders = [], []
    for cycle in CYCLES:
        sp = spenders_for_cycle(cycle)
        print(f"{cycle}: {len(sp)} independent spenders")
        for sid, name in sp:
            contrib, rows = parse_spender(cycle, sid, name)
            spenders.append({"cycle": cycle, "spender_id": sid, "spender": name, "contributions": contrib, "n_rows": len(rows)})
            allrows.extend(rows)
    ie = pd.DataFrame(allrows)
    ie.to_csv(RAW / "independent_expenditures_by_candidate.csv", index=False)
    pd.DataFrame(spenders).to_csv(RAW / "independent_spenders.csv", index=False)
    mayor = ie[ie.office == "Mayor"].groupby(["cycle", "candidate"])[["support", "oppose", "total"]].sum().sort_values("total", ascending=False)
    print(mayor.head(30))
    for cycle, path in FIN.items():
        try:
            r = requests.get("https://www.nyccfb.info" + path, headers=UA, timeout=120); r.raise_for_status()
            (RAW / f"financial_analysis_{cycle}.csv").write_bytes(r.content)
            print(f"financial analysis {cycle}: {len(r.content)} bytes")
        except Exception as ex:
            print(f"financial analysis {cycle}: {ex}")


if __name__ == "__main__":
    main()
