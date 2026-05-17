# services/ingestion_service.py
from data_sources.pubmed_api import PubMedAPI
import os

class IngestionService:
    def __init__(self):
        # استخدمنا الإيميل الخاص بك كما في الملف القديم
        self.api = PubMedAPI(email="yossifmesalam@gmail.com")
        # تعديل المسار ليكون داخل المشروع الحالي
        self.file_path = os.path.join("data", "raw", "pubmed.txt")

    def ingest_pubmed(self, query):
        print(f"📡 Fetching live data from PubMed for: {query}...")
        raw_data = self.api.fetch_papers(query, max_results=10)

        # التأكد من أن الفولدرات موجودة (data/raw)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # حفظ البيانات في المسار الجديد
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(raw_data)
        
        print(f"✅ Data successfully saved to: {self.file_path}")
        return raw_data