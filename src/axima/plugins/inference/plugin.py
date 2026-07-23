"""Inference Plugin — wraps inference_engine with evidence tracking.

Adds evidence tracking and source citations on top of the
knowledge graph inference engine.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract, EvidenceRequirement
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR
from ..base import PluginBase

logger = logging.getLogger(__name__)

_LEGACY_DIR = Path(__file__).parent.parent.parent.parent.parent / "python"


@dataclass
class EvidenceRecord:
    """A single piece of evidence supporting an inference."""

    source: str
    fact: str
    confidence: float = 1.0
    hop_count: int = 0
    derivation_chain: List[str] = field(default_factory=list)


@dataclass
class Citation:
    """A citation to a knowledge base entry."""

    source_id: str
    source_type: str  # "knowledge_base", "derived", "heuristic"
    text: str
    confidence: float = 1.0


class InferencePlugin(PluginBase):
    """Knowledge graph inference with evidence tracking and citations."""

    def __init__(self) -> None:
        self._engine = None
        self._healthy = False
        self._evidence_log: List[EvidenceRecord] = []

    def name(self) -> str:
        return "inference_engine"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["inference", "knowledge", "fact", "reasoning"],
            produced_types=["fact", "derivation", "citation"],
            preconditions=[],
            postconditions=["factual_answer"],
            cost_model={"avg_ms": 80, "max_ms": 2000},
            latency_model={"avg_ms": 80, "p95_ms": 500},
            deterministic=True,
            permissions=["read"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Query the knowledge graph and return factual answers with citations."""
        start = time.time()

        # Extract the query from IR
        query = self._extract_query(ir)
        if not query:
            return ExecutionResult(
                status="error",
                error="Could not extract query from meaning representation",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Query the inference engine
        result = self._infer(query, contract)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            answer = result.get("answer", "")
            evidence = result.get("evidence", [])
            citations = result.get("citations", [])

            # Check if evidence meets contract requirements
            if contract.required_evidence == EvidenceRequirement.SOURCED and not citations:
                return ExecutionResult(
                    answer=answer,
                    status="success",
                    claims=[f"Answer: {answer} (evidence not fully sourced)"],
                    evidence=evidence,
                    engine=self.name(),
                    cost_ms=elapsed,
                )

            return ExecutionResult(
                answer=answer,
                status="success",
                claims=result.get("claims", []),
                evidence=evidence + [c for c in citations],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"No answer found for: {query}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if the inference engine is available."""
        try:
            self._load_engine()
            self._healthy = self._engine is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_engine()

    # --- Evidence Tracking ---

    def get_evidence_log(self) -> List[EvidenceRecord]:
        """Return the evidence log for the last inference."""
        return list(self._evidence_log)

    def clear_evidence_log(self) -> None:
        """Clear the evidence log."""
        self._evidence_log.clear()

    # --- Internal Methods ---

    def _extract_query(self, ir: MeaningIR) -> Optional[str]:
        """Extract a natural language query from the MeaningIR."""
        # Check goals
        for goal in ir.goals:
            if goal.description:
                return goal.description

        # Check predicates
        for pred in ir.predicates:
            if pred.relation in ("is", "has", "belongs_to"):
                return f"what {pred.relation} {pred.subject}"
            return f"{pred.subject} {pred.relation} {pred.object}"

        # Check entities
        if ir.entities:
            entity = ir.entities[0]
            return f"what is {entity.name}"

        return None

    def _infer(
        self, query: str, contract: EpistemicContract
    ) -> Optional[Dict[str, Any]]:
        """Run inference on the query."""
        self._evidence_log.clear()

        try:
            self._load_engine()
            if self._engine is not None:
                # Use the legacy inference engine
                result = self._engine.query(query)
                if result:
                    # Track evidence
                    if isinstance(result, dict):
                        for source in result.get("sources", []):
                            self._evidence_log.append(
                                EvidenceRecord(
                                    source=source,
                                    fact=query,
                                    confidence=result.get("confidence", 0.8),
                                )
                            )
                        return {
                            "answer": result.get("answer", str(result)),
                            "evidence": result.get("sources", []),
                            "citations": result.get("citations", []),
                            "claims": [f"Inferred: {query}"],
                        }
                    else:
                        return {
                            "answer": str(result),
                            "evidence": ["knowledge_base"],
                            "citations": [],
                            "claims": [f"Found: {query}"],
                        }
        except Exception as exc:
            logger.debug(f"Inference failed: {exc}")

        return None

    def _load_engine(self) -> None:
        """Load the inference engine from legacy code."""
        if self._engine is not None:
            return
        try:
            legacy_dir = str(_LEGACY_DIR)
            if legacy_dir not in sys.path:
                sys.path.insert(0, legacy_dir)
            import inference_engine
            self._engine = inference_engine
        except ImportError:
            logger.debug("inference_engine not available")
