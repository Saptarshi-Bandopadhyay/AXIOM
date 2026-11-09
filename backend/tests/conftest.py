"""Global test configuration and fixtures."""

import os
import pytest

# Ensure offline test isolation, clean event loops, and opt out of external telemetry
os.environ["APP_ENV"] = "testing"
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
os.environ["LANGFUSE_PUBLIC_KEY"] = ""
os.environ["LANGFUSE_SECRET_KEY"] = ""
os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
