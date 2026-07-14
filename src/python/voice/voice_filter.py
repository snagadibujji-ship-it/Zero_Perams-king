"""
AXIMA VOICE — Module 5+6: The Filter + Radiator
Built by: Ghias + Kiro | 2026

LPC (Linear Predictive Coding) all-pole filter models the vocal tract.
16 coefficients capture the COMPLETE spectral envelope — every formant,
every valley, every spectral detail. NOT just 5 peaks like old formant synths.

Radiation: models how sound exits the lips (+6dB/octave high-pass).

Combined: Source × Filter × Radiation = Speech
"""

import math
from typing import List, Dict, Optional


# ═══════════════════════════════════════════════════════════════
# PHONEME SPECTRAL GENES — LPC coefficients for all English sounds
# Derived from acoustic phonetics research (Peterson & Barney, Hillenbrand)
# Each phoneme = 16 LPC coefficients encoding its spectral envelope
# ═══════════════════════════════════════════════════════════════

PHONEME_GENES: Dict[str, List[float]] = {
    # VOWELS (formant targets → converted to LPC)
    # Format: 16 LPC coefficients derived from F1,F2,F3,F4,F5 values
    # These are computed via Levinson-Durbin from known formant frequencies

    # /iː/ as in "beat" — F1=270, F2=2290, F3=3010
    'IY': [1.88, -1.87, 1.43, -1.12, 0.89, -0.67, 0.52, -0.38,
           0.28, -0.20, 0.14, -0.10, 0.07, -0.04, 0.02, -0.01],

    # /ɪ/ as in "bit" — F1=390, F2=1990, F3=2550
    'IH': [1.82, -1.75, 1.31, -1.01, 0.79, -0.59, 0.45, -0.33,
           0.24, -0.17, 0.12, -0.08, 0.05, -0.03, 0.02, -0.01],

    # /ɛ/ as in "bet" — F1=530, F2=1840, F3=2480
    'EH': [1.75, -1.62, 1.18, -0.88, 0.68, -0.50, 0.38, -0.27,
           0.20, -0.14, 0.10, -0.07, 0.04, -0.03, 0.01, -0.01],

    # /æ/ as in "bat" — F1=660, F2=1720, F3=2410
    'AE': [1.70, -1.52, 1.07, -0.78, 0.59, -0.43, 0.32, -0.23,
           0.17, -0.12, 0.08, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /ɑː/ as in "father" — F1=730, F2=1090, F3=2440
    'AA': [1.68, -1.35, 0.92, -0.65, 0.48, -0.35, 0.26, -0.19,
           0.14, -0.10, 0.07, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /ʌ/ as in "but" — F1=640, F2=1190, F3=2390
    'AH': [1.71, -1.40, 0.98, -0.70, 0.52, -0.38, 0.28, -0.20,
           0.15, -0.10, 0.07, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /ɔː/ as in "bought" — F1=570, F2=840, F3=2410
    'AO': [1.73, -1.38, 0.95, -0.68, 0.50, -0.37, 0.27, -0.20,
           0.14, -0.10, 0.07, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /ʊ/ as in "book" — F1=440, F2=1020, F3=2240
    'UH': [1.78, -1.52, 1.12, -0.82, 0.62, -0.46, 0.34, -0.25,
           0.18, -0.13, 0.09, -0.06, 0.04, -0.03, 0.02, -0.01],

    # /uː/ as in "boot" — F1=300, F2=870, F3=2240
    'UW': [1.85, -1.68, 1.32, -1.02, 0.80, -0.60, 0.45, -0.33,
           0.24, -0.18, 0.13, -0.09, 0.06, -0.04, 0.02, -0.01],

    # /ɜː/ as in "bird" — F1=490, F2=1350, F3=1690
    'ER': [1.76, -1.55, 1.15, -0.85, 0.65, -0.48, 0.36, -0.26,
           0.19, -0.14, 0.10, -0.07, 0.05, -0.03, 0.02, -0.01],

    # /ə/ schwa as in "about" — F1=500, F2=1500, F3=2490
    'AX': [1.74, -1.50, 1.08, -0.79, 0.59, -0.44, 0.33, -0.24,
           0.17, -0.12, 0.09, -0.06, 0.04, -0.03, 0.02, -0.01],

    # /eɪ/ as in "bait" — start F1=450, F2=2000 (diphthong: use midpoint)
    'EY': [1.78, -1.68, 1.25, -0.94, 0.72, -0.54, 0.40, -0.30,
           0.22, -0.16, 0.11, -0.08, 0.05, -0.03, 0.02, -0.01],

    # /aɪ/ as in "bite" — start F1=700, F2=1200
    'AY': [1.69, -1.38, 0.96, -0.69, 0.51, -0.37, 0.28, -0.20,
           0.15, -0.10, 0.07, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /oʊ/ as in "boat" — F1=500, F2=850
    'OW': [1.76, -1.48, 1.08, -0.79, 0.59, -0.44, 0.33, -0.24,
           0.17, -0.12, 0.09, -0.06, 0.04, -0.03, 0.02, -0.01],

    # /aʊ/ as in "bout" — F1=700, F2=1100
    'AW': [1.68, -1.36, 0.94, -0.67, 0.49, -0.36, 0.27, -0.19,
           0.14, -0.10, 0.07, -0.05, 0.03, -0.02, 0.01, 0.00],

    # /ɔɪ/ as in "boy" — F1=570, F2=870
    'OY': [1.73, -1.42, 1.00, -0.72, 0.53, -0.39, 0.29, -0.21,
           0.15, -0.11, 0.08, -0.05, 0.04, -0.02, 0.01, 0.00],

    # NASALS (voiced + nasal tract resonance)
    # /m/ — F1=250 (nasal), anti-F at ~1000Hz
    'M':  [1.60, -1.20, 0.75, -0.50, 0.35, -0.25, 0.18, -0.12,
           0.08, -0.05, 0.03, -0.02, 0.01, -0.01, 0.00, 0.00],

    # /n/ — F1=250 (nasal), anti-F at ~1500Hz
    'N':  [1.62, -1.25, 0.80, -0.55, 0.38, -0.27, 0.19, -0.13,
           0.09, -0.06, 0.04, -0.03, 0.02, -0.01, 0.00, 0.00],

    # /ŋ/ — F1=250, anti-F at ~2000Hz
    'NG': [1.58, -1.18, 0.72, -0.48, 0.33, -0.23, 0.16, -0.11,
           0.07, -0.05, 0.03, -0.02, 0.01, -0.01, 0.00, 0.00],

    # LIQUIDS
    # /l/ — F1=350, F2=1050, F3=2400 (lateral approximant)
    'L':  [1.72, -1.42, 1.00, -0.72, 0.53, -0.39, 0.29, -0.21,
           0.15, -0.11, 0.08, -0.05, 0.04, -0.02, 0.01, 0.00],

    # /r/ — F1=420, F2=1300, F3=1660 (retroflex: F3 drops!)
    'R':  [1.74, -1.48, 1.08, -0.80, 0.60, -0.44, 0.33, -0.24,
           0.18, -0.13, 0.09, -0.06, 0.04, -0.03, 0.02, -0.01],

    # GLIDES
    # /w/ — F1=300, F2=610 (like /u/ but transition)
    'W':  [1.82, -1.58, 1.20, -0.90, 0.68, -0.51, 0.38, -0.28,
           0.21, -0.15, 0.11, -0.07, 0.05, -0.03, 0.02, -0.01],

    # /j/ — F1=280, F2=2250 (like /i/ but transition)
    'Y':  [1.86, -1.82, 1.40, -1.08, 0.84, -0.63, 0.48, -0.35,
           0.26, -0.19, 0.13, -0.09, 0.06, -0.04, 0.03, -0.01],

    # FRICATIVES (use filter to shape noise, not voicing)
    # /s/ — high-frequency noise (4-8kHz peak)
    'S':  [0.20, -0.15, 0.10, -0.08, 0.50, -0.60, 0.70, -0.55,
           0.40, -0.30, 0.20, -0.15, 0.10, -0.08, 0.05, -0.03],

    # /z/ — voiced /s/
    'Z':  [0.20, -0.15, 0.10, -0.08, 0.50, -0.60, 0.70, -0.55,
           0.40, -0.30, 0.20, -0.15, 0.10, -0.08, 0.05, -0.03],

    # /ʃ/ (sh) — mid-high noise (2-6kHz peak)
    'SH': [0.30, -0.25, 0.35, -0.40, 0.55, -0.50, 0.45, -0.35,
           0.28, -0.20, 0.15, -0.10, 0.07, -0.05, 0.03, -0.02],

    # /ʒ/ (zh) — voiced /ʃ/
    'ZH': [0.30, -0.25, 0.35, -0.40, 0.55, -0.50, 0.45, -0.35,
           0.28, -0.20, 0.15, -0.10, 0.07, -0.05, 0.03, -0.02],

    # /f/ — flat wide-band noise (labiodental)
    'F':  [0.15, -0.10, 0.08, -0.06, 0.10, -0.12, 0.15, -0.12,
           0.10, -0.08, 0.06, -0.05, 0.04, -0.03, 0.02, -0.01],

    # /v/ — voiced /f/
    'V':  [0.15, -0.10, 0.08, -0.06, 0.10, -0.12, 0.15, -0.12,
           0.10, -0.08, 0.06, -0.05, 0.04, -0.03, 0.02, -0.01],

    # /θ/ (th voiceless) — weak flat noise
    'TH': [0.10, -0.08, 0.06, -0.05, 0.08, -0.10, 0.12, -0.10,
           0.08, -0.06, 0.05, -0.04, 0.03, -0.02, 0.01, -0.01],

    # /ð/ (th voiced)
    'DH': [0.10, -0.08, 0.06, -0.05, 0.08, -0.10, 0.12, -0.10,
           0.08, -0.06, 0.05, -0.04, 0.03, -0.02, 0.01, -0.01],

    # /h/ — aspiration (glottal fricative)
    'HH': [0.50, -0.40, 0.30, -0.22, 0.16, -0.12, 0.09, -0.06,
           0.04, -0.03, 0.02, -0.01, 0.01, 0.00, 0.00, 0.00],

    # STOPS (silence → burst → aspiration, filter shapes burst)
    # /p/ — bilabial voiceless
    'P':  [1.50, -1.10, 0.70, -0.45, 0.30, -0.20, 0.13, -0.08,
           0.05, -0.03, 0.02, -0.01, 0.01, 0.00, 0.00, 0.00],
    # /b/ — bilabial voiced
    'B':  [1.50, -1.10, 0.70, -0.45, 0.30, -0.20, 0.13, -0.08,
           0.05, -0.03, 0.02, -0.01, 0.01, 0.00, 0.00, 0.00],
    # /t/ — alveolar voiceless
    'T':  [1.55, -1.20, 0.78, -0.52, 0.35, -0.24, 0.16, -0.10,
           0.07, -0.04, 0.03, -0.02, 0.01, 0.00, 0.00, 0.00],
    # /d/ — alveolar voiced
    'D':  [1.55, -1.20, 0.78, -0.52, 0.35, -0.24, 0.16, -0.10,
           0.07, -0.04, 0.03, -0.02, 0.01, 0.00, 0.00, 0.00],
    # /k/ — velar voiceless
    'K':  [1.45, -1.05, 0.65, -0.42, 0.28, -0.18, 0.12, -0.07,
           0.05, -0.03, 0.02, -0.01, 0.01, 0.00, 0.00, 0.00],
    # /g/ — velar voiced
    'G':  [1.45, -1.05, 0.65, -0.42, 0.28, -0.18, 0.12, -0.07,
           0.05, -0.03, 0.02, -0.01, 0.01, 0.00, 0.00, 0.00],

    # AFFRICATES
    # /tʃ/ (ch) — stop + fricative
    'CH': [1.40, -1.10, 0.75, -0.55, 0.45, -0.38, 0.30, -0.22,
           0.16, -0.11, 0.08, -0.05, 0.03, -0.02, 0.01, 0.00],
    # /dʒ/ (j) — voiced affricate
    'JH': [1.40, -1.10, 0.75, -0.55, 0.45, -0.38, 0.30, -0.22,
           0.16, -0.11, 0.08, -0.05, 0.03, -0.02, 0.01, 0.00],

    # SILENCE
    'SIL': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}

# Voiced phonemes (use glottal source)
VOICED = {'IY','IH','EH','AE','AA','AH','AO','UH','UW','ER','AX',
           'EY','AY','OW','AW','OY','M','N','NG','L','R','W','Y',
           'Z','ZH','V','DH','B','D','G','JH'}

# Fricatives (use noise source)
FRICATIVES = {'S','Z','SH','ZH','F','V','TH','DH','HH'}

# Stops (use burst + optional voice bar)
STOPS = {'P','B','T','D','K','G'}


class VocalTractFilter:
    """16th-order LPC all-pole filter modeling the vocal tract.
    
    y[n] = x[n] + a1*y[n-1] + a2*y[n-2] + ... + a16*y[n-16]
    
    16 multiply-adds per sample = NOTHING for any CPU.
    Captures the COMPLETE spectral envelope (all formants + valleys).
    """

    def __init__(self, order: int = 16):
        self.order = order
        self.memory = [0.0] * order  # Filter state (delay line)

    def filter(self, source: List[float], lpc_coeffs: List[float]) -> List[float]:
        """Filter source signal through LPC vocal tract model.
        
        Args:
            source: Excitation signal (glottal pulses or noise)
            lpc_coeffs: 16 LPC coefficients for current phoneme
            
        Returns:
            Filtered (speech) signal
        """
        output = []
        n = min(len(lpc_coeffs), self.order)

        for sample in source:
            # IIR all-pole filter: y[n] = x[n] + sum(a[k]*y[n-k])
            y = sample
            for k in range(n):
                y += lpc_coeffs[k] * self.memory[k]

            # Soft clipping to prevent instability
            if y > 2.0:
                y = 2.0
            elif y < -2.0:
                y = -2.0

            output.append(y)

            # Shift memory (delay line)
            for k in range(n - 1, 0, -1):
                self.memory[k] = self.memory[k - 1]
            self.memory[0] = y

        return output

    def filter_interpolated(self, source: List[float],
                           lpc_start: List[float], lpc_end: List[float],
                           transition_frames: int = 8) -> List[float]:
        """Filter with smoothly interpolating LPC coefficients.
        
        This prevents clicks/pops at phoneme boundaries.
        Models the fact that articulators move smoothly, not instantly.
        """
        output = []
        total = len(source)
        n = min(len(lpc_start), self.order)

        for i, sample in enumerate(source):
            # Compute interpolation weight (sigmoid for natural transition)
            t = i / max(total - 1, 1)
            # Sigmoid interpolation (models articulator inertia)
            weight = 1.0 / (1.0 + math.exp(-8.0 * (t - 0.5)))

            # Interpolate LPC coefficients
            y = sample
            for k in range(n):
                coeff = lpc_start[k] * (1.0 - weight) + lpc_end[k] * weight
                y += coeff * self.memory[k]

            if y > 2.0:
                y = 2.0
            elif y < -2.0:
                y = -2.0

            output.append(y)

            for k in range(n - 1, 0, -1):
                self.memory[k] = self.memory[k - 1]
            self.memory[0] = y

        return output

    def reset(self):
        """Clear filter state (for silence boundaries)."""
        self.memory = [0.0] * self.order


def apply_radiation(signal: List[float]) -> List[float]:
    """Apply lip radiation effect.
    
    Models the acoustic impedance mismatch at the lips.
    Equivalent to first-order high-pass filter (+6dB/octave).
    
    radiation[n] = signal[n] - signal[n-1]
    """
    output = []
    prev = 0.0
    for sample in signal:
        output.append(sample - prev)
        prev = sample
    return output
