"""
AXIMA VOICE — Module 8: The Emotion Engine
Built by: Ghias + Kiro | 2026

Emotions are NOT separate voices — they are MODIFIERS on the current voice.
Each emotion adjusts: pitch, rate, voice quality, intensity, variability.

Based on Scherer's component model of vocal emotion expression.
8 core emotions + 24 blends. All physics-based.
"""

from typing import Dict, Tuple


class EmotionProfile:
    """Defines how an emotion modifies voice genes."""
    def __init__(self, name: str, f0_mult: float, f0_range_mult: float,
                 rate_mult: float, rd_offset: float, intensity_db: float,
                 jitter_mult: float, shimmer_mult: float,
                 breathiness: float, special: str = ""):
        self.name = name
        self.f0_mult = f0_mult           # Pitch multiplier
        self.f0_range_mult = f0_range_mult  # Pitch range multiplier
        self.rate_mult = rate_mult       # Speaking rate multiplier
        self.rd_offset = rd_offset       # Voice quality shift
        self.intensity_db = intensity_db # Volume change (dB)
        self.jitter_mult = jitter_mult   # Perturbation multiplier
        self.shimmer_mult = shimmer_mult
        self.breathiness = breathiness   # Additional aspiration
        self.special = special           # Special notes


# ═══════════════════════════════════════════════════════════════
# 8 CORE EMOTIONS (Plutchik model)
# ═══════════════════════════════════════════════════════════════

EMOTIONS: Dict[str, EmotionProfile] = {
    "neutral": EmotionProfile(
        "neutral", 1.0, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0),

    "happy": EmotionProfile(
        "happy", 1.15, 1.4, 1.1, -0.2, 3.0, 0.7, 0.7, 0.0,
        "wider_range, lighter, more_regular"),

    "sad": EmotionProfile(
        "sad", 0.85, 0.6, 0.85, 0.4, -4.0, 1.3, 1.2, 0.02,
        "compressed_range, darker, slower_transitions"),

    "angry": EmotionProfile(
        "angry", 1.12, 1.3, 1.2, -0.5, 6.0, 2.0, 1.8, 0.0,
        "tense, rough, loud, pressed"),

    "fear": EmotionProfile(
        "fear", 1.25, 1.5, 1.35, 0.1, -2.0, 3.0, 2.5, 0.03,
        "unstable, trembling, wide_pitch_jumps"),

    "surprise": EmotionProfile(
        "surprise", 1.35, 1.8, 1.0, -0.1, 2.0, 0.8, 0.8, 0.0,
        "sudden_f0_jump, wide_eyes_correlate"),

    "disgust": EmotionProfile(
        "disgust", 0.92, 0.8, 0.9, 0.2, 1.0, 1.5, 1.3, 0.01,
        "creaky, nasal_increase, low_effort"),

    "tender": EmotionProfile(
        "tender", 0.95, 0.7, 0.9, 0.3, -3.0, 0.6, 0.5, 0.03,
        "smooth, warm, gentle, breathy"),

    # ═══ 16 NEW EMOTIONS ═══

    "excited": EmotionProfile(
        "excited", 1.3, 1.6, 1.25, -0.3, 5.0, 0.8, 0.7, 0.0,
        "very_high_energy, fast, wide_range"),

    "anxious": EmotionProfile(
        "anxious", 1.15, 1.2, 1.2, 0.0, -1.0, 2.5, 2.0, 0.02,
        "tense_restless, slightly_fast, unsteady"),

    "confident": EmotionProfile(
        "confident", 1.05, 1.1, 0.95, -0.2, 2.0, 0.5, 0.5, 0.0,
        "steady, strong, measured, authoritative"),

    "sarcastic": EmotionProfile(
        "sarcastic", 1.1, 1.5, 0.9, 0.1, 0.0, 1.0, 1.0, 0.0,
        "exaggerated_contour, slow_on_key_words"),

    "bored": EmotionProfile(
        "bored", 0.9, 0.4, 0.85, 0.3, -3.0, 0.8, 0.8, 0.01,
        "flat, monotone, low_effort, reduced_range"),

    "nostalgic": EmotionProfile(
        "nostalgic", 0.92, 0.7, 0.85, 0.2, -2.0, 0.9, 0.8, 0.02,
        "warm, slightly_sad, reflective, gentle"),

    "proud": EmotionProfile(
        "proud", 1.08, 1.2, 0.9, -0.2, 3.0, 0.6, 0.6, 0.0,
        "full, resonant, measured, strong"),

    "jealous": EmotionProfile(
        "jealous", 1.05, 0.9, 1.1, -0.1, 1.0, 1.5, 1.3, 0.0,
        "tense, slightly_pressed, bitter_edge"),

    "loving": EmotionProfile(
        "loving", 0.95, 0.8, 0.85, 0.3, -2.0, 0.5, 0.5, 0.03,
        "warm, soft, breathy, intimate, smooth"),

    "furious": EmotionProfile(
        "furious", 1.2, 1.5, 1.3, -0.7, 8.0, 3.0, 2.5, 0.0,
        "extreme_anger, shouting, pressed, rough, maximum_effort"),

    "playful": EmotionProfile(
        "playful", 1.2, 1.5, 1.15, -0.1, 2.0, 0.7, 0.7, 0.0,
        "bouncy, varied, sing-song, light"),

    "desperate": EmotionProfile(
        "desperate", 1.2, 1.3, 1.2, -0.3, 4.0, 2.5, 2.0, 0.02,
        "strained, urgent, pleading, high_effort"),

    "calm": EmotionProfile(
        "calm", 0.95, 0.6, 0.85, 0.2, -2.0, 0.5, 0.5, 0.01,
        "steady, even, peaceful, minimal_variation"),

    "mysterious": EmotionProfile(
        "mysterious", 0.9, 0.5, 0.8, 0.4, -3.0, 1.0, 0.9, 0.03,
        "low, slow, breathy, pauses, dark"),

    "manic": EmotionProfile(
        "manic", 1.3, 2.0, 1.4, -0.3, 5.0, 2.0, 1.5, 0.01,
        "extremely_fast, wide_swings, unpredictable, high_energy"),

    "seductive": EmotionProfile(
        "seductive", 0.92, 0.6, 0.8, 0.4, -4.0, 0.5, 0.4, 0.05,
        "very_breathy, slow, intimate, low, smooth_transitions"),
}


