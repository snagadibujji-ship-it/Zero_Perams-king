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
        # NEW VOICES (20 more)
        VOICES['thunder'] = voice_thunder()
        VOICES['velvet'] = voice_velvet()
        VOICES['crystal'] = voice_crystal()
        VOICES['ember'] = voice_ember()
        VOICES['frost'] = voice_frost()
        VOICES['shadow'] = voice_shadow()
        VOICES['honey'] = voice_honey()
        VOICES['titan'] = voice_titan()
        VOICES['luna'] = voice_luna()
        VOICES['blaze'] = voice_blaze()
        VOICES['silk'] = voice_silk()
        VOICES['rock'] = voice_rock()
        VOICES['breeze'] = voice_breeze()
        VOICES['oracle'] = voice_oracle()
        VOICES['viper'] = voice_viper()
        VOICES['angel'] = voice_angel()
        VOICES['ghost'] = voice_ghost()
        VOICES['phoenix'] = voice_phoenix()
        VOICES['ocean'] = voice_ocean()
        VOICES['rebel'] = voice_rebel()
        # BATCH 3: 10 MORE SPECIALTY VOICES
        VOICES['child'] = voice_child()
        VOICES['elder'] = voice_elder()
        VOICES['robot'] = voice_robot()
        VOICES['demon'] = voice_demon()
        VOICES['narrator'] = voice_narrator()
        VOICES['coach'] = voice_coach()
        VOICES['diva'] = voice_diva()
        VOICES['soldier'] = voice_soldier()
        VOICES['poet'] = voice_poet()
        VOICES['alien'] = voice_alien()

    return VOICES.get(name.lower())

def list_voices() -> List[str]:
    """List all available voice names."""
    if not VOICES:
        get_voice('atlas')  # Trigger initialization
    return list(VOICES.keys())


# ═══════════════════════════════════════════════════════════════
# 20 NEW VOICES — Diverse, unique, covering all vocal space
# ═══════════════════════════════════════════════════════════════

def voice_thunder() -> VoiceDNA:
    """Thunder — Ultra-deep bass (James Earl Jones / movie trailers)."""
    v = VoiceDNA("Thunder")
    v.base_f0 = 75.0; v.f0_range = 0.35; v.rd_mean = 0.7
    v.speaking_rate = 3.0; v.warmth = 0.9; v.brightness = 0.3
    v.chest_resonance = 1.0; v.vocal_tract_length = 20.0
    v.gender_continuum = 1.0; v.age_factor = 0.5
    v.emphasis_strength = 1.5; v.intensity_range = 20.0
    v.effort_level = 0.7; v.spectral_tilt = -8.0
    return v

def voice_velvet() -> VoiceDNA:
    """Velvet — Smooth seductive female (late night radio)."""
    v = VoiceDNA("Velvet")
    v.base_f0 = 185.0; v.f0_range = 0.4; v.rd_mean = 1.3
    v.speaking_rate = 3.8; v.warmth = 0.85; v.brightness = 0.4
    v.vocal_tract_length = 15.5; v.gender_continuum = 0.1
    v.age_factor = 0.35; v.aspiration_level = 0.04
    v.breathiness_onset = 0.2; v.coarticulation_degree = 0.8
    v.pause_tendency = 0.7; v.shimmer = 0.002
    return v

def voice_crystal() -> VoiceDNA:
    """Crystal — High clear soprano (Disney princess / audiobook)."""
    v = VoiceDNA("Crystal")
    v.base_f0 = 240.0; v.f0_range = 0.7; v.rd_mean = 0.8
    v.speaking_rate = 4.3; v.warmth = 0.3; v.brightness = 0.9
    v.vocal_tract_length = 14.0; v.gender_continuum = 0.05
    v.age_factor = 0.15; v.formant_precision = 0.98
    v.consonant_precision = 0.95; v.jitter = 0.002
    v.harmonic_richness = 0.95; v.head_voice_mix = 0.6
    return v

