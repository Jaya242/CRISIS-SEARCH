from src.ranker import WEIGHT_PROFILES


def test_weight_profiles_exist():
    assert "standard" in WEIGHT_PROFILES
    assert "emergency" in WEIGHT_PROFILES


def test_weight_profiles_have_all_signals():
    for mode, weights in WEIGHT_PROFILES.items():
        assert "w_r" in weights
        assert "w_c" in weights
        assert "w_f" in weights


def test_standard_favors_relevance_over_emergency():
    # standard mode's relevance weight should be higher than emergency's
    assert WEIGHT_PROFILES["standard"]["w_r"] > WEIGHT_PROFILES["emergency"]["w_r"]


def test_emergency_favors_freshness_and_credibility_over_standard():
    emergency = WEIGHT_PROFILES["emergency"]
    standard = WEIGHT_PROFILES["standard"]
    assert emergency["w_c"] > standard["w_c"]
    assert emergency["w_f"] > standard["w_f"]