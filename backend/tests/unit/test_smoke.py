"""Smoke tests for the ReproCheck backend environment.

This module verifies that the Python environment, packages, and core
dependencies are imported and configured properly.
"""

import os
# Prevent LiteLLM from attempting remote network calls during testing
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

import importlib.metadata
import fastapi
import sqlalchemy
import asyncpg
import langgraph.graph
import litellm
import pymupdf
import langfuse


def test_core_dependencies_importable() -> None:
    """Verify that all foundational packages can be imported without error.

    Tests imports for web framework (FastAPI), ORM (SQLAlchemy),
    database driver (asyncpg), AI orchestration (LangGraph),
    model gateway (LiteLLM), PDF extraction (pymupdf), and observability (Langfuse).
    """
    assert fastapi.__version__ is not None
    assert sqlalchemy.__version__ is not None
    assert asyncpg.__version__ is not None
    assert importlib.metadata.version("langgraph") is not None
    assert pymupdf.__version__ is not None

    # Verify key classes instantiate or are accessible
    app = fastapi.FastAPI(title="TestApp")
    assert app is not None

    graph_builder = langgraph.graph.StateGraph(dict)
    assert graph_builder is not None
