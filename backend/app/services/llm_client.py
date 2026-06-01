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

        last_error = None
        for provider in self.fallback_chain:
            try:
                if provider == "mock":
                    return await self._call_mock(prompt, system, temp, max_tok, structured_output)
                elif provider == "ollama":
                    return await self._call_ollama(prompt, system, temp, max_tok, structured_output)
                elif provider == "anthropic":
                    return await self._call_anthropic(prompt, system, temp, max_tok, structured_output)
                elif provider == "openai":
                    return await self._call_openai(prompt, system, temp, max_tok, structured_output)
                elif provider == "moonshot":
                    return await self._call_moonshot(prompt, system, temp, max_tok, structured_output)
                elif provider == "kimi":
                    return await self._call_kimi(prompt, system, temp, max_tok, structured_output)
            except Exception as e:
                last_error = e
                continue

        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_error}"
        return LLMResponse(
            text=f"Error: {error_msg}. Please check your LLM configuration.",
            provider="none",
            model="error",
            latency_ms=0.0,
        )

    async def _call_mock(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Mock provider — returns a helpful response without calling any API."""
        import hashlib
        # Generate a deterministic but varied response based on prompt
        seed = hashlib.md5(prompt.encode()).hexdigest()[:4]
        
        responses = [
            "I've received your message and I'm processing it. As CEO of Fankaar Digital, I'll coordinate with the relevant agents to handle this.",
            "Understood. Routing this to the appropriate team member now. I'll update you once I have results.",
            "Acknowledged. Your request is being handled by Tiny's Army. I'll keep you posted on progress.",
            "Received. I'm delegating this task to the best-suited agent. Expect an update shortly.",
            "Copy that. I'm on it — coordinating with the team to get this resolved.",
        ]
        idx = int(seed, 16) % len(responses)
        text = responses[idx]
        
        if structured_output:
            text = json.dumps({"response": text, "status": "ok"})
        
        return LLMResponse(
            text=text,
            provider="mock",
            model="mock-mode",
            latency_ms=50.0,
            tokens_used=0,
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

    async def _call_kimi(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: int,
        structured_output: Optional[Dict[str, Any]],
    ) -> LLMResponse:
        """Call Kimi Code (Anthropic-compatible Messages API, Bearer auth)."""
        if not settings.kimi_api_key:
            raise ValueError("Kimi API key not configured")

        url = settings.kimi_base_url.rstrip("/") + "/v1/messages"
        headers = {
            "Authorization": f"Bearer {settings.kimi_api_key}",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": settings.kimi_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        }
        if system:
            payload["system"] = system

        start = time.time()
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage", {})
        return LLMResponse(
            text=text.strip(),
            provider="kimi",
            model=settings.kimi_model,
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
