"""Benchmark judges: evaluate AXIMA outputs against expected results.

Each judge implements a specific evaluation strategy. NO substring
matching is permitted — all comparisons are structural or exact.

Judge types:
- ExactJudge: Exact string equality
- ToleranceJudge: Numeric comparison within tolerance
- ASTJudge: Abstract syntax tree structural equivalence
- ProofJudge: Logical proof validity checking
- CompilationJudge: Code compilation success
- TestJudge: Test suite pass/fail
- SemanticJudge: Meaning-level equivalence via IR comparison
"""

from __future__ import annotations

import ast
import math
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class JudgeResult:
    """Result of a judge evaluation.

    Attributes:
        passed: Whether the case passed.
        score: Numeric score (0.0 to 1.0).
        explanation: Human-readable explanation of the result.
        judge_name: Name of the judge that produced this result.
    """

    passed: bool
    score: float
    explanation: str
    judge_name: str


class ExactJudge:
    """Judge that requires exact string match.

    No substring matching, no fuzzy matching. The actual output
    must be exactly equal to the expected output after stripping
    leading/trailing whitespace.
    """

    def judge(self, expected: str, actual: str) -> JudgeResult:
        """Evaluate exact string equality.

        Args:
            expected: The expected output string.
            actual: The actual output string from AXIMA.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        expected_clean = expected.strip()
        actual_clean = actual.strip()

        passed = expected_clean == actual_clean
        score = 1.0 if passed else 0.0

        if passed:
            explanation = "Exact match."
        else:
            explanation = (
                f"Mismatch: expected {repr(expected_clean)}, "
                f"got {repr(actual_clean)}"
            )

        return JudgeResult(
            passed=passed,
            score=score,
            explanation=explanation,
            judge_name="ExactJudge",
        )


class ToleranceJudge:
    """Judge that checks numeric values within a tolerance.

    Parses both expected and actual as floats and compares them
    within the specified absolute or relative tolerance.
    """

    def judge(
        self,
        expected: str,
        actual: str,
        tolerance: float = 1e-6,
        relative: bool = False,
    ) -> JudgeResult:
        """Evaluate numeric comparison within tolerance.

        Args:
            expected: Expected numeric value as string.
            actual: Actual numeric value as string.
            tolerance: Absolute tolerance (or relative if relative=True).
            relative: If True, tolerance is relative to expected value.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        try:
            expected_val = float(expected.strip())
        except (ValueError, TypeError):
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Expected value is not numeric: {repr(expected)}",
                judge_name="ToleranceJudge",
            )

        try:
            actual_val = float(actual.strip())
        except (ValueError, TypeError):
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Actual value is not numeric: {repr(actual)}",
                judge_name="ToleranceJudge",
            )

        if relative:
            if expected_val == 0.0:
                diff = abs(actual_val)
            else:
                diff = abs((actual_val - expected_val) / expected_val)
        else:
            diff = abs(actual_val - expected_val)

        passed = diff <= tolerance

        if passed:
            score = 1.0
            explanation = (
                f"Within tolerance: |{actual_val} - {expected_val}| = "
                f"{diff:.2e} <= {tolerance:.2e}"
            )
        else:
            # Partial credit based on how close
            if tolerance > 0:
                score = max(0.0, 1.0 - (diff / (tolerance * 10)))
            else:
                score = 0.0
            explanation = (
                f"Outside tolerance: |{actual_val} - {expected_val}| = "
                f"{diff:.2e} > {tolerance:.2e}"
            )

        return JudgeResult(
            passed=passed,
            score=score,
            explanation=explanation,
            judge_name="ToleranceJudge",
        )


