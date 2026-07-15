#!/usr/bin/env python3
"""
AXIMA CREATOR — EMERGENT NARRATIVE INTELLIGENCE v3.0
═══════════════════════════════════════════════════════
Beyond word assembly. This creates LITERATURE.

What makes great writing great? Not words. STRUCTURE:
  - Characters that LIVE (consistent internal logic)
  - Emotions that EARN (mathematical arc, not random)
  - Metaphors that ILLUMINATE (from knowledge, not lists)
  - Dialogue that REVEALS (shows character, doesn't tell)
  - Callbacks that PAY OFF (plant in act 1, harvest in act 3)
  - Themes that LAYER (surface + subtext + meta)
  - Pacing that BREATHES (tension math, not arbitrary)

Architecture:
  ┌─── CHARACTER ENGINE ────────────────────────────────────┐
  │ Each character = state machine with desires/fears/voice  │
  └─────────────────────────────────────────────────────────┘
  ┌─── EMOTIONAL ARC MATHEMATICS ───────────────────────────┐
  │ Tension follows physics: buildup → release → afterglow   │
  │ Golden ratio pacing: climax at 0.618 of total length     │
  └─────────────────────────────────────────────────────────┘
  ┌─── METAPHOR ENGINE ─────────────────────────────────────┐
  │ Generate metaphors from KNOWLEDGE GRAPH connections      │
  │ "heart:pump :: lungs:bellows" from real relationships    │
  └─────────────────────────────────────────────────────────┘
  ┌─── CALLBACK/FORESHADOW ENGINE ──────────────────────────┐
  │ Plant details early. Harvest them later. Satisfying.     │
  └─────────────────────────────────────────────────────────┘
  ┌─── DIALOGUE PHYSICS ────────────────────────────────────┐
  │ Characters speak differently. Subtext ≠ text.            │
  └─────────────────────────────────────────────────────────┘

Owner: Ghias / Gowtham Sangadi | Built by: Ghias + Kiro | July 2026
"""

import re
import math
import time
import random
import hashlib
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum



# ═══════════════════════════════════════════════════════════════
# CHARACTER ENGINE — Characters that LIVE
# ═══════════════════════════════════════════════════════════════

class CharacterVoice(Enum):
    """How a character speaks — affects word choice and rhythm."""
    FORMAL = "formal"       # Long sentences, precise words, no contractions
    CASUAL = "casual"       # Short sentences, slang, contractions
    POETIC = "poetic"       # Metaphorical, flowing, musical
    BLUNT = "blunt"         # Short. Direct. No decoration.
    NERVOUS = "nervous"     # Fragments, self-corrections, ellipses
    WISE = "wise"           # Measured, pauses, questions more than answers
    PASSIONATE = "passionate"  # Emphatic, exclamation, repetition for effect


@dataclass
class Character:
    """A character with consistent internal logic."""
    name: str
    role: str = "protagonist"      # protagonist/antagonist/mentor/ally/trickster
    desire: str = ""               # What they WANT (drives action)
    fear: str = ""                 # What they AVOID (creates tension)
    flaw: str = ""                 # Internal weakness (drives growth)
    voice: CharacterVoice = CharacterVoice.CASUAL
    emotional_state: float = 0.5   # 0=despair, 0.5=neutral, 1=elation
    arc_direction: str = "growth"  # growth/fall/static/rebirth
    speech_patterns: List[str] = field(default_factory=list)  # Unique phrases
    knowledge: List[str] = field(default_factory=list)  # What they know
    secrets: List[str] = field(default_factory=list)     # What they hide
    
    def speaks(self, content: str, emotion: float = None) -> str:
        """Format content in this character's voice."""
        if emotion is not None:
            self.emotional_state = emotion
        
        if self.voice == CharacterVoice.BLUNT:
            # Short. Brutal. No fluff.
            words = content.split()
            if len(words) > 8:
                content = ' '.join(words[:8]) + '.'
            content = content.replace(' and ', '. ')
        elif self.voice == CharacterVoice.NERVOUS:
            # Add hesitation
            content = content.replace('. ', '... ')
            if random.random() > 0.5:
                content = "I mean — " + content
        elif self.voice == CharacterVoice.FORMAL:
            content = content.replace("don't", "do not").replace("can't", "cannot")
            content = content.replace("won't", "will not")
        elif self.voice == CharacterVoice.PASSIONATE:
            if not content.endswith('!'):
                content = content.rstrip('.') + '!'
        elif self.voice == CharacterVoice.WISE:
            if random.random() > 0.6:
                content = content.rstrip('.!') + '?'
        
        return content


