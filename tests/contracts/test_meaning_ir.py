"""Tests for Phase R3: Meaning and Epistemic Compilation.

At least 30 test cases covering:
- MeaningIR creation, hashing, merging
- Compiler on simple queries
- Semantic checksum round-trip
- Epistemic contract compilation
- Intent lattice resolution
"""

import sys
import os
import unittest

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from axima.semantics.meaning_ir import (
    Entity, Event, Quantity, Predicate, Condition, Goal, MeaningIR,
)
from axima.semantics.compiler import MeaningCompiler
from axima.semantics.checksum import semantic_hash, verify_checksum
from axima.semantics.transforms import (
    TransformationType, TransformPlan, TransformOperation, verify_conservation,
)
from axima.epistemics.contracts import (
    AnswerKind, EvidenceRequirement, EpistemicContract, ContractCompiler,
)
from axima.epistemics.entropy import SemanticEntropy, EntropyRecommendation
from axima.epistemics.unknowns import UnknownBoundary, BoundaryMapper
from axima.routing.intent_lattice import IntentCandidate, IntentLattice, IntentDetector


class TestMeaningIRCreation(unittest.TestCase):
    """Test MeaningIR dataclass creation."""

    def test_empty_ir(self):
        ir = MeaningIR()
        self.assertEqual(ir.entities, [])
        self.assertEqual(ir.predicates, [])
        self.assertEqual(ir.language, "en")

    def test_ir_with_entities(self):
        e = Entity(id="e1", name="Python", type="concept")
        ir = MeaningIR(entities=[e])
        self.assertEqual(len(ir.entities), 1)
        self.assertEqual(ir.entities[0].name, "Python")

    def test_ir_with_all_fields(self):
        ir = MeaningIR(
            entities=[Entity(id="e1", name="X", type="object")],
            events=[Event(id="ev1", verb="run")],
            predicates=[Predicate(subject="X", relation="is", object="fast")],
            quantities=[Quantity(value=10.0, unit="m")],
            conditions=[Condition(if_clause="a", then_clause="b")],
            goals=[Goal(description="find X")],
            constraints=["positive"],
            language="en",
        )
        self.assertEqual(len(ir.entities), 1)
        self.assertEqual(len(ir.events), 1)
        self.assertEqual(len(ir.predicates), 1)
        self.assertEqual(len(ir.quantities), 1)
        self.assertEqual(len(ir.conditions), 1)
        self.assertEqual(len(ir.goals), 1)

    def test_entity_source_span(self):
        e = Entity(id="e1", name="Earth", type="location", source_span=(5, 10))
        self.assertEqual(e.source_span, (5, 10))

    def test_quantity_uncertainty(self):
        q = Quantity(value=9.81, unit="m/s", uncertainty=0.01, domain="physics")
        self.assertEqual(q.uncertainty, 0.01)
        self.assertEqual(q.domain, "physics")


class TestMeaningIRHashing(unittest.TestCase):
    """Test semantic hashing."""

    def test_deterministic_hash(self):
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        h1 = ir.semantic_hash()
        h2 = ir.semantic_hash()
        self.assertEqual(h1, h2)

    def test_different_content_different_hash(self):
        ir1 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        ir2 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="C")])
        self.assertNotEqual(ir1.semantic_hash(), ir2.semantic_hash())

    def test_order_independence(self):
        """Entities in different order should produce same hash."""
        e1 = Entity(id="a", name="Alpha", type="concept")
        e2 = Entity(id="b", name="Beta", type="concept")
        ir1 = MeaningIR(entities=[e1, e2])
        ir2 = MeaningIR(entities=[e2, e1])
        self.assertEqual(ir1.semantic_hash(), ir2.semantic_hash())

    def test_hash_ignores_source_spans(self):
        ir1 = MeaningIR(
            entities=[Entity(id="e1", name="X", type="obj", source_span=(0, 1))],
            source_span_map={"e1": (0, 1)},
        )
        ir2 = MeaningIR(
            entities=[Entity(id="e1", name="X", type="obj", source_span=(5, 10))],
            source_span_map={"e1": (5, 10)},
        )
        self.assertEqual(ir1.semantic_hash(), ir2.semantic_hash())

    def test_hash_is_sha256(self):
        ir = MeaningIR()
        h = ir.semantic_hash()
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))


class TestMeaningIRMerge(unittest.TestCase):
    """Test IR merging."""

    def test_merge_entities(self):
        ir1 = MeaningIR(entities=[Entity(id="e1", name="A", type="x")])
        ir2 = MeaningIR(entities=[Entity(id="e2", name="B", type="y")])
        merged = ir1.merge(ir2)
        self.assertEqual(len(merged.entities), 2)

    def test_merge_deduplicates_by_id(self):
        ir1 = MeaningIR(entities=[Entity(id="e1", name="A", type="x")])
        ir2 = MeaningIR(entities=[Entity(id="e1", name="A", type="x")])
        merged = ir1.merge(ir2)
        self.assertEqual(len(merged.entities), 1)

    def test_merge_predicates(self):
        p1 = Predicate(subject="A", relation="is", object="B")
        p2 = Predicate(subject="C", relation="has", object="D")
        ir1 = MeaningIR(predicates=[p1])
        ir2 = MeaningIR(predicates=[p2])
        merged = ir1.merge(ir2)
        self.assertEqual(len(merged.predicates), 2)

    def test_merge_constraints(self):
        ir1 = MeaningIR(constraints=["positive", "integer"])
        ir2 = MeaningIR(constraints=["integer", "non-zero"])
        merged = ir1.merge(ir2)
        self.assertEqual(len(merged.constraints), 3)


