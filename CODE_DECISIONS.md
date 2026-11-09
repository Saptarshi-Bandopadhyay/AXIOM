# ReproCheck — Code-Level Implementation Decisions

This document records code-level implementation choices made during development.
High-level architectural decisions remain in `DECISIONS.md`.
For each decision, this file documents:
- The context and task.
- The choice made.
- The alternatives considered.
- The reason for the choice.

The file is written in approximately 80% ASD-STE100 style.
Entries are organized by phase and task.

---

## Phase 1: Backend Setup and Infrastructure

### CD-001: Backend Build System and Package Layout
- **Task**: Task 1.1 — Initialize backend using `uv`.
- **Choice**: Use `hatchling` as the build backend in `pyproject.toml` with `app` as package directory.
- **Alternatives Considered**:
  - `setuptools`: Slower metadata generation and legacy configuration syntax.
  - `flit-core`: Limited support for complex package mappings.
  - `uv_build`: Experimental and tied to unstable preview flags.
- **Reason**: `hatchling` is lightweight, follows standard PEP 517/621, and supports editable installs reliably.

### CD-002: Pytest Asyncio Event Loop Fixture Scope and Auto Mode
- **Task**: Task 1.1 — Configure test runner settings in `pyproject.toml`.
- **Choice**: Set `asyncio_mode = "auto"` and `asyncio_default_fixture_loop_scope = "function"`.
- **Alternatives Considered**:
  - Leaving fixture loop scope unset: Triggers deprecation warnings in `pytest-asyncio` 1.4+.
  - Using `"session"` scope: Reuses event loops across tests, risking leaked state and race conditions.
  - Adding `@pytest.mark.asyncio` to every async test: Redundant boilerplate.
- **Reason**: Function-level scoping isolates event loops per test case. Setting `asyncio_mode = "auto"` automatically identifies and executes all `async def test_*` coroutines without manual `@pytest.mark.asyncio` decorators.

### CD-003: LiteLLM Local Model Cost Map Isolation
- **Task**: Task 1.1 — Set up testing environment for model gateway dependencies.
- **Choice**: Set `os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"` during testing.
- **Alternatives Considered**:
  - Default remote fetching: Attempts 3 HTTP connections to GitHub, adding 10 seconds of timeout delay in isolated or offline environments.
- **Reason**: Using the bundled local cost map removes unnecessary network calls and avoids test runner latency.

### CD-004: Docker Compose as Optional Local Backing Services
- **Task**: Task 1.2 — Configure local PostgreSQL and Redis connections.
- **Choice**: Maintain `docker-compose.yml` in project root with container definitions for `postgres:16-alpine` and `redis:7-alpine`.
- **Alternatives Considered**:
  - Requiring Docker containers: Creates friction when services are already installed locally.
  - Omitting Docker Compose completely: Breaks portability for users on machines without installed services.
- **Reason**: Preserves local host development speed while offering container convenience for portability.

### CD-005: Dual Database URLs for Async Runtime and Sync Migrations
- **Task**: Task 1.2 — Configure database connection strings.
- **Choice**: Provide both `DATABASE_URL` (`postgresql+asyncpg://`) and `DATABASE_URL_SYNC` (`postgresql://`) in `.env`.
- **Alternatives Considered**:
  - Dynamically altering driver prefix in Python code at runtime.
- **Reason**: Explicit configuration prevents URL parsing errors when database credentials contain special characters. It keeps Alembic migration tooling separate from async application code.

### CD-006: Pydantic Settings with LRU Cache Singleton
- **Task**: Task 1.3 — Configure environment settings in `backend/app/config.py`.
- **Choice**: Define `Settings` using `BaseSettings` and wrap `get_settings()` with `@lru_cache(maxsize=1)`.
- **Alternatives Considered**:
  - Global module-level instantiation (`settings = Settings()`): Reads disk files at import time and makes testing overrides difficult.
  - Instantiating `Settings()` on every call: Causes redundant disk I/O and environment parsing.
- **Reason**: `lru_cache(maxsize=1)` guarantees one parsed instance across the application lifetime. It allows clean cache clearing (`get_settings.cache_clear()`) in unit test fixtures.

### CD-007: Multiple `.env` Path Lookups for Monorepo Execution
- **Task**: Task 1.3 — Configure `SettingsConfigDict` in `config.py`.
- **Choice**: Set `env_file=(".env", "../.env")`.
- **Alternatives Considered**:
  - Single hardcoded path `".env"`: Fails when commands run from repository root instead of `backend/`.
