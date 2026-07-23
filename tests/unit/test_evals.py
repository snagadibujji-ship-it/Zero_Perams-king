"""Tests for the AXIMA eval runner and judges.

Tests cover:
- ExactJudge: exact string matching
- ToleranceJudge: numeric tolerance
- ASTJudge: code structure equivalence
- CompilationJudge: syntax validation
- SemanticJudge: meaning IR comparison
- BenchmarkRunner: suite execution
- Manifest loading and integrity
- Semantic equivalence judge (standalone)
- Report generation
"""

from __future__ import annotations

import json
import math
import tempfile
import time
from pathlib import Path
from typing import List

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from axima.benchmarks.judges import (
    ExactJudge,
    ToleranceJudge,
    ASTJudge,
    CompilationJudge,
    SemanticJudge,
    TestJudge,
    JudgeResult,
)
from axima.benchmarks.manifest import (
    BenchmarkCase,
    BenchmarkManifest,
    ManifestManager,
    JudgeType,
    Difficulty,
)
from axima.benchmarks.runner import (
    BenchmarkRunner,
    BenchmarkReport,
    CaseResult,
    LatencyStats,
    load_manifest_from_file,
    save_report,
    format_report_markdown,
)


# ─── ExactJudge Tests ────────────────────────────────────────────────


class TestExactJudge:
    """Tests for ExactJudge."""

    def setup_method(self):
        self.judge = ExactJudge()

    def test_exact_match_passes(self):
        result = self.judge.judge("42", "42")
        assert result.passed is True
        assert result.score == 1.0

    def test_exact_match_with_whitespace(self):
        result = self.judge.judge("  42  ", " 42 ")
        assert result.passed is True

    def test_mismatch_fails(self):
        result = self.judge.judge("42", "43")
        assert result.passed is False
        assert result.score == 0.0

    def test_substring_does_not_match(self):
        """Verify NO substring matching is used."""
        result = self.judge.judge("2", "x = 2")
        assert result.passed is False

    def test_case_sensitive(self):
        result = self.judge.judge("Hello", "hello")
        assert result.passed is False

    def test_empty_strings_match(self):
        result = self.judge.judge("", "")
        assert result.passed is True

    def test_multiline_exact(self):
        result = self.judge.judge("line1\nline2", "line1\nline2")
        assert result.passed is True

    def test_multiline_mismatch(self):
        result = self.judge.judge("line1\nline2", "line1\nline3")
        assert result.passed is False

    def test_judge_name(self):
        result = self.judge.judge("a", "b")
        assert result.judge_name == "ExactJudge"


# ─── ToleranceJudge Tests ────────────────────────────────────────────


class TestToleranceJudge:
    """Tests for ToleranceJudge."""

    def setup_method(self):
        self.judge = ToleranceJudge()

    def test_exact_numeric_match(self):
        result = self.judge.judge("3.14", "3.14")
        assert result.passed is True
        assert result.score == 1.0

    def test_within_default_tolerance(self):
        result = self.judge.judge("3.14", "3.1400001")
        assert result.passed is True

    def test_outside_tolerance(self):
        result = self.judge.judge("3.14", "3.20")
        assert result.passed is False

    def test_custom_tolerance(self):
        result = self.judge.judge("3.14", "3.15", tolerance=0.02)
        assert result.passed is True

    def test_relative_tolerance(self):
        result = self.judge.judge("100.0", "100.001", tolerance=0.001, relative=True)
        assert result.passed is True

    def test_non_numeric_expected(self):
        result = self.judge.judge("not a number", "42")
        assert result.passed is False

    def test_non_numeric_actual(self):
        result = self.judge.judge("42", "not a number")
        assert result.passed is False

    def test_zero_values(self):
        result = self.judge.judge("0", "0")
        assert result.passed is True

    def test_negative_numbers(self):
        result = self.judge.judge("-5.5", "-5.5")
        assert result.passed is True

    def test_judge_name(self):
        result = self.judge.judge("1", "2")
        assert result.judge_name == "ToleranceJudge"


