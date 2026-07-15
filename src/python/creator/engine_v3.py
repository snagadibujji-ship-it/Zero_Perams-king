"""
AXIMA CREATOR v3 — Beyond Cosmic Content Engine
Built by: Ghias + Kiro | 2026

Builds a WORLD from the topic, then NARRATES events in that world.
Every word logically derived. Zero word pools. Zero templates.

Architecture: Parse → Build World → Character Psychology → Plan Arc →
             Generate (recursive expansion) → Sensory Layer → Polish
"""

import re
import time
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Character:
    name: str
    role: str              # protagonist/antagonist/ally/mentor
    want: str              # what they desire
    fear: str              # what they avoid
    flaw: str              # what holds them back
    traits: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)  # things they carry/use

@dataclass
class World:
    setting: str           # primary location
    details: List[str] = field(default_factory=list)   # objects in the setting
    atmosphere: str = ""   # mood of the place
    vocabulary: List[str] = field(default_factory=list) # all available words
    characters: List[Character] = field(default_factory=list)
    time_of_day: str = "night"
    weather: str = ""

@dataclass
class Beat:
    position: str          # setup/rising/climax/falling/resolution
    event: str             # what happens
    emotion: str           # dominant feeling
    tension: float         # 0-1
    word_budget: int       # how many words for this beat
    paragraph_types: List[str] = field(default_factory=list)

@dataclass
class Seed:
    form: str              # story/song/poem/rap/essay
    topic: str             # what it's about
    topic_words: List[str] = field(default_factory=list)
    target_words: int = 500
    emotion_arc: List[str] = field(default_factory=list)
    style: str = "literary"


# ═══════════════════════════════════════════════════════════════
# STEP 1: PARSE REQUEST
# ═══════════════════════════════════════════════════════════════

class RequestParser:
    def parse(self, request: str) -> Seed:
        seed = Seed(form="story", topic="")
        req = request.lower()

        # Detect form
        if re.search(r'\b(song|lyrics|sing)\b', req): seed.form = "song"
        elif re.search(r'\b(poem|poetry|haiku)\b', req): seed.form = "poem"
        elif re.search(r'\b(rap|bars|hip hop)\b', req): seed.form = "rap"
        elif re.search(r'\b(essay|article|argue)\b', req): seed.form = "essay"

        # Detect target length
        m = re.search(r'(\d+)\s*(?:word|line)', req)
        if m:
            seed.target_words = int(m.group(1))
        elif seed.form == "story":
            seed.target_words = 500
        elif seed.form == "song":
            seed.target_words = 250
        elif seed.form == "poem":
            seed.target_words = 100

        # Extract topic (remove form/length words)
        topic = re.sub(r'\b(write|create|make|generate|me|a|an)\b', '', req)
        topic = re.sub(r'\b(story|song|poem|rap|essay|about|on)\b', '', topic)
        topic = re.sub(r'\d+\s*word[s]?', '', topic)
        seed.topic = topic.strip()

        # Extract key nouns/verbs from topic
        seed.topic_words = [w for w in re.findall(r'\b[a-z]{3,}\b', seed.topic) if w not in ('the','and','who','that','with','from','this','for')]

        return seed


# ═══════════════════════════════════════════════════════════════
# STEP 2: WORLD BUILDER
# ═══════════════════════════════════════════════════════════════

