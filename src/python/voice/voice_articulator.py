"""
AXIMA VOICE — Beast Mode: Articulator System
Built by: Ghias + Kiro | 2026

Maps phonemes to vocal tract AREA FUNCTIONS.
Each phoneme = a specific shape of the 44-section tube.

Area functions derived from:
- MRI studies of vocal tract during speech (Baer et al., Story et al.)
- X-ray microbeam data
- Published acoustic phonetics research

The articulators (tongue, jaw, lips, velum) have PHYSICAL MASS.
They can't teleport — they move with spring-damper dynamics.
This creates NATURAL coarticulation without any rules.
"""

import math
from typing import List, Dict, Tuple


# ═══════════════════════════════════════════════════════════════
# AREA FUNCTIONS PER PHONEME
# 44 values representing cross-sectional area (cm²) from glottis to lips
# Based on published MRI/X-ray data (simplified to key control points,
# then interpolated to 44 sections)
# ═══════════════════════════════════════════════════════════════

def _interpolate_areas(control_points: List[Tuple[int, float]], num_sections: int = 22) -> List[float]:
    """Interpolate sparse control points to num_sections sections.
    Control points are specified as if 44 sections — we rescale to 22."""
    areas = [4.0] * num_sections
    # Rescale control point indices from 0-43 range to 0-21 range
    scaled_points = [(int(idx * (num_sections - 1) / 43), val) for idx, val in control_points]
    for i in range(len(scaled_points) - 1):
        idx1, val1 = scaled_points[i]
        idx2, val2 = scaled_points[i + 1]
        if idx2 <= idx1:
            idx2 = idx1 + 1
        for j in range(idx1, min(idx2 + 1, num_sections)):
            t = (j - idx1) / max(idx2 - idx1, 1)
            areas[j] = val1 + (val2 - val1) * t
    return areas


# Vowel area functions (from MRI studies)
VOWEL_AREAS: Dict[str, List[float]] = {
    # /i/ "beat" — tongue high front, narrow pharynx wide mouth
    'IY': _interpolate_areas([(0, 1.0), (5, 0.8), (15, 0.6), (25, 0.4), (30, 1.5), (35, 4.0), (40, 6.0), (43, 3.0)]),
    # /ɪ/ "bit" — slightly lower than /i/
    'IH': _interpolate_areas([(0, 1.2), (5, 1.0), (15, 0.8), (25, 0.6), (30, 2.0), (35, 4.5), (40, 5.0), (43, 3.0)]),
    # /ɛ/ "bet" — mid front
    'EH': _interpolate_areas([(0, 1.5), (5, 1.2), (15, 1.0), (25, 1.5), (30, 3.0), (35, 5.0), (40, 5.0), (43, 3.5)]),
    # /æ/ "bat" — low front, wide pharynx
    'AE': _interpolate_areas([(0, 2.0), (5, 1.8), (15, 2.5), (25, 3.5), (30, 4.5), (35, 5.5), (40, 5.0), (43, 4.0)]),
    # /ɑ/ "father" — low back, wide pharynx narrow mouth
    'AA': _interpolate_areas([(0, 2.5), (5, 3.0), (15, 4.5), (25, 5.5), (30, 4.0), (35, 2.5), (40, 2.0), (43, 2.5)]),
    # /ʌ/ "but" — mid central
    'AH': _interpolate_areas([(0, 2.0), (5, 2.5), (15, 3.5), (25, 4.0), (30, 3.5), (35, 3.0), (40, 3.0), (43, 3.0)]),
    # /ɔ/ "bought" — mid back rounded
    'AO': _interpolate_areas([(0, 2.0), (5, 2.5), (15, 4.0), (25, 5.0), (30, 3.5), (35, 2.0), (40, 1.5), (43, 1.5)]),
    # /ʊ/ "book" — high back rounded
    'UH': _interpolate_areas([(0, 1.5), (5, 2.0), (15, 3.5), (25, 4.5), (30, 3.0), (35, 1.5), (40, 1.0), (43, 1.0)]),
    # /u/ "boot" — high back very rounded
    'UW': _interpolate_areas([(0, 1.0), (5, 1.5), (15, 3.0), (25, 5.0), (30, 3.0), (35, 1.0), (40, 0.5), (43, 0.5)]),
    # /ɜ/ "bird" — mid central r-colored
    'ER': _interpolate_areas([(0, 1.5), (5, 2.0), (15, 2.5), (25, 2.0), (30, 1.5), (35, 2.5), (40, 3.5), (43, 3.0)]),
    # /ə/ "about" — neutral (schwa, uniform tube)
    'AX': _interpolate_areas([(0, 2.0), (5, 2.5), (15, 3.0), (25, 3.5), (30, 3.5), (35, 3.5), (40, 3.5), (43, 3.0)]),
    # Diphthongs: use midpoint (transitions handled by articulator dynamics)
    'EY': _interpolate_areas([(0, 1.5), (5, 1.2), (15, 1.0), (25, 1.5), (30, 3.0), (35, 5.0), (40, 5.5), (43, 3.5)]),
    'AY': _interpolate_areas([(0, 2.5), (5, 3.0), (15, 4.0), (25, 4.5), (30, 4.0), (35, 3.5), (40, 3.0), (43, 3.0)]),
    'OW': _interpolate_areas([(0, 2.0), (5, 2.5), (15, 3.5), (25, 4.5), (30, 3.0), (35, 2.0), (40, 1.5), (43, 1.5)]),
    'AW': _interpolate_areas([(0, 2.5), (5, 3.0), (15, 4.5), (25, 5.0), (30, 3.5), (35, 2.0), (40, 1.5), (43, 2.0)]),
    'OY': _interpolate_areas([(0, 2.0), (5, 2.5), (15, 4.0), (25, 5.0), (30, 3.5), (35, 2.0), (40, 1.5), (43, 1.5)]),
}