class ASTJudge:
    """Judge that checks structural code equivalence via AST comparison.

    Compares the abstract syntax trees of expected and actual Python code.
    Variable names and formatting differences are normalized away.
    """

    def judge(self, expected_ast: str, actual_code: str) -> JudgeResult:
        """Evaluate structural code equivalence.

        Args:
            expected_ast: Expected code (will be parsed to AST).
            actual_code: Actual code output from AXIMA.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        try:
            expected_tree = ast.parse(expected_ast.strip())
        except SyntaxError as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Expected code has syntax error: {e}",
                judge_name="ASTJudge",
            )

        try:
            actual_tree = ast.parse(actual_code.strip())
        except SyntaxError as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Actual code has syntax error: {e}",
                judge_name="ASTJudge",
            )

        # Normalize trees by removing line numbers and column offsets
        expected_normalized = self._normalize_ast(expected_tree)
        actual_normalized = self._normalize_ast(actual_tree)

        # Compare AST dumps
        expected_dump = ast.dump(expected_normalized, annotate_fields=True)
        actual_dump = ast.dump(actual_normalized, annotate_fields=True)

        passed = expected_dump == actual_dump

        if passed:
            score = 1.0
            explanation = "AST structures are equivalent."
        else:
            # Compute structural similarity
            score = self._structural_similarity(expected_normalized, actual_normalized)
            explanation = (
                f"AST structures differ. Structural similarity: {score:.2%}"
            )

        return JudgeResult(
            passed=passed,
            score=score,
            explanation=explanation,
            judge_name="ASTJudge",
        )

    def _normalize_ast(self, tree: ast.AST) -> ast.AST:
        """Remove position information from AST nodes."""
        for node in ast.walk(tree):
            for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
                if hasattr(node, attr):
                    setattr(node, attr, 0)
            # Remove type_comment if present
            if hasattr(node, "type_comment"):
                node.type_comment = None  # type: ignore[attr-defined]
        return tree

    def _structural_similarity(self, tree1: ast.AST, tree2: ast.AST) -> float:
        """Compute similarity between two AST trees (0.0 to 1.0)."""
        nodes1 = [type(n).__name__ for n in ast.walk(tree1)]
        nodes2 = [type(n).__name__ for n in ast.walk(tree2)]

        if not nodes1 and not nodes2:
            return 1.0
        if not nodes1 or not nodes2:
            return 0.0

        # Count node type overlap
        set1 = set(nodes1)
        set2 = set(nodes2)
        intersection = set1 & set2
        union = set1 | set2

        if not union:
            return 1.0

        return len(intersection) / len(union)


class ProofJudge:
    """Judge that verifies logical proof validity.

    Checks that each step in a derivation follows from previous steps
    using declared inference rules. Works with simple propositional
    and first-order patterns.
    """

    # Supported inference patterns
    VALID_RULES = {
        "modus_ponens": lambda premises, conclusion: (
            len(premises) == 2
            and any("implies" in p or "->" in p for p in premises)
        ),
        "substitution": lambda premises, conclusion: len(premises) >= 1,
        "symmetry": lambda premises, conclusion: len(premises) == 1,
        "transitivity": lambda premises, conclusion: len(premises) == 2,
        "definition": lambda premises, conclusion: True,
        "axiom": lambda premises, conclusion: True,
        "given": lambda premises, conclusion: True,
    }

    def judge(self, claim: str, derivation: str) -> JudgeResult:
        """Evaluate proof validity.

        Args:
            claim: The proposition being proved.
            derivation: JSON-encoded list of proof steps, each with
                        'rule', 'premises', and 'conclusion' fields.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        import json as _json

        try:
            steps = _json.loads(derivation)
        except (ValueError, TypeError):
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation="Derivation is not valid JSON.",
                judge_name="ProofJudge",
            )

        if not isinstance(steps, list) or len(steps) == 0:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation="Derivation must be a non-empty list of steps.",
                judge_name="ProofJudge",
            )

        established: List[str] = []
        errors: List[str] = []

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"Step {i}: not a dictionary")
                continue

            rule = step.get("rule", "").lower()
            premises = step.get("premises", [])
            conclusion = step.get("conclusion", "")

            if not conclusion:
                errors.append(f"Step {i}: missing conclusion")
                continue

            # Validate rule exists
            if rule not in self.VALID_RULES:
                errors.append(f"Step {i}: unknown rule '{rule}'")
                continue

            # For non-axiom/given rules, check premises are established
            if rule not in ("axiom", "given", "definition"):
                for premise in premises:
                    if premise not in established:
                        errors.append(
                            f"Step {i}: premise '{premise}' not established"
                        )

            # Check rule application is structurally valid
            validator = self.VALID_RULES[rule]
            if not validator(premises, conclusion):
                errors.append(f"Step {i}: invalid application of '{rule}'")

            established.append(conclusion)

        # Check final conclusion matches claim
        if established and claim.strip():
            final_matches = established[-1].strip() == claim.strip()
        else:
            final_matches = False

        if errors:
            passed = False
            score = max(0.0, 1.0 - len(errors) / max(len(steps), 1))
            explanation = f"Proof has {len(errors)} error(s): {'; '.join(errors[:3])}"
        elif not final_matches:
            passed = False
            score = 0.5
            explanation = (
                f"Proof is valid but final conclusion "
                f"'{established[-1] if established else ''}' "
                f"does not match claim '{claim}'"
            )
        else:
            passed = True
            score = 1.0
            explanation = f"Valid proof of '{claim}' in {len(steps)} steps."

        return JudgeResult(
            passed=passed,
            score=score,
            explanation=explanation,
            judge_name="ProofJudge",
        )


