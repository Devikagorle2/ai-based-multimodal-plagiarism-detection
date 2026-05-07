"""
Universal Plagiarism + AI Detection — FAISS + MiniLM + SerpAPI + in-memory auth.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
import secrets
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from docx import Document
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field, field_validator
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from behavior_model import predict_behavior_score
from code_engine import analyze_code, ensure_code_index, get_matched_source
from highlight_engine import highlight_matching_lines
from report_generator import generate_code_report, generate_report_pdf
from serp_engine import build_code_serp_query, search_sources

# --- In-memory auth (plain passwords per product spec) --------------------------------
users_db: dict[str, str] = {}
# Optional opaque tokens for localStorage: token -> email
tokens_db: dict[str, str] = {}


_STRONG_PW = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$")


class UserRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        if not _STRONG_PW.match(v):
            raise ValueError(
                "Password must be 8+ characters and include upper, lower, digit, and special (@$!%*?&)"
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


class CodeBehaviorIn(BaseModel):
    typing_speed: float = 0.0
    pause_time: float = 0.0
    backspace_count: int = 0
    paste_size: int = 0
    typing_variance: float = 0.0


class CodeCheckIn(BaseModel):
    code: str = ""
    behavior: CodeBehaviorIn = Field(default_factory=CodeBehaviorIn)


class ReportRequest(BaseModel):
    type: str | None = None
    input_content: str | None = None
    input_text: str = ""
    similarity_results: list[Any] = Field(default_factory=list)
    avg_similarity: float | None = None
    max_similarity: float | None = None
    keyword_overlap: float | None = None
    final_score: float | None = None
    ai_probability: float | None = None
    ai_label: str = ""
    top_sources: list[dict[str, Any]] = Field(default_factory=list)


class PasswordChange(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=8, max_length=256)
    confirm_password: str = Field(..., min_length=8, max_length=256)

    @field_validator("new_password")
    @classmethod
    def strong_new_password(cls, v: str) -> str:
        if not _STRONG_PW.match(v):
            raise ValueError(
                "Password must be 8+ characters and include upper, lower, digit, and special (@$!%*?&)"
            )
        return v


# --- Internal fallback corpus (similarity only when SerpAPI returns nothing; never exposed as sources) ---
SAMPLE_TEXTS: list[str] = [
    "Artificial Intelligence is transforming industries across the globe, from healthcare diagnostics to autonomous vehicles.",
    "Machine learning enables computers to learn from data without being explicitly programmed for every task.",
    "Sorting algorithms like quicksort and mergesort are efficient ways to order large collections of numbers.",
    "Natural language processing helps machines understand, interpret, and generate human language.",
    "Deep neural networks consist of many layers that learn hierarchical representations of input data.",
    "Climate change poses significant challenges to ecosystems, agriculture, and coastal communities worldwide.",
    "Renewable energy sources such as solar and wind are becoming more cost-effective than fossil fuels in many regions.",
    "The scientific method involves observation, hypothesis formation, experimentation, and peer-reviewed validation.",
    "Cybersecurity best practices include strong passwords, multi-factor authentication, and regular software updates.",
    "Blockchain technology provides decentralized ledgers that can increase transparency in supply chains.",
    "Remote work has reshaped collaboration tools, meeting culture, and expectations around work-life balance.",
    "Education technology platforms enable personalized learning paths and scalable assessment at lower cost.",
    "Quantum computing may eventually solve certain optimization and simulation problems intractable for classical computers.",
    "Ethical AI requires fairness, accountability, transparency, and careful handling of sensitive personal data.",
    "Cloud computing offers elastic infrastructure so startups can scale services without large upfront hardware costs.",
    "Biotechnology advances in gene editing raise both therapeutic promise and ethical debate among policymakers.",
    "Urban planning must balance housing density, public transit, green space, and economic opportunity.",
    "Financial markets react to interest rates, inflation expectations, and geopolitical uncertainty in complex ways.",
    "Sports analytics uses statistical models to evaluate player performance and inform coaching decisions.",
    "Literature reviews synthesize prior research to identify gaps and justify new experimental directions.",
]

_model: SentenceTransformer | None = None
_faiss_index: faiss.Index | None = None
_corpus_embeddings: np.ndarray | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Retrying model download...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def build_faiss_index() -> tuple[faiss.Index, np.ndarray]:
    model = get_model()
    emb = model.encode(SAMPLE_TEXTS, normalize_embeddings=True, show_progress_bar=False)
    emb = np.asarray(emb, dtype=np.float32)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)
    return index, emb


def startup_index() -> None:
    global _faiss_index, _corpus_embeddings
    _faiss_index, _corpus_embeddings = build_faiss_index()


app = FastAPI(title="Plagiarism RAG API", version="1.2.0")

# Wildcard CORS: use credentials=False (browsers forbid * with credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _on_startup() -> None:
    startup_index()


def extract_text_from_txt(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")


def extract_text_from_pdf(raw: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n".join(parts)


def extract_text_from_docx(raw: bytes) -> str:
    doc = Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text_from_upload(filename: str, raw: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".txt"):
        return extract_text_from_txt(raw)
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(raw)
    if lower.endswith(".docx"):
        return extract_text_from_docx(raw)
    raise HTTPException(status_code=400, detail="Unsupported file type. Use .txt, .pdf, or .docx.")


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _split_sentences(text: str) -> list[str]:
    t = normalize_whitespace(text)
    if not t:
        return []
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [p.strip() for p in parts if p.strip()]


def _label_for_sentence_sim(mx: float) -> str:
    if mx >= 0.62:
        return "ai"
    if mx >= 0.38:
        return "mixed"
    return "human"


def extract_code_from_upload(filename: str, raw: bytes) -> str:
    lower = (filename or "").lower()
    allowed = (".py", ".cpp", ".java", ".txt", ".cc", ".h", ".hpp", ".cxx")
    if not any(lower.endswith(ext) for ext in allowed):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use .py, .cpp, .java, or .txt.",
        )
    return raw.decode("utf-8", errors="replace")


def word_tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"\b\w+\b", text.lower()) if len(w) > 1}


def keyword_overlap_score(user_text: str, reference_blob: str) -> float:
    a = word_tokens(user_text)
    b = word_tokens(reference_blob)
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b) or 1
    return inter / union


def placeholder_grammar_metrics(text: str) -> dict[str, str]:
    t = normalize_whitespace(text)
    n_words = len(t.split()) if t else 0
    n_sents = max(1, len(re.split(r"[.!?]+", t)))

    avg_len = n_words / n_sents if n_sents else 0

    if n_words < 8:
        grammar = spelling = punctuation = readability = word_choice = "Insufficient text"
        return {
            "grammar": grammar,
            "spelling": spelling,
            "punctuation": punctuation,
            "readability": readability,
            "word_choice": word_choice,
        }

    long_sentences = sum(1 for s in re.split(r"[.!?]+", t) if len(s.split()) > 35)
    commas = t.count(",")
    if long_sentences >= 2 or avg_len > 28:
        grammar = "Review suggested"
        readability = "Hard"
    elif avg_len > 18:
        grammar = "Good"
        readability = "Medium"
    else:
        grammar = "Good"
        readability = "Easy"

    suspicious = len(re.findall(r"(.)\1{2,}", t))
    spelling = "Minor Issues" if suspicious >= 3 else "Good"

    if t.endswith((".", "!", "?")) and commas < n_sents:
        punctuation = "Good"
    elif not re.search(r"[.!?]$", t.strip()):
        punctuation = "Review suggested"
    else:
        punctuation = "Good"

    rare_short_words = sum(1 for w in re.findall(r"\b\w+\b", t.lower()) if len(w) <= 2)
    word_choice = "Review suggested" if rare_short_words > n_words * 0.15 else "Good"

    return {
        "grammar": grammar,
        "spelling": spelling,
        "punctuation": punctuation,
        "readability": readability,
        "word_choice": word_choice,
    }


def compute_typing_metrics(body_text: str, elapsed_ms: float) -> tuple[float, int, float]:
    words = body_text.split()
    paste_size = len(words)
    elapsed_sec = max(elapsed_ms / 1000.0, 0.05)
    typing_speed_wps = paste_size / elapsed_sec
    return typing_speed_wps, paste_size, elapsed_sec


def detect_ai(similarity_pct: float, paste_size: int, _typing_speed: float) -> str:
    """
    similarity_pct: 0–100; paste_size: word count (client or server).
    _typing_speed reserved for future heuristics (behavior JSON still logged in metrics).
    """
    if similarity_pct > 70 and paste_size > 50:
        return "Likely Copied / AI Generated"
    if similarity_pct > 50:
        return "Edited Content"
    return "Human Written"


def combined_plagiarism_score(max_sim: float, avg_sim: float, kw_overlap: float) -> float:
    combined = 0.6 * max_sim + 0.2 * avg_sim + 0.2 * kw_overlap
    return round(float(combined) * 100, 1)


def _dataset_rel_path(abs_path: str) -> str:
    if not abs_path:
        return ""
    try:
        rel = Path(abs_path).resolve().relative_to(Path(__file__).resolve().parent)
        return str(rel).replace("\\", "/")
    except Exception:
        return str(abs_path).replace("\\", "/")


def _code_ai_label(similarity: float) -> str:
    if similarity > 0.75:
        return "Likely Copied / AI Generated"
    if similarity > 0.5:
        return "Partially Modified"
    return "Original Code"


def _code_recommendations(similarity: float, behavior_score: float) -> list[str]:
    recs: list[str] = []
    if similarity > 0.75:
        recs.extend(
            [
                "Rename variables",
                "Change logic structure",
                "Add custom implementation",
            ]
        )
    elif similarity > 0.5:
        recs.extend(
            [
                "Refactor similar blocks to demonstrate original understanding",
                "Add comments explaining your design choices",
            ]
        )
    else:
        recs.extend(
            [
                "Low plagiarism risk detected.",
                "Code appears to be original.",
            ]
        )
    if behavior_score > 0.55:
        recs.append("Typing pattern suggests large paste events; verify originality.")
    return recs[:8]


CODE_CHECK_FALLBACK: dict[str, Any] = {
    "source_type": "dataset",
    "final_score": 0,
    "label": "Original Code",
    "similarity": 0.0,
    "behavior_score": 0.0,
    "matched_file": "",
    "highlighted_code": "",
    "recommendations": ["Analysis temporarily unavailable. Please try again."],
    "sources": [],
}


def _behavior_from_mapping(b: dict[str, Any]) -> CodeBehaviorIn:
    return CodeBehaviorIn(
        typing_speed=float(b.get("typing_speed") or 0),
        pause_time=float(b.get("pause_time") or 0),
        backspace_count=int(b.get("backspace_count") or 0),
        paste_size=int(b.get("paste_size") or 0),
        typing_variance=float(b.get("typing_variance") or 0),
    )


@app.post("/api/code-check")
async def code_check(request: Request) -> dict[str, Any]:
    """Code plagiarism: SerpAPI match first, then local dataset. Accepts JSON or multipart (code + optional file)."""
    raw_code = ""
    behavior_map: dict[str, Any] = {}

    try:
        ct = (request.headers.get("content-type") or "").lower()
        if "multipart/form-data" in ct:
            form = await request.form()
            raw_code = str(form.get("code") or "")
            beh_raw = form.get("behavior")
            if beh_raw:
                try:
                    behavior_map = json.loads(str(beh_raw))
                except json.JSONDecodeError:
                    behavior_map = {}
            fu = form.get("file")
            if fu is not None and hasattr(fu, "read") and getattr(fu, "filename", None):
                raw_bytes = await fu.read()
                if len(raw_bytes) > 2_000_000:
                    raise HTTPException(status_code=400, detail="File too large (max ~2MB).")
                fname = str(getattr(fu, "filename", "") or "snippet.txt")
                file_text = extract_code_from_upload(fname, raw_bytes)
                raw_code = (file_text or raw_code).strip()
        else:
            try:
                body = await request.json()
            except Exception:
                body = None
            if isinstance(body, dict):
                raw_code = str(body.get("code") or "")
                bh = body.get("behavior")
                behavior_map = bh if isinstance(bh, dict) else {}
            else:
                behavior_map = {}
    except HTTPException:
        raise
    except Exception:
        return dict(CODE_CHECK_FALLBACK)

    raw_code = (raw_code or "").strip()
    if not raw_code:
        out = dict(CODE_CHECK_FALLBACK)
        out["recommendations"] = ["Provide non-empty code or a supported file."]
        return out

    b = _behavior_from_mapping(behavior_map)

    try:
        ensure_code_index()
        behavior_score = predict_behavior_score(
            typing_speed=float(b.typing_speed),
            pause_time=float(b.pause_time),
            backspace_count=int(b.backspace_count),
            paste_size=int(b.paste_size),
            typing_variance=float(b.typing_variance),
        )

        serp_query = build_code_serp_query(raw_code)
        sources = await asyncio.to_thread(search_sources, serp_query)

        if sources:
            model = get_model()
            q_emb = model.encode([raw_code], normalize_embeddings=True, show_progress_bar=False)
            q_emb = np.asarray(q_emb, dtype=np.float32)
            texts_for_embed = [f"{s.get('title', '')} {s.get('snippet', '')}" for s in sources]
            ref_emb = model.encode(texts_for_embed, normalize_embeddings=True, show_progress_bar=False)
            ref_emb = np.asarray(ref_emb, dtype=np.float32)
            sims_matrix = cosine_similarity(q_emb, ref_emb)[0]
            max_sim = float(np.max(sims_matrix))
            per_source_sims = [float(x) for x in sims_matrix]

            if max_sim > 0.5:
                out_sources: list[dict[str, Any]] = []
                for i in range(len(sources)):
                    sim_pct = round(per_source_sims[i] * 100, 1) if i < len(per_source_sims) else 0.0
                    out_sources.append(
                        {
                            "title": sources[i].get("title") or "Untitled",
                            "url": sources[i].get("url") or "",
                            "similarity": sim_pct,
                        }
                    )
                final_score = int(round(max(0.0, min(100.0, max_sim * 100.0))))
                highlighted = highlight_matching_lines(raw_code, "")
                return {
                    "source_type": "external",
                    "final_score": final_score,
                    "label": "Likely Copied from Internet",
                    "similarity": round(max_sim, 4),
                    "behavior_score": round(behavior_score, 4),
                    "matched_file": "",
                    "highlighted_code": highlighted,
                    "recommendations": [
                        "Similarity to public web snippets exceeds the threshold.",
                        "Review sources and cite or rewrite in your own words.",
                    ],
                    "sources": out_sources,
                }

        analysis = analyze_code(raw_code)
        similarity = float(analysis.get("max_similarity", 0.0))
        matched_abs = str(analysis.get("matched_file", "") or "")
        ref_src = get_matched_source(matched_abs)
        highlighted = highlight_matching_lines(raw_code, ref_src)

        final = 0.7 * similarity + 0.3 * behavior_score
        final_score = int(round(max(0.0, min(100.0, final * 100.0))))

        label = _code_ai_label(similarity)
        recs = _code_recommendations(similarity, behavior_score)

        return {
            "source_type": "dataset",
            "final_score": final_score,
            "label": label,
            "similarity": round(similarity, 4),
            "behavior_score": round(behavior_score, 4),
            "matched_file": _dataset_rel_path(matched_abs),
            "highlighted_code": highlighted,
            "recommendations": recs,
            "sources": [],
        }
    except Exception:
        return dict(CODE_CHECK_FALLBACK)


@app.post("/api/auth/signup")
def signup(user: UserRegister) -> dict[str, Any]:
    email_norm = user.email.strip().lower()
    if email_norm in users_db:
        return {"error": "User already exists"}
    users_db[email_norm] = user.password
    token = secrets.token_urlsafe(32)
    tokens_db[token] = email_norm
    return {
        "message": "Signup successful",
        "access_token": token,
        "token_type": "bearer",
        "name": user.name.strip(),
        "email": email_norm,
    }


@app.post("/api/auth/login")
def login(user: UserLogin) -> dict[str, Any]:
    email_norm = user.email.strip().lower()
    if users_db.get(email_norm) == user.password:
        token = secrets.token_urlsafe(32)
        tokens_db[token] = email_norm
        return {"message": "Login successful", "access_token": token, "token_type": "bearer", "email": email_norm}
    return {"error": "Invalid credentials"}


@app.post("/api/auth/password")
def change_password(body: PasswordChange) -> dict[str, Any]:
    if body.new_password != body.confirm_password:
        return {"error": "Passwords do not match"}
    email_norm = body.email.strip().lower()
    if email_norm not in users_db:
        return {"error": "User not found"}
    users_db[email_norm] = body.new_password
    return {"message": "Password updated. Please log in again on all devices."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/check")
async def check_plagiarism(
    text: str = Form(""),
    file: UploadFile | None = File(None),
    elapsed_ms: str = Form("0"),
    behavior: str = Form("{}"),
) -> dict[str, Any]:
    if _faiss_index is None or _corpus_embeddings is None:
        raise HTTPException(status_code=503, detail="Index not ready")

    try:
        elapsed = float(elapsed_ms or "0")
    except ValueError:
        elapsed = 0.0
    if elapsed <= 0:
        elapsed = 3000.0

    body_text = normalize_whitespace(text)

    if file is not None and file.filename:
        raw = await file.read()
        if len(raw) > 5_000_000:
            raise HTTPException(status_code=400, detail="File too large (max ~5MB).")
        extracted = extract_text_from_upload(file.filename, raw)
        body_text = normalize_whitespace(extracted if not body_text else body_text + "\n\n" + extracted)

    if not body_text:
        raise HTTPException(status_code=400, detail="Provide non-empty text or a readable file.")

    # Client behavior: optional JSON { "typing_speed", "paste_size" }
    behavior_parsed: dict[str, Any] = {}
    try:
        behavior_parsed = json.loads(behavior or "{}")
    except json.JSONDecodeError:
        behavior_parsed = {}

    model = get_model()
    q = model.encode([body_text], normalize_embeddings=True, show_progress_bar=False)
    q = np.asarray(q, dtype=np.float32)

    # SerpAPI — real URLs only (no "Local Dataset Source" entries)
    sources: list[dict[str, Any]] = await asyncio.to_thread(search_sources, body_text)
    reference_blob = ""
    per_source_sims: list[float] = []
    ref_for_sentences: np.ndarray | None = None

    if sources:
        texts_for_embed = [f"{s.get('title', '')} {s.get('snippet', '')}" for s in sources]
        reference_blob = " ".join(texts_for_embed)
        ref_emb = model.encode(texts_for_embed, normalize_embeddings=True, show_progress_bar=False)
        ref_emb = np.asarray(ref_emb, dtype=np.float32)
        ref_for_sentences = ref_emb
        sims_matrix = cosine_similarity(q, ref_emb)[0]
        per_source_sims = [float(x) for x in sims_matrix]
        max_sim = float(np.max(sims_matrix))
        avg_sim = float(np.mean(sims_matrix))
        # Replace placeholder similarity with semantic match %; omit snippet from API output
        for i in range(len(sources)):
            sim_pct = round(per_source_sims[i] * 100, 1) if i < len(per_source_sims) else float(sources[i].get("similarity", 0))
            sources[i] = {
                "title": sources[i].get("title") or "Untitled",
                "url": sources[i].get("url") or "",
                "similarity": sim_pct,
            }
    else:
        sims_fb = cosine_similarity(q, _corpus_embeddings)[0]
        max_sim = float(np.max(sims_fb))
        avg_sim = float(np.mean(np.sort(sims_fb)[-min(3, len(sims_fb)) :]))
        reference_blob = " ".join(SAMPLE_TEXTS)
        ref_for_sentences = _corpus_embeddings

    kw = keyword_overlap_score(body_text, reference_blob)
    plagiarism_score = combined_plagiarism_score(max_sim, avg_sim, kw)

    typing_speed_wps, paste_size_words, _ = compute_typing_metrics(body_text, elapsed)
    # Prefer client-sent behavior when present
    client_ts = behavior_parsed.get("typing_speed")
    client_ps = behavior_parsed.get("paste_size")
    if isinstance(client_ts, (int, float)):
        typing_speed_wps = float(client_ts)
    if isinstance(client_ps, int):
        paste_size = client_ps
    elif isinstance(client_ps, float):
        paste_size = int(client_ps)
    else:
        paste_size = paste_size_words

    similarity_pct = max_sim * 100.0
    ai_label = detect_ai(similarity_pct, paste_size, typing_speed_wps)

    grammar_block = placeholder_grammar_metrics(body_text)

    sentence_segments: list[dict[str, str]] = []
    ai_detection_summary = {"ai": 33.3, "mixed": 33.3, "human": 33.4}
    sents = _split_sentences(body_text)
    if sents and ref_for_sentences is not None:
        s_emb = model.encode(sents, normalize_embeddings=True, show_progress_bar=False)
        s_emb = np.asarray(s_emb, dtype=np.float32)
        sims_sent = cosine_similarity(s_emb, ref_for_sentences)
        for i, sent in enumerate(sents):
            mx = float(np.max(sims_sent[i]))
            sentence_segments.append({"text": sent, "label": _label_for_sentence_sim(mx)})
        counts = {"ai": 0, "mixed": 0, "human": 0}
        for seg in sentence_segments:
            counts[seg["label"]] = counts.get(seg["label"], 0) + 1
        tot = sum(counts.values()) or 1
        ai_detection_summary = {
            "ai": round(100.0 * counts["ai"] / tot, 1),
            "mixed": round(100.0 * counts["mixed"] / tot, 1),
            "human": round(100.0 * counts["human"] / tot, 1),
        }

    return {
        "plagiarism_score": plagiarism_score,
        "grammar": grammar_block["grammar"],
        "spelling": grammar_block["spelling"],
        "punctuation": grammar_block["punctuation"],
        "readability": grammar_block["readability"],
        "word_choice": grammar_block["word_choice"],
        "ai_detection": ai_label,
        "ai_detection_summary": ai_detection_summary,
        "sentence_segments": sentence_segments,
        "sources": sources,
        "metrics": {
            "typing_speed": round(typing_speed_wps, 2),
            "paste_size": paste_size,
        },
    }


@app.post("/api/generate-report")
async def generate_report(body: ReportRequest) -> StreamingResponse:
    payload = body.model_dump()
    report_type = (payload.get("type") or "").lower().strip()
    if report_type == "code":
        code_payload = {
            "input_content": payload.get("input_content") or payload.get("input_text") or "",
            "similarity_results": payload.get("similarity_results") or [],
            "final_score": payload.get("final_score") or 0,
            "top_sources": payload.get("top_sources") or [],
        }
        pdf_bytes = generate_code_report(code_payload)
    else:
        if not payload.get("input_text") and payload.get("input_content"):
            payload["input_text"] = str(payload.get("input_content") or "")
        pdf_bytes = generate_report_pdf(payload)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=plagiarism_report.pdf"},
    )


if __name__ == "__main__":
    import os

    import uvicorn

    # Port 8000 often triggers WinError 10013 on Windows; 8787 is a safer default for local dev.
    port = int(os.environ.get("PORT", "8787"))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