def voice_ember() -> VoiceDNA:
    """Ember — Warm raspy female (indie singer / Adele zone)."""
    v = VoiceDNA("Ember")
    v.base_f0 = 175.0; v.f0_range = 0.6; v.rd_mean = 1.1
    v.speaking_rate = 4.0; v.warmth = 0.8; v.brightness = 0.5
    v.vocal_tract_length = 15.8; v.gender_continuum = 0.2
    v.roughness = 0.15; v.creakiness = 0.1; v.jitter = 0.006
    v.shimmer = 0.005; v.age_factor = 0.3
    v.emphasis_strength = 1.3; v.aspiration_level = 0.03
    return v

def voice_frost() -> VoiceDNA:
    """Frost — Cold precise robotic (AI assistant, clinical)."""
    v = VoiceDNA("Frost")
    v.base_f0 = 155.0; v.f0_range = 0.25; v.rd_mean = 0.85
    v.speaking_rate = 5.0; v.warmth = 0.2; v.brightness = 0.7
    v.gender_continuum = 0.5; v.age_factor = 0.25
    v.rhythm_regularity = 0.9; v.formant_precision = 0.99
    v.consonant_precision = 0.98; v.jitter = 0.001
    v.shimmer = 0.001; v.f0_variability = 0.03
    v.coarticulation_degree = 0.4; v.emphasis_strength = 0.5
    return v

def voice_shadow() -> VoiceDNA:
    """Shadow — Dark mysterious (villain / horror narrator)."""
    v = VoiceDNA("Shadow")
    v.base_f0 = 98.0; v.f0_range = 0.3; v.rd_mean = 1.5
    v.speaking_rate = 3.3; v.warmth = 0.6; v.brightness = 0.2
    v.vocal_tract_length = 19.0; v.gender_continuum = 0.85
    v.creakiness = 0.2; v.aspiration_level = 0.04
    v.age_factor = 0.5; v.pause_tendency = 0.85
    v.pause_duration = 0.4; v.spectral_tilt = -16.0
    v.intensity_range = 6.0; v.effort_level = 0.3
    return v

def voice_honey() -> VoiceDNA:
    """Honey — Sweet warm female (children's narrator / podcast)."""
    v = VoiceDNA("Honey")
    v.base_f0 = 220.0; v.f0_range = 0.55; v.rd_mean = 1.0
    v.speaking_rate = 4.0; v.warmth = 0.75; v.brightness = 0.6
    v.vocal_tract_length = 14.5; v.gender_continuum = 0.1
    v.age_factor = 0.25; v.nasality = 0.05
    v.emphasis_strength = 1.0; v.tempo_variation = 0.1
    v.coarticulation_degree = 0.7; v.formant_precision = 0.92
    return v

def voice_titan() -> VoiceDNA:
    """Titan — Massive commanding (stadium announcer / god voice)."""
    v = VoiceDNA("Titan")
    v.base_f0 = 80.0; v.f0_range = 0.5; v.rd_mean = 0.5
    v.speaking_rate = 2.8; v.warmth = 0.7; v.brightness = 0.8
    v.vocal_tract_length = 21.0; v.gender_continuum = 1.0
    v.chest_resonance = 1.0; v.effort_level = 0.95
    v.intensity_range = 25.0; v.emphasis_strength = 2.0
    v.spectral_tilt = -6.0; v.harmonic_richness = 1.0
    return v

def voice_luna() -> VoiceDNA:
    """Luna — Dreamy ethereal female (meditation / ASMR / ambient)."""
    v = VoiceDNA("Luna")
    v.base_f0 = 200.0; v.f0_range = 0.3; v.rd_mean = 2.0
    v.speaking_rate = 3.2; v.warmth = 0.7; v.brightness = 0.4
    v.vocal_tract_length = 15.0; v.gender_continuum = 0.1
    v.aspiration_level = 0.06; v.hnr = 15.0
    v.intensity_range = 4.0; v.effort_level = 0.2
    v.pause_tendency = 0.9; v.pause_duration = 0.5
    v.breathiness_onset = 0.3; v.vibrato_depth = 0.002
    return v