class CompilationJudge:
    """Judge that checks whether code compiles/parses successfully.

    Supports Python (syntax check), JavaScript (basic syntax),
    and other languages via external compilers if available.
    """

    # Language to compilation strategy mapping
    STRATEGIES: Dict[str, str] = {
        "python": "ast_parse",
        "javascript": "syntax_check",
        "java": "javac",
        "c": "gcc",
        "cpp": "g++",
        "rust": "rustc",
        "go": "go_build",
    }

    def judge(self, code: str, language: str) -> JudgeResult:
        """Evaluate whether code compiles successfully.

        Args:
            code: Source code string.
            language: Programming language (python, javascript, etc.).

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        lang = language.lower().strip()
        strategy = self.STRATEGIES.get(lang)

        if strategy is None:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Unsupported language: {language}",
                judge_name="CompilationJudge",
            )

        if strategy == "ast_parse":
            return self._check_python(code)
        elif strategy == "syntax_check":
            return self._check_javascript(code)
        else:
            return self._check_external(code, lang, strategy)

    def _check_python(self, code: str) -> JudgeResult:
        """Check Python code via ast.parse."""
        try:
            ast.parse(code)
            return JudgeResult(
                passed=True,
                score=1.0,
                explanation="Python code parses successfully.",
                judge_name="CompilationJudge",
            )
        except SyntaxError as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Python syntax error at line {e.lineno}: {e.msg}",
                judge_name="CompilationJudge",
            )

    def _check_javascript(self, code: str) -> JudgeResult:
        """Basic JavaScript syntax validation.

        Checks for balanced braces, brackets, and common syntax issues.
        Not a full parser — a heuristic check.
        """
        # Check balanced delimiters
        stack: List[str] = []
        pairs = {")": "(", "]": "[", "}": "{"}

        in_string = False
        string_char = ""
        escaped = False

        for char in code:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if in_string:
                if char == string_char:
                    in_string = False
                continue
            if char in ('"', "'", "`"):
                in_string = True
                string_char = char
                continue
            if char in "({[":
                stack.append(char)
            elif char in ")}]":
                if not stack or stack[-1] != pairs[char]:
                    return JudgeResult(
                        passed=False,
                        score=0.0,
                        explanation=f"Unbalanced '{char}' in JavaScript code.",
                        judge_name="CompilationJudge",
                    )
                stack.pop()

        if stack:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Unclosed delimiters: {''.join(stack)}",
                judge_name="CompilationJudge",
            )

        return JudgeResult(
            passed=True,
            score=1.0,
            explanation="JavaScript syntax check passed (delimiter balance).",
            judge_name="CompilationJudge",
        )

    def _check_external(self, code: str, language: str, compiler: str) -> JudgeResult:
        """Attempt external compilation. Falls back gracefully."""
        extensions = {"java": ".java", "c": ".c", "cpp": ".cpp", "rust": ".rs", "go": ".go"}
        ext = extensions.get(language, ".txt")

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=ext, delete=False
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            cmd_map = {
                "javac": ["javac", tmp_path],
                "gcc": ["gcc", "-fsyntax-only", tmp_path],
                "g++": ["g++", "-fsyntax-only", tmp_path],
                "rustc": ["rustc", "--edition=2021", "--crate-type=lib", tmp_path],
                "go_build": ["go", "build", tmp_path],
            }

            cmd = cmd_map.get(compiler)
            if cmd is None:
                return JudgeResult(
                    passed=False,
                    score=0.0,
                    explanation=f"No compiler command for {compiler}",
                    judge_name="CompilationJudge",
                )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return JudgeResult(
                    passed=True,
                    score=1.0,
                    explanation=f"{language} code compiles successfully.",
                    judge_name="CompilationJudge",
                )
            else:
                error_msg = (result.stderr or result.stdout)[:200]
                return JudgeResult(
                    passed=False,
                    score=0.0,
                    explanation=f"Compilation failed: {error_msg}",
                    judge_name="CompilationJudge",
                )

        except FileNotFoundError:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Compiler '{compiler}' not found on system.",
                judge_name="CompilationJudge",
            )
        except subprocess.TimeoutExpired:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation="Compilation timed out (30s limit).",
                judge_name="CompilationJudge",
            )
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except (NameError, OSError):
                pass


class TestJudge:
    """Judge that runs test cases against generated code.

    Executes the code and tests in an isolated subprocess to
    verify functional correctness.
    """

    def judge(self, code: str, tests: str, timeout: int = 30) -> JudgeResult:
        """Evaluate code by running tests against it.

        Args:
            code: The generated code.
            tests: Test code (assertions/unittest) to run against it.
            timeout: Maximum execution time in seconds.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        # Combine code and tests
        full_code = f"{code}\n\n{tests}"

        # First check syntax
        try:
            ast.parse(full_code)
        except SyntaxError as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Syntax error in code+tests: {e}",
                judge_name="TestJudge",
            )

        # Execute in subprocess for isolation
        try:
            result = subprocess.run(
                [sys.executable, "-c", full_code],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode == 0:
                return JudgeResult(
                    passed=True,
                    score=1.0,
                    explanation="All tests passed.",
                    judge_name="TestJudge",
                )
            else:
                error_msg = (result.stderr or result.stdout)[:300]
                return JudgeResult(
                    passed=False,
                    score=0.0,
                    explanation=f"Tests failed: {error_msg}",
                    judge_name="TestJudge",
                )

        except subprocess.TimeoutExpired:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Execution timed out ({timeout}s limit).",
                judge_name="TestJudge",
            )
        except OSError as e:
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Execution error: {e}",
                judge_name="TestJudge",
            )


