"""
AXIMA VOICE — Music & Instrument Synthesis Engine
Built by: Ghias + Kiro | 2026

Physical modeling synthesis of musical instruments.
No samples. No neural networks. Pure physics of vibrating strings,
air columns, membranes, and resonant bodies.

Instruments:
- Piano (struck string + soundboard resonance)
- Guitar (plucked string + body resonance)
- Violin/Strings (bowed string + body)
- Drums (membrane + shell resonance)
- Flute/Wind (air column + turbulence)
- Bass (low-frequency string)
- Synth pads (additive + FM synthesis)
- Bells/Chimes (inharmonic partials)
- Singing voice (melodic mode of voice engine)

All from first principles. Runs on phone CPU.
"""

import math
from typing import List, Tuple, Dict, Optional


class Note:
    """Musical note representation."""
    # MIDI note to frequency (A4 = 440Hz)
    @staticmethod
    def freq(midi_note: int) -> float:
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    @staticmethod
    def name_to_midi(name: str) -> int:
        """Convert note name to MIDI number. e.g., 'C4'=60"""
        notes = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
        n = name[0].upper()
        sharp = 1 if '#' in name else (-1 if 'b' in name else 0)
        octave = int(name[-1])
        return (octave + 1) * 12 + notes[n] + sharp



