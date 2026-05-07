import { Outlet } from "react-router-dom";
import Navbar from "./Navbar.jsx";

export default function Layout({ onLogout }) {
  return (
    <div className="min-h-screen bg-[#f5f5f5] text-gray-800">
      <Navbar onLogout={onLogout} />
      <Outlet />
      <footer className="border-t border-gray-200 bg-white py-6 text-center text-xs text-gray-500">
        AI-Based Plagiarism Detection
      </footer>
    </div>
  );
}
