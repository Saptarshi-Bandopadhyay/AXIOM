# ReproCheck — Free Deployment and CI/CD Guide

This document describes how to deploy ReproCheck for free and configure automated CI/CD with optional LLM evaluation testing.

---

## 1. Zero-Cost Cloud Architecture

ReproCheck operates completely within free cloud tiers:

| Component | Free Cloud Provider | Free Tier Limits | Purpose |
| :--- | :--- | :--- | :--- |
| **App Server & SPA** | **Render** or **Koyeb** | 750 free instance hours / month | Hosts FastAPI backend and compiled React SPA. |
| **Database** | **Neon Serverless PostgreSQL** | 0.5 GB storage, always active | Stores review sessions, papers, and findings. |
| **Cache & Limiter** | **Upstash Redis** | 10,000 commands / day | Caches prompts and deduplicates model requests. |
| **Primary LLM** | **Google Gemini API** | 15 requests / min, 1,500 / day | Runs paradigm classification and review nodes. |
| **Fallback LLM** | **Groq Cloud** | 30 requests / min | Fallback gateway if primary hits rate limits. |
| **CI/CD Automation** | **GitHub Actions** | 2,000 minutes / month | Builds code, runs offline tests, and deploys. |

```mermaid
flowchart TD
    User["Web Browser"] -->|HTTPS| Render["Render / Koyeb Web Service<br>(FastAPI + React SPA)"]
    Render -->|SQL (asyncpg)| Neon["Neon PostgreSQL<br>(Free 0.5 GB)"]
    Render -->|TLS| Upstash["Upstash Redis<br>(Free 10k/day)"]
    Render -->|API Calls| Gemini["Google Gemini API<br>(Free Tier)"]
    Render -->|Fallback API| Groq["Groq Cloud API<br>(Free Tier)"]

    GitHub["GitHub Repository"] -->|Push / PR| GHA["GitHub Actions CI"]
    GHA -->|1. Offline Tests| FastTest["Pytest Unit & Integration<br>(Mock LLM, 0 tokens)"]
    GHA -.->|2. Optional Trigger| LLMTest["DeepEval Evaluation Suite<br>(Manual or [run-evals])"]
    GHA -->|3. On main Push| Webhook["Deploy Hook<br>(Trigger Redeployment)"]
    Webhook --> Render
```

---

## 2. Cloud Backing Services Setup (Free)

### 2.1 Neon Serverless PostgreSQL
1. Sign up at [neon.tech](https://neon.tech) (no credit card required).
2. Create a new project named `reprocheck-db`.
3. Copy the connection string. Neon provides connection details in this format:
   `postgresql://[user]:[password]@[endpoint].neon.tech/neondb?sslmode=require`
4. Formulate the two connection URLs required by ReproCheck:
   - `DATABASE_URL`: `postgresql+asyncpg://[user]:[password]@[endpoint].neon.tech/neondb?ssl=require`
   - `DATABASE_URL_SYNC`: `postgresql://[user]:[password]@[endpoint].neon.tech/neondb?sslmode=require`

### 2.2 Upstash Redis
1. Sign up at [upstash.com](https://upstash.com) (no credit card required).
2. Click **Create Database**, select primary region, and choose **Serverless**.
3. Copy the **Redis URL** (`rediss://default:[token]@[endpoint].upstash.io:6379`).

---

## 3. Web Service Deployment (Render)

1. Sign up at [render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Select **Docker** as the runtime environment.
5. Set instance type to **Free**.
6. Under **Environment Variables**, configure the following keys:

| Environment Variable | Value Example | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@ep.neon.tech/neondb?ssl=require` | Async database URL. |
| `DATABASE_URL_SYNC` | `postgresql://user:pass@ep.neon.tech/neondb?sslmode=require` | Sync database URL for migrations. |
| `REDIS_URL` | `rediss://default:token@endpoint.upstash.io:6379` | Upstash Redis connection string. |
| `PRIMARY_MODEL` | `gemini/gemini-3.1-flash-lite` | Primary LLM model identifier. |
| `FALLBACK_MODEL` | `groq/openai/gpt-oss-120b` | Fallback LLM model identifier. |
| `FAST_CHEAP_MODEL` | `groq/openai/gpt-oss-20b` | Lightweight model for classification. |
| `GEMINI_API_KEY` | `AIzaSy...` | Your Google AI Studio API key. |
| `GROQ_API_KEY` | `gsk_...` | Your Groq Cloud API key. |
| `APP_ENV` | `production` | Production runtime profile. |
| `API_PREFIX` | `/api/v1` | Base prefix for REST API endpoints. |

7. Click **Deploy Web Service**.
8. Go to **Settings** -> **Deploy Hook** and copy the hook URL (`https://api.render.com/deploy/srv-xxxx?key=yyyy`).

---

## 4. CI/CD Integration with GitHub Actions

The repository includes [.github/workflows/ci-cd.yml](file:///.github/workflows/ci-cd.yml).
It automates testing, validation, and zero-downtime deployment.

### 4.1 GitHub Repository Secrets
Navigate to your GitHub repository -> **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:

| Secret Name | Required For | Value |
| :--- | :--- | :--- |
| `RENDER_DEPLOY_HOOK_URL` | Continuous Deployment | Render deploy hook URL from step 3.8. |
| `GEMINI_API_KEY` | Optional LLM Testing | Google AI Studio API key. |
| `GROQ_API_KEY` | Optional LLM Testing | Groq Cloud API key. |

### 4.2 Pipeline Execution Flow

1. **Standard Workflow (Push & Pull Request)**:
   - Builds React SPA frontend with `npm ci && npm run build`.
   - Starts local PostgreSQL and Redis service containers in the GitHub runner.
   - Executes unit tests (`pytest backend/tests/unit/`).
   - Executes integration tests (`pytest backend/tests/integration/`).
   - Uses mocked LLM responses. Consumes **0 API tokens** and runs in under 2 minutes.

2. **Optional LLM Evaluation Testing**:
   - Live LLM testing consumes API rate limits and quotas.
   - You can trigger the evaluation suite in two ways:
     - **Option A (GitHub UI)**: Go to **Actions** tab -> **CI/CD Pipeline** -> **Run workflow** -> Check the box **Run LLM evaluation suite**.
     - **Option B (Commit Keyword)**: Include `[run-evals]` in your git commit message.
   - The workflow runs DeepEval tests (`pytest backend/tests/evaluation/`) against live Gemini and Groq APIs.

3. **Continuous Deployment Job**:
   - When all checks pass on the `main` branch, the pipeline calls `RENDER_DEPLOY_HOOK_URL`.
   - Render automatically pulls the latest commit, builds the Docker image, runs database migrations, and updates the application.

---

## 5. Health Monitoring and Verification

Once deployed, verify your service:
- **API Health Check**: `https://your-service.onrender.com/health` returns `{"status": "ok", "service": "reprocheck-backend"}`.
- **Web Interface**: Open `https://your-service.onrender.com/` in your browser.
- **Database Status**: The container startup script automatically applies Alembic migrations on boot.