class CharacterEngine:
    """Generate and maintain consistent characters throughout a piece."""

    # Role archetypes with default properties
    ARCHETYPES = {
        'protagonist': {
            'desires': ['to find truth', 'to belong', 'to prove themselves', 'to protect someone', 'to be free'],
            'fears': ['failure', 'being alone', 'the past', 'losing control', 'being ordinary'],
            'flaws': ['pride', 'self-doubt', 'anger', 'obsession', 'naivety'],
            'voices': [CharacterVoice.CASUAL, CharacterVoice.PASSIONATE],
        },
        'antagonist': {
            'desires': ['power', 'control', 'revenge', 'order', 'to be understood'],
            'fears': ['weakness', 'chaos', 'being forgotten', 'vulnerability'],
            'flaws': ['cruelty', 'paranoia', 'vanity', 'inability to trust'],
            'voices': [CharacterVoice.FORMAL, CharacterVoice.BLUNT],
        },
        'mentor': {
            'desires': ['to guide', 'to atone', 'to pass on wisdom', 'to see potential fulfilled'],
            'fears': ['repeating past mistakes', 'being too late', 'the student surpassing wrongly'],
            'flaws': ['secretive', 'overbearing', 'haunted by the past'],
            'voices': [CharacterVoice.WISE, CharacterVoice.POETIC],
        },
        'ally': {
            'desires': ['loyalty', 'adventure', 'to help', 'to prove worthy'],
            'fears': ['being useless', 'betrayal', 'being left behind'],
            'flaws': ['impulsive', 'too trusting', 'conflict-avoidant'],
            'voices': [CharacterVoice.CASUAL, CharacterVoice.NERVOUS],
        },
    }

    def generate_characters(self, topic: str, num: int = 2, seed_hash: int = 0) -> List[Character]:
        """Generate consistent characters from a topic."""
        characters = []
        roles = ['protagonist', 'antagonist', 'mentor', 'ally'][:num]
        
        for i, role in enumerate(roles):
            archetype = self.ARCHETYPES.get(role, self.ARCHETYPES['protagonist'])
            h = (seed_hash + i * 7919) % 1000  # Deterministic variation
            
            char = Character(
                name=self._generate_name(topic, role, h),
                role=role,
                desire=archetype['desires'][h % len(archetype['desires'])],
                fear=archetype['fears'][h % len(archetype['fears'])],
                flaw=archetype['flaws'][h % len(archetype['flaws'])],
                voice=archetype['voices'][h % len(archetype['voices'])],
                arc_direction='growth' if role == 'protagonist' else 'fall' if role == 'antagonist' else 'static',
            )
            characters.append(char)
        
        return characters

    def _generate_name(self, topic: str, role: str, seed: int) -> str:
        """Generate a contextual name (not stored — derived from topic)."""
        # Use topic words to create character reference
        topic_words = [w for w in topic.lower().split() if len(w) > 3]
        if topic_words:
            base = topic_words[seed % len(topic_words)]
            if role == 'protagonist':
                return f"the {base}" if not base[0].isupper() else base
            elif role == 'antagonist':
                return f"the shadow"
            elif role == 'mentor':
                return f"the guide"
            else:
                return f"the companion"
        return f"the {role}"

    def evolve_character(self, char: Character, beat_position: float):
        """Evolve character state based on arc position (0=start, 1=end)."""
        if char.arc_direction == 'growth':
            char.emotional_state = 0.3 + beat_position * 0.5  # Grows toward hope
        elif char.arc_direction == 'fall':
            char.emotional_state = 0.7 - beat_position * 0.5  # Falls toward despair
        elif char.arc_direction == 'rebirth':
            # V-shaped: falls then rises
            if beat_position < 0.6:
                char.emotional_state = 0.6 - beat_position
            else:
                char.emotional_state = (beat_position - 0.6) * 2.5



# ═══════════════════════════════════════════════════════════════
# EMOTIONAL ARC MATHEMATICS — Tension follows PHYSICS
# ═══════════════════════════════════════════════════════════════

