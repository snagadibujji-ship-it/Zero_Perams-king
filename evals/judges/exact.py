"""Standalone exact match judge for AXIMA evaluations.

Performs strict exact string comparison. NO substring matching,
NO fuzzy matching, NO partial credit. The actual output must
be exactly equal to the expected output.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ExactResult:
    """Result of an exact match evaluation.

    Attributes:
        passed: Whether the actual matches expected exactly.
        expected: The expected value.
        actual: The actual value.
        explanation: Human-readable explanation.
    """

    passed: bool
    expected: str
    actual: str
    explanation: str


class ExactMatchJudge:
    """Exact string match judge.

    Strips whitespace from both sides before comparison.
    Does NOT perform:
    - Substring matching
    - Fuzzy matching
    - Case-insensitive matching (unless explicitly configured)
    - Partial credit
    """

    def __init__(self, case_sensitive: bool = True, strip: bool = True) -> None:
        """Initialize exact match judge.

        Args:
            case_sensitive: If True (default), comparison is case-sensitive.
            strip: If True (default), strips leading/trailing whitespace.
        """
        self._case_sensitive = case_sensitive
        self._strip = strip

    def judge(self, expected: str, actual: str) -> ExactResult:
        """Judge whether actual exactly matches expected.

        Args:
            expected: The correct/expected output.
            actual: The actual output from the system.

        Returns:
            ExactResult with pass/fail.
        """
        exp = expected
        act = actual

        if self._strip:
            exp = exp.strip()
            act = act.strip()

        if not self._case_sensitive:
            exp = exp.lower()
            act = act.lower()

        passed = exp == act

        if passed:
            explanation = "Exact match."
        else:
            explanation = f"Mismatch: expected {repr(expected.strip())}, got {repr(actual.strip())}"

        return ExactResult(
            passed=passed,
            expected=expected,
            actual=actual,
            explanation=explanation,
        )

    def judge_any(self, expected_options: List[str], actual: str) -> ExactResult:
        """Judge whether actual matches any of the expected options.

        Useful for cases where multiple correct answers exist
        (e.g., "solve x^2 - 4 = 0" → ["2", "-2"]).

        Args:
            expected_options: List of acceptable correct answers.
            actual: The actual output from the system.

        Returns:
            ExactResult (passed=True if ANY option matches).
        """
        act = actual.strip() if self._strip else actual

        if not self._case_sensitive:
            act = act.lower()

        for option in expected_options:
            exp = option.strip() if self._strip else option
            if not self._case_sensitive:
                exp = exp.lower()

            if exp == act:
                return ExactResult(
                    passed=True,
                    expected=option,
                    actual=actual,
                    explanation=f"Matched option: {repr(option)}",
                )

        return ExactResult(
            passed=False,
            expected=f"one of {expected_options}",
            actual=actual,
            explanation=(
                f"No match: actual {repr(actual.strip())} not in "
                f"{[o.strip() for o in expected_options]}"
            ),
        )