# Consonant area functions
CONSONANT_AREAS: Dict[str, List[float]] = {
    # Bilabial /p,b,m/ — lips closed (section 43-44 near zero)
    'P': _interpolate_areas([(0, 2.0), (15, 3.0), (25, 4.0), (35, 4.5), (40, 2.0), (42, 0.5), (43, 0.05)]),
    'B': _interpolate_areas([(0, 2.0), (15, 3.0), (25, 4.0), (35, 4.5), (40, 2.0), (42, 0.5), (43, 0.05)]),
    'M': _interpolate_areas([(0, 2.0), (15, 3.0), (25, 4.0), (35, 4.5), (40, 2.0), (42, 0.5), (43, 0.05)]),
    # Alveolar /t,d,n/ — tongue tip closure at section ~35
    'T': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 4.0), (34, 2.0), (35, 0.05), (37, 0.05), (40, 3.0), (43, 3.0)]),
    'D': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 4.0), (34, 2.0), (35, 0.05), (37, 0.05), (40, 3.0), (43, 3.0)]),
    'N': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 4.0), (34, 2.0), (35, 0.05), (37, 0.05), (40, 3.0), (43, 3.0)]),
    # Velar /k,g,ng/ — tongue body closure at section ~25
    'K': _interpolate_areas([(0, 2.0), (15, 3.5), (22, 3.0), (24, 0.05), (26, 0.05), (30, 3.5), (35, 4.5), (40, 4.0), (43, 3.5)]),
    'G': _interpolate_areas([(0, 2.0), (15, 3.5), (22, 3.0), (24, 0.05), (26, 0.05), (30, 3.5), (35, 4.5), (40, 4.0), (43, 3.5)]),
    'NG': _interpolate_areas([(0, 2.0), (15, 3.5), (22, 3.0), (24, 0.05), (26, 0.05), (30, 3.5), (35, 4.5), (40, 4.0), (43, 3.5)]),
    # Fricatives — narrow constriction (not fully closed)
    # /s/ alveolar fricative — narrow gap at section 35
    'S': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 4.0), (34, 1.5), (35, 0.15), (37, 0.2), (40, 3.0), (43, 2.5)]),
    'Z': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 4.0), (34, 1.5), (35, 0.15), (37, 0.2), (40, 3.0), (43, 2.5)]),
    # /ʃ/ postalveolar — constriction slightly further back
    'SH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 3.0), (32, 0.2), (34, 0.2), (37, 2.5), (40, 2.0), (43, 2.0)]),
    'ZH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 3.0), (32, 0.2), (34, 0.2), (37, 2.5), (40, 2.0), (43, 2.0)]),
    # /f,v/ labiodental — narrow at lips
    'F': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (35, 4.5), (40, 3.0), (42, 1.0), (43, 0.15)]),
    'V': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (35, 4.5), (40, 3.0), (42, 1.0), (43, 0.15)]),
    # /θ,ð/ dental — tongue between teeth
    'TH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (35, 4.0), (38, 2.0), (40, 0.8), (42, 0.2), (43, 0.3)]),
    'DH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (35, 4.0), (38, 2.0), (40, 0.8), (42, 0.2), (43, 0.3)]),
    # /h/ glottal — open tract, constriction at glottis only
    'HH': _interpolate_areas([(0, 0.5), (5, 2.0), (15, 3.5), (25, 4.0), (35, 4.0), (40, 3.5), (43, 3.0)]),
    # Liquids
    'L': _interpolate_areas([(0, 2.0), (15, 3.0), (25, 4.0), (30, 3.5), (34, 1.0), (35, 0.5), (37, 2.0), (40, 4.0), (43, 3.5)]),
    'R': _interpolate_areas([(0, 1.5), (15, 2.5), (25, 2.0), (30, 1.5), (33, 1.0), (35, 1.5), (38, 2.5), (40, 3.5), (43, 3.0)]),
    # Glides
    'W': _interpolate_areas([(0, 1.0), (5, 1.5), (15, 3.0), (25, 5.0), (30, 3.0), (35, 1.0), (40, 0.5), (43, 0.4)]),
    'Y': _interpolate_areas([(0, 1.0), (5, 0.8), (15, 0.6), (25, 0.5), (30, 1.5), (35, 4.0), (40, 5.5), (43, 3.0)]),
    # Affricates (use stop position)
    'CH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 3.0), (32, 0.1), (34, 0.1), (37, 2.5), (40, 2.0), (43, 2.0)]),
    'JH': _interpolate_areas([(0, 2.0), (15, 3.5), (25, 4.5), (30, 3.0), (32, 0.1), (34, 0.1), (37, 2.5), (40, 2.0), (43, 2.0)]),
}

