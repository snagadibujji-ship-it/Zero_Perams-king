"""Unit tests for the AXIMA benchmark system.

Tests manifest management, judges, runner, and immune system.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from typing import Dict, List

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from axima.benchmarks.manifest import (
    BenchmarkCase,
    BenchmarkManifest,
    ManifestManager,
    JudgeType,
    Difficulty,
)
from axima.benchmarks.judges import (
    JudgeResult,
    ExactJudge,
    ToleranceJudge,
    ASTJudge,
    ProofJudge,
    CompilationJudge,
    TestJudge,
    SemanticJudge,
)
from axima.benchmarks.runner import (
    BenchmarkRunner,
    BenchmarkReport,
    LatencyStats,
    CaseResult,
)
from axima.benchmarks.immune_system import (
    BenchmarkImmuneSystem,
    ContaminationReport,
)


# ============================================================
# Manifest Tests
# ============================================================


class TestBenchmarkCase:
    """Tests for BenchmarkCase dataclass."""

    def test_create_case(self):
        case = BenchmarkCase(
            id="test_001",
            category="math",
            input="what is 2+2",
            expected_output="4",
            judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )
        assert case.id == "test_001"
        assert case.category == "math"
        assert case.hidden is False
        assert case.source == "manual"

    def test_case_serialization(self):
        case = BenchmarkCase(
            id="test_002",
            category="physics",
            input="F=ma, find F",
            expected_output="10",
            judge_type=JudgeType.TOLERANCE,
            difficulty=Difficulty.MEDIUM,
            hidden=True,
            source="generated",
        )
        d = case.to_dict()
        assert d["id"] == "test_002"
        assert d["judge_type"] == "tolerance"
        assert d["hidden"] is True

        restored = BenchmarkCase.from_dict(d)
        assert restored == case

    def test_case_is_frozen(self):
        case = BenchmarkCase(
            id="x", category="y", input="z",
            expected_output="w", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        with pytest.raises(AttributeError):
            case.id = "new_id"  # type: ignore[misc]


class TestBenchmarkManifest:
    """Tests for BenchmarkManifest."""

    def _make_manifest(self, n: int = 3) -> BenchmarkManifest:
        cases = [
            BenchmarkCase(
                id=f"case_{i:03d}",
                category="math",
                input=f"question {i}",
                expected_output=f"answer {i}",
                judge_type=JudgeType.EXACT,
                difficulty=Difficulty.EASY,
            )
            for i in range(n)
        ]
        return BenchmarkManifest(
            version="1.0.0",
            cases=cases,
            frozen_at="",
        )

    def test_compute_hash_deterministic(self):
        m = self._make_manifest()
        h1 = m.compute_hash()
        h2 = m.compute_hash()
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_hash_changes_with_content(self):
        m1 = self._make_manifest(3)
        m2 = self._make_manifest(4)
        assert m1.compute_hash() != m2.compute_hash()

    def test_serialization_roundtrip(self):
        m = self._make_manifest()
        m.hash = m.compute_hash()
        d = m.to_dict()
        restored = BenchmarkManifest.from_dict(d)
        assert restored.version == m.version
        assert len(restored.cases) == len(m.cases)
        assert restored.hash == m.hash


class TestManifestManager:
    """Tests for ManifestManager."""

    def test_add_case(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="new_001", category="math", input="1+1",
            expected_output="2", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )
        mgr.add_case(case)
        assert mgr.manifest is not None
        assert len(mgr.manifest.cases) == 1

    def test_duplicate_case_rejected(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="dup", category="math", input="x",
            expected_output="y", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case)
        with pytest.raises(ValueError, match="Duplicate"):
            mgr.add_case(case)

    def test_freeze_sets_hash_and_timestamp(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="f_001", category="math", input="q",
            expected_output="a", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case)
        frozen = mgr.freeze()
        assert frozen.hash != ""
        assert frozen.frozen_at != ""

    def test_cannot_add_to_frozen(self):
        mgr = ManifestManager()
        case1 = BenchmarkCase(
            id="c1", category="math", input="q",
            expected_output="a", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case1)
        mgr.freeze()
        case2 = BenchmarkCase(
            id="c2", category="math", input="q2",
            expected_output="a2", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        with pytest.raises(ValueError, match="frozen"):
            mgr.add_case(case2)

    def test_validate_integrity_passes(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="v_001", category="math", input="q",
            expected_output="a", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case)
        mgr.freeze()
        assert mgr.validate_integrity() is True

    def test_validate_integrity_fails_on_tamper(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="v_002", category="math", input="q",
            expected_output="a_long_answer_here", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case)
        mgr.freeze()
        # Tamper with hash
        mgr.manifest.hash = "tampered"  # type: ignore[union-attr]
        assert mgr.validate_integrity() is False

    def test_detect_contamination(self):
        mgr = ManifestManager()
        case = BenchmarkCase(
            id="c_001", category="math", input="q",
            expected_output="very_specific_long_answer_42",
            judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        mgr.add_case(case)
        source = "if query == 'q': return 'very_specific_long_answer_42'"
        contaminated = mgr.detect_contamination(source)
        assert "c_001" in contaminated

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            mgr = ManifestManager(manifest_path=path)
            case = BenchmarkCase(
                id="sl_001", category="math", input="q",
                expected_output="a", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.EASY,
            )
            mgr.add_case(case)
            mgr.freeze()
            mgr.save()

            mgr2 = ManifestManager(manifest_path=path)
            loaded = mgr2.load()
            assert loaded.version == mgr.manifest.version
            assert len(loaded.cases) == 1
            assert mgr2.validate_integrity() is True


# ============================================================
# Judge Tests
# ============================================================


class TestExactJudge:
    """Tests for ExactJudge."""

    def test_exact_match(self):
        judge = ExactJudge()
        result = judge.judge("hello", "hello")
        assert result.passed is True
        assert result.score == 1.0

    def test_whitespace_stripped(self):
        judge = ExactJudge()
        result = judge.judge("  hello  ", "hello")
        assert result.passed is True

    def test_mismatch(self):
        judge = ExactJudge()
        result = judge.judge("hello", "world")
        assert result.passed is False
        assert result.score == 0.0
        assert "Mismatch" in result.explanation

    def test_case_sensitive(self):
        judge = ExactJudge()
        result = judge.judge("Hello", "hello")
        assert result.passed is False

    def test_judge_name(self):
        judge = ExactJudge()
        result = judge.judge("a", "a")
        assert result.judge_name == "ExactJudge"


class TestToleranceJudge:
    """Tests for ToleranceJudge."""

    def test_within_tolerance(self):
        judge = ToleranceJudge()
        result = judge.judge("3.14", "3.14000001")
        assert result.passed is True

    def test_outside_tolerance(self):
        judge = ToleranceJudge()
        result = judge.judge("3.14", "4.0", tolerance=0.01)
        assert result.passed is False

    def test_relative_tolerance(self):
        judge = ToleranceJudge()
        result = judge.judge("100", "101", tolerance=0.02, relative=True)
        assert result.passed is True  # 1% diff < 2% tolerance

    def test_non_numeric_expected(self):
        judge = ToleranceJudge()
        result = judge.judge("not_a_number", "3.14")
        assert result.passed is False
        assert "not numeric" in result.explanation

    def test_non_numeric_actual(self):
        judge = ToleranceJudge()
        result = judge.judge("3.14", "not_a_number")
        assert result.passed is False


class TestASTJudge:
    """Tests for ASTJudge."""

    def test_equivalent_code(self):
        judge = ASTJudge()
        code1 = "x = 1 + 2"
        code2 = "x = 1 + 2"
        result = judge.judge(code1, code2)
        assert result.passed is True

    def test_different_formatting(self):
        judge = ASTJudge()
        code1 = "x=1+2"
        code2 = "x = 1 + 2"
        result = judge.judge(code1, code2)
        assert result.passed is True

    def test_different_logic(self):
        judge = ASTJudge()
        code1 = "x = 1 + 2"
        code2 = "x = 3 * 4"
        result = judge.judge(code1, code2)
        assert result.passed is False

    def test_syntax_error_in_expected(self):
        judge = ASTJudge()
        result = judge.judge("def (broken", "x = 1")
        assert result.passed is False
        assert "syntax error" in result.explanation.lower()

    def test_syntax_error_in_actual(self):
        judge = ASTJudge()
        result = judge.judge("x = 1", "def (broken")
        assert result.passed is False


class TestProofJudge:
    """Tests for ProofJudge."""

    def test_valid_proof(self):
        judge = ProofJudge()
        claim = "B"
        derivation = json.dumps([
            {"rule": "given", "premises": [], "conclusion": "A"},
            {"rule": "given", "premises": [], "conclusion": "A implies B"},
            {"rule": "modus_ponens", "premises": ["A", "A implies B"], "conclusion": "B"},
        ])
        result = judge.judge(claim, derivation)
        assert result.passed is True
        assert result.score == 1.0

    def test_invalid_json(self):
        judge = ProofJudge()
        result = judge.judge("X", "not valid json")
        assert result.passed is False

    def test_empty_derivation(self):
        judge = ProofJudge()
        result = judge.judge("X", "[]")
        assert result.passed is False

    def test_unestablished_premise(self):
        judge = ProofJudge()
        derivation = json.dumps([
            {"rule": "modus_ponens", "premises": ["A", "A->B"], "conclusion": "B"},
        ])
        result = judge.judge("B", derivation)
        assert result.passed is False
        assert "not established" in result.explanation


class TestCompilationJudge:
    """Tests for CompilationJudge."""

    def test_valid_python(self):
        judge = CompilationJudge()
        result = judge.judge("def foo():\n    return 42", "python")
        assert result.passed is True

    def test_invalid_python(self):
        judge = CompilationJudge()
        result = judge.judge("def foo( broken", "python")
        assert result.passed is False
        assert "syntax error" in result.explanation.lower()

    def test_valid_javascript(self):
        judge = CompilationJudge()
        result = judge.judge("function foo() { return 42; }", "javascript")
        assert result.passed is True

    def test_invalid_javascript(self):
        judge = CompilationJudge()
        result = judge.judge("function foo() { return 42; ", "javascript")
        assert result.passed is False

    def test_unsupported_language(self):
        judge = CompilationJudge()
        result = judge.judge("code", "brainfuck")
        assert result.passed is False
        assert "Unsupported" in result.explanation


class TestTestJudge:
    """Tests for TestJudge."""

    def test_passing_tests(self):
        judge = TestJudge()
        code = "def add(a, b): return a + b"
        tests = "assert add(1, 2) == 3\nassert add(0, 0) == 0"
        result = judge.judge(code, tests)
        assert result.passed is True

    def test_failing_tests(self):
        judge = TestJudge()
        code = "def add(a, b): return a - b"
        tests = "assert add(1, 2) == 3"
        result = judge.judge(code, tests)
        assert result.passed is False

    def test_syntax_error(self):
        judge = TestJudge()
        result = judge.judge("def broken(", "assert True")
        assert result.passed is False


class TestSemanticJudge:
    """Tests for SemanticJudge."""

    def test_identical_ir(self):
        judge = SemanticJudge()
        ir = json.dumps({"type": "add", "args": [1, 2]})
        result = judge.judge(ir, ir)
        assert result.passed is True
        assert result.score >= 0.95

    def test_different_ir(self):
        judge = SemanticJudge()
        ir1 = json.dumps({"type": "add", "args": [1, 2]})
        ir2 = json.dumps({"type": "mul", "args": [3, 4]})
        result = judge.judge(ir1, ir2)
        assert result.passed is False

    def test_invalid_json(self):
        judge = SemanticJudge()
        result = judge.judge("not json", '{"x": 1}')
        assert result.passed is False


# ============================================================
# Runner Tests
# ============================================================


def _mock_query(query: str) -> str:
    """Mock AXIMA query function for testing."""
    answers = {
        "what is 2+2": "4",
        "what is 3*3": "9",
        "solve x=1": "1",
        "unknown": "I don't know the answer",
    }
    return answers.get(query, "unsupported query")


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    def _make_manifest(self) -> BenchmarkManifest:
        cases = [
            BenchmarkCase(
                id="r_001", category="math", input="what is 2+2",
                expected_output="4", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
            BenchmarkCase(
                id="r_002", category="math", input="what is 3*3",
                expected_output="9", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.TRIVIAL,
            ),
            BenchmarkCase(
                id="r_003", category="math", input="unknown",
                expected_output="42", judge_type=JudgeType.EXACT,
                difficulty=Difficulty.EASY,
            ),
        ]
        return BenchmarkManifest(
            version="1.0.0", cases=cases, frozen_at="2026-01-01T00:00:00Z"
        )

    def test_run_suite(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        manifest = self._make_manifest()
        report = runner.run_suite(manifest)
        assert isinstance(report, BenchmarkReport)
        assert len(report.results) == 3
        assert report.manifest_version == "1.0.0"
        assert report.timestamp != ""

    def test_pass_rate_calculation(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        manifest = self._make_manifest()
        report = runner.run_suite(manifest, shuffle=False)
        # 2 pass (2+2=4, 3*3=9), 1 abstention ("I don't know")
        assert report.pass_rate < 1.0
        assert len(report.abstentions) >= 1

    def test_run_single(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        case = BenchmarkCase(
            id="s_001", category="math", input="what is 2+2",
            expected_output="4", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.TRIVIAL,
        )
        result = runner.run_single(case)
        assert result.judge_result.passed is True
        assert result.latency_ms >= 0

    def test_abstention_detected(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        case = BenchmarkCase(
            id="a_001", category="math", input="unknown",
            expected_output="42", judge_type=JudgeType.EXACT,
            difficulty=Difficulty.EASY,
        )
        result = runner.run_single(case)
        # "I don't know" is an abstention marker
        assert result.abstained is True

    def test_deterministic_seed(self):
        manifest = self._make_manifest()
        runner1 = BenchmarkRunner(query_fn=_mock_query, seed=123)
        runner2 = BenchmarkRunner(query_fn=_mock_query, seed=123)
        r1 = runner1.run_suite(manifest)
        r2 = runner2.run_suite(manifest)
        assert r1.pass_rate == r2.pass_rate

    def test_category_filter(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        manifest = self._make_manifest()
        report = runner.run_suite(manifest, categories=["math"])
        assert len(report.results) == 3  # all are math
        report2 = runner.run_suite(manifest, categories=["physics"])
        assert len(report2.results) == 0

    def test_failures_reported(self):
        def always_wrong(q: str) -> str:
            return "wrong answer"

        runner = BenchmarkRunner(query_fn=always_wrong, seed=42)
        manifest = self._make_manifest()
        report = runner.run_suite(manifest)
        assert len(report.failures) == 3
        assert report.pass_rate == 0.0

    def test_report_to_dict(self):
        runner = BenchmarkRunner(query_fn=_mock_query, seed=42)
        manifest = self._make_manifest()
        report = runner.run_suite(manifest)
        d = report.to_dict()
        assert "pass_rate" in d
        assert "total_cases" in d
        assert "latency_stats" in d


class TestLatencyStats:
    """Tests for LatencyStats."""

    def test_from_latencies(self):
        stats = LatencyStats.from_latencies([10.0, 20.0, 30.0, 40.0, 50.0])
        assert stats.min_ms == 10.0
        assert stats.max_ms == 50.0
        assert stats.mean_ms == 30.0

    def test_empty_latencies(self):
        stats = LatencyStats.from_latencies([])
        assert stats.min_ms == 0.0
        assert stats.max_ms == 0.0


# ============================================================
# Immune System Tests
# ============================================================


class TestBenchmarkImmuneSystem:
    """Tests for BenchmarkImmuneSystem."""

    def _make_manifest(self) -> BenchmarkManifest:
        cases = [
            BenchmarkCase(
                id="im_001", category="math",
                input="what is the meaning of life",
                expected_output="forty-two is the answer to everything",
                judge_type=JudgeType.EXACT, difficulty=Difficulty.EASY,
            ),
        ]
        return BenchmarkManifest(
            version="1.0.0", cases=cases, frozen_at="2026-01-01"
        )

    def test_detect_benchmark_branches_clean(self):
        immune = BenchmarkImmuneSystem()
        clean_code = """
