"""Legacy regression tests — all 45 eval cases frozen from evals/.

These tests capture the existing eval cases as of the packaging milestone.
They serve as a regression safety net during refactoring.

Suites:
- Math: 20 cases (algebra, calculus, arithmetic)
- Multilingual: 15 cases (language detection from Romanized input)
- Codegen: 10 cases (algorithm generation)
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pytest


# ─── Frozen eval cases ───────────────────────────────────────────────────────

MATH_CASES: list[dict[str, object]] = [
    {"input": "solve x^2 - 4 = 0", "expected": ["2", "-2"]},
    {"input": "solve 2x + 6 = 0", "expected": ["-3"]},
    {"input": "what is the derivative of x^3", "expected": ["3x^2", "3x²"]},
    {"input": "integrate 2x dx", "expected": ["x^2", "x²"]},
    {"input": "what is 15 * 7", "expected": ["105"]},
    {"input": "what is sqrt(144)", "expected": ["12"]},
    {"input": "solve x^2 + 2x + 1 = 0", "expected": ["-1"]},
    {"input": "what is 2^10", "expected": ["1024"]},
    {"input": "what is the factorial of 5", "expected": ["120"]},
    {"input": "what is sin(0)", "expected": ["0"]},
    {"input": "what is cos(0)", "expected": ["1"]},
    {"input": "solve 3x - 9 = 0", "expected": ["3"]},
    {"input": "what is log(100)", "expected": ["2"]},
    {"input": "what is 17 + 28", "expected": ["45"]},
    {"input": "what is 100 / 4", "expected": ["25"]},
    {"input": "what is pi to 2 decimal places", "expected": ["3.14"]},
    {"input": "what is e to 2 decimal places", "expected": ["2.71"]},
    {"input": "solve x^2 - 9 = 0", "expected": ["3", "-3"]},
    {"input": "what is the GCD of 12 and 18", "expected": ["6"]},
    {"input": "what is 7 mod 3", "expected": ["1"]},
]

MULTILINGUAL_CASES: list[dict[str, object]] = [
    {"input": "gravity ante enti", "expected": "te"},
    {"input": "gravity kya hai", "expected": "hi"},
    {"input": "gravity enna", "expected": "ta"},
    {"input": "gravity nedir", "expected": "tr"},
    {"input": "gravity কী", "expected": "bn"},
    {"input": "gravity って何", "expected": "ja"},
    {"input": "gravity ma hia", "expected": "ar"},
    {"input": "gravity chemu", "expected": "te"},
    {"input": "What is gravity", "expected": "en"},
    {"input": "DNA kya hota hai", "expected": "hi"},
    {"input": "photosynthesis ante", "expected": "te"},
    {"input": "energia que es", "expected": "es"},
    {"input": "gravité c'est quoi", "expected": "fr"},
    {"input": "Schwerkraft was ist", "expected": "de"},
    {"input": "gravity enthu aanu", "expected": "ml"},
]

CODEGEN_CASES: list[dict[str, object]] = [
    {"input": "binary search in python", "expected": ["def ", "while", "mid"]},
    {"input": "quicksort in python", "expected": ["def ", "pivot"]},
    {"input": "fibonacci in python", "expected": ["def ", "fib"]},
    {"input": "linked list in python", "expected": ["class ", "next"]},
    {"input": "stack in python", "expected": ["push", "pop"]},
    {"input": "merge sort in javascript", "expected": ["function", "merge"]},
    {"input": "bubble sort in python", "expected": ["def ", "swap"]},
    {"input": "binary tree in python", "expected": ["class ", "left", "right"]},
    {"input": "hash map in python", "expected": ["def ", "key"]},
    {"input": "dijkstra in python", "expected": ["def ", "dist"]},
]

ALL_CASES: list[dict[str, object]] = MATH_CASES + MULTILINGUAL_CASES + CODEGEN_CASES

# Verify we have exactly 45 cases
assert len(ALL_CASES) == 45, f"Expected 45 cases, got {len(ALL_CASES)}"


# ─── Test infrastructure ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class EvalCase:
    """A single eval test case."""

    input: str
    expected: list[str] | str
    suite: str


def _get_axima_engine() -> object | None:
    """Attempt to import the legacy AXIMA engine."""
    from axima.config import SRC_PYTHON_DIR

    src_str = str(SRC_PYTHON_DIR)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    try:
        # Try the module-style import first
        from axima import get_axima  # type: ignore[import-untyped]
        return get_axima()
    except ImportError:
        pass

    try:
        # Fallback: try importing axima.py directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("axima_legacy", SRC_PYTHON_DIR / "axima.py")
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            get_fn = getattr(mod, "get_axima", None)
            if get_fn:
                return get_fn()
    except Exception:
        pass

    return None


# Cache the engine instance across tests
_engine_cache: dict[str, object | None] = {}


def _get_engine() -> object | None:
    if "engine" not in _engine_cache:
        _engine_cache["engine"] = _get_axima_engine()
    return _engine_cache["engine"]


def _match_expected(actual: str, expected: list[str] | str) -> bool:
    """Check if actual output matches expected (flexible matching)."""
    if isinstance(expected, list):
        return any(exp.lower() in actual.lower() for exp in expected)
    return expected.lower() in actual.lower()


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def axima_engine() -> object | None:
    """Provide the AXIMA engine instance, or None if unavailable."""
    return _get_engine()


# ─── Parametrized tests ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "case",
    MATH_CASES,
    ids=[c["input"][:40] for c in MATH_CASES],  # type: ignore[arg-type]
)
def test_math_legacy(axima_engine: object | None, case: dict[str, object]) -> None:
    """Regression test for math eval cases."""
    if axima_engine is None:
        pytest.skip("AXIMA engine not available")

    input_text = str(case["input"])
    expected = case["expected"]
    assert isinstance(expected, list)

    process_fn = getattr(axima_engine, "process", None)
    assert process_fn is not None, "Engine missing process() method"

    result = process_fn(input_text)
    answer = getattr(result, "answer", str(result))
    assert _match_expected(answer, expected), (
        f"Input: {input_text}\nExpected one of: {expected}\nGot: {answer[:200]}"
    )


@pytest.mark.parametrize(
    "case",
    MULTILINGUAL_CASES,
    ids=[c["input"][:40] for c in MULTILINGUAL_CASES],  # type: ignore[arg-type]
)
def test_multilingual_legacy(axima_engine: object | None, case: dict[str, object]) -> None:
    """Regression test for multilingual detection eval cases."""
    if axima_engine is None:
        pytest.skip("AXIMA engine not available")

    input_text = str(case["input"])
    expected = str(case["expected"])

    process_fn = getattr(axima_engine, "process", None)
    assert process_fn is not None, "Engine missing process() method"

    result = process_fn(input_text)
    language = getattr(result, "language", "")
    assert _match_expected(language, expected), (
        f"Input: {input_text}\nExpected language: {expected}\nGot: {language}"
    )


@pytest.mark.parametrize(
    "case",
    CODEGEN_CASES,
    ids=[c["input"][:40] for c in CODEGEN_CASES],  # type: ignore[arg-type]
)
def test_codegen_legacy(axima_engine: object | None, case: dict[str, object]) -> None:
    """Regression test for code generation eval cases."""
    if axima_engine is None:
        pytest.skip("AXIMA engine not available")

    input_text = str(case["input"])
    expected = case["expected"]
    assert isinstance(expected, list)

    code_fn = getattr(axima_engine, "code", None)
    assert code_fn is not None, "Engine missing code() method"

    result = code_fn(input_text)
    code = getattr(result, "code", str(result))
    assert _match_expected(code, expected), (
        f"Input: {input_text}\nExpected tokens: {expected}\nGot: {code[:200]}"
    )


# ─── Integrity check ─────────────────────────────────────────────────────────


def test_case_count_is_45() -> None:
    """Verify we have exactly 45 frozen eval cases."""
    assert len(MATH_CASES) == 20
    assert len(MULTILINGUAL_CASES) == 15
    assert len(CODEGEN_CASES) == 10
    assert len(ALL_CASES) == 45


def test_cases_match_eval_files() -> None:
    """Verify frozen cases match the eval JSON files on disk (if present)."""
    from axima.config import EVALS_DIR

    math_file = EVALS_DIR / "math" / "cases.json"
    if math_file.is_file():
        with open(math_file) as f:
            disk_cases = json.load(f)
        assert len(disk_cases) == len(MATH_CASES)
        for i, (disk, frozen) in enumerate(zip(disk_cases, MATH_CASES)):
            assert disk["input"] == frozen["input"], f"Math case {i} input mismatch"

    multi_file = EVALS_DIR / "multilingual" / "cases.json"
    if multi_file.is_file():
        with open(multi_file) as f:
            disk_cases = json.load(f)
        assert len(disk_cases) == len(MULTILINGUAL_CASES)
        for i, (disk, frozen) in enumerate(zip(disk_cases, MULTILINGUAL_CASES)):
            assert disk["input"] == frozen["input"], f"Multilingual case {i} input mismatch"

    code_file = EVALS_DIR / "codegen" / "cases.json"
    if code_file.is_file():
        with open(code_file) as f:
            disk_cases = json.load(f)
        assert len(disk_cases) == len(CODEGEN_CASES)
        for i, (disk, frozen) in enumerate(zip(disk_cases, CODEGEN_CASES)):
            assert disk["input"] == frozen["input"], f"Codegen case {i} input mismatch"
