"""
Reasoning Tournament — Self-Challenge System
=============================================

Multi-role adversarial reasoning where claims are proposed, attacked,
defended, and judged. Each role has distinct allowed transformations.
Budget-controlled exploration prevents infinite loops.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class TournamentRole(Enum):
    """Distinct roles in the reasoning tournament.

    Each role applies specific transformations:
    - PROPOSER: Generates initial claims from evidence
    - ASSUMPTION_HUNTER: Identifies hidden assumptions
    - COUNTEREXAMPLE_SEARCHER: Finds cases where claims fail
    - EVIDENCE_AUDITOR: Checks evidence quality and relevance
    - SECURITY_CRITIC: Identifies safety/security implications
    - SIMPLIFIER: Reduces complexity, finds simpler alternatives
    - JUDGE: Weighs arguments, determines survivors
    """

    PROPOSER = "proposer"
    ASSUMPTION_HUNTER = "assumption_hunter"
    COUNTEREXAMPLE_SEARCHER = "counterexample_searcher"
    EVIDENCE_AUDITOR = "evidence_auditor"
    SECURITY_CRITIC = "security_critic"
    SIMPLIFIER = "simplifier"
    JUDGE = "judge"


@dataclass
class Claim:
    """A claim in the tournament."""

    claim_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    statement: str = ""
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.5
    source: str = ""  # Which role generated it
    assumptions: List[str] = field(default_factory=list)
    survived: bool = True


@dataclass
class Attack:
    """An attack on a claim by a tournament role."""

    attack_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_claim_id: str = ""
    role: TournamentRole = TournamentRole.ASSUMPTION_HUNTER
    argument: str = ""
    severity: str = "medium"  # "low", "medium", "high", "fatal"
    counterexample: Optional[str] = None


@dataclass
class Defense:
    """A defense against an attack."""

    defense_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    attack_id: str = ""
    argument: str = ""
    successful: bool = False  # Determined by judge


@dataclass
class TournamentEntry:
    """A complete tournament entry with claim, attacks, and verdict.

    Attributes:
        role: The role that proposed this entry.
        claim: The claim being examined.
        argument: Supporting argument.
        attacks: Attacks received.
        survived: Whether the claim survived the tournament.
    """

    role: TournamentRole
    claim: Claim
    argument: str = ""
    attacks: List[Attack] = field(default_factory=list)
    survived: bool = True


@dataclass
class TournamentBudget:
    """Resource budget for tournament exploration.

    Prevents infinite attack/defense loops.
    """

    max_rounds: int = 5
    max_attacks_per_claim: int = 3
    max_total_attacks: int = 20
    max_total_defenses: int = 15
    current_round: int = 0
    attacks_used: int = 0
    defenses_used: int = 0

    @property
    def exhausted(self) -> bool:
        """Check if any budget limit is reached."""
        return (
            self.current_round >= self.max_rounds
            or self.attacks_used >= self.max_total_attacks
            or self.defenses_used >= self.max_total_defenses
        )

    def can_attack(self) -> bool:
        """Check if we can afford another attack."""
        return self.attacks_used < self.max_total_attacks

    def can_defend(self) -> bool:
        """Check if we can afford another defense."""
        return self.defenses_used < self.max_total_defenses

    def use_attack(self) -> None:
        """Consume one attack from budget."""
        self.attacks_used += 1

    def use_defense(self) -> None:
        """Consume one defense from budget."""
        self.defenses_used += 1

    def advance_round(self) -> None:
        """Move to the next round."""
        self.current_round += 1


# ---------------------------------------------------------------------------
# Role-specific transformations
# ---------------------------------------------------------------------------


class _RoleEngine:
    """Base class for role-specific reasoning."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        """Generate attacks based on this role's perspective."""
        return []


