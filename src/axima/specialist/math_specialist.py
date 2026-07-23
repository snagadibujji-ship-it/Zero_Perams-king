"""Math Specialist — symbolic algebra, calculus, discrete math with proof objects.

Uses a safe AST-based evaluator (never eval/exec). Every result carries a Proof
object describing the derivation chain, assumptions, and domain constraints.
"""

from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ---------------------------------------------------------------------------
# Safe math AST evaluator
# ---------------------------------------------------------------------------

_SAFE_UNARY_OPS: Dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_SAFE_BIN_OPS: Dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_SAFE_FUNCTIONS: Dict[str, Any] = {
    "sqrt": math.sqrt,
    "abs": abs,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "ln": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "pi": math.pi,
    "e": math.e,
}

_MAX_EXPONENT = 1000  # prevent resource exhaustion


class SafeMathError(Exception):
    """Raised when expression cannot be safely evaluated."""


def safe_eval_expr(expr_str: str, variables: Optional[Dict[str, float]] = None) -> float:
    """Evaluate a math expression using AST walking — never calls eval().

    Supports: arithmetic operators, safe functions (sin, cos, log, sqrt, etc.),
    numeric literals, and named variables from *variables* dict.

    Raises SafeMathError on disallowed constructs.
    """
    variables = variables or {}

    try:
        tree = ast.parse(expr_str.strip(), mode="eval")
    except SyntaxError as exc:
        raise SafeMathError(f"Parse error: {exc}") from exc

    def _walk(node: ast.AST) -> float:
        # Numeric literal
        if isinstance(node, ast.Expression):
            return _walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        # Unary op
        if isinstance(node, ast.UnaryOp):
            op_fn = _SAFE_UNARY_OPS.get(type(node.op))
            if op_fn is None:
                raise SafeMathError(f"Unsupported unary op: {type(node.op).__name__}")
            return op_fn(_walk(node.operand))
        # Binary op
        if isinstance(node, ast.BinOp):
            op_fn = _SAFE_BIN_OPS.get(type(node.op))
            if op_fn is None:
                raise SafeMathError(f"Unsupported binary op: {type(node.op).__name__}")
            left = _walk(node.left)
            right = _walk(node.right)
            if isinstance(node.op, ast.Pow) and isinstance(right, (int, float)):
                if abs(right) > _MAX_EXPONENT:
                    raise SafeMathError(f"Exponent too large: {right}")
            return op_fn(left, right)
        # Variable / constant name
        if isinstance(node, ast.Name):
            name = node.id
            if name in variables:
                return variables[name]
            if name in _SAFE_FUNCTIONS:
                val = _SAFE_FUNCTIONS[name]
                if isinstance(val, (int, float)):
                    return val
                raise SafeMathError(f"'{name}' is a function, not a value")
            raise SafeMathError(f"Unknown variable: {name}")
        # Function call
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise SafeMathError("Only named function calls allowed")
            fn_name = node.func.id
            fn = _SAFE_FUNCTIONS.get(fn_name)
            if fn is None or not callable(fn):
                raise SafeMathError(f"Unknown function: {fn_name}")
            args = [_walk(a) for a in node.args]
            return fn(*args)
        raise SafeMathError(f"Unsupported AST node: {type(node).__name__}")

    return _walk(tree)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

class ProofStatus(Enum):
    VERIFIED = auto()
    CONDITIONAL = auto()
    UNVERIFIED = auto()
    FAILED = auto()


@dataclass
class Assumption:
    """A domain assumption required for a derivation step."""
    description: str
    domain: str = "real"
    verified: bool = False


@dataclass
class ProofStep:
    """Single step in a derivation."""
    rule: str
    input_expr: str
    output_expr: str
    justification: str


@dataclass
class Proof:
    """Complete proof/derivation chain for a math result."""
    status: ProofStatus
    steps: List[ProofStep] = field(default_factory=list)
    assumptions: List[Assumption] = field(default_factory=list)
    domain: str = "real"
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class MathResult:
    """Result of a math computation with its proof."""
    expression: str
    result: Any
    proof: Proof
    confidence: str = "direct_fact"  # truth label


