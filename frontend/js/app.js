// ============================================================
// Zomato AI — Frontend Logic (Phase 6)
// Handles form interaction, API calls, and dynamic rendering
// ============================================================

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://your-railway-url.up.railway.app';  // TODO: Replace with your actual Railway URL after deployment

// ── DOM References ──
const elements = {
  navbar: document.getElementById('navbar'),
  form: document.getElementById('preference-form'),
  locationSelect: document.getElementById('location-select'),
  budgetSelect: document.getElementById('budget-select'),
  cuisineSelect: document.getElementById('cuisine-select'),
  ratingSlider: document.getElementById('rating-slider'),
  ratingDisplay: document.getElementById('rating-display'),
  additionalPrefs: document.getElementById('additional-prefs'),
  btnRecommend: document.getElementById('btn-recommend'),
  errorSection: document.getElementById('error-section'),
  aiSummarySection: document.getElementById('ai-summary-section'),
  loadingSection: document.getElementById('loading-section'),
  resultsSection: document.getElementById('results-section'),
  emptyState: document.getElementById('empty-state'),
};

// ── State ──
const state = {
  isLoading: false,
  bookmarkedIds: new Set(),
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', () => {
  initNavbarScroll();
  initRatingSlider();
  initForm();
  loadDropdowns();
});

// ── Navbar scroll effect ──
function initNavbarScroll() {
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        elements.navbar.classList.toggle('scrolled', window.scrollY > 10);
        ticking = false;
      });
      ticking = true;
    }
  });
}

// ── Rating slider ──
function initRatingSlider() {
  const slider = elements.ratingSlider;
  const display = elements.ratingDisplay;

  function update() {
    const val = parseFloat(slider.value);
    display.textContent = val === 0 ? 'Any' : `${val.toFixed(1)}+`;
    const pct = (val / 5) * 100;
    slider.style.setProperty('--slider-fill', `${pct}%`);
  }

  slider.addEventListener('input', update);
  update(); // set initial
}

// ── Form submit ──
function initForm() {
  elements.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (state.isLoading) return;
    await fetchRecommendations();
  });
}

// ============================================================
// API: Load Dropdowns
// ============================================================

async function loadDropdowns() {
  try {
    const [locRes, cuisRes] = await Promise.all([
      fetch(`${API_BASE}/api/locations`),
      fetch(`${API_BASE}/api/cuisines`),
    ]);

    if (locRes.ok) {
      const { locations } = await locRes.json();
      populateSelect(elements.locationSelect, locations, 'Select City');
    }

    if (cuisRes.ok) {
      const { cuisines } = await cuisRes.json();
      populateSelect(elements.cuisineSelect, cuisines, 'Choose Cuisine');
    }
  } catch (err) {
    console.warn('Could not load dropdowns — API may be offline:', err.message);
  }
}

function populateSelect(selectEl, items, placeholder) {
  selectEl.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach((item) => {
    const opt = document.createElement('option');
    opt.value = item;
    opt.textContent = item;
    selectEl.appendChild(opt);
  });
}

// ============================================================
// API: Fetch Recommendations
// ============================================================

