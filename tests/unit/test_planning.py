"""Tests for Phase R4: Planning subsystem — PlanDAG, Transaction, Planner."""

from __future__ import annotations

import time
import pytest

import sys
from pathlib import Path

# Ensure src is on path
_SRC = str(Path(__file__).parent.parent.parent / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from axima.planning.plan_dag import (
    BranchCondition,
    PlanDAG,
    PlanStep,
    ResourceBudget,
    StepStatus,
)
from axima.planning.transaction import (
    AuditEvent,
    InvalidTransitionError,
    RollbackAction,
    Transaction,
    TransactionManager,
    TransactionState,
)
from axima.planning.planner import CognitivePlanner, PlanningContext
from axima.contracts.query import QueryEnvelope, ExecutionResult
from axima.epistemics.contracts import (
    AnswerKind,
    EpistemicContract,
    EvidenceRequirement,
)
from axima.kernel.registry import CapabilityDescriptor


# ============================================================
# PlanStep Tests
# ============================================================

class TestPlanStep:
    def test_create_step(self):
        step = PlanStep(
            id="s1",
            name="Test Step",
            capability="math_solver",
        )
        assert step.id == "s1"
        assert step.name == "Test Step"
        assert step.capability == "math_solver"
        assert step.status == StepStatus.PENDING
        assert step.preconditions == []
        assert step.postconditions == []
        assert step.expected_cost_ms == 100
        assert step.expected_info_gain == 0.5

    def test_step_to_dict(self):
        step = PlanStep(
            id="s1",
            name="Test",
            capability="math",
            preconditions=["input_ready"],
            postconditions=["result_available"],
            expected_cost_ms=200,
        )
        d = step.to_dict()
        assert d["id"] == "s1"
        assert d["status"] == "pending"
        assert d["preconditions"] == ["input_ready"]
        assert d["expected_cost_ms"] == 200

    def test_step_with_branch_condition(self):
        bc = BranchCondition(
            condition_step="s1",
            match_value="done",
            then_steps=["s2"],
            else_steps=["s3"],
        )
        step = PlanStep(id="s1", name="Branch", capability="router", branch_condition=bc)
        d = step.to_dict()
        assert "branch_condition" in d
        assert d["branch_condition"]["then_steps"] == ["s2"]


# ============================================================
# PlanDAG Tests
# ============================================================

class TestPlanDAG:
    def _make_dag(self) -> PlanDAG:
        """Create a simple 3-step DAG: A -> B -> C"""
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="Step A", capability="cap_a", expected_cost_ms=100))
        dag.add_step(PlanStep(id="b", name="Step B", capability="cap_b", expected_cost_ms=200))
        dag.add_step(PlanStep(id="c", name="Step C", capability="cap_c", expected_cost_ms=150))
        dag.add_dependency("b", "a")
        dag.add_dependency("c", "b")
        return dag

    def test_add_step(self):
        dag = PlanDAG()
        step = PlanStep(id="s1", name="S1", capability="cap")
        dag.add_step(step)
        assert "s1" in dag.steps
        assert dag.steps["s1"] is step

    def test_add_duplicate_step_raises(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="s1", name="S1", capability="cap"))
        with pytest.raises(ValueError, match="already exists"):
            dag.add_step(PlanStep(id="s1", name="S1 dup", capability="cap"))

    def test_add_dependency(self):
        dag = self._make_dag()
        assert "a" in dag.dependencies["b"]
        assert "b" in dag.dependencies["c"]

    def test_add_dependency_unknown_step_raises(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="A", capability="cap"))
        with pytest.raises(ValueError, match="not found"):
            dag.add_dependency("a", "nonexistent")

    def test_self_dependency_raises(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="A", capability="cap"))
        with pytest.raises(ValueError, match="cannot depend on itself"):
            dag.add_dependency("a", "a")

    def test_cycle_detection(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="A", capability="cap"))
        dag.add_step(PlanStep(id="b", name="B", capability="cap"))
        dag.add_dependency("b", "a")
        with pytest.raises(ValueError, match="cycle"):
            dag.add_dependency("a", "b")

    def test_topological_sort(self):
        dag = self._make_dag()
        order = dag.topological_sort()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_get_ready_steps_initial(self):
        dag = self._make_dag()
        ready = dag.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "a"

    def test_get_ready_steps_after_completion(self):
        dag = self._make_dag()
        dag.mark_complete("a")
        ready = dag.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].id == "b"

    def test_parallel_groups(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="A", capability="cap", expected_cost_ms=100))
        dag.add_step(PlanStep(id="b", name="B", capability="cap", expected_cost_ms=100))
        dag.add_step(PlanStep(id="c", name="C", capability="cap", expected_cost_ms=100))
        # a and b are independent, c depends on both
        dag.add_dependency("c", "a")
        dag.add_dependency("c", "b")
        groups = dag.get_parallel_groups()
        assert len(groups) == 2
        assert set(groups[0]) == {"a", "b"}
        assert groups[1] == ["c"]

    def test_critical_path(self):
        dag = self._make_dag()
        cp = dag.get_critical_path()
        # All steps are on the critical path in a linear chain
        assert cp == ["a", "b", "c"]

    def test_mark_complete(self):
        dag = self._make_dag()
        dag.mark_complete("a", result={"value": 42})
        assert dag.steps["a"].status == StepStatus.DONE
        assert dag.steps["a"].result == {"value": 42}

    def test_mark_failed_propagates(self):
        dag = self._make_dag()
        dag.mark_failed("a", "timeout")
        assert dag.steps["a"].status == StepStatus.FAILED
        # b depends on a, should be skipped
        assert dag.steps["b"].status == StepStatus.SKIPPED

    def test_rollback_plan(self):
        dag = self._make_dag()
        dag.mark_complete("a")
        dag.mark_complete("b")
        dag.rollback_plan()
        for step in dag.steps.values():
            assert step.status == StepStatus.PENDING
            assert step.result is None

    def test_validate_valid(self):
        dag = self._make_dag()
        dag.deadline_ms = 10000
        errors = dag.validate()
        assert errors == []

    def test_validate_budget_exceeded(self):
        dag = self._make_dag()
        dag.deadline_ms = 100  # Too tight
        errors = dag.validate()
        assert any("exceeds deadline" in e for e in errors)

    def test_to_dict(self):
        dag = self._make_dag()
        d = dag.to_dict()
        assert "steps" in d
        assert "dependencies" in d
        assert "budget" in d
        assert "critical_path" in d
        assert len(d["steps"]) == 3

    def test_remove_step(self):
        dag = self._make_dag()
        dag.remove_step("b")
        assert "b" not in dag.steps
        assert "b" not in dag.dependencies
        # c's dependency on b should be removed
        assert "b" not in dag.dependencies.get("c", [])

    def test_estimated_total_cost(self):
        dag = PlanDAG()
        dag.add_step(PlanStep(id="a", name="A", capability="cap", expected_cost_ms=100))
        dag.add_step(PlanStep(id="b", name="B", capability="cap", expected_cost_ms=200))
        dag.add_step(PlanStep(id="c", name="C", capability="cap", expected_cost_ms=50))
        dag.add_dependency("c", "a")
        dag.add_dependency("c", "b")
        # a and b are parallel (max=200), then c (50) = 250
        cost = dag.estimated_total_cost_ms()
        assert cost == 250


