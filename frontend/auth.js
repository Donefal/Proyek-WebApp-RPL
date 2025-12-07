const API_BASE_URL = "http://localhost:8000";
const STORAGE_KEY = "ParkinglySession";

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const goRegister = document.getElementById("goRegister");
const goLogin = document.getElementById("goLogin");

function persistSession(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

async function apiFetch(path, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  const config = { ...options, headers };
  if (options.body) {
    config.body = JSON.stringify(options.body);
  }
  const res = await fetch(`${API_BASE_URL}${path}`, config);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // FastAPI mengembalikan error dalam format {"detail": "message"}
    throw new Error(err.detail || err.message || "Request failed");
  }
  return res.json();
}

if (goRegister) {
  goRegister.addEventListener("click", () => {
    window.location.href = "register.html";
  });
}

if (goLogin) {
  goLogin.addEventListener("click", () => {
    window.location.href = "login.html";
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(loginForm);
    const payload = Object.fromEntries(form.entries());
    try {
      const data = await apiFetch("/auth/login", { method: "POST", body: payload });
      const session = { token: data.token, user: data.user, role: data.user.role };
      persistSession(session);
      window.location.href = "index.html";
    } catch (err) {
      alert(err.message);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(registerForm);
    const payload = Object.fromEntries(form.entries());
    try {
      await apiFetch("/auth/register", { method: "POST", body: payload });
      alert("Registrasi berhasil. Silakan login.");
      window.location.href = "login.html";
    } catch (err) {
      alert(err.message);
    }
  });
}

