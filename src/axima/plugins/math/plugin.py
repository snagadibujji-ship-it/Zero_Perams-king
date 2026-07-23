"""Math Plugin — symbolic math solver using safe_math evaluator.

Uses safe_math evaluator for arithmetic and simple algebra.
Returns proof/derivation objects with computed results.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract, EvidenceRequirement
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR
from ..base import PluginBase

logger = logging.getLogger(__name__)


class MathPlugin(PluginBase):
    """Symbolic math solver plugin.

    Routes simple arithmetic to the safe_math evaluator (no eval()),
    and attempts basic algebra for simple equations.
    """

    def __init__(self) -> None:
        self._healthy = False

    def name(self) -> str:
        return "math_solver"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["math", "calculate", "algebra", "calculus", "proof"],
            produced_types=["derivation", "proof", "numeric_result"],
            preconditions=[],
            postconditions=["mathematical_result"],
            cost_model={"avg_ms": 50, "max_ms": 2000},
            latency_model={"avg_ms": 50, "p95_ms": 500},
            deterministic=True,
            permissions=["read"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Execute math solving against the MeaningIR.

        Extracts expression from IR, attempts evaluation via safe_math.
        Falls back to simple algebra solver for equations.
        """
        start = time.time()

        # Extract the mathematical expression from IR
        expression = self._extract_expression(ir)
        if not expression:
            return ExecutionResult(
                status="error",
                error="No mathematical expression found in query",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Try to solve
        result = self._solve(expression)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            answer_str = self._format_result(result)
            return ExecutionResult(
                answer=answer_str,
                status="success",
                claims=[f"Computed: {expression} = {answer_str}"],
                evidence=["safe_math_evaluator"],
                engine=self.name(),
                cost_ms=elapsed,
            )

        # Try as equation
        equation_result = self._solve_equation(expression)
        elapsed = (time.time() - start) * 1000

        if equation_result is not None:
            return ExecutionResult(
                answer=equation_result,
                status="success",
                claims=[f"Solved: {expression}"],
                evidence=["algebra_solver"],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"Could not solve: {expression}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if math solving is available."""
        try:
            from ...security.safe_math import safe_eval
            result = safe_eval("2 + 2")
            self._healthy = (result == 4.0)
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        """Initialize — verify safe_math is importable."""
        self.health_check()

    # --- Internal Methods ---

    def _extract_expression(self, ir: MeaningIR) -> Optional[str]:
        """Extract a mathematical expression from the MeaningIR."""
        # Check goals first (from "solve X", "calculate X" patterns)
        for goal in ir.goals:
            if goal.description:
                expr = goal.description.strip()
                # Clean common prefixes
                expr = re.sub(
                    r'^(the\s+)?(value\s+of\s+|result\s+of\s+)?',
                    '', expr, flags=re.IGNORECASE
                ).strip()
                if expr:
                    return expr

        # Check events for calculation verbs
        for event in ir.events:
            if event.verb in ("calculate", "compute", "solve", "evaluate"):
                if event.patient:
                    return event.patient.strip()

        # Check predicates
        for pred in ir.predicates:
            if pred.relation in ("equals", "is", "evaluate"):
                return pred.subject

        # Check quantities — if multiple, try to form an expression
        if ir.quantities:
            parts = []
            for q in ir.quantities:
                parts.append(str(q.value))
            if parts:
                return " ".join(parts)

        return None

    def _solve(self, expression: str) -> Optional[float]:
        """Attempt to solve using safe_math evaluator."""
        try:
            from ...security.safe_math import safe_eval

            # Clean up the expression
            cleaned = self._clean_expression(expression)
            if not cleaned:
                return None

            # Check if it's evaluable (no variables except those we can substitute)
            if self._has_unsolvable_variables(cleaned):
                return None

            result = safe_eval(cleaned)
            return result
        except Exception as exc:
            logger.debug(f"safe_eval failed for '{expression}': {exc}")
            return None

    def _solve_equation(self, expression: str) -> Optional[str]:
        """Attempt to solve simple algebraic equations.

        Handles forms like:
          - x^2 - 4 = 0 → x = ±2
          - x^2 + 3x - 4 = 0 → quadratic formula
          - 2x + 6 = 0 → x = -3
          - x^2 = 9 → x = ±3
        """
        # Check if it's an equation (contains =)
        if '=' not in expression:
            # Try "solve X" where X might be implicit "= 0"
            cleaned = re.sub(r'^solve\s+', '', expression, flags=re.IGNORECASE).strip()
            if '=' not in cleaned:
                # Assume = 0
                expression = cleaned + " = 0"
            else:
                expression = cleaned

        # Split on =
        parts = expression.split('=')
        if len(parts) != 2:
            return None

        lhs = parts[0].strip()
        rhs = parts[1].strip()

        # Try to solve linear equation: ax + b = c
        linear = self._try_linear(lhs, rhs)
        if linear is not None:
            return linear

        # Try to solve quadratic: ax^2 + bx + c = 0
        quadratic = self._try_quadratic(lhs, rhs)
        if quadratic is not None:
            return quadratic

        return None

    def _try_linear(self, lhs: str, rhs: str) -> Optional[str]:
        """Try to solve a linear equation ax + b = c."""
        # Match patterns like: 2x + 6, 3x - 4, x + 1, -x + 5
        linear_re = re.compile(
            r'^([+-]?\s*\d*\.?\d*)\s*\*?\s*([a-zA-Z])\s*([+-]\s*\d+\.?\d*)?\s*$'
        )

        match = linear_re.match(lhs.strip())
        if not match:
            return None

        coeff_str = match.group(1).replace(' ', '') or '1'
        var = match.group(2)
        const_str = match.group(3)

        # Parse coefficient
        if coeff_str in ('', '+', '+1'):
            a = 1.0
        elif coeff_str in ('-', '-1'):
            a = -1.0
        else:
            try:
                a = float(coeff_str)
            except ValueError:
                return None

        # Parse constant
        b = 0.0
        if const_str:
            try:
                b = float(const_str.replace(' ', ''))
            except ValueError:
                return None

        # Parse RHS
        try:
            c = float(rhs) if rhs else 0.0
        except ValueError:
            return None

        if a == 0:
            return None

        # Solve: ax + b = c → x = (c - b) / a
        result = (c - b) / a
        if result == int(result):
            result = int(result)
        return f"{var} = {result}"

    def _try_quadratic(self, lhs: str, rhs: str) -> Optional[str]:
        """Try to solve a quadratic equation ax^2 + bx + c = 0."""
        import math

        # Move RHS to LHS
        try:
            rhs_val = float(rhs) if rhs.strip() else 0.0
        except ValueError:
            rhs_val = 0.0

        expr = lhs.strip()

        # Parse quadratic: ax^2 + bx + c
        # Match coefficient of x^2
        a = 0.0
        b_coeff = 0.0
        c_val = -rhs_val  # Move RHS to LHS

        # Find x^2 term
        x2_match = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*[a-zA-Z]\s*\^\s*2', expr)
        if not x2_match:
            # Also try x² format
            x2_match = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*[a-zA-Z]²', expr)
        if not x2_match:
            return None

        coeff_str = x2_match.group(1).replace(' ', '')
        if coeff_str in ('', '+'):
            a = 1.0
        elif coeff_str == '-':
            a = -1.0
        else:
            try:
                a = float(coeff_str)
            except ValueError:
                return None

        # Remove x^2 term to find remaining
        remaining = expr[:x2_match.start()] + expr[x2_match.end():]
        remaining = remaining.strip()

        # Find x term (linear)
        x_match = re.search(r'([+-]?\s*\d*\.?\d*)\s*\*?\s*[a-zA-Z](?!\s*\^|\s*²)', remaining)
        if x_match:
            coeff_str = x_match.group(1).replace(' ', '')
            if coeff_str in ('', '+'):
                b_coeff = 1.0
            elif coeff_str == '-':
                b_coeff = -1.0
            else:
                try:
                    b_coeff = float(coeff_str)
                except ValueError:
                    b_coeff = 0.0
            # Remove x term
            remaining = remaining[:x_match.start()] + remaining[x_match.end():]

        # Remaining should be constant
        remaining = remaining.strip()
        if remaining:
            # Handle multiple terms like "+ 5 - 3"
            const_match = re.findall(r'[+-]?\s*\d+\.?\d*', remaining)
            for cm in const_match:
                try:
                    c_val += float(cm.replace(' ', ''))
                except ValueError:
                    pass

        # Solve quadratic: ax^2 + bx + c = 0
        if a == 0:
            return None

        discriminant = b_coeff * b_coeff - 4 * a * c_val

        if discriminant < 0:
            # Complex roots
            real = -b_coeff / (2 * a)
            imag = math.sqrt(-discriminant) / (2 * a)
            if real == 0:
                return f"x = ±{self._fmt(imag)}i"
            return f"x = {self._fmt(real)} ± {self._fmt(imag)}i"
        elif discriminant == 0:
            # One repeated root
            x = -b_coeff / (2 * a)
            return f"x = {self._fmt(x)}"
        else:
            # Two real roots
            sqrt_d = math.sqrt(discriminant)
            x1 = (-b_coeff + sqrt_d) / (2 * a)
            x2 = (-b_coeff - sqrt_d) / (2 * a)
            # Special case: symmetric roots
            if x1 == -x2:
                return f"x = ±{self._fmt(abs(x1))}"
            return f"x = {self._fmt(x1)} or x = {self._fmt(x2)}"

    def _clean_expression(self, expression: str) -> str:
        """Clean up expression for safe_eval."""
        cleaned = expression.strip()
        # Remove common prefixes
        cleaned = re.sub(
            r'^(solve|calculate|compute|evaluate|what is|find)\s*',
            '', cleaned, flags=re.IGNORECASE
        ).strip()
        # Remove trailing question marks/periods
        cleaned = cleaned.rstrip('?.!').strip()
        # Replace × with *, ÷ with /
        cleaned = cleaned.replace('×', '*').replace('÷', '/')
        # Replace ^ with ** for exponentiation (safe_math handles ^)
        # Actually safe_math already handles ^ → ** in tokenizer
        return cleaned

    def _has_unsolvable_variables(self, expression: str) -> bool:
        """Check if expression has variables that can't be evaluated directly."""
        # Remove known constants handled by safe_math
        cleaned = re.sub(r'\b(pi|e)\b', '', expression)
        # Remove function names
        cleaned = re.sub(r'\b(sin|cos|tan|sqrt|abs|log|ln|exp|factorial|gcd|lcm|floor|ceil|round|asin|acos|atan|sinh|cosh|tanh)\b', '', cleaned)
        # Check for remaining alphabetic characters (variables)
        if re.search(r'[a-zA-Z]', cleaned):
            return True
        return False

    def _fmt(self, value: float) -> str:
        """Format a numeric result nicely."""
        if value == int(value):
            return str(int(value))
        # Round to avoid floating point noise
        rounded = round(value, 10)
        if rounded == int(rounded):
            return str(int(rounded))
        return str(rounded)

    def _format_result(self, result: float) -> str:
        """Format a numeric result for display."""
        if result == int(result):
            return str(int(result))
        # Check if it's a clean decimal
        rounded = round(result, 10)
        if rounded == int(rounded):
            return str(int(rounded))
        # Otherwise show reasonable precision
        formatted = f"{result:.10g}"
        return formatted
