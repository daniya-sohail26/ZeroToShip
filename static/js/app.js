/**
 * TradePost — Phase 5 Live JS
 * All API calls use fetch() with the JWT from localStorage.
 * No hardcoded mock data remains.
 */
'use strict';

/* ── Modal helpers ──────────────────────────────────────────── */
function openModal(id)  { document.getElementById(id)?.classList.add('open') }
function closeModal(id) { document.getElementById(id)?.classList.remove('open') }
function closeOnBackdrop(e, id) { if (e.target === e.currentTarget) closeModal(id) }
document.addEventListener('keydown', e => {
  if (e.key === 'Escape')
    document.querySelectorAll('.modal-overlay.open').forEach(el => el.classList.remove('open'));
});

/* ── Toast ──────────────────────────────────────────────────── */
function showToast(msg, type = 'info', ms = 3800) {
  const area = document.getElementById('toast-area');
  if (!area) return;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span style="font-size:1rem">${icons[type]||'ℹ'}</span><span>${msg}</span>`;
  area.appendChild(t);
  setTimeout(() => {
    t.style.transition = 'opacity .3s,transform .3s';
    t.style.opacity = '0'; t.style.transform = 'translateX(110%)';
    setTimeout(() => t.remove(), 320);
  }, ms);
}

/* ── Marketplace filter / sort ──────────────────────────────── */
let _activeFilter = 'All';

function setFilter(status, chip) {
  _activeFilter = status;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  chip?.classList.add('active');
  _applyFilters();
}

function filterCards() { _applyFilters(); }

function _applyFilters() {
  const q = (document.getElementById('search-input')?.value || '').toLowerCase();
  document.querySelectorAll('#marketplace-grid .item-card').forEach(card => {
    const status = card.dataset.status || '';
    const title  = card.dataset.title  || '';
    const matchS = _activeFilter === 'All' || status === _activeFilter;
    const matchQ = !q || title.includes(q);
    card.closest('.card').style.display = matchS && matchQ ? '' : 'none';
  });
}

function sortCards(order) {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.card')];
  cards.sort((a, b) => {
    const ia = a.querySelector('.item-card'), ib = b.querySelector('.item-card');
    if (order === 'alpha')  return (ia?.dataset.title||'').localeCompare(ib?.dataset.title||'');
    if (order === 'offers') return parseInt(ib?.dataset.offers||0) - parseInt(ia?.dataset.offers||0);
    if (order === 'oldest') return parseInt(ia?.dataset.offers||0) - parseInt(ib?.dataset.offers||0);
    return 0;
  });
  cards.forEach(c => grid.appendChild(c));
}

/* ── Dashboard tab switching ────────────────────────────────── */
function switchTab(state, tabEl) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  tabEl?.classList.add('active');
  document.querySelectorAll('.negotiation-card').forEach(card => {
    const s = card.dataset.state;
    const show = state === 'all'
      || s === state
      || (state === 'closed' && (s === 'accepted' || s === 'declined'));
    card.style.display = show ? '' : 'none';
  });
}

/* ── Auth helpers ───────────────────────────────────────────── */
function _authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + (APP?.token || localStorage.getItem('tp_token') || ''),
  };
}
