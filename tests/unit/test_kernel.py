"""
Unit Tests for AXIMA Kernel
============================

Tests for:
- Feature flag modes (legacy, shadow, canary, cosmic)
- Trace collection
- Budget enforcement
- Registry operations
- Event ledger CRUD
"""

import os
import sys
import tempfile
import threading
import time
import unittest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from axima.contracts.query import (
    AximaResponseV2,
    ExecutionResult,
    QueryEnvelope,
    ResourceBudgetSpec,
    TruthLevel,
)
from axima.kernel.trace import QueryTrace, TraceEvent
from axima.kernel.scheduler import CognitiveScheduler, ResourceBudget, TaskStatus
from axima.kernel.registry import CapabilityDescriptor, CapabilityRegistry, HealthStatus
from axima.kernel.event_ledger import EventLedger, LedgerEntry


class TestTruthLevel(unittest.TestCase):
    """Test TruthLevel enum."""

    def test_all_values_exist(self):
        self.assertEqual(TruthLevel.DIRECT_FACT.value, "direct_fact")
        self.assertEqual(TruthLevel.DERIVED.value, "derived")
        self.assertEqual(TruthLevel.HEURISTIC.value, "heuristic")
        self.assertEqual(TruthLevel.TEMPLATE.value, "template")
        self.assertEqual(TruthLevel.UNSUPPORTED.value, "unsupported")

    def test_enum_count(self):
        self.assertEqual(len(TruthLevel), 5)


class TestQueryEnvelope(unittest.TestCase):
    """Test QueryEnvelope dataclass."""

    def test_creation_defaults(self):
        env = QueryEnvelope(raw_input="hello world")
        self.assertEqual(env.raw_input, "hello world")
        self.assertEqual(env.normalized_input, "hello world")
        self.assertIsNotNone(env.query_id)
        self.assertEqual(env.language_candidates, ["en"])
        self.assertEqual(env.requested_mode, "deep")
        self.assertIsNotNone(env.deadline)

    def test_deadline_computed(self):
        env = QueryEnvelope(
            raw_input="test",
            resource_budget=ResourceBudgetSpec(max_time_ms=2000.0),
        )
        expected_deadline = env.created_at + 2.0
        self.assertAlmostEqual(env.deadline, expected_deadline, places=2)


class TestAximaResponseV2(unittest.TestCase):
    """Test AximaResponseV2 dataclass."""

    def test_meaning_hash_generated(self):
        resp = AximaResponseV2(answer="x = 2")
        self.assertTrue(len(resp.meaning_hash) > 0)

    def test_trace_id_generated(self):
        resp = AximaResponseV2(answer="test")
        self.assertTrue(len(resp.trace_id) > 0)

    def test_defaults(self):
        resp = AximaResponseV2(answer="hello")
        self.assertEqual(resp.truth_level, TruthLevel.UNSUPPORTED)
        self.assertEqual(resp.calibrated_confidence, 0.0)
        self.assertEqual(resp.language, "en")
        self.assertEqual(resp.mode, "deep")


class TestExecutionResult(unittest.TestCase):
    """Test ExecutionResult dataclass."""

    def test_success_result(self):
        r = ExecutionResult(answer="42", status="success", engine="math")
        self.assertEqual(r.answer, "42")
        self.assertEqual(r.status, "success")
        self.assertIsNone(r.error)

    def test_error_result(self):
        r = ExecutionResult(status="error", error="Something broke", engine="test")
        self.assertIsNone(r.answer)
        self.assertEqual(r.error, "Something broke")


