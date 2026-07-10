# app/Pharmaflow_dashboard.py
"""
PHARMA-Flow AI — Enterprise Multi-Agent Inventory Intelligence
Refactored Data Science Dashboard & Multi-Agent Integration.

Features:
- Tabs for Exploratory Data Analysis (EDA) of Data Science team's Sprint 1 findings.
- Interactive multi-agent pipeline decision controls.
- Dynamic What-If simulation engine with bilingually structured CoT outputs.
- Live PubMed context RAG retrieval.
- Caching layer for optimal performance.

Run: streamlit run app/Pharmaflow_dashboard.py
"""
import sys
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# ── Path bootstrap ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load environment before loading settings
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / ".env")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Project Module Imports ────────────────────────────────────────────────────
try:
    from app.config.settings import settings
    from backend.bootstrap import build_orchestrator
    from backend.agents.shared.constants import ExecutionStatus, ActionType, InventoryStatus, REORDER_ROUNDING
    from backend.agents.shared.utils import round_up_to_nearest
    from rag.pipeline import RAGPipeline
    RAG_AVAILABLE = True
except Exception as e:
    RAG_AVAILABLE = False
    logging.warning(f"Project imports not fully available: {e}")

# ── Page Configuration ──
st.set_page_config(
    page_title="Pharma-Flow AI: Multi-Agent Inventory Intelligence",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Caching Layer for Performance Optimization ──
@st.cache_resource
def get_rag_pipeline():
    """Cache the RAG pipeline (FAISS index + Sentence-Transformers model) to avoid reloading from disk."""
    if RAG_AVAILABLE:
        try:
            return RAGPipeline()
        except Exception as e:
            logging.error(f"Failed to load RAG Pipeline: {e}")
            return None
    return None

@st.cache_resource
def get_cached_orchestrator(api_key: str):
    """Cache the multi-agent orchestrator object instance."""
    return build_orchestrator(api_key)

@st.cache_data
def load_inventory_data(path: str):
    """Cache the dataset load to avoid reading file on every click."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_eda_dataset(path: str):
    """Cache the load of the main raw dataset for Exploratory Data Analysis."""
    if os.path.exists(path):
        df = pd.read_csv(path)
        # Compute Net Sales
        df['net_sales_value_egp'] = df['actual_demand_units'] * df['unit_price_egp']
        return df
    return None

# ── Loading Datasets ──
inventory_json_path = 'data/sprint1_output.json'
eda_csv_path = 'data/final_dataset.csv'

try:
    inventory_data = load_inventory_data(inventory_json_path)
except Exception as e:
    st.error(f"Fatal: Could not load {inventory_json_path}. Error: {e}")
    st.stop()

df_eda = load_eda_dataset(eda_csv_path)

# ── Styling: Premium Dark Clinical Theme ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Cairo:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Cairo', sans-serif;
    }
    
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
    }
    
    /* Agent & Prescriptive Action boxes */
    .agent-box {
        padding: 22px;
        border-radius: 12px;
        margin-bottom: 14px;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 5px solid #58a6ff;
        transition: transform 0.2s, border-color 0.2s;
    }
    .agent-box:hover {
        transform: translateY(-2px);
        border-color: #58a6ff;
    }
    
    /* Decision Hero Card */
    .decision-card {
        padding: 24px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar styling overrides */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Badge Styles */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-right: 6px;
    }
    .badge-green { background: #1a3a1a; color: #3fb950; border: 1px solid #238636; }
    .badge-yellow { background: #3a2e00; color: #d29922; border: 1px solid #9e6a03; }
    .badge-orange { background: #3a1e00; color: #e3b341; border: 1px solid #bc4c00; }
    .badge-red { background: #3a0a0a; color: #f85149; border: 1px solid #6e2b2b; }
    .badge-blue { background: #0d2b45; color: #58a6ff; border: 1px solid #1f6feb; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR: SYSTEM CONTROL & CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown("""
<div style='text-align: center; padding-bottom: 10px;'>
    <h2 style='color:#58a6ff; font-weight:700; margin:0;'>⚙️ PHARMA-Flow</h2>
    <span style='color:#8b949e; font-size:0.8rem;'>Multi-Agent System Control Panel</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.subheader("🔑 API Configuration")

# Sourcing default API key from settings
default_key = ""
try:
    default_key = settings.groq_api_key
except NameError:
    default_key = os.getenv("GROQ_API_KEY", "")

api_key = st.sidebar.text_input("Enter Groq API Key", value=default_key, type="password")

if not api_key:
    st.sidebar.warning("⚠️ Enter a Groq API Key to start analysis.")
else:
    st.sidebar.success("✅ Connected to Groq Engine")

st.sidebar.divider()
st.sidebar.subheader("📊 Dataset Summary")
st.sidebar.info(f"📁 Loaded {len(inventory_data)} SKUs from Data Science Sprint 1 output.")
if df_eda is not None:
    st.sidebar.success(f"📈 Linked {len(df_eda):,} transaction rows for EDA visualization.")
else:
    st.sidebar.warning("⚠️ final_dataset.csv not found for EDA tab.")

st.sidebar.caption("PHARMA-Flow v2.0 · Sprint 2 Cohesive Dashboard")


# ═══════════════════════════════════════════════════════════════════════════════
#  TOP HEADER & CORE TABS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style='padding-bottom: 12px;'>
    <h1 style='margin:0; font-weight:700; color:#e6edf3;'>💊 PHARMA-Flow AI: Unified Decision Platform</h1>
    <p style='color:#8b949e; margin:4px 0 0;'>Data Science Exploratory Analysis & Advanced AI Multi-Agent Prescriptive Engine</p>
</div>
""", unsafe_allow_html=True)

# Main tab selector: EDA vs Multi-Agent Simulation
tab_insights, tab_decision_engine = st.tabs([
    "📊 Supply Chain Insights (EDA & Analytics)",
    "🤖 Multi-Agent Prescriptive Engine (Simulation)"
])


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 1: EXPLORATORY DATA ANALYSIS (EDA)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_insights:
    st.subheader("📈 Egypt Pharmaceutical Market & Supply Chain Insights (Sprint 1)")
    
    if df_eda is None:
        st.warning("⚠️ `data/final_dataset.csv` is missing or could not be loaded. Please ensure the dataset exists to view historical EDA insights.")
    else:
        # Groupings & Preparations for Plotly
        # 1. Monthly sales
        month_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
                       7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        
        df_monthly = df_eda.groupby('month')['net_sales_value_egp'].sum().reindex(month_order).reset_index()
        df_monthly['month_name'] = df_monthly['month'].map(month_names)
        
        # 2. Category demand
        df_manufacturer = df_eda.groupby('manufacturer')['actual_demand_units'].sum().sort_values(ascending=False).head(10).reset_index()
        
        # 3. Top Governorates
        df_gov = df_eda.groupby('governorate')['net_sales_value_egp'].sum().sort_values(ascending=False).head(10).reset_index()
        
        # 4. Facility sales
        df_facility = df_eda.groupby('facility_type')['net_sales_value_egp'].sum().reset_index()
        
        # ── Layout rows of Plotly Charts ──
        r1_col1, r1_col2 = st.columns(2)
        
        with r1_col1:
            st.markdown("##### 1. Monthly Sales Trends | اتجاهات المبيعات الشهرية")
            fig_monthly = px.line(
                df_monthly, x='month_name', y='net_sales_value_egp',
                labels={'net_sales_value_egp': 'Net Sales (EGP)', 'month_name': 'Month'},
                markers=True,
                template="plotly_dark"
            )
            fig_monthly.update_traces(line_color='#58a6ff', line_width=3)
            st.plotly_chart(fig_monthly, use_container_width=True)
            
        with r1_col2:
            st.markdown("##### 2. Top Manufacturers by Actual Demand | كبار المصنعين")
            fig_man = px.bar(
                df_manufacturer, x='actual_demand_units', y='manufacturer',
                orientation='h',
                labels={'actual_demand_units': 'Actual Demand (Units)', 'manufacturer': 'Manufacturer'},
                template="plotly_dark",
                color_discrete_sequence=['#14b8a6']
            )
            fig_man.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_man, use_container_width=True)
            
        r2_col1, r2_col2 = st.columns(2)
        
        with r2_col1:
            st.markdown("##### 3. Top 10 Governorates by Net Sales (EGP) | المبيعات حسب المحافظات")
            fig_gov = px.bar(
                df_gov, x='net_sales_value_egp', y='governorate',
                orientation='h',
                labels={'net_sales_value_egp': 'Net Sales (EGP)', 'governorate': 'Governorate'},
                template="plotly_dark",
                color_discrete_sequence=['#eab308']
            )
            fig_gov.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_gov, use_container_width=True)
            
        with r2_col2:
            st.markdown("##### 4. Net Sales Distribution by Facility Type | توزيع المبيعات")
            fig_fac = px.pie(
                df_facility, values='net_sales_value_egp', names='facility_type',
                hole=0.4,
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_fac, use_container_width=True)

        r3_col1, r3_col2 = st.columns(2)
        
        with r3_col1:
            st.markdown("##### 5. External Factors: Flu Index vs. Demand | تأثير مؤشر الإنفلونزا")
            fig_scatter = px.scatter(
                df_eda, x='flu_index', y='actual_demand_units',
                trendline="ols",
                labels={'flu_index': 'Flu Index', 'actual_demand_units': 'Actual Demand (Units)'},
                template="plotly_dark",
                opacity=0.4,
                color_discrete_sequence=['#f85149']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with r3_col2:
            st.markdown("##### 6. Seasonality Analysis: Demand Distribution | التحليل الموسمي للطلب")
            fig_box = px.box(
                df_eda, x='season', y='actual_demand_units',
                points=False,
                labels={'season': 'Season', 'actual_demand_units': 'Actual Demand (Units)'},
                template="plotly_dark",
                color_discrete_sequence=['#bc8cff']
            )
            st.plotly_chart(fig_box, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TAB 2: MULTI-AGENT SIMULATION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_decision_engine:
    st.subheader("🎯 Drug Selectors & What-If Simulation")
    
    # Selection from inventory options
    sku_options = [f"{item['sku_id']} - {item['generic_name']}" for item in inventory_data]
    selected_sku_str = st.selectbox("Select Medication to Analyze", sku_options, key="tab2_sku_sel")
    
    selected_sku_id = selected_sku_str.split(" - ")[0]
    base_case = next(item for item in inventory_data if item['sku_id'] == selected_sku_id)
    
    # ── Simulation Controller Parameters ──
    st.markdown("##### ⚙️ Adjust Parameters for What-If Simulation")
    sim_c1, sim_c2, sim_c3, sim_c4 = st.columns(4)
    
    with sim_c1:
        sim_stock = st.slider("Current Stock (units)", 0, 3000, int(base_case.get('stock', 100)), key="sim_stock_slider")
    with sim_c2:
        sim_forecast = st.slider("Forecast Demand (units)", 10, 5000, int(base_case.get('forecast_demand', 200)), key="sim_forecast_slider")
    with sim_c3:
        sim_lead = st.slider("Supplier Lead Time (days)", 1, 60, 10, key="sim_lead_slider")
    with sim_c4:
        base_expiry = base_case.get('expiry_days', 90)
        sim_expiry = st.slider("Remaining Shelf Life (days)", 0, 730, abs(int(base_expiry)), key="sim_expiry_slider")
        
    sim_col_conf1, sim_col_conf2 = st.columns(2)
    with sim_col_conf1:
        sim_conf_low = st.number_input("Forecast Bound (Low - units)", value=int(sim_forecast * 0.8), min_value=0, key="sim_conf_low_val")
    with sim_col_conf2:
        sim_conf_high = st.number_input("Forecast Bound (High - units)", value=int(sim_forecast * 1.2), min_value=0, key="sim_conf_high_val")
        
    # Build payload mapping for backend agents
    case_payload = {
        "sku": base_case['sku_id'],
        "sku_name": base_case['generic_name'],
        "location_type": "hospital" if "hospital" in base_case.get('generic_name', '').lower() or sim_lead > 10 else "warehouse",
        "available_stock": sim_stock,
        "forecast_demand": sim_forecast,
        "lead_time": sim_lead,
        "expiry_days": sim_expiry,
        "confidence_low": sim_conf_low,
        "confidence_high": sim_conf_high,
        "stock": sim_stock,
        "on_order": 0
    }
    
    # ── RAG System Section ──
    st.markdown("---")
    st.subheader("📚 PubMed Clinical Context (RAG)")
    
    rag_context = "No RAG context loaded."
    if RAG_AVAILABLE:
        try:
            pipeline = get_rag_pipeline()
            rag_query = f"{case_payload['sku_name']} shortages supply chain alternatives"
            if pipeline:
                rag_chunks = pipeline.retrieve_context(rag_query, k=2)
                if rag_chunks:
                    rag_context = "\n\n".join(rag_chunks)
                    with st.expander("🔍 View Retrieved Clinical Literature Abstract", expanded=False):
                        for idx, chunk in enumerate(rag_chunks):
                            st.markdown(f"**Abstract segment {idx+1}:**")
                            st.info(chunk)
                else:
                    st.caption("No relevant literature found in vector store. Using safety fallback context.")
                    rag_context = "PubMed Shortage Bulletin: Alternative therapeutics recommended if stockout is imminent."
            else:
                st.caption("RAG system index missing. Default metrics context applied.")
                rag_context = f"Shortage guidelines: Alternative procurement paths recommended for generic {case_payload['sku_name']}."
        except Exception as e:
            st.caption(f"RAG retrieval bypassed. Using default metrics context.")
            rag_context = f"Shortage protocols: Substitute sources available for generic {case_payload['sku_name']}."
    else:
        st.caption("RAG module currently disabled. Standard supply metrics fallback applied.")
        rag_context = f"Shortage protocols: Substitute sources available for {case_payload['sku_name']}."

    # ── Trigger Multi-Agent Pipeline Run ──
    st.markdown("---")
    
    if not api_key:
        st.warning("⚠️ Please configure your Groq API Key in the sidebar control panel first.")
    else:
        if st.button("🚀 Run Multi-Agent Decision Pipeline", use_container_width=True, key="run_sim_btn"):
            col_details, col_pipeline = st.columns([1, 2])
            
            with col_details:
                st.subheader("📋 Simulation Payload")
                st.json(case_payload)
                
            with col_pipeline:
                st.subheader("🤖 Agentic Processing Chain")
                
                with st.status("Agent Pipeline Running...", expanded=True) as status:
                    orchestrator = get_cached_orchestrator(api_key)
                    
                    st.write("⚙️ [1/4] Running OpsAgent: Computing stock coverage & reorder points...")
                    time.sleep(0.1)
                    st.write("📊 [2/4] Running RiskAgent: Assessing clinical risk posture & uncertainty...")
                    time.sleep(0.1)
                    st.write("🔏 [3/4] Running AuditorAgent: Conducting compliance audit & GxP validation...")
                    time.sleep(0.1)
                    st.write("📄 [4/4] Running ReportAgent: Synthesizing final decisions and generating action hubs...")
                    
                    workflow_state = orchestrator.run(case_payload)
                    
                    if workflow_state.execution_status == ExecutionStatus.FAILED:
                        status.update(label=f"Pipeline Failed: {workflow_state.error_message}", state="error")
                        st.stop()
                    else:
                        status.update(label="AI Multi-Agent Pipeline Completed!", state="complete")
                
                # Extract results
                ops = workflow_state.operational_result
                risk = workflow_state.risk_result
                audit = workflow_state.audit_result
                report = workflow_state.report_result
                
                # ── Decision Hero Card Display ──
                st.divider()

                # ── Derive badge values from ground-truth computed fields ──
                _approved    = audit.approved if audit else False
                _action      = ops.action if ops else "MONITOR"
                _qty         = ops.recommended_qty if ops else 0
                _gap         = ops.inventory_gap if ops else 0
                _rop         = ops.reorder_point if ops else 0
                _stock       = case_payload.get("available_stock", 0)
                _forecast    = case_payload.get("forecast_demand", 0)
                _risk_level  = risk.risk_level if risk else "LOW"
                _risk_score  = risk.risk_score if risk else 0
                _demand_paused = _forecast <= 0 and _stock > 0
                _target_stock = max(_rop, _forecast)
                if _stock == 0 and ops:
                    _target_stock += max(0, ops.safety_stock)
                _canonical_gap = max(0, _target_stock - _stock)
                if _demand_paused:
                    _canonical_gap = 0
                _math_mismatch = bool(ops and (
                    _gap != _canonical_gap
                    or (_canonical_gap > 0 and (_action != "REORDER" or _qty <= 0))
                    or (_demand_paused and (_action != "HOLD_MONITOR" or _qty != 0))
                    or (_canonical_gap == 0 and not _demand_paused and (_action != "MONITOR" or _qty != 0))
                ))
                if _math_mismatch:
                    st.error(
                        "Ground-truth correction applied: downstream display was realigned "
                        "to reorder point, forecast demand, and current stock."
                    )
                _gap = _canonical_gap
                if _gap > 0:
                    _action = "REORDER"
                    _qty = max(_qty, round_up_to_nearest(_gap, REORDER_ROUNDING))
                elif _demand_paused:
                    _action = "HOLD_MONITOR"
                    _qty = 0
                else:
                    _action = "MONITOR"
                    _qty = 0
                _final_action = report.recommended_action if report else _action

                # Determine the canonical status purely from audit + action,
                # never from LLM text alone.
                if not _approved:
                    if _final_action == "URGENT_DISPOSAL_AND_REPLACEMENT":
                        decision_label = "⛔ FAILED AUDIT — URGENT DISPOSAL & REPLACEMENT"
                    else:
                        decision_label = "⛔ EXECUTION BLOCKED — COMPLIANCE BREACH"
                    bg_color, border_color = "#3a0a0a", "#f85149"
                    status_icon = "🔴"
                elif _gap > 0 and _qty > 0:
                    decision_label = "🚨 CRITICAL SHORTAGE — AUTONOMOUS REORDER AUTHORIZED"
                    bg_color, border_color = "#0d2038", "#388bfd"
                    status_icon = "🔵"
                elif _gap > 0 and _qty == 0:
                    # Edge case: reorder triggered but qty calculation anomaly
                    decision_label = "⚠️ SHORTAGE DETECTED — MANUAL QUANTITY REVIEW REQUIRED"
                    bg_color, border_color = "#3a1e00", "#d4a017"
                    status_icon = "🟡"
                elif _action == "HOLD_MONITOR":
                    decision_label = "⏸️ ZERO DEMAND — INVENTORY TRACKING PAUSED"
                    bg_color, border_color = "#2d2600", "#d29922"
                    status_icon = "🟡"
                else:
                    decision_label = "✅ SUPPLY ADEQUATE — MONITOR STATUS"
                    bg_color, border_color = "#0d2b18", "#238636"
                    status_icon = "🟢"

                # ── Risk badge colour ──
                risk_badge_color = {"LOW": "#238636", "MEDIUM": "#d4a017",
                                    "HIGH": "#f85149", "CRITICAL": "#ff0000"}.get(_risk_level, "#6e7681")

                st.markdown(f"""
                <div class="decision-card" style="background-color: {bg_color}; border: 2px solid {border_color}; border-radius:12px; padding:20px; margin-bottom:16px;">
                    <h2 style="margin: 0 0 12px 0; font-weight:700; color: #ffffff;">{decision_label}</h2>
                    <div style="display:flex; gap:16px; flex-wrap:wrap; margin-bottom:14px;">
                        <div style="background:#161b22; border-radius:8px; padding:10px 18px; min-width:140px; text-align:center;">
                            <div style="font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Current Stock</div>
                            <div style="font-size:1.6rem; font-weight:700; color:#e6edf3;">{_stock:,}</div>
                            <div style="font-size:0.75rem; color:#8b949e;">units</div>
                        </div>
                        <div style="background:#161b22; border-radius:8px; padding:10px 18px; min-width:140px; text-align:center;">
                            <div style="font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Reorder Point</div>
                            <div style="font-size:1.6rem; font-weight:700; color:#f0a500;">{_rop:,}</div>
                            <div style="font-size:0.75rem; color:#8b949e;">units</div>
                        </div>
                        <div style="background:#161b22; border-radius:8px; padding:10px 18px; min-width:140px; text-align:center;">
                            <div style="font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Inventory Gap</div>
                            <div style="font-size:1.6rem; font-weight:700; color:{'#f85149' if _gap > 0 else '#3fb950'};">{_gap:,}</div>
                            <div style="font-size:0.75rem; color:#8b949e;">units short</div>
                        </div>
                        <div style="background:#161b22; border-radius:8px; padding:10px 18px; min-width:140px; text-align:center;">
                            <div style="font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Recommended Order</div>
                            <div style="font-size:1.6rem; font-weight:700; color:{'#388bfd' if _qty > 0 else '#3fb950'};">{_qty:,}</div>
                            <div style="font-size:0.75rem; color:#8b949e;">units</div>
                        </div>
                        <div style="background:#161b22; border-radius:8px; padding:10px 18px; min-width:140px; text-align:center;">
                            <div style="font-size:0.75rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px;">Risk Score</div>
                            <div style="font-size:1.6rem; font-weight:700; color:{risk_badge_color};">{_risk_score}</div>
                            <div style="font-size:0.75rem; color:{risk_badge_color};">{_risk_level}</div>
                        </div>
                    </div>
                    <p style="font-size:1rem; line-height:1.6; color:#e6edf3; margin:0; border-top:1px solid #30363d; padding-top:12px;">
                        <b>Executive Directive:</b> {report.reasoning if report else "No summary report generated."}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                
                # ── The Chain-of-Thought panel ──
                st.subheader("🧠 Deep-Dive: Chain-of-Thought (CoT) Reasoning")
                
                tab_ops, tab_risk, tab_audit, tab_report = st.tabs([
                    "⚙️ Operations Layer",
                    "📊 Clinical Risk Layer",
                    "🔏 Compliance Layer",
                    "📄 Synthesis Layer"
                ])
                
                with tab_ops:
                    st.markdown("### ⚙️ OpsAgent — Deterministic Computations")
                    if ops:
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Action", _action)
                        m2.metric("Inventory Gap", f"{_gap:,} units", delta=f"-{_gap}" if _gap > 0 else "0", delta_color="inverse")
                        m3.metric("Reorder Point (ROP)", f"{_rop:,} units")
                        m4.metric("Safety Stock", f"{ops.safety_stock:,} units")
                        r1, r2 = st.columns(2)
                        r1.metric("Recommended Order Qty", f"{_qty:,} units")
                        r2.metric("Inventory Status", ops.inventory_status)
                        st.markdown("---")
                        st.markdown("**📝 OpsAgent Reasoning Narrative:**")
                        st.info(ops.reasoning or "No reasoning output generated.")
                        if ops.recommendation_details:
                            st.markdown("**📋 Recommendation Details:**")
                            st.caption(ops.recommendation_details)
                    else:
                        st.warning("OpsAgent result unavailable.")
                    
                with tab_risk:
                    st.markdown("### 📊 RiskAgent — Multi-Factor Risk Assessment")
                    if risk:
                        r1, r2, r3 = st.columns(3)
                        r1.metric("Risk Score", f"{risk.risk_score}/100")
                        r2.metric("Risk Level", risk.risk_level)
                        r3.metric("Human Review?", "YES ⚠️" if risk.human_review_recommended else "No ✅")
                        f1, f2, f3 = st.columns(3)
                        f1.metric("Criticality", risk.criticality)
                        f2.metric("Shortage Risk", "Yes 🚨" if risk.shortage_risk else "No ✅")
                        f3.metric("Expiry Risk", "Yes ⚠️" if risk.expiry_risk else "No ✅")
                        st.markdown("---")
                        st.markdown("**🔬 Clinical & Logistics Risk Posture:**")
                        st.warning(risk.reasoning or "No reasoning output generated.")
                    else:
                        st.warning("RiskAgent result unavailable.")
                    
                with tab_audit:
                    st.markdown("### 🔏 AuditorAgent — Compliance & GxP Validation")
                    if audit:
                        a1, a2, a3, a4 = st.columns(4)
                        a1.metric("Audit Status", audit.audit_status)
                        a2.metric("Decision", "✅ APPROVED" if audit.approved else "❌ REJECTED")
                        a3.metric("Warnings", audit.warning_count)
                        a4.metric("Blockers", audit.blocking_errors)
                        if audit.rule_results:
                            st.markdown("**📋 Rule Engine Results:**")
                            rule_rows = [{"Rule": r.rule_name, "Severity": r.severity, "Message": r.message} for r in audit.rule_results]
                            st.dataframe(rule_rows, use_container_width=True)
                        else:
                            st.success("✅ All audit rules passed — no violations detected.")
                        st.markdown("---")
                        st.markdown("**📋 Compliance Audit Trail:**")
                        st.error(audit.reasoning or "No compliance reasoning generated.")
                    else:
                        st.warning("AuditorAgent result unavailable.")
                    
                with tab_report:
                    st.markdown("### 📄 ReportAgent — Executive Synthesis")
                    if report:
                        st.success(report.executive_summary or "No executive summary generated.")
                        if report.report_sections:
                            st.markdown("**📊 Report Sections:**")
                            for sec_name, sec_text in report.report_sections.items():
                                if sec_text and sec_name != "next_actions":
                                    with st.expander(f"📑 {sec_name.replace('_', ' ').title()}"):
                                        st.write(sec_text)
                    else:
                        st.warning("ReportAgent result unavailable.")

                    
                # ── Next actions planning hub ──
                st.subheader("🛠️ Next Prescriptive Actions & Operations Plan")
                
                if report and report.report_sections:
                    next_actions = report.report_sections.get("next_actions", "").strip()
                    if next_actions:
                        st.table(pd.DataFrame([{
                            "Action Step / Division": "Next Actions",
                            "Prescription Instructions": next_actions
                        }]))
                    else:
                        st.info("No detailed prescriptive steps were populated by the Report Agent.")
                else:
                    if not _approved:
                        if _final_action == "URGENT_DISPOSAL_AND_REPLACEMENT":
                            primary_instruction = "Quarantine expiring stock and initiate urgent disposal-and-replacement workflow."
                        else:
                            primary_instruction = "Autonomous execution is blocked; route this case to manual compliance review."
                    elif _gap > 0:
                        primary_instruction = f"Trigger purchase order PO-{case_payload['sku'][:3].upper()}-{_qty} for {_qty:,} units immediately."
                    else:
                        primary_instruction = "Continue monitoring; no purchase order is authorized while the inventory gap is zero."
                    fallback_steps = [
                        {"Action Step / Division": "Procurement / ERP Integration", "Prescription Instructions": primary_instruction},
                        {"Action Step / Division": "Pharmacy Administration", "Prescription Instructions": "Verify remaining shelf life manually and configure localized safety buffers."},
                        {"Action Step / Division": "Compliance & Safety", "Prescription Instructions": "Inspect data bounds for extreme variance to confirm forecasting fidelity."}
                    ]
                    st.table(pd.DataFrame(fallback_steps))