class _AssumptionHunter(_RoleEngine):
    """Identifies hidden assumptions in claims."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        attacks: List[Attack] = []

        # Check for assumption-laden language
        assumption_markers = [
            "always", "never", "all", "none", "must", "obvious",
            "clearly", "everyone knows", "it follows that",
        ]

        statement_lower = claim.statement.lower()
        for marker in assumption_markers:
            if marker in statement_lower:
                attacks.append(Attack(
                    target_claim_id=claim.claim_id,
                    role=TournamentRole.ASSUMPTION_HUNTER,
                    argument=f"Hidden assumption detected: use of '{marker}' implies unstated generalization",
                    severity="medium",
                ))

        # Check if evidence is sufficient for the claim strength
        if claim.confidence > 0.8 and len(claim.evidence) < 2:
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.ASSUMPTION_HUNTER,
                argument="High confidence with insufficient evidence — assumes evidence generalizes",
                severity="high",
            ))

        return attacks


class _CounterexampleSearcher(_RoleEngine):
    """Searches for cases where claims fail."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        attacks: List[Attack] = []

        statement_lower = claim.statement.lower()

        # Universal claims are vulnerable to single counterexamples
        universal_markers = ["all", "every", "always", "no", "never", "none"]
        for marker in universal_markers:
            if marker in statement_lower:
                attacks.append(Attack(
                    target_claim_id=claim.claim_id,
                    role=TournamentRole.COUNTEREXAMPLE_SEARCHER,
                    argument=f"Universal claim ('{marker}') — vulnerable to single counterexample",
                    severity="high",
                    counterexample=f"Consider edge case where '{marker}' fails",
                ))
                break

        # Boundary conditions
        if any(w in statement_lower for w in ["greater than", "less than", "more than", "fewer than"]):
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.COUNTEREXAMPLE_SEARCHER,
                argument="Boundary condition: what happens at the exact threshold?",
                severity="low",
                counterexample="Test at boundary value",
            ))

        return attacks


class _EvidenceAuditor(_RoleEngine):
    """Checks evidence quality and relevance."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        attacks: List[Attack] = []

        if not claim.evidence:
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.EVIDENCE_AUDITOR,
                argument="No evidence provided for this claim",
                severity="high",
            ))
        elif len(claim.evidence) == 1:
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.EVIDENCE_AUDITOR,
                argument="Single source of evidence — no corroboration",
                severity="medium",
            ))

        # Check for circular reasoning
        for ev in claim.evidence:
            if claim.statement.lower() in ev.lower():
                attacks.append(Attack(
                    target_claim_id=claim.claim_id,
                    role=TournamentRole.EVIDENCE_AUDITOR,
                    argument="Circular reasoning: evidence restates the claim",
                    severity="fatal",
                ))

        return attacks


class _SecurityCritic(_RoleEngine):
    """Identifies safety and security implications."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        attacks: List[Attack] = []

        statement_lower = claim.statement.lower()
        security_concerns = [
            ("eval", "Potential code execution vulnerability"),
            ("exec", "Potential code execution vulnerability"),
            ("trust", "Trust boundary assumption"),
            ("safe", "Safety claim without proof"),
            ("secure", "Security claim without verification"),
            ("input", "Potential injection vector"),
            ("user", "User-controlled data assumption"),
            ("permission", "Authorization assumption"),
        ]

        for keyword, concern in security_concerns:
            if keyword in statement_lower:
                attacks.append(Attack(
                    target_claim_id=claim.claim_id,
                    role=TournamentRole.SECURITY_CRITIC,
                    argument=concern,
                    severity="medium",
                ))

        return attacks


class _Simplifier(_RoleEngine):
    """Reduces complexity, suggests simpler alternatives."""

    def generate_attacks(self, claim: Claim) -> List[Attack]:
        attacks: List[Attack] = []

        # Long claims may be over-specified
        if len(claim.statement.split()) > 30:
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.SIMPLIFIER,
                argument="Claim is overly complex — can it be decomposed into simpler sub-claims?",
                severity="low",
            ))

        # Many assumptions indicate complexity
        if len(claim.assumptions) > 3:
            attacks.append(Attack(
                target_claim_id=claim.claim_id,
                role=TournamentRole.SIMPLIFIER,
                argument=f"Claim rests on {len(claim.assumptions)} assumptions — consider simplifying",
                severity="medium",
            ))

        return attacks


