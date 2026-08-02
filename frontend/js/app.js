// ============================================================
// Zomato AI — Frontend Logic
// Handles form interaction, API calls, and dynamic rendering
// Data source: Live Zomato scraping
// ============================================================

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : ''; // Relative path for Vercel Serverless

// ── DOM References ──
const elements = {
  navbar: document.getElementById('navbar'),
  form: document.getElementById('preference-form'),
  citySelect: document.getElementById('city-select'),
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
  loadCities();
  initCityCascade();
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

// ── City cascade: when city changes, reload location & cuisine dropdowns ──
function initCityCascade() {
  elements.citySelect.addEventListener('change', async () => {
    const city = elements.citySelect.value;
    if (!city) {
      resetSelect(elements.locationSelect, 'All Locations');
      resetSelect(elements.cuisineSelect, 'All Cuisines');
      return;
    }
    await loadCityDropdowns(city);
  });
}

// ============================================================
// API: Load Cities
// ============================================================

async function loadCities() {
  try {
    const res = await fetch(`${API_BASE}/api/cities`);
    if (res.ok) {
      const { cities } = await res.json();
      populateSelect(elements.citySelect, cities, 'Select City');
    }
  } catch (err) {
    console.warn('Could not load cities — API may be offline:', err.message);
  }
}

// ============================================================
// API: Load Location & Cuisine Dropdowns for a City
// ============================================================

async function loadCityDropdowns(city) {
  // Show loading state on dropdowns
  resetSelect(elements.locationSelect, 'Loading locations…');
  resetSelect(elements.cuisineSelect, 'Loading cuisines…');

  const citySlug = city.toLowerCase().replace(/ /g, '-');

  try {
    const [locRes, cuisRes] = await Promise.all([
      fetch(`${API_BASE}/api/locations/${citySlug}`),
      fetch(`${API_BASE}/api/cuisines/${citySlug}`),
    ]);

    if (locRes.ok) {
      const { locations } = await locRes.json();
      populateSelect(elements.locationSelect, locations, 'All Locations');
    } else {
      resetSelect(elements.locationSelect, 'All Locations');
    }

    if (cuisRes.ok) {
      const { cuisines } = await cuisRes.json();
      populateSelect(elements.cuisineSelect, cuisines, 'All Cuisines');
    } else {
      resetSelect(elements.cuisineSelect, 'All Cuisines');
    }
  } catch (err) {
    console.warn('Could not load city dropdowns:', err.message);
    resetSelect(elements.locationSelect, 'All Locations');
    resetSelect(elements.cuisineSelect, 'All Cuisines');
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

function resetSelect(selectEl, placeholder) {
  selectEl.innerHTML = `<option value="">${placeholder}</option>`;
}

// ============================================================
// API: Fetch Recommendations
// ============================================================

async function fetchRecommendations() {
  const city = elements.citySelect.value;
  const location = elements.locationSelect.value || null;
  const budget = elements.budgetSelect.value;
  const cuisine = elements.cuisineSelect.value || null;
  const minRating = parseFloat(elements.ratingSlider.value);
  const additional = elements.additionalPrefs.value.trim() || null;

  // Validation
  if (!city) {
    showError('Please select a city to get recommendations.');
    return;
  }
  if (!budget) {
    showError('Please select a budget range.');
    return;
  }

  // Build request body — uses city slug
  const body = {
    city: city.toLowerCase().replace(/ /g, '-'),
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
          <div class="skeleton-line image"></div>
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
// UI: Render Cards (with images and Zomato links)
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
  const hasImage = rec.image_url && rec.image_url.startsWith('http');
  const hasZomatoUrl = rec.zomato_url && rec.zomato_url.startsWith('http');

  return `
    <article class="restaurant-card" id="card-${slugify(rec.restaurant_name)}">
      ${hasImage ? `
        <div class="card-image-wrapper">
          <img src="${escapeHtml(rec.image_url)}" alt="${escapeHtml(rec.restaurant_name)}"
               class="card-image" loading="lazy"
               onerror="this.parentElement.style.display='none'">
        </div>
      ` : ''}
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
      ${hasZomatoUrl ? `
        <a href="${escapeHtml(rec.zomato_url)}" target="_blank" rel="noopener noreferrer"
           class="card-zomato-link">
          View on Zomato ↗
        </a>
      ` : ''}
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
