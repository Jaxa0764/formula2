import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export class MapManager {
  constructor(elementId, options = {}) {
    this.elementId = elementId;
    this.onStationClick = options.onStationClick || (() => {});
    this.map = null;
    this.markersGroup = null;
    this.routePolyline = null;
    this.userMarker = null;
    this.userLocation = { lat: 41.311081, lng: 69.240562 }; // Default Tashkent Center
    this.init();
  }

  init() {
    this.map = L.map(this.elementId, {
      center: [this.userLocation.lat, this.userLocation.lng],
      zoom: 13,
      zoomControl: false
    });

    // Custom positioned zoom control
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // Dark Matter tile layer for futuristic fintech/EV look
    this.darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>, &copy; <a href="https://openstreetmap.org">OSM</a>',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(this.map);

    // Layer group for markers
    this.markersGroup = L.layerGroup().addTo(this.map);

    // Add user marker
    this.updateUserMarker(this.userLocation.lat, this.userLocation.lng);
  }

  updateUserMarker(lat, lng) {
    this.userLocation = { lat, lng };
    if (this.userMarker) {
      this.userMarker.setLatLng([lat, lng]);
    } else {
      const userIcon = L.divIcon({
        className: 'user-location-marker',
        html: `
          <div class="user-pulse-container">
            <div class="user-pulse-ring"></div>
            <div class="user-pulse-core"></div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });
      this.userMarker = L.marker([lat, lng], { icon: userIcon, zIndexOffset: 1000 }).addTo(this.map);
    }
  }

  createMarkerIcon(station) {
    let mainColor = '#00F2FE'; // Cyan default
    let iconSvg = '';
    let badgeText = '';

    const hasCng = station.cng_data && station.cng_data.is_available;
    const hasEv = station.chargers && station.chargers.length > 0;
    const hasLpg = station.lpg_data && station.lpg_data.is_available;
    const isClosed = !station.is_open;

    if (isClosed) {
      mainColor = '#EF4444'; // Red
      badgeText = 'Yopiq';
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>`;
    } else if (hasCng && station.cng_data.pressure_bar < 140) {
      mainColor = '#F59E0B'; // Low pressure warning
      badgeText = `${station.cng_data.pressure_bar}b`;
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4"/><circle cx="12" cy="12" r="7"/></svg>`;
    } else if (hasCng && hasEv) {
      mainColor = '#10B981'; // Green & Electric Hybrid
      badgeText = 'CNG+EV';
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`;
    } else if (hasEv) {
      mainColor = '#3B82F6'; // EV Blue
      const avail = station.chargers[0]?.available_chargers || 0;
      badgeText = `${avail} port`;
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`;
    } else if (hasCng) {
      mainColor = '#10B981'; // CNG Emerald
      badgeText = `${station.cng_data.pressure_bar}b`;
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4.5 16.5c-1.5 1.26-2 3-2 4.5 2 0 3.5-.5 4.5-2"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/></svg>`;
    } else if (hasLpg) {
      mainColor = '#EC4899'; // LPG Pink/Orange
      badgeText = 'LPG';
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>`;
    } else {
      mainColor = '#4FACFE'; // Gasoline Fuel
      badgeText = station.fuels[0]?.price ? `${Math.round(station.fuels[0].price / 1000)}k` : '⛽';
      iconSvg = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M3 22h12M4 9h10M4 4h10a2 2 0 0 1 2 2v16H4V4z"/><path d="M16 8h2a2 2 0 0 1 2 2v7a2 2 0 0 0 2 2v0a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L21 6"/></svg>`;
    }

    return L.divIcon({
      className: 'custom-station-pin',
      html: `
        <div class="station-pin-wrapper" style="--pin-color: ${mainColor}">
          <div class="pin-glow"></div>
          <div class="pin-body">
            <span class="pin-icon">${iconSvg}</span>
            <span class="pin-badge">${badgeText}</span>
          </div>
          <div class="pin-tail"></div>
        </div>
      `,
      iconSize: [46, 52],
      iconAnchor: [23, 50],
      popupAnchor: [0, -48]
    });
  }

  renderStations(stations) {
    this.markersGroup.clearLayers();

    stations.forEach((st) => {
      const icon = this.createMarkerIcon(st);
      const marker = L.marker([st.latitude, st.longitude], { icon });

      // Create quick interactive popup
      const distInfo = st.distance_km ? `<span class="badge badge-dist">${st.distance_km} km</span>` : '';
      let priceInfo = '';
      if (st.cng_data && st.cng_data.is_available) {
        priceInfo = `<span class="tag tag-cng">CNG: ${st.cng_data.pressure_bar} bar | ${st.cng_data.price} so'm</span>`;
      } else if (st.fuels && st.fuels.length > 0) {
        const f = st.fuels[0];
        priceInfo = `<span class="tag tag-fuel">${f.fuel_name}: ${f.price} so'm</span>`;
      } else if (st.chargers && st.chargers.length > 0) {
        priceInfo = `<span class="tag tag-ev">EV: ${st.chargers[0].power_kw}kW | ${st.chargers[0].available_chargers} bo'sh</span>`;
      }

      const popupHtml = `
        <div class="map-popup-card">
          <div class="popup-header">
            <h4>${st.name}</h4>
            ${distInfo}
          </div>
          <p class="popup-address">${st.address}</p>
          <div class="popup-meta">
            ${priceInfo}
            <span class="rating-badge">⭐ ${st.rating}</span>
          </div>
          <div class="popup-actions">
            <button class="btn-popup-open" data-station-id="${st.id}">Batafsil ma'lumot</button>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml, {
        className: 'custom-leaflet-popup',
        maxWidth: 300,
        closeButton: false
      });

      marker.on('click', () => {
        this.onStationClick(st);
      });

      this.markersGroup.addLayer(marker);
    });

    // Delegate popup button click
    this.map.on('popupopen', (e) => {
      const btn = e.popup.getElement().querySelector('.btn-popup-open');
      if (btn) {
        btn.onclick = () => {
          const id = parseInt(btn.getAttribute('data-station-id'));
          const target = stations.find(s => s.id === id);
          if (target) this.onStationClick(target);
        };
      }
    });
  }

  flyToStation(lat, lng, zoom = 15) {
    this.map.flyTo([lat, lng], zoom, {
      duration: 1.2,
      easeLinearity: 0.25
    });
  }

  drawRoute(coordinates) {
    this.clearRoute();
    if (!coordinates || coordinates.length === 0) return;

    this.routePolyline = L.polyline(coordinates, {
      color: '#00F2FE',
      weight: 5,
      opacity: 0.9,
      lineCap: 'round',
      lineJoin: 'round',
      dashArray: null
    }).addTo(this.map);

    // Subtle pulsating glow layer underneath
    this.routeGlow = L.polyline(coordinates, {
      color: '#4FACFE',
      weight: 10,
      opacity: 0.35,
      lineCap: 'round',
      lineJoin: 'round'
    }).addTo(this.map);

    this.map.fitBounds(this.routePolyline.getBounds(), { padding: [50, 50] });
  }

  clearRoute() {
    if (this.routePolyline) {
      this.map.removeLayer(this.routePolyline);
      this.routePolyline = null;
    }
    if (this.routeGlow) {
      this.map.removeLayer(this.routeGlow);
      this.routeGlow = null;
    }
  }

  setCity(cityName) {
    const cities = {
      tashkent: [41.311081, 69.240562],
      samarkand: [39.654200, 66.975800],
      bukhara: [39.774700, 64.428600],
      fergana: [40.386400, 71.786500],
      andijan: [40.782100, 72.344200],
      namangan: [41.002300, 71.672100]
    };

    const target = cities[cityName.toLowerCase()];
    if (target) {
      this.map.flyTo(target, 12, { duration: 1.5 });
      this.updateUserMarker(target[0], target[1]);
    }
  }
}
