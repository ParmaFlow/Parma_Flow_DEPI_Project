# services/action_service.py
"""
Action Service — executes the side effects (ERP orders, notifications,
tickets, alerts) implied by a decision, separate from workflow execution
and response mapping.

This preserves the exact console-output behavior of the original
QueryService._trigger_action, just relocated for single-responsibility.
"""
import datetime

from backend.agents.shared.models import LegacyDecisionResponse
from backend.agents.shared.constants import ActionType


class ActionService:
    """
    Executes operational side effects for a mapped decision.

    Stateless by design (no instance data), so it's exposed as static
    methods rather than requiring instantiation.
    """

    @staticmethod
    def execute(decision: LegacyDecisionResponse) -> None:
        """
        Announce and execute the side effects implied by a decision.

        Inputs:
            decision: LegacyDecisionResponse produced by WorkflowMapper.
                Expected to have action/sku_name/recommended_qty/assignee
                populated (i.e. not a FAILED response).
        Outputs:
            None. Side effects are printed to stdout, matching the
            original system's simulated integrations (ERP, notifications,
            tickets).
        """
        action = (decision.action or ActionType.MONITOR.value).upper()
        sku_name = decision.sku_name or "Unknown SKU"
        qty = decision.recommended_qty or 0

        print("\n" + "=" * 50)
        print(f"🔍 ANALYZING: {sku_name}")
        print(f"🤖 AGENT DECISION: {action}")
        print(f"Reason: {decision.reasoning or 'No reason provided'}")
        print("=" * 50)

        ActionService._trigger_action(action, sku_name, qty, decision)

    @staticmethod
    def _trigger_action(
        action: str,
        sku_name: str,
        qty: int,
        decision: LegacyDecisionResponse,
    ) -> None:
        """
        Perform the action-specific simulated side effect.

        Inputs:
            action: uppercased action string (e.g. "REORDER").
            sku_name: SKU the action concerns.
            qty: recommended quantity, used for REORDER messaging.
            decision: full decision, used for fields like assignee.
        Outputs:
            None.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if action == ActionType.REORDER.value:
            print("📡 [EXTERNAL API]: Connecting to Procurement System (ERP)...")
            print(f"📝 [PURCHASE ORDER]: PO-{sku_name[:3].upper()}-{qty} generated.")
            print(f"✅ [SUCCESS]: Order for {qty} units of {sku_name} sent to supplier at {timestamp}.")

        elif action == ActionType.REDISTRIBUTE.value:
            print(f"📧 [NOTIFICATION]: Sending urgent email to {decision.assignee or 'Store Manager'}...")
            print(f"⚠️ [ALERT]: Request to move {sku_name} to nearest hospital branch issued.")
            print("📲 [PUSH NOTIFICATION]: Sent to Logistics Team handheld devices.")

        elif action == ActionType.HUMAN_REVIEW.value:
            print(f"🚨 [SYSTEM LOCK]: Autonomous ordering suspended for {sku_name} due to HIGH UNCERTAINTY.")
            print("👨‍⚕️ [TICKET CREATED]: Technical Review ticket #7782 assigned to Pharmacy Manager.")
            print("📧 [EMAIL SENT]: Request for manual forecast verification sent to Data Analytics team.")
            print("📊 [DATA]: Confidence gap exceeded safety threshold (Safe AI Protocol).")

        elif action == ActionType.AUDIT.value:
            print(f"🚨 [SECURITY ALERT]: Data anomaly detected for {sku_name}!")
            print("🔒 [ACTION]: SKU flagged for manual audit by the compliance team.")

        else:
            print("📊 [LOG]: No external action required. Status logged in Daily Inventory Report.")

        print("=" * 50 + "\n")