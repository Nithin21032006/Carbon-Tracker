import os
import json
import tempfile
from datetime import date, timedelta
import pytest

import carbon_data
import gamification
import storage

# =====================================================================
# Carbon Data Scoring tests
# =====================================================================

def test_classify_item():
    # Exact match
    key, factor = carbon_data.classify_item("beef")
    assert key == "beef"
    assert factor == 60.0

    # Substring match with clean-up
    key, factor = carbon_data.classify_item("  Organic Milk  ")
    assert key == "milk"
    assert factor == 3.0

    # Tie-breaking matching behavior (longest key / trailing noun preference)
    # "Almond Milk" has "milk" and "almonds" in keys.
    # The classification should map correctly based on latest/longest substring match
    key, factor = carbon_data.classify_item("almond milk")
    assert key == "milk"
    assert factor == 3.0

    # Fallback to other
    key, factor = carbon_data.classify_item("windex glass cleaner")
    assert key == "other"
    assert factor == 1.5


def test_estimate_item_co2():
    res = carbon_data.estimate_item_co2("Fresh Spinach Bunch", 0.5)
    assert res["matched_key"] == "spinach"
    assert res["category"] == "Produce"
    assert res["factor_per_kg"] == 0.5
    assert res["estimated_weight_kg"] == 0.5
    assert res["co2e_kg"] == 0.25  # 0.5 * 0.5


# =====================================================================
# Gamification Engine tests
# =====================================================================

def test_calculate_streak():
    # Empty case
    assert gamification.calculate_streak([]) == 0

    # Single date (today)
    today = date.today()
    assert gamification.calculate_streak([today]) == 1

    # Single date (yesterday)
    yesterday = today - timedelta(days=1)
    assert gamification.calculate_streak([yesterday]) == 1

    # Broken streak (last scan 3 days ago)
    long_ago = today - timedelta(days=3)
    assert gamification.calculate_streak([long_ago]) == 0

    # Multiple days streak
    two_days_ago = today - timedelta(days=2)
    assert gamification.calculate_streak([today, yesterday, two_days_ago]) == 3


def test_evaluate_challenges():
    # Mock daily scans
    scans_low_carbon = [
        {"total_co2e_kg": 1.2, "items": [{"category": "Produce", "co2e_kg": 1.2}]}
    ]
    scans_high_carbon = [
        {"total_co2e_kg": 12.5, "items": [{"category": "Meat & Fish", "co2e_kg": 12.5}]}
    ]

    # Test "scan_streak" challenge
    ch_streak = {"id": "scan_streak", "co2_saved_kg": 0.5}
    assert gamification.evaluate_challenges(ch_streak, scans_low_carbon) is True
    assert gamification.evaluate_challenges(ch_streak, []) is False

    # Test "low_carbon_day" challenge (under 3.0 kg)
    ch_low_co2 = {"id": "low_carbon_day", "co2_saved_kg": 2.0}
    assert gamification.evaluate_challenges(ch_low_co2, scans_low_carbon) is True
    assert gamification.evaluate_challenges(ch_low_co2, scans_high_carbon) is False

    # Test "no_red_meat" challenge (no items in "Meat & Fish")
    ch_no_meat = {"id": "no_red_meat", "co2_saved_kg": 3.5}
    assert gamification.evaluate_challenges(ch_no_meat, scans_low_carbon) is True
    assert gamification.evaluate_challenges(ch_no_meat, scans_high_carbon) is False


def test_check_new_badges():
    # Scenarios for badges check
    earned = set()
    stats = {
        "total_scans": 1,
        "current_streak": 1,
        "longest_streak": 1,
        "challenges_completed": 0,
        "total_co2_saved": 0.0,
        "low_carbon_scans": 1,
        "categories_seen": {"Produce"}
    }
    
    # First scan badge should trigger
    new_badges = gamification.check_new_badges(stats, earned)
    assert len(new_badges) == 1
    assert new_badges[0]["id"] == "first_scan"
    assert "first_scan" in earned

    # Consecutive milestone checks
    stats["longest_streak"] = 3
    new_badges = gamification.check_new_badges(stats, earned)
    assert len(new_badges) == 1
    assert new_badges[0]["id"] == "streak_3"


# =====================================================================
# Database Storage tests
# =====================================================================

def test_storage_db():
    # Setup temporary directory and database file to isolate tests
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_file = os.path.join(tmpdir, "test_db.json")
        storage.DB_FILE = test_db_file
        storage.DATA_DIR = tmpdir
        storage._cached_db = None

        # Verifies database initializes with template dictionary defaults
        db = storage.load_db()
        assert os.path.exists(test_db_file)
        assert db["scans"] == []
        assert db["total_co2_saved"] == 0.0

        # Verify writing/saving works
        db["total_co2_saved"] = 5.5
        storage.save_db(db)

        reloaded = storage.load_db()
        assert reloaded["total_co2_saved"] == 5.5
