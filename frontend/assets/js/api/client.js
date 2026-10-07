const BASE_URL = '/api';

export class ApiClient {
  static getToken() {
    return localStorage.getItem('smartfuel_token');
  }

  static setToken(token) {
    if (token) {
      localStorage.setItem('smartfuel_token', token);
    } else {
      localStorage.removeItem('smartfuel_token');
    }
  }

  static getUser() {
    const u = localStorage.getItem('smartfuel_user');
    try {
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  }

  static setUser(user) {
    if (user) {
      localStorage.setItem('smartfuel_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('smartfuel_user');
    }
  }

  static async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        ...options,
        headers
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // Stations
  static async getStations(params = {}) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        query.append(k, v);
      }
    });
    return this.request(`/stations?${query.toString()}`);
  }

  static async getStationDetail(id, userLat, userLon) {
    const query = new URLSearchParams();
    if (userLat) query.append('user_lat', userLat);
    if (userLon) query.append('user_lon', userLon);
    return this.request(`/stations/${id}?${query.toString()}`);
  }

  static async getBestOption(fuelCode = 'cng', userLat = 41.311081, userLon = 69.240562, lang = 'uz') {
    return this.request(`/stations/recommend/best?fuel_code=${fuelCode}&user_lat=${userLat}&user_lon=${userLon}&lang=${lang}`);
  }

  static async getRoute(startLat, startLon, endLat, endLon) {
    return this.request(`/routes?start_lat=${startLat}&start_lon=${startLon}&end_lat=${endLat}&end_lon=${endLon}`);
  }

  // AI Assistant
  static async askAI(message, userLat, userLon, history = [], lang = 'uz') {
    return this.request('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        user_location: { latitude: userLat, longitude: userLon },
        history,
        lang
      })
    });
  }

  // Analytics
  static async getAnalyticsSummary() {
    return this.request('/analytics/overview-summary');
  }

  static async getPriceTrends(period = '30d') {
    return this.request(`/analytics/price-trends?period=${period}`);
  }

  // Reviews
  static async getReviews(stationId) {
    return this.request(`/reviews/station/${stationId}`);
  }

  static async addReview(stationId, data) {
    return this.request(`/reviews/station/${stationId}`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Reports
  static async submitReport(data) {
    return this.request('/reports', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Favorites
  static async getFavorites() {
    return this.request('/favorites');
  }

  static async addFavorite(stationId) {
    return this.request(`/favorites/${stationId}`, { method: 'POST' });
  }

  static async removeFavorite(stationId) {
    return this.request(`/favorites/${stationId}`, { method: 'DELETE' });
  }

  // Auth
  static async login(email, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    this.setToken(data.access_token);
    this.setUser(data.user);
    return data;
  }

  static async register(name, email, password, phone) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password, phone })
    });
    this.setToken(data.access_token);
    this.setUser(data.user);
    return data;
  }

  static logout() {
    this.setToken(null);
    this.setUser(null);
  }

  // Admin Portal
  static async getAdminOverview() {
    return this.request('/admin/overview');
  }

  static async getAuditLogs(limit = 50) {
    return this.request(`/admin/audit-logs?limit=${limit}`);
  }

  static async getAlerts(onlyActive = true) {
    return this.request(`/admin/alerts?only_active=${onlyActive}`);
  }

  static async dismissAlert(id) {
    return this.request(`/admin/alerts/${id}/dismiss`, { method: 'POST' });
  }

  static async createStation(data) {
    return this.request('/stations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  static async updateStation(id, data) {
    return this.request(`/stations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static async deleteStation(id) {
    return this.request(`/stations/${id}`, { method: 'DELETE' });
  }

  static async updateCNG(stationId, data) {
    return this.request(`/cng/update/${stationId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static async updateLPG(stationId, data) {
    return this.request(`/lpg/update/${stationId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static async bulkUpdatePrices(data) {
    return this.request('/prices/bulk-update', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  static async updateCharger(chargerId, data) {
    return this.request(`/chargers/${chargerId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  static async getFuelTypes() {
    return this.request('/fuels/types');
  }

  static async getUsers() {
    return this.request('/admin/users');
  }

  static async updateUserRole(userId, role) {
    return this.request(`/admin/users/${userId}/role?role=${role}`, { method: 'PUT' });
  }
}
