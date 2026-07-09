"""
Calibration Metrics — Brier Score & Reliability Diagrams
==========================================================
When a model says "80% confident this will fail", it should
actually fail 80% of the time. This module measures that.

Metrics:
1. Brier Score — Mean squared error of probability predictions (lower = better)
2. Expected Calibration Error (ECE) — Weighted gap between confidence and accuracy
3. Reliability Diagram Data — For plotting (confidence bins vs actual accuracy)
4. Sharpness — How spread out the predictions are (sharp = decisive)

Usage:
    from benchmark.calibration_metrics import CalibrationReport
    report = CalibrationReport()
    report.add_predictions(y_true, y_prob)
    metrics = report.compute()
"""
import numpy as np
import json
import os
import sys
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CalibrationReport:
    """Compute calibration metrics for probabilistic predictions."""

    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.y_true_all = []
        self.y_prob_all = []

    def add_predictions(self, y_true: np.ndarray, y_prob: np.ndarray):
        """Add a batch of predictions.
        
        Args:
            y_true: Binary labels (0 or 1), shape (n_samples,)
            y_prob: Predicted probabilities for positive class, shape (n_samples,)
        """
        self.y_true_all.extend(y_true.tolist())
        self.y_prob_all.extend(y_prob.tolist())

    def brier_score(self) -> float:
        """Brier Score = mean((predicted_prob - actual_outcome)^2).
        
        Range: 0 (perfect) to 1 (worst).
        A model that always predicts 0.5 gets Brier = 0.25 on balanced data.
        """
        y_true = np.array(self.y_true_all)
        y_prob = np.array(self.y_prob_all)
        return float(np.mean((y_prob - y_true) ** 2))

    def expected_calibration_error(self) -> float:
        """ECE = weighted average of |accuracy - confidence| per bin.
        
        Lower is better. 0 = perfectly calibrated.
        """
        y_true = np.array(self.y_true_all)
        y_prob = np.array(self.y_prob_all)
        n = len(y_true)

        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        ece = 0.0

        for i in range(self.n_bins):
            mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
            if mask.sum() == 0:
                continue
            bin_acc = y_true[mask].mean()
            bin_conf = y_prob[mask].mean()
            bin_weight = mask.sum() / n
            ece += bin_weight * abs(bin_acc - bin_conf)

        return float(ece)

    def maximum_calibration_error(self) -> float:
        """MCE = max |accuracy - confidence| across bins."""
        y_true = np.array(self.y_true_all)
        y_prob = np.array(self.y_prob_all)

        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        mce = 0.0

        for i in range(self.n_bins):
            mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
            if mask.sum() == 0:
                continue
            bin_acc = y_true[mask].mean()
            bin_conf = y_prob[mask].mean()
            mce = max(mce, abs(bin_acc - bin_conf))

        return float(mce)

    def reliability_diagram_data(self) -> List[Dict]:
        """Get data for plotting reliability diagram.
        
        Returns list of dicts with:
            - bin_center: center of confidence bin
            - accuracy: actual accuracy in this bin
            - confidence: mean predicted probability in bin
            - count: number of samples in bin
            - gap: confidence - accuracy (positive = overconfident)
        """
        y_true = np.array(self.y_true_all)
        y_prob = np.array(self.y_prob_all)

        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        diagram = []

        for i in range(self.n_bins):
            lo, hi = bin_edges[i], bin_edges[i + 1]
            mask = (y_prob >= lo) & (y_prob < hi)
            count = int(mask.sum())
            if count == 0:
                diagram.append({
                    "bin_center": round((lo + hi) / 2, 2),
                    "accuracy": None,
                    "confidence": None,
                    "count": 0,
                    "gap": None,
                })
            else:
                acc = float(y_true[mask].mean())
                conf = float(y_prob[mask].mean())
                diagram.append({
                    "bin_center": round((lo + hi) / 2, 2),
                    "accuracy": round(acc, 4),
                    "confidence": round(conf, 4),
                    "count": count,
                    "gap": round(conf - acc, 4),
                })

        return diagram

    def sharpness(self) -> float:
        """Sharpness = variance of predicted probabilities.
        
        Higher = model is more decisive (predicts near 0 or 1).
        Lower = model hedges (predicts near 0.5).
        """
        y_prob = np.array(self.y_prob_all)
        return float(np.var(y_prob))

    def compute(self) -> Dict:
        """Compute all calibration metrics."""
        return {
            "brier_score": round(self.brier_score(), 6),
            "expected_calibration_error": round(self.expected_calibration_error(), 6),
            "maximum_calibration_error": round(self.maximum_calibration_error(), 6),
            "sharpness": round(self.sharpness(), 6),
            "n_samples": len(self.y_true_all),
            "reliability_diagram": self.reliability_diagram_data(),
        }


# ═══════════════════════════════════════════════════════════
# BENCHMARK INTEGRATION
# ═══════════════════════════════════════════════════════════

