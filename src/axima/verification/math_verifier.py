"""Math verification: equivalence, dimensions, numerics, domains, counterexamples."""

from __future__ import annotations

import math
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .verifier_base import Verifier, VerifierResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VAR_RE = re.compile(r"\b([a-z])\b")


def _extract_variables(expr: str) -> Set[str]:
    """Extract single-letter variable names from an expression string."""
    reserved = {"e", "i"}  # mathematical constants
    return set(_VAR_RE.findall(expr)) - reserved


def _safe_eval(expr: str, bindings: Dict[str, float]) -> Optional[float]:
    """Evaluate a math expression safely with given variable bindings."""
    allowed_names: Dict[str, Any] = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "exp": math.exp,
        "abs": abs,
        "pi": math.pi,
        "e": math.e,
        **bindings,
    }
    try:
        # Replace ^ with ** for exponentiation
        safe_expr = expr.replace("^", "**")
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)  # noqa: S307
        if isinstance(result, (int, float)) and math.isfinite(result):
            return float(result)
        return None
    except Exception:
        return None


def _normalize_expr(expr: str) -> str:
    """Basic algebraic normalization: strip whitespace, lowercase, sort terms."""
    expr = expr.strip().lower().replace(" ", "")
    expr = expr.replace("^", "**")
    return expr


# ---------------------------------------------------------------------------
# MathEquivalenceVerifier
# ---------------------------------------------------------------------------


class MathEquivalenceVerifier(Verifier):
    """Checks symbolic equivalence by substitution and normalization."""

    def name(self) -> str:
        return "math_equivalence"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") == "math_equivalence"

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        lhs = claim.get("lhs", "")
        rhs = claim.get("rhs", "")

        # Step 1: string normalization
        if _normalize_expr(lhs) == _normalize_expr(rhs):
            return VerifierResult(
                passed=True,
                check_name="math_equivalence",
                details="Expressions are syntactically identical after normalization.",
                confidence=1.0,
            )

        # Step 2: numerical sampling
        variables = _extract_variables(lhs) | _extract_variables(rhs)
        num_trials = 20
        failures: List[Dict[str, Any]] = []
        successes = 0

        for _ in range(num_trials):
            bindings = {v: random.uniform(0.1, 10.0) for v in variables}
            val_lhs = _safe_eval(lhs, bindings)
            val_rhs = _safe_eval(rhs, bindings)
            if val_lhs is None or val_rhs is None:
                continue
            if abs(val_lhs - val_rhs) < 1e-9 * max(1.0, abs(val_lhs), abs(val_rhs)):
                successes += 1
            else:
                failures.append(
                    {"bindings": bindings, "lhs_val": val_lhs, "rhs_val": val_rhs}
                )

        if failures:
            return VerifierResult(
                passed=False,
                check_name="math_equivalence",
                details=f"Expressions differ at {len(failures)}/{num_trials} sample points.",
                counterexamples=failures[:5],
                confidence=0.95,
            )

        if successes == 0:
            return VerifierResult(
                passed=False,
                check_name="math_equivalence",
                details="Could not evaluate either expression for any binding.",
                confidence=0.3,
            )

        return VerifierResult(
            passed=True,
            check_name="math_equivalence",
            details=f"Expressions agree at {successes}/{num_trials} random sample points.",
            confidence=min(0.95, 0.5 + 0.025 * successes),
        )


# ---------------------------------------------------------------------------
# DimensionVerifier
# ---------------------------------------------------------------------------

# Basic SI dimension representation: [M, L, T, I, Θ, N, J]
_DIMENSION_KEYS = ("M", "L", "T", "I", "Theta", "N", "J")

_KNOWN_UNITS: Dict[str, Dict[str, int]] = {
    "m": {"L": 1},
    "kg": {"M": 1},
    "s": {"T": 1},
    "A": {"I": 1},
    "K": {"Theta": 1},
    "mol": {"N": 1},
    "cd": {"J": 1},
    "N": {"M": 1, "L": 1, "T": -2},
    "J": {"M": 1, "L": 2, "T": -2},
    "W": {"M": 1, "L": 2, "T": -3},
    "Pa": {"M": 1, "L": -1, "T": -2},
    "V": {"M": 1, "L": 2, "T": -3, "I": -1},
    "m/s": {"L": 1, "T": -1},
    "m/s^2": {"L": 1, "T": -2},
}


