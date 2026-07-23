"""Comprehensive tests for safe_math.py — the typed AST math evaluator.

At least 50 test cases covering:
- Basic arithmetic
- All allowed functions
- Injection attempts
- Resource limits
- Domain errors
"""

from __future__ import annotations

import math

import pytest

from axima.errors import EvalError, ParseError, SecurityError
from axima.security.safe_math import (
    ALLOWED_FUNCTIONS,
    BinOpNode,
    FunctionCallNode,
    MathEvaluator,
    MathParser,
    NumberNode,
    UnaryOpNode,
    VariableNode,
    safe_eval,
)


# ===========================================================================
# Basic Arithmetic (tests 1-15)
# ===========================================================================


class TestBasicArithmetic:
    """Test fundamental arithmetic operations."""

    def test_integer_addition(self) -> None:
        assert safe_eval("2 + 3") == 5.0

    def test_integer_subtraction(self) -> None:
        assert safe_eval("10 - 7") == 3.0

    def test_integer_multiplication(self) -> None:
        assert safe_eval("4 * 5") == 20.0

    def test_integer_division(self) -> None:
        assert safe_eval("20 / 4") == 5.0

    def test_float_division(self) -> None:
        result = safe_eval("7 / 2")
        assert result == 3.5

    def test_floor_division(self) -> None:
        assert safe_eval("7 // 2") == 3.0

    def test_modulo(self) -> None:
        assert safe_eval("17 % 5") == 2.0

    def test_power(self) -> None:
        assert safe_eval("2 ** 10") == 1024.0

    def test_caret_as_power(self) -> None:
        assert safe_eval("2 ^ 10") == 1024.0

    def test_negative_number(self) -> None:
        assert safe_eval("-5") == -5.0

    def test_double_negative(self) -> None:
        assert safe_eval("--5") == 5.0

    def test_operator_precedence(self) -> None:
        assert safe_eval("2 + 3 * 4") == 14.0

    def test_parentheses(self) -> None:
        assert safe_eval("(2 + 3) * 4") == 20.0

    def test_nested_parentheses(self) -> None:
        assert safe_eval("((2 + 3) * (4 - 1))") == 15.0

    def test_complex_expression(self) -> None:
        result = safe_eval("2 ** 3 + 4 * 5 - 10 / 2")
        # 8 + 20 - 5 = 23
        assert result == 23.0

    def test_float_literal(self) -> None:
        assert safe_eval("3.14") == pytest.approx(3.14)

    def test_scientific_notation(self) -> None:
        assert safe_eval("1.5e2") == 150.0

    def test_scientific_notation_negative_exp(self) -> None:
        assert safe_eval("1.5e-2") == pytest.approx(0.015)


# ===========================================================================
# Constants (tests 16-17)
# ===========================================================================


class TestConstants:
    """Test built-in constants."""

    def test_pi(self) -> None:
        assert safe_eval("pi") == pytest.approx(math.pi)

    def test_e(self) -> None:
        assert safe_eval("e") == pytest.approx(math.e)


# ===========================================================================
# Functions (tests 18-35)
# ===========================================================================


class TestFunctions:
    """Test all allowed mathematical functions."""

    def test_sin(self) -> None:
        assert safe_eval("sin(0)") == pytest.approx(0.0)

    def test_sin_pi_half(self) -> None:
        assert safe_eval("sin(pi / 2)") == pytest.approx(1.0)

    def test_cos(self) -> None:
        assert safe_eval("cos(0)") == pytest.approx(1.0)

    def test_tan(self) -> None:
        assert safe_eval("tan(0)") == pytest.approx(0.0)

    def test_sqrt(self) -> None:
        assert safe_eval("sqrt(16)") == 4.0

    def test_sqrt_float(self) -> None:
        assert safe_eval("sqrt(2)") == pytest.approx(math.sqrt(2))

    def test_abs_positive(self) -> None:
        assert safe_eval("abs(5)") == 5.0

    def test_abs_negative(self) -> None:
        assert safe_eval("abs(-5)") == 5.0

    def test_log_natural(self) -> None:
        # log() is now log base 10 (common convention); use ln() for natural log
        assert safe_eval("log(10)") == pytest.approx(1.0)
        assert safe_eval("log(100)") == pytest.approx(2.0)
        assert safe_eval("ln(e)") == pytest.approx(1.0)

    def test_log_base(self) -> None:
        assert safe_eval("log(100, 10)") == pytest.approx(2.0)

    def test_ln(self) -> None:
        assert safe_eval("ln(e)") == pytest.approx(1.0)

    def test_exp(self) -> None:
        assert safe_eval("exp(0)") == 1.0

    def test_exp_1(self) -> None:
        assert safe_eval("exp(1)") == pytest.approx(math.e)

    def test_factorial(self) -> None:
        assert safe_eval("factorial(5)") == 120.0

    def test_factorial_zero(self) -> None:
        assert safe_eval("factorial(0)") == 1.0

    def test_gcd(self) -> None:
        assert safe_eval("gcd(12, 8)") == 4.0

    def test_lcm(self) -> None:
        assert safe_eval("lcm(4, 6)") == 12.0

    def test_floor(self) -> None:
        assert safe_eval("floor(3.7)") == 3.0

    def test_ceil(self) -> None:
        assert safe_eval("ceil(3.2)") == 4.0

    def test_round(self) -> None:
        assert safe_eval("round(3.567, 2)") == pytest.approx(3.57)

    def test_nested_functions(self) -> None:
        assert safe_eval("sqrt(abs(-16))") == 4.0

    def test_function_in_expression(self) -> None:
        assert safe_eval("2 * sin(pi / 6) + 1") == pytest.approx(2.0)


