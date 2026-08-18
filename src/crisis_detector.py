"""
Crisis detector: classifies a query as "standard" or "emergency".

Primary method: keyword-based rules (no external API needed).
Structured so a Claude Haiku classifier could be swapped in later
(see call_claude_haiku, currently unused) without changing the
calling code elsewhere in the pipeline.
"""

import re

# Words/phrases signaling an active, urgent, happening-now situation
EMERGENCY_SIGNALS = [
    "right now", "happening now", "breaking", "live", "urgent",
    "emergency", "evacuate", "evacuation", "warning", "alert",
    "just happened", "ongoing", "currently", "today", "this morning",
    "this hour", "immediate", "danger", "critical",
]

# Words/phrases signaling a retrospective, explanatory, non-urgent query
STANDARD_SIGNALS = [
    "history of", "in the past", "overview", "explain", "what is",
    "what are", "guide to", "background on", "years ago", "retrospective",
    "understanding", "how does", "how do", "study finds", "research shows",
]


def _contains_signal(text: str, signal: str) -> bool:
    """
    Word-boundary matching — avoids false positives like "alert"
    matching inside "ShakeAlert". Multi-word signals (e.g. "right now")
    still match as substrings, since word-boundary regex handles
    phrases fine when spaces are part of the pattern.
    """
    pattern = r'\b' + re.escape(signal) + r'\b'
    return bool(re.search(pattern, text))


def detect_urgency(query: str) -> str:
    """
    Returns "emergency" or "standard" based on keyword matching.
    Emergency signals take priority if both types are present,
    since missing a real emergency is worse than a false alarm.
    """
    q = query.lower()

    has_emergency = any(_contains_signal(q, signal) for signal in EMERGENCY_SIGNALS)
    has_standard = any(_contains_signal(q, signal) for signal in STANDARD_SIGNALS)

    if has_emergency:
        return "emergency"
    if has_standard:
        return "standard"

    return "standard"

def call_claude_haiku(query: str) -> str:
    """
    Placeholder for an LLM-based classifier. Not currently used —
    detect_urgency() (keyword-based) is the active path. Left here
    as documented future work: swap the call in main pipeline code
    from detect_urgency(query) to call_claude_haiku(query) once an
    API key with credits is available.
    """
    raise NotImplementedError(
        "Claude Haiku classification not enabled — using keyword "
        "fallback (detect_urgency) instead. See docstring."
    )


if __name__ == "__main__":
    test_queries = [
        # 5 emergency
        ("wildfire evacuation Napa right now", "emergency"),
        ("earthquake warning Japan happening now", "emergency"),
        ("breaking: hurricane making landfall", "emergency"),
        ("urgent flood alert Mississippi", "emergency"),
        ("live updates active shooter situation", "emergency"),
        # 5 standard
        ("history of earthquakes in Japan", "standard"),
        ("what is herd immunity", "standard"),
        ("overview of hurricane categories", "standard"),
        ("retrospective on 2020 wildfire season", "standard"),
        ("how does the ShakeAlert system work", "standard"),
    ]

    correct = 0
    for query, expected in test_queries:
        result = detect_urgency(query)
        status = "OK" if result == expected else "MISMATCH"
        if result == expected:
            correct += 1
        print(f"[{status}] '{query}' -> {result} (expected {expected})")

    print(f"\n{correct}/{len(test_queries)} correct")