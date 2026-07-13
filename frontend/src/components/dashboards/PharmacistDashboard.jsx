import { AlertTriangle, ClipboardCheck, PackagePlus, ShieldAlert, ShieldX } from "lucide-react";

import { AgentResultTabs } from "../AgentResultTabs";
import { MetricCard } from "../MetricCard";
import { StatusPill } from "../StatusPill";
import {
  getGovernanceState,
  SYSTEM_LOCK_MESSAGE,
  CRITICAL_COMPLIANCE_FAILURE,
} from "../../lib/governance";

export function PharmacistDashboard({ analysis }) {
  const safeAnalysis = analysis || {};
  const ops = safeAnalysis.operational || {};
  const risk = safeAnalysis.risk || {};
  const input = safeAnalysis.input || {};
  const governance = getGovernanceState(safeAnalysis);

  /**
   * GOVERNANCE OVERRIDE: never show ops.action ("REORDER" etc.) when blocked.
   * The directive must be BLOCKED / AUDIT FAILED at all times.
   */
  const action = governance.isBlocked ? "BLOCKED / AUDIT FAILED" : ops.action;

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
              {governance.isBlocked ? "Clinical governance lock" : "Operations"}
            </p>
            <h2
              className={`text-xl font-semibold ${
                governance.isBlocked ? "text-red-950" : "text-ink"
              }`}
            >
              {ops.sku || input.sku_name || "Unknown SKU"}
            </h2>
          </div>
          {/* StatusPill driven by governance-corrected action */}
          <StatusPill value={action} />
        </div>

        {/* Giant red SYSTEM LOCK banner for Pharmacist */}
        {governance.isBlocked ? (
          <div className="mb-4 rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
            {SYSTEM_LOCK_MESSAGE}
          </div>
        ) : null}

        {/* Critical compliance failure notice (Pharmacist-specific call-out box) */}
        {governance.isBlocked ? (
          <div className="mb-4 rounded-lg border-2 border-red-900 bg-red-50 p-5">
            <p className="text-base font-bold uppercase tracking-wide text-red-950">
              ⛔ Stop: audit failed — no replenishment action permitted
            </p>
            <p className="mt-2 text-sm font-medium leading-6 text-red-900">
              {CRITICAL_COMPLIANCE_FAILURE}
            </p>
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={AlertTriangle}
            label="Inventory gap"
            value={ops.inventory_gap?.toLocaleString?.() ?? "0"}
            detail="units short"
            tone={ops.inventory_gap > 0 ? "red" : "teal"}
          />
          <MetricCard
            icon={PackagePlus}
            label="Recommended qty"
            value={ops.recommended_qty?.toLocaleString?.() ?? "0"}
            detail="rounded units"
            tone="indigo"
          />
          <MetricCard
            icon={ClipboardCheck}
            label="Reorder point"
            value={ops.reorder_point?.toLocaleString?.() ?? "0"}
            detail="units"
            tone="amber"
          />
          <MetricCard
            icon={risk.risk_level === "LOW" ? ShieldAlert : ShieldX}
            label="Risk"
            value={risk.risk_level || "Unavailable"}
            detail={risk.risk_score != null ? `${risk.risk_score}/100` : ""}
            tone={risk.risk_level === "LOW" ? "teal" : "red"}
          />
        </div>
      </section>

      <AgentResultTabs analysis={safeAnalysis} role="pharmacist" />
    </div>
  );
}
