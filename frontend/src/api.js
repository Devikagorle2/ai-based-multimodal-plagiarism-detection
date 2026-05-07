/**
 * API origin for Axios.
 * - Default (empty): same origin as the Vite dev server; `/api/*` is proxied to FastAPI (see vite.config.js).
 * - Override: set `VITE_API_URL=http://127.0.0.1:8000` in `.env.local` if you run the backend on another port.
 */
export const API_BASE = import.meta.env.VITE_API_URL ?? "";
