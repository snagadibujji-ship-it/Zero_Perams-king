"""Counterfactual reasoning: twin execution, perturbation testing."""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class PerturbationType(Enum):
    """Types of perturbation for counterfactual testing."""
    NEGATE_PREMISE = "negate_premise"
    PERTURB_QUANTITY = "perturb_quantity"
    SWAP_ENTITY = "swap_entity"
    REMOVE_STEP = "remove_step"
    MUTATE_INPUT = "mutate_input"


@dataclass
class CounterfactualTwin:
    """A counterfactual scenario: what would happen if conditions differed?"""
    original_plan: Dict[str, Any]
    negated_premises: List[str] = field(default_factory=list)
    perturbed_quantities: Dict[str, Any] = field(default_factory=dict)
    expected_change: str = "conclusion_should_differ"

    def describe(self) -> str:
        """Human-readable description of the counterfactual."""
        parts = []
        if self.negated_premises:
            parts.append(f"Negated: {', '.join(self.negated_premises)}")
        if self.perturbed_quantities:
            parts.append(f"Perturbed: {self.perturbed_quantities}")
        return " | ".join(parts) if parts else "identity twin"


@dataclass
class ComparisonResult:
    """Result of comparing original execution with counterfactual twin."""
    original_output: Any
    twin_output: Any
    conclusion_changed: bool
    change_magnitude: float = 0.0
    suspicious: bool = False
    explanation: str = ""

    @property
    def sensitivity_detected(self) -> bool:
        """True if the conclusion properly changed when premises changed."""
        return self.conclusion_changed

    @property
    def insensitivity_warning(self) -> bool:
        """True if conclusion did NOT change when it should have — suspicious."""
        return self.suspicious


