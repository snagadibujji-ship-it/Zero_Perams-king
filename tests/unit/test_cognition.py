"""Unit tests for the cognition module: teaching, narrative, tournament."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import pytest

from axima.cognition.teaching import (
    LearnerModel,
    TeachingPlan,
    AdaptiveTeacher,
    ConceptNode,
)
from axima.cognition.narrative import (
    Character,
    WorldState,
    NarrativeEvent,
    NarrativeReactor,
    Tension,
    TensionType,
    EmotionalValence,
    Promise,
)
from axima.cognition.reasoning_tournament import (
    TournamentRole,
    TournamentEntry,
    ReasoningTournament,
    TournamentBudget,
    Claim,
    Attack,
)


# ===========================================================================
# Tests for AdaptiveTeacher
# ===========================================================================


class TestLearnerModel:
    """Tests for the LearnerModel dataclass."""

    def test_initial_state(self):
        """New learner should have empty knowledge."""
        learner = LearnerModel()
        assert len(learner.known_concepts) == 0
        assert len(learner.misconceptions) == 0

    def test_mark_learned(self):
        """Should track learned concepts."""
        learner = LearnerModel()
        learner.mark_learned("algebra")
        assert learner.knows("algebra")
        assert "algebra" in learner.completed_prerequisites

    def test_misconception_tracking(self):
        """Should track and clear misconceptions."""
        learner = LearnerModel()
        learner.add_misconception("gravity", "things fall because they're heavy")
        assert learner.has_misconception("gravity")
        learner.clear_misconception("gravity")
        assert not learner.has_misconception("gravity")


class TestAdaptiveTeacher:
    """Tests for the AdaptiveTeacher class."""

    def setup_method(self):
        self.teacher = AdaptiveTeacher()
        # Register concept graph
        self.teacher.register_concepts([
            ConceptNode(
                name="calculus",
                prerequisites=["algebra", "limits"],
                related=["analysis"],
                explanations=["Study of continuous change"],
                examples=["Derivative of x^2 is 2x", "Integral of 2x is x^2"],
                transfer_tasks=["Compute d/dx(x^3)", "Explain what a derivative represents"],
                difficulty=3,
            ),
            ConceptNode(
                name="algebra",
                prerequisites=["arithmetic"],
                related=["equations"],
                explanations=["Symbol manipulation"],
                examples=["Solve x + 2 = 5", "Factor x^2 - 1"],
                transfer_tasks=["Solve 2x + 3 = 7"],
                difficulty=2,
            ),
            ConceptNode(
                name="limits",
                prerequisites=["algebra"],
                related=["continuity"],
                explanations=["Value a function approaches"],
                examples=["lim x->0 sin(x)/x = 1"],
                transfer_tasks=["Compute lim x->2 (x^2-4)/(x-2)"],
                difficulty=3,
            ),
            ConceptNode(
                name="arithmetic",
                prerequisites=[],
                related=["numbers"],
                explanations=["Basic number operations"],
                examples=["2 + 3 = 5", "6 * 7 = 42"],
                transfer_tasks=["Compute 123 + 456"],
                difficulty=1,
            ),
        ])

    def test_plan_with_known_bridges(self):
        """Should use known concepts as bridges."""
        learner = LearnerModel(known_concepts={"algebra", "limits", "arithmetic"})
        plan = self.teacher.plan_explanation("calculus", learner)
        assert plan.target_concept == "calculus"
        assert "algebra" in plan.bridge_from or "limits" in plan.bridge_from

    def test_plan_computes_prerequisites(self):
        """Should identify missing prerequisites."""
        learner = LearnerModel(known_concepts={"arithmetic"})
        plan = self.teacher.plan_explanation("calculus", learner)
        # Should include algebra and/or limits in prereq chain
        assert len(plan.prerequisite_chain) > 0

    def test_plan_selects_examples(self):
        """Should include examples from concept graph."""
        learner = LearnerModel(known_concepts={"algebra"})
        plan = self.teacher.plan_explanation("calculus", learner)
        assert len(plan.examples) > 0

    def test_plan_selects_transfer_tasks(self):
        """Should include transfer tasks."""
        learner = LearnerModel(known_concepts={"algebra"})
        plan = self.teacher.plan_explanation("calculus", learner)
        assert len(plan.transfer_tasks) > 0

    def test_expand_depth(self):
        """Should increase depth on request."""
        learner = LearnerModel(known_concepts={"algebra"})
        plan = self.teacher.plan_explanation("calculus", learner)
        original_depth = plan.explanation_depth
        expanded = self.teacher.expand_depth(plan)
        assert expanded.explanation_depth > original_depth

    def test_change_anchors(self):
        """Should allow changing bridge concepts."""
        learner = LearnerModel(known_concepts={"algebra"})
        plan = self.teacher.plan_explanation("calculus", learner)
        new_plan = self.teacher.change_anchors(plan, ["analysis", "physics"])
        assert "analysis" in new_plan.bridge_from

    def test_check_transfer_success(self):
        """Should detect successful understanding."""
        learner = LearnerModel(known_concepts={"algebra", "limits"})
        self.teacher.set_learner(learner)
        result = self.teacher.check_transfer(
            "calculus",
            "Calculus studies limits and continuous change using algebra and analysis",
            learner,
        )
        assert result["confidence"] > 0

    def test_check_transfer_misconception(self):
        """Should detect misconceptions in response."""
        learner = LearnerModel(
            known_concepts={"algebra"},
            misconceptions={"calculus": "calculus is just hard algebra"},
        )
        result = self.teacher.check_transfer(
            "calculus",
            "I think calculus is just hard algebra with extra steps",
            learner,
        )
        assert len(result["misconceptions_detected"]) > 0

    def test_depth_increases_for_misconception(self):
        """Depth should increase when learner has misconception."""
        learner_clean = LearnerModel(known_concepts={"arithmetic"})
        learner_wrong = LearnerModel(
            known_concepts={"arithmetic"},
            misconceptions={"algebra": "just guessing"},
        )
        plan_clean = self.teacher.plan_explanation("algebra", learner_clean)
        plan_wrong = self.teacher.plan_explanation("algebra", learner_wrong)
        assert plan_wrong.explanation_depth >= plan_clean.explanation_depth


# ===========================================================================
# Tests for NarrativeReactor
# ===========================================================================


class TestNarrativeReactor:
    """Tests for the NarrativeReactor class."""

    def setup_method(self):
        self.reactor = NarrativeReactor()
        self.reactor.add_character(Character(
            name="Alice",
            drives=["find the truth", "protect her team"],
            knowledge={"the cave exists", "Bob is her ally"},
            relationships={"Bob": "ally", "Eve": "rival"},
            constraints=["cannot fly", "cannot use magic"],
            state={"health": "good", "location": "village"},
            voice={"style": "formal", "vocabulary": "scientific"},
        ))
        self.reactor.add_character(Character(
            name="Bob",
            drives=["explore the unknown"],
            knowledge={"the cave exists"},
            relationships={"Alice": "ally"},
            constraints=["cannot swim"],
            state={"health": "good", "location": "village"},
        ))
        self.reactor.add_fact("the cave exists")
        self.reactor.add_fact("Alice is in the village")

    def test_generate_event_valid(self):
        """Should generate event when preconditions are met."""
        event, errors = self.reactor.generate_event(
            action="explores the cave entrance",
            characters=["Alice"],
            preconditions=["the cave exists"],
            consequences=["Alice found a map"],
        )
        assert event.action == "explores the cave entrance"
        # No errors for met preconditions
        error_types = [e.error_type for e in errors]
        assert "unknown_fact" not in error_types

    def test_generate_event_unmet_precondition(self):
        """Should flag unmet preconditions."""
        event, errors = self.reactor.generate_event(
            action="flies to the mountain",
            characters=["Alice"],
            preconditions=["Alice can fly"],
            consequences=["Alice reached the mountain"],
        )
        error_types = [e.error_type for e in errors]
        assert "unknown_fact" in error_types

    def test_constraint_violation(self):
        """Should detect constraint violations."""
        event, errors = self.reactor.generate_event(
            action="fly to the mountain",
            characters=["Alice"],
            preconditions=[],
            consequences=[],
        )
        error_types = [e.error_type for e in errors]
        assert "broken_constraint" in error_types

    def test_character_learns_from_event(self):
        """Characters should learn from witnessed events."""
        self.reactor.generate_event(
            action="discovers a secret passage",
            characters=["Alice"],
            consequences=["secret passage exists"],
        )
        alice = self.reactor.characters["Alice"]
        assert "secret passage exists" in alice.knowledge

    def test_advance_world_time(self):
        """Should advance world time."""
        world = self.reactor.advance_world("evening")
        assert world.time == "evening"

    def test_tension_escalation(self):
        """Time pressure tension should escalate on advance."""
        tension = Tension(
            tension_type=TensionType.TIME_PRESSURE,
            description="deadline approaching",
            magnitude=0.5,
        )
        self.reactor.world.add_tension(tension)
        self.reactor.advance_world("next day")
        # Tension should have increased
        assert tension.magnitude > 0.5

    def test_resolve_tension(self):
        """Should resolve tension through an event."""
        tension = Tension(
            tension_type=TensionType.CONFLICT,
            description="Alice vs Eve",
            involved_characters=["Alice", "Eve"],
            magnitude=0.8,
        )
        self.reactor.world.add_tension(tension)
        self.reactor.add_character(Character(name="Eve", drives=["oppose Alice"]))

        event, errors = self.reactor.resolve_tension(
            tension.tension_id,
            "negotiates a truce",
            ["Alice", "Eve"],
        )
        assert event is not None
        assert tension.resolved

    def test_highest_tension(self):
        """Should return highest unresolved tension."""
        self.reactor.world.add_tension(Tension(
            tension_type=TensionType.MYSTERY,
            description="low tension",
            magnitude=0.3,
        ))
        self.reactor.world.add_tension(Tension(
            tension_type=TensionType.CONFLICT,
            description="high tension",
            magnitude=0.9,
        ))
        highest = self.reactor.get_highest_tension()
        assert highest is not None
        assert highest.magnitude == 0.9

    def test_continuity_check(self):
        """Should detect contradictions."""
        self.reactor.add_fact("Bob is alive")
        self.reactor.add_fact("Bob is dead")
        errors = self.reactor.check_continuity()
        contradiction_errors = [e for e in errors if e.error_type == "contradiction"]
        assert len(contradiction_errors) > 0

    def test_character_perspective(self):
        """Should return character's limited view."""
        perspective = self.reactor.get_character_perspective("Alice")
        assert perspective["name"] == "Alice"
        assert "the cave exists" in perspective["knows"]

    def test_world_state_total_tension(self):
        """Total tension should sum active tensions."""
        world = WorldState()
        world.add_tension(Tension(magnitude=0.3))
        world.add_tension(Tension(magnitude=0.5))
        assert abs(world.total_tension - 0.8) < 0.01

    def test_promise_tracking(self):
        """Should track narrative promises."""
        world = WorldState()
        promise = Promise(description="The map will reveal the treasure")
        world.add_promise(promise)
        assert len(world.unresolved_promises) == 1
        world.fulfill_promise(promise.promise_id, "ev_123")
        assert promise.fulfilled