class DimensionVerifier(Verifier):
    """Checks unit/dimension consistency of a physical expression."""

    def name(self) -> str:
        return "dimension_check"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") == "physical_equation" or "units" in claim

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        lhs_units = claim.get("lhs_units", "")
        rhs_units = claim.get("rhs_units", "")

        lhs_dim = self._resolve_dimension(lhs_units)
        rhs_dim = self._resolve_dimension(rhs_units)

        if lhs_dim is None or rhs_dim is None:
            return VerifierResult(
                passed=False,
                check_name="dimension_check",
                details=f"Could not resolve dimensions: lhs={lhs_units}, rhs={rhs_units}",
                confidence=0.4,
            )

        if lhs_dim == rhs_dim:
            return VerifierResult(
                passed=True,
                check_name="dimension_check",
                details=f"Dimensions match: {lhs_dim}",
                confidence=0.99,
            )

        return VerifierResult(
            passed=False,
            check_name="dimension_check",
            details=f"Dimension mismatch: LHS={lhs_dim}, RHS={rhs_dim}",
            counterexamples=[{"lhs_dim": lhs_dim, "rhs_dim": rhs_dim}],
            confidence=0.99,
        )

    def _resolve_dimension(self, unit_str: str) -> Optional[Dict[str, int]]:
        """Resolve a unit string to its dimensional representation."""
        if not unit_str:
            return None
        # Check direct lookup
        if unit_str in _KNOWN_UNITS:
            return _KNOWN_UNITS[unit_str]
        # Check if it's a dict already (pre-resolved)
        if isinstance(unit_str, dict):
            return unit_str
        return None


# ---------------------------------------------------------------------------
# NumericalVerifier
# ---------------------------------------------------------------------------


class NumericalVerifier(Verifier):
    """Checks a math claim by numerical substitution with multiple random values."""

    def __init__(self, num_samples: int = 50, tolerance: float = 1e-8) -> None:
        self._num_samples = num_samples
        self._tolerance = tolerance

    def name(self) -> str:
        return "numerical_substitution"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") in ("math_equivalence", "math_identity", "equation")

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        expr = claim.get("expression", "")
        expected = claim.get("expected_value")
        lhs = claim.get("lhs", "")
        rhs = claim.get("rhs", "")

        if lhs and rhs:
            return self._check_equality(lhs, rhs, claim)
        elif expr and expected is not None:
            return self._check_value(expr, float(expected), claim)
        else:
            return VerifierResult(
                passed=False,
                check_name="numerical_substitution",
                details="Insufficient claim data for numerical verification.",
                confidence=0.2,
            )

    def _check_equality(
        self, lhs: str, rhs: str, claim: Dict[str, Any]
    ) -> VerifierResult:
        variables = _extract_variables(lhs) | _extract_variables(rhs)
        counterexamples: List[Dict[str, Any]] = []
        passes = 0

        for _ in range(self._num_samples):
            bindings = {v: random.uniform(-10.0, 10.0) for v in variables}
            val_lhs = _safe_eval(lhs, bindings)
            val_rhs = _safe_eval(rhs, bindings)
            if val_lhs is None or val_rhs is None:
                continue
            diff = abs(val_lhs - val_rhs)
            scale = max(1.0, abs(val_lhs), abs(val_rhs))
            if diff / scale < self._tolerance:
                passes += 1
            else:
                counterexamples.append({"bindings": bindings, "diff": diff})

        total_evaluated = passes + len(counterexamples)
        if total_evaluated == 0:
            return VerifierResult(
                passed=False,
                check_name="numerical_substitution",
                details="Could not evaluate expressions.",
                confidence=0.1,
            )

        passed = len(counterexamples) == 0 and passes > 0
        confidence = min(0.99, passes / max(1, total_evaluated))
        return VerifierResult(
            passed=passed,
            check_name="numerical_substitution",
            details=f"Passed {passes}/{total_evaluated} numerical trials.",
            counterexamples=counterexamples[:5],
            confidence=confidence,
        )

    def _check_value(
        self, expr: str, expected: float, claim: Dict[str, Any]
    ) -> VerifierResult:
        variables = _extract_variables(expr)
        bindings = {v: claim.get(f"var_{v}", 1.0) for v in variables}
        result = _safe_eval(expr, bindings)
        if result is None:
            return VerifierResult(
                passed=False,
                check_name="numerical_substitution",
                details="Could not evaluate expression.",
                confidence=0.2,
            )
        diff = abs(result - expected)
        scale = max(1.0, abs(expected))
        passed = diff / scale < self._tolerance
        return VerifierResult(
            passed=passed,
            check_name="numerical_substitution",
            details=f"Computed {result}, expected {expected}, diff={diff}.",
            counterexamples=[] if passed else [{"computed": result, "expected": expected}],
            confidence=0.95 if passed else 0.9,
        )


