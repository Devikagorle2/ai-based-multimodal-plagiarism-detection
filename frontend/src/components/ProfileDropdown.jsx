import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

export default function ProfileDropdown({ user, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const name = user?.name || "Guest";
  const email = user?.email || "";

  useEffect(() => {
    const f = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", f);
    return () => document.removeEventListener("mousedown", f);
  }, []);

  const initial = (name || email || "?").charAt(0).toUpperCase();

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full border border-gray-200 bg-white py-1 pl-1 pr-3 shadow-sm transition hover:border-gray-300 hover:shadow-md"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#16a34a] text-sm font-bold text-white">
          {initial}
        </span>
        <span className="max-w-[140px] truncate text-sm font-medium text-gray-800">{name}</span>
      </button>

      {open && (
        <div className="absolute right-0 z-50 mt-2 w-56 origin-top-right animate-fade-in rounded-2xl border border-gray-100 bg-white py-2 shadow-xl ring-1 ring-black/5 transition">
          {email ? <div className="border-b border-gray-100 px-4 py-2 text-xs text-gray-500">{email}</div> : null}
          <Link
            to="/account"
            className="block px-4 py-2.5 text-sm text-gray-800 transition hover:bg-emerald-50/80"
            onClick={() => setOpen(false)}
          >
            Account details
          </Link>
          <button
            type="button"
            className="w-full px-4 py-2.5 text-left text-sm text-gray-800 transition hover:bg-emerald-50/80"
            onClick={() => {
              setOpen(false);
              onLogout();
            }}
          >
            Log out
          </button>
        </div>
      )}
    </div>
  );
}
