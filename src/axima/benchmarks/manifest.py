"""Benchmark manifest: frozen, integrity-verified test case registry.

The manifest is the single source of truth for benchmark cases.
Once frozen, cases cannot be modified without breaking the integrity hash.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Optional


class JudgeType(Enum):
    """Supported judge types for benchmark evaluation."""

    EXACT = "exact"
    TOLERANCE = "tolerance"
    AST = "ast"
    PROOF = "proof"
    HUMAN = "human"
    COMPILATION = "compilation"
    TEST = "test"
    SEMANTIC = "semantic"


class Difficulty(Enum):
    """Case difficulty levels."""

    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    FRONTIER = "frontier"


@dataclass(frozen=True)
class BenchmarkCase:
    """A single benchmark test case.

    Attributes:
        id: Unique case identifier (e.g., 'math_001').
        category: Domain category (math, physics, code, multilingual, etc.).
        input: The query or problem statement.
        expected_output: The correct answer or expected structure.
        judge_type: How to evaluate the response.
        difficulty: How hard the case is.
        hidden: If True, case is not disclosed publicly (canary/secret).
        source: Origin of the case (manual, generated, adapted).
    """

    id: str
    category: str
    input: str
    expected_output: str
    judge_type: JudgeType
    difficulty: Difficulty
    hidden: bool = False
    source: str = "manual"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "category": self.category,
            "input": self.input,
            "expected_output": self.expected_output,
            "judge_type": self.judge_type.value,
            "difficulty": self.difficulty.value,
            "hidden": self.hidden,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BenchmarkCase:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            category=data["category"],
            input=data["input"],
            expected_output=data["expected_output"],
            judge_type=JudgeType(data["judge_type"]),
            difficulty=Difficulty(data["difficulty"]),
            hidden=data.get("hidden", False),
            source=data.get("source", "manual"),
        )


@dataclass
class BenchmarkManifest:
    """A frozen collection of benchmark cases with integrity verification.

    Attributes:
        version: Semantic version of the manifest.
        cases: List of benchmark cases.
        frozen_at: ISO timestamp when the manifest was frozen.
        contamination_disclosures: Known contamination risks.
        hash: SHA-256 hash of the case content for integrity.
    """

    version: str
    cases: List[BenchmarkCase]
    frozen_at: str
    contamination_disclosures: List[str] = field(default_factory=list)
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of all case content."""
        content = json.dumps(
            [c.to_dict() for c in self.cases],
            sort_keys=True,
            ensure_ascii=True,
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        """Serialize manifest to dictionary."""
        return {
            "version": self.version,
            "cases": [c.to_dict() for c in self.cases],
            "frozen_at": self.frozen_at,
            "contamination_disclosures": self.contamination_disclosures,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> BenchmarkManifest:
        """Deserialize manifest from dictionary."""
        cases = [BenchmarkCase.from_dict(c) for c in data.get("cases", [])]
        return cls(
            version=data["version"],
            cases=cases,
            frozen_at=data.get("frozen_at", ""),
            contamination_disclosures=data.get("contamination_disclosures", []),
            hash=data.get("hash", ""),
        )


class ManifestManager:
    """Manages benchmark manifest lifecycle: loading, freezing, validation.

    The manifest manager ensures that once a manifest is frozen, its
    integrity can be verified and contamination can be detected.
    """

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self._manifest_path = manifest_path
        self._manifest: Optional[BenchmarkManifest] = None

    @property
    def manifest(self) -> Optional[BenchmarkManifest]:
        """Current loaded manifest."""
        return self._manifest

    def load(self, path: Optional[Path] = None) -> BenchmarkManifest:
        """Load manifest from a JSON file.

        Args:
            path: Path to manifest JSON. Uses constructor path if None.

        Returns:
            The loaded BenchmarkManifest.

        Raises:
            FileNotFoundError: If the manifest file does not exist.
            ValueError: If the file contains invalid JSON.
        """
        target = path or self._manifest_path
        if target is None:
            raise ValueError("No manifest path specified")

        if not target.exists():
            raise FileNotFoundError(f"Manifest not found: {target}")

        with open(target, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._manifest = BenchmarkManifest.from_dict(data)
        return self._manifest

    def freeze(self, manifest: Optional[BenchmarkManifest] = None) -> BenchmarkManifest:
        """Freeze a manifest: compute hash and set timestamp.

        Once frozen, any modification to cases will invalidate the hash.

        Args:
            manifest: Manifest to freeze. Uses current if None.

        Returns:
            The frozen manifest with computed hash and timestamp.
        """
        target = manifest or self._manifest
        if target is None:
            raise ValueError("No manifest to freeze")

        target.frozen_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        target.hash = target.compute_hash()
        self._manifest = target
        return target

    def add_case(self, case: BenchmarkCase) -> None:
        """Add a case to the current manifest.

        Args:
            case: The benchmark case to add.

        Raises:
            ValueError: If manifest is already frozen (has a hash).
            ValueError: If case ID already exists.
        """
        if self._manifest is None:
            self._manifest = BenchmarkManifest(
                version="0.0.1",
                cases=[],
                frozen_at="",
            )

        if self._manifest.hash:
            raise ValueError(
                "Cannot add cases to a frozen manifest. "
                "Create a new version instead."
            )

        existing_ids = {c.id for c in self._manifest.cases}
        if case.id in existing_ids:
            raise ValueError(f"Duplicate case ID: {case.id}")

        self._manifest.cases.append(case)

    def validate_integrity(self, manifest: Optional[BenchmarkManifest] = None) -> bool:
        """Validate that the manifest hash matches its content.

        Args:
            manifest: Manifest to validate. Uses current if None.

        Returns:
            True if hash matches computed hash, False otherwise.
        """
        target = manifest or self._manifest
        if target is None:
            raise ValueError("No manifest to validate")

        if not target.hash:
            return False  # Unfrozen manifests have no integrity guarantee

        return target.hash == target.compute_hash()

    def detect_contamination(
        self,
        source_code: str,
        manifest: Optional[BenchmarkManifest] = None,
    ) -> List[str]:
        """Detect potential contamination: benchmark answers in source code.

        Scans source code for exact matches of expected outputs from
        benchmark cases. This detects hardcoded answers that would
        inflate scores.

        Args:
            source_code: The source code text to scan.
            manifest: Manifest to check against. Uses current if None.

        Returns:
            List of case IDs whose expected outputs appear in source code.
        """
        target = manifest or self._manifest
        if target is None:
            raise ValueError("No manifest to check")

        contaminated: List[str] = []
        for case in target.cases:
            # Only check non-trivial expected outputs (>3 chars)
            expected = case.expected_output.strip()
            if len(expected) > 3 and expected in source_code:
                contaminated.append(case.id)

        return contaminated

    def save(self, path: Optional[Path] = None) -> None:
        """Save manifest to JSON file.

        Args:
            path: Destination path. Uses constructor path if None.
        """
        target = path or self._manifest_path
        if target is None:
            raise ValueError("No path specified for saving")
        if self._manifest is None:
            raise ValueError("No manifest to save")

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self._manifest.to_dict(), f, indent=2, ensure_ascii=False)
