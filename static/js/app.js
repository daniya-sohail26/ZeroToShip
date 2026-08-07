/**
 * TradePost interaction layer
 * Cursor, ambient canvas, reveal motion, counters, upload preview, filters, and modals.
 */
'use strict';

(function initCursor() {
  const ring = document.querySelector('.cursor__ring');
  const dot = document.querySelector('.cursor__dot');
  if (!ring || !dot || window.matchMedia('(pointer: coarse)').matches) return;

  let mouseX = -120;
  let mouseY = -120;
  let ringX = -120;
  let ringY = -120;

  document.addEventListener('mousemove', event => {
    mouseX = event.clientX;
    mouseY = event.clientY;
    dot.style.left = `${mouseX}px`;
    dot.style.top = `${mouseY}px`;
  });

  document.addEventListener('mousedown', () => ring.classList.add('click'));
  document.addEventListener('mouseup', () => ring.classList.remove('click'));

  document.querySelectorAll('a, button, input, textarea, select, .trade-card, .chip, .tab, .upload-zone')
    .forEach(element => {
      element.addEventListener('mouseenter', () => ring.classList.add('hover'));
      element.addEventListener('mouseleave', () => ring.classList.remove('hover'));
    });

  function animate() {
    ringX += (mouseX - ringX) * 0.1;
    ringY += (mouseY - ringY) * 0.1;
    ring.style.left = `${ringX}px`;
    ring.style.top = `${ringY}px`;
    requestAnimationFrame(animate);
  }

  animate();
})();

(function initCanvas() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let width = 0;
  let height = 0;
  let points = [];

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    const count = Math.min(46, Math.floor((width * height) / 26000));
    points = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.8 + 0.7,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = 'rgba(21,21,18,0.28)';
    points.forEach(point => {
      if (!reduceMotion) {
        point.x += point.vx;
        point.y += point.vy;
        if (point.x < 0 || point.x > width) point.vx *= -1;
        if (point.y < 0 || point.y > height) point.vy *= -1;
      }
      ctx.beginPath();
      ctx.arc(point.x, point.y, point.r, 0, Math.PI * 2);
      ctx.fill();
    });
    if (!reduceMotion) requestAnimationFrame(draw);
  }

  resize();
  draw();
  window.addEventListener('resize', resize);
})();

function initSplitText() {
  document.querySelectorAll('[data-split]').forEach(element => {
    const words = element.textContent.trim().split(/\s+/);
    element.innerHTML = words
      .map(word => `<span class="sw"><i>${word}</i></span>`)
      .join(' ');
    element.classList.add('split-ready');
  });
}

initSplitText();

(function initReveal() {
  const selectors = '.reveal-up,.reveal-left,.reveal-right,.reveal-scale,[data-split]';
  const elements = document.querySelectorAll(selectors);
  if (!elements.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('visible');
      if (entry.target.hasAttribute('data-split')) entry.target.classList.add('in');
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });

  elements.forEach(element => observer.observe(element));
})();

document.querySelectorAll('.btn-magnetic').forEach(button => {
  button.addEventListener('mousemove', event => {
    const rect = button.getBoundingClientRect();
    const x = (event.clientX - rect.left - rect.width / 2) * 0.18;
    const y = (event.clientY - rect.top - rect.height / 2) * 0.18;
    button.style.transform = `translate(${x}px, ${y}px)`;
  });
  button.addEventListener('mouseleave', () => {
    button.style.transform = '';
  });
});

