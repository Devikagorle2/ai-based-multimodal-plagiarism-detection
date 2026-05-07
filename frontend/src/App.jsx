import { useCallback, useState } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import Toast from "./components/Toast.jsx";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";
import AccountPage from "./pages/AccountPage.jsx";
import CodeDetection from "./pages/CodeDetection.jsx";
import CodeResults from "./pages/CodeResults.jsx";
import Login from "./pages/Login.jsx";
import Signup from "./pages/Signup.jsx";
import { clearSession, getStoredUser } from "./authStorage.js";

function RequireAuth() {
  if (!getStoredUser()) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export default function App() {
  const [toast, setToast] = useState(null);

  const logout = useCallback(() => {
    clearSession();
    window.location.assign("/login");
  }, []);

  return (
    <>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route element={<RequireAuth />}>
          <Route element={<Layout onLogout={logout} />}>
            <Route path="/" element={<Home />} />
            <Route path="/account" element={<AccountPage />} />
            <Route path="/code" element={<CodeDetection />} />
            <Route path="/code-results" element={<CodeResults />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toast message={toast} onClose={() => setToast(null)} />
    </>
  );
}
