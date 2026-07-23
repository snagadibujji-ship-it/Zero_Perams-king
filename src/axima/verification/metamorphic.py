"""Metamorphic testing: meaning-preserving and meaning-changing mutations."""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from .verifier_base import VerifierResult


class MutationType(Enum):
    """Categories of metamorphic mutation."""
    MEANING_PRESERVING = "meaning_preserving"
    MEANING_CHANGING = "meaning_changing"


@dataclass
class MetamorphicRelation:
    """Defines a metamorphic relation between input and expected output."""

    name: str
    input_transform: Callable[[Any], Any]
    expected_output_relation: Callable[[Any, Any], bool]
    mutation_type: MutationType = MutationType.MEANING_PRESERVING
    description: str = ""

    def apply(self, original_input: Any) -> Any:
        """Apply the input transformation."""
        return self.input_transform(original_input)

    def check(self, original_output: Any, mutated_output: Any) -> bool:
        """Check if the expected output relation holds."""
        return self.expected_output_relation(original_output, mutated_output)


@dataclass
class TestCase:
    """A metamorphic test case: original + mutated input with expected relation."""

    original_input: Any
    mutated_input: Any
    relation_name: str
    mutation_type: MutationType
    original_output: Optional[Any] = None
    mutated_output: Optional[Any] = None
    relation_holds: Optional[bool] = None


