"""Unit tests for LLM Gateway, prompt caching, retries, and fallback cascade."""

from unittest.mock import AsyncMock, MagicMock, patch
import litellm
import pytest
from app.core.cache import cache_service, compute_cache_key
from app.core.llm_gateway import (
    GatewayResponse,
    LLMGateway,
    LLMGatewayError,
    mask_messages,
    mask_paper_content,
)


@pytest.fixture(autouse=True)
async def clear_cache_before_each_test() -> None:
    """Clear memory cache before every test execution."""
    await cache_service.clear()


def _create_mock_completion(content: str, model: str = "test-model") -> MagicMock:
    """Helper creating a mock LiteLLM completion response object."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp.choices = [mock_choice]
    mock_resp.model = model

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 15
    mock_usage.completion_tokens = 25
    mock_usage.total_tokens = 40
    mock_resp.usage = mock_usage
    return mock_resp


def test_mask_paper_content() -> None:
    """Verify that short text is unmasked while long content is hashed and summarized."""
    short_text = "Brief summary text."
    assert mask_paper_content(short_text) == short_text

    long_text = "Methodology section describing dataset: " + ("A" * 300)
    masked = mask_paper_content(long_text)
    assert "[MASKED len=" in masked
    assert "sha256=" in masked
    assert "Methodology" in masked


def test_mask_messages() -> None:
    """Verify that conversation messages have their content sanitized."""
    messages = [
        {"role": "system", "content": "You are a reviewer."},
        {"role": "user", "content": "Paper text: " + ("X" * 400)},
    ]
    masked = mask_messages(messages)
    assert len(masked) == 2
    assert masked[0]["content"] == "You are a reviewer."
    assert "[MASKED" in masked[1]["content"]


def test_compute_cache_key_deterministic() -> None:
    """Verify that identical model and message inputs generate the exact same hash."""
    messages = [{"role": "user", "content": "Analyze methodology"}]
    key1 = compute_cache_key("gemini/gemini-1.5-flash", messages, temperature=0.0)
    key2 = compute_cache_key("gemini/gemini-1.5-flash", messages, temperature=0.0)
    key_diff = compute_cache_key("gemini/gemini-1.5-flash", messages, temperature=0.7)

    assert key1 == key2
    assert key1 != key_diff


async def test_cache_service_set_and_get() -> None:
    """Verify setting and getting items through CacheService."""
    key = "test_sha_key"
    assert await cache_service.get(key) is None

    await cache_service.set(key, "cached review text")
    assert await cache_service.get(key) == "cached review text"

    await cache_service.clear()
    assert await cache_service.get(key) is None


async def test_complete_returns_cached_response_without_llm_call() -> None:
    """Verify gateway returns cached content on cache hit without invoking LiteLLM."""
    gateway = LLMGateway(primary_model="gemini/gemini-1.5-flash")
    messages = [{"role": "user", "content": "Test prompt"}]

    # Seed the cache
    key = compute_cache_key("gemini/gemini-1.5-flash", messages, temperature=0.0)
    await cache_service.set(key, "Existing cached analysis")

    with patch("litellm.acompletion") as mock_acompletion:
        response = await gateway.complete(messages, use_cache=True)

        assert response.content == "Existing cached analysis"
        assert response.cached is True
        mock_acompletion.assert_not_called()


async def test_complete_invokes_primary_model_on_cache_miss() -> None:
    """Verify gateway calls LiteLLM and caches result on cache miss."""
    gateway = LLMGateway(primary_model="gemini/gemini-1.5-flash")
    messages = [{"role": "user", "content": "Analyze RAG architecture"}]

    mock_resp = _create_mock_completion("Methodology is well documented.")

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.return_value = mock_resp

        response = await gateway.complete(messages, use_cache=True)

        assert response.content == "Methodology is well documented."
        assert response.model == "gemini/gemini-1.5-flash"
        assert response.cached is False
        assert response.total_tokens == 40
        mock_acompletion.assert_called_once()

        # Verify response was cached
        key = compute_cache_key("gemini/gemini-1.5-flash", messages, temperature=0.0)
        assert await cache_service.get(key) == "Methodology is well documented."


async def test_retry_on_rate_limit_recovers() -> None:
    """Verify that transient 429 RateLimitError retries with backoff and succeeds."""
    gateway = LLMGateway(primary_model="gemini/gemini-1.5-flash")
    messages = [{"role": "user", "content": "Review"}]

    success_resp = _create_mock_completion("Review completed after retry")
    rate_limit_error = litellm.RateLimitError(
        message="Rate limit reached", model="gemini/gemini-1.5-flash", llm_provider="gemini"
    )

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = [rate_limit_error, success_resp]

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            response = await gateway.complete(messages, use_cache=False)

            assert response.content == "Review completed after retry"
            assert mock_acompletion.call_count == 2
            mock_sleep.assert_called_once()


async def test_fallback_cascade_when_primary_model_exhausts_retries() -> None:
    """Verify fallback model is called when primary model encounters persistent failures."""
    gateway = LLMGateway(
        primary_model="gemini/gemini-1.5-flash",
        fallback_model="groq/llama-3.3-70b-versatile",
    )
    messages = [{"role": "user", "content": "Review"}]

    primary_error = litellm.InternalServerError(
        message="Gemini 500 error", model="gemini/gemini-1.5-flash", llm_provider="gemini"
    )
    fallback_resp = _create_mock_completion(
        "Fallback model completed review", model="groq/llama-3.3-70b-versatile"
    )

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        # Primary fails (3 attempts: initial + 2 retries), then fallback succeeds on first attempt
        mock_acompletion.side_effect = [
            primary_error,
            primary_error,
            primary_error,
            fallback_resp,
        ]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            response = await gateway.complete(messages, use_cache=False)

            assert response.content == "Fallback model completed review"
            assert response.model == "groq/llama-3.3-70b-versatile"
            assert mock_acompletion.call_count == 4


async def test_llm_gateway_error_when_both_fail() -> None:
    """Verify LLMGatewayError is raised when both primary and fallback models fail."""
    gateway = LLMGateway(
        primary_model="gemini/gemini-1.5-flash",
        fallback_model="groq/llama-3.3-70b-versatile",
    )
    messages = [{"role": "user", "content": "Review"}]

    outage_error = litellm.APIConnectionError(
        message="Network outage", model="test", llm_provider="test"
    )

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = outage_error

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(LLMGatewayError) as exc_info:
                await gateway.complete(messages, use_cache=False)

            assert "Both primary model" in str(exc_info.value)
            assert "and fallback model" in str(exc_info.value)


def test_observe_generation_records_span_with_langfuse() -> None:
    """Verify observe_generation starts a generation span with masked inputs when Langfuse is present."""
    from app.core.llm_gateway import observe_generation

    mock_client = MagicMock()
    mock_span = MagicMock()
    mock_client.start_as_current_observation.return_value.__enter__.return_value = mock_span

    messages = [{"role": "user", "content": "Sensitive paper text: " + ("Z" * 300)}]

    with patch("app.core.llm_gateway.get_langfuse_client", return_value=mock_client):
        with observe_generation(
            name="review_generation",
            model="gemini/gemini-1.5-flash",
            input_messages=messages,
            metadata={"source": "test"},
        ) as span:
            assert span is mock_span

    mock_client.start_as_current_observation.assert_called_once()
    kwargs = mock_client.start_as_current_observation.call_args.kwargs
    assert kwargs["name"] == "review_generation"
    assert kwargs["as_type"] == "generation"
    assert kwargs["model"] == "gemini/gemini-1.5-flash"
    assert "[MASKED" in kwargs["input"][0]["content"]
