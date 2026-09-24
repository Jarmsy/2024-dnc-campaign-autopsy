"""Codebook for super PAC ads in Democratic primaries: what the money says, against what it is for.

Written before any ad was read (2026-09-24). The universe is every Democratic primary, runoff or special
primary, 2022-2026, in which United Democracy Project (AIPAC), DMFI PAC, Fairshake (crypto) or Protect
Progress (Fairshake's Democratic-side affiliate) spent $1M or more (`data/coded/superpac_races_for_coding.csv`, 32 races, from
`superpac_ie_pull.py`). One row per distinct ad or mailer in `data/coded/superpac_ads_coded.csv` (tracked in git: hand-coded, not regenerable), with
the source that describes it. An ad is coded only from a source that quotes or describes its content;
spending with no described ad is recorded as `undocumented`, never inferred.

Each ad gets every mode that applies (multi-label), plus a `lead` mode: the claim the ad opens or closes
on, or the one its headline repeats.

Hypotheses fixed in advance
1. Mismatch: the committees' own issue (Israel for UDP/DMFI, crypto for Fairshake/Protect Progress) appears
   in a minority of their ads. Test: share of ads with `own_issue`.
2. Is it specific to pro-Israel money? Compare the own-issue share between the Israel and crypto committees.
   If both are low, attacking on something other than one's own issue is general super PAC practice.
3. Is it new? Compare 2022 with 2024-26 for the Israel committees. If `own_issue` was already rare in 2022,
   the avoidance predates the shift in public opinion on Gaza.
4. Identity: `terror_association` and `identity_coded` fall on Muslim and Arab targets more than on other
   targets with comparable Israel positions.

Emergent categories. Any theme that recurs in two or more ads and fits none of the modes below becomes a
new mode, defined in EMERGENT with the date and the ads that prompted it. Existing definitions are not
widened after the fact to absorb a new theme.
"""

import pandas as pd

MODES = {
    "own_issue": "Names the committee's own cause: Israel, Gaza, Hamas, antisemitism (UDP, DMFI); crypto, "
                 "digital assets, blockchain (Fairshake, Protect Progress).",
    "party_disloyalty": "Target is disloyal to Democrats or their leaders: attacked Biden/Obama/Harris, "
                        "voted against the party, 'not a real Democrat', backed third parties or 'uncommitted'.",
    "helps_republicans": "Target would help Trump or Republicans, or cannot win a general election.",
    "character": "Personal conduct or temperament: treatment of women or staff, honesty, scandal, "
                 "lawsuits, arrogance, divisiveness.",
    "record_performance": "Job performance: missed votes, absenteeism, ineffectiveness, 'no results', "
                          "spending on self (e.g. security costs).",
    "ideology_label": "Labels the target's ideology: radical, extreme, far-left, socialist, 'the Squad'.",
    "policy_other": "A specific policy position other than the committee's own issue: taxes, policing, "
                    "healthcare, immigration, energy, guns.",
    "terror_association": "Links the target to terrorism or violent extremism: 'sympathy for terrorists', "
                          "ties to extremist figures or groups.",
    "identity_coded": "Draws attention to the target's religion, ethnicity or national origin, or uses "
                      "imagery or associations that do so, without stating a policy.",
    "money_hypocrisy": "Target's own donors, self-dealing, or special-interest money.",
    "positive_other": "Promotes the committee's preferred candidate (biography, record, endorsements) "
                      "without attacking the opponent.",
}

EMERGENT = {   # name -> (definition, date added, ads that prompted it)
    "progressive_mimicry": ("Uses progressive or populist themes (anti-Trump, anti-ICE, anti-billionaire, "
                            "'real progressive results', criminal-justice reform) to brand the favored candidate or "
                            "to attack the target from the left.", "2026-09-24", [7, 36, 37, 38, 39, 40, 41, 42, 44]),
    "borrowed_voice": ("Carries the attack or endorsement in a third party's words: a Democratic leader, an "
                       "activist, a newspaper editorial, or 'Democrats called ...'.", "2026-09-24", [6, 25, 30, 37, 38]),
    "corruption_crime": ("Accuses the target of corruption or crime, or ties them to a convicted figure "
                         "(bank fraud, tax settlements, 'ally of' a convicted speaker, stock trading).",
                         "2026-09-24", [18, 19, 20, 39]),
    "guilt_by_association": ("Attacks the target for appearing with, praising or meeting a controversial "
                             "non-terrorist figure (e.g. a streamer or an activist scholar).", "2026-09-24", [5, 43]),
    "doctored_material": ("Altered images or fabricated attributions: a reshaped photo, invented newspaper "
                          "headlines.", "2026-09-24", [13, 48]),
}

# Whether a named outlet or fact-checker called the ad's central claim false, misleading, baseless,
# distorted or fabricated (the `disputed_by` column); an ad is not coded disputed on the target's word alone.

SPENDER_ISSUE = {"UDP": "israel", "DMFI": "israel", "Fairshake": "crypto", "Protect Progress": "crypto"}


def load(path="data/coded/superpac_ads_coded.csv"):
    d = pd.read_csv(path)
    modes = list(MODES) + list(EMERGENT)
    for m in modes:
        d[m] = d.modes.fillna("").str.split(";").map(lambda xs: m in [x.strip() for x in xs])
    d["issue"] = d.spender.map(SPENDER_ISSUE)
    return d, modes


def mode_shares(d, modes, by="issue"):
    """Share of ads carrying each mode, and share led by each mode, by committee type."""
    carry = d.groupby(by)[modes].mean().T
    lead = pd.crosstab(d.lead, d[by], normalize="columns")
    return carry, lead
