<div align="center">
  <img src="https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/activity.svg" alt="Pharma-Flow Logo" width="120" height="120">

  # 💊 Pharma-Flow: AI-Powered Pharmacy Intelligence

  **Next-Generation Inventory Management, Predictive Analytics, and AI RAG Chatbot**

  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
  [![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](https://vitejs.dev/)
  [![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
  [![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

  ---
</div>

## 🚀 Overview

**Pharma-Flow** is an enterprise-grade web application built to revolutionize pharmaceutical inventory management. By combining modern web technologies with Artificial Intelligence (AI) and Machine Learning (ML) workflows, Pharma-Flow empowers pharmacists and executives to make data-driven decisions seamlessly.

Say goodbye to stockouts, expired medications, and manual demand forecasting. Let AI handle the heavy lifting.

---

## ✨ Features

### 1. 🔮 AI-Powered Inventory Simulator
- **Dynamic Forecasting:** Run "what-if" scenarios instantly. Adjust metrics like stock levels, lead times, and expiry days.
- **Automated Workflows:** Trigger a comprehensive backend AI pipeline that performs risk analysis, compliance auditing, and generates actionable supply chain reports.

### 2. 📊 Real-Time Analytics Dashboard
- **Executive Summaries:** Instantly view Total Stock Items, Items at Risk, and Total Demand Forecast.
- **Interactive Visualizations:** Powered by `Recharts`, providing 6-Month Demand Forecasts (Line Charts) and Stock Distribution (Pie Charts).
- **One-Click Export:** Export your entire inventory dataset to CSV for offline analysis and record-keeping.

### 3. 🤖 Floating RAG AI Assistant
- **Context-Aware Responses:** A built-in Retrieval-Augmented Generation (RAG) chatbot that "sees" your current inventory.
- **LLM Powered:** Uses the Groq LLM (LLaMA/Mixtral) to give intelligent answers.
- **Human-like Interaction:** Beautiful UI with typing indicators and natural conversational flow.

---

## 🛠️ Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.10)
- **AI Integration:** Groq LLM API, LangChain/LlamaIndex concepts
- **Architecture:** Modular routes, Pydantic schemas, Dependency Injection

### Frontend
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS + custom glassmorphism and animations
- **Icons & Charts:** Lucide React, Recharts

### Deployment
- **Containerization:** Docker & Docker Compose
- **Proxy/Web Server:** Nginx (Alpine)

---

## 🐳 Quick Start (Docker - Recommended)

The easiest way to get Pharma-Flow up and running is using Docker.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/Pharma-Flow.git
   cd Pharma-Flow
   ```

2. **Configure Environment Variables:**
   - Rename `.env.example` to `.env` (or create one).
   - Add your `GROQ_API_KEY`.

3. **Spin up the containers:**
   ```bash
   docker-compose up --build -d
   ```

4. **Access the Application:**
   - **Frontend:** http://localhost:80
   - **Backend API Docs:** http://localhost:8000/docs

---

## 💻 Local Development Setup

If you prefer to run the application locally without Docker:

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r ../requirements.txt
uvicorn backend.api.main:app --reload
```
*Backend runs on http://localhost:8000*

### Frontend
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on http://localhost:5173 with a local proxy to the backend API.*

---

## 🎨 UI / UX Highlights
- **Clean Design:** A sophisticated "clinical" color palette focusing on clarity and reduced cognitive load.
- **Micro-interactions:** Hover effects, smooth transitions, and typing indicators make the app feel alive.
- **Fully Responsive:** Beautifully crafted layouts that adapt to your screen.

---

<div align="center">
  <i>Built with ❤️ for the DEPI Project. Ready to disrupt the Pharma Supply Chain!</i>
</div>
