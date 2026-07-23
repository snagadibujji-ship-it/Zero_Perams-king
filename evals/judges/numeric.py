"""Standalone numeric tolerance judge for AXIMA evaluations.

Compares numeric values within a configurable tolerance.
Supports both absolute and relative tolerance modes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NumericResult:
    """Result of a numeric tolerance evaluation.

    Attributes:
        passed: Whether the values are within tolerance.
        expected: Expected numeric value.
        actual: Actual numeric value.
        difference: Absolute difference between values.
        tolerance: The tolerance that was applied.
        relative: Whether relative tolerance was used.
        explanation: Human-readable explanation.
    """

    passed: bool
    expected: float
    actual: float
    difference: float
    tolerance: float
    relative: bool
    explanation: str


class NumericToleranceJudge:
    """Numeric comparison judge with configurable tolerance.

    Parses string inputs as floats and compares within tolerance.
    Supports:
    - Absolute tolerance (default): |actual - expected| <= tolerance
    - Relative tolerance: |actual - expected| / |expected| <= tolerance
    """

    def __init__(
        self,
        default_tolerance: float = 1e-6,
        default_relative: bool = False,
    ) -> None:
        """Initialize numeric tolerance judge.

        Args:
            default_tolerance: Default tolerance for comparisons.
            default_relative: If True, use relative tolerance by default.
        """
        self._default_tolerance = default_tolerance
        self._default_relative = default_relative

    def judge(
        self,
        expected: str,
        actual: str,
        tolerance: Optional[float] = None,
        relative: Optional[bool] = None,
    ) -> NumericResult:
        """Judge whether actual is within tolerance of expected.

        Args:
            expected: Expected value as string.
            actual: Actual value as string.
            tolerance: Override default tolerance.
            relative: Override default relative mode.

        Returns:
            NumericResult with pass/fail and details.
        """
        tol = tolerance if tolerance is not None else self._default_tolerance
        rel = relative if relative is not None else self._default_relative

        # Parse expected
        expected_val = self._parse_numeric(expected)
        if expected_val is None:
            return NumericResult(
                passed=False,
                expected=float("nan"),
                actual=float("nan"),
                difference=float("inf"),
                tolerance=tol,
                relative=rel,
                explanation=f"Cannot parse expected as number: {repr(expected)}",
            )

        # Parse actual
        actual_val = self._parse_numeric(actual)
        if actual_val is None:
            return NumericResult(
                passed=False,
                expected=expected_val,
                actual=float("nan"),
                difference=float("inf"),
                tolerance=tol,
                relative=rel,
                explanation=f"Cannot parse actual as number: {repr(actual)}",
            )

        # Compute difference
        if rel:
            if expected_val == 0.0:
                difference = abs(actual_val)
            else:
                difference = abs((actual_val - expected_val) / expected_val)
        else:
            difference = abs(actual_val - expected_val)

        passed = difference <= tol

        if passed:
            explanation = (
                f"Within {'relative' if rel else 'absolute'} tolerance: "
                f"diff={difference:.2e} <= {tol:.2e}"
            )
        else:
            explanation = (
                f"Outside {'relative' if rel else 'absolute'} tolerance: "
                f"diff={difference:.2e} > {tol:.2e} "
                f"(expected={expected_val}, actual={actual_val})"
            )

        return NumericResult(
            passed=passed,
            expected=expected_val,
            actual=actual_val,
            difference=difference,
            tolerance=tol,
            relative=rel,
            explanation=explanation,
        )

    def judge_close(
        self,
        expected: float,
        actual: float,
        rel_tol: float = 1e-9,
        abs_tol: float = 0.0,
    ) -> NumericResult:
        """Judge using math.isclose semantics.

        Uses both relative and absolute tolerance like Python's
        math.isclose function.

        Args:
            expected: Expected numeric value.
            actual: Actual numeric value.
            rel_tol: Relative tolerance.
            abs_tol: Absolute tolerance.

        Returns:
            NumericResult with pass/fail.
        """
        passed = math.isclose(expected, actual, rel_tol=rel_tol, abs_tol=abs_tol)
        difference = abs(actual - expected)

        if passed:
            explanation = f"Values are close (rel_tol={rel_tol}, abs_tol={abs_tol})"
        else:
            explanation = (
                f"Values not close: |{actual} - {expected}| = {difference} "
                f"(rel_tol={rel_tol}, abs_tol={abs_tol})"
            )

        return NumericResult(
            passed=passed,
            expected=expected,
            actual=actual,
            difference=difference,
            tolerance=max(rel_tol * abs(expected), abs_tol),
            relative=True,
            explanation=explanation,
        )

    def _parse_numeric(self, value: str) -> Optional[float]:
        """Parse a string as a numeric value.

        Handles:
        - Standard float notation: "3.14", "-2.5"
        - Scientific notation: "1.5e-3"
        - Integer: "42"
        - Common math constants: "pi", "e"
        """
        cleaned = value.strip().lower()

        # Handle common math constants
        constants = {
            "pi": math.pi,
            "e": math.e,
            "inf": math.inf,
            "-inf": -math.inf,
            "infinity": math.inf,
            "-infinity": -math.inf,
        }
        if cleaned in constants:
            return constants[cleaned]

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
