"""Universal Meaning IR (UMIR) — language-independent semantic representation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Entity:
    """A named entity extracted from text."""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_span: Optional[Tuple[int, int]] = None


@dataclass
class Event:
    """An event or action extracted from text."""
    id: str
    verb: str
    agent: Optional[str] = None
    patient: Optional[str] = None
    instrument: Optional[str] = None
    location: Optional[str] = None
    time: Optional[str] = None
    modifiers: List[str] = field(default_factory=list)


@dataclass
class Quantity:
    """A numeric quantity with unit and uncertainty."""
    value: float
    unit: Optional[str] = None
    uncertainty: Optional[float] = None
    domain: Optional[str] = None


@dataclass
class Predicate:
    """A logical predicate (subject-relation-object triple)."""
    subject: str
    relation: str
    object: str
    negated: bool = False
    modality: Optional[str] = None
    confidence: float = 1.0


@dataclass
class Condition:
    """A conditional statement (if-then-else)."""
    if_clause: str
    then_clause: str
    else_clause: Optional[str] = None


@dataclass
class Goal:
    """A goal or intent extracted from the query."""
    description: str
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)


@dataclass
class MeaningIR:
    """Universal Meaning Intermediate Representation.

    Captures the full semantic content of a text in a structured,
    language-independent form suitable for reasoning, transformation,
    and verification.
    """
    entities: List[Entity] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    predicates: List[Predicate] = field(default_factory=list)
    quantities: List[Quantity] = field(default_factory=list)
    conditions: List[Condition] = field(default_factory=list)
    goals: List[Goal] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    ambiguity_alternatives: List["MeaningIR"] = field(default_factory=list)
    source_span_map: Dict[str, Tuple[int, int]] = field(default_factory=dict)
    language: str = "en"

    def _canonical_dict(self) -> Dict[str, Any]:
        """Produce a canonical dictionary for deterministic hashing."""

        def _entity_key(e: Entity) -> Dict[str, Any]:
            return {
                "id": e.id,
                "name": e.name,
                "type": e.type,
                "properties": dict(sorted(e.properties.items())) if e.properties else {},
            }

        def _event_key(ev: Event) -> Dict[str, Any]:
            return {
                "id": ev.id,
                "verb": ev.verb,
                "agent": ev.agent,
                "patient": ev.patient,
                "instrument": ev.instrument,
                "location": ev.location,
                "time": ev.time,
                "modifiers": sorted(ev.modifiers),
            }

        def _quantity_key(q: Quantity) -> Dict[str, Any]:
            return {"value": q.value, "unit": q.unit, "uncertainty": q.uncertainty, "domain": q.domain}

        def _predicate_key(p: Predicate) -> Dict[str, Any]:
            return {
                "subject": p.subject,
                "relation": p.relation,
                "object": p.object,
                "negated": p.negated,
                "modality": p.modality,
                "confidence": p.confidence,
            }

        def _condition_key(c: Condition) -> Dict[str, Any]:
            return {"if": c.if_clause, "then": c.then_clause, "else": c.else_clause}

        def _goal_key(g: Goal) -> Dict[str, Any]:
            return {
                "description": g.description,
                "constraints": sorted(g.constraints),
                "success_criteria": sorted(g.success_criteria),
            }

        return {
            "entities": sorted([_entity_key(e) for e in self.entities], key=lambda x: x["id"]),
            "events": sorted([_event_key(ev) for ev in self.events], key=lambda x: x["id"]),
            "predicates": sorted(
                [_predicate_key(p) for p in self.predicates],
                key=lambda x: (x["subject"], x["relation"], x["object"]),
            ),
            "quantities": sorted(
                [_quantity_key(q) for q in self.quantities],
                key=lambda x: (x["value"], x["unit"] or ""),
            ),
            "conditions": [_condition_key(c) for c in self.conditions],
            "goals": sorted([_goal_key(g) for g in self.goals], key=lambda x: x["description"]),
            "constraints": sorted(self.constraints),
            "language": self.language,
        }

    def semantic_hash(self) -> str:
        """Content-addressed hash of the semantic content."""
        canonical = self._canonical_dict()
        serialized = json.dumps(canonical, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def merge(self, other: "MeaningIR") -> "MeaningIR":
        """Merge another MeaningIR into this one, combining all fields."""
        entity_map = {e.id: e for e in self.entities}
        for e in other.entities:
            if e.id not in entity_map:
                entity_map[e.id] = e

        event_map = {ev.id: ev for ev in self.events}
        for ev in other.events:
            if ev.id not in event_map:
                event_map[ev.id] = ev

        pred_key_fn = lambda p: (p.subject, p.relation, p.object, p.negated)
        pred_map = {pred_key_fn(p): p for p in self.predicates}
        for p in other.predicates:
            k = pred_key_fn(p)
            if k not in pred_map:
                pred_map[k] = p

        qty_key_fn = lambda q: (q.value, q.unit, q.domain)
        qty_map = {qty_key_fn(q): q for q in self.quantities}
        for q in other.quantities:
            k = qty_key_fn(q)
            if k not in qty_map:
                qty_map[k] = q

        cond_key_fn = lambda c: (c.if_clause, c.then_clause, c.else_clause)
        cond_map = {cond_key_fn(c): c for c in self.conditions}
        for c in other.conditions:
            k = cond_key_fn(c)
            if k not in cond_map:
                cond_map[k] = c

        goal_map = {g.description: g for g in self.goals}
        for g in other.goals:
            if g.description not in goal_map:
                goal_map[g.description] = g

        merged_constraints = list(set(self.constraints + other.constraints))
        merged_spans = dict(self.source_span_map)
        merged_spans.update(other.source_span_map)
        merged_alts = self.ambiguity_alternatives + other.ambiguity_alternatives

        return MeaningIR(
            entities=list(entity_map.values()),
            events=list(event_map.values()),
            predicates=list(pred_map.values()),
            quantities=list(qty_map.values()),
            conditions=list(cond_map.values()),
            goals=list(goal_map.values()),
            constraints=merged_constraints,
            ambiguity_alternatives=merged_alts,
            source_span_map=merged_spans,
            language=self.language,
        )
