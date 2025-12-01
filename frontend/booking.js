// Booking page specific logic
const API_BASE_URL = "http://localhost:5001/api";
const STORAGE_KEY = "smartParkingSession";

const bookingState = {
  token: null,
  user: null,
  selectedSpot: null,
  activeBooking: null,
  countdownInterval: null,
  durationInterval: null,
};

const bookingElements = {
  headerActions: document.getElementById("headerActions"),
  activeUser: document.getElementById("activeUser"),
  logoutBtn: document.getElementById("logoutBtn"),
  userView: document.getElementById("userView"),
  backToMap: document.getElementById("backToMap"),
  newBookingSection: document.getElementById("newBookingSection"),
  activeBookingSection: document.getElementById("activeBookingSection"),
  bookingForm: document.getElementById("bookingForm"),
  selectedSpotId: document.getElementById("selectedSpotId"),
  selectedSpotCode: document.getElementById("selectedSpotCode"),
  selectedSpotNameDisplay: document.getElementById("selectedSpotNameDisplay"),
  selectedSpotLevel: document.getElementById("selectedSpotLevel"),
  submitBookingBtn: document.getElementById("submitBookingBtn"),
  cancelBooking: document.getElementById("cancelBooking"),
  bookingFields: {
    bookingId: document.querySelector("[data-field='bookingId']"),
    status: document.querySelector("[data-field='bookingStatus']"),
    qrCode: document.querySelector("[data-field='qrCode']"),
    duration: document.querySelector("[data-field='duration']"),
    cost: document.querySelector("[data-field='cost']"),
  },
  timelineSteps: {
    qr: document.querySelector("[data-step='qr']"),
    scan: document.querySelector("[data-step='scan']"),
  },
  qrBox: document.getElementById("qrBox"),
  qrExpiredHint: document.getElementById("qrExpiredHint"),
};

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  if (bookingState.token) {
    headers.Authorization = `Bearer ${bookingState.token}`;
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
    throw new Error(error.message || "Request failed");
  }
  return res.json();
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
  bookingState.token = null;
  bookingState.user = null;
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
  const PRICING = {
    firstHour: 10000,
    extraHour: 5000,
  };
  const hours = Math.max(1, Math.ceil(ms / (1000 * 60 * 60)));
  return PRICING.firstHour + Math.max(0, hours - 1) * PRICING.extraHour;
}

function loadSelectedSpot() {
  const selectedSpotData = sessionStorage.getItem("selectedSpot");
  if (selectedSpotData) {
    try {
      const spot = JSON.parse(selectedSpotData);
      bookingState.selectedSpot = spot;
      updateSelectedSpotDisplay(spot);
    } catch (err) {
      console.error("Error loading selected spot:", err);
    }
  }
}

function updateSelectedSpotDisplay(spot) {
  if (!spot) {
    bookingElements.selectedSpotCode.textContent = "-";
    bookingElements.selectedSpotNameDisplay.textContent = "Belum dipilih";
    bookingElements.selectedSpotLevel.textContent = "-";
    bookingElements.selectedSpotId.value = "";
    bookingElements.submitBookingBtn.disabled = true;
    return;
  }

  bookingElements.selectedSpotCode.textContent = spot.code;
  bookingElements.selectedSpotNameDisplay.textContent = spot.name;
  bookingElements.selectedSpotLevel.textContent = `Level ${spot.level}`;
  bookingElements.selectedSpotId.value = spot.id;
  bookingElements.submitBookingBtn.disabled = false;
}

function showActiveBooking(booking) {
  bookingState.activeBooking = booking;
  bookingElements.newBookingSection.classList.add("hidden");
  bookingElements.activeBookingSection.classList.remove("hidden");
  
  bookingElements.bookingFields.bookingId.textContent = booking.id;
  bookingElements.bookingFields.status.textContent =
    booking.status === "pending" ? "Menunggu validasi" : "Sedang parkir";
  bookingElements.bookingFields.qrCode.textContent = booking.qr.token;
  bookingElements.qrBox.textContent = booking.qr.token.slice(0, 8).toUpperCase();
  bookingElements.qrExpiredHint.classList.add("hidden");
  
  updateTimeline(booking.status, booking.qr.token);
  
  const isCheckedIn = booking.status === "checked-in";
  if (bookingElements.cancelBooking) {
    bookingElements.cancelBooking.classList.toggle("hidden", booking.status !== "pending");
  }
  
  if (isCheckedIn) {
    startDurationTimer(booking.startTime);
  } else {
    startCountdown(booking.qr.expiresAt);
  }
}

