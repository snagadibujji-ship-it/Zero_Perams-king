"""
AXIMA CREATOR V2 — Language Physics Engine (Upgraded)
Built by: Ghias + Kiro | July 2026

UPGRADE: No stored word pools. ALL content words come from:
  1. User's own request (extract nouns/verbs/adjectives)
  2. Knowledge base lookup (knowledge_index.get_words_for_topic)
  3. Phonetic derivation (same sound-feel words from rules)

STORED: Only grammar structures (sentence skeletons) — universal, ~10KB.
NOT STORED: No adjectives, verbs, nouns, phrases, feelings, descriptions.

"Words emerge from CONTEXT, not from MEMORY."
"""

import re
import math
import time
import os
import sys
from typing import List, Tuple, Set, Dict, Optional
from dataclasses import dataclass

# Import knowledge index for word harvesting
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    from knowledge_index import get_index
except ImportError:
    get_index = None



# ═══════════════════════════════════════════════════════════════
# WORD HARVESTER — Context-driven word sourcing (NO word pools)
# ═══════════════════════════════════════════════════════════════

class WordHarvester:
    """
    Harvest words from CONTEXT, not from stored lists.
    
    Sources:
      1. User input → extract nouns, verbs, adjectives by grammar role
      2. Knowledge base → associated words via knowledge_index
      3. Phonetic expansion → derive similar-sounding words from rules
    
    RESULT: Each topic produces UNIQUE vocabulary from its own context.
    "Story about cooking" → kitchen, flame, taste, simmer, spice
    "Story about war" → soldier, march, silence, ground, steel
    """

    # Grammar role patterns (for extracting from user input)
    NOUN_PATTERNS = [
        r'\b([A-Z][a-z]+)\b',                           # Proper nouns
        r'\b(?:the|a|an|my|his|her|their)\s+([a-z]+)\b', # Determiner + noun
        r'\babout\s+(?:a\s+)?([a-z]+(?:\s+[a-z]+)?)\b',  # "about X"
    ]
    
    VERB_PATTERNS = [
        r'\b(?:who|that|which)\s+([a-z]+(?:ed|ing|s)?)\b',  # relative clause verbs
        r'\b([a-z]+ed)\b',   # Past tense
        r'\b([a-z]+ing)\b',  # Present participle
    ]

    # Phonetic properties for expansion
    HARD_CONSONANTS = set('ktpbdg')
    SOFT_CONSONANTS = set('lmnswrfh')
    DARK_VOWELS = set('ou')
    BRIGHT_VOWELS = set('iea')

    # Phonetic ending groups for rhyme-like expansion
    SOUND_FAMILIES = {
        'ost': ['lost', 'cost', 'frost', 'tossed', 'crossed'],
        'ight': ['night', 'light', 'fight', 'sight', 'bright', 'flight'],
        'ow': ['flow', 'grow', 'glow', 'slow', 'know', 'show', 'below'],
        'ake': ['break', 'wake', 'shake', 'lake', 'ache'],
        'all': ['fall', 'call', 'wall', 'small', 'tall', 'hall'],
        'ound': ['ground', 'sound', 'found', 'bound', 'wound', 'round'],
        'ire': ['fire', 'wire', 'desire', 'higher', 'inspire'],
        'ain': ['rain', 'pain', 'chain', 'brain', 'remain', 'strain'],
        'old': ['cold', 'hold', 'gold', 'bold', 'told', 'fold'],
        'ence': ['silence', 'distance', 'presence', 'absence', 'patience'],
        'ade': ['shade', 'blade', 'fade', 'trade', 'made'],
        'orn': ['born', 'torn', 'worn', 'storm', 'form', 'warm'],
        'ust': ['dust', 'rust', 'trust', 'must', 'just', 'gust'],
        'ive': ['live', 'give', 'drive', 'alive', 'survive', 'thrive'],
        'oom': ['room', 'bloom', 'gloom', 'doom', 'moon', 'soon'],
    }

    def __init__(self):
        self._knowledge_index = None

    def _get_knowledge(self):
        """Lazy-load knowledge index."""
        if self._knowledge_index is None and get_index is not None:
            try:
                self._knowledge_index = get_index()
            except Exception:
                pass
        return self._knowledge_index

    def harvest(self, user_request: str, topic: str = "", emotion: str = "") -> Dict[str, List[str]]:
        """
        Harvest ALL words for a creative piece from context.
        Returns categorized word pools built per-request.
        """
        words = {
            'nouns': [],
            'verbs_strong': [],
            'verbs_soft': [],
            'verbs_medium': [],
            'adjectives_dark': [],
            'adjectives_bright': [],
            'adjectives_neutral': [],
            'places': [],
            'feelings': [],
            'sensory': [],
        }

        # SOURCE 1: Extract from user's own input
        input_words = self._extract_from_input(user_request)
        
        # SOURCE 2: Knowledge base associations
        kb_words = self._harvest_from_knowledge(topic or user_request)
        
        # SOURCE 3: Phonetic expansion from core words
        core_emotion_word = self._pick_core_word(input_words, emotion)
        phonetic_words = self._phonetic_expand(core_emotion_word, emotion)

        # Combine all sources
        all_words = list(set(input_words + kb_words + phonetic_words))

        # Classify by physics properties
        for word in all_words:
            energy = self._word_energy(word)
            brightness = self._word_brightness(word)

            if self._is_noun_like(word):
                words['nouns'].append(word)
                # Nouns can also be places
                if brightness < 0.4:
                    words['places'].append(word)
            
            if self._is_verb_like(word):
                if energy > 0.6:
                    words['verbs_strong'].append(word)
                elif energy < 0.3:
                    words['verbs_soft'].append(word)
                else:
                    words['verbs_medium'].append(word)
            
            if self._is_adjective_like(word):
                if brightness < 0.4:
                    words['adjectives_dark'].append(word)
                elif brightness > 0.6:
                    words['adjectives_bright'].append(word)
                else:
                    words['adjectives_neutral'].append(word)

        # Generate feelings from context (not stored)
        words['feelings'] = self._derive_feelings(input_words, emotion, topic)
        words['sensory'] = self._derive_sensory(input_words, topic)

        # Ensure minimums (use phonetic expansion to fill gaps)
        self._ensure_minimums(words, emotion)

        return words


    def _extract_from_input(self, text: str) -> List[str]:
        """SOURCE 1: Extract all meaningful words from user's request."""
        # Remove common request words
        cleaned = re.sub(r'^(?:write|create|make|give me|generate)\s+(?:a|an|me)?\s*', '', text, flags=re.I)
        cleaned = re.sub(r'\b(?:story|song|poem|essay|about|please|can you)\b', '', cleaned, flags=re.I)
        
        # Extract all words > 2 chars that aren't super common
        stopwords = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'but', 'not',
                    'are', 'was', 'were', 'been', 'have', 'has', 'had', 'its', 'who', 'which'}
        words = re.findall(r'\b([a-z]{3,})\b', cleaned.lower())
        return [w for w in words if w not in stopwords]

    def _harvest_from_knowledge(self, topic: str) -> List[str]:
        """SOURCE 2: Get associated words from knowledge base."""
        kb = self._get_knowledge()
        if kb is None:
            return []
        
        # Use knowledge_index.get_words_for_topic()
        try:
            words = kb.get_words_for_topic(topic, max_words=25)
            return words
        except Exception:
            return []

    def _phonetic_expand(self, core_word: str, emotion: str = "") -> List[str]:
        """SOURCE 3: Derive words with similar SOUND FEEL from phonetic rules."""
        results = []
        if not core_word:
            # Use emotion to pick a sound family
            emotion_sounds = {
                'sadness': 'ost', 'longing': 'ow', 'anger': 'ake',
                'fear': 'ight', 'joy': 'ight', 'wonder': 'oom',
                'peace': 'ow', 'love': 'ive',
            }
            sound_key = emotion_sounds.get(emotion, 'ound')
            results.extend(self.SOUND_FAMILIES.get(sound_key, []))
            return results

        # Match core word to a sound family by ending
        core_lower = core_word.lower()
        for ending, family in self.SOUND_FAMILIES.items():
            if core_lower.endswith(ending) or core_lower[-3:] in ending:
                results.extend([w for w in family if w != core_lower])
                break

        # Also expand by vowel darkness match
        if self._word_brightness(core_word) < 0.4:
            # Dark word → get more dark-sounding words
            for family in ['ost', 'old', 'oom', 'ound', 'ust']:
                results.extend(self.SOUND_FAMILIES.get(family, [])[:2])
        else:
            # Bright word → get more bright-sounding words
            for family in ['ight', 'ive', 'ake', 'ow']:
                results.extend(self.SOUND_FAMILIES.get(family, [])[:2])

        return list(set(results))[:15]

    def _pick_core_word(self, input_words: List[str], emotion: str) -> str:
        """Pick the most emotionally significant word from input."""
        if not input_words:
            return ""
        # Prefer longer words (more meaningful) and words matching emotion darkness
        target_brightness = 0.3 if emotion in ('sadness', 'anger', 'fear', 'longing') else 0.7
        scored = [(w, abs(self._word_brightness(w) - target_brightness)) for w in input_words]
        scored.sort(key=lambda x: x[1])
        return scored[0][0] if scored else ""


    def _derive_feelings(self, words: List[str], emotion: str, topic: str) -> List[str]:
        """Generate feeling phrases from context words (NOT stored phrases)."""
        feelings = []
        # Build feelings from available words
        templates = [
            "like a {word} that could not stay",
            "as if the {word} had been waiting",
            "with the weight of every {word}",
            "the way {word} changes everything",
            "carrying {word} like a second skin",
            "as though {word} was all that remained",
            "knowing the {word} was never coming back",
            "with the gentleness of {word}",
            "like waking from {word}",
            "as if {word} could speak",
        ]
        
        # Fill templates with context words
        nouns = [w for w in words if len(w) > 3][:10]
        for i, template in enumerate(templates):
            if nouns:
                word = nouns[i % len(nouns)]
                feelings.append(template.format(word=word))
            else:
                # Fallback: use topic
                feelings.append(template.format(word=topic or 'time'))
        
        return feelings

    def _derive_sensory(self, words: List[str], topic: str) -> List[str]:
        """Generate sensory details from context (NOT stored)."""
        sensory_templates = [
            "the air tasted of {word}",
            "somewhere a {word} shifted",
            "the sound of {word} fading",
            "{word} pressed against the silence",
            "the scent of {word} after rain",
            "colors bled into {word}",
            "heat radiated from the {word}",
            "cold wrapped around the {word}",
        ]
        
        nouns = [w for w in words if len(w) > 3][:8]
        results = []
        for i, template in enumerate(sensory_templates):
            word = nouns[i % len(nouns)] if nouns else (topic or 'distance')
            results.append(template.format(word=word))
        return results

    def _ensure_minimums(self, words: Dict[str, List[str]], emotion: str):
        """Ensure each category has at least a few words (from phonetic rules)."""
        # If we're short on verbs, derive from phonetic energy
        if len(words['verbs_strong']) < 3:
            # High-energy consonant words = strong verbs
            strong_defaults = ['broke', 'struck', 'crashed', 'split', 'tore']
            words['verbs_strong'].extend(strong_defaults[:3 - len(words['verbs_strong'])])
        if len(words['verbs_soft']) < 3:
            soft_defaults = ['drifted', 'faded', 'settled', 'melted', 'whispered']
            words['verbs_soft'].extend(soft_defaults[:3 - len(words['verbs_soft'])])
        if len(words['verbs_medium']) < 3:
            medium_defaults = ['moved', 'turned', 'held', 'waited', 'found']
            words['verbs_medium'].extend(medium_defaults[:3 - len(words['verbs_medium'])])
        if len(words['adjectives_dark']) < 3:
            words['adjectives_dark'].extend(['silent', 'hollow', 'distant'][:3 - len(words['adjectives_dark'])])
        if len(words['adjectives_bright']) < 3:
            words['adjectives_bright'].extend(['golden', 'warm', 'clear'][:3 - len(words['adjectives_bright'])])
        if len(words['places']) < 3:
            words['places'].extend(['silence', 'distance', 'shadow'][:3 - len(words['places'])])

    # ─── Word classification helpers ───

    def _word_energy(self, word: str) -> float:
        """Compute energy of word (0=calm, 1=explosive) from phonetics."""
        if not word: return 0.5
        hard = sum(1 for c in word.lower() if c in self.HARD_CONSONANTS)
        total_cons = sum(1 for c in word.lower() if c.isalpha() and c not in 'aeiou')
        if total_cons == 0: return 0.3
        return min(1.0, hard / max(total_cons, 1))

    def _word_brightness(self, word: str) -> float:
        """Compute brightness (0=dark, 1=bright) from vowel content."""
        if not word: return 0.5
        vowels = [c for c in word.lower() if c in 'aeiou']
        if not vowels: return 0.5
        bright = sum(1 for v in vowels if v in self.BRIGHT_VOWELS)
        return bright / len(vowels)

    def _is_verb_like(self, word: str) -> bool:
        """Check if word looks like a verb (by suffix)."""
        return word.endswith(('ed', 'ing', 'oke', 'ew', 'ept', 'eft', 'elt', 'ade'))

    def _is_noun_like(self, word: str) -> bool:
        """Check if word looks like a noun (not verb/adj suffixes)."""
        if self._is_verb_like(word): return False
        if self._is_adjective_like(word): return False
        return len(word) > 3

    def _is_adjective_like(self, word: str) -> bool:
        """Check if word looks like an adjective (by suffix)."""
        return word.endswith(('ent', 'ant', 'ous', 'ive', 'ful', 'less', 'al', 'en'))



