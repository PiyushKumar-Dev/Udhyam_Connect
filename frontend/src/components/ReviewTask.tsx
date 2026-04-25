import type { MatchPair } from "../types";

interface ReviewTaskProps {
  match: MatchPair;
  note: string;
  reviewer: string;
  onNoteChange: (value: string) => void;
  onReviewerChange: (value: string) => void;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}

function pct(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function ReviewTask({
  match,
  note,
  reviewer,
  onNoteChange,
  onReviewerChange,
  onApprove,
  onReject,
  busy
}: ReviewTaskProps) {
  const rows = [
    ["Name", match.record_a.raw_name, match.record_b.raw_name, pct(match.evidence.name_score)],
    ["Address", match.record_a.raw_address, match.record_b.raw_address, pct(match.evidence.address_score)],
    ["PAN", match.record_a.pan ?? "N/A", match.record_b.pan ?? "N/A", pct(match.evidence.pan_score)],
    ["GSTIN", match.record_a.gstin ?? "N/A", match.record_b.gstin ?? "N/A", pct(match.evidence.gstin_score)],
    [
      "Licenses",
      match.record_a.license_ids.join(", ") || "N/A",
      match.record_b.license_ids.join(", ") || "N/A",
      pct(match.evidence.license_score)
    ]
  ];

  return (
    <div className="space-y-6">
      <div className="panel p-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="font-display text-2xl font-semibold text-slate-900">
              {match.record_a.raw_name} vs {match.record_b.raw_name}
            </h2>
            <p className="text-sm text-muted">Confidence {pct(match.confidence)}</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-muted">
              <tr>
                <th className="px-4 py-3">Field</th>
                <th className="px-4 py-3">Record A value</th>
                <th className="px-4 py-3">Record B value</th>
                <th className="px-4 py-3">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border text-sm text-slate-700">
              {rows.map(([field, aValue, bValue, score]) => (
                <tr key={field}>
                  <td className="px-4 py-3 font-semibold">{field}</td>
                  <td className="px-4 py-3">{aValue}</td>
                  <td className="px-4 py-3">{bValue}</td>
                  <td className="px-4 py-3 font-semibold">{score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-100 ring-1 ring-blue-200">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-white">
            <span className="text-[10px] font-bold italic">AI</span>
          </div>
          <h3 className="text-sm font-bold uppercase tracking-widest text-primary/80">Intelligent Insight</h3>
        </div>
        <p className="mt-4 text-base font-medium leading-relaxed text-slate-800 italic">
          "{match.explanation}"
        </p>
      </div>

      <div className="panel p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-900" htmlFor="reviewer">
              Reviewer
            </label>
            <input
              className="w-full rounded-xl border border-border px-4 py-3 outline-none ring-primary/20 focus:ring"
              id="reviewer"
              onChange={(event) => onReviewerChange(event.target.value)}
              value={reviewer}
            />
          </div>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-900" htmlFor="note">
              Note
            </label>
            <textarea
              className="h-28 w-full rounded-xl border border-border px-4 py-3 outline-none ring-primary/20 focus:ring"
              id="note"
              onChange={(event) => onNoteChange(event.target.value)}
              placeholder="Add optional reviewer context."
              value={note}
            />
          </div>
        </div>

        <div className="mt-6 grid gap-3 md:grid-cols-2">
          <button
            className="rounded-2xl bg-success px-6 py-4 text-base font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
            disabled={busy || !reviewer.trim()}
            onClick={onApprove}
            type="button"
          >
            Approve Match
          </button>
          <button
            className="rounded-2xl bg-danger px-6 py-4 text-base font-semibold text-white transition hover:opacity-90 disabled:opacity-60"
            disabled={busy || !reviewer.trim()}
            onClick={onReject}
            type="button"
          >
            Reject Match
          </button>
        </div>
      </div>
    </div>
  );
}
