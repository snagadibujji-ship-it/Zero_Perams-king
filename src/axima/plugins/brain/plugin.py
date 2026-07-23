"""Brain Plugin — wraps brain_* modules for document Q&A.

Adds document citation tracking on top of the document
ingestion and reasoning pipeline.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR
from ..base import PluginBase

logger = logging.getLogger(__name__)

_LEGACY_DIR = Path(__file__).parent.parent.parent.parent.parent / "python"


@dataclass
class DocumentCitation:
    """A citation to a specific location in a document."""

    document_id: str
    document_name: str
    section: str = ""
    page: Optional[int] = None
    paragraph: Optional[int] = None
    text_excerpt: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_name": self.document_name,
            "section": self.section,
            "page": self.page,
            "paragraph": self.paragraph,
            "text_excerpt": self.text_excerpt,
            "confidence": self.confidence,
        }


class BrainPlugin(PluginBase):
    """Document Q&A with citation tracking.

    Wraps the brain_ingest, brain_reason, brain_study, brain_compute,
    brain_cross, and brain_tracker modules.
    """

    def __init__(self) -> None:
        self._ingest = None
        self._reason = None
        self._study = None
        self._healthy = False
        self._citations: List[DocumentCitation] = []

    def name(self) -> str:
        return "brain"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["document", "brain", "study", "research"],
            produced_types=["answer", "citation", "summary"],
            preconditions=["documents_ingested"],
            postconditions=["document_answer"],
            cost_model={"avg_ms": 300, "max_ms": 10000},
            latency_model={"avg_ms": 300, "p95_ms": 5000},
            deterministic=True,
            permissions=["read"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Query ingested documents and return answers with citations."""
        start = time.time()
        self._citations.clear()

        # Extract the query
        query = self._extract_query(ir)
        if not query:
            return ExecutionResult(
                status="error",
                error="Could not extract query for document search",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Query the brain modules
        result = self._query_brain(query)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            citations_str = [
                f"[{c.document_name}:{c.section}]" for c in self._citations
            ]

            return ExecutionResult(
                answer=result.get("answer", ""),
                status="success",
                claims=result.get("claims", [f"Found in documents: {query}"]),
                evidence=citations_str or ["brain_modules"],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"No document answer found for: {query}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if brain modules are available."""
        try:
            self._load_modules()
            self._healthy = self._reason is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_modules()

    # --- Citation Tracking ---

    def get_citations(self) -> List[DocumentCitation]:
        """Get citations from the last query."""
        return list(self._citations)

    def clear_citations(self) -> None:
        """Clear citation history."""
        self._citations.clear()

    # --- Internal Methods ---

    def _extract_query(self, ir: MeaningIR) -> Optional[str]:
        """Extract document query from IR."""
        for goal in ir.goals:
            if goal.description:
                return goal.description

        for pred in ir.predicates:
            return f"{pred.subject} {pred.relation} {pred.object}"

        if ir.entities:
            return f"information about {ir.entities[0].name}"

        return None

    def _query_brain(self, query: str) -> Optional[Dict[str, Any]]:
        """Query the brain reasoning modules."""
        try:
            self._load_modules()
            if self._reason is not None:
                result = self._reason.query(query)
                if result:
                    # Track citations
                    if isinstance(result, dict):
                        for source in result.get("sources", []):
                            self._citations.append(
                                DocumentCitation(
                                    document_id=source.get("id", "unknown"),
                                    document_name=source.get("name", "unknown"),
                                    section=source.get("section", ""),
                                    text_excerpt=source.get("excerpt", ""),
                                    confidence=source.get("confidence", 0.8),
                                )
                            )
                        return {
                            "answer": result.get("answer", str(result)),
                            "claims": [f"Document answer: {query}"],
                        }
                    return {"answer": str(result), "claims": [f"Found: {query}"]}
        except Exception as exc:
            logger.debug(f"Brain query failed: {exc}")
        return None

    def _load_modules(self) -> None:
        """Load brain modules from legacy code."""
        legacy_dir = str(_LEGACY_DIR)
        if legacy_dir not in sys.path:
            sys.path.insert(0, legacy_dir)

        if self._reason is None:
            try:
                import brain_reason
                self._reason = brain_reason
            except ImportError:
                logger.debug("brain_reason not available")

        if self._ingest is None:
            try:
                import brain_ingest
                self._ingest = brain_ingest
            except ImportError:
                logger.debug("brain_ingest not available")

        if self._study is None:
            try:
                import brain_study
                self._study = brain_study
            except ImportError:
                logger.debug("brain_study not available")
