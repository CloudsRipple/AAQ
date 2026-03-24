from __future__ import annotations

import asyncio
from dataclasses import dataclass
import threading
import time
from typing import Any, Callable

from .config import AppConfig, RuntimeProfile


@dataclass(frozen=True)
class LLMGatewaySettings:
    base_url: str
    api_key: str
    local_model: str
    cloud_model: str
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float
    rate_limit_per_second: float

    @classmethod
    def from_app_config(cls, config: AppConfig) -> "LLMGatewaySettings":
        return cls(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            local_model=config.llm_local_model,
            cloud_model=config.llm_cloud_model,
            timeout_seconds=config.llm_timeout_seconds,
            max_retries=config.llm_max_retries,
            backoff_seconds=config.llm_backoff_seconds,
            rate_limit_per_second=config.llm_rate_limit_per_second,
        )

    def resolve_model(self, profile: RuntimeProfile) -> str:
        if profile == RuntimeProfile.CLOUD:
            return self.cloud_model
        return self.local_model

    def is_configured(self) -> bool:
        return bool(self.base_url.strip())


class RateLimiter:
    def __init__(
        self,
        permits_per_second: float,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        normalized = permits_per_second if permits_per_second > 0 else 1e9
        self._interval = 1.0 / normalized
        self._clock = clock or time.monotonic
        self._sleeper = sleeper or time.sleep
        self._next_allowed = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = self._clock()
            if self._next_allowed <= 0:
                self._next_allowed = now
            wait_seconds = self._next_allowed - now
            if wait_seconds > 0:
                self._sleeper(wait_seconds)
                now = self._clock()
            self._next_allowed = max(now, self._next_allowed) + self._interval


class UnifiedLLMGateway:
    def __init__(
        self,
        settings: LLMGatewaySettings,
        profile: RuntimeProfile,
        client_factory: Callable[[], Any] | None = None,
        limiter: RateLimiter | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._settings = settings
        self._profile = profile
        self._model = settings.resolve_model(profile)
        self._client_factory = client_factory or self._build_client
        self._client = self._client_factory()
        self._limiter = limiter or RateLimiter(settings.rate_limit_per_second)
        self._sleeper = sleeper or time.sleep
        self._async_lock = asyncio.Lock()

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._settings.base_url

    def generate(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 256,
        model: str | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return self._chat(messages, temperature=temperature, max_tokens=max_tokens, model=model)

    def check_connectivity(self) -> dict[str, Any]:
        started = time.monotonic()
        text = self.generate(
            user_prompt="请仅回复 pong",
            system_prompt="你是联通探活助手，只能返回一个单词。",
            temperature=0.0,
            max_tokens=8,
        )
        latency_ms = round((time.monotonic() - started) * 1000, 3)
        return {
            "ok": True,
            "base_url": self.base_url,
            "model": self.model,
            "latency_ms": latency_ms,
            "reply": text.strip(),
        }

    async def async_generate(
        self,
        user_prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 256,
        model: str | None = None,
    ) -> str:
        async with self._async_lock:
            return await asyncio.to_thread(
                self.generate,
                user_prompt,
                system_prompt,
                temperature,
                max_tokens,
                model,
            )

    def _chat(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> str:
        attempt = 0
        while True:
            self._limiter.acquire()
            try:
                response = self._client.chat.completions.create(
                    model=model or self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content
                if content is None:
                    return ""
                return str(content)
            except Exception as exc:
                if attempt >= self._settings.max_retries or not _is_retryable_exception(exc):
                    raise
                delay = self._settings.backoff_seconds * (2**attempt)
                self._sleeper(delay)
                attempt += 1

    def _build_client(self) -> Any:
        from openai import OpenAI

        return OpenAI(
            base_url=self._settings.base_url,
            api_key=self._settings.api_key,
            timeout=self._settings.timeout_seconds,
        )


def build_optional_gateway(
    *,
    settings: LLMGatewaySettings,
    profile: RuntimeProfile,
    client_factory: Callable[[], Any] | None = None,
    limiter: RateLimiter | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> UnifiedLLMGateway | None:
    if not settings.is_configured():
        return None
    try:
        return UnifiedLLMGateway(
            settings=settings,
            profile=profile,
            client_factory=client_factory,
            limiter=limiter,
            sleeper=sleeper,
        )
    except Exception:
        return None


def _is_retryable_exception(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {408, 409, 429, 500, 502, 503, 504}:
        return True
    name = exc.__class__.__name__
    return name in {
        "APIConnectionError",
        "APITimeoutError",
        "RateLimitError",
        "InternalServerError",
    }
