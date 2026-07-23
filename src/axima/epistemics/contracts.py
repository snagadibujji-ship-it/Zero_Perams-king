"""Epistemic Contract Compiler — determines what kind of answer a query demands."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AnswerKind(Enum):
    """The type of answer expected."""
    FACT = "fact"
    DERIVATION = "derivation"
    ESTIMATE = "estimate"
    PROOF = "proof"
    PLAN = "plan"
    ACTION = "action"
    CREATIVE = "creative"
    CLARIFICATION = "clarification"


class EvidenceRequirement(Enum):
    """Required evidence level for the answer."""
    NONE = "none"
    HEURISTIC = "heuristic"
    SOURCED = "sourced"
    PROVEN = "proven"
    WITNESSED = "witnessed"


@dataclass
class EpistemicContract:
    """A contract specifying what kind of answer is required and how to verify it."""
    answer_kind: AnswerKind
    required_evidence: EvidenceRequirement
    allowed_inference_types: List[str] = field(default_factory=list)
    maximum_hops: int = 3
    freshness_requirement: Optional[str] = None  # e.g. "24h", "7d", None
    unit_requirement: Optional[str] = None
    verification_level: str = "standard"
    safety_class: str = "normal"
    confidence_floor: float = 0.5
    abstention_rule: str = "if_below_floor"
    output_schema: Optional[Dict[str, Any]] = None


# Keyword patterns for answer kind inference
_PROOF_PATTERNS = re.compile(r"\b(prove|proof|demonstrate|show that|QED)\b", re.I)
_ESTIMATE_PATTERNS = re.compile(r"\b(estimate|approximate|roughly|about how|ballpark)\b", re.I)
_FACT_PATTERNS = re.compile(r"\b(what is|what are|who is|who are|when did|where is|define|name)\b", re.I)
_DERIVATION_PATTERNS = re.compile(r"\b(derive|calculate|compute|solve|find the value|evaluate)\b", re.I)
_PLAN_PATTERNS = re.compile(r"\b(how to|how do|how can|steps to|plan for|strategy)\b", re.I)
_ACTION_PATTERNS = re.compile(r"\b(create|build|make|generate|write|implement|code)\b", re.I)
_CREATIVE_PATTERNS = re.compile(r"\b(write a (story|poem|song)|compose|imagine|invent)\b", re.I)
_CLARIFICATION_PATTERNS = re.compile(r"\b(what do you mean|clarify|explain what|which one)\b", re.I)

# Time-sensitivity patterns
_TIME_SENSITIVE_RE = re.compile(r"\b(today|now|current|latest|recent|this year|this month)\b", re.I)

# Unit requirement patterns
_UNIT_REQ_RE = re.compile(r"\b(in (?:meters|kg|seconds|miles|celsius|fahrenheit|dollars|euros|percent))\b", re.I)

# Safety-critical patterns
_SAFETY_RE = re.compile(
    r"\b(medical|drug|dosage|voltage|toxic|poison|explosive|radiation|surgery|legal)\b", re.I
)


class ContractCompiler:
    """Compiles a query into an EpistemicContract.

    Analyzes the query to determine what kind of answer is expected,
    what evidence level is required, and what constraints apply.
    """

    def compile(self, query: str, context: Optional[Dict[str, Any]] = None) -> EpistemicContract:
        """Compile a query into an epistemic contract."""
        context = context or {}

        answer_kind = self._infer_answer_kind(query)
        evidence = self._infer_evidence_requirement(answer_kind, query)
        inference_types = self._infer_allowed_inferences(answer_kind)
        max_hops = self._infer_max_hops(answer_kind)
        freshness = self._detect_freshness(query)
        unit_req = self._detect_unit_requirement(query)
        safety = self._detect_safety_class(query)
        confidence_floor = self._compute_confidence_floor(answer_kind, safety)

        return EpistemicContract(
            answer_kind=answer_kind,
            required_evidence=evidence,
            allowed_inference_types=inference_types,
            maximum_hops=max_hops,
            freshness_requirement=freshness,
            unit_requirement=unit_req,
            verification_level="rigorous" if safety == "critical" else "standard",
            safety_class=safety,
            confidence_floor=confidence_floor,
            abstention_rule="always_abstain" if safety == "critical" else "if_below_floor",
            output_schema=context.get("output_schema"),
        )

    def _infer_answer_kind(self, query: str) -> AnswerKind:
        """Infer the expected answer kind from query keywords."""
        if _PROOF_PATTERNS.search(query):
            return AnswerKind.PROOF
        if _CREATIVE_PATTERNS.search(query):
            return AnswerKind.CREATIVE
        if _CLARIFICATION_PATTERNS.search(query):
            return AnswerKind.CLARIFICATION
        if _DERIVATION_PATTERNS.search(query):
            return AnswerKind.DERIVATION
        if _ESTIMATE_PATTERNS.search(query):
            return AnswerKind.ESTIMATE
        if _PLAN_PATTERNS.search(query):
            return AnswerKind.PLAN
        if _ACTION_PATTERNS.search(query):
            return AnswerKind.ACTION
        if _FACT_PATTERNS.search(query):
            return AnswerKind.FACT
        return AnswerKind.FACT  # default

    def _infer_evidence_requirement(self, kind: AnswerKind, query: str) -> EvidenceRequirement:
        """Determine evidence level from answer kind."""
        evidence_map = {
            AnswerKind.PROOF: EvidenceRequirement.PROVEN,
            AnswerKind.FACT: EvidenceRequirement.SOURCED,
            AnswerKind.DERIVATION: EvidenceRequirement.SOURCED,
            AnswerKind.ESTIMATE: EvidenceRequirement.HEURISTIC,
            AnswerKind.PLAN: EvidenceRequirement.HEURISTIC,
            AnswerKind.ACTION: EvidenceRequirement.NONE,
            AnswerKind.CREATIVE: EvidenceRequirement.NONE,
            AnswerKind.CLARIFICATION: EvidenceRequirement.NONE,
        }
        return evidence_map.get(kind, EvidenceRequirement.HEURISTIC)

    def _infer_allowed_inferences(self, kind: AnswerKind) -> List[str]:
        """Determine which inference types are allowed."""
        inference_map = {
            AnswerKind.PROOF: ["deduction"],
            AnswerKind.FACT: ["lookup", "deduction"],
            AnswerKind.DERIVATION: ["deduction", "calculation"],
            AnswerKind.ESTIMATE: ["deduction", "induction", "analogy"],
            AnswerKind.PLAN: ["deduction", "induction", "analogy", "abduction"],
            AnswerKind.ACTION: ["deduction", "pattern_matching"],
            AnswerKind.CREATIVE: ["analogy", "pattern_matching", "generation"],
            AnswerKind.CLARIFICATION: ["lookup"],
        }
        return inference_map.get(kind, ["deduction"])

    def _infer_max_hops(self, kind: AnswerKind) -> int:
        """Maximum inference hops allowed."""
        hop_map = {
            AnswerKind.FACT: 2,
            AnswerKind.PROOF: 10,
            AnswerKind.DERIVATION: 5,
            AnswerKind.ESTIMATE: 3,
            AnswerKind.PLAN: 5,
            AnswerKind.ACTION: 3,
            AnswerKind.CREATIVE: 1,
            AnswerKind.CLARIFICATION: 1,
        }
        return hop_map.get(kind, 3)

    def _detect_freshness(self, query: str) -> Optional[str]:
        """Detect if the query requires fresh/current information."""
        if _TIME_SENSITIVE_RE.search(query):
            return "24h"
        return None

    def _detect_unit_requirement(self, query: str) -> Optional[str]:
        """Detect if specific units are requested."""
        match = _UNIT_REQ_RE.search(query)
        if match:
            return match.group(1).replace("in ", "")
        return None

    def _detect_safety_class(self, query: str) -> str:
        """Detect if the query involves safety-critical domains."""
        if _SAFETY_RE.search(query):
            return "critical"
        return "normal"

    def _compute_confidence_floor(self, kind: AnswerKind, safety: str) -> float:
        """Compute minimum confidence threshold."""
        base = {
            AnswerKind.PROOF: 0.99,
            AnswerKind.FACT: 0.8,
            AnswerKind.DERIVATION: 0.85,
            AnswerKind.ESTIMATE: 0.4,
            AnswerKind.PLAN: 0.6,
            AnswerKind.ACTION: 0.7,
            AnswerKind.CREATIVE: 0.3,
            AnswerKind.CLARIFICATION: 0.5,
        }.get(kind, 0.5)

        if safety == "critical":
            base = max(base, 0.95)

        return base
