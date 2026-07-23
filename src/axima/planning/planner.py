"""Cognitive Planner — builds PlanDAGs from queries, contracts, and capabilities.

Selects capabilities based on contract requirements, builds dependency graphs,
estimates costs, and handles partial failure recovery.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..contracts.query import QueryEnvelope, ResourceBudgetSpec
from ..epistemics.contracts import AnswerKind, EpistemicContract, EvidenceRequirement
from ..kernel.registry import CapabilityDescriptor
from .plan_dag import BranchCondition, PlanDAG, PlanStep, ResourceBudget, StepStatus


@dataclass
class PlanningContext:
    """Context gathered during planning for decision-making."""

    query: QueryEnvelope
    contract: EpistemicContract
    available_capabilities: List[CapabilityDescriptor] = field(default_factory=list)
    matched_capabilities: List[CapabilityDescriptor] = field(default_factory=list)
    planning_notes: List[str] = field(default_factory=list)


class CognitivePlanner:
    """Builds execution plans (PlanDAGs) from queries and contracts.

    The planner:
    1. Analyzes the contract to determine required capability types
    2. Matches available capabilities to requirements
    3. Builds a dependency graph (some capabilities need outputs of others)
    4. Estimates costs and selects fast/deep path based on budget
    5. Adds verification steps where required by evidence level
    6. Configures failure recovery (retries, fallbacks)
    """

    # Mapping from answer kinds to required capability types
    _KIND_TO_CAPABILITIES: Dict[AnswerKind, List[str]] = {
        AnswerKind.FACT: ["inference", "knowledge"],
        AnswerKind.DERIVATION: ["math", "physics", "inference"],
        AnswerKind.ESTIMATE: ["math", "inference"],
        AnswerKind.PROOF: ["math"],
        AnswerKind.PLAN: ["inference", "coder"],
        AnswerKind.ACTION: ["coder", "web", "creator"],
        AnswerKind.CREATIVE: ["creator"],
        AnswerKind.CLARIFICATION: ["inference"],
    }

    # Capability types that can verify others
    _VERIFICATION_CAPABILITIES: Dict[str, List[str]] = {
        "math": ["math"],  # Math can self-verify with alternate methods
        "physics": ["math", "physics"],
        "inference": ["inference"],
        "coder": ["coder"],  # Code can be tested
    }

    def plan(
        self,
        query: QueryEnvelope,
        contract: EpistemicContract,
        capabilities: List[CapabilityDescriptor],
    ) -> PlanDAG:
        """Build an execution plan for the given query and contract.

        Args:
            query: The incoming query envelope.
            contract: The epistemic contract specifying answer requirements.
            capabilities: Available capability descriptors.

        Returns:
            A PlanDAG ready for execution.
        """
        ctx = PlanningContext(
            query=query,
            contract=contract,
            available_capabilities=capabilities,
        )

        # Step 1: Determine needed capability types
        needed_types = self._determine_needed_types(contract)

        # Step 2: Match capabilities
        matched = self._match_capabilities(needed_types, capabilities)
        ctx.matched_capabilities = matched

        if not matched:
            # No capabilities match — create a minimal plan with an unsupported step
            return self._create_unsupported_plan(query, contract)

        # Step 3: Determine execution mode (fast vs deep)
        mode = self._select_mode(query, contract, matched)

        # Step 4: Build the DAG
        dag = self._build_dag(ctx, matched, mode)

        # Step 5: Add verification steps if required
        if contract.required_evidence in (
            EvidenceRequirement.PROVEN,
            EvidenceRequirement.SOURCED,
        ):
            self._add_verification_steps(dag, contract, capabilities)

        # Step 6: Configure budget
        dag.budget = self._compute_budget(query.resource_budget)
        dag.deadline_ms = int(query.resource_budget.max_time_ms)

        return dag

    def plan_recovery(
        self,
        original_plan: PlanDAG,
        failed_steps: List[str],
        capabilities: List[CapabilityDescriptor],
    ) -> Optional[PlanDAG]:
        """Create a recovery plan after partial failure.

        Attempts to find alternative capabilities for failed steps,
        or create a reduced plan that skips non-essential failures.

        Returns:
            A new PlanDAG for recovery, or None if recovery is not possible.
        """
        if not failed_steps:
            return None

        recovery_dag = PlanDAG(deadline_ms=original_plan.deadline_ms)
        recovery_dag.budget = original_plan.budget

        any_recovered = False
        for step_id in failed_steps:
            if step_id not in original_plan.steps:
                continue

            original_step = original_plan.steps[step_id]
            # Try to find an alternative capability
            alternatives = [
                cap for cap in capabilities
                if original_step.capability in cap.accepted_types
                and cap.name != original_step.capability
            ]

            if alternatives:
                # Use the first alternative
                alt = alternatives[0]
                recovery_step = PlanStep(
                    id=f"recovery_{step_id}",
                    name=f"Retry {original_step.name} via {alt.name}",
                    capability=alt.name,
                    preconditions=original_step.preconditions,
                    postconditions=original_step.postconditions,
                    expected_cost_ms=int(alt.latency_model.get("avg_ms", 200)),
                    expected_info_gain=original_step.expected_info_gain * 0.8,
                )
                recovery_dag.add_step(recovery_step)
                any_recovered = True

        return recovery_dag if any_recovered else None

    # --- Internal Methods ---

    def _determine_needed_types(self, contract: EpistemicContract) -> List[str]:
        """Determine which capability types are needed for this contract."""
        types = self._KIND_TO_CAPABILITIES.get(contract.answer_kind, ["inference"])
        return list(types)

    def _match_capabilities(
        self,
        needed_types: List[str],
        available: List[CapabilityDescriptor],
    ) -> List[CapabilityDescriptor]:
        """Match available capabilities to needed types."""
        matched: List[CapabilityDescriptor] = []
        for cap in available:
            for needed in needed_types:
                if needed in cap.accepted_types or needed in cap.name:
                    matched.append(cap)
                    break
        return matched

    def _select_mode(
        self,
        query: QueryEnvelope,
        contract: EpistemicContract,
        capabilities: List[CapabilityDescriptor],
    ) -> str:
        """Select fast or deep mode based on budget and requirements.

        Returns 'fast' or 'deep'.
        """
        # If user explicitly requested a mode, honor it
        if query.requested_mode in ("fast", "deep"):
            return query.requested_mode

        # If high evidence requirement, use deep
        if contract.required_evidence in (
            EvidenceRequirement.PROVEN,
            EvidenceRequirement.WITNESSED,
        ):
            return "deep"

        # If tight budget, use fast
        total_estimated = sum(
            cap.latency_model.get("avg_ms", 100) for cap in capabilities
        )
        if total_estimated > query.resource_budget.max_time_ms * 0.7:
            return "fast"

        return "deep"

    def _build_dag(
        self,
        ctx: PlanningContext,
        capabilities: List[CapabilityDescriptor],
        mode: str,
    ) -> PlanDAG:
        """Build the execution DAG from matched capabilities."""
        dag = PlanDAG()

        # In fast mode, use only the best single capability
        if mode == "fast" and capabilities:
            cap = capabilities[0]
            step = PlanStep(
                id=f"exec_{cap.name}",
                name=f"Execute {cap.name}",
                capability=cap.name,
                preconditions=cap.preconditions,
                postconditions=cap.postconditions,
                expected_cost_ms=int(cap.latency_model.get("avg_ms", 100)),
                expected_info_gain=0.7,
            )
            dag.add_step(step)
            return dag

        # In deep mode, build full dependency chain
        previous_step_id: Optional[str] = None
        step_ids: List[str] = []

        for i, cap in enumerate(capabilities):
            step_id = f"exec_{cap.name}_{i}"
            step = PlanStep(
                id=step_id,
                name=f"Execute {cap.name}",
                capability=cap.name,
                preconditions=cap.preconditions,
                postconditions=cap.postconditions,
                expected_cost_ms=int(cap.latency_model.get("avg_ms", 100)),
                expected_info_gain=1.0 / (i + 1),
            )
            dag.add_step(step)
            step_ids.append(step_id)

            # Determine dependencies based on pre/postcondition matching
            if previous_step_id is not None:
                prev_step = dag.steps[previous_step_id]
                # If this step's preconditions overlap with previous postconditions
                if self._conditions_overlap(
                    cap.preconditions, prev_step.postconditions
                ):
                    dag.add_dependency(step_id, previous_step_id)

            previous_step_id = step_id

        # Add aggregation step if multiple capabilities
        if len(step_ids) > 1:
            agg_step = PlanStep(
                id="aggregate",
                name="Aggregate results",
                capability="aggregator",
                preconditions=[f"result_{sid}" for sid in step_ids],
                postconditions=["final_answer"],
                expected_cost_ms=10,
                expected_info_gain=0.1,
            )
            dag.add_step(agg_step)
            # Aggregation depends on all execution steps
            for sid in step_ids:
                dag.add_dependency("aggregate", sid)

        return dag

    def _add_verification_steps(
        self,
        dag: PlanDAG,
        contract: EpistemicContract,
        capabilities: List[CapabilityDescriptor],
    ) -> None:
        """Add verification steps for steps that need evidence."""
        steps_to_verify = [
            sid for sid, step in dag.steps.items()
            if step.capability != "aggregator"
            and step.id != "aggregate"
        ]

        for step_id in steps_to_verify:
            step = dag.steps[step_id]
            verify_step = PlanStep(
                id=f"verify_{step_id}",
                name=f"Verify {step.name}",
                capability=f"{step.capability}_verify",
                preconditions=[f"result_{step_id}"],
                postconditions=[f"verified_{step_id}"],
                expected_cost_ms=max(step.expected_cost_ms // 2, 10),
                expected_info_gain=0.1,
            )
            dag.add_step(verify_step)
            dag.add_dependency(f"verify_{step_id}", step_id)

            # If there's an aggregation step, it should depend on verification
            if "aggregate" in dag.steps:
                # Remove direct dependency and add through verify
                if step_id in dag.dependencies.get("aggregate", []):
                    dag.dependencies["aggregate"].remove(step_id)
                    dag.add_dependency("aggregate", f"verify_{step_id}")

    def _create_unsupported_plan(
        self,
        query: QueryEnvelope,
        contract: EpistemicContract,
    ) -> PlanDAG:
        """Create a minimal plan for unsupported queries."""
        dag = PlanDAG(deadline_ms=int(query.resource_budget.max_time_ms))
        step = PlanStep(
            id="unsupported",
            name="No matching capability",
            capability="none",
            preconditions=[],
            postconditions=["unsupported_response"],
            expected_cost_ms=1,
            expected_info_gain=0.0,
        )
        dag.add_step(step)
        return dag

    def _compute_budget(self, spec: ResourceBudgetSpec) -> ResourceBudget:
        """Convert query budget spec to plan budget."""
        return ResourceBudget(
            max_time_ms=int(spec.max_time_ms),
            max_memory_mb=int(spec.max_memory_mb),
            max_parallel=4,
            max_retries=2,
        )

    def _conditions_overlap(self, preconditions: List[str], postconditions: List[str]) -> bool:
        """Check if any precondition is satisfied by a postcondition."""
        pre_set = set(preconditions)
        post_set = set(postconditions)
        return bool(pre_set & post_set)