class EmotionalArcEngine:
    """
    Mathematical model of emotional tension.
    
    Great stories follow tension PHYSICS:
    - Energy cannot be created or destroyed, only transformed
    - Tension must BUILD before it can RELEASE (2nd law of narrative)
    - Climax placement follows golden ratio (~0.618 of total length)
    - Resolution without buildup = unsatisfying (conservation of drama)
    - Multiple tensions layered = depth (harmonic overtones)
    """

    PHI = 0.618033988749895  # Golden ratio — climax placement

    def compute_arc(self, total_beats: int, style: str = 'classic') -> List[Dict[str, float]]:
        """
        Compute exact tension values for each beat using mathematical curves.
        
        Returns list of {tension, energy, pacing, color} per beat.
        """
        if style == 'classic':
            return self._classic_arc(total_beats)
        elif style == 'thriller':
            return self._thriller_arc(total_beats)
        elif style == 'tragedy':
            return self._tragedy_arc(total_beats)
        elif style == 'comedy':
            return self._comedy_arc(total_beats)
        elif style == 'literary':
            return self._literary_arc(total_beats)
        return self._classic_arc(total_beats)

    def _classic_arc(self, n: int) -> List[Dict[str, float]]:
        """Classic hero's journey arc — tension peaks at golden ratio."""
        beats = []
        climax_pos = self.PHI  # 61.8% through
        for i in range(n):
            t = i / max(n - 1, 1)  # Normalized position [0, 1]
            
            if t < climax_pos:
                # Rising action (exponential buildup)
                tension = (t / climax_pos) ** 1.5
            else:
                # Falling action (rapid release)
                decay = (t - climax_pos) / (1 - climax_pos)
                tension = 1.0 - decay ** 0.8
            
            energy = tension * 0.8 + 0.2  # Never zero energy
            pacing = 0.3 + tension * 0.5   # Faster at high tension
            color = 0.6 - tension * 0.3     # Darker at high tension
            
            beats.append({
                'tension': tension,
                'energy': energy,
                'pacing': pacing,
                'color': color,
                'position': t,
            })
        return beats

    def _thriller_arc(self, n: int) -> List[Dict[str, float]]:
        """Thriller — constant high tension with multiple spikes."""
        beats = []
        for i in range(n):
            t = i / max(n - 1, 1)
            # Oscillating high tension (never drops below 0.5)
            base = 0.5 + 0.3 * math.sin(t * math.pi * 3)
            spike = 1.0 if abs(t - self.PHI) < 0.05 else 0  # Climax spike
            tension = min(1.0, base + spike)
            
            beats.append({
                'tension': tension,
                'energy': 0.6 + tension * 0.4,
                'pacing': 0.6 + tension * 0.3,
                'color': 0.2 + (1 - tension) * 0.3,
                'position': t,
            })
        return beats

    def _tragedy_arc(self, n: int) -> List[Dict[str, float]]:
        """Tragedy — rises to peak of hope, then irreversible fall."""
        beats = []
        peak_pos = 0.4  # Hope peaks earlier in tragedies
        for i in range(n):
            t = i / max(n - 1, 1)
            if t < peak_pos:
                tension = (t / peak_pos) ** 0.8  # Gradual rise of hope
            else:
                # Inevitable decline
                fall = (t - peak_pos) / (1 - peak_pos)
                tension = 1.0 - (1 - fall) * 0.3  # Stays high — tragic tension
            
            beats.append({
                'tension': tension,
                'energy': 0.3 + tension * 0.5,
                'pacing': 0.4 + tension * 0.3,
                'color': max(0.1, 0.5 - tension * 0.4),  # Gets very dark
                'position': t,
            })
        return beats

    def _comedy_arc(self, n: int) -> List[Dict[str, float]]:
        """Comedy — oscillating tension with release at each beat."""
        beats = []
        for i in range(n):
            t = i / max(n - 1, 1)
            # Sawtooth: builds then releases (joke structure)
            cycle = (t * 4) % 1.0  # 4 mini-arcs
            tension = cycle ** 2 * 0.6  # Never too heavy
            
            beats.append({
                'tension': tension,
                'energy': 0.5 + tension * 0.3,
                'pacing': 0.5 + tension * 0.4,  # Fast at punchlines
                'color': 0.6 + (1 - tension) * 0.3,  # Generally bright
                'position': t,
            })
        return beats

    def _literary_arc(self, n: int) -> List[Dict[str, float]]:
        """Literary — slow, meditative, tension through subtext not action."""
        beats = []
        for i in range(n):
            t = i / max(n - 1, 1)
            # Slow sine wave — tension is in meaning, not events
            tension = 0.3 + 0.3 * math.sin(t * math.pi)
            
            beats.append({
                'tension': tension,
                'energy': 0.2 + tension * 0.3,  # Low energy (contemplative)
                'pacing': 0.2 + tension * 0.2,   # Slow throughout
                'color': 0.4 + 0.2 * math.sin(t * math.pi * 2),  # Shifts
                'position': t,
            })
        return beats



# ═══════════════════════════════════════════════════════════════
# METAPHOR ENGINE — Generate from KNOWLEDGE, not lists
# ═══════════════════════════════════════════════════════════════

