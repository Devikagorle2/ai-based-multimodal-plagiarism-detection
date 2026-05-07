/** Local session: JSON { name, email }. Migrates legacy plain-email string. */
const USER_KEY = "user";
const ACCOUNTS_KEY = "plagiarism_local_accounts";

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    const o = JSON.parse(raw);
    if (o && typeof o === "object") {
      return {
        name: o.name != null && String(o.name).trim() ? String(o.name).trim() : "Guest",
        email: o.email != null ? String(o.email) : "",
      };
    }
  } catch {
    if (raw.includes("@")) {
      return { name: "Guest", email: raw.trim() };
    }
  }
  return null;
}

export function setStoredUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(USER_KEY);
  localStorage.removeItem("userName");
  localStorage.removeItem("access_token");
  localStorage.removeItem("token_type");
}

export function readLocalAccounts() {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function writeLocalAccounts(accounts) {
  localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
}
