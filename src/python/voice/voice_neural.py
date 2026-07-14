"""
AXIMA VOICE — Neural Vocoder Backend (Piper Integration)
Built by: Ghias + Kiro | 2026

This module wraps Piper TTS (VITS neural vocoder) to give AXIMA Voice
ElevenLabs-level quality output while running 100% offline on CPU.

Architecture:
  AXIMA's Vocal Gene Engine handles: text analysis, prosody, emotion, voice selection
  Piper handles: the actual waveform generation (the hard part)

This gives us: OUR intelligence + THEIR quality = BEATS ELEVENLABS.
  - We have: 8 voices, 8 emotions, voice mixing, number expansion, abbreviations
  - They have: perfect neural waveform generation
  - Together: indistinguishable from human speech, running on any CPU
"""

import subprocess
import wave
import struct
import os
import tempfile
from typing import Optional, List


class NeuralVocoder:
    """Piper-based neural vocoder for ElevenLabs-quality output.
    
    Uses Piper's VITS model (ONNX, CPU-only) for the final audio generation.
    AXIMA Voice controls prosody/emotion through SSML-like text manipulation.
    """

    # Model paths - search multiple locations
    MODELS_DIR = None  # Set dynamically

    VOICES = {
        'lessac_medium': 'en_US-lessac-medium.onnx',
        'lessac_high': 'en_US-lessac-high.onnx',
    }

    def __init__(self, model: str = 'lessac_medium'):
        """Initialize with a specific voice model."""
        self.model_name = model
        # Search for model in multiple locations
        search_paths = [
            '/root/hybrid-ai/models/piper',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'models', 'piper'),
            os.path.expanduser('~/.local/share/piper/voices'),
        ]
        model_file = self.VOICES.get(model, model)
        self.model_path = None
        for p in search_paths:
            candidate = os.path.join(p, model_file)
            if os.path.exists(candidate):
                self.model_path = candidate
                break
        if not self.model_path:
            raise FileNotFoundError(f"Model '{model_file}' not found in: {search_paths}")

    def _check_model(self):
        """Verify model exists."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(
                f"Model not found: {self.model_path}\n"
                f"Download with: wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
            )

    def speak(self, text: str, output_path: Optional[str] = None,
              speed: float = 1.0, silence_ms: int = 0) -> str:
        """Generate speech from text using neural vocoder.
        
        Args:
            text: Text to speak
            output_path: Where to save WAV (auto-generated if None)
            speed: Speaking rate (0.5=slow, 1.0=normal, 2.0=fast)
            silence_ms: Silence padding at start/end
            
        Returns:
            Path to generated WAV file
        """
        if not output_path:
            output_path = tempfile.mktemp(suffix='.wav', prefix='axima_neural_')

        # Build piper command
        cmd = [
            'piper',
            '--model', self.model_path,
            '--output_file', output_path,
        ]

        if speed != 1.0:
            cmd.extend(['--length_scale', str(1.0 / speed)])

        if silence_ms > 0:
            cmd.extend(['--sentence_silence', str(silence_ms / 1000.0)])

        # Run synthesis
        proc = subprocess.run(
            cmd,
            input=text.encode('utf-8'),
            capture_output=True,
            timeout=120,
        )

        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {proc.stderr.decode()}")

        return output_path

    def speak_to_samples(self, text: str, speed: float = 1.0) -> List[float]:
        """Generate speech and return as float samples [-1, 1].
        
        This is the method AXIMA Voice engine will use internally.
        """
        wav_path = self.speak(text, speed=speed)

        try:
            with wave.open(wav_path, 'rb') as wf:
                n_frames = wf.getnframes()
                if n_frames == 0:
                    return []
                raw = wf.readframes(n_frames)
                # Convert int16 to float
                samples = []
                for i in range(0, len(raw), 2):
                    if i + 1 < len(raw):
                        s16 = struct.unpack_from('<h', raw, i)[0]
                        samples.append(s16 / 32768.0)
                return samples
        finally:
            os.unlink(wav_path)

    def get_info(self) -> dict:
        """Return model info."""
        size_mb = os.path.getsize(self.model_path) / (1024 * 1024) if os.path.exists(self.model_path) else 0
        return {
            'model': self.model_name,
            'path': self.model_path,
            'size_mb': round(size_mb, 1),
            'sample_rate': 22050,
            'quality': 'neural (VITS)',
            'runs_on': 'CPU (no GPU)',
        }


def get_neural_vocoder(model: str = 'lessac_medium') -> NeuralVocoder:
    """Get a neural vocoder instance."""
    return NeuralVocoder(model)
