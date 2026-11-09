"""Model gateway service providing unified LLM access with caching, retries, and fallback.

Integrates LiteLLM for routing free-tier Gemini and Groq models, Redis prompt caching,
exponential backoff retry for rate limits, fallback cascade, and masked Langfuse observability.
"""

import asyncio
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import logging
import os
from typing import Any
import litellm
from pydantic import BaseModel
from app.config import get_settings
from app.core.cache import cache_service, compute_cache_key

# Prevent LiteLLM from attempting external cost map HTTP calls and telemetry
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
litellm.telemetry = False

logger = logging.getLogger(__name__)
settings = get_settings()

# Retryable exception types (rate limits, server errors, transient timeouts)
RETRYABLE_EXCEPTIONS = (
    litellm.RateLimitError,
    litellm.InternalServerError,
    litellm.APIConnectionError,
    litellm.Timeout,
)


class GatewayResponse(BaseModel):
    """Structured response container returned by the model gateway."""

    content: str
    model: str
    cached: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMGatewayError(Exception):
    """Raised when all configured models and fallbacks fail."""
    pass


def mask_paper_content(content: str, max_chars: int = 150) -> str:
    """Mask paper text before external tracing to prevent leaking sensitive paper excerpts.

    Args:
        content: Raw message text string.
        max_chars: Maximum characters before content is masked with SHA-256 fingerprint.

    Returns:
        str: Masked string safe for observability traces.
    """
    if len(content) <= max_chars:
        return content

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    preview = content[:80].replace("\n", " ").strip()
    return f"{preview}... [MASKED len={len(content)} sha256={content_hash}]"


def mask_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a masked copy of conversation messages safe for telemetry logging."""
    return [
        {
            "role": msg.get("role", "user"),
            "content": mask_paper_content(str(msg.get("content", ""))),
        }
        for msg in messages
    ]


@lru_cache(maxsize=1)
def get_langfuse_client() -> Any | None:
    """Return Langfuse client if API keys are configured, otherwise None."""
    pub_key = os.environ.get("LANGFUSE_PUBLIC_KEY", settings.LANGFUSE_PUBLIC_KEY)
    sec_key = os.environ.get("LANGFUSE_SECRET_KEY", settings.LANGFUSE_SECRET_KEY)
    if pub_key and sec_key:
        try:
            from langfuse import Langfuse
            return Langfuse(
                public_key=pub_key,
                secret_key=sec_key,
                host=settings.LANGFUSE_HOST,
            )
        except Exception as exc:
            logger.warning("Failed to initialize Langfuse client: %s", exc)
            return None
    return None


@contextmanager
def observe_generation(
    name: str,
    model: str,
    input_messages: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
):
    """Context manager wrapping LLM generation in Langfuse observation if available.

    Uses `start_as_current_observation` and sanitizes paper inputs to protect privacy.
    """
    client = get_langfuse_client()
    if client:
        with client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=mask_messages(input_messages),
            metadata=metadata or {},
        ) as span:
            yield span
    else:
        yield None


class LLMGateway:
    """Unified LLM gateway managing routing, caching, retries, and fallbacks."""

    def __init__(
        self,
        primary_model: str | None = None,
        fallback_model: str | None = None,
    ) -> None:
        self.primary_model = primary_model or settings.PRIMARY_MODEL
        self.fallback_model = fallback_model or settings.FALLBACK_MODEL

        # Configure provider API keys
        if settings.GEMINI_API_KEY:
            os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
        if settings.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

    async def _invoke_with_retry(
        self,
        model: str,
        messages: list[dict[str, Any]],
        max_retries: int = 2,
        base_delay: float = 0.5,
        **kwargs: Any,
    ) -> Any:
        """Execute model completion with exponential backoff on retryable errors."""
        for attempt in range(max_retries + 1):
            try:
                return await litellm.acompletion(
                    model=model,
                    messages=messages,
                    **kwargs,
                )
            except RETRYABLE_EXCEPTIONS as exc:
                if attempt == max_retries:
                    logger.error("Model %s exhausted %d retries: %s", model, max_retries, exc)
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(
                    "Model %s failed with %s. Retrying in %.2fs (attempt %d/%d)...",
                    model,
                    type(exc).__name__,
                    delay,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(delay)

    async def complete(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        fallback_model: str | None = None,
        use_cache: bool = True,
        temperature: float = 0.0,
        span_name: str = "llm_completion",
        **kwargs: Any,
    ) -> GatewayResponse:
        """Request completion from the model gateway with caching and fallback.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            model: Optional model override; defaults to primary model.
            fallback_model: Optional fallback model override.
            use_cache: Whether to check and populate the prompt cache.
            temperature: Sampling temperature.
            span_name: Observability trace label.
            **kwargs: Extra parameters passed to LiteLLM.

        Returns:
            GatewayResponse: Structured response containing text and usage diagnostics.

        Raises:
            LLMGatewayError: If both primary and fallback model invocations fail.
        """
        primary = model or self.primary_model
        fallback = fallback_model or self.fallback_model

        # 1. Check prompt cache
        cache_key = compute_cache_key(primary, messages, temperature=temperature, **kwargs)
        if use_cache:
            cached_text = await cache_service.get(cache_key)
            if cached_text is not None:
                return GatewayResponse(
                    content=cached_text,
                    model=primary,
                    cached=True,
                )

        # 2. Invoke primary model inside masked observability span
        with observe_generation(
            name=span_name,
            model=primary,
            input_messages=messages,
            metadata={"temperature": temperature, "fallback": fallback},
        ) as span:
            response_obj = None
            resolved_model = primary

            try:
                response_obj = await self._invoke_with_retry(
                    primary, messages, temperature=temperature, **kwargs
                )
            except Exception as primary_exc:
                logger.warning(
                    "Primary model %s failed: %s. Activating fallback cascade to %s...",
                    primary,
                    primary_exc,
                    fallback,
                )
                try:
                    resolved_model = fallback
                    response_obj = await self._invoke_with_retry(
                        fallback, messages, temperature=temperature, **kwargs
                    )
                except Exception as fallback_exc:
                    logger.error("Fallback model %s also failed: %s", fallback, fallback_exc)
                    raise LLMGatewayError(
                        f"Both primary model ({primary}) and fallback model ({fallback}) failed. "
                        f"Primary error: {primary_exc}; Fallback error: {fallback_exc}"
                    ) from fallback_exc

            # Extract generated content and token usage
            content = response_obj.choices[0].message.content or ""
            usage = getattr(response_obj, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", prompt_tokens + completion_tokens) if usage else 0

            # Attach output to Langfuse span if active
            if span and hasattr(span, "update"):
                try:
                    span.update(output=mask_paper_content(content))
                except Exception:
                    pass

            # 3. Save to prompt cache
            if use_cache:
                await cache_service.set(cache_key, content)

            return GatewayResponse(
                content=content,
                model=resolved_model,
                cached=False,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )


# Singleton gateway instance
llm_gateway = LLMGateway()
