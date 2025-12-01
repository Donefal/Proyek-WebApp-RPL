const express = require("express");
const cors = require("cors");
const path = require("path");
const { nanoid } = require("nanoid");

const PORT = process.env.PORT || 5001;
const QR_TTL_MINUTES = 30;
const FIRST_HOUR_RATE = 10000;
const EXTRA_HOUR_RATE = 5000;

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

const users = [
  { id: "u1", name: "Budi", email: "user@demo.com", password: "123456", role: "user" },
  { id: "a1", name: "Admin", email: "admin@demo.com", password: "123456", role: "admin" },
];

const wallets = { u1: 50000 };

const spots = Array.from({ length: 8 }).map((_, idx) => ({
  id: `S${idx + 1}`,
  name: `Slot ${idx + 1}`,
  code: `P-${idx + 1}`,
  level: 1,
  isAvailable: true,
  ratePerHour: FIRST_HOUR_RATE,
}));

const bookings = [];
const history = [];

const reports = {
  todayRevenue: 0,
  monthRevenue: 0,
  todayEntries: 0,
  todayExits: 0,
};

function calculateParkingCost(startTime, endTime = new Date()) {
  const elapsedMs = new Date(endTime).getTime() - new Date(startTime).getTime();
  const hours = Math.max(1, Math.ceil(elapsedMs / (60 * 60 * 1000)));
  const cost =
    FIRST_HOUR_RATE + Math.max(0, hours - 1) * EXTRA_HOUR_RATE;
  return { hours, cost };
}

function buildToken(userId) {
  return `token-${userId}`;
}

function findUserByToken(header) {
  if (!header) return null;
  const token = header.replace("Bearer ", "").trim();
  const userId = token.split("token-")[1];
  return users.find((u) => u.id === userId) || null;
}

function createQrToken() {
  return {
    token: nanoid(12),
    expiresAt: new Date(Date.now() + QR_TTL_MINUTES * 60 * 1000).toISOString(),
  };
}

function getWalletBalance(userId) {
  if (!(userId in wallets)) wallets[userId] = 0;
  return wallets[userId];
}

function ensureAuth(req, res, next) {
  const user = findUserByToken(req.headers.authorization);
  if (!user) {
    return res.status(401).json({ message: "Unauthorized" });
  }
  req.user = user;
  next();
}

function ensureRole(role) {
  return (req, res, next) => {
    if (req.user.role !== role) {
      return res.status(403).json({ message: "Forbidden" });
    }
    next();
  };
}

function cleanupExpiredBooking(booking) {
  if (!booking || booking.status !== "pending") return booking;
  const expired = new Date(booking.qr.expiresAt).getTime() < Date.now();
  if (expired) {
    booking.status = "expired";
    const slot = spots.find((spot) => spot.id === booking.spotId);
    if (slot) slot.isAvailable = true;
  }
  return booking;
}

app.post("/api/auth/register", (req, res) => {
  const { name, email, password } = req.body || {};
  const role = "user";
  if (!name || !email || !password) {
    return res.status(400).json({ message: "Data tidak lengkap" });
  }
  const exists = users.some((u) => u.email === email);
  if (exists) {
    return res.status(409).json({ message: "Email sudah terdaftar" });
  }
  const id = nanoid(6);
  const user = { id, name, email, password, role };
  users.push(user);
  res.json({ message: "Registrasi berhasil" });
});

app.post("/api/auth/login", (req, res) => {
  const { email, password } = req.body || {};
  const user = users.find((u) => u.email === email && u.password === password);
  if (!user) {
    return res.status(401).json({ message: "Email atau password salah" });
  }
  res.json({
    token: buildToken(user.id),
    user: { id: user.id, name: user.name, email: user.email, role: user.role },
  });
});

app.use("/api", ensureAuth);

app.get("/api/parking/spots", (req, res) => {
  res.json({ spots });
});

app.post("/api/parking/book", ensureRole("user"), (req, res) => {
  const { spotId } = req.body || {};
  const slot = spots.find((spot) => spot.id === spotId && spot.isAvailable);
  if (!slot) {
    return res.status(400).json({ message: "Lahan tidak tersedia" });
  }
  const existingActive = bookings.find(
    (booking) => booking.userId === req.user.id && ["pending", "checked-in"].includes(booking.status),
  );
  if (existingActive && existingActive.status === "pending") {
    cleanupExpiredBooking(existingActive);
    if (existingActive.status !== "expired") {
      return res.status(400).json({ message: "Masih ada booking aktif." });
    }
  }
  const booking = {
    id: `B-${nanoid(6)}`,
    userId: req.user.id,
    spotId,
    qr: createQrToken(),
    status: "pending",
    createdAt: new Date().toISOString(),
    startTime: null,
    endTime: null,
    cost: null,
  };
  bookings.push(booking);
  slot.isAvailable = false;
  res.json({ booking });
});