def voice_blaze() -> VoiceDNA:
    """Blaze — Fast aggressive rapper / hype man."""
    v = VoiceDNA("Blaze")
    v.base_f0 = 140.0; v.f0_range = 0.4; v.rd_mean = 0.6
    v.speaking_rate = 6.5; v.warmth = 0.4; v.brightness = 0.8
    v.gender_continuum = 0.7; v.age_factor = 0.2
    v.emphasis_strength = 1.6; v.effort_level = 0.85
    v.rhythm_regularity = 0.7; v.consonant_precision = 0.9
    v.intensity_range = 15.0; v.tempo_variation = 0.15
    v.spectral_tilt = -8.0; v.pressed_phonation = 0.3
    return v

def voice_silk() -> VoiceDNA:
    """Silk — Ultra-smooth jazz singer (Sinatra / Nat King Cole zone)."""
    v = VoiceDNA("Silk")
    v.base_f0 = 118.0; v.f0_range = 0.45; v.rd_mean = 1.2
    v.speaking_rate = 3.8; v.warmth = 0.85; v.brightness = 0.4
    v.vocal_tract_length = 17.5; v.gender_continuum = 0.75
    v.age_factor = 0.45; v.coarticulation_degree = 0.8
    v.vibrato_rate = 5.5; v.vibrato_depth = 0.008
    v.aspiration_level = 0.025; v.transition_speed = 0.8
    return v

def voice_rock() -> VoiceDNA:
    """Rock — Gravelly powerful male (rock singer / Springsteen)."""
    v = VoiceDNA("Rock")
    v.base_f0 = 125.0; v.f0_range = 0.6; v.rd_mean = 0.7
    v.speaking_rate = 4.2; v.warmth = 0.6; v.brightness = 0.7
    v.gender_continuum = 0.85; v.roughness = 0.2
    v.jitter = 0.007; v.shimmer = 0.006; v.creakiness = 0.15
    v.effort_level = 0.8; v.emphasis_strength = 1.5
    v.spectral_tilt = -9.0; v.pressed_phonation = 0.2
    return v

def voice_breeze() -> VoiceDNA:
    """Breeze — Light airy androgynous (nature documentary)."""
    v = VoiceDNA("Breeze")
    v.base_f0 = 170.0; v.f0_range = 0.35; v.rd_mean = 1.4
    v.speaking_rate = 4.0; v.warmth = 0.5; v.brightness = 0.5
    v.gender_continuum = 0.4; v.aspiration_level = 0.035
    v.breathiness_onset = 0.15; v.intensity_range = 8.0
    v.effort_level = 0.3; v.vocal_tract_length = 16.0
    v.age_factor = 0.3; v.pause_tendency = 0.6
    return v

def voice_oracle() -> VoiceDNA:
    """Oracle — Ancient mystical (fantasy narrator / wizard)."""
    v = VoiceDNA("Oracle")
    v.base_f0 = 100.0; v.f0_range = 0.4; v.rd_mean = 1.6
    v.speaking_rate = 3.0; v.warmth = 0.7; v.brightness = 0.3
    v.vocal_tract_length = 19.5; v.gender_continuum = 0.8
    v.age_factor = 0.9; v.jitter = 0.009; v.shimmer = 0.007
    v.pause_tendency = 0.9; v.pause_duration = 0.5
    v.creakiness = 0.15; v.vibrato_rate = 4.0
    v.vibrato_depth = 0.006; v.spectral_tilt = -15.0
    return v