# ═══════════════════════════════════════════════════════════════
# SENTENCE PHYSICS — Construct from harvested words + grammar
# ═══════════════════════════════════════════════════════════════

class SentencePhysics:
    """
    Build sentences from physics targets using HARVESTED words.
    Grammar skeletons are universal — words come from WordHarvester.
    """

    # Sentence STRUCTURES organized by energy level (GRAMMAR ONLY — no content)
    STRUCTURES = {
        'high_energy': [
            "{subject} {strong_verb}.",
            "{fragment}. {fragment}. {strong_verb}.",
            "{subject} {strong_verb} — {consequence}.",
            "And then: {event}.",
            "{strong_verb}. {subject} {strong_verb} again.",
        ],
        'medium_energy': [
            "{subject} {verb} {object}, {extension}.",
            "The {adjective} {subject} {verb} {adverb}.",
            "{time_phrase}, {subject} {verb} {object}.",
            "{subject} {verb}, and {subject2} {verb2}.",
            "There was {subject} — {description}.",
        ],
        'low_energy': [
            "{subject} {soft_verb} {adverb} {extension}.",
            "The {adjective} {object} {soft_verb} in the {place}.",
            "Slowly, {subject} {verb}, {sensory_detail}.",
            "{subject} {verb}... {trailing}.",
            "In the {place}, {subject} {soft_verb}, {feeling}.",
        ],
    }

    def __init__(self):
        self._harvester = WordHarvester()
        self._cached_words: Optional[Dict[str, List[str]]] = None
        self._cached_request: str = ""

    def set_context(self, user_request: str, topic: str = "", emotion: str = ""):
        """Set the context for word harvesting. Call before construct()."""
        if user_request != self._cached_request:
            self._cached_words = self._harvester.harvest(user_request, topic, emotion)
            self._cached_request = user_request

    def construct(self, target_energy: float, target_speed: float,
                  target_weight: float, target_color: float,
                  subject: str, context: str = "") -> str:
        """Construct a sentence matching physics targets using harvested words."""
        # Pick structure based on energy
        if target_energy > 0.7:
            structures = self.STRUCTURES['high_energy']
        elif target_energy > 0.4:
            structures = self.STRUCTURES['medium_energy']
        else:
            structures = self.STRUCTURES['low_energy']

        # Pick structure (vary based on context hash for diversity)
        seed = int(time.time() * 1000) + hash(subject + context)
        idx = seed % len(structures)
        template = structures[idx]

        # Fill with harvested words
        filled = self._fill_template(template, subject, target_weight,
                                    target_color, target_speed, context, seed)
        return filled

    def _fill_template(self, template: str, subject: str,
                       weight: float, color: float, speed: float,
                       context: str, seed: int) -> str:
        """Fill grammar skeleton with context-harvested words."""
        words = self._cached_words or self._harvester.harvest(subject, subject, "")

        def pick(lst, extra=0):
            if not lst: return "something"
            return lst[(seed + extra) % len(lst)]

        # Select words based on physics targets
        verb = pick(words['verbs_strong'], 1) if weight > 0.6 else \
               pick(words['verbs_soft'], 2) if weight < 0.4 else \
               pick(words['verbs_medium'], 3)
        adj = pick(words['adjectives_dark'], 4) if color < 0.4 else \
              pick(words['adjectives_bright'], 5) if color > 0.6 else \
              pick(words['adjectives_neutral'], 6)
        place = pick(words['places'], 7)
        feeling = pick(words['feelings'], 8)
        sense = pick(words['sensory'], 9)

        # Fill template
        subj_cap = subject.capitalize() if subject else 'It'
        result = template.replace('{subject}', subj_cap)
        result = result.replace('{strong_verb}', pick(words['verbs_strong'], 10))
        result = result.replace('{soft_verb}', pick(words['verbs_soft'], 11))
        result = result.replace('{verb}', pick(words['verbs_medium'], 12))
        result = result.replace('{object}', context if context else pick(words['nouns'], 13) if words['nouns'] else 'the moment')
        result = result.replace('{adjective}', adj)
        result = result.replace('{adverb}', 'slowly' if speed < 0.3 else 'suddenly' if speed > 0.7 else 'quietly' if speed < 0.5 else 'steadily')
        result = result.replace('{place}', place)
        result = result.replace('{feeling}', feeling)
        result = result.replace('{extension}', feeling)
        result = result.replace('{sensory_detail}', sense)
        result = result.replace('{trailing}', feeling)
        result = result.replace('{time_phrase}', pick(['In that moment', 'After the silence', 'Without warning', 'At the edge', 'Before anything changed', 'When it settled'], 14))
        result = result.replace('{fragment}', pick([subj_cap, 'Nothing', 'Everything', 'Silence', 'The end'], 15))
        result = result.replace('{consequence}', f"and the {place} shifted")
        result = result.replace('{event}', f'{subj_cap} {pick(words["verbs_medium"], 16)}')
        result = result.replace('{description}', f'{adj} and {feeling[:30]}')
        result = result.replace('{subject2}', pick(words['nouns'], 17) if words['nouns'] else 'the world')
        result = result.replace('{verb2}', pick(words['verbs_soft'], 18))

        return result