# ============================================================
# Transaction Tests
# ============================================================

class TestTransaction:
    def test_create_transaction(self):
        txn = Transaction()
        assert txn.state == TransactionState.PLANNING
        assert txn.audit_events == []
        assert txn.rollback_actions == []
        assert not txn.is_terminal

    def test_valid_transition(self):
        txn = Transaction()
        txn.transition_to(TransactionState.PREFLIGHT, "starting checks")
        assert txn.state == TransactionState.PREFLIGHT
        assert len(txn.audit_events) == 1
        assert txn.audit_events[0].to_state == TransactionState.PREFLIGHT

    def test_invalid_transition_raises(self):
        txn = Transaction()
        with pytest.raises(InvalidTransitionError):
            txn.transition_to(TransactionState.EXECUTING)

    def test_terminal_states(self):
        txn = Transaction()
        txn.transition_to(TransactionState.PREFLIGHT)
        txn.transition_to(TransactionState.ROLLED_BACK)
        assert txn.is_terminal

    def test_audit_trail(self):
        txn = Transaction()
        txn.transition_to(TransactionState.PREFLIGHT, "preflight")
        txn.transition_to(TransactionState.ROLLED_BACK, "failed check")
        assert len(txn.audit_events) == 2
        assert txn.audit_events[0].detail == "preflight"
        assert txn.audit_events[1].detail == "failed check"

    def test_rollback_action(self):
        called = []
        action = RollbackAction(
            step_id="s1",
            undo_fn=lambda: called.append(True),
            description="undo s1",
        )
        assert action.execute()
        assert called == [True]
        assert action.executed

    def test_rollback_action_failure(self):
        def bad_undo():
            raise RuntimeError("undo failed")

        action = RollbackAction(step_id="s1", undo_fn=bad_undo)
        assert not action.execute()
        assert not action.executed

    def test_to_dict(self):
        txn = Transaction()
        d = txn.to_dict()
        assert d["state"] == "planning"
        assert "audit_events" in d
        assert "plan" in d


