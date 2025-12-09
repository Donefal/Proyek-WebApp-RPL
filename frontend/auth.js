// Dynamic API URL - use current hostname for cross-device access
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

function showError(inputId, errorId, message) {
  const input = document.getElementById(inputId);
  const errorElement = document.getElementById(errorId);
  if (input && errorElement) {
    input.classList.add("border-red-500");
    errorElement.textContent = message;
    errorElement.classList.remove("hidden");
  }
}

function clearError(inputId, errorId) {
  const input = document.getElementById(inputId);
  const errorElement = document.getElementById(errorId);
  if (input && errorElement) {
    input.classList.remove("border-red-500");
    errorElement.classList.add("hidden");
  }
}

function clearAllErrors() {
  clearError("loginEmail", "loginEmailError");
  clearError("loginPassword", "loginPasswordError");
  clearError("registerName", "registerNameError");
  clearError("registerEmail", "registerEmailError");
  clearError("registerNotelp", "registerNotelpError");
  clearError("registerPassword", "registerPasswordError");
}

if (loginForm) {
  // Clear errors when user types
  const loginEmail = document.getElementById("loginEmail");
  const loginPassword = document.getElementById("loginPassword");
  if (loginEmail) {
    loginEmail.addEventListener("input", () => clearError("loginEmail", "loginEmailError"));
  }
  if (loginPassword) {
    loginPassword.addEventListener("input", () => clearError("loginPassword", "loginPasswordError"));
  }
  
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAllErrors();
    const form = new FormData(loginForm);
    const payload = Object.fromEntries(form.entries());
    try {
      const data = await apiFetch("/auth/login", { method: "POST", body: payload });
      const session = { token: data.token, user: data.user, role: data.user.role };
      persistSession(session);
      window.location.href = "index.html";
    } catch (err) {
      // Show error in email field (most common error)
      showError("loginEmail", "loginEmailError", err.message);
      showError("loginPassword", "loginPasswordError", err.message);
    }
  });
}

if (registerForm) {
  // Clear errors when user types
  const registerName = document.getElementById("registerName");
  const registerEmail = document.getElementById("registerEmail");
  const registerNotelp = document.getElementById("registerNotelp");
  const registerPassword = document.getElementById("registerPassword");
  
  if (registerName) {
    registerName.addEventListener("input", () => clearError("registerName", "registerNameError"));
  }
  if (registerEmail) {
    registerEmail.addEventListener("input", () => clearError("registerEmail", "registerEmailError"));
  }
  if (registerNotelp) {
    registerNotelp.addEventListener("input", () => clearError("registerNotelp", "registerNotelpError"));
  }
  if (registerPassword) {
    registerPassword.addEventListener("input", () => clearError("registerPassword", "registerPasswordError"));
  }
  
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearAllErrors();
    const form = new FormData(registerForm);
    const payload = Object.fromEntries(form.entries());
    
    // Validate password length
    if (payload.password && payload.password.length < 8) {
      showError("registerPassword", "registerPasswordError", "Password harus minimal 8 karakter");
      return;
    }
    
    try {
      await apiFetch("/auth/register", { method: "POST", body: payload });
      // No alert, just redirect
      window.location.href = "login.html";
    } catch (err) {
      // Show error in appropriate field
      const errorMsg = err.message || "Terjadi kesalahan";
      if (errorMsg.toLowerCase().includes("email")) {
        showError("registerEmail", "registerEmailError", errorMsg);
      } else if (errorMsg.toLowerCase().includes("password")) {
        showError("registerPassword", "registerPasswordError", errorMsg);
      } else {
        // Show in email field as default
        showError("registerEmail", "registerEmailError", errorMsg);
      }
    }
  });
}

