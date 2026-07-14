"""
ACES v2 — Phase 10: Memory Versioning
Stores, recalls, and versions explanations. Prevents stale answers.
"""

import time
import json
import os
from typing import Optional, List, Dict
from .models import MeaningGraph, ReasonChain, ExplanationFrame, MemoryRecord


class Memory:
    """Versioned explanation memory. Remembers without becoming stale."""

    VERSION = 2  # Increment to invalidate old memories

    def __init__(self, persist_path: str = "user_data/aces_memory"):
        self.records: Dict[str, MemoryRecord] = {}
        self.persist_path = persist_path
        self._load()

    def store(self, topic: str, graph: MeaningGraph,
              chain: ReasonChain, frame: ExplanationFrame):
        """Store an explanation for future recall."""
        key = self._normalize_key(topic)

        # Check if we already have a record
        existing = self.records.get(key)
        if existing and not existing.superseded:
            # Increment version
            existing.version += 1
            existing.superseded = True

        # Create new record
        record = MemoryRecord(
            topic=topic,
            version=self.VERSION,
            graph=graph,
            chain=chain,
            best_mode=frame.mode,
            confidence=0.8,
            times_used=1,
            last_used=time.time(),
            superseded=False,
        )
        self.records[key] = record
        self._save()

    def recall(self, topic: str) -> Optional[MemoryRecord]:
        """Recall a previous explanation if available and not stale."""
        key = self._normalize_key(topic)
        record = self.records.get(key)

        if record is None:
            return None

        # Check if stale (old version)
        if record.version < self.VERSION:
            record.superseded = True
            return None

        # Update usage stats
        record.times_used += 1
        record.last_used = time.time()

        return record

    def get_related(self, topic: str, limit: int = 5) -> List[MemoryRecord]:
        """Find related topics in memory."""
        key_words = set(self._normalize_key(topic).split('_'))
        scored = []

        for stored_key, record in self.records.items():
            if record.superseded:
                continue
            stored_words = set(stored_key.split('_'))
            overlap = len(key_words & stored_words)
            if overlap > 0:
                scored.append((overlap, record))

        scored.sort(key=lambda x: -x[0])
        return [r for _, r in scored[:limit]]

    def invalidate_version(self, old_version: int):
        """Mark all records from old version as superseded."""
        for record in self.records.values():
            if record.version <= old_version:
                record.superseded = True
        self._save()

    def get_stats(self) -> Dict:
        """Memory statistics."""
        active = sum(1 for r in self.records.values() if not r.superseded)
        stale = sum(1 for r in self.records.values() if r.superseded)
        return {
            "total": len(self.records),
            "active": active,
            "stale": stale,
            "version": self.VERSION,
        }

    def _normalize_key(self, topic: str) -> str:
        """Normalize topic to storage key."""
        import re
        key = topic.lower().strip()
        key = re.sub(r'[^a-z0-9\s]', '', key)
        key = re.sub(r'\s+', '_', key)
        return key[:100]

    def _save(self):
        """Persist memory to disk."""
        os.makedirs(os.path.dirname(self.persist_path) if os.path.dirname(self.persist_path) else '.', exist_ok=True)
        # Save as simple JSON (without graph objects for now)
        data = {}
        for key, record in self.records.items():
            data[key] = {
                "topic": record.topic,
                "version": record.version,
                "best_mode": record.best_mode,
                "confidence": record.confidence,
                "times_used": record.times_used,
                "last_used": record.last_used,
                "superseded": record.superseded,
            }
        try:
            with open(self.persist_path + ".json", 'w') as f:
                json.dump(data, f)
        except:
            pass

    def _load(self):
        """Load memory from disk."""
        path = self.persist_path + ".json"
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for key, d in data.items():
                    self.records[key] = MemoryRecord(
                        topic=d["topic"],
                        version=d.get("version", 1),
                        best_mode=d.get("best_mode", "deep"),
                        confidence=d.get("confidence", 0.5),
                        times_used=d.get("times_used", 0),
                        last_used=d.get("last_used", 0),
                        superseded=d.get("superseded", False),
                    )
            except:
                pass
