"""Text to MeaningIR compiler — rule-based semantic parsing."""

from __future__ import annotations

import re
import uuid
from typing import List, Optional, Tuple

from .meaning_ir import (
    Condition,
    Entity,
    Event,
    Goal,
    MeaningIR,
    Predicate,
    Quantity,
)


def _gen_id(prefix: str = "node") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# Unit patterns for quantity extraction
_UNIT_PATTERNS = [
    "kg", "g", "mg", "lb", "oz",
    "m", "km", "cm", "mm", "mi", "ft", "in",
    "s", "ms", "min", "hr", "h",
    "m/s", "km/h", "mph",
    "N", "J", "W", "Pa", "Hz",
    "K", "C", "F",
    "V", "A", "ohm",
    "mol", "L", "mL",
    "%", "USD", "EUR", "GBP",
]

_QUANTITY_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(" + "|".join(re.escape(u) for u in _UNIT_PATTERNS) + r")\b"
)

_BARE_NUMBER_RE = re.compile(r"\b(\d+(?:\.\d+)?)\b")

# Condition patterns
_IF_THEN_RE = re.compile(
    r"\bif\s+(.+?)\s*,?\s*then\s+(.+?)(?:\s*,?\s*else\s+(.+?))?[.!?]?\s*$",
    re.IGNORECASE,
)

# Goal patterns
_GOAL_PATTERNS = [
    re.compile(r"\b(?:find|calculate|compute|determine|solve for|evaluate)\s+(.+)", re.IGNORECASE),
    re.compile(r"\b(?:how (?:to|do|can))\s+(.+)", re.IGNORECASE),
    re.compile(r"\b(?:what is|what are|what's)\s+(.+)", re.IGNORECASE),
]

# Predicate patterns (subject-verb-object)
_SVO_RE = re.compile(
    r"^([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(is|are|was|were|has|have|can|will|does)\s+(.+?)[.!?]?\s*$"
)

_RELATION_PATTERNS = [
    (re.compile(r"(.+?)\s+(?:is|are)\s+(?:a|an)\s+(.+)", re.IGNORECASE), "is_a"),
    (re.compile(r"(.+?)\s+(?:is|are)\s+(?:not)\s+(.+)", re.IGNORECASE), "is_not"),
    (re.compile(r"(.+?)\s+(?:is|are)\s+(.+)", re.IGNORECASE), "is"),
    (re.compile(r"(.+?)\s+(?:has|have)\s+(.+)", re.IGNORECASE), "has"),
    (re.compile(r"(.+?)\s+(?:contains?)\s+(.+)", re.IGNORECASE), "contains"),
]

# Entity type heuristics
_ENTITY_TYPE_PATTERNS = {
    "person": re.compile(r"\b(?:person|man|woman|boy|girl|student|teacher|doctor|engineer)\b", re.I),
    "location": re.compile(r"\b(?:city|country|place|location|town|village|planet|earth)\b", re.I),
    "object": re.compile(r"\b(?:ball|car|book|table|machine|computer|device)\b", re.I),
    "concept": re.compile(r"\b(?:algorithm|theory|idea|concept|method|process)\b", re.I),
}

# Negation detection
_NEGATION_RE = re.compile(r"\b(?:not|no|never|neither|nor|isn't|aren't|wasn't|weren't|don't|doesn't)\b", re.I)

# Modality detection
_MODALITY_PATTERNS = {
    "possible": re.compile(r"\b(?:might|may|could|possibly|perhaps)\b", re.I),
    "necessary": re.compile(r"\b(?:must|necessarily|always|certainly)\b", re.I),
    "likely": re.compile(r"\b(?:probably|likely|usually|often)\b", re.I),
}


