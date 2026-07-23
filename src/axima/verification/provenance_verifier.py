"""Provenance verification: citations, temporal validity, source independence."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .verifier_base import Verifier, VerifierResult


# ---------------------------------------------------------------------------
# ProvenanceVerifier
# ---------------------------------------------------------------------------


class ProvenanceVerifier(Verifier):
    """Checks citation validity and source spans."""

    def name(self) -> str:
        return "provenance_check"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return "citations" in claim or "sources" in claim

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        citations = claim.get("citations", claim.get("sources", []))
        source_corpus = evidence.get("corpus", {})

        if not citations:
            return VerifierResult(
                passed=False,
                check_name="provenance_check",
                details="No citations provided for claim.",
                confidence=0.7,
            )

        valid_count = 0
        invalid: List[Dict[str, Any]] = []

        for citation in citations:
            result = self._validate_citation(citation, source_corpus)
            if result["valid"]:
                valid_count += 1
            else:
                invalid.append(result)

        total = len(citations)
        passed = valid_count > 0 and len(invalid) == 0

        return VerifierResult(
            passed=passed,
            check_name="provenance_check",
            details=f"{valid_count}/{total} citations valid.",
            counterexamples=invalid,
            confidence=min(0.95, valid_count / max(1, total)),
        )

    def _validate_citation(
        self, citation: Dict[str, Any], corpus: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single citation against the corpus."""
        source_id = citation.get("source_id", citation.get("id", ""))
        span_start = citation.get("span_start", 0)
        span_end = citation.get("span_end", 0)
        quoted_text = citation.get("text", "")

        # Check source exists
        if source_id and source_id not in corpus:
            return {
                "valid": False,
                "source_id": source_id,
                "reason": "Source not found in corpus.",
            }

        # If corpus contains the source, verify span
        if source_id and source_id in corpus:
            source_text = corpus[source_id]
            if span_start >= 0 and span_end > span_start:
                actual_text = source_text[span_start:span_end]
                if quoted_text and quoted_text not in actual_text:
                    return {
                        "valid": False,
                        "source_id": source_id,
                        "reason": "Quoted text not found at specified span.",
                    }
            elif quoted_text and quoted_text not in source_text:
                return {
                    "valid": False,
                    "source_id": source_id,
                    "reason": "Quoted text not found in source.",
                }

        return {"valid": True, "source_id": source_id}


# ---------------------------------------------------------------------------
# TemporalVerifier
# ---------------------------------------------------------------------------


class TemporalVerifier(Verifier):
    """Checks time validity of claims (freshness, temporal consistency)."""

    def name(self) -> str:
        return "temporal_validity"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        return (
            "timestamp" in claim
            or "valid_until" in claim
            or "as_of" in claim
            or claim.get("type") == "temporal"
        )

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        now = time.time()
        issues: List[Dict[str, Any]] = []

        # Check if claim has expired
        valid_until = claim.get("valid_until")
        if valid_until is not None:
            if isinstance(valid_until, (int, float)) and valid_until < now:
                issues.append(
                    {
                        "type": "expired",
                        "valid_until": valid_until,
                        "current_time": now,
                        "expired_seconds_ago": now - valid_until,
                    }
                )

        # Check source freshness
        source_timestamp = claim.get("timestamp", evidence.get("timestamp"))
        freshness_requirement = claim.get("freshness_seconds")
        if source_timestamp and freshness_requirement:
            age = now - source_timestamp
            if age > freshness_requirement:
                issues.append(
                    {
                        "type": "stale_source",
                        "source_age_seconds": age,
                        "max_allowed_seconds": freshness_requirement,
                    }
                )

        # Check temporal ordering of evidence
        evidence_timestamps = evidence.get("timestamps", [])
        if len(evidence_timestamps) > 1:
            for i in range(1, len(evidence_timestamps)):
                if evidence_timestamps[i] < evidence_timestamps[i - 1]:
                    issues.append(
                        {
                            "type": "temporal_ordering_violation",
                            "position": i,
                            "earlier": evidence_timestamps[i - 1],
                            "later": evidence_timestamps[i],
                        }
                    )

        # Check "as_of" claim — claim states something true at a specific time
        as_of = claim.get("as_of")
        if as_of and source_timestamp:
            # Source must predate or match the "as_of" time
            if source_timestamp > as_of:
                issues.append(
                    {
                        "type": "source_postdates_claim",
                        "source_time": source_timestamp,
                        "claim_as_of": as_of,
                    }
                )

        if issues:
            return VerifierResult(
                passed=False,
                check_name="temporal_validity",
                details=f"{len(issues)} temporal issue(s) found.",
                counterexamples=issues,
                confidence=0.9,
            )

        return VerifierResult(
            passed=True,
            check_name="temporal_validity",
            details="Temporal constraints satisfied.",
            confidence=0.85,
        )


# ---------------------------------------------------------------------------
# IndependenceVerifier
# ---------------------------------------------------------------------------


class IndependenceVerifier(Verifier):
    """Checks source independence — correlated sources not counted separately."""

    def name(self) -> str:
        return "source_independence"

    def applicable(self, claim: Dict[str, Any]) -> bool:
        sources = claim.get("sources", claim.get("citations", []))
        return len(sources) > 1

    def verify(
        self,
        claim: Dict[str, Any],
        evidence: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifierResult:
        sources = claim.get("sources", claim.get("citations", []))
        known_groups = evidence.get("independence_groups", {})
        correlation_matrix = evidence.get("correlation_matrix", {})

        source_ids = [s.get("source_id", s.get("id", f"src_{i}")) for i, s in enumerate(sources)]
        groups = self._identify_groups(source_ids, known_groups, correlation_matrix)

        independent_count = len(groups)
        total_count = len(source_ids)

        if independent_count < total_count:
            # Some sources are correlated
            correlated_sets = [g for g in groups if len(g) > 1]
            details = (
                f"{total_count} sources collapse to {independent_count} independent group(s). "
                f"Correlated sets: {correlated_sets}"
            )
            # Not a failure per se, but reduces effective evidence
            return VerifierResult(
                passed=True,
                check_name="source_independence",
                details=details,
                counterexamples=[{"correlated_groups": correlated_sets}],
                confidence=independent_count / max(1, total_count),
            )

        return VerifierResult(
            passed=True,
            check_name="source_independence",
            details=f"All {total_count} sources appear independent.",
            confidence=0.8,
        )

    def _identify_groups(
        self,
        source_ids: List[str],
        known_groups: Dict[str, List[str]],
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> List[Set[str]]:
        """Group sources by correlation/dependence."""
        # Start with each source in its own group
        groups: List[Set[str]] = [set([sid]) for sid in source_ids]

        # Merge based on known groups
        for group_name, members in known_groups.items():
            member_set = set(members)
            relevant = [g for g in groups if g & member_set]
            if len(relevant) > 1:
                merged = set()
                for g in relevant:
                    merged |= g
                    groups.remove(g)
                groups.append(merged)

        # Merge based on correlation matrix (threshold 0.8)
        threshold = 0.8
        for src_a, correlations in correlation_matrix.items():
            for src_b, corr_val in correlations.items():
                if corr_val >= threshold and src_a != src_b:
                    # Find groups containing src_a and src_b
                    group_a = next((g for g in groups if src_a in g), None)
                    group_b = next((g for g in groups if src_b in g), None)
                    if group_a and group_b and group_a is not group_b:
                        merged = group_a | group_b
                        groups.remove(group_a)
                        groups.remove(group_b)
                        groups.append(merged)

        return groups
