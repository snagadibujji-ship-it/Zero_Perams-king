"""Code verification: compilation, tests, static analysis, output schema."""

from __future__ import annotations

import ast
import io
import re
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .verifier_base import Verifier, VerifierResult


# ---------------------------------------------------------------------------
# CompilationVerifier
# ---------------------------------------------------------------------------


class CompilationVerifier(Verifier):
    """Checks that generated code compiles/parses without syntax errors."""

    _LANGUAGE_PARSERS = {"python", "py"}

    def name(self) -> str:
        return "compilation_check"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") == "code" or "code" in claim

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        code = claim.get("code", evidence.get("code", ""))
        language = claim.get("language", evidence.get("language", "python")).lower()

        if not code:
            return VerifierResult(
                passed=False,
                check_name="compilation_check",
                details="No code provided to verify.",
                confidence=0.5,
            )

        if language in ("python", "py"):
            return self._check_python(code)
        elif language in ("javascript", "js"):
            return self._check_javascript(code)
        else:
            return self._check_generic(code, language)

    def _check_python(self, code: str) -> VerifierResult:
        """Parse Python code with the ast module."""
        try:
            ast.parse(code)
            return VerifierResult(
                passed=True,
                check_name="compilation_check",
                details="Python code parses successfully.",
                confidence=1.0,
            )
        except SyntaxError as e:
            return VerifierResult(
                passed=False,
                check_name="compilation_check",
                details=f"SyntaxError at line {e.lineno}: {e.msg}",
                counterexamples=[{"line": e.lineno, "error": e.msg}],
                confidence=1.0,
            )

    def _check_javascript(self, code: str) -> VerifierResult:
        """Basic JS syntax check via bracket/paren matching."""
        issues = self._check_balanced(code)
        if issues:
            return VerifierResult(
                passed=False,
                check_name="compilation_check",
                details=f"Bracket/paren mismatch: {issues}",
                counterexamples=[{"issue": issues}],
                confidence=0.7,
            )
        return VerifierResult(
            passed=True,
            check_name="compilation_check",
            details="JavaScript passes basic bracket/paren check.",
            confidence=0.6,
        )

    def _check_generic(self, code: str, language: str) -> VerifierResult:
        """Generic check: balanced brackets, no empty body."""
        issues = self._check_balanced(code)
        if issues:
            return VerifierResult(
                passed=False,
                check_name="compilation_check",
                details=f"Structural issue in {language} code: {issues}",
                counterexamples=[{"issue": issues}],
                confidence=0.5,
            )
        return VerifierResult(
            passed=True,
            check_name="compilation_check",
            details=f"{language} code passes structural checks.",
            confidence=0.4,
        )

    @staticmethod
    def _check_balanced(code: str) -> str:
        """Check balanced brackets, parens, and braces."""
        stack: List[str] = []
        pairs = {"(": ")", "[": "]", "{": "}"}
        for i, ch in enumerate(code):
            if ch in pairs:
                stack.append(ch)
            elif ch in pairs.values():
                if not stack:
                    return f"Unexpected '{ch}' at position {i}"
                expected = pairs[stack.pop()]
                if ch != expected:
                    return f"Expected '{expected}' but found '{ch}' at position {i}"
        if stack:
            return f"Unclosed: {''.join(stack)}"
        return ""


# ---------------------------------------------------------------------------
# TestVerifier
# ---------------------------------------------------------------------------


class TestVerifier(Verifier):
    """Runs generated tests against generated code (Python only for safety)."""

    def name(self) -> str:
        return "test_execution"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        ct = claim.get("type", "")
        lang = claim.get("language", "python").lower()
        return ct == "code" and lang in ("python", "py")

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        code = claim.get("code", evidence.get("code", ""))
        tests = evidence.get("tests", "")

        if not code or not tests:
            return VerifierResult(
                passed=False,
                check_name="test_execution",
                details="Missing code or tests for execution.",
                confidence=0.3,
            )

        # Combine code + tests and attempt to execute in restricted env
        combined = code + "\n\n" + tests
        return self._execute_safely(combined)

    def _execute_safely(self, code: str) -> VerifierResult:
        """Execute code in an isolated namespace with limited builtins."""
        restricted_builtins = {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "bool": bool,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "isinstance": isinstance,
            "type": type,
            "hasattr": hasattr,
            "getattr": getattr,
            "AssertionError": AssertionError,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "Exception": Exception,
            "True": True,
            "False": False,
            "None": None,
        }

        namespace: Dict[str, Any] = {"__builtins__": restricted_builtins}
        old_stdout = sys.stdout
        captured = io.StringIO()
        sys.stdout = captured

        try:
            exec(code, namespace)  # noqa: S102
            sys.stdout = old_stdout
            output = captured.getvalue()
            return VerifierResult(
                passed=True,
                check_name="test_execution",
                details=f"All tests passed. Output: {output[:500]}",
                confidence=0.9,
            )
        except AssertionError as e:
            sys.stdout = old_stdout
            return VerifierResult(
                passed=False,
                check_name="test_execution",
                details=f"Test assertion failed: {e}",
                counterexamples=[{"assertion_error": str(e)}],
                confidence=0.95,
            )
        except Exception as e:
            sys.stdout = old_stdout
            return VerifierResult(
                passed=False,
                check_name="test_execution",
                details=f"Execution error: {type(e).__name__}: {e}",
                counterexamples=[{"error": str(e), "type": type(e).__name__}],
                confidence=0.8,
            )


