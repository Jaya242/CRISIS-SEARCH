"""
Per-publisher trust prior, blended with the DistilBERT classifier's output.

Why this exists:
  The classifier scores article text. LIAR2 (its training data) is short
  political claims by politicians, so on news headlines the model is out of
  distribution and its output clusters low — NPR scoring 0.01 while BuzzFeed
  scores 0.04 is exactly the kind of ranking a human newsroom would never
  make. A hand-curated per-publisher prior gives us the source-level signal
  the classifier can't recover from text alone.

Blend formula (see live_pipeline.py):
  final_credibility = 0.6 * publisher_prior + 0.4 * classifier_score

Values are informed by widely-cited factuality/reliability assessments
(Ad Fontes Media, Media Bias/Fact Check, NewsGuard) and adjusted for this
demo's focus on news reporting rather than opinion columns.

This table is a hypothesis, not a fitted result. See README's Limitations
section for the honest caveat.
"""

TRUST_SCORES = {
    # Wire services and government science — top tier
    "reuters": 0.90,
    "associated press": 0.90,
    "ap news": 0.90,
    "afp": 0.85,
    "usgs": 0.95,
    "noaa": 0.95,
    "national weather service": 0.95,
    "cdc": 0.90,
    "who": 0.90,
    "nasa": 0.95,

    # Major mainstream (US / UK / financial)
    "bbc": 0.85,
    "bbc news": 0.85,
    "npr": 0.85,
    "pbs newshour": 0.85,
    "the new york times": 0.85,
    "new york times": 0.85,
    "the washington post": 0.85,
    "washington post": 0.85,
    "the wall street journal": 0.85,
    "wall street journal": 0.85,
    "bloomberg": 0.85,
    "the economist": 0.85,
    "financial times": 0.85,
    "the guardian": 0.80,
    "the atlantic": 0.80,
    "propublica": 0.85,

    # Broadcast / cable mainstream
    "abc news": 0.75,
    "cbs news": 0.75,
    "nbc news": 0.75,
    "cnn": 0.70,
    "usa today": 0.70,

    # Local network affiliates (mostly pass-through of AP + local reporting)
    "abc7 bay area": 0.70,
    "abc7": 0.70,
    "abc10": 0.70,
    "kcra": 0.70,
    "kcra 3": 0.70,
    "sfgate": 0.70,
    "san francisco chronicle": 0.75,
    "los angeles times": 0.80,
    "chicago tribune": 0.75,

    # Tech / science / academic
    "cnet": 0.70,
    "the verge": 0.75,
    "ars technica": 0.80,
    "wired": 0.75,
    "techcrunch": 0.70,
    "mit news": 0.80,
    "science": 0.90,
    "nature": 0.90,
    "scientific american": 0.85,

    # International
    "al jazeera": 0.70,
    "deutsche welle": 0.80,
    "dw news": 0.80,
    "france 24": 0.75,

    # State media — lower for political topics; keep separate tier
    "xinhua": 0.35,
    "cgtn": 0.35,
    "rt": 0.25,
    "sputnik": 0.25,
    "press tv": 0.25,

    # US partisan / opinion-heavy
    "fox news": 0.55,
    "new york post": 0.55,
    "the daily wire": 0.45,
    "breitbart": 0.30,
    "the daily caller": 0.40,
    "vox": 0.70,
    "the intercept": 0.70,
    "slate": 0.65,

    # Aggregators / mixed factuality
    "buzzfeed news": 0.65,
    "buzzfeed": 0.45,
    "vice": 0.60,
    "the daily beast": 0.60,
    "huffpost": 0.60,
    "huffington post": 0.60,
    "yahoo news": 0.65,
    "the week": 0.65,
    "newsweek": 0.60,

    # Independent investigative
    "investigate europe": 0.75,
    "bellingcat": 0.85,

    # Universities and research institutions
    "la trobe university": 0.75,
    "harvard": 0.80,
    "stanford": 0.80,
    "mit": 0.80,

    # Tabloids — bottom tier
    "the sun": 0.30,
    "the daily mail": 0.40,
    "the mirror": 0.40,
    "national enquirer": 0.15,
}

# Fallback for publishers not in the table.
# 0.55 is deliberately a hair above neutral — most Google News RSS results
# come from mainstream outlets even if the exact name isn't listed, so a
# very low default would be more wrong than slightly-above-neutral.
DEFAULT_TRUST = 0.55

# Blend weights for the final credibility score.
# See live_pipeline.py — final_C = PRIOR_WEIGHT * publisher + CLASSIFIER_WEIGHT * text
PRIOR_WEIGHT = 0.6
CLASSIFIER_WEIGHT = 0.4


def get_publisher_trust(publisher_name: str) -> float:
    """
    Look up a publisher's trust score, falling back to DEFAULT_TRUST.

    Matching is case-insensitive and forgiving of common name variants
    (e.g. "BBC" matches "BBC News", "NYT" prefix falls through to default).
    """
    if not publisher_name:
        return DEFAULT_TRUST
    key = publisher_name.strip().lower()
    if key in TRUST_SCORES:
        return TRUST_SCORES[key]
    # Substring match for e.g. "The New York Times (via Yahoo)" or
    # "ABC7 Bay Area - KGO" — take the highest-scoring partial match so
    # a co-branded source doesn't get demoted by a lower-tier partner.
    best = None
    for name, score in TRUST_SCORES.items():
        if name in key or key in name:
            if best is None or score > best:
                best = score
    return best if best is not None else DEFAULT_TRUST


if __name__ == "__main__":
    # Quick sanity checks against the audit's real observed sources
    for pub in [
        "NPR", "BBC News", "Reuters", "BuzzFeed News", "ABC7 Bay Area",
        "San Francisco Chronicle", "CNET", "Xinhua", "La Trobe University",
        "Some Blog That Doesnt Exist",
    ]:
        print(f"{pub:35s} -> {get_publisher_trust(pub):.2f}")