- **Reason**: Searching both paths allows scripts and tests to run smoothly from both repository root and `backend/` directory.

### CD-008: SQLAlchemy 2.0 Async Engine and DeclarativeBase with AsyncAttrs
- **Task**: Task 1.4 — Set up SQLAlchemy async engine and base models.
- **Choice**: Use `create_async_engine` bound to `asyncpg` with `pool_pre_ping=True`, and `Base` subclassing `AsyncAttrs` and `DeclarativeBase`.
- **Alternatives Considered**:
  - Legacy `declarative_base()` from SQLAlchemy 1.4: Lacks modern typing and Mapped column support.
  - Omitting `AsyncAttrs`: Prevents awaiting relationships dynamically in asynchronous graph nodes.
- **Reason**: Provides modern type hints, avoids stale connection errors using pre-ping, and enables safe async relationship access.

### CD-009: Alembic Async Environment Integration with Pydantic Settings
- **Task**: Task 1.4 — Configure Alembic migration framework in `backend/alembic/`.
- **Choice**: Initialize Alembic with `-t async` template and bind `env.py` directly to `app.config.get_settings()` and `app.models.Base.metadata`.
- **Alternatives Considered**:
  - Hardcoding connection strings in `alembic.ini`: Insecure and prone to configuration divergence.
  - Sync-only Alembic configuration: Requires maintaining separate synchronous database drivers.
- **Reason**: Centralizes database configuration in `.env` and uses the existing asynchronous engine cleanly.

### CD-010: Generic UUID and Dialect-Variant JSONB Column Types
- **Task**: Task 1.5 — Create database models for ReviewSession and Paper.
- **Choice**: Use `sqlalchemy.Uuid(as_uuid=True)` and `sa.JSON().with_variant(postgresql.JSONB, "postgresql")`.
- **Alternatives Considered**:
  - Hardcoded `postgresql.UUID` and `postgresql.JSONB`: Fails on non-Postgres engines during local testing.
  - Plain string columns for JSON lists: Removes structured query capabilities.
- **Reason**: Produces native PostgreSQL UUID and JSONB columns in production while maintaining cross-engine compatibility.

### CD-011: String-Backed Enums for Model Statuses
- **Task**: Task 1.5 — Define SessionStatus and InputType enums.
- **Choice**: Subclass `(str, Enum)`.
- **Alternatives Considered**:
  - Standard `Enum`: Requires `.value` access during serialization and creates friction with Pydantic.
  - PostgreSQL native ENUM types: Requires schema alter statements when adding new enum values.
- **Reason**: Simplifies JSON serialization, maintains type safety, and allows adding new statuses without table alterations.

### CD-012: Pre-Flush UUID and Default Attribute Initialization
- **Task**: Task 1.5 — Initialize default model attributes.
- **Choice**: Provide `__init__` on `ReviewSession` and `Paper` assigning `uuid.uuid4()` and default status/lists before database flush.
- **Alternatives Considered**:
  - Relying solely on `mapped_column(default=...)`: Leaves attributes as `None` in memory until after a database `session.flush()`.
- **Reason**: Ensures models are valid, fully populated objects immediately upon instantiation in memory.

### CD-013: NullPool for Asyncpg Integration Testing Across Event Loops
- **Task**: Task 1.6 — Verify database connectivity and migration execution.
- **Choice**: Use `sqlalchemy.pool.NullPool` in asynchronous integration tests.
- **Alternatives Considered**:
  - Default connection pooling (`QueuePool`): Holds open asyncpg connections across pytest functions. When pytest closes the function-scoped event loop, cached connections crash with `RuntimeError: got Future attached to a different loop`.
- **Reason**: `NullPool` opens and closes fresh database connections per test, preventing connection leaks across event loops.

---

## Phase 2: Core Abstractions, Storage, and PDF Extraction

### CD-014: Asynchronous StorageInterface Byte Contract
- **Task**: Task 2.1 — Implement StorageInterface in `backend/app/interfaces/storage.py`.
- **Choice**: Use an `abc.ABC` abstract base class defining async `save()`, `load()`, `exists()`, `delete()`, and `get_path()`, using raw `bytes`.
- **Alternatives Considered**:
  - File-pointer/stream interface (`io.BytesIO`): Adds wrapper overhead for bounded files (up to 20MB).
  - Synchronous filesystem calls: Blocks the asyncio event loop during disk I/O and future cloud uploads.
