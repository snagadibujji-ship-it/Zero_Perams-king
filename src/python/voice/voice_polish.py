"""
AXIMA VOICE — Module 10: The Polisher (ElevenLabs-quality post-processing)
Built by: Ghias + Kiro | 2026

Final audio processing that takes synthesis from "good" to "professional studio."
This is the difference between a demo and a product.

Includes:
- Presence boost (3-5kHz clarity)
- Warmth (200-400Hz body)
- De-essing (dynamic sibilant control)
- Soft compression (natural dynamics)
- Spectral smoothing (removes digital artifacts)
"""

import math
from typing import List


class AudioPolisher:
    """Professional-grade audio post-processing for synthesized speech."""

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        # Biquad filter states
        self._presence_z1 = 0.0
        self._presence_z2 = 0.0
        self._warmth_z1 = 0.0
        self._warmth_z2 = 0.0
        self._hp_z1 = 0.0
        self._hp_z2 = 0.0

    def polish(self, audio: List[float], 
               presence: float = 2.0,
               warmth: float = 1.5,
               compression: float = 0.3,
               deess: float = 0.5) -> List[float]:
        """Apply full polishing chain.
        
        Args:
            audio: Input audio
            presence: Presence boost in dB at 3-5kHz (0-4)
            warmth: Warmth boost in dB at 200-400Hz (0-3)
            compression: Compression amount (0-1)
            deess: De-essing amount (0-1)
        """
        if not audio:
            return audio

        result = list(audio)

        # 1. High-pass filter (remove sub-80Hz rumble)
        result = self._highpass(result, 80.0)

        # 2. Warmth boost (200-400Hz low shelf)
        if warmth > 0:
            result = self._boost_band(result, 300.0, warmth, 1.0)

        # 3. Presence boost (3-5kHz for clarity and "air")
        if presence > 0:
            result = self._boost_band(result, 4000.0, presence, 2.0)

        # 4. De-essing (tame sibilants at 5-8kHz)
        if deess > 0:
            result = self._deess(result, deess)

        # 5. Soft compression (keep dynamics natural but controlled)
        if compression > 0:
            result = self._compress(result, compression)

        # 6. Final limiter (prevent clipping)
        result = self._soft_clip(result)

        return result

    def _highpass(self, audio: List[float], cutoff: float) -> List[float]:
        """First-order high-pass filter to remove DC and rumble."""
        rc = 1.0 / (2.0 * math.pi * cutoff)
        dt = 1.0 / self.sr
        alpha = rc / (rc + dt)

        result = []
        prev_in = 0.0
        prev_out = 0.0
        for sample in audio:
            out = alpha * (prev_out + sample - prev_in)
            prev_in = sample
            prev_out = out
            result.append(out)
        return result

    def _boost_band(self, audio: List[float], freq: float, 
                    gain_db: float, q: float) -> List[float]:
        """Parametric EQ boost at specified frequency."""
        # Biquad peaking EQ coefficients
        w0 = 2.0 * math.pi * freq / self.sr
        A = 10.0 ** (gain_db / 40.0)
        alpha = math.sin(w0) / (2.0 * q)

        b0 = 1.0 + alpha * A
        b1 = -2.0 * math.cos(w0)
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * math.cos(w0)
        a2 = 1.0 - alpha / A

        # Normalize
        b0 /= a0; b1 /= a0; b2 /= a0
        a1 /= a0; a2 /= a0

        # Apply biquad
        result = []
        x1 = x2 = y1 = y2 = 0.0
        for sample in audio:
            y = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2 = x1; x1 = sample
            y2 = y1; y1 = y
            result.append(y)
        return result

    def _deess(self, audio: List[float], amount: float) -> List[float]:
        """Dynamic de-esser: reduce energy at 5-8kHz when it exceeds threshold."""
        # Detect sibilant energy using bandpass at 6kHz
        w0 = 2.0 * math.pi * 6000.0 / self.sr
        q = 2.0
        alpha = math.sin(w0) / (2.0 * q)
        # Bandpass coefficients
        b0 = alpha
        b1 = 0.0
        b2 = -alpha
        a0 = 1.0 + alpha
        a1 = -2.0 * math.cos(w0)
        a2 = 1.0 - alpha
        b0 /= a0; b1 /= a0; b2 /= a0; a1 /= a0; a2 /= a0

        result = []
        x1 = x2 = y1 = y2 = 0.0
        env = 0.0
        threshold = 0.15

        for sample in audio:
            # Detect sibilant
            det = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2 = x1; x1 = sample; y2 = y1; y1 = det

            # Envelope follower
            env = max(abs(det), env * 0.999)

            # If sibilant detected, reduce gain
            if env > threshold:
                reduction = 1.0 - amount * min(1.0, (env - threshold) / threshold)
                result.append(sample * max(0.3, reduction))
            else:
                result.append(sample)

        return result

    def _compress(self, audio: List[float], amount: float) -> List[float]:
        """Soft compression: 2:1 ratio above threshold."""
        threshold = 0.4
        ratio = 2.0
        attack = 0.005 * self.sr  # 5ms attack
        release = 0.05 * self.sr   # 50ms release

        result = []
        envelope = 0.0

        for sample in audio:
            level = abs(sample)
            # Envelope follower
            if level > envelope:
                envelope += (level - envelope) / attack
            else:
                envelope += (level - envelope) / release

            # Compression
            if envelope > threshold:
                over = envelope - threshold
                gain_reduction = over * (1.0 - 1.0/ratio) * amount
                gain = 1.0 - gain_reduction / max(envelope, 0.001)
                result.append(sample * max(0.2, gain))
            else:
                result.append(sample)

        return result

    def _soft_clip(self, audio: List[float]) -> List[float]:
        """Soft clipping limiter (tanh-style)."""
        result = []
        for sample in audio:
            if abs(sample) > 0.9:
                # Soft saturation
                result.append(math.tanh(sample * 1.5) * 0.85)
            else:
                result.append(sample)
        return result
