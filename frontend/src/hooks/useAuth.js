import { useState } from "react";

export default function useAuth() {
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    if (!email || !password) return { status: "error", message: "Harus diisi" };

    if (email === "test@mail.com" && password === "123456") {
      setUser({ email });
      return { status: "success" };
    }

    return { status: "error", message: "Email atau password salah" };
  };

  const logout = () => setUser(null);

  return { user, login, logout };
}
