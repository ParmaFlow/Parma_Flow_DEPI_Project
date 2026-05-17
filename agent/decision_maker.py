# agent/decision_maker.py
from core.llm import LLMModel
from app.config.prompts import PHARMA_AGENT_PROMPT
from rag.pipline import RAGPipeline
import json

class PharmaAgent:
    def __init__(self, api_key):
        self.llm = LLMModel(api_key)
        # تأكد أن المسار صحيح لملف الـ RAG
        self.rag = RAGPipeline("data/raw/pubmed.txt")

    def process_inventory_item(self, item_data):
        # 1. تحليل البيانات شاملة الـ Confidence Intervals
        raw_decision_json = self.llm.get_decision(PHARMA_AGENT_PROMPT, item_data)
        decision = json.loads(raw_decision_json)
        
        # 2. فحص الأمان (Safe AI Protocol)
        # إذا كانت الفجوة بين High و Low كبيرة، الأجنت سيتوقف عن اتخاذ قرار آلي
        if decision.get("action") == "HUMAN_REVIEW":
            print(f"⚠️ [SAFETY PROTOCOL]: High uncertainty detected for {item_data.get('sku_name')}.")
            decision["reasoning"] += " | Reason: Prediction interval exceeds safety threshold."
            return decision 

        # 3. الربط الذكي مع الـ RAG (في حالة الـ REORDER)
        if decision.get("action") == "REORDER":
            sku_name = item_data.get("sku_name")
            print(f"🧠 [AGENT THOUGHT]: Shortage detected for {sku_name}. Searching RAG for medical alternatives...")
            
            query = f"What are the clinical alternatives or substitutes for {sku_name} in case of shortage?"
            medical_context = self.rag.run(query)
            
            decision["medical_insight"] = medical_context
            decision["recommendation_details"] += f"\n\n[Medical Note from PubMed]: {medical_context[:300]}..."
        
        return decision