"""
Builds the weekly progress report: CO2 saved, streak status, challenges
completed, category breakdown for the last 7 days. Rendered as HTML
suitable for emailing (inline styles only — most email clients strip <style> blocks).

Actually sending email requires SMTP credentials or an email API key, which
this app does not have configured. send_weekly_email() is wired up and will
work the moment EMAIL_HOST / EMAIL_USER / EMAIL_PASSWORD env vars are set;
until then the /report/weekly route just renders the same content in-browser.
"""
import os
import smtplib
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import storage
import gamification
from carbon_data import get_category_color


def build_weekly_report_data() -> dict:
    today = date.today()
    week_ago = today - timedelta(days=6)

    all_scans = storage.get_scans()
    week_scans = [s for s in all_scans if week_ago.isoformat() <= s["scanned_at"][:10] <= today.isoformat()]

    total_co2 = round(sum(s["total_co2e_kg"] for s in week_scans), 2)

    category_totals = {}
    for s in week_scans:
        for item in s["items"]:
            category_totals[item["category"]] = round(
                category_totals.get(item["category"], 0) + item["co2e_kg"], 2
            )

    scan_dates = storage.get_scan_dates()
    current_streak = gamification.calculate_streak(scan_dates)

    completed = storage.get_completed_challenges()
    week_completed = [c for c in completed if week_ago.isoformat() <= c["date"] <= today.isoformat()]
    week_co2_saved = sum(
        next((ch["co2_saved_kg"] for ch in gamification.DAILY_CHALLENGES if ch["id"] == c["challenge_id"]), 0)
        for c in week_completed
    )

    earned_badges = storage.get_earned_badges()
    badge_details = [b for b in gamification.BADGES if b["id"] in earned_badges]

    # daily breakdown for the little 7-day bar strip
    daily_totals = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_total = sum(s["total_co2e_kg"] for s in all_scans if s["scanned_at"][:10] == d.isoformat())
        daily_totals.append({"date": d.strftime("%a"), "co2": round(day_total, 2)})

    return {
        "week_start": week_ago.strftime("%b %d"),
        "week_end": today.strftime("%b %d, %Y"),
        "total_co2_kg": total_co2,
        "scans_count": len(week_scans),
        "category_totals": category_totals,
        "current_streak": current_streak,
        "longest_streak": storage.load_db()["longest_streak"],
        "challenges_completed_count": len(week_completed),
        "co2_saved_this_week": round(week_co2_saved, 2),
        "total_co2_saved_alltime": storage.get_total_co2_saved(),
        "badges": badge_details,
        "daily_totals": daily_totals,
    }


