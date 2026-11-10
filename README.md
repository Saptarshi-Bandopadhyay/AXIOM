# ReproCheck — AI Research Methodology Reviewer

ReproCheck is an AI-powered methodology reviewer for computer science research papers. It evaluates empirical machine learning and computer science papers against reproducibility criteria, detects missing experimental parameters, identifies cross-section contradictions, extracts verbatim quotations as evidence, and supports evidence-grounded interactive Q&A.

---

## 1. The Problem & Vision

Empirical computer science and machine learning research frequently suffers from reproducibility gaps. Papers often omit vital experimental details such as:
- Random seeds and weight initialization procedures.
- Compute infrastructure (GPU models, count, memory, wall-clock training time).
- Hyperparameters and baseline tuning budgets.
- Dataset splits, preprocessing pipelines, and filtering heuristics.
- Cross-section contradictions between methodology claims and experimental findings.

ReproCheck acts as an automated methodology pre-reviewer. It does not replace peer review or attempt to execute code; instead, it provides rigorous reporting transparency by evaluating what the paper actually describes.

---

## 2. System Architecture & Tech Stack

ReproCheck uses a decoupled full-stack architecture combining a modern React frontend, a FastAPI REST service, and a LangGraph workflow state machine.

```mermaid
flowchart TD
    User["Reviewer / Researcher"] -->|"PDF Upload / Text Paste"| Frontend["React 18 + Vite SPA"]
    Frontend -->|"REST API (/api/v1)"| API["FastAPI Application"]

    subgraph Backend_Boundary["FastAPI Backend Layer"]
        API --> Guardrails["Input Guardrails & Security Scanner"]
        Guardrails --> Extractor["PyMuPDF Extractor (Two-Column Reading Order)"]
        Guardrails --> Storage["LocalStorageService (StorageInterface)"]
        API --> DB[(PostgreSQL 16 + Alembic)]
        API --> Cache[(Redis Cache / In-Memory)]
    end

    subgraph Workflow_Engine["LangGraph State Machine Engine"]
        Classify["1. Classify Research Paradigm"] --> Checklist["2. Generate Two-Tier Checklist"]
        Checklist --> Interrupt["3. Human-in-the-Loop Pause (interrupt)"]
        Interrupt -->|"Checklist Approved"| Review["4. Methodology Completeness Review"]
        Review --> Consistency["5. Cross-Section Consistency Check"]
        Consistency --> Assessment["6. Synthesize Qualitative Assessment"]
        Assessment --> Report["7. Compile Findings Report"]
    end

    API -->|"BackgroundTasks"| Workflow_Engine
    Workflow_Engine --> Gateway["LiteLLM Gateway & Resilience Engine"]

    subgraph LLM_Cascade["Model Cascade (Free Tiers)"]
        Gateway --> Primary["Primary: Gemini 1.5 Flash"]
        Gateway -.->|"Fallback Cascade"| Secondary["Fallback: Groq Llama 3.3 70B / 3.1 8B"]
        Gateway --> Langfuse["Langfuse Observability (Text Masked)"]
    end
```

### Confirmed Technology Stack

| Component | Technology | Responsibility |
|---|---|---|
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS | Single-page UI, drag-and-drop submission, checklist editor, report view, Q&A drawer |
| **Backend API** | FastAPI, Python 3.12, `uv` | REST API routes, input validation, background task orchestration |
| **Database** | PostgreSQL 16, SQLAlchemy 2.0 (asyncpg) | Session persistence, paper records, LangGraph checkpoints |
| **Database Migrations** | Alembic | Schema versioning and reproducible migrations |
| **Cache** | Redis 7 + In-Memory Fallback | SHA-256 deterministic prompt caching |
| **Workflow Engine** | LangGraph, LangChain | State machine orchestration, checkpointing, and human-in-the-loop interruption |
| **Model Gateway** | LiteLLM | Unified access to Google Gemini and Groq with retries and fallback cascade |
| **PDF Extraction** | PyMuPDF (`fitz`) | Multi-column layout reading order text parsing behind `ExtractorInterface` |
| **Storage** | Local Filesystem | PDF document persistence behind `StorageInterface` |
| **Observability** | Langfuse SDK | Latency, token, and trace tracking with paper text masking |
| **Evaluation Suite** | DeepEval, Pytest | Multi-level testing across classification, checklist quality, completeness, and Q&A |

---

## 3. End-to-End Review Lifecycle

