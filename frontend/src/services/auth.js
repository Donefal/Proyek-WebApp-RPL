export async function loginService(email, password) {
  if (email === "test@mail.com" && password === "123456") {
    return { status: "success", token: "FAKE_TOKEN_123" };
  }
  return { status: "error", message: "Email atau password salah" };
}

export async function registerService(data) {
  return { status: "success", message: "Registrasi berhasil" };
}
