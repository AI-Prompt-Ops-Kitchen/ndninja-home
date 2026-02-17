"""
Real Multi-LLM Council — async parallel queries to 4 providers via httpx.

Providers: Anthropic, OpenAI, Perplexity, Google Gemini
Retry: 3 attempts on 429/5xx, exponential backoff (tenacity)
Graceful degradation: failed models excluded, council succeeds if >=1 responds.

Usage:
    from lib.llm_council import run_council, council_result_to_daily_review_format

    result = run_council("What is 2+2?")
    for r in result.responses:
        print(f"{r.model}: {r.content[:80]}")

    fmt = council_result_to_daily_review_format(result)
    # {"individual_responses": {"claude-sonnet-4-6": "...", ...}}
"""

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from lib.structured_logger import get_logger

logger = get_logger("llm-council", log_to_stdout=True)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    name: str
    provider: str  # anthropic | openai | perplexity | gemini
    model_id: str
    api_key_env: str
    timeout: float = 60.0
    max_tokens: int = 2048


@dataclass
class ModelResponse:
    model: str
    provider: str
    content: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    latency: float = 0.0
    error: str = ""
    success: bool = False


@dataclass
class CouncilResult:
    responses: list[ModelResponse] = field(default_factory=list)
    total_cost: float = 0.0
    total_latency: float = 0.0
    models_succeeded: int = 0
    models_failed: int = 0


# ---------------------------------------------------------------------------
# Default models
# ---------------------------------------------------------------------------

DEFAULT_MODELS = [
    ModelConfig(
        name="claude-opus-4-6",
        provider="anthropic",
        model_id="claude-opus-4-6",
        api_key_env="ANTHROPIC_API_KEY",
        timeout=120.0,
    ),
    ModelConfig(
        name="gpt-5.2",
        provider="openai",
        model_id="gpt-5.2",
        api_key_env="OPENAI_API_KEY",
        timeout=90.0,
    ),
    ModelConfig(
        name="sonar-reasoning-pro",
        provider="perplexity",
        model_id="sonar-reasoning-pro",
        api_key_env="PERPLEXITY_API_KEY",
    ),
    ModelConfig(
        name="gemini-3-pro",
        provider="gemini",
        model_id="gemini-3-pro-preview",
        api_key_env="GEMINI_API_KEY",
        timeout=90.0,
    ),
]


# ---------------------------------------------------------------------------
# Retryable HTTP exception
# ---------------------------------------------------------------------------

class RetryableHTTPError(Exception):
    """Raised on 429 / 5xx so tenacity retries."""
    pass


def _should_retry_status(status_code: int) -> bool:
    return status_code == 429 or status_code >= 500


# ---------------------------------------------------------------------------
# Provider query functions
# ---------------------------------------------------------------------------

async def _query_anthropic(
    client: httpx.AsyncClient, cfg: ModelConfig, prompt: str, api_key: str
) -> ModelResponse:
    """POST api.anthropic.com/v1/messages"""
    t0 = time.monotonic()
    resp = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": cfg.model_id,
            "max_tokens": cfg.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=cfg.timeout,
    )
    latency = time.monotonic() - t0

    if _should_retry_status(resp.status_code):
        raise RetryableHTTPError(f"Anthropic {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()

    data = resp.json()
    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content += block.get("text", "")

    usage = data.get("usage", {})
    return ModelResponse(
        model=cfg.name,
        provider=cfg.provider,
        content=content,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        latency=latency,
        success=True,
    )


async def _query_openai(
    client: httpx.AsyncClient, cfg: ModelConfig, prompt: str, api_key: str
) -> ModelResponse:
    """POST api.openai.com/v1/chat/completions"""
    t0 = time.monotonic()
    resp = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": cfg.model_id,
            # GPT-5.x requires max_completion_tokens instead of max_tokens
            "max_completion_tokens": cfg.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=cfg.timeout,
    )
    latency = time.monotonic() - t0

    if _should_retry_status(resp.status_code):
        raise RetryableHTTPError(f"OpenAI {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()

    data = resp.json()
    choice = data["choices"][0]
    content = choice.get("message", {}).get("content", "")
    # GPT-5.2 thinking models may wrap output differently
    if not content and "text" in choice:
        content = choice["text"]
    usage = data.get("usage", {})
    return ModelResponse(
        model=cfg.name,
        provider=cfg.provider,
        content=content,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        latency=latency,
        success=True,
    )


async def _query_perplexity(
    client: httpx.AsyncClient, cfg: ModelConfig, prompt: str, api_key: str
) -> ModelResponse:
    """POST api.perplexity.ai/chat/completions (OpenAI-compatible)"""
    t0 = time.monotonic()
    resp = await client.post(
        "https://api.perplexity.ai/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": cfg.model_id,
            "max_tokens": cfg.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=cfg.timeout,
    )
    latency = time.monotonic() - t0

    if _should_retry_status(resp.status_code):
        raise RetryableHTTPError(f"Perplexity {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return ModelResponse(
        model=cfg.name,
        provider=cfg.provider,
        content=content,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        latency=latency,
        success=True,
    )


async def _query_gemini(
    client: httpx.AsyncClient, cfg: ModelConfig, prompt: str, api_key: str
) -> ModelResponse:
    """POST generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"""
    t0 = time.monotonic()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"models/{cfg.model_id}:generateContent?key={api_key}"
    )
    resp = await client.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": cfg.max_tokens},
        },
        timeout=cfg.timeout,
    )
    latency = time.monotonic() - t0

    if _should_retry_status(resp.status_code):
        raise RetryableHTTPError(f"Gemini {resp.status_code}: {resp.text[:200]}")
    resp.raise_for_status()

    data = resp.json()
    content = ""
    for candidate in data.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            content += part.get("text", "")

    usage_meta = data.get("usageMetadata", {})
    return ModelResponse(
        model=cfg.name,
        provider=cfg.provider,
        content=content,
        input_tokens=usage_meta.get("promptTokenCount", 0),
        output_tokens=usage_meta.get("candidatesTokenCount", 0),
        latency=latency,
        success=True,
    )


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