class TestMeaningCompiler(unittest.TestCase):
    """Test the rule-based meaning compiler."""

    def setUp(self):
        self.compiler = MeaningCompiler()

    def test_compile_simple_fact(self):
        ir = self.compiler.compile("Python is a programming language")
        self.assertTrue(len(ir.predicates) > 0)
        pred = ir.predicates[0]
        self.assertIn("python", pred.subject.lower())

    def test_compile_quantity(self):
        ir = self.compiler.compile("The ball weighs 5kg")
        self.assertTrue(len(ir.quantities) > 0)
        self.assertEqual(ir.quantities[0].value, 5.0)
        self.assertEqual(ir.quantities[0].unit, "kg")

    def test_compile_condition(self):
        ir = self.compiler.compile("if x is positive, then x squared is positive")
        self.assertTrue(len(ir.conditions) > 0)
        self.assertIn("positive", ir.conditions[0].if_clause)

    def test_compile_goal(self):
        ir = self.compiler.compile("calculate the area of a circle with radius 5m")
        self.assertTrue(len(ir.goals) > 0)
        self.assertTrue(len(ir.quantities) > 0)

    def test_compile_entity_extraction(self):
        ir = self.compiler.compile("Albert Einstein developed the theory of relativity")
        names = [e.name for e in ir.entities]
        self.assertIn("Albert Einstein", names)

    def test_compile_preserves_language(self):
        ir = self.compiler.compile("Bonjour le monde", language="fr")
        self.assertEqual(ir.language, "fr")

    def test_compile_negation(self):
        ir = self.compiler.compile("Water is not a gas")
        self.assertTrue(len(ir.predicates) > 0)
        self.assertTrue(ir.predicates[0].negated)


class TestSemanticChecksum(unittest.TestCase):
    """Test checksum round-trip."""

    def test_hash_roundtrip(self):
        ir = MeaningIR(predicates=[Predicate(subject="X", relation="is", object="Y")])
        h = semantic_hash(ir)
        self.assertTrue(verify_checksum(ir, h))

    def test_hash_mismatch(self):
        ir = MeaningIR(predicates=[Predicate(subject="X", relation="is", object="Y")])
        self.assertFalse(verify_checksum(ir, "badhash"))

    def test_normalized_hash_deterministic(self):
        ir = MeaningIR(predicates=[Predicate(subject="Hello", relation="is", object="World")])
        h1 = semantic_hash(ir)
        h2 = semantic_hash(ir)
        self.assertEqual(h1, h2)


class TestEpistemicContracts(unittest.TestCase):
    """Test epistemic contract compilation."""

    def setUp(self):
        self.compiler = ContractCompiler()

    def test_proof_query(self):
        contract = self.compiler.compile("prove that the sum of angles in a triangle is 180")
        self.assertEqual(contract.answer_kind, AnswerKind.PROOF)
        self.assertEqual(contract.required_evidence, EvidenceRequirement.PROVEN)

    def test_estimate_query(self):
        contract = self.compiler.compile("estimate the population of France")
        self.assertEqual(contract.answer_kind, AnswerKind.ESTIMATE)
        self.assertEqual(contract.required_evidence, EvidenceRequirement.HEURISTIC)

    def test_fact_query(self):
        contract = self.compiler.compile("what is the speed of light")
        self.assertEqual(contract.answer_kind, AnswerKind.FACT)
        self.assertEqual(contract.required_evidence, EvidenceRequirement.SOURCED)

    def test_derivation_query(self):
        contract = self.compiler.compile("calculate the derivative of x^2")
        self.assertEqual(contract.answer_kind, AnswerKind.DERIVATION)

    def test_plan_query(self):
        contract = self.compiler.compile("how to build a REST API")
        self.assertEqual(contract.answer_kind, AnswerKind.PLAN)

    def test_action_query(self):
        contract = self.compiler.compile("create a sorting function")
        self.assertEqual(contract.answer_kind, AnswerKind.ACTION)

    def test_creative_query(self):
        contract = self.compiler.compile("write a poem about the ocean")
        self.assertEqual(contract.answer_kind, AnswerKind.CREATIVE)

    def test_safety_critical(self):
        contract = self.compiler.compile("what is the correct dosage of aspirin")
        self.assertEqual(contract.safety_class, "critical")
        self.assertGreaterEqual(contract.confidence_floor, 0.95)

    def test_time_sensitive(self):
        contract = self.compiler.compile("what is the current temperature today")
        self.assertEqual(contract.freshness_requirement, "24h")

    def test_unit_requirement(self):
        contract = self.compiler.compile("what is the distance in meters")
        self.assertEqual(contract.unit_requirement, "meters")


