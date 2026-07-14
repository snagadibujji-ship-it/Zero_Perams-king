"""
AXIMA VOICE — Module 7: Voice DNA Profiler
Built by: Ghias + Kiro | 2026

A voice is defined by 72 Vocal Genes. That's 288 bytes.
Any voice in the world can be represented this way.
Clone a voice from 5 seconds of audio. Create infinite new voices.

No neural network. Pure DSP analysis.
"""

import math
from typing import Dict, List, Optional


class VoiceDNA:
    """A complete voice identity encoded as 72 Vocal Genes."""

    def __init__(self, name: str = "Default"):
        self.name = name

        # ═══ PITCH GENES (8) ═══
        self.base_f0 = 130.0          # Base pitch (Hz)
        self.f0_range = 0.5           # Range in octaves
        self.f0_variability = 0.10    # How much F0 varies (0-0.3)
        self.vibrato_rate = 5.0       # Hz (0 = no vibrato)
        self.vibrato_depth = 0.005    # Fraction of F0
        self.declination_rate = 1.5   # Hz per syllable drop
        self.question_rise = 0.5      # Fraction rise on questions
        self.creak_threshold = 80.0   # F0 below this → vocal fry

        # ═══ TRACT GENES (20) ═══
        self.vocal_tract_length = 17.0  # cm (shifts all formants)
        self.lpc_bias = [0.0] * 16      # Personal formant deviation
        self.jaw_openness = 0.5         # 0=closed, 1=wide
        self.lip_rounding = 0.3         # 0=spread, 1=rounded
        self.tongue_advance = 0.5       # 0=back, 1=front

        # ═══ SOURCE GENES (16) ═══
        self.rd_mean = 1.0            # Voice quality (0.3=tense, 2.7=breathy)
        self.rd_range = 0.3           # How much Rd varies
        self.hnr = 25.0               # Harmonic-to-noise ratio (dB)
        self.jitter = 0.004           # F0 perturbation (fraction)
        self.shimmer = 0.003          # Amplitude perturbation (fraction)
        self.spectral_tilt = -12.0    # dB/octave (energy rolloff)
        self.open_quotient = 0.5      # Fraction of cycle glottis is open
        self.subglottal_coupling = 0.05
        self.diplophonia = 0.0        # Alternating cycle (0=none, 1=max)
        self.aspiration_level = 0.02  # Breathiness noise
        self.creakiness = 0.0         # Vocal fry tendency
        self.pulse_asymmetry = 0.6    # Opening vs closing phase ratio
        self.harmonic_richness = 0.8  # How many overtones
        self.perturbation_corr = 0.3  # Jitter correlation between cycles
        self.amplitude_mod = 0.01     # Slow amplitude variation
        self.noise_color = -3.0       # Noise spectral tilt

        # ═══ TIMING GENES (12) ═══
        self.speaking_rate = 4.5      # Syllables per second
        self.pause_tendency = 0.5     # Likelihood of inserting pauses
        self.vowel_reduction = 0.5    # How much unstressed vowels reduce
        self.consonant_precision = 0.8  # Clarity of consonants
        self.coarticulation_degree = 0.6  # How much phonemes blend
        self.preboundary_lengthening = 1.3  # Factor at phrase ends
        self.rhythm_regularity = 0.5  # 0=irregular, 1=metronomic
        self.emphasis_strength = 1.0  # Pitch accent magnitude
        self.intensity_range = 12.0   # dB range of loudness
        self.tempo_variation = 0.08   # ±% rate variation
        self.articulation_rate = 5.5  # Syllables/sec excluding pauses
        self.pause_duration = 0.25    # Seconds (typical pause)

        # ═══ QUALITY GENES (16) ═══
        self.nasality = 0.1           # Nasal resonance amount
        self.brightness = 0.5         # High-frequency presence
        self.warmth = 0.5             # Low-mid frequency body
        self.roughness = 0.0          # Irregular voicing
        self.strain = 0.0             # Effortful sound
        self.vocal_fry_rate = 0.0     # How often fry occurs
        self.head_voice_mix = 0.2     # Head vs chest register
        self.chest_resonance = 0.5    # Sub-glottal body
        self.formant_precision = 0.9  # How close to target formants
        self.transition_speed = 0.7   # Fast/slow transitions
        self.breathiness_onset = 0.1  # Breathiness at phrase start
        self.pressed_phonation = 0.0  # Pressed/tense voice
        self.age_factor = 0.3         # 0=child, 0.3=young, 0.7=middle, 1=old
        self.gender_continuum = 0.7   # 0=feminine, 1=masculine
        self.size_factor = 0.5        # Body size (affects tract length)
        self.effort_level = 0.5       # Overall vocal effort

    def apply_to_engine(self, engine):
        """Apply this Voice DNA to an AximaVoice engine instance."""
        engine.f0 = self.base_f0
        engine.rd = self.rd_mean
        engine.rate = self.speaking_rate / 4.5  # Normalize to default rate

        # Update source parameters
        engine.source_jitter = self.jitter
        engine.source_shimmer = self.shimmer

        # Update humanizer
        engine.humanizer_aspiration = self.aspiration_level

    def to_dict(self) -> Dict:
        """Export Voice DNA as dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    @classmethod
    def from_dict(cls, data: Dict) -> 'VoiceDNA':
        """Create Voice DNA from dictionary."""
        dna = cls(data.get('name', 'Custom'))
        for k, v in data.items():
            if hasattr(dna, k):
                setattr(dna, k, v)
        return dna

    @classmethod
    def mix(cls, dna1: 'VoiceDNA', dna2: 'VoiceDNA', weight: float = 0.5) -> 'VoiceDNA':
        """Mix two voices together. weight=0 is all dna1, weight=1 is all dna2."""
        result = cls(f"{dna1.name}+{dna2.name}")
        w1, w2 = 1.0 - weight, weight

        for attr in vars(dna1):
            if attr.startswith('_') or attr == 'name':
                continue
            v1 = getattr(dna1, attr)
            v2 = getattr(dna2, attr)
            if isinstance(v1, (int, float)):
                setattr(result, attr, v1 * w1 + v2 * w2)
            elif isinstance(v1, list):
                setattr(result, attr, [a * w1 + b * w2 for a, b in zip(v1, v2)])

        return result


# ═══════════════════════════════════════════════════════════════
# PRE-BUILT VOICES — 8 distinct identities, 288 bytes each
# ═══════════════════════════════════════════════════════════════

def voice_atlas() -> VoiceDNA:
    """Atlas — Deep warm male narrator (Morgan Freeman zone)."""
    v = VoiceDNA("Atlas")
    v.base_f0 = 95.0
    v.f0_range = 0.4
    v.rd_mean = 1.1
    v.speaking_rate = 3.8
    v.warmth = 0.8
    v.brightness = 0.4
    v.chest_resonance = 0.9
    v.vocal_tract_length = 18.5
    v.gender_continuum = 0.9
    v.age_factor = 0.6
    v.emphasis_strength = 0.8
    v.pause_tendency = 0.7
    v.spectral_tilt = -10.0
    return v

def voice_nova() -> VoiceDNA:
    """Nova — Clear professional female, neutral accent."""
    v = VoiceDNA("Nova")
    v.base_f0 = 210.0
    v.f0_range = 0.5
    v.rd_mean = 0.9
    v.speaking_rate = 4.5
    v.warmth = 0.5
    v.brightness = 0.7
    v.vocal_tract_length = 15.0
    v.gender_continuum = 0.2
    v.age_factor = 0.3
    v.formant_precision = 0.95
    v.consonant_precision = 0.9
    return v

def voice_spark() -> VoiceDNA:
    """Spark — Young energetic podcast host."""
    v = VoiceDNA("Spark")
    v.base_f0 = 145.0
    v.f0_range = 0.7
    v.f0_variability = 0.15
    v.rd_mean = 0.8
    v.speaking_rate = 5.2
    v.warmth = 0.4
    v.brightness = 0.8
    v.emphasis_strength = 1.4
    v.gender_continuum = 0.5
    v.age_factor = 0.2
    v.tempo_variation = 0.12
    return v

def voice_sage() -> VoiceDNA:
    """Sage — Elder wisdom, measured pace (Attenborough zone)."""
    v = VoiceDNA("Sage")
    v.base_f0 = 105.0
    v.f0_range = 0.35
    v.rd_mean = 1.3
    v.speaking_rate = 3.5
    v.warmth = 0.7
    v.brightness = 0.3
    v.jitter = 0.008
    v.shimmer = 0.006
    v.age_factor = 0.8
    v.gender_continuum = 0.8
    v.pause_tendency = 0.8
    v.pause_duration = 0.35
    v.aspiration_level = 0.03
    return v

def voice_aria() -> VoiceDNA:
    """Aria — Warm female storyteller, audiobook quality."""
    v = VoiceDNA("Aria")
    v.base_f0 = 190.0
    v.f0_range = 0.6
    v.rd_mean = 1.0
    v.speaking_rate = 4.0
    v.warmth = 0.7
    v.brightness = 0.5
    v.vocal_tract_length = 15.5
    v.gender_continuum = 0.15
    v.age_factor = 0.35
    v.emphasis_strength = 1.1
    v.coarticulation_degree = 0.7
    return v

def voice_echo() -> VoiceDNA:
    """Echo — Gender-neutral, modern tech assistant."""
    v = VoiceDNA("Echo")
    v.base_f0 = 165.0
    v.f0_range = 0.4
    v.rd_mean = 0.9
    v.speaking_rate = 4.8
    v.warmth = 0.4
    v.brightness = 0.6
    v.gender_continuum = 0.45
    v.age_factor = 0.25
    v.consonant_precision = 0.95
    v.formant_precision = 0.95
    v.rhythm_regularity = 0.6
    return v

def voice_storm() -> VoiceDNA:
    """Storm — Powerful commanding announcer/trailer voice."""
    v = VoiceDNA("Storm")
    v.base_f0 = 88.0
    v.f0_range = 0.6
    v.rd_mean = 0.6  # Tense, powerful
    v.speaking_rate = 3.2
    v.warmth = 0.6
    v.brightness = 0.7
    v.chest_resonance = 1.0
    v.vocal_tract_length = 19.0
    v.gender_continuum = 1.0
    v.emphasis_strength = 1.8
    v.intensity_range = 18.0
    v.effort_level = 0.8
    return v

def voice_whisper() -> VoiceDNA:
    """Whisper — ASMR intimate voice."""
    v = VoiceDNA("Whisper")
    v.base_f0 = 180.0
    v.f0_range = 0.2
    v.rd_mean = 2.2  # Very breathy
    v.speaking_rate = 3.5
    v.warmth = 0.8
    v.brightness = 0.3
    v.aspiration_level = 0.08
    v.hnr = 12.0  # Low HNR = lots of noise
    v.intensity_range = 4.0  # Very quiet, even
    v.gender_continuum = 0.3
    v.effort_level = 0.2
    v.pause_tendency = 0.9
    return v


# Voice registry
VOICES: Dict[str, VoiceDNA] = {}

def get_voice(name: str) -> Optional[VoiceDNA]:
    """Get a pre-built voice by name."""
    if not VOICES:
        # Initialize on first access
        VOICES['atlas'] = voice_atlas()
        VOICES['nova'] = voice_nova()
        VOICES['spark'] = voice_spark()
        VOICES['sage'] = voice_sage()
        VOICES['aria'] = voice_aria()
        VOICES['echo'] = voice_echo()
        VOICES['storm'] = voice_storm()
        VOICES['whisper'] = voice_whisper()

    return VOICES.get(name.lower())

def list_voices() -> List[str]:
    """List all available voice names."""
    if not VOICES:
        get_voice('atlas')  # Trigger initialization
    return list(VOICES.keys())
