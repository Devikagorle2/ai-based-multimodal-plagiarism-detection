import { useMemo, useState } from "react";

const labelTitle = {
  ai: "AI-generated",
  mixed: "Mixed",
  human: "Human-written",
};

const scoreToPalette = (score) => {
  if (score >= 80) return { bg: "bg-[#7f1d1d]", text: "text-white" };
  if (score >= 60) return { bg: "bg-[#dc2626]", text: "text-white" };
  if (score >= 30) return { bg: "bg-[#eab308]", text: "text-gray-900" };
  return { bg: "bg-[#16a34a]", text: "text-white" };
};

const labelFallbackScore = (label) => {
  if (label === "ai") return 75;
  if (label === "mixed") return 45;
  if (label === "human") return 15;
  return 0;
};

export default function TextHighlighter({ segments = [] }) {
  const [filter, setFilter] = useState("all");
  const [aiOnly, setAiOnly] = useState(false);

  const list = useMemo(() => {
    const s = Array.isArray(segments) ? segments : [];
    let out = s.filter((x) => x && typeof x.text === "string");
    if (aiOnly) out = out.filter((x) => x.label === "ai");
    else if (filter !== "all") out = out.filter((x) => x.label === filter);
    return out;
  }, [segments, filter, aiOnly]);

  if (!segments || segments.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-gray-200 bg-gray-50/80 px-3 py-4 text-sm text-gray-500">
        Run a scan to see sentence-level highlights.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {["all", "ai", "human", "mixed"].map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setFilter(key);
              setAiOnly(false);
            }}
            className={[
              "rounded-lg px-3 py-1.5 text-xs font-semibold transition",
              filter === key && !aiOnly ? "bg-[#16a34a] text-white shadow-sm" : "bg-gray-100 text-gray-700 hover:bg-gray-200",
            ].join(" ")}
          >
            {key === "all" ? "All" : key === "ai" ? "AI" : key === "human" ? "Human" : "Mixed"}
          </button>
        ))}
        <label className="ml-auto flex cursor-pointer items-center gap-2 text-xs text-gray-600">
          <input type="checkbox" checked={aiOnly} onChange={(e) => setAiOnly(e.target.checked)} className="rounded border-gray-300" />
          Show AI sentences only
        </label>
      </div>

      <div className="rounded-xl border border-gray-100 bg-white/90 p-3 leading-relaxed">
        {list.map((seg, i) => {
          const lab = seg.label === "mixed" || seg.label === "human" || seg.label === "ai" ? seg.label : "human";
          const score = typeof seg.similarity === "number" ? seg.similarity : labelFallbackScore(lab);
          const palette = scoreToPalette(score);
          return (
            <span
              key={`${i}-${seg.text.slice(0, 12)}`}
              title={labelTitle[lab] || ""}
              className={[
                "inline rounded-md px-2 py-1 text-sm",
                palette.bg,
                palette.text,
              ].join(" ")}
            >
              {seg.text}
              {i < list.length - 1 ? " " : ""}
            </span>
          );
        })}
      </div>
    </div>
  );
}
