import { ArrowLeft, Clipboard, Database, Layers3, Link2, TimerReset } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { AuthSwitcher } from "../components/AuthSwitcher";
import { useEntity } from "../api/hooks";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { EvidenceTimeline } from "../components/EvidenceTimeline";
import { JsonTree } from "../components/JsonTree";
import { LinkedRecords } from "../components/LinkedRecords";
import { RiskBadge } from "../components/RiskBadge";
import { StatusBadge } from "../components/StatusBadge";

const tabs = ["Overview", "Linked Records", "Activity Timeline", "Raw Data"] as const;

export function BusinessProfile() {
  const { ubid } = useParams();
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Overview");
  const entity = useEntity(ubid);

  if (!entity.data) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-12 text-sm text-muted">
        Loading business profile...
      </div>
    );
  }

  const detail = entity.data;
  const firstPan = detail.linked_records.find((record) => record.pan)?.pan ?? "N/A";
  const firstGstin = detail.linked_records.find((record) => record.gstin)?.gstin ?? "N/A";
  const primaryAddress = detail.linked_records[0]?.raw_address ?? "N/A";
  const sourceSystems = [...new Set(detail.linked_records.map((record) => record.source_system))];
  const lastEvent = detail.activity_timeline[0];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <Link className="inline-flex items-center gap-2 text-sm font-semibold text-primary" to="/">
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>
        <AuthSwitcher />
      </div>

      <section className="panel p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h1 className="font-display text-4xl font-semibold text-slate-900">{detail.canonical_name}</h1>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <span className="rounded-full bg-blue-100 px-4 py-2 font-mono text-sm font-semibold text-primary">
                {detail.ubid}
              </span>
              <button
                className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-semibold text-slate-700"
                onClick={() => navigator.clipboard.writeText(detail.ubid)}
                type="button"
              >
                <Clipboard className="h-4 w-4" />
                Copy UBID
              </button>
              <StatusBadge status={detail.status} />
              <RiskBadge level={detail.risk.level} score={detail.risk.score} />
            </div>
          </div>

          <div className="w-full max-w-sm space-y-3">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">Confidence score</p>
                <span className="text-xs text-muted" title={detail.explanation}>
                  Why this score?
                </span>
              </div>
              <ConfidenceBadge value={detail.confidence} />
              <p className="mt-3 text-sm text-slate-600">{detail.explanation}</p>
            </div>
            <div className="rounded-2xl bg-red-50 p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">Anomaly watch</p>
                <RiskBadge level={detail.risk.level} score={detail.risk.score} />
              </div>
              <ul className="space-y-2 text-sm text-slate-700">
                {detail.risk.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
            <p className="text-sm text-muted">Last updated {new Date(detail.updated_at).toLocaleString()}</p>
          </div>
        </div>
      </section>

      <div className="mt-8 flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            className={`rounded-full px-4 py-2 text-sm font-semibold ${
              activeTab === tab ? "bg-primary text-white" : "bg-white text-slate-700"
            }`}
            key={tab}
            onClick={() => setActiveTab(tab)}
            type="button"
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" && (
        <section className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="panel p-6">
            <div className="mb-4 flex items-center gap-2">
              <Layers3 className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-slate-900">Key fields</h2>
            </div>
            <dl className="grid gap-4 text-sm">
              <div>
                <dt className="text-muted">PAN</dt>
                <dd className="mt-1 font-mono text-slate-900">{firstPan}</dd>
              </div>
              <div>
                <dt className="text-muted">GSTIN</dt>
                <dd className="mt-1 font-mono text-slate-900">{firstGstin}</dd>
              </div>
              <div>
                <dt className="text-muted">Address</dt>
                <dd className="mt-1 text-slate-900">{primaryAddress}</dd>
              </div>
              <div>
                <dt className="text-muted">Source systems</dt>
                <dd className="mt-2 flex flex-wrap gap-2">
                  {sourceSystems.map((source) => (
                    <span className="status-pill bg-slate-100 text-slate-700" key={source}>
                      {source}
                    </span>
                  ))}
                </dd>
              </div>
            </dl>
          </div>

          <div className="panel p-6">
            <div className="mb-4 flex items-center gap-2">
              <TimerReset className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-slate-900">Activity summary</h2>
            </div>
            <div className="space-y-4 text-sm">
              <div>
                <p className="text-muted">Last event</p>
                <p className="mt-1 text-slate-900">
                  {lastEvent ? `${new Date(lastEvent.event_date).toLocaleDateString()} | ${lastEvent.event_type}` : "No events recorded"}
                </p>
              </div>
              <div>
                <p className="text-muted">Event count</p>
                <p className="mt-1 text-slate-900">{detail.activity_timeline.length}</p>
              </div>
              <div>
                <p className="text-muted">Classification reasoning</p>
                <p className="mt-1 leading-6 text-slate-900">{detail.status_reason}</p>
              </div>
            </div>
          </div>
        </section>
      )}

      {activeTab === "Linked Records" && (
        <section className="mt-6">
          <LinkedRecords canonicalName={detail.canonical_name} records={detail.linked_records} />
        </section>
      )}

      {activeTab === "Activity Timeline" && (
        <section className="mt-6 space-y-4">
          {detail.status === "DORMANT" && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-warning">
              No activity in 12 months. This business is currently classified as dormant.
            </div>
          )}
          <div className="panel p-6">
            <EvidenceTimeline events={detail.activity_timeline} />
          </div>
        </section>
      )}

      {activeTab === "Raw Data" && (
        <section className="mt-6 panel p-6">
          <div className="mb-4 flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-slate-900">Entity payload</h2>
          </div>
          <JsonTree data={detail} />
        </section>
      )}

      <div className="mt-8 panel p-5">
        <div className="flex items-center gap-3">
          <Link2 className="h-5 w-5 text-primary" />
          <p className="text-sm text-slate-700">
            Linked records remain reversible through the review log and match evidence trail.
          </p>
        </div>
      </div>
    </div>
  );
}