class NotationNormalizer:
    """Handles adversarial / non-standard notation and normalizes to parseable form."""

    _REPLACEMENTS: List[Tuple[str, str]] = [
        ("×", "*"),
        ("÷", "/"),
        ("−", "-"),
        ("⁰", "**0"),
        ("¹", "**1"),
        ("²", "**2"),
        ("³", "**3"),
        ("⁴", "**4"),
        ("⁵", "**5"),
        ("⁶", "**6"),
        ("⁷", "**7"),
        ("⁸", "**8"),
        ("⁹", "**9"),
        ("√", "sqrt"),
        ("π", "pi"),
        ("∞", "inf"),
    ]

    _IMPLICIT_MULT_PATTERNS: List[Tuple[str, str]] = [
        # 2x -> 2*x, 3sin -> 3*sin (digit followed by letter)
    ]

    @classmethod
    def normalize(cls, expr: str) -> str:
        """Normalize adversarial notation to standard form."""
        result = expr.strip()
        for old, new in cls._REPLACEMENTS:
            result = result.replace(old, new)
        # Handle implicit multiplication: digit followed by letter
        normalized: List[str] = []
        for i, ch in enumerate(result):
            normalized.append(ch)
            if i < len(result) - 1:
                next_ch = result[i + 1]
                if ch.isdigit() and (next_ch.isalpha() or next_ch == "("):
                    normalized.append("*")
                elif ch == ")" and (next_ch.isalpha() or next_ch.isdigit() or next_ch == "("):
                    normalized.append("*")
        return "".join(normalized)


# ---------------------------------------------------------------------------
# Specialist
# ---------------------------------------------------------------------------

