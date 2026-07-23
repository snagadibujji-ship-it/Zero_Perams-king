"""Tests for Phase R11: Governed Symbolic Self-Improvement.

Covers prediction engine, skill foundry, learning loop, and governance gate.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

sys.path.insert(0, "/root/hybrid-ai/src")

from axima.cognition.prediction import Prediction, PredictionEngine
from axima.cognition.skill_foundry import ApprovalStatus, SkillCandidate, SkillFoundry, SkillSpec
from axima.cognition.learning_loop import LearningSignal, RealityGapLoop, RevisionScope, RevisionStatus
from axima.cognition.governance import GovernanceGate, GovernancePolicy, PermissionResult
from axima.cognition.experiment import Experiment, ExperimentEngine, ExperimentStatus, ResultDomain


# ===========================================================================
# Prediction Engine Tests
# ===========================================================================


class TestPrediction(unittest.TestCase):
    """Tests for Prediction dataclass validation."""

    def test_valid_prediction(self) -> None:
        now = datetime.now(timezone.utc)
        p = Prediction(
            id="test-1",
            claim="X will happen",
            predicted_outcome=True,
            confidence=0.8,
            timestamp=now,
            resolution_deadline=now + timedelta(hours=1),
        )
        self.assertEqual(p.id, "test-1")
        self.assertEqual(p.confidence, 0.8)
        self.assertIsNone(p.actual_outcome)

    def test_invalid_confidence_too_high(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            Prediction(
                id="test-2",
                claim="bad",
                predicted_outcome=True,
                confidence=1.5,
                timestamp=now,
                resolution_deadline=now + timedelta(hours=1),
            )

    def test_invalid_confidence_negative(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            Prediction(
                id="test-3",
                claim="bad",
                predicted_outcome=True,
                confidence=-0.1,
                timestamp=now,
                resolution_deadline=now + timedelta(hours=1),
            )

    def test_invalid_deadline_before_timestamp(self) -> None:
        now = datetime.now(timezone.utc)
        with self.assertRaises(ValueError):
            Prediction(
                id="test-4",
                claim="bad",
                predicted_outcome=True,
                confidence=0.5,
                timestamp=now,
                resolution_deadline=now - timedelta(hours=1),
            )


class TestPredictionEngine(unittest.TestCase):
    """Tests for PredictionEngine lifecycle."""

    def setUp(self) -> None:
        self.engine = PredictionEngine()

    def test_predict_creates_record(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        pred = self.engine.predict("test claim", True, 0.9, deadline)
        self.assertIsNotNone(pred.id)
        self.assertEqual(pred.claim, "test claim")
        self.assertEqual(pred.confidence, 0.9)
        self.assertIsNone(pred.actual_outcome)

    def test_record_outcome_resolves_prediction(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        pred = self.engine.predict("will succeed", True, 0.8, deadline)
        resolved = self.engine.record_outcome(pred.id, True)
        self.assertTrue(resolved.correct)
        self.assertEqual(resolved.actual_outcome, True)
        self.assertIsNotNone(resolved.resolved_at)

    def test_record_outcome_incorrect(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        pred = self.engine.predict("will succeed", True, 0.8, deadline)
        resolved = self.engine.record_outcome(pred.id, False)
        self.assertFalse(resolved.correct)

    def test_no_post_hoc_rewriting(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        pred = self.engine.predict("test", True, 0.7, deadline)
        self.engine.record_outcome(pred.id, False)
        with self.assertRaises(ValueError):
            self.engine.record_outcome(pred.id, True)

    def test_record_outcome_unknown_id(self) -> None:
        with self.assertRaises(KeyError):
            self.engine.record_outcome("nonexistent", True)

    def test_brier_score_perfect(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        # Perfect predictions: confidence 1.0, all correct
        for _ in range(5):
            pred = self.engine.predict("will happen", True, 1.0, deadline)
            self.engine.record_outcome(pred.id, True)
        self.assertAlmostEqual(self.engine.brier_score(), 0.0)

    def test_brier_score_worst(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        # Worst predictions: confidence 1.0, all wrong
        for _ in range(5):
            pred = self.engine.predict("will happen", True, 1.0, deadline)
            self.engine.record_outcome(pred.id, False)
        self.assertAlmostEqual(self.engine.brier_score(), 1.0)

    def test_calibration_score_empty(self) -> None:
        self.assertEqual(self.engine.calibration_score(), 0.0)

    def test_brier_score_empty(self) -> None:
        self.assertEqual(self.engine.brier_score(), 0.0)

    def test_get_pending(self) -> None:
        deadline = datetime.now(timezone.utc) + timedelta(hours=1)
        p1 = self.engine.predict("a", True, 0.5, deadline)
        p2 = self.engine.predict("b", False, 0.6, deadline)
        self.engine.record_outcome(p1.id, True)
        pending = self.engine.get_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].id, p2.id)


# ===========================================================================
# Skill Foundry Tests
# ===========================================================================


class TestSkillFoundry(unittest.TestCase):
    """Tests for skill extraction, anti-unification, and governance."""

    def setUp(self) -> None:
        self.foundry = SkillFoundry()

    def _make_traces(self, n: int = 4) -> list:
        return [
            {"operation": "sort", "input": list(range(n - i, 0, -1)), "output": list(range(1, n - i + 1)), "success": True}
            for i in range(n)
        ]

    def test_extract_from_trace(self) -> None:
        traces = self._make_traces()
        spec = self.foundry.extract_from_trace(traces)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.name, "sort")
        self.assertIn("input is not None", spec.preconditions)
        self.assertIn("output is not None", spec.postconditions)

    def test_extract_from_empty_traces(self) -> None:
        self.assertIsNone(self.foundry.extract_from_trace([]))

    def test_anti_unify_single_trace(self) -> None:
        traces = [{"operation": "sort", "input": [3, 2, 1]}]
        result = self.foundry.anti_unify(traces)
        self.assertIn("sort", result)

    def test_anti_unify_multiple_traces(self) -> None:
        traces = self._make_traces()
        result = self.foundry.anti_unify(traces)
        self.assertIn("def skill(", result)
        self.assertIn("parameter", result)

    def test_submit_for_approval(self) -> None:
        traces = self._make_traces()
        spec = self.foundry.extract_from_trace(traces)
        candidate = self.foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [3, 1, 2], "expected": [1, 2, 3]}],
            negative_tests=[{"input": None, "expected": "error"}],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        self.assertEqual(candidate.approval_status, ApprovalStatus.CANDIDATE)
        self.assertIn(candidate.id, self.foundry.candidates)

    def test_reject_overfitting(self) -> None:
        """Candidates with < 3 traces are rejected as overfitting."""
        traces = self._make_traces(2)
        spec = self.foundry.extract_from_trace(traces)
        candidate = self.foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [2, 1], "expected": [1, 2]}],
            negative_tests=[],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        passed, reason = self.foundry.test_candidate(candidate)
        self.assertFalse(passed)
        self.assertIn("overfitting", reason.lower())

    def test_promote_without_governance(self) -> None:
        traces = self._make_traces(4)
        spec = self.foundry.extract_from_trace(traces)
        candidate = self.foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [3, 1], "expected": [1, 3]}],
            negative_tests=[{"input": None, "expected": "error"}],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        promoted = self.foundry.promote(candidate.id)
        self.assertEqual(promoted.approval_status, ApprovalStatus.APPROVED)
        self.assertIn(candidate.id, self.foundry.promoted_skills)

    def test_revoke_skill(self) -> None:
        traces = self._make_traces(4)
        spec = self.foundry.extract_from_trace(traces)
        candidate = self.foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [3, 1], "expected": [1, 3]}],
            negative_tests=[{"input": None, "expected": "error"}],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        self.foundry.promote(candidate.id)
        revoked = self.foundry.revoke(candidate.id, "found bug")
        self.assertEqual(revoked.approval_status, ApprovalStatus.REVOKED)
        self.assertNotIn(candidate.id, self.foundry.promoted_skills)


# ===========================================================================
# Learning Loop Tests
# ===========================================================================


class TestLearningLoop(unittest.TestCase):
    """Tests for reality gap detection and bounded revision."""

    def setUp(self) -> None:
        self.loop = RealityGapLoop()
        self.loop.set_rule("gravity", 9.81)
        self.loop.set_rule("speed_of_light", 299792458)

    def test_record_gap(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="Update gravity constant for altitude",
            scope=RevisionScope.LOCAL,
        )
        self.assertEqual(signal.prediction_id, "pred-1")
        self.assertEqual(signal.error_type, "false_positive")
        self.assertEqual(len(self.loop.signals), 1)

    def test_identify_cause(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="miscalibration",
            causal_rule="gravity",
            proposed_revision="adjust",
        )
        cause = self.loop.identify_cause(signal)
        self.assertEqual(cause["rule"], "gravity")
        self.assertEqual(cause["current_state"], 9.81)
        self.assertIn("miscalibration", cause["error_type"])

    def test_propose_and_validate_local_revision(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="Use 9.80 for sea level",
        )
        revision = self.loop.propose_revision(signal, {"gravity": 9.80})
        self.assertEqual(revision.status, RevisionStatus.PROPOSED)

        passed, reason = self.loop.validate_revision(revision.id)
        self.assertTrue(passed)
        self.assertIn("LOCAL", reason)

    def test_apply_revision(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="adjust",
        )
        revision = self.loop.propose_revision(signal, {"gravity": 9.80})
        self.loop.validate_revision(revision.id)
        success, _ = self.loop.apply_if_approved(revision.id)
        self.assertTrue(success)
        self.assertEqual(self.loop.get_rule("gravity"), 9.80)

    def test_rollback_revision(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="adjust",
        )
        revision = self.loop.propose_revision(signal, {"gravity": 9.80})
        self.loop.validate_revision(revision.id)
        self.loop.apply_if_approved(revision.id)
        self.assertEqual(self.loop.get_rule("gravity"), 9.80)

        success, _ = self.loop.rollback(revision.id)
        self.assertTrue(success)
        self.assertEqual(self.loop.get_rule("gravity"), 9.81)

    def test_cannot_apply_unvalidated(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="adjust",
        )
        revision = self.loop.propose_revision(signal, {"gravity": 9.80})
        success, reason = self.loop.apply_if_approved(revision.id)
        self.assertFalse(success)
        self.assertIn("not validated", reason.lower())

    def test_cannot_rollback_unapplied(self) -> None:
        signal = self.loop.record_gap(
            prediction_id="pred-1",
            error_type="false_positive",
            causal_rule="gravity",
            proposed_revision="adjust",
        )
        revision = self.loop.propose_revision(signal, {"gravity": 9.80})
        success, reason = self.loop.rollback(revision.id)
        self.assertFalse(success)


# ===========================================================================
# Governance Tests
# ===========================================================================


class TestGovernance(unittest.TestCase):
    """Tests for governance gate and policy enforcement."""

    def setUp(self) -> None:
        self.gate = GovernanceGate()

    def test_allowed_action(self) -> None:
        perm = self.gate.check_permission("search_local_graph")
        self.assertTrue(perm.allowed)
        self.assertEqual(perm.result, PermissionResult.ALLOWED)

    def test_forbidden_action(self) -> None:
        perm = self.gate.check_permission("deploy_to_production")
        self.assertFalse(perm.allowed)
        self.assertEqual(perm.result, PermissionResult.DENIED)

    def test_cannot_change_governance(self) -> None:
        perm = self.gate.check_permission("change_governance")
        self.assertFalse(perm.allowed)

    def test_cannot_grant_self_capabilities(self) -> None:
        perm = self.gate.check_permission("grant_self_capabilities")
        self.assertFalse(perm.allowed)

    def test_cannot_delete_audit_history(self) -> None:
        perm = self.gate.check_permission("delete_audit_history")
        self.assertFalse(perm.allowed)

    def test_cannot_claim_benchmark_victory(self) -> None:
        perm = self.gate.check_permission("claim_benchmark_victory")
        self.assertFalse(perm.allowed)

    def test_approval_required_action(self) -> None:
        perm = self.gate.check_permission("promote_skill")
        self.assertEqual(perm.result, PermissionResult.REQUIRES_APPROVAL)
        self.assertFalse(perm.allowed)

    def test_approval_workflow(self) -> None:
        # Request approval
        request_id = self.gate.request_approval("promote_skill", "Skill passed all tests")
        # Grant approval
        self.gate.grant_approval(request_id, "human_operator")
        # Now check permission
        perm = self.gate.check_permission("promote_skill")
        self.assertTrue(perm.allowed)

    def test_deny_approval(self) -> None:
        request_id = self.gate.request_approval("promote_skill", "Please")
        self.gate.deny_approval(request_id, "human", "Not ready")
        # Still not allowed (no standing approval)
        perm = self.gate.check_permission("promote_skill")
        self.assertEqual(perm.result, PermissionResult.REQUIRES_APPROVAL)

    def test_unknown_action_denied(self) -> None:
        perm = self.gate.check_permission("hack_the_planet")
        self.assertFalse(perm.allowed)
        self.assertEqual(perm.result, PermissionResult.DENIED)

    def test_enforce_raises_on_denied(self) -> None:
        with self.assertRaises(PermissionError):
            self.gate.enforce("deploy_to_production")

    def test_enforce_passes_on_allowed(self) -> None:
        perm = self.gate.enforce("search_local_graph")
        self.assertTrue(perm.allowed)

    def test_audit_log_records_all_checks(self) -> None:
        self.gate.check_permission("search_local_graph")
        self.gate.check_permission("deploy_to_production")
        log = self.gate.audit()
        self.assertEqual(len(log), 2)
        self.assertEqual(log[0].action, "search_local_graph")
        self.assertEqual(log[1].action, "deploy_to_production")

    def test_all_forbidden_actions_denied(self) -> None:
        """Verify every forbidden action in policy is actually denied."""
        policy = self.gate.policy
        for action in policy.forbidden_actions:
            perm = self.gate.check_permission(action)
            self.assertFalse(perm.allowed, f"Action '{action}' should be denied but was allowed")


# ===========================================================================
# Experiment Engine Tests
# ===========================================================================


class TestExperimentEngine(unittest.TestCase):
    """Tests for preregistered experiments and simulation boundary."""

    def setUp(self) -> None:
        self.engine = ExperimentEngine()

    def test_design_experiment(self) -> None:
        exp = self.engine.design(
            hypothesis="Sorting is O(n log n)",
            variables={"n": [100, 1000, 10000]},
            controls=["random_input", "sorted_input"],
        )
        self.assertEqual(exp.status, ExperimentStatus.PLANNED)
        self.assertEqual(exp.hypothesis, "Sorting is O(n log n)")

    def test_preregister_criteria(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        exp = self.engine.preregister(exp.id, ["time < n*log(n)*2", "memory < 2*n"])
        self.assertEqual(len(exp.preregistered_criteria), 2)
        self.assertIsNotNone(exp.preregistered_at)

    def test_cannot_preregister_after_start(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["criterion"])
        self.engine.run(exp.id, lambda e: {"success": True})
        with self.assertRaises(ValueError):
            self.engine.preregister(exp.id, ["new criterion"])

    def test_cannot_preregister_twice(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["criterion 1"])
        with self.assertRaises(ValueError):
            self.engine.preregister(exp.id, ["criterion 2"])

    def test_cannot_run_without_preregistration(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        with self.assertRaises(ValueError):
            self.engine.run(exp.id, lambda e: {"success": True})

    def test_run_experiment_success(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["output is valid"])
        exp = self.engine.run(exp.id, lambda e: {"success": True, "value": 42})
        self.assertEqual(exp.status, ExperimentStatus.COMPLETE)
        self.assertIsNotNone(exp.results)
        self.assertEqual(exp.results.data["value"], 42)

    def test_run_experiment_failure(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["output is valid"])

        def failing_runner(e: Experiment) -> Dict[str, Any]:
            raise RuntimeError("Experiment crashed")

        exp = self.engine.run(exp.id, failing_runner)
        self.assertEqual(exp.status, ExperimentStatus.FAILED)
        self.assertIn("failed", exp.conclusion)

    def test_simulated_result_not_fact(self) -> None:
        """Simulated results cannot be promoted to real-world facts."""
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["success"])
        self.engine.run(exp.id, lambda e: {"success": True}, domain=ResultDomain.SIMULATED)
        self.engine.analyze(exp.id)
        discovery = self.engine.submit_discovery(exp.id, "Found something")
        self.assertEqual(discovery["domain"], "SIMULATED")
        self.assertFalse(discovery["is_fact"])
        self.assertIn("simulation", discovery["caveat"])

    def test_observed_result_can_be_fact(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["success"])
        self.engine.run(exp.id, lambda e: {"success": True}, domain=ResultDomain.OBSERVED)
        self.engine.analyze(exp.id)
        discovery = self.engine.submit_discovery(exp.id, "Confirmed finding")
        self.assertEqual(discovery["domain"], "OBSERVED")
        self.assertTrue(discovery["is_fact"])

    def test_analyze_results(self) -> None:
        exp = self.engine.design("H1", {"x": [1]}, ["control"])
        self.engine.preregister(exp.id, ["success"])
        self.engine.run(exp.id, lambda e: {"success": True})
        analysis = self.engine.analyze(exp.id)
        self.assertTrue(analysis["meets_criteria"])
        self.assertTrue(analysis["is_simulated"])


# ===========================================================================
# Integration: Governance + Skill Foundry
# ===========================================================================


class TestGovernanceIntegration(unittest.TestCase):
    """Test governance enforcement across components."""

    def test_skill_promotion_blocked_without_approval(self) -> None:
        """Skill foundry respects governance gate."""
        gate = GovernanceGate()
        foundry = SkillFoundry(governance_gate=gate)

        traces = [
            {"operation": "sort", "input": [i, i - 1], "output": [i - 1, i], "success": True}
            for i in range(5)
        ]
        spec = foundry.extract_from_trace(traces)
        candidate = foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [2, 1], "expected": [1, 2]}],
            negative_tests=[{"input": None, "expected": "error"}],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        # Promotion should be blocked — no approval granted
        result = foundry.promote(candidate.id)
        self.assertEqual(result.approval_status, ApprovalStatus.REJECTED)

    def test_skill_promotion_with_approval(self) -> None:
        """Skill foundry allows promotion after governance approval."""
        gate = GovernanceGate()
        foundry = SkillFoundry(governance_gate=gate)

        # Grant approval first
        req_id = gate.request_approval("promote_skill", "Skill validated")
        gate.grant_approval(req_id)

        traces = [
            {"operation": "sort", "input": [i, i - 1], "output": [i - 1, i], "success": True}
            for i in range(5)
        ]
        spec = foundry.extract_from_trace(traces)
        candidate = foundry.submit_for_approval(
            spec=spec,
            traces=traces,
            positive_tests=[{"input": [2, 1], "expected": [1, 2]}],
            negative_tests=[{"input": None, "expected": "error"}],
            adversarial_tests=[{"input": [], "expected": []}],
        )
        result = foundry.promote(candidate.id)
        self.assertEqual(result.approval_status, ApprovalStatus.APPROVED)

    def test_experiment_discovery_blocked_without_approval(self) -> None:
        """Experiment engine respects governance for discoveries."""
        gate = GovernanceGate()
        engine = ExperimentEngine(governance_gate=gate)

        exp = engine.design("H1", {"x": [1]}, ["control"])
        engine.preregister(exp.id, ["success"])
        engine.run(exp.id, lambda e: {"success": True}, domain=ResultDomain.OBSERVED)
        engine.analyze(exp.id)
        discovery = engine.submit_discovery(exp.id, "Finding")
        self.assertEqual(discovery["status"], "blocked_by_governance")


if __name__ == "__main__":
    unittest.main()
