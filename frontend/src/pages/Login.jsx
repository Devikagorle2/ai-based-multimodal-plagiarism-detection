import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { getStoredUser, readLocalAccounts, setStoredUser } from "../authStorage.js";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  if (getStoredUser()) {
    return <Navigate to="/" replace />;
  }

  const submit = (e) => {
    e.preventDefault();
    setError("");
    const em = email.trim().toLowerCase();
    if (!em || !password) {
      setError("Email and password are required.");
      return;
    }
    const accounts = readLocalAccounts();
    const acc = accounts[em];
    if (!acc || acc.password !== password) {
      setError("Invalid email or password.");
      return;
    }
    setStoredUser({
      name: acc.name || "Guest",
      email: em,
    });
    if (acc.name) localStorage.setItem("userName", acc.name);
    navigate("/", { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#f5f5f5] px-4 py-12">
      <Link to="/" className="mb-6 flex items-center gap-2 text-gray-800">
        <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#16a34a] text-lg font-bold text-white">P</span>
        <span className="text-xl font-semibold">Plagiarism AI</span>
      </Link>
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl ring-1 ring-gray-100">
        <h1 className="text-xl font-bold text-gray-900">Log in</h1>
        <p className="mt-1 text-sm text-gray-500">Use your local account credentials.</p>
        <form onSubmit={submit} className="mt-6 space-y-3">
          <input
            type="email"
            autoComplete="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
          />
          <input
            type="password"
            autoComplete="current-password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm outline-none focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
          />
          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-100">{error}</p>
          )}
          <button
            type="submit"
            className="w-full rounded-xl bg-[#16a34a] py-3 text-sm font-semibold text-white shadow-md transition hover:bg-green-700"
          >
            Log in
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-600">
          No account?{" "}
          <Link to="/signup" className="font-semibold text-[#16a34a] hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
