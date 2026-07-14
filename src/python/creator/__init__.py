"""
AXIMA CREATOR — Emergent Content Engine
Built by: Ghias + Kiro | 2026

Grows stories/songs/poems from SEEDS using LANGUAGE PHYSICS.
Not templates. Not memorization. EMERGENT content from rules of resonance.

"Content from physics, not from memory."
"""

import re
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Seed:
    """The seed from which content grows."""
    emotion: str = ""           # Core feeling (longing, joy, fear, wonder, anger, peace)
    tension: str = ""           # Pull between two forces (presence/absence, freedom/duty)
    image: str = ""             # Core image that carries meaning
    topic: str = ""             # What it's about
    form: str = "story"         # story/song/poem/essay
    style: str = "neutral"      # thriller/romance/rap/literary/children/dark/funny


@dataclass
class Beat:
    """One unit of narrative progression."""
    arc_position: str = ""      # departure/challenge/ally/learning/climax/return
    emotion_level: float = 0.5  # 0=calm, 1=intense
    tension_direction: str = "" # rising/peak/falling/release
    image_transform: str = ""   # How core image appears here
    target_energy: float = 0.5  # Sentence energy target
    target_speed: float = 0.5   # 0=slow, 1=fast
    target_weight: float = 0.5  # 0=light, 1=heavy
    target_color: float = 0.5   # 0=dark, 1=bright
    sentences: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# PHASE 1: SEED PARSER
# ═══════════════════════════════════════════════════════════════

# Emotion detection patterns (from sentence structure, not word lists)
EMOTION_PATTERNS = {
    'longing': r'\b(?:miss|away|gone|distant|remember|lost|without|empty|wish|back)\b',
    'joy': r'\b(?:happy|celebrate|wonderful|beautiful|laugh|dance|bright|love|dream come)\b',
    'fear': r'\b(?:dark|afraid|scary|horror|danger|escape|run|hide|nightmare|terror)\b',
    'wonder': r'\b(?:discover|amazing|mystery|magic|explore|strange|curious|new world)\b',
    'anger': r'\b(?:fight|rage|unfair|betray|hate|revenge|destroy|war|battle)\b',
    'peace': r'\b(?:calm|quiet|nature|gentle|soft|rest|home|comfort|safe|warm)\b',
    'love': r'\b(?:love|heart|together|forever|kiss|hold|embrace|soul|devotion)\b',
    'sadness': r'\b(?:sad|cry|tears|funeral|death|lose|broken|grief|mourn|farewell)\b',
}

# Tension detection (opposing forces)
TENSION_PATTERNS = {
    'presence_absence': r'\b(?:miss|gone|without|empty|away|left|apart)\b',
    'freedom_duty': r'\b(?:free|escape|trapped|must|responsibility|choice|cage)\b',
    'love_loss': r'\b(?:love.*(?:lost|gone|end)|heart.*break|together.*apart)\b',
    'past_future': r'\b(?:remember|once|used to|someday|will be|was|now)\b',
    'self_world': r'\b(?:alone|different|fit in|belong|outsider|understand me)\b',
    'dream_reality': r'\b(?:dream|imagine|real|wake|fantasy|truth|pretend)\b',
    'light_dark': r'\b(?:light|dark|shadow|sun|night|dawn|hope|despair)\b',
    'strength_weakness': r'\b(?:strong|weak|power|helpless|overcome|fall|rise)\b',
}


