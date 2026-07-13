import { useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Boxes,
  ClipboardList,
  PackagePlus,
  ShieldCheck,
  ShieldX,
  TerminalSquare,
} from "lucide-react";

import {
  getGovernanceState,
  SYSTEM_LOCK_MESSAGE,
  CRITICAL_COMPLIANCE_FAILURE,
} from "../lib/governance";

// ---------------------------------------------------------------------------
// Status badge colour map
// ---------------------------------------------------------------------------
const statusStyles = {
  OUT_OF_STOCK: "border-red-200 bg-red-50 text-red-700",
  CRITICAL: "border-red-200 bg-red-50 text-red-700",
  LOW: "border-amber-200 bg-amber-50 text-amber-700",
  LOW_STOCK: "border-amber-200 bg-amber-50 text-amber-700",
  NORMAL: "border-emerald-200 bg-emerald-50 text-emerald-700",
  HEALTHY: "border-emerald-200 bg-emerald-50 text-emerald-700",
  APPROVED: "border-emerald-200 bg-emerald-50 text-emerald-700",
  PASS: "border-emerald-200 bg-emerald-50 text-emerald-700",
  APPROVED_WITH_WARNINGS: "border-amber-200 bg-amber-50 text-amber-700",
  FAILED_AUDIT: "border-red-900 bg-red-900 text-white",
  REJECTED: "border-red-900 bg-red-900 text-white",
  BLOCKED: "border-red-900 bg-red-900 text-white",
  "BLOCKED / AUDIT FAILED": "border-red-900 bg-red-900 text-white",
};

// ---------------------------------------------------------------------------
// Tab configuration
// ---------------------------------------------------------------------------
const tabSets = {
  admin: ["operations", "risk", "audit", "report", "logs"],
  pharmacist: ["operations", "audit"],
  executive: ["risk", "report", "audit"],
};

const tabMeta = {
  operations: { label: "Operations Agent", icon: ClipboardList },
  risk: { label: "Risk Agent", icon: AlertTriangle },
  audit: { label: "GxP Audit", icon: ShieldCheck },
  report: { label: "Final Report", icon: BarChart3 },
  logs: { label: "System Logs", icon: TerminalSquare },
};