class CounterfactualExecutor:
    """Executes counterfactual twins and compares results.

    Core principle: if a premise changes but the conclusion doesn't,
    either the premise is irrelevant or the reasoning is insensitive/broken.
    """

    def __init__(
        self,
        executor: Optional[Callable[[Dict[str, Any]], Any]] = None,
    ) -> None:
        """
        Args:
            executor: A callable that takes a plan dict and returns a result.
                      If None, uses a simple evaluation strategy.
        """
        self._executor = executor or self._default_executor

    def run_twin(
        self,
        plan: Dict[str, Any],
        perturbation: PerturbationType,
        target: Optional[str] = None,
        magnitude: float = 1.0,
    ) -> ComparisonResult:
        """Run original plan and a perturbed twin, compare results.

        Args:
            plan: The original execution plan.
            perturbation: Type of perturbation to apply.
            target: Specific premise/quantity/entity to perturb.
            magnitude: How much to perturb (for quantity changes).

        Returns:
            ComparisonResult comparing original and twin outcomes.
        """
        # Execute original
        original_output = self._executor(plan)

        # Create and execute twin
        twin_plan = self._create_twin(plan, perturbation, target, magnitude)
        twin_output = self._executor(twin_plan.original_plan)

        # Compare
        conclusion_changed = not self._outputs_equivalent(original_output, twin_output)

        # Determine if this is suspicious
        # If we negated a premise and conclusion didn't change → suspicious
        suspicious = False
        explanation = ""

        if perturbation == PerturbationType.NEGATE_PREMISE:
            if not conclusion_changed:
                suspicious = True
                explanation = (
                    f"Negating premise '{target}' did not change the conclusion. "
                    "Either the premise is irrelevant or reasoning is insensitive."
                )
            else:
                explanation = f"Conclusion properly changed when premise '{target}' was negated."

        elif perturbation == PerturbationType.PERTURB_QUANTITY:
            if not conclusion_changed and magnitude > 0.5:
                suspicious = True
                explanation = (
                    f"Perturbing quantity '{target}' by {magnitude} did not affect conclusion. "
                    "Reasoning may not be using this input."
                )
            else:
                change_mag = self._compute_magnitude(original_output, twin_output)
                explanation = (
                    f"Quantity perturbation of '{target}' produced "
                    f"change magnitude {change_mag:.4f}."
                )

        elif perturbation == PerturbationType.MUTATE_INPUT:
            if not conclusion_changed:
                suspicious = True
                explanation = "Input mutation produced identical output — possible constant function."
            else:
                explanation = "Input mutation correctly produced different output."

        change_magnitude = self._compute_magnitude(original_output, twin_output)

        return ComparisonResult(
            original_output=original_output,
            twin_output=twin_output,
            conclusion_changed=conclusion_changed,
            change_magnitude=change_magnitude,
            suspicious=suspicious,
            explanation=explanation,
        )

    def run_sensitivity_suite(
        self,
        plan: Dict[str, Any],
        premises: Optional[List[str]] = None,
        quantities: Optional[Dict[str, float]] = None,
    ) -> List[ComparisonResult]:
        """Run a suite of counterfactual tests on a plan.

        Tests each premise and quantity for sensitivity.
        """
        results: List[ComparisonResult] = []

        # Test premise sensitivity
        if premises:
            for premise in premises:
                result = self.run_twin(
                    plan, PerturbationType.NEGATE_PREMISE, target=premise
                )
                results.append(result)

        # Test quantity sensitivity
        if quantities:
            for qty_name, qty_value in quantities.items():
                for magnitude in [0.1, 1.0, 10.0]:
                    result = self.run_twin(
                        plan,
                        PerturbationType.PERTURB_QUANTITY,
                        target=qty_name,
                        magnitude=magnitude,
                    )
                    results.append(result)

        return results

    def _create_twin(
        self,
        plan: Dict[str, Any],
        perturbation: PerturbationType,
        target: Optional[str],
        magnitude: float,
    ) -> CounterfactualTwin:
        """Create a counterfactual twin from the original plan."""
        twin_plan = copy.deepcopy(plan)

        if perturbation == PerturbationType.NEGATE_PREMISE:
            premises = twin_plan.get("premises", [])
            if target and target in premises:
                premises.remove(target)
                twin = CounterfactualTwin(
                    original_plan=twin_plan,
                    negated_premises=[target],
                    expected_change="conclusion_should_differ",
                )
            elif premises:
                removed = premises.pop(0)
                twin = CounterfactualTwin(
                    original_plan=twin_plan,
                    negated_premises=[removed],
                    expected_change="conclusion_should_differ",
                )
            else:
                twin = CounterfactualTwin(original_plan=twin_plan)
            return twin

        elif perturbation == PerturbationType.PERTURB_QUANTITY:
            quantities = twin_plan.get("quantities", twin_plan.get("inputs", {}))
            if target and target in quantities:
                original_val = quantities[target]
                if isinstance(original_val, (int, float)):
                    quantities[target] = original_val * (1 + magnitude)
            twin = CounterfactualTwin(
                original_plan=twin_plan,
                perturbed_quantities={target: magnitude} if target else {},
                expected_change="output_should_scale",
            )
            return twin

        elif perturbation == PerturbationType.MUTATE_INPUT:
            inputs = twin_plan.get("inputs", {})
            for key in inputs:
                if isinstance(inputs[key], (int, float)):
                    inputs[key] = inputs[key] + random.uniform(-magnitude, magnitude)
                elif isinstance(inputs[key], str):
                    inputs[key] = inputs[key][::-1]  # Reverse string
            twin = CounterfactualTwin(
                original_plan=twin_plan,
                expected_change="output_should_differ",
            )
            return twin

        elif perturbation == PerturbationType.SWAP_ENTITY:
            entities = twin_plan.get("entities", [])
            if len(entities) >= 2:
                entities[0], entities[1] = entities[1], entities[0]
            twin = CounterfactualTwin(
                original_plan=twin_plan,
                expected_change="conclusion_may_differ",
            )
            return twin

        elif perturbation == PerturbationType.REMOVE_STEP:
            steps = twin_plan.get("steps", [])
            if steps:
                steps.pop(-1)  # Remove last step
            twin = CounterfactualTwin(
                original_plan=twin_plan,
                expected_change="conclusion_should_differ",
            )
            return twin

        return CounterfactualTwin(original_plan=twin_plan)

    def _default_executor(self, plan: Dict[str, Any]) -> Any:
        """Default executor: returns the plan's 'conclusion' or evaluates 'expression'."""
        if "conclusion" in plan:
            return plan["conclusion"]
        if "expression" in plan and "inputs" in plan:
            from .math_verifier import _safe_eval
            return _safe_eval(plan["expression"], plan["inputs"])
        if "output" in plan:
            return plan["output"]
        return plan

    def _outputs_equivalent(self, a: Any, b: Any) -> bool:
        """Check if two outputs are equivalent."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a == 0 and b == 0:
                return True
            return abs(a - b) / max(1.0, abs(a), abs(b)) < 1e-9
        return a == b

    def _compute_magnitude(self, a: Any, b: Any) -> float:
        """Compute the magnitude of difference between two outputs."""
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if a == 0 and b == 0:
                return 0.0
            return abs(a - b) / max(1.0, abs(a), abs(b))
        if a == b:
            return 0.0
        return 1.0  # Binary: different or same
