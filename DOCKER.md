# Running with Docker

## Prerequisites

- Docker and Docker Compose
- `backend/.env` with at least `OPENAI_API_KEY` (and optional `MODEL_NAME`, Azure vars, etc.)

## Build and run

From the project root:

```bash
docker compose up --build
```

- **Frontend:** http://localhost:3000 (nginx serves the React app and proxies `/api` to the backend)
- **Backend:** http://localhost:8000 (API and docs at `/docs`)

The SQLite DB is stored in a Docker volume `backend_data` and is initialized with sample sales data on first run.

## Optional

- Run in background: `docker compose up -d --build`
- Stop: `docker compose down`
- Reset DB (delete volume): `docker compose down -v`