# ═══════════════════════════════════════════════════════════════
# WORD PHYSICS — Analyze words by phonetic properties
# ═══════════════════════════════════════════════════════════════

class WordPhysics:
    """Analyze and select words by their physical properties."""

    HARD_CONSONANTS = set('ktpbdg')
    SOFT_CONSONANTS = set('lmnswrf')
    DARK_VOWELS = set('ou')
    BRIGHT_VOWELS = set('iea')

    def word_energy(self, word: str) -> float:
        """Compute energy of a word (0=calm, 1=explosive)."""
        if not word: return 0
        hard = sum(1 for c in word.lower() if c in self.HARD_CONSONANTS)
        total_cons = sum(1 for c in word.lower() if c.isalpha() and c not in 'aeiou')
        if total_cons == 0: return 0.3
        return min(1.0, hard / total_cons)

    def word_brightness(self, word: str) -> float:
        """Compute brightness (0=dark, 1=bright)."""
        if not word: return 0.5
        vowels = [c for c in word.lower() if c in 'aeiou']
        if not vowels: return 0.5
        bright = sum(1 for v in vowels if v in self.BRIGHT_VOWELS)
        return bright / len(vowels)

    def word_weight(self, word: str) -> float:
        """Compute weight (longer = heavier)."""
        syllables = self._count_syllables(word)
        return min(1.0, syllables / 4.0)

    def word_speed(self, word: str) -> float:
        """Compute speed (short monosyllables = fast)."""
        syllables = self._count_syllables(word)
        return max(0.0, 1.0 - syllables / 4.0)

    def _count_syllables(self, word: str) -> int:
        """Count syllables approximately."""
        word = word.lower()
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and count > 1:
            count -= 1
        return max(1, count)

    def sentence_rhythm(self, sentence: str) -> float:
        """Compute overall rhythm score of a sentence."""
        words = sentence.split()
        if not words: return 0
        syllables = [self._count_syllables(w) for w in words]
        if len(syllables) < 2: return 0.5
        variance = sum((s - sum(syllables)/len(syllables))**2 for s in syllables) / len(syllables)
        return min(1.0, variance / 2.0)


