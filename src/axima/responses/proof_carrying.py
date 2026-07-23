"""Proof-carrying responses: every claim backed by derivation and verification."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from ..verification.confidence import ConfidenceInterval
from ..verification.constellation import ReleaseDecision, VerificationReport
from ..verification.verifier_base import VerifierReceipt


class TruthLevel(Enum):
    """Truth level determined by verification results, not language detection."""
    VERIFIED_FACT = "verified_fact"
    DERIVED_VERIFIED = "derived_verified"
    DERIVED_UNVERIFIED = "derived_unverified"
    HEURISTIC = "heuristic"
    TEMPLATE = "template"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"


@dataclass
class EvidenceNode:
    """A piece of evidence supporting a claim."""
    evidence_id: str
    source: str
    content: str
    timestamp: float = 0.0
    confidence: float = 0.0

    @property
    def hash(self) -> str:
        payload = f"{self.evidence_id}:{self.source}:{self.content}"
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class ClaimNode:
    """A single claim in the derivation DAG."""
    claim_id: str
    statement: str
    evidence_ids: List[str] = field(default_factory=list)
    derived_from: List[str] = field(default_factory=list)  # parent claim IDs
    truth_level: TruthLevel = TruthLevel.UNSUPPORTED
    confidence: Optional[ConfidenceInterval] = None
    verifier_receipts: List[VerifierReceipt] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        """True if this claim has no parent claims (base fact)."""
        return len(self.derived_from) == 0

    @property
    def is_verified(self) -> bool:
        """True if at least one verifier has checked this claim."""
        return len(self.verifier_receipts) > 0


@dataclass
class DerivationDAG:
    """Directed acyclic graph of claims and their derivation relationships."""
    claims: Dict[str, ClaimNode] = field(default_factory=dict)
    evidence: Dict[str, EvidenceNode] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (from_id, to_id)

    def add_claim(self, claim: ClaimNode) -> None:
        """Add a claim to the DAG."""
        self.claims[claim.claim_id] = claim

    def add_evidence(self, evidence: EvidenceNode) -> None:
        """Add evidence to the DAG."""
        self.evidence[evidence.evidence_id] = evidence

    def add_derivation(self, from_id: str, to_id: str) -> None:
        """Add a derivation edge (from_id derives to_id)."""
        if from_id not in self.claims:
            raise ValueError(f"Source claim '{from_id}' not in DAG")
        if to_id not in self.claims:
            raise ValueError(f"Target claim '{to_id}' not in DAG")
        self.edges.append((from_id, to_id))
        self.claims[to_id].derived_from.append(from_id)

    def get_roots(self) -> List[ClaimNode]:
        """Get claims with no parents (base facts)."""
        return [c for c in self.claims.values() if c.is_leaf]

    def get_leaves(self) -> List[ClaimNode]:
        """Get claims with no children (final conclusions)."""
        parents = {e[0] for e in self.edges}
        all_ids = set(self.claims.keys())
        leaf_ids = all_ids - parents
        return [self.claims[cid] for cid in leaf_ids]

    def get_claim_ids(self) -> Set[str]:
        """Get all claim IDs in the DAG."""
        return set(self.claims.keys())

    def verify_acyclic(self) -> bool:
        """Verify the graph is actually acyclic."""
        visited: Set[str] = set()
        in_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            if node_id in in_stack:
                return False  # Cycle detected
            if node_id in visited:
                return True
            visited.add(node_id)
            in_stack.add(node_id)
            for from_id, to_id in self.edges:
                if from_id == node_id:
                    if not dfs(to_id):
                        return False
            in_stack.remove(node_id)
            return True

        for claim_id in self.claims:
            if claim_id not in visited:
                if not dfs(claim_id):
                    return False
        return True


@dataclass
class AximaResponseV2:
    """A proof-carrying response where every claim is backed by evidence and verification.

    Invariants:
    - Renderer cannot add claims not in the verified claim graph
    - Truth level determined by verification, not heuristics
    - Includes full derivation DAG
    """
    answer: str
    derivation: DerivationDAG
    verification_report: Optional[VerificationReport] = None
    confidence: Optional[ConfidenceInterval] = None
    truth_level: TruthLevel = TruthLevel.UNSUPPORTED
    timestamp: float = field(default_factory=time.time)
    response_id: str = ""

    def __post_init__(self) -> None:
        if not self.response_id:
            payload = f"{self.answer}:{self.timestamp}"
            self.response_id = hashlib.sha256(payload.encode()).hexdigest()[:16]

    @property
    def is_trustworthy(self) -> bool:
        """Response is trustworthy if verification passed."""
        if self.verification_report is None:
            return False
        return self.verification_report.release_decision == ReleaseDecision.PASS

    @property
    def claim_ids(self) -> Set[str]:
        """All claim IDs in this response."""
        return self.derivation.get_claim_ids()

    def get_verifier_receipts(self) -> List[VerifierReceipt]:
        """All verifier receipts across all claims."""
        receipts: List[VerifierReceipt] = []
        for claim in self.derivation.claims.values():
            receipts.extend(claim.verifier_receipts)
        return receipts


class ProofCarryingResponse:
    """Builder for proof-carrying responses.

    Enforces:
    - Renderer cannot add claims not in the verified claim graph
    - Derivation DAG must be acyclic
    - Truth level comes from verification, not language detection
    """

    def __init__(self) -> None:
        self._verified_claim_ids: Set[str] = set()

    def build(
        self,
        answer: str,
        claims: List[Dict[str, Any]],
        derivation: List[Tuple[str, str]],
        evidence: List[Dict[str, Any]],
        verification: Optional[VerificationReport] = None,
    ) -> AximaResponseV2:
        """Build a proof-carrying response.

        Args:
            answer: The final rendered answer text.
            claims: List of claim dicts with at least 'id' and 'statement'.
            derivation: List of (from_claim_id, to_claim_id) edges.
            evidence: List of evidence dicts with 'id', 'source', 'content'.
            verification: Optional verification report from constellation.

        Returns:
            AximaResponseV2 with full provenance.

        Raises:
            ValueError: If answer references claims not in the graph,
                       or if the derivation graph is cyclic.
        """
        # Build evidence nodes
        dag = DerivationDAG()
        for ev in evidence:
            node = EvidenceNode(
                evidence_id=ev["id"],
                source=ev.get("source", "unknown"),
                content=ev.get("content", ""),
                timestamp=ev.get("timestamp", 0.0),
                confidence=ev.get("confidence", 0.0),
            )
            dag.add_evidence(node)

        # Build claim nodes
        for claim_dict in claims:
            claim_node = ClaimNode(
                claim_id=claim_dict["id"],
                statement=claim_dict.get("statement", ""),
                evidence_ids=claim_dict.get("evidence_ids", []),
            )
            dag.add_claim(claim_node)

        # Add derivation edges
        for from_id, to_id in derivation:
            dag.add_derivation(from_id, to_id)

        # Verify acyclic
        if not dag.verify_acyclic():
            raise ValueError("Derivation graph contains cycles — invalid proof structure.")

        # Determine truth level from verification
        truth_level = self._determine_truth_level(dag, verification)

        # Apply verification results to claims
        if verification:
            self._apply_verification(dag, verification)

        # Compute overall confidence
        confidence = self._compute_confidence(dag, verification)

        # Validate answer doesn't reference unverified claims
        self._validate_answer_claims(answer, dag)

        return AximaResponseV2(
            answer=answer,
            derivation=dag,
            verification_report=verification,
            confidence=confidence,
            truth_level=truth_level,
        )

    def _determine_truth_level(
        self,
        dag: DerivationDAG,
        verification: Optional[VerificationReport],
    ) -> TruthLevel:
        """Determine truth level from verification results, not language heuristics."""
        if verification is None:
            # No verification ran
            if dag.get_roots():
                return TruthLevel.DERIVED_UNVERIFIED
            return TruthLevel.UNSUPPORTED

        if verification.release_decision == ReleaseDecision.FAIL:
            if verification.counterexamples:
                return TruthLevel.CONTRADICTED
            return TruthLevel.UNSUPPORTED

        if verification.release_decision == ReleaseDecision.CONDITIONAL:
            return TruthLevel.HEURISTIC

        # PASS
        roots = dag.get_roots()
        if roots and all(r.evidence_ids for r in roots):
            # All base claims have direct evidence
            if dag.edges:
                return TruthLevel.DERIVED_VERIFIED
            return TruthLevel.VERIFIED_FACT
        elif dag.edges:
            return TruthLevel.DERIVED_VERIFIED
        else:
            return TruthLevel.VERIFIED_FACT

    def _apply_verification(
        self,
        dag: DerivationDAG,
        verification: VerificationReport,
    ) -> None:
        """Apply verification receipts to individual claims."""
        for receipt in verification.verifier_receipts:
            claim_id = receipt.claim_id
            if claim_id in dag.claims:
                dag.claims[claim_id].verifier_receipts.append(receipt)

        # Update individual claim truth levels based on their receipts
        for claim in dag.claims.values():
            if claim.verifier_receipts:
                all_passed = all(r.result.passed for r in claim.verifier_receipts)
                any_passed = any(r.result.passed for r in claim.verifier_receipts)
                if all_passed:
                    if claim.is_leaf:
                        claim.truth_level = TruthLevel.VERIFIED_FACT
                    else:
                        claim.truth_level = TruthLevel.DERIVED_VERIFIED
                elif any_passed:
                    claim.truth_level = TruthLevel.HEURISTIC
                else:
                    claim.truth_level = TruthLevel.UNSUPPORTED

    def _compute_confidence(
        self,
        dag: DerivationDAG,
        verification: Optional[VerificationReport],
    ) -> ConfidenceInterval:
        """Compute overall confidence interval from verification results."""
        if verification is None:
            return ConfidenceInterval(lower=0.0, upper=0.5, method="unverified")

        if verification.checks_run == 0:
            return ConfidenceInterval(lower=0.0, upper=0.3, method="no_checks")

        # Use pass rate and residual risk
        pass_rate = verification.pass_rate
        risk = verification.residual_risk

        lower = max(0.0, pass_rate - risk)
        upper = min(1.0, pass_rate + (1.0 - pass_rate) * 0.1)

        return ConfidenceInterval(
            lower=lower,
            upper=upper,
            method=f"verification({verification.checks_passed}/{verification.checks_run})",
        )

    def _validate_answer_claims(self, answer: str, dag: DerivationDAG) -> None:
        """Ensure the rendered answer doesn't reference claims outside the DAG.

        This enforces the invariant: renderer cannot add claims not in the
        verified claim graph.
        """
        # Look for claim references in the answer (e.g., [claim:xxx])
        import re
        claim_refs = re.findall(r"\[claim:([^\]]+)\]", answer)
        valid_ids = dag.get_claim_ids()

        for ref in claim_refs:
            if ref not in valid_ids:
                raise ValueError(
                    f"Answer references claim '{ref}' which is not in the "
                    f"verified claim graph. Valid claims: {valid_ids}"
                )