class TestQueryTrace(unittest.TestCase):
    """Test trace collection."""

    def test_add_event(self):
        trace = QueryTrace(query_id="q-1")
        trace.add_event("input", {"raw": "hello"})
        self.assertEqual(len(trace.events), 1)
        self.assertEqual(trace.events[0].stage, "input")
        self.assertEqual(trace.events[0].data, {"raw": "hello"})

    def test_multiple_events(self):
        trace = QueryTrace(query_id="q-2")
        trace.add_event("input", {"raw": "test"})
        trace.add_event("route", {"target": "math"})
        trace.add_event("execute", {"engine": "math"})
        trace.add_event("respond", {"answer": "42"})
        self.assertEqual(len(trace.events), 4)

    def test_timed_context(self):
        trace = QueryTrace(query_id="q-3")
        with trace.timed("execute", {"engine": "test"}):
            time.sleep(0.01)
        self.assertEqual(len(trace.events), 1)
        self.assertGreater(trace.events[0].duration_ms, 5.0)

    def test_to_dict(self):
        trace = QueryTrace(query_id="q-4")
        trace.add_event("input", {"raw": "x"})
        d = trace.to_dict()
        self.assertEqual(d["query_id"], "q-4")
        self.assertEqual(d["event_count"], 1)
        self.assertIn("events", d)
        self.assertIn("total_duration_ms", d)

    def test_summary(self):
        trace = QueryTrace(query_id="q-5")
        trace.add_event("input", {})
        trace.add_event("execute", {"engine": "math"})
        trace.add_event("error", {"msg": "fail"})
        s = trace.summary()
        self.assertEqual(s["error_count"], 1)
        self.assertEqual(s["engines_used"], ["math"])
        self.assertEqual(s["stages"], ["input", "execute", "error"])

    def test_total_duration(self):
        trace = QueryTrace(query_id="q-6")
        time.sleep(0.01)
        self.assertGreater(trace.total_duration_ms(), 5.0)


class TestCognitiveScheduler(unittest.TestCase):
    """Test budget enforcement and scheduling."""

    def test_schedule_and_complete(self):
        scheduler = CognitiveScheduler()
        budget = ResourceBudget(max_time_ms=2000)

        def work(cancel):
            return "done"

        task_id = scheduler.schedule("t-1", budget, work)
        result = scheduler.get_result(task_id, timeout_ms=1000)
        self.assertEqual(result, "done")

    def test_timeout_enforcement(self):
        scheduler = CognitiveScheduler()
        budget = ResourceBudget(max_time_ms=50)

        def slow_work(cancel):
            # Check cancellation in a loop
            for _ in range(100):
                if cancel.is_set():
                    raise RuntimeError("Cancelled")
                time.sleep(0.01)
            return "should not reach"

        task_id = scheduler.schedule("t-2", budget, slow_work)
        time.sleep(0.15)
        status = scheduler.get_status(task_id)
        self.assertIn(status["status"], ["timeout", "budget_exceeded", "cancelled"])

    def test_cancellation(self):
        scheduler = CognitiveScheduler()
        budget = ResourceBudget(max_time_ms=5000)

        started = threading.Event()

        def cancellable_work(cancel):
            started.set()
            while not cancel.is_set():
                time.sleep(0.01)
            raise RuntimeError("Cancelled")

        task_id = scheduler.schedule("t-3", budget, cancellable_work)
        started.wait(timeout=1.0)
        cancelled = scheduler.cancel(task_id)
        self.assertTrue(cancelled)
        time.sleep(0.05)
        status = scheduler.get_status(task_id)
        self.assertEqual(status["status"], "cancelled")

    def test_get_status_unknown(self):
        scheduler = CognitiveScheduler()
        self.assertIsNone(scheduler.get_status("nonexistent"))

    def test_step_budget(self):
        scheduler = CognitiveScheduler()
        budget = ResourceBudget(max_time_ms=5000, max_steps=3)

        def step_work(cancel):
            for i in range(10):
                if cancel.is_set():
                    return f"stopped at {i}"
                time.sleep(0.01)
            return "completed"

        task_id = scheduler.schedule("t-4", budget, step_work)
        time.sleep(0.02)
        # Exceed step budget
        scheduler.increment_steps(task_id)
        scheduler.increment_steps(task_id)
        scheduler.increment_steps(task_id)
        ok = scheduler.increment_steps(task_id)  # Should exceed
        self.assertFalse(ok)

    def test_shutdown(self):
        scheduler = CognitiveScheduler()
        budget = ResourceBudget(max_time_ms=5000)

        def long_work(cancel):
            while not cancel.is_set():
                time.sleep(0.01)
            return "shutdown"

        scheduler.schedule("t-5", budget, long_work)
        time.sleep(0.02)
        scheduler.shutdown()
        time.sleep(0.05)
        status = scheduler.get_status("t-5")
        self.assertEqual(status["status"], "cancelled")