ReproCheck executes a 7-stage review process designed around transparency and human oversight:

```mermaid
sequenceDiagram
    autonumber
    actor User as Researcher
    participant UI as React Frontend
    participant API as FastAPI Backend
    participant WF as LangGraph Engine
    participant LLM as Model Gateway

    User->>UI: Submits PDF or Pastes Methodology
    UI->>API: POST /api/v1/sessions/upload (or /paste)
    API->>API: Input Guardrails Check (size, format, magic bytes, injection)
    API->>WF: Start Background Workflow
    WF->>LLM: Classify Research Paradigm (e.g., RAG, Fine-Tuning, Agents)
    WF->>LLM: Generate Two-Tier Candidate Checklist
    WF->>WF: interrupt() Execution & Save State Checkpoint to PostgreSQL
    API-->>UI: Status: AWAITING_CHECKLIST_APPROVAL
    UI->>User: Displays Interactive Checklist Editor
    User->>UI: Edits / Adds Custom Criteria & Clicks "Approve"
    UI->>API: POST /api/v1/sessions/{id}/checklist/approve
    API->>WF: Resume Workflow with Command(resume=checklist)
    WF->>LLM: Review Methodology Completeness (Extract Verbatim Quotes)
    WF->>LLM: Check Cross-Section Inconsistencies
    WF->>LLM: Synthesize Qualitative Assessment
    WF->>API: Mark Session COMPLETED
    UI->>API: GET /api/v1/sessions/{id}/report
    API-->>UI: Return Full Findings, Quotes, and Qualitative Assessment
    User->>UI: Opens Grounded Q&A Drawer
    UI->>API: POST /api/v1/sessions/{id}/qna
    API-->>UI: Returns Grounded Response with Verbatim Excerpts
```

### 1. Document Ingestion & Guardrails
- **File Upload**: PDF files up to 20MB are validated via `%PDF-` magic header bytes.
- **Pasted Text**: Direct methodology text entry with length validation.
- **Adversarial Scanner**: Scans inputs for prompt injection patterns before passing text to language models.
- **Reading Order Extraction**: PyMuPDF extracts two-column academic paper layouts in reading order (`sort=True`) and splits text into Title, Abstract, Methodology, Experiments, and Results.

### 2. Research Paradigm Classification
- Automatically classifies papers into an extensible two-tier taxonomy:
  - `Retrieval-Augmented Generation (RAG)`
  - `LLM Fine-Tuning & Alignment`
  - `AI Agents & Multi-Agent Systems`
  - `Computer Vision & Multimodal Learning`
  - `Reinforcement Learning & Robotics`
  - `Classical Machine Learning & Tabular`
  - `General / Novel AI Research`
- The user can optionally override or preselect the paradigm.

### 3. Two-Tier Checklist Generation
The system generates a customized evaluation checklist composed of:
- **Tier 1 (Universal Scientific Rigor)**: Essential empirical standards that apply across computer science (hardware/compute, hyperparameters, datasets, multi-run variance, baseline fairness).
- **Tier 2 (Domain & Paradigm Specific)**: Tailored criteria matching the paper's specific contributions (e.g., chunk size/overlap and index parameters for RAG; adapter rank/alpha and quantization for LoRA; environment loop steps and reflection for Agents).

### 4. Human-in-the-Loop Interruption
- LangGraph pauses execution using `interrupt()` and persists state to PostgreSQL.
- The reviewer inspects candidate criteria in the frontend checklist editor.
- The reviewer can enable/disable criteria, edit criterion wording, or add custom criteria.
- Once approved, the workflow resumes execution from the exact checkpoint.

### 5. Methodology Completeness Review & Evidence Extraction
- Evaluates the methodology against every approved criterion.
- Assigns findings with strict status codes:
  - `MET`: Satisfied with supporting verbatim evidence.
  - `INCOMPLETE`: Mentioned in the paper, but lacking essential implementation details.
  - `MISSING`: Entirely omitted from the paper.
- Assigns severity levels: `CRITICAL` (missing essential reproducibility factors), `WARNING` (partial reporting), and `NOTE` (minor suggestions).
- **Verbatim Quotation Requirement**: Every `MET` and `INCOMPLETE` finding must include verbatim text excerpts directly extracted from the paper. Findings marked `MISSING` have empty quotes.

