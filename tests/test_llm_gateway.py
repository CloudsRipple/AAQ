from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phase0.config import RuntimeProfile
from phase0.llm_gateway import LLMGatewaySettings, RateLimiter, UnifiedLLMGateway


class RetryableError(Exception):
    status_code = 429


class NonRetryableError(Exception):
    status_code = 400


class FakeCompletions:
    def __init__(self, outcomes: list[object]) -> None:
        self._outcomes = outcomes
        self.calls = 0

    def create(self, **_: object) -> object:
        self.calls += 1
        outcome = self._outcomes[self.calls - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeChat:
    def __init__(self, completions: FakeCompletions) -> None:
        self.completions = completions


class FakeClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.chat = FakeChat(FakeCompletions(outcomes))


class FakeResponse:
    def __init__(self, text: str) -> None:
        message = type("Message", (), {"content": text})
        choice = type("Choice", (), {"message": message()})
        self.choices = [choice()]


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class LLMGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = LLMGatewaySettings(
            base_url="http://localhost:11434/v1",
            api_key="dummy",
            local_model="llama3.1:8b",
            cloud_model="gpt-4o-mini",
            timeout_seconds=20.0,
            max_retries=2,
            backoff_seconds=0.1,
            rate_limit_per_second=100.0,
        )

    def test_uses_local_model_for_non_cloud_profile(self) -> None:
        gateway = UnifiedLLMGateway(
            settings=self.settings,
            profile=RuntimeProfile.LOCAL,
            client_factory=lambda: FakeClient([FakeResponse("ok")]),
        )
        self.assertEqual("llama3.1:8b", gateway.model)

    def test_retries_on_retryable_error_and_succeeds(self) -> None:
        sleep_calls: list[float] = []
        gateway = UnifiedLLMGateway(
            settings=self.settings,
            profile=RuntimeProfile.CLOUD,
            client_factory=lambda: FakeClient([RetryableError("busy"), FakeResponse("pong")]),
            sleeper=lambda seconds: sleep_calls.append(seconds),
        )
        result = gateway.generate("hello")
        self.assertEqual("pong", result)
        self.assertEqual([0.1], sleep_calls)

    def test_raises_without_retry_for_non_retryable_error(self) -> None:
        gateway = UnifiedLLMGateway(
            settings=self.settings,
            profile=RuntimeProfile.CLOUD,
            client_factory=lambda: FakeClient([NonRetryableError("bad request")]),
        )
        with self.assertRaises(NonRetryableError):
            gateway.generate("hello")

    def test_rate_limiter_waits_for_next_permit(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(permits_per_second=2.0, clock=clock, sleeper=clock.sleep)
        limiter.acquire()
        limiter.acquire()
        self.assertAlmostEqual(0.5, clock.now)


if __name__ == "__main__":
    unittest.main()
