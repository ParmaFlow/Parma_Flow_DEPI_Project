# Pharma-Flow AI

Production-grade multi-agent pharmaceutical inventory intelligence for shortage detection, clinical risk assessment, GxP audit control, and executive reporting.

Pharma-Flow runs inventory scenarios through a deterministic Ops -> Risk -> Audit -> Report pipeline. Numeric decisions are computed in Python first; generated text is grounded from those computed fields so the dashboard, agent narratives, and next actions cannot disagree about stock gaps, reorder quantities, audit blocks, or final status.

---

## What It Does

- Computes reorder point, safety stock, inventory gap, stock cover, and recommended order quantity.
- Scores shortage, expiry, lead-time, confidence, and clinical criticality risk.
- Applies a GxP-style audit rule engine before autonomous execution is allowed.
- Produces executive report sections and prescriptive next actions from one unified state.
- Cleans PubMed/RAG context before it reaches the UI or prompt layer.
- Provides a Streamlit dashboard for EDA, what-if simulation, agent traces, and report output.

---

## Core Guarantees

### Deterministic Math First

The LLM is never trusted to calculate inventory or risk values. Agents compute all operational facts in Python, then any narrative text is generated from those facts.

Key invariant:

```text
inventory_gap = max(max(reorder_point, forecast_demand) - available_stock, 0)
```

For zero-stock emergencies, OpsAgent adds the safety target to force a full shelf reset.

### Guardrails

- If `available_stock == 0`, stock cover is `0.00`, action is `REORDER`, and recommended quantity is nonzero.
- If `forecast_demand <= 0` while stock is positive, action becomes `HOLD_MONITOR`; RiskAgent suppresses shortage alarms and logs: `Zero demand input detected; inventory tracking paused.`
- All displayed and reported order quantities use the same rounded `recommended_qty`.
- If `expiry_days < lead_time` or `expiry_days < 30`, AuditorAgent forces `FAILED_AUDIT`, blocks execution, and ReportAgent recommends `URGENT_DISPOSAL_AND_REPLACEMENT`.
- Report sections render once in the dashboard; next actions appear only in the prescriptive action table.
- RAG context strips emails, affiliations, DOI/PMID metadata, and researcher-address noise.

---

## Architecture

```text
app/Pharmaflow_dashboard.py
  Streamlit dashboard
  - EDA and supply-chain insights
  - What-if simulation controls
  - PubMed/RAG context display
  - Multi-agent trace and executive report

app/main.py
  CLI/demo entry point

backend/bootstrap.py
  Composition root for registry, logger, and orchestrator

backend/agents/orchestrator/
  Orchestrator
  - OpsAgent
  - RiskAgent
  - AuditorAgent
  - ReportAgent

backend/agents/shared/
  Dataclasses, constants, registry, mapper, exceptions, logger

core/
  llm.py          LLM client wrapper
  embeddings.py   Sentence-transformers wrapper
  vectorstore.py  FAISS vector store

rag/
  pipeline.py     RAG retrieval and context cleaning
  indexing.py     Corpus indexing
  chunking.py     Text chunking
  retriever.py    Nearest-neighbor retrieval

services/
  query_service.py
  action_service.py
  ingestion_service.py
```

---

## Agent Responsibilities

| Agent | Responsibility | Deterministic Outputs |
|---|---|---|
| OpsAgent | Inventory math and operational action | `inventory_gap`, `safety_stock`, `reorder_point`, `recommended_qty`, `inventory_status`, `action` |
| RiskAgent | Clinical and supply-chain risk scoring | `risk_score`, `risk_level`, `shortage_risk`, `expiry_risk`, `human_review_recommended` |
| AuditorAgent | Compliance and consistency checks | `approved`, `audit_status`, `failed_rules`, `warning_count`, `blocking_errors` |
| ReportAgent | Executive synthesis from upstream state | `execution_allowed`, `final_status`, `recommended_action`, report sections |

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Required for LLM-backed runtime:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key for the OpenAI-compatible LLM endpoint |

