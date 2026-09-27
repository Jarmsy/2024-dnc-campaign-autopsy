# Chart specs

One entry per `{{CHART:<id>}}` slot in `content.md`. Data: `data/<id>.json` (each file has a `note` explaining the numbers). Build with whatever the site already uses; the recommendation is **Observable Plot** in a client-side script, which fits Astro islands well.

## Rules for every chart

- **Numbers come only from the JSON.** Never retype or round differently from what's shown; one decimal for percentages and points unless noted.
- **Group colors are fixed across all charts.** Color follows the group, never its position:

  | Role | Light | Dark |
  |---|---|---|
  | Loyal Democrats (Biden→Harris) | `#2a78d6` | `#3987e5` |
  | Switchers (Biden→Trump) | `#d97706` | `#c98500` |
  | Loyal Republicans (Trump→Trump) | `#b8323a` | `#d9485c` |
  | Highlight / 4th series (e.g. Mamdani, El-Sayed) | `#6a55b8` | `#9085e9` |
  | Other / reference series | `#8a8a86` | `#8f8e87` |

  Validated for colour-blind separation and contrast in both modes. The orange is just under 3:1 contrast in light mode, so **direct-label the lines and points** rather than relying on a legend alone.
- **Hover tooltips** on every mark, showing the exact value and, where given, N or a count.
- **Direct labels** on lines, with a legend as well when there are two or more series. Axis titles in plain words. Thin marks; a light grid.
- **Every chart has a caption** (text provided below) and an accessible data-table fallback (a `<details>` element with the table is fine).
- **Phone width (375px) must work:** stack small multiples vertically, and keep the tick labels short.

---

### 01_fundamentals: "The loss the conditions predicted"
- **Data:** `elections[]` (year, actual, predicted, incumbent_party) and `harris_2024` (predicted 47.9, actual 49.25, error_band_pp 3.75).
- **Form:** a dot plot by year (x = year 1948–2024, y = Democratic two-party share). A grey hollow dot for each prediction, a filled dot for each actual, and a thin line joining the pair. For 2024, draw the prediction with a ±3.75 shaded band, and highlight 2024 with the highlight color.
- **Caption:** "Each pair is one election: the model's prediction (hollow) and the actual result (filled). For 2024 the model, fit on 1948–2020, predicted 47.9%; Harris won 49.25%, inside its usual margin of error (shaded)."

### 02_turnout_vs_share: "Where the votes went"
- **Data:** `bins[]`: county groups by 2020 Democratic share, with turnout_M and share_M (millions of Democratic votes; negative = lost).
- **Form:** horizontal diverging bars, one row per county group ("R strongholds" through "D strongholds"), split into the turnout part and the share part. Use two neutral tones from one hue, not party colors, since these are components, not groups.
- **Caption:** "Change in Democratic votes, 2020→2024, by how Democratic the county was. In the strongest Democratic counties most of the loss was turnout, 2.9 million votes in total, but those counties were mostly in safe states."

### 02b_stayhome_counterfactual: "Would the stay-homes have changed anything?"
- **Data:** `states[]`: margin_2024 (Democratic margin, negative = lost), net_if_stayhomes_voted, lo, hi.
- **Form:** a paired horizontal bar per state (the seven swing states plus National): the actual margin, and the margin if the stay-homes had voted, with the interval. Draw a zero line; a state flips only if it crosses zero.
- **Caption:** "If every 2020 voter who stayed home in 2024 had voted as in 2020, no swing state flips."

### 03_perception_by_party: "The economy through a partisan lens"
- **Data:** `years[]`: mean economic rating (+2 much better … −2 much worse) for Democrats, Independents and Republicans in 2016, 2020, 2024, plus the incumbent party.
- **Form:** a slope chart with three lines (parties) across the three years. Use party-hue lines (Democrats blue, Republicans red, Independents grey); these are party identifiers, not the vote-path groups, so label them clearly. Shade the background or tag each year with who held the White House. Optional toggle: show the `variance_explained` pair (0.6% county economy vs 34% party) as two big numbers beside it.
- **Caption:** "How each party's voters rated the national economy flipped whenever the White House changed hands. A county's actual economic record explains 0.6% of the differences in ratings; party explains 34%."

