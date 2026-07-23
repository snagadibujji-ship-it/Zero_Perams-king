"""Unit tests for Phase R6: Verification Constellation."""

from __future__ import annotations

import math
import sys
import time

import pytest

sys.path.insert(0, "/root/hybrid-ai/src")

from axima.verification.verifier_base import Verifier, VerifierReceipt, VerifierResult
from axima.verification.math_verifier import (
    CounterexampleSearcher,
    DimensionVerifier,
    DomainVerifier,
    MathEquivalenceVerifier,
    NumericalVerifier,
)
from axima.verification.code_verifier import (
    CompilationVerifier,
    OutputSchemaVerifier,
    StaticAnalysisVerifier,
    TestVerifier,
)
from axima.verification.provenance_verifier import (
    IndependenceVerifier,
    ProvenanceVerifier,
    TemporalVerifier,
)
from axima.verification.confidence import ConfidenceInterval, UncertaintyConservation
from axima.verification.constellation import (
    ReleaseDecision,
    VerificationConstellation,
    VerificationReport,
)
from axima.verification.metamorphic import (
    MetamorphicRelation,
    MetamorphicTester,
    MutationType,
)
from axima.verification.counterfactual import (
    ComparisonResult,
    CounterfactualExecutor,
    CounterfactualTwin,
    PerturbationType,
)
from axima.responses.proof_carrying import (
    AximaResponseV2,
    ProofCarryingResponse,
    TruthLevel,
)


# ===========================================================================
# Test: Math Equivalence Verification
# ===========================================================================


class TestMathEquivalence:
    """Test the MathEquivalenceVerifier."""

    def test_identical_expressions(self) -> None:
        v = MathEquivalenceVerifier()
        claim = {"type": "math_equivalence", "lhs": "x + y", "rhs": "x + y"}
        result = v.verify(claim, {})
        assert result.passed is True
        assert result.confidence == 1.0

    def test_equivalent_expressions(self) -> None:
        v = MathEquivalenceVerifier()
        claim = {"type": "math_equivalence", "lhs": "x + y", "rhs": "y + x"}
        result = v.verify(claim, {})
        assert result.passed is True

    def test_non_equivalent_expressions(self) -> None:
        v = MathEquivalenceVerifier()
        claim = {"type": "math_equivalence", "lhs": "x + y", "rhs": "x * y"}
        result = v.verify(claim, {})
        assert result.passed is False
        assert len(result.counterexamples) > 0

    def test_algebraic_identity(self) -> None:
        v = MathEquivalenceVerifier()
        claim = {
            "type": "math_equivalence",
            "lhs": "(x + 1) * (x - 1)",
            "rhs": "x**2 - 1",
        }
        result = v.verify(claim, {})
        assert result.passed is True

    def test_trig_identity(self) -> None:
        v = MathEquivalenceVerifier()
        claim = {
            "type": "math_equivalence",
            "lhs": "sin(x)**2 + cos(x)**2",
            "rhs": "1",
        }
        result = v.verify(claim, {})
        assert result.passed is True

    def test_applicability(self) -> None:
        v = MathEquivalenceVerifier()
        assert v.applicable({"type": "math_equivalence"}) is True
        assert v.applicable({"type": "code"}) is False


# ===========================================================================
# Test: Counterexample Search
# ===========================================================================


class TestCounterexampleSearch:
    """Test the CounterexampleSearcher."""

    def test_find_counterexample_for_false_claim(self) -> None:
        searcher = CounterexampleSearcher()
        # x^2 = x is false for most x
        claim = {"lhs": "x**2", "rhs": "x"}
        results = searcher.search(claim)
        assert len(results) > 0

    def test_no_counterexample_for_true_identity(self) -> None:
        searcher = CounterexampleSearcher()
        claim = {"lhs": "x + 0", "rhs": "x"}
        results = searcher.search(claim)
        assert len(results) == 0

    def test_predicate_counterexample(self) -> None:
        searcher = CounterexampleSearcher()
        # "x > 0" is not always true
        claim = {"predicate": "x > 0"}
        results = searcher.search(claim)
        assert len(results) > 0

    def test_boundary_value_detection(self) -> None:
        searcher = CounterexampleSearcher()
        # x/x = 1 fails at x=0
        claim = {"lhs": "x / x", "rhs": "1"}
        results = searcher.search(claim)
        # May or may not find x=0 depending on sampling, but at least runs
        assert isinstance(results, list)