class MeaningCompiler:
    """Rule-based compiler from text to MeaningIR.

    Uses pattern matching to extract entities, quantities, predicates,
    conditions, and goals from natural language text. Preserves source
    spans and generates alternatives for ambiguous inputs.
    """

    def compile(self, text: str, language: str = "en") -> MeaningIR:
        """Compile text into a MeaningIR representation."""
        entities = self._extract_entities(text)
        quantities = self._extract_quantities(text)
        predicates = self._extract_predicates(text)
        conditions = self._extract_conditions(text)
        goals = self._extract_goals(text)
        events = self._extract_events(text)

        source_span_map = {"_raw": text}
        for ent in entities:
            if ent.source_span:
                source_span_map[ent.id] = ent.source_span

        ir = MeaningIR(
            entities=entities,
            events=events,
            predicates=predicates,
            quantities=quantities,
            conditions=conditions,
            goals=goals,
            source_span_map=source_span_map,
            language=language,
        )

        # Generate alternatives for ambiguous parses
        alternatives = self._detect_ambiguity(text, ir, language)
        if alternatives:
            ir.ambiguity_alternatives = alternatives

        return ir

    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities using capitalization and type heuristics."""
        entities: List[Entity] = []
        seen_names: set = set()

        # Capitalized word sequences (simple NER)
        cap_re = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
        for match in cap_re.finditer(text):
            name = match.group(1)
            if name.lower() in ("if", "then", "else", "the", "what", "how", "why", "when", "where"):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            etype = self._infer_entity_type(name, text)
            entities.append(Entity(
                id=_gen_id("ent"),
                name=name,
                type=etype,
                source_span=(match.start(), match.end()),
            ))

        return entities

    def _infer_entity_type(self, name: str, context: str) -> str:
        """Infer entity type from context patterns."""
        name_lower = name.lower()
        for etype, pattern in _ENTITY_TYPE_PATTERNS.items():
            if pattern.search(name_lower) or pattern.search(context):
                return etype
        return "concept"

    def _extract_quantities(self, text: str) -> List[Quantity]:
        """Extract numeric quantities with units."""
        quantities: List[Quantity] = []
        seen_positions: set = set()

        for match in _QUANTITY_RE.finditer(text):
            pos = match.start()
            if pos in seen_positions:
                continue
            seen_positions.add(pos)
            value = float(match.group(1))
            unit = match.group(2)
            domain = self._infer_quantity_domain(unit)
            quantities.append(Quantity(value=value, unit=unit, domain=domain))

        # Bare numbers without units (only if no unit-quantities found)
        if not quantities:
            for match in _BARE_NUMBER_RE.finditer(text):
                value = float(match.group(1))
                quantities.append(Quantity(value=value))

        return quantities

    def _infer_quantity_domain(self, unit: str) -> Optional[str]:
        """Infer domain from unit."""
        physics_units = {"m", "km", "cm", "mm", "s", "ms", "N", "J", "W", "Pa", "Hz", "K", "V", "A", "ohm", "m/s", "km/h"}
        mass_units = {"kg", "g", "mg", "lb", "oz"}
        finance_units = {"USD", "EUR", "GBP", "%"}
        if unit in physics_units or unit in mass_units:
            return "physics"
        if unit in finance_units:
            return "finance"
        return None

    def _extract_predicates(self, text: str) -> List[Predicate]:
        """Extract predicates using relation patterns."""
        predicates: List[Predicate] = []
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            negated = bool(_NEGATION_RE.search(sentence))
            modality = None
            for mod, pattern in _MODALITY_PATTERNS.items():
                if pattern.search(sentence):
                    modality = mod
                    break

            for pattern, relation in _RELATION_PATTERNS:
                match = pattern.match(sentence)
                if match:
                    subject = match.group(1).strip()
                    obj = match.group(2).strip()
                    # Clean negation markers from relation
                    if relation == "is_not":
                        negated = True
                        relation = "is"
                    predicates.append(Predicate(
                        subject=subject,
                        relation=relation,
                        object=obj,
                        negated=negated,
                        modality=modality,
                    ))
                    break

        return predicates

    def _extract_conditions(self, text: str) -> List[Condition]:
        """Extract if-then-else conditions."""
        conditions: List[Condition] = []
        for match in _IF_THEN_RE.finditer(text):
            conditions.append(Condition(
                if_clause=match.group(1).strip(),
                then_clause=match.group(2).strip(),
                else_clause=match.group(3).strip() if match.group(3) else None,
            ))
        return conditions

    def _extract_goals(self, text: str) -> List[Goal]:
        """Extract goals/intents from query text."""
        goals: List[Goal] = []
        for pattern in _GOAL_PATTERNS:
            match = pattern.search(text)
            if match:
                desc = match.group(1).strip().rstrip("?.")
                goals.append(Goal(description=desc))
                break

        # If no match but query starts with an action verb, extract the rest as a goal
        if not goals:
            action_match = re.match(
                r"^(solve|calculate|compute|evaluate|simplify|factor|integrate|derive)\s+(.+)",
                text, re.IGNORECASE,
            )
            if action_match:
                desc = action_match.group(2).strip().rstrip("?.")
                goals.append(Goal(description=desc))

        # If query is a pure math expression (function call or arithmetic), treat as goal
        if not goals:
            math_expr_match = re.match(
                r"^((?:sqrt|sin|cos|tan|log|ln|exp|factorial|gcd|lcm|abs|asin|acos|atan|floor|ceil|round)"
                r"\s*\(.+\)|[\d\s+\-*/^().]+)$",
                text.strip(), re.IGNORECASE,
            )
            if math_expr_match:
                goals.append(Goal(description=text.strip()))

        return goals

    def _extract_events(self, text: str) -> List[Event]:
        """Extract events (verb + arguments)."""
        events: List[Event] = []
        # Simple SVO pattern
        action_re = re.compile(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+"
            r"(moves?|runs?|throws?|calculates?|computes?|builds?|creates?|sends?|receives?)\s+"
            r"(.+?)(?:[.!?]|$)",
            re.IGNORECASE,
        )
        for match in action_re.finditer(text):
            events.append(Event(
                id=_gen_id("evt"),
                verb=match.group(2).lower(),
                agent=match.group(1),
                patient=match.group(3).strip(),
            ))
        return events

    def _detect_ambiguity(self, text: str, primary: MeaningIR, language: str) -> List[MeaningIR]:
        """Detect ambiguous parses and generate alternatives."""
        alternatives: List[MeaningIR] = []

        # Ambiguity: "X or Y" could mean disjunction or alternative parse
        or_match = re.search(r"(.+?)\s+or\s+(.+)", text, re.IGNORECASE)
        if or_match and primary.predicates:
            # Generate alternative where the "or" branch is the main predicate
            alt_text = or_match.group(2)
            alt_predicates = self._extract_predicates(alt_text)
            if alt_predicates:
                alt = MeaningIR(
                    predicates=alt_predicates,
                    language=language,
                )
                alternatives.append(alt)

        return alternatives