async function fetchRecommendations() {
  const location = elements.locationSelect.value;
  const budget = elements.budgetSelect.value;
  const cuisine = elements.cuisineSelect.value || null;
  const minRating = parseFloat(elements.ratingSlider.value);
  const additional = elements.additionalPrefs.value.trim() || null;

  // Validation
  if (!location) {
    showError('Please select a location to get recommendations.');
    return;
  }
  if (!budget) {
    showError('Please select a budget range.');
    return;
  }

  // Build request body
  const body = {
    location,
    budget,
    cuisine,
    min_rating: minRating,
    additional_preferences: additional,
  };

  // Show loading
  setLoading(true);
  hideError();
  hideSummary();
  hideResults();
  hideEmptyState();

  try {
    const res = await fetch(`${API_BASE}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => null);
      const msg = errData?.detail || `Server error (${res.status})`;

      if (res.status === 404) {
        setLoading(false);
        showEmptyState(msg);
        return;
      }

      throw new Error(msg);
    }

    const data = await res.json();
    setLoading(false);

    if (!data.recommendations || data.recommendations.length === 0) {
      showEmptyState('No restaurants found matching your preferences. Try relaxing your filters.');
      return;
    }

    // Render results
    showSummary(data.ai_summary, data.query, data.total_matches);
    renderCards(data.recommendations);
  } catch (err) {
    setLoading(false);
    showError(err.message || 'Something went wrong. Please try again.');
  }
}

// ============================================================
// UI: Loading State
// ============================================================

function setLoading(loading) {
  state.isLoading = loading;
  const btn = elements.btnRecommend;

  if (loading) {
    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = 'Finding restaurants…';
    btn.querySelector('.sparkle-icon').innerHTML = '<span class="btn-spinner"></span>';
    showLoadingSkeleton();
  } else {
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = 'Get Recommendations';
    btn.querySelector('.sparkle-icon').textContent = '✨';
    hideLoadingSkeleton();
  }
}

function showLoadingSkeleton() {
  elements.loadingSection.classList.remove('hidden');
  elements.loadingSection.innerHTML = `
    <div class="skeleton-grid">
      ${[1, 2, 3].map(() => `
        <div class="skeleton-card">
          <div class="skeleton-line title"></div>
          <div class="skeleton-line medium"></div>
          <div class="skeleton-line short"></div>
          <div class="skeleton-line block"></div>
        </div>
      `).join('')}
    </div>
  `;
}

function hideLoadingSkeleton() {
  elements.loadingSection.classList.add('hidden');
  elements.loadingSection.innerHTML = '';
}

// ============================================================
// UI: Error State
// ============================================================

function showError(message) {
  elements.errorSection.classList.remove('hidden');
  elements.errorSection.innerHTML = `
    <div class="error-banner">
      <span class="error-banner-icon">⚠️</span>
      <div class="error-banner-content">
        <div class="error-banner-title">Something went wrong</div>
        <div class="error-banner-text">${escapeHtml(message)}</div>
      </div>
      <button class="error-dismiss" id="error-dismiss-btn" title="Dismiss" aria-label="Dismiss error">&times;</button>
    </div>
  `;
  document.getElementById('error-dismiss-btn').addEventListener('click', hideError);
}

function hideError() {
  elements.errorSection.classList.add('hidden');
  elements.errorSection.innerHTML = '';
}

// ============================================================
// UI: AI Summary
// ============================================================

function showSummary(summary, query, totalMatches) {
  if (!summary) return;
  elements.aiSummarySection.classList.remove('hidden');
  elements.aiSummarySection.innerHTML = `
    <div class="ai-summary-section">
      <div class="ai-summary-card">
        <div class="ai-summary-icon">💡</div>
        <div class="ai-summary-text">
          <strong>Based on your preferences,</strong> ${escapeHtml(summary)}
        </div>
      </div>
    </div>
  `;
}

function hideSummary() {
  elements.aiSummarySection.classList.add('hidden');
  elements.aiSummarySection.innerHTML = '';
}

// ============================================================
// UI: Render Cards
// ============================================================

function renderCards(recommendations) {
  elements.resultsSection.classList.remove('hidden');
  elements.resultsSection.innerHTML = `
    <div class="results-section">
      <div class="results-grid">
        ${recommendations.map((rec) => createCardHTML(rec)).join('')}
      </div>
    </div>
  `;

  // Attach bookmark handlers
  elements.resultsSection.querySelectorAll('.card-bookmark').forEach((btn) => {
    btn.addEventListener('click', () => {
      const id = btn.dataset.name;
      toggleBookmark(btn, id);
    });
  });
}

function createCardHTML(rec) {
  const isBookmarked = state.bookmarkedIds.has(rec.restaurant_name);
  const stars = renderStars(rec.rating);

  return `
    <article class="restaurant-card" id="card-${slugify(rec.restaurant_name)}">
      <span class="card-rank">#${rec.rank}</span>
      <div class="card-header">
        <div class="card-title-group">
          <span class="card-title">${escapeHtml(rec.restaurant_name)}</span>
          <span class="card-rating">${rec.rating.toFixed(1)} ${stars}</span>
        </div>
        <button class="card-bookmark ${isBookmarked ? 'bookmarked' : ''}"
                data-name="${escapeHtml(rec.restaurant_name)}"
                title="Bookmark" aria-label="Bookmark ${escapeHtml(rec.restaurant_name)}">
          ${isBookmarked ? '🔖' : '🏷️'}
        </button>
      </div>
      <div class="card-meta">
        <span class="card-tag">${escapeHtml(rec.cuisine)}</span>
        <span class="card-cost">${escapeHtml(rec.estimated_cost)}</span>
      </div>
      <div class="card-reason">
        <div class="card-reason-label">AI Reason</div>
        <p class="card-reason-text">${escapeHtml(rec.explanation)}</p>
      </div>
    </article>
  `;
}

function hideResults() {
  elements.resultsSection.classList.add('hidden');
  elements.resultsSection.innerHTML = '';
}

// ============================================================
// UI: Empty State
// ============================================================

function showEmptyState(message) {
  elements.emptyState.classList.remove('hidden');
  elements.emptyState.innerHTML = `
    <div class="empty-state">
      <div class="empty-state-icon">🍽️</div>
      <h3 class="empty-state-title">No restaurants found</h3>
      <p class="empty-state-text">${escapeHtml(message || 'Try adjusting your filters for more results.')}</p>
    </div>
  `;
}

function hideEmptyState() {
  elements.emptyState.classList.add('hidden');
  elements.emptyState.innerHTML = '';
}

// ============================================================
// UI: Bookmark Toggle
// ============================================================

function toggleBookmark(btnEl, name) {
  if (state.bookmarkedIds.has(name)) {
    state.bookmarkedIds.delete(name);
    btnEl.classList.remove('bookmarked');
    btnEl.textContent = '🏷️';
  } else {
    state.bookmarkedIds.add(name);
    btnEl.classList.add('bookmarked');
    btnEl.textContent = '🔖';
  }
}

// ============================================================
// HELPERS
// ============================================================

function renderStars(rating) {
  const full = Math.floor(rating);
  const half = rating - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return (
    '<span class="star">★</span>'.repeat(full) +
    (half ? '<span class="star" style="opacity:0.5">★</span>' : '') +
    '<span class="star" style="opacity:0.18">★</span>'.repeat(empty)
  );
}

function escapeHtml(text) {
  if (!text) return '';
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, (m) => map[m]);
}

function slugify(text) {
  return String(text)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}