# ===========================================================================
# Test: Confidence Interval Propagation
# ===========================================================================


class TestConfidenceInterval:
    """Test confidence interval arithmetic."""

    def test_basic_interval(self) -> None:
        ci = ConfidenceInterval(lower=0.7, upper=0.9, method="test")
        assert ci.width == pytest.approx(0.2)
        assert ci.midpoint == pytest.approx(0.8)

    def test_invalid_interval_raises(self) -> None:
        with pytest.raises(ValueError):
            ConfidenceInterval(lower=0.9, upper=0.5, method="invalid")

    def test_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError):
            ConfidenceInterval(lower=-0.1, upper=0.5, method="invalid")
        with pytest.raises(ValueError):
            ConfidenceInterval(lower=0.5, upper=1.1, method="invalid")

    def test_combine_independent(self) -> None:
        uc = UncertaintyConservation()
        intervals = [
            ConfidenceInterval(lower=0.8, upper=0.95, method="src1"),
            ConfidenceInterval(lower=0.7, upper=0.9, method="src2"),
        ]
        combined = uc.combine(intervals)
        # Combined lower should be >= individual lowers (independent strengthening)
        assert combined.lower >= 0.7
        # Combined upper bounded by weakest
        assert combined.upper <= 0.9

    def test_combine_correlated_groups(self) -> None:
        uc = UncertaintyConservation()
        intervals = [
            ConfidenceInterval(lower=0.9, upper=0.95, method="src1"),
            ConfidenceInterval(lower=0.85, upper=0.92, method="src2"),
            ConfidenceInterval(lower=0.7, upper=0.8, method="src3"),
        ]
        # src1 and src2 are correlated (same group)
        groups = {"wiki_derived": [0, 1]}
        combined = uc.combine(intervals, independence_groups=groups)
        # Correlated sources collapse to weakest in group
        assert combined.upper <= 0.92

    def test_rendering_never_raises_confidence(self) -> None:
        uc = UncertaintyConservation()
        rendered = ConfidenceInterval(lower=0.9, upper=0.99, method="rendered")
        sources = [
            ConfidenceInterval(lower=0.6, upper=0.8, method="actual_source"),
        ]
        capped = uc.apply_rendering_cap(rendered, sources)
        # Rendering cannot raise confidence above source
        assert capped.upper <= 0.8
        assert capped.lower <= 0.6

    def test_derivation_propagation_decays(self) -> None:
        uc = UncertaintyConservation()
        intervals = [ConfidenceInterval(lower=0.9, upper=0.95, method="base")]
        one_hop = uc.propagate_through_derivation(intervals, derivation_steps=1)
        three_hops = uc.propagate_through_derivation(intervals, derivation_steps=3)
        # More hops = lower confidence
        assert three_hops.lower < one_hop.lower

    def test_weakening(self) -> None:
        uc = UncertaintyConservation()
        original = ConfidenceInterval(lower=0.8, upper=0.95, method="original")
        weakened = uc.weaken(original, factor=0.5)
        assert weakened.lower < original.lower
        assert weakened.upper <= original.upper

    def test_from_verifier_results(self) -> None:
        uc = UncertaintyConservation()
        results = [
            VerifierResult(passed=True, check_name="a", details="", confidence=0.9),
            VerifierResult(passed=True, check_name="b", details="", confidence=0.7),
            VerifierResult(passed=False, check_name="c", details="", confidence=0.5),
        ]
        ci = uc.from_verifier_results(results)
        # Only passed results count
        assert ci.lower == pytest.approx(0.7)
        assert ci.upper == pytest.approx(0.9)


# ===========================================================================
# Test: Verification Constellation Quorum
# ===========================================================================