# ─── ASTJudge Tests ──────────────────────────────────────────────────


class TestASTJudge:
    """Tests for ASTJudge (Python AST comparison)."""

    def setup_method(self):
        self.judge = ASTJudge()

    def test_identical_code(self):
        code = "def foo(x):\n    return x + 1"
        result = self.judge.judge(code, code)
        assert result.passed is True
        assert result.score == 1.0

    def test_whitespace_difference(self):
        code1 = "def foo(x):\n    return x+1"
        code2 = "def foo(x):\n    return x + 1"
        result = self.judge.judge(code1, code2)
        assert result.passed is True

    def test_different_logic(self):
        code1 = "def foo(x):\n    return x + 1"
        code2 = "def foo(x):\n    return x - 1"
        result = self.judge.judge(code1, code2)
        assert result.passed is False

    def test_syntax_error_in_expected(self):
        result = self.judge.judge("def foo(:", "def foo(x): pass")
        assert result.passed is False
        assert "syntax error" in result.explanation.lower()

    def test_syntax_error_in_actual(self):
        result = self.judge.judge("def foo(x): pass", "def foo(:")
        assert result.passed is False
        assert "syntax error" in result.explanation.lower()

    def test_structural_similarity_partial(self):
        code1 = "def foo(x):\n    return x + 1"
        code2 = "def bar(y):\n    return y * 2"
        result = self.judge.judge(code1, code2)
        # Should have some similarity score since both are function defs
        assert result.score > 0.0

    def test_judge_name(self):
        result = self.judge.judge("x = 1", "x = 2")
        assert result.judge_name == "ASTJudge"


# ─── CompilationJudge Tests ──────────────────────────────────────────


class TestCompilationJudge:
    """Tests for CompilationJudge."""

    def setup_method(self):
        self.judge = CompilationJudge()

    def test_valid_python(self):
        code = "def binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n    return -1"
        result = self.judge.judge(code, "python")
        assert result.passed is True

    def test_invalid_python(self):
        code = "def broken(\n    ?????"
        result = self.judge.judge(code, "python")
        assert result.passed is False

    def test_valid_javascript(self):
        code = "function mergeSort(arr) { return arr; }"
        result = self.judge.judge(code, "javascript")
        assert result.passed is True

    def test_unbalanced_javascript(self):
        code = "function broken(arr) { if (true {"
        result = self.judge.judge(code, "javascript")
        assert result.passed is False

    def test_unsupported_language(self):
        result = self.judge.judge("code", "brainfuck")
        assert result.passed is False
        assert "unsupported" in result.explanation.lower()

    def test_empty_python(self):
        result = self.judge.judge("", "python")
        assert result.passed is True  # Empty code is valid syntax

    def test_judge_name(self):
        result = self.judge.judge("x = 1", "python")
        assert result.judge_name == "CompilationJudge"


# ─── SemanticJudge Tests ─────────────────────────────────────────────


class TestSemanticJudge:
    """Tests for SemanticJudge (IR comparison)."""

    def setup_method(self):
        self.judge = SemanticJudge()

    def test_identical_ir(self):
        ir = json.dumps({"type": "number", "value": 42})
        result = self.judge.judge(ir, ir)
        assert result.passed is True
        assert result.score >= 0.95

    def test_equivalent_nested_ir(self):
        ir1 = json.dumps({"entities": [{"name": "x", "value": 3.14}]})
        ir2 = json.dumps({"entities": [{"name": "x", "value": 3.14}]})
        result = self.judge.judge(ir1, ir2)
        assert result.passed is True

    def test_different_ir(self):
        ir1 = json.dumps({"type": "number", "value": 42})
        ir2 = json.dumps({"type": "string", "value": "hello"})
        result = self.judge.judge(ir1, ir2)
        assert result.passed is False

    def test_numeric_tolerance_in_ir(self):
        ir1 = json.dumps({"value": 3.14159265})
        ir2 = json.dumps({"value": 3.14159266})
        result = self.judge.judge(ir1, ir2)
        assert result.passed is True

    def test_invalid_json_expected(self):
        result = self.judge.judge("not json", '{"x": 1}')
        assert result.passed is False

    def test_invalid_json_actual(self):
        result = self.judge.judge('{"x": 1}', "not json")
        assert result.passed is False

    def test_judge_name(self):
        result = self.judge.judge('{"x": 1}', '{"x": 2}')
        assert result.judge_name == "SemanticJudge"


