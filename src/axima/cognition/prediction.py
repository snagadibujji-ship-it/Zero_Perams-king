"""Prediction engine — calibrated forecasting with no post-hoc rewriting.

Predictions are recorded BEFORE outcomes are observed.  Once recorded, a
prediction's claim, predicted_outcome, and confidence are immutable.
Calibration and Brier scores are computed over the resolved prediction history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Prediction:
    """A single recorded prediction — immutable once created."""

    id: str
    claim: str
    predicted_outcome: Any
    confidence: float  # 0.0–1.0
    timestamp: datetime
    resolution_deadline: datetime
    actual_outcome: Optional[Any] = None
    resolved_at: Optional[datetime] = None
    correct: Optional[bool] = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be in [0, 1], got {self.confidence}")
        if self.resolution_deadline <= self.timestamp:
            raise ValueError("Resolution deadline must be after prediction timestamp")


class PredictionEngine:
    """Manages the prediction lifecycle: predict → observe → score."""

    def __init__(self) -> None:
        self._predictions: Dict[str, Prediction] = {}
        self._history: List[Prediction] = []

    @property
    def predictions(self) -> Dict[str, Prediction]:
        return dict(self._predictions)

    def predict(
        self,
        claim: str,
        predicted_outcome: Any,
        confidence: float,
        resolution_deadline: datetime,
    ) -> Prediction:
        """Record a prediction BEFORE the outcome is known.

        Returns the immutable Prediction record.
        """
        now = datetime.now(timezone.utc)
        pred = Prediction(
            id=str(uuid.uuid4()),
            claim=claim,
            predicted_outcome=predicted_outcome,
            confidence=confidence,
            timestamp=now,
            resolution_deadline=resolution_deadline,
        )
        self._predictions[pred.id] = pred
        return pred

    def record_outcome(self, prediction_id: str, actual_outcome: Any) -> Prediction:
        """Record the actual outcome for a previously made prediction.

        The original claim and confidence are NEVER modified (no post-hoc rewriting).
        """
        if prediction_id not in self._predictions:
            raise KeyError(f"Prediction {prediction_id} not found")

        pred = self._predictions[prediction_id]
        if pred.actual_outcome is not None:
            raise ValueError(f"Prediction {prediction_id} already resolved — no rewriting allowed")

        now = datetime.now(timezone.utc)
        # Determine correctness
        correct = pred.predicted_outcome == actual_outcome

        # Create resolved copy (original fields untouched)
        resolved = Prediction(
            id=pred.id,
            claim=pred.claim,
            predicted_outcome=pred.predicted_outcome,
            confidence=pred.confidence,
            timestamp=pred.timestamp,
            resolution_deadline=pred.resolution_deadline,
            actual_outcome=actual_outcome,
            resolved_at=now,
            correct=correct,
        )
        self._predictions[prediction_id] = resolved
        self._history.append(resolved)
        return resolved

    def calibration_score(self, n_bins: int = 10) -> float:
        """Compute calibration error (ECE — Expected Calibration Error).

        Groups predictions into bins by confidence and computes the weighted
        average |accuracy − confidence| across bins.  Lower is better (0 = perfect).
        """
        resolved = [p for p in self._history if p.correct is not None]
        if not resolved:
            return 0.0

        bin_width = 1.0 / n_bins
        total_error = 0.0
        total_count = len(resolved)

        for i in range(n_bins):
            lo = i * bin_width
            hi = lo + bin_width
            bucket = [p for p in resolved if lo <= p.confidence < hi or (i == n_bins - 1 and p.confidence == 1.0 and lo <= p.confidence <= hi)]
            if not bucket:
                continue
            avg_confidence = sum(p.confidence for p in bucket) / len(bucket)
            accuracy = sum(1 for p in bucket if p.correct) / len(bucket)
            total_error += len(bucket) * abs(accuracy - avg_confidence)

        return total_error / total_count if total_count else 0.0

    def brier_score(self) -> float:
        """Compute Brier score over resolved predictions.

        Brier score = mean( (confidence − outcome)^2 ) where outcome ∈ {0, 1}.
        Lower is better (0 = perfect).
        """
        resolved = [p for p in self._history if p.correct is not None]
        if not resolved:
            return 0.0

        total = 0.0
        for p in resolved:
            outcome = 1.0 if p.correct else 0.0
            total += (p.confidence - outcome) ** 2
        return total / len(resolved)

    def get_resolved(self) -> List[Prediction]:
        """Return all resolved predictions."""
        return list(self._history)

    def get_pending(self) -> List[Prediction]:
        """Return predictions awaiting resolution."""
        return [p for p in self._predictions.values() if p.correct is None]