def solve(query):
    if 'math' in query:
        return do_math(query)
    return None
"""
        findings = immune.detect_benchmark_branches(clean_code)
        assert len(findings) == 0

    def test_detect_benchmark_branches_suspicious(self):
        immune = BenchmarkImmuneSystem()
        dirty_code = """
def solve(query):
    if "benchmark" in mode:
        return hardcoded_answers[query]
    return do_real_work(query)
"""
        findings = immune.detect_benchmark_branches(dirty_code)
        assert len(findings) > 0

    def test_check_contamination_clean(self):
        immune = BenchmarkImmuneSystem()
        manifest = self._make_manifest()
        source = "def solve(q): return compute(q)"
        report = immune.check_contamination(source, manifest)
        assert report.clean is True

    def test_check_contamination_dirty(self):
        immune = BenchmarkImmuneSystem()
        manifest = self._make_manifest()
        source = 'return "forty-two is the answer to everything"'
        report = immune.check_contamination(source, manifest)
        assert report.clean is False
        assert "im_001" in report.contaminated_cases

    def test_canary_validation_no_query_fn(self):
        immune = BenchmarkImmuneSystem(query_fn=None)
        failures = immune.validate_canaries()
        assert failures == []

    def test_leakage_analysis_no_history(self):
        immune = BenchmarkImmuneSystem()
        anomalies = immune.leakage_analysis()
        assert anomalies == []

    def test_leakage_analysis_detects_jump(self):
        immune = BenchmarkImmuneSystem()
        immune.record_scores("v1", {"pass_rate": 0.5, "categories": {}})
        immune.record_scores("v2", {"pass_rate": 0.9, "categories": {}})
        anomalies = immune.leakage_analysis()
        assert len(anomalies) > 0
        assert "jump" in anomalies[0].lower() or "Score" in anomalies[0]

    def test_semantic_mutations_no_query_fn(self):
        immune = BenchmarkImmuneSystem(query_fn=None)
        manifest = self._make_manifest()
        inconsistencies = immune.semantic_mutations(manifest)
        assert inconsistencies == []
