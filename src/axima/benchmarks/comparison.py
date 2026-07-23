"""Frontier comparison: head-to-head evaluation against baseline models.

Produces structured claims in the format required by the AXIMA master plan:
"AXIMA scores X% on [benchmark] vs [baseline] at Y% (N cases, judge: [type])"

This module does NOT call external APIs — it provides the framework for
configuring baselines and collecting/comparing results.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from .judges import JudgeResult
from .manifest import BenchmarkCase, BenchmarkManifest, JudgeType
from .runner import BenchmarkReport, BenchmarkRunner, CaseResult


class Winner(Enum):
    """Outcome of a comparison."""

    AXIMA = "axima"
    BASELINE = "baseline"
    TIE = "tie"
    INSUFFICIENT = "insufficient"


@dataclass
class RetryPolicy:
    """Retry policy for baseline queries.

    Attributes:
        max_retries: Maximum number of retry attempts.
        backoff_seconds: Initial backoff between retries.
        backoff_multiplier: Multiplier for exponential backoff.
    """

    max_retries: int = 3
    backoff_seconds: float = 1.0
    backoff_multiplier: float = 2.0


@dataclass
class BaselineConfig:
    """Configuration for a baseline model to compare against.

    Attributes:
        model_name: Name of the model (e.g., 'gpt-4', 'claude-3').
        version: Version or checkpoint identifier.
        api_endpoint: Optional API endpoint for querying the baseline.
        system_prompt: System prompt used for the baseline.
        tool_permissions: What tools the baseline has access to.
        temperature: Sampling temperature (0.0 for deterministic).
        context_limit: Maximum context window in tokens.
        retry_policy: How to handle API failures.
    """

    model_name: str
    version: str
    api_endpoint: Optional[str] = None
    system_prompt: str = ""
    tool_permissions: List[str] = field(default_factory=list)
    temperature: float = 0.0
    context_limit: int = 4096
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "model_name": self.model_name,
            "version": self.version,
            "api_endpoint": self.api_endpoint,
            "system_prompt": self.system_prompt,
            "tool_permissions": self.tool_permissions,
            "temperature": self.temperature,
            "context_limit": self.context_limit,
            "retry_policy": {
                "max_retries": self.retry_policy.max_retries,
                "backoff_seconds": self.retry_policy.backoff_seconds,
                "backoff_multiplier": self.retry_policy.backoff_multiplier,
            },
        }


@dataclass
class ConfidenceInterval:
    """Statistical confidence interval.

    Attributes:
        lower: Lower bound.
        upper: Upper bound.
        confidence_level: Confidence level (e.g., 0.95 for 95% CI).
    """

    lower: float
    upper: float
    confidence_level: float = 0.95


@dataclass
class ComparisonResult:
    """Result of a frontier comparison.

    Attributes:
        axima_score: AXIMA's pass rate on the benchmark.
        baseline_score: Baseline model's pass rate.
        categories: Per-category comparison results.
        effect_size: Cohen's d effect size.
        confidence_interval: CI for the score difference.
        winner: Who won (or tie/insufficient data).
        claim_format: Formatted claim string per master plan format.
    """

    axima_score: float
    baseline_score: float
    categories: Dict[str, Dict[str, float]]
    effect_size: float
    confidence_interval: ConfidenceInterval
    winner: Winner
    claim_format: str

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "axima_score": self.axima_score,
            "baseline_score": self.baseline_score,
            "categories": self.categories,
            "effect_size": self.effect_size,
            "confidence_interval": {
                "lower": self.confidence_interval.lower,
                "upper": self.confidence_interval.upper,
                "confidence_level": self.confidence_interval.confidence_level,
            },
            "winner": self.winner.value,
            "claim_format": self.claim_format,
        }


class BaselineQueryFn(Protocol):
    """Protocol for querying a baseline model."""

    def __call__(self, query: str) -> str: ...


class FrontierComparison:
    """Head-to-head evaluation of AXIMA against frontier baselines.

    Runs the same benchmark cases through both AXIMA and a baseline
    model, then produces a structured comparison with statistical
    rigor.
    """

    def __init__(
        self,
        axima_query_fn: Callable[[str], str],
        axima_version: str = "0.1.0",
    ) -> None:
        """Initialize frontier comparison.

        Args:
            axima_query_fn: Function to query AXIMA.
            axima_version: AXIMA version string.
        """
        self._axima_query_fn = axima_query_fn
        self._axima_version = axima_version
        self._baseline_config: Optional[BaselineConfig] = None
        self._baseline_query_fn: Optional[BaselineQueryFn] = None

    def configure_baseline(
        self,
        config: BaselineConfig,
        query_fn: BaselineQueryFn,
    ) -> None:
        """Configure the baseline model for comparison.

        Args:
            config: Baseline configuration.
            query_fn: Function to query the baseline model.
        """
        self._baseline_config = config
        self._baseline_query_fn = query_fn

    def run_comparison(
        self,
        manifest: BenchmarkManifest,
        seed: int = 42,
        categories: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """Run head-to-head comparison.

        Args:
            manifest: Benchmark manifest with cases.
            seed: Deterministic seed for reproducibility.
            categories: Optional category filter.

        Returns:
            ComparisonResult with scores, stats, and formatted claim.

        Raises:
            ValueError: If baseline is not configured.
        """
        if self._baseline_config is None or self._baseline_query_fn is None:
            raise ValueError(
                "Baseline not configured. Call configure_baseline() first."
            )

        # Run AXIMA
        axima_runner = BenchmarkRunner(
            query_fn=self._axima_query_fn,
            axima_version=self._axima_version,
            seed=seed,
        )
        axima_report = axima_runner.run_suite(
            manifest, categories=categories, shuffle=False
        )

        # Run baseline
        baseline_runner = BenchmarkRunner(
            query_fn=self._baseline_query_fn,
            axima_version=f"{self._baseline_config.model_name}-{self._baseline_config.version}",
            seed=seed,
        )
        baseline_report = baseline_runner.run_suite(
            manifest, categories=categories, shuffle=False
        )

        # Compute comparison
        return self._compute_comparison(
            axima_report, baseline_report, manifest
        )

    def generate_claim(self, result: ComparisonResult) -> str:
        """Generate the formatted claim string.

        Format: "AXIMA scores X% on [benchmark] vs [baseline] at Y%
                 (N cases, judge: [type], effect_size: d)"

        Args:
            result: The comparison result.

        Returns:
            Formatted claim string.
        """
        return result.claim_format

    def _compute_comparison(
        self,
        axima_report: BenchmarkReport,
        baseline_report: BenchmarkReport,
        manifest: BenchmarkManifest,
    ) -> ComparisonResult:
        """Compute comparison metrics between AXIMA and baseline."""
        axima_score = axima_report.pass_rate
        baseline_score = baseline_report.pass_rate

        # Per-category comparison
        categories: Dict[str, Dict[str, float]] = {}
        for cat in set(list(axima_report.categories.keys()) +
                       list(baseline_report.categories.keys())):
            categories[cat] = {
                "axima": axima_report.categories.get(cat, 0.0),
                "baseline": baseline_report.categories.get(cat, 0.0),
            }

        # Effect size (Cohen's d approximation)
        axima_scores = [
            r.judge_result.score for r in axima_report.results
        ]
        baseline_scores = [
            r.judge_result.score for r in baseline_report.results
        ]
        effect_size = self._cohens_d(axima_scores, baseline_scores)

        # Confidence interval for the difference
        n = len(axima_report.results)
        ci = self._compute_ci(axima_score, baseline_score, n)

        # Determine winner
        winner = self._determine_winner(axima_score, baseline_score, ci, n)

        # Format claim
        assert self._baseline_config is not None
        claim_format = (
            f"AXIMA scores {axima_score:.1%} on benchmark v{manifest.version} "
            f"vs {self._baseline_config.model_name} at {baseline_score:.1%} "
            f"({n} cases, effect_size: d={effect_size:.2f}, "
            f"CI: [{ci.lower:.3f}, {ci.upper:.3f}])"
        )

        return ComparisonResult(
            axima_score=axima_score,
            baseline_score=baseline_score,
            categories=categories,
            effect_size=effect_size,
            confidence_interval=ci,
            winner=winner,
            claim_format=claim_format,
        )

    def _cohens_d(
        self, group1: List[float], group2: List[float]
    ) -> float:
        """Compute Cohen's d effect size."""
        if not group1 or not group2:
            return 0.0

        n1, n2 = len(group1), len(group2)
        mean1 = sum(group1) / n1
        mean2 = sum(group2) / n2

        # Pooled standard deviation
        var1 = sum((x - mean1) ** 2 for x in group1) / max(n1 - 1, 1)
        var2 = sum((x - mean2) ** 2 for x in group2) / max(n2 - 1, 1)

        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / max(n1 + n2 - 2, 1)
        pooled_sd = math.sqrt(pooled_var) if pooled_var > 0 else 1e-10

        return (mean1 - mean2) / pooled_sd

    def _compute_ci(
        self,
        score1: float,
        score2: float,
        n: int,
        confidence: float = 0.95,
    ) -> ConfidenceInterval:
        """Compute confidence interval for score difference.

        Uses normal approximation for proportions.
        """
        if n == 0:
            return ConfidenceInterval(lower=0.0, upper=0.0, confidence_level=confidence)

        diff = score1 - score2

        # Standard error of difference of proportions
        se1 = math.sqrt(score1 * (1 - score1) / max(n, 1))
        se2 = math.sqrt(score2 * (1 - score2) / max(n, 1))
        se_diff = math.sqrt(se1**2 + se2**2)

        # Z-score for confidence level (1.96 for 95%)
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)

        lower = diff - z * se_diff
        upper = diff + z * se_diff

        return ConfidenceInterval(
            lower=lower, upper=upper, confidence_level=confidence
        )

    def _determine_winner(
        self,
        axima_score: float,
        baseline_score: float,
        ci: ConfidenceInterval,
        n: int,
    ) -> Winner:
        """Determine comparison winner with statistical rigor."""
        # Need minimum sample size
        if n < 10:
            return Winner.INSUFFICIENT

        # If CI for difference doesn't include 0, result is significant
        if ci.lower > 0:
            return Winner.AXIMA
        elif ci.upper < 0:
            return Winner.BASELINE
        else:
            # CI includes 0 — no significant difference
            # But if scores are very close, call it a tie
            if abs(axima_score - baseline_score) < 0.02:
                return Winner.TIE
            return Winner.INSUFFICIENT
