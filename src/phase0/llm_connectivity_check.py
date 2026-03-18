from __future__ import annotations

import argparse
from dataclasses import replace
import json
from typing import Any

from .config import RuntimeProfile, load_config
from .errors import ErrorCode
from .llm_gateway import LLMGatewaySettings, UnifiedLLMGateway


def run_llm_probe(
    profile: RuntimeProfile | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    local_model: str | None = None,
    cloud_model: str | None = None,
) -> dict[str, Any]:
    config = load_config()
    active_profile = profile or config.runtime_profile
    settings = LLMGatewaySettings.from_app_config(config)
    settings = replace(
        settings,
        base_url=base_url or settings.base_url,
        api_key=api_key or settings.api_key,
        local_model=local_model or settings.local_model,
        cloud_model=cloud_model or settings.cloud_model,
    )
    report: dict[str, Any] = {
        "kind": "llm_connectivity_probe",
        "profile": active_profile.value,
        "base_url": settings.base_url,
        "model": settings.resolve_model(active_profile),
    }
    try:
        gateway = UnifiedLLMGateway(settings=settings, profile=active_profile)
        report["model"] = gateway.model
        outcome = gateway.check_connectivity()
        report.update(outcome)
    except Exception as exc:
        report["ok"] = False
        report["error"] = exc.__class__.__name__
        report["error_type"] = exc.__class__.__name__
        report["error_code"] = ErrorCode.INTERNAL_ERROR.value
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="phase0-llm-check")
    parser.add_argument("--profile", choices=[p.value for p in RuntimeProfile], default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--local-model", default=None)
    parser.add_argument("--cloud-model", default=None)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    profile = RuntimeProfile(args.profile) if args.profile else None
    report = run_llm_probe(
        profile=profile,
        base_url=args.base_url,
        api_key=args.api_key,
        local_model=args.local_model,
        cloud_model=args.cloud_model,
    )
    print(json.dumps(report, ensure_ascii=False))
    if report.get("ok"):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