### 04_rating_2022_predicts_switch: "The bad rating came first"
- **Data:** `ratings[]`: 2022 rating, N, switched, rate_unweighted, rate_weighted.
- **Form:** vertical bars of **rate_unweighted** by 2022 rating (much worse → much better), in the switcher color. Tooltip: "19 of 240 switched". Show weighted rates only in the table fallback.
- **Caption:** "Biden 2020 voters, grouped by how they rated the economy in 2022. Share who voted Trump two years later. Not one of the 438 who saw improvement switched. (Same people re-interviewed; unweighted.)"

### 05_issue_positions: "Agreeing on economics, not on immigration"
- **Data:** `items[]`: axis (economic / immigration / social), item label, and the shares for loyal_democrats, switchers and loyal_republicans taking the Democratic-aligned position.
- **Form:** a dot plot. One row per item, grouped by axis, with x = share (0–100%) and three dots per row in the group colors joined by a thin line. Sort within each axis group.
- **Caption:** "Share taking the Democratic position, 2024. Switchers (orange) sit near loyal Democrats on economic policy and near loyal Republicans on immigration."

### 06_order_of_events: CENTREPIECE, "The order of events"
- **Data:** `series[]`, one row per measure × wave: loyal, switchers, switchers_lo, switchers_hi, N_switchers, and switchers_count for the ANES measure. The measures:
  - "approves Biden" (2022, 2024)
  - "voted Democratic for House, 2022 (of voters)" (2022)
  - "supports Medicare for all" (2020, 2022, 2024)
  - "immigration conservatism (0-1)" (2020, 2022, 2024)
  - "says Trump 'really cares about people like you' (ANES)" (2016, 2020, 2024)
  - "economy got worse" (2020, 2022, 2024)
- **Form:** small multiples, one panel per measure. x = year; two lines, switchers (orange, with a light interval band) and loyal Democrats (blue). A shared vertical guide at 2022 labelled "before the campaign". Recommended order: approves Biden → Medicare for all → immigration → Trump cares. Put "economy got worse" and "voted Democratic for House" in a collapsible "more" row.
- **Tooltip must show N:** "Switchers, 2022: 31% (n = 38)"; for the ANES item: "2 of 21".
- **Caption:** "The same people followed over time. By 2022, future switchers had turned on the Biden government but still backed Medicare for All; their policy views and their picture of Trump changed only between 2022 and 2024. Switcher samples are small (39 and 21); bands show uncertainty."

### sidebar_recall: "The bug in my own numbers"
- **Data:** `panel` (44 recalled switchers, 34 real, 9 who had reported Trump) and `corrections` (before/after for the switch rate 5.2→4.1, the ratio 3.4→2.6, the switching share of the shift 62→53%, and the "much worse" switch rate 31.6→28.0).
- **Form:** (a) a unit chart of 44 squares: 34 in the switcher color, 9 in the Republican color labelled "had voted Trump in 2020", 1 grey "no 2020 report". (b) Beside it, a before/after arrow list of the four corrections.
- **Caption:** "Of 44 people who remembered switching from Biden to Trump, 9 had told the same survey in 2020 that they voted Trump. Correcting for this shrank my estimates but left the patterns intact."

### 07_nyc_same_ballot: "Every Democrat gained where voters had swung"
- **Data:** `deciles[]`: swing_to_trump_2024 (x) and mamdani_vs_harris, levine_vs_harris, williams_vs_harris (y, points).
- **Form:** a line chart over the 10 deciles, x = the 2020→24 swing to Trump (points). Mamdani in the highlight violet; Levine and Williams in the grey reference tone, direct-labelled. Zero line.
- **Caption:** "New York City election districts grouped by how far they swung to Trump in 2024. Each line is a 2025 Democrat's share minus Harris's. All three Democrats gained most where the swing was largest; the comptroller and public advocate gained more than Mamdani."

### 08_testA_benchmark: "The pre-registered test"
- **Data:** `rows[]`: comparison, sample, kind, slope, lo, hi. The El-Sayed row has null values until results exist.
- **Form:** a horizontal dot-and-interval plot. Grey band from −0.1 to +0.1 labelled "ordinary candidate differences". Group the 2022 benchmark rows in grey, the 2024 dry run in muted grey with the tag "pipeline check (presidential ticket-splitting)", and the El-Sayed row as a highlight-violet placeholder reading "result: late November 2026".
- **Caption:** "How much the gap between two Democrats on the same Michigan ballot tracks the 2020→24 swing to Trump. Ordinary down-ballot pairs sit near zero. The 2026 El-Sayed–Benson result will count as meaningful only if it lands clearly outside the grey band."
