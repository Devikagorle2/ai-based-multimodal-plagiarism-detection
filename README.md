# Universal Plagiarism + AI Detection System (RAG-Based)

Full-stack app: **React + Tailwind + Axios + React Router** frontend and **FastAPI + Sentence-Transformers + FAISS + SerpAPI** backend.

- **Local ML**: `all-MiniLM-L6-v2` (downloaded once from Hugging Face).
- **Live sources**: [SerpAPI](https://serpapi.com) Google organic results (`serp_engine.py`).
- **Auth**: `POST /api/auth/signup`, `POST /api/auth/login` — **in-memory** user store (demo; passwords stored as plain text per product spec).

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm

## Backend

Default dev port is **8787** (port **8000** is often blocked on Windows with `WinError 10013`).

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app:app --host 127.0.0.1 --port 8787 --reload
```

Or: `python app.py` (same default). Override with `set PORT=8000` if that port works on your machine.

- `POST /api/check` — multipart: `text`, optional `file`, `elapsed_ms`, `behavior` (JSON string: `{ "typing_speed", "paste_size" }`).
- `POST /api/auth/signup` — JSON: `name`, `email`, `password`.
- `POST /api/auth/login` — JSON: `email`, `password`.
- `GET /health`

CORS is set to `allow_origins=["*"]` with `allow_credentials=False` (required for browser compatibility with wildcards).

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. Routes: `/` (checker), `/login`, `/signup`.

The Vite dev server **proxies** `/api/*` to `http://127.0.0.1:8787`. The frontend uses **relative** `/api/...` URLs by default, so signup/login hit the backend through the proxy (no hard-coded `localhost:8000`). To point at another port, set `VITE_PROXY_TARGET` when starting Vite, or set `VITE_API_URL=http://127.0.0.1:YOUR_PORT` in `frontend/.env.local`.

## Plagiarism score

`0.6 × max_similarity + 0.2 × avg_similarity + 0.2 × keyword_overlap` (vs Serp result snippets). If SerpAPI returns no results, similarity falls back to the internal corpus (**sources list stays empty** — no fake “Local Dataset” URLs).

## AI detection label

Uses **semantic similarity %** (0–100) and **paste size** (words): if similarity > 70 and paste size > 50 → **Likely Copied / AI Generated**; elif similarity > 50 → **Edited Content**; else **Human Written**.

## File uploads

Supported: `.txt`, `.pdf`, `.docx`. After a successful scan, the UI hides file upload until the text area is cleared.

## Layout

- `backend/app.py` — main API + in-memory auth
- `backend/serp_engine.py` — SerpAPI (`requests`)
- `frontend/src/pages/Home.jsx` — checker
- `frontend/src/pages/Login.jsx`, `Signup.jsx`
- `frontend/src/components/Layout.jsx`
