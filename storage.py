"""
Lightweight JSON-file storage. Stands in for a real database — swap this
module for a SQLAlchemy model layer later without touching the routes much,
since everything goes through these functions.
"""
import json
import os
from datetime import date, datetime
from threading import Lock

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_FILE = os.path.join(DATA_DIR, "db.json")
_lock = Lock()
_cached_db = None

DEFAULT_DB = {
    "scans": [],            # list of scan dicts
    "earned_badges": [],    # list of badge ids
    "completed_challenges": [],  # list of {date, challenge_id}
    "total_co2_saved": 0.0,
    "longest_streak": 0,
}


def _ensure_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump(DEFAULT_DB, f, indent=2)


def load_db() -> dict:
    global _cached_db
    _ensure_db()
    with _lock:
        if _cached_db is None:
            with open(DB_FILE, "r") as f:
                _cached_db = json.load(f)
        return _cached_db


def save_db(db: dict):
    global _cached_db
    with _lock:
        with open(DB_FILE, "w") as f:
            json.dump(db, f, indent=2, default=str)
        _cached_db = db


def add_scan(scan: dict) -> dict:
    db = load_db()
    scan["id"] = len(db["scans"]) + 1
    scan["scanned_at"] = datetime.now().isoformat()
    db["scans"].append(scan)
    save_db(db)
    return scan


def get_scans() -> list:
    return load_db()["scans"]


def get_scans_for_date(d: date) -> list:
    iso = d.isoformat()
    return [s for s in get_scans() if s["scanned_at"][:10] == iso]


def get_scan_dates() -> list:
    """All unique dates (as date objects) on which at least one scan happened."""
    dates = {s["scanned_at"][:10] for s in get_scans()}
    return [date.fromisoformat(d) for d in dates]


def mark_challenge_complete(challenge_id: str, d: date, co2_saved: float):
    db = load_db()
    iso = d.isoformat()
    already = any(c["date"] == iso and c["challenge_id"] == challenge_id for c in db["completed_challenges"])
    if not already:
        db["completed_challenges"].append({"date": iso, "challenge_id": challenge_id})
        db["total_co2_saved"] = round(db["total_co2_saved"] + co2_saved, 2)
        save_db(db)
        return True
    return False


def get_completed_challenges() -> list:
    return load_db()["completed_challenges"]


def get_earned_badges() -> list:
    return load_db()["earned_badges"]


def add_earned_badge(badge_id: str):
    db = load_db()
    if badge_id not in db["earned_badges"]:
        db["earned_badges"].append(badge_id)
        save_db(db)


def update_longest_streak(streak: int):
    db = load_db()
    if streak > db["longest_streak"]:
        db["longest_streak"] = streak
        save_db(db)
    return db["longest_streak"]


def get_total_co2_saved() -> float:
    return load_db()["total_co2_saved"]


def reset_all():
    save_db(dict(DEFAULT_DB))
