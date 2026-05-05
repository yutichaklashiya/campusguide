// ============================================================
// CHARUSAT Campus Map Navigation (Leaflet + OpenStreetMap)
// Simple map with start/end location markers + live tracking
// ============================================================

// ---------- Fixed CHARUSAT campus locations (destinations) ----------
const charusatLocations = {
  "Iceberg": { lat: 22.601636, lng: 72.820389 },
  "CSPIT": { lat: 22.600379, lng: 72.819418 },
  "DEPSTAR": { lat: 22.600306, lng: 72.820168 },
  "RPCP (Pharmacy)": { lat: 22.599540, lng: 72.819968 },
  "PDPIAS": { lat: 22.601572, lng: 72.819314 },
  "Library": { lat: 22.600129, lng: 72.820120 },
  "ARIP": { lat: 22.5972, lng: 72.8335 },
  "Admin Building": { lat: 22.599394, lng: 72.820629 },
  "Girls Hostel": { lat: 22.5945, lng: 72.8340 },
  "CMPICA": { lat: 22.603446, lng: 72.818564 },
  "Main Gate": { lat: 22.598143, lng: 72.821536 }
};

// ---------- CHARUSAT campus center (default fallback) ----------
const CHARUSAT_CENTER = [22.6000, 72.8200];

// ---------- State ----------
let leafletMap = null;
let routeLayer = null;
let userLatLng = null;
let mapInitialized = false;
let eagleMarker = null;
let accuracyCircle = null;
let liveWatchId = null;
let currentDestination = null;
let isNavigating = false;

// ---------- Eagle mascot icon ----------
function createEagleIcon() {
  return L.divIcon({
    className: "eagle-marker",
    html: '<img src="/static/images/eagle_marker.png" class="eagle-img" alt="You">',
    iconSize: [52, 52],
    iconAnchor: [26, 26]
  });
}

// ---------- Campus location icon ----------
function createLocationIcon() {
  return L.divIcon({
    className: "campus-marker",
    html: '<div class="campus-marker-dot"></div>',
    iconSize: [18, 18],
    iconAnchor: [9, 9]
  });
}

function createStartIcon() {
  return L.icon({
    iconUrl: "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png",
    iconRetinaUrl: "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon-2x.png",
    shadowUrl: "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
  });
}

function createEndIcon() {
  return L.icon({
    iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
    shadowUrl: "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
  });
}

// ---------- Helpers ----------
function showMapStatus(msg, isError) {
  const el = document.getElementById("mapStatus");
  if (!el) return;
  el.textContent = msg;
  el.style.color = isError ? "#ef4444" : "#16a34a";
  if (msg && !isNavigating) {
    setTimeout(() => { if (el.textContent === msg) el.textContent = ""; }, 8000);
  }
}

// Distance between two lat/lng in meters
function distanceBetween(lat1, lng1, lat2, lng2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// ---------- Populate destination dropdown ----------
function populateDestinations() {
  const select = document.getElementById("mapEndPoint");
  if (!select) return;
  while (select.options.length > 1) select.remove(1);
  Object.keys(charusatLocations).sort().forEach(name => {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    select.appendChild(opt);
  });
}

// ---------- Get user GPS (one-time) ----------
function fetchUserLocation() {
  return new Promise((resolve, reject) => {
    // If live tracking already has a position, use it immediately
    if (userLatLng && userLatLng.lat && userLatLng.lng) {
      resolve(userLatLng);
      return;
    }

    if (!navigator.geolocation) {
      reject(new Error("Geolocation is not supported by your browser."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLatLng = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        resolve(userLatLng);
      },
      (err) => {
        console.warn("getCurrentPosition error:", err.code, err.message);
        if (err.code === 1) {
          reject(new Error("Location access denied. Please allow location permission in your browser settings."));
        } else if (err.code === 2) {
          reject(new Error("Location unavailable. Please check your device's GPS/location settings."));
        } else {
          reject(new Error("Location request timed out. Please try again or select a campus starting point."));
        }
      },
      { enableHighAccuracy: true, timeout: 20000, maximumAge: 30000 }
    );
  });
}

// ---------- Smoothly animate marker to new position ----------
function smoothMoveMarker(marker, newLatLng, duration) {
  if (!marker) return;
  const start = marker.getLatLng();
  const startTime = performance.now();

  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-in-out
    const ease = progress < 0.5
      ? 2 * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 2) / 2;

    const lat = start.lat + (newLatLng.lat - start.lat) * ease;
    const lng = start.lng + (newLatLng.lng - start.lng) * ease;

    marker.setLatLng([lat, lng]);

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  }

  requestAnimationFrame(animate);
}

