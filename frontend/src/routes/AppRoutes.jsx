import React, { Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";

// Import halaman asli
import Login from "../pages/Login";
import Register from "../pages/Register";
import Map from "../pages/Map";
import Ticket from "../pages/Ticket";
import Wallet from "../pages/Wallet";
import AdminDashboard from "../pages/AdminDashboard";
import AdminScan from "../pages/AdminScan";
const Placeholder = ({ title }) => (
  <div style={{ maxWidth: 800, margin: "32px auto", padding: 20 }}>
    <h1 style={{ marginBottom: 12 }}>{title}</h1>
    <p style={{ color: "#555" }}>Halaman ini belum diimplementasikan. Ganti dengan file page yang sesuai.</p>
  </div>
);

export default function AppRoutes() {
  return (
    <Suspense fallback={<div style={{ padding: 20 }}>Memuat...</div>}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<Map />} />
        <Route path="/ticket/:id" element={<Ticket />} />
        <Route path="/wallet" element={<Wallet />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/scan" element={<AdminScan />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
