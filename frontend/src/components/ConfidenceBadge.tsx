interface ConfidenceBadgeProps {
  value: number;
}

export function ConfidenceBadge({ value }: ConfidenceBadgeProps) {
  const percent = Math.round(value * 100);
  const tone = value >= 0.8 ? "bg-green-500" : value >= 0.6 ? "bg-amber-500" : "bg-red-500";

  return (
    <div className="min-w-28">
      <div className="mb-1 flex items-center justify-between text-xs font-semibold text-slate-700">
        <span>{percent}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
