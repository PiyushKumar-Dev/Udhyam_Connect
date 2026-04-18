import { AlertTriangle, MapPin, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { usePincodeStats } from "../api/hooks";
import { AuthSwitcher } from "../components/AuthSwitcher";

const maxBarHeight = 160;

export function PincodeExplorer() {
  const [search, setSearch] = useState("");
  const pincodeStats = usePincodeStats(search.trim() || undefined);
  const navigate = useNavigate();

  const topPincodes = useMemo(() => {
    if (!pincodeStats.data) return [];
    return pincodeStats.data.pincodes.slice(0, 12);
  }, [pincodeStats.data]);

  const maxTotal = useMemo(() => {
    return Math.max(1, ...topPincodes.map((p) => p.total));
  }, [topPincodes]);

  return (
    <div className="min-h-screen">
      <nav className="sticky top-0 z-30 border-b border-border bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <p className="font-display text-2xl font-semibold text-primary">Pincode Explorer</p>
            <p className="text-sm text-muted">Browse businesses by geographic pincode with status and risk breakdowns.</p>
          </div>
          <div className="flex items-center gap-3">
            <AuthSwitcher />
            <Link className="text-sm font-semibold text-primary" to="/graph">
              Graph Explorer
            </Link>
            <Link className="text-sm font-semibold text-primary" to="/">
              Dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {/* Summary stats */}
        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Total Pincodes</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {pincodeStats.data?.total_pincodes ?? "-"}
                </p>
              </div>
              <MapPin className="h-8 w-8 text-primary" />
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Businesses Mapped</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {pincodeStats.data
                    ? pincodeStats.data.pincodes.reduce((sum, p) => sum + p.total, 0)
                    : "-"}
                </p>
              </div>
              <span className="status-pill bg-blue-100 text-primary">GEO</span>
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">High Risk Zones</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {pincodeStats.data
                    ? pincodeStats.data.pincodes.filter((p) => p.high_risk > 0).length
                    : "-"}
                </p>
              </div>
              <AlertTriangle className="h-8 w-8 text-danger" />
            </div>
          </div>
        </section>

        {/* Search */}
        <section className="mb-8">
          <div className="panel p-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-muted" />
              <input
                className="w-full rounded-2xl border border-border bg-slate-50 py-3.5 pl-12 pr-4 text-base placeholder:text-muted focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Search by pincode (e.g. 560001)..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
        </section>

        {/* Bar chart */}
        {topPincodes.length > 0 && (
          <section className="mb-8">
            <div className="panel p-6">
              <p className="mb-6 text-sm font-semibold uppercase tracking-wide text-primary">
                Top Pincodes by Business Count
              </p>
              <div className="flex items-end gap-3" style={{ minHeight: maxBarHeight + 60 }}>
                {topPincodes.map((p) => {
                  const barH = Math.max(8, (p.total / maxTotal) * maxBarHeight);
                  const activeH = (p.active / Math.max(p.total, 1)) * barH;
                  const dormantH = (p.dormant / Math.max(p.total, 1)) * barH;
                  const closedH = barH - activeH - dormantH;
                  return (
                    <button
                      key={p.pincode}
                      className="group flex flex-1 flex-col items-center gap-2 transition hover:scale-105"
                      onClick={() => navigate(`/?pincode=${p.pincode}`)}
                      type="button"
                    >
                      <span className="text-xs font-semibold text-slate-700">{p.total}</span>
                      <div
                        className="relative w-full overflow-hidden rounded-t-xl shadow-sm transition-all"
                        style={{ height: barH }}
                      >
                        <div
                          className="absolute bottom-0 left-0 right-0 bg-emerald-500"
                          style={{ height: activeH }}
                        />
                        <div
                          className="absolute left-0 right-0 bg-amber-400"
                          style={{ bottom: activeH, height: dormantH }}
                        />
                        <div
                          className="absolute left-0 right-0 top-0 bg-slate-400"
                          style={{ height: closedH }}
                        />
                        {p.high_risk > 0 && (
                          <div className="absolute right-0.5 top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[8px] font-bold text-white">
                            {p.high_risk}
                          </div>
                        )}
                      </div>
                      <span className="text-[11px] font-semibold text-muted group-hover:text-primary">
                        {p.pincode}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="mt-4 flex items-center gap-6 text-xs text-muted">
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm bg-emerald-500" /> Active
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm bg-amber-400" /> Dormant
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm bg-slate-400" /> Closed
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> High Risk
                </span>
              </div>
            </div>
          </section>
        )}

        {/* Pincode cards grid */}
        <section>
          {pincodeStats.isLoading && (
            <div className="flex items-center justify-center py-16">
              <p className="text-muted">Loading pincode data...</p>
            </div>
          )}
          {pincodeStats.error && (
            <div className="flex items-center gap-3 border-l-4 border-danger bg-red-50 px-5 py-4">
              <AlertTriangle className="h-5 w-5 text-danger" />
              <p className="font-semibold text-danger">Error loading pincode data.</p>
            </div>
          )}
          {pincodeStats.data && pincodeStats.data.pincodes.length === 0 && (
            <div className="panel px-6 py-16 text-center">
              <MapPin className="mx-auto h-10 w-10 text-muted" />
              <p className="mt-3 text-sm text-muted">No pincodes matched your search.</p>
            </div>
          )}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {pincodeStats.data?.pincodes.map((p) => (
              <button
                key={p.pincode}
                className="panel p-5 text-left transition hover:border-primary/30 hover:shadow-lg"
                onClick={() => navigate(`/?pincode=${p.pincode}`)}
                type="button"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-primary" />
                    <span className="font-mono text-lg font-bold text-slate-900">{p.pincode}</span>
                  </div>
                  <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-primary">
                    {p.total} total
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-4 gap-2 text-center text-xs">
                  <div className="rounded-xl bg-emerald-50 px-2 py-2">
                    <p className="text-lg font-bold text-emerald-700">{p.active}</p>
                    <p className="text-emerald-600">Active</p>
                  </div>
                  <div className="rounded-xl bg-amber-50 px-2 py-2">
                    <p className="text-lg font-bold text-amber-700">{p.dormant}</p>
                    <p className="text-amber-600">Dormant</p>
                  </div>
                  <div className="rounded-xl bg-slate-100 px-2 py-2">
                    <p className="text-lg font-bold text-slate-700">{p.closed}</p>
                    <p className="text-slate-500">Closed</p>
                  </div>
                  <div className="rounded-xl bg-red-50 px-2 py-2">
                    <p className="text-lg font-bold text-red-700">{p.high_risk}</p>
                    <p className="text-red-500">High Risk</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
