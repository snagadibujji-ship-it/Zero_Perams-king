"""Provenance tracking — source tiers, evidence records, and integrity verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple


class SourceTier(Enum):
    """Tier classification for evidence sources."""
    T0_VERIFIED = "t0_verified"
    T1_AUTHORITATIVE = "t1_authoritative"
    T2_SECONDARY = "t2_secondary"
    T3_USER = "t3_user"
    T4_GENERATED = "t4_generated"


@dataclass
class EvidenceRecord:
    """A single piece of evidence linking a source to a claim."""
    evidence_id: str
    claim_id: str
    source_uri: str
    source_hash: str
    source_tier: SourceTier
    extraction_method: str
    valid_time: Tuple[Optional[datetime], Optional[datetime]] = (None, None)
    observed_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    independence_group: str = ""
    supports_or_refutes: bool = True  # True = supports, False = refutes
    confidence: float = 0.5
    license: str = "unknown"


class ProvenanceStore:
    """In-memory store for evidence records with integrity verification."""

    def __init__(self) -> None:
        self._records: Dict[str, EvidenceRecord] = {}
        self._by_claim: Dict[str, List[str]] = {}
        self._by_source: Dict[str, List[str]] = {}

    def add(self, record: EvidenceRecord) -> EvidenceRecord:
        """Add an evidence record to the store."""
        if record.evidence_id in self._records:
            raise ValueError(f"Evidence {record.evidence_id} already exists")
        self._records[record.evidence_id] = record
        self._by_claim.setdefault(record.claim_id, []).append(record.evidence_id)
        self._by_source.setdefault(record.source_uri, []).append(record.evidence_id)
        return record

    def query_for_claim(self, claim_id: str) -> List[EvidenceRecord]:
        """Return all evidence records for a given claim."""
        ids = self._by_claim.get(claim_id, [])
        return [self._records[eid] for eid in ids]

    def get_by_source(self, source_uri: str) -> List[EvidenceRecord]:
        """Return all evidence records from a given source URI."""
        ids = self._by_source.get(source_uri, [])
        return [self._records[eid] for eid in ids]

    def get(self, evidence_id: str) -> Optional[EvidenceRecord]:
        """Get a single evidence record by ID."""
        return self._records.get(evidence_id)

    def verify_integrity(self) -> List[str]:
        """Verify internal consistency. Returns list of issues found."""
        issues: List[str] = []
        # Check index consistency
        for claim_id, eids in self._by_claim.items():
            for eid in eids:
                if eid not in self._records:
                    issues.append(f"Orphan index entry: claim {claim_id} -> evidence {eid}")
                elif self._records[eid].claim_id != claim_id:
                    issues.append(
                        f"Mismatched claim index: {eid} indexed under {claim_id} "
                        f"but record says {self._records[eid].claim_id}"
                    )
        for source_uri, eids in self._by_source.items():
            for eid in eids:
                if eid not in self._records:
                    issues.append(f"Orphan source index: {source_uri} -> {eid}")
        return issues

    @property
    def count(self) -> int:
        return len(self._records)
