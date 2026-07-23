"""
Integration Tests — End-to-End Flow
====================================

Tests the full query lifecycle:
  input -> parse -> route -> execute -> verify -> respond

Also tests:
- Trace generation across the stack
- Error handling and propagation
- Cross-module interactions
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from axima.language.parser import LanguageParser
from axima.language.realizer import NativeRealizer, LanguageProfile
from axima.language.register import Register, RegisterAdapter
from axima.cognition.teaching import AdaptiveTeacher, LearnerModel, ConceptNode
from axima.cognition.narrative import (
    NarrativeReactor,
    Character,
    WorldState,
    Tension,
    TensionType,
)
from axima.cognition.reasoning_tournament import ReasoningTournament, TournamentBudget
from axima.observability.traces import DistributedTrace, SpanKind, SpanContext
from axima.observability.metrics import MetricsCollector, MetricType
from axima.plugins.document.plugin import DocumentPlugin, DocumentFormat
from axima.plugins.multimodal.plugin import MultimodalPlugin
from axima.semantics.meaning_ir import MeaningIR, Predicate, Entity, Event, Quantity


# ===========================================================================
# Integration Test: Full Query Flow
# ===========================================================================


class TestFullQueryFlow:
    """Tests the complete input -> parse -> route -> execute -> verify -> respond pipeline."""

    def test_parse_route_execute_respond(self):
        """Full flow: parse input, route to realizer, produce output."""
        # 1. INPUT: raw text
        raw_input = "Water is a liquid. The temperature is 100 °C."

        # 2. PARSE: extract semantics
        parser = LanguageParser()
        ir = parser.parse_to_ir(raw_input, "en")

        assert ir.language == "en"
        assert len(ir.predicates) >= 1 or len(ir.quantities) >= 1

        # 3. ROUTE: decide engine (we route to realizer for reformulation)
        realizer = NativeRealizer()

        # 4. EXECUTE: realize in target language
        output = realizer.realize(ir, "en")

        # 5. VERIFY: output should contain key concepts from input
        assert "water" in output.lower() or "liquid" in output.lower()

        # 6. RESPOND: output is a valid string
        assert isinstance(output, str)
        assert len(output) > 0

    def test_multilingual_parse_realize(self):
        """Parse English, realize in different language profile."""
        parser = LanguageParser()
        realizer = NativeRealizer()

        # Parse English input
        ir = parser.parse_to_ir("The cat is a mammal", "en")

        # Realize in Spanish word order (SVO same as English for Spanish)
        output_es = realizer.realize(ir, "es")
        assert isinstance(output_es, str)
        assert len(output_es) > 0

        # Realize in German (SOV in subordinate clauses)
        output_de = realizer.realize(ir, "de")
        assert isinstance(output_de, str)
        assert len(output_de) > 0

    def test_parse_detect_realize_flow(self):
        """Detect language, parse, then realize."""
        parser = LanguageParser()
        realizer = NativeRealizer()

        text = "The quick brown fox jumps over the lazy dog"
        languages = parser.detect_language(text)
        assert languages[0][0] == "en"

        ir = parser.parse_to_ir(text, languages[0][0])
        output = realizer.realize(ir, "en")
        assert isinstance(output, str)

    def test_register_adaptation_in_flow(self):
        """Parse -> realize -> adapt register."""
        parser = LanguageParser()
        realizer = NativeRealizer()
        adapter = RegisterAdapter()

        ir = parser.parse_to_ir("Energy is conserved in a closed system", "en")
        neutral_output = realizer.realize(ir, "en", register="neutral")

        # Adapt to pedagogical
        pedagogical = adapter.adapt(neutral_output, Register.NEUTRAL, Register.PEDAGOGICAL)
        assert len(pedagogical) >= len(neutral_output)

    def test_teaching_flow_with_parsed_concepts(self):
        """Parse concepts, build teaching plan, check transfer."""
        teacher = AdaptiveTeacher()
        teacher.register_concepts([
            ConceptNode(
                name="photosynthesis",
                prerequisites=["light", "chlorophyll"],
                related=["energy"],
                explanations=["Plants convert light to chemical energy"],
                examples=["Leaves absorb sunlight"],
                transfer_tasks=["Explain why plants need light"],
                difficulty=2,
            ),
            ConceptNode(name="light", prerequisites=[], difficulty=1),
            ConceptNode(name="chlorophyll", prerequisites=[], difficulty=1),
        ])

        learner = LearnerModel(known_concepts={"light"})
        plan = teacher.plan_explanation("photosynthesis", learner)

        assert plan.target_concept == "photosynthesis"
        assert "light" in plan.bridge_from
        assert len(plan.prerequisite_chain) >= 1  # chlorophyll not known

        # Check transfer
        result = teacher.check_transfer(
            "photosynthesis",
            "Photosynthesis uses light and chlorophyll to create energy",
            learner,
        )
        assert result["confidence"] > 0

    def test_narrative_event_chain(self):
        """Generate a chain of events maintaining continuity."""
        reactor = NarrativeReactor()
        reactor.add_character(Character(
            name="Hero",
            drives=["save the village"],
            knowledge={"dragon threatens village"},
            constraints=["cannot fly"],
        ))
        reactor.add_fact("dragon threatens village")
        reactor.add_fact("Hero has a sword")

        # Event 1: Hero prepares
        ev1, err1 = reactor.generate_event(
            action="sharpens the sword",
            characters=["Hero"],
            preconditions=["Hero has a sword"],
            consequences=["sword is sharp"],
        )
        assert ev1.action == "sharpens the sword"

        # Event 2: Hero confronts (uses consequence of event 1)
        ev2, err2 = reactor.generate_event(
            action="confronts the dragon",
            characters=["Hero"],
            preconditions=["sword is sharp", "dragon threatens village"],
            consequences=["dragon is defeated", "village is safe"],
        )
        # Preconditions should be met (sword is sharp was established)
        fact_errors = [e for e in err2 if e.error_type == "unknown_fact"]
        assert len(fact_errors) == 0

        # Verify Hero learned from events
        hero = reactor.characters["Hero"]
        assert "village is safe" in hero.knowledge

    def test_tournament_with_parsed_claims(self):
        """Parse claims from text and run through tournament."""
        parser = LanguageParser()
        tournament = ReasoningTournament()

        # Parse text containing claims
        ir = parser.parse_to_ir("Water always flows downhill. All rivers reach the sea.", "en")

        # Extract claims from predicates
        claims_text = []
        for pred in ir.predicates:
            claims_text.append(f"{pred.subject} {pred.relation} {pred.object}")

        # If no predicates, use raw assertions
        if not claims_text:
            claims_text = ["Water always flows downhill", "All rivers reach the sea"]

        survivors = tournament.run_full_tournament(claims_text)
        # Some claims should survive (they have evidence gaps but aren't fatal)
        assert isinstance(survivors, list)


# ===========================================================================
# Integration Test: Trace Generation
# ===========================================================================


class TestTraceGeneration:
    """Tests that traces are properly generated across the full stack."""

    def test_trace_captures_all_stages(self):
        """Trace should capture INPUT, PARSE, ROUTE, EXECUTE, VERIFY, RESPOND."""
        trace = DistributedTrace(trace_id="test-trace-1")

        # INPUT stage
        root = trace.start_span(SpanKind.INPUT, attributes={"raw": "solve x=2"})

        # PARSE stage
        parse_span = trace.start_span(SpanKind.PARSE, parent_id=root.span_id)
        parser = LanguageParser()
        ir = parser.parse_to_ir("solve x=2", "en")
        parse_span.set_attribute("entities_found", len(ir.entities))
        parse_span.end()

        # ROUTE stage
        route_span = trace.start_span(SpanKind.ROUTE, parent_id=root.span_id)
        route_span.set_attribute("selected_engine", "math")
        route_span.end()

        # EXECUTE stage
        exec_span = trace.start_span(SpanKind.EXECUTE, parent_id=root.span_id)
        exec_span.set_attribute("engine", "math")
        time.sleep(0.001)  # Simulate work
        exec_span.end()

        # VERIFY stage
        verify_span = trace.start_span(SpanKind.VERIFY, parent_id=root.span_id)
        verify_span.set_attribute("verification_passed", True)
        verify_span.end()

        # RESPOND stage
        respond_span = trace.start_span(SpanKind.RESPOND, parent_id=root.span_id)
        respond_span.set_attribute("answer_length", 5)
        respond_span.end()

        root.end()

        # Verify trace structure
        assert trace.span_count == 6
        assert trace.get_root() == root
        children = trace.get_children(root.span_id)
        assert len(children) == 5

        kinds = {s.kind for s in children}
        assert SpanKind.PARSE in kinds
        assert SpanKind.ROUTE in kinds
        assert SpanKind.EXECUTE in kinds
        assert SpanKind.VERIFY in kinds
        assert SpanKind.RESPOND in kinds

    def test_trace_serialization(self):
        """Trace should serialize to a complete dict."""
        trace = DistributedTrace(trace_id="ser-test")
        root = trace.start_span(SpanKind.INPUT)
        child = trace.start_span(SpanKind.PARSE, parent_id=root.span_id)
        child.add_event("token_count", {"count": 42})
        child.end()
        root.end()

        data = trace.to_dict()
        assert data["trace_id"] == "ser-test"
        assert data["span_count"] == 2
        assert len(data["spans"]) == 2

    def test_span_context_manager(self):
        """SpanContext should auto-start and end spans."""
        trace = DistributedTrace()

        with SpanContext(trace, SpanKind.EXECUTE, attributes={"engine": "test"}) as span:
            span.set_attribute("status", "running")
            time.sleep(0.001)

        assert span.end_time is not None
        assert span.duration_ms > 0

    def test_span_context_captures_errors(self):
        """SpanContext should capture exceptions."""
        trace = DistributedTrace()

        with pytest.raises(ValueError):
            with SpanContext(trace, SpanKind.EXECUTE) as span:
                raise ValueError("test error")

        assert span.attributes.get("error") is True
        assert "test error" in span.attributes.get("error.message", "")

    def test_trace_error_spans(self):
        """Should be able to query error spans."""
        trace = DistributedTrace()
        root = trace.start_span(SpanKind.INPUT)
        error_span = trace.start_span(SpanKind.ERROR, parent_id=root.span_id)
        error_span.set_error("Division by zero", "ZeroDivisionError")
        error_span.end()
        root.end()

        errors = trace.get_error_spans()
        assert len(errors) == 1
        assert errors[0].attributes["error.message"] == "Division by zero"


# ===========================================================================
# Integration Test: Error Handling
# ===========================================================================


class TestErrorHandling:
    """Tests error handling and propagation through the stack."""

    def test_parser_handles_empty_input(self):
        """Parser should handle empty input gracefully."""
        parser = LanguageParser()
        ir = parser.parse_to_ir("", "en")
        assert isinstance(ir, MeaningIR)

    def test_realizer_handles_unknown_language(self):
        """Realizer should fall back for unknown language."""
        realizer = NativeRealizer()
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        result = realizer.realize(ir, "xx_unknown")
        # Should fall back to English
        assert isinstance(result, str)
        assert len(result) > 0

    def test_narrative_unknown_character_error(self):
        """Narrative should flag events with unknown characters."""
        reactor = NarrativeReactor()
        event, errors = reactor.generate_event(
            action="does something",
            characters=["NonexistentCharacter"],
        )
        error_types = [e.error_type for e in errors]
        assert "unknown_character" in error_types

    def test_tournament_empty_claims(self):
        """Tournament should handle empty input gracefully."""
        tournament = ReasoningTournament()
        survivors = tournament.judge()
        assert survivors == []

    def test_document_plugin_empty_text(self):
        """Document plugin should handle empty text."""
        plugin = DocumentPlugin()
        structure = plugin.ingest("")
        assert structure.word_count == 0

    def test_metrics_handles_rapid_recording(self):
        """Metrics should handle rapid recording without error."""
        collector = MetricsCollector()
        for i in range(100):
            collector.record_query(
                latency_ms=float(i),
                engine="test",
                success=(i % 10 != 0),
            )
        all_metrics = collector.get_all()
        assert all_metrics["counters"]["query_count"] == 100

    def test_trace_handles_unended_spans(self):
        """Trace should handle spans that were never ended."""
        trace = DistributedTrace()
        span = trace.start_span(SpanKind.EXECUTE)
        # Never call span.end()
        duration = trace.duration()
        assert duration > 0

    def test_register_adapter_preserves_urls(self):
        """URLs should survive register adaptation."""
        adapter = RegisterAdapter()
        text = "See https://example.com/docs for details"
        result = adapter.adapt(text, Register.NEUTRAL, Register.FORMAL)
        assert "https://example.com/docs" in result


# ===========================================================================
# Integration Test: Document Plugin Full Flow
# ===========================================================================


class TestDocumentPluginIntegration:
    """Tests document plugin with various formats."""

    def setup_method(self):
        self.plugin = DocumentPlugin()

    def test_markdown_full_parse(self):
        """Should parse full markdown document."""
        md_text = """# Introduction

