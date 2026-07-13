/**
 * governance.js — Top-Down Unified Governance Rule
 *
 * Single source of truth for determining whether the current workflow
 * is BLOCKED / FAILED by the GxP Audit Agent.  Import this helper in
 * every dashboard and tab component to avoid duplicating the logic.
 */

/** Statuses that unconditionally lock the workflow. */
export const BLOCKING_STATUSES = new Set([
  "BLOCKED",
  "FAILED_AUDIT",
  "REJECTED",
  "FAILED",
  "DENIED",
]);

/** Standard messages re-used across all views. */
export const SYSTEM_LOCK_MESSAGE =
  "[SYSTEM LOCK] Operational replenishment halted by Clinical Governance.";

export const CRITICAL_COMPLIANCE_FAILURE =
  "CRITICAL COMPLIANCE FAILURE: This workflow has been blocked by the GxP Guardrail " +
  "due to severe regulatory or safety violations (e.g., Expired Product). " +
  "No operational actions are permitted.";

/**
 * Derives the governance state from an analysis response object.
 *
 * Priority order:
 *   1. Any status value that matches BLOCKING_STATUSES
 *   2. execution_allowed === false (explicit denial flag)
 *   3. audit.approved === false or compliance.approved === false
 *
 * @param {object} analysis - The full backend analysis response.
 * @returns {{ isBlocked: boolean, status: string }}
 */
export function getGovernanceState(analysis = {}) {
  const audit = analysis.audit || {};
  const report = analysis.report || {};
  const kpis = analysis.kpis || {};
  const compliance = analysis.compliance || {};

  const statusValues = [
    report.final_status,
    kpis.final_status,
    audit.disposition,
    audit.audit_status,
    audit.status,
    compliance.status,
    compliance.gxp_guardrail,
  ]
    .filter(Boolean)
    .map((v) => String(v).toUpperCase());

  const hasBlockingStatus = statusValues.some((v) => BLOCKING_STATUSES.has(v));

  const executionDenied = [
    report.execution_allowed,
    kpis.execution_allowed,
    compliance.execution_allowed,
  ].some((v) => v === false);

  const auditDenied =
    audit.approved === false || compliance.approved === false;

  const isBlocked = hasBlockingStatus || executionDenied || auditDenied;

  return {
    isBlocked,
    /** The first blocking status found, or the first status value, or a fallback. */
    status:
      statusValues.find((v) => BLOCKING_STATUSES.has(v)) ||
      statusValues[0] ||
      "UNAVAILABLE",
  };
}
