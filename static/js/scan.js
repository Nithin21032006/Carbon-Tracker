const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const chooseBtn = document.getElementById('chooseBtn');
const previewImg = document.getElementById('previewImg');
const scanStatus = document.getElementById('scanStatus');
const receiptResult = document.getElementById('receiptResult');
const tipResult = document.getElementById('tipResult');
const toastStack = document.getElementById('toastStack');

const ICONS = {
  leaf: '🌿', sprout: '🌱', carrot: '🥕', flame: '🔥', receipt: '🧾',
  trophy: '🏆', target: '🎯', medal: '🏅', feather: '🪶', globe: '🌍', compass: '🧭'
};

chooseBtn.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('click', (e) => { if (e.target === dropzone) fileInput.click(); });

['dragenter', 'dragover'].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(evt =>
  dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); })
);
dropzone.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewImg.style.display = 'block';
  };
  reader.readAsDataURL(file);
  uploadReceipt(file);
}

async function uploadReceipt(file) {
  receiptResult.innerHTML = '';
  tipResult.innerHTML = '';
  scanStatus.style.display = 'block';
  scanStatus.className = 'scan-status';
  scanStatus.innerHTML = '<span class="spinner"></span>Reading your receipt…';

  const formData = new FormData();
  formData.append('receipt', file);

  try {
    const res = await fetch('/api/scan', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) {
      scanStatus.className = 'scan-status error';
      scanStatus.textContent = data.error || 'Something went wrong reading that receipt.';
      return;
    }

    scanStatus.style.display = 'none';
    renderReceipt(data.scan);
    renderTip(data.tip);
    showGameToasts(data);
  } catch (err) {
    scanStatus.className = 'scan-status error';
    scanStatus.textContent = 'Could not reach the server. Try again.';
  }
}

function renderReceipt(scan) {
  const date = new Date(scan.scanned_at);
  const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });

  const lines = scan.items.map(item => `
    <div class="receipt-line">
      <span class="item-name">
        ${escapeHtml(item.name)}
        <span class="item-cat"><span class="cat-dot" style="background:${item.color}"></span>${item.category}</span>
      </span>
      <span class="item-co2">${item.co2e_kg.toFixed(2)} kg</span>
    </div>
  `).join('');

  receiptResult.innerHTML = `
    <div class="receipt-card">
      <div class="receipt-inner">
        <div class="receipt-head">
          <div class="store">CARBON RECEIPT</div>
          <div class="meta">${dateStr} · ${timeStr}</div>
        </div>
        ${lines}
        <div class="receipt-total">
          <span class="total-label">TOTAL CO2e</span>
          <span class="total-value">${scan.total_co2e_kg.toFixed(2)} kg</span>
        </div>
      </div>
    </div>
  `;
}

function renderTip(tip) {
  if (!tip) return;
  tipResult.innerHTML = `
    <div class="tip-card">
      <span class="tip-icon">💡</span>
      <div>
        <span class="tip-cat">${escapeHtml(tip.category)}</span>
        ${escapeHtml(tip.tip)}
      </div>
    </div>
  `;
}

function showGameToasts(data) {
  const toasts = [];

  if (data.challenge && data.challenge.newly_completed) {
    toasts.push({
      icon: ICONS[data.challenge.icon] || '🎯',
      title: 'Challenge complete',
      sub: data.challenge.title
    });
  }

  if (data.new_badges && data.new_badges.length) {
    data.new_badges.forEach(b => {
      toasts.push({
        icon: ICONS[b.icon] || '🏅',
        title: 'Badge earned',
        sub: b.title
      });
    });
  }

  if (data.streak >= 2) {
    toasts.push({
      icon: '🔥',
      title: `${data.streak}-day streak`,
      sub: 'Keep it going tomorrow'
    });
  }

  toasts.forEach((t, i) => {
    setTimeout(() => spawnToast(t), i * 300);
  });
}

function spawnToast({ icon, title, sub }) {
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div><strong>${escapeHtml(title)}</strong><span class="sub">${escapeHtml(sub)}</span></div>
  `;
  toastStack.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
