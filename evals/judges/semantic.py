"""Semantic equivalence judge for AXIMA evaluations.

Uses MeaningIR comparison for semantic equivalence checking.
NOT substring matching — compares structural meaning, numeric
values within tolerance, and equivalent expressions.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class SemanticResult:
    """Result of a semantic equivalence evaluation.

    Attributes:
        passed: Whether the outputs are semantically equivalent.
        score: Similarity score (0.0 to 1.0).
        expected: The expected value.
        actual: The actual value.
        explanation: Human-readable explanation.
        components: Breakdown of which aspects matched/differed.
    """

    passed: bool
    score: float
    expected: str
    actual: str
    explanation: str
    components: Dict[str, float]


class SemanticEquivalenceJudge:
    """Judge that determines semantic equivalence between expected and actual outputs.

    Uses multiple strategies:
    1. Numeric equivalence with configurable tolerance
    2. Expression normalization (e.g., "3x^2" == "3*x^2" == "3x²")
    3. Set equivalence for multi-valued answers (e.g., roots)
    4. MeaningIR structural comparison when available
    5. Canonical form reduction

    Does NOT use:
    - Substring matching
    - Fuzzy/edit distance matching
    - Case-insensitive contains checks
    """

    def __init__(
        self,
        numeric_tolerance: float = 1e-6,
        relative_tolerance: float = 1e-4,
        equivalence_threshold: float = 0.90,
    ) -> None:
        """Initialize the semantic equivalence judge.

        Args:
            numeric_tolerance: Absolute tolerance for numeric comparisons.
            relative_tolerance: Relative tolerance for numeric comparisons.
            equivalence_threshold: Score threshold for considering equivalence.
        """
        self._numeric_tolerance = numeric_tolerance
        self._relative_tolerance = relative_tolerance
        self._equivalence_threshold = equivalence_threshold

        # Expression normalization patterns
        self._superscript_map = {
            "²": "^2", "³": "^3", "⁴": "^4", "⁵": "^5",
            "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
            "⁰": "^0", "¹": "^1",
        }

        # Known equivalent expressions
        self._equivalences: Dict[str, Set[str]] = {
            "pi": {"π", "3.14159", "3.1416"},
            "e": {"2.71828", "2.7183"},
            "inf": {"infinity", "∞"},
            "true": {"yes", "1", "correct"},
            "false": {"no", "0", "incorrect"},
        }

    def judge(self, expected: str, actual: str) -> SemanticResult:
        """Judge semantic equivalence between expected and actual.

        Tries multiple comparison strategies in order of specificity:
        1. Exact match (after normalization)
        2. Numeric equivalence
        3. Expression equivalence
        4. Set equivalence (for multi-valued answers)
        5. Structural IR comparison

        Args:
            expected: The expected output.
            actual: The actual output from the system.

        Returns:
            SemanticResult with detailed scoring.
        """
        components: Dict[str, float] = {}

        # Normalize whitespace
        exp_norm = self._normalize(expected)
        act_norm = self._normalize(actual)

        # Strategy 1: Exact match after normalization
        if exp_norm == act_norm:
            return SemanticResult(
                passed=True,
                score=1.0,
                expected=expected,
                actual=actual,
                explanation="Exact match after normalization.",
                components={"exact": 1.0},
            )
        components["exact"] = 0.0

        # Strategy 2: Numeric equivalence
        numeric_score = self._numeric_equivalence(exp_norm, act_norm)
        components["numeric"] = numeric_score
        if numeric_score >= self._equivalence_threshold:
            return SemanticResult(
                passed=True,
                score=numeric_score,
                expected=expected,
                actual=actual,
                explanation=f"Numeric equivalence (score={numeric_score:.3f}).",
                components=components,
            )

        # Strategy 3: Expression equivalence
        expr_score = self._expression_equivalence(exp_norm, act_norm)
        components["expression"] = expr_score
        if expr_score >= self._equivalence_threshold:
            return SemanticResult(
                passed=True,
                score=expr_score,
                expected=expected,
                actual=actual,
                explanation=f"Expression equivalence (score={expr_score:.3f}).",
                components=components,
            )

        # Strategy 4: Set equivalence (for multi-valued answers)
        set_score = self._set_equivalence(exp_norm, act_norm)
        components["set"] = set_score
        if set_score >= self._equivalence_threshold:
            return SemanticResult(
                passed=True,
                score=set_score,
                expected=expected,
                actual=actual,
                explanation=f"Set equivalence (score={set_score:.3f}).",
                components=components,
            )

        # Strategy 5: Structural comparison
        struct_score = self._structural_equivalence(exp_norm, act_norm)
        components["structural"] = struct_score
        if struct_score >= self._equivalence_threshold:
            return SemanticResult(
                passed=True,
                score=struct_score,
                expected=expected,
                actual=actual,
                explanation=f"Structural equivalence (score={struct_score:.3f}).",
                components=components,
            )

        # Compute overall score as weighted max
        overall = max(components.values()) if components else 0.0
        passed = overall >= self._equivalence_threshold

        return SemanticResult(
            passed=passed,
            score=overall,
            expected=expected,
            actual=actual,
            explanation=(
                f"Semantic comparison complete. Best strategy score: {overall:.3f}. "
                f"Threshold: {self._equivalence_threshold}."
            ),
            components=components,
        )

    def judge_with_ir(
        self,
        expected_ir: Dict[str, Any],
        actual_ir: Dict[str, Any],
    ) -> SemanticResult:
        """Judge semantic equivalence using MeaningIR structures.

        This is the preferred method when both expected and actual
        have been parsed into MeaningIR form.

        Args:
            expected_ir: Expected MeaningIR as dictionary.
            actual_ir: Actual MeaningIR as dictionary.

        Returns:
            SemanticResult with IR comparison details.
        """
        score = self._compare_ir_recursive(expected_ir, actual_ir)
        passed = score >= self._equivalence_threshold

        return SemanticResult(
            passed=passed,
            score=score,
            expected=str(expected_ir)[:200],
            actual=str(actual_ir)[:200],
            explanation=(
                f"MeaningIR comparison score: {score:.3f}. "
                f"{'Equivalent' if passed else 'Not equivalent'}."
            ),
            components={"ir_comparison": score},
        )

    # --- Private comparison strategies ---

    def _normalize(self, text: str) -> str:
        """Normalize text for comparison (whitespace, superscripts, etc.)."""
        result = text.strip()

        # Replace Unicode superscripts with caret notation
        for sup, replacement in self._superscript_map.items():
            result = result.replace(sup, replacement)

        # Normalize whitespace
        result = re.sub(r"\s+", " ", result)

        # Normalize multiplication signs
        result = result.replace("×", "*").replace("·", "*")

        # Normalize division
        result = result.replace("÷", "/")

        return result

    def _numeric_equivalence(self, expected: str, actual: str) -> float:
        """Check if two strings represent the same number within tolerance."""
        exp_val = self._parse_number(expected)
        act_val = self._parse_number(actual)

        if exp_val is None or act_val is None:
            return 0.0

        # Check absolute tolerance
        abs_diff = abs(exp_val - act_val)
        if abs_diff <= self._numeric_tolerance:
            return 1.0

        # Check relative tolerance
        if exp_val != 0:
            rel_diff = abs_diff / abs(exp_val)
            if rel_diff <= self._relative_tolerance:
                return 1.0

        # Partial credit for close values
        if exp_val != 0:
            ratio = 1.0 - min(1.0, abs_diff / abs(exp_val))
            return max(0.0, ratio)

        return 0.0

    def _expression_equivalence(self, expected: str, actual: str) -> float:
        """Check if two expressions are mathematically equivalent."""
        # Normalize expression forms
        exp_canonical = self._canonicalize_expression(expected)
        act_canonical = self._canonicalize_expression(actual)

        if exp_canonical == act_canonical:
            return 1.0

        # Check known equivalences
        exp_lower = expected.lower().strip()
        act_lower = actual.lower().strip()

        for canonical, equivalents in self._equivalences.items():
            all_forms = equivalents | {canonical}
            if exp_lower in all_forms and act_lower in all_forms:
                return 1.0

        # Check if one is a simplified form of the other
        # e.g., "3x^2" vs "3*x^2" vs "3 * x ** 2"
        exp_tokens = self._tokenize_expression(exp_canonical)
        act_tokens = self._tokenize_expression(act_canonical)

        if exp_tokens == act_tokens:
            return 1.0

        # Token overlap for partial credit
        if exp_tokens and act_tokens:
            overlap = len(set(exp_tokens) & set(act_tokens))
            total = max(len(set(exp_tokens)), len(set(act_tokens)))
            return overlap / total if total > 0 else 0.0

        return 0.0

    def _set_equivalence(self, expected: str, actual: str) -> float:
        """Check set equivalence for multi-valued answers.

        Handles cases like "x = 2, -2" vs "x = -2, 2" vs "{2, -2}".
        """
        exp_values = self._extract_values(expected)
        act_values = self._extract_values(actual)

        if not exp_values or not act_values:
            return 0.0

        # Try numeric set comparison
        exp_nums = set()
        act_nums = set()

        for v in exp_values:
            n = self._parse_number(v)
            if n is not None:
                exp_nums.add(round(n, 8))

        for v in act_values:
            n = self._parse_number(v)
            if n is not None:
                act_nums.add(round(n, 8))

        if exp_nums and act_nums:
            if exp_nums == act_nums:
                return 1.0
            # Check with tolerance
            matched = 0
            for e in exp_nums:
                for a in act_nums:
                    if abs(e - a) <= self._numeric_tolerance:
                        matched += 1
                        break
            total = max(len(exp_nums), len(act_nums))
            return matched / total if total > 0 else 0.0

        # String set comparison
        exp_set = {v.strip().lower() for v in exp_values}
        act_set = {v.strip().lower() for v in act_values}

        if exp_set == act_set:
            return 1.0

        overlap = len(exp_set & act_set)
        total = max(len(exp_set), len(act_set))
        return overlap / total if total > 0 else 0.0

    def _structural_equivalence(self, expected: str, actual: str) -> float:
        """Compare structural similarity of two text outputs."""
        # Extract key-value pairs or structured content
        exp_parts = self._extract_structure(expected)
        act_parts = self._extract_structure(actual)

        if not exp_parts or not act_parts:
            # Fall back to token-level Jaccard similarity
            exp_tokens = set(expected.lower().split())
            act_tokens = set(actual.lower().split())
            if not exp_tokens or not act_tokens:
                return 0.0
            intersection = exp_tokens & act_tokens
            union = exp_tokens | act_tokens
            return len(intersection) / len(union)

        # Compare structured parts
        matched = 0
        for key, value in exp_parts.items():
            if key in act_parts:
                if act_parts[key] == value:
                    matched += 1
                elif self._numeric_equivalence(str(value), str(act_parts[key])) > 0.9:
                    matched += 1

        total = max(len(exp_parts), len(act_parts))
        return matched / total if total > 0 else 0.0

    def _compare_ir_recursive(self, expected: Any, actual: Any) -> float:
        """Recursively compare two IR structures."""
        if type(expected) != type(actual):
            # Allow numeric type coercion
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                return self._numeric_equivalence(str(expected), str(actual))
            return 0.0

        if isinstance(expected, dict):
            if not expected and not actual:
                return 1.0
            all_keys = set(expected.keys()) | set(actual.keys())
            if not all_keys:
                return 1.0
            scores = []
            for key in all_keys:
                if key in expected and key in actual:
                    scores.append(self._compare_ir_recursive(expected[key], actual[key]))
                else:
                    scores.append(0.0)
            return sum(scores) / len(scores)

        elif isinstance(expected, list):
            if not expected and not actual:
                return 1.0
            if not expected or not actual:
                return 0.0
            max_len = max(len(expected), len(actual))
            scores = []
            for i in range(max_len):
                if i < len(expected) and i < len(actual):
                    scores.append(self._compare_ir_recursive(expected[i], actual[i]))
                else:
                    scores.append(0.0)
            return sum(scores) / len(scores)

        elif isinstance(expected, (int, float)):
            return self._numeric_equivalence(str(expected), str(actual))

        elif isinstance(expected, str):
            if expected == actual:
                return 1.0
            # Try expression equivalence for string values
            return self._expression_equivalence(expected, actual)

        else:
            return 1.0 if expected == actual else 0.0

    # --- Utility methods ---

    def _parse_number(self, text: str) -> Optional[float]:
        """Parse a string as a numeric value."""
        cleaned = text.strip().lower()

        # Known constants
        constants = {
            "pi": math.pi, "π": math.pi,
            "e": math.e,
            "inf": math.inf, "infinity": math.inf, "∞": math.inf,
            "-inf": -math.inf, "-infinity": -math.inf,
        }
        if cleaned in constants:
            return constants[cleaned]

        # Try direct float parse
        try:
            return float(cleaned)
        except ValueError:
            pass

        # Try removing trailing units or symbols
        # e.g., "42.0ms", "3.14rad"
        match = re.match(r"^([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)", cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass

        return None

    def _canonicalize_expression(self, expr: str) -> str:
        """Reduce an expression to canonical form."""
        result = expr.strip().lower()

        # Remove spaces around operators
        result = re.sub(r"\s*([+\-*/^=])\s*", r"\1", result)

        # Normalize exponentiation
        result = result.replace("**", "^")

        # Remove redundant multiplication signs between number and variable
        # e.g., "3*x" → "3x"
        result = re.sub(r"(\d)\*([a-z])", r"\1\2", result)

        # Remove leading "x = " or "y = " for solution expressions
        result = re.sub(r"^[a-z]\s*=\s*", "", result)

        return result

    def _tokenize_expression(self, expr: str) -> List[str]:
        """Tokenize a mathematical expression."""
        # Split on operators and whitespace, keep tokens
        tokens = re.findall(r"[a-z_]+|\d+\.?\d*|[+\-*/^()=]", expr.lower())
        return tokens

    def _extract_values(self, text: str) -> List[str]:
        """Extract individual values from a multi-valued answer."""
        # Split on common delimiters
        # Handle formats: "2, -2", "{2, -2}", "x = 2 or x = -2", "±3"
        cleaned = text.strip()

        # Handle ± notation
        if "±" in cleaned:
            match = re.search(r"±\s*(\d+\.?\d*)", cleaned)
            if match:
                val = match.group(1)
                return [val, f"-{val}"]

        # Remove set braces
        cleaned = cleaned.strip("{}[]() ")

        # Split on various delimiters
        parts = re.split(r"[,;]|\bor\b|\band\b", cleaned)

        # Clean each part
        values = []
        for part in parts:
            part = part.strip()
            # Remove "x = " prefix
            part = re.sub(r"^[a-z]\s*=\s*", "", part)
            if part:
                values.append(part)

        return values if len(values) > 1 else [cleaned]

    def _extract_structure(self, text: str) -> Dict[str, str]:
        """Extract key-value structure from text."""
        result: Dict[str, str] = {}

        # Try "key: value" patterns
        for match in re.finditer(r"(\w+)\s*[:=]\s*(.+?)(?:\n|$)", text):
            result[match.group(1).lower()] = match.group(2).strip()

        return result