class TestSemanticEntropy(unittest.TestCase):
    """Test semantic entropy gauge."""

    def setUp(self):
        self.gauge = SemanticEntropy()

    def test_no_alternatives(self):
        entropy = self.gauge.compute([])
        self.assertEqual(entropy, 0.0)

    def test_single_unambiguous(self):
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        entropy = self.gauge.compute([ir])
        self.assertEqual(entropy, 0.0)

    def test_conflicting_alternatives(self):
        ir1 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B", negated=False)])
        ir2 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B", negated=True)])
        entropy = self.gauge.compute([ir1, ir2])
        self.assertGreater(entropy, 0.3)

    def test_recommend_proceed(self):
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        result = self.gauge.recommend([ir])
        self.assertEqual(result.recommendation, EntropyRecommendation.PROCEED)


class TestIntentLattice(unittest.TestCase):
    """Test intent lattice resolution."""

    def test_add_and_resolve(self):
        lattice = IntentLattice()
        lattice.add_candidate(IntentCandidate(
            intent="math", confidence=0.9, engine="prometheus", cost=1.0,
        ))
        result = lattice.resolve()
        self.assertIsNotNone(result)
        self.assertEqual(result.intent, "math")

    def test_needs_clarification(self):
        lattice = IntentLattice()
        lattice.add_candidate(IntentCandidate(intent="math", confidence=0.5, engine="a", cost=1.0))
        lattice.add_candidate(IntentCandidate(intent="physics", confidence=0.48, engine="b", cost=1.0))
        self.assertTrue(lattice.needs_clarification())

    def test_no_clarification_needed(self):
        lattice = IntentLattice()
        lattice.add_candidate(IntentCandidate(intent="math", confidence=0.9, engine="a", cost=1.0))
        lattice.add_candidate(IntentCandidate(intent="physics", confidence=0.3, engine="b", cost=1.0))
        self.assertFalse(lattice.needs_clarification())

    def test_top_k(self):
        lattice = IntentLattice()
        for i, name in enumerate(["a", "b", "c", "d"]):
            lattice.add_candidate(IntentCandidate(
                intent=name, confidence=0.9 - i * 0.2, engine="x", cost=1.0,
            ))
        top = lattice.get_top_k(2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0].intent, "a")

    def test_intent_detector_math(self):
        detector = IntentDetector()
        lattice = detector.detect("solve x^2 + 3x - 4 = 0")
        top = lattice.get_top_k(1)
        self.assertEqual(top[0].intent, "math")

    def test_intent_detector_code(self):
        detector = IntentDetector()
        lattice = detector.detect("write a binary search function in Python")
        top = lattice.get_top_k(1)
        self.assertEqual(top[0].intent, "code")

    def test_intent_detector_knowledge(self):
        detector = IntentDetector()
        lattice = detector.detect("what is photosynthesis")
        top = lattice.get_top_k(1)
        self.assertIn(top[0].intent, ("knowledge", "explanation"))

    def test_intent_detector_fallback(self):
        detector = IntentDetector()
        lattice = detector.detect("xyzzy plugh")
        top = lattice.get_top_k(1)
        self.assertIsNotNone(top[0])


class TestTransforms(unittest.TestCase):
    """Test semantic transformations."""

    def test_preserve_conservation(self):
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        plan = TransformPlan(
            operations=[TransformOperation(type=TransformationType.PRESERVE, target="all")],
            input_hash=ir.semantic_hash(),
        )
        self.assertTrue(verify_conservation(ir, ir, plan))

    def test_preserve_fails_on_change(self):
        ir1 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        ir2 = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="C")])
        plan = TransformPlan(
            operations=[TransformOperation(type=TransformationType.PRESERVE, target="all")],
            input_hash=ir1.semantic_hash(),
        )
        self.assertFalse(verify_conservation(ir1, ir2, plan))

    def test_wrong_input_hash_fails(self):
        ir = MeaningIR(predicates=[Predicate(subject="A", relation="is", object="B")])
        plan = TransformPlan(
            operations=[TransformOperation(type=TransformationType.PRESERVE, target="all")],
            input_hash="wrong_hash",
        )
        self.assertFalse(verify_conservation(ir, ir, plan))


class TestBoundaryMapper(unittest.TestCase):
    """Test unknown boundary mapping."""

    def test_no_evidence(self):
        compiler = ContractCompiler()
        contract = compiler.compile("what is the mass of the sun")
        mapper = BoundaryMapper()
        boundary = mapper.map(contract, [])
        self.assertTrue(len(boundary.unresolved) > 0)
        self.assertTrue(len(boundary.missing_evidence) > 0)

    def test_with_evidence(self):
        compiler = ContractCompiler()
        contract = compiler.compile("what is gravity")
        mapper = BoundaryMapper()
        boundary = mapper.map(contract, ["gravity is 9.81 m/s^2"])
        self.assertTrue(len(boundary.known_claims) > 0)


if __name__ == "__main__":
    unittest.main()
