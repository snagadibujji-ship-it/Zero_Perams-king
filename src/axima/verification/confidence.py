"""Confidence interval arithmetic and uncertainty conservation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ConfidenceInterval:
    """A confidence interval with provenance of how it was derived."""

    lower: float
    upper: float
    method: str = "unknown"

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError(
                f"lower ({self.lower}) cannot exceed upper ({self.upper})"
            )
        if self.lower < 0.0 or self.upper > 1.0:
            raise ValueError(
                f"Confidence must be in [0,1], got [{self.lower}, {self.upper}]"
            )

    @property
    def width(self) -> float:
        """Width of the interval (uncertainty)."""
        return self.upper - self.lower

    @property
    def midpoint(self) -> float:
        """Center point of the interval."""
        return (self.lower + self.upper) / 2.0

    @property
    def is_certain(self) -> bool:
        """True if interval has zero width (point estimate)."""
        return abs(self.upper - self.lower) < 1e-12

    def contains(self, value: float) -> bool:
        """Check if a value falls within this interval."""
        return self.lower <= value <= self.upper

    def overlaps(self, other: "ConfidenceInterval") -> bool:
        """Check if two intervals overlap."""
        return self.lower <= other.upper and other.lower <= self.upper

    def intersect(self, other: "ConfidenceInterval") -> Optional["ConfidenceInterval"]:
        """Return the intersection of two intervals, or None if disjoint."""
        new_lower = max(self.lower, other.lower)
        new_upper = min(self.upper, other.upper)
        if new_lower > new_upper:
            return None
        return ConfidenceInterval(
            lower=new_lower,
            upper=new_upper,
            method=f"intersect({self.method},{other.method})",
        )


class UncertaintyConservation:
    """Combines confidence intervals respecting conservation rules.

    Core rules:
    1. Combined confidence is bounded by the weakest evidence
    2. Correlated sources share independence groups (counted once)
    3. Rendering/formatting never raises confidence
    4. Interval arithmetic for propagation
    """

    def combine(
        self,
        intervals: List[ConfidenceInterval],
        independence_groups: Optional[Dict[str, List[int]]] = None,
    ) -> ConfidenceInterval:
        """Combine multiple confidence intervals respecting independence.

        Args:
            intervals: List of confidence intervals from different sources.
            independence_groups: Maps group name to list of interval indices
                               that belong to that group. Intervals in the
                               same group are treated as a single source.

        Returns:
            Combined confidence interval (conservative).
        """
        if not intervals:
            return ConfidenceInterval(lower=0.0, upper=1.0, method="empty")

        if len(intervals) == 1:
            return ConfidenceInterval(
                lower=intervals[0].lower,
                upper=intervals[0].upper,
                method=f"single({intervals[0].method})",
            )

        # Resolve independence groups
        effective_intervals = self._resolve_groups(intervals, independence_groups)

        # Rule 1: bounded by weakest evidence
        min_lower = min(ci.lower for ci in effective_intervals)
        min_upper = min(ci.upper for ci in effective_intervals)

        # For independent sources, we can strengthen slightly
        # but never above the minimum upper bound
        if len(effective_intervals) > 1:
            # Independent combination: product of (1 - lower) gives combined lower
            combined_lower = self._independent_lower(effective_intervals)
            # But still bounded by weakest individual
            combined_lower = max(combined_lower, min_lower)
            # Upper bounded by weakest evidence
            combined_upper = min_upper
        else:
            combined_lower = min_lower
            combined_upper = min_upper

        # Ensure valid interval
        combined_lower = min(combined_lower, combined_upper)

        return ConfidenceInterval(
            lower=combined_lower,
            upper=combined_upper,
            method=f"combined({len(effective_intervals)}_sources)",
        )

    def propagate_through_derivation(
        self,
        intervals: List[ConfidenceInterval],
        derivation_steps: int = 1,
    ) -> ConfidenceInterval:
        """Propagate confidence through a derivation chain.

        Each derivation step can only maintain or reduce confidence.
        Confidence degrades with more hops.
        """
        if not intervals:
            return ConfidenceInterval(lower=0.0, upper=1.0, method="empty_derivation")

        # Start with the combined interval
        base = self.combine(intervals)

        # Each derivation step reduces confidence
        # Using geometric decay: conf * (1 - decay_per_step)^steps
        decay_per_step = 0.05  # 5% confidence loss per hop
        decay_factor = (1.0 - decay_per_step) ** derivation_steps

        new_lower = base.lower * decay_factor
        new_upper = base.upper  # Upper stays (conservative)

        return ConfidenceInterval(
            lower=max(0.0, new_lower),
            upper=min(1.0, new_upper),
            method=f"derivation({derivation_steps}_steps,base={base.method})",
        )

    def apply_rendering_cap(
        self,
        interval: ConfidenceInterval,
        source_intervals: List[ConfidenceInterval],
    ) -> ConfidenceInterval:
        """Apply the rendering-never-raises-confidence rule.

        The rendered output confidence cannot exceed the minimum
        confidence of any source used in rendering.
        """
        if not source_intervals:
            return interval

        max_allowed_upper = min(ci.upper for ci in source_intervals)
        max_allowed_lower = min(ci.lower for ci in source_intervals)

        return ConfidenceInterval(
            lower=min(interval.lower, max_allowed_lower),
            upper=min(interval.upper, max_allowed_upper),
            method=f"render_capped({interval.method})",
        )

    def weaken(
        self,
        interval: ConfidenceInterval,
        factor: float,
    ) -> ConfidenceInterval:
        """Weaken a confidence interval by a factor (for heuristic downgrade).

        Args:
            interval: Original interval.
            factor: Weakening factor in (0, 1]. 1.0 = no change, 0.5 = halve lower.
        """
        if not 0.0 < factor <= 1.0:
            raise ValueError(f"factor must be in (0, 1], got {factor}")

        new_lower = interval.lower * factor
        # Upper stays or gets slightly weakened
        new_upper = interval.upper * (1.0 - (1.0 - factor) * 0.5)

        return ConfidenceInterval(
            lower=max(0.0, new_lower),
            upper=min(1.0, new_upper),
            method=f"weakened({factor},{interval.method})",
        )

    def from_verifier_results(
        self,
        results: List[Any],
    ) -> ConfidenceInterval:
        """Convert a list of VerifierResult objects to a confidence interval.

        Uses the range of reported confidences as the interval.
        """
        if not results:
            return ConfidenceInterval(lower=0.0, upper=1.0, method="no_results")

        confidences = [
            getattr(r, "confidence", 0.5) for r in results if getattr(r, "passed", False)
        ]

        if not confidences:
            return ConfidenceInterval(lower=0.0, upper=0.3, method="all_failed")

        return ConfidenceInterval(
            lower=min(confidences),
            upper=max(confidences),
            method=f"from_verifiers({len(confidences)}_passed)",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_groups(
        self,
        intervals: List[ConfidenceInterval],
        independence_groups: Optional[Dict[str, List[int]]],
    ) -> List[ConfidenceInterval]:
        """Collapse correlated sources into single representative intervals."""
        if not independence_groups:
            return intervals

        # Find which indices belong to groups
        grouped_indices: Set[int] = set()
        group_representatives: List[ConfidenceInterval] = []

        for group_name, indices in independence_groups.items():
            valid_indices = [i for i in indices if i < len(intervals)]
            if not valid_indices:
                continue
            grouped_indices.update(valid_indices)

            # For correlated sources, take the weakest (most conservative)
            group_intervals = [intervals[i] for i in valid_indices]
            representative = ConfidenceInterval(
                lower=min(ci.lower for ci in group_intervals),
                upper=min(ci.upper for ci in group_intervals),
                method=f"group({group_name})",
            )
            group_representatives.append(representative)

        # Add ungrouped intervals
        ungrouped = [
            intervals[i] for i in range(len(intervals)) if i not in grouped_indices
        ]

        return group_representatives + ungrouped

    def _independent_lower(
        self, intervals: List[ConfidenceInterval]
    ) -> float:
        """Combine independent lower bounds.

        For independent sources, P(all wrong) = product of P(each wrong).
        So combined lower = 1 - product(1 - lower_i).
        """
        if not intervals:
            return 0.0

        prob_all_wrong = 1.0
        for ci in intervals:
            prob_all_wrong *= (1.0 - ci.lower)

        return 1.0 - prob_all_wrong