# ===========================================================================
# Variables (tests 36-38)
# ===========================================================================


class TestVariables:
    """Test variable substitution."""

    def test_simple_variable(self) -> None:
        assert safe_eval("x + 1", {"x": 5.0}) == 6.0

    def test_multiple_variables(self) -> None:
        result = safe_eval("x * y + z", {"x": 2.0, "y": 3.0, "z": 1.0})
        assert result == 7.0

    def test_undefined_variable(self) -> None:
        with pytest.raises(EvalError, match="Undefined variable"):
            safe_eval("x + 1")


# ===========================================================================
# Injection Attempts (tests 39-52)
# ===========================================================================


class TestInjectionAttempts:
    """Test that code injection attempts are blocked."""

    def test_import_os(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("import os")

    def test_dunder_import(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("__import__('os')")

    def test_eval_call(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("eval('1+1')")

    def test_exec_call(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("exec('print(1)')")

    def test_compile_call(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("compile('x', '', 'eval')")

    def test_dunder_class(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("().__class__.__bases__")

    def test_os_system(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("os.system('ls')")

    def test_subprocess(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("subprocess.run(['ls'])")

    def test_open_file(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("open('/etc/passwd')")

    def test_globals_access(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("globals()['os']")

    def test_lambda(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("lambda: 1")

    def test_semicolon_injection(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("1; import os")

    def test_bracket_access(self) -> None:
        with pytest.raises(SecurityError, match="[Ii]njection"):
            safe_eval("a[0]")

    def test_disallowed_function(self) -> None:
        with pytest.raises(SecurityError, match="not allowed"):
            safe_eval("system(1)")


# ===========================================================================
# Domain Errors (tests 53-59)
# ===========================================================================


class TestDomainErrors:
    """Test domain checking catches invalid math operations."""

    def test_division_by_zero(self) -> None:
        with pytest.raises(EvalError, match="[Dd]ivision by zero"):
            safe_eval("1 / 0")

    def test_floor_division_by_zero(self) -> None:
        with pytest.raises(EvalError, match="[Dd]ivision by zero"):
            safe_eval("1 // 0")

    def test_modulo_by_zero(self) -> None:
        with pytest.raises(EvalError, match="[Mm]odulo by zero"):
            safe_eval("5 % 0")

    def test_sqrt_negative(self) -> None:
        with pytest.raises(EvalError, match="[Dd]omain|negative"):
            safe_eval("sqrt(-1)")

    def test_log_zero(self) -> None:
        with pytest.raises(EvalError, match="[Dd]omain|non-positive"):
            safe_eval("log(0)")

    def test_log_negative(self) -> None:
        with pytest.raises(EvalError, match="[Dd]omain|non-positive"):
            safe_eval("log(-5)")

    def test_factorial_negative(self) -> None:
        with pytest.raises(EvalError, match="[Dd]omain|non-negative"):
            safe_eval("factorial(-1)")


# ===========================================================================
# Resource Limits (tests 60-65)
# ===========================================================================


class TestResourceLimits:
    """Test resource limit enforcement."""

    def test_expression_too_long(self) -> None:
        expr = "1 + " * 1000 + "1"
        with pytest.raises(ParseError, match="too long"):
            safe_eval(expr)

    def test_huge_exponent(self) -> None:
        with pytest.raises(EvalError, match="[Ee]xponent too large"):
            safe_eval("2 ** 5000")

    def test_value_overflow(self) -> None:
        # 10^400 exceeds 1e308
        with pytest.raises(EvalError, match="[Ee]xponent too large|[Bb]ounds|[Oo]verflow"):
            safe_eval("10 ** 400")

    def test_factorial_too_large(self) -> None:
        with pytest.raises(EvalError, match="[Oo]verflow|too large"):
            safe_eval("factorial(200)")

    def test_exp_overflow(self) -> None:
        with pytest.raises(EvalError, match="[Oo]verflow"):
            safe_eval("exp(1000)")

    def test_many_tokens(self) -> None:
        # Generate expression with > 500 tokens
        expr = "+".join(["1"] * 600)
        with pytest.raises(ParseError, match="[Tt]oo many tokens|too long"):
            safe_eval(expr)


# ===========================================================================
# Parser Edge Cases (tests 66-72)
# ===========================================================================


class TestParserEdgeCases:
    """Test parser handles edge cases correctly."""

    def test_empty_expression(self) -> None:
        with pytest.raises(ParseError):
            safe_eval("")

    def test_only_whitespace(self) -> None:
        with pytest.raises(ParseError):
            safe_eval("   ")

    def test_unclosed_paren(self) -> None:
        with pytest.raises(ParseError):
            safe_eval("(2 + 3")

    def test_extra_paren(self) -> None:
        with pytest.raises(ParseError):
            safe_eval("2 + 3)")

    def test_consecutive_operators(self) -> None:
        # "2 + * 3" should fail
        with pytest.raises(ParseError):
            safe_eval("2 + * 3")

    def test_trailing_operator(self) -> None:
        with pytest.raises(ParseError):
            safe_eval("2 + 3 +")

    def test_invalid_character(self) -> None:
        with pytest.raises((ParseError, SecurityError)):
            safe_eval("2 @ 3")


# ===========================================================================
# AST Structure (tests 73-75)
# ===========================================================================


class TestASTStructure:
    """Test that parser produces correct AST nodes."""

    def test_number_node(self) -> None:
        parser = MathParser("42")
        ast = parser.parse()
        assert isinstance(ast, NumberNode)
        assert ast.value == 42.0

    def test_binop_node(self) -> None:
        parser = MathParser("2 + 3")
        ast = parser.parse()
        assert isinstance(ast, BinOpNode)
        assert ast.op == "+"
        assert isinstance(ast.left, NumberNode)
        assert isinstance(ast.right, NumberNode)

    def test_function_node(self) -> None:
        parser = MathParser("sin(1)")
        ast = parser.parse()
        assert isinstance(ast, FunctionCallNode)
        assert ast.name == "sin"
        assert len(ast.args) == 1


# ===========================================================================
# Integration / Real-world expressions (tests 76-80)
# ===========================================================================


class TestRealWorldExpressions:
    """Test expressions that the math engine would actually receive."""

    def test_quadratic_formula_discriminant(self) -> None:
        # b^2 - 4ac with a=1, b=5, c=6
        result = safe_eval("b**2 - 4*a*c", {"a": 1.0, "b": 5.0, "c": 6.0})
        assert result == 1.0

    def test_distance_formula(self) -> None:
        result = safe_eval(
            "sqrt((x2-x1)**2 + (y2-y1)**2)",
            {"x1": 0.0, "x2": 3.0, "y1": 0.0, "y2": 4.0},
        )
        assert result == 5.0

    def test_compound_interest(self) -> None:
        # A = P(1 + r/n)^(nt)
        result = safe_eval(
            "P * (1 + r/n) ** (n*t)",
            {"P": 1000.0, "r": 0.05, "n": 12.0, "t": 1.0},
        )
        assert result == pytest.approx(1051.16, rel=1e-2)

    def test_trig_identity(self) -> None:
        # sin^2(x) + cos^2(x) = 1
        result = safe_eval("sin(x)**2 + cos(x)**2", {"x": 1.23})
        assert result == pytest.approx(1.0)

    def test_euler_formula_magnitude(self) -> None:
        # |e^(ix)| = 1, approximated as sqrt(cos(x)^2 + sin(x)^2)
        result = safe_eval("sqrt(cos(x)**2 + sin(x)**2)", {"x": 2.7})
        assert result == pytest.approx(1.0)
