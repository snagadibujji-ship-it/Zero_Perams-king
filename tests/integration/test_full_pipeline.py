"""Integration tests for the full AXIMA pipeline.

Tests that Axima.query() actually processes queries end-to-end,
returning correct answers with proper metadata, traces, and truth levels.
"""

from __future__ import annotations

import pytest

from axima.api import Axima, AximaResponse
from axima.contracts.query import AximaResponseV2, TruthLevel
from axima.errors import AximaError


@pytest.fixture
def ax():
    """Create a fresh Axima instance for each test."""
    return Axima()


# --- Basic Arithmetic ---


class TestArithmetic:
    """Test basic arithmetic through the full pipeline."""

    def test_addition(self, ax: Axima):
        """2 + 2 returns '4'."""
        result = ax.query("2 + 2")
        assert result.answer == "4"
        assert result.truth_level == TruthLevel.DERIVED
        assert "math" in result.engine

    def test_multiplication(self, ax: Axima):
        """15 * 7 returns '105'."""
        result = ax.query("15 * 7")
        assert result.answer == "105"

    def test_complex_arithmetic(self, ax: Axima):
        """100 / 4 + 25 returns '50'."""
        result = ax.query("100 / 4 + 25")
        assert result.answer == "50"

    def test_exponentiation(self, ax: Axima):
        """2^10 returns '1024'."""
        result = ax.query("2^10")
        assert result.answer == "1024"

    def test_subtraction(self, ax: Axima):
        """50 - 23 returns '27'."""
        result = ax.query("50 - 23")
        assert result.answer == "27"

    def test_sqrt(self, ax: Axima):
        """sqrt(144) returns '12'."""
        result = ax.query("sqrt(144)")
        assert result.answer == "12"

    def test_factorial(self, ax: Axima):
        """factorial(5) returns '120'."""
        result = ax.query("factorial(5)")
        assert result.answer == "120"

    def test_what_is_prefix(self, ax: Axima):
        """'what is 2+2' still computes correctly."""
        result = ax.query("what is 2 + 2")
        assert result.answer == "4"

    def test_calculate_prefix(self, ax: Axima):
        """'calculate 15 * 7 + 3' works."""
        result = ax.query("calculate 15 * 7 + 3")
        assert result.answer == "108"


# --- Algebra ---


class TestAlgebra:
    """Test algebraic equation solving."""

    def test_quadratic_basic(self, ax: Axima):
        """solve x^2 - 4 = 0 returns x = ±2."""
        result = ax.query("solve x^2 - 4 = 0")
        assert "2" in result.answer
        assert "math" in result.engine

    def test_linear_equation(self, ax: Axima):
        """solve 2x + 6 = 0 returns x = -3."""
        result = ax.query("solve 2x + 6 = 0")
        assert "-3" in result.answer

    def test_quadratic_full(self, ax: Axima):
        """solve x^2 + 3x - 4 = 0 should find roots."""
        result = ax.query("solve x^2 + 3x - 4 = 0")
        assert result.status == "success" if hasattr(result, 'status') else result.answer != ""
        # Should find x = 1 or x = -4
        assert "1" in result.answer or "-4" in result.answer


# --- Knowledge / Facts ---


class TestKnowledge:
    """Test factual knowledge retrieval."""

    def test_capital_of_france(self, ax: Axima):
        """what is the capital of France → Paris."""
        result = ax.query("what is the capital of France?")
        assert "Paris" in result.answer
        assert result.truth_level == TruthLevel.DIRECT_FACT

    def test_capital_of_japan(self, ax: Axima):
        """what is the capital of Japan → Tokyo."""
        result = ax.query("what is the capital of Japan?")
        assert "Tokyo" in result.answer

    def test_speed_of_light(self, ax: Axima):
        """Speed of light returns a factual answer."""
        result = ax.query("what is the speed of light?")
        assert "299" in result.answer or "light" in result.answer.lower()
        assert result.truth_level == TruthLevel.DIRECT_FACT

    def test_boiling_point(self, ax: Axima):
        """Boiling point of water."""
        result = ax.query("what is the boiling point of water?")
        assert "100" in result.answer
        assert "knowledge" in result.engine


# --- Intent Detection & Routing ---


class TestRouting:
    """Test that queries are routed to the correct engine."""

    def test_math_routing(self, ax: Axima):
        """Math queries route to math engine."""
        result = ax.query("solve x^2 - 4 = 0")
        assert "math" in result.engine

    def test_code_intent_detected(self, ax: Axima):
        """Code queries detect code intent."""
        result = ax.query("write a hello world in python")
        trace = ax.get_last_trace()
        intent_events = [e for e in trace["events"] if e["stage"] == "intent"]
        assert intent_events
        assert intent_events[0]["data"]["intent"] == "code"

    def test_knowledge_routing(self, ax: Axima):
        """Knowledge queries route to knowledge engine."""
        result = ax.query("what is the capital of France?")
        assert "knowledge" in result.engine

    def test_arithmetic_routing(self, ax: Axima):
        """Pure arithmetic routes to safe_eval."""
        result = ax.query("2 + 2")
        assert "math" in result.engine