class TestCapabilityRegistry(unittest.TestCase):
    """Test registry operations."""

    def test_register_and_query(self):
        reg = CapabilityRegistry()
        cap = CapabilityDescriptor(
            name="math_solver",
            version="2.0.0",
            accepted_types=["math", "calculate"],
            produced_types=["answer"],
            handler=lambda q: "42",
        )
        reg.register(cap)
        self.assertEqual(reg.count, 1)

        results = reg.query(accepted_type="math")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "math_solver")

    def test_unregister(self):
        reg = CapabilityRegistry()
        cap = CapabilityDescriptor(name="test_cap", handler=lambda q: None)
        reg.register(cap)
        self.assertEqual(reg.count, 1)

        removed = reg.unregister("test_cap")
        self.assertTrue(removed)
        self.assertEqual(reg.count, 0)

        removed_again = reg.unregister("test_cap")
        self.assertFalse(removed_again)

    def test_query_by_produced_type(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityDescriptor(
            name="a", produced_types=["answer", "explanation"],
        ))
        reg.register(CapabilityDescriptor(
            name="b", produced_types=["code"],
        ))

        results = reg.query(produced_type="code")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "b")

    def test_get_best_for(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityDescriptor(
            name="fast_math",
            accepted_types=["math"],
            latency_model={"avg_ms": 10},
            health=HealthStatus.HEALTHY,
            deterministic=True,
            handler=lambda q: "fast",
        ))
        reg.register(CapabilityDescriptor(
            name="slow_math",
            accepted_types=["math"],
            latency_model={"avg_ms": 500},
            health=HealthStatus.HEALTHY,
            handler=lambda q: "slow",
        ))

        best = reg.get_best_for("math")
        self.assertEqual(best.name, "fast_math")

    def test_get_best_for_no_match(self):
        reg = CapabilityRegistry()
        best = reg.get_best_for("nonexistent")
        self.assertIsNone(best)

    def test_health_check_all(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityDescriptor(
            name="healthy_cap",
            handler=lambda q: None,
        ))
        reg.register(CapabilityDescriptor(
            name="check_cap",
            handler=lambda q: None,
            health_check_fn=lambda: HealthStatus.DEGRADED,
        ))

        results = reg.health_check_all()
        self.assertEqual(results["healthy_cap"], HealthStatus.HEALTHY)
        self.assertEqual(results["check_cap"], HealthStatus.DEGRADED)

    def test_list_all(self):
        reg = CapabilityRegistry()
        reg.register(CapabilityDescriptor(name="a", version="1.0.0"))
        reg.register(CapabilityDescriptor(name="b", version="2.0.0"))

        listed = reg.list_all()
        self.assertEqual(len(listed), 2)
        names = {item["name"] for item in listed}
        self.assertEqual(names, {"a", "b"})

    def test_auto_discover_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reg = CapabilityRegistry(plugins_dir=tmpdir)
            count = reg.auto_discover()
            self.assertEqual(count, 0)

    def test_auto_discover_with_plugin(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a plugin file
            plugin_code = '''
def register_plugin(registry):
    from axima.kernel.registry import CapabilityDescriptor
    registry.register(CapabilityDescriptor(
        name="discovered_plugin",
        accepted_types=["test"],
    ))
'''
            plugin_path = os.path.join(tmpdir, "test_plugin.py")
            with open(plugin_path, "w") as f:
                f.write(plugin_code)

            reg = CapabilityRegistry(plugins_dir=tmpdir)
            count = reg.auto_discover()
            self.assertEqual(count, 1)
            self.assertEqual(reg.count, 1)


class TestEventLedger(unittest.TestCase):
    """Test event ledger CRUD."""

    def test_append_and_count(self):
        ledger = EventLedger()  # memory-only
        ledger.append("test_event", {"key": "value"})
        self.assertEqual(ledger.count, 1)

    def test_query_by_type(self):
        ledger = EventLedger()
        ledger.append("start", {"q": "hello"}, query_id="q1")
        ledger.append("complete", {"a": "world"}, query_id="q1")
        ledger.append("start", {"q": "bye"}, query_id="q2")

        results = ledger.query(event_type="start")
        self.assertEqual(len(results), 2)

    def test_query_by_query_id(self):
        ledger = EventLedger()
        ledger.append("a", {}, query_id="q1")
        ledger.append("b", {}, query_id="q2")
        ledger.append("c", {}, query_id="q1")

        results = ledger.query(query_id="q1")
        self.assertEqual(len(results), 2)

    def test_query_by_session_id(self):
        ledger = EventLedger()
        ledger.append("a", {}, session_id="s1")
        ledger.append("b", {}, session_id="s2")

        results = ledger.query(session_id="s1")
        self.assertEqual(len(results), 1)

    def test_query_with_limit(self):
        ledger = EventLedger()
        for i in range(10):
            ledger.append("event", {"i": i})

        results = ledger.query(limit=3)
        self.assertEqual(len(results), 3)

    def test_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            # Write events
            ledger1 = EventLedger(path=path)
            ledger1.append("e1", {"x": 1})
            ledger1.append("e2", {"x": 2})
            self.assertEqual(ledger1.count, 2)

            # Read back
            ledger2 = EventLedger(path=path)
            self.assertEqual(ledger2.count, 2)
            results = ledger2.query(event_type="e1")
            self.assertEqual(len(results), 1)
        finally:
            os.unlink(path)

    def test_export(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            export_path = f.name

        try:
            ledger = EventLedger()
            ledger.append("a", {"val": 1})
            ledger.append("b", {"val": 2})

            count = ledger.export(export_path)
            self.assertEqual(count, 2)

            # Verify export file
            with open(export_path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(len(lines), 2)
        finally:
            os.unlink(export_path)

    def test_replay(self):
        ledger = EventLedger()
        ledger.append("a", {"i": 1})
        ledger.append("b", {"i": 2})
        ledger.append("c", {"i": 3})

        replayed = list(ledger.replay())
        self.assertEqual(len(replayed), 3)
        self.assertEqual(replayed[0].event_type, "a")
        self.assertEqual(replayed[2].event_type, "c")

    def test_close_prevents_append(self):
        ledger = EventLedger()
        ledger.append("ok", {})
        ledger.close()

        with self.assertRaises(RuntimeError):
            ledger.append("fail", {})

    def test_clear(self):
        ledger = EventLedger()
        ledger.append("a", {})
        ledger.append("b", {})
        self.assertEqual(ledger.count, 2)
        ledger.clear()
        self.assertEqual(ledger.count, 0)


class TestCosmicMicrokernel(unittest.TestCase):
    """Test feature flag modes and kernel operations."""

    def _make_kernel(self, mode="legacy"):
        """Create a kernel in the specified mode without legacy adapter init."""
        from axima.kernel.runtime import CosmicMicrokernel
        # Use cosmic mode with a mock capability to avoid legacy import
        return CosmicMicrokernel(mode=mode)

    def test_mode_from_constructor(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")
        self.assertEqual(k.mode, "cosmic")

    def test_mode_from_env(self):
        from axima.kernel.runtime import CosmicMicrokernel
        os.environ["AXIMA_RUNTIME_MODE"] = "shadow"
        try:
            k = CosmicMicrokernel(mode=None)
            self.assertEqual(k.mode, "shadow")
        finally:
            del os.environ["AXIMA_RUNTIME_MODE"]

    def test_mode_invalid_falls_back(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="invalid_mode")
        self.assertEqual(k.mode, "legacy")

    def test_shutdown(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")
        self.assertFalse(k.is_shutdown)
        k.shutdown()
        self.assertTrue(k.is_shutdown)

    def test_process_query_after_shutdown(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")
        k.shutdown()
        resp = k.process_query("hello")
        self.assertEqual(resp.answer, "")
        self.assertIn("shutting down", resp.caveats[0].lower())

    def test_health_report(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")
        h = k.health()
        self.assertEqual(h["mode"], "cosmic")
        self.assertFalse(h["shutdown"])
        self.assertIn("query_count", h)

    def test_cosmic_mode_with_registered_capability(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")

        # Register a test capability
        cap = CapabilityDescriptor(
            name="test_math",
            accepted_types=["math"],
            health=HealthStatus.HEALTHY,
            handler=lambda q: "x = 42",
        )
        k.registry.register(cap)

        resp = k.process_query("solve x + 1 = 43")
        self.assertEqual(resp.answer, "x = 42")
        self.assertIn("test_math", resp.engine)

    def test_query_count_increments(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")

        # Register a dummy handler so it doesn't need legacy
        k.registry.register(CapabilityDescriptor(
            name="dummy",
            accepted_types=["general"],
            health=HealthStatus.HEALTHY,
            handler=lambda q: "ok",
        ))

        self.assertEqual(k.query_count, 0)
        k.process_query("test 1")
        k.process_query("test 2")
        self.assertEqual(k.query_count, 2)

    def test_ledger_records_events(self):
        from axima.kernel.runtime import CosmicMicrokernel
        k = CosmicMicrokernel(mode="cosmic")

        k.registry.register(CapabilityDescriptor(
            name="dummy",
            accepted_types=["general"],
            health=HealthStatus.HEALTHY,
            handler=lambda q: "ok",
        ))

        k.process_query("test query", session_id="sess-1")
        events = k.ledger.query(event_type="query_start")
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[-1].data["query"], "test query")


if __name__ == "__main__":
    unittest.main()
