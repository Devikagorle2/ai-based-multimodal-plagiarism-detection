import { Link, NavLink } from "react-router-dom";
import ProfileDropdown from "./ProfileDropdown.jsx";
import { getStoredUser } from "../authStorage.js";

export default function Navbar({ onLogout }) {
  const user = getStoredUser();

  return (
    <header className="sticky top-0 z-30 border-b border-gray-200/80 bg-white/95 shadow-sm backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link to="/" className="flex items-center gap-2 rounded-lg outline-none ring-[#16a34a]/40 transition hover:opacity-90 focus-visible:ring-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#16a34a] text-lg font-bold text-white shadow-md">
            P
          </span>
          <span className="text-xl font-semibold tracking-tight text-gray-900">Plagiarism AI</span>
        </Link>

        <nav className="flex flex-wrap items-center gap-2 text-sm font-medium text-gray-600">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              [
                "rounded-lg px-4 py-2 transition duration-200",
                isActive ? "bg-emerald-50 text-[#16a34a] ring-1 ring-emerald-200 shadow-sm" : "hover:bg-gray-100",
              ].join(" ")
            }
          >
            Plagiarism Checker
          </NavLink>
          <NavLink
            to="/code"
            className={({ isActive }) =>
              [
                "rounded-lg px-4 py-2 transition duration-200",
                isActive ? "bg-emerald-50 text-[#16a34a] ring-1 ring-emerald-200 shadow-sm" : "hover:bg-gray-100",
              ].join(" ")
            }
          >
            Code checker
          </NavLink>
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <ProfileDropdown user={user} onLogout={onLogout} />
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="rounded-lg px-3 py-2 text-sm font-semibold text-gray-700 transition hover:bg-gray-100"
              >
                Log in
              </Link>
              <Link
                to="/signup"
                className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-green-700"
              >
                Sign up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
