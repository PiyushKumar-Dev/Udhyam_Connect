import type { EntitySummary } from "../types";
import { StatusBadge } from "./StatusBadge";

interface EntityCardProps {
  entity: EntitySummary;
  onSelect: (ubid: string) => void;
}

export function EntityCard({ entity, onSelect }: EntityCardProps) {
  return (
    <button
      className="flex w-full items-center justify-between gap-4 rounded-xl border border-border bg-white px-4 py-3 text-left transition hover:border-primary/40 hover:bg-blue-50"
      onClick={() => onSelect(entity.ubid)}
      type="button"
    >
      <div>
        <p className="font-semibold text-slate-900">{entity.canonical_name}</p>
        <p className="font-mono text-xs text-muted">{entity.ubid}</p>
      </div>
      <StatusBadge status={entity.status} />
    </button>
  );
}