class KarplusStrong:
    """Karplus-Strong string synthesis (plucked/struck strings).
    
    The most efficient physical model of a vibrating string.
    A short burst of noise → delay line → lowpass filter → feedback.
    The delay length sets the pitch. The filter models string damping.
    
    Used for: Guitar, Piano, Bass, Harp, Banjo
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def pluck(self, freq: float, duration_s: float,
              brightness: float = 0.5,
              decay: float = 0.996,
              pluck_position: float = 0.5) -> List[float]:
        """Generate plucked string sound.
        
        Args:
            freq: Fundamental frequency (Hz)
            duration_s: Duration in seconds
            brightness: 0=mellow, 1=bright (controls filter cutoff)
            decay: Feedback gain (0.99=short, 0.999=long sustain)
            pluck_position: Where on string it's plucked (affects harmonics)
        """
        n_samples = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        # Initialize delay line with shaped noise (the "pluck")
        delay = [0.0] * period
        for i in range(period):
            # Shaped noise: pluck position affects harmonic content
            noise = self._noise(i)
            # Remove harmonics at pluck position (comb filter effect)
            pos = int(pluck_position * period)
            if pos > 0 and i % pos == 0:
                noise *= 0.3  # Notch at pluck harmonics
            delay[i] = noise

        # Synthesis loop
        output = []
        read_ptr = 0
        filter_state = 0.0

        for i in range(n_samples):
            # Read from delay line
            sample = delay[read_ptr]

            # Lowpass filter (models string damping)
            # Brightness controls filter: 0=very filtered, 1=minimal filtering
            alpha = 0.3 + brightness * 0.65
            filtered = alpha * sample + (1.0 - alpha) * filter_state
            filter_state = filtered

            # Write back with decay (feedback)
            delay[read_ptr] = filtered * decay

            output.append(sample)
            read_ptr = (read_ptr + 1) % period

        return output

    def strike(self, freq: float, duration_s: float,
               hardness: float = 0.7,
               decay: float = 0.998) -> List[float]:
        """Generate struck string sound (piano/hammered dulcimer).
        
        Harder strike = brighter attack, more high harmonics initially.
        """
        n_samples = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        # Initialize: short impulse (hammer strike)
        delay = [0.0] * period
        strike_len = max(1, int(period * (0.1 + (1.0 - hardness) * 0.3)))
        for i in range(strike_len):
            # Hammer shape: raised cosine
            t = i / strike_len
            delay[i] = math.sin(t * math.pi) * (0.5 + hardness * 0.5)

        output = []
        read_ptr = 0
        z1 = 0.0

        for i in range(n_samples):
            sample = delay[read_ptr]
            # Two-point average lowpass (gentler for piano)
            next_ptr = (read_ptr + 1) % period
            filtered = 0.5 * (sample + delay[next_ptr])
            # Decay
            delay[read_ptr] = filtered * decay
            output.append(sample)
            read_ptr = (read_ptr + 1) % period

        return output

    def _noise(self, n: int) -> float:
        return ((n * 0.6180339887) % 1.0) * 2.0 - 1.0



class BowedString:
    """Physical model of bowed string (violin, cello, viola).
    
    Uses waveguide model with nonlinear bow-string interaction.
    The bow applies friction that causes stick-slip vibration.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def bow(self, freq: float, duration_s: float,
            bow_pressure: float = 0.5,
            bow_speed: float = 0.3,
            vibrato_rate: float = 5.5,
            vibrato_depth: float = 0.005) -> List[float]:
        """Generate bowed string sound.
        
        Args:
            freq: Pitch
            duration_s: Duration
            bow_pressure: Force on string (0.1=light, 1.0=heavy)
            bow_speed: Bow velocity (affects brightness)
            vibrato_rate: Vibrato frequency (Hz)
            vibrato_depth: Vibrato depth (fraction of freq)
        """
        n_samples = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        # Delay lines (nut side and bridge side)
        delay_nut = [0.0] * (period // 2 + 1)
        delay_bridge = [0.0] * (period // 2 + 1)
        nut_ptr = 0
        bridge_ptr = 0
        nut_len = len(delay_nut)
        bridge_len = len(delay_bridge)

        output = []
        v_bow = bow_speed
        z1 = 0.0

        for i in range(n_samples):
            t = i / self.sr

            # Vibrato
            vib = 1.0 + vibrato_depth * math.sin(2 * math.pi * vibrato_rate * t)

            # Read from both delay lines
            nut_out = delay_nut[nut_ptr]
            bridge_out = delay_bridge[bridge_ptr]

            # Bow-string interaction (simplified friction model)
            v_string = nut_out + bridge_out
            v_diff = v_bow - v_string

            # Nonlinear friction curve (hyperbolic tangent approximation)
            friction = bow_pressure * math.tanh(4.0 * v_diff)

            # Inject friction force into delay lines
            delay_nut[nut_ptr] = -bridge_out * 0.98 + friction * 0.1
            delay_bridge[bridge_ptr] = -nut_out * 0.98 + friction * 0.1

            # Low-pass at bridge (body coupling)
            sample = bridge_out
            filtered = 0.7 * sample + 0.3 * z1
            z1 = filtered

            output.append(filtered)

            nut_ptr = (nut_ptr + 1) % nut_len
            bridge_ptr = (bridge_ptr + 1) % bridge_len

        # Apply envelope
        output = self._apply_envelope(output, attack_ms=80, release_ms=100)
        return output

    def _apply_envelope(self, audio: List[float],
                        attack_ms: float = 50,
                        release_ms: float = 100) -> List[float]:
        n = len(audio)
        attack_samples = int(attack_ms * self.sr / 1000)
        release_samples = int(release_ms * self.sr / 1000)
        result = list(audio)
        for i in range(min(attack_samples, n)):
            result[i] *= i / attack_samples
        for i in range(min(release_samples, n)):
            idx = n - 1 - i
            result[idx] *= i / release_samples
        return result



class WindInstrument:
    """Physical model of wind instruments (flute, clarinet, trumpet).
    
    Models air column resonance + turbulence at the mouthpiece.
    The tube length determines pitch. End conditions determine timbre.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def flute(self, freq: float, duration_s: float,
              breath_noise: float = 0.08,
              vibrato_rate: float = 5.0,
              vibrato_depth: float = 0.003) -> List[float]:
        """Generate flute-like sound (open tube + jet noise)."""
        n_samples = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        # Delay line (air column)
        delay = [0.0] * period
        ptr = 0
        output = []
        z1 = 0.0

        for i in range(n_samples):
            t = i / self.sr
            # Vibrato
            vib_mod = 1.0 + vibrato_depth * math.sin(2 * math.pi * vibrato_rate * t)

            # Read from delay
            sample = delay[ptr]

            # Jet excitation (noise + feedback)
            jet_noise = self._noise(i) * breath_noise
            excitation = math.tanh(3.0 * (sample * 0.4 + jet_noise))

            # Lowpass (air absorption)
            filtered = 0.6 * excitation + 0.4 * z1
            z1 = filtered

            # Write back (inverted for open tube)
            delay[ptr] = -filtered * 0.95

            output.append(sample * 0.8)
            ptr = (ptr + 1) % period

        output = self._envelope(output, 40, 60)
        return output

    def clarinet(self, freq: float, duration_s: float,
                 reed_stiffness: float = 0.5) -> List[float]:
        """Generate clarinet-like sound (closed tube + reed).
        
        Closed tube = only odd harmonics (characteristic hollow sound).
        """
        n_samples = int(duration_s * self.sr)
        # Closed tube: effective length is 2x for same pitch
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        delay = [0.0] * period
        ptr = 0
        output = []
        z1 = 0.0

        for i in range(n_samples):
            sample = delay[ptr]

            # Reed model (nonlinear pressure-flow)
            pressure = sample * 0.5
            # Reed displacement (cubic nonlinearity)
            reed = pressure - reed_stiffness * pressure ** 3
            reed = max(-1.0, min(1.0, reed))

            # Embouchure noise
            noise = self._noise(i + 33333) * 0.02

            excitation = reed + noise

            # Reflection at closed end (no inversion = odd harmonics only)
            filtered = 0.55 * excitation + 0.45 * z1
            z1 = filtered
            delay[ptr] = filtered * 0.97  # No inversion for closed tube

            output.append(sample * 0.7)
            ptr = (ptr + 1) % period

        output = self._envelope(output, 30, 80)
        return output

    def trumpet(self, freq: float, duration_s: float,
                lip_tension: float = 0.6) -> List[float]:
        """Generate trumpet-like brass sound (lip reed + flared bell)."""
        n_samples = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2:
            return [0.0] * n_samples

        delay = [0.0] * period
        ptr = 0
        output = []
        z1 = z2 = 0.0

        for i in range(n_samples):
            sample = delay[ptr]

            # Lip reed (oscillating valve)
            lip = math.tanh(lip_tension * 5.0 * sample) * 0.8

            # Bell radiation (high-pass boost = bright)
            bell = lip - z1 * 0.3
            z1 = lip

            # Feedback into tube
            delay[ptr] = -bell * 0.92

            # Output with bell radiation effect
            out = bell - z2
            z2 = bell
            output.append(out * 0.6)
            ptr = (ptr + 1) % period

        output = self._envelope(output, 20, 50)
        return output

    def _noise(self, n: int) -> float:
        return ((n * 0.6180339887) % 1.0) * 2.0 - 1.0

    def _envelope(self, audio, attack_ms, release_ms):
        n = len(audio)
        att = int(attack_ms * self.sr / 1000)
        rel = int(release_ms * self.sr / 1000)
        result = list(audio)
        for i in range(min(att, n)):
            result[i] *= i / att
        for i in range(min(rel, n)):
            result[n-1-i] *= i / rel
        return result



class Drums:
    """Physical model percussion synthesis.
    
    Drums are membranes (circular) vibrating with inharmonic partials.
    Different drums = different membrane size, tension, shell resonance.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def kick(self, duration_s: float = 0.5) -> List[float]:
        """Bass drum: low pitch sweep + body resonance."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            # Pitch sweep: starts high (~150Hz) drops to ~50Hz
            freq = 50 + 100 * math.exp(-t * 30)
            # Sine with exponential decay
            env = math.exp(-t * 8)
            sample = math.sin(2 * math.pi * freq * t) * env
            # Add click transient
            if t < 0.005:
                sample += (1.0 - t/0.005) * 0.8
            output.append(sample * 0.9)
        return output

    def snare(self, duration_s: float = 0.3) -> List[float]:
        """Snare drum: membrane + snare wire buzz."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 12)
            # Membrane (200Hz body)
            body = math.sin(2 * math.pi * 200 * t) * env * 0.5
            # Snare wires (high-freq noise)
            noise = self._noise(i) * env * 0.7
            # Transient click
            click = 0.0
            if t < 0.003:
                click = (1.0 - t/0.003) * 0.9
            output.append(body + noise + click)
        return output

    def hihat(self, duration_s: float = 0.1, open_hat: bool = False) -> List[float]:
        """Hi-hat: metallic noise (short=closed, long=open)."""
        dur = duration_s if not open_hat else duration_s * 4
        n = int(dur * self.sr)
        decay_rate = 30 if not open_hat else 5
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * decay_rate)
            # Metallic: sum of inharmonic partials
            metal = 0.0
            freqs = [800, 1600, 3200, 5500, 8000, 10000]
            for f in freqs:
                metal += math.sin(2 * math.pi * f * t + f * 0.01) * 0.15
            noise = self._noise(i) * 0.5
            output.append((metal + noise) * env)
        return output

    def tom(self, pitch: float = 150, duration_s: float = 0.4) -> List[float]:
        """Tom drum: tuned membrane."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            freq = pitch + 30 * math.exp(-t * 20)
            env = math.exp(-t * 10)
            sample = math.sin(2 * math.pi * freq * t) * env
            if t < 0.003:
                sample += (1.0 - t/0.003) * 0.6
            output.append(sample * 0.8)
        return output

    def clap(self, duration_s: float = 0.15) -> List[float]:
        """Hand clap: multiple short noise bursts."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 20)
            # Multiple micro-bursts (fingers hitting)
            burst = 0.0
            for b in range(4):
                bt = t - b * 0.004
                if 0 <= bt < 0.003:
                    burst += self._noise(i + b * 1000) * (1.0 - bt/0.003)
            noise = self._noise(i) * env * 0.3
            output.append((burst * 0.7 + noise) * 0.8)
        return output

    def cymbal(self, duration_s: float = 2.0) -> List[float]:
        """Crash/ride cymbal: complex inharmonic metallic."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 2)
            metal = 0.0
            # Many inharmonic partials
            for k, f in enumerate([500, 1234, 2567, 3891, 5123, 6789, 8456, 9999]):
                amp = 1.0 / (k + 1)
                metal += math.sin(2*math.pi*f*t + k*1.7) * amp
            noise = self._noise(i) * 0.3
            output.append((metal * 0.3 + noise) * env)
        return output

    def _noise(self, n: int) -> float:
        return ((n * 0.6180339887) % 1.0) * 2.0 - 1.0



class Synthesizer:
    """Electronic synthesizer (additive, FM, subtractive).
    
    For pads, leads, bass, and atmospheric sounds.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def pad(self, freq: float, duration_s: float,
            warmth: float = 0.7, detune: float = 0.003) -> List[float]:
        """Warm synthesizer pad (multiple detuned oscillators)."""
        n = int(duration_s * self.sr)
        output = []
        # 4 slightly detuned oscillators for width
        freqs = [freq * (1 - detune), freq, freq * (1 + detune), freq * 2 * (1 + detune*0.5)]
        for i in range(n):
            t = i / self.sr
            sample = 0.0
            for k, f in enumerate(freqs):
                # Saw wave (rich harmonics)
                phase = (f * t) % 1.0
                saw = 2.0 * phase - 1.0
                sample += saw * (0.3 / (k + 1))
            # Low-pass filter for warmth
            cutoff_mod = 0.3 + warmth * 0.5
            # Simple one-pole LP
            if i > 0:
                sample = sample * cutoff_mod + output[-1] * (1 - cutoff_mod)
            # Envelope
            att = min(1.0, t / 0.5)  # 500ms attack
            rel_t = duration_s - t
            rel = min(1.0, rel_t / 0.3) if rel_t < 0.3 else 1.0
            output.append(sample * att * rel * 0.5)
        return output

    def lead(self, freq: float, duration_s: float,
             saw_mix: float = 0.7, pulse_width: float = 0.5) -> List[float]:
        """Synth lead (saw + pulse mix)."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            phase = (freq * t) % 1.0
            # Saw oscillator
            saw = 2.0 * phase - 1.0
            # Pulse oscillator
            pulse = 1.0 if phase < pulse_width else -1.0
            # Mix
            sample = saw * saw_mix + pulse * (1.0 - saw_mix)
            # Envelope
            att = min(1.0, t / 0.01)
            rel_t = duration_s - t
            rel = min(1.0, rel_t / 0.05) if rel_t < 0.05 else 1.0
            output.append(sample * att * rel * 0.4)
        return output

    def bass(self, freq: float, duration_s: float,
             sub: float = 0.6) -> List[float]:
        """Deep bass synth (sub-oscillator + harmonics)."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            # Sub oscillator (pure sine, one octave below)
            sub_osc = math.sin(2 * math.pi * freq * 0.5 * t) * sub
            # Main (triangle for warm bass)
            phase = (freq * t) % 1.0
            tri = 4.0 * abs(phase - 0.5) - 1.0
            sample = sub_osc + tri * (1.0 - sub) * 0.7
            # Pluck envelope
            env = math.exp(-t * 3)
            att = min(1.0, t / 0.005)
            output.append(sample * env * att * 0.7)
        return output

    def fm_bell(self, freq: float, duration_s: float,
                mod_ratio: float = 7.0, mod_index: float = 5.0) -> List[float]:
        """FM synthesis bell/chime (inharmonic, metallic)."""
        n = int(duration_s * self.sr)
        output = []
        mod_freq = freq * mod_ratio
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 3)
            # Modulator decays faster (spectrum simplifies over time)
            mod_env = math.exp(-t * 5)
            modulator = math.sin(2 * math.pi * mod_freq * t) * mod_index * mod_env
            carrier = math.sin(2 * math.pi * freq * t + modulator)
            output.append(carrier * env * 0.5)
        return output

    def noise_sweep(self, duration_s: float, 
                    start_freq: float = 100, end_freq: float = 8000) -> List[float]:
        """Filtered noise sweep (risers, impacts, transitions)."""
        n = int(duration_s * self.sr)
        output = []
        z1 = 0.0
        for i in range(n):
            t = i / n
            # Sweep cutoff frequency
            cutoff = start_freq * ((end_freq/start_freq) ** t)
            # Generate noise
            noise = ((i * 0.6180339887) % 1.0) * 2.0 - 1.0
            # One-pole filter at sweeping cutoff
            alpha = min(0.99, 2 * math.pi * cutoff / self.sr)
            z1 = z1 * (1.0 - alpha) + noise * alpha
            # Envelope
            env = min(1.0, t * 4) * min(1.0, (1.0 - t) * 10)
            output.append(z1 * env * 0.6)
        return output



