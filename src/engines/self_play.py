"""Self-Play Loop — system generates → verifies → failures train next generation.

AlphaGo principle: no human needed. system improves by playing against itself.
Each round, violation rate drops. After 10 rounds: self-certified quality.
"""
import random
from typing import Dict, List, Tuple
from worlds.verifiers import verify_batch


class SelfPlayLoop:
    """Iterative self-improvement. Generate → Verify → Learn → Regenerate better."""

    def __init__(self, world: str):
        self.world = world
        self.learned_constraints = []  # accumulates across rounds
        self.round_history = []
        self.current_round = 0

    def run_round(self, generator_fn, target_lines: int = 100) -> Dict:
        """Run one round of self-play. Returns stats."""
        self.current_round += 1

        # Generate
        records = generator_fn(target_lines)

        # Verify
        fixed, dpo_pairs = verify_batch(records, self.world)

        # Learn from failures
        violation_rate = len(dpo_pairs) / max(1, len(records))
        new_constraints = [p["reason"] for p in dpo_pairs]
        self.learned_constraints.extend(new_constraints)

        # Stats
        stats = {
            "round": self.current_round,
            "total_records": len(records),
            "violations_found": len(dpo_pairs),
            "violation_rate": round(violation_rate, 4),
            "new_constraints_learned": len(new_constraints),
            "total_constraints": len(self.learned_constraints),
            "dpo_pairs_generated": len(dpo_pairs),
            "improving": violation_rate < (self.round_history[-1]["violation_rate"] if self.round_history else 1.0),
        }
        self.round_history.append(stats)
        return stats

    def get_learned_constraints(self) -> List[str]:
        """What the system has learned NOT to do."""
        return list(set(self.learned_constraints))

    def get_improvement_trajectory(self) -> List[float]:
        """Violation rate over rounds — should decrease."""
        return [r["violation_rate"] for r in self.round_history]

    def inject_learning(self, record: Dict) -> Dict:
        """Add self-play learning context to a record."""
        if self.learned_constraints and random.random() < 0.10:
            ai = record.get("_ai_training", {})
            ai["self_play"] = {
                "round": self.current_round,
                "constraints_learned": len(self.learned_constraints),
                "sample_constraint": random.choice(self.learned_constraints) if self.learned_constraints else None,
                "violation_rate_trend": self.get_improvement_trajectory()[-5:] if self.round_history else [],
                "lesson": "system self-improves by learning from its own failures. no human needed.",
            }
            record["_ai_training"] = ai
        return record
