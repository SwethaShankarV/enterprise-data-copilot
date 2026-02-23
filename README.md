# Enterprise Data Copilot

Multi-agent conversational app for querying enterprise sales data in natural language. Backend: FastAPI, orchestrator + analyst agents, SQL over SQLite (or pluggable adapter). Frontend: React (Vite) + Tailwind, chat UI with optional charts.

## Prerequisites

- **Python 3.12+** (backend)
- **Node 18+** (frontend)
- **OpenAI API key** (or Azure OpenAI; see `backend/.env`)
- Optional: **Docker & Docker Compose** for one-command run

## Quick start

### Option A: Run locally (development)

1. **Backend** (from project root):
   ```bash
   cd backend
   cp .env.example .env   # or create .env with OPENAI_API_KEY=...
   pip install -r requirements.txt
   python -m app.tools.init_db   # seed SQLite (once)
   uvicorn app.main:app --reload
   ```
   API: http://localhost:8000 — docs at http://localhost:8000/docs

2. **Frontend** (new terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   App: http://localhost:5173 (proxies `/api` to backend)

### Option B: Run with Docker

From project root, with `backend/.env` containing at least `OPENAI_API_KEY`:

```bash
docker compose up --build
```

- **App:** http://localhost:3000  
- **API:** http://localhost:8000  

See [DOCKER.md](DOCKER.md) for details (stop, reset DB, etc.).

---

## How to run the demo

1. Start the app (local or Docker as above).
2. Open the app in a browser (http://localhost:5173 for local dev, http://localhost:3000 for Docker).
3. Try natural-language questions, e.g.:
   - “What is total revenue in the West region?”
   - “Break that down”
   - “What about the East?”
   - “Total revenue by region”
   - “Give me revenue for Tablets”
4. Replies are grounded in the `sales` table; breakdowns show a chart when the response has two columns (e.g. product/region + value).

---

## Project layout

- **backend/** — FastAPI app, `app/` (agents, tools, config)
- **frontend/** — Vite + React, chat UI and chart component
- **docker-compose.yml** — backend + frontend (nginx) services
- **DOCKER.md** — Docker run/stop/reset

---

## Enterprise Cloud Compatibility

This project is architected with cloud-agnostic abstraction layers to support enterprise deployments on:

- **Azure OpenAI**
- **Microsoft Fabric SQL Warehouses**
- **Power BI Semantic Models** (via XMLA / DAX)

For development and evaluation, the system runs locally using SQLite or Postgres.

The following components are provider-abstracted and environment-configurable:

- **LLMClient** → supports OpenAI or Azure OpenAI via environment variables
- **SQLAdapter** → supports SQLite (dev) and is compatible with Fabric/Azure SQL endpoints
- **DAXAdapter** → structured for Power BI XMLA/DAX execution
- **Retriever** → supports metric definition grounding (RAG)

Switching to Azure OpenAI, Fabric SQL endpoints, or Power BI XMLA requires only credential configuration and environment updates — the orchestration and agent architecture remain unchanged.
