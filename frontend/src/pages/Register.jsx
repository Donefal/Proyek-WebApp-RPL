import React, { useState } from "react";
import Input from "../components/input";
import Button from "../components/button";
import { registerService } from "../services/auth";
import { Link, useNavigate } from "react-router-dom";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [msg, setMsg] = useState("");

  const update = (field, value) => {
    setForm({ ...form, [field]: value });
  };

  const submit = async (e) => {
    e.preventDefault();
    const res = await registerService(form);

    if (res.status === "success") {
      setMsg("Registrasi berhasil. Silakan login.");
      setTimeout(() => navigate("/login"), 1200);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-6 bg-white shadow rounded-lg">
      <h1 className="text-2xl font-bold mb-4">Register</h1>

      {msg && <p className="text-green-600 mb-2">{msg}</p>}

      <form onSubmit={submit}>
        <Input label="Nama" value={form.name} onChange={(v) => update("name", v)} />
        <Input label="Email" value={form.email} onChange={(v) => update("email", v)} />
        <Input label="Password" type="password" value={form.password} onChange={(v) => update("password", v)} />

        <Button type="submit">Daftar</Button>
      </form>

      <p className="mt-3 text-sm">
        Sudah punya akun?{" "}
        <Link to="/login" className="text-blue-600">Login</Link>
      </p>
    </div>
  );
}
