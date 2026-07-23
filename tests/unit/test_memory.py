"""Tests for the AXIMA memory subsystem."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from datetime import datetime, timedelta, timezone

from axima.memory.four_plane import (
    FourPlaneMemory, WorkingMemory, EpisodicMemory,
    SemanticMemory, ProceduralMemory, MemoryEntry,
    RetentionPolicy, SensitivityLabel,
)
from axima.memory.recall import RecallRequest, RecallResult, MemoryRecaller


class TestWorkingMemory:
    def test_set_and_clear_goal(self):
        wm = WorkingMemory()
        wm.set_goal("solve equation")
        assert "solve equation" in wm.goals
        wm.clear_goal("solve equation")
        assert "solve equation" not in wm.goals

    def test_set_context(self):
        wm = WorkingMemory()
        wm.set_context("user_query", "what is 2+2?")
        assert wm.context["user_query"] == "what is 2+2?"

    def test_clear(self):
        wm = WorkingMemory()
        wm.set_goal("g1")
        wm.set_context("k", "v")
        wm.clear()
        assert len(wm.goals) == 0
        assert len(wm.context) == 0


class TestEpisodicMemory:
    def test_append_and_count(self):
        em = EpisodicMemory()
        entry = MemoryEntry(
            id="ep1", content="user asked about gravity",
            schema="interaction", source="cli",
            retention_policy=RetentionPolicy.LONG_TERM,
            sensitivity_label=SensitivityLabel.INTERNAL,
        )
        em.append(entry)
        assert em.count == 1

    def test_get_recent(self):
        em = EpisodicMemory()
        for i in range(20):
            em.append(MemoryEntry(
                id=f"ep{i}", content=f"event {i}",
                schema="event", source="test",
                retention_policy=RetentionPolicy.SESSION,
                sensitivity_label=SensitivityLabel.PUBLIC,
            ))
        recent = em.get_recent(5)
        assert len(recent) == 5
        assert recent[0].id == "ep15"

    def test_search(self):
        em = EpisodicMemory()
        em.append(MemoryEntry(
            id="ep1", content="discussed quantum physics",
            schema="interaction", source="cli",
            retention_policy=RetentionPolicy.LONG_TERM,
            sensitivity_label=SensitivityLabel.INTERNAL,
        ))
        em.append(MemoryEntry(
            id="ep2", content="solved algebra problem",
            schema="interaction", source="cli",
            retention_policy=RetentionPolicy.LONG_TERM,
            sensitivity_label=SensitivityLabel.INTERNAL,
        ))
        results = em.search("quantum")
        assert len(results) == 1
        assert results[0].id == "ep1"


class TestSemanticMemory:
    def test_store_and_get(self):
        sm = SemanticMemory()
        entry = MemoryEntry(
            id="sm1", content={"fact": "water freezes at 0C"},
            schema="fact", source="knowledge_base",
            retention_policy=RetentionPolicy.PERMANENT,
            sensitivity_label=SensitivityLabel.PUBLIC,
        )
        sm.store(entry)
        assert sm.get("sm1") is not None
        assert sm.count == 1

    def test_remove(self):
        sm = SemanticMemory()
        entry = MemoryEntry(
            id="sm1", content="test",
            schema="fact", source="test",
            retention_policy=RetentionPolicy.LONG_TERM,
            sensitivity_label=SensitivityLabel.INTERNAL,
        )
        sm.store(entry)
        assert sm.remove("sm1")
        assert sm.get("sm1") is None


class TestProceduralMemory:
    def test_store_and_get_by_tag(self):
        pm = ProceduralMemory()
        entry = MemoryEntry(
            id="pm1", content={"skill": "solve_quadratic", "steps": ["..."]},
            schema="skill", source="verified",
            retention_policy=RetentionPolicy.PERMANENT,
            sensitivity_label=SensitivityLabel.INTERNAL,
            tags=["math", "algebra"],
        )
        pm.store(entry)
        results = pm.get_by_tag("math")
        assert len(results) == 1
        assert results[0].id == "pm1"


class TestFourPlaneMemory:
    def test_remember_and_recall(self):
        mem = FourPlaneMemory()
        mem.remember(
            plane="semantic",
            content="Python is a programming language",
            schema="fact",
            source="knowledge_base",
        )
        results = mem.recall("Python")
        assert len(results) >= 1

    def test_remember_episodic(self):
        mem = FourPlaneMemory()
        entry = mem.remember(
            plane="episodic",
            content="User asked about sorting algorithms",
            schema="interaction",
            source="session_1",
            retention_policy=RetentionPolicy.SESSION,
            sensitivity_label=SensitivityLabel.INTERNAL,
        )
        assert entry.id is not None
        assert mem.episodic.count == 1

    def test_forget(self):
        mem = FourPlaneMemory()
        entry = mem.remember(
            plane="semantic",
            content="temporary fact",
            schema="fact",
            source="test",
        )
        assert mem.forget(entry.id)
        results = mem.recall("temporary")
        assert len(results) == 0

    def test_export_and_import(self):
        mem = FourPlaneMemory()
        mem.remember(
            plane="semantic",
            content="Earth orbits the Sun",
            schema="fact",
            source="astronomy",
        )
        mem.remember(
            plane="episodic",
            content="User session started",
            schema="event",
            source="system",
        )
        exported = mem.export()

        new_mem = FourPlaneMemory()
        new_mem.import_from(exported)
        assert new_mem.semantic.count == 1
        assert new_mem.episodic.count == 1

    def test_verify_integrity_clean(self):
        mem = FourPlaneMemory()
        mem.remember(plane="semantic", content="test",
                     schema="s", source="t")
        issues = mem.verify_integrity()
        assert len(issues) == 0

    def test_working_memory_integration(self):
        mem = FourPlaneMemory()
        mem.working.set_goal("answer user question")
        mem.working.set_context("domain", "physics")
        assert "answer user question" in mem.working.goals
        assert mem.working.context["domain"] == "physics"


class TestMemoryRecaller:
    def test_recall_with_relevance(self):
        mem = FourPlaneMemory()
        mem.remember(plane="semantic", content="quantum mechanics principles",
                     schema="concept", source="physics_kb")
        mem.remember(plane="semantic", content="classical mechanics newton",
                     schema="concept", source="physics_kb")
        mem.remember(plane="semantic", content="organic chemistry reactions",
                     schema="concept", source="chemistry_kb")

        recaller = MemoryRecaller(mem)
        request = RecallRequest(query="quantum mechanics", max_results=5)
        result = recaller.recall(request)
        assert len(result.items) >= 1
        # Quantum mechanics entry should have highest relevance
        assert "quantum" in str(result.items[0].content).lower()
        assert result.relevance_scores[0] > 0

    def test_recall_respects_max_results(self):
        mem = FourPlaneMemory()
        for i in range(20):
            mem.remember(plane="semantic", content=f"fact number {i} about science",
                         schema="fact", source="test")

        recaller = MemoryRecaller(mem)
        request = RecallRequest(query="science", max_results=5)
        result = recaller.recall(request)
        assert len(result.items) <= 5

    def test_recall_min_relevance_filter(self):
        mem = FourPlaneMemory()
        mem.remember(plane="semantic", content="exact match query test",
                     schema="fact", source="test")
        mem.remember(plane="semantic", content="completely unrelated xyz abc",
                     schema="fact", source="test")

        recaller = MemoryRecaller(mem)
        request = RecallRequest(query="exact match query test",
                                min_relevance=0.5, max_results=10)
        result = recaller.recall(request)
        # Only the matching entry should pass the relevance threshold
        for score in result.relevance_scores:
            assert score >= 0.5

    def test_staleness_computed(self):
        mem = FourPlaneMemory()
        mem.remember(plane="semantic", content="recent fact about physics",
                     schema="fact", source="test")

        recaller = MemoryRecaller(mem)
        request = RecallRequest(query="physics")
        result = recaller.recall(request)
        if result.items:
            # Just created, should be fresh (low staleness)
            assert result.staleness[0] < 0.1


# === Run all tests ===

def run_tests():
    """Simple test runner."""
    test_classes = [
        TestWorkingMemory,
        TestEpisodicMemory,
        TestSemanticMemory,
        TestProceduralMemory,
        TestFourPlaneMemory,
        TestMemoryRecaller,
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
