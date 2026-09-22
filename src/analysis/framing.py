"""Framing measures for candidate coverage: what a headline calls someone, not how positive its words are.

The design problem this solves. Sentiment scoring fails on political coverage because it reads word
valence in isolation -- Part 10 documents an A1 headline leading with a candidate's religion that
scores negative on the unrelated tokens *war* and *criticism*. Framing is not valence. It is which
description a headline reaches for, and the informative comparison is between descriptions that
refer to the same fact.

That last point drives the whole lexicon. Calling a Democratic Socialists of America member a
"democratic socialist" is accurate reporting, and a naive "socialist-mention rate" would score
accurate description and hostile labelling identically, then find -- trivially and uselessly -- that
DSA candidates are called socialists more often. So labels are split by register:

  SELF_DESCRIPTION  the candidate's own term and neutral synonyms: democratic socialist, progressive
  LOADED            intensified or historically weaponised variants: radical, far-left, Marxist,
                    communist, extremist, bare "socialist" where "democratic" does not precede it
  THREAT            fear framing independent of any label: dangerous, takeover, purge, threat
  DELEGITIMISING    treats the candidacy as unserious: fringe, upstart, unqualified, gadfly

The measure of interest is then the **loaded share** -- loaded labels as a fraction of all
ideological labels -- which asks, of the times a headline reached for an ideological description,
how often it reached for the hostile one. That is comparable across candidates whose actual
politics differ, which a raw rate is not.

Limits that do not go away. Headlines only, so a piece can be scrupulous in the body and loaded in
the headline or the reverse. A term appearing is not a claim about how it was used: "Republicans
call her a radical" and "the radical candidate" both match. No inference about any individual
article is supported; these are rates over corpora.
"""

import re

import numpy as np
import pandas as pd

# "democratic socialist" is accurate for a DSA member; bare "socialist" is the loaded register.
# Matching the phrase first lets the bare pattern be computed as a residual rather than double-counting.
DEMSOC = r"democratic[\s-]socialis|democratic[\s-]socialism"

FRAMES = {
    "self_description": r"\bprogressive|\bdemocratic[\s-]socialis|\bleft[\s-]wing\b|\bliberal\b",
    "loaded_label": (r"\bradical|\bfar[\s-]left|\bhard[\s-]left|\bultra[\s-]left|\bextremis|\bextreme\b|"
                     r"\bmarxis|\bcommunis|\bsocialist\b|\bsocialism\b|\bleftis"),
    "threat": (r"\bthreat|\bdanger|\btakeover|\btake over\b|\bpurge|\bpurity\b|\bwar on\b|\bdestroy|"
               r"\battack on\b|\bassault on\b|\bcoup\b|\binvasion\b"),
    "delegitimising": r"\bfringe\b|\bupstart\b|\bunqualified\b|\bgadfly\b|\bnovice\b|\bunknown\b|\binexperienc",
    "identity": r"\bmuslim|\bislam|\bjewish\b|\bsomali|\bimmigrant\b|\bforeign[\s-]born\b|\bnaturaliz",
    "israel_gaza": r"\bisrael|\bgaza|\bpalestin|\bantisemit|\banti[\s-]semit|\bhamas|\bzionis|\bintifada|\bbds\b",
    "insurgency": r"\bprimary\b|\bprimaried\b|\bchalleng|\bousted?\b|\bunseat|\btoppl|\bupset\b",
    "policy": (r"\bmedicare for all\b|\bgreen new deal\b|\bminimum wage\b|\bhealth ?care\b|\bhousing\b|"
               r"\brent\b|\bclimate\b|\bstudent debt\b|\btuition\b|\bchild ?care\b"),
}

# Right-leaning and movement-conservative outlets, where "fear framing" is most often alleged.
RIGHT = {"foxnews.com", "breitbart.com", "dailywire.com", "washingtontimes.com", "nypost.com",
         "dailycaller.com", "newsmax.com", "theblaze.com", "nationalreview.com", "washingtonexaminer.com",
         "thefederalist.com", "pjmedia.com", "townhall.com", "redstate.com", "freebeacon.com"}
MAINSTREAM = {"cnn.com", "nytimes.com", "washingtonpost.com", "apnews.com", "reuters.com", "nbcnews.com",
              "abcnews.go.com", "cbsnews.com", "usatoday.com", "politico.com", "thehill.com", "axios.com",
              "npr.org", "bloomberg.com", "msnbc.com", "theguardian.com"}


def outlet_class(domain):
    d = str(domain).lower()
    if d in RIGHT:
        return "right"
    if d in MAINSTREAM:
        return "mainstream"
    return "other"


def score(df, text_col="title"):
    """Add one boolean column per frame, plus the loaded-share components."""
    out = df.copy()
    t = out[text_col].fillna("").str.lower()
    for name, pat in FRAMES.items():
        out[name] = t.str.contains(pat, regex=True, na=False)
    out["demsoc_phrase"] = t.str.contains(DEMSOC, regex=True, na=False)
    # A headline saying "democratic socialist" matches the loaded pattern via "socialist"; it should
    # not count as loaded unless it also carries an independently loaded term.
    independently_loaded = t.str.contains(
        r"\bradical|\bfar[\s-]left|\bhard[\s-]left|\bultra[\s-]left|\bextremis|\bextreme\b|\bmarxis|\bcommunis|\bleftis",
        regex=True, na=False)
    out["loaded_label"] = np.where(out.demsoc_phrase & ~independently_loaded, False, out.loaded_label)
    out["any_ideology"] = out.self_description | out.loaded_label
    out["outlet_class"] = out.domain.map(outlet_class)
    return out


def rates(scored, by):
    """Frame rates and loaded share for each group in `by`."""
    cols = list(FRAMES) + ["demsoc_phrase", "any_ideology"]
    g = scored.groupby(by)
    r = g[cols].mean()
    r["n_articles"] = g.size()
    lab = g[["loaded_label", "any_ideology"]].sum()
    r["loaded_share"] = (lab.loaded_label / lab.any_ideology.replace(0, np.nan))
    return r.reset_index()
