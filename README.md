# Receipt — Carbon Footprint Tracker

Upload a photo of a grocery receipt → Claude reads the line items → each item
gets a CO2e estimate → results land in a dashboard with category breakdown,
daily challenges, streaks, badges, and a weekly progress report.

## Stack
Flask (Python) backend · server-rendered HTML/CSS/vanilla JS frontend ·
JSON-file storage (`data/db.json`, created automatically) · Claude vision API
for receipt OCR/extraction.

## Setup

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables. Copy the template configuration file:
   ```bash
   cp .env.example .env
   # On Windows: copy .env.example .env
   ```
   Open the `.env` file and fill in your API keys and/or SMTP settings.

3. Run the application:
   ```bash
   python app.py
   ```

Then open `http://localhost:5000`.

### Required: Anthropic API key
Receipt scanning calls Claude's vision API to read the photo and extract line items. Set `ANTHROPIC_API_KEY` in your `.env` file. Without it set, the scan endpoint returns a clear error explaining this rather than crashing.

### Optional: email sending for the weekly report
The `/report/weekly` page always renders the report in-browser. To actually *send* it by email, configure the following SMTP credentials in your `.env` file:

- `EMAIL_HOST`: SMTP host (e.g. `smtp.gmail.com`)
- `EMAIL_PORT`: SMTP port (e.g. `587`)
- `EMAIL_USER`: Your SMTP username or email address
- `EMAIL_PASSWORD`: Your SMTP password or App Password

Works with any standard SMTP provider (Gmail app password, SendGrid SMTP relay, Mailgun, etc). Without these set, the "Send Report" button returns a clear error telling you what to configure.


## How it works

1. **`/api/scan`** — accepts an uploaded image, sends it to Claude
   (`receipt_scanner.py`), gets back structured line items, scores each one
   for CO2e using a lookup table of emission factors (`carbon_data.py`), and
   saves the scan (`storage.py`).
2. **Gamification** (`gamification.py`) runs on every scan: checks if today's
   rotating daily challenge is satisfied, recalculates the current streak,
   and checks badge thresholds (first scan, streak lengths, challenges
   completed, total CO2e saved, category diversity).
3. **Dashboard** (`/dashboard`) — aggregates all scans into category totals,
   running stats, and a personalized reduction tip for whichever category
   dominates your footprint.
4. **Weekly report** (`report.py`) — builds a 7-day summary (CO2e total,
   streak, challenges completed, category breakdown, badges) as inline-styled
   HTML, viewable on `/report/weekly` and sendable via the email button.

## Notes on the carbon estimates
Emission factors in `carbon_data.py` are reasonable lifecycle-average
estimates (kg CO2e per kg of product), not laboratory-grade measurements —
good enough to show *relative* impact between food categories (red meat vs.
produce, for example) and motivate behavior change, not for scientific or
regulatory reporting. Item weights are estimated by Claude from the receipt
photo and default to 0.4kg when no quantity is visible.

## Swapping in a real database
Everything reads/writes through `storage.py`'s functions
(`add_scan`, `get_scans`, `mark_challenge_complete`, etc). To move off the
JSON file, reimplement those functions against a real database — the rest of
the app doesn't need to change.