Required only for PubMed ingestion:

| Variable | Description |
|---|---|
| `ENTREZ_EMAIL` | Institutional email for NCBI Entrez |
| `ENTREZ_API_KEY` | Optional NCBI API key for higher rate limits |

---

## Running the App

### Streamlit dashboard

```bash
streamlit run app/Pharmaflow_dashboard.py
```

### CLI/demo workflow

```bash
python app/main.py
```

---

## Data Inputs

The dashboard expects:

```text
data/sprint1_output.json
data/final_dataset.csv
```

RAG ingestion writes the PubMed corpus to:

```text
data/raw/pubmed.txt
```

That corpus is intentionally excluded from version control.

---

## Optional PubMed/RAG Ingestion

Use the ingestion service from a Python shell or script:

```python
from services.ingestion_service import IngestionService

svc = IngestionService()
svc.ingest_pubmed("drug shortage alternatives hospital pharmacy")
```

The dashboard will still run without a RAG index. If retrieval is unavailable, it falls back to standard shortage-protocol context.

---

## Testing

Run the regression suite:

```bash
python -m unittest discover -s tests
```

Compile-check the main modules:

```bash
python -m py_compile backend/agents/ops_agent/ops_agent.py backend/agents/risk_agent/risk_agent.py backend/agents/auditor_agent/auditor_agent.py backend/agents/report_agent/report_agent.py app/Pharmaflow_dashboard.py
```

Current regression coverage includes:

- Clopidogrel-style ROP shortage alignment.
- Zero-stock divide-by-zero protection.
- Zero-demand `HOLD_MONITOR` behavior.
- Expiry dominance audit block.
- Report quantity consistency.
- RAG metadata/email cleaning.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---:|---|
| `GROQ_API_KEY` | none | LLM API key |
| `LLM_MODEL` | `llama-3.1-8b-instant` | LLM model name |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible endpoint |
| `LLM_TIMEOUT_SECONDS` | `30.0` | LLM request timeout |
| `LLM_MAX_RETRIES` | `3` | Retry attempts |
| `LLM_TEMPERATURE` | `0.2` | Generation temperature |
| `LLM_MAX_TOKENS` | `800` | Response token limit |
| `ENTREZ_EMAIL` | none | NCBI Entrez email |
| `ENTREZ_API_KEY` | none | Optional NCBI key |
| `PUBMED_DATA_PATH` | `data/raw/pubmed.txt` | RAG corpus path |
| `PUBMED_MAX_RESULTS` | `10` | PubMed articles per ingestion |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `RAG_CHUNK_SIZE` | `300` | RAG chunk size |
| `RAG_CHUNK_OVERLAP` | `50` | RAG chunk overlap |
| `RAG_RETRIEVAL_K` | `3` | Number of retrieved chunks |

---

## Repository Layout

```text
app/
  Pharmaflow_dashboard.py
  main.py
  config/settings.py

backend/
  bootstrap.py
  agents/
    orchestrator/
    ops_agent/
    risk_agent/
    auditor_agent/
    report_agent/
    shared/

core/
  llm.py
  embeddings.py
  vectorstore.py

rag/
  pipeline.py
  indexing.py
  chunking.py
  retriever.py

services/
  query_service.py
  action_service.py
  ingestion_service.py

data_sources/
  pubmed_api.py
  loaders.py

tests/
  test_inventory_alignment.py
```

---

## Security Notes

- Do not commit `.env`.
- Keep API keys out of notebooks, logs, and screenshots.
- PubMed ingestion requires a valid institutional email for NCBI compliance.
- LLM output is treated as explanatory text only; deterministic Python state remains the source of truth.

---

## Production Posture

Pharma-Flow is designed so operational math, risk scoring, audit gating, dashboard badges, and final report text all derive from the same state object. If a hidden edge case appears, the intended failure mode is a blocked or paused workflow with explicit reasoning, not contradictory procurement instructions.
