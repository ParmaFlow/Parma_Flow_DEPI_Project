import { Activity, Clock3, Database, ShieldCheck, ShieldX } from "lucide-react";

import { AgentResultTabs } from "../AgentResultTabs";
import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";
import {
  getGovernanceState,
  SYSTEM_LOCK_MESSAGE,
} from "../../lib/governance";

export function AdminDashboard({ analysis }) {
  const safeAnalysis = analysis || {};
  const input = safeAnalysis.input || {};
  const execution = safeAnalysis.execution || {};
  const compliance = safeAnalysis.compliance || {};
  const governance = getGovernanceState(safeAnalysis);

  /**
   * GOVERNANCE OVERRIDE: if the system is blocked the top-level status pill
   * must reflect the lock, not the raw execution.status value.
   */
  const displayStatus = governance.isBlocked
    ? "BLOCKED / AUDIT FAILED"
    : execution.status;

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
              {governance.isBlocked ? "Clinical governance lock" : "Admin view"}
            </p>
            <h2
              className={`text-xl font-semibold ${
                governance.isBlocked ? "text-red-950" : "text-ink"
              }`}
            >
              {input.sku_name || "Unknown SKU"}
            </h2>
          </div>
          {/* Always governance-corrected status */}
          <StatusPill value={displayStatus} />
        </div>

        {/* SYSTEM LOCK banner for Admin */}
        {governance.isBlocked ? (
          <div className="mb-4 rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
            {SYSTEM_LOCK_MESSAGE}
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={governance.isBlocked ? ShieldX : ShieldCheck}
            label="GxP guardrail"
            value={
              governance.isBlocked
                ? "BLOCKED"
                : compliance.gxp_guardrail || "Unavailable"
            }
            tone={governance.isBlocked || !compliance.approved ? "red" : "teal"}
          />
          <MetricCard
            icon={Database}
            label="Failed rules"
            value={compliance.failed_rules?.length ?? 0}
            tone="amber"
          />
          <MetricCard
            icon={Clock3}
            label="Pipeline time"
            value={totalDuration(execution.step_durations)}
            detail="seconds"
            tone="indigo"
          />
          <MetricCard
            icon={Activity}
            label="Current step"
            value={execution.current_step || "Unavailable"}
            tone="slate"
          />
        </div>
      </section>

      <AgentResultTabs analysis={safeAnalysis} role="admin" />
    </div>
  );
}

function totalDuration(durations = {}) {
  return Object.values(durations)
    .reduce((sum, value) => sum + Number(value || 0), 0)
    .toFixed(3);
}
