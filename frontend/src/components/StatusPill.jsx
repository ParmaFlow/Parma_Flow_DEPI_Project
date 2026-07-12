const styles = {
  EXECUTED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  EXECUTED_WITH_WARNINGS: "border-amber-200 bg-amber-50 text-amber-700",
  BLOCKED: "border-red-200 bg-red-50 text-red-700",
  APPROVED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  APPROVED_WITH_WARNINGS: "border-amber-200 bg-amber-50 text-amber-700",
  FAILED_AUDIT: "border-red-200 bg-red-50 text-red-700",
  REJECTED: "border-red-200 bg-red-50 text-red-700",
  COMPLETED: "border-emerald-200 bg-emerald-50 text-emerald-700"
};

export function StatusPill({ value }) {
  return (
    <span className={`inline-flex min-h-7 items-center rounded-md border px-2.5 text-xs font-bold uppercase tracking-wide ${styles[value] || "border-slate-200 bg-slate-50 text-slate-700"}`}>
      {value || "unknown"}
    </span>
  );
}

