// Dynamic API URL - use current hostname for cross-device access
// For localhost development, use localhost:8000
// For production or network access, use the server's IP/hostname
const getApiBaseUrl = () => {
  const hostname = window.location.hostname;
  // If accessing from localhost, use localhost:8000
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000';
  }
  // Otherwise, use the same hostname with port 8000
  return `http://${hostname}:8000`;
};
const API_BASE_URL = getApiBaseUrl();
const STORAGE_KEY = "ParkinglySession";
const PRICING = {
  firstHour: 10000,
  extraHour: 5000,
};

// Hanya izinkan slot nomor 1 dan 2 untuk bisa dibooking
function isBookableSpot(spot) {
  if (!spot || !spot.code) return false;
  const numeric = parseInt(String(spot.code).replace(/\D/g, ""), 10);
  return numeric === 1 || numeric === 2;
}

const state = {
  token: null,
  user: null,
  role: null,
  activeBooking: null,
  countdownInterval: null,
  durationInterval: null,
  selectedSpot: null,
  cachedSpots: [],
};

const elements = {
  headerActions: document.getElementById("headerActions"),
  activeUser: document.getElementById("activeUser"),
  logoutBtn: document.getElementById("logoutBtn"),
  userView: document.getElementById("userView"),
  adminView: document.getElementById("adminView"),
  userNavButtons: document.querySelectorAll("#userSidebar [data-view]"),
  adminNavButtons: document.querySelectorAll("#adminSidebar [data-view]"),
  spotList: document.getElementById("spotList"),
  parkingGrid: document.getElementById("parkingGrid"),
  spotFilter: document.getElementById("spotFilter"),
  adminSpotList: document.getElementById("adminSpotList"),
  bookingForm: document.getElementById("bookingForm"),
  selectedSpotId: document.getElementById("selectedSpotId"),
  selectedSpotName: document.getElementById("selectedSpotName"),
  selectedSpotMeta: document.getElementById("selectedSpotMeta"),
  activeBooking: document.getElementById("activeBooking"),
  qrBox: document.getElementById("qrBox"),
  bookingFields: {
    bookingId: document.querySelector("[data-field='bookingId']"),
    status: document.querySelector("[data-field='bookingStatus']"),
    qrCode: document.querySelector("[data-field='qrCode']"),
    countdown: document.querySelector("[data-field='countdown']"),
    duration: document.querySelector("[data-field='duration']"),
    cost: document.querySelector("[data-field='cost']"),
  },
  timelineSteps: {
    qr: document.querySelector("[data-step='qr']"),
    scan: document.querySelector("[data-step='scan']"),
  },
  qrExpiredHint: document.getElementById("qrExpiredHint"),
  walletBalance: document.getElementById("walletBalance"),
  topupForm: document.getElementById("topupForm"),
  historyTable: document.getElementById("historyTable"),
  refreshHistory: document.getElementById("refreshHistory"),
  refreshSpots: document.getElementById("refreshSpots"),
  adminRefreshSpots: document.getElementById("adminRefreshSpots"),
  adminScanForm: document.getElementById("adminScanForm"),
  adminScanResult: document.getElementById("adminScanResult"),
  reportFields: document.querySelectorAll("[data-report]"),
  cancelBooking: document.getElementById("cancelBooking"),
  heroSlots: document.getElementById("heroSlots"),
  goToBooking: document.getElementById("goToBooking"),
  goToBookingSelected: document.getElementById("goToBookingSelected"),
  goToBookingPageBtn: document.getElementById("goToBookingPageBtn"),
  selectedSlotInfo: document.getElementById("selectedSlotInfo"),
};

const historyTemplate = document.getElementById("historyTemplate");

// ---------- API WRAPPER ----------
async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const config = {
    ...options,
    headers,
  };

  if (options.body && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  }

  const res = await fetch(`${API_BASE_URL}${path}`, config);
  if (!res.ok) {
    const error = await res.json().catch(() => ({}));
    // Handle both FastAPI (detail) and Express (message) error formats
    const errorMessage = error.detail || error.message || "Request failed";
    throw new Error(errorMessage);
  }
  return res.json();
}

function persistSession(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function restoreSession() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
  state.token = null;
  state.user = null;
  state.role = null;
}

function switchUserPanel(target) {
  document
    .querySelectorAll("#userView .view")
    .forEach((view) => view.classList.toggle("visible", view.dataset.panel === target));
  elements.userNavButtons.forEach((button) =>
    button.classList.toggle("active", button.dataset.view === target),
  );
}

