"""Unit tests for Phase R7: Specialist engines."""

import math
from datetime import datetime, timedelta

import pytest

from axima.specialist.math_specialist import (
    MathSpecialist,
    MathResult,
    Proof,
    ProofStatus,
    SafeMathError,
    safe_eval_expr,
    NotationNormalizer,
)
from axima.specialist.physics_specialist import (
    PhysicsSpecialist,
    PhysicalQuantity,
    Dimension,
    Derivation,
    METER,
    KILOGRAM,
    SECOND,
    VELOCITY,
    ACCELERATION,
    ENERGY,
    FORCE,
    DIMENSIONLESS,
)
from axima.specialist.knowledge_specialist import (
    KnowledgeSpecialist,
    Fact,
    Citation,
    ConfidenceLevel,
    QueryResult,
)


# ===========================================================================
# Math Specialist Tests
# ===========================================================================

class TestSafeMathEvaluator:
    """Tests for the safe AST-based math evaluator."""

    def test_basic_arithmetic(self) -> None:
        assert safe_eval_expr("2 + 3") == 5.0
        assert safe_eval_expr("10 - 4") == 6.0
        assert safe_eval_expr("3 * 7") == 21.0
        assert safe_eval_expr("15 / 3") == 5.0

    def test_power(self) -> None:
        assert safe_eval_expr("2 ** 10") == 1024.0
        assert safe_eval_expr("3 ** 3") == 27.0

    def test_functions(self) -> None:
        assert abs(safe_eval_expr("sqrt(16)") - 4.0) < 1e-10
        assert abs(safe_eval_expr("abs(-5)") - 5.0) < 1e-10
        assert abs(safe_eval_expr("sin(0)") - 0.0) < 1e-10
        assert abs(safe_eval_expr("cos(0)") - 1.0) < 1e-10

    def test_variables(self) -> None:
        assert safe_eval_expr("x + y", {"x": 3, "y": 4}) == 7.0
        assert safe_eval_expr("x ** 2", {"x": 5}) == 25.0

    def test_constants(self) -> None:
        assert abs(safe_eval_expr("pi") - math.pi) < 1e-10
        assert abs(safe_eval_expr("e") - math.e) < 1e-10

    def test_rejects_unknown_names(self) -> None:
        with pytest.raises(SafeMathError, match="Unknown variable"):
            safe_eval_expr("undefined_var")

    def test_rejects_large_exponents(self) -> None:
        with pytest.raises(SafeMathError, match="Exponent too large"):
            safe_eval_expr("2 ** 10000")

    def test_rejects_invalid_syntax(self) -> None:
        with pytest.raises(SafeMathError, match="Parse error"):
            safe_eval_expr("2 +* 3")

    def test_nested_expressions(self) -> None:
        result = safe_eval_expr("sqrt(3**2 + 4**2)")
        assert abs(result - 5.0) < 1e-10

    def test_no_eval_bypass(self) -> None:
        """Ensure no code execution is possible."""
        with pytest.raises(SafeMathError):
            safe_eval_expr("__import__('os').system('echo pwned')")


class TestNotationNormalizer:
    """Tests for adversarial notation handling."""

    def test_unicode_operators(self) -> None:
        n = NotationNormalizer()
        assert "×" not in n.normalize("3×4")
        assert "*" in n.normalize("3×4")
        assert "÷" not in n.normalize("12÷3")
        assert "/" in n.normalize("12÷3")

    def test_superscript_exponents(self) -> None:
        n = NotationNormalizer()
        result = n.normalize("x²")
        assert "**2" in result

    def test_implicit_multiplication(self) -> None:
        n = NotationNormalizer()
        result = n.normalize("2x")
        assert "*" in result

    def test_sqrt_symbol(self) -> None:
        n = NotationNormalizer()
        result = n.normalize("√16")
        assert "sqrt" in result