This is a paragraph about testing.

## Methods

- Item one
- Item two

| Name | Value |
|------|-------|
| A    | 1     |
| B    | 2     |

```python
x = 42
```
"""
        structure = self.plugin.ingest(md_text, title="Test Doc")
        assert structure.title == "Test Doc"
        assert structure.format == DocumentFormat.MARKDOWN
        assert len(structure.sections) >= 2
        assert len(structure.tables) >= 1
        assert structure.tables[0].headers == ["Name", "Value"]
        assert structure.word_count > 0

    def test_html_full_parse(self):
        """Should parse HTML document."""
        html_text = """<html><body>
<h1>Title</h1>
<p>First paragraph.</p>
<h2>Section</h2>
<p>Second paragraph.</p>
<ul><li>Item A</li><li>Item B</li></ul>
</body></html>"""
        structure = self.plugin.ingest(html_text)
        assert structure.format == DocumentFormat.HTML
        assert len(structure.elements) >= 4

    def test_citation_spans(self):
        """Should find and cite matching spans."""
        text = "# Overview\n\nThe algorithm runs in O(n) time.\n\n# Details\n\nFor large inputs, the algorithm is efficient."
        structure = self.plugin.ingest(text, title="Algo Doc")
        citations = self.plugin.cite_spans(structure.document_id, "algorithm")
        assert len(citations) >= 1
        assert citations[0].text == "algorithm"


# ===========================================================================
# Integration Test: Metrics with Real Workload
# ===========================================================================


class TestMetricsIntegration:
    """Tests metrics collection with realistic workload."""

    def test_metrics_track_query_lifecycle(self):
        """Metrics should track a full query lifecycle."""
        collector = MetricsCollector()

        # Simulate queries
        start = time.time()
        parser = LanguageParser()
        ir = parser.parse_to_ir("What is 2+2?", "en")
        latency = (time.time() - start) * 1000

        collector.record_query(latency_ms=latency, engine="math", success=True)

        assert collector.get_counter("query_count") == 1
        assert collector.get_counter("engine_calls", {"engine": "math"}) == 1
        hist = collector.get_histogram("latency_ms")
        assert hist is not None
        assert hist.count == 1

    def test_metrics_export_prometheus(self):
        """Should export in Prometheus format."""
        collector = MetricsCollector()
        collector.record_query(latency_ms=50.0, engine="math", success=True)
        collector.record_query(latency_ms=150.0, engine="physics", success=False)

        output = collector.export(format="prometheus")
        assert "query_count" in output
        assert "latency_ms" in output
        assert "error_count" in output

    def test_metrics_reset(self):
        """Reset should clear all metrics."""
        collector = MetricsCollector()
        collector.record_query(latency_ms=10.0, engine="test", success=True)
        collector.reset()
        assert collector.get_counter("query_count") == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