function switchAdminPanel(target) {
  document
    .querySelectorAll("#adminView .view")
    .forEach((view) => view.classList.toggle("visible", view.dataset.panel === target));
  elements.adminNavButtons.forEach((button) =>
    button.classList.toggle("active", button.dataset.view === target),
  );
}

function setAppState(role) {
  elements.headerActions.classList.remove("hidden");
  if (role === "user") {
    elements.adminView.classList.add("hidden");
    elements.userView.classList.remove("hidden");
    switchUserPanel("map");
  } else {
    elements.userView.classList.add("hidden");
    elements.adminView.classList.remove("hidden");
    switchAdminPanel("scanner");
  }
}

function resetAppState() {
  elements.userView.classList.add("hidden");
  elements.adminView.classList.add("hidden");
  elements.headerActions.classList.add("hidden");
  elements.activeUser.textContent = "";
  clearCountdown();
  clearDurationTimer();
  state.cachedSpots = [];
  setSelectedSpot(null);
  resetLiveMetrics();
}

function renderParkingGrid(list) {
  if (!elements.parkingGrid) return;
  
  elements.parkingGrid.innerHTML = "";
  if (!list || !list.length) {
    elements.parkingGrid.innerHTML = `<div class="muted" style="grid-column: 1/-1; text-align: center; padding: 2rem;">Belum ada data.</div>`;
    return;
  }
  
  // Sort spots by code for better organization
  const sortedSpots = [...list].sort((a, b) => {
    const aNum = parseInt(a.code.replace(/\D/g, '')) || 0;
    const bNum = parseInt(b.code.replace(/\D/g, '')) || 0;
    return aNum - bNum;
  });

  sortedSpots.forEach((spot) => {
    const bookable = isBookableSpot(spot);
    const isAvailableForUser = spot.isAvailable && bookable;

    const slot = document.createElement("div");
    slot.className = `parking-slot ${isAvailableForUser ? "available" : "occupied"}`;
    slot.dataset.id = spot.id;
    slot.dataset.code = spot.code;
    
    if (state.selectedSpot?.id === spot.id) {
      slot.classList.add("selected");
    }
    
    slot.innerHTML = `
      <div class="parking-slot-code">${spot.code}</div>
      <div class="parking-slot-name">${spot.name}</div>
    `;
    
    // Hanya slot 1 dan 2 yang bisa dipilih pengguna
    if (isAvailableForUser) {
      slot.addEventListener("click", () => setSelectedSpot(spot));
    }
    
    elements.parkingGrid.appendChild(slot);
  });
}

function renderAdminSpotsGrid(list) {
  if (!elements.adminSpotList) return;
  
  elements.adminSpotList.innerHTML = "";
  if (!list || !list.length) {
    elements.adminSpotList.innerHTML = `<div class="muted" style="text-align: center; padding: 2rem;">Belum ada data.</div>`;
    return;
  }
  
  // Update statistics
  const available = list.filter((spot) => spot.isAvailable).length;
  const occupied = list.filter((spot) => !spot.isAvailable).length;
  const total = list.length;
  
  const availableCountEl = document.getElementById("adminAvailableCount");
  const occupiedCountEl = document.getElementById("adminOccupiedCount");
  const totalCountEl = document.getElementById("adminTotalCount");
  
  if (availableCountEl) availableCountEl.textContent = available;
  if (occupiedCountEl) occupiedCountEl.textContent = occupied;
  if (totalCountEl) totalCountEl.textContent = total;
  
  // Sort spots by code
  const sortedSpots = [...list].sort((a, b) => {
    const aNum = parseInt(a.code.replace(/\D/g, '')) || 0;
    const bNum = parseInt(b.code.replace(/\D/g, '')) || 0;
    return aNum - bNum;
  });
  
  sortedSpots.forEach((spot) => {
    const card = document.createElement("div");
    card.className = `admin-spot-card ${spot.isAvailable ? "available" : "occupied"}`;
    card.innerHTML = `
      <div class="admin-spot-header">
        <div class="admin-spot-name">${spot.name}</div>
        <span class="admin-spot-status ${spot.isAvailable ? "available" : "occupied"}">
          ${spot.isAvailable ? "Tersedia" : "Terisi"}
        </span>
      </div>
      <div class="admin-spot-code">Kode: ${spot.code}</div>
    `;
    elements.adminSpotList.appendChild(card);
  });
}