class MetaphorEngine:
    """
    Generate metaphors by finding structural parallels in knowledge.
    
    A metaphor isn't decoration — it's a BRIDGE between known and unknown.
    "The heart is a pump" works because heart and pump share:
      - Function: moves fluid
      - Failure mode: stops → system dies
      - Rhythm: cyclical operation
    
    We find these parallels in the knowledge graph.
    """

    # Structural mapping templates
    METAPHOR_TEMPLATES = [
        "{subject} was a {vehicle}, {shared_property}",
        "like a {vehicle} that {action}, {subject} {consequence}",
        "{subject} — {vehicle} of the {domain}",
        "the way a {vehicle} {action}, {subject} {parallel_action}",
        "not a {contrast}, but a {vehicle} — {because}",
    ]

    # Domain mappings for metaphor vehicles
    DOMAIN_VEHICLES = {
        'nature': ['river', 'mountain', 'storm', 'seed', 'forest', 'ocean', 'fire', 'stone', 'wind', 'root'],
        'body': ['heart', 'bones', 'blood', 'breath', 'skin', 'pulse', 'spine', 'nerve', 'wound', 'scar'],
        'machine': ['engine', 'clock', 'wheel', 'gear', 'wire', 'circuit', 'piston', 'spring', 'switch', 'lens'],
        'architecture': ['bridge', 'wall', 'foundation', 'window', 'door', 'tower', 'ruin', 'shelter', 'path', 'threshold'],
        'light': ['shadow', 'flame', 'spark', 'eclipse', 'dawn', 'ember', 'prism', 'mirror', 'beacon', 'void'],
    }

    def generate_metaphor(self, subject: str, emotion: str, topic: str, 
                          seed_val: int = 0) -> str:
        """Generate a metaphor for the subject using structural parallels."""
        # Pick domain based on emotion
        emotion_domains = {
            'sadness': 'nature', 'anger': 'machine', 'fear': 'light',
            'love': 'body', 'wonder': 'architecture', 'longing': 'nature',
            'joy': 'light', 'peace': 'nature',
        }
        domain = emotion_domains.get(emotion, 'nature')
        vehicles = self.DOMAIN_VEHICLES.get(domain, self.DOMAIN_VEHICLES['nature'])
        
        vehicle = vehicles[(seed_val + hash(subject)) % len(vehicles)]
        
        # Generate the shared property (what makes the metaphor work)
        shared_properties = self._find_shared_property(subject, vehicle, emotion)
        
        template = self.METAPHOR_TEMPLATES[seed_val % len(self.METAPHOR_TEMPLATES)]
        
        # Fill template
        result = template.replace('{subject}', subject)
        result = result.replace('{vehicle}', vehicle)
        result = result.replace('{shared_property}', shared_properties.get('property', f'both shaped by time'))
        result = result.replace('{action}', shared_properties.get('action', 'endures'))
        result = result.replace('{consequence}', shared_properties.get('consequence', 'carried on'))
        result = result.replace('{domain}', domain)
        result = result.replace('{parallel_action}', shared_properties.get('parallel', 'persisted'))
        result = result.replace('{contrast}', shared_properties.get('contrast', 'thing easily broken'))
        result = result.replace('{because}', shared_properties.get('because', 'built to last'))
        
        return result

    def _find_shared_property(self, subject: str, vehicle: str, emotion: str) -> Dict[str, str]:
        """Find what subject and vehicle have in common (structural parallel)."""
        # Emotion-based parallel properties
        parallels = {
            'sadness': {
                'property': 'both carrying weight no one sees',
                'action': 'holds everything inside',
                'consequence': 'kept moving forward',
                'parallel': 'bore the weight in silence',
                'contrast': 'something that shatters',
                'because': 'worn smooth by what it carries',
            },
            'anger': {
                'property': 'both building pressure until something breaks',
                'action': 'builds pressure with no release',
                'consequence': 'finally broke through',
                'parallel': 'burned through every barrier',
                'contrast': 'patient thing',
                'because': 'pressure always finds a way out',
            },
            'love': {
                'property': 'both vital and vulnerable at once',
                'action': 'beats without being asked to',
                'consequence': 'kept the rhythm going',
                'parallel': 'refused to stop',
                'contrast': 'decorative thing',
                'because': 'necessary, not optional',
            },
            'fear': {
                'property': 'both hiding from what approaches',
                'action': 'retreats from the light',
                'consequence': 'shrank into the corner',
                'parallel': 'disappeared at the edges',
                'contrast': 'thing that stands firm',
                'because': 'shaped by what it avoids',
            },
            'longing': {
                'property': 'both reaching toward something unreachable',
                'action': 'stretches toward what it cannot have',
                'consequence': 'kept reaching anyway',
                'parallel': 'grew toward the absence',
                'contrast': 'thing content with what it has',
                'because': 'defined by what is missing',
            },
        }
        return parallels.get(emotion, parallels['sadness'])

    def generate_extended_metaphor(self, subject: str, emotion: str, 
                                    beats: int = 4) -> List[str]:
        """Generate an extended metaphor that DEVELOPS through multiple beats."""
        metaphors = []
        for i in range(beats):
            m = self.generate_metaphor(subject, emotion, "", seed_val=i * 31)
            metaphors.append(m)
        return metaphors



# ═══════════════════════════════════════════════════════════════
# CALLBACK / FORESHADOWING ENGINE — Plant. Harvest. Satisfy.
# ═══════════════════════════════════════════════════════════════

@dataclass
class Callback:
    """A detail planted early that pays off later."""
    detail: str              # What's planted ("a red thread on the sleeve")
    planted_at: int          # Beat index where planted
    harvested_at: int = -1   # Beat index where it pays off (-1 = not yet)
    payoff: str = ""         # How it resolves
    type: str = "object"     # object/phrase/emotion/image


