const challengeHero = document.getElementById('challengeHero');
const badgeGrid = document.getElementById('badgeGrid');
const badgeProgress = document.getElementById('badgeProgress');

const ICONS = {
  leaf: '🌿', sprout: '🌱', carrot: '🥕', flame: '🔥', receipt: '🧾',
  trophy: '🏆', target: '🎯', medal: '🏅', feather: '🪶', globe: '🌍', compass: '🧭'
};

async function loadChallenge() {
  try {
    const res = await fetch('/api/challenges/today');
    const c = await res.json();
    challengeHero.innerHTML = `
      <div class="eyebrow">Today's Challenge</div>
      <h2>${ICONS[c.icon] || '🎯'} ${escapeHtml(c.title)}</h2>
      <p>${escapeHtml(c.description)}</p>
      <span class="challenge-status ${c.completed ? 'done' : 'pending'}">
        ${c.completed ? '✓ Completed today' : `Scan a receipt to complete · saves ${c.co2_saved_kg} kg CO2e`}
      </span>
    `;
  } catch (err) {
    challengeHero.innerHTML = `<div class="eyebrow">Today's Challenge</div><h2>Couldn't load challenge</h2>`;
  }
}

async function loadBadges() {
  try {
    const res = await fetch('/api/badges');
    const data = await res.json();
    badgeProgress.textContent = `${data.earned_count} / ${data.total_count} earned`;
    badgeGrid.innerHTML = data.badges.map(b => `
      <div class="badge-tile ${b.earned ? 'earned' : 'locked'}">
        <span class="badge-icon">${ICONS[b.icon] || '🏅'}</span>
        <div class="badge-title">${escapeHtml(b.title)}</div>
        <div class="badge-desc">${escapeHtml(b.description)}</div>
      </div>
    `).join('');
  } catch (err) {
    badgeGrid.innerHTML = `<div class="empty-state">Couldn't load badges.</div>`;
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

loadChallenge();
loadBadges();
