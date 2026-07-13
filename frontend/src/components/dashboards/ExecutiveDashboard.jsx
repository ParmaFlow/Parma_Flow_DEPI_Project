import { BarChart3, CheckCircle2, FileText, Gauge, ShieldX } from "lucide-react";

import { AgentResultTabs } from "../AgentResultTabs";
import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";
import {
  getGovernanceState,
  SYSTEM_LOCK_MESSAGE,
  CRITICAL_COMPLIANCE_FAILURE,
} from "../../lib/governance";

export function ExecutiveDashboard({ analysis }) {
  const safeAnalysis = analysis || {};
  const report = safeAnalysis.report || {};
  const kpis = safeAnalysis.kpis || {};
  const input = safeAnalysis.input || {};
  const governance = getGovernanceState(safeAnalysis);

  /**
   * GOVERNANCE OVERRIDE: the top-level status pill must always reflect the
   * governance lock before falling back to report.final_status or kpis.
   */
  const displayStatus = governance.isBlocked
    ? "BLOCKED / AUDIT FAILED"
    : report.final_status || kpis.final_status;

  return (
    <div className="space-y-4">
      <section
        className={`rounded-lg border p-5 shadow-sm ${
          governance.isBlocked
            ? "border-red-300 bg-red-50"
            : "border-slate-200 bg-white"
        }`}
      >
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p
              className={`text-xs font-semibold uppercase tracking-wide ${
                governance.isBlocked ? "text-red-800" : "text-slate-500"
              }`}
            >
              {governance.isBlocked ? "Clinical governance lock" : "Executive view"}
            </p>
            <h2
              className={`text-xl font-semibold ${
                governance.isBlocked ? "text-red-950" : "text-ink"
              }`}
            >
              {report.sku || input.sku_name || "Unknown SKU"}
            </h2>
          </div>
          {/* Always governance-corrected status */}
          <StatusPill value={displayStatus} />
        </div>

        {/* SYSTEM LOCK banner for Executive */}
        {governance.isBlocked ? (
          <div className="mb-4 rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
            {SYSTEM_LOCK_MESSAGE}
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={CheckCircle2}
            label="Execution allowed"
            value={governance.isBlocked ? "false" : String(Boolean(kpis.execution_allowed))}
            tone={governance.isBlocked || !kpis.execution_allowed ? "red" : "teal"}
          />
          <MetricCard
            icon={Gauge}
            label="Risk level"
            value={kpis.risk_level || "Unavailable"}
            detail={kpis.risk_score != null ? `${kpis.risk_score}/100` : ""}
            tone="amber"
          />
          <MetricCard
            icon={BarChart3}
            label="Inventory gap"
            value={kpis.inventory_gap?.toLocaleString?.() ?? "0"}
            detail="units"
            tone="indigo"
          />
          <MetricCard
            icon={governance.isBlocked ? ShieldX : FileText}
            label="Audit"
            value={
              governance.isBlocked
                ? "BLOCKED"
                : kpis.audit_status || "Unavailable"
            }
            tone={governance.isBlocked || kpis.blocking_errors ? "red" : "teal"}
          />
        </div>

        {/* Executive summary — replaced with compliance failure text when blocked */}
        <p className={`mt-5 text-sm leading-6 ${governance.isBlocked ? "font-medium text-red-900" : "text-slate-700"}`}>
          {governance.isBlocked
            ? CRITICAL_COMPLIANCE_FAILURE
            : report.executive_summary ||
              report.reasoning ||
              "No executive report returned."}
        </p>
      </section>

      <AgentResultTabs analysis={safeAnalysis} role="executive" />
    </div>
  );
}