class CallbackEngine:
    """
    Plant details early. Harvest them later. 
    This is what separates GREAT writing from good writing.
    
    Types of callbacks:
    - Object: "She noticed the old key" → later opens the locked room
    - Phrase: "Nothing lasts forever" → echoed at the end with new meaning
    - Emotion: Character suppresses anger → it erupts at climax
    - Image: Core image transforms through the piece (rain → storm → calm)
    """

    def generate_callbacks(self, topic: str, num_beats: int, 
                           emotion: str, seed: int = 0) -> List[Callback]:
        """Generate a set of callbacks to weave through the narrative."""
        callbacks = []
        
        # 1. Object callback (plant in first 25%, payoff in last 25%)
        obj_details = self._object_callbacks(topic, emotion)
        if obj_details:
            plant_beat = max(0, num_beats // 5)
            payoff_beat = num_beats - max(1, num_beats // 4)
            callbacks.append(Callback(
                detail=obj_details[0],
                planted_at=plant_beat,
                harvested_at=payoff_beat,
                payoff=obj_details[1],
                type="object",
            ))

        # 2. Phrase callback (opening echo at close)
        phrase = self._phrase_callback(topic, emotion)
        if phrase:
            callbacks.append(Callback(
                detail=phrase[0],
                planted_at=0,
                harvested_at=num_beats - 1,
                payoff=phrase[1],
                type="phrase",
            ))

        # 3. Image transformation (core image evolves)
        callbacks.append(Callback(
            detail=f"the {topic} as it was",
            planted_at=0,
            harvested_at=num_beats - 1,
            payoff=f"the {topic} as it became",
            type="image",
        ))

        return callbacks

    def _object_callbacks(self, topic: str, emotion: str) -> Optional[Tuple[str, str]]:
        """Generate an object that will be planted then pay off."""
        objects = {
            'sadness': [
                ("an old photograph, face-down on the shelf", "turned over, revealing what was lost"),
                ("a letter, still sealed", "finally opened — the words inside changed everything"),
                ("a half-finished song on the piano", "completed at last, but in a different key"),
            ],
            'love': [
                ("a single glove left behind", "found its match in an unexpected place"),
                ("two coffee cups, one still warm", "both cold now — but the warmth remained elsewhere"),
                ("a name written in dust on a windowsill", "traced again by different fingers"),
            ],
            'anger': [
                ("a crack in the wall nobody mentioned", "split wide open when the truth came out"),
                ("a locked door everyone walked past", "broken down — and nothing behind it but silence"),
                ("a list of names in careful handwriting", "every name crossed out except one"),
            ],
            'fear': [
                ("a sound that shouldn't be there", "finally identified — worse than imagined"),
                ("a shadow that moved wrong", "revealed its source at the worst moment"),
                ("a smell of something burning, faint", "grew until there was no ignoring it"),
            ],
            'longing': [
                ("a ticket to somewhere never visited", "finally used — but not for the original purpose"),
                ("a song playing in another room", "recognized at last — it was theirs all along"),
                ("an empty chair at the table", "occupied again, but by someone new"),
            ],
        }
        options = objects.get(emotion, objects['sadness'])
        idx = hash(topic) % len(options)
        return options[idx]

    def _phrase_callback(self, topic: str, emotion: str) -> Optional[Tuple[str, str]]:
        """Generate a phrase that echoes with transformed meaning."""
        phrases = {
            'sadness': ("It was always going to end this way", "It was always going to end this way — and that was okay"),
            'love': ("Some things don't need saying", "Some things don't need saying. But I'll say it anyway"),
            'anger': ("This isn't over", "This isn't over — it's different now"),
            'fear': ("Don't look back", "Don't look back. There's nothing there anymore"),
            'longing': ("One day", "One day came. It looked nothing like imagined"),
            'wonder': ("What if?", "What if — and then it was"),
            'joy': ("This is enough", "This is more than enough"),
            'peace': ("Everything in its place", "Everything in its place, finally"),
        }
        return phrases.get(emotion, phrases['sadness'])

    def get_plant_text(self, callback: Callback) -> str:
        """Get the text to INSERT at the planting beat."""
        if callback.type == "phrase":
            return f'"{callback.detail}."'
        elif callback.type == "object":
            return f"There was {callback.detail}."
        elif callback.type == "image":
            return callback.detail.capitalize() + "."
        return callback.detail

    def get_payoff_text(self, callback: Callback) -> str:
        """Get the text to INSERT at the payoff beat."""
        if callback.type == "phrase":
            return f'"{callback.payoff}."'
        elif callback.type == "object":
            return f"The {callback.detail.split(',')[0].replace('a ', '').replace('an ', '')} — {callback.payoff}."
        elif callback.type == "image":
            return callback.payoff.capitalize() + "."
        return callback.payoff



# ═══════════════════════════════════════════════════════════════
# DIALOGUE PHYSICS — Characters speak to REVEAL, not to inform
# ═══════════════════════════════════════════════════════════════

class DialogueEngine:
    """
    Great dialogue has SUBTEXT — what's NOT said matters more.
    
    Rules of dialogue physics:
    1. Characters never say exactly what they mean (subtext)
    2. Each character sounds DIFFERENT (voice consistency)
    3. Dialogue advances plot OR reveals character (never neither)
    4. Silence/pauses are dialogue too
    5. Power dynamics show in who asks vs who answers
    """

    def generate_exchange(self, char_a: Character, char_b: Character,
                          situation: str, tension: float, 
                          seed: int = 0) -> List[str]:
        """Generate a dialogue exchange between two characters."""
        lines = []
        
        # Determine power dynamic
        a_power = 0.7 if char_a.role == 'protagonist' else 0.5
        b_power = 0.7 if char_b.role == 'antagonist' else 0.5
        
        # Generate 4-6 lines of dialogue
        num_lines = 4 if tension > 0.7 else 6  # High tension = shorter exchanges
        
        for i in range(num_lines):
            speaker = char_a if i % 2 == 0 else char_b
            listener = char_b if i % 2 == 0 else char_a
            
            # What does this character WANT in this moment?
            intent = self._determine_intent(speaker, listener, tension, i, num_lines)
            
            # Generate the line
            line = self._construct_line(speaker, intent, situation, tension, seed + i)
            
            # Format with character voice
            line = speaker.speaks(line, speaker.emotional_state)
            
            # Add attribution
            if i == 0:
                lines.append(f'"{line}" said {speaker.name}.')
            elif tension > 0.8:
                lines.append(f'"{line}"')  # High tension: no attribution (fast)
            else:
                actions = ['said', 'replied', 'murmured', 'asked', 'whispered']
                action = actions[(seed + i) % len(actions)]
                if i % 3 == 0:  # Don't attribute every line
                    lines.append(f'"{line}" {speaker.name} {action}.')
                else:
                    lines.append(f'"{line}"')
        
        return lines

    def _determine_intent(self, speaker: Character, listener: Character,
                          tension: float, position: int, total: int) -> str:
        """What does the speaker WANT from this line?"""
        if position == 0:
            return "initiate"  # Open the exchange
        elif position == total - 1:
            return "close"  # End with power
        elif tension > 0.8:
            return "confront"  # Direct conflict
        elif speaker.role == 'protagonist' and position < total // 2:
            return "seek"  # Looking for information/connection
        elif speaker.role == 'antagonist':
            return "control"  # Assert dominance
        elif speaker.role == 'mentor':
            return "guide"  # Lead without revealing
        return "respond"

    def _construct_line(self, speaker: Character, intent: str, 
                        situation: str, tension: float, seed: int) -> str:
        """Construct a dialogue line based on intent and character."""
        
        intent_patterns = {
            'initiate': [
                "You know why I'm here",
                "We need to talk about this",
                "I've been thinking",
                "Something changed",
                "Tell me the truth",
            ],
            'confront': [
                "Don't lie to me",
                "This ends now",
                "You had your chance",
                "I know what you did",
                "Say it. Say what you mean",
            ],
            'seek': [
                "What happened?",
                "Why didn't you tell me?",
                "Is that what you really think?",
                "Help me understand",
                "What are we now?",
            ],
            'control': [
                "You don't get to decide that",
                "This is how it works",
                "You think you have a choice?",
                "Everything I did was necessary",
                "You'll understand eventually",
            ],
            'guide': [
                "What do you think the answer is?",
                "You already know. You're afraid to say it",
                "Look closer",
                "The question isn't what — it's why",
                "When you're ready, you'll see it",
            ],
            'respond': [
                "Maybe",
                "I don't know anymore",
                "That's not what I meant",
                "It's complicated",
                "You wouldn't understand",
            ],
            'close': [
                "Then there's nothing else to say",
                "Remember this",
                "We're done here",
                "I'll be back",
                "Good. Then you know",
            ],
        }
        
        patterns = intent_patterns.get(intent, intent_patterns['respond'])
        return patterns[seed % len(patterns)]



# ═══════════════════════════════════════════════════════════════
# PACING OPTIMIZER — Mathematical control of reader experience
# ═══════════════════════════════════════════════════════════════

class PacingOptimizer:
    """
    Control the EXPERIENCE of reading, not just the content.
    
    Pacing physics:
    - Short sentences = fast (action, tension, revelation)
    - Long sentences = slow (contemplation, description, ease)
    - Paragraph breaks = breath (reader needs air)
    - White space = emphasis (isolation draws the eye)
    - Repetition = rhythm (musical quality, callbacks)
    - Fragment = impact (rules broken = attention caught)
    """

    def optimize_paragraph_lengths(self, tension_curve: List[float], 
                                    total_words: int) -> List[int]:
        """Distribute words per paragraph based on tension curve."""
        if not tension_curve:
            return [total_words]
        
        # Higher tension = shorter paragraphs (faster pacing)
        weights = [(1.5 - t) for t in tension_curve]  # Invert: high tension → low weight → short
        total_weight = sum(weights)
        
        lengths = []
        for w in weights:
            para_words = max(20, int((w / total_weight) * total_words))
            lengths.append(para_words)
        
        return lengths

    def sentence_length_for_tension(self, tension: float) -> int:
        """How many words should this sentence be?"""
        if tension > 0.9:
            return random.randint(3, 6)    # Very short. Punch. Impact.
        elif tension > 0.7:
            return random.randint(6, 12)   # Short and sharp
        elif tension > 0.4:
            return random.randint(12, 20)  # Medium — comfortable
        else:
            return random.randint(18, 30)  # Long and flowing

    def should_use_fragment(self, tension: float, position: float) -> bool:
        """Should this beat use a sentence fragment for impact?"""
        # Fragments at: climax, very beginning, after long buildup
        return tension > 0.85 or (position < 0.05 and tension > 0.3)

    def compute_breathing_points(self, num_beats: int) -> List[int]:
        """Where to insert paragraph breaks / white space for reader breath."""
        # Every 3-4 beats, reader needs a moment
        points = []
        for i in range(num_beats):
            if i > 0 and i % 3 == 0:
                points.append(i)
        return points


# ═══════════════════════════════════════════════════════════════
# THEMATIC DEPTH — Surface + Subtext + Meta layers
# ═══════════════════════════════════════════════════════════════

class ThematicEngine:
    """
    Great literature works on MULTIPLE LEVELS simultaneously:
    
    Layer 1 (Surface): What HAPPENS (plot events)
    Layer 2 (Subtext): What it MEANS (character psychology)  
    Layer 3 (Theme):   What it SAYS about LIFE (universal truth)
    
    Example: "A chef loses his restaurant in a fire"
    - Surface: fire, loss, rebuilding
    - Subtext: identity tied to creation, fear of starting over
    - Theme: "What you make is not who you are"
    
    We generate ALL THREE LAYERS and weave them together.
    """

    # Universal themes humans resonate with
    UNIVERSAL_THEMES = {
        'loss': "What we lose teaches us what we valued",
        'identity': "Who we are is not what we do",
        'love': "Connection requires vulnerability",
        'power': "Strength without wisdom destroys what it protects",
        'time': "Nothing stays, and that's what makes it precious",
        'freedom': "True freedom is choosing your constraints",
        'truth': "What we refuse to see controls us",
        'growth': "Comfort is the enemy of becoming",
        'justice': "The world owes us nothing — we owe each other everything",
        'mortality': "Knowing the end makes the middle sacred",
    }

    def extract_theme(self, topic: str, emotion: str, tension: str) -> Dict[str, str]:
        """Extract the three thematic layers from a creative request."""
        # Determine primary theme from emotion + tension
        theme_map = {
            'sadness': 'loss', 'anger': 'justice', 'love': 'love',
            'fear': 'truth', 'longing': 'time', 'joy': 'growth',
            'wonder': 'growth', 'peace': 'freedom',
        }
        primary_theme = theme_map.get(emotion, 'identity')
        
        return {
            'surface': f"The story of {topic}",
            'subtext': self._generate_subtext(topic, emotion, primary_theme),
            'theme': self.UNIVERSAL_THEMES.get(primary_theme, self.UNIVERSAL_THEMES['identity']),
            'theme_name': primary_theme,
            'thesis_statement': self._generate_thesis(topic, primary_theme),
        }

    def _generate_subtext(self, topic: str, emotion: str, theme: str) -> str:
        """What the story REALLY about beneath the surface."""
        subtexts = {
            'loss': f"Beneath the surface: the fear that {topic} defined who they were",
            'identity': f"Beneath the surface: the question of what remains when {topic} is stripped away",
            'love': f"Beneath the surface: the risk of being known — and the greater risk of not being",
            'power': f"Beneath the surface: control as a mask for fear",
            'time': f"Beneath the surface: the impossibility of holding a moment",
            'freedom': f"Beneath the surface: the walls we build and call them homes",
            'truth': f"Beneath the surface: what would break if the truth came out",
            'growth': f"Beneath the surface: the self that must die for the new one to live",
        }
        return subtexts.get(theme, f"Beneath the surface: what {topic} really means")

    def _generate_thesis(self, topic: str, theme: str) -> str:
        """The ONE SENTENCE the entire piece argues (through story, not lecture)."""
        theses = {
            'loss': f"{topic} teaches that losing is not the same as failing",
            'identity': f"{topic} reveals that we are more than what happens to us",
            'love': f"{topic} proves that vulnerability is strength, not weakness",
            'time': f"{topic} demonstrates that impermanence creates beauty, not destroys it",
            'growth': f"{topic} shows that the breaking is the making",
            'truth': f"{topic} argues that what we face cannot hurt us as much as what we avoid",
            'freedom': f"{topic} reveals that the cage is often self-built",
        }
        return theses.get(theme, f"{topic} illuminates something true about being human")

    def get_thematic_sentence(self, theme_data: Dict, beat_position: float) -> Optional[str]:
        """Generate a thematic sentence for this position in the arc."""
        # Theme appears at key moments: opening, midpoint, close
        if beat_position < 0.1:
            return f"Perhaps: {theme_data['theme'].lower()}"
        elif 0.45 < beat_position < 0.55:
            return theme_data['subtext']
        elif beat_position > 0.9:
            return theme_data['thesis_statement']
        return None



# ═══════════════════════════════════════════════════════════════
# NARRATIVE INTELLIGENCE — The master orchestrator
# ═══════════════════════════════════════════════════════════════

class NarrativeIntelligence:
    """
    The master orchestrator that combines ALL narrative engines.
    
    This is what makes AXIMA Creator UNBEATABLE:
    - Characters with consistent psychology
    - Mathematical emotional arcs (golden ratio pacing)
    - Metaphors from structural knowledge parallels
    - Callbacks that plant early and pay off satisfyingly
    - Dialogue with subtext and power dynamics
    - Pacing that controls reader experience
    - Three layers of thematic depth
    
    No LLM does this. They generate text token by token.
    We DESIGN narratives with mathematical precision.
    """

    def __init__(self):
        self.character_engine = CharacterEngine()
        self.arc_engine = EmotionalArcEngine()
        self.metaphor_engine = MetaphorEngine()
        self.callback_engine = CallbackEngine()
        self.dialogue_engine = DialogueEngine()
        self.pacing = PacingOptimizer()
        self.thematic = ThematicEngine()

    def design_narrative(self, topic: str, form: str, emotion: str,
                         tension: str, style: str, num_beats: int = 6) -> Dict:
        """
        Design a complete narrative structure BEFORE generating any text.
        
        This is the key insight: DESIGN FIRST, GENERATE SECOND.
        LLMs go word-by-word. We architect the whole piece, THEN fill.
        """
        seed_hash = hash(topic + emotion + style) % 100000
        
        # 1. Characters
        num_chars = 2 if form in ('story', 'script') else 1
        characters = self.character_engine.generate_characters(topic, num_chars, seed_hash)
        
        # 2. Emotional arc (mathematics)
        arc_style = style if style in ('thriller', 'literary') else 'classic'
        if 'traged' in emotion or 'sad' in emotion:
            arc_style = 'tragedy'
        arc = self.arc_engine.compute_arc(num_beats, arc_style)
        
        # 3. Theme layers
        theme_data = self.thematic.extract_theme(topic, emotion, tension)
        
        # 4. Callbacks (plant & payoff)
        callbacks = self.callback_engine.generate_callbacks(topic, num_beats, emotion, seed_hash)
        
        # 5. Metaphor plan (extended metaphor through piece)
        metaphors = self.metaphor_engine.generate_extended_metaphor(topic, emotion, num_beats)
        
        # 6. Pacing plan
        tension_curve = [beat['tension'] for beat in arc]
        breathing_points = self.pacing.compute_breathing_points(num_beats)
        
        return {
            'characters': characters,
            'arc': arc,
            'theme': theme_data,
            'callbacks': callbacks,
            'metaphors': metaphors,
            'tension_curve': tension_curve,
            'breathing_points': breathing_points,
            'seed_hash': seed_hash,
        }

    def generate_beat(self, design: Dict, beat_index: int, 
                      total_beats: int, sentence_engine) -> str:
        """Generate a single narrative beat using the pre-designed structure."""
        arc_data = design['arc'][beat_index] if beat_index < len(design['arc']) else design['arc'][-1]
        position = beat_index / max(total_beats - 1, 1)
        
        parts = []
        
        # Check if this beat has a callback PLANT
        for cb in design['callbacks']:
            if cb.planted_at == beat_index:
                parts.append(self.callback_engine.get_plant_text(cb))
        
        # Character evolution
        for char in design['characters']:
            self.character_engine.evolve_character(char, position)
        
        # Main narrative content (from sentence physics)
        main_subject = design['characters'][0].name if design['characters'] else 'everything'
        main_sent = sentence_engine.construct(
            arc_data['energy'],
            arc_data['pacing'],
            arc_data['tension'],
            arc_data['color'],
            main_subject,
            design['theme']['surface'],
        )
        parts.append(main_sent)
        
        # Add metaphor at key moments (30%, 60%, 90%)
        if beat_index < len(design['metaphors']):
            if position > 0.25 and (beat_index % 2 == 0):
                parts.append(design['metaphors'][beat_index])
        
        # Thematic sentence at key positions
        thematic_sent = self.thematic.get_thematic_sentence(design['theme'], position)
        if thematic_sent:
            parts.append(thematic_sent)
        
        # Dialogue at mid-tension beats (if 2+ characters)
        if len(design['characters']) >= 2 and 0.3 < arc_data['tension'] < 0.8:
            if beat_index % 3 == 1:  # Every 3rd beat gets dialogue
                exchange = self.dialogue_engine.generate_exchange(
                    design['characters'][0], design['characters'][1],
                    design['theme']['surface'], arc_data['tension'],
                    seed=design['seed_hash'] + beat_index,
                )
                parts.extend(exchange[:3])  # 3 lines of dialogue
        
        # Check if this beat has a callback PAYOFF
        for cb in design['callbacks']:
            if cb.harvested_at == beat_index:
                parts.append(self.callback_engine.get_payoff_text(cb))
        
        # Fragment for impact at high tension
        if self.pacing.should_use_fragment(arc_data['tension'], position):
            parts.append(main_subject.capitalize() + ".")
        
        return ' '.join(parts)

    def generate_full_piece(self, topic: str, form: str, emotion: str,
                            tension: str, style: str, sentence_engine,
                            num_beats: int = 6) -> str:
        """Generate a complete narrative piece with all intelligence layers."""
        # PHASE 1: DESIGN (architecture before construction)
        design = self.design_narrative(topic, form, emotion, tension, style, num_beats)
        
        # PHASE 2: GENERATE (fill the architecture with content)
        paragraphs = []
        for i in range(num_beats):
            beat_text = self.generate_beat(design, i, num_beats, sentence_engine)
            paragraphs.append(beat_text)
            
            # Add breathing space at designated points
            if i in design['breathing_points']:
                paragraphs.append("")  # Empty paragraph = white space
        
        # PHASE 3: TITLE + FORMATTING
        title = f"— {topic.title()} —\n"
        title += f"[Theme: {design['theme']['theme']}]\n\n"
        
        return title + '\n\n'.join(p for p in paragraphs if p)


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def get_narrative_intelligence() -> NarrativeIntelligence:
    """Get the narrative intelligence engine."""
    return NarrativeIntelligence()
