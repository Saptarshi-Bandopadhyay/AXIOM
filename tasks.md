# ReproCheck — Implementation Tasks

This file tracks implementation progress from project setup to completion.
The backend is built and tested completely before starting the frontend.
Follow the steps in order. Complete each task before starting the next task.
For each task:
- Add clear code comments and docstrings explaining intent and logic.
- Record code-level technical choices and alternatives in `CODE_DECISIONS.md`.
- Run relevant tests before marking a task as done.

---

## Phase 1: Backend Setup and Infrastructure

- [x] **Task 1.1**: Initialize backend using `uv` with `pyproject.toml` and dependencies.
- [x] **Task 1.2**: Configure local PostgreSQL (port 5432) and Redis (port 6379) connections, with an optional `docker-compose.yml` for convenience.
- [x] **Task 1.3**: Configure environment settings and Pydantic configuration in `backend/app/config.py`.
- [x] **Task 1.4**: Set up SQLAlchemy 2.0 async engine and Alembic migration framework in `backend/alembic/`.
- [x] **Task 1.5**: Create database models for `ReviewSession` and `Paper` with initial Alembic migration.
- [x] **Task 1.6**: Verify database connectivity and migration execution using `uv run alembic upgrade head`.

## Phase 2: Core Abstractions, Storage, and PDF Extraction

- [x] **Task 2.1**: Implement `StorageInterface` in `backend/app/interfaces/storage.py`.
- [x] **Task 2.2**: Implement concrete `LocalStorageService` for reading and writing files on disk.
- [x] **Task 2.3**: Implement `ExtractorInterface` in `backend/app/interfaces/extractor.py`.
- [x] **Task 2.4**: Implement `PyMuPDFExtractor` with two-column reading order support (`sort=True`).
- [x] **Task 2.5**: Implement section segmentation logic (Title, Abstract, Methodology, Experiments, Results).
- [x] **Task 2.6**: Add unit tests in `tests/unit/test_storage.py` and `tests/unit/test_extractor.py`.

## Phase 3: Model Gateway, Guardrails, and Observability

- [x] **Task 3.1**: Implement input guardrails for file size (20MB max), format, and prompt injection detection.
- [x] **Task 3.2**: Configure LiteLLM gateway with free models (`gemini-1.5-flash`, `llama-3.3-70b-versatile`).
- [x] **Task 3.3**: Implement Redis prompt caching using SHA-256 hash of model parameters and prompt content.
- [x] **Task 3.4**: Implement retry engine with exponential backoff on rate limits (429) and server errors (5xx).
- [x] **Task 3.5**: Implement provider fallback cascade switching to `llama-3.1-8b-instant` when primary fails.
- [x] **Task 3.6**: Implement Langfuse observability using `start_as_current_observation` and `propagate_attributes`.
- [x] **Task 3.7**: Implement paper text data masking to prevent sending raw paper text to external trace logs.
- [x] **Task 3.8**: Add unit tests in `tests/unit/test_gateway.py` and `tests/unit/test_guardrails.py`.

## Phase 4: LangGraph Review Workflow Engine

- [x] **Task 4.1**: Define `ReviewGraphState` typed schema in `backend/app/workflows/state.py`.
- [x] **Task 4.2**: Implement research paradigm classification node with extensible two-tier taxonomy.
- [x] **Task 4.3**: Implement checklist generation node with Tier 1 and Tier 2 criteria and rationales.
- [x] **Task 4.4**: Implement human-in-the-loop pause (`interrupt()`) and PostgreSQL state checkpointing.
- [x] **Task 4.5**: Implement methodology completeness review node with verbatim quote extraction.
- [x] **Task 4.6**: Implement cross-section inconsistency node comparing methodology, experiments, and results.
- [x] **Task 4.7**: Implement qualitative overall assessment synthesis node.
- [x] **Task 4.8**: Implement grounded Q&A node restricted to paper text and review findings.
- [x] **Task 4.9**: Add workflow integration tests in `tests/integration/test_workflow.py`.

## Phase 5: FastAPI Backend Endpoints

- [x] **Task 5.1**: Implement dependency injection for database sessions, services, and session context.
- [x] **Task 5.2**: Implement session creation, PDF upload, and pasted methodology endpoints in `sessions.py`.
- [x] **Task 5.3**: Implement checklist retrieval, edit, and approval endpoints in `checklists.py`.
- [x] **Task 5.4**: Implement review status polling and report retrieval endpoints in `reviews.py`.
- [x] **Task 5.5**: Implement grounded Q&A endpoint in `qna.py`.
- [x] **Task 5.6**: Add API integration tests in `tests/integration/test_api.py`.

## Phase 6: Backend Multi-Level DeepEval Test Suite

- [x] **Task 6.1**: Implement `test_01_classification.py` for standard and novel research paradigms.
- [x] **Task 6.2**: Implement `test_02_checklist_quality.py` for relevance, clarity, and non-redundancy.
- [x] **Task 6.3**: Implement `test_03_review_completeness.py` for missing methodology detection.
- [x] **Task 6.4**: Implement `test_04_consistency_check.py` for section discrepancy detection.
- [x] **Task 6.5**: Implement `test_05_evidence_grounding.py` for verbatim quotation verification.
- [x] **Task 6.6**: Implement `test_06_qna_faithfulness.py` for answer grounding and out-of-scope refusal.

## Phase 7: Frontend Setup and User Interface

- [x] **Task 7.1**: Initialize frontend with Vite, React 18, TypeScript, and Tailwind CSS.
- [x] **Task 7.2**: Create TypeScript API client and shared data types matching backend schemas.
- [x] **Task 7.3**: Build paper submission component with PDF drag-and-drop and text paste area.
- [x] **Task 7.4**: Build research paradigm confirmation and selection badge component.
- [x] **Task 7.5**: Build interactive checklist editor component for adding, editing, and approving criteria.
- [x] **Task 7.6**: Build review report view with category cards, severity badges, and quote drawers.
- [x] **Task 7.7**: Build grounded Q&A chat drawer component with cited excerpts.
- [x] **Task 7.8**: Connect frontend views with verified backend endpoints.

## Phase 8: End-to-End Verification and Documentation

- [x] **Task 8.1**: Run full automated backend test suite (`uv run pytest tests/`).
- [x] **Task 8.2**: Perform manual review of a sample academic paper with known methodological gaps.
- [x] **Task 8.3**: Verify human-in-the-loop checklist edit and approval flow.
- [x] **Task 8.4**: Verify verbatim quotes in findings report and grounded Q&A responses.
- [x] **Task 8.5**: Update project documentation and record final observations.