// ---------------------------------------------------------------------------
// Root export
// ---------------------------------------------------------------------------
export function AgentResultTabs({ analysis, role = "pharmacist" }) {
  const safeAnalysis = analysis || {};
  const normalizedRole = String(
    role || safeAnalysis.role || "pharmacist"
  ).toLowerCase();
  const tabs = tabSets[normalizedRole] || tabSets.pharmacist;
  const [activeTab, setActiveTab] = useState(tabs[0]);

  const tab = tabs.includes(activeTab) ? activeTab : tabs[0];

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 pt-4">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((key) => {
            const Icon = tabMeta[key].icon;
            const active = key === tab;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
                className={`group inline-flex min-h-11 shrink-0 items-center gap-2 border-b-2 px-3 text-sm font-semibold transition-colors ${
                  active
                    ? "border-blue-600 text-blue-700"
                    : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-800"
                }`}
              >
                <Icon
                  className={`h-4 w-4 ${
                    active
                      ? "text-blue-600"
                      : "text-slate-400 group-hover:text-slate-600"
                  }`}
                />
                {tabMeta[key].label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="p-5">
        {tab === "operations" ? (
          <OperationsTab analysis={safeAnalysis} role={normalizedRole} />
        ) : null}
        {tab === "risk" ? (
          <RiskTab analysis={safeAnalysis} role={normalizedRole} />
        ) : null}
        {tab === "audit" ? <AuditTab analysis={safeAnalysis} /> : null}
        {tab === "report" ? (
          <ReportTab analysis={safeAnalysis} role={normalizedRole} />
        ) : null}
        {tab === "logs" ? <LogsTab analysis={safeAnalysis} /> : null}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// OperationsTab — enforces governance override on directive & GxP card
// ---------------------------------------------------------------------------
function OperationsTab({ analysis, role }) {
  const ops = analysis.operational || {};
  const input = analysis.input || {};
  const compliance = analysis.compliance || {};
  const governance = getGovernanceState(analysis);
  const hasOps = Boolean(Object.keys(ops).length);

  if (!hasOps && role !== "executive") {
    return <EmptyState title="No operations data generated for this step" />;
  }

  const inventoryStatus =
    ops.inventory_status ||
    (input.available_stock <= 0 ? "OUT_OF_STOCK" : "UNKNOWN");
  const currentStock = input.available_stock ?? input.stock ?? 0;

  /**
   * GOVERNANCE OVERRIDE — if blocked, the directive label and badge are
   * always "BLOCKED / AUDIT FAILED", never the raw ops.action value.
   */
  const action = governance.isBlocked
    ? "BLOCKED / AUDIT FAILED"
    : ops.action || analysis.kpis?.recommended_action || "PENDING";

  const directiveBadge = governance.isBlocked
    ? "BLOCKED / AUDIT FAILED"
    : inventoryStatus;

  const guardrailStatus = governance.isBlocked
    ? "BLOCKED"
    : compliance.gxp_guardrail || "UNAVAILABLE";

  return (
    <div className="space-y-5">
      {/* ── Operational Directive header ─────────────────────────────── */}
      <div
        className={`rounded-lg border p-4 ${
          governance.isBlocked
            ? "border-red-300 bg-red-50"
            : "border-transparent bg-transparent p-0"
        }`}
      >
        {/* SYSTEM LOCK banner — shown for ALL roles when blocked */}
        {governance.isBlocked ? (
          <div className="mb-3 rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
            {SYSTEM_LOCK_MESSAGE}
          </div>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p
              className={`text-xs font-semibold uppercase tracking-wide ${
                governance.isBlocked ? "text-red-800" : "text-slate-500"
              }`}
            >
              Operational directive
            </p>
            <h3
              className={`mt-1 text-xl font-semibold ${
                governance.isBlocked ? "text-red-950" : "text-ink"
              }`}
            >
              {action}
            </h3>
          </div>
          {/* Badge is always dark-red when blocked */}
          <StatusBadge value={directiveBadge} />
        </div>
      </div>

      {/* ── Pharmacist: giant red stop directive ──────────────────────── */}
      {role === "pharmacist" && governance.isBlocked ? (
        <div className="rounded-lg border-2 border-red-900 bg-red-50 p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-base font-bold uppercase tracking-wide text-red-950">
              Stop: audit failed
            </p>
            <StatusBadge value="BLOCKED" />
          </div>
          <p className="mt-3 text-sm font-medium leading-6 text-red-900">
            {CRITICAL_COMPLIANCE_FAILURE}
          </p>
        </div>
      ) : null}

      {/* ── Summary metric cards ──────────────────────────────────────── */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          icon={Boxes}
          label="Current Stock"
          value={formatNumber(currentStock)}
          tone="blue"
        />
        <SummaryCard
          icon={ShieldCheck}
          label="Safety Stock Buffer"
          value={formatNumber(ops.safety_stock ?? 0)}
          tone="emerald"
        />
        <SummaryCard
          icon={ClipboardList}
          label="Reorder Point"
          value={formatNumber(ops.reorder_point ?? 0)}
          tone="amber"
        />
        <SummaryCard
          icon={PackagePlus}
          label="Recommended Qty"
          value={formatNumber(ops.recommended_qty ?? 0)}
          tone="indigo"
        />
      </div>

      {/* ── GxP Guardrail card (Pharmacist) — colour driven by governance */}
      {role === "pharmacist" ? (
        <div
          className={`rounded-lg border p-4 ${
            governance.isBlocked
              ? "border-red-200 bg-red-50"   // ← blocked: red alert box
              : "border-emerald-200 bg-emerald-50"
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p
              className={`text-sm font-semibold ${
                governance.isBlocked ? "text-red-950" : "text-emerald-900"
              }`}
            >
              GxP guardrail
            </p>
            <StatusBadge value={guardrailStatus} />
          </div>
          <p
            className={`mt-2 text-sm leading-6 ${
              governance.isBlocked
                ? "font-medium text-red-900"
                : "text-emerald-900"
            }`}
          >
            {governance.isBlocked
              ? CRITICAL_COMPLIANCE_FAILURE
              : "Execute store action only when the audit disposition permits the workflow."}
          </p>
        </div>
      ) : null}

      {/* ── AI Reasoning — prepends SYSTEM LOCK banner when blocked ───── */}
      <NarrativeCard
        title="AI Reasoning"
        tone={governance.isBlocked ? "red" : "blue"}
        alert={governance.isBlocked ? SYSTEM_LOCK_MESSAGE : ""}
        content={ops.reasoning || "No operational reasoning returned."}
      />

      {/* ── Recommendation Details — same guard ───────────────────────── */}
      <NarrativeCard
        title="Recommendation Details"
        tone={governance.isBlocked ? "red" : "indigo"}
        alert={governance.isBlocked ? SYSTEM_LOCK_MESSAGE : ""}
        content={
          ops.recommendation_details || "No recommendation details returned."
        }
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// RiskTab
// ---------------------------------------------------------------------------
function RiskTab({ analysis, role }) {
  const risk = analysis.risk || {};
  const kpis = analysis.kpis || {};
  const input = analysis.input || {};
  const governance = getGovernanceState(analysis);
  const hasRisk = Boolean(
    Object.keys(risk).length || kpis.risk_level || kpis.risk_score != null
  );

  if (!hasRisk) {
    return <EmptyState title="No risk data generated for this step" />;
  }

  return (
    <div className="space-y-5">
      {/* SYSTEM LOCK banner is shown at the top of every tab when blocked */}
      {governance.isBlocked ? (
        <div className="rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
          {SYSTEM_LOCK_MESSAGE}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          icon={AlertTriangle}
          label="Risk Level"
          value={risk.risk_level || kpis.risk_level || "Unavailable"}
          tone="amber"
        />
        <SummaryCard
          icon={BarChart3}
          label="Risk Score"
          value={risk.risk_score ?? kpis.risk_score ?? "-"}
          detail="/100"
          tone="red"
        />
        <SummaryCard
          icon={Boxes}
          label="Current Stock"
          value={formatNumber(input.available_stock ?? input.stock ?? 0)}
          tone="blue"
        />
        <SummaryCard
          icon={PackagePlus}
          label="Forecast Demand"
          value={formatNumber(input.forecast_demand ?? 0)}
          tone="indigo"
        />
      </div>

      {role === "executive" ? (
        <div
          className={`rounded-lg border p-4 ${
            governance.isBlocked
              ? "border-red-200 bg-red-50"
              : "border-slate-200 bg-slate-50"
          }`}
        >
          <p
            className={`text-xs font-semibold uppercase tracking-wide ${
              governance.isBlocked ? "text-red-800" : "text-slate-500"
            }`}
          >
            {governance.isBlocked
              ? "⚠ Continuity risk — workflow blocked"
              : "Continuity risk snapshot"}
          </p>
          <p
            className={`mt-2 text-sm leading-6 ${
              governance.isBlocked ? "font-medium text-red-900" : "text-slate-700"
            }`}
          >
            {governance.isBlocked
              ? CRITICAL_COMPLIANCE_FAILURE
              : `Current stock is ${formatNumber(
                  input.available_stock ?? input.stock ?? 0
                )} units against forecast demand of ${formatNumber(
                  input.forecast_demand ?? 0
                )} units. Review the final report before approving any strategic action.`}
          </p>
        </div>
      ) : null}

      <Accordion
        items={[
          {
            title: "Risk reasoning",
            content: risk.reasoning || "No risk reasoning returned.",
          },
          {
            title: "Structured risk factors",
            content: {
              shortage_risk: risk.shortage_risk,
              expiry_risk: risk.expiry_risk,
              criticality: risk.criticality,
              alert_level: risk.alert_level,
              confidence_width: risk.confidence_width,
              human_review_recommended: risk.human_review_recommended,
            },
          },
        ]}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// AuditTab — card colour is always derived from governance, never from raw
//            audit.approved alone (which could conflict with disposition)
// ---------------------------------------------------------------------------
function AuditTab({ analysis }) {
  const audit = analysis.audit || {};
  const compliance = analysis.compliance || {};
  const governance = getGovernanceState(analysis);
  const rules = Array.isArray(audit.rule_results) ? audit.rule_results : [];
  const failedRules = Array.isArray(audit.failed_rules)
    ? audit.failed_rules
    : Array.isArray(compliance.failed_rules)
    ? compliance.failed_rules
    : [];
  const status = audit.audit_status || compliance.status || "UNAVAILABLE";

  /**
   * pass is ONLY true when governance confirms the workflow is NOT blocked.
   * This prevents the green card from rendering alongside a BLOCKED badge.
   */
  const pass =
    !governance.isBlocked && Boolean(audit.approved ?? compliance.approved);

  return (
    <div className="space-y-5">
      {/* Clinical compliance certificate card */}
      <div
        className={`rounded-lg border p-5 ${
          pass ? "border-emerald-200 bg-emerald-50" : "border-red-200 bg-red-50"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p
              className={`text-xs font-semibold uppercase tracking-wide ${
                pass ? "text-emerald-700" : "text-red-700"
              }`}
            >
              Clinical compliance certificate
            </p>
            <h3
              className={`mt-1 text-xl font-semibold ${
                pass ? "text-emerald-950" : "text-red-950"
              }`}
            >
              GxP guardrail {pass ? "PASS" : "BLOCKED"}
            </h3>
          </div>
          <StatusBadge value={status} />
        </div>
        <p
          className={`mt-3 text-sm leading-6 ${
            pass ? "text-emerald-900" : "font-medium text-red-900"
          }`}
        >
          {governance.isBlocked
            ? CRITICAL_COMPLIANCE_FAILURE
            : `Audit status: ${status}. Blocking errors: ${
                audit.blocking_errors ?? 0
              }. Warnings: ${audit.warning_count ?? 0}.`}
        </p>
      </div>

      {/* Rule results table */}
      <div className="overflow-hidden rounded-lg border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Rule</th>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rules.length ? (
              rules.map((rule) => (
                <tr key={`${rule.rule_name}-${rule.message}`}>
                  <td className="px-4 py-3 font-medium text-ink">
                    {rule.rule_name}
                  </td>
                  <td className="px-4 py-3 text-slate-700">{rule.severity}</td>
                  <td className="px-4 py-3 leading-6 text-slate-600">
                    {rule.message}
                  </td>
                </tr>
              ))
            ) : failedRules.length ? (
              failedRules.map((rule) => (
                <tr key={rule}>
                  <td className="px-4 py-3 font-medium text-ink">{rule}</td>
                  <td className="px-4 py-3 text-slate-700">Recorded</td>
                  <td className="px-4 py-3 text-slate-600">
                    See audit summary for disposition.
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-3 text-slate-600" colSpan="3">
                  No failed audit rules.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <NarrativeCard
        title="Audit reasoning"
        tone={pass ? "emerald" : "red"}
        alert={governance.isBlocked ? SYSTEM_LOCK_MESSAGE : ""}
        content={audit.reasoning || "No audit reasoning returned."}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// ReportTab — prepends lock banner for all roles when blocked
// ---------------------------------------------------------------------------
function ReportTab({ analysis, role }) {
  const report = analysis.report || {};
  const sections = report.report_sections || {};
  const governance = getGovernanceState(analysis);
  const nextActions = Array.isArray(sections.next_actions || report.next_actions)
    ? sections.next_actions || report.next_actions
    : [];
  const sectionEntries = Object.entries(sections).filter(
    ([key]) => key !== "next_actions"
  );

  if (!Object.keys(report).length) {
    return <EmptyState title="No final report generated for this step" />;
  }

  return (
    <div className="space-y-5">
      {/* SYSTEM LOCK banner — visible to Admin & Executive too */}
      {governance.isBlocked ? (
        <div className="rounded-md border border-red-900 bg-red-900 px-4 py-3 text-sm font-bold uppercase tracking-wide text-white">
          {SYSTEM_LOCK_MESSAGE}
        </div>
      ) : null}

      <NarrativeCard
        title={role === "executive" ? "Executive Summary" : "Final Recommendation"}
        tone={governance.isBlocked ? "red" : "indigo"}
        alert={governance.isBlocked ? SYSTEM_LOCK_MESSAGE : ""}
        content={
          report.executive_summary ||
          report.reasoning ||
          "No report summary returned."
        }
      />

      {sectionEntries.length ? (
        <Accordion
          items={sectionEntries.map(([key, value]) => ({
            title: key.replaceAll("_", " "),
            content: value,
          }))}
        />
      ) : null}

      {nextActions.length ? (
        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Division</th>
                <th className="px-4 py-3">Prescriptive action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {nextActions.map((row, index) => (
                <tr key={`${row.role || "role"}-${index}`}>
                  <td className="px-4 py-3 font-medium text-ink">{row.role}</td>
                  <td className="px-4 py-3 leading-6 text-slate-600">
                    {row.action}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// LogsTab
// ---------------------------------------------------------------------------
function LogsTab({ analysis }) {
  const traces = Array.isArray(analysis.traces) ? analysis.traces : [];
  const logs = Array.isArray(analysis.system_logs) ? analysis.system_logs : [];

  return (
    <div className="space-y-5">
      <div>
        <h3 className="text-base font-semibold text-ink">
          Raw Agent JSON Traces
        </h3>
        <div className="mt-3 space-y-3">
          {traces.length ? (
            traces.map((trace) => (
              <details
                key={trace.step}
                className="rounded-lg border border-slate-200 bg-slate-50 p-4"
              >
                <summary className="cursor-pointer text-sm font-semibold text-ink">
                  {trace.step} - {trace.duration_seconds ?? 0}s
                </summary>
                <pre className="mt-3 max-h-80 overflow-auto rounded-md bg-slate-950 p-3 text-xs leading-5 text-slate-100">
                  {JSON.stringify(trace.result, null, 2)}
                </pre>
              </details>
            ))
          ) : (
            <EmptyState title="No trace data generated for this step" />
          )}
        </div>
      </div>

      <div>
        <h3 className="text-base font-semibold text-ink">System Logs</h3>
        {logs.length ? (
          <ul className="mt-3 space-y-2">
            {logs.map((line, index) => (
              <li
                key={`${line}-${index}`}
                className="rounded-md bg-slate-50 px-3 py-2 font-mono text-xs text-slate-700"
              >
                {line}
              </li>
            ))}
          </ul>
        ) : (
          <div className="mt-3">
            <EmptyState title="No system logs generated for this step" />
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared UI primitives
// ---------------------------------------------------------------------------
function Accordion({ items }) {
  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <details
          key={`${item.title}-${index}`}
          className="rounded-lg border border-slate-200 bg-white p-4 open:bg-slate-50"
        >
          <summary className="cursor-pointer text-sm font-semibold capitalize text-ink">
            {item.title}
          </summary>
          <div className="mt-3">
            <ContentBlock content={item.content} />
          </div>
        </details>
      ))}
    </div>
  );
}

function ContentBlock({ content }) {
  if (content == null || content === "") {
    return (
      <p className="text-sm text-slate-500">No data generated for this step.</p>
    );
  }

  if (typeof content === "object") {
    return (
      <dl className="grid gap-2 sm:grid-cols-2">
        {Object.entries(content).map(([key, value]) => (
          <div
            key={key}
            className="rounded-md border border-slate-200 bg-white p-3"
          >
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {key.replaceAll("_", " ")}
            </dt>
            <dd className="mt-1 text-sm font-medium text-ink">
              {String(value ?? "Unavailable")}
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return <MarkdownLikeText text={String(content)} />;
}

function MarkdownLikeText({ text }) {
  const lines = text
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (!lines.length) {
    return (
      <p className="text-sm text-slate-500">No data generated for this step.</p>
    );
  }

  return (
    <div className="space-y-2 text-sm leading-6 text-slate-700">
      {lines.map((line, index) => {
        const listLike = /^[-*]\s+/.test(line);
        const cleanLine = line.replace(/^[-*]\s+/, "");
        return listLike ? (
          <div key={`${line}-${index}`} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 rounded-full bg-blue-500" />
            <p>{cleanLine}</p>
          </div>
        ) : (
          <p key={`${line}-${index}`}>{cleanLine}</p>
        );
      })}
    </div>
  );
}

function NarrativeCard({ title, content, tone = "blue", alert = "" }) {
  const tones = {
    blue: "border-blue-200 bg-blue-50",
    indigo: "border-indigo-200 bg-indigo-50",
    emerald: "border-emerald-200 bg-emerald-50",
    red: "border-red-200 bg-red-50",
  };

  return (
    <div className={`rounded-lg border p-4 ${tones[tone] || tones.blue}`}>
      <p className="text-sm font-semibold text-ink">{title}</p>
      {alert ? (
        <div className="mt-3 rounded-md border border-red-900 bg-red-900 px-3 py-2 text-xs font-bold uppercase tracking-wide text-white">
          {alert}
        </div>
      ) : null}
      <div className="mt-2">
        <ContentBlock content={content} />
      </div>
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, detail, tone = "blue" }) {
  const tones = {
    blue: "bg-blue-50 text-blue-700",
    emerald: "bg-emerald-50 text-emerald-700",
    amber: "bg-amber-50 text-amber-700",
    indigo: "bg-indigo-50 text-indigo-700",
    red: "bg-red-50 text-red-700",
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-semibold uppercase tracking-wide text-slate-500">
            {label}
          </p>
          <p className="mt-1 text-2xl font-semibold text-ink">
            {value ?? "-"}
          </p>
          {detail ? (
            <p className="mt-1 text-sm text-slate-500">{detail}</p>
          ) : null}
        </div>
        <div
          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-md ${
            tones[tone] || tones.blue
          }`}
        >
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ value }) {
  const normalized = String(value || "UNKNOWN").toUpperCase();
  return (
    <span
      className={`inline-flex min-h-7 items-center rounded-md border px-2.5 text-xs font-bold uppercase tracking-wide ${
        statusStyles[normalized] || "border-slate-200 bg-slate-50 text-slate-700"
      }`}
    >
      {normalized.replaceAll("_", " ")}
    </span>
  );
}

function EmptyState({ title }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
      <div className="mx-auto mb-3 h-8 w-32 animate-pulse rounded bg-slate-200" />
      <p className="text-sm font-medium text-slate-600">{title}</p>
    </div>
  );
}

function formatNumber(value) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) return "0";
  return numeric.toLocaleString();
}
