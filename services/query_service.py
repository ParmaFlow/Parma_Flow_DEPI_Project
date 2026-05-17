# services/query_service.py
from agent.decision_maker import PharmaAgent
import datetime

class QueryService:
    def __init__(self, api_key):
        self.agent = PharmaAgent(api_key)

    def execute_agent_decision(self, item_data):
        # 1. الحصول على القرار الذكي من الأجنت
        decision = self.agent.process_inventory_item(item_data)
        
        # 2. استخراج الأكشن والبيانات
        action = decision.get("action", "MONITOR").upper()
        sku_name = item_data.get("sku_name", "Unknown SKU")
        qty = decision.get("recommended_qty", 0)
        
        print(f"\n" + "="*50)
        print(f"🔍 ANALYZING: {sku_name} at {item_data.get('location_id', 'Main Branch')}")
        print(f"🤖 AGENT DECISION: {action}")
        print(f"Reason: {decision.get('reasoning', 'No reason provided')}")
        print("="*50)

        # 3. تنفيذ "Real Action" (Trigger)
        self._trigger_action(action, sku_name, qty, decision)
        
        return decision

    def _trigger_action(self, action, sku_name, qty, decision):
       """
       هذه الدالة تحاكي الاتصال بأنظمة خارجية (ERP, Email, Logistics) 
       مع إضافة منطق التعامل مع حالات عدم اليقين (Confidence Intervals).
       """
       import datetime
       timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
       # تحويل الأكشن لـ Upper Case لضمان المطابقة
       action = action.upper()
    
       if action == "REORDER":
           print(f"📡 [EXTERNAL API]: Connecting to Procurement System (ERP)...")
           print(f"📝 [PURCHASE ORDER]: PO-{sku_name[:3].upper()}-{qty} generated.")
           print(f"✅ [SUCCESS]: Order for {qty} units of {sku_name} sent to supplier at {timestamp}.")
        
       elif action == "REDISTRIBUTE":
           print(f"📧 [NOTIFICATION]: Sending urgent email to {decision.get('assignee', 'Store Manager')}...")
           print(f"⚠️ [ALERT]: Request to move {sku_name} to nearest hospital branch issued.")
           print(f"📲 [PUSH NOTIFICATION]: Sent to Logistics Team handheld devices.")

       elif action == "HUMAN_REVIEW":
           print(f"🚨 [SYSTEM LOCK]: Autonomous ordering suspended for {sku_name} due to HIGH UNCERTAINTY.")
           print(f"👨‍⚕️ [TICKET CREATED]: Technical Review ticket #7782 assigned to Pharmacy Manager.")
           print(f"📧 [EMAIL SENT]: Request for manual forecast verification sent to Data Analytics team.")
           print(f"📊 [DATA]: Confidence gap exceeded safety threshold (Safe AI Protocol).")
        
       elif action == "AUDIT":
           print(f"🚨 [SECURITY ALERT]: Data anomaly detected for {sku_name}!")
           print(f"🔒 [ACTION]: SKU flagged for manual audit by the compliance team.")
        
       else:
           print(f"📊 [LOG]: No external action required. Status logged in Daily Inventory Report.")

       print("="*50 + "\n")