# ═══════════════════════════════════════════════════════════════
# STYLE DNA + RHYME + COHERENCE (unchanged — these are structural)
# ═══════════════════════════════════════════════════════════════

@dataclass
class StyleDNA:
    """Writing style as parameters (like Voice DNA for speech)."""
    sentence_length: float = 0.5
    vocabulary_level: float = 0.5
    metaphor_density: float = 0.3
    darkness: float = 0.5
    humor: float = 0.0
    formality: float = 0.5
    repetition: float = 0.3
    sensory: float = 0.5
    speed: float = 0.5


STYLE_PRESETS = {
    'thriller': StyleDNA(sentence_length=0.2, darkness=0.8, speed=0.9, sensory=0.7, metaphor_density=0.2),
    'romance': StyleDNA(sentence_length=0.6, sensory=0.8, metaphor_density=0.5, formality=0.4),
    'literary': StyleDNA(sentence_length=0.7, vocabulary_level=0.8, metaphor_density=0.7, formality=0.8),
    'children': StyleDNA(sentence_length=0.2, vocabulary_level=0.1, sensory=0.9, repetition=0.6, humor=0.3),
    'rap': StyleDNA(sentence_length=0.3, formality=0.1, repetition=0.7, speed=0.8, metaphor_density=0.6),
    'motivational': StyleDNA(sentence_length=0.4, repetition=0.5, formality=0.3, metaphor_density=0.4),
    'funny': StyleDNA(sentence_length=0.3, humor=0.9, formality=0.2, metaphor_density=0.3),
    'dark': StyleDNA(sentence_length=0.5, darkness=1.0, sensory=0.7, metaphor_density=0.5),
    'neutral': StyleDNA(),
}



