<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/activity.svg" alt="Pharma-Flow Logo" width="120" height="120">

  # 💊 Pharma-Flow: AI-Powered Pharmacy Intelligence & Multi-Agent Ecosystem

  **DEPI Project Showcase: Advanced Data Science, LangChain Multi-Agents, RAG, and Modern Web Dashboard**

  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
  [![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
  [![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge)](https://langchain.com/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
  [![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

  ---
</div>

## 🚀 Overview

**Pharma-Flow** is a comprehensive, enterprise-grade AI solution designed to revolutionize pharmaceutical supply chain and inventory management. Developed as part of the **DEPI Project**, this application bridges the gap between raw data science and actionable operational intelligence.

Instead of just predicting numbers, Pharma-Flow utilizes a **Multi-Agent AI Architecture** that reasons about stock levels, evaluates risks, audits compliance, and talks to users via an intelligent RAG-powered chatbot—all wrapped in a sleek, real-time React dashboard.

---

## 🧠 Core Ecosystem & Data Science

### 1. Data Science & Machine Learning (`/notebooks`)
- **Extensive EDA & Data Cleaning:** Deep exploratory data analysis on raw pharmaceutical datasets (`PHARMA_Flow_Sprint_1_.ipynb`) to identify trends, seasonality, and missing anomalies.
- **Demand Forecasting:** Implementation of ML models to predict future drug demand (`forecast_demand`), optimizing safety stock and reorder points based on historical consumption patterns.

### 2. Multi-Agent AI System (`/backend/agents`)
Our intelligence layer is orchestrated by a team of specialized AI Agents powered by Groq LLMs:
- 👑 **Orchestrator Agent:** The brain that coordinates tasks, passing state between specialized agents.
- 📦 **Ops Agent (Operations):** Analyzes logistics, current stock, lead times, and recommends immediate supply chain actions.
- ⚠️ **Risk Agent:** Identifies vulnerabilities (e.g., stockouts, imminent expiry, overstocking) and assigns risk scores.
- 🛡️ **Auditor Agent:** Ensures regulatory compliance, checks financial constraints, and validates ops decisions against medical guidelines.
- 📝 **Report Agent:** Synthesizes the multi-agent debate into a concise, actionable JSON report for the frontend.

### 3. RAG-Powered AI Chatbot (`/rag`)
- **Context-Aware Assistant:** Not just a generic chatbot. It retrieves live Medical knowledge and your **Current Inventory Context** using Vector Search (FAISS) and LLMs.
- **Interactive:** Ask it *"Which medications are at risk of expiring?"* or *"What is the medical implication of a Paracetamol shortage?"* and get instant, grounded answers.

---

## 💻 Interactive Dashboard (MVP Presentation Layer)

The data science and AI models are exposed through a beautifully crafted, responsive dashboard built with **React, Vite, and TailwindCSS**.

- **Inventory Simulator:** A "what-if" testing ground. Adjust `available_stock`, `lead_time`, or `expiry_days` and hit **Run AI Analysis** to trigger the Multi-Agent workflow in real-time.
- **Analytics Dashboard:** Powered by `Recharts`, providing live metrics (Total Stock, Items at Risk, Demand Forecasts) and data visualizations.
- **Floating AI Assistant:** A seamless, typing-effect chat widget integrated directly into the UI.
- **One-Click Export:** Export your inventory insights to CSV for offline reporting.

---

## 🛠️ Technology Stack

- **Data Science:** Python, Pandas, NumPy, Scikit-Learn, Jupyter
- **AI & Agents:** LangChain, Groq API (LLaMA/Mixtral), FAISS (Vector DB)
- **Backend:** FastAPI, Uvicorn, Pydantic
- **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons, Recharts
- **Infrastructure:** Docker, Docker Compose, Nginx

---

## 🐳 Quick Start (Docker - Recommended)

Experience the entire ecosystem (Frontend, FastAPI, and Multi-Agents) with a single command.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ParmaFlow/Parma_Flow_DEPI_Project.git
   cd Parma_Flow_DEPI_Project
   ```

2. **Configure Environment Variables:**
   - Add your `GROQ_API_KEY` to the `.env` file to empower the LLM agents.

3. **Spin up the containers:**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Application:**
   - **Frontend Dashboard:** http://localhost:80
   - **Backend API Docs:** http://localhost:8000/docs

---

## 🏗️ Local Development Setup

### Backend & AI Services
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r ../requirements.txt
uvicorn backend.api.main:app --reload
```

### Frontend UI
```bash
cd frontend
npm install
npm run dev
```

---

<div align="center">
  <i>Built with ❤️ for the DEPI Project. Bringing Data Science and AI to the Pharmacy Supply Chain!</i>
</div>
