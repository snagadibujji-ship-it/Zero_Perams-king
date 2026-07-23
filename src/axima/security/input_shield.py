"""Input validation and normalization shield for AXIMA.

All external input passes through InputShield before reaching
any engine. Detects injection, normalizes encoding, enforces limits.
"""

from __future__ import annotations

import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from axima.errors import SecurityError


@dataclass
class ShieldConfig:
    """Configuration for input validation."""

    max_input_length: int = 10_000
    max_line_count: int = 500
    rate_limit_per_second: float = 1000.0
    rate_limit_burst: int = 10000
    normalize_unicode: bool = True
    strip_control_chars: bool = True


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    normalized_input: str
    warnings: list[str] = field(default_factory=list)
    blocked_reason: str | None = None

    @property
    def blocked(self) -> bool:
        return not self.valid


# Injection patterns grouped by category
_INJECTION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "code_injection": [
        re.compile(r"__\w+__", re.IGNORECASE),
        re.compile(r"\b(?:exec|eval|compile)\s*\(", re.IGNORECASE),
        re.compile(r"\b__import__\s*\(", re.IGNORECASE),
        re.compile(r"\bimport\s+(?:os|sys|subprocess|shutil)", re.IGNORECASE),
        re.compile(r"\bglobals\s*\(\s*\)", re.IGNORECASE),
        re.compile(r"\blocals\s*\(\s*\)", re.IGNORECASE),
        re.compile(r"\bgetattr\s*\(", re.IGNORECASE),
        re.compile(r"\bsetattr\s*\(", re.IGNORECASE),
    ],
    "path_traversal": [
        re.compile(r"\.\./"),
        re.compile(r"\.\.\x5c"),  # ..\
        re.compile(r"/etc/(?:passwd|shadow|hosts)"),
        re.compile(r"(?:^|/)\.\.(?:/|$)"),
        re.compile(r"%2e%2e[/\\%]", re.IGNORECASE),
        re.compile(r"~root"),
    ],
    "shell_metachar": [
        re.compile(r"[;|&`$]"),
        re.compile(r"\$\("),
        re.compile(r"\$\{"),
        re.compile(r">\s*/"),
        re.compile(r"<\s*/"),
        re.compile(r"\brm\s+-rf\b"),
        re.compile(r"\bchmod\b"),
        re.compile(r"\bchown\b"),
        re.compile(r"\bsudo\b"),
        re.compile(r"\bdd\s+if="),
    ],
    "sql_injection": [
        re.compile(r"(?:^|\s)(?:DROP|DELETE|INSERT|UPDATE|ALTER)\s", re.IGNORECASE),
        re.compile(r"(?:^|\s)UNION\s+(?:ALL\s+)?SELECT\b", re.IGNORECASE),
        re.compile(r"'\s*(?:OR|AND)\s+['\d]", re.IGNORECASE),
        re.compile(r";\s*--"),
    ],
}