### 6. Cross-Section Consistency Check
- Compares claims across Methodology, Experiments, and Results.
- Flags factual contradictions (e.g., methodology specifying 8 A100 GPUs while experimental results note single RTX 3090 evaluation).
- If only methodology text was submitted (`PASTED_TEXT`), cross-section checks are gracefully skipped with an explanatory note.

### 7. Qualitative Overall Assessment
- Generates a qualitative reproducibility label:
  - **Well documented**: Complete configuration, clear hyperparameters, transparent baselines.
  - **Partially documented**: Core methodology described, but omissions present in compute, seeds, or hyperparameter details.
  - **Insufficiently documented**: Critical gaps in reproducibility requirements.
- *Notice*: ReproCheck intentionally avoids numerical scores (e.g. 0-100), focusing instead on qualitative assessment with key strengths and critical reporting gaps.

### 8. Evidence-Grounded Q&A
- Reviewers can query paper details in an interactive chat drawer.
- Answers are strictly restricted to the submitted text and review findings.
- Out-of-scope or general knowledge queries (e.g. general trivia, coding tasks) are explicitly declined.

---

## 4. Repository Structure

```
reprocheck/
├── backend/
│   ├── alembic/                    # Database migrations
│   │   ├── env.py                  # Async Alembic migration environment
│   │   └── versions/               # Versioned migration scripts
│   ├── app/
│   │   ├── api/                    # FastAPI route handlers
│   │   │   ├── deps.py             # Dependency injection providers
│   │   │   ├── sessions.py         # Session upload and paste endpoints
│   │   │   ├── checklists.py       # Checklist inspection and approval
│   │   │   ├── reviews.py          # Status polling and report retrieval
│   │   │   └── qna.py              # Grounded Q&A endpoint
│   │   ├── core/                   # Infrastructure services
│   │   │   ├── database.py         # SQLAlchemy async engine & sessionmaker
│   │   │   ├── cache.py            # Redis & in-memory SHA-256 prompt cache
│   │   │   ├── guardrails.py       # File size, magic bytes & injection scanner
│   │   │   └── llm_gateway.py      # LiteLLM gateway, retries, fallback & Langfuse
│   │   ├── interfaces/             # Storage and extractor interfaces
│   │   │   ├── storage.py          # StorageInterface abstraction
│   │   │   ├── local_storage.py    # Local disk file storage implementation
│   │   │   ├── extractor.py        # ExtractorInterface abstraction
│   │   │   └── pymupdf_extractor.py# Multi-column PyMuPDF extractor
│   │   ├── models/                 # SQLAlchemy 2.0 ORM database models
│   │   │   ├── base.py             # Base declarative model & TimestampMixin
│   │   │   └── session.py          # ReviewSession & Paper models
│   │   ├── schemas/                # Pydantic request & response schemas
│   │   │   ├── session.py          # Session creation & metadata schemas
│   │   │   ├── checklist.py        # Checklist approval schemas
│   │   │   ├── review.py           # Report and finding schemas
│   │   │   └── qna.py              # Question & answer schemas
│   │   ├── services/               # Application service layer
│   │   │   └── workflow_service.py # LangGraph background orchestration
│   │   ├── workflows/              # LangGraph review workflow engine
│   │   │   ├── state.py            # Typed state schema & finding models
│   │   │   ├── graph.py            # Workflow compilation & checkpointing
│   │   │   ├── nodes/              # Workflow node functions
│   │   │   │   ├── classify.py     # Paradigm classification node
│   │   │   │   ├── checklist.py    # Checklist generation node
│   │   │   │   ├── approval.py     # Human-in-the-loop interrupt node
│   │   │   │   ├── review.py       # Methodology review node
│   │   │   │   ├── consistency.py  # Cross-section consistency node
│   │   │   │   ├── assessment.py   # Assessment synthesis node
│   │   │   │   └── qna.py          # Grounded Q&A node
│   │   │   └── prompts/            # Versioned prompt templates
│   │   ├── config.py               # Pydantic BaseSettings environment config
│   │   └── main.py                 # FastAPI application entry & static SPA mount
│   ├── tests/
│   │   ├── conftest.py             # Global test fixtures and environment overrides
│   │   ├── unit/                   # Unit tests (models, gateway, extractor, nodes)
│   │   ├── integration/            # Integration tests (PostgreSQL, APIs, E2E lifecycle)
│   │   └── evaluation/             # DeepEval LLM evaluation test suites (6 suites)
│   └── pyproject.toml              # Backend dependencies & configuration
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts           # Typed API client for FastAPI endpoints
│   │   ├── components/
│   │   │   ├── SubmissionForm.tsx  # PDF drag-and-drop & paste form
│   │   │   ├── ParadigmSelector.tsx# Research paradigm selection badge pills
│   │   │   ├── ChecklistEditor.tsx # Interactive two-tier checklist editor
│   │   │   ├── ReviewReportView.tsx# Findings report, severity badges & quote drawers
│   │   │   └── GroundedQnADrawer.tsx# Grounded chat slide-over drawer
│   │   ├── types/
│   │   │   └── index.ts            # Shared TypeScript domain models
│   │   ├── App.tsx                 # Root component orchestrating review lifecycle
│   │   ├── main.tsx                # React 18 DOM mount point
│   │   └── index.css               # Tailwind CSS directives
│   ├── index.html                  # HTML template
│   ├── package.json                # Frontend dependencies
│   ├── tailwind.config.js          # Tailwind design system configuration
│   └── vite.config.ts              # Vite configuration with backend API proxy
│
├── AGENTS.md                       # Coding instructions & architectural constraints
├── ARCHITECTURE.md                 # System architecture specification
├── CODE_DECISIONS.md               # Low-level implementation decisions & alternatives
├── DECISIONS.md                    # High-level Architecture Decision Records (ADRs)
├── PROJECT.md                      # Product vision and scope definition
├── tasks.md                        # Implementation progress tracking
└── docker-compose.yml              # Local PostgreSQL & Redis infrastructure
```

