from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCode(str, Enum):
    CONFIG_INVALID_PROFILE = "CONFIG_INVALID_PROFILE"
    CONFIG_INVALID_VALUE = "CONFIG_INVALID_VALUE"
    CONNECTIVITY_UNREACHABLE = "CONNECTIVITY_UNREACHABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass
class AppError(Exception):
    code: ErrorCode
    message: str

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
