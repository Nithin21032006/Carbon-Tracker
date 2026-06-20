const statRow = document.getElementById('statRow');
const categoryBreakdown = document.getElementById('categoryBreakdown');
const scanList = document.getElementById('scanList');
const tipSlot = document.getElementById('tipSlot');

const CATEGORY_ORDER = ['Meat & Fish', 'Dairy & Eggs', 'Packaged & Drinks', 'Grains & Staples', 'Produce', 'Household', 'Other'];

async function loadDashboard() {
  try {
    const res = await fetch('/api/dashboard');
    const data = await res.json();
    renderStats(data);
    renderCategories(data.category_totals);
    renderScanList(data.scans);
    renderTip(data.tip);
  } catch (err) {
    scanList.innerHTML = `<div class="empty-state">Couldn't load dashboard data.</div>`;
  }
}

function renderStats(data) {
  statRow.innerHTML = `
    <div class="stat-box">
      <div class="stat-value">${data.total_co2e_kg.toFixed(1)}</div>
      <div class="stat-label">Total kg CO2e · ${data.total_scans} scans</div>
    </div>
    <div class="stat-box streak">
      <div class="stat-value">${data.current_streak}</div>
      <div class="stat-label">Day streak · best ${data.longest_streak}</div>
    </div>
    <div class="stat-box saved">
      <div class="stat-value">${data.total_co2_saved.toFixed(1)}</div>
      <div class="stat-label">kg CO2e saved via challenges</div>
    </div>
  `;
}

function renderTip(tip) {
  if (!tip) return;
  tipSlot.innerHTML = `
    <div class="tip-card" style="max-width:none;">
      <span class="tip-icon">💡</span>
      <div>
        <span class="tip-cat">${escapeHtml(tip.category)}</span>
        ${escapeHtml(tip.tip)}
      </div>
    </div>
  `;
}

const CATEGORY_COLORS = {
  'Meat & Fish': '#C4622D', 'Dairy & Eggs': '#D4AF37', 'Grains & Staples': '#8B8578',
  'Produce': '#3D5A3D', 'Packaged & Drinks': '#6B4C8A', 'Household': '#4A6B8A', 'Other': '#8B8578'
};

function renderCategories(totals) {
  const entries = Object.entries(totals);
  if (!entries.length) {
    categoryBreakdown.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">🧾</span>
        No scans yet. Upload a receipt to see your breakdown.
      </div>`;
    return;
  }
  const max = Math.max(...entries.map(([, v]) => v));
  entries.sort((a, b) => b[1] - a[1]);

  categoryBreakdown.innerHTML = entries.map(([cat, val]) => {
    const color = CATEGORY_COLORS[cat] || '#8B8578';
    const pct = max > 0 ? (val / max) * 100 : 0;
    return `
      <div class="cat-bar-row">
        <div class="cat-bar-label">
          <span class="name"><span class="cat-dot" style="background:${color}"></span>${cat}</span>
          <span class="value">${val.toFixed(2)} kg</span>
        </div>
        <div class="cat-bar-track">
          <div class="cat-bar-fill" style="width:${pct}%; background:${color};"></div>
        </div>
      </div>
    `;
  }).join('');
}

function renderScanList(scans) {
  if (!scans.length) {
    scanList.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon">📭</span>
        No receipts scanned yet.
      </div>`;
    return;
  }
  scanList.innerHTML = scans.map(scan => {
    const date = new Date(scan.scanned_at);
    const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    return `
      <div class="scan-row">
        <div>
          <div>${scan.items.length} item${scan.items.length === 1 ? '' : 's'}</div>
          <div class="scan-date">${dateStr} · ${timeStr}</div>
        </div>
        <div class="scan-co2">${scan.total_co2e_kg.toFixed(2)} kg</div>
      </div>
    `;
  }).join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

loadDashboard();
