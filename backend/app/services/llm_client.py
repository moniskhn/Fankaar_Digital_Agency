"""
Fankaar Digital — LLM Client
Unified interface for Ollama, Anthropic, and OpenAI with fallback chain.
"""

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings


class LLMResponse:
    """Standardized LLM response wrapper."""

    def __init__(
        self,
        text: str,
        provider: str,
        model: str,
        latency_ms: float,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.text = text
        self.provider = provider
        self.model = model
        self.latency_ms = latency_ms
        self.tokens_used = tokens_used
        self.metadata = metadata or {}


class LLMClient:
    """Unified LLM client with provider fallback."""

    def __init__(self):
        self.provider = settings.llm_provider
        self.fallback_chain = settings.llm_fallback_chain

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        structured_output: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a completion request with automatic fallback.

        Args:
            prompt: The user prompt
            system: Optional system message
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            structured_output: JSON schema for structured output

        Returns:
            LLMResponse with standardized fields
        """
        temp = temperature if temperature is not None else settings.llm_temperature
        max_tok = max_tokens if max_tokens is not None else settings.llm_max_tokens

        errors = {}
        attempted_providers = []
        for provider in self.fallback_chain:
            try:
                if provider == "ollama":
                    # Only try Ollama if it's the primary provider or if in development
                    if settings.llm_provider != "ollama" and settings.app_env != "development":
                        continue
                    attempted_providers.append(provider)
                    return await self._call_ollama(prompt, system, temp, max_tok, structured_output)
                elif provider == "anthropic":
                    if not settings.anthropic_api_key:
                        continue
                    attempted_providers.append(provider)
                    return await self._call_anthropic(prompt, system, temp, max_tok, structured_output)
                elif provider == "openai":
                    if not settings.openai_api_key:
                        continue
                    attempted_providers.append(provider)
                    return await self._call_openai(prompt, system, temp, max_tok, structured_output)
                elif provider == "moonshot":
                    if not settings.moonshot_api_key:
                        continue
                    attempted_providers.append(provider)
                    return await self._call_moonshot(prompt, system, temp, max_tok, structured_output)
            except Exception as e:
                error_detail = f"{type(e).__name__}: {str(e)}"
                errors[provider] = error_detail
                continue

        # All providers failed
        if not attempted_providers:
            missing_vars = []
            if not settings.moonshot_api_key: missing_vars.append("MOONSHOT_API_KEY")
            if not settings.anthropic_api_key: missing_vars.append("ANTHROPIC_API_KEY")
            if not settings.openai_api_key: missing_vars.append("OPENAI_API_KEY")

            error_msg = f"No LLM providers are configured. Missing variables: {', '.join(missing_vars)}. Please check your .env file."
        else:
            error_details = "; ".join([f"{p}: {err}" for p, err in errors.items()])
            error_msg = f"All attempted LLM providers ({', '.join(attempted_providers)}) failed. Details: {error_details}"
        return LLMResponse(
            text=f"Error: {error_msg}. Please check your LLM configuration.",
            provider="none",
            model="error",
            latency_ms=0.0,
        )

    async def _call_ollama(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Call local Ollama instance."""
        url = f"http://{settings.ollama_host}/api/generate"

        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": settings.ollama_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if structured_output:
            payload["format"] = "json"

        start = time.time()
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        text = data.get("response", "").strip()

        # Try to parse JSON if structured output was requested
        if structured_output and text:
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed)
            except json.JSONDecodeError:
                pass

        return LLMResponse(
            text=text,
            provider="ollama",
            model=settings.ollama_model,
            latency_ms=latency,
            tokens_used=data.get("eval_count", 0),
        )

    async def _call_anthropic(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Call Anthropic Claude API."""
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        content = [{"type": "text", "text": prompt}]

        payload: Dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": content}],
        }

        if system:
            payload["system"] = system

        start = time.time()
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = data.get("usage", {})

        return LLMResponse(
            text=text.strip(),
            provider="anthropic",
            model=settings.anthropic_model,
            latency_ms=latency,
            tokens_used=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        )

    async def _call_openai(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Call OpenAI API."""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if structured_output:
            payload["response_format"] = {"type": "json_object"}

        start = time.time()
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        choice = data.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "").strip()

        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            provider="openai",
            model=settings.openai_model,
            latency_ms=latency,
            tokens_used=usage.get("total_tokens", 0),
        )

    async def _call_moonshot(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Call Moonshot (Kimi) API — OpenAI-compatible."""
        if not settings.moonshot_api_key:
            raise ValueError("Moonshot API key not configured")

        url = f"{settings.moonshot_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.moonshot_api_key}",
            "Content-Type": "application/json",
        }

        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": settings.moonshot_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if structured_output:
            payload["response_format"] = {"type": "json_object"}

        start = time.time()
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        choice = data.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "").strip()

        usage = data.get("usage", {})

        return LLMResponse(
            text=text,
            provider="moonshot",
            model=settings.moonshot_model,
            latency_ms=latency,
            tokens_used=usage.get("total_tokens", 0),
        )

    async def check_health(self) -> Dict[str, Any]:
        """Check if the primary LLM provider is available."""
        try:
            resp = await self.complete("Say 'OK' and nothing else.", max_tokens=10, temperature=0)
            return {
                "provider": resp.provider,
                "model": resp.model,
                "available": resp.provider != "none",
                "latency_ms": resp.latency_ms,
            }
        except Exception as e:
            return {
                "provider": self.provider,
                "available": False,
                "error": str(e),
            }


# Global instance
llm_client = LLMClient()