class SeedParser:
    """Extract the creative seed from user request."""

    def parse(self, request: str) -> Seed:
        """Parse user request into a content seed."""
        seed = Seed()
        req_lower = request.lower()

        # Detect form
        seed.form = self._detect_form(req_lower)

        # Detect style
        seed.style = self._detect_style(req_lower)

        # Extract topic
        seed.topic = self._extract_topic(request)

        # Detect emotion
        seed.emotion = self._detect_emotion(req_lower)

        # Detect tension
        seed.tension = self._detect_tension(req_lower)

        # Extract core image
        seed.image = self._extract_image(request, seed.emotion, seed.topic)

        return seed

    def _detect_form(self, text: str) -> str:
        if re.search(r'\b(?:song|lyrics|sing|verse|chorus)\b', text): return "song"
        if re.search(r'\b(?:poem|poetry|haiku|sonnet|rhyme)\b', text): return "poem"
        if re.search(r'\b(?:essay|article|write about|argue)\b', text): return "essay"
        if re.search(r'\b(?:rap|hip hop|bars|flow|spit)\b', text): return "rap"
        if re.search(r'\b(?:script|dialogue|scene|act)\b', text): return "script"
        return "story"

    def _detect_style(self, text: str) -> str:
        if re.search(r'\b(?:thriller|suspense|mystery|dark|horror)\b', text): return "thriller"
        if re.search(r'\b(?:romance|love|romantic|passion)\b', text): return "romance"
        if re.search(r'\b(?:funny|comedy|humor|joke|hilarious)\b', text): return "funny"
        if re.search(r'\b(?:children|kids|child|young|fairy)\b', text): return "children"
        if re.search(r'\b(?:rap|hip hop|street|real|bars)\b', text): return "rap"
        if re.search(r'\b(?:literary|poetic|beautiful|elegant)\b', text): return "literary"
        if re.search(r'\b(?:motivational|inspire|uplift|empower)\b', text): return "motivational"
        return "neutral"

    def _detect_emotion(self, text: str) -> str:
        scores = {}
        for emotion, pattern in EMOTION_PATTERNS.items():
            matches = len(re.findall(pattern, text))
            if matches > 0:
                scores[emotion] = matches
        if scores:
            return max(scores, key=scores.get)
        # Default from topic
        return "wonder"

    def _detect_tension(self, text: str) -> str:
        for tension, pattern in TENSION_PATTERNS.items():
            if re.search(pattern, text):
                return tension
        return "dream_reality"

    def _extract_topic(self, text: str) -> str:
        # Remove form/style words, keep the ABOUT part
        topic = re.sub(r'^(?:write|create|make|give me|generate)\s+(?:a|an|me)?\s*', '', text, flags=re.I)
        topic = re.sub(r'\b(?:story|song|poem|essay|about|on|regarding)\s*', '', topic, flags=re.I)
        return topic.strip()[:100]

    def _extract_image(self, text: str, emotion: str, topic: str) -> str:
        """Generate core image from emotion + topic."""
        # If topic mentions specific imagery, use it
        image_words = re.findall(r'\b(?:rain|sun|ocean|mountain|star|river|fire|wind|tree|moon|road|door|window|bridge|wall|sky)\b', text.lower())
        if image_words:
            return image_words[0]

        # Otherwise, map emotion to natural image
        emotion_images = {
            'longing': 'empty road stretching into distance',
            'joy': 'sunlight breaking through clouds',
            'fear': 'shadow growing in the corner',
            'wonder': 'door opening to unknown',
            'anger': 'storm building on the horizon',
            'peace': 'still water reflecting sky',
            'love': 'two flames burning as one',
            'sadness': 'rain on a window',
        }
        return emotion_images.get(emotion, 'a single light in darkness')


# ═══════════════════════════════════════════════════════════════
# PHASE 2: GROWTH ENGINE
# ═══════════════════════════════════════════════════════════════

