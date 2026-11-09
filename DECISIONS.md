# Architecture Decision Records (ADR) — ReproCheck

This document records the technical decisions for the ReproCheck project.
It explains the choices made, the reasons for each choice, and the consequences.

---

## ADR-001: Frontend Tooling and Framework

- **Status**: Accepted
- **Context**: The user interface needs interactive forms, checklist tables, report cards, and a chat drawer.
- **Decision**: Use React 18 with TypeScript and Vite.
- **Reasons**:
  - Vite provides fast local development and fast builds.
  - TypeScript ensures type safety between backend schemas and frontend components.
  - React has large community support and established component libraries.
- **Consequences**:
  - The team must maintain TypeScript types matching backend schemas.

---

## ADR-002: PDF Text Extraction and Layout Handling

- **Status**: Accepted
- **Context**: The system must extract text from academic computer science papers. Many papers use two-column layouts.
- **Decision**: Use PyMuPDF (`fitz`) behind a generic `ExtractorInterface`.
- **Reasons**:
  - PyMuPDF runs locally without external server daemons or Java dependencies.
  - PyMuPDF supports reading order sorting flags to parse two-column text correctly.
  - PyMuPDF extracts text quickly and reliably.
- **Consequences**:
  - Scanned image PDFs without text layers will require an OCR extractor later.
  - The interface abstraction allows adding OCR extractors without changing application code.

---

## ADR-003: Database Engine and Migrations

- **Status**: Accepted
- **Context**: The system needs persistent storage for sessions, paper metadata, checklists, findings, and evidence quotes.
- **Decision**: Use PostgreSQL with SQLAlchemy 2.0 (asyncio + asyncpg) and Alembic.
- **Reasons**:
  - PostgreSQL provides reliable relational storage and native JSONB columns.
  - SQLAlchemy 2.0 provides typed asynchronous database operations.
  - Alembic manages database schema migrations reliably.
- **Consequences**:
  - The development environment runs PostgreSQL and Redis directly on the host.
  - A `docker-compose.yml` file is provided as an optional convenience.

---

## ADR-004: Workflow Coordination and Human-in-the-Loop State

- **Status**: Accepted
- **Context**: The review workflow must pause after checklist generation so the user can inspect, edit, and approve criteria.
- **Decision**: Use LangGraph `StateGraph` with PostgreSQL state checkpointing (`PostgresSaver`).
- **Reasons**:
  - LangGraph manages stateful workflows with explicit pause and resume points.
  - `PostgresSaver` persists review state safely across application restarts.
  - Resumption endpoints can load state directly by session ID.
- **Consequences**:
  - Workflow logic stays separate from API route handlers.

---

## ADR-005: Language Model Gateway and Free Model Providers

- **Status**: Accepted
- **Context**: Development requires reliable language model access without high costs. The system must tolerate rate limits.
- **Decision**: Use LiteLLM with free models from Google Gemini and Groq.
- **Reasons**:
  - Google Gemini and Groq provide capable free tiers.
  - Primary model: `gemini/gemini-1.5-flash` or `groq/llama-3.3-70b-versatile`.
  - Fallback model: `groq/llama-3.1-8b-instant`.
  - The gateway retries on rate limits (429) and switches automatically to the fallback provider.
- **Consequences**:
  - Free tiers impose requests-per-minute limits. Redis caching reduces duplicate model calls.

---

## ADR-006: Observability with Langfuse Context Manager

- **Status**: Accepted
- **Context**: Developers need traces for model latency, token counts, and failures. System rules forbid leaking full paper text.
- **Decision**: Use the Langfuse SDK context manager (`start_as_current_observation`, `propagate_attributes`).
- **Reasons**:
  - Direct context managers provide full control over span boundaries and timing.
  - The application can sanitize and hash paper text before recording trace data.
  - It avoids unexpected data leaks from automatic callback handlers.
- **Consequences**:
  - Developers must write explicit span context managers inside gateway and workflow functions.

---

## ADR-007: Session Management and Authentication

- **Status**: Accepted
- **Context**: The initial version needs simple session isolation without premature account management.
- **Decision**: Use UUID session IDs with a nullable `user_id` database column.
- **Reasons**:
  - Keeps the initial version simple (KISS).
  - Allows users to review papers immediately without signing up.
  - FastAPI dependency injection supplies session context to routes.
- **Consequences**:
  - Adding user authentication later requires setting `user_id` without changing table structures.

---

## ADR-008: Extensible Research Type Taxonomy

- **Status**: Accepted
- **Context**: The system must evaluate both the 6 initial AI research areas and general or novel AI papers.
- **Decision**: Use a two-tier checklist generation system.
- **Reasons**:
  - Tier 1 enforces core AI scientific rigor (compute setup, hyperparameters, dataset details, seed variance).
  - Tier 2 evaluates specific domain heuristics or dynamically derived criteria based on claimed contributions.
  - This allows the system to review any AI paper.
- **Consequences**:
  - Prompts must handle both recognized research types and novel contribution profiles.

---

## ADR-009: File Storage Architecture

- **Status**: Accepted
- **Context**: The system must store uploaded PDF files safely.
- **Decision**: Use local disk storage behind a `StorageInterface`.
- **Reasons**:
  - Local disk storage requires no cloud setup for local development.
  - The interface abstraction makes switching to S3 or Google Cloud Storage simple.
- **Consequences**:
  - File paths must not be hardcoded across the application.

---

## ADR-010: Multi-Level Evaluation Suite

- **Status**: Accepted
- **Context**: AI workflow outputs must be evaluated systematically to prevent regressions.
- **Decision**: Use DeepEval split across 6 independent test files.
- **Reasons**:
  - Isolates testing for classification, checklist quality, review completeness, consistency, evidence grounding, and Q&A.
  - Allows running specific evaluation suites when changing individual prompts or nodes.
- **Consequences**:
  - Evaluation tests run separately from normal unit and integration tests.

---

## ADR-011: Package Management and Build Sequence

- **Status**: Accepted
- **Context**: The project needs reliable Python package management and a clear development order.
- **Decision**: Use `uv` for Python package management. Build the backend first, then the frontend.
- **Reasons**:
  - `uv` provides fast dependency resolution and reproducible lockfiles.
  - Building the backend first verifies workflow correctness, API contracts, and evaluations before UI integration.
- **Consequences**:
  - Developers use `uv` commands (`uv run`, `uv add`) for backend development.