class MusicEngine:
    """Main music synthesis engine — orchestrates all instruments.
    
    Can play sequences of notes, chords, drum patterns, and full arrangements.
    Generates WAV-ready audio from simple notation.
    """

    def __init__(self, sample_rate: int = 22050, bpm: float = 120.0):
        self.sr = sample_rate
        self.bpm = bpm
        self.strings = KarplusStrong(sample_rate)
        self.drums = Drums(sample_rate)
        self.synth = Synthesizer(sample_rate)
        self.bowed = BowedString(sample_rate)
        self.wind = WindInstrument(sample_rate)

    def beat_to_seconds(self, beats: float) -> float:
        return beats * 60.0 / self.bpm

    def play_chord(self, notes: List[int], duration_beats: float = 1.0,
                   instrument: str = "guitar") -> List[float]:
        """Play a chord (multiple notes simultaneously)."""
        dur = self.beat_to_seconds(duration_beats)
        chord_audio = [0.0] * int(dur * self.sr)

        for midi_note in notes:
            freq = Note.freq(midi_note)
            if instrument == "guitar":
                note_audio = self.strings.pluck(freq, dur, brightness=0.6)
            elif instrument == "piano":
                note_audio = self.strings.strike(freq, dur, hardness=0.6)
            elif instrument == "pad":
                note_audio = self.synth.pad(freq, dur)
            elif instrument == "strings":
                note_audio = self.bowed.bow(freq, dur)
            else:
                note_audio = self.strings.pluck(freq, dur)

            for i in range(min(len(chord_audio), len(note_audio))):
                chord_audio[i] += note_audio[i] * 0.5

        return chord_audio

    def play_melody(self, notes: List[Tuple[int, float]], 
                    instrument: str = "flute") -> List[float]:
        """Play a sequence of notes (midi_note, duration_beats).
        
        Args:
            notes: List of (midi_note, duration_in_beats). Use 0 for rest.
            instrument: "flute", "clarinet", "trumpet", "violin", "guitar", "piano", "lead"
        """
        audio = []
        for midi_note, beats in notes:
            dur = self.beat_to_seconds(beats)
            if midi_note <= 0:
                # Rest
                audio.extend([0.0] * int(dur * self.sr))
            else:
                freq = Note.freq(midi_note)
                if instrument == "flute":
                    note = self.wind.flute(freq, dur)
                elif instrument == "clarinet":
                    note = self.wind.clarinet(freq, dur)
                elif instrument == "trumpet":
                    note = self.wind.trumpet(freq, dur)
                elif instrument == "violin":
                    note = self.bowed.bow(freq, dur)
                elif instrument == "guitar":
                    note = self.strings.pluck(freq, dur, brightness=0.5)
                elif instrument == "piano":
                    note = self.strings.strike(freq, dur)
                elif instrument == "lead":
                    note = self.synth.lead(freq, dur)
                elif instrument == "bass":
                    note = self.synth.bass(freq, dur)
                else:
                    note = self.strings.pluck(freq, dur)
                audio.extend(note)
        return audio

    def play_drum_pattern(self, pattern: str, bars: int = 4) -> List[float]:
        """Play drum pattern from text notation.
        
        Pattern format (16th notes, | = bar line):
        K = kick, S = snare, H = hihat, O = open hat, 
        T = tom, C = crash, . = rest
        
        Example: "K.H.S.H.|K.H.S.HO|K.H.S.H.|K.H.S.HC"
        """
        beat_dur = self.beat_to_seconds(0.25)  # 16th note
        steps = pattern.replace('|', '')
        total_steps = len(steps) * bars
        audio = [0.0] * int(total_steps * beat_dur * self.sr)

        for bar in range(bars):
            for i, ch in enumerate(steps):
                pos = int((bar * len(steps) + i) * beat_dur * self.sr)
                hit = []
                if ch == 'K':
                    hit = self.drums.kick(0.3)
                elif ch == 'S':
                    hit = self.drums.snare(0.2)
                elif ch == 'H':
                    hit = self.drums.hihat(0.08)
                elif ch == 'O':
                    hit = self.drums.hihat(0.3, open_hat=True)
                elif ch == 'T':
                    hit = self.drums.tom(180, 0.3)
                elif ch == 'C':
                    hit = self.drums.cymbal(1.5)
                elif ch == 'X':
                    hit = self.drums.clap(0.12)

                for j in range(len(hit)):
                    idx = pos + j
                    if idx < len(audio):
                        audio[idx] += hit[j] * 0.7

        return audio

    def mix(self, tracks: List[Tuple[List[float], float]]) -> List[float]:
        """Mix multiple audio tracks together with volume levels.
        
        Args:
            tracks: List of (audio, volume) tuples
        """
        if not tracks:
            return []
        max_len = max(len(t[0]) for t in tracks)
        output = [0.0] * max_len
        for audio, vol in tracks:
            for i in range(min(len(audio), max_len)):
                output[i] += audio[i] * vol
        # Normalize
        peak = max(abs(s) for s in output) or 1.0
        if peak > 1.0:
            output = [s / peak * 0.9 for s in output]
        return output

    def save_wav(self, filename: str, audio: List[float]):
        """Save audio to WAV file."""
        import wave, struct
        with wave.open(filename, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            data = b''
            for s in audio:
                s = max(-1.0, min(1.0, s))
                data += struct.pack('<h', int(s * 32767))
            wf.writeframes(data)



class Orchestra:
    """Orchestral instruments: strings section, horns, woodwinds, harp."""

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.bowed = BowedString(sample_rate)
        self.wind = WindInstrument(sample_rate)

    def string_section(self, freq: float, duration_s: float,
                       size: int = 8) -> List[float]:
        """Full string section (multiple detuned bowed strings)."""
        n = int(duration_s * self.sr)
        output = [0.0] * n
        for v in range(size):
            # Each player slightly detuned + different timing
            detune = 1.0 + (v - size/2) * 0.002
            delay = int(v * 0.01 * self.sr)  # Stagger entries
            note = self.bowed.bow(freq * detune, duration_s - delay/self.sr,
                                  bow_pressure=0.4 + v*0.05,
                                  vibrato_depth=0.004 + v*0.001)
            for i in range(len(note)):
                idx = delay + i
                if idx < n:
                    output[idx] += note[i] / size
        return output

    def french_horn(self, freq: float, duration_s: float) -> List[float]:
        """French horn (mellow brass, hand-stopped bell)."""
        n = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2: return [0.0] * n
        delay = [0.0] * period
        ptr = 0; z1 = z2 = 0.0
        output = []
        for i in range(n):
            sample = delay[ptr]
            # Softer lip reed than trumpet
            lip = math.tanh(3.0 * sample) * 0.6
            # More filtering (hand in bell = mellow)
            filt = 0.6*lip + 0.3*z1 + 0.1*z2
            z2 = z1; z1 = lip
            delay[ptr] = -filt * 0.94
            output.append(filt * 0.5)
            ptr = (ptr + 1) % period
        return self._env(output, 60, 100)

    def oboe(self, freq: float, duration_s: float) -> List[float]:
        """Oboe (double reed, nasal quality)."""
        n = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2: return [0.0] * n
        delay = [0.0] * period
        ptr = 0; z1 = 0.0
        output = []
        for i in range(n):
            sample = delay[ptr]
            # Double reed: sharper nonlinearity
            reed = sample - 0.7 * sample**3 + 0.3 * sample**5
            reed = max(-1.0, min(1.0, reed))
            noise = ((i*0.618)%1.0)*2-1
            exc = reed * 0.9 + noise * 0.02
            filt = 0.5*exc + 0.5*z1; z1 = filt
            delay[ptr] = filt * 0.96
            output.append(sample * 0.6)
            ptr = (ptr + 1) % period
        return self._env(output, 25, 40)

    def harp(self, freq: float, duration_s: float = 3.0) -> List[float]:
        """Harp string (plucked, long decay, bright)."""
        ks = KarplusStrong(self.sr)
        return ks.pluck(freq, duration_s, brightness=0.8, decay=0.9995)

    def timpani(self, freq: float = 80, duration_s: float = 1.5) -> List[float]:
        """Timpani (tuned kettledrum)."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 4)
            # Inharmonic membrane modes
            modes = [1.0, 1.504, 1.742, 2.0, 2.295]
            sample = 0.0
            for k, ratio in enumerate(modes):
                sample += math.sin(2*math.pi*freq*ratio*t) * env / (k+1)
            if t < 0.005: sample += (1-t/0.005) * 0.5
            output.append(sample * 0.6)
        return output

    def _env(self, audio, att_ms, rel_ms):
        n = len(audio); r = list(audio)
        att = int(att_ms * self.sr / 1000)
        rel = int(rel_ms * self.sr / 1000)
        for i in range(min(att, n)): r[i] *= i / att
        for i in range(min(rel, n)): r[n-1-i] *= i / rel
        return r


class EthnicInstruments:
    """World music instruments: sitar, tabla, koto, didgeridoo, kalimba."""

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def sitar(self, freq: float, duration_s: float = 2.0) -> List[float]:
        """Indian sitar (sympathetic strings + buzz bridge)."""
        n = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2: return [0.0] * n
        # Main string (Karplus-Strong with nonlinear bridge)
        delay = [((i*0.618)%1.0)*2-1 for i in range(period)]
        ptr = 0; output = []
        for i in range(n):
            sample = delay[ptr]
            # Buzz bridge nonlinearity (creates sitar's characteristic buzz)
            if abs(sample) > 0.3:
                sample = math.copysign(0.3 + (abs(sample)-0.3)*0.2, sample)
            # Lowpass
            next_ptr = (ptr+1)%period
            delay[ptr] = 0.5*(sample + delay[next_ptr]) * 0.998
            output.append(sample * 0.7)
            ptr = (ptr+1) % period
        return output

    def tabla(self, pitch: str = "high", duration_s: float = 0.5) -> List[float]:
        """Indian tabla (tuned hand drum)."""
        n = int(duration_s * self.sr)
        freq = 200 if pitch == "high" else 80
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * (15 if pitch == "high" else 8))
            # Membrane modes (slightly inharmonic)
            s = 0.0
            modes = [1.0, 1.59, 2.14, 2.3] if pitch == "high" else [1.0, 1.5, 2.0]
            for k, m in enumerate(modes):
                s += math.sin(2*math.pi*freq*m*t) * env / (k+1)
            # Attack
            if t < 0.003: s += (1-t/0.003) * 0.6
            output.append(s * 0.7)
        return output

    def koto(self, freq: float, duration_s: float = 2.0) -> List[float]:
        """Japanese koto (plucked zither with bridge)."""
        ks = KarplusStrong(self.sr)
        # Koto: bright pluck + slight detuning of overtones
        note = ks.pluck(freq, duration_s, brightness=0.9, decay=0.997)
        # Add slight "twang" (bridge effect)
        for i in range(min(100, len(note))):
            note[i] *= 1.0 + 0.3 * math.exp(-i/20.0)
        return note

    def didgeridoo(self, freq: float = 65, duration_s: float = 4.0) -> List[float]:
        """Australian didgeridoo (drone tube)."""
        n = int(duration_s * self.sr)
        period = int(self.sr / freq)
        if period < 2: return [0.0] * n
        delay = [0.0] * period
        ptr = 0; z1 = 0.0; output = []
        for i in range(n):
            sample = delay[ptr]
            # Lip buzz + harmonics
            lip = math.tanh(2.0 * sample + 0.3*math.sin(i*0.01)) * 0.7
            # Heavy filtering (long tube = fundamental dominates)
            filt = 0.7*lip + 0.3*z1; z1 = filt
            delay[ptr] = -filt * 0.97
            # Add drone modulation
            mod = 1.0 + 0.1*math.sin(2*math.pi*2.0*i/self.sr)
            output.append(sample * mod * 0.5)
            ptr = (ptr+1)%period
        return output

    def kalimba(self, freq: float, duration_s: float = 2.0) -> List[float]:
        """African kalimba (thumb piano)."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            env = math.exp(-t * 3)
            # Tine vibration (nearly pure tone + slight inharmonicity)
            s = math.sin(2*math.pi*freq*t) * env
            s += math.sin(2*math.pi*freq*2.01*t) * env * 0.3
            s += math.sin(2*math.pi*freq*3.02*t) * env * 0.1
            # Click attack
            if t < 0.002: s += (1-t/0.002) * 0.4
            output.append(s * 0.6)
        return output


class ElectronicSounds:
    """Electronic/EDM sounds: 808, acid bass, supersaw, arp, wobble."""

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate

    def tr808_kick(self, duration_s: float = 0.8) -> List[float]:
        """Roland TR-808 style kick (deep sub bass sweep)."""
        n = int(duration_s * self.sr)
        output = []
        for i in range(n):
            t = i / self.sr
            # Deep pitch sweep (starts at 300Hz, drops to 30Hz)
            freq = 30 + 270 * math.exp(-t * 40)
            env = math.exp(-t * 5)
            sample = math.sin(2*math.pi*freq*t) * env
            # Add sub-harmonic
            sample += math.sin(2*math.pi*30*t) * env * 0.5
            # Transient click
            if t < 0.003: sample += (1-t/0.003) * 0.7
            output.append(sample * 0.9)
        return output

    def acid_bass(self, freq: float, duration_s: float = 0.3,
                  cutoff_sweep: float = 0.8, resonance: float = 0.7) -> List[float]:
        """TB-303 acid bass (saw + resonant filter sweep)."""
        n = int(duration_s * self.sr)
        output = []; z1 = z2 = 0.0
        for i in range(n):
            t = i / self.sr
            progress = i / n
            # Saw oscillator
            phase = (freq * t) % 1.0
            saw = 2.0 * phase - 1.0
            # Filter sweep (high → low)
            cutoff = freq * (2 + cutoff_sweep * 10 * math.exp(-progress * 8))
            # Resonant lowpass (state variable filter)
            f = 2.0 * math.sin(math.pi * min(cutoff/self.sr, 0.49))
            q = 1.0 - resonance * 0.9
            hp = saw - z1 - q * z2
            bp = hp * f + z2
            lp = bp * f + z1
            z1 = lp; z2 = bp
            # Envelope
            env = math.exp(-progress * 3)
            output.append(lp * env * 0.6)
        return output

    def supersaw(self, freq: float, duration_s: float,
                 num_oscs: int = 7, detune: float = 0.01) -> List[float]:
        """JP-8000 style supersaw (many detuned saws)."""
        n = int(duration_s * self.sr)
        output = []
        detunes = [(i - num_oscs//2) * detune for i in range(num_oscs)]
        for i in range(n):
            t = i / self.sr
            sample = 0.0
            for d in detunes:
                phase = (freq * (1+d) * t) % 1.0
                sample += (2.0*phase - 1.0) / num_oscs
            # Envelope
            att = min(1.0, t / 0.02)
            rel_t = duration_s - t
            rel = min(1.0, rel_t / 0.05) if rel_t < 0.05 else 1.0
            output.append(sample * att * rel * 0.5)
        return output

    def wobble_bass(self, freq: float, duration_s: float,
                    lfo_rate: float = 4.0) -> List[float]:
        """Dubstep wobble bass (filtered saw with LFO)."""
        n = int(duration_s * self.sr)
        output = []; z1 = 0.0
        for i in range(n):
            t = i / self.sr
            # Saw oscillator
            phase = (freq * t) % 1.0
            saw = 2.0 * phase - 1.0
            # LFO modulates filter cutoff
            lfo = (math.sin(2*math.pi*lfo_rate*t) + 1.0) * 0.5
            cutoff = freq * (1 + lfo * 8)
            # One-pole filter
            alpha = min(0.99, 2*math.pi*cutoff/self.sr)
            z1 = z1*(1-alpha) + saw*alpha
            output.append(z1 * 0.7)
        return output

    def arp(self, notes: List[int], duration_s: float,
            rate: float = 8.0, waveform: str = "saw") -> List[float]:
        """Arpeggiator (cycle through notes at rate)."""
        n = int(duration_s * self.sr)
        note_dur = 1.0 / rate  # seconds per note
        output = []
        for i in range(n):
            t = i / self.sr
            # Which note in sequence
            note_idx = int(t / note_dur) % len(notes)
            freq = 440.0 * (2.0 ** ((notes[note_idx] - 69) / 12.0))
            # Within-note position
            note_t = (t % note_dur) / note_dur
            # Envelope per note
            env = math.exp(-note_t * 5)
            # Waveform
            phase = (freq * t) % 1.0
            if waveform == "saw":
                sample = (2.0*phase - 1.0) * env
            elif waveform == "square":
                sample = (1.0 if phase < 0.5 else -1.0) * env
            else:
                sample = math.sin(2*math.pi*phase) * env
            output.append(sample * 0.4)
        return output
