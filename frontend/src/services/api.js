// simple fetch wrapper. Set VITE_API_BASE in .env if backend not at default.
const BASE = import.meta.env.VITE_API_BASE || "http://localhost:3000/api";

async function request(path, opts = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, opts);
  // Try parse JSON safely
  const text = await res.text();
  try {
    return { ok: res.ok, status: res.status, data: JSON.parse(text) };
  } catch {
    return { ok: res.ok, status: res.status, data: text };
  }
}

export async function apiGet(path, token) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  return request(path, { method: "GET", headers });
}

export async function apiPost(path, body = {}, token) {
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  return request(path, { method: "POST", headers, body: JSON.stringify(body) });
}

export async function apiPatch(path, body = {}, token) {
  const headers = { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  return request(path, { method: "PATCH", headers, body: JSON.stringify(body) });
}