def render_report_html(data: dict) -> str:
    """Inline-styled HTML, safe for both email clients and in-browser preview."""

    category_rows = "".join(
        f"""
        <tr>
          <td style="padding:6px 0; font-family:'Courier New',monospace; font-size:14px; color:#1C1B17;">
            <span style="display:inline-block;width:10px;height:10px;background:{get_category_color(cat)};border-radius:2px;margin-right:8px;"></span>
            {cat}
          </td>
          <td style="padding:6px 0; font-family:'Courier New',monospace; font-size:14px; color:#1C1B17; text-align:right;">
            {amt} kg CO2e
          </td>
        </tr>"""
        for cat, amt in sorted(data["category_totals"].items(), key=lambda x: -x[1])
    ) or "<tr><td style='padding:6px 0;color:#8B8578;font-family:Arial,sans-serif;'>No scans this week yet.</td></tr>"

    badge_html = "".join(
        f"""<span style="display:inline-block;background:#FAF7F0;border:1px solid #D4AF37;border-radius:16px;
            padding:4px 12px;margin:3px;font-family:Arial,sans-serif;font-size:12px;color:#1C1B17;">
            🏅 {b['title']}</span>"""
        for b in data["badges"]
    ) or "<span style='font-family:Arial,sans-serif;font-size:13px;color:#8B8578;'>No badges yet — scan a receipt to start earning them.</span>"

    bars = "".join(
        f"""<div style="display:inline-block; text-align:center; margin:0 6px; vertical-align:bottom;">
              <div style="background:#3D5A3D; width:24px; height:{max(4, int(d['co2']*8))}px; border-radius:3px 3px 0 0;"></div>
              <div style="font-family:Arial,sans-serif; font-size:11px; color:#8B8578; margin-top:4px;">{d['date']}</div>
            </div>"""
        for d in data["daily_totals"]
    )

    streak_flame = "🔥" * min(data["current_streak"], 7) if data["current_streak"] > 0 else "—"

    return f"""
<div style="max-width:600px;margin:0 auto;background:#FAF7F0;border:1px solid #E5E0D5;font-family:Arial,sans-serif;">
  <div style="background:#1C1B17;padding:24px 28px;">
    <p style="margin:0;color:#FAF7F0;font-family:'Courier New',monospace;font-size:12px;letter-spacing:2px;text-transform:uppercase;">Weekly Footprint Report</p>
    <p style="margin:6px 0 0;color:#8B8578;font-family:'Courier New',monospace;font-size:13px;">{data['week_start']} – {data['week_end']}</p>
  </div>

  <div style="padding:28px;">
    <table width="100%" style="margin-bottom:24px;">
      <tr>
        <td style="text-align:center;padding:12px;border-right:1px solid #E5E0D5;">
          <div style="font-family:'Courier New',monospace;font-size:28px;font-weight:bold;color:#1C1B17;">{data['total_co2_kg']}</div>
          <div style="font-family:Arial,sans-serif;font-size:12px;color:#8B8578;">kg CO2e this week</div>
        </td>
        <td style="text-align:center;padding:12px;border-right:1px solid #E5E0D5;">
          <div style="font-family:'Courier New',monospace;font-size:28px;font-weight:bold;color:#C4622D;">{streak_flame}</div>
          <div style="font-family:Arial,sans-serif;font-size:12px;color:#8B8578;">{data['current_streak']}-day streak</div>
        </td>
        <td style="text-align:center;padding:12px;">
          <div style="font-family:'Courier New',monospace;font-size:28px;font-weight:bold;color:#3D5A3D;">{data['co2_saved_this_week']}</div>
          <div style="font-family:Arial,sans-serif;font-size:12px;color:#8B8578;">kg CO2e saved</div>
        </td>
      </tr>
    </table>

    <p style="font-family:Arial,sans-serif;font-size:13px;color:#1C1B17;font-weight:bold;margin:0 0 10px;">Daily activity</p>
    <div style="text-align:center;margin-bottom:24px;">{bars}</div>

    <p style="font-family:Arial,sans-serif;font-size:13px;color:#1C1B17;font-weight:bold;margin:0 0 10px;">Category breakdown</p>
    <table width="100%" style="margin-bottom:24px;border-top:1px solid #E5E0D5;border-bottom:1px solid #E5E0D5;">
      {category_rows}
    </table>

    <p style="font-family:Arial,sans-serif;font-size:13px;color:#1C1B17;font-weight:bold;margin:0 0 10px;">Badges earned</p>
    <div style="margin-bottom:8px;">{badge_html}</div>

    <p style="font-family:Arial,sans-serif;font-size:11px;color:#8B8578;margin-top:28px;border-top:1px solid #E5E0D5;padding-top:14px;">
      {data['challenges_completed_count']} challenges completed this week · {data['total_co2_saved_alltime']} kg CO2e saved all-time
    </p>
  </div>
</div>
"""


def send_weekly_email(to_address: str) -> dict:
    """
    Sends the report via SMTP. Requires EMAIL_HOST, EMAIL_PORT, EMAIL_USER,
    EMAIL_PASSWORD env vars to be set — none are configured in this environment,
    so this will raise until the user supplies their own SMTP credentials
    (e.g. a Gmail app password, SendGrid SMTP relay, etc).
    """
    host = os.environ.get("EMAIL_HOST")
    port = int(os.environ.get("EMAIL_PORT", 587))
    user = os.environ.get("EMAIL_USER")
    password = os.environ.get("EMAIL_PASSWORD")

    if not all([host, user, password]):
        raise RuntimeError(
            "Email sending isn't configured yet. Set EMAIL_HOST, EMAIL_PORT, "
            "EMAIL_USER, and EMAIL_PASSWORD environment variables with your "
            "SMTP provider's details (e.g. Gmail, SendGrid, Mailgun) to enable this."
        )

    data = build_weekly_report_data()
    html = render_report_html(data)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your weekly carbon report — {data['week_start']} to {data['week_end']}"
    msg["From"] = user
    msg["To"] = to_address
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

    return {"sent_to": to_address, "subject": msg["Subject"]}
