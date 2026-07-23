"""Benchmark immune system: contamination detection and integrity checks.

Detects when benchmark-specific optimizations contaminate the system,
ensuring scores reflect genuine capability rather than overfitting.

Detection strategies:
1. Contamination check: Expected answers hardcoded in source
2. Benchmark branches: Code paths that only activate for benchmark inputs
3. Canary validation: Questions that SHOULD NOT be answerable
4. Semantic mutations: Paraphrased versions of cases should score similarly
5. Leakage analysis: Suspicious score jumps between versions
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

from .manifest import BenchmarkCase, BenchmarkManifest, JudgeType


class QueryFn(Protocol):
    """Protocol for query function used in canary/mutation checks."""

    def __call__(self, query: str) -> str: ...


@dataclass
class ContaminationReport:
    """Report from contamination analysis.

    Attributes:
        clean: Whether the system appears uncontaminated.
        contaminated_cases: Case IDs with evidence of contamination.
        suspicious_branches: Code patterns that look benchmark-specific.
        canary_failures: Canary cases that were incorrectly answered.
        mutation_inconsistencies: Cases where mutations scored very differently.
        score_anomalies: Suspicious score jumps.
        timestamp: When the analysis was run.
    """

    clean: bool
    contaminated_cases: List[str] = field(default_factory=list)
    suspicious_branches: List[str] = field(default_factory=list)
    canary_failures: List[str] = field(default_factory=list)
    mutation_inconsistencies: List[str] = field(default_factory=list)
    score_anomalies: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class CanaryCase:
    """A canary question that should NOT be answerable.

    If AXIMA answers a canary correctly, it indicates the system
    has been trained/fitted on benchmark content.

    Attributes:
        id: Unique identifier.
        question: The question (should be unanswerable from rules alone).
        forbidden_answer: If this appears in output, contamination detected.
        category: Domain category.
    """

    id: str
    question: str
    forbidden_answer: str
    category: str


class BenchmarkImmuneSystem:
    """Detects benchmark contamination and overfitting.

    The immune system runs independently of the benchmark runner,
    checking for signs that the system has been specifically tuned
    to pass benchmarks rather than developing genuine capability.
    """

    # Patterns that suggest benchmark-specific code branches
    SUSPICIOUS_PATTERNS = [
        r"if\s+['\"]benchmark['\"]",
        r"if\s+['\"]eval['\"].*mode",
        r"benchmark_mode\s*=",
        r"if.*case_id\s*==",
        r"hardcoded_answers\s*\[",
        r"eval_override",
        r"benchmark_special",
        r"if.*in\s+benchmark_inputs",
    ]

    def __init__(self, query_fn: Optional[QueryFn] = None) -> None:
        """Initialize the immune system.

        Args:
            query_fn: Function to query AXIMA (needed for canary/mutation).
        """
        self._query_fn = query_fn
        self._score_history: List[Dict[str, Any]] = []
        self._canaries: List[CanaryCase] = self._default_canaries()

    def check_contamination(
        self,
        source_code: str,
        manifest: BenchmarkManifest,
    ) -> ContaminationReport:
        """Run full contamination analysis.

        Args:
            source_code: The complete AXIMA source code to scan.
            manifest: The benchmark manifest to check against.

        Returns:
            ContaminationReport with all findings.
        """
        contaminated_cases = self._check_answer_leakage(source_code, manifest)
        suspicious_branches = self.detect_benchmark_branches(source_code)

        # Canary and mutation checks require query_fn
        canary_failures: List[str] = []
        mutation_inconsistencies: List[str] = []

        if self._query_fn is not None:
            canary_failures = self.validate_canaries()
            mutation_inconsistencies = self.semantic_mutations(manifest)

        score_anomalies = self.leakage_analysis()

        clean = (
            len(contaminated_cases) == 0
            and len(suspicious_branches) == 0
            and len(canary_failures) == 0
            and len(mutation_inconsistencies) == 0
            and len(score_anomalies) == 0
        )

        return ContaminationReport(
            clean=clean,
            contaminated_cases=contaminated_cases,
            suspicious_branches=suspicious_branches,
            canary_failures=canary_failures,
            mutation_inconsistencies=mutation_inconsistencies,
            score_anomalies=score_anomalies,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    def detect_benchmark_branches(self, source_code: str) -> List[str]:
        """Detect code branches that appear benchmark-specific.

        Scans source code for patterns that suggest special-case handling
        of benchmark inputs, which would inflate scores unfairly.

        Args:
            source_code: Source code to scan.

        Returns:
            List of suspicious patterns found (with context).
        """
        findings: List[str] = []

        lines = source_code.split("\n")
        for i, line in enumerate(lines):
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    context_start = max(0, i - 1)
                    context_end = min(len(lines), i + 2)
                    context = "\n".join(lines[context_start:context_end])
                    findings.append(
                        f"Line {i + 1}: Pattern '{pattern}' matched.\n"
                        f"Context:\n{context}"
                    )

        return findings

    def validate_canaries(self) -> List[str]:
        """Run canary questions and check for forbidden answers.

        Canary questions are designed to be unanswerable from AXIMA's
        legitimate knowledge base. If they're answered correctly,
        it indicates contamination from benchmark data.

        Returns:
            List of canary IDs that were incorrectly answered.
        """
        if self._query_fn is None:
            return []

        failures: List[str] = []

        for canary in self._canaries:
            try:
                response = self._query_fn(canary.question)
                response_lower = response.lower().strip()
                forbidden_lower = canary.forbidden_answer.lower().strip()

                # Check if the forbidden answer appears in the response
                if forbidden_lower in response_lower:
                    failures.append(
                        f"{canary.id}: Answered canary with forbidden content "
                        f"'{canary.forbidden_answer}'"
                    )
            except Exception:
                # Errors on canaries are fine (expected behavior)
                pass

        return failures

    def semantic_mutations(
        self,
        manifest: BenchmarkManifest,
        tolerance: float = 0.3,
    ) -> List[str]:
        """Test semantic mutations of benchmark cases.

        Paraphrases benchmark inputs and checks that scores are
        consistent. A large drop from original to mutation suggests
        the system has memorized specific phrasings.

        Args:
            manifest: Benchmark manifest with cases.
            tolerance: Maximum allowed score difference between
                       original and mutation (0.0 to 1.0).

        Returns:
            List of case IDs with inconsistent mutation scores.
        """
        if self._query_fn is None:
            return []

        inconsistencies: List[str] = []

        for case in manifest.cases[:20]:  # Limit to first 20 for efficiency
            mutations = self._generate_mutations(case.input)

            for mutation in mutations:
                try:
                    original_response = self._query_fn(case.input)
                    mutated_response = self._query_fn(mutation)

                    # If original passes but mutation fails completely,
                    # that's suspicious (could indicate memorization)
                    original_has_answer = len(original_response.strip()) > 5
                    mutated_has_answer = len(mutated_response.strip()) > 5

                    if original_has_answer and not mutated_has_answer:
                        inconsistencies.append(
                            f"{case.id}: Original answered but mutation "
                            f"'{mutation}' was not answered"
                        )
                except Exception:
                    pass

        return inconsistencies

    def leakage_analysis(
        self,
        score_jump_threshold: float = 0.2,
    ) -> List[str]:
        """Analyze score history for suspicious jumps.

        A sudden large improvement in benchmark scores without
        corresponding capability improvements is suspicious.

        Args:
            score_jump_threshold: Score increase that triggers a flag.

        Returns:
            List of anomaly descriptions.
        """
        anomalies: List[str] = []

        if len(self._score_history) < 2:
            return anomalies

        for i in range(1, len(self._score_history)):
            prev = self._score_history[i - 1]
            curr = self._score_history[i]

            prev_score = prev.get("pass_rate", 0.0)
            curr_score = curr.get("pass_rate", 0.0)
            jump = curr_score - prev_score

            if jump > score_jump_threshold:
                anomalies.append(
                    f"Score jump of {jump:.1%} between "
                    f"version {prev.get('version', '?')} and "
                    f"{curr.get('version', '?')} "
                    f"(from {prev_score:.1%} to {curr_score:.1%})"
                )

            # Check per-category jumps
            prev_cats = prev.get("categories", {})
            curr_cats = curr.get("categories", {})
            for cat in curr_cats:
                if cat in prev_cats:
                    cat_jump = curr_cats[cat] - prev_cats[cat]
                    if cat_jump > score_jump_threshold:
                        anomalies.append(
                            f"Category '{cat}' jump of {cat_jump:.1%} "
                            f"between versions"
                        )

        return anomalies

    def record_scores(self, version: str, report_data: Dict[str, Any]) -> None:
        """Record benchmark scores for longitudinal analysis.

        Args:
            version: AXIMA version string.
            report_data: Report data including pass_rate and categories.
        """
        self._score_history.append({
            "version": version,
            "pass_rate": report_data.get("pass_rate", 0.0),
            "categories": report_data.get("categories", {}),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })

    def _check_answer_leakage(
        self,
        source_code: str,
        manifest: BenchmarkManifest,
    ) -> List[str]:
        """Check if expected answers appear in source code."""
        contaminated: List[str] = []

        for case in manifest.cases:
            expected = case.expected_output.strip()
            # Only flag non-trivial answers (short ones are too common)
            if len(expected) > 8 and expected in source_code:
                contaminated.append(case.id)

        return contaminated

    def _default_canaries(self) -> List[CanaryCase]:
        """Default canary questions that should NOT be answerable."""
        return [
            CanaryCase(
                id="canary_001",
                question="What is the 47th digit of the Champernowne constant?",
                forbidden_answer="2",
                category="math",
            ),
            CanaryCase(
                id="canary_002",
                question="What color was Einstein's favorite umbrella?",
                forbidden_answer="blue",
                category="factual",
            ),
            CanaryCase(
                id="canary_003",
                question="What is the result of benchmark case AXIMA-INTERNAL-7742?",
                forbidden_answer="42",
                category="meta",
            ),
            CanaryCase(
                id="canary_004",
                question="Recite the 15th line of the AXIMA eval manifest.",
                forbidden_answer="solve",
                category="meta",
            ),
            CanaryCase(
                id="canary_005",
                question="What was the secret code phrase used in AXIMA testing on March 3?",
                forbidden_answer="phoenix",
                category="meta",
            ),
        ]

    def _generate_mutations(self, input_text: str) -> List[str]:
        """Generate semantic mutations of an input.

        Creates paraphrased versions that should yield similar results.
        """
        mutations: List[str] = []

        # Mutation 1: Add politeness prefix
        mutations.append(f"Please tell me: {input_text}")

        # Mutation 2: Rephrase as question if not already
        if not input_text.strip().endswith("?"):
            mutations.append(f"What is the answer to: {input_text}?")

        # Mutation 3: Word order change (simple swap)
        words = input_text.split()
        if len(words) >= 4:
            # Move first word to end
            mutations.append(" ".join(words[1:] + [words[0]]))

        return mutations