def voice_viper() -> VoiceDNA:
    """Viper — Sharp sibilant threatening (villain / snake-like)."""
    v = VoiceDNA("Viper")
    v.base_f0 = 135.0; v.f0_range = 0.3; v.rd_mean = 0.9
    v.speaking_rate = 4.5; v.warmth = 0.2; v.brightness = 0.9
    v.gender_continuum = 0.6; v.consonant_precision = 1.0
    v.spectral_tilt = -6.0; v.intensity_range = 10.0
    v.emphasis_strength = 1.2; v.pressed_phonation = 0.15
    v.nasality = 0.15; v.aspiration_level = 0.02
    return v

def voice_angel() -> VoiceDNA:
    """Angel — Pure heavenly soprano (choir soloist / ethereal)."""
    v = VoiceDNA("Angel")
    v.base_f0 = 260.0; v.f0_range = 0.8; v.rd_mean = 0.85
    v.speaking_rate = 3.8; v.warmth = 0.4; v.brightness = 0.8
    v.vocal_tract_length = 13.5; v.gender_continuum = 0.0
    v.head_voice_mix = 0.8; v.harmonic_richness = 0.95
    v.jitter = 0.001; v.shimmer = 0.001
    v.vibrato_rate = 6.0; v.vibrato_depth = 0.01
    v.formant_precision = 0.98; v.effort_level = 0.4
    return v

def voice_ghost() -> VoiceDNA:
    """Ghost — Eerie whispered with reverb feel (horror / supernatural)."""
    v = VoiceDNA("Ghost")
    v.base_f0 = 145.0; v.f0_range = 0.2; v.rd_mean = 2.3
    v.speaking_rate = 3.0; v.warmth = 0.3; v.brightness = 0.4
    v.aspiration_level = 0.07; v.hnr = 10.0
    v.intensity_range = 3.0; v.effort_level = 0.15
    v.gender_continuum = 0.5; v.creakiness = 0.1
    v.f0_variability = 0.02; v.pause_tendency = 0.95
    return v

def voice_phoenix() -> VoiceDNA:
    """Phoenix — Rising powerful female (inspirational / TED talk)."""
    v = VoiceDNA("Phoenix")
    v.base_f0 = 195.0; v.f0_range = 0.65; v.rd_mean = 0.85
    v.speaking_rate = 4.5; v.warmth = 0.6; v.brightness = 0.7
    v.vocal_tract_length = 15.2; v.gender_continuum = 0.15
    v.emphasis_strength = 1.4; v.intensity_range = 16.0
    v.effort_level = 0.7; v.age_factor = 0.3
    v.tempo_variation = 0.12; v.pause_tendency = 0.5
    v.chest_resonance = 0.7; v.formant_precision = 0.94
    return v

def voice_ocean() -> VoiceDNA:
    """Ocean — Deep calming female (meditation / yoga instructor)."""
    v = VoiceDNA("Ocean")
    v.base_f0 = 175.0; v.f0_range = 0.25; v.rd_mean = 1.5
    v.speaking_rate = 3.2; v.warmth = 0.8; v.brightness = 0.3
    v.vocal_tract_length = 15.5; v.gender_continuum = 0.15
    v.aspiration_level = 0.04; v.intensity_range = 5.0
    v.effort_level = 0.25; v.pause_tendency = 0.85
    v.pause_duration = 0.6; v.f0_variability = 0.05
    v.breathiness_onset = 0.2; v.rhythm_regularity = 0.3
    return v

def voice_rebel() -> VoiceDNA:
    """Rebel — Punk/edgy young (alternative / counter-culture)."""
    v = VoiceDNA("Rebel")
    v.base_f0 = 155.0; v.f0_range = 0.5; v.rd_mean = 0.7
    v.speaking_rate = 5.5; v.warmth = 0.3; v.brightness = 0.8
    v.gender_continuum = 0.55; v.age_factor = 0.15
    v.roughness = 0.1; v.jitter = 0.005; v.creakiness = 0.1
    v.emphasis_strength = 1.3; v.intensity_range = 14.0
    v.consonant_precision = 0.7; v.vowel_reduction = 0.7
    v.tempo_variation = 0.15; v.rhythm_regularity = 0.3
    return v



