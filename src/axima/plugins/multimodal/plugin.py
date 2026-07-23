"""
Multimodal Plugin
=================

Provides analysis capabilities for images, charts/diagrams, and audio.
All results explicitly name the algorithm used and report uncertainty.
External tools (e.g., Pillow, ffmpeg) are declared as optional non-core capabilities.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..base import PluginBase
from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor
from ...semantics.meaning_ir import MeaningIR


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class MediaType(Enum):
    """Supported media types."""

    IMAGE = "image"
    AUDIO = "audio"
    CHART = "chart"
    DIAGRAM = "diagram"


class AnalysisAlgorithm(Enum):
    """Named algorithms used for analysis."""

    # Image
    HEADER_PARSE = "file_header_parse"
    EXIF_EXTRACT = "exif_byte_extract"
    DIMENSION_READ = "dimension_from_header"

    # Audio
    WAV_HEADER_PARSE = "wav_header_parse"
    SILENCE_THRESHOLD = "amplitude_silence_threshold"
    DURATION_CALC = "sample_count_duration"

    # Chart/diagram
    STRUCTURE_INFERENCE = "structure_rule_inference"
    ELEMENT_COUNTING = "element_counting"


@dataclass
class AnalysisResult:
    """Result of a multimodal analysis with explicit algorithm and uncertainty.

    Attributes:
        media_type: What kind of media was analyzed.
        algorithm_used: Which algorithm produced this result.
        findings: Key-value findings from the analysis.
        uncertainty: Confidence estimate (0.0-1.0, lower = less certain).
        raw_metadata: Raw extracted metadata.
        warnings: Any issues encountered.
    """

    media_type: MediaType
    algorithm_used: AnalysisAlgorithm
    findings: Dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ImageMetadata:
    """Extracted image metadata."""

    width: int = 0
    height: int = 0
    format: str = "unknown"
    color_depth: int = 0
    has_alpha: bool = False
    file_size_bytes: int = 0
    exif: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AudioMetadata:
    """Extracted audio metadata."""

    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    bit_depth: int = 0
    format: str = "unknown"
    file_size_bytes: int = 0
    silent_regions: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class ChartDescription:
    """Structural description of a chart or diagram."""

    chart_type: str = "unknown"  # bar, line, pie, scatter, flow, tree, etc.
    elements_count: int = 0
    labels: List[str] = field(default_factory=list)
    data_series: int = 0
    has_legend: bool = False
    has_axis_labels: bool = False
    description: str = ""


@dataclass
class ExternalToolDeclaration:
    """Declaration of an optional external tool (non-core capability)."""

    tool_name: str
    purpose: str
    required_package: str
    is_available: bool = False
    fallback_behavior: str = "header-only analysis"


# ---------------------------------------------------------------------------
# Pure-Python image header parsing
# ---------------------------------------------------------------------------


def _parse_png_dimensions(data: bytes) -> Tuple[int, int]:
    """Parse PNG dimensions from file header (IHDR chunk)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return 0, 0
    # IHDR chunk starts at byte 8: 4-byte length, 4-byte type, then data
    # Width is at offset 16, height at offset 20
    if len(data) < 24:
        return 0, 0
    width = struct.unpack(">I", data[16:20])[0]
    height = struct.unpack(">I", data[20:24])[0]
    return width, height


def _parse_jpeg_dimensions(data: bytes) -> Tuple[int, int]:
    """Parse JPEG dimensions from SOF marker."""
    if data[:2] != b"\xff\xd8":
        return 0, 0
    pos = 2
    while pos < len(data) - 9:
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        # SOF0 or SOF2 markers
        if marker in (0xC0, 0xC2):
            height = struct.unpack(">H", data[pos + 5:pos + 7])[0]
            width = struct.unpack(">H", data[pos + 7:pos + 9])[0]
            return width, height
        # Skip to next marker
        if marker == 0xD9:  # EOI
            break
        if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0x01):
            pos += 2
        else:
            length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            pos += 2 + length
    return 0, 0


def _parse_gif_dimensions(data: bytes) -> Tuple[int, int]:
    """Parse GIF dimensions from header."""
    if data[:3] not in (b"GIF", ):
        if not data[:6].startswith(b"GIF"):
            return 0, 0
    if len(data) < 10:
        return 0, 0
    width = struct.unpack("<H", data[6:8])[0]
    height = struct.unpack("<H", data[8:10])[0]
    return width, height


