import { ApiClient } from './api/client.js';
import { MapManager } from './map/mapManager.js';
import { AIAssistant } from './ai/aiAssistant.js';
import { RealtimeManager } from './utils/websocket.js';
import { getLang, setLang, t } from './i18n/translations.js';

class App {
  constructor() {
    this.mapManager = null;
    this.aiAssistant = null;
    this.realtime = null;
    this.stations = [];
    this.selectedStation = null;
    this.currentFilter = 'all';
    this.currentCity = 'tashkent';
    this.searchQuery = '';
    this.userLocation = { lat: 41.311081, lng: 69.240562 }; // Default Tashkent Center
  }

  async init() {
    this.initMap();
    this.initAI();
    this.initRealtime();
    this.attachDOMEvents();
    this.updateUserAuthUI();
    await this.loadInitialData();
  }

  initMap() {
    this.mapManager = new MapManager('map-container', {
      onStationClick: (station) => this.openStationDetails(station)
    });

    // Detect user geolocation if allowed
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.userLocation = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude
          };
          this.mapManager.updateUserMarker(this.userLocation.lat, this.userLocation.lng);
          this.loadStations();
          this.loadBestOption();
        },
        () => {
          console.log('Using default Tashkent center coordinates.');
        }
      );
    }
  }

  initAI() {
    this.aiAssistant = new AIAssistant({
      getUserLocation: () => this.userLocation,
      onAction: (type, stationId) => this.handleAIAction(type, stationId)
    });
  }

  initRealtime() {
    this.realtime = new RealtimeManager((msg) => {
      this.handleRealtimeEvent(msg);
    });
  }

  handleRealtimeEvent(msg) {
    if (msg.type === 'CNG_PRESSURE_UPDATED' || msg.type === 'PRICE_UPDATED' || msg.type === 'STATION_UPDATED') {
      this.showToast(`⚡ Yangilanish: ${msg.station_name || 'Zapravka'} ma'lumotlari yangilandi!`);
      this.loadStations();
      this.loadBestOption();
      this.loadLiveTicker();
      if (this.selectedStation && this.selectedStation.id === msg.station_id) {
        this.openStationDetails({ id: msg.station_id });
      }
    } else if (msg.type === 'ANNOUNCEMENT') {
      this.showToast(`📢 ${msg.title}: ${msg.message}`);
    }
  }

  showToast(text) {
    const toast = document.createElement('div');
    toast.className = 'live-toast';
    toast.textContent = text;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('visible'), 50);
    setTimeout(() => {
      toast.classList.remove('visible');
      setTimeout(() => toast.remove(), 400);
    }, 4500);
  }

  async loadInitialData() {
    await Promise.all([
      this.loadStations(),
      this.loadBestOption(),
      this.loadLiveTicker()
    ]);
  }

  async loadLiveTicker() {
    try {
      const summary = await ApiClient.getAnalyticsSummary();
      const avgPresEl = document.getElementById('ticker-avg-pressure');
      const min92El = document.getElementById('ticker-min-92');
      const evPortsEl = document.getElementById('ticker-ev-ports');

      if (avgPresEl) avgPresEl.textContent = `${summary.cng.average_pressure_bar} bar`;
      if (evPortsEl) evPortsEl.textContent = `${summary.ev.available_ports} / ${summary.ev.total_ports}`;
      
      const ai92 = summary.fuels.find(f => f.code === 'ai_92');
      if (min92El && ai92) {
        min92El.textContent = `${ai92.min_price.toLocaleString()} so'm`;
      }
    } catch (e) {
      console.warn('Ticker load failed:', e);
    }
  }

  async loadStations() {
    const params = {
      user_lat: this.userLocation.lat,
      user_lon: this.userLocation.lng,
      sort_by: 'nearest'
    };

    if (this.searchQuery) params.search = this.searchQuery;
    if (this.currentCity && this.currentCity !== 'all') params.city = this.currentCity;

    if (this.currentFilter === 'cng') params.only_cng = true;
    else if (this.currentFilter === 'lpg') params.only_lpg = true;
    else if (this.currentFilter === 'ev') params.only_ev = true;
    else if (this.currentFilter === 'ai_92') params.fuel_code = 'ai_92';
    else if (this.currentFilter === 'ai_95') params.fuel_code = 'ai_95';
    else if (this.currentFilter === 'diesel') params.only_diesel = true;
    else if (this.currentFilter === 'open') params.only_open = true;

    try {
      this.stations = await ApiClient.getStations(params);
      this.mapManager.renderStations(this.stations);
      this.renderStationList(this.stations);
    } catch (err) {
      console.error('Failed to load stations:', err);
    }
  }

  async loadBestOption() {
    const fuelTarget = this.currentFilter.startsWith('ai_') ? this.currentFilter : (this.currentFilter === 'lpg' ? 'lpg' : 'cng');
    try {
      const bestRes = await ApiClient.getBestOption(fuelTarget, this.userLocation.lat, this.userLocation.lng, getLang());
      this.renderBestOptionCard(bestRes);
    } catch (err) {
      console.warn('Best option recommendation unavailable:', err);
      const card = document.getElementById('best-option-card');
      if (card) card.classList.add('hidden');
    }
  }

  renderBestOptionCard(bestRes) {
    const card = document.getElementById('best-option-card');
    if (!card || !bestRes || !bestRes.station) return;

    card.classList.remove('hidden');
    const st = bestRes.station;

    let priceTag = '';
    if (st.cng_data) {
      priceTag = `<span class="bo-price">${st.cng_data.price.toLocaleString()} so'm</span> (Metan)`;
    } else if (st.fuels && st.fuels.length > 0) {
      priceTag = `<span class="bo-price">${st.fuels[0].price.toLocaleString()} so'm</span> (${st.fuels[0].fuel_name})`;
    }

    const reasonsList = bestRes.reasons.map(r => `<li>✓ ${r}</li>`).join('');

    card.innerHTML = `
      <div class="bo-header">
        <div class="bo-badge">🏆 ${t('best_option')} (${bestRes.score} ball)</div>
        <button class="bo-close" id="bo-card-close">✕</button>
      </div>
      <div class="bo-body">
        <h3 class="bo-title">${st.name}</h3>
        <p class="bo-address">${st.address}</p>
        <div class="bo-meta">
          <span>📍 ${st.distance_km || 1.2} km</span>
          <span>⏱ ~${st.estimated_time_mins || 4} daqiqa</span>
          <span>⭐ ${st.rating}</span>
          ${priceTag}
        </div>
        <ul class="bo-reasons">${reasonsList}</ul>
      </div>
      <div class="bo-actions">
        <button class="btn btn-primary" id="bo-btn-route">🚀 Marshrut tuzish</button>
        <button class="btn btn-secondary" id="bo-btn-detail">Batafsil</button>
      </div>
    `;

    document.getElementById('bo-card-close').onclick = () => card.classList.add('hidden');
    document.getElementById('bo-btn-route').onclick = () => this.buildRouteToStation(st);
    document.getElementById('bo-btn-detail').onclick = () => this.openStationDetails(st);
  }

  renderStationList(stations) {
    const container = document.getElementById('station-cards-list');
    if (!container) return;

    if (stations.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M16 16s-1.5-2-4-2-4 2-4 2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
          <p>Hech qanday zapravka topilmadi</p>
        </div>
      `;
      return;
    }

    container.innerHTML = stations.map(st => {
      let mainBadge = '';
      if (st.cng_data && st.cng_data.is_available) {
        const presClass = st.cng_data.pressure_bar < 140 ? 'warn' : 'good';
        mainBadge = `<span class="st-chip cng-${presClass}">🟢 Metan: ${st.cng_data.pressure_bar} bar</span>`;
      }
      if (st.chargers && st.chargers.length > 0) {
        mainBadge += `<span class="st-chip ev-chip">⚡ EV: ${st.chargers[0].available_chargers}/${st.chargers[0].total_chargers}</span>`;
      }

      return `
        <div class="station-mini-card" data-station-id="${st.id}">
          <div class="mini-card-top">
            <h4>${st.name}</h4>
            <span class="mini-dist">${st.distance_km ? `${st.distance_km} km` : ''}</span>
          </div>
          <p class="mini-address">${st.address}</p>
          <div class="mini-chips">${mainBadge}</div>
          <div class="mini-bottom">
            <span class="mini-queue">🚗 Navbat: ${st.queue_length} mashina (~${st.queue_wait_minutes} daq.)</span>
            <span class="mini-rating">⭐ ${st.rating}</span>
          </div>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.station-mini-card').forEach(card => {
      card.onclick = () => {
        const id = parseInt(card.getAttribute('data-station-id'));
        const st = stations.find(s => s.id === id);
        if (st) {
          this.mapManager.flyToStation(st.latitude, st.longitude);
          this.openStationDetails(st);
        }
      };
    });
  }

  async openStationDetails(station) {
    this.selectedStation = station;
    const modal = document.getElementById('station-detail-drawer');
    if (!modal) return;

    modal.classList.remove('hidden');
    modal.classList.add('active');

    // Fetch freshest details
    try {
      const full = await ApiClient.getStationDetail(station.id, this.userLocation.lat, this.userLocation.lng);
      this.selectedStation = full;
      this.renderDrawerContent(full);
    } catch {
      this.renderDrawerContent(station);
    }
  }

  renderDrawerContent(st) {
    const container = document.getElementById('drawer-content');
    if (!container) return;

    // Fuels Table
    let fuelsHtml = '<p class="text-muted">Yoqilg\'i ma\'lumotlari yo\'q</p>';
    if (st.fuels && st.fuels.length > 0) {
      fuelsHtml = `
        <table class="spec-table">
          <thead>
            <tr><th>Turi</th><th>Narxi</th><th>Holat</th></tr>
          </thead>
          <tbody>
            ${st.fuels.map(f => `
              <tr>
                <td><b>${f.fuel_name}</b></td>
                <td class="price-val">${f.price.toLocaleString()} so'm</td>
                <td><span class="status-dot ${f.is_available ? 'active' : 'inactive'}"></span> ${f.is_available ? 'Mavjud' : 'Tugagan'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }

    // CNG Section
    let cngHtml = '';
    if (st.cng_data) {
      const p = st.cng_data;
      const presColor = p.pressure_bar >= 190 ? '#10B981' : (p.pressure_bar >= 140 ? '#F59E0B' : '#EF4444');
      cngHtml = `
        <div class="cng-gauge-card">
          <div class="cng-gauge-header">
            <h4>🟢 Metan Gaz (CNG)</h4>
            <span class="cng-price-tag">${p.price.toLocaleString()} so'm/m³</span>
          </div>
          <div class="pressure-bar-visual">
            <div class="pressure-fill" style="width: ${Math.min(100, (p.pressure_bar / 240) * 100)}%; background: ${presColor}"></div>
          </div>
          <div class="gauge-details">
            <span class="pressure-num" style="color: ${presColor}">${p.pressure_bar} BAR</span>
            <span class="gauge-status">${p.status === 'low_pressure' ? '⚠️ Past bosim' : '✅ Me\'yoriy bosim'}</span>
          </div>
        </div>
      `;
    }

    // EV Section
    let evHtml = '';
    if (st.chargers && st.chargers.length > 0) {
      evHtml = `
        <div class="ev-chargers-card">
          <h4>⚡ Elektromobil Quvvatlash (EV)</h4>
          ${st.chargers.map(c => `
            <div class="charger-item">
              <div>
                <b>${c.charger_type}</b> (${c.connector_type})
                <div class="charger-sub">${c.power_kw} kW quvvat | ${c.price_per_kwh.toLocaleString()} so'm/kWh</div>
              </div>
              <div class="charger-avail-badge ${c.available_chargers > 0 ? 'avail' : 'busy'}">
                ${c.available_chargers} / ${c.total_chargers} bo'sh
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    container.innerHTML = `
      <div class="drawer-header-view">
        <div>
          <h2>${st.name}</h2>
          <p class="drawer-address">${st.address} (${st.city || 'Toshkent'})</p>
        </div>
        <button id="drawer-close-btn" class="drawer-close">✕</button>
      </div>

      <div class="drawer-quick-stats">
        <div class="q-stat"><span>Masofa</span><b>${st.distance_km || 0} km</b></div>
        <div class="q-stat"><span>Kutish vaqti</span><b>~${st.queue_wait_minutes || 0} daq.</b></div>
        <div class="q-stat"><span>Navbat</span><b>${st.queue_length || 0} ta mashina</b></div>
        <div class="q-stat"><span>Reyting</span><b>⭐ ${st.rating}</b></div>
      </div>

      <div class="drawer-actions-bar">
        <button class="btn btn-primary" id="btn-drawer-route">🚀 Marshrut tuzish</button>
        <button class="btn btn-secondary" id="btn-drawer-fav">❤️ Sevimlilar</button>
        <button class="btn btn-outline" id="btn-drawer-report">⚠️ Xatolik</button>
        <button class="btn btn-outline" id="btn-drawer-review">⭐ Sharh</button>
      </div>

      <div class="drawer-details-body">
        ${cngHtml}
        ${evHtml}
        <div class="fuels-section">
          <h4>Yoqilg'i narxlari</h4>
          ${fuelsHtml}
        </div>
      </div>
    `;

    document.getElementById('drawer-close-btn').onclick = () => {
      document.getElementById('station-detail-drawer').classList.remove('active');
    };

    document.getElementById('btn-drawer-route').onclick = () => this.buildRouteToStation(st);
    document.getElementById('btn-drawer-fav').onclick = () => this.toggleFavorite(st.id);
    document.getElementById('btn-drawer-report').onclick = () => this.openReportModal(st);
    document.getElementById('btn-drawer-review').onclick = () => this.openReviewModal(st);
  }

  async buildRouteToStation(station) {
    try {
      this.showToast("Marshrut chizilmoqda...");
      const routeData = await ApiClient.getRoute(
        this.userLocation.lat,
        this.userLocation.lng,
        station.latitude,
        station.longitude
      );
      this.mapManager.drawRoute(routeData.coordinates);
      this.showToast(`🚀 Masofa: ${routeData.distance_km} km, yetib borish vaqti ~${routeData.duration_minutes} daqiqa`);
    } catch (err) {
      console.error('Route error:', err);
      this.showToast("Marshrut chizishda xatolik yuz berdi");
    }
  }

  async toggleFavorite(stationId) {
    if (!ApiClient.getUser()) {
      this.openAuthModal();
      return;
    }
    try {
      await ApiClient.addFavorite(stationId);
      this.showToast("Zapravka sevimlilarga qo'shildi!");
    } catch {
      this.showToast("Allaqachon sevimlilarga kiritilgan");
    }
  }

  openReportModal(station) {
    const modal = document.getElementById('report-modal');
    if (!modal) return;
    document.getElementById('report-station-name').textContent = station.name;
    document.getElementById('report-station-id').value = station.id;
    modal.classList.remove('hidden');
  }

  openReviewModal(station) {
    const modal = document.getElementById('review-modal');
    if (!modal) return;
    document.getElementById('review-station-name').textContent = station.name;
    document.getElementById('review-station-id').value = station.id;
    modal.classList.remove('hidden');
  }

  handleAIAction(type, stationId) {
    const st = this.stations.find(s => s.id === stationId);
    if (!st) return;

    if (type === 'SHOW_ON_MAP') {
      this.mapManager.flyToStation(st.latitude, st.longitude, 16);
    } else if (type === 'BUILD_ROUTE') {
      this.mapManager.flyToStation(st.latitude, st.longitude, 15);
      this.buildRouteToStation(st);
    } else if (type === 'VIEW_STATION') {
      this.openStationDetails(st);
    }
  }

  attachDOMEvents() {
    // Search input with debounce
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      let timeout = null;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          this.searchQuery = e.target.value.trim();
          this.loadStations();
        }, 300);
      });
    }

    // Filter Chips
    const filterButtons = document.querySelectorAll('.filter-chip');
    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentFilter = btn.getAttribute('data-filter');
        this.loadStations();
        this.loadBestOption();
      });
    });

    // City Selector
    const citySelector = document.getElementById('city-select');
    if (citySelector) {
      citySelector.addEventListener('change', (e) => {
        this.currentCity = e.target.value;
        this.mapManager.setCity(this.currentCity);
        this.loadStations();
      });
    }

    // Language Selector
    const langSelect = document.getElementById('lang-select');
    if (langSelect) {
      langSelect.value = getLang();
      langSelect.addEventListener('change', (e) => {
        setLang(e.target.value);
        window.location.reload();
      });
    }

    // User auth trigger
    const authBtn = document.getElementById('user-auth-btn');
    if (authBtn) {
      authBtn.onclick = () => {
        const user = ApiClient.getUser();
        if (user) {
          if (confirm(`${user.name} hisobidan chiqmoqchimisiz?`)) {
            ApiClient.logout();
            this.updateUserAuthUI();
          }
        } else {
          this.openAuthModal();
        }
      };
    }

    // Report modal submission
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
      reportForm.onsubmit = async (e) => {
        e.preventDefault();
        const stationId = parseInt(document.getElementById('report-station-id').value);
        const reportType = document.getElementById('report-type').value;
        const description = document.getElementById('report-desc').value;
        try {
          await ApiClient.submitReport({ station_id: stationId, report_type: reportType, description });
          this.showToast("Xabaringiz moderatorlarga yuborildi. Rahmat!");
          document.getElementById('report-modal').classList.add('hidden');
        } catch {
          this.showToast("Hisobot yuborishda xatolik");
        }
      };
    }

    // Review modal submission
    const reviewForm = document.getElementById('review-form');
    if (reviewForm) {
      reviewForm.onsubmit = async (e) => {
        e.preventDefault();
        if (!ApiClient.getUser()) {
          this.openAuthModal();
          return;
        }
        const stationId = parseInt(document.getElementById('review-station-id').value);
        const rating = parseFloat(document.getElementById('review-rating').value);
        const comment = document.getElementById('review-comment').value;
        try {
          await ApiClient.addReview(stationId, { rating, comment });
          this.showToast("Sharhingiz qabul qilindi va reyting yangilandi!");
          document.getElementById('review-modal').classList.add('hidden');
          this.loadStations();
        } catch {
          this.showToast("Sharh yuborishda xatolik");
        }
      };
    }

    // Close modals
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
      btn.onclick = () => {
        btn.closest('.modal-overlay').classList.add('hidden');
      };
    });
  }

  openAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (modal) modal.classList.remove('hidden');
  }

  updateUserAuthUI() {
    const user = ApiClient.getUser();
    const btn = document.getElementById('user-auth-btn');
    if (!btn) return;
    if (user) {
      btn.innerHTML = `👤 ${user.name.split(' ')[0]}`;
      btn.classList.add('btn-user-logged');
    } else {
      btn.innerHTML = `Kirish`;
      btn.classList.remove('btn-user-logged');
    }
  }
}

// Bootstrap application on load
window.addEventListener('DOMContentLoaded', () => {
  const app = new App();
  app.init();
});