// ---------- Start live GPS tracking ----------
function startLiveTracking() {
  if (liveWatchId !== null) return; // already tracking

  if (!navigator.geolocation) {
    showMapStatus("Geolocation not supported.", true);
    return;
  }

  liveWatchId = navigator.geolocation.watchPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      const accuracy = position.coords.accuracy; // in meters
      userLatLng = { lat, lng };

      if (!leafletMap) return;

      // Update or create eagle marker
      if (eagleMarker) {
        smoothMoveMarker(eagleMarker, { lat, lng }, 800);
      } else {
        eagleMarker = L.marker([lat, lng], {
          icon: createEagleIcon(),
          zIndexOffset: 1000
        }).addTo(leafletMap).bindPopup("📍 You are here");
      }

      // Show accuracy circle around the eagle
      if (accuracyCircle) {
        accuracyCircle.setLatLng([lat, lng]);
        accuracyCircle.setRadius(accuracy);
      } else {
        accuracyCircle = L.circle([lat, lng], {
          radius: accuracy,
          color: "#4a6cf7",
          fillColor: "#4a6cf7",
          fillOpacity: 0.1,
          weight: 1,
          opacity: 0.3
        }).addTo(leafletMap);
      }

      // Show accuracy info (only when not navigating)
      if (!isNavigating) {
        if (accuracy > 100) {
          showMapStatus("📍 GPS accuracy: ~" + Math.round(accuracy) + "m (low — try on mobile for better accuracy)", true);
        } else {
          showMapStatus("📍 GPS accuracy: ~" + Math.round(accuracy) + "m", false);
        }
      }

      // Keep map centered on user during navigation
      if (isNavigating) {
        leafletMap.panTo([lat, lng], { animate: true, duration: 0.8 });

        // Check if user reached destination
        if (currentDestination) {
          const dist = distanceBetween(lat, lng, currentDestination.lat, currentDestination.lng);
          if (dist < 15) {
            showMapStatus("🎉 You have arrived at your destination!", false);
            isNavigating = false;
            currentDestination = null;
          } else {
            const distText = dist < 1000
              ? Math.round(dist) + " m"
              : (dist / 1000).toFixed(2) + " km";
            showMapStatus("🚶 " + distText + " remaining to destination", false);
          }
        }
      }
    },
    (err) => {
      console.warn("GPS watch error:", err.code, err.message);
      if (err.code === 1) {
        showMapStatus("❌ Location permission denied. Please allow GPS in browser settings.", true);
      } else if (err.code === 2) {
        showMapStatus("❌ GPS unavailable. Try on a mobile phone for better accuracy.", true);
      }
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 }
  );
}

// ---------- Stop live GPS tracking ----------
function stopLiveTracking() {
  if (liveWatchId !== null) {
    navigator.geolocation.clearWatch(liveWatchId);
    liveWatchId = null;
  }
  isNavigating = false;
  currentDestination = null;
}

// ---------- Initialize Leaflet Map ----------
function initMap() {
  if (mapInitialized && leafletMap) return;

  const mapDiv = document.getElementById("campusMap");
  if (!mapDiv) return;

  // Use user's current location if available, otherwise CHARUSAT center
  const centre = (userLatLng && userLatLng.lat && userLatLng.lng)
    ? [userLatLng.lat, userLatLng.lng]
    : CHARUSAT_CENTER;

  leafletMap = L.map(mapDiv, {
    center: centre,
    zoom: 17,
    minZoom: 3,
    maxZoom: 19
  });

  // OpenStreetMap tiles
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19
  }).addTo(leafletMap);

  // Add markers for all campus locations
  Object.entries(charusatLocations).forEach(([name, pos]) => {
    const marker = L.marker([pos.lat, pos.lng], { icon: createLocationIcon() })
      .addTo(leafletMap)
      .bindPopup("<strong>" + name + "</strong>");
    marker.bindTooltip(name, {
      permanent: false,
      direction: "top",
      offset: [0, -10],
      className: "campus-tooltip"
    });
  });

  mapInitialized = true;

  // Start live tracking immediately
  startLiveTracking();

  // Once GPS arrives, center map on user's actual location
  fetchUserLocation().then(loc => {
    if (leafletMap && loc) {
      leafletMap.setView([loc.lat, loc.lng], 17, { animate: true });
    }
  }).catch(() => {
    // GPS not available — stay on CHARUSAT center
    showMapStatus("📍 GPS not available. Please select a starting point manually.", false);
  });
}

// ---------- Clear previous route ----------
function clearRoute() {
  if (routeLayer) {
    leafletMap.removeLayer(routeLayer);
    routeLayer = null;
  }
  leafletMap.eachLayer(layer => {
    if (layer._isRouteMarker) {
      leafletMap.removeLayer(layer);
    }
  });
}