# ---------------------------------------------------------------------------
# DomainVerifier
# ---------------------------------------------------------------------------


class DomainVerifier(Verifier):
    """Checks domain constraints: division by zero, sqrt of negative, log of non-positive."""

    def name(self) -> str:
        return "domain_constraints"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") in (
            "math_equivalence",
            "math_identity",
            "equation",
            "expression",
        )

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        expr = claim.get("expression", claim.get("lhs", ""))
        domain_constraints = claim.get("domain", {})
        variables = _extract_variables(expr)

        violations: List[Dict[str, Any]] = []

        # Check for division by zero possibility
        if "/" in expr:
            for _ in range(30):
                bindings = {v: random.uniform(-5.0, 5.0) for v in variables}
                # Try evaluating denominator parts
                parts = expr.split("/")
                if len(parts) > 1:
                    denom = parts[1].split("+")[0].split("-")[0].strip("()")
                    val = _safe_eval(denom, bindings)
                    if val is not None and abs(val) < 1e-12:
                        violations.append(
                            {"type": "division_by_zero", "bindings": bindings}
                        )
                        break

        # Check sqrt of negative
        if "sqrt" in expr:
            for _ in range(30):
                bindings = {v: random.uniform(-10.0, 10.0) for v in variables}
                # Find sqrt argument
                sqrt_match = re.search(r"sqrt\(([^)]+)\)", expr)
                if sqrt_match:
                    arg = sqrt_match.group(1)
                    val = _safe_eval(arg, bindings)
                    if val is not None and val < 0:
                        violations.append(
                            {"type": "sqrt_of_negative", "bindings": bindings, "arg_val": val}
                        )
                        break

        # Check log of non-positive
        if "log" in expr:
            for _ in range(30):
                bindings = {v: random.uniform(-10.0, 10.0) for v in variables}
                log_match = re.search(r"log\(([^)]+)\)", expr)
                if log_match:
                    arg = log_match.group(1)
                    val = _safe_eval(arg, bindings)
                    if val is not None and val <= 0:
                        violations.append(
                            {"type": "log_of_non_positive", "bindings": bindings, "arg_val": val}
                        )
                        break

        # Apply domain constraints from claim
        constraint_violations = self._check_domain_constraints(
            expr, variables, domain_constraints
        )
        violations.extend(constraint_violations)

        if violations:
            return VerifierResult(
                passed=False,
                check_name="domain_constraints",
                details=f"Found {len(violations)} domain violation(s).",
                counterexamples=violations,
                confidence=0.9,
            )

        return VerifierResult(
            passed=True,
            check_name="domain_constraints",
            details="No domain violations found in random sampling.",
            confidence=0.8,
        )

    def _check_domain_constraints(
        self,
        expr: str,
        variables: Set[str],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check explicit domain constraints."""
        violations: List[Dict[str, Any]] = []
        for var, constraint in constraints.items():
            if var not in variables:
                continue
            if "min" in constraint:
                # Variable must be >= min
                pass  # These are declarations, not violations to check
            if "exclude" in constraint:
                excluded_vals = constraint["exclude"]
                # Check if expression is defined at excluded values
                for exc_val in excluded_vals:
                    bindings = {v: 1.0 for v in variables}
                    bindings[var] = exc_val
                    result = _safe_eval(expr, bindings)
                    if result is not None:
                        violations.append(
                            {
                                "type": "excluded_value_reachable",
                                "variable": var,
                                "excluded_value": exc_val,
                            }
                        )
        return violations


# ---------------------------------------------------------------------------
# CounterexampleSearcher
# ---------------------------------------------------------------------------


class CounterexampleSearcher:
    """Tries to find counterexamples to mathematical claims."""

    def __init__(self, max_attempts: int = 200) -> None:
        self._max_attempts = max_attempts

    def search(
        self,
        claim: Dict[str, Any],
        variables: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for counterexamples that disprove the claim.

        A claim is expected to have:
          - lhs, rhs (for equivalence)
          - OR predicate (a boolean expression that should always be True)
        """
        lhs = claim.get("lhs", "")
        rhs = claim.get("rhs", "")
        predicate = claim.get("predicate", "")

        if lhs and rhs:
            return self._search_equivalence(lhs, rhs, variables)
        elif predicate:
            return self._search_predicate(predicate, variables)
        return []

    def _search_equivalence(
        self, lhs: str, rhs: str, variables: Optional[Set[str]]
    ) -> List[Dict[str, Any]]:
        if variables is None:
            variables = _extract_variables(lhs) | _extract_variables(rhs)

        counterexamples: List[Dict[str, Any]] = []

        # Strategy 1: random sampling
        for _ in range(self._max_attempts // 2):
            bindings = {v: random.uniform(-100.0, 100.0) for v in variables}
            val_lhs = _safe_eval(lhs, bindings)
            val_rhs = _safe_eval(rhs, bindings)
            if val_lhs is None or val_rhs is None:
                continue
            diff = abs(val_lhs - val_rhs)
            scale = max(1.0, abs(val_lhs), abs(val_rhs))
            if diff / scale > 1e-8:
                counterexamples.append(
                    {"bindings": bindings, "lhs_val": val_lhs, "rhs_val": val_rhs}
                )
                if len(counterexamples) >= 5:
                    return counterexamples

        # Strategy 2: boundary values
        boundary_vals = [0.0, 1.0, -1.0, 0.5, -0.5, 2.0, -2.0, 10.0, -10.0, 100.0, 0.001]
        for val in boundary_vals:
            bindings = {v: val for v in variables}
            val_lhs = _safe_eval(lhs, bindings)
            val_rhs = _safe_eval(rhs, bindings)
            if val_lhs is None or val_rhs is None:
                continue
            diff = abs(val_lhs - val_rhs)
            scale = max(1.0, abs(val_lhs), abs(val_rhs))
            if diff / scale > 1e-8:
                counterexamples.append(
                    {"bindings": bindings, "lhs_val": val_lhs, "rhs_val": val_rhs}
                )
                if len(counterexamples) >= 5:
                    return counterexamples

        return counterexamples

    def _search_predicate(
        self, predicate: str, variables: Optional[Set[str]]
    ) -> List[Dict[str, Any]]:
        """Search for inputs where a predicate evaluates to False."""
        if variables is None:
            variables = _extract_variables(predicate)

        counterexamples: List[Dict[str, Any]] = []

        for _ in range(self._max_attempts):
            bindings = {v: random.uniform(-100.0, 100.0) for v in variables}
            try:
                allowed: Dict[str, Any] = {
                    "sqrt": math.sqrt,
                    "abs": abs,
                    "sin": math.sin,
                    "cos": math.cos,
                    "pi": math.pi,
                    "e": math.e,
                    **bindings,
                }
                safe_pred = predicate.replace("^", "**")
                result = eval(safe_pred, {"__builtins__": {}}, allowed)  # noqa: S307
                if not result:
                    counterexamples.append({"bindings": bindings, "result": result})
                    if len(counterexamples) >= 5:
                        return counterexamples
            except Exception:
                continue

        return counterexamples
