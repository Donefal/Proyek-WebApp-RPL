import React, { useState } from "react";
import Input from "../components/input";
import Button from "../components/button";
import { loginService } from "../services/auth";
import { useNavigate, Link } from "react-router-dom";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    const res = await loginService(email, password);

    if (res.status === "success") {
      navigate("/");
    } else {
      setError(res.message);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-20 p-6 bg-white shadow rounded-lg">
      <h1 className="text-2xl font-bold mb-4">Login</h1>

      {error && <p className="text-red-500 mb-2">{error}</p>}

      <form onSubmit={submit}>
        <Input label="Email" value={email} onChange={setEmail} />
        <Input label="Password" type="password" value={password} onChange={setPassword} />

        <Button type="submit">Login</Button>
      </form>

      <p className="mt-3 text-sm">
        Belum punya akun?{" "}
        <Link to="/register" className="text-blue-600">Daftar</Link>
      </p>
    </div>
  );
}