function renderSpots(list, targetList, includeMeta = true) {
  // Use grid layout for user view, grid for admin view
  if (targetList === elements.spotList && elements.parkingGrid) {
    renderParkingGrid(list);
    return;
  }
  
  // Use new admin grid layout
  if (targetList === elements.adminSpotList) {
    renderAdminSpotsGrid(list);
    return;
  }
  
  targetList.innerHTML = "";
  if (!list || !list.length) {
    targetList.innerHTML = `<li class="muted">Belum ada data.</li>`;
    return;
  }
  list.forEach((spot) => {
    if (!includeMeta) {
      const row = document.createElement("li");
      row.className = `spot-card ${spot.isAvailable ? "available" : "occupied"} admin`;
      row.innerHTML = `
        <div class="spot-title">
          <strong>${spot.name} (${spot.code})</strong>
          <span class="chip">${spot.isAvailable ? "Tersedia" : "Dipakai"}</span>
        </div>
        <div class="meta">Kode: ${spot.code}</div>
      `;
      targetList.appendChild(row);
      return;
    }
    const li = document.createElement("li");
    const bookable = isBookableSpot(spot);
    const isAvailableForUser = spot.isAvailable && bookable;
    li.className = `spot-card ${isAvailableForUser ? "available" : "occupied"}`;
    li.dataset.id = spot.id;
    li.innerHTML = `
      <div class="spot-title">
        <strong>${spot.name} (${spot.code})</strong>
        <span class="chip">${isAvailableForUser ? "Tersedia" : "Dipakai"}</span>
      </div>
      <div class="meta">
        Level ${spot.level} • Rp10.000 (1 jam pertama) • Rp5.000/jam berikutnya
      </div>
    `;
    if (state.selectedSpot?.id === spot.id) {
      li.classList.add("selected");
    }
    // Hanya slot 1 dan 2 yang bisa dipilih pengguna
    if (isAvailableForUser) {
      li.addEventListener("click", () => setSelectedSpot(spot));
    }
    targetList.appendChild(li);
  });
}

function filterSpots(spots) {
  if (!elements.spotFilter) return spots;
  const filter = elements.spotFilter.value;
  if (filter === "available") {
    return spots.filter((spot) => spot.isAvailable);
  }
  if (filter === "occupied") {
    return spots.filter((spot) => !spot.isAvailable);
  }
  return spots;
}

function setHeroSlots(spots) {
  if (!elements.heroSlots) return;
  const list = Array.isArray(spots) ? spots : [];
  // Hanya hitung slot yang benar-benar bisa dibooking (nomor 1 dan 2)
  const available = list.filter((spot) => spot.isAvailable && isBookableSpot(spot)).length;
  elements.heroSlots.textContent = available;
}

function setSelectedSpot(spot) {
  state.selectedSpot = spot;
  if (elements.selectedSpotId) {
    elements.selectedSpotId.value = spot?.id || "";
  }
  if (elements.selectedSpotName) {
    elements.selectedSpotName.textContent = spot
      ? `${spot.name} (${spot.code})`
      : "Belum dipilih";
  }
  if (elements.selectedSpotMeta) {
    elements.selectedSpotMeta.textContent = spot
      ? `Level ${spot.level} • Rp10.000 (1 jam pertama) • Rp5.000/jam berikutnya`
      : "Silakan pilih slot dari daftar ketersediaan di kiri.";
  }
  // Update grid selection
  if (elements.parkingGrid) {
    elements.parkingGrid.querySelectorAll(".parking-slot").forEach((slot) => {
      slot.classList.toggle("selected", Boolean(spot && slot.dataset.id === spot.id));
    });
  }
  // Update list selection (for admin view)
  if (elements.spotList) {
    elements.spotList.querySelectorAll(".spot-card").forEach((card) => {
      card.classList.toggle("selected", Boolean(spot && card.dataset.id === spot.id));
    });
  }
  // Show/hide selected slot info
  if (elements.selectedSlotInfo) {
    if (spot) {
      elements.selectedSlotInfo.classList.add("show");
      if (elements.goToBookingSelected) {
        elements.goToBookingSelected.disabled = false;
      }
    } else {
      elements.selectedSlotInfo.classList.remove("show");
      if (elements.goToBookingSelected) {
        elements.goToBookingSelected.disabled = true;
      }
    }
  }
}

