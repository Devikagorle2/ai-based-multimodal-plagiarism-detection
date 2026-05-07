import { useState } from "react";
import axios from "axios";
import { API_BASE } from "../api.js";
import { validateEmail, validatePassword } from "../utils/validation.js";

export default function LoginModal({ onSuccess }) {
  const [showLogin, setShowLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submitLogin = async (e) => {
    e.preventDefault();
    setError("");
    if (!validateEmail(email)) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!validatePassword(password)) {
      setError(
        "Password must be 8+ characters with uppercase, lowercase, number, and special character (@$!%*?&)."
      );
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/api/auth/login`, { email, password });
      if (data.error) {
        setError(data.error);
        return;
      }
      localStorage.setItem("user", data.email || email.trim().toLowerCase());
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type || "bearer");
      }
      onSuccess(data.email || email.trim().toLowerCase(), null);
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg = Array.isArray(d) ? d.map((x) => x.msg).join(" ") : err.response?.data?.detail || err.message;
      setError(typeof msg === "string" ? msg : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const submitRegister = async (e) => {
    e.preventDefault();
    setError("");
    if (!name.trim()) {
      setError("Name is required.");
      return;
    }
    if (!validateEmail(email)) {
      setError("Please enter a valid email address.");
      return;
    }
    if (!validatePassword(password)) {
      setError(
        "Password must be 8+ characters with uppercase, lowercase, number, and special character (@$!%*?&)."
      );
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API_BASE}/api/auth/signup`, { name: name.trim(), email, password });
      if (data.error) {
        setError(data.error);
        return;
      }
      const em = data.email || email.trim().toLowerCase();
      localStorage.setItem("user", em);
      localStorage.setItem("userName", data.name || name.trim());
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type || "bearer");
      }
      onSuccess(em, data.name || name.trim());
    } catch (err) {
      const d = err.response?.data?.detail;
      const msg = Array.isArray(d) ? d.map((x) => x.msg).join(" ") : err.response?.data?.detail || err.message;
      setError(typeof msg === "string" ? msg : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div
        className="w-full max-w-sm animate-scale-in rounded-2xl bg-white p-6 shadow-xl ring-1 ring-gray-100"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
      >
        <h2 id="login-title" className="mb-1 text-xl font-bold text-gray-900">
          {showLogin ? "Login" : "Create account"}
        </h2>
        <p className="mb-4 text-sm text-gray-500">AI-Based Plagiarism Detection System</p>

        <form onSubmit={showLogin ? submitLogin : submitRegister} className="space-y-3">
          {!showLogin && (
            <input
              type="text"
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
            />
          )}
          <input
            type="email"
            placeholder="example@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
            autoComplete="email"
          />
          <input
            type="password"
            placeholder="Enter strong password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none transition focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
            autoComplete={showLogin ? "current-password" : "new-password"}
          />

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-100">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[#16a34a] py-3 text-sm font-semibold text-white shadow-md transition hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Please wait…" : showLogin ? "Login" : "Register"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          {showLogin ? (
            <>
              No account?{" "}
              <button
                type="button"
                className="font-semibold text-[#16a34a] hover:underline"
                onClick={() => {
                  setError("");
                  setShowLogin(false);
                }}
              >
                Register here
              </button>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <button
                type="button"
                className="font-semibold text-[#16a34a] hover:underline"
                onClick={() => {
                  setError("");
                  setShowLogin(true);
                }}
              >
                Login
              </button>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