class InputShield:
    """Validates and normalizes all inputs before processing.

    Features:
      - Max input length enforcement
      - UTF-8 encoding normalization
      - Control character stripping
      - Injection pattern detection (code, path traversal, shell, SQL)
      - Per-source rate limiting
    """

    def __init__(self, config: ShieldConfig | None = None) -> None:
        self._config = config or ShieldConfig()
        # Rate limiting state: source_id -> (token_count, last_refill_time)
        self._rate_state: dict[str, tuple[float, float]] = defaultdict(
            lambda: (float(self._config.rate_limit_burst), time.monotonic())
        )

    @property
    def config(self) -> ShieldConfig:
        return self._config

    def validate(
        self,
        input_text: str,
        *,
        source_id: str = "default",
        context: str = "general",
        strict: bool = False,
    ) -> ValidationResult:
        """Validate and normalize input text.

        Args:
            input_text: Raw input string.
            source_id: Identifier for rate limiting.
            context: Usage context ('math', 'query', 'code', 'general').
            strict: If True, block on warnings instead of just warning.

        Returns:
            ValidationResult with normalized text and any issues found.
        """
        warnings: list[str] = []

        # Rate limit check
        if not self._check_rate_limit(source_id):
            return ValidationResult(
                valid=False,
                normalized_input="",
                blocked_reason="Rate limit exceeded",
            )

        # Encoding normalization
        try:
            normalized = self._normalize_encoding(input_text)
        except UnicodeError as exc:
            return ValidationResult(
                valid=False,
                normalized_input="",
                blocked_reason=f"Invalid encoding: {exc}",
            )

        # Length check
        if len(normalized) > self._config.max_input_length:
            return ValidationResult(
                valid=False,
                normalized_input="",
                blocked_reason=(
                    f"Input too long: {len(normalized)} > {self._config.max_input_length}"
                ),
            )

        # Line count check
        line_count = normalized.count("\n") + 1
        if line_count > self._config.max_line_count:
            return ValidationResult(
                valid=False,
                normalized_input="",
                blocked_reason=f"Too many lines: {line_count} > {self._config.max_line_count}",
            )

        # Strip control characters
        if self._config.strip_control_chars:
            cleaned = self._strip_control_chars(normalized)
            if cleaned != normalized:
                warnings.append("Control characters removed")
                normalized = cleaned

        # Injection detection
        injection_hits = self._detect_injections(normalized, context)
        if injection_hits:
            categories = [cat for cat, _ in injection_hits]
            if strict or context in ("code", "math"):
                raise SecurityError(
                    f"Injection attempt detected: {categories}",
                    context={
                        "categories": categories,
                        "patterns": [pat for _, pat in injection_hits],
                    },
                )
            # In non-strict general context, warn but allow
            # (user might be asking about code injection as a topic)
            if context == "general" and not strict:
                warnings.extend(
                    f"Potential {cat} pattern: '{pat}'" for cat, pat in injection_hits
                )
            else:
                return ValidationResult(
                    valid=False,
                    normalized_input="",
                    blocked_reason=f"Injection patterns detected: {categories}",
                )

        return ValidationResult(
            valid=True,
            normalized_input=normalized,
            warnings=warnings,
        )

    def validate_or_raise(
        self,
        input_text: str,
        *,
        source_id: str = "default",
        context: str = "general",
    ) -> str:
        """Validate input and return normalized text, or raise SecurityError."""
        result = self.validate(input_text, source_id=source_id, context=context, strict=True)
        if not result.valid:
            raise SecurityError(
                result.blocked_reason or "Input validation failed",
                context={"input_length": len(input_text)},
            )
        return result.normalized_input

    def _normalize_encoding(self, text: str) -> str:
        """Normalize Unicode to NFC form."""
        if self._config.normalize_unicode:
            return unicodedata.normalize("NFC", text)
        return text

    def _strip_control_chars(self, text: str) -> str:
        """Remove control characters except newline, tab, carriage return."""
        allowed = {"\n", "\t", "\r"}
        return "".join(
            ch for ch in text
            if ch in allowed or not unicodedata.category(ch).startswith("C")
        )

    def _detect_injections(
        self, text: str, context: str
    ) -> list[tuple[str, str]]:
        """Scan text for injection patterns. Returns (category, matched_text) pairs."""
        hits: list[tuple[str, str]] = []

        # Skip certain checks based on context
        skip_categories: set[str] = set()
        if context == "general":
            # General queries might mention SQL keywords normally
            skip_categories.add("sql_injection")

        for category, patterns in _INJECTION_PATTERNS.items():
            if category in skip_categories:
                continue
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    hits.append((category, match.group()))
                    break  # One hit per category is enough

        return hits

    def _check_rate_limit(self, source_id: str) -> bool:
        """Token bucket rate limiter. Returns True if request is allowed."""
        now = time.monotonic()
        tokens, last_time = self._rate_state[source_id]

        # Refill tokens based on elapsed time
        elapsed = now - last_time
        tokens = min(
            self._config.rate_limit_burst,
            tokens + elapsed * self._config.rate_limit_per_second,
        )

        if tokens >= 1.0:
            self._rate_state[source_id] = (tokens - 1.0, now)
            return True

        self._rate_state[source_id] = (tokens, now)
        return False
