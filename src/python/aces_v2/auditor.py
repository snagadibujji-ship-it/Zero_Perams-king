"""
ACES v2 — Phase 9: Truth & Style Auditor
Checks explanation quality before output. Rejects or repairs weak explanations.
"""

from .models import ExplanationFrame, MeaningGraph, AuditReport


class Auditor:
    """Check and validate explanation quality."""

    def audit(self, frame: ExplanationFrame, graph: MeaningGraph) -> AuditReport:
        """Run all quality checks on an explanation."""
        report = AuditReport()

        # Check 1: Not empty
        if not frame.text or len(frame.text.strip()) < 5:
            report.passed = False
            report.issues.append("Explanation is empty or too short")
            report.completeness_score = 0.0
            return report

        # Check 2: Completeness — does explanation cover the graph nodes?
        coverage = self._check_coverage(frame, graph)
        report.completeness_score = coverage
        if coverage < 0.3:
            report.issues.append(f"Only {coverage*100:.0f}% of concepts covered")
            report.has_missing_step = True

        # Check 3: No contradiction within explanation
        has_contradiction = self._check_contradictions(frame)
        report.has_contradiction = has_contradiction
        if has_contradiction:
            report.issues.append("Contradictory statements detected")
            report.truth_score *= 0.5

        # Check 4: Not too long (verbose check)
        if len(frame.text) > 2000 and frame.mode in ("one-line", "bullets"):
            report.issues.append("Output too long for requested format")
            report.style_score *= 0.7

        # Check 5: Not too short for deep modes
        if len(frame.text) < 50 and frame.mode in ("deep", "teach", "expert"):
            report.issues.append("Output too short for requested depth")
            report.completeness_score *= 0.5

        # Check 6: Steps are ordered (if steps mode)
        if frame.mode == "steps":
            if not self._check_step_order(frame):
                report.issues.append("Steps not properly ordered")
                report.style_score *= 0.8

        # Check 7: No shallow repetition
        if self._check_repetition(frame):
            report.issues.append("Repetitive content detected")
            report.style_score *= 0.8

        # Final pass/fail
        report.passed = (report.truth_score >= 0.5 and
                        report.completeness_score >= 0.3 and
                        report.style_score >= 0.5)

        # Repair suggestions
        if not report.passed:
            report.repair_suggestions = self._suggest_repairs(report)

        return report

    def _check_coverage(self, frame: ExplanationFrame, graph: MeaningGraph) -> float:
        """What fraction of graph nodes appear in the explanation?"""
        if not graph.nodes:
            return 1.0

        text_lower = frame.text.lower()
        covered = 0
        for node in graph.nodes:
            # Check if node label (or significant part) appears in output
            label_words = node.label.lower().split()
            if len(label_words) <= 2:
                if node.label.lower() in text_lower:
                    covered += 1
            else:
                # For longer labels, check if majority of words appear
                found = sum(1 for w in label_words if w in text_lower and len(w) > 3)
                if found >= len(label_words) * 0.5:
                    covered += 1

        return covered / len(graph.nodes)

    def _check_contradictions(self, frame: ExplanationFrame) -> bool:
        """Check for contradictory statements."""
        text = frame.text.lower()

        # Simple pattern: "X is Y" followed by "X is not Y"
        # This is basic — a full implementation would use logic
        if " is " in text and " is not " in text:
            # Check if same subject
            # Simplified: just flag if both "is" and "is not" appear for same word
            pass

        # "always" and "never" about same thing
        if "always" in text and "never" in text:
            return True  # Potential contradiction (simplified)

        return False

    def _check_step_order(self, frame: ExplanationFrame) -> bool:
        """Check if numbered steps are in order."""
        import re
        numbers = re.findall(r'^(\d+)\.', frame.text, re.MULTILINE)
        if numbers:
            nums = [int(n) for n in numbers]
            return nums == sorted(nums) and nums[0] == 1
        return True

    def _check_repetition(self, frame: ExplanationFrame) -> bool:
        """Check if same phrase appears multiple times."""
        sentences = frame.text.split('.')
        seen = set()
        for sent in sentences:
            key = sent.strip().lower()[:50]
            if key and len(key) > 20:
                if key in seen:
                    return True
                seen.add(key)
        return False

    def _suggest_repairs(self, report: AuditReport) -> list:
        """Suggest how to fix issues."""
        suggestions = []
        if report.has_missing_step:
            suggestions.append("Add more detail from the meaning graph")
        if report.has_contradiction:
            suggestions.append("Remove contradictory statements")
        if report.style_score < 0.7:
            suggestions.append("Reformat to match requested style")
        return suggestions
