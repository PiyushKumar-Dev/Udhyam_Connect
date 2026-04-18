import { AlertTriangle, ArrowRight, Building2, CircleAlert, Inbox, MapPin, X } from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { useAuth } from "../auth";
import { useEntities, useStats } from "../api/hooks";
import { AuthSwitcher } from "../components/AuthSwitcher";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { RiskBadge } from "../components/RiskBadge";
import { SearchBar } from "../components/SearchBar";
import { StatusBadge } from "../components/StatusBadge";

const filters = ["ALL", "ACTIVE", "DORMANT", "CLOSED"] as const;

export function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const pincodeParam = searchParams.get("pincode") || undefined;
  const [statusFilter, setStatusFilter] = useState<(typeof filters)[number]>("ALL");
  const [riskFilter, setRiskFilter] = useState<string | undefined>(undefined);
  const [page, setPage] = useState(1);
  const stats = useStats();
  const entities = useEntities({
    status: statusFilter === "ALL" ? undefined : statusFilter,
    risk_level: riskFilter,
    pincode: pincodeParam,
    page,
    limit: 20
  });

  const clearPincode = () => {
    searchParams.delete("pincode");
    setSearchParams(searchParams);
  };

  useEffect(() => {
    setPage(1);
  }, [statusFilter, riskFilter, pincodeParam]);

  const totalPages = entities.data ? Math.max(1, Math.ceil(entities.data.total / 20)) : 1;

  return (
    <div className="min-h-screen">
      <nav className="sticky top-0 z-30 border-b border-border bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <p className="font-display text-2xl font-semibold text-primary">Udhyam Connect</p>
            <p className="text-sm text-muted">Unified Business Identity & Activity Intelligence</p>
          </div>
          <div className="flex items-center gap-3">
            <AuthSwitcher />
            <Link
              className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700"
              to="/pincodes"
            >
              <MapPin className="h-3.5 w-3.5" />
              Pincode Explorer
            </Link>
            <Link
              className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-blue-50 px-4 py-2 text-sm font-semibold text-primary"
              to="/graph"
            >
              Graph Explorer
            </Link>
            {user.role !== "viewer" ? (
              <Link
                className="inline-flex items-center gap-2 rounded-full border border-danger/20 bg-red-50 px-4 py-2 text-sm font-semibold text-danger"
                to="/review"
              >
                Review Queue ({stats.data?.pending_review ?? 0})
              </Link>
            ) : null}
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {pincodeParam && (
          <div className="mb-6 flex items-center gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3">
            <MapPin className="h-5 w-5 text-emerald-700" />
            <p className="text-sm font-semibold text-emerald-800">
              Filtered by pincode: <span className="font-mono">{pincodeParam}</span>
            </p>
            <button
              className="ml-auto flex items-center gap-1 rounded-full border border-emerald-300 bg-white px-3 py-1 text-xs font-semibold text-emerald-700 hover:bg-emerald-100"
              onClick={clearPincode}
              type="button"
            >
              <X className="h-3 w-3" />
              Clear
            </button>
          </div>
        )}
        <section className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Total Businesses</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {stats.data?.total_businesses ?? "-"}
                </p>
              </div>
              <Building2 className="h-8 w-8 text-primary" />
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Active</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">{stats.data?.active ?? "-"}</p>
              </div>
              <span className="status-pill bg-green-100 text-success">LIVE</span>
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Dormant</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {stats.data?.dormant ?? "-"}
                </p>
              </div>
              <span className="status-pill bg-amber-100 text-warning">WATCH</span>
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Pending Review</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {stats.data?.pending_review ?? "-"}
                </p>
              </div>
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${
                  (stats.data?.pending_review ?? 0) > 0
                    ? "animate-pulse border-danger/20 bg-red-100 text-danger"
                    : "border-border bg-slate-100 text-muted"
                }`}
              >
                Queue
              </span>
            </div>
          </div>
          <div
            className={`panel p-5 cursor-pointer transition hover:border-danger/30 ${
              riskFilter === "HIGH" ? "ring-2 ring-danger border-danger" : ""
            }`}
            onClick={() => setRiskFilter(riskFilter === "HIGH" ? undefined : "HIGH")}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">High Risk</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {stats.data?.high_risk_entities ?? "-"}
                </p>
              </div>
              <span className="status-pill bg-red-100 text-danger">WATCH</span>
            </div>
          </div>
        </section>

        <section className="mb-8">
          <SearchBar />
        </section>

        <section className="panel overflow-hidden">
          <div className="flex flex-col gap-4 border-b border-border px-5 py-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap gap-2">
              {filters.map((filter) => (
                <button
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    statusFilter === filter
                      ? "bg-primary text-white"
                      : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                  key={filter}
                  onClick={() => setStatusFilter(filter)}
                  type="button"
                >
                  {filter === "ALL" ? "All" : filter}
                </button>
              ))}
              <div className="mx-2 w-px bg-border" />
              <button
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition ${
                  riskFilter === "HIGH"
                    ? "bg-danger text-white"
                    : "bg-red-50 text-danger hover:bg-red-100"
                }`}
                onClick={() => setRiskFilter(riskFilter === "HIGH" ? undefined : "HIGH")}
                type="button"
              >
                High Risk Only
              </button>
            </div>
            <div className="text-sm text-muted">
              {stats.data ? `${stats.data.auto_linked_today} auto-linked today` : "Loading stats..."}
            </div>
          </div>

          <div className="overflow-x-auto">
            {entities.isLoading && (
              <div className="flex items-center justify-center px-6 py-16">
                <p className="text-muted">Loading businesses...</p>
              </div>
            )}
            {entities.error && (
              <div className="flex items-center gap-3 border-l-4 border-danger bg-red-50 px-5 py-4">
                <AlertTriangle className="h-5 w-5 text-danger" />
                <div>
                  <p className="font-semibold text-danger">Error loading data</p>
                  <p className="text-sm text-slate-600">
                    {entities.error instanceof Error ? entities.error.message : "An error occurred"}
                  </p>
                </div>
              </div>
            )}
            {!entities.isLoading && !entities.error && (
              <table className="min-w-full divide-y divide-border">
                <thead className="bg-slate-50">
                  <tr className="text-left text-xs uppercase tracking-wide text-muted">
                    <th className="px-5 py-3">UBID</th>
                    <th className="px-5 py-3">Canonical Name</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Source Count</th>
                    <th className="px-5 py-3">Confidence</th>
                    <th className="px-5 py-3">Risk</th>
                    <th className="px-5 py-3">Last Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border text-sm text-slate-700">
                  {entities.data?.items.map((entity) => (
                    <tr
                      className="cursor-pointer transition hover:bg-blue-50"
                      key={entity.ubid}
                      onClick={() => navigate(`/entity/${entity.ubid}`)}
                    >
                      <td className="px-5 py-4 font-mono text-xs text-primary">{entity.ubid}</td>
                      <td className="px-5 py-4 font-semibold text-slate-900">{entity.canonical_name}</td>
                      <td className="px-5 py-4">
                        <StatusBadge status={entity.status} />
                      </td>
                      <td className="px-5 py-4">{entity.source_count}</td>
                      <td className="px-5 py-4">
                        <ConfidenceBadge value={entity.confidence} />
                      </td>
                      <td className="px-5 py-4">
                        <RiskBadge level={entity.risk.level} score={entity.risk.score} />
                      </td>
                      <td className="px-5 py-4">{new Date(entity.updated_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {!entities.isLoading && !entities.error && !entities.data?.items.length && (
            <div className="flex flex-col items-center gap-3 px-6 py-16 text-center">
              <Inbox className="h-10 w-10 text-muted" />
              <p className="text-sm text-muted">No businesses matched the current filter.</p>
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-border px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted">
              Page {page} of {totalPages}
            </p>
            <div className="flex gap-2">
              <button
                className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40"
                disabled={page === 1}
                onClick={() => setPage((value) => value - 1)}
                type="button"
              >
                Previous
              </button>
              <button
                className="rounded-xl border border-border px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40"
                disabled={page >= totalPages}
                onClick={() => setPage((value) => value + 1)}
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="panel p-5">
            <div className="flex items-center gap-3">
              <ArrowRight className="h-5 w-5 text-primary" />
              <div>
                <p className="font-semibold text-slate-900">Fast search</p>
                <p className="text-sm text-muted">Search spans canonical names, GSTIN, PAN, and display UBIDs.</p>
              </div>
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-warning" />
              <div>
                <p className="font-semibold text-slate-900">Human review preserved</p>
                <p className="text-sm text-muted">Ambiguous link decisions stay reversible through audit-backed review tasks.</p>
              </div>
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center gap-3">
              <CircleAlert className="h-5 w-5 text-danger" />
              <div>
                <p className="font-semibold text-slate-900">Explainable scoring</p>
                <p className="text-sm text-muted">Every confidence score is broken down by names, address, identifiers, and licenses.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
