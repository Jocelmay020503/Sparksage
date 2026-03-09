from __future__ import annotations

import time
from typing import Any
from openai import OpenAI
import config


def _create_client(provider_name: str) -> OpenAI | None:
    """Create an OpenAI-compatible client for the given provider."""
    provider = config.PROVIDERS.get(provider_name)
    if not provider or not provider["api_key"]:
        return None

    extra_headers = {}
    if provider_name == "anthropic":
        extra_headers["anthropic-version"] = "2023-06-01"

    return OpenAI(
        base_url=provider["base_url"],
        api_key=provider["api_key"],
        default_headers=extra_headers or None,
    )


def _build_fallback_order() -> list[str]:
    """Build the provider fallback order: primary first, then free providers."""
    primary = config.AI_PROVIDER
    order = [primary]
    for name in config.FREE_FALLBACK_CHAIN:
        if name not in order:
            order.append(name)
    return order


def _build_clients() -> dict[str, OpenAI]:
    """Build clients for all configured providers."""
    clients = {}
    for name in set([config.AI_PROVIDER] + config.FREE_FALLBACK_CHAIN + list(config.PROVIDERS.keys())):
        client = _create_client(name)
        if client:
            clients[name] = client
    return clients


# Pre-build clients for all configured providers
_clients: dict[str, OpenAI] = _build_clients()
FALLBACK_ORDER = _build_fallback_order()


def reload_clients():
    """Rebuild all clients and fallback order from current config."""
    global _clients, FALLBACK_ORDER
    _clients = _build_clients()
    FALLBACK_ORDER = _build_fallback_order()


def get_available_providers() -> list[str]:
    """Return list of provider names that have valid API keys configured."""
    return [name for name in FALLBACK_ORDER if name in _clients]


def _safe_int(value: Any) -> int:
    """Convert provider usage values to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _estimate_tokens(text: str) -> int:
    """Estimate tokens using a conservative 4 chars/token heuristic."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _estimate_prompt_tokens(messages: list[dict], system_prompt: str) -> int:
    """Estimate prompt tokens from system prompt and conversation messages."""
    total_chars = len(system_prompt or "")
    for message in messages:
        total_chars += len(str(message.get("role", "")))
        total_chars += len(str(message.get("content", "")))
    if total_chars <= 0:
        return 0
    return max(1, (total_chars + 3) // 4)


def _extract_usage_metrics(response: Any, messages: list[dict], system_prompt: str, output_text: str) -> dict[str, int]:
    """Extract usage from provider response or fall back to token estimates."""
    usage = getattr(response, "usage", None)
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if usage is not None:
        prompt_tokens = _safe_int(getattr(usage, "prompt_tokens", None))
        completion_tokens = _safe_int(getattr(usage, "completion_tokens", None))
        total_tokens = _safe_int(getattr(usage, "total_tokens", None))

        if isinstance(usage, dict):
            prompt_tokens = prompt_tokens or _safe_int(usage.get("prompt_tokens"))
            completion_tokens = completion_tokens or _safe_int(usage.get("completion_tokens"))
            total_tokens = total_tokens or _safe_int(usage.get("total_tokens"))

    if prompt_tokens <= 0:
        prompt_tokens = _estimate_prompt_tokens(messages, system_prompt)
    if completion_tokens <= 0:
        completion_tokens = _estimate_tokens(output_text)
    if total_tokens <= 0:
        total_tokens = prompt_tokens + completion_tokens

    return {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def test_provider(name: str) -> dict:
    """Test a provider with a minimal API call. Returns {success, latency_ms, error}."""
    provider = config.PROVIDERS.get(name)
    if not provider:
        return {"success": False, "latency_ms": 0, "error": f"Unknown provider: {name}"}

    client = _clients.get(name)
    if not client:
        # Try creating a fresh client in case config was just updated
        client = _create_client(name)
        if not client:
            return {"success": False, "latency_ms": 0, "error": "No API key configured"}

    try:
        start = time.time()
        response = client.chat.completions.create(
            model=provider["model"],
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
        latency = int((time.time() - start) * 1000)
        return {"success": True, "latency_ms": latency, "error": None}
    except Exception as e:
        latency = int((time.time() - start) * 1000)
        return {"success": False, "latency_ms": latency, "error": str(e)}


def chat(
    messages: list[dict],
    system_prompt: str,
    preferred_provider: str | None = None,
    include_usage: bool = False,
) -> tuple[str, str] | tuple[str, str, dict[str, int]]:
    """Send messages to AI and return response text/provider (and optional usage).

    Tries the primary provider first, then falls back through free providers.
    Raises RuntimeError if all providers fail.
    """
    errors = []

    fallback_order = FALLBACK_ORDER
    if preferred_provider and preferred_provider in config.PROVIDERS:
        fallback_order = [preferred_provider] + [p for p in FALLBACK_ORDER if p != preferred_provider]

    for provider_name in fallback_order:
        client = _clients.get(provider_name)
        if not client:
            continue

        provider = config.PROVIDERS[provider_name]
        try:
            response = client.chat.completions.create(
                model=provider["model"],
                max_tokens=config.MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages,
                ],
            )
            text = response.choices[0].message.content or ""
            usage_metrics = _extract_usage_metrics(response, messages, system_prompt, text)
            if include_usage:
                return text, provider_name, usage_metrics
            return text, provider_name

        except Exception as e:
            errors.append(f"{provider['name']}: {e}")
            continue

    error_details = "\n".join(errors)
    raise RuntimeError(f"All providers failed:\n{error_details}")