- **Reason**: Async methods prevent event-loop stalling. Operating on raw `bytes` maintains a clean, simple contract (KISS) across local disk, AWS S3, and Google Cloud Storage.

### CD-015: Non-Blocking File I/O and Path Traversal Protection
- **Task**: Task 2.2 — Implement `LocalStorageService` in `backend/app/services/local_storage.py`.
- **Choice**: Use `asyncio.to_thread` for all disk operations, and validate paths via `target.resolve().relative_to(self.base_dir)`.
- **Alternatives Considered**:
  - Direct synchronous `Path.read_bytes()` / `write_bytes()`: Blocks the asyncio event loop during file I/O.
  - Adding `aiofiles` dependency: Unnecessary dependency when `asyncio.to_thread` is built-in and robust.
  - Regex sanitization for path traversal: Fragile against URL-encoding or backslash variations.
- **Reason**: `asyncio.to_thread` prevents event loop blocking without extra packages. `Path.relative_to` provides airtight path traversal defense.

### CD-016: ExtractorInterface with Pydantic ExtractedDocument Schema
- **Task**: Task 2.3 — Implement `ExtractorInterface` in `backend/app/interfaces/extractor.py`.
- **Choice**: Define an abstract base class returning an `ExtractedDocument` Pydantic model with dedicated fields for title, abstract, methodology, experiments, results, and full text.
- **Alternatives Considered**:
  - Returning untyped Python dictionaries: Lacks validation and auto-complete for callers.
  - Synchronous extraction contract: Would block the web event loop during multi-page document parsing.
- **Reason**: Pydantic models guarantee typed section boundaries across different extractor implementations. Async methods prevent blocking during heavy document processing.

### CD-017: PyMuPDF Reading Order and Heading-Based Section Segmentation
- **Task**: Tasks 2.4 & 2.5 — Implement `PyMuPDFExtractor` with reading order and section segmentation.
- **Choice**: Use `page.get_text("text", sort=True)` combined with concise regex heading matching and a fallback to `full_text` when explicit methodology headers are missing.
- **Alternatives Considered**:
  - Complex XML/bounding-box layout engines: Hundreds of lines of code with brittle heuristics across diverse LaTeX templates.
  - LLM-based section segmentation: Slower, costly, and burns model quota on basic parsing.
- **Reason**: Achieves clean multi-column reading order in under 115 lines of code (minimizing code liability) while providing reliable fallback handling.

### CD-018: Code Liability Reduction Across Models, Services, and Tests
- **Task**: Phase 2 Refactoring — Streamline codebase and test suite per code liability principle.
- **Choice**: Remove verbose attribute metadata descriptions, redundant validators, custom `__init__` overrides, and internal language/framework unit test boilerplate. Retain clean interfaces, essential business logic, and behavioral tests.
- **Alternatives Considered**:
  - Retaining verbose `Field(description=...)` and extensive defensive edge-case handlers.
  - Retaining extensive mock tests verifying SQLAlchemy and Python standard library internals.
- **Reason**: Treats unnecessary code as a maintenance liability. Reduced total codebase by >40% (from ~990 to 567 lines) and cut test execution time while maintaining 100% test pass rate and high readability.

---

## Phase 3: Model Gateway, Guardrails, and Observability

### CD-019: Input Guardrails and Adversarial Prompt Injection Scanning
- **Task**: Task 3.1 — Implement input guardrails in `backend/app/core/guardrails.py`.
- **Choice**: Validate file size (20MB limit) and PDF magic header (`%PDF-`), and scan extracted or pasted text using regex heuristics for adversarial directives.
- **Alternatives Considered**:
  - Running a secondary LLM classifier for prompt injection on every input: Slower, costly, and wastes free API quotas.
  - Relying solely on file extension without header inspection: Easily bypassed by renaming files.
- **Reason**: Regex heuristics provide instantaneous, zero-cost defense against common jailbreak and override patterns without external dependencies.

