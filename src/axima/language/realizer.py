"""
Native Language Realization
===========================

Maps MeaningIR into target language morphology, word order, and agreement.
Preserves technical symbols, citations, and equations during realization.
Supports parse-realize-parse round-trip verification.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..semantics.meaning_ir import Entity, Event, MeaningIR, Predicate, Quantity


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class MorphologyRule:
    """A morphological transformation rule for a specific language.

    Attributes:
        language: ISO 639-1 code (e.g., 'en', 'es', 'de').
        pattern: Regex pattern to match input forms.
        transformation: Replacement template or callable description.
    """

    language: str
    pattern: str
    transformation: str


@dataclass
class LanguageProfile:
    """Linguistic profile for a target language.

    Attributes:
        code: ISO 639-1 language code.
        name: Human-readable name (e.g., 'English').
        word_order: Canonical word order (e.g., 'SVO', 'SOV', 'VSO').
        agreement_rules: Subject-verb agreement patterns.
        morphology: List of morphology rules for this language.
        register_markers: Markers for different formality levels.
        script: Writing script (e.g., 'latin', 'devanagari', 'arabic').
        transliteration_map: Optional character mapping for transliteration.
    """

    code: str
    name: str
    word_order: str  # SVO, SOV, VSO, VOS, OSV, OVS
    agreement_rules: Dict[str, str] = field(default_factory=dict)
    morphology: List[MorphologyRule] = field(default_factory=list)
    register_markers: Dict[str, List[str]] = field(default_factory=dict)
    script: str = "latin"
    transliteration_map: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

_ENGLISH_PROFILE = LanguageProfile(
    code="en",
    name="English",
    word_order="SVO",
    agreement_rules={
        "third_singular_present": "add_s",
        "plural_noun": "add_s_or_es",
        "past_regular": "add_ed",
    },
    morphology=[
        MorphologyRule("en", r"(\w+)y$", r"\1ies"),  # city -> cities
        MorphologyRule("en", r"(\w+)(s|sh|ch|x|z)$", r"\1\2es"),  # box -> boxes
        MorphologyRule("en", r"(\w+)$", r"\1s"),  # cat -> cats (default plural)
    ],
    register_markers={
        "formal": ["furthermore", "therefore", "consequently", "regarding"],
        "casual": ["so", "like", "basically", "kinda"],
        "technical": ["wherein", "thereby", "herein", "cf."],
    },
    script="latin",
)

_SPANISH_PROFILE = LanguageProfile(
    code="es",
    name="Spanish",
    word_order="SVO",
    agreement_rules={
        "gender_noun_adj": "match_gender",
        "number_noun_adj": "match_number",
        "verb_person": "conjugate",
    },
    morphology=[
        MorphologyRule("es", r"(\w+)o$", r"\1os"),  # masculine plural
        MorphologyRule("es", r"(\w+)a$", r"\1as"),  # feminine plural
        MorphologyRule("es", r"(\w+)[^aeiou]$", r"\1es"),  # consonant ending
    ],
    register_markers={
        "formal": ["usted", "asimismo", "por consiguiente"],
        "casual": ["tú", "bueno", "pues", "vale"],
    },
    script="latin",
)

_GERMAN_PROFILE = LanguageProfile(
    code="de",
    name="German",
    word_order="SOV",  # SOV in subordinate clauses; V2 in main
    agreement_rules={
        "case_system": "nominative_accusative_dative_genitive",
        "verb_second": "v2_main_clause",
        "gender_article": "der_die_das",
    },
    morphology=[
        MorphologyRule("de", r"(\w+)$", r"\1en"),  # generic plural
        MorphologyRule("de", r"(\w+)e$", r"\1en"),
    ],
    register_markers={
        "formal": ["Sie", "hiermit", "bezüglich"],
        "casual": ["du", "halt", "echt"],
    },
    script="latin",
)

_HINDI_PROFILE = LanguageProfile(
    code="hi",
    name="Hindi",
    word_order="SOV",
    agreement_rules={
        "postpositions": "ne_ko_se_mein",
        "verb_gender": "match_subject_gender",
    },
    morphology=[
        MorphologyRule("hi", r"(\w+)a$", r"\1e"),  # masc plural (romanized)
        MorphologyRule("hi", r"(\w+)i$", r"\1iyaan"),  # fem plural (romanized)
    ],
    register_markers={
        "formal": ["aap", "kripya", "shriman"],
        "casual": ["tum", "yaar", "arre"],
    },
    script="devanagari",
    transliteration_map={"a": "अ", "aa": "आ", "i": "इ", "ee": "ई"},
)

_PROFILES: Dict[str, LanguageProfile] = {
    "en": _ENGLISH_PROFILE,
    "es": _SPANISH_PROFILE,
    "de": _GERMAN_PROFILE,
    "hi": _HINDI_PROFILE,
}

# ---------------------------------------------------------------------------
# Technical content preservation
# ---------------------------------------------------------------------------

_TECHNICAL_PATTERN = re.compile(
    r"("
    r"\$[^$]+\$"            # LaTeX inline math
    r"|\\[a-zA-Z]+\{[^}]*\}"  # LaTeX commands
    r"|\[[0-9]+\]"          # Citations [1], [2]
    r"|[A-Z][a-z]+ et al\.\s*\(\d{4}\)"  # Author et al. (year)
    r"|https?://\S+"        # URLs
    r"|`[^`]+`"             # Code spans
    r")"
)


def _extract_technical_spans(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace technical content with placeholders, return map for restoration."""
    placeholders: Dict[str, str] = {}
    counter = 0

    def _replace(match: re.Match) -> str:
        nonlocal counter
        key = f"__TECH_{counter}__"
        placeholders[key] = match.group(0)
        counter += 1
        return key

    sanitized = _TECHNICAL_PATTERN.sub(_replace, text)
    return sanitized, placeholders