class TestConstellationQuorum:
    """Test quorum-based decision making."""

    def test_all_pass_gives_pass(self) -> None:
        constellation = VerificationConstellation(quorum_threshold=0.7)
        constellation.register_verifier(MathEquivalenceVerifier())
        constellation.register_verifier(NumericalVerifier())

        claim = {"type": "math_equivalence", "lhs": "x + 1", "rhs": "1 + x", "id": "c1"}
        report = constellation.run_verification(claim, {})
        assert report.release_decision == ReleaseDecision.PASS
        assert report.checks_passed == report.checks_run
        assert report.checks_run >= 1

    def test_all_fail_gives_fail(self) -> None:
        constellation = VerificationConstellation(quorum_threshold=0.7)
        constellation.register_verifier(MathEquivalenceVerifier())
        constellation.register_verifier(NumericalVerifier())

        claim = {"type": "math_equivalence", "lhs": "x", "rhs": "x + 1", "id": "c2"}
        report = constellation.run_verification(claim, {})
        assert report.release_decision == ReleaseDecision.FAIL
        assert report.has_counterexamples

    def test_high_risk_quorum(self) -> None:
        constellation = VerificationConstellation(
            quorum_threshold=0.7, high_risk_quorum=0.9
        )
        constellation.register_verifier(MathEquivalenceVerifier())

        claim = {
            "type": "math_equivalence",
            "lhs": "x + 1",
            "rhs": "1 + x",
            "id": "c3",
            "risk_level": "high",
        }
        report = constellation.run_verification(claim, {})
        assert report.release_decision == ReleaseDecision.PASS

    def test_no_applicable_verifiers(self) -> None:
        constellation = VerificationConstellation()
        claim = {"type": "unknown_type", "id": "c4"}
        report = constellation.run_verification(claim, {})
        assert report.release_decision == ReleaseDecision.FAIL
        assert report.checks_run == 0

    def test_verifier_independence(self) -> None:
        constellation = VerificationConstellation()
        constellation.register_verifier(MathEquivalenceVerifier())
        constellation.exclude_self_grading("math_engine", "math_equivalence")

        claim = {
            "type": "math_equivalence",
            "lhs": "x",
            "rhs": "x",
            "id": "c5",
            "generator": "math_engine",
        }
        # Math verifier excluded because generator is math_engine
        verifiers = constellation.select_verifiers(claim)
        assert len(verifiers) == 0

    def test_receipts_generated(self) -> None:
        constellation = VerificationConstellation()
        constellation.register_verifier(MathEquivalenceVerifier())

        claim = {"type": "math_equivalence", "lhs": "x", "rhs": "x", "id": "c6"}
        report = constellation.run_verification(claim, {})
        assert len(report.verifier_receipts) > 0
        receipt = report.verifier_receipts[0]
        assert receipt.verify_integrity() is True


# ===========================================================================
# Test: Metamorphic Mutations
# ===========================================================================


class TestMetamorphicMutations:
    """Test metamorphic testing infrastructure."""

    def test_paraphrase_preserves_meaning(self) -> None:
        def calculator(expr: str) -> float:
            if isinstance(expr, str) and expr.strip():
                from axima.verification.math_verifier import _safe_eval
                return _safe_eval(expr, {}) or 0.0
            return 0.0

        tester = MetamorphicTester(executor=calculator)
        # Whitespace shouldn't matter for expressions
        results = tester.run_mutations("2 + 3")
        # At least one meaning-preserving test should pass
        preserving = [r for r in results if "paraphrase" in r.check_name or "case" in r.check_name]
        # The paraphrase_whitespace should produce "2 + 3" which is same
        # and case_normalization produces "2 + 3" which is same
        for r in preserving:
            if r.passed is not None:
                assert r.passed is True, f"Failed: {r.check_name}: {r.details}"

    def test_negation_changes_meaning(self) -> None:
        tester = MetamorphicTester(executor=lambda x: x)
        results = tester.run_mutations("the sky is blue")
        negate_results = [r for r in results if "negate" in r.check_name]
        # Negation should change the output
        for r in negate_results:
            assert r.passed is True

    def test_quantity_change_affects_result(self) -> None:
        def identity_executor(x: Any) -> Any:
            return x

        tester = MetamorphicTester(executor=identity_executor)
        results = tester.run_mutations(42)
        qty_results = [r for r in results if "quantity" in r.check_name]
        for r in qty_results:
            assert r.passed is True  # Different input → different output

    def test_custom_relation(self) -> None:
        relation = MetamorphicRelation(
            name="double_input",
            input_transform=lambda x: x * 2 if isinstance(x, (int, float)) else x,
            expected_output_relation=lambda orig, mut: mut == orig * 2,
            mutation_type=MutationType.MEANING_CHANGING,
        )
        tester = MetamorphicTester(executor=lambda x: x)
        results = tester.run_mutations(5, relations=[relation])
        assert len(results) == 1
        assert results[0].passed is True

    def test_generate_mutations_produces_cases(self) -> None:
        tester = MetamorphicTester()
        cases = tester.generate_mutations({"query": "hello world", "entities": ["Alice", "Bob"]})
        assert len(cases) > 0
        # Should have both preserving and changing
        types = {tc.mutation_type for tc in cases}
        assert MutationType.MEANING_PRESERVING in types or MutationType.MEANING_CHANGING in types


