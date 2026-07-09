import math
from typing import Dict, Any, List
from core.random.deterministic_rng import DeterministicRNG

class CausalAuditEngine:
    """
    Engine 9: CAUSAL AUDIT ENGINE
    Validates causal consistency, transition validity, and computes transition entropy.
    """
    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state

        # Initialize audit state if not present
        if "audit_reports" not in hidden:
            hidden["audit_reports"] = []
        if "impossible_transitions_count" not in hidden:
            hidden["impossible_transitions_count"] = 0

        # We validate the latest transition in regime history
        regime_history = hidden.get("regime_history", [])
        
        impossible_detected = False
        
        # Reuse last calculated entropy by default
        if "last_calculated_entropy" in hidden:
            entropy = hidden["last_calculated_entropy"]
        else:
            entropy = 0.0

        if len(regime_history) >= 2:
            prev_regime = regime_history[-2]
            current_regime = regime_history[-1]

            # 1. Impossible Transitions Detection (Continuous Lightweight Verification)
            if prev_regime == "stable" and current_regime == "overload_spiral":
                impossible_detected = True
                hidden["impossible_transitions_count"] += 1
                
                world_state.validation_errors.append(
                    f"Impossible transition: stable -> overload_spiral at tick {world_state.world_tick}"
                )

            # Update online transition matrix incrementally
            if "online_transition_matrix" not in hidden:
                hidden["online_transition_matrix"] = {}
            matrix = hidden["online_transition_matrix"]
            if prev_regime not in matrix:
                matrix[prev_regime] = {}
            matrix[prev_regime][current_regime] = matrix[prev_regime].get(current_regime, 0) + 1

            # 2. Entropy Calculation (Periodic Heavy Audit - run every 10 ticks)
            if world_state.world_tick % 10 == 0 or "last_calculated_entropy" not in hidden:
                entropy = 0.0
                for state, targets in matrix.items():
                    total_transitions = sum(targets.values())
                    if total_transitions > 0:
                        state_entropy = 0.0
                        for count in targets.values():
                            prob = count / total_transitions
                            state_entropy -= prob * math.log2(prob)
                        entropy += state_entropy
                if matrix:
                    entropy /= len(matrix)
                hidden["last_calculated_entropy"] = round(entropy, 4)
                entropy = hidden["last_calculated_entropy"]

        # 3. Create Audit Report
        report = {
            "tick": world_state.world_tick,
            "regime": hidden.get("active_regime", "stable"),
            "entropy": round(entropy, 4),
            "impossible_detected": impossible_detected,
            "projection_gap": hidden.get("projection_gap_from_truth", 0.0),
            "cascading_risk": hidden.get("cascading_risk_factor", 0.0)
        }
        hidden["audit_reports"].append(report)

        # Truncate reports to save memory
        if len(hidden["audit_reports"]) > 100:
            hidden["audit_reports"].pop(0)

        # Generate audit artifact on major discrepancies or impossible transitions
        if impossible_detected:
            world_state.artifacts.append({
                "artifact_type": "causal_audit_report",
                "timestamp": world_state.world_tick,
                "report": report,
                "message": "Causal verification audit failed due to impossible state transition."
            })
