/**
 * TradePost — Premium Frontend Engine
 * =====================================
 * Scroll-reveal, 3D card tilt, particle canvas, animated counters,
 * ripple effects, typed text, smooth toast system.
 */
'use strict';

/* ══════════════════════════════════════════════════════════════
   1. PARTICLE BACKGROUND
══════════════════════════════════════════════════════════════ */
(function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let particles = [];
  let W, H;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  function Particle() {
    this.reset();
  }
  Particle.prototype.reset = function() {
    this.x  = Math.random() * W;
    this.y  = Math.random() * H;
    this.r  = Math.random() * 1.5 + .4;
    this.vx = (Math.random() - .5) * .35;
    this.vy = (Math.random() - .5) * .35;
    this.alpha = Math.random() * .45 + .1;
    this.hue = Math.random() > .5 ? '91,156,246' : '139,92,246';
  };
  Particle.prototype.update = function() {
    this.x += this.vx; this.y += this.vy;
    if (this.x < -5 || this.x > W+5 || this.y < -5 || this.y > H+5) this.reset();
  };
  Particle.prototype.draw = function() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.hue},${this.alpha})`;
    ctx.fill();
  };

  const N = Math.min(80, Math.floor(W * H / 14000));
  for (let i = 0; i < N; i++) particles.push(new Particle());

  // Draw connections between nearby particles
  function drawConnections() {
    const MAX_DIST = 120;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i+1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < MAX_DIST) {
          const alpha = (1 - dist/MAX_DIST) * .12;
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(91,156,246,${alpha})`;
          ctx.lineWidth = .6;
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach(p => { p.update(); p.draw(); });
    requestAnimationFrame(loop);
  }
  loop();
})();


/* ══════════════════════════════════════════════════════════════
   2. SCROLL REVEAL (Intersection Observer)
══════════════════════════════════════════════════════════════ */
(function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal-up,.reveal-left,.reveal-right,.reveal-scale')
    .forEach(el => observer.observe(el));
})();


/* ══════════════════════════════════════════════════════════════
   3. 3D CARD TILT
══════════════════════════════════════════════════════════════ */
(function initCardTilt() {
  const TILT = 8; // max degrees

  document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width  - .5;
      const y = (e.clientY - rect.top)  / rect.height - .5;
      card.style.transform = `
        perspective(900px)
        rotateY(${x * TILT}deg)
        rotateX(${-y * TILT}deg)
        translateY(-6px) scale(1.01)
      `;
      // update radial spotlight
      card.style.setProperty('--mouse-x', `${(x+.5)*100}%`);
      card.style.setProperty('--mouse-y', `${(y+.5)*100}%`);
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();


/* ══════════════════════════════════════════════════════════════
   4. ANIMATED COUNTERS (odometer effect)
══════════════════════════════════════════════════════════════ */
function animateCounter(el, target, duration = 1400) {
  const start = performance.now();
  const from = 0;
  function step(ts) {
    const progress = Math.min((ts - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 4); // ease-out-quart
    el.textContent = Math.round(from + (target - from) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

(function initCounters() {
  const counterEls = document.querySelectorAll('[data-count]');
  if (!counterEls.length) return;

  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const val = parseInt(el.dataset.count, 10);
        animateCounter(el, val);
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  counterEls.forEach(el => obs.observe(el));
})();


/* ══════════════════════════════════════════════════════════════
   5. STAGGERED CARD ENTRANCE
══════════════════════════════════════════════════════════════ */
(function initStaggeredCards() {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;

  const cards = grid.querySelectorAll('.card');
  cards.forEach((card, i) => {
    card.style.opacity    = '0';
    card.style.transform  = 'translateY(32px)';
    card.style.transition = `opacity .55s ease ${i * 70}ms, transform .55s cubic-bezier(.22,1,.36,1) ${i * 70}ms`;
  });

  // Trigger after a short delay
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      cards.forEach(card => {
        card.style.opacity   = '1';
        card.style.transform = '';
      });
    });
  });
})();


/* ══════════════════════════════════════════════════════════════
   6. NAVBAR SCROLL EFFECT
══════════════════════════════════════════════════════════════ */
(function initNavbarScroll() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }, { passive: true });
})();