# ===========================================================================
# Tests for ReasoningTournament
# ===========================================================================


class TestReasoningTournament:
    """Tests for the ReasoningTournament class."""

    def setup_method(self):
        self.tournament = ReasoningTournament()

    def test_propose_claim(self):
        """Should register a claim."""
        claim = self.tournament.propose(
            statement="All primes greater than 2 are odd",
            evidence=["2 is the only even prime", "Definition of prime"],
            confidence=0.9,
        )
        assert claim.statement == "All primes greater than 2 are odd"
        assert claim.confidence == 0.9

    def test_attack_generates_attacks(self):
        """Should generate attacks from multiple roles."""
        claim = self.tournament.propose(
            statement="All algorithms always terminate",
            evidence=["Most algorithms I've seen terminate"],
            confidence=0.8,
        )
        attacks = self.tournament.attack(claim.claim_id)
        assert len(attacks) > 0
        # Should flag the universal claim "always"
        roles_used = {a.role for a in attacks}
        assert TournamentRole.COUNTEREXAMPLE_SEARCHER in roles_used or \
               TournamentRole.ASSUMPTION_HUNTER in roles_used

    def test_evidence_auditor_no_evidence(self):
        """Evidence auditor should flag claims without evidence."""
        claim = self.tournament.propose(
            statement="The earth is flat",
            evidence=[],
            confidence=0.3,
        )
        attacks = self.tournament.attack(
            claim.claim_id,
            roles=[TournamentRole.EVIDENCE_AUDITOR],
        )
        assert any("No evidence" in a.argument for a in attacks)

    def test_defense_reduces_impact(self):
        """Defended attacks should have less impact on confidence."""
        claim = self.tournament.propose(
            statement="Water always boils at 100°C",
            evidence=["Standard boiling point"],
            confidence=0.7,
        )
        attacks = self.tournament.attack(claim.claim_id)

        # Defend all attacks
        for attack in attacks:
            self.tournament.defend(
                attack.attack_id,
                "At standard pressure, this is correct by definition",
            )

        survivors = self.tournament.judge()
        # With defenses, claim should survive (confidence reduced less)
        judged_claim = self.tournament._claims[claim.claim_id]
        # Confidence reduced but claim survived due to defenses
        assert judged_claim.confidence > 0

    def test_fatal_attack_kills_claim(self):
        """Fatal undefended attack should eliminate claim."""
        claim = self.tournament.propose(
            statement="This claim proves itself because this claim proves itself",
            evidence=["This claim proves itself because this claim proves itself"],
            confidence=0.9,
        )
        attacks = self.tournament.attack(
            claim.claim_id,
            roles=[TournamentRole.EVIDENCE_AUDITOR],
        )
        # Should detect circular reasoning (fatal)
        fatal = [a for a in attacks if a.severity == "fatal"]
        assert len(fatal) > 0

        survivors = self.tournament.judge()
        assert claim.claim_id not in {c.claim_id for c in survivors}

    def test_budget_enforcement(self):
        """Should stop attacking when budget is exhausted."""
        budget = TournamentBudget(max_total_attacks=3)
        tournament = ReasoningTournament(budget=budget)

        c1 = tournament.propose("All X are Y", evidence=["source 1"])
        c2 = tournament.propose("All A are B", evidence=["source 2"])

        tournament.attack(c1.claim_id)
        tournament.attack(c2.claim_id)

        # Total attacks should not exceed budget
        assert budget.attacks_used <= 3

    def test_full_tournament(self):
        """run_full_tournament should process multiple claims."""
        statements = [
            "Water is wet",
            "All cats always land on their feet",
            "The sun is a star",
        ]
        evidence_map = {
            "Water is wet": ["Physical property of water"],
            "All cats always land on their feet": ["Righting reflex observation"],
            "The sun is a star": ["Astronomical classification", "Nuclear fusion core"],
        }
        survivors = self.tournament.run_full_tournament(statements, evidence_map)
        assert len(survivors) > 0
        assert len(survivors) <= 3

    def test_tournament_summary(self):
        """Should produce a tournament summary."""
        self.tournament.propose("Test claim", evidence=["ev1"], confidence=0.7)
        self.tournament.judge()
        summary = self.tournament.get_tournament_summary()
        assert "total_claims" in summary
        assert "survived" in summary
        assert "budget_used" in summary

    def test_tournament_roles_enum(self):
        """All required roles should exist."""
        assert TournamentRole.PROPOSER.value == "proposer"
        assert TournamentRole.ASSUMPTION_HUNTER.value == "assumption_hunter"
        assert TournamentRole.COUNTEREXAMPLE_SEARCHER.value == "counterexample_searcher"
        assert TournamentRole.EVIDENCE_AUDITOR.value == "evidence_auditor"
        assert TournamentRole.SECURITY_CRITIC.value == "security_critic"
        assert TournamentRole.SIMPLIFIER.value == "simplifier"
        assert TournamentRole.JUDGE.value == "judge"

    def test_security_critic(self):
        """Security critic should flag security-relevant claims."""
        claim = self.tournament.propose(
            statement="The user input is safe to eval directly",
            evidence=["It's a number"],
            confidence=0.6,
        )
        attacks = self.tournament.attack(
            claim.claim_id,
            roles=[TournamentRole.SECURITY_CRITIC],
        )
        assert len(attacks) > 0

    def test_simplifier(self):
        """Simplifier should flag overly complex claims."""
        long_statement = " ".join(["word"] * 35)  # 35 words
        claim = self.tournament.propose(
            statement=long_statement,
            evidence=["source"],
            assumptions=["a1", "a2", "a3", "a4"],
            confidence=0.5,
        )
        attacks = self.tournament.attack(
            claim.claim_id,
            roles=[TournamentRole.SIMPLIFIER],
        )
        assert len(attacks) > 0

    def test_tournament_entry_dataclass(self):
        """TournamentEntry should be a proper dataclass."""
        claim = Claim(statement="test", confidence=0.5)
        entry = TournamentEntry(
            role=TournamentRole.PROPOSER,
            claim=claim,
            argument="test argument",
            attacks=[],
            survived=True,
        )
        assert entry.role == TournamentRole.PROPOSER
        assert entry.survived is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
