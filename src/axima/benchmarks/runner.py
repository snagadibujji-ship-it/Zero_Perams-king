"""Benchmark runner: isolated execution with deterministic seeding.

The runner executes benchmark cases against AXIMA in isolation,
ensuring the active runtime cannot inspect or influence results.
Reports failures and abstentions prominently, not just passes.

Enhanced to support:
- Loading cases from manifest files on disk
- Running through the Axima API (src/axima/api.py)
- Applying appropriate judges per case
- Generating BenchmarkReport
- Saving reports to evals/reports/
"""

from __future__ import annotations

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

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
from .manifest import BenchmarkCase, BenchmarkManifest, ManifestManager, JudgeType


class AximaQueryFn(Protocol):
    """Protocol for the AXIMA query function."""

    def __call__(self, query: str) -> str: ...


@dataclass
class LatencyStats:
    """Latency statistics for a benchmark run.

    Attributes:
        min_ms: Minimum latency in milliseconds.
        max_ms: Maximum latency in milliseconds.
        mean_ms: Mean latency in milliseconds.
        p50_ms: Median latency.
        p95_ms: 95th percentile latency.
        p99_ms: 99th percentile latency.
    """

    min_ms: float = 0.0
    max_ms: float = 0.0
    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0

    @classmethod
    def from_latencies(cls, latencies: List[float]) -> LatencyStats:
        """Compute stats from a list of latency values (in ms)."""
        if not latencies:
            return cls()

        sorted_lats = sorted(latencies)
        n = len(sorted_lats)

        return cls(
            min_ms=sorted_lats[0],
            max_ms=sorted_lats[-1],
            mean_ms=sum(sorted_lats) / n,
            p50_ms=sorted_lats[n // 2],
            p95_ms=sorted_lats[int(n * 0.95)],
            p99_ms=sorted_lats[int(n * 0.99)],
        )


@dataclass
class ResourceUsage:
    """Resource usage during benchmark run.

    Attributes:
        peak_memory_mb: Peak memory usage in megabytes.
        total_time_s: Total wall-clock time in seconds.
        cases_per_second: Throughput.
    """

    peak_memory_mb: float = 0.0
    total_time_s: float = 0.0
    cases_per_second: float = 0.0


@dataclass
class CaseResult:
    """Result for a single benchmark case.

    Attributes:
        case_id: Identifier of the case.
        category: Category of the case.
        judge_result: The judge's evaluation.
        actual_output: What AXIMA produced.
        latency_ms: Time taken in milliseconds.
        abstained: Whether AXIMA abstained from answering.
    """

    case_id: str
    category: str
    judge_result: JudgeResult
    actual_output: str
    latency_ms: float
    abstained: bool = False


@dataclass
class BenchmarkReport:
    """Complete benchmark execution report.

    Attributes:
        manifest_version: Version of the manifest used.
        axima_version: Version of AXIMA under test.
        results: Individual case results.
        pass_rate: Overall pass rate (0.0 to 1.0).
        categories: Pass rate breakdown by category.
        failures: List of failed case IDs with explanations.
        abstentions: List of cases where AXIMA abstained.
        latency_stats: Latency distribution.
        resource_usage: Resource consumption.
        timestamp: ISO timestamp of the run.
    """

    manifest_version: str
    axima_version: str
    results: List[CaseResult]
    pass_rate: float
    categories: Dict[str, float]
    failures: List[Dict[str, str]]
    abstentions: List[str]
    latency_stats: LatencyStats
    resource_usage: ResourceUsage
    timestamp: str

    def to_dict(self) -> dict:
        """Serialize report to dictionary."""
        return {
            "manifest_version": self.manifest_version,
            "axima_version": self.axima_version,
            "pass_rate": self.pass_rate,
            "categories": self.categories,
            "failures": self.failures,
            "abstentions": self.abstentions,
            "latency_stats": {
                "min_ms": self.latency_stats.min_ms,
                "max_ms": self.latency_stats.max_ms,
                "mean_ms": self.latency_stats.mean_ms,
                "p50_ms": self.latency_stats.p50_ms,
                "p95_ms": self.latency_stats.p95_ms,
                "p99_ms": self.latency_stats.p99_ms,
            },
            "resource_usage": {
                "peak_memory_mb": self.resource_usage.peak_memory_mb,
                "total_time_s": self.resource_usage.total_time_s,
                "cases_per_second": self.resource_usage.cases_per_second,
            },
            "timestamp": self.timestamp,
            "total_cases": len(self.results),
            "passed": sum(1 for r in self.results if r.judge_result.passed),
            "failed": len(self.failures),
            "abstained": len(self.abstentions),
        }


class BenchmarkRunner:
    """Isolated benchmark runner with deterministic seeding.

    The runner is designed to be opaque to the active AXIMA runtime —
    it does not expose its cases, expected outputs, or evaluation
    logic to the system under test.
    """

    # Abstention markers - responses that indicate AXIMA chose not to answer
    ABSTENTION_MARKERS = [
        "unsupported",
        "i don't know",
        "cannot answer",
        "outside my capabilities",
        "no reliable answer",
        "insufficient information",
    ]

    def __init__(
        self,
        query_fn: AximaQueryFn,
        axima_version: str = "0.1.0",
        seed: Optional[int] = None,
    ) -> None:
        """Initialize the benchmark runner.

        Args:
            query_fn: Function that takes a query string and returns
                      AXIMA's response string.
            axima_version: Version string for the system under test.
            seed: Deterministic seed for reproducibility. If None, uses
                  current time.
        """
        self._query_fn = query_fn
        self._axima_version = axima_version
        self._seed = seed if seed is not None else int(time.time())
        self._rng = random.Random(self._seed)

        # Initialize judges
        self._judges = {
            JudgeType.EXACT: ExactJudge(),
            JudgeType.TOLERANCE: ToleranceJudge(),
            JudgeType.AST: ASTJudge(),
            JudgeType.PROOF: ProofJudge(),
            JudgeType.COMPILATION: CompilationJudge(),
            JudgeType.TEST: TestJudge(),
            JudgeType.SEMANTIC: SemanticJudge(),
        }

    def run_suite(
        self,
        manifest: BenchmarkManifest,
        categories: Optional[List[str]] = None,
        shuffle: bool = True,
    ) -> BenchmarkReport:
        """Run the full benchmark suite.

        Args:
            manifest: The benchmark manifest to execute.
            categories: If set, only run cases from these categories.
            shuffle: If True, randomize case order (with seed).

        Returns:
            BenchmarkReport with all results.
        """
        start_time = time.time()

        # Filter cases
        cases = list(manifest.cases)
        if categories:
            cases = [c for c in cases if c.category in categories]

        # Shuffle for isolation (prevents order-dependent behavior)
        if shuffle:
            self._rng.shuffle(cases)

        # Execute each case
        results: List[CaseResult] = []
        for case in cases:
            result = self.run_single(case)
            results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        return self._compile_report(manifest, results, total_time)

    def run_single(self, case: BenchmarkCase) -> CaseResult:
        """Run a single benchmark case.

        Args:
            case: The benchmark case to execute.

        Returns:
            CaseResult with judge evaluation.
        """
        # Time the query
        start = time.time()
        try:
            actual_output = self._query_fn(case.input)
        except Exception as e:
            actual_output = f"[ERROR: {type(e).__name__}: {e}]"
        elapsed_ms = (time.time() - start) * 1000

        # Check for abstention
        abstained = self._is_abstention(actual_output)

        # Judge the result
        if abstained:
            judge_result = JudgeResult(
                passed=False,
                score=0.0,
                explanation="AXIMA abstained from answering.",
                judge_name="Abstention",
            )
        else:
            judge_result = self._evaluate(case, actual_output)

        return CaseResult(
            case_id=case.id,
            category=case.category,
            judge_result=judge_result,
            actual_output=actual_output,
            latency_ms=elapsed_ms,
            abstained=abstained,
        )

    def compare_with_baseline(
        self,
        manifest: BenchmarkManifest,
        baseline_results: List[CaseResult],
    ) -> Dict[str, Any]:
        """Compare current results with a baseline run.

        Args:
            manifest: The benchmark manifest.
            baseline_results: Results from a previous/baseline run.

        Returns:
            Dictionary with comparison metrics.
        """
        current_report = self.run_suite(manifest, shuffle=False)

        current_by_id = {r.case_id: r for r in current_report.results}
        baseline_by_id = {r.case_id: r for r in baseline_results}

        improvements: List[str] = []
        regressions: List[str] = []
        unchanged: List[str] = []

        for case_id in current_by_id:
            if case_id not in baseline_by_id:
                continue

            current_passed = current_by_id[case_id].judge_result.passed
            baseline_passed = baseline_by_id[case_id].judge_result.passed

            if current_passed and not baseline_passed:
                improvements.append(case_id)
            elif not current_passed and baseline_passed:
                regressions.append(case_id)
            else:
                unchanged.append(case_id)

        return {
            "improvements": improvements,
            "regressions": regressions,
            "unchanged": unchanged,
            "current_pass_rate": current_report.pass_rate,
            "regression_count": len(regressions),
            "improvement_count": len(improvements),
        }

    def generate_report(
        self,
        manifest: BenchmarkManifest,
        categories: Optional[List[str]] = None,
    ) -> BenchmarkReport:
        """Generate a full benchmark report.

        Alias for run_suite that emphasizes the report generation aspect.

        Args:
            manifest: The benchmark manifest.
            categories: Optional category filter.

        Returns:
            Complete BenchmarkReport.
        """
        return self.run_suite(manifest, categories=categories)

    def _evaluate(self, case: BenchmarkCase, actual_output: str) -> JudgeResult:
        """Evaluate a case output using the appropriate judge."""
        judge_type = case.judge_type

        # HUMAN judge type cannot be automated
        if judge_type == JudgeType.HUMAN:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation="Requires human evaluation.",
                judge_name="HumanJudge",
            )

        judge = self._judges.get(judge_type)
        if judge is None:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"No judge available for type: {judge_type.value}",
                judge_name="Unknown",
            )

        # Dispatch to appropriate judge method
        if judge_type == JudgeType.EXACT:
            return judge.judge(case.expected_output, actual_output)  # type: ignore[union-attr]
        elif judge_type == JudgeType.TOLERANCE:
            return judge.judge(case.expected_output, actual_output)  # type: ignore[union-attr]
        elif judge_type == JudgeType.AST:
            return judge.judge(case.expected_output, actual_output)  # type: ignore[union-attr]
        elif judge_type == JudgeType.PROOF:
            return judge.judge(case.expected_output, actual_output)  # type: ignore[union-attr]
        elif judge_type == JudgeType.COMPILATION:
            return judge.judge(actual_output, "python")  # type: ignore[union-attr]
        elif judge_type == JudgeType.TEST:
            return judge.judge(actual_output, case.expected_output)  # type: ignore[union-attr]
        elif judge_type == JudgeType.SEMANTIC:
            return judge.judge(case.expected_output, actual_output)  # type: ignore[union-attr]
        else:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Unhandled judge type: {judge_type.value}",
                judge_name="Unknown",
            )

    def _is_abstention(self, output: str) -> bool:
        """Check if the output indicates abstention."""
        lower_output = output.lower().strip()
        return any(marker in lower_output for marker in self.ABSTENTION_MARKERS)

    def _compile_report(
        self,
        manifest: BenchmarkManifest,
        results: List[CaseResult],
        total_time: float,
    ) -> BenchmarkReport:
        """Compile individual results into a complete report."""
        if not results:
            return BenchmarkReport(
                manifest_version=manifest.version,
                axima_version=self._axima_version,
                results=[],
                pass_rate=0.0,
                categories={},
                failures=[],
                abstentions=[],
                latency_stats=LatencyStats(),
                resource_usage=ResourceUsage(),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )

        # Compute pass rate
        passed_count = sum(1 for r in results if r.judge_result.passed)
        pass_rate = passed_count / len(results)

        # Category breakdown
        category_results: Dict[str, List[bool]] = {}
        for r in results:
            category_results.setdefault(r.category, []).append(
                r.judge_result.passed
            )
        categories = {
            cat: sum(passes) / len(passes)
            for cat, passes in category_results.items()
        }

        # Failures
        failures = [
            {
                "case_id": r.case_id,
                "category": r.category,
                "explanation": r.judge_result.explanation,
                "actual": r.actual_output[:200],
            }
            for r in results
            if not r.judge_result.passed and not r.abstained
        ]

        # Abstentions
        abstentions = [r.case_id for r in results if r.abstained]

        # Latency stats
        latencies = [r.latency_ms for r in results]
        latency_stats = LatencyStats.from_latencies(latencies)

        # Resource usage
        resource_usage = ResourceUsage(
            total_time_s=total_time,
            cases_per_second=len(results) / total_time if total_time > 0 else 0.0,
        )

        return BenchmarkReport(
            manifest_version=manifest.version,
            axima_version=self._axima_version,
            results=results,
            pass_rate=pass_rate,
            categories=categories,
            failures=failures,
            abstentions=abstentions,
            latency_stats=latency_stats,
            resource_usage=resource_usage,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )


