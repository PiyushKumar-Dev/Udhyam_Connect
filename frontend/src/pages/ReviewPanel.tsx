import { CheckCircle2, ListChecks } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { AuthSwitcher } from "../components/AuthSwitcher";
import { useDecideMatch, usePendingMatches } from "../api/hooks";
import { ReviewTask as ReviewTaskPanel } from "../components/ReviewTask";

export function ReviewPanel() {
  const pendingMatches = usePendingMatches();
  const decideMatch = useDecideMatch();
  const [selectedId, setSelectedId] = useState<string>("");
  const [reviewer, setReviewer] = useState("review.analyst");
  const [note, setNote] = useState("");
  const [confirmation, setConfirmation] = useState("");

  useEffect(() => {
    if (pendingMatches.data?.length && !pendingMatches.data.find((match) => match.id === selectedId)) {
      setSelectedId(pendingMatches.data[0].id);
    }
  }, [pendingMatches.data, selectedId]);

  const activeMatch = pendingMatches.data?.find((match) => match.id === selectedId) ?? pendingMatches.data?.[0];

  async function handleDecision(decision: "APPROVE" | "REJECT") {
    if (!activeMatch) {
      return;
    }
    await decideMatch.mutateAsync({
      matchId: activeMatch.id,
      payload: { decision, reviewer, note }
    });
    setConfirmation(
      decision === "APPROVE" ? "Match approved and records merged." : "Match rejected and future auto-linking blocked."
    );
    setNote("");
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
      <div className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-primary">Review workflow</p>
          <h1 className="font-display text-4xl font-semibold text-slate-900">Pending match queue</h1>
          <p className="mt-2 text-sm text-muted">
            High-confidence ambiguous matches are sorted first so reviewers can clear the most likely merges quickly.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <AuthSwitcher />
          <Link className="text-sm font-semibold text-primary" to="/">
            Back to dashboard
          </Link>
        </div>
      </div>

      <div className="mb-4 rounded-2xl border border-border bg-white px-4 py-3 text-sm text-muted lg:hidden">
        <label className="mb-2 block font-semibold text-slate-900" htmlFor="match-select">
          Queue
        </label>
        <select
          className="w-full rounded-xl border border-border px-4 py-3"
          id="match-select"
          onChange={(event) => setSelectedId(event.target.value)}
          value={activeMatch?.id ?? ""}
        >
          {pendingMatches.data?.map((match) => (
            <option key={match.id} value={match.id}>
              {match.record_a.raw_name} vs {match.record_b.raw_name}
            </option>
          ))}
        </select>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="panel hidden max-h-[75vh] overflow-y-auto lg:block">
          <div className="border-b border-border px-5 py-4">
            <div className="flex items-center gap-2">
              <ListChecks className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-slate-900">Queue list</h2>
            </div>
          </div>
          <div className="divide-y divide-border">
            {pendingMatches.data?.map((match) => (
              <button
                className={`w-full px-5 py-4 text-left transition ${
                  activeMatch?.id === match.id ? "bg-blue-50" : "hover:bg-slate-50"
                }`}
                key={match.id}
                onClick={() => setSelectedId(match.id)}
                type="button"
              >
                <p className="font-semibold text-slate-900">
                  {match.record_a.raw_name} vs {match.record_b.raw_name}
                </p>
                <p className="mt-1 text-xs text-muted">Confidence {Math.round(match.confidence * 100)}%</p>
              </button>
            ))}
          </div>
        </aside>

        <section>
          {confirmation && (
            <div className="mb-4 flex items-center gap-3 rounded-2xl border border-green-200 bg-green-50 px-5 py-4 text-sm text-success">
              <CheckCircle2 className="h-5 w-5" />
              {confirmation}
            </div>
          )}

          {activeMatch ? (
            <ReviewTaskPanel
              busy={decideMatch.isPending}
              match={activeMatch}
              note={note}
              onApprove={() => handleDecision("APPROVE")}
              onNoteChange={setNote}
              onReject={() => handleDecision("REJECT")}
              onReviewerChange={setReviewer}
              reviewer={reviewer}
            />
          ) : (
            <div className="panel px-6 py-16 text-center text-sm text-muted">
              No open review tasks remain.
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