class TestMathSpecialist:
    """Tests for the MathSpecialist class."""

    def test_exact_algebra_basic(self) -> None:
        ms = MathSpecialist()
        result = ms.exact_algebra("2 + 3 * 4")
        assert result.result == 14.0
        assert result.proof.status == ProofStatus.VERIFIED
        assert result.confidence == "direct_fact"

    def test_exact_algebra_with_variables(self) -> None:
        ms = MathSpecialist()
        ms.set_variables({"x": 5, "y": 3})
        result = ms.exact_algebra("x + y")
        assert result.result == 8.0
        assert result.proof.status == ProofStatus.VERIFIED

    def test_exact_algebra_adversarial_notation(self) -> None:
        ms = MathSpecialist()
        result = ms.exact_algebra("3×4")
        assert result.result == 12.0
        # Should have a normalization step in proof
        assert any(s.rule == "notation_normalization" for s in result.proof.steps)

    def test_exact_algebra_failure(self) -> None:
        ms = MathSpecialist()
        result = ms.exact_algebra("undefined_var + 1")
        assert result.result is None
        assert result.proof.status == ProofStatus.FAILED
        assert result.confidence == "unsupported"

    def test_symbolic_differentiation_power_rule(self) -> None:
        ms = MathSpecialist()
        result = ms.symbolic_calculus("x**3", operation="differentiate", variable="x")
        assert result.result == "3*x**2"
        assert result.proof.status == ProofStatus.VERIFIED

    def test_symbolic_differentiation_constant(self) -> None:
        ms = MathSpecialist()
        result = ms.symbolic_calculus("5", operation="differentiate", variable="x")
        assert result.result == "0"

    def test_symbolic_differentiation_variable(self) -> None:
        ms = MathSpecialist()
        result = ms.symbolic_calculus("x", operation="differentiate", variable="x")
        assert result.result == "1"

    def test_symbolic_integration_power_rule(self) -> None:
        ms = MathSpecialist()
        result = ms.symbolic_calculus("x**2", operation="integrate", variable="x")
        assert result.result is not None
        assert "x**3" in result.result
        assert "C" in result.result

    def test_discrete_math_combination(self) -> None:
        ms = MathSpecialist()
        result = ms.discrete_math("combination", n=10, k=3)
        assert result.result == 120
        assert result.proof.status == ProofStatus.VERIFIED

    def test_discrete_math_factorial(self) -> None:
        ms = MathSpecialist()
        result = ms.discrete_math("factorial", n=5)
        assert result.result == 120

    def test_discrete_math_prime(self) -> None:
        ms = MathSpecialist()
        result = ms.discrete_math("is_prime", n=17)
        assert result.result is True
        result2 = ms.discrete_math("is_prime", n=15)
        assert result2.result is False

    def test_proof_obligations(self) -> None:
        ms = MathSpecialist()
        obligations = ms.proof_obligations("sqrt(x) / y")
        descriptions = [o.description for o in obligations]
        assert any("non-negative" in d for d in descriptions)
        assert any("non-zero" in d for d in descriptions)


# ===========================================================================
# Physics Specialist Tests
# ===========================================================================

class TestPhysicsSpecialist:
    """Tests for the PhysicsSpecialist class."""

    def test_solve_newton_second_law(self) -> None:
        ps = PhysicsSpecialist()
        result = ps.solve_with_units("newton_second", {
            "m": PhysicalQuantity(10.0, KILOGRAM, "kg"),
            "a": PhysicalQuantity(3.0, ACCELERATION, "m/s^2"),
        })
        assert result.valid
        assert result.result is not None
        assert abs(result.result.value - 30.0) < 1e-10
        assert result.result.dimension == FORCE

    def test_solve_kinetic_energy(self) -> None:
        ps = PhysicsSpecialist()
        result = ps.solve_with_units("kinetic_energy", {
            "m": PhysicalQuantity(2.0, KILOGRAM, "kg"),
            "v": PhysicalQuantity(3.0, VELOCITY, "m/s"),
        })
        assert result.valid
        assert result.result is not None
        assert abs(result.result.value - 9.0) < 1e-10  # 0.5 * 2 * 9

    def test_dimensional_check_fails(self) -> None:
        ps = PhysicsSpecialist()
        # Pass velocity where mass is expected
        result = ps.solve_with_units("newton_second", {
            "m": PhysicalQuantity(10.0, VELOCITY, "m/s"),  # wrong dimension!
            "a": PhysicalQuantity(3.0, ACCELERATION, "m/s^2"),
        })
        assert not result.valid
        assert "Dimensional inconsistency" in (result.error or "")

    def test_dimensional_analysis_multiply(self) -> None:
        ps = PhysicsSpecialist()
        dim, err = ps.dimensional_analysis([
            PhysicalQuantity(5.0, KILOGRAM, "kg"),
            PhysicalQuantity(3.0, ACCELERATION, "m/s^2"),
        ], operation="multiply")
        assert err is None
        assert dim == FORCE

    def test_dimensional_analysis_add_mismatch(self) -> None:
        ps = PhysicsSpecialist()
        _, err = ps.dimensional_analysis([
            PhysicalQuantity(5.0, KILOGRAM, "kg"),
            PhysicalQuantity(3.0, METER, "m"),
        ], operation="add")
        assert err is not None
        assert "dimensions differ" in err.context

    def test_uncertainty_propagation(self) -> None:
        ps = PhysicsSpecialist()
        result = ps.solve_with_units("newton_second", {
            "m": PhysicalQuantity(10.0, KILOGRAM, "kg", uncertainty=0.1),
            "a": PhysicalQuantity(3.0, ACCELERATION, "m/s^2", uncertainty=0.05),
        })
        assert result.valid
        assert result.result is not None
        assert result.result.uncertainty is not None
        assert result.result.uncertainty > 0

    def test_unknown_equation(self) -> None:
        ps = PhysicsSpecialist()
        result = ps.solve_with_units("nonexistent_law", {})
        assert not result.valid
        assert "Unknown equation" in (result.error or "")

    def test_derive(self) -> None:
        ps = PhysicsSpecialist()
        result = ps.derive(
            target="force",
            given={
                "m": PhysicalQuantity(5.0, KILOGRAM, "kg"),
                "a": PhysicalQuantity(2.0, ACCELERATION, "m/s^2"),
            },
            assumptions=["Object is in free fall"],
        )
        assert result.valid
        assert result.result is not None
        assert abs(result.result.value - 10.0) < 1e-10