# --- Trace Collection ---


class TestTracing:
    """Test that traces are collected for every query."""

    def test_trace_collected(self, ax: Axima):
        """Every query produces a trace."""
        ax.query("2 + 2")
        traces = ax.get_traces()
        assert len(traces) == 1
        trace = traces[0]
        assert "events" in trace
        assert trace["event_count"] > 0

    def test_trace_has_stages(self, ax: Axima):
        """Trace includes input, validate, intent, execute, respond stages."""
        ax.query("hello world")
        trace = ax.get_last_trace()
        stages = [e["stage"] for e in trace["events"]]
        assert "input" in stages
        assert "validate" in stages or "shield" in stages
        assert "intent" in stages
        assert "respond" in stages

    def test_trace_has_timing(self, ax: Axima):
        """Trace includes total duration."""
        ax.query("2 + 2")
        trace = ax.get_last_trace()
        assert "total_duration_ms" in trace
        assert trace["total_duration_ms"] > 0

    def test_multiple_queries_collect_traces(self, ax: Axima):
        """Multiple queries accumulate traces."""
        ax.query("2 + 2")
        ax.query("3 * 3")
        ax.query("what is pi?")
        traces = ax.get_traces()
        assert len(traces) == 3


# --- Error Handling ---


class TestErrorHandling:
    """Test that errors are structured, never bare exceptions."""

    def test_empty_input(self, ax: Axima):
        """Empty input returns structured error, not exception."""
        result = ax.query("")
        assert isinstance(result, AximaResponseV2)
        assert result.truth_level == TruthLevel.UNSUPPORTED
        assert result.caveats  # Should have error info

    def test_whitespace_only(self, ax: Axima):
        """Whitespace-only input returns structured error."""
        result = ax.query("   ")
        assert isinstance(result, AximaResponseV2)
        assert result.truth_level == TruthLevel.UNSUPPORTED

    def test_very_long_input(self, ax: Axima):
        """Very long input is handled gracefully."""
        long_text = "a " * 6000  # 12000 chars, exceeds limit
        result = ax.query(long_text)
        assert isinstance(result, AximaResponseV2)
        # Should either work (truncated) or return structured error
        assert result.truth_level in (TruthLevel.UNSUPPORTED, TruthLevel.HEURISTIC)

    def test_response_type(self, ax: Axima):
        """All responses are AximaResponseV2 instances."""
        result = ax.query("2 + 2")
        assert isinstance(result, AximaResponseV2)
        assert hasattr(result, "answer")
        assert hasattr(result, "truth_level")
        assert hasattr(result, "engine")
        assert hasattr(result, "trace_id")
        assert hasattr(result, "latency_ms")


# --- Response Metadata ---


class TestResponseMetadata:
    """Test that responses carry proper metadata."""

    def test_truth_level_set(self, ax: Axima):
        """Responses always have a truth level."""
        result = ax.query("2 + 2")
        assert result.truth_level is not None
        assert isinstance(result.truth_level, TruthLevel)

    def test_engine_set(self, ax: Axima):
        """Responses always name their engine."""
        result = ax.query("2 + 2")
        assert result.engine != ""
        assert result.engine != "unknown"

    def test_trace_id_set(self, ax: Axima):
        """Responses always carry a trace ID."""
        result = ax.query("hello")
        assert result.trace_id != ""

    def test_latency_recorded(self, ax: Axima):
        """Responses record latency."""
        result = ax.query("2 + 2")
        assert result.latency_ms > 0

    def test_confidence_range(self, ax: Axima):
        """Confidence is in [0, 1]."""
        result = ax.query("what is the capital of France?")
        assert 0.0 <= result.calibrated_confidence <= 1.0

    def test_claims_populated(self, ax: Axima):
        """Successful math queries have claims."""
        result = ax.query("2 + 2")
        assert result.claims  # Should have at least one claim


# --- Legacy Compatibility ---


class TestLegacyCompat:
    """Test that the legacy .process() API still works."""

    def test_process_returns_axima_response(self, ax: Axima):
        """process() returns old-style AximaResponse."""
        result = ax.process("2 + 2")
        assert isinstance(result, AximaResponse)
        assert result.answer == "4"

    def test_process_has_confidence(self, ax: Axima):
        """process() carries confidence info."""
        result = ax.process("what is the capital of France?")
        assert result.confidence != ""
        assert "Paris" in result.answer


# --- Plugin System ---


class TestPluginSystem:
    """Test that the plugin system works."""

    def test_plugins_loaded(self, ax: Axima):
        """At least math plugin should be loaded."""
        ax._ensure_init()
        assert "math_solver" in ax._plugins

    def test_math_plugin_solves(self, ax: Axima):
        """Math plugin solves equations."""
        result = ax.query("solve x^2 - 9 = 0")
        assert "3" in result.answer

    def test_plugins_listed(self, ax: Axima):
        """plugins_loaded property lists available plugins."""
        plugins = ax.plugins_loaded
        assert isinstance(plugins, list)
        assert "math_solver" in plugins
