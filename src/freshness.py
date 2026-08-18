"""
Freshness scoring: e^(-age_in_days / 30)

A 0-day-old article scores 1.0 (maximally fresh).
As age increases, the score decays exponentially toward 0.
The constant 30 controls decay speed — roughly, an article
loses meaningful freshness over the course of ~30 days.
"""

import math
from datetime import date


def freshness_score(publish_date: str, today: date = None) -> float:
    """
    publish_date: ISO format string, e.g. "2026-08-13"
    today: optional override for testing; defaults to actual today
    Returns a float in (0, 1], where 1.0 = published today.
    """
    if today is None:
        today = date.today()

    pub = date.fromisoformat(publish_date)
    age_days = (today - pub).days

    if age_days < 0:
        age_days = 0  # guard against future-dated articles

    return math.exp(-age_days / 30)


if __name__ == "__main__":
    # Hand-computed sanity checks (per your plan: verify on paper)
    test_today = date(2026, 8, 13)

    tests = [
        ("2026-08-13", 0),   # published today -> age 0
        ("2026-07-14", 30),  # 30 days old
        ("2026-05-15", 90),  # 90 days old
    ]

    for pub_date, expected_age in tests:
        score = freshness_score(pub_date, today=test_today)
        expected_score = math.exp(-expected_age / 30)
        print(f"publish_date={pub_date} | age={expected_age}d | "
              f"score={score:.4f} | expected={expected_score:.4f}")