import { BarChart3, CheckCircle2, FileText, Gauge } from "lucide-react";

import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";

export function ExecutiveDashboard({ analysis }) {
  const report = analysis.report || {};
  const sections = report.report_sections || {};

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Executive view</p>
            <h2 className="text-xl font-semibold text-ink">{report.sku || analysis.input?.sku_name}</h2>
          </div>
          <StatusPill value={report.final_status || analysis.kpis.final_status} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={CheckCircle2} label="Execution allowed" value={String(analysis.kpis.execution_allowed)} tone={analysis.kpis.execution_allowed ? "teal" : "red"} />
          <MetricCard icon={Gauge} label="Risk level" value={analysis.kpis.risk_level} detail={analysis.kpis.risk_score != null ? `${analysis.kpis.risk_score}/100` : ""} tone="amber" />
          <MetricCard icon={BarChart3} label="Inventory gap" value={analysis.kpis.inventory_gap?.toLocaleString()} detail="units" tone="indigo" />
          <MetricCard icon={FileText} label="Audit" value={analysis.kpis.audit_status} tone={analysis.kpis.blocking_errors ? "red" : "teal"} />
        </div>

        <p className="mt-5 text-sm leading-6 text-slate-700">{report.executive_summary || report.reasoning}</p>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-base font-semibold text-ink">Report sections</h3>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          {Object.entries(sections)
            .filter(([key]) => key !== "next_actions")
            .map(([key, value]) => (
              <article key={key} className="rounded-md border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">{key.replaceAll("_", " ")}</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">{value}</p>
              </article>
            ))}
        </div>
      </section>
    </div>
  );
}