// ---------- Get directions — show direct path on map ----------
function getDirections() {
  if (!leafletMap) {
    showMapStatus("Map not ready. Please wait.", true);
    return;
  }

  const startInput = document.getElementById("mapStartPoint");
  const endSelect = document.getElementById("mapEndPoint");

  if (!endSelect || !endSelect.value) {
    showMapStatus("Please select a destination.", true);
    return;
  }

  const destination = charusatLocations[endSelect.value];
  if (!destination) {
    showMapStatus("Unknown destination.", true);
    return;
  }

  const startValue = (startInput.value || "").trim();
  let originPromise;

  if (startValue === "" || startValue.toLowerCase() === "current location") {
    originPromise = fetchUserLocation();
  } else {
    const match = Object.keys(charusatLocations).find(
      k => k.toLowerCase() === startValue.toLowerCase()
    );
    if (match) {
      originPromise = Promise.resolve(charusatLocations[match]);
    } else {
      showMapStatus("Starting point not recognized. Use 'Current Location' or a campus location name.", true);
      return;
    }
  }

  showMapStatus("Getting directions...", false);

  originPromise.then(origin => {
    if (!origin) return;

    clearRoute();

// Use OSRM free routing API to get road-following route
    const osrmUrl = `https://router.project-osrm.org/route/v1/foot/${origin.lng},${origin.lat};${destination.lng},${destination.lat}?overview=full&geometries=geojson&steps=true`;

    fetch(osrmUrl)
      .then(res => res.json())
      .then(data => {
        if (data.code !== "Ok" || !data.routes || !data.routes.length) {
          // Fallback: draw straight red line if OSRM fails
          drawStraightRoute(origin, destination, endSelect.value);
          return;
        }
// No road-following route drawn; show only start/end markers
// Add start marker (green)
const startLabel = (startValue.toLowerCase() === "current location" || startValue === "")
  ? "Your Location" : startValue;
const startM = L.marker([origin.lat, origin.lng], { icon: createStartIcon() })
  .addTo(leafletMap)
  .bindPopup("🟢 " + startLabel);
startM._isRouteMarker = true;

// Add end marker (red)
const endM = L.marker([destination.lat, destination.lng], { icon: createEndIcon() })
  .addTo(leafletMap)
  .bindPopup("🔴 " + endSelect.value);
endM._isRouteMarker = true;

// Fit map to show both markers
const group = new L.featureGroup([startM, endM]);
leafletMap.fitBounds(group.getBounds(), { padding: [60, 60] });

// Show straight-line distance
const dist = distanceBetween(origin.lat, origin.lng, destination.lat, destination.lng);
const distText = dist < 1000 ? Math.round(dist) + " m" : (dist / 1000).toFixed(2) + " km";
const walkMin = Math.max(1, Math.ceil(dist / 80));
showMapStatus(`🚶 ${distText} · ~${walkMin} min walk to ${endSelect.value}`, false);

        // Enable live navigation mode
        isNavigating = true;
        currentDestination = { lat: destination.lat, lng: destination.lng };
        startLiveTracking();
      })
      .catch(() => {
        // If OSRM fails, inform the user and do not draw a route
        showMapStatus('🚫 Unable to fetch route. Please try again later.', true);
      });

  }).catch(err => {
    showMapStatus(err.message || "Location error.", true);
  });
}

// ---------- Toggle map panel ----------
function toggleMapPanel() {
  const overlay = document.getElementById("mapOverlay");
  if (!overlay) return;

  const isOpen = overlay.classList.contains("open");
  if (isOpen) {
    overlay.classList.remove("open");
    stopLiveTracking();
  } else {
    overlay.classList.add("open");
    populateDestinations();
    setTimeout(() => {
      initMap();
      if (leafletMap) leafletMap.invalidateSize();
    }, 350);
  }
}

// ---------- Close map panel ----------
function closeMapPanel() {
  const overlay = document.getElementById("mapOverlay");
  if (overlay) overlay.classList.remove("open");
  stopLiveTracking();
}

// ---------- Populate start-point suggestions ----------
function populateStartSuggestions() {
  const datalist = document.getElementById("startPointSuggestions");
  if (!datalist) return;
  datalist.innerHTML = "";
  const currentOpt = document.createElement("option");
  currentOpt.value = "Current Location";
  datalist.appendChild(currentOpt);
  Object.keys(charusatLocations).sort().forEach(name => {
    const opt = document.createElement("option");
    opt.value = name;
    datalist.appendChild(opt);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  populateStartSuggestions();
});