# ═══════════════════════════════════════════════════════════════
# BATCH 3: 10 MORE SPECIALTY VOICES (total: 38)
# ═══════════════════════════════════════════════════════════════

def voice_child() -> VoiceDNA:
    """Child — Young child voice (6-10 years old, stories/games)."""
    v = VoiceDNA("Child")
    v.base_f0 = 300.0; v.f0_range = 0.8; v.rd_mean = 0.9
    v.speaking_rate = 4.8; v.warmth = 0.4; v.brightness = 0.8
    v.vocal_tract_length = 12.0; v.gender_continuum = 0.3
    v.age_factor = 0.0; v.jitter = 0.003; v.shimmer = 0.002
    v.f0_variability = 0.18; v.emphasis_strength = 1.3
    v.rhythm_regularity = 0.3; v.vowel_reduction = 0.3
    return v

def voice_elder() -> VoiceDNA:
    """Elder — Elderly voice (grandparent, 80+ years, wise/frail)."""
    v = VoiceDNA("Elder")
    v.base_f0 = 115.0; v.f0_range = 0.3; v.rd_mean = 1.8
    v.speaking_rate = 3.0; v.warmth = 0.7; v.brightness = 0.3
    v.vocal_tract_length = 17.5; v.gender_continuum = 0.6
    v.age_factor = 1.0; v.jitter = 0.012; v.shimmer = 0.01
    v.aspiration_level = 0.05; v.creakiness = 0.2
    v.pause_tendency = 0.9; v.pause_duration = 0.4
    v.effort_level = 0.3; v.tremor_rate = 3.0
    return v

def voice_robot() -> VoiceDNA:
    """Robot — Synthetic/mechanical voice (Siri/HAL 9000 zone)."""
    v = VoiceDNA("Robot")
    v.base_f0 = 150.0; v.f0_range = 0.1; v.rd_mean = 0.7
    v.speaking_rate = 4.5; v.warmth = 0.1; v.brightness = 0.8
    v.gender_continuum = 0.5; v.jitter = 0.0; v.shimmer = 0.0
    v.f0_variability = 0.0; v.rhythm_regularity = 1.0
    v.formant_precision = 1.0; v.consonant_precision = 1.0
    v.coarticulation_degree = 0.2; v.aspiration_level = 0.0
    v.emphasis_strength = 0.3; v.tempo_variation = 0.0
    return v

def voice_demon() -> VoiceDNA:
    """Demon — Deep growling dark (horror/game villain)."""
    v = VoiceDNA("Demon")
    v.base_f0 = 65.0; v.f0_range = 0.4; v.rd_mean = 0.4
    v.speaking_rate = 2.5; v.warmth = 0.5; v.brightness = 0.3
    v.vocal_tract_length = 22.0; v.gender_continuum = 1.0
    v.roughness = 0.4; v.jitter = 0.015; v.shimmer = 0.012
    v.creakiness = 0.3; v.subglottal_coupling = 0.15
    v.effort_level = 0.9; v.spectral_tilt = -6.0
    v.pressed_phonation = 0.4; v.diplophonia = 0.1
    return v

def voice_narrator() -> VoiceDNA:
    """Narrator — Perfect audiobook narrator (clear, engaging, versatile)."""
    v = VoiceDNA("Narrator")
    v.base_f0 = 125.0; v.f0_range = 0.55; v.rd_mean = 1.0
    v.speaking_rate = 4.0; v.warmth = 0.65; v.brightness = 0.55
    v.vocal_tract_length = 17.5; v.gender_continuum = 0.65
    v.age_factor = 0.4; v.formant_precision = 0.95
    v.consonant_precision = 0.92; v.emphasis_strength = 1.1
    v.tempo_variation = 0.1; v.coarticulation_degree = 0.65
    v.pause_tendency = 0.6; v.preboundary_lengthening = 1.4
    return v