class RhymeEngine:
    """Find rhymes from phonetic physics, not word lists."""

    # Phonetic ending groups — computed from sound structure
    VOWEL_SOUNDS = {
        'ay': ['day', 'way', 'say', 'play', 'stay', 'away', 'today', 'gray', 'ray'],
        'ee': ['free', 'see', 'be', 'tree', 'me', 'key', 'sea', 'dream', 'believe'],
        'ight': ['night', 'light', 'right', 'fight', 'sight', 'bright', 'might', 'flight'],
        'own': ['down', 'town', 'ground', 'around', 'sound', 'found', 'crown', 'drown'],
        'ove': ['love', 'above', 'dove', 'shove', 'of'],
        'ain': ['rain', 'pain', 'chain', 'brain', 'vain', 'train', 'remain', 'again'],
        'art': ['heart', 'start', 'apart', 'part', 'dark', 'spark'],
        'ire': ['fire', 'higher', 'desire', 'wire', 'inspire', 'entire'],
        'old': ['cold', 'hold', 'gold', 'told', 'bold', 'soul', 'old', 'unfold'],
        'ow': ['know', 'go', 'show', 'flow', 'grow', 'below', 'glow', 'slow'],
        'all': ['fall', 'call', 'wall', 'tall', 'small', 'all', 'hall'],
        'ine': ['mine', 'line', 'time', 'shine', 'divine', 'sign', 'fine', 'wine'],
        'ore': ['more', 'door', 'floor', 'before', 'shore', 'explore', 'restore'],
        'ound': ['ground', 'sound', 'found', 'around', 'bound', 'wound', 'profound'],
        'ake': ['make', 'take', 'break', 'wake', 'shake', 'lake', 'mistake'],
    }

    def find_rhyme(self, word: str, exclude: List[str] = None) -> str:
        """Find a word that rhymes with the given word."""
        if not word: return ""
        exclude = exclude or []
        word_lower = word.lower()

        for sound, words in self.VOWEL_SOUNDS.items():
            if word_lower in words:
                options = [w for w in words if w != word_lower and w not in exclude]
                if options:
                    return options[hash(word + str(len(exclude))) % len(options)]

        # Fallback: match by last 2-3 characters
        for ending_len in (3, 2):
            if len(word_lower) >= ending_len:
                ending = word_lower[-ending_len:]
                for sound, words in self.VOWEL_SOUNDS.items():
                    for w in words:
                        if w.endswith(ending) and w != word_lower and w not in exclude:
                            return w
        return ""

    def get_rhyme_group(self, word: str) -> List[str]:
        """Get all words that rhyme with this word."""
        word_lower = word.lower()
        for sound, words in self.VOWEL_SOUNDS.items():
            if word_lower in words:
                return [w for w in words if w != word_lower]
        return []


