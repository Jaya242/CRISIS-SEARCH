import math
from datetime import date
from src.freshness import freshness_score


def test_freshness_zero_days():
    score = freshness_score("2026-08-13", today=date(2026, 8, 13))
    assert math.isclose(score, 1.0, rel_tol=1e-6)


def test_freshness_thirty_days():
    score = freshness_score("2026-07-14", today=date(2026, 8, 13))
    assert math.isclose(score, math.exp(-1), rel_tol=1e-6)


def test_freshness_ninety_days():
    score = freshness_score("2026-05-15", today=date(2026, 8, 13))
    assert math.isclose(score, math.exp(-3), rel_tol=1e-6)