function renderHistory(rows) {
  elements.historyTable.innerHTML = "";
  if (!rows || !rows.length) {
    elements.historyTable.innerHTML =
      '<tr><td colspan="6" class="empty-state"><div class="empty-icon">📭</div><p class="empty-text">Belum ada riwayat parkir</p><p class="empty-subtext">Riwayat parkir Anda akan muncul di sini</p></td></tr>';
    return;
  }
  rows.forEach((item) => {
    const node = historyTemplate.content.cloneNode(true);
    node.querySelector("[data-field='bookingId']").textContent = item.bookingId;
    node.querySelector("[data-field='spot']").textContent = item.spotName;
    node.querySelector("[data-field='start']").textContent = formatDate(item.startTime);
    node.querySelector("[data-field='end']").textContent = formatDate(item.endTime);
    
    // Format cost - show "-" if no cost (for pending/cancelled)
    const costElement = node.querySelector("[data-field='cost']");
    if (item.cost !== null && item.cost !== undefined) {
      costElement.textContent = formatCurrency(item.cost);
    } else {
      costElement.textContent = "-";
    }
    
    // Format status badge
    const statusElement = node.querySelector("[data-field='status']");
    const statusDisplay = item.statusDisplay || item.status || "Unknown";
    statusElement.textContent = statusDisplay;
    
    // Add status-specific class
    statusElement.className = "status-badge";
    if (item.status === "completed") {
      statusElement.classList.add("status-badge-completed");
    } else if (item.status === "cancelled") {
      statusElement.classList.add("status-badge-cancelled");
    } else if (item.status === "checked-in") {
      statusElement.classList.add("status-badge-checkedin");
    } else if (item.status === "pending") {
      statusElement.classList.add("status-badge-pending");
    }
    
    elements.historyTable.appendChild(node);
  });
}

function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("id-ID", { hour12: false });
}

function formatCurrency(value) {
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    minimumFractionDigits: 0,
  }).format(value || 0);
}

function formatDuration(ms) {
  const totalMinutes = Math.max(0, Math.floor(ms / (1000 * 60)));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) {
    return `${hours}j ${minutes}m`;
  }
  return `${minutes}m`;
}

function estimateCostFromMs(ms) {
  const hours = Math.max(1, Math.ceil(ms / (1000 * 60 * 60)));
  return PRICING.firstHour + Math.max(0, hours - 1) * PRICING.extraHour;
}

function setWalletBalance(amount) {
  elements.walletBalance.textContent = formatCurrency(amount);
}

function showBookingPanel(booking) {
  state.activeBooking = booking;
  if (elements.activeBooking) {
    elements.activeBooking.classList.remove("hidden");
  }
  if (elements.bookingFields.bookingId) {
    elements.bookingFields.bookingId.textContent = booking.id;
  }
  if (elements.bookingFields.status) {
    elements.bookingFields.status.textContent =
      booking.status === "pending" ? "Menunggu validasi" : "Sedang parkir";
  }
  // Show QR code for pending and checked-in status
  if ((booking.status === "pending" || booking.status === "checked-in") && booking.qr && booking.qr.token) {
    if (elements.bookingFields.qrCode) {
      elements.bookingFields.qrCode.textContent = booking.qr.token;
    }
    
    // Generate QR code image
    if (elements.qrBox && typeof QRCode !== 'undefined') {
      elements.qrBox.innerHTML = "";
      QRCode.toCanvas(elements.qrBox, booking.qr.token, {
        width: 200,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF'
        }
      }, function (error) {
        if (error) {
          console.error("QR Code generation error:", error);
          elements.qrBox.textContent = booking.qr.token.slice(0, 8).toUpperCase();
        }
      });
    } else {
      // Fallback if QRCode library not loaded
      elements.qrBox.textContent = booking.qr.token.slice(0, 8).toUpperCase();
      // Try to load QRCode library dynamically
      if (typeof QRCode === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js';
        script.onload = function() {
          if (elements.qrBox && booking.qr && booking.qr.token && (booking.status === "pending" || booking.status === "checked-in")) {
            elements.qrBox.innerHTML = "";
            QRCode.toCanvas(elements.qrBox, booking.qr.token, {
              width: 200,
              margin: 2,
              color: {
                dark: '#000000',
                light: '#FFFFFF'
              }
            });
          }
        };
        document.head.appendChild(script);
      }
    }
  } else {
    // Hide QR code for checked-in or completed status
    if (elements.qrBox) {
      elements.qrBox.innerHTML = "";
      elements.qrBox.textContent = booking.status === "checked-in" ? "QR tidak diperlukan (sudah masuk)" : "QR tidak tersedia";
    }
    if (elements.bookingFields.qrCode) {
      elements.bookingFields.qrCode.textContent = "-";
    }
  }
  
  if (elements.qrExpiredHint) {
    elements.qrExpiredHint.classList.add("hidden");
  }
  resetLiveMetrics();
  const isCheckedIn = booking.status === "checked-in";
  if (elements.cancelBooking) {
    elements.cancelBooking.classList.toggle("hidden", booking.status !== "pending");
  }
  if (elements.timelineSteps.qr && elements.timelineSteps.scan) {
    updateTimeline(booking.status, booking.qr ? booking.qr.token : null);
  }
  if (isCheckedIn) {
    startDurationTimer(booking.startTime);
    if (elements.bookingFields.countdown) {
      elements.bookingFields.countdown.textContent = "Sedang parkir";
    }
  } else if (booking.qr && booking.qr.expiresAt) {
    startCountdown(booking.qr.expiresAt);
  }
  

