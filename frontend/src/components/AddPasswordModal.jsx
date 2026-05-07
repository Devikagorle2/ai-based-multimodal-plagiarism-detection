import { useState } from "react";
import axios from "axios";
import { API_BASE } from "../api.js";
import { validatePassword } from "../utils/validation.js";
import { getStoredUser } from "../authStorage.js";

export default function AddPasswordModal({ open, onClose, onSuccess }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [show1, setShow1] = useState(false);
  const [show2, setShow2] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (!validatePassword(newPassword)) {
      setError("Use 8+ chars with upper, lower, number, and special (@$!%*?&).");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    const email = getStoredUser()?.email || "";
    if (!email) {
      setError("Not logged in.");
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/api/auth/password`, {
        email,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      if (data.error) {
        setError(data.error);
        return;
      }
      onSuccess?.();
      onClose();
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg = Array.isArray(d) ? d.map((x) => x.msg).join(" ") : err.response?.data?.detail || err.message;
      setError(typeof msg === "string" ? msg : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md animate-scale-in rounded-2xl bg-white p-6 shadow-xl ring-1 ring-gray-100" role="dialog">
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-xl font-bold text-slate-900">Add password</h2>
          <button type="button" onClick={onClose} className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700">
            ×
          </button>
        </div>
        <p className="mb-6 text-sm text-slate-600">
          Adding the password will sign you out of all your sessions. You will need to log in again on all your devices.
        </p>
        <form onSubmit={submit} className="space-y-4">
          <div className="relative">
            <input
              type={show1 ? "text" : "password"}
              placeholder="New password *"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-4 py-3 pr-10 text-sm outline-none focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
            />
            <button
              type="button"
              className="absolute right-0 top-0 flex h-full items-center px-3 text-gray-500 hover:text-gray-800"
              onClick={() => setShow1((s) => !s)}
              aria-label="Toggle password visibility"
            >
              {show1 ? "🙈" : "👁"}
            </button>
          </div>
          <div className="relative">
            <input
              type={show2 ? "text" : "password"}
              placeholder="Confirm password *"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-4 py-3 pr-10 text-sm outline-none focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
            />
            <button
              type="button"
              className="absolute right-0 top-0 flex h-full items-center px-3 text-gray-500 hover:text-gray-800"
              onClick={() => setShow2((s) => !s)}
              aria-label="Toggle password visibility"
            >
              {show2 ? "🙈" : "👁"}
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="rounded-full px-4 py-2 text-sm font-medium text-[#16a34a] hover:underline">
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-full bg-[#16a34a] px-6 py-2 text-sm font-semibold text-white shadow-md transition hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? "Saving…" : "Add Password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
