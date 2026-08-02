/**
 * TradePost — Phase 4 Static UI
 * Shared JavaScript: modals, toasts, marketplace filter/sort, dashboard tabs.
 * No frameworks. All data is static mock.
 */

'use strict';

/* ══════════════════════════════════════════════════════════
   MODAL HELPERS
══════════════════════════════════════════════════════════ */

function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}

function closeOnBackdrop(event, id) {
  if (event.target === event.currentTarget) closeModal(id);
}

// Close any open modal on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open')
      .forEach(el => el.classList.remove('open'));
  }
});

/* ══════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
══════════════════════════════════════════════════════════ */

function showToast(message, type = 'info', duration = 3500) {
  const area = document.getElementById('toast-area');
  if (!area) return;

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  area.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity .3s, transform .3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 320);
  }, duration);
}

/* ══════════════════════════════════════════════════════════
   MARKETPLACE — FILTER & SORT
══════════════════════════════════════════════════════════ */

let activeFilter = 'All';

function setFilter(category, chipEl) {
  activeFilter = category;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  if (chipEl) chipEl.classList.add('active');
  applyFilters();
}

function filterCards() { applyFilters(); }

function applyFilters() {
  const query = (document.getElementById('search-input')?.value || '').toLowerCase();
  const cards  = document.querySelectorAll('#marketplace-grid .item-card');

  cards.forEach(card => {
    const category = card.dataset.category || '';
    const title    = (card.dataset.title || '').toLowerCase();
    const matchCat = activeFilter === 'All' || category === activeFilter;
    const matchQ   = !query || title.includes(query);
    card.closest('.card').style.display = (matchCat && matchQ) ? '' : 'none';
  });
}

function sortCards(order) {
  const grid  = document.getElementById('marketplace-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.card')];

  cards.sort((a, b) => {
    const ia = a.querySelector('.item-card');
    const ib = b.querySelector('.item-card');
    if (order === 'alpha') {
      return (ia?.dataset.title || '').localeCompare(ib?.dataset.title || '');
    }
    if (order === 'offers') {
      return parseInt(ib?.dataset.offers || 0) - parseInt(ia?.dataset.offers || 0);
    }
    return 0; // newest — keep DOM order
  });

  cards.forEach(c => grid.appendChild(c));
}

/* ══════════════════════════════════════════════════════════
   MARKETPLACE — OFFER MODAL
══════════════════════════════════════════════════════════ */

function openOffer(title, emoji, postId) {
  const titleEl = document.getElementById('offer-target-title');
  const emojiEl = document.getElementById('offer-emoji');
  if (titleEl) titleEl.textContent = title;
  if (emojiEl) emojiEl.innerHTML   = emoji;

  // store postId on the form for submission
  const form = document.querySelector('#modal-offer form');
  if (form) form.dataset.postId = postId;

  openModal('modal-offer');
}

function submitOffer(e) {
  e.preventDefault();
  closeModal('modal-offer');
  showToast('Offer submitted! Waiting for the post owner to respond.', 'success');
  e.target.reset();
}

function submitPost(e) {
  e.preventDefault();
  closeModal('modal-post');
  showToast('Listing posted to the Trading Board!', 'success');
  e.target.reset();
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD — TAB SWITCHING
══════════════════════════════════════════════════════════ */

function switchTab(state, tabEl) {
  // update tab styles
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  if (tabEl) tabEl.classList.add('active');

  // show/hide negotiation cards
  const cards = document.querySelectorAll('.negotiation-card');
  cards.forEach(card => {
    const cardState = card.dataset.state;
    const show = state === 'all'
      || cardState === state
      || (state === 'closed' && cardState === 'closed');
    card.style.display = show ? '' : 'none';
  });
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD — COUNTER MODAL
══════════════════════════════════════════════════════════ */

function openCounter(offerId, postTitle) {
  const titleEl = document.getElementById('counter-post-title');
  if (titleEl) titleEl.textContent = postTitle;

  const form = document.querySelector('#modal-counter form');
  if (form) form.dataset.offerId = offerId;

  openModal('modal-counter');
}

function submitCounter(e) {
  e.preventDefault();
  closeModal('modal-counter');
  showToast('Counter-offer sent. Turn flipped to your peer.', 'success');
  e.target.reset();
}

/* ══════════════════════════════════════════════════════════
   DASHBOARD — ACCEPT / DECLINE ACTIONS
══════════════════════════════════════════════════════════ */

function handleAction(action, offerId) {
  if (action === 'accept') {
    showToast(`Offer #${offerId} accepted! All rival offers auto-declined.`, 'success');
  } else if (action === 'decline') {
    showToast(`Offer #${offerId} declined.`, 'error');
  }
}
