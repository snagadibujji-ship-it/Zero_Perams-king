"""Metamorphic tests: meaning preservation, negation, quantity changes."""

from __future__ import annotations

import sys
from typing import Any, Dict

import pytest

sys.path.insert(0, "/root/hybrid-ai/src")

from axima.verification.metamorphic import (
    MetamorphicRelation,
    MetamorphicTester,
    MutationType,
)
from axima.verification.math_verifier import _safe_eval


# ===========================================================================
# Test fixture: a simple "system under test" that processes queries
# ===========================================================================


def simple_math_executor(input_data: Any) -> Any:
    """A simple executor that evaluates math expressions or returns strings."""
    if isinstance(input_data, (int, float)):
        return input_data
    if isinstance(input_data, str):
        result = _safe_eval(input_data.strip(), {})
        if result is not None:
            return result
        return input_data
    if isinstance(input_data, dict):
        if "expression" in input_data:
            bindings = input_data.get("inputs", {})
            result = _safe_eval(input_data["expression"], bindings)
            return result if result is not None else input_data
        if "query" in input_data:
            return input_data["query"].lower().strip()
        return input_data
    return input_data


# ===========================================================================
# Tests: Paraphrased queries produce equivalent meaning
# ===========================================================================


class TestMeaningPreservation:
    """Tests that meaning-preserving mutations don't change outputs."""

    def test_whitespace_normalization_preserves_math(self) -> None:
        """Extra whitespace shouldn't change math results."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations("2 + 3")
        whitespace_results = [r for r in results if "whitespace" in r.check_name]
        for r in whitespace_results:
            assert r.passed is True, f"Whitespace change broke result: {r.details}"

    def test_case_normalization_preserves_query(self) -> None:
        """Case changes shouldn't change factual query results."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations({"query": "What is Python?"})
        case_results = [r for r in results if "case" in r.check_name]
        for r in case_results:
            assert r.passed is True, f"Case change broke result: {r.details}"

    def test_commutative_reorder_preserves_addition(self) -> None:
        """a + b should equal b + a."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations("3 + 5")
        reorder_results = [r for r in results if "reorder" in r.check_name]
        for r in reorder_results:
            assert r.passed is True, f"Commutative reorder broke result: {r.details}"

    def test_commutative_reorder_preserves_multiplication(self) -> None:
        """a * b should equal b * a."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations("4 * 7")
        reorder_results = [r for r in results if "reorder" in r.check_name]
        for r in reorder_results:
            assert r.passed is True, f"Commutative reorder broke result: {r.details}"

    def test_unit_conversion_preserves_meaning(self) -> None:
        """Converting units should yield equivalent results."""
        # Custom executor that understands units
        def unit_aware_executor(data: Any) -> Any:
            if isinstance(data, dict) and "value" in data and "unit" in data:
                # Normalize to base units for comparison
                val = data["value"]
                unit = data["unit"]
                # Convert everything to meters/kg/seconds
                conversions_to_base = {
                    "m": 1.0, "km": 1000.0, "mm": 0.001,
                    "kg": 1.0, "g": 0.001, "mg": 0.000001,
                    "s": 1.0, "ms": 0.001, "min": 60.0,
                }
                factor = conversions_to_base.get(unit, 1.0)
                return val * factor
            return data

        tester = MetamorphicTester(executor=unit_aware_executor)
        input_data = {"value": 5.0, "unit": "km"}
        results = tester.run_mutations(input_data)
        unit_results = [r for r in results if "unit" in r.check_name]
        for r in unit_results:
            assert r.passed is True, f"Unit conversion broke equivalence: {r.details}"

    def test_multiple_preserving_mutations_all_pass(self) -> None:
        """Multiple meaning-preserving mutations should all preserve output."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations("10 + 20")
        preserving = [
            r for r in results
            if any(kw in r.check_name for kw in ["whitespace", "case", "reorder", "unit"])
        ]
        # All preserving mutations should pass
        for r in preserving:
            assert r.passed is True, f"{r.check_name} failed: {r.details}"


# ===========================================================================
# Tests: Negation changes claims
# ===========================================================================


class TestNegationChanges:
    """Tests that negation properly changes outputs."""

    def test_negating_string_changes_output(self) -> None:
        """Adding 'not' to a statement should change the response."""
        tester = MetamorphicTester(executor=lambda x: x)
        results = tester.run_mutations("the earth is round")
        negate_results = [r for r in results if "negate" in r.check_name]
        for r in negate_results:
            assert r.passed is True, "Negation didn't change output"

    def test_negating_number_changes_value(self) -> None:
        """Negating a number should produce a different result."""
        tester = MetamorphicTester(executor=lambda x: x)
        results = tester.run_mutations(42)
        negate_results = [r for r in results if "negate" in r.check_name]
        for r in negate_results:
            assert r.passed is True, "Negating number didn't change value"

    def test_negating_query_changes_meaning(self) -> None:
        """Negating a query should produce different results."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations({"query": "Water boils at 100C"})
        negate_results = [r for r in results if "negate" in r.check_name]
        for r in negate_results:
            assert r.passed is True, "Negated query produced same result"

    def test_double_negation_concept(self) -> None:
        """Verify that negation is detectable as meaning-changing."""
        relation = MetamorphicRelation(
            name="negate_test",
            input_transform=lambda x: f"not {x}" if isinstance(x, str) else -x,
            expected_output_relation=lambda orig, mut: orig != mut,
            mutation_type=MutationType.MEANING_CHANGING,
        )
        tester = MetamorphicTester(executor=lambda x: x)
        results = tester.run_mutations("true statement", relations=[relation])
        assert len(results) == 1
        assert results[0].passed is True