# ─── Standalone Semantic Equivalence Judge Tests ─────────────────────


class TestSemanticEquivalenceJudge:
    """Tests for the standalone semantic equivalence judge (evals/judges/semantic.py)."""

    def setup_method(self):
        evals_path = str(Path(__file__).resolve().parent.parent.parent / "evals")
        if evals_path not in sys.path:
            sys.path.insert(0, evals_path)
        from judges.semantic import SemanticEquivalenceJudge
        self.judge = SemanticEquivalenceJudge()

    def test_exact_match(self):
        result = self.judge.judge("42", "42")
        assert result.passed is True
        assert result.score == 1.0

    def test_numeric_equivalence(self):
        result = self.judge.judge("3.14", "3.14")
        assert result.passed is True

    def test_numeric_tolerance(self):
        result = self.judge.judge("3.14159", "3.14160")
        assert result.passed is True

    def test_expression_equivalence_superscript(self):
        result = self.judge.judge("3x^2", "3x²")
        assert result.passed is True

    def test_expression_equivalence_multiplication(self):
        result = self.judge.judge("3x^2", "3*x^2")
        assert result.passed is True

    def test_set_equivalence(self):
        result = self.judge.judge("2, -2", "-2, 2")
        assert result.passed is True

    def test_no_substring_match(self):
        """Verify semantic judge does NOT do substring matching."""
        result = self.judge.judge("2", "The answer is 2 and more text here")
        # Should fail because this is not semantic equivalence
        assert result.passed is False

    def test_completely_different(self):
        result = self.judge.judge("42", "hello world")
        assert result.passed is False
        assert result.score < 0.5

    def test_ir_comparison(self):
        expected_ir = {"type": "number", "value": 42}
        actual_ir = {"type": "number", "value": 42}
        result = self.judge.judge_with_ir(expected_ir, actual_ir)
        assert result.passed is True

    def test_ir_comparison_numeric_tolerance(self):
        expected_ir = {"value": 3.14159}
        actual_ir = {"value": 3.14160}
        result = self.judge.judge_with_ir(expected_ir, actual_ir)
        assert result.passed is True


# ─── BenchmarkManifest Tests ─────────────────────────────────────────