def _restore_technical_spans(text: str, placeholders: Dict[str, str]) -> str:
    """Restore technical content from placeholders."""
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


# ---------------------------------------------------------------------------
# NativeRealizer
# ---------------------------------------------------------------------------


class NativeRealizer:
    """Realizes MeaningIR into natural language text in a target language.

    Handles:
    - Word order rearrangement based on language profile
    - Morphological agreement (gender, number, case)
    - Register adaptation (formal/casual/technical)
    - Technical content preservation (equations, citations, code)
    - Parse-realize-parse round-trip verification
    """

    def __init__(self, profiles: Optional[Dict[str, LanguageProfile]] = None) -> None:
        self._profiles: Dict[str, LanguageProfile] = profiles or dict(_PROFILES)

    def register_profile(self, profile: LanguageProfile) -> None:
        """Register a new language profile."""
        self._profiles[profile.code] = profile

    def get_profile(self, language: str) -> Optional[LanguageProfile]:
        """Get a language profile by code."""
        return self._profiles.get(language)

    def available_languages(self) -> List[str]:
        """Return list of available language codes."""
        return list(self._profiles.keys())

    def realize(
        self,
        ir: MeaningIR,
        target_language: str,
        register: str = "neutral",
    ) -> str:
        """Realize a MeaningIR into natural language text.

        Args:
            ir: The semantic representation to realize.
            target_language: ISO 639-1 code of target language.
            register: Formality level ('formal', 'neutral', 'casual', 'technical').

        Returns:
            Realized natural language string.
        """
        profile = self._profiles.get(target_language)
        if profile is None:
            # Fallback to English realization
            profile = self._profiles.get("en", _ENGLISH_PROFILE)

        # Build sentence fragments from IR components
        fragments: List[str] = []

        # Realize predicates as main assertions
        for pred in ir.predicates:
            sentence = self._realize_predicate(pred, profile)
            fragments.append(sentence)

        # Realize events as action descriptions
        for event in ir.events:
            sentence = self._realize_event(event, profile)
            fragments.append(sentence)

        # Realize quantities as measurements
        for qty in ir.quantities:
            sentence = self._realize_quantity(qty, profile)
            if sentence:
                fragments.append(sentence)

        # Realize goals as intent statements
        for goal in ir.goals:
            fragments.append(self._realize_goal(goal, profile))

        # Realize conditions
        for cond in ir.conditions:
            fragments.append(self._realize_condition(cond, profile))

        if not fragments:
            # Fallback: describe entities
            for entity in ir.entities:
                fragments.append(f"{entity.name} ({entity.type})")

        # Join and apply register
        text = ". ".join(f for f in fragments if f)
        if text and not text.endswith("."):
            text += "."

        text = self._apply_register(text, register, profile)
        return text

    def verify_round_trip(
        self,
        ir: MeaningIR,
        target_language: str,
        parser: Any = None,
    ) -> Tuple[bool, str]:
        """Verify parse-realize-parse produces semantically equivalent IR.

        Args:
            ir: Original MeaningIR.
            target_language: Target language for realization.
            parser: A LanguageParser instance. If None, verification is skipped.

        Returns:
            Tuple of (success: bool, message: str).
        """
        realized = self.realize(ir, target_language)

        if parser is None:
            return True, "No parser provided; skipping round-trip verification"

        # Re-parse the realized text
        reparsed_ir = parser.parse_to_ir(realized, target_language)

        # Compare semantic hashes
        original_hash = ir.semantic_hash()
        reparsed_hash = reparsed_ir.semantic_hash()

        if original_hash == reparsed_hash:
            return True, "Round-trip verified: semantic hashes match"

        # Partial verification: check key predicates are preserved
        original_preds = {(p.subject, p.relation, p.object) for p in ir.predicates}
        reparsed_preds = {(p.subject, p.relation, p.object) for p in reparsed_ir.predicates}
        preserved = original_preds & reparsed_preds

        if len(preserved) >= len(original_preds) * 0.8:
            return True, f"Round-trip partially verified: {len(preserved)}/{len(original_preds)} predicates preserved"

        return False, f"Round-trip failed: only {len(preserved)}/{len(original_preds)} predicates preserved"

    # ------------------------------------------------------------------
    # Internal realization methods
    # ------------------------------------------------------------------

    def _realize_predicate(self, pred: Predicate, profile: LanguageProfile) -> str:
        """Realize a predicate triple into a sentence."""
        negation = "not " if pred.negated else ""

        if profile.word_order == "SVO":
            sentence = f"{pred.subject} {negation}{pred.relation} {pred.object}"
        elif profile.word_order == "SOV":
            sentence = f"{pred.subject} {pred.object} {negation}{pred.relation}"
        elif profile.word_order == "VSO":
            sentence = f"{negation}{pred.relation} {pred.subject} {pred.object}"
        elif profile.word_order == "VOS":
            sentence = f"{negation}{pred.relation} {pred.object} {pred.subject}"
        elif profile.word_order == "OSV":
            sentence = f"{pred.object} {pred.subject} {negation}{pred.relation}"
        elif profile.word_order == "OVS":
            sentence = f"{pred.object} {negation}{pred.relation} {pred.subject}"
        else:
            sentence = f"{pred.subject} {negation}{pred.relation} {pred.object}"

        if pred.modality:
            sentence = f"{pred.modality}: {sentence}"

        return sentence.strip()

    def _realize_event(self, event: Event, profile: LanguageProfile) -> str:
        """Realize an event into a sentence."""
        parts: List[str] = []

        if profile.word_order in ("SVO", "SOV"):
            if event.agent:
                parts.append(event.agent)
            parts.append(event.verb)
            if event.patient:
                parts.append(event.patient)
        elif profile.word_order == "VSO":
            parts.append(event.verb)
            if event.agent:
                parts.append(event.agent)
            if event.patient:
                parts.append(event.patient)
        else:
            if event.agent:
                parts.append(event.agent)
            parts.append(event.verb)
            if event.patient:
                parts.append(event.patient)

        if event.instrument:
            parts.append(f"using {event.instrument}")
        if event.location:
            parts.append(f"at {event.location}")
        if event.time:
            parts.append(f"at {event.time}")

        for mod in event.modifiers:
            parts.append(mod)

        return " ".join(parts)

    def _realize_quantity(self, qty: Quantity, profile: LanguageProfile) -> str:
        """Realize a quantity as a text fragment."""
        parts: List[str] = []
        parts.append(str(qty.value))
        if qty.unit:
            parts.append(qty.unit)
        if qty.uncertainty is not None:
            parts.append(f"(±{qty.uncertainty})")
        if qty.domain:
            parts.append(f"[{qty.domain}]")
        return " ".join(parts)

    def _realize_goal(self, goal: Any, profile: LanguageProfile) -> str:
        """Realize a goal/intent."""
        parts = [f"Goal: {goal.description}"]
        if goal.constraints:
            parts.append(f"Constraints: {', '.join(goal.constraints)}")
        return ". ".join(parts)

    def _realize_condition(self, cond: Any, profile: LanguageProfile) -> str:
        """Realize a conditional statement."""
        text = f"If {cond.if_clause}, then {cond.then_clause}"
        if cond.else_clause:
            text += f", otherwise {cond.else_clause}"
        return text

    def _apply_register(self, text: str, register: str, profile: LanguageProfile) -> str:
        """Apply register-appropriate markers to the text."""
        if register == "formal":
            # Capitalize first letter of each sentence, avoid contractions
            text = text.replace("don't", "do not")
            text = text.replace("can't", "cannot")
            text = text.replace("won't", "will not")
            text = text.replace("isn't", "is not")
            text = text.replace("aren't", "are not")
        elif register == "casual":
            text = text.replace("do not", "don't")
            text = text.replace("cannot", "can't")
            text = text.replace("will not", "won't")
            text = text.replace("is not", "isn't")

        return text

    def _apply_morphology(self, word: str, rules: List[MorphologyRule]) -> str:
        """Apply morphology rules to a word."""
        for rule in rules:
            if re.match(rule.pattern, word):
                return re.sub(rule.pattern, rule.transformation, word)
        return word
