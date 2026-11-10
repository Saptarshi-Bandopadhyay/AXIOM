# ReproCheck — Backend Developer Guide

This directory contains the Python FastAPI backend and LangGraph workflow engine for ReproCheck.

---

## 1. Directory Structure

- `app/api/`: FastAPI route handlers and dependency injection (`deps.py`).
- `app/core/`: Database engine, prompt cache, security guardrails, and LiteLLM gateway.
- `app/interfaces/`: Storage and PDF extraction abstract interfaces.
- `app/models/`: SQLAlchemy 2.0 async database models.
- `app/schemas/`: Pydantic request and response schemas.
- `app/services/`: Application coordination services (`workflow_service.py`).
- `app/workflows/`: LangGraph review workflow state machine, nodes, and prompts.
- `alembic/`: Async database schema migrations.
- `tests/`: Unit, integration, and DeepEval evaluation suites.

---

## 2. Setup & Installation

### Dependency Installation
Install dependencies using `uv`:
```bash
uv sync
```

### PostgreSQL & Redis Setup

#### Option A: Native Local Services (Without Docker)
```bash
# Ubuntu/Debian:
sudo apt install postgresql redis-server
sudo systemctl start postgresql redis-server

# Configure database and user credentials:
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
sudo -u postgres psql -c "CREATE DATABASE reprocheck OWNER postgres;"

# macOS:
brew install postgresql@16 redis
brew services start postgresql@16 redis
```

#### Option B: Docker Compose
From the project root:
```bash
docker compose up -d
```

*(Note: Redis is optional in development; ReproCheck falls back to an in-memory cache if Redis is unavailable.)*

### Database Migrations
Apply migrations to local PostgreSQL:
```bash
uv run alembic upgrade head
```

Create a new migration after model changes:
```bash
uv run alembic revision --autogenerate -m "describe_change"
```

---

## 3. Running the Server

Start development server on port 8000:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger API documentation: `http://localhost:8000/docs`

---

## 4. Running Tests

Run all unit and evaluation tests:
```bash
uv run pytest tests/unit/ tests/evaluation/ -v
```

Run database integration tests (requires PostgreSQL running):
```bash
uv run pytest tests/integration/ -v
```

Run end-to-end lifecycle verification test:
```bash
uv run pytest tests/integration/test_e2e_verification.py -v
```

---

## 5. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Application environment (`development`, `testing`, `production`) | `development` |
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis cache connection string | `redis://127.0.0.1:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | None |
| `GROQ_API_KEY` | Groq API key | None |
| `PRIMARY_MODEL` | Primary LLM gateway model | `gemini/gemini-3.1-flash-lite` |
| `FALLBACK_MODEL` | Primary fallback model | `groq/openai/gpt-oss-120b` |
