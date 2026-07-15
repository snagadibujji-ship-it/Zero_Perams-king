"""
AXIMA VOICE — Module 2: The Prosodist (COSMIC LEVEL)
Built by: Ghias + Kiro | 2026

Advanced prosody model that makes speech sound ALIVE.
Multiple layers of pitch, timing, and intensity control.

This is what separates a robotic TTS from a human narrator.
ElevenLabs learns this from data. We COMPUTE it from linguistics.

Layers:
  L1: Base F0 from Voice DNA
  L2: Declination (-1.5Hz per syllable within phrase)
  L3: Pitch accents (H*, L+H*, H+L*, etc. — ToBI-inspired)
  L4: Question intonation (terminal rise)
  L5: Micro-prosody (consonant perturbation of F0)
  L6: Perlin drift (never-repeating natural variation)
  L7: Vibrato (optional, for singing/expressive)
  L8: Emotion overlay (from EmotionEngine)
"""

import math
from typing import List, Dict, Tuple


class ProsodyEngine:
    """Advanced prosody model — 8-layer F0 + timing + intensity."""

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.frame_ms = 5.0  # 5ms frames for prosody
        self._perlin_state = 0.0
        self._perm = self._build_perm()

    def generate_f0_contour(self, sequence: List[Dict], 
                            base_f0: float = 130.0,
                            emotion_mult: float = 1.0,
                            f0_range: float = 0.5) -> List[float]:
        """Generate frame-by-frame F0 contour for entire utterance.
        
        Returns F0 value per synthesis frame (5ms resolution).
        This is the MELODY of speech — the most important quality signal.
        """
        contour = []
        syllable_idx = 0
        total_syllables = sum(1 for s in sequence if s.get('stress', 0) > 0)
        phrase_position = 0.0  # 0=start, 1=end of phrase

        for i, seg in enumerate(sequence):
            dur_ms = seg.get('duration_ms', 70)
            num_frames = max(1, int(dur_ms / self.frame_ms))
            stress = seg.get('stress', 0)
            phone = seg.get('phone', 'SIL')
            is_voiced = seg.get('voiced', False)

            if phone == 'SIL' and dur_ms > 100:
                # Phrase break — reset
                syllable_idx = 0
                phrase_position = 0.0

            for frame in range(num_frames):
                if not is_voiced or phone == 'SIL':
                    contour.append(0.0)  # Unvoiced = no F0
                    continue

                # L1: Base pitch
                f0 = base_f0 * emotion_mult

                # L2: Declination (-1.5Hz per syllable)
                f0 -= syllable_idx * 1.5
                f0 = max(f0, base_f0 * 0.65)

                # L3: Pitch accent
                if stress == 1:
                    # Primary stress: H* accent (rise then fall)
                    accent_phase = frame / max(num_frames - 1, 1)
                    # Bell-shaped accent curve
                    accent = math.exp(-(accent_phase - 0.3)**2 / 0.1)
                    f0 *= (1.0 + 0.25 * accent * f0_range)
                elif stress == 2:
                    # Secondary stress: smaller accent
                    accent_phase = frame / max(num_frames - 1, 1)
                    accent = math.exp(-(accent_phase - 0.4)**2 / 0.15)
                    f0 *= (1.0 + 0.12 * accent * f0_range)

                # L4: Phrase position effect
                # Slight rise at start, fall toward end
                if total_syllables > 0:
                    pos = syllable_idx / max(total_syllables, 1)
                    phrase_curve = 1.0 + 0.05 * math.sin(pos * math.pi)
                    f0 *= phrase_curve

                # L5: Micro-prosody (consonant → vowel perturbation)
                if phone in ('P','T','K','S','F','TH','SH','CH'):
                    f0 *= 1.02  # Voiceless consonants raise F0 slightly
                elif phone in ('B','D','G','V','Z','DH','ZH','JH'):
                    f0 *= 0.98  # Voiced consonants lower F0 slightly

                # L6: Perlin drift (smooth natural variation ±2%)
                t = len(contour) * self.frame_ms / 1000.0
                drift = self._perlin_1d(t * 3.5 + 13.7)
                f0 *= (1.0 + drift * 0.025)

                # L7: Vibrato (subtle, like real speaker)
                vibrato = math.sin(2 * math.pi * 5.0 * t) * 0.005 * f0
                f0 += vibrato

                # Clamp
                f0 = max(50.0, min(500.0, f0))
                contour.append(f0)

            if stress > 0:
                syllable_idx += 1

        return contour

    def apply_question_intonation(self, contour: List[float], 
                                   rise_amount: float = 0.5) -> List[float]:
        """Apply terminal rise for yes/no questions."""
        if not contour:
            return contour
        
        result = list(contour)
        # Find last voiced segment
        last_voiced = len(result) - 1
        while last_voiced > 0 and result[last_voiced] == 0:
            last_voiced -= 1

        # Rise over last 20% of voiced frames
        rise_start = int(last_voiced * 0.8)
        for i in range(rise_start, last_voiced + 1):
            progress = (i - rise_start) / max(last_voiced - rise_start, 1)
            # Exponential rise
            rise = 1.0 + rise_amount * (progress ** 2)
            if result[i] > 0:
                result[i] *= rise

        return result

    def generate_duration_pattern(self, sequence: List[Dict],
                                   rate: float = 1.0) -> List[float]:
        """Generate natural duration pattern with variation.
        
        Returns modified duration_ms for each segment.
        Applies: pre-boundary lengthening, stress effects, phrase-final decel.
        """
        durations = []
        n = len(sequence)

        for i, seg in enumerate(sequence):
            dur = seg.get('duration_ms', 70)

            # Stress effect
            stress = seg.get('stress', 0)
            if stress == 1:
                dur *= 1.3
            elif stress == 2:
                dur *= 1.1
            elif stress == 0:
                dur *= 0.85

            # Pre-boundary lengthening
            if i + 1 < n and sequence[i+1].get('phone') == 'SIL':
                next_dur = sequence[i+1].get('duration_ms', 0)
                if next_dur > 100:  # Major boundary
                    dur *= 1.4
                elif next_dur > 30:  # Minor boundary
                    dur *= 1.15

            # Phrase-final deceleration (last 3 segments before pause)
            if i + 2 < n and sequence[i+2].get('phone') == 'SIL':
                dur *= 1.1
            if i + 3 < n and sequence[i+3].get('phone') == 'SIL':
                dur *= 1.05

            # Natural variation (±8%)
            t = i * 0.618
            variation = self._perlin_1d(t + 42.0) * 0.08
            dur *= (1.0 + variation)

            # Rate
            dur /= rate

            durations.append(max(20, dur))

        return durations

    def generate_intensity_contour(self, sequence: List[Dict],
                                    base_intensity: float = 0.8) -> List[float]:
        """Generate per-segment intensity targets.
        
        Stressed syllables louder, unstressed quieter, phrase-final reduction.
        """
        intensities = []
        n = len(sequence)

        for i, seg in enumerate(sequence):
            intensity = base_intensity
            stress = seg.get('stress', 0)

            if stress == 1:
                intensity *= 1.15
            elif stress == 0:
                intensity *= 0.85

            # Phrase-final reduction
            if i + 1 < n and sequence[i+1].get('phone') == 'SIL':
                intensity *= 0.9

            # Natural variation
            t = i * 1.23
            drift = self._perlin_1d(t + 77.0) * 0.05
            intensity *= (1.0 + drift)

            intensities.append(max(0.2, min(1.0, intensity)))

        return intensities

    def _perlin_1d(self, x: float) -> float:
        """1D Perlin noise in [-1, 1]."""
        xi = int(math.floor(x)) & 255
        xf = x - math.floor(x)
        u = xf * xf * xf * (xf * (xf * 6.0 - 15.0) + 10.0)
        g0 = xf if (self._perm[xi] & 1) == 0 else -xf
        g1 = (xf - 1.0) if (self._perm[(xi+1)&255] & 1) == 0 else -(xf - 1.0)
        return g0 + u * (g1 - g0)

    def _build_perm(self) -> List[int]:
        p = list(range(256))
        for i in range(255, 0, -1):
            j = (i * 7919 + 104729) % (i + 1)
            p[i], p[j] = p[j], p[i]
        return p + p
