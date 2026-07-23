"""AXIMA Benchmark and Frontier Qualification System.

Provides:
- BenchmarkManifest: Frozen, integrity-verified test cases
- Judges: Exact, tolerance, AST, proof, compilation, test, semantic
- Runner: Isolated benchmark execution with reporting
- ImmuneSystem: Contamination detection and canary validation
- FrontierComparison: Head-to-head evaluation against baselines
"""

from __future__ import annotations

from .manifest import BenchmarkCase, BenchmarkManifest, ManifestManager
from .judges import (
    JudgeResult,
    ExactJudge,
    ToleranceJudge,
    ASTJudge,
    ProofJudge,
    CompilationJudge,
    TestJudge,
    SemanticJudge,
)
from .runner import BenchmarkRunner, BenchmarkReport
from .immune_system import BenchmarkImmuneSystem
from .comparison import BaselineConfig, ComparisonResult, FrontierComparison

__all__ = [
    "BenchmarkCase",
    "BenchmarkManifest",
    "ManifestManager",
    "JudgeResult",
    "ExactJudge",
    "ToleranceJudge",
    "ASTJudge",
    "ProofJudge",
    "CompilationJudge",
    "TestJudge",
    "SemanticJudge",
    "BenchmarkRunner",
    "BenchmarkReport",
    "BenchmarkImmuneSystem",
    "BaselineConfig",
    "ComparisonResult",
    "FrontierComparison",
]