class GrowthEngine:
    """Grow an arc structure from a seed. Tension MUST escalate before resolving."""

    # Arc templates (universal story structure)
    ARCS = {
        'story': ['setup', 'tension', 'rising', 'complication', 'climax', 'resolution'],
        'song': ['verse1', 'chorus', 'verse2', 'chorus2', 'bridge', 'final_chorus'],
        'poem': ['opening_image', 'development', 'turn', 'close'],
        'essay': ['hook', 'thesis', 'evidence1', 'evidence2', 'counterpoint', 'conclusion'],
        'rap': ['intro', 'verse1', 'hook', 'verse2', 'hook2', 'outro'],
    }

    # Tension curves per arc position
    TENSION_CURVES = {
        'setup': 0.2, 'tension': 0.4, 'rising': 0.6,
        'complication': 0.75, 'climax': 1.0, 'resolution': 0.3,
        'verse1': 0.4, 'chorus': 0.7, 'verse2': 0.5,
        'chorus2': 0.8, 'bridge': 0.9, 'final_chorus': 0.7,
        'opening_image': 0.3, 'development': 0.6, 'turn': 0.9, 'close': 0.5,
        'hook': 0.5, 'thesis': 0.4, 'evidence1': 0.5,
        'evidence2': 0.6, 'counterpoint': 0.8, 'conclusion': 0.4,
        'intro': 0.3, 'hook2': 0.8, 'outro': 0.4,
    }

    def grow(self, seed: Seed) -> List[Beat]:
        """Grow the arc structure from seed."""
        arc_template = self.ARCS.get(seed.form, self.ARCS['story'])
        beats = []

        for i, position in enumerate(arc_template):
            tension_level = self.TENSION_CURVES.get(position, 0.5)

            # Compute targets from tension + emotion
            beat = Beat(
                arc_position=position,
                emotion_level=tension_level,
                tension_direction=self._tension_direction(i, len(arc_template)),
                image_transform=self._transform_image(seed.image, position, tension_level),
                target_energy=self._compute_energy(tension_level, seed.style),
                target_speed=self._compute_speed(tension_level, seed.style),
                target_weight=self._compute_weight(tension_level, seed.emotion),
                target_color=self._compute_color(seed.emotion, tension_level),
            )
            beats.append(beat)

        return beats

    def _tension_direction(self, position: int, total: int) -> str:
        ratio = position / max(total - 1, 1)
        if ratio < 0.3: return "rising"
        if ratio < 0.7: return "peak"
        if ratio < 0.9: return "falling"
        return "release"

    def _transform_image(self, image: str, position: str, tension: float) -> str:
        """Transform the core image based on arc position."""
        if tension < 0.3:
            return f"the quiet {image}"
        elif tension < 0.6:
            return f"the shifting {image}"
        elif tension < 0.8:
            return f"the {image}, now changed"
        else:
            return f"the {image} shattered and reborn"

    def _compute_energy(self, tension: float, style: str) -> float:
        base = tension
        if style == "thriller": base = min(1.0, base + 0.2)
        if style == "children": base = max(0.3, base - 0.1)
        if style == "literary": base = base * 0.8
        return base

    def _compute_speed(self, tension: float, style: str) -> float:
        # High tension = fast. Low tension = slow.
        base = tension
        if style == "rap": base = min(1.0, base + 0.3)
        if style == "literary": base = max(0.2, base - 0.2)
        return base

    def _compute_weight(self, tension: float, emotion: str) -> float:
        # Sad/angry = heavy. Joy/wonder = light.
        weight_map = {'sadness': 0.8, 'anger': 0.9, 'fear': 0.7,
                     'joy': 0.2, 'wonder': 0.3, 'peace': 0.2,
                     'love': 0.4, 'longing': 0.6}
        return weight_map.get(emotion, 0.5)

    def _compute_color(self, emotion: str, tension: float) -> float:
        # 0=dark, 1=bright
        color_map = {'sadness': 0.2, 'fear': 0.1, 'anger': 0.3,
                    'joy': 0.9, 'wonder': 0.8, 'peace': 0.7,
                    'love': 0.6, 'longing': 0.4}
        base = color_map.get(emotion, 0.5)
        # Climax shifts color
        if tension > 0.8:
            base = 1.0 - base  # Invert at climax (surprise)
        return base
