"""
AXIMA VOICE — Beast Mode Synthesizer
Built by: Ghias + Kiro | 2026

Wires together: Glottal Source + Vocal Tract + Articulators + Linguist
The complete physical voice simulation.
"""

import math
import wave
import struct
from typing import List, Dict

from voice_tract import VocalTract
from voice_articulator import Articulator, NASALS, FRICATIVE_PHONES, VOICED_PHONES, STOP_PHONES
from voice_source import GlottalSource
from voice_linguist import Linguist


class BeastSynth:
    """Physical model voice synthesizer.
    
    Simulates actual sound wave propagation through the vocal tract.
    No stored audio. No neural network. Pure physics at sample rate.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.tract = VocalTract(sample_rate)
        self.articulator = Articulator(sample_rate)
        self.source = GlottalSource(sample_rate)
        self.linguist = Linguist()

        # Voice parameters
        self.f0 = 130.0   # Base pitch
        self.rd = 1.0     # Voice quality
        self.rate = 1.0   # Speaking rate

        # Phoneme durations (ms)
        self.durations = {
            'IY': 90, 'IH': 70, 'EH': 80, 'AE': 90, 'AA': 100,
            'AH': 70, 'AO': 90, 'UH': 70, 'UW': 90, 'ER': 90,
            'AX': 50, 'EY': 100, 'AY': 110, 'OW': 100, 'AW': 110, 'OY': 110,
            'M': 70, 'N': 60, 'NG': 60,
            'L': 60, 'R': 60, 'W': 50, 'Y': 50,
            'S': 90, 'Z': 70, 'SH': 90, 'ZH': 70, 'F': 80,
            'V': 60, 'TH': 70, 'DH': 50, 'HH': 60,
            'P': 80, 'B': 60, 'T': 70, 'D': 50, 'K': 80, 'G': 60,
            'CH': 100, 'JH': 80, 'SIL': 100,
        }

    def speak(self, text: str) -> List[float]:
        """Synthesize text to audio using physical model."""
        # Text → phonemes
        words = self.linguist.process(text)
        if not words:
            return []

        # Build phoneme sequence with timing
        sequence = self._build_sequence(words)

        # Synthesize sample-by-sample through physics
        audio = self._synthesize_physical(sequence)

        # Normalize
        if audio:
            peak = max(abs(s) for s in audio) or 1.0
            audio = [s * 0.8 / peak for s in audio]

        return audio

    def _build_sequence(self, words: List[Dict]) -> List[Dict]:
        """Build phoneme sequence with timing."""
        sequence = []
        for word_info in words:
            for phone, stress in word_info['phonemes']:
                dur_ms = self.durations.get(phone, 70)
                if stress == 1:
                    dur_ms *= 1.3
                dur_ms /= self.rate

                f0 = self.f0
                if stress == 1:
                    f0 *= 1.2

                sequence.append({
                    'phone': phone,
                    'duration_ms': dur_ms,
                    'f0': f0,
                })

            # Inter-word silence
            if word_info.get('phrase_break'):
                sequence.append({'phone': 'SIL', 'duration_ms': 150, 'f0': 0})
            else:
                sequence.append({'phone': 'SIL', 'duration_ms': 20, 'f0': 0})

        return sequence

    def _synthesize_physical(self, sequence: List[Dict]) -> List[float]:
        """Sample-by-sample physical synthesis."""
        audio = []
        turb_seed = 0

        for seg in sequence:
            phone = seg['phone']
            dur_samples = int(seg['duration_ms'] * self.sr / 1000)
            f0 = seg['f0']

            if dur_samples <= 0:
                continue

            # Set articulator target
            self.articulator.set_target(phone)

            # Configure tract
            is_voiced = phone in VOICED_PHONES
            is_fricative = phone in FRICATIVE_PHONES
            is_nasal = phone in NASALS
            is_stop = phone in STOP_PHONES

            # Set velum
            self.tract.velum_open = 0.8 if is_nasal else 0.0

            for i in range(dur_samples):
                # 1. Update articulator physics (smooth movement)
                current_areas = self.articulator.update()

                # 2. Update tract shape
                self.tract.set_area_function(current_areas)

                # 3. Generate source signal
                if is_stop and i < dur_samples * 0.4:
                    # Stop closure: no source
                    glottal = 0.0
                elif is_voiced:
                    # Voiced: glottal pulses
                    glottal = self.source.generate(1, f0, self.rd, jitter=0.005)[0]
                else:
                    glottal = 0.0

                # 4. Generate turbulence noise for fricatives
                noise = 0.0
                noise_pos = -1
                if is_fricative or (is_stop and i > dur_samples * 0.4):
                    # Find constriction point
                    constr_idx, constr_area = self.tract.get_constriction_point()
                    # Noise amount proportional to 1/area (more constriction = more noise)
                    noise_strength = min(1.0, 0.3 / max(constr_area, 0.01))
                    # Generate noise
                    turb_seed += 1
                    noise = self._turbulence(turb_seed) * noise_strength * 0.3
                    noise_pos = constr_idx

                # 5. Propagate through vocal tract (THE PHYSICS)
                sample = self.tract.process_sample(glottal, noise, noise_pos)

                audio.append(sample)

        return audio

    def _turbulence(self, seed: int) -> float:
        """Generate turbulence noise (pseudo-random, no import needed)."""
        x = ((seed * 0.6180339887) % 1.0)
        return 2.0 * x - 1.0

    def save_wav(self, filename: str, audio: List[float]):
        """Save audio to WAV file."""
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            data = b''
            for sample in audio:
                s = max(-1.0, min(1.0, sample))
                data += struct.pack('<h', int(s * 32767))
            wf.writeframes(data)
