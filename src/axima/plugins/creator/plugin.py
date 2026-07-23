"""Creator Plugin — wraps creator/engine_v3 for content generation.

Adds narrative state tracking on top of the grammar-based
content generation engine.
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
class NarrativeState:
    """Tracks the state of an ongoing narrative generation."""

    genre: str = "general"
    tone: str = "neutral"
    characters: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    arc_position: str = "beginning"  # beginning, rising, climax, falling, resolution
    word_count: int = 0
    segments_generated: int = 0


class CreatorPlugin(PluginBase):
    """Content generation (stories, songs, poems) with narrative state tracking."""

    def __init__(self) -> None:
        self._engine = None
        self._healthy = False
        self._narrative_states: Dict[str, NarrativeState] = {}

    def name(self) -> str:
        return "creator"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["creative", "story", "poem", "song", "content"],
            produced_types=["creative_text", "narrative"],
            preconditions=[],
            postconditions=["generated_content"],
            cost_model={"avg_ms": 200, "max_ms": 5000},
            latency_model={"avg_ms": 200, "p95_ms": 2000},
            deterministic=False,
            permissions=["read"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Generate creative content from the MeaningIR."""
        start = time.time()

        # Extract generation parameters
        params = self._extract_params(ir)
        if not params:
            return ExecutionResult(
                status="error",
                error="Could not determine content generation parameters",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        content_type = params.get("type", "story")
        topic = params.get("topic", "")

        # Create or retrieve narrative state
        state_key = f"{content_type}_{topic[:20]}"
        state = self._narrative_states.get(state_key, NarrativeState(genre=content_type))

        # Generate content
        result = self._generate(content_type, topic, params, state)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            # Update narrative state
            state.segments_generated += 1
            state.word_count += len(result.split())
            self._narrative_states[state_key] = state

            return ExecutionResult(
                answer=result,
                status="success",
                claims=[f"Generated {content_type}: {topic}"],
                evidence=["creator_engine_v3"],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"Content generation failed for: {content_type} about {topic}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if the creator engine is available."""
        try:
            self._load_engine()
            self._healthy = self._engine is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_engine()

    # --- Narrative State ---

    def get_narrative_state(self, key: str) -> Optional[NarrativeState]:
        """Get the narrative state for a given content stream."""
        return self._narrative_states.get(key)

    def reset_narrative(self, key: str) -> None:
        """Reset a narrative state."""
        self._narrative_states.pop(key, None)

    # --- Internal Methods ---

    def _extract_params(self, ir: MeaningIR) -> Optional[Dict[str, Any]]:
        """Extract content generation parameters from IR."""
        params: Dict[str, Any] = {}

        # Detect content type from goals
        for goal in ir.goals:
            desc = goal.description.lower()
            if "poem" in desc:
                params["type"] = "poem"
            elif "song" in desc:
                params["type"] = "song"
            elif "story" in desc:
                params["type"] = "story"
            else:
                params["type"] = "story"
            params["topic"] = goal.description
            params["constraints"] = goal.constraints
            break

        # Check events
        if not params:
            for event in ir.events:
                if event.verb in ("write", "compose", "create", "imagine"):
                    params["type"] = "story"
                    params["topic"] = event.patient or ""
                    break

        if not params:
            return None

        # Extract characters from entities
        params["characters"] = [
            e.name for e in ir.entities if e.type in ("person", "character")
        ]

        # Extract themes from predicates
        params["themes"] = [
            pred.object for pred in ir.predicates
            if pred.relation in ("about", "theme", "involves")
        ]

        return params

    def _generate(
        self,
        content_type: str,
        topic: str,
        params: Dict[str, Any],
        state: NarrativeState,
    ) -> Optional[str]:
        """Generate content using the creator engine."""
        try:
            self._load_engine()
            if self._engine is not None:
                result = self._engine.generate(
                    content_type=content_type,
                    topic=topic,
                )
                if result:
                    return result if isinstance(result, str) else str(result)
        except Exception as exc:
            logger.debug(f"Creator generation failed: {exc}")
        return None

    def _load_engine(self) -> None:
        """Load the creator engine from legacy code."""
        if self._engine is not None:
            return
        try:
            legacy_dir = str(_LEGACY_DIR)
            if legacy_dir not in sys.path:
                sys.path.insert(0, legacy_dir)
            from creator.engine_v3 import CreatorEngine
            self._engine = CreatorEngine()
        except ImportError:
            logger.debug("creator.engine_v3 not available")
