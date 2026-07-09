from typing import Dict, Any, List
from core.random.deterministic_rng import DeterministicRNG

class RegimeIntelligenceEngine:
    """
    Engine 5: REGIME INTELLIGENCE ENGINE
    Identifies the active operational regime, manages regime persistence, and uses transition matrices.
    Target Regimes:
    - stable
    - thermal_drift
    - cavitation_escalation
    - maintenance_recovery
    - AI_disagreement
    - suppressed_anomaly
    - false_stability
    - overload_spiral
    """
    REGIMES = [
        "stable",
        "thermal_drift",
        "cavitation_escalation",
        "maintenance_recovery",
        "AI_disagreement",
        "suppressed_anomaly",
        "false_stability",
        "overload_spiral"
    ]

    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state

        # Initialize regime state if not present
        if "active_regime" not in hidden:
            hidden["active_regime"] = "stable"
        if "regime_duration" not in hidden:
            hidden["regime_duration"] = 0
        if "regime_history" not in hidden:
            hidden["regime_history"] = []

        current_regime = hidden["active_regime"]
        
        # 1. Determine next candidate regime based on state indicators
        stress = hidden.get("systemic_stress_level", 0.0)
        temp = hidden.get("temperature_level", 50.0)
        vib = hidden.get("vibration_level", 0.05)
        fatigue = hidden.get("operator_fatigue", 0.15)
        trust = hidden.get("ai_trust", 0.85)
        anomaly = hidden.get("anomaly_active", False)
        alarm = hidden.get("alarm_triggered", False)
        suppression = hidden.get("alarm_suppression_active", False)
        repaired = hidden.get("maintenance_repaired_tick", -1) == world_state.world_tick

        candidate_regime = "stable"

        if stress > 0.85 and temp > 80.0:
            candidate_regime = "overload_spiral"
        elif repaired:
            candidate_regime = "maintenance_recovery"
        elif suppression and alarm:
            candidate_regime = "suppressed_anomaly"
        elif trust < 0.4 and alarm:
            candidate_regime = "AI_disagreement"
        elif anomaly and not alarm:
            candidate_regime = "false_stability"
        elif vib > 0.15:
            candidate_regime = "cavitation_escalation"
        elif temp > 65.0:
            candidate_regime = "thermal_drift"

        # 2. Stickiness via Transition Matrix / Probability Check
        # Regimes are sticky; switching shouldn't happen instantly unless stress is high.
        # We define a transition probability from current_regime to candidate_regime.
        transition_prob = 0.25  # Base transition probability
        if current_regime == candidate_regime:
            transition_prob = 1.0
        elif current_regime == "overload_spiral":
            # Very sticky, hard to escape without maintenance
            transition_prob = 0.05 if candidate_regime == "maintenance_recovery" else 0.01
        elif current_regime == "maintenance_recovery":
            # Remains in recovery mode for a couple of ticks
            transition_prob = 0.4 if hidden["regime_duration"] > 3 else 0.1

        # Check if we transition
        if rng.random() < transition_prob:
            next_regime = candidate_regime
        else:
            next_regime = current_regime

        # Update duration and state
        if next_regime == current_regime:
            hidden["regime_duration"] += 1
        else:
            hidden["active_regime"] = next_regime
            hidden["regime_duration"] = 1
            
            # Log transition event
            world_state.event_log.append({
                "tick": world_state.world_tick,
                "type": "regime_transition",
                "message": f"System regime transitioned from '{current_regime}' to '{next_regime}'."
            })

        # Append to history
        hidden["regime_history"].append(next_regime)
        if len(hidden["regime_history"]) > 50:
            hidden["regime_history"].pop(0)
