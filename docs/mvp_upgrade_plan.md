# Pharma-Flow AI MVP Upgrade Plan

## 1. Backend/API Structure

1. Keep the existing deterministic agents and RAG modules unchanged.
2. Add a FastAPI layer under `backend/api/`:
   - `main.py`: FastAPI app, CORS, router registration, health endpoint.
   - `schemas.py`: Pydantic request/response contracts.
   - `security.py`: mock authentication, token parsing, RBAC dependencies.
   - `services.py`: dataset loading, orchestrator execution, response mapping, role filtering.
   - `routes/auth.py`: login and current-user endpoints.
   - `routes/inventory.py`: inventory SKU list and dataset summary.
   - `routes/workflows.py`: multi-agent analysis endpoint replacing the Streamlit pipeline button.
   - `routes/rag.py`: optional clinical/RAG context endpoint.
3. Let API callers submit inventory cases through `POST /api/workflows/analyze`.
4. Return the same underlying workflow facts to all roles, but expose role-specific API views:
   - Pharmacist/Ops: operational alerts, inventory gap, recommended quantity, risk posture, next actions.
   - Executive: high-level KPIs, final status, report sections, executive summary.
   - Admin: full state, agent traces, durations, audit rules, system/compliance status.
5. Move real authentication later behind the same dependency boundary. The mock RBAC layer can later be replaced with JWT/OIDC without rewriting agents or dashboards.

## 2. Frontend Structure

1. Add a standalone React app under `frontend/` using Vite and Tailwind CSS.
2. Keep the UI role-aware:
   - `LoginPanel`: mock login for admin/pharmacist/executive users.
   - `Shell`: application chrome and role badge.
   - `SimulationPanel`: SKU selection and what-if input controls.
   - `DashboardRouter`: selects the dashboard for the logged-in role.
   - `PharmacistDashboard`: operational alerts and reorder actions.
   - `ExecutiveDashboard`: KPIs and ReportAgent sections.
   - `AdminDashboard`: trace, compliance, audit rules, raw state.
3. Use `frontend/src/api/client.js` as the only browser-to-API client boundary.
4. Keep all computed quantities server-side. React only displays API data.

## 3. Migration Steps

1. Run existing tests to baseline deterministic behavior.
2. Add FastAPI dependencies and launch `uvicorn backend.api.main:app --reload`.
3. Confirm `GET /api/health`, `POST /api/auth/login`, `GET /api/inventory/items`, and `POST /api/workflows/analyze`.
4. Launch React with `npm run dev` from `frontend/`.
5. Validate each role with one normal, one shortage, one expiry-blocked, and one zero-demand scenario.
6. Deprecate Streamlit once React covers EDA, simulation, RAG context, agent traces, and report output.
7. Replace mock auth with production identity provider and persist audit traces to durable storage.