### CD-020: Deterministic SHA-256 Prompt Caching with In-Memory Fallback
- **Task**: Task 3.3 — Implement prompt caching in `backend/app/core/cache.py`.
- **Choice**: Serialize model name, messages, and parameters into a canonical JSON string and compute a SHA-256 hash. Query Redis and gracefully fall back to an in-memory dictionary if Redis is offline.
- **Alternatives Considered**:
  - Hard requirement on Redis: Causes local development and unit tests to fail if the Redis container is not running.
  - Caching raw prompt strings without model parameters: Causes cache collisions when temperatures or system messages differ.
- **Reason**: SHA-256 keys ensure deterministic cache hits across identical prompts. The in-memory fallback ensures zero setup friction during development.

### CD-021: Exponential Backoff Retries and Provider Fallback Cascade
- **Task**: Tasks 3.2, 3.4, 3.5 — Configure LiteLLM gateway with retries and fallback cascade in `backend/app/core/llm_gateway.py`.
- **Choice**: Retry transient 429 and 5xx errors up to 2 times with exponential delay (`delay = base * 2^attempt`). If retries on the primary model (`gemini-1.5-flash`) fail, cascade to the fallback model (`llama-3.3-70b-versatile`).
- **Alternatives Considered**:
  - Immediate failure on 429: Causes workflow failures during rate spikes on free-tier APIs.
  - Infinite retry loop: Stalls background workflow tasks when a provider experiences extended outages.
- **Reason**: Balances resilience against transient rate spikes while providing seamless fallback to alternative providers.

### CD-022: Langfuse Observability with Paper Text Privacy Masking
- **Task**: Tasks 3.6, 3.7 — Implement Langfuse observability with paper data masking in `backend/app/core/llm_gateway.py`.
- **Choice**: Wrap generation calls with Langfuse context manager (`start_as_current_observation`). Hash and mask long paper excerpts (`[MASKED len=... sha256=...]`) before recording trace inputs and outputs.
- **Alternatives Considered**:
  - Automatic Langfuse callback handlers: Leaks full research paper text to third-party telemetry servers.
  - Omitting tracing completely: Removes latency and token usage visibility in production.
- **Reason**: Protects unpublished paper research from data leakage while giving developers token, latency, and error tracking.

---

## Phase 4: LangGraph Review Workflow Engine

### CD-023: LangGraph Typed State Schema with Component Validation
- **Task**: Task 4.1 — Define state schema in `backend/app/workflows/state.py`.
- **Choice**: Use a `TypedDict` (`ReviewGraphState`) for LangGraph state passing combined with strict Pydantic models (`ChecklistItem`, `ReviewFinding`, `InconsistencyItem`, `OverallAssessment`) for node inputs and outputs.
- **Alternatives Considered**:
  - Pure untyped dictionaries: Prone to missing key errors across graph nodes.
  - Pydantic BaseModel as root graph state: Slower in LangGraph state transitions and serialization.
- **Reason**: Combines LangGraph native TypedDict graph execution with typed Pydantic validation at node boundaries.

### CD-024: Two-Tier Review Taxonomy with Paradigm Inheritance
- **Task**: Tasks 4.2 & 4.3 — Implement classification and checklist generation nodes.
- **Choice**: Use Tier 1 for universal empirical rigor (compute, hyperparameters, datasets, variance, baselines) and Tier 2 for domain-specific criteria based on the classified paradigm (RAG, Agents, Fine-Tuning, etc.).
- **Alternatives Considered**:
  - One generic checklist for all papers: Misses critical domain details (e.g., chunk size in RAG).
  - Completely custom unconstrained checklists: Generates arbitrary or irrelevant criteria.
- **Reason**: Guarantees standard scientific rigor across all empirical AI papers while evaluating domain-specific contributions.

### CD-025: Human-in-the-Loop Interrupt Pattern for Checklist Approval
- **Task**: Task 4.4 — Implement checklist approval pause in `backend/app/workflows/nodes/approval.py`.
- **Choice**: Use `langgraph.types.interrupt()` to pause workflow execution, and resume via `Command(resume=approved_checklist)`.
- **Alternatives Considered**:
  - Splitting the workflow into two disconnected StateGraphs: Requires duplicate session retrieval logic and manual state synchronization.
  - Polling a database table within a synchronous loop: Wastes compute resources and blocks worker threads.
- **Reason**: Native LangGraph `interrupt()` pauses execution cleanly, saves state to the checkpointer, and allows immediate resumption when user approval arrives.