# --- Functional API for running benchmarks end-to-end ---


def load_manifest_from_file(path: Path) -> BenchmarkManifest:
    """Load a BenchmarkManifest from a JSON file on disk.

    Args:
        path: Path to the manifest JSON file.

    Returns:
        Loaded BenchmarkManifest instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON or has wrong structure.
    """
    manager = ManifestManager(path)
    return manager.load()


def create_axima_query_fn() -> AximaQueryFn:
    """Create a query function that routes through the Axima API.

    Returns a callable that accepts a query string and returns
    the response string. For codegen queries, returns code output;
    for multilingual queries, returns detected language; otherwise
    returns the answer field.

    Returns:
        Function compatible with BenchmarkRunner's query_fn protocol.
    """
    from axima.api import Axima

    ax = Axima()

    def query_fn(query: str) -> str:
        # Detect category from query content heuristics
        lower = query.lower()

        # Code generation queries
        code_keywords = [
            "in python", "in javascript", "in java", "in c++",
            "in rust", "in go", "in typescript",
            "binary search", "quicksort", "fibonacci", "linked list",
            "stack", "queue", "merge sort", "bubble sort", "binary tree",
            "hash map", "dijkstra", "heap sort",
        ]
        if any(kw in lower for kw in code_keywords):
            response = ax.code(query)
            return response.code

        # General query
        response = ax.process(query)
        return response.answer

    return query_fn


