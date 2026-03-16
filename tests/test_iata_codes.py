"""Tests for IATA delay code reference data."""
from aerops.data.iata_codes import (
    load_iata_codes,
    get_code_description,
    get_all_categories,
    map_bts_cause_to_iata,
    BTS_TO_IATA,
)


def test_load_all_codes():
    codes = load_iata_codes()
    assert len(codes) > 40  # We have ~65 codes
    assert all("code" in c for c in codes)
    assert all("category" in c for c in codes)
    assert all("description" in c for c in codes)


def test_code_descriptions():
    assert "weather" in get_code_description("71").lower()
    assert "ATC" in get_code_description("81") or "restriction" in get_code_description("81").lower()
    assert "aircraft" in get_code_description("93").lower() or "rotation" in get_code_description("93").lower()


def test_bts_to_iata_mapping_covers_all_causes():
    expected_causes = ["CarrierDelay", "WeatherDelay", "NASDelay",
                       "SecurityDelay", "LateAircraftDelay"]
    for cause in expected_causes:
        assert cause in BTS_TO_IATA
        code, category = map_bts_cause_to_iata(cause)
        assert code is not None
        assert category is not None


def test_get_all_categories():
    categories = get_all_categories()
    assert len(categories) >= 8
    assert "Weather" in categories
    assert "Technical" in categories
    assert "ATC/Airport" in categories


def test_unknown_code_returns_default():
    code, cat = map_bts_cause_to_iata("UnknownCause")
    assert code == "99"
    assert cat == "Miscellaneous"