_ROLE_ENGINES: Dict[TournamentRole, _RoleEngine] = {
    TournamentRole.ASSUMPTION_HUNTER: _AssumptionHunter(),
    TournamentRole.COUNTEREXAMPLE_SEARCHER: _CounterexampleSearcher(),
    TournamentRole.EVIDENCE_AUDITOR: _EvidenceAuditor(),
    TournamentRole.SECURITY_CRITIC: _SecurityCritic(),
    TournamentRole.SIMPLIFIER: _Simplifier(),
}


# ---------------------------------------------------------------------------
# ReasoningTournament
# ---------------------------------------------------------------------------


class ReasoningTournament:
    """Multi-role adversarial reasoning system.

    Claims are proposed, then attacked by specialist roles:
    - Assumption Hunter: finds hidden assumptions
    - Counterexample Searcher: finds failure cases
    - Evidence Auditor: checks evidence quality
    - Security Critic: identifies safety issues
    - Simplifier: suggests simpler alternatives

    The Judge weighs all arguments and determines which claims survive.
    Budget-controlled to prevent infinite exploration.
    """

    def __init__(self, budget: Optional[TournamentBudget] = None) -> None:
        self._budget = budget or TournamentBudget()
        self._claims: Dict[str, Claim] = {}
        self._attacks: Dict[str, List[Attack]] = {}  # claim_id -> attacks
        self._defenses: Dict[str, List[Defense]] = {}  # attack_id -> defenses
        self._entries: List[TournamentEntry] = []
        self._judgments: Dict[str, bool] = {}  # claim_id -> survived

    @property
    def budget(self) -> TournamentBudget:
        """Current budget state."""
        return self._budget

    @property
    def entries(self) -> List[TournamentEntry]:
        """All tournament entries."""
        return list(self._entries)

    def propose(
        self,
        statement: str,
        evidence: Optional[List[str]] = None,
        assumptions: Optional[List[str]] = None,
        confidence: float = 0.5,
    ) -> Claim:
        """Propose a new claim for tournament evaluation.

        Args:
            statement: The claim statement.
            evidence: Supporting evidence.
            assumptions: Known assumptions.
            confidence: Initial confidence (0.0 - 1.0).

        Returns:
            The registered Claim.
        """
        claim = Claim(
            statement=statement,
            evidence=evidence or [],
            confidence=confidence,
            source=TournamentRole.PROPOSER.value,
            assumptions=assumptions or [],
        )
        self._claims[claim.claim_id] = claim
        self._attacks[claim.claim_id] = []
        return claim

    def attack(
        self,
        claim_id: str,
        roles: Optional[List[TournamentRole]] = None,
    ) -> List[Attack]:
        """Run attack roles against a claim.

        Args:
            claim_id: ID of the claim to attack.
            roles: Specific roles to use (None = all non-proposer, non-judge roles).

        Returns:
            List of generated attacks.
        """
        claim = self._claims.get(claim_id)
        if claim is None:
            return []

        if self._budget.exhausted:
            return []

        roles = roles or [
            TournamentRole.ASSUMPTION_HUNTER,
            TournamentRole.COUNTEREXAMPLE_SEARCHER,
            TournamentRole.EVIDENCE_AUDITOR,
            TournamentRole.SECURITY_CRITIC,
            TournamentRole.SIMPLIFIER,
        ]

        all_attacks: List[Attack] = []

        for role in roles:
            if not self._budget.can_attack():
                break

            engine = _ROLE_ENGINES.get(role)
            if engine is None:
                continue

            role_attacks = engine.generate_attacks(claim)

            # Respect per-claim limit
            remaining = self._budget.max_attacks_per_claim - len(self._attacks.get(claim_id, []))
            role_attacks = role_attacks[:max(remaining, 0)]

            for attack in role_attacks:
                if not self._budget.can_attack():
                    break
                self._budget.use_attack()
                all_attacks.append(attack)
                self._attacks.setdefault(claim_id, []).append(attack)

        return all_attacks

    def defend(
        self,
        attack_id: str,
        argument: str,
    ) -> Optional[Defense]:
        """Submit a defense against an attack.

        Args:
            attack_id: ID of the attack to defend against.
            argument: The defense argument.

        Returns:
            The Defense, or None if budget exhausted.
        """
        if not self._budget.can_defend():
            return None

        defense = Defense(
            attack_id=attack_id,
            argument=argument,
        )
        self._budget.use_defense()
        self._defenses.setdefault(attack_id, []).append(defense)
        return defense

    def judge(self) -> List[Claim]:
        """Judge all claims based on attacks and defenses.

        Determines which claims survive the tournament.
        Scoring:
        - Fatal attacks with no defense: claim dies
        - High severity attacks reduce confidence
        - Defended attacks are partially neutralized
        - Claims below confidence threshold don't survive

        Returns:
            List of surviving claims.
        """
        self._budget.advance_round()
        surviving: List[Claim] = []
        confidence_threshold = 0.3

        for claim_id, claim in self._claims.items():
            attacks = self._attacks.get(claim_id, [])
            effective_confidence = claim.confidence

            for attack in attacks:
                # Check if this attack was defended
                defenses = self._defenses.get(attack.attack_id, [])

                if attack.severity == "fatal" and not defenses:
                    effective_confidence = 0.0
                    break
                elif attack.severity == "high":
                    reduction = 0.3 if not defenses else 0.1
                    effective_confidence -= reduction
                elif attack.severity == "medium":
                    reduction = 0.15 if not defenses else 0.05
                    effective_confidence -= reduction
                elif attack.severity == "low":
                    reduction = 0.05 if not defenses else 0.0
                    effective_confidence -= reduction

                # Mark defenses as successful if they reduce impact
                for defense in defenses:
                    defense.successful = True

            claim.confidence = max(effective_confidence, 0.0)
            claim.survived = effective_confidence >= confidence_threshold
            self._judgments[claim_id] = claim.survived

            if claim.survived:
                surviving.append(claim)

        # Build tournament entries
        self._entries = []
        for claim_id, claim in self._claims.items():
            entry = TournamentEntry(
                role=TournamentRole.PROPOSER,
                claim=claim,
                argument=claim.statement,
                attacks=self._attacks.get(claim_id, []),
                survived=claim.survived,
            )
            self._entries.append(entry)

        return surviving

    def run_full_tournament(
        self,
        statements: List[str],
        evidence_map: Optional[Dict[str, List[str]]] = None,
    ) -> List[Claim]:
        """Run a complete tournament on multiple claims.

        Proposes all claims, runs attacks, then judges.

        Args:
            statements: List of claim statements.
            evidence_map: Optional map of statement -> evidence list.

        Returns:
            List of surviving claims.
        """
        evidence_map = evidence_map or {}

        # Propose all claims
        claims: List[Claim] = []
        for stmt in statements:
            evidence = evidence_map.get(stmt, [])
            claim = self.propose(stmt, evidence=evidence)
            claims.append(claim)

        # Attack each claim
        for claim in claims:
            if self._budget.exhausted:
                break
            self.attack(claim.claim_id)

        # Judge all
        return self.judge()

    def get_tournament_summary(self) -> Dict[str, Any]:
        """Get a summary of the tournament results."""
        total = len(self._claims)
        survived = sum(1 for c in self._claims.values() if c.survived)
        total_attacks = sum(len(a) for a in self._attacks.values())
        total_defenses = sum(len(d) for d in self._defenses.values())

        return {
            "total_claims": total,
            "survived": survived,
            "eliminated": total - survived,
            "survival_rate": survived / max(total, 1),
            "total_attacks": total_attacks,
            "total_defenses": total_defenses,
            "budget_used": {
                "rounds": self._budget.current_round,
                "attacks": self._budget.attacks_used,
                "defenses": self._budget.defenses_used,
            },
            "budget_remaining": {
                "rounds": self._budget.max_rounds - self._budget.current_round,
                "attacks": self._budget.max_total_attacks - self._budget.attacks_used,
                "defenses": self._budget.max_total_defenses - self._budget.defenses_used,
            },
        }