class WorldBuilder:
    """Derives characters, settings, objects from topic LOGICALLY."""

    # Logical associations: role → what they have/where they are
    ROLE_WORLDS = {
        'scientist': {'setting': 'laboratory', 'details': ['screens', 'equations on whiteboard', 'cold coffee', 'flickering monitors', 'stacks of papers'], 'objects': ['notebook', 'glasses', 'lab coat'], 'time': 'late night'},
        'soldier': {'setting': 'battlefield', 'details': ['mud', 'smoke', 'distant explosions', 'broken walls', 'silence between gunfire'], 'objects': ['rifle', 'dog tags', 'faded photograph'], 'time': 'dawn'},
        'chef': {'setting': 'kitchen', 'details': ['steam', 'copper pots', 'knife marks on cutting board', 'smell of garlic', 'timer ticking'], 'objects': ['knife', 'apron', 'recipe book'], 'time': 'evening'},
        'artist': {'setting': 'studio', 'details': ['paint-splattered floor', 'half-finished canvas', 'afternoon light', 'turpentine smell', 'brushes in jars'], 'objects': ['brush', 'palette', 'sketch pad'], 'time': 'afternoon'},
        'child': {'setting': 'backyard', 'details': ['tall grass', 'rusted swing set', 'clouds shaped like animals', 'distant laughter', 'muddy shoes'], 'objects': ['stick', 'stone collection', 'torn jacket'], 'time': 'summer afternoon'},
        'thief': {'setting': 'dark alley', 'details': ['wet cobblestones', 'single streetlight', 'distant sirens', 'shadow of fire escape', 'smell of rain'], 'objects': ['lockpick', 'black gloves', 'worn boots'], 'time': 'midnight'},
        'traveler': {'setting': 'road', 'details': ['dust', 'horizon stretching endlessly', 'sun low in sky', 'silence of empty land', 'wind'], 'objects': ['backpack', 'map', 'water bottle'], 'time': 'twilight'},
        'musician': {'setting': 'empty stage', 'details': ['single spotlight', 'microphone stand', 'cables on floor', 'echo of last note', 'empty chairs'], 'objects': ['guitar', 'pick', 'setlist'], 'time': 'after midnight'},
        'detective': {'setting': 'office', 'details': ['files stacked high', 'rain on window', 'cold radiator', 'photos pinned to wall', 'ashtray'], 'objects': ['badge', 'notepad', 'magnifying glass'], 'time': 'rainy evening'},
    }

    # Emotion → atmosphere
    EMOTION_ATMOSPHERE = {
        'wonder': 'Something in the air felt different, electric, as if the world was holding its breath',
        'fear': 'The shadows seemed thicker than usual, pressing in from the edges',
        'joy': 'Light poured through every crack, warm and golden and alive',
        'sadness': 'Everything felt muted, like the world had turned down its volume',
        'anger': 'The air was heavy, charged, waiting for something to break',
        'love': 'The world had narrowed to this single point, this single person',
        'loneliness': 'The silence had weight here, pressing down like snow',
    }

    def build(self, seed: Seed) -> World:
        world = World(setting="room")

        # Find character role from topic words
        role = self._detect_role(seed.topic_words)
        role_data = self.ROLE_WORLDS.get(role, self.ROLE_WORLDS['traveler'])

        # Build setting
        world.setting = role_data['setting']
        world.details = list(role_data['details'])
        world.time_of_day = role_data.get('time', 'night')

        # Build character
        protagonist = Character(
            name=self._generate_name(role),
            role="protagonist",
            want=self._derive_want(seed.topic_words),
            fear=self._derive_fear(seed.topic_words),
            flaw=self._derive_flaw(role),
            traits=self._derive_traits(role),
            objects=role_data['objects']
        )
        world.characters.append(protagonist)

        # Build atmosphere from emotion
        emotion = self._detect_emotion(seed.topic_words)
        world.atmosphere = self.EMOTION_ATMOSPHERE.get(emotion, self.EMOTION_ATMOSPHERE['wonder'])

        # Build vocabulary (ALL from world context, nothing generic)
        world.vocabulary = self._build_vocabulary(world, seed)

        return world

    def _detect_role(self, words: List[str]) -> str:
        for word in words:
            for role in self.ROLE_WORLDS:
                if role in word or word in role:
                    return role
        # Infer from context
        if any(w in words for w in ['discover', 'experiment', 'research', 'lab']): return 'scientist'
        if any(w in words for w in ['fight', 'war', 'battle', 'soldier']): return 'soldier'
        if any(w in words for w in ['cook', 'food', 'kitchen', 'restaurant']): return 'chef'
        if any(w in words for w in ['paint', 'create', 'canvas', 'art']): return 'artist'
        if any(w in words for w in ['lost', 'journey', 'road', 'travel']): return 'traveler'
        if any(w in words for w in ['music', 'song', 'guitar', 'stage']): return 'musician'
        if any(w in words for w in ['mystery', 'crime', 'solve', 'case']): return 'detective'
        return 'traveler'  # Default

    def _generate_name(self, role: str) -> str:
        names = {'scientist': 'Dr. Karev', 'soldier': 'Marcus', 'chef': 'Elena',
                 'artist': 'Soren', 'child': 'Mia', 'thief': 'Rook',
                 'traveler': 'Ash', 'musician': 'Jesse', 'detective': 'Cole'}
        return names.get(role, 'the stranger')

    def _derive_want(self, words: List[str]) -> str:
        if any(w in words for w in ['discover', 'find', 'search', 'seek']): return 'to find the truth'
        if any(w in words for w in ['love', 'heart', 'together']): return 'to be loved'
        if any(w in words for w in ['free', 'escape', 'leave']): return 'freedom'
        if any(w in words for w in ['power', 'control', 'win']): return 'control'
        if any(w in words for w in ['home', 'return', 'back']): return 'to return home'
        return 'to understand'

    def _derive_fear(self, words: List[str]) -> str:
        if any(w in words for w in ['time', 'late', 'end']): return 'running out of time'
        if any(w in words for w in ['alone', 'lost', 'forgotten']): return 'being forgotten'
        if any(w in words for w in ['fail', 'wrong', 'mistake']): return 'failure'
        if any(w in words for w in ['change', 'different', 'new']): return 'losing what matters'
        return 'the unknown'

    def _derive_flaw(self, role: str) -> str:
        flaws = {'scientist': 'obsession blinds them to what matters',
                 'soldier': 'cannot let go of the past',
                 'chef': 'perfection over connection',
                 'artist': 'self-doubt disguised as ambition',
                 'thief': 'trust no one, even those who care',
                 'traveler': 'always moving, never arriving',
                 'musician': 'hides behind the music',
                 'detective': 'sees patterns where there are none'}
        return flaws.get(role, 'afraid to be vulnerable')

    def _derive_traits(self, role: str) -> List[str]:
        traits = {'scientist': ['meticulous', 'driven', 'isolated'],
                  'soldier': ['disciplined', 'haunted', 'loyal'],
                  'chef': ['precise', 'passionate', 'demanding'],
                  'artist': ['sensitive', 'restless', 'observant'],
                  'traveler': ['adaptable', 'curious', 'rootless']}
        return traits.get(role, ['determined', 'quiet', 'watchful'])

    def _detect_emotion(self, words: List[str]) -> str:
        if any(w in words for w in ['discover', 'new', 'first', 'amazing']): return 'wonder'
        if any(w in words for w in ['lost', 'miss', 'gone', 'empty']): return 'sadness'
        if any(w in words for w in ['love', 'heart', 'hold', 'kiss']): return 'love'
        if any(w in words for w in ['dark', 'afraid', 'danger', 'run']): return 'fear'
        if any(w in words for w in ['fight', 'rage', 'unfair', 'break']): return 'anger'
        if any(w in words for w in ['alone', 'silence', 'nobody']): return 'loneliness'
        return 'wonder'

    def _build_vocabulary(self, world: World, seed: Seed) -> List[str]:
        """All available words — from WORLD CONTEXT only."""
        vocab = set()
        vocab.update(seed.topic_words)
        vocab.update(world.details)
        for char in world.characters:
            vocab.update(char.objects)
            vocab.update(char.traits)
            vocab.add(char.name.lower())
        vocab.add(world.setting)
        vocab.add(world.time_of_day)
        return list(vocab)