_PROVIDER_FN = {
    "anthropic": _query_anthropic,
    "openai": _query_openai,
    "perplexity": _query_perplexity,
    "gemini": _query_gemini,
}


async def _query_model(
    client: httpx.AsyncClient, cfg: ModelConfig, prompt: str
) -> ModelResponse:
    """Query a single model with retry on transient errors."""
    api_key = os.environ.get(cfg.api_key_env, "")
    if not api_key:
        logger.warning(f"{cfg.name}: {cfg.api_key_env} not set, skipping")
        return ModelResponse(
            model=cfg.name,
            provider=cfg.provider,
            error=f"{cfg.api_key_env} not set",
        )

    fn = _PROVIDER_FN.get(cfg.provider)
    if not fn:
        return ModelResponse(
            model=cfg.name,
            provider=cfg.provider,
            error=f"Unknown provider: {cfg.provider}",
        )

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            retry=retry_if_exception_type((RetryableHTTPError, httpx.ConnectError, httpx.TimeoutException)),
            reraise=True,
        ):
            with attempt:
                logger.info(f"{cfg.name}: querying (attempt {attempt.retry_state.attempt_number})")
                return await fn(client, cfg, prompt, api_key)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.error(f"{cfg.name}: failed after retries — {error_msg}")
        return ModelResponse(
            model=cfg.name,
            provider=cfg.provider,
            error=error_msg,
        )

    # Unreachable, but satisfy type checker
    return ModelResponse(model=cfg.name, provider=cfg.provider, error="Unknown error")


# ---------------------------------------------------------------------------
# Council orchestration
# ---------------------------------------------------------------------------

async def query_council(
    prompt: str,
    models: Optional[list[ModelConfig]] = None,
    timeout: float = 120.0,
) -> CouncilResult:
    """Query all models in parallel, return aggregated result."""
    models = models or DEFAULT_MODELS
    logger.info(f"Council convened with {len(models)} models (timeout={timeout}s)")

    async with httpx.AsyncClient() as client:
        tasks = [_query_model(client, cfg, prompt) for cfg in models]
        try:
            responses = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error(f"Council timed out after {timeout}s")
            responses = [
                ModelResponse(model=cfg.name, provider=cfg.provider, error="Council timeout")
                for cfg in models
            ]

    result = CouncilResult(responses=list(responses))
    for r in result.responses:
        if r.success:
            result.models_succeeded += 1
            result.total_cost += r.cost
            result.total_latency = max(result.total_latency, r.latency)
        else:
            result.models_failed += 1

    logger.info(
        f"Council complete: {result.models_succeeded} succeeded, "
        f"{result.models_failed} failed, {result.total_latency:.1f}s wall time"
    )
    return result


def run_council(
    prompt: str,
    models: Optional[list[ModelConfig]] = None,
    timeout: float = 120.0,
) -> CouncilResult:
    """Synchronous wrapper around query_council."""
    return asyncio.run(query_council(prompt, models, timeout))


# ---------------------------------------------------------------------------
# Format conversion
# ---------------------------------------------------------------------------

def council_result_to_daily_review_format(result: CouncilResult) -> dict:
    """Convert to {"individual_responses": {"model_name": "text", ...}} format."""
    responses = {}
    for r in result.responses:
        if r.success:
            responses[r.model] = r.content
    return {"individual_responses": responses}