# ===========================================================================
# Tests: Quantity changes affect results
# ===========================================================================


class TestQuantityChanges:
    """Tests that changing quantities affects computational results."""

    def test_changing_numbers_changes_math_result(self) -> None:
        """Doubling numbers in an expression should change the result."""
        tester = MetamorphicTester(executor=simple_math_executor)
        results = tester.run_mutations("5 + 3")
        qty_results = [r for r in results if "quantity" in r.check_name]
        for r in qty_results:
            assert r.passed is True, "Changing quantities didn't change result"

    def test_changing_input_dict_values(self) -> None:
        """Changing numeric values in a dict should change output."""
        tester = MetamorphicTester(executor=lambda x: x)
        data = {"temperature": 100.0, "pressure": 1.0}
        results = tester.run_mutations(data)
        qty_results = [r for r in results if "quantity" in r.check_name]
        for r in qty_results:
            assert r.passed is True, "Dict value change didn't affect output"

    def test_zero_stays_different_from_nonzero(self) -> None:
        """Changing 0 to non-zero should definitely change results."""
        relation = MetamorphicRelation(
            name="zero_to_nonzero",
            input_transform=lambda x: x + 1 if isinstance(x, (int, float)) else x,
            expected_output_relation=lambda orig, mut: orig != mut,
            mutation_type=MutationType.MEANING_CHANGING,
        )
        tester = MetamorphicTester(executor=lambda x: x * 2)
        results = tester.run_mutations(0, relations=[relation])
        assert len(results) == 1
        assert results[0].passed is True

    def test_entity_swap_changes_claims(self) -> None:
        """Swapping entities should produce different claims."""
        tester = MetamorphicTester(executor=lambda x: x)
        data = {"entities": ["Einstein", "Newton"], "claim": "discovered relativity"}
        results = tester.run_mutations(data)
        swap_results = [r for r in results if "swap" in r.check_name]
        for r in swap_results:
            assert r.passed is True, "Entity swap didn't change output"

    def test_large_quantity_change_always_detected(self) -> None:
        """A 10x change in quantity should always be detected."""
        relation = MetamorphicRelation(
            name="10x_change",
            input_transform=lambda x: x * 10 if isinstance(x, (int, float)) else x,
            expected_output_relation=lambda orig, mut: orig != mut,
            mutation_type=MutationType.MEANING_CHANGING,
        )
        tester = MetamorphicTester(executor=lambda x: x ** 2 if isinstance(x, (int, float)) else x)
        results = tester.run_mutations(3.0, relations=[relation])
        assert len(results) == 1
        assert results[0].passed is True