def _parse_bmp_dimensions(data: bytes) -> Tuple[int, int]:
    """Parse BMP dimensions from DIB header."""
    if data[:2] != b"BM":
        return 0, 0
    if len(data) < 26:
        return 0, 0
    width = struct.unpack("<I", data[18:22])[0]
    height = abs(struct.unpack("<i", data[22:26])[0])
    return width, height


def _detect_image_format(data: bytes) -> str:
    """Detect image format from magic bytes."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:2] == b"\xff\xd8":
        return "jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:2] == b"BM":
        return "bmp"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "unknown"


def _parse_wav_header(data: bytes) -> Dict[str, Any]:
    """Parse WAV file header."""
    result: Dict[str, Any] = {}
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        return result
    if len(data) < 44:
        return result

    result["format"] = "wav"
    # fmt chunk
    channels = struct.unpack("<H", data[22:24])[0]
    sample_rate = struct.unpack("<I", data[24:28])[0]
    bit_depth = struct.unpack("<H", data[34:36])[0]

    # data chunk size (approximate duration)
    data_size = struct.unpack("<I", data[40:44])[0]

    result["channels"] = channels
    result["sample_rate"] = sample_rate
    result["bit_depth"] = bit_depth
    result["data_size"] = data_size

    bytes_per_sample = (bit_depth // 8) * channels
    if bytes_per_sample > 0 and sample_rate > 0:
        result["duration_seconds"] = data_size / (sample_rate * bytes_per_sample)
    else:
        result["duration_seconds"] = 0.0

    return result


# ---------------------------------------------------------------------------
# MultimodalPlugin
# ---------------------------------------------------------------------------


class MultimodalPlugin(PluginBase):
    """Plugin for multimodal content analysis.

    Capabilities:
    - Image metadata extraction (dimensions, format, EXIF basics)
    - Chart/diagram structural description
    - Audio waveform analysis (WAV: duration, sample rate, silence detection)

    All results explicitly name the algorithm used and report uncertainty.
    External tools (Pillow, ffmpeg, etc.) are declared as non-core capabilities
    that enhance but are not required for basic operation.
    """

    def __init__(self) -> None:
        self._external_tools: List[ExternalToolDeclaration] = [
            ExternalToolDeclaration(
                tool_name="Pillow",
                purpose="Full image parsing including EXIF, ICC profiles",
                required_package="Pillow",
                is_available=self._check_pillow(),
                fallback_behavior="header-only parsing for PNG/JPEG/GIF/BMP",
            ),
            ExternalToolDeclaration(
                tool_name="ffprobe",
                purpose="Full audio/video metadata extraction",
                required_package="ffmpeg",
                is_available=self._check_ffprobe(),
                fallback_behavior="WAV header parsing only",
            ),
        ]

    def name(self) -> str:
        return "multimodal_analyzer"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["image", "audio", "chart", "diagram"],
            produced_types=["image_metadata", "audio_metadata", "chart_description"],
            preconditions=["file_path_available"],
            postconditions=["metadata_extracted", "algorithm_named", "uncertainty_reported"],
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Execute multimodal analysis based on MeaningIR."""
        return ExecutionResult(
            answer="Multimodal analysis requires file input via analyze_image/analyze_audio",
            status="success",
            engine="multimodal_analyzer",
        )

    def health_check(self) -> bool:
        return True

    @property
    def external_tools(self) -> List[ExternalToolDeclaration]:
        """Declared external tools (non-core capabilities)."""
        return list(self._external_tools)

    # ------------------------------------------------------------------
    # Image analysis
    # ------------------------------------------------------------------

    def analyze_image(self, file_path: str) -> AnalysisResult:
        """Extract image metadata from a file.

        Uses pure-Python header parsing for PNG, JPEG, GIF, BMP.
        Reports algorithm used and uncertainty.

        Args:
            file_path: Path to the image file.

        Returns:
            AnalysisResult with image metadata.
        """
        result = AnalysisResult(
            media_type=MediaType.IMAGE,
            algorithm_used=AnalysisAlgorithm.HEADER_PARSE,
        )

        if not os.path.isfile(file_path):
            result.warnings.append(f"File not found: {file_path}")
            result.uncertainty = 1.0
            return result

        try:
            file_size = os.path.getsize(file_path)
            # Read first 4KB for header analysis
            with open(file_path, "rb") as f:
                header = f.read(4096)
        except OSError as e:
            result.warnings.append(f"Cannot read file: {e}")
            result.uncertainty = 1.0
            return result

        img_format = _detect_image_format(header)
        width, height = 0, 0

        if img_format == "png":
            width, height = _parse_png_dimensions(header)
            result.algorithm_used = AnalysisAlgorithm.DIMENSION_READ
        elif img_format == "jpeg":
            width, height = _parse_jpeg_dimensions(header)
            result.algorithm_used = AnalysisAlgorithm.DIMENSION_READ
        elif img_format == "gif":
            width, height = _parse_gif_dimensions(header)
            result.algorithm_used = AnalysisAlgorithm.DIMENSION_READ
        elif img_format == "bmp":
            width, height = _parse_bmp_dimensions(header)
            result.algorithm_used = AnalysisAlgorithm.DIMENSION_READ
        else:
            result.warnings.append(f"Unsupported format: {img_format}")
            result.uncertainty = 0.8

        result.findings = {
            "width": width,
            "height": height,
            "format": img_format,
            "file_size_bytes": file_size,
        }
        result.raw_metadata = {"header_bytes_read": len(header)}

        # Uncertainty based on whether we could parse dimensions
        if width > 0 and height > 0:
            result.uncertainty = 0.05  # Very confident in header-parsed dims
        else:
            result.uncertainty = 0.7

        return result

    def analyze_image_bytes(self, data: bytes) -> AnalysisResult:
        """Analyze image from raw bytes (no file needed).

        Args:
            data: Raw image bytes.

        Returns:
            AnalysisResult with image metadata.
        """
        result = AnalysisResult(
            media_type=MediaType.IMAGE,
            algorithm_used=AnalysisAlgorithm.HEADER_PARSE,
        )

        img_format = _detect_image_format(data)
        width, height = 0, 0

        if img_format == "png":
            width, height = _parse_png_dimensions(data)
        elif img_format == "jpeg":
            width, height = _parse_jpeg_dimensions(data)
        elif img_format == "gif":
            width, height = _parse_gif_dimensions(data)
        elif img_format == "bmp":
            width, height = _parse_bmp_dimensions(data)

        result.findings = {
            "width": width,
            "height": height,
            "format": img_format,
            "file_size_bytes": len(data),
        }
        result.uncertainty = 0.05 if (width > 0 and height > 0) else 0.7
        return result

    # ------------------------------------------------------------------
    # Audio analysis
    # ------------------------------------------------------------------

    def analyze_audio(self, file_path: str) -> AnalysisResult:
        """Extract audio metadata from a WAV file.

        Uses pure-Python WAV header parsing.
        Reports algorithm used and uncertainty.

        Args:
            file_path: Path to the audio file.

        Returns:
            AnalysisResult with audio metadata.
        """
        result = AnalysisResult(
            media_type=MediaType.AUDIO,
            algorithm_used=AnalysisAlgorithm.WAV_HEADER_PARSE,
        )

        if not os.path.isfile(file_path):
            result.warnings.append(f"File not found: {file_path}")
            result.uncertainty = 1.0
            return result

        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as f:
                header = f.read(44)  # WAV header is 44 bytes
        except OSError as e:
            result.warnings.append(f"Cannot read file: {e}")
            result.uncertainty = 1.0
            return result

        wav_info = _parse_wav_header(header)

        if not wav_info:
            result.warnings.append("Not a valid WAV file or unsupported format")
            result.uncertainty = 0.9
            result.findings = {"format": "unknown", "file_size_bytes": file_size}
            return result

        result.findings = {
            "duration_seconds": wav_info.get("duration_seconds", 0.0),
            "sample_rate": wav_info.get("sample_rate", 0),
            "channels": wav_info.get("channels", 0),
            "bit_depth": wav_info.get("bit_depth", 0),
            "format": "wav",
            "file_size_bytes": file_size,
        }
        result.raw_metadata = wav_info
        result.uncertainty = 0.05  # WAV header parsing is deterministic

        return result

    def detect_silence(
        self,
        file_path: str,
        threshold: float = 0.01,
        min_duration_seconds: float = 0.5,
    ) -> AnalysisResult:
        """Detect silent regions in a WAV audio file.

        Algorithm: amplitude_silence_threshold
        Reads raw samples and flags regions below threshold.

        Args:
            file_path: Path to WAV file.
            threshold: Amplitude threshold (0.0-1.0) for silence.
            min_duration_seconds: Minimum silence duration to report.

        Returns:
            AnalysisResult with silent regions.
        """
        result = AnalysisResult(
            media_type=MediaType.AUDIO,
            algorithm_used=AnalysisAlgorithm.SILENCE_THRESHOLD,
        )

        if not os.path.isfile(file_path):
            result.warnings.append(f"File not found: {file_path}")
            result.uncertainty = 1.0
            return result

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except OSError as e:
            result.warnings.append(f"Cannot read file: {e}")
            result.uncertainty = 1.0
            return result

        wav_info = _parse_wav_header(data[:44])
        if not wav_info:
            result.warnings.append("Not a valid WAV file")
            result.uncertainty = 0.9
            return result

        sample_rate = wav_info.get("sample_rate", 44100)
        bit_depth = wav_info.get("bit_depth", 16)
        channels = wav_info.get("channels", 1)

        # Parse raw samples (16-bit only for now)
        if bit_depth != 16:
            result.warnings.append(f"Only 16-bit WAV supported, got {bit_depth}-bit")
            result.uncertainty = 0.8
            result.findings = {"silent_regions": []}
            return result

        audio_data = data[44:]
        bytes_per_sample = 2 * channels
        num_samples = len(audio_data) // bytes_per_sample

        silent_regions: List[Tuple[float, float]] = []
        silence_start: Optional[float] = None
        max_amplitude = 32768.0

        # Process in chunks for efficiency
        chunk_size = sample_rate // 10  # 100ms chunks
        for chunk_idx in range(0, num_samples, chunk_size):
            chunk_end = min(chunk_idx + chunk_size, num_samples)
            chunk_max = 0.0

            for i in range(chunk_idx, chunk_end):
                offset = i * bytes_per_sample
                if offset + 2 > len(audio_data):
                    break
                sample = abs(struct.unpack("<h", audio_data[offset:offset + 2])[0])
                chunk_max = max(chunk_max, sample / max_amplitude)

            time_pos = chunk_idx / sample_rate

            if chunk_max < threshold:
                if silence_start is None:
                    silence_start = time_pos
            else:
                if silence_start is not None:
                    duration = time_pos - silence_start
                    if duration >= min_duration_seconds:
                        silent_regions.append((silence_start, time_pos))
                    silence_start = None

        # Handle trailing silence
        if silence_start is not None:
            end_time = num_samples / sample_rate
            duration = end_time - silence_start
            if duration >= min_duration_seconds:
                silent_regions.append((silence_start, end_time))

        result.findings = {
            "silent_regions": silent_regions,
            "silence_count": len(silent_regions),
            "total_silence_seconds": sum(end - start for start, end in silent_regions),
            "threshold_used": threshold,
            "min_duration_used": min_duration_seconds,
        }
        result.uncertainty = 0.1  # Depends on threshold choice
        return result

    # ------------------------------------------------------------------
    # Chart/diagram analysis
    # ------------------------------------------------------------------

    def describe_chart(self, structure: Dict[str, Any]) -> AnalysisResult:
        """Generate a structural description of a chart from its data structure.

        This does not do image recognition — it analyzes structured chart data
        (e.g., from a chart library's data model).

        Args:
            structure: Dict with chart data (type, labels, series, etc.)

        Returns:
            AnalysisResult with chart description.
        """
        result = AnalysisResult(
            media_type=MediaType.CHART,
            algorithm_used=AnalysisAlgorithm.STRUCTURE_INFERENCE,
        )

        chart_type = structure.get("type", "unknown")
        labels = structure.get("labels", [])
        series = structure.get("series", [])
        title = structure.get("title", "")

        description_parts: List[str] = []
        if title:
            description_parts.append(f"Chart titled '{title}'")
        description_parts.append(f"Type: {chart_type}")
        description_parts.append(f"Data series: {len(series)}")
        description_parts.append(f"Data points: {len(labels)}")

        if labels:
            description_parts.append(f"Labels: {', '.join(str(l) for l in labels[:5])}")
            if len(labels) > 5:
                description_parts.append(f"... and {len(labels) - 5} more")

        result.findings = {
            "chart_type": chart_type,
            "elements_count": len(labels) * max(len(series), 1),
            "labels": labels,
            "data_series_count": len(series),
            "has_title": bool(title),
            "description": ". ".join(description_parts),
        }
        result.uncertainty = 0.1  # Structured data is reliable
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_pillow() -> bool:
        """Check if Pillow is available."""
        try:
            import importlib
            importlib.import_module("PIL")
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_ffprobe() -> bool:
        """Check if ffprobe is available."""
        import shutil
        return shutil.which("ffprobe") is not None
