# Pharma-Flow

**Multi-Agent Pharmaceutical Supply Chain Intelligence System**

An enterprise-grade AI pipeline that analyzes pharmaceutical inventory data through a four-stage multi-agent workflow (Ops → Risk → Audit → Report) with deterministic business logic, LLM-powered explanations, and a Safe AI Guardrail.

---

## Architecture

```
app/main.py
  └─ QueryService
       ├─ backend.bootstrap.build_orchestrator()
       │    └─ Orchestrator
       │         ├─ OpsAgent    → inventory gap, safety stock, reorder point (Python)
       │         │               + LLM explanation (OPS_AGENT_PROMPT)
       │         ├─ RiskAgent   → multi-factor risk score 0-100 (Python)
       │         │               + LLM clinical risk bulletin
       │         ├─ AuditorAgent→ GxP rule engine (Python)
       │         │               + LLM compliance narrative
       │         └─ ReportAgent → LLM executive report synthesis
       └─ ActionService  (ERP side-effects: purchase orders, alerts, tickets)

core/llm.py          → single LLM integration point (retry, backoff, timeout)
core/vectorstore.py  → FAISS nearest-neighbour retrieval
core/embeddings.py   → sentence-transformers embedding wrapper
rag/pipeline.py      → RAG pipeline (chunking → embedding → retrieval)
data_sources/        → PubMed API client + Document loader
app/config/settings.py → centralized configuration (all env vars)
```

### Explainable AI Contract
All numerical calculations (inventory gap, risk score, rule checks) are performed **deterministically in Python**. The LLM is used **only** to generate human-readable explanation text. This ensures results are auditable, reproducible, and free from LLM arithmetic errors.

---

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd Parma_Flow_DEPI_Project-mainn
```

### 2. Create a virtual environment
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```

Edit `.env` and fill in **at minimum** these two required values:

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key ([get one here](https://console.groq.com)) | ✅ Yes |
| `ENTREZ_EMAIL` | Institutional email for NCBI Entrez API | ✅ Yes |

See `.env.example` for all optional tuning variables (LLM model, RAG chunk size, etc.).

### 5. (Optional) Ingest PubMed data for RAG
The application runs without RAG in Development Mode. To enable RAG:
```bash
# Uncomment the IngestionService lines in app/main.py, then run:
python app/main.py
```
Or run ingestion standalone:
```python
from services.ingestion_service import IngestionService
svc = IngestionService()
svc.ingest_pubmed("Paracetamol drug interactions and alternatives")
```
> The corpus is saved to `data/raw/pubmed.txt` (excluded from git via `.gitignore`).

### 6. Run the demo
```bash
python app/main.py
```

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Groq LLM API key **(required)** |
| `ENTREZ_EMAIL` | — | NCBI institutional email **(required for ingestion)** |
| `ENTREZ_API_KEY` | — | NCBI API key (optional — raises rate limit) |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Groq model name |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | LLM API endpoint |
| `LLM_TIMEOUT_SECONDS` | `30.0` | Request timeout |
| `LLM_MAX_RETRIES` | `3` | Retry attempts on transient errors |
| `LLM_TEMPERATURE` | `0.2` | Sampling temperature |
| `LLM_MAX_TOKENS` | `800` | Max response tokens |
| `PUBMED_DATA_PATH` | `data/raw/pubmed.txt` | RAG corpus file path |
| `PUBMED_MAX_RESULTS` | `10` | Articles fetched per ingestion query |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `RAG_CHUNK_SIZE` | `300` | Characters per text chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks |
| `RAG_RETRIEVAL_K` | `3` | Nearest-neighbour results to retrieve |

---

## Project Structure

```
├── app/
│   ├── main.py                    # Application entry point
│   └── config/
│       └── settings.py            # Centralized configuration (all env vars)
├── backend/
│   ├── bootstrap.py               # Dependency injection / composition root
│   └── agents/
│       ├── orchestrator/          # Multi-agent workflow coordinator
│       ├── ops_agent/             # Inventory gap & reorder logic
│       ├── risk_agent/            # Multi-factor risk scoring
│       ├── auditor_agent/         # GxP compliance rule engine
│       ├── report_agent/          # Executive report synthesis
│       └── shared/                # Models, constants, exceptions, logger
├── core/
│   ├── llm.py                     # LLM client (retry, backoff, timeout)
│   ├── embeddings.py              # Sentence-transformers wrapper
│   └── vectorstore.py             # FAISS vector store
├── rag/
│   ├── pipeline.py                # RAG pipeline (canonical)
│   ├── indexing.py                # Index builder
│   ├── chunking.py                # Text chunking
│   └── retriever.py               # Nearest-neighbour retrieval
├── services/
│   ├── query_service.py           # API-facing entry point
│   ├── action_service.py          # ERP/notification side effects
│   └── ingestion_service.py       # PubMed data ingestion
├── data_sources/
│   ├── pubmed_api.py              # NCBI Entrez client
│   └── loaders.py                 # Document loader
├── data/
│   └── raw/
│       └── .gitkeep               # Placeholder — pubmed.txt goes here
├── .env.example                   # Environment variable template
├── .gitignore
└── requirements.txt
```

---

## Running Tests

```bash
# Verification script (mock LLM, no API key needed)
python C:\Users\HP\.gemini\antigravity\brain\0fe6be55-9bce-44b8-8cbf-a3854cb557c2\scratch\verify_merged.py
```

---

## Security Notes

- **Never commit `.env`** — it is excluded via `.gitignore`
- The NCBI SSL bypass (`ssl._create_default_https_context`) has been removed. All HTTPS requests use Python's default SSL context with the `certifi` CA bundle
- The `ENTREZ_EMAIL` must be an institutional address per NCBI Terms of Service

---

## Sprint Status

| Sprint | Feature | Status |
|---|---|---|
| Sprint 1 | Single-agent decision engine + RAG pipeline | ✅ Complete |
| Sprint 2 | Multi-agent orchestrator (Ops/Risk/Audit/Report) | ✅ Complete |
| Sprint 2 | Enterprise-grade audit hardening (23 findings resolved) | ✅ Complete |