class TestBenchmarkManifest:
    """Tests for manifest loading, saving, and integrity."""

    def test_case_serialization_roundtrip(self):
        case = BenchmarkCase(
            id="test_001",
            category="math",
            input="what is 2 + 2",
            expected_output="4",
            judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )
        d = case.to_dict()
        restored = BenchmarkCase.from_dict(d)
        assert restored == case

    def test_manifest_hash_stable(self):
        cases = [
            BenchmarkCase(
                id="math_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="")
        h1 = manifest.compute_hash()
        h2 = manifest.compute_hash()
        assert h1 == h2

    def test_manifest_hash_changes_on_modification(self):
        cases1 = [
            BenchmarkCase(
                id="math_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        cases2 = [
            BenchmarkCase(
                id="math_001", category="math", input="1+1",
                expected_output="3", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        m1 = BenchmarkManifest(version="1.0.0", cases=cases1, frozen_at="")
        m2 = BenchmarkManifest(version="1.0.0", cases=cases2, frozen_at="")
        assert m1.compute_hash() != m2.compute_hash()

    def test_manifest_save_and_load(self):
        cases = [
            BenchmarkCase(
                id="math_001", category="math", input="2+2",
                expected_output="4", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="2026-01-01T00:00:00Z")
        manifest.hash = manifest.compute_hash()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(manifest.to_dict(), f)
            tmp_path = Path(f.name)

        try:
            loaded = load_manifest_from_file(tmp_path)
            assert loaded.version == "1.0.0"
            assert len(loaded.cases) == 1
            assert loaded.cases[0].id == "math_001"
            assert loaded.hash == manifest.hash
        finally:
            tmp_path.unlink()

    def test_integrity_validation(self):
        cases = [
            BenchmarkCase(
                id="math_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="")
        manager = ManifestManager()
        manager._manifest = manifest

        # Unfrozen manifest has no hash
        assert manager.validate_integrity() is False

        # Freeze and validate
        manager.freeze()
        assert manager.validate_integrity() is True

    def test_contamination_detection(self):
        cases = [
            BenchmarkCase(
                id="math_001", category="math", input="what is sqrt(144)",
                expected_output="12", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
            BenchmarkCase(
                id="math_002", category="math", input="what is 2+2",
                expected_output="4", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="")
        manager = ManifestManager()
        manager._manifest = manifest

        # "12" is only 2 chars, won't trigger (threshold is >3)
        # "4" is only 1 char, won't trigger either
        source = "return 12"
        contaminated = manager.detect_contamination(source)
        assert contaminated == []  # Both expected outputs are <=3 chars

        # Longer expected output
        cases_long = [
            BenchmarkCase(
                id="code_001", category="codegen", input="fibonacci",
                expected_output="def fibonacci(n):", judge_type=JudgeType.COMPILATION,
                difficulty=Difficulty.EASY,
            ),
        ]
        manifest_long = BenchmarkManifest(version="1.0.0", cases=cases_long, frozen_at="")
        manager._manifest = manifest_long
        source_contaminated = "patterns = {'fibonacci': 'def fibonacci(n):'}"
        contaminated = manager.detect_contamination(source_contaminated)
        assert "code_001" in contaminated


# ─── BenchmarkRunner Tests ───────────────────────────────────────────


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    def _make_manifest(self, cases: List[BenchmarkCase]) -> BenchmarkManifest:
        return BenchmarkManifest(
            version="test-1.0.0",
            cases=cases,
            frozen_at="2026-01-01T00:00:00Z",
        )

    def test_run_single_exact_pass(self):
        """Test running a single case that passes."""
        case = BenchmarkCase(
            id="test_001", category="math", input="what is 2+2",
            expected_output="4", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )

        def query_fn(q: str) -> str:
            return "4"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        result = runner.run_single(case)

        assert result.case_id == "test_001"
        assert result.judge_result.passed is True
        assert result.latency_ms > 0

    def test_run_single_exact_fail(self):
        """Test running a single case that fails."""
        case = BenchmarkCase(
            id="test_002", category="math", input="what is 2+2",
            expected_output="4", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )

        def query_fn(q: str) -> str:
            return "5"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        result = runner.run_single(case)

        assert result.judge_result.passed is False

    def test_run_single_abstention(self):
        """Test that abstention is detected."""
        case = BenchmarkCase(
            id="test_003", category="math", input="what is 2+2",
            expected_output="4", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )

        def query_fn(q: str) -> str:
            return "I don't know the answer"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        result = runner.run_single(case)

        assert result.abstained is True
        assert result.judge_result.passed is False

    def test_run_suite(self):
        """Test running a full suite."""
        cases = [
            BenchmarkCase(
                id=f"test_{i:03d}", category="math",
                input=f"what is {i}+{i}",
                expected_output=str(i + i),
                judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            )
            for i in range(1, 6)
        ]
        manifest = self._make_manifest(cases)

        def query_fn(q: str) -> str:
            # Parse "what is X+X" and return 2X
            import re
            m = re.search(r"what is (\d+)\+(\d+)", q)
            if m:
                return str(int(m.group(1)) + int(m.group(2)))
            return "unknown"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest)

        assert report.pass_rate == 1.0
        assert len(report.results) == 5
        assert len(report.failures) == 0
        assert len(report.abstentions) == 0

    def test_run_suite_with_category_filter(self):
        """Test category filtering in run_suite."""
        cases = [
            BenchmarkCase(
                id="math_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
            BenchmarkCase(
                id="code_001", category="codegen", input="hello world in python",
                expected_output="print('hello')", judge_type=JudgeType.COMPILATION,
                difficulty=Difficulty.EASY,
            ),
        ]
        manifest = self._make_manifest(cases)

        def query_fn(q: str) -> str:
            return "2"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest, categories=["math"])

        assert len(report.results) == 1
        assert report.results[0].case_id == "math_001"

    def test_run_suite_handles_errors(self):
        """Test that exceptions in query_fn are handled gracefully."""
        cases = [
            BenchmarkCase(
                id="test_001", category="math", input="crash",
                expected_output="4", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = self._make_manifest(cases)

        def query_fn(q: str) -> str:
            raise RuntimeError("Engine crashed!")

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest)

        assert report.pass_rate == 0.0
        assert len(report.results) == 1
        # Should not raise, should capture the error

    def test_latency_stats(self):
        """Test latency statistics computation."""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        stats = LatencyStats.from_latencies(latencies)

        assert stats.min_ms == 10.0
        assert stats.max_ms == 50.0
        assert stats.mean_ms == 30.0
        assert stats.p50_ms == 30.0

    def test_latency_stats_empty(self):
        """Test latency stats with no data."""
        stats = LatencyStats.from_latencies([])
        assert stats.min_ms == 0.0
        assert stats.max_ms == 0.0

    def test_report_to_dict(self):
        """Test report serialization."""
        cases = [
            BenchmarkCase(
                id="test_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = self._make_manifest(cases)

        def query_fn(q: str) -> str:
            return "2"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest)
        d = report.to_dict()

        assert "pass_rate" in d
        assert "categories" in d
        assert "latency_stats" in d
        assert "timestamp" in d
        assert d["passed"] == 1


# ─── Report Generation Tests ─────────────────────────────────────────


class TestReportGeneration:
    """Tests for report saving and formatting."""

    def test_save_report_creates_files(self):
        """Test that save_report creates JSON and Markdown files."""
        cases = [
            BenchmarkCase(
                id="test_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="")

        def query_fn(q: str) -> str:
            return "2"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest)

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = save_report(report, Path(tmpdir))
            assert "json" in paths
            assert "markdown" in paths
            assert paths["json"].exists()
            assert paths["markdown"].exists()

            # Verify JSON is valid
            with open(paths["json"]) as f:
                data = json.load(f)
            assert data["passed"] == 1

            # Verify Markdown has content
            with open(paths["markdown"]) as f:
                md = f.read()
            assert "# AXIMA Benchmark Report" in md

    def test_format_report_markdown(self):
        """Test markdown formatting."""
        cases = [
            BenchmarkCase(
                id="test_001", category="math", input="1+1",
                expected_output="2", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
        ]
        manifest = BenchmarkManifest(version="1.0.0", cases=cases, frozen_at="")

        def query_fn(q: str) -> str:
            return "2"

        runner = BenchmarkRunner(query_fn=query_fn, seed=42)
        report = runner.run_suite(manifest)

        md = format_report_markdown(report)
        assert "## Summary" in md
        assert "## Per-Category Results" in md
        assert "## Latency" in md
        assert "Pass Rate" in md


# ─── Integration: Tolerance Judge with real math ─────────────────────


class TestToleranceJudgeIntegration:
    """Integration tests for tolerance judge with realistic values."""

    def setup_method(self):
        self.judge = ToleranceJudge()

    def test_pi_approximation(self):
        result = self.judge.judge("3.14", "3.14159", tolerance=0.01)
        assert result.passed is True

    def test_e_approximation(self):
        result = self.judge.judge("2.71", "2.71828", tolerance=0.01)
        assert result.passed is True

    def test_large_number(self):
        result = self.judge.judge("1000000", "1000001", tolerance=2.0)
        assert result.passed is True

    def test_very_small_difference(self):
        result = self.judge.judge("0.000001", "0.000002", tolerance=1e-8)
        assert result.passed is False


# ─── Run all tests ───────────────────────────────────────────────────

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