class TestTransactionManager:
    def _make_plan(self) -> PlanDAG:
        dag = PlanDAG(deadline_ms=10000)
        dag.add_step(PlanStep(id="a", name="A", capability="cap", expected_cost_ms=100))
        dag.add_step(PlanStep(id="b", name="B", capability="cap", expected_cost_ms=100))
        dag.add_dependency("b", "a")
        return dag

    def test_begin(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)
        assert txn.state == TransactionState.PLANNING
        assert mgr.active_count == 1

    def test_begin_invalid_plan_raises(self):
        mgr = TransactionManager()
        plan = PlanDAG()
        plan.steps["ghost"] = PlanStep(id="ghost", name="G", capability="cap")
        plan.dependencies["ghost"] = ["nonexistent"]
        with pytest.raises(ValueError):
            mgr.begin(plan)

    def test_full_lifecycle(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)

        # Preflight
        warnings = mgr.preflight(txn)
        assert txn.state == TransactionState.PREFLIGHT

        # Authorize
        mgr.authorize(txn, actor="test_user")
        assert txn.state == TransactionState.AUTHORIZED

        # Execute
        results = mgr.execute(txn)
        assert txn.state == TransactionState.EXECUTING
        assert "a" in results
        assert "b" in results

        # Verify
        issues = mgr.verify(txn)
        assert txn.state == TransactionState.VERIFYING
        assert issues == []

        # Commit
        mgr.commit(txn)
        assert txn.state == TransactionState.COMMITTED
        assert txn.is_terminal
        assert mgr.active_count == 0
        assert len(mgr.history) == 1

    def test_execute_with_custom_executor(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)
        mgr.preflight(txn)
        mgr.authorize(txn)

        def my_executor(step):
            return {"computed": step.name}

        results = mgr.execute(txn, executor=my_executor)
        assert results["a"] == {"computed": "A"}
        assert results["b"] == {"computed": "B"}

    def test_execute_with_failure(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)
        mgr.preflight(txn)
        mgr.authorize(txn)

        def failing_executor(step):
            if step.id == "a":
                raise RuntimeError("step a failed")
            return {"ok": True}

        results = mgr.execute(txn, executor=failing_executor)
        assert "error" in results["a"]
        # b depends on a, should be skipped
        assert plan.steps["b"].status == StepStatus.SKIPPED

    def test_rollback(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)
        mgr.preflight(txn)
        mgr.authorize(txn)
        mgr.execute(txn)

        # Rollback instead of verify/commit
        failures = mgr.rollback(txn, reason="test rollback")
        assert failures == []
        assert txn.state == TransactionState.ROLLED_BACK
        assert txn.is_terminal
        # Plan should be reset
        for step in plan.steps.values():
            assert step.status == StepStatus.PENDING

    def test_cannot_rollback_committed(self):
        mgr = TransactionManager()
        plan = self._make_plan()
        txn = mgr.begin(plan)
        mgr.preflight(txn)
        mgr.authorize(txn)
        mgr.execute(txn)
        mgr.verify(txn)
        mgr.commit(txn)

        with pytest.raises(InvalidTransitionError):
            mgr.rollback(txn)


# ============================================================
# CognitivePlanner Tests
# ============================================================

