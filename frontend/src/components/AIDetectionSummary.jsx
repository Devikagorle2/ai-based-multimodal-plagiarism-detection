const AI = "#facc15";
const MIXED = "#9ca3af";
const HUMAN = "#4ade80";

export default function AIDetectionSummary({ aiPct = 0, mixedPct = 0, humanPct = 0 }) {
  const a = Number(aiPct) || 0;
  const m = Number(mixedPct) || 0;
  const h = Number(humanPct) || 0;
  const top = Math.max(a, m, h);
  const dominant =
    top <= 0 ? "—" : a === top && a >= m && a >= h ? "AI" : m === top && m >= a && m >= h ? "Mixed" : "Human";

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">AI-style breakdown</p>
      <div className="mt-3 flex items-start gap-4">
        <div
          className="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-4 text-xs font-bold text-gray-800 shadow-inner"
          style={{
            borderColor:
              dominant === "AI" ? AI : dominant === "Mixed" ? MIXED : dominant === "Human" ? HUMAN : "#e5e7eb",
            backgroundColor:
              dominant === "—"
                ? "#f9fafb"
                : `${dominant === "AI" ? AI : dominant === "Mixed" ? MIXED : HUMAN}22`,
          }}
          title={dominant}
        >
          {dominant === "—" ? "?" : dominant.slice(0, 2)}
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <p className="text-sm text-gray-700">
            Sentence labels are heuristic (similarity to matched reference text).
          </p>
          <div className="flex flex-wrap gap-2">
            <span
              className="inline-flex items-center gap-1 rounded-full border-2 px-3 py-1 text-xs font-semibold"
              style={{ borderColor: AI, color: "#854d0e", backgroundColor: "#fef9c3" }}
            >
              AI {a}%
            </span>
            <span
              className="inline-flex items-center gap-1 rounded-full border-2 px-3 py-1 text-xs font-semibold text-gray-700"
              style={{ borderColor: MIXED, backgroundColor: "#f3f4f6" }}
            >
              Mixed {m}%
            </span>
            <span
              className="inline-flex items-center gap-1 rounded-full border-2 px-3 py-1 text-xs font-semibold text-gray-800"
              style={{ borderColor: HUMAN, backgroundColor: "#dcfce7" }}
            >
              Human {h}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