/* ══════════════════════════════════════════════════════════════
   7. BUTTON RIPPLE EFFECT
══════════════════════════════════════════════════════════════ */
document.addEventListener('click', e => {
  const btn = e.target.closest('.btn');
  if (!btn || btn.disabled) return;
  const rect   = btn.getBoundingClientRect();
  const size   = Math.max(rect.width, rect.height) * 2;
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  ripple.style.cssText = `
    width:${size}px; height:${size}px;
    left:${e.clientX - rect.left - size/2}px;
    top:${e.clientY - rect.top - size/2}px;
  `;
  btn.appendChild(ripple);
  ripple.addEventListener('animationend', () => ripple.remove());
});


/* ══════════════════════════════════════════════════════════════
   8. MODAL HELPERS
══════════════════════════════════════════════════════════════ */
function openModal(id)  { document.getElementById(id)?.classList.add('open') }
function closeModal(id) { document.getElementById(id)?.classList.remove('open') }
function closeOnBackdrop(e, id) { if (e.target === e.currentTarget) closeModal(id) }
document.addEventListener('keydown', e => {
  if (e.key === 'Escape')
    document.querySelectorAll('.modal-overlay.open').forEach(el => el.classList.remove('open'));
});


/* ══════════════════════════════════════════════════════════════
   9. TOAST SYSTEM
══════════════════════════════════════════════════════════════ */
function showToast(msg, type = 'info', ms = 4000) {
  const area = document.getElementById('toast-area');
  if (!area) return;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span style="font-size:1.05rem;font-weight:700">${icons[type]||'ℹ'}</span><span>${msg}</span>`;
  area.appendChild(t);
  setTimeout(() => {
    t.style.transition = 'opacity .35s ease, transform .35s ease';
    t.style.opacity    = '0';
    t.style.transform  = 'translateX(110%)';
    setTimeout(() => t.remove(), 360);
  }, ms);
}


/* ══════════════════════════════════════════════════════════════
   10. MARKETPLACE FILTER / SORT
══════════════════════════════════════════════════════════════ */
let _activeFilter = 'All';

function setFilter(status, chip) {
  _activeFilter = status;
  document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  chip?.classList.add('active');
  _applyFilters();
}

function filterCards() { _applyFilters(); }

function _applyFilters() {
  const q = (document.getElementById('search-input')?.value || '').toLowerCase().trim();
  document.querySelectorAll('#marketplace-grid .item-card').forEach(card => {
    const status = card.dataset.status || '';
    const title  = card.dataset.title  || '';
    const desc   = card.dataset.desc   || '';
    const matchS = _activeFilter === 'All' || status === _activeFilter;
    const matchQ = !q || title.includes(q) || desc.includes(q);
    const el = card.closest('.card') || card;
    el.style.display = matchS && matchQ ? '' : 'none';
  });
}

function sortCards(order) {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.card')];
  cards.sort((a, b) => {
    const ia = a.querySelector('.item-card');
    const ib = b.querySelector('.item-card');
    if (!ia || !ib) return 0;
    if (order === 'alpha')   return (ia.dataset.title||'').localeCompare(ib.dataset.title||'');
    if (order === 'offers')  return parseInt(ib.dataset.offers||0) - parseInt(ia.dataset.offers||0);
    if (order === 'oldest')  return parseInt(ia.dataset.id||0) - parseInt(ib.dataset.id||0);
    // newest (default): highest id first
    return parseInt(ib.dataset.id||0) - parseInt(ia.dataset.id||0);
  });
  cards.forEach(c => grid.appendChild(c));
}


/* ══════════════════════════════════════════════════════════════
   11. DASHBOARD TAB SWITCHING
══════════════════════════════════════════════════════════════ */
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


/* ══════════════════════════════════════════════════════════════
   12. AUTH HELPERS
══════════════════════════════════════════════════════════════ */
function _authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + (APP?.token || localStorage.getItem('tp_token') || ''),
  };
}