def run_calibration_benchmark(n_events=5000, seed=42):
    """Run calibration benchmark on escalation prediction task.
    
    Uses LightGBM probability outputs and measures how well-calibrated they are.
    """
    import time
    from world_engine.episode import EpisodeGenerator
    from world_engine.registry import INDUSTRIES
    import random

    print("=" * 60)
    print("CALIBRATION BENCHMARK — Brier Score & Reliability")
    print("=" * 60)
    print()

    t0 = time.time()
    rng = random.Random(seed)
    industry_ids = list(INDUSTRIES.keys())
    selected = rng.sample(industry_ids, min(10, len(industry_ids)))
    events_per = n_events // len(selected)

    # Generate events with labels
    features = []
    labels = []  # Binary: did this event escalate? (safety/crisis = escalated)
    
    escalation_categories = {"safety_accidents", "crisis", "mistakes_failures"}

    for idx, iid in enumerate(selected):
        industry = INDUSTRIES[iid]
        ep_seed = seed + idx * 1000
        gen = EpisodeGenerator(industry, seed=ep_seed, year=2024)
        records = gen.generate_episode(target_lines=events_per)

        for i, r in enumerate(records):
            # Features: simple numeric features
            hour = int(r["timestamp"].split("T")[1][:2]) if "T" in r["timestamp"] else 12
            feat = [
                hour / 24.0,
                r.get("involved_count", 1) / 10.0,
                1.0 if r.get("shift") == "night" else 0.0,
                1.0 if r.get("assets_mentioned") else 0.0,
                len(r.get("tags", [])) / 5.0,
                idx / len(selected),  # Industry index (proxy)
            ]
            features.append(feat)

            # Label: does event escalate?
            # Look ahead: if next 5 events contain crisis/safety, this escalated
            is_escalated = 0
            if r["event_category"] in escalation_categories:
                is_escalated = 1
            labels.append(is_escalated)

    X = np.array(features, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)

    print(f"  Data: {len(X)} events, {y.sum()} escalations ({y.mean()*100:.1f}% positive rate)")

    # Train/test split
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Train LightGBM for probability prediction
    try:
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(
            n_estimators=100, max_depth=5, learning_rate=0.1,
            random_state=seed, verbose=-1
        )
        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        model_name = "LightGBM"
    except ImportError:
        # Fallback: logistic regression style
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(random_state=seed, max_iter=200)
        model.fit(X_train, y_train)
        y_prob = model.predict_proba(X_test)[:, 1]
        model_name = "LogisticRegression"

    # Compute calibration
    report = CalibrationReport(n_bins=10)
    report.add_predictions(y_test, y_prob)
    metrics = report.compute()

    elapsed = time.time() - t0

    print(f"\n  Model: {model_name}")
    print(f"  Brier Score:  {metrics['brier_score']:.6f}  (0=perfect, 0.25=random)")
    print(f"  ECE:          {metrics['expected_calibration_error']:.6f}  (0=perfectly calibrated)")
    print(f"  MCE:          {metrics['maximum_calibration_error']:.6f}  (max bin error)")
    print(f"  Sharpness:    {metrics['sharpness']:.6f}  (higher=more decisive)")
    print(f"  Time:         {elapsed:.1f}s")
    print()

    # Reliability diagram (text-based)
    print("  Reliability Diagram:")
    print("  Conf Bin  | Accuracy | Confidence | Count | Gap")
    print("  ----------|----------|------------|-------|--------")
    for bin_data in metrics["reliability_diagram"]:
        if bin_data["count"] > 0:
            gap_str = f"{bin_data['gap']:+.4f}" if bin_data["gap"] is not None else "N/A"
            over = " ← OVER" if bin_data["gap"] and bin_data["gap"] > 0.1 else ""
            under = " ← UNDER" if bin_data["gap"] and bin_data["gap"] < -0.1 else ""
            print(f"  {bin_data['bin_center']:.2f}      | {bin_data['accuracy']:.4f}  | {bin_data['confidence']:.4f}    | {bin_data['count']:5d} | {gap_str}{over}{under}")
        else:
            print(f"  {bin_data['bin_center']:.2f}      |   N/A    |    N/A     |     0 |  N/A")

    print()

    # Interpretation
    if metrics["expected_calibration_error"] < 0.05:
        print("  ✓ WELL CALIBRATED — predictions match reality within 5%")
    elif metrics["expected_calibration_error"] < 0.10:
        print("  ~ MODERATELY CALIBRATED — some confidence/accuracy mismatch")
    else:
        print("  ✗ POORLY CALIBRATED — model confidence doesn't match outcomes")
        print("    Consider: temperature scaling, Platt scaling, or isotonic regression")

    # Add metadata
    metrics["model"] = model_name
    metrics["seed"] = seed
    metrics["n_events"] = n_events
    metrics["elapsed_seconds"] = round(elapsed, 1)

    return metrics


if __name__ == "__main__":
    seeds = [42, 123, 456]
    all_results = []
    
    for s in seeds:
        r = run_calibration_benchmark(n_events=5000, seed=s)
        all_results.append(r)
        print()

    # Summary
    print("=" * 60)
    print("CALIBRATION SUMMARY (across seeds)")
    print("=" * 60)
    avg_brier = np.mean([r["brier_score"] for r in all_results])
    avg_ece = np.mean([r["expected_calibration_error"] for r in all_results])
    print(f"  Mean Brier Score: {avg_brier:.6f}")
    print(f"  Mean ECE:         {avg_ece:.6f}")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "results", "calibration_benchmark_results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  Results saved to: {out_path}")