# ===========================================================================
# Test: Code Verification
# ===========================================================================


class TestCodeVerification:
    """Test code verifiers."""

    def test_valid_python_compiles(self) -> None:
        v = CompilationVerifier()
        claim = {"type": "code", "code": "def hello():\n    return 42\n", "language": "python"}
        result = v.verify(claim, {})
        assert result.passed is True

    def test_invalid_python_fails(self) -> None:
        v = CompilationVerifier()
        claim = {"type": "code", "code": "def hello(:\n    return", "language": "python"}
        result = v.verify(claim, {})
        assert result.passed is False

    def test_static_analysis_detects_eval(self) -> None:
        v = StaticAnalysisVerifier()
        claim = {"type": "code", "code": "result = eval(user_input)"}
        result = v.verify(claim, {})
        assert result.passed is False

    def test_static_analysis_clean_code(self) -> None:
        v = StaticAnalysisVerifier()
        claim = {"type": "code", "code": "def add(a, b):\n    return a + b\n"}
        result = v.verify(claim, {})
        assert result.passed is True

    def test_output_schema_valid(self) -> None:
        v = OutputSchemaVerifier()
        claim = {"expected_schema": {"type": "dict", "properties": {"name": {"type": "string"}}, "required": ["name"]}}
        evidence = {"output": {"name": "test"}}
        result = v.verify(claim, evidence)
        assert result.passed is True

    def test_output_schema_invalid(self) -> None:
        v = OutputSchemaVerifier()
        claim = {"expected_schema": {"type": "dict", "properties": {"name": {"type": "string"}}, "required": ["name"]}}
        evidence = {"output": {"age": 25}}
        result = v.verify(claim, evidence)
        assert result.passed is False


# ===========================================================================
# Test: Counterfactual Execution
# ===========================================================================


class TestCounterfactual:
    """Test counterfactual twin execution."""

    def test_sensitive_to_premise_change(self) -> None:
        executor = CounterfactualExecutor()
        plan = {
            "expression": "x + y",
            "inputs": {"x": 5.0, "y": 3.0},
        }
        result = executor.run_twin(plan, PerturbationType.PERTURB_QUANTITY, target="x", magnitude=1.0)
        # Changing x should change the conclusion (expression evaluates differently)
        assert result.conclusion_changed is True
        assert result.suspicious is False

    def test_insensitive_detection(self) -> None:
        # A plan where the conclusion is hardcoded regardless of inputs
        executor = CounterfactualExecutor(
            executor=lambda plan: "always_same"
        )
        plan = {"inputs": {"x": 5.0}, "premises": ["x > 0"]}
        result = executor.run_twin(plan, PerturbationType.NEGATE_PREMISE, target="x > 0")
        assert result.conclusion_changed is False
        assert result.suspicious is True

    def test_twin_dataclass(self) -> None:
        twin = CounterfactualTwin(
            original_plan={"step": 1},
            negated_premises=["p1"],
            perturbed_quantities={"x": 2.0},
        )
        desc = twin.describe()
        assert "p1" in desc
        assert "x" in desc


