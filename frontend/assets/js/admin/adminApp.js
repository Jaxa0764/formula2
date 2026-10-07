import { ApiClient } from '../api/client.js';
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

class AdminApp {
  constructor() {
    this.currentTab = 'overview';
    this.overviewData = null;
    this.stations = [];
    this.trendChart = null;
    this.currentUser = null;
  }

  async init() {
    this.checkAuth();
    this.setupTabs();
    this.setupModals();
    await this.loadCurrentTab();
  }

  checkAuth() {
    const user = ApiClient.getUser();
    if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) {
      // Allow entering demo admin credentials or redirect
      const loginOverlay = document.getElementById('admin-login-overlay');
      if (loginOverlay) {
        loginOverlay.classList.remove('hidden');
        document.getElementById('admin-login-form').onsubmit = async (e) => {
          e.preventDefault();
          const email = document.getElementById('admin-email').value;
          const password = document.getElementById('admin-password').value;
          try {
            await ApiClient.login(email, password);
            loginOverlay.classList.add('hidden');
            window.location.reload();
          } catch (err) {
            alert('Kirish xatosi: ' + err.message);
          }
        };
      }
    } else {
      this.currentUser = user;
      document.getElementById('admin-profile-name').textContent = user.name;
    }
  }

  setupTabs() {
    const tabs = document.querySelectorAll('.nav-tab-btn');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        this.currentTab = tab.getAttribute('data-tab');
        this.switchTab(this.currentTab);
      });
    });
  }

  switchTab(tabId) {
    document.querySelectorAll('.admin-section').forEach(sec => sec.classList.add('hidden'));
    const target = document.getElementById(`section-${tabId}`);
    if (target) target.classList.remove('hidden');
    this.loadCurrentTab();
  }

  async loadCurrentTab() {
    if (this.currentTab === 'overview') await this.loadOverview();
    else if (this.currentTab === 'stations') await this.loadStations();
    else if (this.currentTab === 'cng') await this.loadCNG();
    else if (this.currentTab === 'prices') await this.loadPrices();
    else if (this.currentTab === 'ev') await this.loadEV();
    else if (this.currentTab === 'reports') await this.loadReports();
    else if (this.currentTab === 'alerts') await this.loadAlerts();
    else if (this.currentTab === 'audit') await this.loadAudit();
    else if (this.currentTab === 'users') await this.loadUsers();
  }

  async loadOverview() {
    try {
      const stats = await ApiClient.getAdminOverview();
      this.overviewData = stats;

      document.getElementById('stat-total-stations').textContent = stats.total_stations;
      document.getElementById('stat-active-stations').textContent = stats.active_stations;
      document.getElementById('stat-cng-available').textContent = stats.cng_available;
      document.getElementById('stat-ev-chargers').textContent = stats.ev_chargers;
      document.getElementById('stat-low-pressure').textContent = stats.low_pressure_stations;
      document.getElementById('stat-pending-reports').textContent = stats.pending_reports;
      document.getElementById('stat-user-count').textContent = stats.user_count;
      document.getElementById('stat-avg-pressure').textContent = `${stats.avg_cng_pressure} bar`;

      this.renderTrendChart();
    } catch (err) {
      console.error('Failed to load admin overview:', err);
    }
  }

  async renderTrendChart() {
    const ctx = document.getElementById('priceTrendChart');
    if (!ctx) return;

    try {
      const trends = await ApiClient.getPriceTrends('30d');
      if (this.trendChart) this.trendChart.destroy();

      this.trendChart = new Chart(ctx, {
        type: 'line',
        data: trends,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#94A3B8' } }
          },
          scales: {
            x: { ticks: { color: '#64748B' }, grid: { color: 'rgba(255,255,255,0.05)' } },
            y: { ticks: { color: '#64748B' }, grid: { color: 'rgba(255,255,255,0.05)' } }
          }
        }
      });
    } catch (e) {
      console.warn('Trend chart error:', e);
    }
  }

  async loadStations() {
    const tbody = document.getElementById('stations-table-body');
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="7" class="text-center">Yuklanmoqda...</td></tr>`;

    try {
      this.stations = await ApiClient.getStations();
      tbody.innerHTML = this.stations.map(st => `
        <tr>
          <td><b>#${st.id}</b></td>
          <td><b>${st.name}</b><br><small class="text-muted">${st.brand || ''}</small></td>
          <td>${st.city}</td>
          <td>${st.address}</td>
          <td>
            <span class="badge ${st.is_open ? 'badge-green' : 'badge-red'}">
              ${st.is_open ? 'Faol' : 'Yopiq'}
            </span>
          </td>
          <td>⭐ ${st.rating} (${st.reviews_count})</td>
          <td class="action-cells">
            <button class="btn-sm btn-edit" data-id="${st.id}">Tahrirlash</button>
            <button class="btn-sm btn-del" data-id="${st.id}">O'chirish</button>
          </td>
        </tr>
      `).join('');

      // Attach actions
      tbody.querySelectorAll('.btn-edit').forEach(b => {
        b.onclick = () => this.openEditStationModal(parseInt(b.getAttribute('data-id')));
      });
      tbody.querySelectorAll('.btn-del').forEach(b => {
        b.onclick = () => this.deleteStation(parseInt(b.getAttribute('data-id')));
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7">Yuklashda xatolik yuz berdi</td></tr>`;
    }
  }

  async loadCNG() {
    const container = document.getElementById('cng-control-cards');
    if (!container) return;
    container.innerHTML = 'Yuklanmoqda...';

    const stations = await ApiClient.getStations({ only_cng: true });
    container.innerHTML = stations.map(st => {
      const p = st.cng_data || { pressure_bar: 200, price: 3750 };
      return `
        <div class="cng-admin-card" data-id="${st.id}">
          <div class="card-head">
            <h4>${st.name}</h4>
            <span class="cng-cur-bar" id="cng-bar-val-${st.id}">${p.pressure_bar} BAR</span>
          </div>
          <p class="text-muted">${st.address}</p>
          <div class="slider-group">
            <label>Metan bosimi (bar):</label>
            <input type="range" class="cng-slider" data-id="${st.id}" min="90" max="240" value="${p.pressure_bar}" />
          </div>
          <div class="card-foot">
            <button class="btn btn-primary btn-save-cng" data-id="${st.id}">Bosimni saqlash</button>
          </div>
        </div>
      `;
    }).join('');

    container.querySelectorAll('.cng-slider').forEach(slider => {
      slider.oninput = (e) => {
        const id = slider.getAttribute('data-id');
        document.getElementById(`cng-bar-val-${id}`).textContent = `${e.target.value} BAR`;
      };
    });

    container.querySelectorAll('.btn-save-cng').forEach(btn => {
      btn.onclick = async () => {
        const id = parseInt(btn.getAttribute('data-id'));
        const card = btn.closest('.cng-admin-card');
        const slider = card.querySelector('.cng-slider');
        const val = parseFloat(slider.value);
        try {
          await ApiClient.updateCNG(id, { pressure_bar: val, is_available: true });
          alert(`Zapravka #${id} uchun metan bosimi ${val} bar ga o'zgartirildi! Barcha foydalanuvchilarga real-vaqtda jo'natildi.`);
        } catch (e) {
          alert('Xatolik: ' + e.message);
        }
      };
    });
  }

  async loadPrices() {
    const fuelSelect = document.getElementById('bulk-fuel-type');
    if (!fuelSelect) return;
    try {
      const types = await ApiClient.getFuelTypes();
      fuelSelect.innerHTML = types.map(t => `<option value="${t.id}">${t.name} (${t.code})</option>`).join('');

      document.getElementById('bulk-price-form').onsubmit = async (e) => {
        e.preventDefault();
        const fuelId = parseInt(fuelSelect.value);
        const price = parseFloat(document.getElementById('bulk-price-input').value);
        try {
          const res = await ApiClient.bulkUpdatePrices({ fuel_type_id: fuelId, price });
          alert(res.message);
        } catch (err) {
          alert('Narxni yangilashda xatolik: ' + err.message);
        }
      };
    } catch (e) {
      console.warn(e);
    }
  }

  async loadEV() {
    const list = document.getElementById('ev-control-list');
    if (!list) return;
    const stations = await ApiClient.getStations({ only_ev: true });
    list.innerHTML = stations.map(st => `
      <div class="admin-ev-card">
        <h4>${st.name}</h4>
        <p class="text-muted">${st.address}</p>
        ${st.chargers.map(c => `
          <div class="charger-row">
            <span><b>${c.charger_type}</b> (${c.power_kw} kW)</span>
            <span>Portlar: ${c.available_chargers} / ${c.total_chargers}</span>
            <span>Narx: ${c.price_per_kwh} so'm/kWh</span>
            <button class="btn-sm btn-ev-toggle" data-id="${c.id}" data-status="${c.status}">
              ${c.status === 'available' ? '✅ Faol' : '⚠️ Ta\'mirda'}
            </button>
          </div>
        `).join('')}
      </div>
    `).join('');
  }

  async loadReports() {
    const tbody = document.getElementById('reports-table-body');
    if (!tbody) return;
    const reports = await ApiClient.request('/reports');
    tbody.innerHTML = reports.map(r => `
      <tr>
        <td>#${r.id}</td>
        <td><b>${r.station_name}</b></td>
        <td><span class="badge badge-warn">${r.report_type}</span></td>
        <td>${r.description || '-'}</td>
        <td>${r.user_email}</td>
        <td>${r.status}</td>
        <td>
          <button class="btn-sm btn-resolve" data-id="${r.id}">Hal qilindi</button>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.btn-resolve').forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute('data-id');
        await ApiClient.request(`/reports/${id}/status`, { method: 'PUT', body: JSON.stringify({ status: 'resolved' }) });
        this.loadReports();
      };
    });
  }

  async loadAlerts() {
    const list = document.getElementById('alerts-feed');
    if (!list) return;
    const alerts = await ApiClient.getAlerts();
    list.innerHTML = alerts.map(a => `
      <div class="alert-card alert-${a.severity.toLowerCase()}">
        <div class="alert-head">
          <b>[${a.severity}] ${a.title}</b>
          <button class="btn-sm btn-dismiss-alert" data-id="${a.id}">Yopish</button>
        </div>
        <p>${a.message}</p>
        <small class="text-muted">${new Date(a.created_at).toLocaleString()}</small>
      </div>
    `).join('');

    list.querySelectorAll('.btn-dismiss-alert').forEach(btn => {
      btn.onclick = async () => {
        const id = btn.getAttribute('data-id');
        await ApiClient.dismissAlert(id);
        this.loadAlerts();
      };
    });
  }

  async loadAudit() {
    const tbody = document.getElementById('audit-table-body');
    if (!tbody) return;
    const logs = await ApiClient.getAuditLogs(30);
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>${new Date(l.created_at).toLocaleTimeString()}</td>
        <td><b>${l.user_email}</b></td>
        <td><span class="badge badge-blue">${l.action}</span></td>
        <td>${l.entity} (#${l.entity_id || '-'})</td>
        <td><pre class="json-snippet">${JSON.stringify(l.new_values)}</pre></td>
      </tr>
    `).join('');
  }

  async loadUsers() {
    const tbody = document.getElementById('users-table-body');
    if (!tbody) return;
    const users = await ApiClient.getUsers();
    tbody.innerHTML = users.map(u => `
      <tr>
        <td>#${u.id}</td>
        <td><b>${u.name}</b></td>
        <td>${u.email}</td>
        <td>${u.phone || '-'}</td>
        <td><span class="badge badge-purple">${u.role}</span></td>
        <td>
          <select class="role-selector" data-id="${u.id}">
            <option value="user" ${u.role === 'user' ? 'selected' : ''}>User</option>
            <option value="station_manager" ${u.role === 'station_manager' ? 'selected' : ''}>Manager</option>
            <option value="moderator" ${u.role === 'moderator' ? 'selected' : ''}>Moderator</option>
            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Admin</option>
            <option value="super_admin" ${u.role === 'super_admin' ? 'selected' : ''}>Super Admin</option>
          </select>
        </td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.role-selector').forEach(sel => {
      sel.onchange = async () => {
        const uid = sel.getAttribute('data-id');
        await ApiClient.updateUserRole(uid, sel.value);
        alert(`Foydalanuvchi roli o'zgartirildi: ${sel.value}`);
      };
    });
  }

  setupModals() {
    // Add station modal
    const addBtn = document.getElementById('btn-add-station');
    const modal = document.getElementById('station-form-modal');
    if (addBtn && modal) {
      addBtn.onclick = () => {
        document.getElementById('station-form').reset();
        document.getElementById('station-form-id').value = '';
        modal.classList.remove('hidden');
      };
    }

    const form = document.getElementById('station-form');
    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const id = document.getElementById('station-form-id').value;
        const data = {
          name: document.getElementById('form-st-name').value,
          brand: document.getElementById('form-st-brand').value,
          city: document.getElementById('form-st-city').value,
          address: document.getElementById('form-st-address').value,
          latitude: parseFloat(document.getElementById('form-st-lat').value),
          longitude: parseFloat(document.getElementById('form-st-lon').value),
          working_hours: document.getElementById('form-st-hours').value,
          is_open: document.getElementById('form-st-open').checked
        };

        try {
          if (id) {
            await ApiClient.updateStation(parseInt(id), data);
            alert("Zapravka ma'lumotlari yangilandi!");
          } else {
            await ApiClient.createStation(data);
            alert("Yangi zapravka yaratildi!");
          }
          modal.classList.add('hidden');
          this.loadStations();
        } catch (err) {
          alert('Xatolik: ' + err.message);
        }
      };
    }

    document.querySelectorAll('.admin-modal-close').forEach(btn => {
      btn.onclick = () => btn.closest('.modal-overlay').classList.add('hidden');
    });
  }

  openEditStationModal(id) {
    const st = this.stations.find(s => s.id === id);
    if (!st) return;
    document.getElementById('station-form-id').value = st.id;
    document.getElementById('form-st-name').value = st.name;
    document.getElementById('form-st-brand').value = st.brand || '';
    document.getElementById('form-st-city').value = st.city;
    document.getElementById('form-st-address').value = st.address;
    document.getElementById('form-st-lat').value = st.latitude;
    document.getElementById('form-st-lon').value = st.longitude;
    document.getElementById('form-st-hours').value = st.working_hours || '24/7';
    document.getElementById('form-st-open').checked = st.is_open;
    document.getElementById('station-form-modal').classList.remove('hidden');
  }

  async deleteStation(id) {
    if (confirm(`Rostdan ham #${id} zapravkani o'chirmoqchimisiz?`)) {
      try {
        await ApiClient.deleteStation(id);
        alert("Zapravka o'chirildi!");
        this.loadStations();
      } catch (err) {
        alert('Xatolik: ' + err.message);
      }
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  const admin = new AdminApp();
  admin.init();
});
