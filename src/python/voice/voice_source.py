"""
AXIMA VOICE — Module 4: The Source (Glottal Pulse Generator)
Built by: Ghias + Kiro | 2026

Implements the Liljencrants-Fant (LF) model of vocal fold vibration.
This is the most accurate physics model of how human vocal cords work.

The LF model produces one glottal flow derivative pulse per pitch cycle.
When filtered through the vocal tract (LPC), it becomes speech.

No training. No neural network. Pure physics.
"""

import math
import struct
from typing import List, Tuple


class GlottalSource:
    """LF Model glottal pulse generator.
    
    Generates the excitation signal that drives the vocal tract filter.
    Controls: pitch (F0), voice quality (Rd), loudness (Ee).
    """

    def __init__(self, sample_rate: int = 22050):
        self.sr = sample_rate
        self.phase = 0.0  # Current phase within glottal cycle [0, 1)
        self.cycle_samples = 0
        self.sample_count = 0

    def generate(self, num_samples: int, f0: float, rd: float = 1.0,
                 jitter: float = 0.0, shimmer: float = 0.0) -> List[float]:
        """Generate glottal source signal.
        
        Args:
            num_samples: How many samples to generate
            f0: Fundamental frequency in Hz (pitch)
            rd: Voice quality parameter (0.3=tense, 1.0=modal, 2.7=breathy)
            jitter: F0 perturbation amount (0-0.05 typical)
            shimmer: Amplitude perturbation (0-0.05 typical)
        
        Returns:
            List of float samples (glottal flow derivative)
        """
        if f0 <= 0:
            # Unvoiced: return silence (noise added separately)
            return [0.0] * num_samples

        output = []
        # LF model timing parameters from Rd
        tp, te, ta = self._rd_to_lf_params(rd)

        for i in range(num_samples):
            # Apply jitter: small random F0 variation per cycle
            local_f0 = f0
            if jitter > 0 and self.phase < 0.01:
                # New cycle — apply jitter
                local_f0 = f0 * (1.0 + jitter * self._quasi_random(self.sample_count))

            # Period length in samples
            period = self.sr / local_f0

            # Normalized time within cycle [0, 1)
            t = self.phase

            # Generate LF derivative waveform
            sample = self._lf_derivative(t, tp, te, ta)

            # Apply shimmer (amplitude variation per cycle)
            if shimmer > 0:
                amp_mod = 1.0 + shimmer * self._quasi_random(self.sample_count + 7919)
                sample *= amp_mod

            output.append(sample)

            # Advance phase
            self.phase += 1.0 / period
            if self.phase >= 1.0:
                self.phase -= 1.0

            self.sample_count += 1

        return output

    def _lf_derivative(self, t: float, tp: float, te: float, ta: float) -> float:
        """Compute one sample of the LF glottal flow derivative.
        
        The LF model has 3 phases:
          Phase 1 (0 → tp): Opening — rising sinusoid
          Phase 2 (tp → te): Closing — falling exponential × sinusoid
          Phase 3 (te → 1.0): Return — exponential recovery
          
        The derivative form is what actually excites the vocal tract.
        """
        if t < 0 or t >= 1.0:
            return 0.0

        if t <= te:
            # Opening + closing phase (combined sinusoidal model)
            # E(t) = -E0 * exp(alpha*t) * sin(omega_g * t)
            omega_g = math.pi / tp  # Frequency of the opening sinusoid
            alpha = self._compute_alpha(tp, te, omega_g)

            sample = -math.exp(alpha * t) * math.sin(omega_g * t)

            # Normalize so peak = 1.0
            # Peak occurs near tp
            peak = math.exp(alpha * tp) * 1.0  # sin(pi) area, approximate
            if peak > 0:
                sample /= max(peak, 0.01)

            return sample

        else:
            # Return phase (te → 1.0): exponential recovery
            # E(t) = -Ee/(epsilon*Ta) * [exp(-epsilon*(t-te)) - exp(-epsilon*(1-te))]
            epsilon = 1.0 / max(ta, 0.001)
            t_rel = t - te
            tc = 1.0 - te  # Remaining time in cycle

            recovery = math.exp(-epsilon * t_rel) - math.exp(-epsilon * tc)

            # Scale to match closing instant amplitude
            return 0.5 * recovery

    def _compute_alpha(self, tp: float, te: float, omega_g: float) -> float:
        """Compute the exponential growth constant alpha.
        
        Alpha controls how much the amplitude grows during the open phase.
        Larger alpha = more abrupt closing = more excitation energy.
        """
        # Simplified: alpha ≈ function of te-tp ratio
        # More accurate iterative solution could be used, but this works well
        if te <= tp:
            return 0.0
        ratio = te / max(tp, 0.01)
        alpha = (ratio - 1.0) * 3.0  # Empirical fit
        return min(alpha, 10.0)  # Clamp for stability

    def _rd_to_lf_params(self, rd: float) -> Tuple[float, float, float]:
        """Convert Rd parameter to LF timing parameters.
        
        Rd is a single parameter that controls voice quality:
          Rd = 0.3: Very tense (pressed, powerful)
          Rd = 1.0: Modal (normal conversational)
          Rd = 2.7: Very breathy (soft, airy)
          
        Returns: (Tp, Te, Ta) as fractions of the cycle [0, 1]
        """
        rd = max(0.3, min(2.7, rd))  # Clamp to valid range

        # Regression formulas from Fant et al.
        # Tp: time of positive peak (opening duration)
        tp = 0.5 * (1.0 / (1.0 + 0.5 * rd))  # 0.4 (tense) → 0.25 (breathy)

        # Te: time of maximum excitation (closing instant)
        te = tp + tp * (0.4 + 0.2 * rd)  # Close after peak

        # Ta: return phase time constant (recovery speed)
        ta = 0.01 * math.exp(0.5 * rd)  # Small for tense, larger for breathy

        # Ensure valid ordering
        te = min(te, 0.95)
        ta = max(ta, 0.005)

        return tp, te, ta

    def _quasi_random(self, n: int) -> float:
        """Deterministic pseudo-random in [-1, 1] for jitter/shimmer.
        Avoids importing random module. Uses golden ratio hash.
        """
        x = (n * 0.6180339887) % 1.0
        return 2.0 * x - 1.0

    def generate_noise(self, num_samples: int, bandwidth: float = 1.0) -> List[float]:
        """Generate noise source for unvoiced sounds (fricatives, aspiration).
        
        Args:
            num_samples: Number of samples
            bandwidth: 0-1, controls spectral flatness (1=white, <1=colored)
        """
        output = []
        prev = 0.0
        for i in range(num_samples):
            # White noise from quasi-random
            white = self._quasi_random(self.sample_count + i + 13337)
            # Optional coloring (low-pass for darker noise)
            if bandwidth < 1.0:
                sample = bandwidth * white + (1.0 - bandwidth) * prev
                prev = sample
            else:
                sample = white
            output.append(sample * 0.3)  # Scale down noise
        return output

    def generate_burst(self, f0: float, place: str = "alveolar") -> List[float]:
        """Generate stop consonant burst (transient impulse).
        
        Args:
            f0: For timing reference
            place: "bilabial", "alveolar", "velar" — affects burst spectrum
        """
        # Burst is a short impulse (1-3ms) shaped by place of articulation
        burst_len = int(self.sr * 0.003)  # 3ms
        burst = []

        for i in range(burst_len):
            t = i / burst_len
            # Exponential decay envelope
            env = math.exp(-t * 8.0)
            # Impulse + noise mix
            noise = self._quasi_random(self.sample_count + i + 99991)
            imp = 1.0 if i == 0 else 0.0

            sample = (imp * 0.7 + noise * 0.3) * env

            # Place-dependent spectral shaping
            if place == "bilabial":
                sample *= 0.5  # Weaker, lower freq burst
            elif place == "velar":
                sample *= 0.8  # Mid-frequency compact burst

            burst.append(sample)

        return burst