# ---------------------------------------------------------------------------
# StaticAnalysisVerifier
# ---------------------------------------------------------------------------

_SECURITY_PATTERNS = [
    (r"\beval\s*\(", "eval() usage — potential code injection"),
    (r"\bexec\s*\(", "exec() usage — potential code injection"),
    (r"\b__import__\s*\(", "__import__() — dynamic import risk"),
    (r"\bos\.system\s*\(", "os.system() — shell injection risk"),
    (r"\bsubprocess\b", "subprocess usage — shell command risk"),
    (r"\bpickle\.loads?\s*\(", "pickle deserialization — arbitrary code execution risk"),
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password detected"),
    (r"(api_key|secret|token)\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret detected"),
]

_QUALITY_PATTERNS = [
    (r"except\s*:", "Bare except clause — catches all exceptions"),
    (r"\bpass\b\s*$", "Empty pass statement — potential incomplete implementation"),
    (r"# TODO", "TODO comment — incomplete implementation"),
    (r"# FIXME", "FIXME comment — known issue"),
    (r"# HACK", "HACK comment — workaround"),
]


class StaticAnalysisVerifier(Verifier):
    """Basic security and quality checks on generated code."""

    def name(self) -> str:
        return "static_analysis"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return claim.get("type") == "code" or "code" in claim

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        code = claim.get("code", evidence.get("code", ""))
        if not code:
            return VerifierResult(
                passed=False,
                check_name="static_analysis",
                details="No code to analyze.",
                confidence=0.5,
            )

        security_findings: List[Dict[str, str]] = []
        quality_findings: List[Dict[str, str]] = []

        for pattern, description in _SECURITY_PATTERNS:
            matches = re.findall(pattern, code, re.MULTILINE)
            if matches:
                security_findings.append(
                    {"pattern": pattern, "description": description, "count": str(len(matches))}
                )

        for pattern, description in _QUALITY_PATTERNS:
            matches = re.findall(pattern, code, re.MULTILINE)
            if matches:
                quality_findings.append(
                    {"pattern": pattern, "description": description, "count": str(len(matches))}
                )

        all_findings = security_findings + quality_findings
        # Security findings are failures; quality findings are warnings
        passed = len(security_findings) == 0
        confidence = 0.85 if code.strip() else 0.3

        details_parts = []
        if security_findings:
            details_parts.append(
                f"{len(security_findings)} security issue(s): "
                + "; ".join(f["description"] for f in security_findings)
            )
        if quality_findings:
            details_parts.append(
                f"{len(quality_findings)} quality warning(s): "
                + "; ".join(f["description"] for f in quality_findings)
            )
        if not details_parts:
            details_parts.append("No security or quality issues detected.")

        return VerifierResult(
            passed=passed,
            check_name="static_analysis",
            details=" | ".join(details_parts),
            counterexamples=security_findings,
            confidence=confidence,
        )


# ---------------------------------------------------------------------------
# OutputSchemaVerifier
# ---------------------------------------------------------------------------


class OutputSchemaVerifier(Verifier):
    """Verifies that output matches an expected schema (type/structure check)."""

    def name(self) -> str:
        return "output_schema"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return "expected_schema" in claim or "output_schema" in claim

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        schema = claim.get("expected_schema", claim.get("output_schema", {}))
        output = evidence.get("output", evidence.get("result"))

        if not schema:
            return VerifierResult(
                passed=False,
                check_name="output_schema",
                details="No schema provided.",
                confidence=0.3,
            )

        violations = self._validate(output, schema, path="root")

        if violations:
            return VerifierResult(
                passed=False,
                check_name="output_schema",
                details=f"{len(violations)} schema violation(s).",
                counterexamples=violations,
                confidence=0.9,
            )

        return VerifierResult(
            passed=True,
            check_name="output_schema",
            details="Output matches expected schema.",
            confidence=0.95,
        )

    def _validate(
        self, value: Any, schema: Dict[str, Any], path: str
    ) -> List[Dict[str, str]]:
        """Recursively validate a value against a schema."""
        violations: List[Dict[str, str]] = []
        expected_type = schema.get("type")

        if expected_type:
            type_map = {
                "string": str,
                "str": str,
                "int": int,
                "integer": int,
                "float": float,
                "number": (int, float),
                "bool": bool,
                "boolean": bool,
                "list": list,
                "array": list,
                "dict": dict,
                "object": dict,
                "null": type(None),
                "none": type(None),
            }
            py_type = type_map.get(expected_type)
            if py_type and not isinstance(value, py_type):
                violations.append(
                    {
                        "path": path,
                        "expected_type": expected_type,
                        "actual_type": type(value).__name__,
                    }
                )
                return violations

        # Check required fields for dicts
        if isinstance(value, dict) and "properties" in schema:
            required = schema.get("required", [])
            for field_name in required:
                if field_name not in value:
                    violations.append(
                        {"path": f"{path}.{field_name}", "error": "missing required field"}
                    )
            for field_name, field_schema in schema["properties"].items():
                if field_name in value:
                    sub_violations = self._validate(
                        value[field_name], field_schema, f"{path}.{field_name}"
                    )
                    violations.extend(sub_violations)

        # Check list items
        if isinstance(value, list) and "items" in schema:
            for i, item in enumerate(value):
                sub_violations = self._validate(item, schema["items"], f"{path}[{i}]")
                violations.extend(sub_violations)

        return violations
