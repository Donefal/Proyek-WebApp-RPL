import React, { useEffect } from "react";
import AppRoutes from "./routes/AppRoutes";

export default function App() {

  useEffect(() => {
    fetch("https://jsonplaceholder.typicode.com/todos/1")
      .then(r => r.json())
      .then(console.log);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <AppRoutes />
    </div>
  );
}