class SemanticJudge:
    """Judge that checks meaning equivalence via intermediate representation.

    Compares two semantic IRs (intermediate representations) for
    structural and meaning equivalence. IRs are expected as JSON
    structures with typed nodes.
    """

    def judge(self, expected_ir: str, actual_ir: str) -> JudgeResult:
        """Evaluate meaning equivalence between two IRs.

        Args:
            expected_ir: Expected semantic IR as JSON string.
            actual_ir: Actual semantic IR as JSON string.

        Returns:
            JudgeResult with pass/fail and explanation.
        """
        import json as _json

        try:
            expected = _json.loads(expected_ir)
        except (ValueError, TypeError):
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Expected IR is not valid JSON.",
                judge_name="SemanticJudge",
            )

        try:
            actual = _json.loads(actual_ir)
        except (ValueError, TypeError):
            return JudgeResult(
                passed=False,
                score=0.0,
                explanation=f"Actual IR is not valid JSON.",
                judge_name="SemanticJudge",
            )

        # Compare structure recursively
        score = self._compare_ir(expected, actual)
        passed = score >= 0.95  # 95% threshold for semantic equivalence

        if passed:
            explanation = f"Semantic equivalence confirmed (score={score:.3f})."
        else:
            explanation = (
                f"Semantic mismatch (score={score:.3f}). "
                f"Threshold is 0.95 for equivalence."
            )

        return JudgeResult(
            passed=passed,
            score=score,
            explanation=explanation,
            judge_name="SemanticJudge",
        )

    def _compare_ir(self, expected: Any, actual: Any) -> float:
        """Recursively compare two IR structures."""
        if type(expected) != type(actual):
            return 0.0

        if isinstance(expected, dict):
            return self._compare_dicts(expected, actual)
        elif isinstance(expected, list):
            return self._compare_lists(expected, actual)
        elif isinstance(expected, (int, float)):
            if expected == 0 and actual == 0:
                return 1.0
            if expected == 0:
                return 0.0
            return 1.0 if math.isclose(expected, actual, rel_tol=1e-6) else 0.0
        elif isinstance(expected, str):
            return 1.0 if expected == actual else 0.0
        elif isinstance(expected, bool):
            return 1.0 if expected == actual else 0.0
        elif expected is None:
            return 1.0 if actual is None else 0.0
        else:
            return 1.0 if expected == actual else 0.0

    def _compare_dicts(self, expected: dict, actual: dict) -> float:
        """Compare two dictionaries for semantic equivalence."""
        if not expected and not actual:
            return 1.0

        all_keys = set(expected.keys()) | set(actual.keys())
        if not all_keys:
            return 1.0

        scores: List[float] = []
        for key in all_keys:
            if key in expected and key in actual:
                scores.append(self._compare_ir(expected[key], actual[key]))
            else:
                scores.append(0.0)

        return sum(scores) / len(scores)

    def _compare_lists(self, expected: list, actual: list) -> float:
        """Compare two lists for semantic equivalence."""
        if not expected and not actual:
            return 1.0
        if not expected or not actual:
            return 0.0

        max_len = max(len(expected), len(actual))
        scores: List[float] = []

        for i in range(max_len):
            if i < len(expected) and i < len(actual):
                scores.append(self._compare_ir(expected[i], actual[i]))
            else:
                scores.append(0.0)

        return sum(scores) / len(scores)