class TestCognitivePlanner:
    def _make_capabilities(self) -> list:
        return [
            CapabilityDescriptor(
                name="math_solver",
                accepted_types=["math", "calculate"],
                produced_types=["derivation"],
                preconditions=[],
                postconditions=["mathematical_result"],
                latency_model={"avg_ms": 150},
            ),
            CapabilityDescriptor(
                name="inference_engine",
                accepted_types=["inference", "knowledge", "fact"],
                produced_types=["fact"],
                preconditions=[],
                postconditions=["factual_answer"],
                latency_model={"avg_ms": 80},
            ),
            CapabilityDescriptor(
                name="physics_solver",
                accepted_types=["physics"],
                produced_types=["numeric_result"],
                preconditions=[],
                postconditions=["physics_result"],
                latency_model={"avg_ms": 200},
            ),
            CapabilityDescriptor(
                name="coder",
                accepted_types=["code", "algorithm"],
                produced_types=["code"],
                preconditions=[],
                postconditions=["generated_code"],
                latency_model={"avg_ms": 300},
            ),
            CapabilityDescriptor(
                name="creator",
                accepted_types=["creative", "story", "poem"],
                produced_types=["creative_text"],
                preconditions=[],
                postconditions=["generated_content"],
                latency_model={"avg_ms": 200},
            ),
        ]

    def test_plan_fact_query(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="What is the capital of France?")
        contract = EpistemicContract(
            answer_kind=AnswerKind.FACT,
            required_evidence=EvidenceRequirement.SOURCED,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        assert len(dag.steps) > 0
        errors = dag.validate()
        # Filter out budget warnings
        structural_errors = [e for e in errors if "cycle" in e or "unknown" in e]
        assert structural_errors == []

    def test_plan_math_query(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Solve x^2 + 3x + 2 = 0")
        contract = EpistemicContract(
            answer_kind=AnswerKind.DERIVATION,
            required_evidence=EvidenceRequirement.PROVEN,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        assert len(dag.steps) > 0
        # Should include verification steps for PROVEN evidence
        verify_steps = [s for s in dag.steps if s.startswith("verify_")]
        assert len(verify_steps) > 0

    def test_plan_creative_query(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Write a poem about the ocean")
        contract = EpistemicContract(
            answer_kind=AnswerKind.CREATIVE,
            required_evidence=EvidenceRequirement.NONE,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        assert len(dag.steps) > 0
        # Creative doesn't need verification
        verify_steps = [s for s in dag.steps if s.startswith("verify_")]
        assert len(verify_steps) == 0

    def test_plan_no_matching_capabilities(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Do something impossible")
        contract = EpistemicContract(
            answer_kind=AnswerKind.FACT,
            required_evidence=EvidenceRequirement.SOURCED,
        )
        # No capabilities at all
        dag = planner.plan(query, contract, [])
        assert "unsupported" in dag.steps

    def test_plan_fast_mode(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Quick answer", requested_mode="fast")
        contract = EpistemicContract(
            answer_kind=AnswerKind.FACT,
            required_evidence=EvidenceRequirement.HEURISTIC,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        # Fast mode should produce fewer steps
        non_verify = [s for s in dag.steps if not s.startswith("verify_")]
        assert len(non_verify) <= 2  # Single exec step (maybe + aggregate)

    def test_plan_recovery(self):
        planner = CognitivePlanner()
        # Create a plan and simulate failure
        query = QueryEnvelope(raw_input="Calculate pi")
        contract = EpistemicContract(
            answer_kind=AnswerKind.DERIVATION,
            required_evidence=EvidenceRequirement.SOURCED,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        # Pick a step to fail
        failed_steps = [list(dag.steps.keys())[0]]
        recovery = planner.plan_recovery(dag, failed_steps, caps)
        # Recovery may or may not be possible depending on alternatives
        # but should not crash
        assert recovery is None or isinstance(recovery, PlanDAG)

    def test_plan_sets_budget(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Solve 2+2")
        query.resource_budget.max_time_ms = 3000
        contract = EpistemicContract(
            answer_kind=AnswerKind.FACT,
            required_evidence=EvidenceRequirement.NONE,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        assert dag.budget.max_time_ms == 3000
        assert dag.deadline_ms == 3000

    def test_plan_topological_order_valid(self):
        planner = CognitivePlanner()
        query = QueryEnvelope(raw_input="Complex derivation")
        contract = EpistemicContract(
            answer_kind=AnswerKind.DERIVATION,
            required_evidence=EvidenceRequirement.SOURCED,
        )
        caps = self._make_capabilities()

        dag = planner.plan(query, contract, caps)
        # Should not raise
        order = dag.topological_sort()
        assert len(order) == len(dag.steps)
