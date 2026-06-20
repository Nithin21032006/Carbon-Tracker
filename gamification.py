"""
Gamification engine: daily challenges, badges, streaks.
Pure functions operating on the scan-history data structure stored in storage.py.
"""
from datetime import date, datetime, timedelta

# ---- Daily challenge pool ----------------------------------------------
# Each challenge has a check function name (resolved in evaluate_challenges)
# and a CO2-savings value awarded on completion, used in the weekly report.
DAILY_CHALLENGES = [
    {
        "id": "low_carbon_day",
        "title": "Low-Carbon Day",
        "description": "Keep today's scanned total under 3 kg CO2e.",
        "icon": "leaf",
        "co2_saved_kg": 2.0,
    },
    {
        "id": "no_red_meat",
        "title": "Meat-Free Receipt",
        "description": "Scan a receipt with zero items from Meat & Fish.",
        "icon": "sprout",
        "co2_saved_kg": 3.5,
    },
    {
        "id": "produce_forward",
        "title": "Produce Forward",
        "description": "Make Produce your largest category on a scanned receipt.",
        "icon": "carrot",
        "co2_saved_kg": 1.5,
    },
    {
        "id": "scan_streak",
        "title": "Keep the Streak",
        "description": "Scan at least one receipt today.",
        "icon": "flame",
        "co2_saved_kg": 0.5,
    },
]


def get_challenge_for_date(d: date) -> dict:
    """Deterministic 'daily' challenge so it's stable within a day, rotates by date."""
    idx = d.toordinal() % len(DAILY_CHALLENGES)
    return DAILY_CHALLENGES[idx]


def evaluate_challenges(challenge: dict, day_scans: list) -> bool:
    """Check whether a given day's scans satisfy a challenge's condition."""
    if not day_scans:
        return False

    cid = challenge["id"]
    if cid == "scan_streak":
        return True  # any scan that day satisfies it

    if cid == "low_carbon_day":
        total = sum(s["total_co2e_kg"] for s in day_scans)
        return total < 3.0

    if cid == "no_red_meat":
        return any(
            not any(item["category"] == "Meat & Fish" for item in s["items"])
            for s in day_scans
        )

    if cid == "produce_forward":
        for s in day_scans:
            cat_totals = {}
            for item in s["items"]:
                cat_totals[item["category"]] = cat_totals.get(item["category"], 0) + item["co2e_kg"]
            if cat_totals and max(cat_totals, key=cat_totals.get) == "Produce":
                return True
        return False

    return False


# ---- Badges --------------------------------------------------------------
BADGES = [
    {"id": "first_scan", "title": "First Receipt", "description": "Scanned your first receipt.", "icon": "receipt"},
    {"id": "streak_3", "title": "3-Day Streak", "description": "Scanned receipts 3 days in a row.", "icon": "flame"},
    {"id": "streak_7", "title": "Week Warrior", "description": "Scanned receipts 7 days in a row.", "icon": "flame"},
    {"id": "streak_30", "title": "Habit Formed", "description": "Scanned receipts 30 days in a row.", "icon": "trophy"},
    {"id": "challenges_5", "title": "Challenger", "description": "Completed 5 daily challenges.", "icon": "target"},
    {"id": "challenges_20", "title": "Challenge Master", "description": "Completed 20 daily challenges.", "icon": "medal"},
    {"id": "low_carbon_10", "title": "Featherweight", "description": "10 receipts scanned under 3 kg CO2e.", "icon": "feather"},
    {"id": "saved_50kg", "title": "50kg Saved", "description": "Saved 50kg CO2e total through challenges.", "icon": "globe"},
    {"id": "saved_200kg", "title": "200kg Club", "description": "Saved 200kg CO2e total through challenges.", "icon": "globe"},
    {"id": "category_explorer", "title": "Category Explorer", "description": "Scanned items from all 6 categories.", "icon": "compass"},
]


def calculate_streak(scan_dates: list) -> int:
    """
    scan_dates: list of date objects (one per day that has at least one scan),
    already deduplicated. Returns current consecutive-day streak ending today
    or yesterday (so a streak isn't lost just because today hasn't been scanned yet).
    """
    if not scan_dates:
        return 0
    unique_days = sorted(set(scan_dates), reverse=True)
    today = date.today()

    # streak must include today or yesterday to still be "current"
    if unique_days[0] not in (today, today - timedelta(days=1)):
        return 0

    streak = 1
    for i in range(len(unique_days) - 1):
        if (unique_days[i] - unique_days[i + 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def check_new_badges(stats: dict, earned_badge_ids: set) -> list:
    """
    stats: dict with keys total_scans, current_streak, longest_streak,
           challenges_completed, total_co2_saved, categories_seen (set)
    Returns list of newly-earned badge dicts (not already in earned_badge_ids).
    """
    newly_earned = []

    def award(bid):
        if bid not in earned_badge_ids:
            badge = next(b for b in BADGES if b["id"] == bid)
            newly_earned.append(badge)
            earned_badge_ids.add(bid)

    if stats["total_scans"] >= 1:
        award("first_scan")
    if stats["longest_streak"] >= 3:
        award("streak_3")
    if stats["longest_streak"] >= 7:
        award("streak_7")
    if stats["longest_streak"] >= 30:
        award("streak_30")
    if stats["challenges_completed"] >= 5:
        award("challenges_5")
    if stats["challenges_completed"] >= 20:
        award("challenges_20")
    if stats.get("low_carbon_scans", 0) >= 10:
        award("low_carbon_10")
    if stats["total_co2_saved"] >= 50:
        award("saved_50kg")
    if stats["total_co2_saved"] >= 200:
        award("saved_200kg")
    if len(stats.get("categories_seen", set())) >= 6:
        award("category_explorer")

    return newly_earned
