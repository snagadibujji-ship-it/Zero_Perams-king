#!/usr/bin/env python3
"""AXIMA Cosmic Eval Runner — Benchmarks against the new architecture.

Runs eval cases through the Axima API using proper judges (no substring matching).
Generates detailed reports in both JSON and Markdown formats.

Usage:
    python evals/run_cosmic_evals.py
    python evals/run_cosmic_evals.py --category math
    python evals/run_cosmic_evals.py --category codegen --output evals/reports/
    python evals/run_cosmic_evals.py --manifest evals/public/manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from axima.api import Axima, AximaResponse, CodeResponse
from axima.benchmarks.judges import (
    ExactJudge,
    ToleranceJudge,
    ASTJudge,
    CompilationJudge,
    SemanticJudge,
    JudgeResult,
)
from axima.benchmarks.manifest import (
    BenchmarkCase,
    BenchmarkManifest,
    ManifestManager,
    JudgeType,
    Difficulty,
)


@dataclass
class CaseOutcome:
    """Result of evaluating a single case."""

    case_id: str
    category: str
    input: str
    expected: str
    actual: str
    passed: bool
    abstained: bool
    score: float
    judge_name: str
    explanation: str
    latency_ms: float
    error: Optional[str] = None


@dataclass
class CategoryStats:
    """Statistics for a single category."""

    category: str
    total: int
    passed: int
    failed: int
    abstained: int
    pass_rate: float
    mean_latency_ms: float


@dataclass
class LatencyReport:
    """Latency statistics across all cases."""

    min_ms: float
    max_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float

    @classmethod
    def from_latencies(cls, latencies: List[float]) -> "LatencyReport":
        if not latencies:
            return cls(0, 0, 0, 0, 0, 0)
        s = sorted(latencies)
        n = len(s)
        return cls(
            min_ms=s[0],
            max_ms=s[-1],
            mean_ms=sum(s) / n,
            p50_ms=s[n // 2],
            p95_ms=s[min(int(n * 0.95), n - 1)],
            p99_ms=s[min(int(n * 0.99), n - 1)],
        )


@dataclass
class EvalReport:
    """Complete evaluation report."""

    timestamp: str
    axima_version: str
    manifest_version: str
    total_cases: int
    passed: int
    failed: int
    abstained: int
    pass_rate: float
    category_stats: List[CategoryStats]
    latency: LatencyReport
    outcomes: List[CaseOutcome]
    failures: List[CaseOutcome]
    category_filter: Optional[str] = None


# --- Abstention detection ---

ABSTENTION_MARKERS = [
    "unsupported",
    "i don't know",
    "cannot answer",
    "outside my capabilities",
    "no reliable answer",
    "insufficient information",
    "not initialized",
    "engine not initialized",
]


def is_abstention(output: str) -> bool:
    """Check if the output indicates AXIMA abstained."""
    lower = output.lower().strip()
    return any(marker in lower for marker in ABSTENTION_MARKERS)


# --- Judge dispatch ---


def get_judge_for_case(case: BenchmarkCase) -> Any:
    """Return the appropriate judge instance for a case."""
    judges = {
        JudgeType.EXACT: ExactJudge(),
        JudgeType.TOLERANCE: ToleranceJudge(),
        JudgeType.AST: ASTJudge(),
        JudgeType.COMPILATION: CompilationJudge(),
        JudgeType.SEMANTIC: SemanticJudge(),
    }
    return judges.get(case.judge_type)


def evaluate_case(case: BenchmarkCase, actual: str) -> JudgeResult:
    """Evaluate a case output using the appropriate judge."""
    judge = get_judge_for_case(case)

    if judge is None:
        return JudgeResult(
            passed=False,
            score=0.0,
            explanation=f"No judge for type: {case.judge_type.value}",
            judge_name="Unknown",
        )

    if case.judge_type == JudgeType.EXACT:
        return judge.judge(case.expected_output, actual)
    elif case.judge_type == JudgeType.TOLERANCE:
        return judge.judge(case.expected_output, actual, tolerance=0.01)
    elif case.judge_type == JudgeType.AST:
        return judge.judge(case.expected_output, actual)
    elif case.judge_type == JudgeType.COMPILATION:
        # For codegen, judge compilation of actual output
        language = "python"
        if "javascript" in case.input.lower() or "js" in case.input.lower():
            language = "javascript"
        return judge.judge(actual, language)
    elif case.judge_type == JudgeType.SEMANTIC:
        return judge.judge(case.expected_output, actual)
    else:
        return JudgeResult(
            passed=False,
            score=0.0,
            explanation=f"Unhandled judge type: {case.judge_type.value}",
            judge_name="Unknown",
        )


# --- Main execution ---


def load_manifest(manifest_path: Path) -> BenchmarkManifest:
    """Load benchmark manifest from file."""
    manager = ManifestManager(manifest_path)
    return manager.load()


def load_from_legacy_cases(evals_dir: Path) -> BenchmarkManifest:
    """Fall back to loading from legacy cases.json files."""
    cases: List[BenchmarkCase] = []
    case_id_counter = 0

    # Math cases
    math_path = evals_dir / "math" / "cases.json"
    if math_path.exists():
        with open(math_path) as f:
            raw = json.load(f)
        for item in raw:
            case_id_counter += 1
            expected = item["expected"]
            if isinstance(expected, list):
                expected_str = expected[0]
            else:
                expected_str = str(expected)
            cases.append(BenchmarkCase(
                id=f"math_{case_id_counter:03d}",
                category="math",
                input=item["input"],
                expected_output=expected_str,
                judge_type=JudgeType.EXACT,
                difficulty=Difficulty.EASY,
            ))

    # Multilingual cases
    multi_path = evals_dir / "multilingual" / "cases.json"
    if multi_path.exists():
        with open(multi_path) as f:
            raw = json.load(f)
        for item in raw:
            case_id_counter += 1
            cases.append(BenchmarkCase(
                id=f"multi_{case_id_counter:03d}",
                category="multilingual",
                input=item["input"],
                expected_output=str(item["expected"]),
                judge_type=JudgeType.EXACT,
                difficulty=Difficulty.MEDIUM,
            ))

    # Codegen cases
    code_path = evals_dir / "codegen" / "cases.json"
    if code_path.exists():
        with open(code_path) as f:
            raw = json.load(f)
        for item in raw:
            case_id_counter += 1
            cases.append(BenchmarkCase(
                id=f"codegen_{case_id_counter:03d}",
                category="codegen",
                input=item["input"],
                expected_output=str(item["expected"][0]) if isinstance(item["expected"], list) else str(item["expected"]),
                judge_type=JudgeType.COMPILATION,
                difficulty=Difficulty.EASY,
            ))

    return BenchmarkManifest(
        version="legacy-1.0.0",
        cases=cases,
        frozen_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


def run_case(ax: Axima, case: BenchmarkCase) -> CaseOutcome:
    """Run a single eval case through the Axima API."""
    start = time.time()
    error = None

    try:
        if case.category == "codegen":
            response = ax.code(case.input)
            actual = response.code
        elif case.category == "multilingual":
            response = ax.process(case.input)
            actual = response.language
        else:
            response = ax.process(case.input)
            actual = response.answer
    except Exception as exc:
        actual = f"[ERROR: {type(exc).__name__}: {exc}]"
        error = str(exc)

    elapsed_ms = (time.time() - start) * 1000

    # Check abstention
    abstained = is_abstention(actual)

    if abstained:
        judge_result = JudgeResult(
            passed=False,
            score=0.0,
            explanation="AXIMA abstained from answering.",
            judge_name="Abstention",
        )
    elif error:
        judge_result = JudgeResult(
            passed=False,
            score=0.0,
            explanation=f"Execution error: {error}",
            judge_name="Error",
        )
    else:
        judge_result = evaluate_case(case, actual)

    return CaseOutcome(
        case_id=case.id,
        category=case.category,
        input=case.input,
        expected=case.expected_output,
        actual=actual[:500],
        passed=judge_result.passed,
        abstained=abstained,
        score=judge_result.score,
        judge_name=judge_result.judge_name,
        explanation=judge_result.explanation,
        latency_ms=elapsed_ms,
        error=error,
    )


def compile_report(
    outcomes: List[CaseOutcome],
    manifest: BenchmarkManifest,
    category_filter: Optional[str] = None,
) -> EvalReport:
    """Compile individual outcomes into a full report."""
    passed = sum(1 for o in outcomes if o.passed)
    failed = sum(1 for o in outcomes if not o.passed and not o.abstained)
    abstained = sum(1 for o in outcomes if o.abstained)
    total = len(outcomes)

    # Category breakdown
    cat_groups: Dict[str, List[CaseOutcome]] = {}
    for o in outcomes:
        cat_groups.setdefault(o.category, []).append(o)

    category_stats = []
    for cat, cat_outcomes in sorted(cat_groups.items()):
        cat_passed = sum(1 for o in cat_outcomes if o.passed)
        cat_failed = sum(1 for o in cat_outcomes if not o.passed and not o.abstained)
        cat_abstained = sum(1 for o in cat_outcomes if o.abstained)
        cat_total = len(cat_outcomes)
        cat_latencies = [o.latency_ms for o in cat_outcomes]
        category_stats.append(CategoryStats(
            category=cat,
            total=cat_total,
            passed=cat_passed,
            failed=cat_failed,
            abstained=cat_abstained,
            pass_rate=cat_passed / cat_total if cat_total > 0 else 0.0,
            mean_latency_ms=sum(cat_latencies) / len(cat_latencies) if cat_latencies else 0.0,
        ))

    # Latency
    latencies = [o.latency_ms for o in outcomes]
    latency_report = LatencyReport.from_latencies(latencies)

    # Failures
    failures = [o for o in outcomes if not o.passed]

    return EvalReport(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        axima_version="0.1.0",
        manifest_version=manifest.version,
        total_cases=total,
        passed=passed,
        failed=failed,
        abstained=abstained,
        pass_rate=passed / total if total > 0 else 0.0,
        category_stats=category_stats,
        latency=latency_report,
        outcomes=outcomes,
        failures=failures,
        category_filter=category_filter,
    )


# --- Output formatting ---


def report_to_json(report: EvalReport) -> dict:
    """Convert report to JSON-serializable dict."""
    return {
        "timestamp": report.timestamp,
        "axima_version": report.axima_version,
        "manifest_version": report.manifest_version,
        "total_cases": report.total_cases,
        "passed": report.passed,
        "failed": report.failed,
        "abstained": report.abstained,
        "pass_rate": round(report.pass_rate, 4),
        "category_filter": report.category_filter,
        "category_stats": [
            {
                "category": s.category,
                "total": s.total,
                "passed": s.passed,
                "failed": s.failed,
                "abstained": s.abstained,
                "pass_rate": round(s.pass_rate, 4),
                "mean_latency_ms": round(s.mean_latency_ms, 2),
            }
            for s in report.category_stats
        ],
        "latency": {
            "min_ms": round(report.latency.min_ms, 2),
            "max_ms": round(report.latency.max_ms, 2),
            "mean_ms": round(report.latency.mean_ms, 2),
            "p50_ms": round(report.latency.p50_ms, 2),
            "p95_ms": round(report.latency.p95_ms, 2),
            "p99_ms": round(report.latency.p99_ms, 2),
        },
        "outcomes": [
            {
                "case_id": o.case_id,
                "category": o.category,
                "input": o.input,
                "expected": o.expected,
                "actual": o.actual,
                "passed": o.passed,
                "abstained": o.abstained,
                "score": round(o.score, 4),
                "judge": o.judge_name,
                "explanation": o.explanation,
                "latency_ms": round(o.latency_ms, 2),
                "error": o.error,
            }
            for o in report.outcomes
        ],
        "failure_analysis": [
            {
                "case_id": f.case_id,
                "category": f.category,
                "input": f.input,
                "expected": f.expected,
                "actual": f.actual[:200],
                "explanation": f.explanation,
            }
            for f in report.failures[:20]
        ],
    }


def report_to_markdown(report: EvalReport) -> str:
    """Convert report to markdown format."""
    lines: List[str] = []

    lines.append("# AXIMA Cosmic Eval Report")
    lines.append("")
    lines.append(f"**Timestamp:** {report.timestamp}")
    lines.append(f"**AXIMA Version:** {report.axima_version}")
    lines.append(f"**Manifest Version:** {report.manifest_version}")
    if report.category_filter:
        lines.append(f"**Category Filter:** {report.category_filter}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Cases | {report.total_cases} |")
    lines.append(f"| Passed | {report.passed} |")
    lines.append(f"| Failed | {report.failed} |")
    lines.append(f"| Abstained | {report.abstained} |")
    lines.append(f"| Pass Rate | {report.pass_rate:.1%} |")
    lines.append("")

    # Category breakdown
    lines.append("## Per-Category Results")
    lines.append("")
    lines.append("| Category | Total | Passed | Failed | Abstained | Pass Rate | Avg Latency |")
    lines.append("|----------|-------|--------|--------|-----------|-----------|-------------|")
    for s in report.category_stats:
        lines.append(
            f"| {s.category} | {s.total} | {s.passed} | {s.failed} | "
            f"{s.abstained} | {s.pass_rate:.1%} | {s.mean_latency_ms:.1f}ms |"
        )
    lines.append("")

    # Latency
    lines.append("## Latency Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Min | {report.latency.min_ms:.1f}ms |")
    lines.append(f"| Max | {report.latency.max_ms:.1f}ms |")
    lines.append(f"| Mean | {report.latency.mean_ms:.1f}ms |")
    lines.append(f"| P50 | {report.latency.p50_ms:.1f}ms |")
    lines.append(f"| P95 | {report.latency.p95_ms:.1f}ms |")
    lines.append(f"| P99 | {report.latency.p99_ms:.1f}ms |")
    lines.append("")

    # Failure analysis
    if report.failures:
        lines.append("## Failure Analysis")
        lines.append("")
        for f in report.failures[:20]:
            lines.append(f"### {f.case_id} ({f.category})")
            lines.append(f"- **Input:** `{f.input}`")
            lines.append(f"- **Expected:** `{f.expected}`")
            lines.append(f"- **Actual:** `{f.actual[:100]}`")
            lines.append(f"- **Judge:** {f.judge_name}")
            lines.append(f"- **Explanation:** {f.explanation}")
            if f.abstained:
                lines.append(f"- **Status:** ABSTAINED")
            lines.append("")

    # Per-case results table
    lines.append("## All Cases")
    lines.append("")
    lines.append("| ID | Category | Input | Result | Score | Latency |")
    lines.append("|----|----------|-------|--------|-------|---------|")
    for o in report.outcomes:
        status = "✅" if o.passed else ("⏭️" if o.abstained else "❌")
        input_short = o.input[:40] + ("..." if len(o.input) > 40 else "")
        lines.append(
            f"| {o.case_id} | {o.category} | {input_short} | "
            f"{status} | {o.score:.2f} | {o.latency_ms:.1f}ms |"
        )
    lines.append("")

    return "\n".join(lines)


# --- CLI ---


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AXIMA Cosmic Eval Runner — benchmark against the new architecture"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to manifest JSON (defaults to evals/public/manifest.json)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter to a specific category (math, multilingual, codegen)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output directory for reports (defaults to evals/reports/)",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Only output JSON report (skip markdown)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-case results to stdout",
    )

    args = parser.parse_args()

    # Determine paths
    evals_dir = Path(__file__).resolve().parent
    manifest_path = args.manifest or (evals_dir / "public" / "manifest.json")
    output_dir = args.output or (evals_dir / "reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest
    print(f"{'═' * 60}")
    print(f"  AXIMA COSMIC EVAL RUNNER")
    print(f"{'═' * 60}")
    print()

    if manifest_path.exists():
        print(f"  Loading manifest: {manifest_path}")
        manifest = load_manifest(manifest_path)
    else:
        print(f"  Manifest not found at {manifest_path}, loading legacy cases...")
        manifest = load_from_legacy_cases(evals_dir)

    print(f"  Manifest version: {manifest.version}")
    print(f"  Total cases: {len(manifest.cases)}")

    # Filter by category
    cases = list(manifest.cases)
    if args.category:
        cases = [c for c in cases if c.category == args.category]
        print(f"  Category filter: {args.category} ({len(cases)} cases)")

    if not cases:
        print("\n  No cases to run. Exiting.")
        return 1

    # Initialize Axima
    print(f"\n  Initializing AXIMA engine...")
    ax = Axima()
    print(f"  Engine available: {ax.available}")
    print()

    # Run cases
    print(f"  Running {len(cases)} cases...")
    print(f"{'─' * 60}")

    outcomes: List[CaseOutcome] = []
    for i, case in enumerate(cases, 1):
        outcome = run_case(ax, case)
        outcomes.append(outcome)

        if args.verbose:
            status = "PASS" if outcome.passed else ("SKIP" if outcome.abstained else "FAIL")
            print(f"  [{i:3d}/{len(cases)}] {status:4s} {case.id:15s} ({outcome.latency_ms:.0f}ms)")

    # Compile report
    report = compile_report(outcomes, manifest, args.category)

    # Print summary
    print(f"{'─' * 60}")
    print()
    print(f"  RESULTS")
    print(f"  {'─' * 40}")
    print(f"  Total:     {report.total_cases}")
    print(f"  Passed:    {report.passed}")
    print(f"  Failed:    {report.failed}")
    print(f"  Abstained: {report.abstained}")
    print(f"  Pass Rate: {report.pass_rate:.1%}")
    print()

    for s in report.category_stats:
        print(f"  {s.category:15s} {s.passed}/{s.total} ({s.pass_rate:.0%}) avg {s.mean_latency_ms:.0f}ms")

    print()
    print(f"  Latency: min={report.latency.min_ms:.0f}ms "
          f"mean={report.latency.mean_ms:.0f}ms "
          f"p95={report.latency.p95_ms:.0f}ms "
          f"max={report.latency.max_ms:.0f}ms")

    # Save reports
    timestamp_str = time.strftime("%Y%m%d_%H%M%S")

    # JSON report
    json_path = output_dir / f"eval_{timestamp_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_to_json(report), f, indent=2, ensure_ascii=False)
    print(f"\n  JSON report: {json_path}")

    # Markdown report
    if not args.json_only:
        md_path = output_dir / f"eval_{timestamp_str}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_to_markdown(report))
        print(f"  Markdown report: {md_path}")

    print(f"\n{'═' * 60}")
    return 0 if report.pass_rate > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