def run_benchmarks(
    manifest_path: Path,
    categories: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
    seed: int = 42,
) -> BenchmarkReport:
    """Run the full benchmark suite end-to-end.

    This is the high-level entry point that:
    1. Loads cases from a manifest file
    2. Creates an Axima query function
    3. Runs all cases through BenchmarkRunner
    4. Saves the report to evals/reports/

    Args:
        manifest_path: Path to the manifest JSON.
        categories: Optional list of categories to filter.
        output_dir: Directory to save reports. If None, uses evals/reports/.
        seed: Random seed for deterministic execution order.

    Returns:
        Complete BenchmarkReport.
    """
    # Load manifest
    manifest = load_manifest_from_file(manifest_path)

    # Create query function
    query_fn = create_axima_query_fn()

    # Create runner
    runner = BenchmarkRunner(
        query_fn=query_fn,
        axima_version="0.1.0",
        seed=seed,
    )

    # Run suite
    report = runner.run_suite(manifest, categories=categories)

    # Save report
    if output_dir is None:
        # Default to evals/reports/ relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        output_dir = project_root / "evals" / "reports"

    output_dir.mkdir(parents=True, exist_ok=True)
    save_report(report, output_dir)

    return report


def save_report(report: BenchmarkReport, output_dir: Path) -> Dict[str, Path]:
    """Save a BenchmarkReport to JSON and Markdown files.

    Args:
        report: The report to save.
        output_dir: Directory to write report files.

    Returns:
        Dictionary mapping format names to file paths.
    """
    timestamp_str = report.timestamp.replace(":", "").replace("-", "").replace("T", "_").rstrip("Z")
    paths: Dict[str, Path] = {}

    # JSON report
    json_path = output_dir / f"benchmark_{timestamp_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
    paths["json"] = json_path

    # Markdown report
    md_path = output_dir / f"benchmark_{timestamp_str}.md"
    md_content = format_report_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    paths["markdown"] = md_path

    return paths