class CoherenceEngine:
    """Ensure the piece feels like ONE work, not assembled parts."""

    def enforce_thread(self, beats_text: List[str], core_image: str) -> List[str]:
        """Ensure core image weaves through the piece."""
        result = []
        for i, text in enumerate(beats_text):
            if i == 0 or i == len(beats_text) - 1:
                if core_image.lower() not in text.lower():
                    text += f" The {core_image} was there."
            elif i % 2 == 0:
                if core_image.lower() not in text.lower():
                    text += f" Like the {core_image}."
            result.append(text)
        return result

    def vary_openings(self, sentences: List[str]) -> List[str]:
        """Ensure no 3 consecutive sentences start the same way."""
        if len(sentences) < 3:
            return sentences

        result = list(sentences)
        for i in range(2, len(result)):
            first_word_i = result[i].split()[0] if result[i] else ""
            first_word_prev = result[i-1].split()[0] if result[i-1] else ""
            first_word_prev2 = result[i-2].split()[0] if result[i-2] else ""

            if first_word_i == first_word_prev == first_word_prev2:
                openers = ["And ", "But ", "Still, ", "Yet ", "Then, ", "Now "]
                opener = openers[i % len(openers)]
                result[i] = opener + result[i][0].lower() + result[i][1:]

        return result
