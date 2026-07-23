"""Verification Constellation: orchestrates multiple verifiers with quorum decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .verifier_base import Verifier, VerifierReceipt, VerifierResult


class ReleaseDecision(Enum):
    """Final release decision for a verified claim."""
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL = "CONDITIONAL"


@dataclass
class VerificationReport:
    """Complete report from a verification constellation run."""

    checks_run: int
    checks_passed: int
    counterexamples: List[Any] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    security_findings: List[Dict[str, Any]] = field(default_factory=list)
    residual_risk: float = 0.0
    verifier_receipts: List[VerifierReceipt] = field(default_factory=list)
    release_decision: ReleaseDecision = ReleaseDecision.FAIL
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        """Fraction of checks that passed."""
        if self.checks_run == 0:
            return 0.0
        return self.checks_passed / self.checks_run

    @property
    def has_security_issues(self) -> bool:
        return len(self.security_findings) > 0

    @property
    def has_counterexamples(self) -> bool:
        return len(self.counterexamples) > 0


class VerificationConstellation:
    """Orchestrates multiple independent verifiers with quorum-based decisions.

    Core invariants:
    - No generator may grade itself (verifier independence)
    - High-risk claims require quorum agreement
    - Counterexamples override pass votes
    - Security findings force CONDITIONAL or FAIL
    """

    def __init__(
        self,
        quorum_threshold: float = 0.7,
        high_risk_quorum: float = 0.9,
    ) -> None:
        self._verifiers: List[Verifier] = []
        self._excluded_pairs: Dict[str, Set[str]] = {}  # generator -> excluded verifiers
        self._quorum_threshold = quorum_threshold
        self._high_risk_quorum = high_risk_quorum

    def register_verifier(self, verifier: Verifier) -> None:
        """Register a verifier in the constellation."""
        self._verifiers.append(verifier)

    def exclude_self_grading(self, generator_name: str, verifier_name: str) -> None:
        """Prevent a generator from being verified by a related verifier."""
        if generator_name not in self._excluded_pairs:
            self._excluded_pairs[generator_name] = set()
        self._excluded_pairs[generator_name].add(verifier_name)

    def select_verifiers(
        self,
        claim: Dict[str, Any],
        contract: Optional[Dict[str, Any]] = None,
    ) -> List[Verifier]:
        """Select applicable verifiers for a claim, respecting independence constraints."""
        generator = claim.get("generator", "")
        excluded = self._excluded_pairs.get(generator, set())

        applicable = []
        for v in self._verifiers:
            if v.name() in excluded:
                continue
            if v.applicable(claim):
                applicable.append(v)

        # If contract specifies required verifiers, filter
        if contract and "required_verifiers" in contract:
            required_names = set(contract["required_verifiers"])
            # Ensure required verifiers are included
            required = [v for v in applicable if v.name() in required_names]
            others = [v for v in applicable if v.name() not in required_names]
            return required + others

        return applicable

    def run_verification(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        contract: Optional[Dict[str, Any]] = None,
    ) -> VerificationReport:
        """Run all applicable verifiers and produce a report.

        Args:
            claim: The claim to verify (includes type, content, generator info).
            evidence: Supporting evidence for the claim.
            contract: Optional epistemic contract specifying requirements.

        Returns:
            VerificationReport with quorum-based release decision.
        """
        verifiers = self.select_verifiers(claim, contract)

        if not verifiers:
            return VerificationReport(
                checks_run=0,
                checks_passed=0,
                release_decision=ReleaseDecision.FAIL,
                details={"reason": "No applicable verifiers found."},
            )

        results: List[VerifierResult] = []
        receipts: List[VerifierReceipt] = []
        counterexamples: List[Any] = []
        contradictions: List[Dict[str, Any]] = []
        security_findings: List[Dict[str, Any]] = []

        claim_id = claim.get("id", claim.get("claim_id", "unknown"))

        for verifier in verifiers:
            result = verifier.verify(claim, evidence, contract)
            results.append(result)
            receipt = verifier.make_receipt(str(claim_id), result)
            receipts.append(receipt)

            if result.counterexamples:
                counterexamples.extend(result.counterexamples)

            # Detect security findings
            if result.check_name == "static_analysis" and not result.passed:
                security_findings.extend(result.counterexamples)

        # Detect contradictions between verifiers
        contradictions = self._find_contradictions(results)

        checks_run = len(results)
        checks_passed = sum(1 for r in results if r.passed)

        # Determine release decision
        release_decision = self._decide_release(
            results=results,
            claim=claim,
            contract=contract,
            counterexamples=counterexamples,
            security_findings=security_findings,
            contradictions=contradictions,
        )

        # Calculate residual risk
        residual_risk = self._calculate_residual_risk(results, counterexamples)

        return VerificationReport(
            checks_run=checks_run,
            checks_passed=checks_passed,
            counterexamples=counterexamples,
            contradictions=contradictions,
            security_findings=security_findings,
            residual_risk=residual_risk,
            verifier_receipts=receipts,
            release_decision=release_decision,
            details={
                "verifiers_used": [v.name() for v in verifiers],
                "individual_results": [
                    {
                        "verifier": v.name(),
                        "passed": r.passed,
                        "confidence": r.confidence,
                        "details": r.details,
                    }
                    for v, r in zip(verifiers, results)
                ],
            },
        )

    def _decide_release(
        self,
        results: List[VerifierResult],
        claim: Dict[str, Any],
        contract: Optional[Dict[str, Any]],
        counterexamples: List[Any],
        security_findings: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
    ) -> ReleaseDecision:
        """Make a quorum-based release decision."""
        if not results:
            return ReleaseDecision.FAIL

        # Hard failures
        if counterexamples:
            return ReleaseDecision.FAIL

        if security_findings:
            return ReleaseDecision.CONDITIONAL

        if contradictions:
            return ReleaseDecision.CONDITIONAL

        # Quorum calculation
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        pass_rate = passed / total

        # Determine required quorum
        risk_level = claim.get("risk_level", "normal")
        if contract:
            risk_level = contract.get("risk_level", risk_level)

        if risk_level == "high":
            required_quorum = self._high_risk_quorum
        else:
            required_quorum = self._quorum_threshold

        # Weighted by confidence
        weighted_pass = sum(r.confidence for r in results if r.passed)
        weighted_total = sum(r.confidence for r in results)
        weighted_rate = weighted_pass / max(0.001, weighted_total)

        if weighted_rate >= required_quorum:
            return ReleaseDecision.PASS
        elif weighted_rate >= required_quorum * 0.7:
            return ReleaseDecision.CONDITIONAL
        else:
            return ReleaseDecision.FAIL

    def _find_contradictions(
        self, results: List[VerifierResult]
    ) -> List[Dict[str, Any]]:
        """Find contradictions between verifier results."""
        contradictions: List[Dict[str, Any]] = []

        # Simple contradiction: two verifiers checking the same property disagree
        by_check: Dict[str, List[VerifierResult]] = {}
        for r in results:
            base_check = r.check_name.split("_")[0]
            if base_check not in by_check:
                by_check[base_check] = []
            by_check[base_check].append(r)

        for check_type, check_results in by_check.items():
            passed_results = [r for r in check_results if r.passed]
            failed_results = [r for r in check_results if not r.passed]
            if passed_results and failed_results:
                contradictions.append(
                    {
                        "check_type": check_type,
                        "passed_count": len(passed_results),
                        "failed_count": len(failed_results),
                        "details": "Verifiers disagree on this check category.",
                    }
                )

        return contradictions

    def _calculate_residual_risk(
        self,
        results: List[VerifierResult],
        counterexamples: List[Any],
    ) -> float:
        """Calculate residual risk after verification.

        Residual risk is bounded by:
        - 1.0 if there are counterexamples
        - inverse of average confidence of passing checks
        - higher if few checks ran
        """
        if counterexamples:
            return 1.0

        if not results:
            return 1.0

        passed = [r for r in results if r.passed]
        if not passed:
            return 0.95

        avg_confidence = sum(r.confidence for r in passed) / len(passed)
        coverage_factor = min(1.0, len(results) / 3.0)  # 3+ checks = full coverage

        # Residual risk decreases with confidence and coverage
        risk = (1.0 - avg_confidence) * (1.0 / max(0.1, coverage_factor))
        return min(1.0, max(0.0, risk))
