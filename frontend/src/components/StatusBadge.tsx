interface StatusBadgeProps {
  status: "ACTIVE" | "DORMANT" | "CLOSED";
}

const styles: Record<StatusBadgeProps["status"], string> = {
  ACTIVE: "bg-green-100 text-success",
  DORMANT: "bg-amber-100 text-warning",
  CLOSED: "bg-red-100 text-danger"
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-pill ${styles[status]}`}>{status}</span>;
}
