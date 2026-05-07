import { useState } from "react";
import { Link } from "react-router-dom";
import AddPasswordModal from "../components/AddPasswordModal.jsx";
import { getStoredUser } from "../authStorage.js";

export default function AccountPage() {
  const [pwdOpen, setPwdOpen] = useState(false);
  const user = getStoredUser() || { name: "Guest", email: "" };
  const name = user?.name || "Guest";
  const email = user?.email || "";
  const initial = (name || email || "?").charAt(0).toUpperCase();
  const hasBackendSession = Boolean(localStorage.getItem("access_token"));

  const handlePasswordSuccess = () => {
    localStorage.removeItem("user");
    localStorage.removeItem("userName");
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    window.location.reload();
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-6">
        <Link to="/" className="text-sm font-medium text-[#16a34a] hover:underline">
          ← Back to checker
        </Link>
      </div>

      <div className="grid gap-8 lg:grid-cols-[220px_1fr]">
        <aside className="space-y-2">
          <div className="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50/50 px-4 py-3">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#16a34a] text-lg font-bold text-white">{initial}</span>
            <div>
              <p className="text-sm font-semibold text-gray-900">Profile</p>
              <p className="text-xs text-gray-500">Account</p>
            </div>
          </div>
        </aside>

        <div className="space-y-6">
          <div className="flex flex-wrap items-start gap-6">
            <div className="flex items-center gap-4">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#16a34a] text-2xl font-bold text-white">{initial}</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{name}</h1>
                {email ? <p className="text-gray-600">{email}</p> : <p className="text-sm text-gray-500">No email on file</p>}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-lg">
            <div className="flex flex-col gap-6 lg:flex-row lg:justify-between">
              <div className="space-y-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Name</p>
                  <p className="text-lg font-medium text-gray-900">{name}</p>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Email</p>
                  {email ? (
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-lg text-gray-900">{email}</span>
                      <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">✓ Verified</span>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Not provided</p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">Stored locally in your browser</p>
                </div>
              </div>

              {hasBackendSession ? (
                <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-4 lg:min-w-[200px]">
                  <p className="text-sm font-semibold text-gray-900">Server account</p>
                  <button
                    type="button"
                    onClick={() => setPwdOpen(true)}
                    className="mt-3 flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-[#16a34a] shadow-sm transition hover:bg-emerald-50"
                  >
                    <span aria-hidden>🔒</span> Add password
                  </button>
                </div>
              ) : null}
            </div>

            <div className="mt-8 border-t border-gray-100 pt-6">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Subscription</p>
              <p className="text-lg font-semibold text-gray-900">Free</p>
              <p className="text-sm text-gray-500">User since Mar 2026</p>
            </div>
          </div>
        </div>
      </div>

      <AddPasswordModal
        open={pwdOpen}
        onClose={() => setPwdOpen(false)}
        onSuccess={handlePasswordSuccess}
      />
    </div>
  );
}
