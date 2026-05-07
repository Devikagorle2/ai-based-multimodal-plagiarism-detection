import { useCallback, useRef, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../api.js";

const CODE_EXT = /\.(py|cpp|java|txt|cc|h|hpp|cxx)$/i;

const EXAMPLE_CODE = `class Mobile:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

    def describe(self):
        return f"{self.brand} {self.model}"

phone = Mobile("Acme", "X1")
print(phone.describe())`;

export default function CodeDetection() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const sessionStartRef = useRef(null);
  const keyTimesRef = useRef([]);
  const backspaceCountRef = useRef(0);
  const pasteSizeRef = useRef(0);

  const resetBehavior = useCallback(() => {
    sessionStartRef.current = null;
    keyTimesRef.current = [];
    backspaceCountRef.current = 0;
    pasteSizeRef.current = 0;
  }, []);

  const handleCodeChange = (e) => {
    setCode(e.target.value);
    if (!e.target.value.trim()) {
      resetBehavior();
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Backspace") {
      backspaceCountRef.current += 1;
    }
    const now = Date.now();
    if (sessionStartRef.current === null) {
      sessionStartRef.current = now;
    }
    keyTimesRef.current.push(now);
  };

  const onPaste = (e) => {
    const text = e.clipboardData.getData("text") || "";
    pasteSizeRef.current += text.length;
  };

  const buildBehavior = (currentCode) => {
    const times = keyTimesRef.current;
    const gaps = [];
    for (let i = 1; i < times.length; i += 1) {
      gaps.push((times[i] - times[i - 1]) / 1000);
    }
    const meanGap =
      gaps.length > 0 ? gaps.reduce((a, b) => a + b, 0) / gaps.length : 0.15;
    const variance =
      gaps.length > 0
        ? gaps.reduce((s, g) => s + (g - meanGap) ** 2, 0) / gaps.length
        : 0.05;
    const start = sessionStartRef.current ?? Date.now();
    const elapsedSec = Math.max((Date.now() - start) / 1000, 0.05);
    const len = currentCode.length;
    const typing_speed = len / elapsedSec;

    return {
      typing_speed: Math.round(typing_speed * 100) / 100,
      pause_time: Math.round(meanGap * 1000) / 1000,
      backspace_count: Math.min(99999, backspaceCountRef.current),
      paste_size: Math.min(999999, pasteSizeRef.current),
      typing_variance: Math.round(variance * 1000) / 1000,
    };
  };

  const clearAll = () => {
    setCode("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    setError("");
    resetBehavior();
  };

  const onPickFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) {
      return;
    }
    if (!CODE_EXT.test(f.name)) {
      setError("Please choose a .py, .cpp, .java, or .txt file.");
      e.target.value = "";
      return;
    }
    setError("");
    const reader = new FileReader();
    reader.onload = () => {
      setCode(String(reader.result || ""));
      sessionStartRef.current = Date.now();
    };
    reader.onerror = () => setError("Could not read file.");
    reader.readAsText(f);
  };

  const loadExample = () => {
    setError("");
    setCode(EXAMPLE_CODE);
    resetBehavior();
    sessionStartRef.current = Date.now();
  };

  const canScan = Boolean(code.trim());
  const lineCount = code ? code.split(/\n/).length : 0;
  const charCount = code.length;

  const scan = async () => {
    setError("");
    if (!canScan) {
      setError("Paste or type code before scanning.");
      return;
    }

    setLoading(true);
    const behavior = buildBehavior(code);

    try {
      const form = new FormData();
      form.append("code", code);
      form.append("behavior", JSON.stringify(behavior));

      const { data } = await axios.post(`${API_BASE}/api/code-check`, form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
      });
      navigate("/code-results", { state: { result: data, inputCode: code } });
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Request failed. Is the backend running?";
      setError(typeof msg === "string" ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-[calc(100vh-8rem)] bg-gradient-to-br from-emerald-50 via-white to-teal-50">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#16a34a] text-2xl font-bold text-white shadow-md">
            {"</>"}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 sm:text-3xl">
            Code Plagiarism Checker
          </h1>
          <p className="mt-2 text-sm text-gray-600 sm:text-base">
            Semantic match on a local code corpus + behavioral signals from your typing session.
          </p>
        </div>

        <section className="rounded-2xl bg-white p-6 shadow-md ring-1 ring-gray-100 sm:p-8">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <label className="text-sm font-semibold text-gray-800">Paste your code here</label>
            <div className="flex flex-wrap gap-2">
              <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm transition hover:bg-gray-50">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".py,.cpp,.java,.txt,.h,.hpp,.cc,.cxx"
                  className="sr-only"
                  onChange={onPickFile}
                />
                <span aria-hidden>📄</span> Upload file
              </label>
              <button
                type="button"
                onClick={clearAll}
                className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 shadow-sm transition hover:bg-gray-50"
              >
                <span aria-hidden>↺</span> Clear
              </button>
              <button
                type="button"
                onClick={loadExample}
                className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/80 px-3 py-1.5 text-xs font-medium text-emerald-900 transition hover:bg-emerald-100"
              >
                <span aria-hidden>💡</span> Example
              </button>
            </div>
          </div>

          <textarea
            value={code}
            onChange={handleCodeChange}
            onKeyDown={onKeyDown}
            onPaste={onPaste}
            spellCheck={false}
            placeholder="# Paste Python or other source code…"
            rows={16}
            className="w-full resize-y rounded-xl border border-gray-200 bg-gray-50/90 p-4 font-mono text-sm leading-relaxed text-gray-900 shadow-inner outline-none ring-0 transition focus:border-[#16a34a] focus:ring-2 focus:ring-[#16a34a]/25"
          />

          <div className="mt-2 flex flex-wrap justify-between gap-2 text-xs text-gray-500">
            <span>{charCount} characters</span>
            <span>{lineCount} lines</span>
          </div>

          {error && (
            <p
              className="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm text-red-800 ring-1 ring-red-100"
              role="alert"
            >
              {error}
            </p>
          )}

          <div className="mt-6 flex flex-col items-center gap-3">
            <button
              type="button"
              onClick={scan}
              disabled={loading || !canScan}
              className="inline-flex min-w-[220px] items-center justify-center gap-2 rounded-xl bg-[#16a34a] px-6 py-3.5 text-sm font-semibold text-white shadow-md transition hover:bg-green-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading && (
                <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" aria-hidden>
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              {loading ? "Analyzing…" : "Analyze for plagiarism"}
            </button>
            <p className="flex items-center gap-1.5 text-xs text-gray-500">
              <span aria-hidden>ⓘ</span>
              Behavioral tracking is enabled while you type (speed, pauses, backspaces, paste size).
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
