import React from "react";

export default function Button({ children, onClick, type = "button" }) {
  return (
    <button
      type={type}
      onClick={onClick}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
    >
      {children}
    </button>
  );
}