//===============================================================================================


  // Show button to go to booking page (for pending and checked-in status)
  if (booking.status === "pending" || booking.status === "checked-in") {
    //showGoToBookingButton();
    
    btn.style.display = "inline-block";

    const btn = elements.goToBookingPageBtn || document.getElementById("goToBookingPageBtn");
    if (!btn) return; // button not present in DOM — nothing to do

    // Ensure a click handler exists (idempotent)
    if (!btn.hasAttribute("data-listener-added")) {
      btn.addEventListener("click", () => {
        // optional: persist selected booking or state if needed
        window.location.href = "booking.html";
      });
      btn.setAttribute("data-listener-added", "true");
    }

    // Only show when there is an active booking in pending/checked-in
    // if (state.activeBooking && (state.activeBooking.status === "pending" || state.activeBooking.status === "checked-in")) {
    //   btn.style.display = "inline-block";
    // } else {
    //   btn.style.display = "none";
    // }


  } else {
    //hideGoToBookingButton();


    const btn = elements.goToBookingPageBtn || document.getElementById("goToBookingPageBtn");
    if (!btn) return;
   // btn.style.display = "none";


  }
}

function showGoToBookingButton() {
  // const btn = elements.goToBookingPageBtn || document.getElementById("goToBookingPageBtn");
  // if (!btn) return; // button not present in DOM — nothing to do

  // // Ensure a click handler exists (idempotent)
  // if (!btn.hasAttribute("data-listener-added")) {
  //   btn.addEventListener("click", () => {
  //     // optional: persist selected booking or state if needed
  //     window.location.href = "booking.html";
  //   });
  //   btn.setAttribute("data-listener-added", "true");
  // }

  // // Only show when there is an active booking in pending/checked-in
  // if (state.activeBooking && (state.activeBooking.status === "pending" || state.activeBooking.status === "checked-in")) {
  //   btn.style.display = "inline-block";
  // } else {
  //   btn.style.display = "none";
  // }
}

function hideGoToBookingButton() {
  // const btn = elements.goToBookingPageBtn || document.getElementById("goToBookingPageBtn");
  // if (!btn) return;
  // btn.style.display = "none";
}


//===============================================================================================

function hideBookingPanel() {
  state.activeBooking = null;
  if (elements.activeBooking) {
    elements.activeBooking.classList.add("hidden");
  }
  if (elements.qrExpiredHint) {
    elements.qrExpiredHint.classList.add("hidden");
  }
  hideGoToBookingButton();
  clearCountdown();
  clearDurationTimer();
  elements.bookingFields.countdown.textContent = "30:00";
  if (elements.bookingFields.status) {
    elements.bookingFields.status.textContent = "-";
  }
  if (elements.cancelBooking) {
    elements.cancelBooking.classList.add("hidden");
  }
  updateTimeline(null, null);
  resetLiveMetrics();
}