function hideActiveBooking() {
  bookingState.activeBooking = null;
  bookingElements.newBookingSection.classList.remove("hidden");
  bookingElements.activeBookingSection.classList.add("hidden");
  clearCountdown();
  clearDurationTimer();
  resetMetrics();
}

function startCountdown(expiry) {
  clearCountdown();
  clearDurationTimer();
  function tick() {
    const diff = new Date(expiry).getTime() - Date.now();
    if (diff <= 0) {
      bookingElements.qrExpiredHint.classList.remove("hidden");
      clearCountdown();
      return;
    }
  }
  tick();
  bookingState.countdownInterval = setInterval(tick, 1000);
}

function clearCountdown() {
  if (bookingState.countdownInterval) {
    clearInterval(bookingState.countdownInterval);
    bookingState.countdownInterval = null;
  }
}

function startDurationTimer(startTime) {
  if (!startTime) return;
  clearDurationTimer();
  function tick() {
    const diff = Date.now() - new Date(startTime).getTime();
    if (diff < 0) return;
    if (bookingElements.bookingFields.duration) {
      bookingElements.bookingFields.duration.textContent = formatDuration(diff);
    }
    if (bookingElements.bookingFields.cost) {
      bookingElements.bookingFields.cost.textContent = formatCurrency(estimateCostFromMs(diff));
    }
  }
  tick();
  bookingState.durationInterval = setInterval(tick, 1000 * 30);
}

function clearDurationTimer() {
  if (bookingState.durationInterval) {
    clearInterval(bookingState.durationInterval);
    bookingState.durationInterval = null;
  }
}

function resetMetrics() {
  if (bookingElements.bookingFields.duration) {
    bookingElements.bookingFields.duration.textContent = "-";
  }
  if (bookingElements.bookingFields.cost) {
    bookingElements.bookingFields.cost.textContent = formatCurrency(0);
  }
}

function updateTimeline(status, qrToken) {
  const { qr, scan } = bookingElements.timelineSteps;
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

async function loadActiveBooking() {
  try {
    const { booking } = await apiFetch("/parking/active");
    if (booking) {
      showActiveBooking(booking);
    } else {
      hideActiveBooking();
    }
  } catch (err) {
    hideActiveBooking();
  }
}

async function bootstrapSession(session) {
  bookingState.token = session.token;
  bookingState.user = session.user;
  bookingElements.headerActions.classList.remove("hidden");
  bookingElements.activeUser.textContent = `${session.user.name} (${session.user.role})`;
  bookingElements.userView.classList.remove("hidden");
  
  loadSelectedSpot();
  await loadActiveBooking();
}

// Event Handlers
if (bookingElements.backToMap) {
  bookingElements.backToMap.addEventListener("click", () => {
    window.location.href = "index.html";
  });
}

if (bookingElements.logoutBtn) {
  bookingElements.logoutBtn.addEventListener("click", () => {
    clearSession();
    window.location.href = "login.html";
  });
}

if (bookingElements.bookingForm) {
  bookingElements.bookingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!bookingState.selectedSpot) {
      alert("Silakan pilih slot parkir terlebih dahulu.");
      return;
    }
    const payload = {
      spotId: bookingState.selectedSpot.id,
    };
    try {
      const data = await apiFetch("/parking/book", {
        method: "POST",
        body: payload,
      });
      showActiveBooking(data.booking);
      sessionStorage.removeItem("selectedSpot");
    } catch (err) {
      alert(err.message);
    }
  });
}

if (bookingElements.cancelBooking) {
  bookingElements.cancelBooking.addEventListener("click", async () => {
    if (!bookingState.activeBooking || bookingState.activeBooking.status !== "pending") return;
    if (!confirm("Yakin ingin membatalkan booking?")) return;
    try {
      await apiFetch("/parking/cancel", {
        method: "POST",
      });
      hideActiveBooking();
      window.location.href = "index.html";
    } catch (err) {
      alert(err.message);
    }
  });
}

// Initialize
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

