"""
Language Parser
===============

Rules-based language detection and structural parsing into MeaningIR.
Extracts entities, quantities, predicates, and events from natural language text.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ..semantics.meaning_ir import (
    Condition,
    Entity,
    Event,
    Goal,
    MeaningIR,
    Predicate,
    Quantity,
)


# ---------------------------------------------------------------------------
# Language detection patterns
# ---------------------------------------------------------------------------

_LANGUAGE_INDICATORS: Dict[str, List[str]] = {
    "en": [
        r"\b(the|is|are|was|were|have|has|had|will|would|could|should|can|do|does)\b",
        r"\b(this|that|these|those|here|there|where|when|which|what|who)\b",
    ],
    "es": [
        r"\b(el|la|los|las|es|son|está|están|tiene|hay|puede|como)\b",
        r"\b(que|de|en|por|para|con|una|uno|del|más)\b",
    ],
    "de": [
        r"\b(der|die|das|ist|sind|hat|haben|wird|werden|kann|mit)\b",
        r"\b(und|oder|aber|nicht|ein|eine|einer|dem|den|des)\b",
    ],
    "fr": [
        r"\b(le|la|les|est|sont|a|ont|fait|pour|dans|avec|que)\b",
        r"\b(un|une|des|du|au|aux|ce|cette|ces|ne|pas)\b",
    ],
    "hi": [
        r"\b(hai|hain|ka|ki|ke|mein|se|ko|ne|par|aur|ya)\b",
        r"\b(kya|kaise|kahan|kaun|yeh|woh|ek|do|bahut|nahi)\b",
    ],
    "ja": [
        r"[\u3040-\u309F]",  # Hiragana
        r"[\u30A0-\u30FF]",  # Katakana
    ],
    "zh": [
        r"[\u4E00-\u9FFF]",  # CJK Unified Ideographs
    ],
    "ar": [
        r"[\u0600-\u06FF]",  # Arabic script
    ],
    "ru": [
        r"[\u0400-\u04FF]",  # Cyrillic
    ],
    "pt": [
        r"\b(o|a|os|as|é|são|está|tem|para|com|não|um|uma)\b",
        r"\b(de|em|por|que|do|da|dos|das|ao|aos)\b",
    ],
    "it": [
        r"\b(il|lo|la|i|gli|le|è|sono|ha|hanno|per|con)\b",
        r"\b(di|da|in|su|un|una|che|non|del|della)\b",
    ],
    "ko": [
        r"[\uAC00-\uD7AF]",  # Hangul syllables
    ],
    "te": [
        r"[\u0C00-\u0C7F]",  # Telugu script
    ],
    "ta": [
        r"[\u0B80-\u0BFF]",  # Tamil script
    ],
    "tr": [
        r"\b(bir|ve|bu|için|ile|var|yok|olan|olarak|gibi)\b",
        r"[ğıöüşçĞİÖÜŞÇ]",
    ],
}

# ---------------------------------------------------------------------------
# Structural parsing patterns
# ---------------------------------------------------------------------------

_QUANTITY_PATTERN = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*"
    r"(kg|g|mg|m|km|cm|mm|s|ms|min|h|Hz|kHz|MHz|GHz|"
    r"°C|°F|K|J|kJ|W|kW|MW|V|A|Ω|Pa|atm|bar|mol|L|mL|"
    r"N|lb|oz|ft|in|mi|mph|m/s|km/h|%|dollars?|USD|EUR|GBP)?\b"
)

_ENTITY_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"
)

_IS_A_PATTERN = re.compile(
    r"\b(\w[\w\s]*?)\s+(?:is|are)\s+(?:a|an|the)?\s*(\w[\w\s]*?)(?:\.|$)",
    re.I,
)

_HAS_PATTERN = re.compile(
    r"\b(\w[\w\s]*?)\s+(?:has|have|had)\s+(?:a|an|the)?\s*(\w[\w\s]*?)(?:\.|$)",
    re.I,
)

_ACTION_PATTERN = re.compile(
    r"\b(\w+)\s+(solve|calculate|compute|find|determine|explain|describe|"
    r"create|build|generate|write|implement|analyze|compare|list|define|"
    r"translate|convert|prove|derive)\s+(.+?)(?:\.|$)",
    re.I,
)

_VERB_PATTERN = re.compile(
    r"\b(\w[\w\s]*?)\s+(moves?|runs?|goes?|takes?|gives?|makes?|puts?|"
    r"sends?|comes?|works?|calls?|uses?|finds?|gets?|sets?|plays?)\s+"
    r"([\w\s]+?)(?:\.|$)",
    re.I,
)

_CONDITIONAL_PATTERN = re.compile(
    r"\bif\s+(.+?)\s*,?\s*then\s+(.+?)(?:\s*(?:else|otherwise)\s+(.+?))?(?:\.|$)",
    re.I,
)

_GOAL_PATTERN = re.compile(
    r"\b(?:I want to|please|could you|can you|help me|need to)\s+(.+?)(?:\.|$)",
    re.I,
)


# ---------------------------------------------------------------------------
# LanguageParser
# ---------------------------------------------------------------------------


class LanguageParser:
    """Rules-based language detection and structural text parsing.

    Extracts:
    - Language detection scores based on character/word patterns
    - Entities (proper nouns, named entities)
    - Quantities (numeric values with units)
    - Predicates (is-a, has-a relations)
    - Events (subject-verb-object actions)
    - Conditions (if-then-else)
    - Goals (intent/request patterns)
    """

    def detect_language(self, text: str) -> List[Tuple[str, float]]:
        """Detect likely languages of the input text.

        Args:
            text: Input text to analyze.

        Returns:
            List of (language_code, confidence) tuples, sorted by confidence desc.
        """
        if not text or not text.strip():
            return [("en", 0.5)]

        scores: Dict[str, float] = {}
        text_lower = text.lower()
        text_len = max(len(text), 1)

        for lang, patterns in _LANGUAGE_INDICATORS.items():
            total_matches = 0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower if lang in (
                    "en", "es", "de", "fr", "hi", "pt", "it", "tr"
                ) else text, re.I)
                total_matches += len(matches)

            # Normalize score by text length
            score = min(total_matches / (text_len / 10.0), 1.0)
            if score > 0.01:
                scores[lang] = score

        if not scores:
            return [("en", 0.3)]

        # Normalize scores to sum to 1.0
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        result = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return result[:5]

    def parse_to_ir(self, text: str, language: str = "en") -> MeaningIR:
        """Parse text into a MeaningIR representation.

        Performs structural extraction of:
        - Named entities (proper nouns)
        - Quantities (numbers with units)
        - Predicates (relations between entities)
        - Events (actions)
        - Conditions (if-then)
        - Goals (intents)

        Args:
            text: Input text to parse.
            language: Language code for parsing rules.

        Returns:
            MeaningIR populated with extracted semantic components.
        """
        entities: List[Entity] = []
        events: List[Event] = []
        predicates: List[Predicate] = []
        quantities: List[Quantity] = []
        conditions: List[Condition] = []
        goals: List[Goal] = []
        span_map: Dict[str, Tuple[int, int]] = {}

        # Extract quantities
        for match in _QUANTITY_PATTERN.finditer(text):
            value_str = match.group(1)
            unit = match.group(2) if match.group(2) else None
            try:
                value = float(value_str)
            except ValueError:
                continue
            quantities.append(Quantity(value=value, unit=unit))
            span_map[f"qty_{len(quantities)}"] = (match.start(), match.end())

        # Extract named entities
        seen_names: set = set()
        for match in _ENTITY_PATTERN.finditer(text):
            name = match.group(1)
            if name.lower() in ("the", "a", "an", "this", "that", "if", "then"):
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            entity = Entity(
                id=f"e_{uuid.uuid4().hex[:8]}",
                name=name,
                type="named_entity",
                source_span=(match.start(), match.end()),
            )
            entities.append(entity)
            span_map[entity.id] = (match.start(), match.end())

        # Extract is-a predicates
        for match in _IS_A_PATTERN.finditer(text):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if subject and obj and len(subject) < 50 and len(obj) < 50:
                predicates.append(Predicate(
                    subject=subject,
                    relation="is_a",
                    object=obj,
                ))

        # Extract has-a predicates
        for match in _HAS_PATTERN.finditer(text):
            subject = match.group(1).strip()
            obj = match.group(2).strip()
            if subject and obj and len(subject) < 50 and len(obj) < 50:
                predicates.append(Predicate(
                    subject=subject,
                    relation="has",
                    object=obj,
                ))

        # Extract action events
        for match in _ACTION_PATTERN.finditer(text):
            agent = match.group(1).strip()
            verb = match.group(2).strip()
            patient = match.group(3).strip()
            events.append(Event(
                id=f"ev_{uuid.uuid4().hex[:8]}",
                verb=verb,
                agent=agent if agent.lower() not in ("please", "i", "you") else None,
                patient=patient,
            ))

        # Extract verb-based events
        for match in _VERB_PATTERN.finditer(text):
            agent = match.group(1).strip()
            verb = match.group(2).strip()
            patient = match.group(3).strip()
            if len(agent) < 50 and len(patient) < 50:
                events.append(Event(
                    id=f"ev_{uuid.uuid4().hex[:8]}",
                    verb=verb,
                    agent=agent,
                    patient=patient,
                ))

        # Extract conditions
        for match in _CONDITIONAL_PATTERN.finditer(text):
            if_clause = match.group(1).strip()
            then_clause = match.group(2).strip()
            else_clause = match.group(3).strip() if match.group(3) else None
            conditions.append(Condition(
                if_clause=if_clause,
                then_clause=then_clause,
                else_clause=else_clause,
            ))

        # Extract goals
        for match in _GOAL_PATTERN.finditer(text):
            description = match.group(1).strip()
            if description:
                goals.append(Goal(description=description))

        return MeaningIR(
            entities=entities,
            events=events,
            predicates=predicates,
            quantities=quantities,
            conditions=conditions,
            goals=goals,
            source_span_map=span_map,
            language=language,
        )
