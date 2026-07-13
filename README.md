# 💊 Pharma-Flow: AI-Powered Pharmacy Intelligence & Multi-Agent Ecosystem

Pharma-Flow is a production-ready pharmaceutical supply chain intelligence platform. It combines a deterministic multi-agent reasoning engine, a sanitized RAG pipeline, a FastAPI backend, and a React dashboard into one clean delivery repository.

The system is designed around a strict principle: LLMs may explain precomputed facts, but they do not calculate, validate, or decide operational outcomes.

## 🚀 Overview

Pharma-Flow helps pharmacy, procurement, compliance, and executive teams evaluate inventory shortages, replenishment risk, expiry dominance, and clinical governance status through one unified workflow.

The production flow is:

```text
React Simulator
  -> FastAPI /api/workflows/analyze
  -> Multi-Agent Orchestrator
  -> OpsAgent -> RiskAgent -> AuditorAgent -> ReportAgent
  -> deterministic JSON response
  -> role-aware React dashboards
```

## 🧠 Core Production Ecosystem

### 1. Production Data Inputs (`/data`)

- Forecast demand, available stock, lead time, expiry days, on-order quantity, and confidence bounds are accepted through the React simulator and FastAPI workflow endpoint.
- Optional inventory datasets can populate inventory summaries and selection lists.

### 2. Multi-Agent AI System (`/backend/agents`)

- 👑 **Orchestrator Agent:** Coordinates the Ops, Risk, Auditor, and Report agents in a deterministic execution order.
- 📦 **OpsAgent:** Calculates stock gap, safety stock, reorder point, rounded reorder quantity, inventory status, and operational action.
- ⚠️ **RiskAgent:** Scores shortage, expiry, criticality, lead-time, low-stock, and confidence-width risk factors.
- 🛡️ **AuditorAgent:** Enforces compliance rules, expiry dominance, blocker counts, and workflow approval.
- 📝 **ReportAgent:** Produces the final executive report and strictly partitioned `next_actions` array for React.

### 3. RAG-Powered Clinical Context (`/backend/rag`)

- Retrieves clinical or PubMed-derived context through FAISS vector search.
- Purges institutional metadata, emails, copyright/publisher noise, affiliations, and non-clinical boilerplate before prompt injection.
- Keeps RAG context focused on biomedical relevance: safety, efficacy, dosing, mechanisms, and therapeutic continuity.

## 💻 React Dashboard

The frontend is built with React, Vite, Tailwind CSS, Lucide Icons, and Recharts.

- **Inventory Simulator:** Runs full multi-agent analysis using dynamic inventory inputs.
- **Executive Dashboard:** Displays final status, report sections, and a three-row `next_actions` matrix.
- **Pharmacist Dashboard:** Shows operational reasoning, risk posture, and actionable alerts.
- **Admin Dashboard:** Shows audit rules, traces, execution metadata, and system logs.
- **Floating AI Assistant:** Uses the RAG chat endpoint for contextual inventory and clinical questions.

## 🛡️ Quality Assurance & Invariants

The repository includes **7 automated unit tests** in `tests/test_inventory_alignment.py`. These tests protect the core business and clinical invariants that make the system production-safe.

| Test Focus | Invariant Protected | Why It Matters |
|---|---|---|
| Clopidogrel stockout alignment | Rounded `recommended_qty` must never contradict deterministic shortage math | Prevents raw gap leakage and UI quantity drift |
| Report quantity coherence | Report prose and action payloads must use one rounded procurement quantity | Prevents hallucinated or duplicate reorder numbers |
| Zero-stock cold start | Stock cover is forced to `0.00`; full target plus safety reset is reordered | Prevents divide-by-zero and under-ordering during stockout |
| Zero-demand simulation | Zero or negative demand locks action to `HOLD_MONITOR` and suppresses shortage risk | Prevents non-logical alerts from simulator edge cases |
| Expiry dominance | Shelf life below lead time or below 30 days forces `FAILED_AUDIT` and disposal/replacement | Ensures clinical governance overrides volume logic |
| RAG purification | Metadata, emails, and institutional boilerplate are stripped from retrieved context | Prevents polluted biomedical context from entering prompts |
| React action contract | `next_actions` is normalized into exactly three role rows | Prevents flattened UI blocks and rendering duplication |

