"""
AXIMA CREATOR — Main Engine
Grows stories/songs/poems from seeds using language physics.
"""

from typing import List
from . import SeedParser, GrowthEngine, Seed, Beat
from .physics import SentencePhysics, WordPhysics, RhymeEngine, CoherenceEngine, STYLE_PRESETS


class Creator:
    """The AXIMA Content Creator. Grows content from seeds."""

    def __init__(self):
        self.seed_parser = SeedParser()
        self.growth = GrowthEngine()
        self.sentence = SentencePhysics()
        self.words = WordPhysics()
        self.rhyme = RhymeEngine()
        self.coherence = CoherenceEngine()

    def create(self, request: str) -> str:
        """Create content from a user request.
        
        "Write a story about a lost dog"
        "Write a song about missing someone"
        "Write a poem about the ocean"
        """
        # Step 1: Parse seed
        seed = self.seed_parser.parse(request)

        # Step 2: Grow arc
        beats = self.growth.grow(seed)

        # Step 3: Generate content per form
        if seed.form == "song":
            return self._create_song(seed, beats)
        elif seed.form == "poem":
            return self._create_poem(seed, beats)
        elif seed.form == "rap":
            return self._create_rap(seed, beats)
        elif seed.form == "essay":
            return self._create_essay(seed, beats)
        else:
            return self._create_story(seed, beats)

    def _create_story(self, seed: Seed, beats: List[Beat]) -> str:
        """Generate a story."""
        paragraphs = []
        style = STYLE_PRESETS.get(seed.style, STYLE_PRESETS['neutral'])

        for i, beat in enumerate(beats):
            sentences = []
            # 3-5 sentences per beat
            num_sentences = 3 if style.speed > 0.6 else 5 if style.speed < 0.3 else 4

            for j in range(num_sentences):
                # Vary subject across sentences
                subjects = [seed.topic, 'the world', 'everything', 'silence', 'the moment', seed.image]
                subj = subjects[(i * num_sentences + j) % len(subjects)]

                sent = self.sentence.construct(
                    beat.target_energy,
                    beat.target_speed,
                    beat.target_weight,
                    beat.target_color,
                    subj,
                    beat.image_transform
                )
                sentences.append(sent)

            # Vary openings
            sentences = self.coherence.vary_openings(sentences)
            paragraphs.append(' '.join(sentences))

        # Apply thread (core image weaves through)
        paragraphs = self.coherence.enforce_thread(paragraphs, seed.image)

        # Format
        title = f"— {seed.topic.title()} —\n\n" if seed.topic else ""
        return title + '\n\n'.join(paragraphs)

    def _create_song(self, seed: Seed, beats: List[Beat]) -> str:
        """Generate a song with verse/chorus/bridge structure."""
        sections = []
        chorus_lines = []

        for i, beat in enumerate(beats):
            lines = []
            is_chorus = 'chorus' in beat.arc_position

            # Generate 4 lines per section
            for j in range(4):
                subjects = [seed.topic, 'you', 'I', 'we', seed.image, 'the night']
                subj = subjects[(i * 4 + j) % len(subjects)]

                line = self.sentence.construct(
                    beat.target_energy, beat.target_speed,
                    beat.target_weight, beat.target_color,
                    subj, beat.image_transform
                )

                # For songs: shorter lines
                words = line.split()
                if len(words) > 10:
                    line = ' '.join(words[:10])

                lines.append(line)

            # Try to add rhyme (last word of line 1 rhymes with line 2, etc.)
            for k in range(0, len(lines) - 1, 2):
                last_word = lines[k].rstrip('.!?,;:').split()[-1] if lines[k].split() else ""
                rhyme_word = self.rhyme.find_rhyme(last_word)
                if rhyme_word and lines[k + 1].split():
                    # Replace last word of next line with rhyme
                    words = lines[k + 1].split()
                    words[-1] = rhyme_word
                    lines[k + 1] = ' '.join(words)

            # Store chorus for repetition
            if is_chorus:
                if not chorus_lines:
                    chorus_lines = lines
                else:
                    lines = chorus_lines  # Repeat chorus

            # Format section
            label = beat.arc_position.replace('_', ' ').title()
            section = f"[{label}]\n" + '\n'.join(lines)
            sections.append(section)

        title = f"🎵 {seed.topic.title()}\n\n" if seed.topic else "🎵\n\n"
        return title + '\n\n'.join(sections)

    def _create_poem(self, seed: Seed, beats: List[Beat]) -> str:
        """Generate a poem."""
        stanzas = []

        for i, beat in enumerate(beats):
            lines = []
            # 3-4 lines per stanza
            for j in range(3):
                subjects = [seed.topic, seed.image, 'silence', 'the world', 'time']
                subj = subjects[(i * 3 + j) % len(subjects)]

                line = self.sentence.construct(
                    beat.target_energy, beat.target_speed,
                    beat.target_weight, beat.target_color,
                    subj, beat.image_transform
                )
                # Poems: trim to ~8 words max
                words = line.split()
                if len(words) > 8:
                    line = ' '.join(words[:8])
                lines.append(line)

            stanzas.append('\n'.join(lines))

        title = f"✨ {seed.topic.title()}\n\n" if seed.topic else "✨\n\n"
        return title + '\n\n'.join(stanzas)

    def _create_rap(self, seed: Seed, beats: List[Beat]) -> str:
        """Generate rap lyrics with heavy rhyme and rhythm."""
        sections = []

        for i, beat in enumerate(beats):
            lines = []
            prev_end_word = ""

            for j in range(4):
                subjects = ['I', seed.topic, 'the game', 'my mind', 'the streets', 'life']
                subj = subjects[(i * 4 + j) % len(subjects)]

                line = self.sentence.construct(
                    min(1.0, beat.target_energy + 0.2),  # Rap = always energetic
                    0.8,  # Fast
                    beat.target_weight,
                    beat.target_color,
                    subj, beat.image_transform
                )
                # Short punchy lines for rap
                words = line.split()
                if len(words) > 8:
                    line = ' '.join(words[:8])

                # Heavy rhyme: every line end rhymes with previous
                if prev_end_word:
                    rhyme_word = self.rhyme.find_rhyme(prev_end_word)
                    if rhyme_word:
                        words = line.split()
                        if words:
                            words[-1] = rhyme_word
                            line = ' '.join(words)

                prev_end_word = line.rstrip('.!?,').split()[-1] if line.split() else ""
                lines.append(line)

            label = beat.arc_position.replace('_', ' ').title()
            section = f"[{label}]\n" + '\n'.join(lines)
            sections.append(section)

        title = f"🎤 {seed.topic.title()}\n\n" if seed.topic else "🎤\n\n"
        return title + '\n\n'.join(sections)

    def _create_essay(self, seed: Seed, beats: List[Beat]) -> str:
        """Generate an essay with argument structure."""
        paragraphs = []

        for i, beat in enumerate(beats):
            sentences = []
            # Essay = longer sentences, formal
            for j in range(4):
                subjects = [seed.topic, 'this concept', 'the evidence', 'we', 'it', 'the truth']
                subj = subjects[(i * 4 + j) % len(subjects)]

                sent = self.sentence.construct(
                    max(0.3, beat.target_energy - 0.1),  # Essays = calmer
                    0.4,  # Medium speed
                    beat.target_weight,
                    0.5,  # Neutral color
                    subj, beat.image_transform
                )
                sentences.append(sent)

            paragraphs.append(' '.join(sentences))

        title = f"📝 {seed.topic.title()}\n\n" if seed.topic else ""
        return title + '\n\n'.join(paragraphs)


def get_creator() -> Creator:
    """Get creator instance."""
    return Creator()
