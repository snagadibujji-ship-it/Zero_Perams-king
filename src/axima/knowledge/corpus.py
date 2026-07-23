"""Corpus ingestion and manifest tracking."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Tuple


@dataclass
class CorpusManifest:
    """Manifest describing the state of an imported corpus."""
    sources: List[str] = field(default_factory=list)
    total_records: int = 0
    unique_facts: int = 0
    accepted: int = 0
    rejected: int = 0
    duplicates: int = 0
    graph_hash: str = ""
    built_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ImportRecord:
    """Internal record of a single imported item."""
    subject: str
    relation: str
    obj: str
    source: str
    raw_hash: str


class CorpusImporter:
    """Imports knowledge from various formats into a unified representation.

    Tracks file hashes, parser versions, and record counts.
    """

    PARSER_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._records: List[ImportRecord] = []
        self._seen_hashes: set = set()
        self._sources: List[str] = []
        self._rejected: int = 0
        self._duplicates: int = 0

    def _hash_record(self, subject: str, relation: str, obj: str) -> str:
        content = f"{subject}|{relation}|{obj}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _add_record(self, subject: str, relation: str, obj: str, source: str) -> bool:
        """Add a record. Returns True if accepted, False if duplicate/rejected."""
        if not subject or not relation or not obj:
            self._rejected += 1
            return False
        h = self._hash_record(subject, relation, obj)
        if h in self._seen_hashes:
            self._duplicates += 1
            return False
        self._seen_hashes.add(h)
        self._records.append(ImportRecord(
            subject=subject, relation=relation, obj=obj, source=source, raw_hash=h
        ))
        return True

    def import_csv(self, lines: List[str], source: str = "csv") -> int:
        """Import from CSV lines (subject,relation,object format)."""
        if source not in self._sources:
            self._sources.append(source)
        count = 0
        for line in lines:
            parts = line.strip().split(",", 2)
            if len(parts) == 3:
                if self._add_record(parts[0].strip(), parts[1].strip(), parts[2].strip(), source):
                    count += 1
        return count

    def import_triples(self, triples: List[Tuple[str, str, str]], source: str = "triples") -> int:
        """Import from a list of (subject, relation, object) tuples."""
        if source not in self._sources:
            self._sources.append(source)
        count = 0
        for subj, rel, obj in triples:
            if self._add_record(subj, rel, obj, source):
                count += 1
        return count

    def import_json(self, data: List[Dict[str, str]], source: str = "json") -> int:
        """Import from list of dicts with 'subject', 'relation', 'object' keys."""
        if source not in self._sources:
            self._sources.append(source)
        count = 0
        for item in data:
            subj = item.get("subject", "")
            rel = item.get("relation", "")
            obj = item.get("object", "")
            if self._add_record(subj, rel, obj, source):
                count += 1
        return count

    def build_manifest(self) -> CorpusManifest:
        """Build and return the corpus manifest."""
        combined = "".join(sorted(r.raw_hash for r in self._records))
        graph_hash = hashlib.sha256(combined.encode()).hexdigest() if combined else ""

        return CorpusManifest(
            sources=list(self._sources),
            total_records=len(self._records) + self._rejected + self._duplicates,
            unique_facts=len(self._records),
            accepted=len(self._records),
            rejected=self._rejected,
            duplicates=self._duplicates,
            graph_hash=graph_hash,
            built_at=datetime.now(timezone.utc),
        )

    @property
    def records(self) -> List[ImportRecord]:
        return list(self._records)
