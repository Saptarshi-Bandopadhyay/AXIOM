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

---

## Phase 3: Model Gateway, Guardrails, and Observability

*(Entries will be added as each Phase 3 task is implemented.)*

---

## Phase 4: LangGraph Review Workflow Engine

*(Entries will be added as each Phase 4 task is implemented.)*

---

## Phase 5: FastAPI Backend Endpoints

*(Entries will be added as each Phase 5 task is implemented.)*

---

## Phase 6: Backend Multi-Level DeepEval Test Suite

*(Entries will be added as each Phase 6 task is implemented.)*

---

## Phase 7: Frontend Setup and User Interface

*(Entries will be added as each Phase 7 task is implemented.)*

---

## Phase 8: End-to-End Verification and Documentation

*(Entries will be added as each Phase 8 task is implemented.)*
