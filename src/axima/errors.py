"""AXIMA structured error hierarchy.

All errors are typed, traceable, and carry context.
NEVER use bare `except:` or `except Exception: pass`.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class ErrorCategory(Enum):
    """Classification of error origin."""

    PARSE = auto()
    EVALUATION = auto()
    SECURITY = auto()
    RESOURCE = auto()
    CAPABILITY = auto()
    TIMEOUT = auto()
    ABSTRACTION = auto()
    INTERNAL = auto()


class ErrorSeverity(Enum):
    """How severe is this error."""

    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass(frozen=True)
class ErrorResult:
    """Structured error result for API responses."""

    error_code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for JSON output."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.name,
            "severity": self.severity.name,
            "context": self.context,
            "recoverable": self.recoverable,
        }


class AximaError(Exception):
    """Base exception for all AXIMA errors."""

    category: ErrorCategory = ErrorCategory.INTERNAL
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    error_code: str = "AXIMA_INTERNAL"

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        recoverable: bool = True,
    ) -> None:
        super().__init__(message)
        self.context = context or {}
        self.recoverable = recoverable
        self._traceback = traceback.format_stack()

    def to_result(self) -> ErrorResult:
        """Convert to an ErrorResult for structured reporting."""
        return ErrorResult(
            error_code=self.error_code,
            message=str(self),
            category=self.category,
            severity=self.severity,
            context=self.context,
            recoverable=self.recoverable,
        )


class ParseError(AximaError):
    """Failed to parse input (math expression, query, etc.)."""

    category = ErrorCategory.PARSE
    severity = ErrorSeverity.LOW
    error_code = "PARSE_ERROR"


class EvalError(AximaError):
    """Error during expression evaluation (domain error, overflow, etc.)."""

    category = ErrorCategory.EVALUATION
    severity = ErrorSeverity.MEDIUM
    error_code = "EVAL_ERROR"


class SecurityError(AximaError):
    """Security violation detected (injection attempt, sandbox escape, etc.)."""

    category = ErrorCategory.SECURITY
    severity = ErrorSeverity.CRITICAL
    error_code = "SECURITY_VIOLATION"

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        recoverable: bool = False,
    ) -> None:
        super().__init__(message, context=context, recoverable=recoverable)


class ResourceError(AximaError):
    """Resource limits exceeded (memory, time, output size)."""

    category = ErrorCategory.RESOURCE
    severity = ErrorSeverity.HIGH
    error_code = "RESOURCE_EXCEEDED"


class CapabilityError(AximaError):
    """Requested capability is not available or not supported."""

    category = ErrorCategory.CAPABILITY
    severity = ErrorSeverity.LOW
    error_code = "CAPABILITY_UNAVAILABLE"


class TimeoutError(AximaError):  # noqa: A001
    """Operation timed out."""

    category = ErrorCategory.TIMEOUT
    severity = ErrorSeverity.MEDIUM
    error_code = "TIMEOUT"


class AbstractionError(AximaError):
    """Abstraction layer violation."""

    category = ErrorCategory.ABSTRACTION
    severity = ErrorSeverity.MEDIUM
    error_code = "ABSTRACTION_VIOLATION"
