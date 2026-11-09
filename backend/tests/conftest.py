"""Global test configuration and fixtures."""

import os
import pytest

# Ensure offline test isolation
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""