---

## 5. Prerequisites & Environment Setup

### Prerequisites
- **Python**: 3.12 or newer.
- **uv**: Fast Python package installer and resolver.
- **Node.js**: v20 LTS or newer with npm.
- **PostgreSQL**: Local or Dockerized PostgreSQL 16 on port `5432`.
- **Redis**: Local or Dockerized Redis on port `6379`.
- **API Keys**: Google Gemini API key and/or Groq API key (free tier models).

### 1. Clone & Configure Environment
Create `.env` inside the `backend/` directory:
```bash
cp backend/.env.example backend/.env
```

Ensure your `.env` contains your API credentials and database configuration:
```ini
# Environment Configuration
APP_ENV=development
DEBUG=True
PROJECT_NAME="ReproCheck"

# PostgreSQL Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/reprocheck
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=reprocheck

# Redis Prompt Cache
REDIS_URL=redis://127.0.0.1:6379/0

# Model Provider API Keys (Free Tier)
GEMINI_API_KEY="your-gemini-api-key"
GROQ_API_KEY="your-groq-api-key"

# LiteLLM Configuration
PRIMARY_MODEL="gemini/gemini-1.5-flash"
FALLBACK_MODEL="groq/llama-3.3-70b-versatile"
EMERGENCY_MODEL="groq/llama-3.1-8b-instant"

# Langfuse Observability (Optional)
LANGFUSE_PUBLIC_KEY=""
LANGFUSE_SECRET_KEY=""
LANGFUSE_HOST="https://cloud.langfuse.com"
```

### 2. Start PostgreSQL & Redis
Using the provided `docker-compose.yml`:
```bash
docker compose up -d
```

### 3. Run Database Migrations
Apply Alembic migrations to create tables and schemas:
```bash
uv run --project backend alembic upgrade head
```

---

## 6. Running the Application

### Option A: Unified Full-Stack Server (Recommended for Quick Start)
Build the frontend production bundle and run the FastAPI application:
```bash
# 1. Build frontend
cd frontend
npm install
npm run build
cd ..

# 2. Start FastAPI backend (serves both API and SPA)
uv run --project backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to **`http://localhost:8000`** in your browser.

### Option B: Separate Development Servers (Hot Reloading)
**Terminal 1 — Backend API**:
```bash
uv run --project backend uvicorn app.main:app --port 8000 --reload
```
API Documentation (Swagger UI) is available at **`http://localhost:8000/docs`**.

**Terminal 2 — Frontend Dev Server**:
```bash
cd frontend
npm run dev
```
Vite development server runs at **`http://localhost:3000`** and proxies `/api` requests to the backend on port 8000.

---

## 7. API Reference

All backend API routes are prefixed with `/api/v1`:

