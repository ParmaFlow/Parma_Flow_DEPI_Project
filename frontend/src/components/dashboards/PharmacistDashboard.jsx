import { AlertTriangle, ClipboardCheck, PackagePlus, ShieldAlert } from "lucide-react";

import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";

export function PharmacistDashboard({ analysis }) {
  const ops = analysis.operational || {};
  const risk = analysis.risk || {};
  const audit = analysis.audit || {};

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Operations</p>
            <h2 className="text-xl font-semibold text-ink">{ops.sku || analysis.input?.sku_name}</h2>
          </div>
          <StatusPill value={ops.action} />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard icon={AlertTriangle} label="Inventory gap" value={ops.inventory_gap?.toLocaleString()} detail="units short" tone={ops.inventory_gap > 0 ? "red" : "teal"} />
          <MetricCard icon={PackagePlus} label="Recommended qty" value={ops.recommended_qty?.toLocaleString()} detail="rounded units" tone="indigo" />
          <MetricCard icon={ClipboardCheck} label="Reorder point" value={ops.reorder_point?.toLocaleString()} detail="units" tone="amber" />
          <MetricCard icon={ShieldAlert} label="Risk" value={risk.risk_level} detail={risk.risk_score != null ? `${risk.risk_score}/100` : ""} tone={risk.risk_level === "LOW" ? "teal" : "red"} />
        </div>

        <div className="mt-5 rounded-md border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-ink">OpsAgent reasoning</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{ops.reasoning || "No reasoning returned."}</p>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-ink">Action queue</h3>
          <StatusPill value={audit.audit_status} />
        </div>
        <div className="divide-y divide-slate-200">
          {analysis.actionable_alerts.map((alert) => (
            <div key={`${alert.title}-${alert.owner}`} className="py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-ink">{alert.title}</p>
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{alert.owner}</span>
              </div>
              <p className="mt-1 text-sm leading-6 text-slate-600">{alert.message}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