class MathSpecialist:
    """Domain specialist for exact symbolic mathematics.

    - Uses safe AST evaluator (never eval/exec)
    - Produces Proof objects for every result
    - Tracks domain and assumptions
    - Handles adversarial notation
    """

    def __init__(self) -> None:
        self._normalizer = NotationNormalizer()
        self._variables: Dict[str, float] = {}

    def set_variables(self, variables: Dict[str, float]) -> None:
        """Set variable bindings for evaluation."""
        self._variables = dict(variables)

    def exact_algebra(self, expression: str) -> MathResult:
        """Evaluate an algebraic expression exactly.

        Normalizes notation, evaluates via safe AST, returns Proof.
        """
        normalized = self._normalizer.normalize(expression)
        steps: List[ProofStep] = []
        assumptions: List[Assumption] = []

        if expression != normalized:
            steps.append(ProofStep(
                rule="notation_normalization",
                input_expr=expression,
                output_expr=normalized,
                justification="Adversarial/non-standard notation converted to canonical form",
            ))

        # Domain assumption: real numbers unless specified
        assumptions.append(Assumption(
            description="All variables are real-valued",
            domain="real",
            verified=True,
        ))

        try:
            value = safe_eval_expr(normalized, self._variables)
            steps.append(ProofStep(
                rule="safe_ast_evaluation",
                input_expr=normalized,
                output_expr=str(value),
                justification="Evaluated via AST-walking evaluator (no eval/exec)",
            ))
            proof = Proof(
                status=ProofStatus.VERIFIED,
                steps=steps,
                assumptions=assumptions,
                domain="real",
                result=str(value),
            )
            return MathResult(
                expression=expression,
                result=value,
                proof=proof,
                confidence="direct_fact",
            )
        except SafeMathError as exc:
            proof = Proof(
                status=ProofStatus.FAILED,
                steps=steps,
                assumptions=assumptions,
                domain="real",
                error=str(exc),
            )
            return MathResult(
                expression=expression,
                result=None,
                proof=proof,
                confidence="unsupported",
            )

    def symbolic_calculus(
        self,
        expression: str,
        operation: str = "differentiate",
        variable: str = "x",
    ) -> MathResult:
        """Perform symbolic differentiation or integration using rules.

        Supports power rule, constant rule, sum rule, product rule (basic).
        """
        normalized = self._normalizer.normalize(expression)
        steps: List[ProofStep] = []
        assumptions: List[Assumption] = [
            Assumption(
                description=f"Function is differentiable with respect to {variable}",
                domain="real",
                verified=False,
            ),
        ]

        # Basic symbolic differentiation via pattern matching
        result_expr: Optional[str] = None

        if operation == "differentiate":
            result_expr = self._differentiate(normalized, variable, steps)
        elif operation == "integrate":
            result_expr = self._integrate(normalized, variable, steps)
        else:
            proof = Proof(
                status=ProofStatus.FAILED,
                steps=steps,
                assumptions=assumptions,
                error=f"Unknown operation: {operation}",
            )
            return MathResult(expression=expression, result=None, proof=proof, confidence="unsupported")

        if result_expr is not None:
            proof = Proof(
                status=ProofStatus.VERIFIED,
                steps=steps,
                assumptions=assumptions,
                domain="real",
                result=result_expr,
            )
            return MathResult(
                expression=expression,
                result=result_expr,
                proof=proof,
                confidence="derived",
            )
        else:
            proof = Proof(
                status=ProofStatus.FAILED,
                steps=steps,
                assumptions=assumptions,
                domain="real",
                error="Expression not matched by known differentiation rules",
            )
            return MathResult(expression=expression, result=None, proof=proof, confidence="unsupported")

    def _differentiate(self, expr: str, var: str, steps: List[ProofStep]) -> Optional[str]:
        """Apply differentiation rules symbolically."""
        expr = expr.strip()

        # Constant
        try:
            float(expr)
            steps.append(ProofStep(
                rule="constant_rule",
                input_expr=f"d/d{var}({expr})",
                output_expr="0",
                justification="Derivative of a constant is 0",
            ))
            return "0"
        except ValueError:
            pass

        # Pure variable
        if expr == var:
            steps.append(ProofStep(
                rule="identity_rule",
                input_expr=f"d/d{var}({var})",
                output_expr="1",
                justification="d/dx(x) = 1",
            ))
            return "1"

        # Power rule: x**n or var**n
        if "**" in expr:
            parts = expr.split("**", 1)
            base = parts[0].strip()
            exp_str = parts[1].strip()
            if base == var:
                try:
                    n = float(exp_str)
                    new_coeff = n
                    new_exp = n - 1
                    if new_exp == 0:
                        result = str(int(new_coeff)) if new_coeff == int(new_coeff) else str(new_coeff)
                    elif new_exp == 1:
                        result = f"{int(new_coeff) if new_coeff == int(new_coeff) else new_coeff}*{var}"
                    else:
                        new_exp_s = str(int(new_exp)) if new_exp == int(new_exp) else str(new_exp)
                        coeff_s = str(int(new_coeff)) if new_coeff == int(new_coeff) else str(new_coeff)
                        result = f"{coeff_s}*{var}**{new_exp_s}"
                    steps.append(ProofStep(
                        rule="power_rule",
                        input_expr=f"d/d{var}({expr})",
                        output_expr=result,
                        justification=f"d/dx(x^n) = n*x^(n-1), n={n}",
                    ))
                    return result
                except ValueError:
                    pass

        # Coefficient * variable: c*x
        if "*" in expr and "**" not in expr:
            parts = expr.split("*", 1)
            left = parts[0].strip()
            right = parts[1].strip()
            try:
                coeff = float(left)
                if right == var:
                    result = str(int(coeff)) if coeff == int(coeff) else str(coeff)
                    steps.append(ProofStep(
                        rule="constant_multiple_rule",
                        input_expr=f"d/d{var}({expr})",
                        output_expr=result,
                        justification=f"d/dx(c*x) = c, c={coeff}",
                    ))
                    return result
            except ValueError:
                pass

        # Sum rule: expr + expr or expr - expr
        # Find top-level + or -
        depth = 0
        split_idx: Optional[int] = None
        split_op: Optional[str] = None
        for i, ch in enumerate(expr):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and ch in "+-" and i > 0:
                split_idx = i
                split_op = ch

        if split_idx is not None and split_op is not None:
            left_expr = expr[:split_idx].strip()
            right_expr = expr[split_idx + 1:].strip()
            left_deriv = self._differentiate(left_expr, var, steps)
            right_deriv = self._differentiate(right_expr, var, steps)
            if left_deriv is not None and right_deriv is not None:
                result = f"{left_deriv} {split_op} {right_deriv}"
                steps.append(ProofStep(
                    rule="sum_rule",
                    input_expr=f"d/d{var}({expr})",
                    output_expr=result,
                    justification="d/dx(f+g) = f' + g'",
                ))
                return result

        return None

    def _integrate(self, expr: str, var: str, steps: List[ProofStep]) -> Optional[str]:
        """Apply integration rules symbolically (power rule reverse)."""
        expr = expr.strip()

        # Constant
        try:
            c = float(expr)
            result = f"{int(c) if c == int(c) else c}*{var} + C"
            steps.append(ProofStep(
                rule="constant_integration",
                input_expr=f"∫({expr})d{var}",
                output_expr=result,
                justification="∫c dx = c*x + C",
            ))
            return result
        except ValueError:
            pass

        # Pure variable: ∫x dx = x²/2 + C
        if expr == var:
            result = f"{var}**2/2 + C"
            steps.append(ProofStep(
                rule="power_rule_integration",
                input_expr=f"∫({var})d{var}",
                output_expr=result,
                justification="∫x dx = x²/2 + C (power rule, n=1)",
            ))
            return result

        # Power rule: x**n -> x**(n+1)/(n+1) + C
        if "**" in expr:
            parts = expr.split("**", 1)
            base = parts[0].strip()
            exp_str = parts[1].strip()
            if base == var:
                try:
                    n = float(exp_str)
                    if n == -1:
                        result = f"ln(abs({var})) + C"
                        steps.append(ProofStep(
                            rule="reciprocal_integration",
                            input_expr=f"∫({expr})d{var}",
                            output_expr=result,
                            justification="∫x^(-1) dx = ln|x| + C",
                        ))
                    else:
                        new_exp = n + 1
                        new_exp_s = str(int(new_exp)) if new_exp == int(new_exp) else str(new_exp)
                        coeff_s = str(int(new_exp)) if new_exp == int(new_exp) else str(new_exp)
                        result = f"{var}**{new_exp_s}/{coeff_s} + C"
                        steps.append(ProofStep(
                            rule="power_rule_integration",
                            input_expr=f"∫({expr})d{var}",
                            output_expr=result,
                            justification=f"∫x^n dx = x^(n+1)/(n+1) + C, n={n}",
                        ))
                    return result
                except ValueError:
                    pass

        return None

    def discrete_math(
        self,
        operation: str,
        *,
        n: Optional[int] = None,
        k: Optional[int] = None,
        elements: Optional[List[Any]] = None,
    ) -> MathResult:
        """Discrete math operations: combinations, permutations, GCD, prime check, etc."""
        steps: List[ProofStep] = []
        assumptions: List[Assumption] = [
            Assumption(description="Inputs are non-negative integers", domain="natural", verified=True),
        ]

        result: Any = None
        expr_str = f"{operation}(n={n}, k={k})"

        if operation == "combination" and n is not None and k is not None:
            if k < 0 or k > n:
                result = 0
            else:
                result = math.comb(n, k)
            steps.append(ProofStep(
                rule="combination_formula",
                input_expr=f"C({n},{k})",
                output_expr=str(result),
                justification=f"C(n,k) = n! / (k!(n-k)!), computed as {result}",
            ))
        elif operation == "permutation" and n is not None and k is not None:
            if k < 0 or k > n:
                result = 0
            else:
                result = math.perm(n, k)
            steps.append(ProofStep(
                rule="permutation_formula",
                input_expr=f"P({n},{k})",
                output_expr=str(result),
                justification=f"P(n,k) = n! / (n-k)!, computed as {result}",
            ))
        elif operation == "factorial" and n is not None:
            if n < 0:
                proof = Proof(
                    status=ProofStatus.FAILED, steps=steps, assumptions=assumptions,
                    error="Factorial undefined for negative integers",
                )
                return MathResult(expression=expr_str, result=None, proof=proof, confidence="unsupported")
            result = math.factorial(n)
            steps.append(ProofStep(
                rule="factorial_computation",
                input_expr=f"{n}!",
                output_expr=str(result),
                justification=f"Direct computation of {n}!",
            ))
        elif operation == "gcd" and elements is not None and len(elements) >= 2:
            result = elements[0]
            for el in elements[1:]:
                result = math.gcd(int(result), int(el))
            steps.append(ProofStep(
                rule="euclidean_algorithm",
                input_expr=f"gcd({elements})",
                output_expr=str(result),
                justification="Computed via Euclidean algorithm",
            ))
        elif operation == "is_prime" and n is not None:
            if n < 2:
                result = False
            elif n < 4:
                result = True
            else:
                result = all(n % i != 0 for i in range(2, int(math.isqrt(n)) + 1))
            steps.append(ProofStep(
                rule="trial_division",
                input_expr=f"is_prime({n})",
                output_expr=str(result),
                justification=f"Trial division up to √{n}",
            ))
        else:
            proof = Proof(
                status=ProofStatus.FAILED, steps=steps, assumptions=assumptions,
                error=f"Unknown discrete math operation: {operation}",
            )
            return MathResult(expression=expr_str, result=None, proof=proof, confidence="unsupported")

        proof = Proof(
            status=ProofStatus.VERIFIED,
            steps=steps,
            assumptions=assumptions,
            domain="natural",
            result=str(result),
        )
        return MathResult(expression=expr_str, result=result, proof=proof, confidence="direct_fact")

    def proof_obligations(self, expression: str) -> List[Assumption]:
        """Return the list of assumptions required to prove a given expression.

        Useful for identifying what must be verified before trusting a result.
        """
        obligations: List[Assumption] = []
        normalized = self._normalizer.normalize(expression)

        # Division present → denominator non-zero
        if "/" in normalized:
            obligations.append(Assumption(
                description="Denominator is non-zero",
                domain="real",
                verified=False,
            ))

        # Square root → argument non-negative (real domain)
        if "sqrt" in normalized:
            obligations.append(Assumption(
                description="Argument of sqrt is non-negative (real domain)",
                domain="real",
                verified=False,
            ))

        # Logarithm → argument positive
        if "log" in normalized or "ln" in normalized:
            obligations.append(Assumption(
                description="Argument of logarithm is positive",
                domain="real",
                verified=False,
            ))

        # Power with fractional exponent → base non-negative
        if "**" in normalized:
            obligations.append(Assumption(
                description="Base is non-negative for fractional exponents (real domain)",
                domain="real",
                verified=False,
            ))

        # Default: real-valued
        obligations.append(Assumption(
            description="All variables are real-valued",
            domain="real",
            verified=False,
        ))

        return obligations