# ===========================================================================
# Knowledge Specialist Tests
# ===========================================================================

class TestKnowledgeSpecialist:
    """Tests for the KnowledgeSpecialist class."""

    def setup_method(self) -> None:
        self.ks = KnowledgeSpecialist()
        self.ks.add_facts([
            Fact(
                statement="Python was created by Guido van Rossum in 1991",
                citations=[Citation(source="Wikipedia", section="History")],
                confidence=ConfidenceLevel.HIGH,
                domain="programming",
            ),
            Fact(
                statement="The speed of light is approximately 299792458 meters per second",
                citations=[Citation(source="NIST", section="Constants")],
                confidence=ConfidenceLevel.HIGH,
                domain="physics",
            ),
            Fact(
                statement="Water boils at 100 degrees Celsius at sea level",
                citations=[Citation(source="Chemistry Textbook", page=42)],
                confidence=ConfidenceLevel.HIGH,
                domain="chemistry",
            ),
        ])

    def test_factual_query_found(self) -> None:
        result = self.ks.factual_query("Who created Python?")
        assert result.answer is not None
        assert "Guido" in result.answer
        assert result.confidence != ConfidenceLevel.ABSTAIN
        assert result.truth_label == "direct_fact"

    def test_factual_query_not_found(self) -> None:
        result = self.ks.factual_query("What is the capital of Mars?")
        assert result.confidence == ConfidenceLevel.ABSTAIN
        assert result.abstention_reason is not None
        assert result.truth_label == "unsupported"

    def test_temporal_query_valid(self) -> None:
        self.ks.add_fact(Fact(
            statement="The current president is Example Person",
            citations=[Citation(source="News")],
            confidence=ConfidenceLevel.HIGH,
            valid_from=datetime(2024, 1, 1),
            valid_until=datetime(2028, 12, 31),
        ))
        result = self.ks.temporal_query(
            "Who is the current president?",
            as_of=datetime(2025, 6, 1),
        )
        assert result.answer is not None

    def test_temporal_query_expired(self) -> None:
        self.ks.add_fact(Fact(
            statement="The old president was Previous Person",
            citations=[Citation(source="Archive")],
            confidence=ConfidenceLevel.HIGH,
            valid_from=datetime(2016, 1, 1),
            valid_until=datetime(2020, 1, 1),
        ))
        result = self.ks.temporal_query(
            "Who is the old president?",
            as_of=datetime(2023, 1, 1),
        )
        assert result.confidence == ConfidenceLevel.ABSTAIN

    def test_contradiction_detection(self) -> None:
        facts = [
            Fact(statement="The earth is round", domain="geography"),
            Fact(statement="The earth is not round", domain="geography"),
        ]
        contradictions = self.ks.contradiction_check(facts)
        assert len(contradictions) > 0
        assert "contradiction" in contradictions[0].description.lower() or "Negation" in contradictions[0].description

    def test_no_contradiction(self) -> None:
        facts = [
            Fact(statement="Water is wet", domain="physics"),
            Fact(statement="Fire is hot", domain="physics"),
        ]
        contradictions = self.ks.contradiction_check(facts)
        assert len(contradictions) == 0