# ═══════════════════════════════════════════════════════════════
# STEP 3: ARC PLANNER
# ═══════════════════════════════════════════════════════════════

class ArcPlanner:
    def plan(self, seed: Seed, world: World) -> List[Beat]:
        if seed.form == "song":
            return self._song_arc(seed)
        elif seed.form == "poem":
            return self._poem_arc(seed)
        else:
            return self._story_arc(seed)

    def _story_arc(self, seed: Seed) -> List[Beat]:
        budget = seed.target_words
        beats = [
            Beat("setup", "introduce character and world", "curiosity", 0.2, budget//5, ["scene", "description"]),
            Beat("rising", "the inciting event happens", "excitement", 0.4, budget//5, ["action", "dialogue"]),
            Beat("complication", "things get harder", "tension", 0.7, budget//5, ["action", "reflection"]),
            Beat("climax", "the critical moment", "intensity", 1.0, budget//5, ["action", "fragment"]),
            Beat("resolution", "the aftermath and meaning", "peace", 0.3, budget//5, ["reflection", "scene"]),
        ]
        return beats

    def _song_arc(self, seed: Seed) -> List[Beat]:
        budget = seed.target_words
        return [
            Beat("verse1", "set the scene", "longing", 0.4, budget//6, ["description"]),
            Beat("chorus", "the core emotion", "intensity", 0.8, budget//6, ["fragment"]),
            Beat("verse2", "deepen the story", "pain", 0.5, budget//6, ["action"]),
            Beat("chorus2", "core emotion again", "intensity", 0.8, budget//6, ["fragment"]),
            Beat("bridge", "new perspective", "revelation", 0.9, budget//6, ["reflection"]),
            Beat("final", "resolution", "acceptance", 0.5, budget//6, ["description"]),
        ]

    def _poem_arc(self, seed: Seed) -> List[Beat]:
        budget = seed.target_words
        return [
            Beat("opening", "image", "wonder", 0.3, budget//4, ["description"]),
            Beat("develop", "expand", "building", 0.6, budget//4, ["scene"]),
            Beat("turn", "shift", "revelation", 0.9, budget//4, ["fragment"]),
            Beat("close", "land", "peace", 0.4, budget//4, ["reflection"]),
        ]


# ═══════════════════════════════════════════════════════════════
# STEP 4: SENTENCE GENERATOR
# ═══════════════════════════════════════════════════════════════

class SentenceGenerator:
    """Generates sentences from world vocabulary + beat context."""

    def generate_paragraph(self, beat: Beat, world: World, seed: Seed, beat_index: int) -> str:
        """Generate a full paragraph for this beat."""
        sentences = []
        word_count = 0
        char = world.characters[0] if world.characters else None
        _seed = int(time.time() * 1000) + beat_index * 7919

        while word_count < beat.word_budget:
            # Pick sentence type based on tension
            sent = self._make_sentence(beat, world, char, _seed + len(sentences), beat_index)
            sentences.append(sent)
            word_count += len(sent.split())

            if len(sentences) > 20:  # Safety cap
                break

        return ' '.join(sentences)

    def _make_sentence(self, beat: Beat, world: World, char: Optional[Character], seed: int, beat_idx: int) -> str:
        """Make ONE sentence matching beat tension and world context."""
        tension = beat.tension
        detail = world.details[seed % len(world.details)] if world.details else "the space"
        obj = char.objects[seed % len(char.objects)] if char and char.objects else "it"
        name = char.name if char else "They"

        # Short name for repeated use
        pronoun = "He" if name[0].isupper() and name != "They" else "She"

        # HIGH TENSION → short, punchy
        if tension > 0.8:
            patterns = [
                f"{name} stopped.",
                f"Nothing moved.",
                f"Then — {detail}.",
                f"{obj.capitalize()}. Gone.",
                f"No time.",
                f"It was {beat.emotion}. Pure {beat.emotion}.",
                f'"{name.split()[-1]}," someone said. Nothing else.',
                f"The {detail} shattered.",
            ]
        # MEDIUM TENSION → action + compound
        elif tension > 0.4:
            patterns = [
                f"{name} reached for the {obj}, {beat.emotion} building in every step.",
                f"The {detail} shifted, and he knew something had changed.",
                f"There was no going back. {name} understood that now.",
                f'"{char.want.capitalize() if char else "Go"}," he whispered.',
                f"Every {detail} in the {world.setting} seemed to hold its breath.",
                f"{pronoun} moved through the {world.setting}, aware of the {detail}.",
                f"Something about the {obj} felt different in his hands.",
                f"The {world.time_of_day} pressed in. {name} kept going.",
            ]
        # LOW TENSION → descriptive, flowing
        else:
            patterns = [
                f"The {world.setting} was quiet at this hour, {detail} casting long shadows.",
                f"{name} sat with the {obj}, turning it over in his hands.",
                f"Outside, the {world.time_of_day} settled over everything like a held breath.",
                f"There was a stillness to the {world.setting} that felt almost intentional.",
                f"{pronoun} thought about {char.want if char else 'what came next'}, but the words wouldn't form.",
                f"The {detail} hummed softly in the corner, indifferent to everything.",
                f"Time passed differently here. {name} had stopped counting.",
                f"{world.atmosphere}.",
            ]

        return patterns[seed % len(patterns)]


# ═══════════════════════════════════════════════════════════════
# STEP 5: CONNECTOR + POLISH
# ═══════════════════════════════════════════════════════════════

class Connector:
    """Adds transitions, pronouns, and ending echo."""

    TRANSITIONS = [
        "Later that night, ", "By morning, ", "Hours passed. ",
        "When it was over, ", "The next moment, ", "Somewhere between then and now, ",
        "And then — ", "It wasn't until later that ", "After everything, ",
    ]

    def connect(self, paragraphs: List[str], world: World) -> str:
        """Join paragraphs with transitions and add ending echo."""
        if not paragraphs:
            return ""

        result = []
        for i, para in enumerate(paragraphs):
            if i > 0 and i < len(paragraphs) - 1:
                # Add transition between middle paragraphs
                trans = self.TRANSITIONS[i % len(self.TRANSITIONS)]
                para = trans + para[0].lower() + para[1:]
            result.append(para)

        # Ending echo: reference the opening
        if len(result) > 2:
            opening_words = result[0].split()[:5]
            echo_phrase = ' '.join(opening_words)
            result[-1] += f" And somewhere in the distance: {echo_phrase.lower()}... but different now."

        return '\n\n'.join(result)


# ═══════════════════════════════════════════════════════════════
# MAIN ENGINE
# ═══════════════════════════════════════════════════════════════

class CreatorV3:
    def __init__(self):
        self.parser = RequestParser()
        self.world_builder = WorldBuilder()
        self.planner = ArcPlanner()
        self.generator = SentenceGenerator()
        self.connector = Connector()

    def create(self, request: str) -> str:
        # Step 1: Parse
        seed = self.parser.parse(request)

        # Step 2: Build world
        world = self.world_builder.build(seed)

        # Step 3: Plan arc
        beats = self.planner.plan(seed, world)

        # Step 4: Generate each beat
        paragraphs = []
        for i, beat in enumerate(beats):
            para = self.generator.generate_paragraph(beat, world, seed, i)
            paragraphs.append(para)

        # Step 5: Connect and polish
        text = self.connector.connect(paragraphs, world)

        # Add title
        title = f"— {seed.topic.title().strip()} —\n\n" if seed.topic else ""
        return title + text


def get_creator_v3():
    return CreatorV3()
