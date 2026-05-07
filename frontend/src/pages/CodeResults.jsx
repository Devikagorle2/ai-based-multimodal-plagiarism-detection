import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import axios from "axios";
import { API_BASE } from "../api.js";

function num(v, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function labelStyle(label) {
  const s = String(label || "");
  if (s.includes("Likely Copied") || s.includes("Internet")) return "bg-red-100 text-red-800 ring-red-200";
  if (s.includes("Partially")) return "bg-amber-100 text-amber-900 ring-amber-200";
  return "bg-emerald-100 text-emerald-900 ring-emerald-200";
}

export default function CodeResults() {
  const location = useLocation();
  const raw = location.state?.result;
  const inputCode = typeof location.state?.inputCode === "string" ? location.state.inputCode : "";
  const [downloading, setDownloading] = useState(false);

  if (!raw || typeof raw !== "object") {
    return (
      <main className="mx-auto max-w-3xl px-4 py-16 text-center">
        <p className="text-lg font-medium text-gray-800">No results found</p>
        <p className="mt-2 text-sm text-gray-600">Run an analysis from the code checker first.</p>
        <Link
          to="/code"
          className="mt-6 inline-flex rounded-xl bg-[#16a34a] px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-green-700"
        >
          Go to code checker
        </Link>
      </main>
    );
  }

  const sourceType = raw.source_type === "external" ? "external" : "dataset";
  const finalScore = Math.round(num(raw.final_score, 0));
  const similarity = num(raw.similarity, 0);
  const similarityPct = Math.round(similarity * 100);
  const behaviorScore = num(raw.behavior_score, 0);
  const behaviorPct = Math.round(behaviorScore * 100);
  const label = String(raw.label || "Original Code");
  const matchedFile = raw.matched_file != null ? String(raw.matched_file) : "";
  const highlighted =
    typeof raw.highlighted_code === "string" ? raw.highlighted_code : "";
  const recommendations = Array.isArray(raw.recommendations) ? raw.recommendations : [];
  const sources = Array.isArray(raw.sources) ? raw.sources : [];

  const safeRecs = recommendations
    .filter((x) => typeof x === "string" && x.trim())
    .map((x) => x.trim());

  const scoreHue =
    finalScore >= 70 ? "from-red-500 to-rose-600" : finalScore >= 40 ? "from-amber-500 to-orange-500" : "from-emerald-500 to-teal-600";

  const paletteColor = (score) => {
    if (score >= 80) return "text-[#7f1d1d]";
    if (score >= 60) return "text-[#dc2626]";
    if (score >= 30) return "text-[#eab308]";
    return "text-[#16a34a]";
  };

  const buildCodeSimilarityResults = () => {
    if (typeof highlighted !== "string") return [];
    const lines = highlighted.split("\n");
    return lines.map((line, idx) => {
      const score = line.includes("<mark") ? 85 : 10;
      return { line_number: idx + 1, similarity: score };
    });
  };

  const downloadCodeReport = async () => {
    if (!raw) return;
    setDownloading(true);
    try {
      const response = await axios({
        url: `${API_BASE}/api/generate-report`,
        method: "POST",
        data: {
          type: "code",
          input_content: inputCode || "",
          similarity_results: buildCodeSimilarityResults(),
          final_score: finalScore,
          top_sources: sources.map((s) => ({
            url: s.url || "",
            score: typeof s.similarity === "number" ? s.similarity : num(s.similarity, 0),
          })),
        },
        responseType: "blob",
        timeout: 120000,
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `code_report_${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <main className="min-h-[calc(100vh-8rem)] bg-gradient-to-br from-emerald-50/80 via-white to-slate-50">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <h1 className="flex items-center gap-2 text-xl font-bold text-gray-900 sm:text-2xl">
            <span aria-hidden className="text-[#16a34a]">
              📊
            </span>
            Analysis results
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={downloadCodeReport}
              disabled={downloading}
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-800 shadow-sm transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {downloading ? "Preparing report..." : "Download Code Report"}
            </button>
            <Link
              to="/code"
              className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-800 shadow-sm transition hover:bg-gray-50"
            >
              New scan
            </Link>
          </div>
        </div>

        <section className="rounded-2xl bg-white p-6 shadow-md ring-1 ring-gray-100 sm:p-8">
          <p className="mb-4 text-sm font-medium text-gray-600">
            {sourceType === "external" ? "External Sources (SerpAPI)" : "Best Match (Dataset)"}
          </p>

          <div className="flex flex-col items-center gap-4">
            <div
              className={`flex h-40 w-40 flex-col items-center justify-center rounded-full bg-gradient-to-br ${scoreHue} px-4 text-center text-white shadow-lg`}
            >
              <span className="text-4xl font-bold tabular-nums leading-none">{finalScore}%</span>
              <span className="mt-2 text-xs font-medium opacity-95">Plagiarism score</span>
            </div>
            <span
              className={`rounded-full px-4 py-1.5 text-sm font-semibold ring-1 ${labelStyle(label)}`}
            >
              {label}
            </span>
          </div>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Semantic similarity</p>
              <p className="mt-1 text-2xl font-bold tabular-nums text-gray-900">{similarityPct}%</p>
            </div>
            <div className="rounded-xl border border-gray-100 bg-gray-50/80 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Behavior score</p>
              <p className="mt-1 text-2xl font-bold tabular-nums text-gray-900">{behaviorPct}%</p>
            </div>
            {sourceType === "dataset" ? (
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-4 sm:col-span-2">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Best Match (Dataset)</p>
                <p className="mt-1 break-all font-mono text-sm text-gray-900">
                  {matchedFile || "—"}
                </p>
              </div>
            ) : null}
          </div>

          {sourceType === "external" && sources.length > 0 ? (
            <div className="mt-8 rounded-xl border border-gray-100 bg-gray-50/50 p-4">
              <h2 className="text-sm font-semibold text-gray-900">External Sources (SerpAPI)</h2>
              <ul className="mt-3 space-y-3">
                {sources.map((s, i) => (
                  <li key={`${s.url}-${i}`} className="rounded-lg border border-gray-100 bg-white p-3 text-sm">
                    <a
                      href={s.url || "#"}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={`font-semibold hover:underline ${paletteColor(num(s.similarity, 0))}`}
                    >
                      {s.title || "Untitled"}
                    </a>
                    <p className="mt-1 break-all text-xs text-gray-600">{s.url || ""}</p>
                    <p className={`mt-1 text-xs font-medium tabular-nums ${paletteColor(num(s.similarity, 0))}`}>
                      Match: {typeof s.similarity === "number" ? `${s.similarity}%` : `${num(s.similarity, 0)}%`}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="mt-8">
            <h2 className="text-sm font-semibold text-gray-900">Highlighted code (matches corpus)</h2>
            <div className="mt-3 overflow-x-auto rounded-xl border border-gray-200 bg-slate-900 p-4 text-left shadow-inner">
              {highlighted ? (
                <pre
                  className="whitespace-pre-wrap break-words font-mono text-sm text-slate-100 [&_mark]:text-gray-900"
                  dangerouslySetInnerHTML={{ __html: highlighted }}
                />
              ) : (
                <p className="text-sm text-slate-400">No highlight data.</p>
              )}
            </div>
          </div>

          <div className="mt-8">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
              <span aria-hidden>💡</span> Recommendations
            </h2>
            <ul className="mt-3 space-y-2">
              {safeRecs.length === 0 && (
                <li className="rounded-lg border border-gray-100 bg-white px-4 py-3 text-sm text-gray-600">
                  No specific recommendations.
                </li>
              )}
              {safeRecs.map((line, i) => (
                <li
                  key={`${i}-${line.slice(0, 24)}`}
                  className="flex gap-3 rounded-lg border border-emerald-100 bg-emerald-50/40 px-4 py-3 text-sm text-gray-800"
                >
                  <span className="text-emerald-600" aria-hidden>
                    ✓
                  </span>
                  <span>{line}</span>
                </li>
              ))}
            </ul>
          </div>

          <p className="mt-8 text-center text-xs text-gray-500">
            {sourceType === "external"
              ? "Score reflects semantic similarity between your code and web search snippets."
              : "Final score combines ~70% semantic similarity and ~30% behavioral signals."}
          </p>
        </section>
      </div>
    </main>
  );
}
