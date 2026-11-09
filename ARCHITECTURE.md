# ReproCheck — System Architecture

## 1. Architecture Overview

ReproCheck uses a decoupled frontend and backend.
The React frontend provides the user interface.
The FastAPI backend manages application logic, data access, and the review workflow.
LangGraph coordinates AI review steps using a state machine.
LiteLLM provides access to language models from Google Gemini and Groq.
PostgreSQL stores application data and LangGraph workflow checkpoints.
Redis provides prompt caching and short-lived state storage.
The local filesystem stores uploaded PDF files behind an abstract interface.
Langfuse tracks operational metrics through an explicit context manager.

## 2. Confirmed Technology Stack

| Area | Technology | Responsibility |
|---|---|---|
| Frontend | React 18, Vite, TypeScript | User interface and client state |
| Backend | FastAPI, uv | API routes, package management, and coordination |
| Database | PostgreSQL | Persistent application records and checkpoints |
| ORM & Migrations | SQLAlchemy 2.0 (asyncpg), Alembic | Typed database models and schema migrations |
| Cache | Redis | Prompt caching and transient session state |
| AI Orchestration | LangGraph | State machine and human-in-the-loop workflow |
| Model Gateway | LiteLLM | Unified access to Google Gemini and Groq |
| Observability | Langfuse | Tracing with context manager and data masking |
| Evaluation | DeepEval | Multi-stage evaluation of model outputs |
| PDF Extraction | PyMuPDF (`fitz`) | Two-column text extraction behind interface |
| File Storage | Local filesystem | PDF file storage behind interface |

## 3. System Components and Boundaries

### 3.1 Frontend Layer
The frontend provides user interaction.
It presents upload forms, research paradigm selectors, and checklist editors.
It displays review findings with exact paper quotes.
It provides a grounded chat drawer for questions about the review.

### 3.2 API and Input Guardrail Layer
FastAPI route handlers validate all requests.
Before passing input to workflows, guardrails check file size, format, and text sanity.
Guardrails detect prompt injection patterns in submitted papers.
Route handlers stay thin and call application services.

### 3.3 Storage and Extractor Interfaces
The backend accesses external services through modular Python interfaces.
`StorageInterface` isolates file persistence.
`ExtractorInterface` isolates PDF text extraction.
This allows swapping to cloud storage or alternate extractors without changing application logic.

### 3.4 Model Gateway Layer
`LLMGatewayService` wraps LiteLLM calls.
It checks Redis for cached model responses before calling external APIs.
It runs primary models (`gemini-1.5-flash` or `llama-3.3-70b-versatile`).
It retries on rate limits (429) with exponential backoff.
It fails over to fallback models (`llama-3.1-8b-instant`) when primary calls fail.
It validates model outputs against Pydantic schemas.

### 3.5 LangGraph Review Workflow
LangGraph manages the multi-step review state machine:
1. **Classify**: Identifies research paradigm (extensible taxonomy for any AI paper).
2. **Generate Checklist**: Creates paper-specific criteria across two tiers.
3. **Interrupt**: Pauses workflow and saves state to PostgreSQL for user approval.
4. **Review**: Checks completeness, missing details, and cross-section consistency.
5. **Assess**: Synthesizes qualitative label (`Well documented`, `Partially documented`, `Insufficiently documented`).
6. **Q&A**: Answers questions strictly grounded in methodology and review findings.

### 3.6 Observability Layer
The application uses the Langfuse context manager (`start_as_current_observation`).
It traces latency, token usage, and errors.
It strips or hashes sensitive paper text before sending traces.

## 4. Main Request Flow

1. The user uploads a PDF or pastes methodology text.
2. FastAPI validates the input and creates a review session.
3. PyMuPDF extracts text sections using reading order flags.
4. LangGraph classifies the research type and generates a candidate checklist.
5. LangGraph pauses execution and saves checkpoint state to PostgreSQL.
6. The user reviews, edits, and approves the checklist in the frontend.
7. The user approval resumes the workflow from the saved checkpoint.
8. The workflow evaluates methodology completeness and section consistency.
9. The workflow saves findings, evidence quotes, and assessment to PostgreSQL.
10. The user inspects the review report and asks questions in the grounded chat drawer.

## 5. Background Processing

The initial version uses FastAPI `BackgroundTasks` for workflow execution.
LangGraph persists step progress in PostgreSQL using `PostgresSaver`.
If an application restart occurs, the workflow resumes from the latest saved step.
A distributed worker queue can replace `BackgroundTasks` if future load requires it.

## 6. Architecture Decisions and Evolution

Technical decisions are recorded in `DECISIONS.md`.
The architecture keeps components modular:
- Add user authentication by setting the nullable `user_id` on sessions.
- Replace local file storage by implementing `StorageInterface` for cloud storage.
- Run PostgreSQL and Redis locally, with Docker Compose as an optional convenience.
- Support new paper types through the extensible two-tier taxonomy.
- Add new review checks by registering new LangGraph nodes.
Follow KISS in every implementation change.