(function initTiltCards() {
  if (window.matchMedia('(pointer: coarse), (prefers-reduced-motion: reduce)').matches) return;

  document.querySelectorAll('.tilt-card').forEach(card => {
    card.addEventListener('mousemove', event => {
      const rect = card.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      card.style.transform = `perspective(900px) rotateX(${y * -5}deg) rotateY(${x * 7}deg) translateY(-6px)`;
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
})();

(function initFloatOnScroll() {
  const floaters = document.querySelectorAll('[data-float]');
  if (!floaters.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  let ticking = false;
  function update() {
    floaters.forEach(element => {
      const rect = element.getBoundingClientRect();
      const progress = (rect.top + rect.height / 2 - window.innerHeight / 2) / window.innerHeight;
      element.style.transform = `translateY(${progress * -28}px)`;
    });
    ticking = false;
  }

  function requestUpdate() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(update);
  }

  update();
  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', requestUpdate);
})();

function animateCount(element, target, ms = 1100) {
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / ms, 1);
    const eased = 1 - Math.pow(1 - progress, 4);
    element.textContent = Math.round(target * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

(function initCounters() {
  const counters = document.querySelectorAll('[data-count]');
  if (!counters.length) return;

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      animateCount(entry.target, parseInt(entry.target.dataset.count || '0', 10));
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.45 });

  counters.forEach(counter => observer.observe(counter));
})();

(function initNavbar() {
  const nav = document.querySelector('.navbar');
  if (!nav) return;
  const update = () => nav.classList.toggle('scrolled', window.scrollY > 18);
  update();
  window.addEventListener('scroll', update, { passive: true });
})();

let _selectedFile = null;

(function initUpload() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('post-image');
  const preview = document.getElementById('upload-preview');
  const removeButton = document.getElementById('upload-remove');
  if (!zone || !input || !preview) return;

  function resetUpload() {
    _selectedFile = null;
    preview.innerHTML = '';
    zone.classList.remove('has-image', 'dragging');
    input.value = '';
    if (removeButton) removeButton.style.display = 'none';
  }

  function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image must be under 5 MB.', 'error');
      return;
    }

    _selectedFile = file;
    const reader = new FileReader();
    reader.onload = event => {
      preview.innerHTML = `<img src="${event.target.result}" alt="Selected listing preview">`;
      zone.classList.add('has-image');
      if (removeButton) removeButton.style.display = 'block';
    };
    reader.readAsDataURL(file);
  }

  zone.addEventListener('dragover', event => {
    event.preventDefault();
    zone.classList.add('dragging');
  });

  zone.addEventListener('dragleave', () => zone.classList.remove('dragging'));

  zone.addEventListener('drop', event => {
    event.preventDefault();
    zone.classList.remove('dragging');
    handleFile(event.dataTransfer.files[0]);
  });

  zone.addEventListener('click', () => input.click());
  zone.addEventListener('keydown', event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      input.click();
    }
  });
  input.addEventListener('change', event => handleFile(event.target.files[0]));

  if (removeButton) {
    removeButton.addEventListener('click', event => {
      event.stopPropagation();
      resetUpload();
    });
  }

  window.resetNewPostForm = resetUpload;
})();

function openModal(id) {
  if (id === 'modal-post' && typeof window.resetNewPostForm === 'function') {
    window.resetNewPostForm();
  }
  document.getElementById(id)?.classList.add('open');
}

function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

function closeOnBackdrop(event, id) {
  if (event.target === event.currentTarget) closeModal(id);
}

document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  document.querySelectorAll('.modal-overlay.open').forEach(modal => modal.classList.remove('open'));
});

function showToast(message, type = 'info', ms = 4200) {
  const area = document.getElementById('toast-area');
  if (!area) return;

  const toast = document.createElement('div');
  const icon = document.createElement('span');
  const text = document.createElement('span');
  const icons = { success: 'OK', error: '!', info: 'i' };

  toast.className = `toast ${type}`;
  icon.className = 'toast__icon';
  icon.textContent = icons[type] || icons.info;
  text.textContent = message;

  toast.append(icon, text);
  area.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 240ms ease, transform 240ms ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(24px)';
    setTimeout(() => toast.remove(), 260);
  }, ms);
}

let _activeFilter = 'All';

function setFilter(status, chip) {
  _activeFilter = status;
  document.querySelectorAll('.chip').forEach(element => element.classList.remove('active'));
  chip?.classList.add('active');
  _applyFilters();
}

function filterCards() {
  _applyFilters();
}

function _applyFilters() {
  const query = (document.getElementById('search-input')?.value || '').toLowerCase().trim();
  document.querySelectorAll('#marketplace-grid .trade-card').forEach(card => {
    const status = card.dataset.status || '';
    const title = card.dataset.title || '';
    const desc = card.dataset.desc || '';
    const matchesStatus = _activeFilter === 'All' || status === _activeFilter;
    const matchesQuery = !query || title.includes(query) || desc.includes(query);
    card.style.display = matchesStatus && matchesQuery ? '' : 'none';
  });
}

function sortCards(order) {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.trade-card')];
  cards.sort((a, b) => {
    if (order === 'alpha') return (a.dataset.title || '').localeCompare(b.dataset.title || '');
    if (order === 'offers') return parseInt(b.dataset.offers || '0', 10) - parseInt(a.dataset.offers || '0', 10);
    if (order === 'oldest') return parseInt(a.dataset.id || '0', 10) - parseInt(b.dataset.id || '0', 10);
    return parseInt(b.dataset.id || '0', 10) - parseInt(a.dataset.id || '0', 10);
  });
  cards.forEach(card => grid.appendChild(card));
}

function switchTab(state, tabEl) {
  document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
  tabEl?.classList.add('active');
  document.querySelectorAll('.negotiation-card').forEach(card => {
    const cardState = card.dataset.state;
    const show = state === 'all'
      || cardState === state
      || (state === 'closed' && (cardState === 'accepted' || cardState === 'declined'));
    card.style.display = show ? '' : 'none';
  });
}

function _authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + (APP?.token || localStorage.getItem('tp_token') || ''),
  };
}