def format_report_markdown(report: BenchmarkReport) -> str:
    """Format a BenchmarkReport as readable Markdown.

    Args:
        report: The report to format.

    Returns:
        Markdown string.
    """
    lines: List[str] = []

    lines.append("# AXIMA Benchmark Report")
    lines.append("")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**AXIMA Version:** {report.axima_version}")
    lines.append(f"**Manifest Version:** {report.manifest_version}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Cases | {len(report.results)} |")
    lines.append(f"| Passed | {sum(1 for r in report.results if r.judge_result.passed)} |")
    lines.append(f"| Failed | {len(report.failures)} |")
    lines.append(f"| Abstained | {len(report.abstentions)} |")
    lines.append(f"| Pass Rate | {report.pass_rate:.1%} |")
    lines.append("")

    # Category breakdown
    lines.append("## Per-Category Results")
    lines.append("")
    lines.append("| Category | Pass Rate |")
    lines.append("|----------|-----------|")
    for cat, rate in sorted(report.categories.items()):
        lines.append(f"| {cat} | {rate:.1%} |")
    lines.append("")

    # Latency
    lines.append("## Latency")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Min | {report.latency_stats.min_ms:.1f}ms |")
    lines.append(f"| Mean | {report.latency_stats.mean_ms:.1f}ms |")
    lines.append(f"| P50 | {report.latency_stats.p50_ms:.1f}ms |")
    lines.append(f"| P95 | {report.latency_stats.p95_ms:.1f}ms |")
    lines.append(f"| P99 | {report.latency_stats.p99_ms:.1f}ms |")
    lines.append(f"| Max | {report.latency_stats.max_ms:.1f}ms |")
    lines.append("")

    # Resource usage
    lines.append("## Resources")
    lines.append("")
    lines.append(f"- Total time: {report.resource_usage.total_time_s:.2f}s")
    lines.append(f"- Throughput: {report.resource_usage.cases_per_second:.1f} cases/sec")
    lines.append("")

    # Failures
    if report.failures:
        lines.append("## Failures")
        lines.append("")
        for f in report.failures[:25]:
            lines.append(f"- **{f['case_id']}** ({f['category']}): {f['explanation']}")
            if f.get("actual"):
                lines.append(f"  - Actual: `{f['actual'][:80]}`")
        lines.append("")

    # Abstentions
    if report.abstentions:
        lines.append("## Abstentions")
        lines.append("")
        for case_id in report.abstentions:
            lines.append(f"- {case_id}")
        lines.append("")

    return "\n".join(lines)
