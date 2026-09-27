# Handoff: "Why Democrats Lost the Voters They Lost" portfolio page

**For:** the Claude Code session that builds the user's Astro website.
**From:** the analysis session in `C:\Users\starh\OneDrive\Desktop\Projects\2024 DNC Campaign autopsy`.

## What this is

An interactive project page for the user's portfolio, summarizing a data-driven autopsy of the 2024 US presidential election. Most visitors will be **hiring managers and recruiters** (roles in data or business analytics, political strategy, and policy research) arriving from job applications. They should get, in about five minutes:

1. **a clear thesis**;
2. **8 readable interactive charts**;
3. **evidence of careful method:** each section explains how the finding was established, plus a sidebar where the user found and corrected an error in their own numbers.

**Thesis:** Democrats didn't lose the 2024 swing voters because those voters feared left-wing economics; they largely agreed with it. By 2022 they had decided the Biden government wasn't delivering, and their views on Trump, immigration and health care changed only after they switched. It was a credibility problem, not a platform problem.

## Files (all in `portfolio/`)

| File | Use |
|---|---|
| `content.md` | The full page text with frontmatter. Chart slots are marked `{{CHART:<id>}}`. Convert to the site's MDX and page conventions; keep the wording and every number. |
| `CHARTS.md` | A spec per chart: data, form, colors, tooltips, caption, and mobile behavior. |
| `data/*.json` | One file per chart; the **only** source of numbers. Copy into the site, e.g. `src/data/dnc-autopsy/`. |
| `data/CHECKS.txt` | Headline numbers checked against the report, for reference. |
| `export_data.py` | Regenerates `data/` from the analysis repo. You don't need it; it's for the analysis session. |

## Guardrails (please keep)

1. **Don't retype, round or restate numbers** beyond what the JSON and `content.md` show. If a number seems off, ask the analysis session; don't fix it.
2. **Keep the caveats:** the small-sample notes (21 and 39 switchers), "what it doesn't show" lines, and the unweighted label on chart 04. They're part of the pitch, since they show judgment.
3. **Keep the group colors consistent** across charts (table in `CHARTS.md`), validated for colour-blind readers in light and dark modes.
4. **Keep the tone nonpartisan.** It's an analysis, not advocacy.
5. **Chart 08's El-Sayed row is a placeholder** until results arrive in late November 2026; render it as "pending".

## Suggested build

- **Observable Plot** (`@observablehq/plot`) in client-side scripts or as an Astro island, one component per chart, reading its JSON via import.
- Respect the site's existing light and dark theme; colors are given for both.
- Check at 375px width and on desktop.

## Deliberately left out

The analysis repo also covers insurgent House primaries, super PAC ad coding, news-framing analysis (GDELT, the NYT archive), local news deserts and YouTube reach. These are out of scope for this page; a possible second post later.

## Links used on the page

- Repo: https://github.com/Jarmsy/2024-dnc-campaign-autopsy
- Full report: `report/main_report.md` in the repo
- Pre-registration: `report/preregistration_2026_general.md` (plus `..._addendum_1.md`)