# Combine into single lookup
PHONEME_AREAS: Dict[str, List[float]] = {}
PHONEME_AREAS.update(VOWEL_AREAS)
PHONEME_AREAS.update(CONSONANT_AREAS)

# Which phonemes are nasal (need velum open)
NASALS = {'M', 'N', 'NG'}

# Which phonemes are fricatives (need turbulence noise)
FRICATIVE_PHONES = {'S', 'Z', 'SH', 'ZH', 'F', 'V', 'TH', 'DH', 'HH'}

# Which phonemes are stops (closure then release)
STOP_PHONES = {'P', 'B', 'T', 'D', 'K', 'G'}

# Which are voiced
VOICED_PHONES = {'IY','IH','EH','AE','AA','AH','AO','UH','UW','ER','AX',
                 'EY','AY','OW','AW','OY','M','N','NG','L','R','W','Y',
                 'Z','ZH','V','DH','B','D','G','JH'}


class Articulator:
    """Physical articulator model with mass and spring dynamics.
    
    Real articulators (tongue, jaw, lips) have INERTIA.
    They can't change shape instantly — they accelerate and decelerate.
    This creates NATURAL coarticulation from physics alone.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.num_sections = 22  # Match tract model
        # Current area function (starts at neutral schwa)
        self.current_area = list(PHONEME_AREAS.get('AX', [4.0] * self.num_sections))
        # Target area function
        self.target_area = list(self.current_area)
        # Velocity (for spring-damper dynamics)
        self.velocity = [0.0] * self.num_sections
        # Spring constant (controls speed of movement)
        self.stiffness = 800.0  # Higher = faster transitions
        # Damping (prevents oscillation)
        self.damping = 60.0

    def set_target(self, phoneme: str):
        """Set target area function for a phoneme."""
        if phoneme in PHONEME_AREAS:
            self.target_area = list(PHONEME_AREAS[phoneme])
        elif phoneme == 'SIL':
            self.target_area = [2.0] * self.num_sections

    def update(self) -> List[float]:
        """Advance articulator physics by one sample."""
        dt = 1.0 / self.sr

        for i in range(self.num_sections):
            displacement = self.current_area[i] - self.target_area[i]
            spring_force = -self.stiffness * displacement
            damp_force = -self.damping * self.velocity[i]
            accel = spring_force + damp_force
            self.velocity[i] += accel * dt
            self.current_area[i] += self.velocity[i] * dt
            self.current_area[i] = max(0.01, min(10.0, self.current_area[i]))

        return self.current_area

    def get_velum(self, phoneme: str) -> float:
        """Get velum opening for current phoneme."""
        if phoneme in NASALS:
            return 0.8  # Open for nasals
        return 0.0  # Closed otherwise

    def is_fricative(self, phoneme: str) -> bool:
        """Check if current phoneme needs turbulence."""
        return phoneme in FRICATIVE_PHONES

    def is_voiced(self, phoneme: str) -> bool:
        """Check if phoneme uses glottal voicing."""
        return phoneme in VOICED_PHONES

    def is_stop(self, phoneme: str) -> bool:
        """Check if phoneme is a stop consonant."""
        return phoneme in STOP_PHONES
