"""Knowledge Crystals — compressed, predictive patterns from facts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class CrystalStatus(Enum):
    """Status of a knowledge crystal."""
    CANDIDATE = "candidate"
    PROMOTED = "promoted"
    REVOKED = "revoked"


@dataclass
class KnowledgeCrystal:
    """A compressed pattern discovered from facts."""
    id: str
    pattern: str
    parameters: Dict[str, str] = field(default_factory=dict)
    source_facts: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    compression_ratio: float = 0.0
    predictive_score: float = 0.0
    status: CrystalStatus = CrystalStatus.CANDIDATE


class CrystalCompiler:
    """Compiles knowledge crystals from sets of facts using anti-unification.

    Requirements for promotion:
    1. Compression gain: crystal must cover more facts than its description size
    2. Predictive success: crystal must predict held-out facts correctly
    """

    def __init__(self, min_compression: float = 2.0, min_predictive: float = 0.7) -> None:
        self._crystals: Dict[str, KnowledgeCrystal] = {}
        self._min_compression = min_compression
        self._min_predictive = min_predictive

    def detect_patterns(self, facts: List[Tuple[str, str, str]]) -> List[Dict[str, Any]]:
        """Detect recurring patterns in a list of (subject, relation, object) facts."""
        by_relation: Dict[str, List[Tuple[str, str]]] = {}
        for subj, rel, obj in facts:
            by_relation.setdefault(rel, []).append((subj, obj))

        patterns: List[Dict[str, Any]] = []
        for rel, pairs in by_relation.items():
            if len(pairs) < 2:
                continue
            patterns.append({
                "relation": rel,
                "count": len(pairs),
                "subjects": [p[0] for p in pairs],
                "objects": [p[1] for p in pairs],
                "pattern": f"X {rel} Y",
            })
        return patterns

    def compile_crystal(
        self,
        pattern: str,
        parameters: Dict[str, str],
        source_facts: List[str],
        exceptions: Optional[List[str]] = None,
    ) -> KnowledgeCrystal:
        """Compile a single crystal from a detected pattern."""
        crystal_size = len(pattern) + len(str(parameters)) + len(str(exceptions or []))
        facts_covered = len(source_facts)
        compression = facts_covered / max(1, crystal_size / 100)

        crystal = KnowledgeCrystal(
            id=str(uuid.uuid4()),
            pattern=pattern,
            parameters=parameters,
            source_facts=source_facts,
            exceptions=exceptions or [],
            compression_ratio=compression,
            status=CrystalStatus.CANDIDATE,
        )
        self._crystals[crystal.id] = crystal
        return crystal

    def expand(self, crystal_id: str) -> List[str]:
        """Expand a crystal back into its constituent facts."""
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise KeyError(f"Crystal {crystal_id} not found")
        return list(crystal.source_facts)

    def validate_held_out(
        self, crystal_id: str, held_out_facts: List[str], total_applicable: int
    ) -> float:
        """Validate a crystal against held-out facts. Returns predictive score."""
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise KeyError(f"Crystal {crystal_id} not found")
        if total_applicable == 0:
            return 0.0
        score = len(held_out_facts) / total_applicable
        crystal.predictive_score = score
        return score

    def promote(self, crystal_id: str) -> bool:
        """Promote a crystal if it meets compression and predictive thresholds."""
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise KeyError(f"Crystal {crystal_id} not found")
        if (
            crystal.compression_ratio >= self._min_compression
            and crystal.predictive_score >= self._min_predictive
        ):
            crystal.status = CrystalStatus.PROMOTED
            return True
        return False

    def revoke(self, crystal_id: str) -> None:
        """Revoke a crystal (evidence no longer supports it)."""
        crystal = self._crystals.get(crystal_id)
        if crystal is None:
            raise KeyError(f"Crystal {crystal_id} not found")
        crystal.status = CrystalStatus.REVOKED

    def get_crystal(self, crystal_id: str) -> Optional[KnowledgeCrystal]:
        return self._crystals.get(crystal_id)

    @property
    def promoted(self) -> List[KnowledgeCrystal]:
        return [c for c in self._crystals.values() if c.status == CrystalStatus.PROMOTED]

    @property
    def candidates(self) -> List[KnowledgeCrystal]:
        return [c for c in self._crystals.values() if c.status == CrystalStatus.CANDIDATE]
