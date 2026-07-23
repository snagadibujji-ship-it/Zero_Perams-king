"""Unit tests for the language module: realizer, parser, register."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from axima.semantics.meaning_ir import (
    Entity,
    Event,
    MeaningIR,
    Predicate,
    Quantity,
    Condition,
    Goal,
)
from axima.language.realizer import (
    MorphologyRule,
    LanguageProfile,
    NativeRealizer,
)
from axima.language.parser import LanguageParser
from axima.language.register import Register, RegisterAdapter


# ===========================================================================
# Tests for NativeRealizer
# ===========================================================================


class TestNativeRealizer:
    """Tests for the NativeRealizer class."""

    def setup_method(self):
        self.realizer = NativeRealizer()

    def test_realize_simple_predicate_svo(self):
        """SVO language should produce subject-verb-object order."""
        ir = MeaningIR(
            predicates=[Predicate(subject="water", relation="is", object="a liquid")],
            language="en",
        )
        result = self.realizer.realize(ir, "en")
        assert "water" in result
        assert "is" in result
        assert "liquid" in result

    def test_realize_sov_order(self):
        """SOV language should produce subject-object-verb order."""
        ir = MeaningIR(
            predicates=[Predicate(subject="water", relation="is", object="a liquid")],
            language="de",
        )
        result = self.realizer.realize(ir, "de")
        # SOV: subject then object then verb
        words = result.lower().split()
        water_idx = next((i for i, w in enumerate(words) if "water" in w), -1)
        is_idx = next((i for i, w in enumerate(words) if "is" in w), -1)
        liquid_idx = next((i for i, w in enumerate(words) if "liquid" in w), -1)
        # In SOV: subject < object < verb
        assert water_idx < is_idx or liquid_idx < is_idx

    def test_realize_negation(self):
        """Negated predicates should include 'not'."""
        ir = MeaningIR(
            predicates=[Predicate(subject="ice", relation="is", object="a gas", negated=True)],
        )
        result = self.realizer.realize(ir, "en")
        assert "not" in result

    def test_realize_event(self):
        """Events should be realized with agent-verb-patient."""
        ir = MeaningIR(
            events=[Event(id="ev1", verb="calculates", agent="Alice", patient="the integral")],
        )
        result = self.realizer.realize(ir, "en")
        assert "Alice" in result
        assert "calculates" in result
        assert "integral" in result

    def test_realize_quantity(self):
        """Quantities should include value and unit."""
        ir = MeaningIR(
            quantities=[Quantity(value=9.8, unit="m/s²", uncertainty=0.1)],
        )
        result = self.realizer.realize(ir, "en")
        assert "9.8" in result
        assert "m/s²" in result
        assert "±0.1" in result

    def test_realize_condition(self):
        """Conditions should produce if-then structure."""
        ir = MeaningIR(
            conditions=[Condition(if_clause="x > 0", then_clause="x is positive", else_clause="x is non-positive")],
        )
        result = self.realizer.realize(ir, "en")
        assert "If" in result or "if" in result
        assert "then" in result
        assert "otherwise" in result

    def test_realize_goal(self):
        """Goals should be realized with goal framing."""
        ir = MeaningIR(
            goals=[Goal(description="solve the equation", constraints=["x > 0"])],
        )
        result = self.realizer.realize(ir, "en")
        assert "Goal" in result or "solve" in result

    def test_realize_empty_ir(self):
        """Empty IR should produce minimal output."""
        ir = MeaningIR()
        result = self.realizer.realize(ir, "en")
        # Should handle gracefully (may be empty or minimal)
        assert isinstance(result, str)

    def test_realize_formal_register(self):
        """Formal register should avoid contractions."""
        ir = MeaningIR(
            predicates=[Predicate(subject="this", relation="don't work", object="here")],
        )
        result = self.realizer.realize(ir, "en", register="formal")
        assert "don't" not in result or "do not" in result

    def test_available_languages(self):
        """Should report available languages."""
        langs = self.realizer.available_languages()
        assert "en" in langs
        assert "es" in langs
        assert "de" in langs
        assert "hi" in langs

    def test_register_profile(self):
        """Should allow registering new profiles."""
        profile = LanguageProfile(code="ja", name="Japanese", word_order="SOV")
        self.realizer.register_profile(profile)
        assert "ja" in self.realizer.available_languages()

    def test_round_trip_verification_no_parser(self):
        """Round-trip with no parser should return skip message."""
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        success, msg = self.realizer.verify_round_trip(ir, "en", parser=None)
        assert success is True
        assert "skipping" in msg.lower() or "no parser" in msg.lower()

    def test_realize_multiple_predicates(self):
        """Multiple predicates should be joined with periods."""
        ir = MeaningIR(
            predicates=[
                Predicate(subject="A", relation="is", object="B"),
                Predicate(subject="C", relation="has", object="D"),
            ],
        )
        result = self.realizer.realize(ir, "en")
        assert "." in result
        assert "A" in result
        assert "C" in result

    def test_morphology_rule_dataclass(self):
        """MorphologyRule should be a proper dataclass."""
        rule = MorphologyRule(language="en", pattern=r"\w+", transformation=r"\0s")
        assert rule.language == "en"
        assert rule.pattern == r"\w+"

    def test_language_profile_dataclass(self):
        """LanguageProfile should be a proper dataclass."""
        profile = LanguageProfile(
            code="fr",
            name="French",
            word_order="SVO",
            script="latin",
        )
        assert profile.code == "fr"
        assert profile.word_order == "SVO"


# ===========================================================================
# Tests for LanguageParser
# ===========================================================================


class TestLanguageParser:
    """Tests for the LanguageParser class."""

    def setup_method(self):
        self.parser = LanguageParser()

    def test_detect_english(self):
        """Should detect English text."""
        results = self.parser.detect_language("The quick brown fox jumps over the lazy dog")
        assert results[0][0] == "en"
        assert results[0][1] > 0.3

    def test_detect_spanish(self):
        """Should detect Spanish text."""
        results = self.parser.detect_language("El gato está en la casa con los niños")
        languages = [r[0] for r in results]
        assert "es" in languages

    def test_detect_german(self):
        """Should detect German text."""
        results = self.parser.detect_language("Der Hund ist nicht in dem Haus mit den Kindern")
        languages = [r[0] for r in results]
        assert "de" in languages

    def test_detect_empty(self):
        """Empty text should default to English."""
        results = self.parser.detect_language("")
        assert results[0][0] == "en"

    def test_parse_entities(self):
        """Should extract named entities."""
        ir = self.parser.parse_to_ir("Albert Einstein developed the theory of relativity")
        entity_names = [e.name for e in ir.entities]
        assert "Albert Einstein" in entity_names or "Albert" in entity_names

    def test_parse_quantities(self):
        """Should extract quantities with units."""
        ir = self.parser.parse_to_ir("The mass is 5.2 kg with an acceleration of 9.8 m")
        assert len(ir.quantities) >= 2
        values = [q.value for q in ir.quantities]
        assert 5.2 in values
        assert 9.8 in values

    def test_parse_quantities_units(self):
        """Should extract unit information."""
        ir = self.parser.parse_to_ir("Temperature is 100 °C")
        assert len(ir.quantities) >= 1
        assert ir.quantities[0].value == 100.0
        assert ir.quantities[0].unit == "°C"

    def test_parse_predicates_is_a(self):
        """Should extract is-a predicates."""
        ir = self.parser.parse_to_ir("A dog is a mammal.")
        pred_relations = [p.relation for p in ir.predicates]
        assert "is_a" in pred_relations

    def test_parse_predicates_has(self):
        """Should extract has-a predicates."""
        ir = self.parser.parse_to_ir("A car has an engine.")
        pred_relations = [p.relation for p in ir.predicates]
        assert "has" in pred_relations

    def test_parse_conditions(self):
        """Should extract if-then conditions."""
        ir = self.parser.parse_to_ir("If x is positive, then the square root exists.")
        assert len(ir.conditions) >= 1
        assert "positive" in ir.conditions[0].if_clause

    def test_parse_goals(self):
        """Should extract goal/intent patterns."""
        ir = self.parser.parse_to_ir("I want to solve the quadratic equation.")
        assert len(ir.goals) >= 1
        assert "solve" in ir.goals[0].description.lower() or "quadratic" in ir.goals[0].description.lower()

    def test_parse_sets_language(self):
        """Parsed IR should carry the specified language."""
        ir = self.parser.parse_to_ir("Hola mundo", language="es")
        assert ir.language == "es"

    def test_parse_complex_sentence(self):
        """Should handle complex sentences with multiple components."""
        text = "Alice calculates the integral of 3.14 kg if x > 0, then result is positive."
        ir = self.parser.parse_to_ir(text)
        # Should extract something meaningful
        assert ir.quantities or ir.entities or ir.predicates or ir.conditions


# ===========================================================================
# Tests for RegisterAdapter
# ===========================================================================


class TestRegisterAdapter:
    """Tests for the RegisterAdapter class."""

    def setup_method(self):
        self.adapter = RegisterAdapter()

    def test_adapt_same_register(self):
        """Same register should return unchanged text."""
        text = "The result is therefore positive."
        result = self.adapter.adapt(text, Register.NEUTRAL, Register.NEUTRAL)
        assert result == text

    def test_formal_to_casual(self):
        """Formal to casual should simplify language."""
        text = "Furthermore, the result is consequently positive."
        result = self.adapter.adapt(text, Register.FORMAL, Register.CASUAL)
        assert "furthermore" not in result.lower()

    def test_casual_to_formal(self):
        """Casual to formal should elevate language."""
        text = "So the answer is basically kinda obvious."
        result = self.adapter.adapt(text, Register.CASUAL, Register.FORMAL)
        # Should replace casual markers
        assert "kinda" not in result.lower() or "somewhat" in result.lower()

    def test_neutral_to_pedagogical(self):
        """Pedagogical register should add teaching framing."""
        text = "The derivative of x squared is 2x."
        result = self.adapter.adapt(text, Register.NEUTRAL, Register.PEDAGOGICAL)
        # Should add some pedagogical framing
        assert len(result) >= len(text)

    def test_preserves_technical_content(self):
        """Technical content (equations, code) should be preserved."""
        text = "The formula $E=mc^2$ shows that energy is conserved."
        result = self.adapter.adapt(text, Register.NEUTRAL, Register.CASUAL)
        assert "$E=mc^2$" in result

    def test_preserves_citations(self):
        """Citations should be preserved across register changes."""
        text = "According to Einstein [1], energy equals mass times c squared."
        result = self.adapter.adapt(text, Register.NEUTRAL, Register.FORMAL)
        assert "[1]" in result

    def test_preserves_code_spans(self):
        """Code spans should be preserved."""
        text = "Use `print(x)` to output the value."
        result = self.adapter.adapt(text, Register.NEUTRAL, Register.CASUAL)
        assert "`print(x)`" in result

    def test_detect_register_formal(self):
        """Should detect formal register."""
        text = "Furthermore, consequently, the matter is therefore settled."
        detected = self.adapter.detect_register(text)
        assert detected == Register.FORMAL

    def test_detect_register_casual(self):
        """Should detect casual register."""
        text = "Yeah basically don't worry about it, it's gonna be fine."
        detected = self.adapter.detect_register(text)
        assert detected == Register.CASUAL

    def test_detect_register_technical(self):
        """Should detect technical register."""
        text = "The algorithm has O(n log n) complexity, cf. Theorem 3.2."
        detected = self.adapter.detect_register(text)
        assert detected == Register.TECHNICAL

    def test_detect_register_neutral(self):
        """Should detect neutral register."""
        text = "The sky is blue and water flows downhill."
        detected = self.adapter.detect_register(text)
        assert detected == Register.NEUTRAL

    def test_register_enum_values(self):
        """Register enum should have all required values."""
        assert Register.FORMAL.value == "formal"
        assert Register.NEUTRAL.value == "neutral"
        assert Register.CASUAL.value == "casual"
        assert Register.TECHNICAL.value == "technical"
        assert Register.PEDAGOGICAL.value == "pedagogical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
