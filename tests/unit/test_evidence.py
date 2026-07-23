"""Tests for the AXIMA evidence subsystem."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from datetime import datetime, timedelta, timezone

from axima.evidence.claims import Claim, ClaimStatus, ClaimGraph
from axima.evidence.derivation import DerivationStep, DerivationDAG
from axima.evidence.provenance import SourceTier, EvidenceRecord, ProvenanceStore
from axima.evidence.reality_ledger import EventType, LedgerEvent, RealityLedger
from axima.evidence.contradiction import Resolution, ContradictionCase, ContradictionCourt


# === Claims Tests ===

class TestClaimGraph:
    def test_add_claim(self):
        graph = ClaimGraph()
        claim = Claim(
            id="c1", statement="Water boils at 100C",
            status=ClaimStatus.PROPOSED, source_engine="physics",
            confidence_interval=(0.9, 0.99),
        )
        result = graph.add_claim(claim)
        assert result.id == "c1"
        assert graph.get_claim("c1") is not None

    def test_support_changes_status(self):
        graph = ClaimGraph()
        c1 = Claim(id="c1", statement="A", status=ClaimStatus.VERIFIED,
                   source_engine="math", confidence_interval=(0.95, 1.0))
        c2 = Claim(id="c2", statement="B", status=ClaimStatus.PROPOSED,
                   source_engine="math", confidence_interval=(0.8, 0.9))
        graph.add_claim(c1)
        graph.add_claim(c2)
        graph.support("c1", "c2")
        assert graph.get_claim("c2").status == ClaimStatus.SUPPORTED

    def test_contradict_changes_status(self):
        graph = ClaimGraph()
        c1 = Claim(id="c1", statement="A", status=ClaimStatus.VERIFIED,
                   source_engine="math", confidence_interval=(0.95, 1.0))
        c2 = Claim(id="c2", statement="not A", status=ClaimStatus.PROPOSED,
                   source_engine="physics", confidence_interval=(0.7, 0.8))
        graph.add_claim(c1)
        graph.add_claim(c2)
        graph.contradict("c1", "c2")
        assert graph.get_claim("c2").status == ClaimStatus.CONTRADICTED

    def test_retract(self):
        graph = ClaimGraph()
        c1 = Claim(id="c1", statement="A", status=ClaimStatus.VERIFIED,
                   source_engine="math", confidence_interval=(0.9, 1.0))
        graph.add_claim(c1)
        graph.retract("c1")
        assert graph.get_claim("c1").status == ClaimStatus.RETRACTED

    def test_get_unsupported(self):
        graph = ClaimGraph()
        c1 = Claim(id="c1", statement="A", status=ClaimStatus.PROPOSED,
                   source_engine="math", confidence_interval=(0.5, 0.6))
        c2 = Claim(id="c2", statement="B", status=ClaimStatus.VERIFIED,
                   source_engine="math", confidence_interval=(0.9, 1.0))
        graph.add_claim(c1)
        graph.add_claim(c2)
        unsupported = graph.get_unsupported()
        assert len(unsupported) == 1
        assert unsupported[0].id == "c1"

    def test_get_chain(self):
        graph = ClaimGraph()
        c1 = Claim(id="c1", statement="axiom", status=ClaimStatus.VERIFIED,
                   source_engine="math", confidence_interval=(1.0, 1.0))
        c2 = Claim(id="c2", statement="derived", status=ClaimStatus.PROPOSED,
                   source_engine="math", confidence_interval=(0.8, 0.9))
        graph.add_claim(c1)
        graph.add_claim(c2)
        graph.support("c1", "c2")
        chain = graph.get_chain("c2")
        assert "c1" in chain
        assert "c2" in chain


# === Derivation Tests ===

class TestDerivationDAG:
    def test_add_step_and_verify(self):
        dag = DerivationDAG(
            root_claim_id="result",
            assumptions=["premise_a", "premise_b"],
        )
        step1 = DerivationStep(
            id="s1", rule="modus_ponens",
            inputs=["premise_a", "premise_b"],
            output="intermediate",
            justification="If A and A->B then B",
        )
        dag.add_step(step1)
        assert dag.verify_chain()

    def test_invalid_input_raises(self):
        dag = DerivationDAG(root_claim_id="r", assumptions=["a"])
        step = DerivationStep(
            id="s1", rule="r1", inputs=["nonexistent"],
            output="out", justification="test"
        )
        try:
            dag.add_step(step)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_to_dict_and_from_dict(self):
        dag = DerivationDAG(root_claim_id="r", assumptions=["a", "b"])
        step = DerivationStep(id="s1", rule="r1", inputs=["a", "b"],
                              output="c", justification="combine")
        dag.add_step(step)
        data = dag.to_dict()
        restored = DerivationDAG.from_dict(data)
        assert restored.root_claim_id == "r"
        assert "s1" in restored.steps
        assert restored.steps["s1"].output == "c"

    def test_replay_dry(self):
        dag = DerivationDAG(root_claim_id="r", assumptions=["x", "y"])
        step = DerivationStep(id="s1", rule="add", inputs=["x", "y"],
                              output="z", justification="x+y=z")
        dag.add_step(step)
        results = dag.replay()
        assert results["s1"] == "z"

    def test_replay_with_registry(self):
        dag = DerivationDAG(root_claim_id="r", assumptions=["3", "4"])
        step = DerivationStep(id="s1", rule="concat", inputs=["3", "4"],
                              output="placeholder", justification="concat")
        dag.add_step(step)
        registry = {"concat": lambda a, b: a + b}
        results = dag.replay(rule_registry=registry)
        assert results["s1"] == "34"


# === Provenance Tests ===

class TestProvenanceStore:
    def test_add_and_query(self):
        store = ProvenanceStore()
        record = EvidenceRecord(
            evidence_id="e1", claim_id="c1",
            source_uri="https://example.com/data",
            source_hash="abc123", source_tier=SourceTier.T1_AUTHORITATIVE,
            extraction_method="manual", confidence=0.95,
        )
        store.add(record)
        results = store.query_for_claim("c1")
        assert len(results) == 1
        assert results[0].evidence_id == "e1"

    def test_get_by_source(self):
        store = ProvenanceStore()
        r1 = EvidenceRecord(
            evidence_id="e1", claim_id="c1",
            source_uri="src_a", source_hash="h1",
            source_tier=SourceTier.T2_SECONDARY,
            extraction_method="auto", confidence=0.7,
        )
        r2 = EvidenceRecord(
            evidence_id="e2", claim_id="c2",
            source_uri="src_a", source_hash="h2",
            source_tier=SourceTier.T2_SECONDARY,
            extraction_method="auto", confidence=0.6,
        )
        store.add(r1)
        store.add(r2)
        results = store.get_by_source("src_a")
        assert len(results) == 2

    def test_verify_integrity_clean(self):
        store = ProvenanceStore()
        record = EvidenceRecord(
            evidence_id="e1", claim_id="c1",
            source_uri="src", source_hash="h",
            source_tier=SourceTier.T0_VERIFIED,
            extraction_method="verified", confidence=1.0,
        )
        store.add(record)
        issues = store.verify_integrity()
        assert len(issues) == 0

    def test_duplicate_raises(self):
        store = ProvenanceStore()
        record = EvidenceRecord(
            evidence_id="e1", claim_id="c1",
            source_uri="src", source_hash="h",
            source_tier=SourceTier.T3_USER,
            extraction_method="input", confidence=0.5,
        )
        store.add(record)
        try:
            store.add(record)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# === Reality Ledger Tests ===

class TestRealityLedger:
    def test_assert_and_query(self):
        ledger = RealityLedger()
        ledger.assert_fact("claim_1", "Earth is round", source="textbook")
        result = ledger.get_current("claim_1")
        assert result == "Earth is round"

    def test_retract(self):
        ledger = RealityLedger()
        ledger.assert_fact("c1", "value", source="src")
        ledger.retract("c1", source="correction")
        assert ledger.get_current("c1") is None

    def test_correct(self):
        ledger = RealityLedger()
        ledger.assert_fact("c1", "old_value", source="src")
        ledger.correct("c1", "new_value", source="update")
        assert ledger.get_current("c1") == "new_value"

    def test_history(self):
        ledger = RealityLedger()
        ledger.assert_fact("c1", "v1", source="s1")
        ledger.correct("c1", "v2", source="s2")
        history = ledger.history("c1")
        assert len(history) == 2
        assert history[0].event_type == EventType.ASSERT
        assert history[1].event_type == EventType.CORRECT

    def test_rebuild_from_events(self):
        ledger = RealityLedger()
        ledger.assert_fact("c1", "v1", source="s1")
        ledger.correct("c1", "v2", source="s2")
        ledger.assert_fact("c2", "x", source="s1")
        events = ledger.events

        new_ledger = RealityLedger()
        new_ledger.rebuild_from_events(events)
        assert new_ledger.get_current("c1") == "v2"
        assert new_ledger.get_current("c2") == "x"

    def test_bitemporal_query(self):
        ledger = RealityLedger()
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=30)
        future = now + timedelta(days=30)
        ledger.assert_fact("c1", "historical", source="s",
                           valid_time=(past, now))
        ledger.assert_fact("c1", "current", source="s",
                           valid_time=(now, future))
        # Query as of a past valid time
        result = ledger.query_as_of("c1", valid_time=past + timedelta(days=1))
        assert result == "historical"


# === Contradiction Tests ===

class TestContradictionCourt:
    def test_file_and_resolve(self):
        court = ContradictionCourt()
        case = court.file_case("claim_a", "claim_b")
        assert case.resolution == Resolution.PENDING
        assert len(court.get_pending()) == 1

        court.resolve(case.id, Resolution.A_WINS, reasoning="Higher tier source")
        assert case.resolution == Resolution.A_WINS
        assert len(court.get_pending()) == 0

    def test_present_evidence(self):
        court = ContradictionCourt()
        case = court.file_case("ca", "cb")
        court.present_evidence(case.id, "ev1", "ca")
        court.present_evidence(case.id, "ev2", "cb")
        assert "ev1" in case.evidence_for_a
        assert "ev2" in case.evidence_for_b

    def test_invalid_evidence_target(self):
        court = ContradictionCourt()
        case = court.file_case("ca", "cb")
        try:
            court.present_evidence(case.id, "ev1", "wrong_claim")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# === Run all tests ===

def run_tests():
    """Simple test runner."""
    test_classes = [
        TestClaimGraph,
        TestDerivationDAG,
        TestProvenanceStore,
        TestRealityLedger,
        TestContradictionCourt,
    ]
    total = 0
    passed = 0
    failed = 0
    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            total += 1
            try:
                getattr(instance, method_name)()
                passed += 1
                print(f"  PASS: {cls.__name__}.{method_name}")
            except Exception as e:
                failed += 1
                print(f"  FAIL: {cls.__name__}.{method_name} — {e}")
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
