import { Activity, Eye, EyeOff, GitBranch, Network, ScanSearch, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useEntityGraph, useGraphOverview } from "../api/hooks";
import { AuthSwitcher } from "../components/AuthSwitcher";
import { RelationshipGraph } from "../components/RelationshipGraph";
import { StatusBadge } from "../components/StatusBadge";
import type { GraphNode, GraphEdge } from "../types";

const nodeTypeLabels: Record<string, string> = {
  record: "Records",
  activity: "Activities",
  review: "Reviews"
};

export function GraphExplorer() {
  const overview = useGraphOverview();
  const [selectedUbid, setSelectedUbid] = useState("");
  const [hotspotSearch, setHotspotSearch] = useState("");
  const [hiddenTypes, setHiddenTypes] = useState<Set<string>>(new Set());
  const graph = useEntityGraph(selectedUbid);

  useEffect(() => {
    if (!selectedUbid && overview.data?.hotspots.length) {
      setSelectedUbid(overview.data.hotspots[0].ubid);
    }
  }, [overview.data, selectedUbid]);

  const filteredHotspots = useMemo(() => {
    if (!overview.data) return [];
    if (!hotspotSearch.trim()) return overview.data.hotspots;
    const q = hotspotSearch.toLowerCase();
    return overview.data.hotspots.filter(
      (h) =>
        h.canonical_name.toLowerCase().includes(q) ||
        h.ubid.toLowerCase().includes(q)
    );
  }, [overview.data, hotspotSearch]);

  const toggleType = (type: string) => {
    setHiddenTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  };

  // Filter nodes and edges based on hidden types
  const filteredNodes: GraphNode[] = useMemo(() => {
    if (!graph.data) return [];
    return graph.data.nodes.filter((n) => !hiddenTypes.has(n.node_type));
  }, [graph.data, hiddenTypes]);

  const filteredEdges: GraphEdge[] = useMemo(() => {
    if (!graph.data) return [];
    const visibleIds = new Set(filteredNodes.map((n) => n.id));
    return graph.data.edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target));
  }, [graph.data, filteredNodes]);

  return (
    <div className="min-h-screen">
      <nav className="sticky top-0 z-30 border-b border-border bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div>
            <p className="font-display text-2xl font-semibold text-primary">Graph Explorer</p>
            <p className="text-sm text-muted">Relationship intelligence across businesses, records, events, and review tasks.</p>
          </div>
          <div className="flex items-center gap-3">
            <AuthSwitcher />
            <Link className="text-sm font-semibold text-primary" to="/pincodes">
              Pincode Explorer
            </Link>
            <Link className="text-sm font-semibold text-primary" to="/">
              Back to dashboard
            </Link>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <section className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Graph Nodes</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {overview.data?.metrics.node_count ?? "-"}
                </p>
              </div>
              <Network className="h-8 w-8 text-primary" />
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Edges</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {overview.data?.metrics.edge_count ?? "-"}
                </p>
              </div>
              <GitBranch className="h-8 w-8 text-emerald-700" />
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Components</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {overview.data?.metrics.connected_components ?? "-"}
                </p>
              </div>
              <ScanSearch className="h-8 w-8 text-amber-600" />
            </div>
          </div>
          <div className="panel p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wide text-muted">Open Reviews</p>
                <p className="mt-3 text-3xl font-semibold text-slate-900">
                  {overview.data?.metrics.open_review_count ?? "-"}
                </p>
              </div>
              <Activity className="h-8 w-8 text-danger" />
            </div>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[320px_minmax(0,1fr)]">
          <aside className="space-y-6">
            {/* Search hotspots */}
            <div className="panel p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                <input
                  className="w-full rounded-xl border border-border bg-slate-50 py-2.5 pl-10 pr-3 text-sm placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  placeholder="Search hotspots..."
                  value={hotspotSearch}
                  onChange={(e) => setHotspotSearch(e.target.value)}
                />
              </div>
            </div>

            <div className="panel p-5">
              <p className="text-sm font-semibold uppercase tracking-wide text-primary">Hotspots</p>
              <div className="mt-4 max-h-[420px] space-y-3 overflow-y-auto">
                {filteredHotspots.map((hotspot) => (
                  <button
                    className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                      selectedUbid === hotspot.ubid
                        ? "border-primary bg-blue-50"
                        : "border-border bg-white hover:bg-slate-50"
                    }`}
                    key={hotspot.ubid}
                    onClick={() => setSelectedUbid(hotspot.ubid)}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-semibold text-slate-900">{hotspot.canonical_name}</p>
                        <p className="mt-1 font-mono text-xs text-primary">{hotspot.ubid}</p>
                      </div>
                      <StatusBadge status={hotspot.status} />
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-muted">
                      <div>
                        <p className="font-semibold text-slate-900">{hotspot.linked_record_count}</p>
                        <p>Records</p>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{hotspot.activity_count}</p>
                        <p>Events</p>
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{hotspot.open_review_count}</p>
                        <p>Reviews</p>
                      </div>
                    </div>
                  </button>
                ))}
                {filteredHotspots.length === 0 && (
                  <p className="py-4 text-center text-sm text-muted">No matching hotspots found.</p>
                )}
              </div>
            </div>

            {/* Legend + Node toggles */}
            <div className="panel p-5">
              <p className="text-sm font-semibold uppercase tracking-wide text-primary">Legend & Filters</p>
              <div className="mt-4 space-y-3 text-sm text-slate-700">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full bg-blue-700" />
                  Businesses
                </div>
                {Object.entries(nodeTypeLabels).map(([type, label]) => (
                  <button
                    key={type}
                    className="flex w-full items-center gap-3 text-left"
                    onClick={() => toggleType(type)}
                    type="button"
                  >
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{
                        background:
                          type === "record"
                            ? "#0f766e"
                            : type === "activity"
                              ? "#d97706"
                              : "#dc2626",
                        opacity: hiddenTypes.has(type) ? 0.25 : 1,
                      }}
                    />
                    <span className={hiddenTypes.has(type) ? "text-muted line-through" : ""}>
                      {label}
                    </span>
                    {hiddenTypes.has(type) ? (
                      <EyeOff className="ml-auto h-3.5 w-3.5 text-muted" />
                    ) : (
                      <Eye className="ml-auto h-3.5 w-3.5 text-slate-400" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </aside>

          <section className="space-y-6">
            <div className="panel p-6">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-sm uppercase tracking-wide text-primary">Entity subgraph</p>
                  <h1 className="font-display text-4xl font-semibold text-slate-900">
                    {graph.data?.canonical_name ?? "Select a hotspot"}
                  </h1>
                  <p className="mt-2 text-sm text-muted">
                    Focus graph shows how the selected business connects to linked records, activity evidence, and review tasks.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-muted">Largest component</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {graph.data?.metrics.largest_component_size ?? "-"}
                    </p>
                  </div>
                  <div className="rounded-2xl bg-slate-50 px-4 py-3">
                    <p className="text-muted">Local edges</p>
                    <p className="mt-1 font-semibold text-slate-900">{graph.data?.metrics.edge_count ?? "-"}</p>
                  </div>
                </div>
              </div>
            </div>

            {graph.data ? (
              <>
                <RelationshipGraph edges={filteredEdges} nodes={filteredNodes} />
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="panel p-5">
                    <p className="text-sm uppercase tracking-wide text-muted">Businesses</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{graph.data.metrics.business_count}</p>
                  </div>
                  <div className="panel p-5">
                    <p className="text-sm uppercase tracking-wide text-muted">Records</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{graph.data.metrics.source_record_count}</p>
                  </div>
                  <div className="panel p-5">
                    <p className="text-sm uppercase tracking-wide text-muted">Events</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{graph.data.metrics.activity_event_count}</p>
                  </div>
                  <div className="panel p-5">
                    <p className="text-sm uppercase tracking-wide text-muted">Reviews</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{graph.data.metrics.open_review_count}</p>
                  </div>
                </div>
              </>
            ) : (
              <div className="panel px-6 py-16 text-center text-sm text-muted">
                {selectedUbid ? "Loading graph..." : "Select a hotspot to inspect its relationship graph."}
              </div>
            )}
          </section>
        </section>
      </main>
    </div>
  );
}
