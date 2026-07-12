import { Activity, Clock3, Database, ShieldCheck } from "lucide-react";

import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";

export function AdminDashboard({ analysis }) {
  const audit = analysis.audit || {};

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Admin view</p>
            <h2 className="text-xl font-semibold text-ink">{analysis.input?.sku_name}</h2>
          </div>
          <StatusPill value={analysis.execution.status} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={ShieldCheck} label="GxP guardrail" value={analysis.compliance.gxp_guardrail} tone={analysis.compliance.approved ? "teal" : "red"} />
          <MetricCard icon={Database} label="Failed rules" value={analysis.compliance.failed_rules?.length ?? 0} tone="amber" />
          <MetricCard icon={Clock3} label="Pipeline time" value={totalDuration(analysis.execution.step_durations)} detail="seconds" tone="indigo" />
          <MetricCard icon={Activity} label="Current step" value={analysis.execution.current_step} tone="slate" />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">Audit status</h3>
          <StatusPill value={audit.audit_status} />
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4">Rule</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(audit.rule_results || []).map((rule) => (
                <tr key={`${rule.rule_name}-${rule.message}`}>
                  <td className="py-3 pr-4 font-medium text-ink">{rule.rule_name}</td>
                  <td className="py-3 pr-4 text-slate-700">{rule.severity}</td>
                  <td className="py-3 pr-4 text-slate-600">{rule.message}</td>
                </tr>
              ))}
              {!(audit.rule_results || []).length ? (
                <tr>
                  <td className="py-3 pr-4 text-slate-600" colSpan="3">No failed audit rules.</td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-base font-semibold text-ink">Agent traces</h3>
        <div className="mt-3 space-y-3">
          {analysis.traces.map((trace) => (
            <details key={trace.step} className="rounded-md border border-slate-200 bg-slate-50 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">
                {trace.step} - {trace.duration_seconds ?? 0}s
              </summary>
              <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">
                {JSON.stringify(trace.result, null, 2)}
              </pre>
            </details>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-base font-semibold text-ink">System logs</h3>
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {analysis.system_logs.map((line) => (
            <li key={line} className="rounded-md bg-slate-50 px-3 py-2 font-mono text-xs">{line}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function totalDuration(durations = {}) {
  return Object.values(durations)
    .reduce((sum, value) => sum + Number(value || 0), 0)
    .toFixed(3);
}