### CD-026: Grounded Evidence Extraction and Pasted Text Scoping
- **Task**: Tasks 4.5 & 4.6 — Implement review and cross-section inconsistency nodes.
- **Choice**: Require verbatim quotes for `MET` and `INCOMPLETE` findings. Automatically skip cross-section inconsistency checks when only methodology text is submitted (`PASTED_TEXT`).
- **Alternatives Considered**:
  - Synthesizing paraphrased quotes: Risks hallucinating details not stated in the paper.
  - Forcing cross-section checks on single-section inputs: Causes false positive discrepancies.
- **Reason**: Protects review truthfulness by ensuring every finding is backed by verbatim paper excerpts, and gracefully scopes checks when input is limited.

### CD-027: Qualitative Assessment Synthesizer without Numerical Scoring
- **Task**: Task 4.7 — Implement assessment node in `backend/app/workflows/nodes/assessment.py`.
- **Choice**: Constrain the overall assessment to three qualitative labels (`Well documented`, `Partially documented`, `Insufficiently documented`) with strengths and critical gaps.
- **Alternatives Considered**:
  - Computing a numerical score (e.g., 0-100 or percentage): Gives a misleading impression of precision and scientific validity.
- **Reason**: Follows project guidelines (PROJECT.md section 6.5) by focusing on descriptive reporting completeness rather than subjective numeric grading.

---

## Phase 5: FastAPI Backend Endpoints

### CD-028: Clean Dependency Injection for Sessions and Services
- **Task**: Task 5.1 — Implement dependency providers in `backend/app/api/deps.py`.
- **Choice**: Use standard FastAPI `Depends()` for database sessions, `StorageInterface`, `ExtractorInterface`, and `WorkflowService`.
- **Alternatives Considered**:
  - Global variable imports inside route handlers: Makes unit and integration test mocking cumbersome.
  - Complex dependency containers (e.g., dependency-injector): Unnecessary abstraction overhead for a focused service layer.
- **Reason**: Standard FastAPI dependencies enable seamless override during testing (`app.dependency_overrides`) while maintaining clean separation of concerns.

### CD-029: BackgroundTasks Workflow Progression without Heavy Task Queues
- **Task**: Tasks 5.2 & 5.3 — Coordinate workflow state machine from REST endpoints.
- **Choice**: Dispatch workflow stages (`execute_initial_phase` and `resume_with_approval`) using FastAPI's built-in `BackgroundTasks`.
- **Alternatives Considered**:
  - Introducing Celery or RabbitMQ: Adds substantial operational complexity and broker dependencies before real production scale justifies it.
  - Running workflow steps synchronously inside HTTP request handlers: Causes client HTTP request timeouts during multi-page LLM reviews.
- **Reason**: `BackgroundTasks` returns HTTP 201 immediately while executing the LangGraph review in the background, minimizing code liability and operational overhead.

### CD-030: Boundary Guardrails and Multi-Input Validation
- **Task**: Tasks 5.2 & 5.3 — Validate PDF uploads and pasted methodology submissions.
- **Choice**: Perform size, format, magic bytes, and adversarial prompt injection validation at the route boundary before persisting or running extraction.
- **Alternatives Considered**:
  - Checking security guardrails inside LangGraph nodes: Wastes storage I/O and creates unnecessary database records for invalid or malicious inputs.
- **Reason**: Fails fast at the API perimeter with clear HTTP 400 errors, protecting background workflows from malformed or hostile payloads.

### CD-031: NullPool Asyncpg Configuration for Multi-Loop Testing and Local Dev
- **Task**: Task 5.6 — Configure SQLAlchemy engine pool class in `app/core/database.py`.
- **Choice**: Automatically select `NullPool` when `APP_ENV` is `"testing"` or `"development"`.
- **Alternatives Considered**:
  - Forcing manual connection closing across every test function: Brittle and prone to regressions when new tests are added.
  - Using synchronous SQLite for tests: Diverges from PostgreSQL native JSONB and Uuid types.
- **Reason**: Prevents `RuntimeError: got Future attached to a different loop` when function-scoped async pytest loops close, while retaining identical PostgreSQL dialect behavior.

---

## Phase 6: Backend Multi-Level DeepEval Test Suite

*(Entries will be added as each Phase 6 task is implemented.)*

---

## Phase 7: Frontend Setup and User Interface

*(Entries will be added as each Phase 7 task is implemented.)*

---

## Phase 8: End-to-End Verification and Documentation

*(Entries will be added as each Phase 8 task is implemented.)*
