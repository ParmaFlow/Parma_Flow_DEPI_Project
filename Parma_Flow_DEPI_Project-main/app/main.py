# app/main.py
import os
from pathlib import Path  
from dotenv import load_dotenv
from services.ingestion_service import IngestionService
from services.query_service import QueryService

base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv(dotenv_path=base_dir / '.env.txt')
# ----------------------------------------------------

if __name__ == "__main__":
    MY_GROQ_KEY = os.getenv("GROQ_API_KEY") 
    
    if not MY_GROQ_KEY:
        print("❌ ERROR: GROQ_API_KEY not found in your .env file!")
        print("💡 Please create a .env file in the root directory and add: GROQ_API_KEY=your_key")
        exit(1)
    
# ----------------------------------------------------
# STEP 1 (TEMPORARILY DISABLED)
# Skip PubMed ingestion during local development.
# Existing indexed data (if any) will be used instead.
# ----------------------------------------------------

print("\n⏭️ STEP 1: Skipping PubMed ingestion (Development Mode)...")

# ingestor = IngestionService()
# ingestor.ingest_pubmed("Paracetamol drug interactions and alternatives")

print("\n🤖 STEP 2: Initializing Pharma-Flow Multi-Agent System...")

service = QueryService(api_key=MY_GROQ_KEY)


case_1 = {
        "sku": "PARA-500",
        "sku_name": "Paracetamol",
        "location_type": "hospital",
        "stock": 0,             
        "on_order": 0,
        "forecast_demand": 500, 
        "expiry_days": 60,
        "available_stock": 0,
        "confidence_low": 90,   
        "confidence_high": 95   
    }


case_2 = {
        "sku": "ASP-100",
        "sku_name": "Aspirin",
        "location_type": "warehouse",
        "stock": 10,
        "on_order": 0,
        "forecast_demand": 100,
        "expiry_days": 100,
        "available_stock": 10,
        "confidence_low": 1,   
        "confidence_high": 99   
    }


print("\n🔥 RUNNING SCENARIO 1: Clinical Shortage (RAG Enabled)")
service.execute_agent_decision(case_1)

print("\n🔥 RUNNING SCENARIO 2: Data Uncertainty (Safe AI Mode)")
service.execute_agent_decision(case_2)

print("\n✅ --- SPRINT 2 DEMO COMPLETED SUCCESSFULLY --- ✅")