const tones = {
  clinical: "bg-blue-50 text-clinical",
  teal: "bg-blue-50 text-clinical", // fallback for older dashboards
  amber: "bg-amber-50 text-signal",
  red: "bg-red-50 text-red-700",
  indigo: "bg-indigo-50 text-indigo-700",
  slate: "bg-slate-100 text-slate-700"
};

export function MetricCard({ icon: Icon, label, value, detail, tone = "clinical" }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-semibold text-ink">{value ?? "-"}</p>
          {detail ? <p className="mt-1 text-sm text-slate-500">{detail}</p> : null}
        </div>
        {Icon ? (
          <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${tones[tone] || tones.teal}`}>
            <Icon className="h-4 w-4" />
          </div>
        ) : null}
      </div>
    </div>
  );
}

