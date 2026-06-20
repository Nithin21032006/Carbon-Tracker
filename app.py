import os
from datetime import date

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

import storage
import gamification
import report
from carbon_data import estimate_item_co2, get_top_tip
from receipt_scanner import extract_items_from_receipt

app = Flask(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_DIR, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------- pages --

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/challenges")
def challenges_page():
    return render_template("challenges.html")


@app.route("/report/weekly")
def weekly_report_page():
    data = report.build_weekly_report_data()
    html_report = report.render_report_html(data)
    return render_template("report.html", report_html=html_report, data=data)


# ------------------------------------------------------------- api: scan --

@app.route("/api/scan", methods=["POST"])
def api_scan():
    if "receipt" not in request.files:
        return jsonify({"error": "No file uploaded. Choose a receipt image first."}), 400

    file = request.files["receipt"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use JPG, PNG, or WEBP."}), 400

    filename = secure_filename(file.filename)
    unique_name = f"{date.today().isoformat()}_{len(storage.get_scans()) + 1}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, unique_name)
    file.save(save_path)

    try:
        raw_items = extract_items_from_receipt(save_path)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502

    if not raw_items:
        return jsonify({"error": "Couldn't find any line items on that receipt. Try a clearer photo."}), 422

    scored_items = []
    for raw in raw_items:
        scored = estimate_item_co2(raw["name"], raw["estimated_weight_kg"])
        scored["name"] = raw["name"]
        scored_items.append(scored)

    total_co2 = round(sum(i["co2e_kg"] for i in scored_items), 2)

    scan = {
        "filename": unique_name,
        "items": scored_items,
        "total_co2e_kg": total_co2,
    }
    saved_scan = storage.add_scan(scan)

    # ---- gamification side-effects ----
    today = date.today()
    todays_challenge = gamification.get_challenge_for_date(today)
    today_scans = storage.get_scans_for_date(today)
    challenge_completed_now = gamification.evaluate_challenges(todays_challenge, today_scans)

    newly_completed = False
    if challenge_completed_now:
        newly_completed = storage.mark_challenge_complete(
            todays_challenge["id"], today, todays_challenge["co2_saved_kg"]
        )

    scan_dates = storage.get_scan_dates()
    current_streak = gamification.calculate_streak(scan_dates)
    longest_streak = storage.update_longest_streak(current_streak)

    db = storage.load_db()
    low_carbon_scans = sum(1 for s in db["scans"] if s["total_co2e_kg"] < 3.0)
    categories_seen = {item["category"] for s in db["scans"] for item in s["items"]}

    stats = {
        "total_scans": len(db["scans"]),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "challenges_completed": len(db["completed_challenges"]),
        "total_co2_saved": db["total_co2_saved"],
        "low_carbon_scans": low_carbon_scans,
        "categories_seen": categories_seen,
    }
    earned_ids = set(storage.get_earned_badges())
    new_badges = gamification.check_new_badges(stats, earned_ids)
    for b in new_badges:
        storage.add_earned_badge(b["id"])

    category_totals = {}
    for item in scored_items:
        category_totals[item["category"]] = round(category_totals.get(item["category"], 0) + item["co2e_kg"], 2)
    tip = get_top_tip(category_totals)

    return jsonify({
        "scan": saved_scan,
        "category_totals": category_totals,
        "tip": tip,
        "streak": current_streak,
        "challenge": {
            **todays_challenge,
            "completed": challenge_completed_now,
            "newly_completed": newly_completed,
        },
        "new_badges": new_badges,
    })


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# --------------------------------------------------------- api: dashboard --

@app.route("/api/dashboard")
def api_dashboard():
    db = storage.load_db()
    scans = db["scans"]

    category_totals = {}
    for s in scans:
        for item in s["items"]:
            category_totals[item["category"]] = round(category_totals.get(item["category"], 0) + item["co2e_kg"], 2)

    total_co2 = round(sum(s["total_co2e_kg"] for s in scans), 2)
    scan_dates = storage.get_scan_dates()
    current_streak = gamification.calculate_streak(scan_dates)

    tip = get_top_tip(category_totals)

    return jsonify({
        "scans": list(reversed(scans))[:20],
        "category_totals": category_totals,
        "total_co2e_kg": total_co2,
        "total_scans": len(scans),
        "current_streak": current_streak,
        "longest_streak": db["longest_streak"],
        "total_co2_saved": db["total_co2_saved"],
        "tip": tip,
        "earned_badges": db["earned_badges"],
    })


# -------------------------------------------------------- api: challenges --

@app.route("/api/challenges/today")
def api_challenge_today():
    today = date.today()
    challenge = gamification.get_challenge_for_date(today)
    today_scans = storage.get_scans_for_date(today)
    completed = gamification.evaluate_challenges(challenge, today_scans)

    completed_list = storage.get_completed_challenges()
    already_logged = any(c["date"] == today.isoformat() and c["challenge_id"] == challenge["id"] for c in completed_list)

    return jsonify({**challenge, "completed": completed or already_logged})


@app.route("/api/badges")
def api_badges():
    earned = set(storage.get_earned_badges())
    all_badges = [
        {**b, "earned": b["id"] in earned}
        for b in gamification.BADGES
    ]
    return jsonify({"badges": all_badges, "earned_count": len(earned), "total_count": len(gamification.BADGES)})


# ----------------------------------------------------------- api: report --

@app.route("/api/report/weekly")
def api_weekly_report():
    return jsonify(report.build_weekly_report_data())


@app.route("/api/report/send", methods=["POST"])
def api_send_report():
    email = request.json.get("email") if request.is_json else None
    if not email:
        return jsonify({"error": "Provide an email address."}), 400
    try:
        result = report.send_weekly_email(email)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    return jsonify(result)


# ------------------------------------------------------------- api: misc --

@app.route("/api/reset", methods=["POST"])
def api_reset():
    storage.reset_all()
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
