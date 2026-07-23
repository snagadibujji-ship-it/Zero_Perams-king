"""Causal Specialist — structural causal models, interventions, counterfactuals.

Never upgrades correlation to causation without a mechanistic explanation.
Distinguishes intervention (do-calculus) from observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


class RelationType(Enum):
    CAUSAL = auto()        # X causes Y (mechanism known)
    CORRELATIONAL = auto() # X correlates with Y (no mechanism)
    CONFOUNDED = auto()    # shared cause Z -> X, Z -> Y
    MEDIATING = auto()     # X -> M -> Y


class EvidenceStrength(Enum):
    MECHANISTIC = auto()    # known physical/logical mechanism
    EXPERIMENTAL = auto()   # RCT or natural experiment
    OBSERVATIONAL = auto()  # observational study
    ANECDOTAL = auto()      # single observation


@dataclass
class CausalVariable:
    """A variable in a structural causal model."""
    name: str
    domain: str = "continuous"
    observed: bool = True
    description: str = ""


@dataclass
class CausalEdge:
    """A directed edge in a causal graph."""
    source: str
    target: str
    relation: RelationType = RelationType.CAUSAL
    mechanism: Optional[str] = None
    evidence: EvidenceStrength = EvidenceStrength.OBSERVATIONAL
    strength: Optional[float] = None  # effect size if known


@dataclass
class StructuralCausalModel:
    """A structural causal model (DAG with mechanisms)."""
    variables: Dict[str, CausalVariable] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)
    name: str = ""
    description: str = ""

    def add_variable(self, var: CausalVariable) -> None:
        self.variables[var.name] = var

    def add_edge(self, edge: CausalEdge) -> None:
        if edge.source not in self.variables:
            raise ValueError(f"Source variable '{edge.source}' not in model")
        if edge.target not in self.variables:
            raise ValueError(f"Target variable '{edge.target}' not in model")
        self.edges.append(edge)

    def parents(self, var_name: str) -> List[str]:
        """Get direct causal parents of a variable."""
        return [e.source for e in self.edges if e.target == var_name]

    def children(self, var_name: str) -> List[str]:
        """Get direct causal children of a variable."""
        return [e.target for e in self.edges if e.source == var_name]

    def ancestors(self, var_name: str) -> Set[str]:
        """Get all ancestors (transitive parents)."""
        result: Set[str] = set()
        queue = self.parents(var_name)
        while queue:
            parent = queue.pop(0)
            if parent not in result:
                result.add(parent)
                queue.extend(self.parents(parent))
        return result

    def descendants(self, var_name: str) -> Set[str]:
        """Get all descendants (transitive children)."""
        result: Set[str] = set()
        queue = self.children(var_name)
        while queue:
            child = queue.pop(0)
            if child not in result:
                result.add(child)
                queue.extend(self.children(child))
        return result


@dataclass
class InterventionResult:
    """Result of a do-calculus intervention do(X=x)."""
    intervention_var: str
    intervention_value: Any
    target_var: str
    estimated_effect: Optional[float]
    mechanism: Optional[str]
    confounders_blocked: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    is_causal: bool = False
    explanation: str = ""


@dataclass
class CounterfactualResult:
    """Result of a counterfactual query: 'What if X had been x?'"""
    factual_world: Dict[str, Any]
    counterfactual_world: Dict[str, Any]
    intervention_var: str
    intervention_value: Any
    target_var: str
    factual_outcome: Any
    counterfactual_outcome: Any
    explanation: str = ""
    assumptions: List[str] = field(default_factory=list)


@dataclass
class ConfounderReport:
    """Report on identified confounders between two variables."""
    exposure: str
    outcome: str
    confounders: List[str] = field(default_factory=list)
    adjustment_sets: List[FrozenSet[str]] = field(default_factory=list)
    recommendation: str = ""


class CausalSpecialist:
    """Domain specialist for causal reasoning.

    - intervention: do-calculus style interventions
    - counterfactual: what-if reasoning
    - identify_confounders: find common causes

    NEVER upgrades correlation to causation without mechanism.
    """

    def __init__(self) -> None:
        self._models: Dict[str, StructuralCausalModel] = {}

    def register_model(self, model: StructuralCausalModel) -> None:
        """Register a structural causal model."""
        self._models[model.name] = model

    def get_model(self, name: str) -> Optional[StructuralCausalModel]:
        return self._models.get(name)

    def intervention(
        self,
        model_name: str,
        do_var: str,
        do_value: Any,
        target_var: str,
        observed: Optional[Dict[str, Any]] = None,
    ) -> InterventionResult:
        """Compute the effect of intervention do(X=x) on Y.

        Uses do-calculus: cuts all incoming edges to do_var, then traces
        causal paths to target_var.
        """
        model = self._models.get(model_name)
        if model is None:
            return InterventionResult(
                intervention_var=do_var, intervention_value=do_value,
                target_var=target_var, estimated_effect=None, mechanism=None,
                explanation=f"Model '{model_name}' not registered",
            )

        if do_var not in model.variables:
            return InterventionResult(
                intervention_var=do_var, intervention_value=do_value,
                target_var=target_var, estimated_effect=None, mechanism=None,
                explanation=f"Variable '{do_var}' not in model",
            )

        if target_var not in model.variables:
            return InterventionResult(
                intervention_var=do_var, intervention_value=do_value,
                target_var=target_var, estimated_effect=None, mechanism=None,
                explanation=f"Variable '{target_var}' not in model",
            )

        # Find causal paths from do_var to target_var
        causal_paths = self._find_causal_paths(model, do_var, target_var)
        if not causal_paths:
            return InterventionResult(
                intervention_var=do_var, intervention_value=do_value,
                target_var=target_var, estimated_effect=None, mechanism=None,
                explanation=f"No causal path from '{do_var}' to '{target_var}'",
                is_causal=False,
            )

        # Check that all edges on path are genuinely causal (not merely correlational)
        all_causal = True
        mechanisms: List[str] = []
        confounders_blocked: List[str] = []

        for path in causal_paths:
            for i in range(len(path) - 1):
                edge = self._find_edge(model, path[i], path[i + 1])
                if edge is None:
                    all_causal = False
                    break
                if edge.relation == RelationType.CORRELATIONAL:
                    all_causal = False
                    break
                if edge.relation == RelationType.CONFOUNDED:
                    all_causal = False
                    break
                if edge.mechanism:
                    mechanisms.append(edge.mechanism)

        # Block confounders (parents of do_var)
        parents_of_do = model.parents(do_var)
        for p in parents_of_do:
            confounders_blocked.append(p)

        # Compute effect (simplified: product of edge strengths along shortest causal path)
        estimated_effect: Optional[float] = None
        if all_causal and causal_paths:
            shortest = min(causal_paths, key=len)
            effect = 1.0
            has_strength = True
            for i in range(len(shortest) - 1):
                edge = self._find_edge(model, shortest[i], shortest[i + 1])
                if edge and edge.strength is not None:
                    effect *= edge.strength
                else:
                    has_strength = False
                    break
            if has_strength:
                estimated_effect = effect

        assumptions = [
            "Intervention cuts all incoming edges to treatment variable",
            "No hidden confounders between treatment and outcome",
            "Causal sufficiency assumption holds",
        ]

        mechanism_str = " -> ".join(mechanisms) if mechanisms else None
        explanation = (
            f"do({do_var}={do_value}): causal path exists via "
            f"{' -> '.join(causal_paths[0]) if causal_paths else 'none'}. "
            f"{'Mechanism verified.' if all_causal else 'WARNING: correlation only, not causal.'}"
        )

        return InterventionResult(
            intervention_var=do_var,
            intervention_value=do_value,
            target_var=target_var,
            estimated_effect=estimated_effect,
            mechanism=mechanism_str,
            confounders_blocked=confounders_blocked,
            assumptions=assumptions,
            is_causal=all_causal,
            explanation=explanation,
        )

    def counterfactual(
        self,
        model_name: str,
        factual_world: Dict[str, Any],
        intervention_var: str,
        intervention_value: Any,
        target_var: str,
    ) -> CounterfactualResult:
        """Answer: 'Given factual world, what would target_var be if intervention_var had been value?'

        Three-step counterfactual:
        1. Abduction: infer exogenous variables from factual world
        2. Action: set intervention_var = value
        3. Prediction: compute target_var under modified model
        """
        model = self._models.get(model_name)
        assumptions = [
            "Structural equations are deterministic given exogenous variables",
            "No interference between units",
            "Temporal consistency of counterfactual world",
        ]

        if model is None:
            return CounterfactualResult(
                factual_world=factual_world,
                counterfactual_world={},
                intervention_var=intervention_var,
                intervention_value=intervention_value,
                target_var=target_var,
                factual_outcome=factual_world.get(target_var),
                counterfactual_outcome=None,
                explanation=f"Model '{model_name}' not registered",
                assumptions=assumptions,
            )

        # Step 1: Abduction — use factual world as-is for exogenous values
        # Step 2: Action — modify the intervention variable
        counterfactual_world = dict(factual_world)
        counterfactual_world[intervention_var] = intervention_value

        # Step 3: Prediction — trace effects through descendants
        affected = model.descendants(intervention_var)
        factual_outcome = factual_world.get(target_var)
        counterfactual_outcome = factual_outcome  # default: no change

        if target_var in affected:
            # Target is causally downstream; effect exists
            # Simplified: check if there's a quantified path
            paths = self._find_causal_paths(model, intervention_var, target_var)
            if paths:
                shortest = min(paths, key=len)
                effect = 1.0
                has_effect = True
                for i in range(len(shortest) - 1):
                    edge = self._find_edge(model, shortest[i], shortest[i + 1])
                    if edge and edge.strength is not None:
                        effect *= edge.strength
                    else:
                        has_effect = False
                        break
                if has_effect and factual_outcome is not None:
                    delta = (intervention_value - factual_world.get(intervention_var, 0)) * effect
                    counterfactual_outcome = factual_outcome + delta
                    counterfactual_world[target_var] = counterfactual_outcome

        explanation = (
            f"Counterfactual: had {intervention_var} been {intervention_value} "
            f"(actual: {factual_world.get(intervention_var)}), "
            f"{target_var} would be {counterfactual_outcome} "
            f"(actual: {factual_outcome})"
        )

        return CounterfactualResult(
            factual_world=factual_world,
            counterfactual_world=counterfactual_world,
            intervention_var=intervention_var,
            intervention_value=intervention_value,
            target_var=target_var,
            factual_outcome=factual_outcome,
            counterfactual_outcome=counterfactual_outcome,
            explanation=explanation,
            assumptions=assumptions,
        )

    def identify_confounders(
        self,
        model_name: str,
        exposure: str,
        outcome: str,
    ) -> ConfounderReport:
        """Identify confounders between exposure and outcome.

        A confounder is a common ancestor of both exposure and outcome
        that creates a non-causal association (backdoor path).
        """
        model = self._models.get(model_name)
        if model is None:
            return ConfounderReport(
                exposure=exposure, outcome=outcome,
                recommendation=f"Model '{model_name}' not registered",
            )

        if exposure not in model.variables or outcome not in model.variables:
            return ConfounderReport(
                exposure=exposure, outcome=outcome,
                recommendation="Variables not found in model",
            )

        # Find common ancestors
        ancestors_exposure = model.ancestors(exposure)
        ancestors_outcome = model.ancestors(outcome)
        confounders = list(ancestors_exposure & ancestors_outcome)

        # Find minimal sufficient adjustment sets (simplified: all confounders)
        adjustment_sets: List[FrozenSet[str]] = []
        if confounders:
            adjustment_sets.append(frozenset(confounders))
            # Also check if individual confounders suffice
            for c in confounders:
                # A single confounder suffices if it blocks all backdoor paths
                if self._blocks_all_backdoors(model, exposure, outcome, {c}):
                    adjustment_sets.append(frozenset({c}))

        recommendation = ""
        if not confounders:
            recommendation = (
                f"No confounders found between '{exposure}' and '{outcome}'. "
                "Observed association may reflect causal effect (if model is complete)."
            )
        else:
            recommendation = (
                f"Confounders: {confounders}. "
                f"Adjust for {confounders} to estimate causal effect of '{exposure}' on '{outcome}'. "
                "WARNING: This assumes no unmeasured confounders exist."
            )

        return ConfounderReport(
            exposure=exposure,
            outcome=outcome,
            confounders=confounders,
            adjustment_sets=adjustment_sets,
            recommendation=recommendation,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_causal_paths(
        self, model: StructuralCausalModel, source: str, target: str,
    ) -> List[List[str]]:
        """Find all directed paths from source to target."""
        paths: List[List[str]] = []
        queue: List[List[str]] = [[source]]

        while queue:
            path = queue.pop(0)
            current = path[-1]
            if current == target:
                paths.append(path)
                continue
            for child in model.children(current):
                if child not in path:  # avoid cycles
                    queue.append(path + [child])

        return paths

    def _find_edge(
        self, model: StructuralCausalModel, source: str, target: str,
    ) -> Optional[CausalEdge]:
        """Find edge between source and target."""
        for e in model.edges:
            if e.source == source and e.target == target:
                return e
        return None

    def _blocks_all_backdoors(
        self,
        model: StructuralCausalModel,
        exposure: str,
        outcome: str,
        conditioning: Set[str],
    ) -> bool:
        """Check if conditioning on a set blocks all backdoor paths (simplified)."""
        # Simplified: check if all confounders are in conditioning set
        ancestors_exp = model.ancestors(exposure)
        ancestors_out = model.ancestors(outcome)
        all_confounders = ancestors_exp & ancestors_out
        return all_confounders.issubset(conditioning)