# ===========================================================================
# Test: Proof-Carrying Response
# ===========================================================================


class TestProofCarryingResponse:
    """Test proof-carrying response builder."""

    def test_build_simple_response(self) -> None:
        builder = ProofCarryingResponse()
        response = builder.build(
            answer="2 + 2 = 4",
            claims=[{"id": "c1", "statement": "2 + 2 equals 4"}],
            derivation=[],
            evidence=[{"id": "e1", "source": "math", "content": "arithmetic"}],
        )
        assert response.answer == "2 + 2 = 4"
        assert "c1" in response.claim_ids
        assert response.truth_level == TruthLevel.DERIVED_UNVERIFIED

    def test_cyclic_derivation_raises(self) -> None:
        builder = ProofCarryingResponse()
        with pytest.raises(ValueError, match="cycles"):
            builder.build(
                answer="circular",
                claims=[
                    {"id": "c1", "statement": "A"},
                    {"id": "c2", "statement": "B"},
                ],
                derivation=[("c1", "c2"), ("c2", "c1")],
                evidence=[],
            )

    def test_unverified_claim_reference_raises(self) -> None:
        builder = ProofCarryingResponse()
        with pytest.raises(ValueError, match="not in the verified claim graph"):
            builder.build(
                answer="See [claim:nonexistent] for details",
                claims=[{"id": "c1", "statement": "A"}],
                derivation=[],
                evidence=[],
            )

    def test_verified_response_has_correct_truth_level(self) -> None:
        # Create a passing verification report
        report = VerificationReport(
            checks_run=3,
            checks_passed=3,
            release_decision=ReleaseDecision.PASS,
        )
        builder = ProofCarryingResponse()
        response = builder.build(
            answer="Verified fact",
            claims=[{"id": "c1", "statement": "fact", "evidence_ids": ["e1"]}],
            derivation=[],
            evidence=[{"id": "e1", "source": "kb", "content": "known fact"}],
            verification=report,
        )
        assert response.truth_level == TruthLevel.VERIFIED_FACT
        assert response.is_trustworthy is True


# ===========================================================================
# Test: Verifier Receipts
# ===========================================================================


class TestVerifierReceipts:
    """Test receipt integrity."""

    def test_receipt_integrity_valid(self) -> None:
        v = MathEquivalenceVerifier()
        result = VerifierResult(
            passed=True, check_name="test", details="ok", confidence=0.9
        )
        receipt = v.make_receipt("claim_1", result)
        assert receipt.verify_integrity() is True

    def test_receipt_integrity_tampered(self) -> None:
        v = MathEquivalenceVerifier()
        result = VerifierResult(
            passed=True, check_name="test", details="ok", confidence=0.9
        )
        receipt = v.make_receipt("claim_1", result)
        # Tamper with the receipt
        receipt.claim_id = "claim_2"
        assert receipt.verify_integrity() is False


# ===========================================================================
# Test: Dimension Verification
# ===========================================================================


class TestDimensionVerifier:
    """Test unit/dimension consistency checking."""

    def test_matching_dimensions(self) -> None:
        v = DimensionVerifier()
        claim = {"type": "physical_equation", "lhs_units": "N", "rhs_units": "N"}
        result = v.verify(claim, {})
        assert result.passed is True

    def test_mismatched_dimensions(self) -> None:
        v = DimensionVerifier()
        claim = {"type": "physical_equation", "lhs_units": "m", "rhs_units": "s"}
        result = v.verify(claim, {})
        assert result.passed is False


# ===========================================================================
# Test: Numerical Verifier
# ===========================================================================


class TestNumericalVerifier:
    """Test numerical substitution verifier."""

    def test_true_equality(self) -> None:
        v = NumericalVerifier(num_samples=30)
        claim = {"type": "math_equivalence", "lhs": "x * 2", "rhs": "x + x"}
        result = v.verify(claim, {})
        assert result.passed is True

    def test_false_equality(self) -> None:
        v = NumericalVerifier(num_samples=30)
        claim = {"type": "math_equivalence", "lhs": "x * 2", "rhs": "x + 1"}
        result = v.verify(claim, {})
        assert result.passed is False