Run the validation suite:

```bash
python -m unittest discover tests
```

Run syntax validation:

```bash
python -m compileall backend tests
```

## 📊 Integrated Evaluation Matrix

The multi-agent ecosystem avoids LLM hallucinations by separating deterministic computation from language generation. Each agent receives structured inputs, performs bounded logic, and emits a typed contract consumed by the next layer.

| Agent | Input Sources | Core Reasoning Logic | Strict Invariants Enforced | Output API Contract |
|---|---|---|---|---|
| OpsAgent | `sku_name`, `available_stock`, `forecast_demand`, lead time, demand statistics, location type | Calculates safety stock, reorder point, inventory gap, rounded reorder quantity, inventory status, and action | Zero stock produces `OUT_OF_STOCK`, `0.00` stock cover, and mandatory `REORDER`; zero/negative demand produces `HOLD_MONITOR`; `recommended_qty` is rounded up and never below positive gap | `OperationalDecision` with `action`, `inventory_gap`, `recommended_qty`, `safety_stock`, `reorder_point`, `inventory_status`, `reasoning` |
| RiskAgent | `OperationalDecision`, expiry days, confidence interval, critical drug category, lead time | Scores shortage, expiry, low stock, criticality, long lead time, and epistemic uncertainty | `HOLD_MONITOR` suppresses shortage risk; risk score is bounded 0-100; high risk triggers human review | `RiskAssessment` with `risk_score`, `risk_level`, `shortage_risk`, `expiry_risk`, `criticality`, `human_review_recommended` |
| AuditorAgent | `OperationalDecision`, `RiskAssessment`, original inventory payload | Validates input quality, business rules, cross-agent consistency, expiry dominance, blocker severity, warning severity | Expiry below lead time or below 30 days emits `EXPIRY_DOMINANCE_OVERRIDE`; `blocking_errors=1` for expiry dominance; positive reorder quantity must match `REORDER`; impossible states are rejected | `AuditResult` with `approved`, `audit_status`, `failed_rules`, `warning_count`, `blocking_errors`, `rule_results` |
| ReportAgent | `OperationalDecision`, `RiskAssessment`, `AuditResult` | Synthesizes a grounded executive report without recalculating upstream quantities | Expiry dominance shifts final action to `URGENT_DISPOSAL_AND_REPLACEMENT`; rounded quantity is the only procurement quantity; `next_actions` remains role-partitioned | `FinalDecision` with `execution_allowed`, `final_status`, `recommended_action`, `report_sections`, and `next_actions` array |

### API Contract Guardrail

The FastAPI bridge in `backend/api/services.py` converts dataclass outputs into JSON-safe payloads and applies `normalize_next_actions()` from `backend/api/contracts.py`.

The React-facing `next_actions` contract is always:

```json
[
  {"role": "Procurement Officer", "action": "string"},
  {"role": "Clinical Governance", "action": "string"},
  {"role": "Supply Chain Lead", "action": "string"}
]
```

This prevents role flattening, duplicate table rendering, and accidental free-text action blobs.

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Agents:** Deterministic Python rule engines with LLM-grounded explanation support
- **LLM Client:** OpenAI-compatible Groq API wrapper
- **RAG:** FAISS, sentence-transformers, PubMed ingestion utilities
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Infrastructure:** Docker, Docker Compose, Nginx

## 🐳 Quick Start: Docker

1. Configure environment variables:

```bash
cp .env.example .env
```

Add your `GROQ_API_KEY` to `.env`.

2. Build and start:

```bash
docker-compose up --build
```

3. Open:

```text
Frontend: http://localhost
Backend API Docs: http://localhost:8000/docs
```

## 🏗️ Local Development

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📁 Repository Layout

```text
backend/
  agents/
  api/
  config/
  core/
  data_sources/
  rag/
  services/
frontend/
tests/
data/
docker-compose.yml
backend.Dockerfile
requirements.txt
```

## ✅ Production Contract Summary

- React is the only presentation layer.
- FastAPI is the only backend entrypoint.
- Agent logic is deterministic and typed.
- LLMs explain grounded facts only.
- RAG context is sanitized before use.
- Tests lock the critical numerical, clinical, and UI contract invariants.
