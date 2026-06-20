# Receipt — Carbon Footprint Tracker

A smart web application that tracks individual carbon footprints and consumer habits by scanning grocery/shopping receipts. Upload a photo of a receipt → AI extracts line items → each item gets scored for its CO2e lifecycle impact → results feed into a dashboard with challenges, streaks, badges, and weekly progress reports.

---

## 📋 Hackathon Evaluation Alignment

### 1. Chosen Vertical
* **Personal Sustainability & Consumer Impact Tracker**: Focuses on micro-level consumer habits by analyzing physical receipts to highlight the hidden carbon footprint of daily purchasing decisions.

### 2. Approach & Core Logic
* **Hybrid OCR Scanning Engine**: Uses the **Claude 3.5 Sonnet Vision API** to read receipt photos and extract line items.
* **Robust Mock Fallback Mode**: If the Anthropic API key is unconfigured or returns an authorization error (e.g. `401 invalid x-api-key`), the scanner logs a warning and falls back to a realistic mock grocery dataset. This keeps the application fully functional and testable without a paid Anthropic key.
* **Emissions Factor Mapping**: Items are classified into six categories (Produce, Grains, Dairy, Meat/Fish, Packaged/Drinks, and Household) using a custom substring-matching algorithm that favors trailing nouns (e.g. "almond milk" matches "milk" rather than "almonds" to capture the correct product type).
* **Streak & Milestone Calculation**: Tracks active consecutive scanning days (permitting a 1-day grace period to complete today's scans) and checks earned milestones (e.g. "Category Explorer" for scans spanning all 6 categories).

### 3. How the Solution Works
1. **API Scan (`/api/scan`)** — Receives uploaded receipt image and extracts items/estimated weights.
2. **Carbon Estimate** — Evaluates each item using lifecycle emissions coefficients.
3. **Gamification Processing** — Recalculates streak records, checks daily challenge status, and flags newly unlocked badges.
4. **Dashboard View (`/dashboard`)** — Aggregates stats, renders color-coded category breakdown tracks, and gives reduction recommendations.
5. **Weekly Summary (`/report/weekly`)** — Dynamically compiles a weekly progress summary designed with inline styles for email client compatibility.

### 4. Assumptions Made
* **Weight Estimation**: If the AI scanner cannot determine the quantity/weight of an item from the receipt, it defaults to a reasonable single-grocery item guess of `0.4 kg`.
* **Lifecycle Assessment Averages**: Emission factors (e.g. `60.0 kg CO2e` per kg of beef) represent average global farm-to-retail lifecycle greenhouse gas emissions based on statistical aggregations (like Poore & Nemecek 2018), intended to show relative categories for behavioral changes.
* **Storage Limit**: Local storage utilizes a lightweight JSON database file. The design allows replacing this layer with standard relational databases (SQLite/PostgreSQL) without modifying the web endpoints.

### 5. Testing & Code Quality
* A complete unit and endpoint test suite (`pytest`) is included inside `/tests` to validate:
  - Substring search classification and carbon math correctness.
  - Streak consecutive days math, daily challenge criteria, and badge thresholds.
  - Mock database load/save and Flask endpoint page loads / API scan uploads.
* Execute tests using:
  ```bash
  python -m pytest
  ```

### 6. Web Accessibility (WCAG AA Compliance)
* **Contrast Compliance**: Core colors shifted (e.g., `--gray` to `#706A5F` and `--terracotta` to `#B5521E`) to pass the WCAG AA minimum contrast ratio of `4.5:1` on light backgrounds.
* **Aria Landmarks & Labels**: Navigation blocks mapped with `aria-label="Primary Navigation"`, decorative icons hidden using `aria-hidden="true"`, and form controls linked with explicit descriptive labels (such as `visually-hidden` email tags).

---

## 🛠️ Stack & Setup

* **Backend**: Flask (Python 3.10+) & Gunicorn (production WSGI server)
* **Frontend**: Vanilla CSS & responsive JavaScript (no massive dependencies, optimized for fast loads)
* **Host Compatibility**: Fully configured for Render deployment using [`render.yaml`](file:///c:/Users/nithu/OneDrive/Desktop/carbon-tracker/render.yaml) blueprints.

### Local Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables. Copy the template `.env` configuration file:
   ```bash
   copy .env.example .env
   # On Linux/macOS: cp .env.example .env
   ```
   Open `.env` and fill in your SMTP email or Anthropic API credentials. If left blank, receipt scanning will gracefully run in Mock Fallback Mode.

3. Run the application:
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your web browser.