| Method | Endpoint | Description | Request Body |
|---|---|---|---|
| `POST` | `/sessions/upload` | Upload PDF research paper | `multipart/form-data` (`file`, optional `primary_research_type`) |
| `POST` | `/sessions/paste` | Submit pasted methodology text | JSON `{ methodology_text, title?, primary_research_type? }` |
| `GET` | `/sessions/{id}` | Get session lifecycle status | None |
| `GET` | `/sessions/{id}/checklist` | Retrieve generated review checklist | None |
| `POST` | `/sessions/{id}/checklist/approve` | Approve & resume review with customized checklist | JSON `{ checklist: ChecklistItem[] }` |
| `GET` | `/sessions/{id}/status` | Poll review progress | None |
| `GET` | `/sessions/{id}/report` | Retrieve completed review report | None |
| `POST` | `/sessions/{id}/qna` | Ask grounded question about paper | JSON `{ question: string }` |
| `GET` | `/health` | System health status check | None |

---

## 8. Testing & Evaluation Guide

The codebase includes a comprehensive 64-test automated test suite across unit, evaluation, and live database integration tiers.

### Run All Unit and Evaluation Tests
```bash
uv run --project backend pytest backend/tests/unit/ backend/tests/evaluation/ -v
```

### Run Live Database Integration Tests
Ensure PostgreSQL is running on port 5432, then run:
```bash
uv run --project backend pytest backend/tests/integration/ -v
```

### Test Suite Overview

1. **Unit Tests (`backend/tests/unit/`) — 39 tests**:
   - `test_config.py`: Environment variable loading, fallback defaults, cached settings.
   - `test_database.py`: SQLAlchemy async engine and connection pooling.
   - `test_extractor.py`: Multi-column text reading order and section segmentation.
   - `test_gateway.py`: LiteLLM gateway, prompt hashing, Redis caching, exponential backoffs, and fallback cascades.
   - `test_guardrails.py`: File size limit (20MB), magic byte verification, and adversarial prompt injection heuristics.
   - `test_health.py`: Health check endpoint and static SPA index serving.
   - `test_models.py`: Database models, relationship cascades, and JSONB persistence.
   - `test_storage.py`: Local disk file storage lifecycle (save, read, delete).
   - `test_workflow_nodes.py`: Individual LangGraph node logic (classify, checklist, review, consistency, assessment, Q&A).

2. **DeepEval LLM Evaluation Suites (`backend/tests/evaluation/`) — 15 tests**:
   - `test_01_classification.py`: Paradigm accuracy across RAG, Fine-Tuning, Agents, and Novel AI.
   - `test_02_checklist_quality.py`: Two-tier coverage, non-redundancy, and rationale clarity.
   - `test_03_review_completeness.py`: Intentional omission detection (`MISSING`/`INCOMPLETE`) and fully met reporting.
   - `test_04_consistency_check.py`: Section discrepancy detection and single-section input scoping.
   - `test_05_evidence_grounding.py`: Verbatim quote verification and hallucinated quote prevention.
   - `test_06_qna_faithfulness.py`: Grounded citation retrieval and out-of-scope question refusal.

3. **Integration Tests (`backend/tests/integration/`) — 10 tests**:
   - `test_db_integration.py`: Live PostgreSQL connection and CRUD lifecycle.
   - `test_api.py`: FastAPI endpoints (upload, paste, checklist approval, report, Q&A).
   - `test_workflow.py`: End-to-end LangGraph state machine with PostgreSQL checkpointing and HITL resumption.
   - `test_e2e_verification.py`: Full end-to-end paper review lifecycle on an academic paper with known gaps.

---

## 9. Core Engineering Principles

- **KISS (Keep It Simple, Stupid)**: Favor readable, direct code over heavy design patterns, unnecessary wrappers, and speculative abstractions.
- **Code Liability**: Code is a maintenance liability. Accomplish system goals with minimal code lines, clear modularity, and high test coverage.
- **Maintainability & Documentation**: Adhere to ASD-STE100 principles (short sentences, active voice, clear headings). Architectural decisions are recorded in `DECISIONS.md`, and code-level technical choices in `CODE_DECISIONS.md`.
- **Zero Hallucination & Data Privacy**: Never synthesize quotes or send unmasked research paper text to third-party observability providers.
- **Free Model Cascade**: Operates on free-tier models (Gemini 1.5 Flash and Groq Llama 3.3/3.1) with prompt caching and exponential backoffs to eliminate operational cost.

---

## 10. License

ReproCheck is distributed under the MIT License.