function startCountdown(expiry) {
  clearCountdown();
  clearDurationTimer();
  
  function tick() {
    const diff = new Date(expiry).getTime() - Date.now();
    if (diff <= 0) {
      // Time expired - auto cancel booking
      if (elements.bookingFields.countdown) {
        elements.bookingFields.countdown.textContent = "00:00";
      }
      if (elements.qrExpiredHint) {
        elements.qrExpiredHint.classList.remove("hidden");
        elements.qrExpiredHint.textContent = "⚠️ QR kadaluarsa, booking otomatis dibatalkan.";
      }
      clearCountdown();
      
      // Auto cancel booking
      cancelExpiredBooking();
      return;
    }
    
    const minutes = Math.floor(diff / 1000 / 60);
    const seconds = Math.floor((diff / 1000) % 60);
    const countdownText = `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    
    if (elements.bookingFields.countdown) {
      elements.bookingFields.countdown.textContent = `Waktu tersisa: ${countdownText}`;
    }
  }
  tick();
  state.countdownInterval = setInterval(tick, 1000);
}

async function cancelExpiredBooking() {
  try {
    await apiFetch("/parking/cancel", {
      method: "POST",
    });
    // Reload page or show message
    setTimeout(() => {
      window.location.reload();
    }, 2000);
  } catch (err) {
    console.error("Error canceling expired booking:", err);
  }
}

function clearCountdown() {
  if (state.countdownInterval) {
    clearInterval(state.countdownInterval);
    state.countdownInterval = null;
  }
}

function startDurationTimer(startTime) {
  if (!startTime) return;
  clearDurationTimer();
  function tick() {
    const diff = Date.now() - new Date(startTime).getTime();
    if (diff < 0) return;
    if (elements.bookingFields.duration) {
      elements.bookingFields.duration.textContent = formatDuration(diff);
    }
    if (elements.bookingFields.cost) {
      elements.bookingFields.cost.textContent = formatCurrency(estimateCostFromMs(diff));
    }
  }
  tick();
  state.durationInterval = setInterval(tick, 1000 * 30);
}

function clearDurationTimer() {
  if (state.durationInterval) {
    clearInterval(state.durationInterval);
    state.durationInterval = null;
  }
}

function resetLiveMetrics() {
  if (elements.bookingFields.duration) {
    elements.bookingFields.duration.textContent = "-";
  }
  if (elements.bookingFields.cost) {
    elements.bookingFields.cost.textContent = formatCurrency(0);
  }
}

function setReportFields(payload) {
  elements.reportFields.forEach((node) => {
    const key = node.dataset.report;
    let value = payload?.[key] ?? 0;
    if (key.includes("Revenue")) {
      value = formatCurrency(value);
    }
    node.textContent = value;
  });
}

function updateTimeline(status, qrToken) {
  const { qr, scan } = elements.timelineSteps;
  if (!qr || !scan) return;
  const qrSmall = qr.querySelector("small");
  const scanSmall = scan.querySelector("small");
  if (!status) {
    qr.classList.remove("active", "completed");
    scan.classList.remove("active", "completed");
    if (qrSmall) qrSmall.textContent = "-";
    if (scanSmall) scanSmall.textContent = "Menunggu";
    return;
  }

  qr.classList.add("active", "completed");
  if (qrSmall) {
    qrSmall.textContent = qrToken || "-";
  }
  scan.classList.toggle("active", status === "checked-in");
  scan.classList.toggle("completed", status === "checked-in");
  if (scanSmall) {
    scanSmall.textContent = status === "checked-in" ? "Selesai" : "Menunggu";
  }
}

// ---------- DATA LOADERS ----------
async function bootstrapSession(session) {
  state.token = session.token;
  state.user = session.user;
  state.role = session.role;
  setAppState(session.role);
  elements.activeUser.textContent = `${session.user.name} (${session.role})`;
  try {
    if (session.role === "user") {
      await Promise.all([loadSpots(), loadWallet(), loadHistory(), loadActiveBooking()]);
      // Show/hide booking button based on active booking after loading
      setTimeout(() => {
        if (state.activeBooking && (state.activeBooking.status === "pending" || state.activeBooking.status === "checked-in")) {
          showGoToBookingButton();
        } else {
          hideGoToBookingButton();
        }
      }, 100);
    } else {
      await Promise.all([loadAdminSpots(), loadReports()]);
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadSpots() {
  try {
    const { spots } = await apiFetch("/parking/spots");
    state.cachedSpots = spots;
    const filtered = filterSpots(spots);
    renderSpots(filtered, elements.spotList);
    const validSelection = state.selectedSpot
      ? spots.find(
          (spot) =>
            spot.id === state.selectedSpot.id &&
            spot.isAvailable &&
            isBookableSpot(spot),
        )
      : null;
    setSelectedSpot(validSelection || null);
    setHeroSlots(spots);
  } catch (err) {
    console.error("Load spots failed", err);
    if (elements.parkingGrid) {
      renderParkingGrid([]);
    } else {
      renderSpots([], elements.spotList);
    }
    setHeroSlots([]);
    setSelectedSpot(null);
  }
}

async function loadAdminSpots() {
  try {
    const { spots } = await apiFetch("/admin/spots");
    renderSpots(spots, elements.adminSpotList, false);
  } catch (err) {
    renderSpots([], elements.adminSpotList, false);
  }
}

async function loadActiveBooking() {
  try {
    const { booking } = await apiFetch("/parking/active");
    if (booking) {
      showBookingPanel(booking);
      // Show button if booking is pending or checked-in
      if (booking.status === "pending" || booking.status === "checked-in") {
        showGoToBookingButton();
      } else {
        hideGoToBookingButton();
      }
    } else {
      hideBookingPanel();
      hideGoToBookingButton(); // Hide button when no active booking
    }
    // Reload history to include all bookings
    await loadHistory();
  } catch (err) {
    hideBookingPanel();
    hideGoToBookingButton(); // Hide button on error
  }
}

async function loadWallet() {
  try {
    const { balance } = await apiFetch("/wallet");
    setWalletBalance(balance);
  } catch (err) {
    setWalletBalance(0);
  }
}

async function loadHistory() {
  try {
    const { history } = await apiFetch("/parking/history");
    renderHistory(history);
  } catch (err) {
    renderHistory([]);
  }
}

async function loadReports() {
  try {
    const { reports } = await apiFetch("/admin/reports");
    setReportFields(reports);
  } catch (err) {
    setReportFields({});
  }
}

// ---------- EVENT HANDLERS ----------
elements.userNavButtons.forEach((button) =>
  button.addEventListener("click", () => switchUserPanel(button.dataset.view)),
);

elements.adminNavButtons.forEach((button) =>
  button.addEventListener("click", () => switchAdminPanel(button.dataset.view)),
);

elements.logoutBtn.addEventListener("click", () => {
  clearSession();
  resetAppState();
  window.location.href = "login.html";
});

elements.refreshSpots.addEventListener("click", () => {
  elements.refreshSpots.classList.add("refreshing");
  loadSpots().finally(() => {
    setTimeout(() => {
      elements.refreshSpots.classList.remove("refreshing");
    }, 600); // Remove after animation completes
  });
});

elements.adminRefreshSpots.addEventListener("click", () => {
  elements.adminRefreshSpots.classList.add("refreshing");
  loadAdminSpots().finally(() => {
    setTimeout(() => {
      elements.adminRefreshSpots.classList.remove("refreshing");
    }, 600); // Remove after animation completes
  });
});

elements.refreshHistory.addEventListener("click", () => {
  elements.refreshHistory.classList.add("refreshing");
  loadHistory().finally(() => {
    setTimeout(() => {
      elements.refreshHistory.classList.remove("refreshing");
    }, 600); // Remove after animation completes
  });
});

// Redirect to booking page instead of inline booking
if (elements.goToBooking) {
  elements.goToBooking.addEventListener("click", () => {
    if (!state.selectedSpot) {
      alert("Silakan pilih slot parkir terlebih dahulu.");
      return;
    }
    if (!isBookableSpot(state.selectedSpot)) {
      alert("Slot yang dipilih tidak tersedia untuk booking. Hanya slot 1 dan 2 yang dapat dibooking.");
      return;
    }
    sessionStorage.setItem("selectedSpot", JSON.stringify(state.selectedSpot));
    window.location.href = "booking.html";
  });
}

if (elements.goToBookingSelected) {
  elements.goToBookingSelected.addEventListener("click", () => {
    if (!state.selectedSpot) {
      alert("Silakan pilih slot parkir terlebih dahulu.");
      return;
    }
    if (!isBookableSpot(state.selectedSpot)) {
      alert("Slot yang dipilih tidak tersedia untuk booking. Hanya slot 1 dan 2 yang dapat dibooking.");
      return;
    }
    sessionStorage.setItem("selectedSpot", JSON.stringify(state.selectedSpot));
    window.location.href = "booking.html";
  });
}

if (elements.goToBookingPageBtn) {
  if (!elements.goToBookingPageBtn.hasAttribute("data-listener-added")) {
    elements.goToBookingPageBtn.addEventListener("click", () => {
      window.location.href = "booking.html";
    });
    elements.goToBookingPageBtn.setAttribute("data-listener-added", "true");
  }
  // keep it hidden by default; visibility will be controlled by show/hide functions
  //elements.goToBookingPageBtn.style.display = "block";
}

// Keep old booking form for backward compatibility (if exists)
if (elements.bookingForm) {
  elements.bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!state.selectedSpot) {
      alert("Silakan pilih lahan parkir terlebih dahulu.");
      return;
    }
    sessionStorage.setItem("selectedSpot", JSON.stringify(state.selectedSpot));
    window.location.href = "booking.html";
  });
}

elements.topupForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const amount = Number(event.target.amount.value);
  if (!amount) return;
  try {
    const { balance } = await apiFetch("/wallet/topup", {
      method: "POST",
      body: { amount },
    });
    setWalletBalance(balance);
    event.target.reset();
  } catch (err) {
    alert(err.message);
  }
});

// Quick amount buttons
document.querySelectorAll(".amount-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const amount = btn.dataset.amount;
    const input = document.querySelector(".topup-input");
    if (input) {
      input.value = amount;
      input.focus();
    }
  });
});

// Camera scanning state
let cameraStream = null;
let scanInterval = null;

function startCameraScan() {
  const video = document.getElementById("cameraVideo");
  const canvas = document.getElementById("qrCanvas");
  const qrTokenInput = document.getElementById("qrTokenInput");
  const cameraContainer = document.getElementById("cameraContainer");
  const startBtn = document.getElementById("startCameraBtn");
  const stopBtn = document.getElementById("stopCameraBtn");
  
  if (!video || !canvas || !qrTokenInput) return;
  
  navigator.mediaDevices.getUserMedia({ 
    video: { 
      facingMode: 'environment' // Use back camera on mobile
    } 
  })
  .then(stream => {
    cameraStream = stream;
    video.srcObject = stream;
    cameraContainer.style.display = "block";
    startBtn.style.display = "none";
    stopBtn.style.display = "block";
    
    const ctx = canvas.getContext('2d');
    
    scanInterval = setInterval(() => {
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        if (typeof jsQR !== 'undefined') {
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          if (code) {
            qrTokenInput.value = code.data;
            stopCameraScan();
            // Auto-submit or show success message
            const resultBox = elements.adminScanResult;
            resultBox.className = "scan-result-box success";
            resultBox.innerHTML = `
              <div class="result-icon">✅</div>
              <p class="result-text">QR Code berhasil dipindai</p>
              <p class="result-subtext">Token: ${code.data}</p>
            `;
          }
        }
      }
    }, 100);
  })
  .catch(err => {
    console.error("Camera access error:", err);
    alert("Tidak dapat mengakses kamera. Pastikan izin kamera sudah diberikan.");
  });
}

function stopCameraScan() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
  if (scanInterval) {
    clearInterval(scanInterval);
    scanInterval = null;
  }
  const video = document.getElementById("cameraVideo");
  const cameraContainer = document.getElementById("cameraContainer");
  const startBtn = document.getElementById("startCameraBtn");
  const stopBtn = document.getElementById("stopCameraBtn");
  
  if (video) video.srcObject = null;
  if (cameraContainer) cameraContainer.style.display = "none";
  if (startBtn) startBtn.style.display = "block";
  if (stopBtn) stopBtn.style.display = "none";
}

// Camera button handlers
const startCameraBtn = document.getElementById("startCameraBtn");
const stopCameraBtn = document.getElementById("stopCameraBtn");

if (startCameraBtn) {
  startCameraBtn.addEventListener("click", startCameraScan);
}

if (stopCameraBtn) {
  stopCameraBtn.addEventListener("click", stopCameraScan);
}

elements.adminScanForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  const resultBox = elements.adminScanResult;
  
  // Show loading state
  resultBox.className = "scan-result-box";
  resultBox.innerHTML = `
    <div class="result-icon">⏳</div>
    <p class="result-text">Memproses...</p>
    <p class="result-subtext">Mohon tunggu</p>
  `;
  
  try {
    const { message } = await apiFetch("/admin/scan", {
      method: "POST",
      body: payload,
    });
    
    // Show success state
    resultBox.className = "scan-result-box success";
    resultBox.innerHTML = `
      <div class="result-icon">✅</div>
      <p class="result-text">${message}</p>
      <p class="result-subtext">Validasi berhasil</p>
    `;
    
    await Promise.all([loadAdminSpots(), loadReports()]);
    
    // Reset form
    event.target.reset();
  } catch (err) {
    // Show error state
    resultBox.className = "scan-result-box error";
    resultBox.innerHTML = `
      <div class="result-icon">❌</div>
      <p class="result-text">${err.message}</p>
      <p class="result-subtext">Validasi gagal</p>
    `;
  }
});

if (elements.spotFilter) {
  elements.spotFilter.addEventListener("change", () => {
    const spots = state.cachedSpots || [];
    const filtered = filterSpots(spots);
    renderSpots(filtered, elements.spotList);
    const current = state.selectedSpot
      ? filtered.find((spot) => spot.id === state.selectedSpot.id && spot.isAvailable)
      : null;
    setSelectedSpot(current || null);
  });
}

if (elements.cancelBooking) {
  elements.cancelBooking.addEventListener("click", async () => {
    if (!state.activeBooking || state.activeBooking.status !== "pending") return;
    if (!confirm("Yakin ingin membatalkan booking?")) return;
    try {
      await apiFetch("/parking/cancel", {
        method: "POST",
      });
      hideBookingPanel();
      hideGoToBookingButton();
      await Promise.all([loadSpots(), loadHistory(), loadActiveBooking()]);
    } catch (err) {
      alert(err.message);
    }
  });
}

// ---------- INITIALIZE ----------
(async function init() {
  const session = restoreSession();
  if (session?.token) {
    try {
      await bootstrapSession(session);
    } catch (err) {
      clearSession();
      window.location.href = "login.html";
    }
  } else {
    window.location.href = "login.html";
  }
})();