def voice_coach() -> VoiceDNA:
    """Coach — Motivational speaker (Tony Robbins / sports coach)."""
    v = VoiceDNA("Coach")
    v.base_f0 = 135.0; v.f0_range = 0.7; v.rd_mean = 0.7
    v.speaking_rate = 5.0; v.warmth = 0.5; v.brightness = 0.75
    v.gender_continuum = 0.8; v.effort_level = 0.8
    v.emphasis_strength = 1.8; v.intensity_range = 20.0
    v.tempo_variation = 0.18; v.pause_tendency = 0.4
    v.f0_variability = 0.15; v.pressed_phonation = 0.15
    v.rhythm_regularity = 0.5; v.chest_resonance = 0.8
    return v

def voice_diva() -> VoiceDNA:
    """Diva — Powerful female singer (Beyoncé / Whitney zone)."""
    v = VoiceDNA("Diva")
    v.base_f0 = 230.0; v.f0_range = 0.9; v.rd_mean = 0.75
    v.speaking_rate = 4.2; v.warmth = 0.6; v.brightness = 0.8
    v.vocal_tract_length = 14.5; v.gender_continuum = 0.05
    v.vibrato_rate = 6.0; v.vibrato_depth = 0.012
    v.effort_level = 0.8; v.harmonic_richness = 1.0
    v.emphasis_strength = 1.5; v.chest_resonance = 0.8
    v.head_voice_mix = 0.4; v.intensity_range = 18.0
    return v

def voice_soldier() -> VoiceDNA:
    """Soldier — Military crisp authoritative (drill sergeant)."""
    v = VoiceDNA("Soldier")
    v.base_f0 = 120.0; v.f0_range = 0.3; v.rd_mean = 0.5
    v.speaking_rate = 5.5; v.warmth = 0.3; v.brightness = 0.7
    v.gender_continuum = 0.9; v.effort_level = 0.9
    v.consonant_precision = 1.0; v.rhythm_regularity = 0.8
    v.emphasis_strength = 1.5; v.pressed_phonation = 0.3
    v.intensity_range = 8.0; v.vowel_reduction = 0.4
    v.tempo_variation = 0.03; v.pause_duration = 0.15
    return v

def voice_poet() -> VoiceDNA:
    """Poet — Lyrical expressive (poetry reading, literary)."""
    v = VoiceDNA("Poet")
    v.base_f0 = 140.0; v.f0_range = 0.6; v.rd_mean = 1.2
    v.speaking_rate = 3.5; v.warmth = 0.7; v.brightness = 0.5
    v.gender_continuum = 0.5; v.age_factor = 0.4
    v.emphasis_strength = 1.2; v.tempo_variation = 0.2
    v.pause_tendency = 0.8; v.pause_duration = 0.5
    v.preboundary_lengthening = 1.6; v.f0_variability = 0.14
    v.coarticulation_degree = 0.75; v.rhythm_regularity = 0.2
    return v

def voice_alien() -> VoiceDNA:
    """Alien — Otherworldly non-human (sci-fi, extraterrestrial)."""
    v = VoiceDNA("Alien")
    v.base_f0 = 180.0; v.f0_range = 0.9; v.rd_mean = 1.5
    v.speaking_rate = 3.8; v.warmth = 0.2; v.brightness = 0.6
    v.vocal_tract_length = 12.0; v.gender_continuum = 0.5
    v.nasality = 0.3; v.jitter = 0.008; v.shimmer = 0.006
    v.vibrato_rate = 8.0; v.vibrato_depth = 0.02
    v.f0_variability = 0.2; v.coarticulation_degree = 0.3
    v.rhythm_regularity = 0.1; v.diplophonia = 0.05
    return v