class MetamorphicTester:
    """Generates and runs metamorphic mutations to verify system consistency.

    Meaning-preserving mutations:
    - Paraphrase (reword a query)
    - Reorder (swap independent clauses)
    - Unit conversion (same quantity, different units)

    Meaning-changing mutations:
    - Negate (add/remove negation)
    - Change quantities (multiply/add to numbers)
    - Swap entities (replace subject with different entity)
    """

    def __init__(
        self,
        executor: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """
        Args:
            executor: A callable that produces output from an input.
                      Used to run both original and mutated inputs.
        """
        self._executor = executor or (lambda x: x)
        self._relations: List[MetamorphicRelation] = []
        self._register_default_relations()

    def register_relation(self, relation: MetamorphicRelation) -> None:
        """Register a custom metamorphic relation."""
        self._relations.append(relation)

    def generate_mutations(
        self,
        input_data: Any,
        relations: Optional[List[MetamorphicRelation]] = None,
    ) -> List[TestCase]:
        """Generate mutated test cases for the given input.

        Args:
            input_data: Original input to mutate.
            relations: Specific relations to use (defaults to all registered).

        Returns:
            List of TestCase objects with mutated inputs.
        """
        if relations is None:
            relations = self._relations

        test_cases: List[TestCase] = []

        for relation in relations:
            try:
                mutated = relation.apply(input_data)
                # Only include if mutation actually changed something
                if mutated != input_data:
                    test_cases.append(
                        TestCase(
                            original_input=input_data,
                            mutated_input=mutated,
                            relation_name=relation.name,
                            mutation_type=relation.mutation_type,
                        )
                    )
            except Exception:
                # Mutation not applicable to this input type
                continue

        return test_cases

    def run_mutations(
        self,
        input_data: Any,
        relations: Optional[List[MetamorphicRelation]] = None,
    ) -> List[VerifierResult]:
        """Generate and execute metamorphic mutations, returning verification results.

        Args:
            input_data: Original input.
            relations: Optional specific relations.

        Returns:
            List of VerifierResult for each mutation test.
        """
        test_cases = self.generate_mutations(input_data, relations)
        results: List[VerifierResult] = []

        # Run original
        original_output = self._executor(input_data)

        for tc in test_cases:
            tc.original_output = original_output

            try:
                tc.mutated_output = self._executor(tc.mutated_input)
            except Exception as e:
                results.append(
                    VerifierResult(
                        passed=False,
                        check_name=f"metamorphic_{tc.relation_name}",
                        details=f"Mutated input caused error: {e}",
                        counterexamples=[{"mutation": tc.relation_name, "error": str(e)}],
                        confidence=0.7,
                    )
                )
                continue

            # Find the matching relation
            matching_relation = next(
                (r for r in (relations or self._relations) if r.name == tc.relation_name),
                None,
            )

            if matching_relation:
                try:
                    relation_holds = matching_relation.check(
                        original_output, tc.mutated_output
                    )
                    tc.relation_holds = relation_holds
                except Exception:
                    relation_holds = False
                    tc.relation_holds = False

                if relation_holds:
                    results.append(
                        VerifierResult(
                            passed=True,
                            check_name=f"metamorphic_{tc.relation_name}",
                            details=(
                                f"Metamorphic relation '{tc.relation_name}' holds. "
                                f"Mutation type: {tc.mutation_type.value}."
                            ),
                            confidence=0.85,
                        )
                    )
                else:
                    results.append(
                        VerifierResult(
                            passed=False,
                            check_name=f"metamorphic_{tc.relation_name}",
                            details=(
                                f"Metamorphic relation '{tc.relation_name}' violated. "
                                f"Mutation type: {tc.mutation_type.value}."
                            ),
                            counterexamples=[
                                {
                                    "original_input": tc.original_input,
                                    "mutated_input": tc.mutated_input,
                                    "original_output": tc.original_output,
                                    "mutated_output": tc.mutated_output,
                                }
                            ],
                            confidence=0.8,
                        )
                    )

        return results

    # ------------------------------------------------------------------
    # Built-in metamorphic relations
    # ------------------------------------------------------------------

    def _register_default_relations(self) -> None:
        """Register standard meaning-preserving and meaning-changing relations."""

        # --- Meaning-preserving ---

        self._relations.append(
            MetamorphicRelation(
                name="paraphrase_whitespace",
                input_transform=self._paraphrase_whitespace,
                expected_output_relation=self._outputs_equivalent,
                mutation_type=MutationType.MEANING_PRESERVING,
                description="Adding/removing whitespace should not change meaning.",
            )
        )

        self._relations.append(
            MetamorphicRelation(
                name="reorder_commutative",
                input_transform=self._reorder_commutative,
                expected_output_relation=self._outputs_equivalent,
                mutation_type=MutationType.MEANING_PRESERVING,
                description="Reordering commutative operands should preserve result.",
            )
        )

        self._relations.append(
            MetamorphicRelation(
                name="case_normalization",
                input_transform=self._case_normalize,
                expected_output_relation=self._outputs_equivalent,
                mutation_type=MutationType.MEANING_PRESERVING,
                description="Case changes in queries should not change factual answers.",
            )
        )

        self._relations.append(
            MetamorphicRelation(
                name="unit_conversion_identity",
                input_transform=self._unit_conversion,
                expected_output_relation=self._outputs_equivalent,
                mutation_type=MutationType.MEANING_PRESERVING,
                description="Converting units should yield equivalent results.",
            )
        )

        # --- Meaning-changing ---

        self._relations.append(
            MetamorphicRelation(
                name="negate",
                input_transform=self._negate,
                expected_output_relation=self._outputs_differ,
                mutation_type=MutationType.MEANING_CHANGING,
                description="Negation should change the answer.",
            )
        )

        self._relations.append(
            MetamorphicRelation(
                name="quantity_change",
                input_transform=self._change_quantity,
                expected_output_relation=self._outputs_differ,
                mutation_type=MutationType.MEANING_CHANGING,
                description="Changing numeric quantities should change results.",
            )
        )

        self._relations.append(
            MetamorphicRelation(
                name="swap_entities",
                input_transform=self._swap_entities,
                expected_output_relation=self._outputs_differ,
                mutation_type=MutationType.MEANING_CHANGING,
                description="Swapping entities should change claims.",
            )
        )

    # ------------------------------------------------------------------
    # Transform implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _paraphrase_whitespace(input_data: Any) -> Any:
        """Add or normalize whitespace."""
        if isinstance(input_data, str):
            # Normalize multiple spaces, add spaces around operators
            result = re.sub(r"\s+", " ", input_data).strip()
            return result
        if isinstance(input_data, dict) and "query" in input_data:
            data = copy.deepcopy(input_data)
            data["query"] = re.sub(r"\s+", " ", data["query"]).strip()
            return data
        return input_data

    @staticmethod
    def _reorder_commutative(input_data: Any) -> Any:
        """Reorder commutative operations (e.g., a + b → b + a)."""
        if isinstance(input_data, str):
            # Try to swap around + or *
            if "+" in input_data:
                parts = input_data.split("+")
                if len(parts) == 2:
                    return parts[1].strip() + " + " + parts[0].strip()
            if "*" in input_data and "**" not in input_data:
                parts = input_data.split("*")
                if len(parts) == 2:
                    return parts[1].strip() + " * " + parts[0].strip()
        if isinstance(input_data, dict) and "expression" in input_data:
            data = copy.deepcopy(input_data)
            expr = data["expression"]
            if "+" in expr:
                parts = expr.split("+")
                if len(parts) == 2:
                    data["expression"] = parts[1].strip() + " + " + parts[0].strip()
            return data
        return input_data

    @staticmethod
    def _case_normalize(input_data: Any) -> Any:
        """Change case of text input."""
        if isinstance(input_data, str):
            return input_data.lower()
        if isinstance(input_data, dict) and "query" in input_data:
            data = copy.deepcopy(input_data)
            data["query"] = data["query"].lower()
            return data
        return input_data

    @staticmethod
    def _unit_conversion(input_data: Any) -> Any:
        """Apply identity unit conversion (e.g., 1000m → 1km conceptually)."""
        if isinstance(input_data, dict):
            data = copy.deepcopy(input_data)
            # If there's a value with units, convert
            if "value" in data and "unit" in data:
                conversions = {
                    "m": ("km", 0.001),
                    "km": ("m", 1000.0),
                    "kg": ("g", 1000.0),
                    "g": ("kg", 0.001),
                    "s": ("ms", 1000.0),
                    "ms": ("s", 0.001),
                }
                unit = data["unit"]
                if unit in conversions:
                    new_unit, factor = conversions[unit]
                    data["value"] = data["value"] * factor
                    data["unit"] = new_unit
            return data
        return input_data

    @staticmethod
    def _negate(input_data: Any) -> Any:
        """Negate the input (add 'not', negate expression)."""
        if isinstance(input_data, str):
            if input_data.startswith("not "):
                return input_data[4:]
            return "not " + input_data
        if isinstance(input_data, dict):
            data = copy.deepcopy(input_data)
            if "query" in data:
                q = data["query"]
                if "not" in q.lower():
                    data["query"] = re.sub(r"\bnot\s+", "", q, flags=re.I)
                else:
                    data["query"] = "not " + q
            elif "expression" in data:
                data["expression"] = f"-({data['expression']})"
            elif "predicate" in data:
                data["predicate"] = f"not ({data['predicate']})"
            return data
        if isinstance(input_data, (int, float)):
            return -input_data
        return input_data

    @staticmethod
    def _change_quantity(input_data: Any) -> Any:
        """Change numeric quantities in the input."""
        if isinstance(input_data, (int, float)):
            return input_data * 2 + 1
        if isinstance(input_data, str):
            # Find and double numbers
            def double_num(m: re.Match) -> str:
                val = float(m.group())
                return str(val * 2)
            return re.sub(r"\b\d+\.?\d*\b", double_num, input_data)
        if isinstance(input_data, dict):
            data = copy.deepcopy(input_data)
            for key, val in data.items():
                if isinstance(val, (int, float)):
                    data[key] = val * 2 + 1
            return data
        return input_data

    @staticmethod
    def _swap_entities(input_data: Any) -> Any:
        """Swap named entities in the input."""
        if isinstance(input_data, dict):
            data = copy.deepcopy(input_data)
            entities = data.get("entities", [])
            if len(entities) >= 2:
                entities[0], entities[1] = entities[1], entities[0]
                data["entities"] = entities
            elif "subject" in data and "object" in data:
                data["subject"], data["object"] = data["object"], data["subject"]
            return data
        if isinstance(input_data, str):
            # Simple word swap for short inputs
            words = input_data.split()
            if len(words) >= 2:
                words[0], words[-1] = words[-1], words[0]
                return " ".join(words)
        return input_data

    # ------------------------------------------------------------------
    # Output relation checkers
    # ------------------------------------------------------------------

    @staticmethod
    def _outputs_equivalent(original: Any, mutated: Any) -> bool:
        """Check if two outputs are semantically equivalent."""
        if original is None and mutated is None:
            return True
        if original is None or mutated is None:
            return False
        if isinstance(original, (int, float)) and isinstance(mutated, (int, float)):
            if original == 0 and mutated == 0:
                return True
            return abs(original - mutated) / max(1.0, abs(original), abs(mutated)) < 1e-6
        if isinstance(original, str) and isinstance(mutated, str):
            # Normalize for comparison
            return original.strip().lower() == mutated.strip().lower()
        return original == mutated

    @staticmethod
    def _outputs_differ(original: Any, mutated: Any) -> bool:
        """Check that outputs are different (for meaning-changing mutations)."""
        if original is None and mutated is None:
            return False  # Both None = same = relation violated
        if original is None or mutated is None:
            return True
        if isinstance(original, (int, float)) and isinstance(mutated, (int, float)):
            if original == 0 and mutated == 0:
                return False
            return abs(original - mutated) / max(1.0, abs(original), abs(mutated)) > 1e-6
        if isinstance(original, str) and isinstance(mutated, str):
            return original.strip().lower() != mutated.strip().lower()
        return original != mutated
