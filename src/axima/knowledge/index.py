"""Knowledge index — multi-index fact store with dependency invalidation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set


@dataclass
class Fact:
    """A stored fact with metadata."""
    id: str
    subject: str
    relation: str
    object: str
    source: str = ""
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    added_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    depends_on: List[str] = field(default_factory=list)


class KnowledgeIndex:
    """Multi-index knowledge store supporting subject/object/relation/temporal/lexical queries.

    Supports incremental updates and dependency invalidation.
    """

    def __init__(self) -> None:
        self._facts: Dict[str, Fact] = {}
        self._by_subject: Dict[str, Set[str]] = {}
        self._by_object: Dict[str, Set[str]] = {}
        self._by_relation: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}

    def add_fact(
        self,
        subject: str,
        relation: str,
        obj: str,
        source: str = "",
        valid_from: Optional[datetime] = None,
        valid_to: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
        fact_id: Optional[str] = None,
    ) -> Fact:
        """Add a fact to the index."""
        fid = fact_id or str(uuid.uuid4())
        fact = Fact(
            id=fid,
            subject=subject,
            relation=relation,
            object=obj,
            source=source,
            valid_from=valid_from,
            valid_to=valid_to,
            depends_on=depends_on or [],
        )
        self._facts[fid] = fact
        self._by_subject.setdefault(subject.lower(), set()).add(fid)
        self._by_object.setdefault(obj.lower(), set()).add(fid)
        self._by_relation.setdefault(relation.lower(), set()).add(fid)
        for dep_id in fact.depends_on:
            self._dependents.setdefault(dep_id, set()).add(fid)
        return fact

    def remove_fact(self, fact_id: str, cascade: bool = True) -> List[str]:
        """Remove a fact and optionally cascade to dependents. Returns removed IDs."""
        if fact_id not in self._facts:
            return []
        removed: List[str] = []
        to_remove = [fact_id]
        while to_remove:
            fid = to_remove.pop(0)
            if fid not in self._facts:
                continue
            fact = self._facts.pop(fid)
            removed.append(fid)
            subj_set = self._by_subject.get(fact.subject.lower())
            if subj_set:
                subj_set.discard(fid)
            obj_set = self._by_object.get(fact.object.lower())
            if obj_set:
                obj_set.discard(fid)
            rel_set = self._by_relation.get(fact.relation.lower())
            if rel_set:
                rel_set.discard(fid)
            if cascade and fid in self._dependents:
                for dep in self._dependents.pop(fid):
                    to_remove.append(dep)
        return removed

    def query(
        self,
        subject: Optional[str] = None,
        relation: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[Fact]:
        """Query facts by any combination of subject, relation, object."""
        candidate_sets: List[Set[str]] = []
        if subject is not None:
            candidate_sets.append(self._by_subject.get(subject.lower(), set()))
        if relation is not None:
            candidate_sets.append(self._by_relation.get(relation.lower(), set()))
        if obj is not None:
            candidate_sets.append(self._by_object.get(obj.lower(), set()))

        if not candidate_sets:
            return list(self._facts.values())

        result_ids = candidate_sets[0]
        for s in candidate_sets[1:]:
            result_ids = result_ids & s

        return [self._facts[fid] for fid in result_ids if fid in self._facts]

    def query_by_relation(self, relation: str) -> List[Fact]:
        """Get all facts with a specific relation."""
        ids = self._by_relation.get(relation.lower(), set())
        return [self._facts[fid] for fid in ids if fid in self._facts]

    def query_by_entity(self, entity: str) -> List[Fact]:
        """Get all facts mentioning an entity as subject or object."""
        subj_ids = self._by_subject.get(entity.lower(), set())
        obj_ids = self._by_object.get(entity.lower(), set())
        all_ids = subj_ids | obj_ids
        return [self._facts[fid] for fid in all_ids if fid in self._facts]

    def get_connected(self, entity: str, max_depth: int = 2) -> List[Fact]:
        """Get facts connected to an entity up to max_depth hops."""
        visited_entities: Set[str] = set()
        result_ids: Set[str] = set()
        frontier: Set[str] = {entity.lower()}

        for _ in range(max_depth):
            next_frontier: Set[str] = set()
            for ent in frontier:
                if ent in visited_entities:
                    continue
                visited_entities.add(ent)
                for fid in self._by_subject.get(ent, set()):
                    if fid in self._facts:
                        result_ids.add(fid)
                        next_frontier.add(self._facts[fid].object.lower())
                for fid in self._by_object.get(ent, set()):
                    if fid in self._facts:
                        result_ids.add(fid)
                        next_frontier.add(self._facts[fid].subject.lower())
            frontier = next_frontier - visited_entities

        return [self._facts[fid] for fid in result_ids if fid in self._facts]

    def count(self) -> int:
        """Total number of facts in the index."""
        return len(self._facts)

    def get_fact(self, fact_id: str) -> Optional[Fact]:
        """Get a fact by ID."""
        return self._facts.get(fact_id)
