"""
Register Adaptation
===================

Manages formality/register levels and adapts text between registers.
Supports FORMAL, NEUTRAL, CASUAL, TECHNICAL, and PEDAGOGICAL registers.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Register(Enum):
    """Formality/register levels for text output."""

    FORMAL = "formal"
    NEUTRAL = "neutral"
    CASUAL = "casual"
    TECHNICAL = "technical"
    PEDAGOGICAL = "pedagogical"


# ---------------------------------------------------------------------------
# Transformation rules between registers
# ---------------------------------------------------------------------------

_FORMAL_TO_CASUAL: List[Tuple[str, str]] = [
    (r"\bfurthermore\b", "also"),
    (r"\bconsequently\b", "so"),
    (r"\btherefore\b", "so"),
    (r"\bnevertheless\b", "still"),
    (r"\bhowever\b", "but"),
    (r"\bmoreover\b", "plus"),
    (r"\bregarding\b", "about"),
    (r"\bpreviously\b", "before"),
    (r"\bsubsequently\b", "then"),
    (r"\butilize\b", "use"),
    (r"\bpurchase\b", "buy"),
    (r"\binquire\b", "ask"),
    (r"\bcommence\b", "start"),
    (r"\bterminate\b", "end"),
    (r"\bdo not\b", "don't"),
    (r"\bcannot\b", "can't"),
    (r"\bwill not\b", "won't"),
    (r"\bis not\b", "isn't"),
    (r"\bare not\b", "aren't"),
    (r"\bshall\b", "will"),
    (r"\bhence\b", "so"),
    (r"\bthus\b", "so"),
]

_CASUAL_TO_FORMAL: List[Tuple[str, str]] = [
    (r"\bso\b", "therefore"),
    (r"\bbut\b", "however"),
    (r"\bplus\b", "moreover"),
    (r"\babout\b", "regarding"),
    (r"\bbefore\b", "previously"),
    (r"\bthen\b", "subsequently"),
    (r"\buse\b", "utilize"),
    (r"\bbuy\b", "purchase"),
    (r"\bask\b", "inquire"),
    (r"\bstart\b", "commence"),
    (r"\bend\b", "terminate"),
    (r"\bdon't\b", "do not"),
    (r"\bcan't\b", "cannot"),
    (r"\bwon't\b", "will not"),
    (r"\bisn't\b", "is not"),
    (r"\baren't\b", "are not"),
    (r"\bkinda\b", "somewhat"),
    (r"\bgonna\b", "going to"),
    (r"\bwanna\b", "want to"),
    (r"\bgotta\b", "have to"),
    (r"\byeah\b", "yes"),
    (r"\bnope\b", "no"),
    (r"\bstuff\b", "material"),
    (r"\bgot\b", "obtained"),
]

_NEUTRAL_TO_TECHNICAL: List[Tuple[str, str]] = [
    (r"\bsolution\b", "solution set"),
    (r"\banswer\b", "result"),
    (r"\bguess\b", "estimate"),
    (r"\bkind of\b", "type of"),
    (r"\bsort of\b", "category of"),
    (r"\bpart\b", "component"),
    (r"\bpiece\b", "element"),
    (r"\bgroup\b", "set"),
    (r"\brule\b", "constraint"),
    (r"\bway\b", "method"),
    (r"\bthing\b", "entity"),
]

_NEUTRAL_TO_PEDAGOGICAL: List[Tuple[str, str]] = [
    (r"\bthe result is\b", "notice that the result is"),
    (r"\bwe get\b", "this gives us"),
    (r"\bnote that\b", "it's important to observe that"),
    (r"\bsince\b", "recall that since"),
]

_PEDAGOGICAL_PREFIXES = [
    "Let's break this down: ",
    "Think of it this way: ",
    "Here's the key insight: ",
    "To understand this, consider: ",
    "Step by step: ",
]


class RegisterAdapter:
    """Adapts text between different formality registers.

    Applies rule-based transformations to shift text from one register
    to another while preserving technical content (equations, code, citations).
    """

    def __init__(self) -> None:
        self._technical_pattern = re.compile(
            r"("
            r"\$[^$]+\$"
            r"|\\[a-zA-Z]+\{[^}]*\}"
            r"|\[[0-9]+\]"
            r"|`[^`]+`"
            r"|https?://\S+"
            r")"
        )

    def adapt(
        self,
        text: str,
        source_register: Register,
        target_register: Register,
    ) -> str:
        """Adapt text from source register to target register.

        Args:
            text: Input text.
            source_register: Current register of the text.
            target_register: Desired register.

        Returns:
            Text adapted to the target register.
        """
        if source_register == target_register:
            return text

        # Protect technical content
        protected, placeholders = self._protect_technical(text)

        # Apply transformations based on source -> target path
        adapted = self._transform(protected, source_register, target_register)

        # Restore technical content
        result = self._restore_technical(adapted, placeholders)
        return result

    def detect_register(self, text: str) -> Register:
        """Detect the likely register of the given text.

        Returns:
            Best-guess Register for the input text.
        """
        text_lower = text.lower()

        # Check for pedagogical markers
        pedagogical_markers = [
            "let's", "step by step", "think of it",
            "notice that", "recall that", "key insight",
            "to understand", "for example", "in other words",
        ]
        pedagogical_count = sum(1 for m in pedagogical_markers if m in text_lower)
        if pedagogical_count >= 2:
            return Register.PEDAGOGICAL

        # Check for technical markers
        technical_markers = [
            "algorithm", "constraint", "parameter", "implementation",
            "complexity", "theorem", "proof", "hypothesis",
            "cf.", "i.e.", "e.g.", "et al.",
        ]
        technical_count = sum(1 for m in technical_markers if m in text_lower)
        if technical_count >= 2:
            return Register.TECHNICAL

        # Check for formal markers
        formal_markers = [
            "furthermore", "consequently", "nevertheless",
            "moreover", "regarding", "therefore", "hence",
            "subsequently", "henceforth",
        ]
        formal_count = sum(1 for m in formal_markers if m in text_lower)
        if formal_count >= 2:
            return Register.FORMAL

        # Check for casual markers
        casual_markers = [
            "don't", "can't", "won't", "gonna", "wanna",
            "kinda", "gotta", "yeah", "nope", "stuff",
            "like,", "basically,",
        ]
        casual_count = sum(1 for m in casual_markers if m in text_lower)
        if casual_count >= 2:
            return Register.CASUAL

        return Register.NEUTRAL

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _transform(
        self,
        text: str,
        source: Register,
        target: Register,
    ) -> str:
        """Apply transformation rules to shift register."""
        # Determine the rule set
        rules = self._get_rules(source, target)

        result = text
        for pattern, replacement in rules:
            result = re.sub(pattern, replacement, result, flags=re.I)

        # Additional structural changes
        if target == Register.PEDAGOGICAL:
            result = self._pedagogical_wrap(result)
        elif target == Register.FORMAL:
            result = self._formalize_structure(result)

        return result

    def _get_rules(
        self,
        source: Register,
        target: Register,
    ) -> List[Tuple[str, str]]:
        """Get the transformation rule list for a source->target pair."""
        if target == Register.CASUAL:
            if source in (Register.FORMAL, Register.NEUTRAL, Register.TECHNICAL):
                return _FORMAL_TO_CASUAL
        elif target == Register.FORMAL:
            if source in (Register.CASUAL, Register.NEUTRAL):
                return _CASUAL_TO_FORMAL
        elif target == Register.TECHNICAL:
            if source in (Register.NEUTRAL, Register.CASUAL):
                return _NEUTRAL_TO_TECHNICAL
        elif target == Register.PEDAGOGICAL:
            if source in (Register.NEUTRAL, Register.FORMAL, Register.TECHNICAL):
                return _NEUTRAL_TO_PEDAGOGICAL
        elif target == Register.NEUTRAL:
            # Neutralize from either direction
            if source == Register.FORMAL:
                return _FORMAL_TO_CASUAL[:6]  # Partial de-formalization
            elif source == Register.CASUAL:
                return _CASUAL_TO_FORMAL[:6]  # Partial formalization

        return []

    def _pedagogical_wrap(self, text: str) -> str:
        """Add pedagogical framing to text."""
        sentences = text.split(". ")
        if len(sentences) > 1 and not any(
            text.startswith(p) for p in _PEDAGOGICAL_PREFIXES
        ):
            # Add framing to first sentence
            text = f"Let's break this down: {text}"
        return text

    def _formalize_structure(self, text: str) -> str:
        """Apply structural formalization (e.g., avoid starting with 'So')."""
        if text.startswith("So ") or text.startswith("so "):
            text = "Therefore, " + text[3:]
        if text.startswith("But ") or text.startswith("but "):
            text = "However, " + text[4:]
        return text

    def _protect_technical(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace technical content with placeholders."""
        placeholders: Dict[str, str] = {}
        counter = 0

        def _sub(match: re.Match) -> str:
            nonlocal counter
            key = f"__REG_TECH_{counter}__"
            placeholders[key] = match.group(0)
            counter += 1
            return key

        protected = self._technical_pattern.sub(_sub, text)
        return protected, placeholders

    def _restore_technical(self, text: str, placeholders: Dict[str, str]) -> str:
        """Restore technical content from placeholders."""
        for key, value in placeholders.items():
            text = text.replace(key, value)
        return text