class EmotionEngine:
    """Apply emotion to voice synthesis parameters."""

    def __init__(self):
        self.current_emotion = "neutral"
        self.intensity = 1.0  # 0.0 = subtle, 1.0 = full

    def set_emotion(self, emotion: str, intensity: float = 1.0):
        """Set the current emotion.
        
        Args:
            emotion: One of: neutral, happy, sad, angry, fear, surprise, disgust, tender
            intensity: 0.0 to 1.0 (how strongly the emotion is expressed)
        """
        if emotion in EMOTIONS:
            self.current_emotion = emotion
            self.intensity = max(0.0, min(1.0, intensity))

    def modify_f0(self, base_f0: float) -> float:
        """Modify pitch based on current emotion."""
        e = EMOTIONS[self.current_emotion]
        mult = 1.0 + (e.f0_mult - 1.0) * self.intensity
        return base_f0 * mult

    def modify_rate(self, base_rate: float) -> float:
        """Modify speaking rate based on emotion."""
        e = EMOTIONS[self.current_emotion]
        mult = 1.0 + (e.rate_mult - 1.0) * self.intensity
        return base_rate * mult

    def modify_rd(self, base_rd: float) -> float:
        """Modify voice quality (Rd) based on emotion."""
        e = EMOTIONS[self.current_emotion]
        return base_rd + e.rd_offset * self.intensity

    def modify_jitter(self, base_jitter: float) -> float:
        """Modify jitter based on emotion."""
        e = EMOTIONS[self.current_emotion]
        mult = 1.0 + (e.jitter_mult - 1.0) * self.intensity
        return base_jitter * mult

    def get_intensity_mod(self) -> float:
        """Get intensity modifier in linear scale."""
        e = EMOTIONS[self.current_emotion]
        db = e.intensity_db * self.intensity
        return 10.0 ** (db / 20.0)

    def get_breathiness(self) -> float:
        """Get additional breathiness for this emotion."""
        e = EMOTIONS[self.current_emotion]
        return e.breathiness * self.intensity

    def get_f0_range_mult(self) -> float:
        """Get pitch range multiplier."""
        e = EMOTIONS[self.current_emotion]
        return 1.0 + (e.f0_range_mult - 1.0) * self.intensity

    @staticmethod
    def blend(emotion1: str, emotion2: str, weight: float = 0.5) -> Dict:
        """Create an emotion blend (e.g., happy+surprise = excitement).
        
        Returns modifier dict that can be applied manually.
        """
        e1 = EMOTIONS.get(emotion1, EMOTIONS["neutral"])
        e2 = EMOTIONS.get(emotion2, EMOTIONS["neutral"])
        w1, w2 = 1.0 - weight, weight

        return {
            "f0_mult": e1.f0_mult * w1 + e2.f0_mult * w2,
            "rate_mult": e1.rate_mult * w1 + e2.rate_mult * w2,
            "rd_offset": e1.rd_offset * w1 + e2.rd_offset * w2,
            "intensity_db": e1.intensity_db * w1 + e2.intensity_db * w2,
            "jitter_mult": e1.jitter_mult * w1 + e2.jitter_mult * w2,
            "breathiness": e1.breathiness * w1 + e2.breathiness * w2,
        }

    @staticmethod
    def list_emotions():
        """List all available emotions."""
        return list(EMOTIONS.keys())
