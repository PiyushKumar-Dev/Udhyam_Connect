interface RiskBadgeProps {
  level: "LOW" | "MEDIUM" | "HIGH";
  score: number;
}

const styles: Record<RiskBadgeProps["level"], string> = {
  LOW: "bg-emerald-100 text-emerald-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  HIGH: "bg-red-100 text-red-700"
};

export function RiskBadge({ level, score }: RiskBadgeProps) {
  return <span className={`status-pill ${styles[level]}`}>{level} {score}</span>;
}