app.get("/api/parking/active", ensureRole("user"), (req, res) => {
  const booking = bookings.find(
    (item) => item.userId === req.user.id && ["pending", "checked-in"].includes(item.status),
  );
  res.json({ booking: cleanupExpiredBooking(booking) && booking.status !== "expired" ? booking : null });
});

app.post("/api/parking/cancel", ensureRole("user"), (req, res) => {
  const booking = bookings.find(
    (item) => item.userId === req.user.id && ["pending"].includes(item.status),
  );
  if (!booking) {
    return res.status(400).json({ message: "Tidak ada booking yang bisa dibatalkan" });
  }
  cleanupExpiredBooking(booking);
  if (booking.status === "expired") {
    return res.status(400).json({ message: "QR sudah kadaluarsa" });
  }
  booking.status = "cancelled";
  booking.cancelledAt = new Date().toISOString();
  const slot = spots.find((spot) => spot.id === booking.spotId);
  if (slot) slot.isAvailable = true;
  res.json({ message: "Booking berhasil dibatalkan" });
});

app.post("/api/parking/scan-entry", ensureRole("user"), (req, res) => {
  return res
    .status(403)
    .json({ message: "Validasi QR hanya dapat dilakukan oleh petugas/admin." });
});

app.post("/api/parking/scan-exit", ensureRole("user"), (req, res) => {
  return res
    .status(403)
    .json({ message: "Validasi QR hanya dapat dilakukan oleh petugas/admin." });
});

app.get("/api/wallet", ensureRole("user"), (req, res) => {
  res.json({ balance: getWalletBalance(req.user.id) });
});

app.post("/api/wallet/topup", ensureRole("user"), (req, res) => {
  const { amount } = req.body || {};
  if (!amount || amount <= 0) {
    return res.status(400).json({ message: "Nominal tidak valid" });
  }
  wallets[req.user.id] = getWalletBalance(req.user.id) + Number(amount);
  res.json({ balance: wallets[req.user.id] });
});

app.get("/api/parking/history", ensureRole("user"), (req, res) => {
  const userHistory = history.filter((item) => item.userId === req.user.id);
  res.json({ history: userHistory });
});

app.get("/api/admin/spots", ensureRole("admin"), (req, res) => {
  res.json({ spots });
});

app.post("/api/admin/scan", ensureRole("admin"), (req, res) => {
  const { qrToken, action } = req.body || {};
  const booking = bookings.find((item) => item.qr.token === qrToken);
  if (!booking) {
    return res.status(404).json({ message: "QR tidak ditemukan" });
  }
  if (action === "enter") {
    cleanupExpiredBooking(booking);
    if (booking.status === "expired") {
      return res.status(400).json({ message: "QR kadaluarsa" });
    }
    if (booking.status === "checked-in") {
      return res.status(400).json({ message: "Kedatangan sudah dikonfirmasi" });
    }
    booking.status = "checked-in";
    booking.startTime = new Date().toISOString();
    reports.todayEntries += 1;
    return res.json({ message: "Masuk dikonfirmasi admin" });
  }
  if (action === "exit") {
    if (booking.status !== "checked-in") {
      return res.status(400).json({ message: "Belum masuk atau sudah selesai" });
    }
    const slot = spots.find((spot) => spot.id === booking.spotId);
    const { hours, cost: total } = calculateParkingCost(booking.startTime);
    const wallet = getWalletBalance(booking.userId);
    if (wallet < total) {
      return res.status(400).json({ message: "Saldo user tidak cukup" });
    }
    wallets[booking.userId] = wallet - total;
    booking.status = "completed";
    booking.endTime = new Date().toISOString();
    booking.cost = total;
    booking.durationHours = hours;
    if (slot) slot.isAvailable = true;
    history.push({
      bookingId: booking.id,
      userId: booking.userId,
      spotName: slot?.name || booking.spotId,
      startTime: booking.startTime,
      endTime: booking.endTime,
      durationHours: hours,
      cost: total,
    });
    reports.todayRevenue += total;
    reports.monthRevenue += total;
    reports.todayExits += 1;
    return res.json({ message: "Keluar dikonfirmasi admin" });
  }
  res.status(400).json({ message: "Aksi tidak dikenal" });
});

app.get("/api/admin/reports", ensureRole("admin"), (req, res) => {
  res.json({ reports });
});

app.get("/", (req, res) => {
  res.sendFile(path.join(__dirname, "index.html"));
});

app.listen(PORT, () => {
  console.log(`Smart Parking API running on http://localhost:${PORT}`);
});

