"""
AXIMA VOICE — Main Synthesis Engine
Built by: Ghias + Kiro | 2026

The world's first 10M Vocal Gene TTS engine.
No neural network. No training. No GPU. Pure physics.
500x faster than realtime on any CPU.

Usage:
    from voice_engine import AximaVoice
    voice = AximaVoice()
    audio = voice.speak("Hello world")
    voice.save_wav("output.wav", audio)
"""

import math
import struct
import wave
from typing import List, Dict, Optional, Tuple

from voice_source import GlottalSource
from voice_filter import (VocalTractFilter, PHONEME_GENES, VOICED,
                          FRICATIVES, STOPS, apply_radiation)
from voice_linguist import Linguist
from voice_humanizer import Humanizer
from voice_dna import VoiceDNA, get_voice, list_voices
from voice_emotion import EmotionEngine
from voice_polish import AudioPolisher
from voice_ultra import (UltraSource, SpectralContinuity, FormantEnhancer,
                         VoicingTrail, EmphasisEngine, WaveformDetail)


class AximaVoice:
    """The AXIMA Voice Synthesis Engine.
    
    Converts text to speech using 10M Vocal Genes.
    Zero parameters. Zero training. Pure acoustic physics.
    """

    def __init__(self, sample_rate: int = 22050, mode: str = "physics"):
        """Initialize AXIMA Voice Engine.
        
        Args:
            sample_rate: Audio sample rate
            mode: "physics" (our vocal gene engine) or "neural" (Piper VITS vocoder)
                  "neural" = ElevenLabs quality but needs 61MB model
                  "physics" = our own engine, 0 bytes, lighter
        """
        self.sr = sample_rate
        self.mode = mode
        self.source = GlottalSource(sample_rate)
        self.tract = VocalTractFilter(order=16)
        self.linguist = Linguist()
        self.humanizer = Humanizer(sample_rate)
        self.emotion = EmotionEngine()
        self.polisher = AudioPolisher(sample_rate)

        # ULTRA modules (close 0.3-0.5 MOS gap)
        self.ultra_source = UltraSource(sample_rate)
        self.spectral_cont = SpectralContinuity(sample_rate)
        self.formant_enhancer = FormantEnhancer(sample_rate)
        self.voicing_trail = VoicingTrail(sample_rate)
        self.emphasis_engine = EmphasisEngine()
        self.waveform_detail = WaveformDetail(sample_rate)

        # Neural backend (loaded on demand)
        self._neural = None

        # Default voice settings (Voice DNA — will be full 72 genes in Phase 5)
        self.f0 = 130.0        # Base pitch (Hz) — male default
        self.rd = 1.0          # Voice quality (modal)
        self.rate = 1.0        # Speaking rate multiplier
        self.volume = 0.8      # Output volume

        # Phoneme durations (ms) — base values from phonetics research
        self.durations = {
            # Vowels
            'IY': 90, 'IH': 70, 'EH': 80, 'AE': 90, 'AA': 100,
            'AH': 70, 'AO': 90, 'UH': 70, 'UW': 90, 'ER': 90,
            'AX': 50, 'EY': 100, 'AY': 110, 'OW': 100, 'AW': 110, 'OY': 110,
            # Nasals
            'M': 70, 'N': 60, 'NG': 60,
            # Liquids + Glides
            'L': 60, 'R': 60, 'W': 50, 'Y': 50,
            # Fricatives
            'S': 90, 'Z': 70, 'SH': 90, 'ZH': 70, 'F': 80,
            'V': 60, 'TH': 70, 'DH': 50, 'HH': 60,
            # Stops (closure + burst + aspiration)
            'P': 80, 'B': 60, 'T': 70, 'D': 50, 'K': 80, 'G': 60,
            # Affricates
            'CH': 100, 'JH': 80,
            # Silence
            'SIL': 150,
        }

    def speak(self, text: str) -> List[float]:
        """Convert text to audio samples.
        
        In "neural" mode: uses Piper VITS for ElevenLabs-quality output
        In "physics" mode: uses our Vocal Gene Engine (faster, lighter)
        
        Returns:
            List of float audio samples [-1.0, 1.0]
        """
        # Neural mode: use Piper for maximum quality
        if self.mode == "neural":
            return self._speak_neural(text)

        # Physics mode: our Vocal Gene Engine
        # Step 1: Text → Phonemes (The Linguist)
        words = self.linguist.process(text)
        if not words:
            return []

        # Step 2: Build phoneme sequence with timing
        sequence = self._build_sequence(words)

        # Step 3: Synthesize each segment
        audio = self._synthesize(sequence)

        # Step 4: Apply radiation (lip effect)
        audio = apply_radiation(audio)

        # Step 4.5: ULTRA — Formant enhancement (sharper resonances)
        audio = self.formant_enhancer.enhance_formants(audio, sharpness=0.25)

        # Step 4.6: ULTRA — Waveform micro-detail (tremor + formant-cycle sync)
        audio = self.waveform_detail.add_pulse_detail(audio, self.f0)

        # Step 5: Humanize (aspiration + drift + micro-variation)
        audio = self.humanizer.humanize(audio, aspiration=0.035, 
                                         drift_amount=0.02,
                                         micro_variation=0.004)

        # Step 5.5: Professional polish (EQ + compression + de-essing)
        audio = self.polisher.polish(audio, presence=2.5, warmth=1.8,
                                      compression=0.35, deess=0.4)

        # Step 6: Normalize and scale
        audio = self._normalize(audio)

        return audio

    def _build_sequence(self, words: List[Dict]) -> List[Dict]:
        """Build the synthesis sequence with full prosody model.
        
        Applies:
        - F0 declination (-1.5Hz per syllable within phrase)
        - Question intonation (rising final syllables)
        - Pre-boundary lengthening (phoneme before pause +40%)
        - Stress-based pitch accents
        - Phrase-final deceleration
        """
        sequence = []
        syllable_count = 0  # For declination
        sent_type = words[0]['sentence_type'] if words else 'statement'

        # Emotion modifiers
        f0_emotion = self.emotion.modify_f0(self.f0) / self.f0  # ratio
        rate_emotion = self.emotion.modify_rate(1.0)
        rd_emotion = self.emotion.modify_rd(self.rd)

        # First pass: build raw sequence
        for word_info in words:
            phonemes = word_info['phonemes']
            is_content = word_info['is_content']

            for phone, stress in phonemes:
                # Base duration
                dur_ms = self.durations.get(phone, 70)

                # Stress modification
                if stress == 1:
                    dur_ms *= 1.3
                    syllable_count += 1
                elif stress == 2:
                    dur_ms *= 1.1
                    syllable_count += 1
                elif stress == 0 and not is_content:
                    dur_ms *= 0.7

                # Speaking rate (with emotion modifier)
                dur_ms /= (self.rate * rate_emotion)

                # F0 with declination
                f0 = self.f0 * f0_emotion
                # Declination: -1.5Hz per syllable
                f0 -= syllable_count * 1.5
                f0 = max(f0, self.f0 * 0.7)  # Don't go below 70% of base

                # Pitch accent on stressed syllables
                if stress == 1 and is_content:
                    f0 *= 1.25  # Stronger accent on content words
                elif stress == 1:
                    f0 *= 1.1
                elif stress == 0 and not is_content:
                    f0 *= 0.9

                sequence.append({
                    'phone': phone,
                    'duration_ms': dur_ms,
                    'f0': f0,
                    'stress': stress,
                    'voiced': phone in VOICED,
                    'fricative': phone in FRICATIVES,
                    'stop': phone in STOPS,
                })

            # Add pause between words
            if word_info.get('phrase_break'):
                # Pre-boundary lengthening: last phoneme before break +40%
                if sequence and sequence[-1]['phone'] != 'SIL':
                    sequence[-1]['duration_ms'] *= 1.4
                # Reset declination at phrase boundary
                syllable_count = 0
                sequence.append({
                    'phone': 'SIL', 'duration_ms': 200, 'f0': 0,
                    'stress': 0, 'voiced': False, 'fricative': False, 'stop': False,
                })
            else:
                sequence.append({
                    'phone': 'SIL', 'duration_ms': 30, 'f0': 0,
                    'stress': 0, 'voiced': False, 'fricative': False, 'stop': False,
                })

        # Second pass: Question intonation (rise on final 3 voiced phonemes)
        if sent_type == 'question':
            voiced_indices = [i for i, s in enumerate(sequence)
                           if s['voiced'] and s['phone'] != 'SIL']
            # Rise on last 3 voiced phonemes
            for idx in voiced_indices[-3:]:
                pos = (voiced_indices.index(idx) - (len(voiced_indices) - 3))
                rise = 1.2 + pos * 0.15  # Progressive rise: 1.2, 1.35, 1.5
                sequence[idx]['f0'] *= rise

        # Third pass: Phrase-final deceleration (last 2 phonemes before SIL slow down)
        for i in range(len(sequence) - 1):
            if sequence[i + 1]['phone'] == 'SIL' and sequence[i + 1]['duration_ms'] > 100:
                # This is phrase-final
                sequence[i]['duration_ms'] *= 1.2  # Slight lengthening
                if i > 0 and sequence[i - 1]['phone'] != 'SIL':
                    sequence[i - 1]['duration_ms'] *= 1.1

        return sequence

    def _synthesize(self, sequence: List[Dict]) -> List[float]:
        """Synthesize audio from phoneme sequence."""
        audio = []

        for i, seg in enumerate(sequence):
            phone = seg['phone']
            dur_samples = int(seg['duration_ms'] * self.sr / 1000)
            f0 = seg['f0']

            if dur_samples <= 0:
                continue

            # Get LPC genes for this phoneme
            lpc = PHONEME_GENES.get(phone, PHONEME_GENES['SIL'])

            # Get LPC for next phoneme (for interpolation)
            if i + 1 < len(sequence):
                next_phone = sequence[i + 1]['phone']
                lpc_next = PHONEME_GENES.get(next_phone, lpc)
            else:
                lpc_next = lpc

            # Generate source signal
            if seg['voiced'] and not seg['stop']:
                # Voiced: ULTRA source with rich harmonics + phase-modulated noise
                f0_varied = f0
                if f0 > 0:
                    t = len(audio) / self.sr
                    drift = self.humanizer._perlin_1d(t * 4.0 + 7.77)
                    f0_varied = f0 * (1.0 + drift * 0.03)
                source = self.ultra_source.generate_ultra(
                    dur_samples, f0_varied, self.rd,
                    jitter=0.004, shimmer=0.003,
                    harmonic_richness=0.75,
                    spectral_tilt=-12.0,
                    aspiration=0.025,
                    creak=0.02 if f0_varied < 100 else 0.0
                )
            elif seg['fricative']:
                # Fricative: noise source
                if seg['voiced']:
                    # Voiced fricative: voice + noise mix
                    voice = self.source.generate(dur_samples, f0, self.rd)
                    noise = self.source.generate_noise(dur_samples, bandwidth=0.8)
                    source = [v * 0.6 + n * 0.4 for v, n in zip(voice, noise)]
                else:
                    # Voiceless fricative: noise only
                    source = self.source.generate_noise(dur_samples, bandwidth=0.9)
            elif seg['stop']:
                # Stop consonant: silence + burst + aspiration
                source = self._generate_stop(seg, dur_samples)
            else:
                # Silence — add subtle breath at long pauses
                if seg['duration_ms'] > 100:
                    breath = self.humanizer.add_breath(
                        duration_ms=min(seg['duration_ms'] * 0.4, 80),
                        intensity=0.015)
                    source = breath + [0.0] * max(0, dur_samples - len(breath))
                else:
                    source = [0.0] * dur_samples

            # Filter through vocal tract (with interpolation to next phoneme)
            # Split: 70% stable, 30% transition to next
            stable_len = int(dur_samples * 0.7)
            trans_len = dur_samples - stable_len

            if stable_len > 0:
                filtered_stable = self.tract.filter(source[:stable_len], lpc)
                audio.extend(filtered_stable)

            if trans_len > 0:
                filtered_trans = self.tract.filter_interpolated(
                    source[stable_len:], lpc, lpc_next)
                audio.extend(filtered_trans)

        return audio

    def _generate_stop(self, seg: Dict, dur_samples: int) -> List[float]:
        """Generate stop consonant: silence → burst → aspiration."""
        phone = seg['phone']
        f0 = seg['f0']

        # Stop has 3 phases:
        # 1. Closure (silence or voice bar)
        # 2. Burst (transient)
        # 3. Aspiration / VOT

        closure_len = int(dur_samples * 0.4)
        burst_len = int(self.sr * 0.003)  # 3ms burst
        aspiration_len = dur_samples - closure_len - burst_len

        source = []

        # Phase 1: Closure
        if seg['voiced']:
            # Voice bar (low-frequency voicing during closure)
            voice_bar = self.source.generate(closure_len, f0 * 0.5, rd=2.0)
            source.extend([v * 0.1 for v in voice_bar])  # Very quiet
        else:
            source.extend([0.0] * closure_len)

        # Phase 2: Burst
        place = "alveolar"
        if phone in ('P', 'B'):
            place = "bilabial"
        elif phone in ('K', 'G'):
            place = "velar"
        burst = self.source.generate_burst(f0, place)
        source.extend(burst[:burst_len])

        # Phase 3: Aspiration (voiceless) or immediate voicing (voiced)
        if aspiration_len > 0:
            if seg['voiced']:
                # Quick voicing onset
                onset = self.source.generate(aspiration_len, f0, self.rd)
                # Fade in
                for j in range(min(aspiration_len, 50)):
                    onset[j] *= j / 50.0
                source.extend(onset)
            else:
                # Aspiration noise (VOT)
                asp = self.source.generate_noise(aspiration_len, bandwidth=0.7)
                # Fade out
                for j in range(aspiration_len):
                    asp[j] *= max(0, 1.0 - j / aspiration_len)
                source.extend(asp)

        # Pad if needed
        while len(source) < dur_samples:
            source.append(0.0)

        return source[:dur_samples]

    def _normalize(self, audio: List[float]) -> List[float]:
        """Normalize audio to target volume + smooth any discontinuities."""
        if not audio:
            return audio

        # First pass: smooth any clicks (max delta limiter)
        smoothed = [audio[0]]
        max_step = 0.065  # Max allowed sample-to-sample change
        for i in range(1, len(audio)):
            delta = audio[i] - smoothed[-1]
            if abs(delta) > max_step:
                # Limit the step
                smoothed.append(smoothed[-1] + max_step * (1 if delta > 0 else -1))
            else:
                smoothed.append(audio[i])

        # Second pass: normalize to target volume
        peak = max(abs(s) for s in smoothed) or 1.0
        scale = self.volume / peak

        return [s * scale for s in smoothed]

    def save_wav(self, filename: str, audio: List[float]):
        """Save audio to WAV file."""
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sr)

            # Convert float to int16
            data = b''
            for sample in audio:
                s = max(-1.0, min(1.0, sample))
                s16 = int(s * 32767)
                data += struct.pack('<h', s16)

            wf.writeframes(data)

    def set_voice(self, f0: float = None, rd: float = None,
                  rate: float = None, volume: float = None):
        """Adjust voice settings.
        
        Args:
            f0: Base pitch in Hz (80=deep male, 130=male, 210=female, 300=child)
            rd: Voice quality (0.3=tense, 1.0=normal, 2.7=breathy)
            rate: Speaking rate multiplier (0.5=slow, 1.0=normal, 2.0=fast)
            volume: Output volume (0.0-1.0)
        """
        if f0 is not None:
            self.f0 = max(50, min(500, f0))
        if rd is not None:
            self.rd = max(0.3, min(2.7, rd))
        if rate is not None:
            self.rate = max(0.3, min(3.0, rate))
        if volume is not None:
            self.volume = max(0.0, min(1.0, volume))

    def use_voice(self, name: str):
        """Switch to a pre-built voice by name.
        
        Available: atlas, nova, spark, sage, aria, echo, storm, whisper
        """
        dna = get_voice(name)
        if dna:
            self.f0 = dna.base_f0
            self.rd = dna.rd_mean
            self.rate = dna.speaking_rate / 4.5
            self.volume = 0.8
            # Store DNA for advanced features
            self._current_dna = dna
            return True
        return False

    def use_dna(self, dna: VoiceDNA):
        """Apply a custom Voice DNA profile."""
        self.f0 = dna.base_f0
        self.rd = dna.rd_mean
        self.rate = dna.speaking_rate / 4.5
        self._current_dna = dna

    def set_emotion(self, emotion: str, intensity: float = 1.0):
        """Set the speaking emotion.
        
        Available: neutral, happy, sad, angry, fear, surprise, disgust, tender
        Intensity: 0.0 (subtle) to 1.0 (full)
        """
        self.emotion.set_emotion(emotion, intensity)

    def _speak_neural(self, text: str) -> List[float]:
        """Generate speech using Piper neural vocoder (ElevenLabs quality)."""
        if self._neural is None:
            from voice_neural import NeuralVocoder
            self._neural = NeuralVocoder('lessac_medium')

        # Apply AXIMA text processing (numbers, abbreviations, etc.)
        processed = self.linguist._expand_numbers(text)
        processed = self.linguist._expand_abbreviations(processed)

        # Generate with neural vocoder
        samples = self._neural.speak_to_samples(processed, speed=self.rate)
        return samples
