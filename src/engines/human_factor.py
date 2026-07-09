from typing import Dict, Any
from core.random.deterministic_rng import DeterministicRNG

class HumanFactorEngine:
    """
    Engine 2: HUMAN FACTOR ENGINE
    Models operator fatigue, cognitive overload, trust decay, alarm suppression,
    procedural drift, and panic behavior.
    """
    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state
        
        # Initialize human variables if not present
        if "operator_fatigue" not in hidden:
            hidden["operator_fatigue"] = 0.15
        if "cognitive_load" not in hidden:
            hidden["cognitive_load"] = 0.1
        if "ai_trust" not in hidden:
            hidden["ai_trust"] = 0.85
        if "alarm_suppression_active" not in hidden:
            hidden["alarm_suppression_active"] = False
        if "procedural_drift" not in hidden:
            hidden["procedural_drift"] = 0.0

        current_stress = hidden.get("systemic_stress_level", 0.0)
        anomaly_active = hidden.get("anomaly_active", False)
        major_event = hidden.get("major_event_active", False)

        # 1. Update Fatigue and Cognitive Load
        # Fatigue increments with stress and major/minor events
        fatigue_growth = 0.02
        if anomaly_active:
            fatigue_growth += 0.05
        if major_event:
            fatigue_growth += 0.15
        
        if current_stress < 0.3 and not anomaly_active:
            # Recuperation during boring periods
            hidden["operator_fatigue"] = max(0.05, hidden["operator_fatigue"] - 0.04)
            hidden["cognitive_load"] = max(0.05, hidden["cognitive_load"] - 0.06)
        else:
            hidden["operator_fatigue"] = min(1.0, hidden["operator_fatigue"] + fatigue_growth)
            hidden["cognitive_load"] = min(1.0, (current_stress * 0.5) + (0.5 * hidden["operator_fatigue"]))

        # 2. AI Trust Evolution
        # Trust decays if alarms are frequent but no actual failure is happening (false alarms)
        # Trust also decays if a surprise failure happens that the AI did not predict.
        alarm_triggered = hidden.get("alarm_triggered", False)
        actual_failure = hidden.get("failure_occurring", False)

        if alarm_triggered and not actual_failure:
            hidden["ai_trust"] = max(0.0, hidden["ai_trust"] - 0.05)
        elif not alarm_triggered and actual_failure:
            hidden["ai_trust"] = max(0.0, hidden["ai_trust"] - 0.15)
        elif alarm_triggered and actual_failure:
            # Positive reinforcement of trust
            hidden["ai_trust"] = min(1.0, hidden["ai_trust"] + 0.03)

        # 3. Alarm Suppression
        # Fatigue > 0.7 triggers alarm suppression behavior (operator ignores warnings to reduce stress)
        if hidden["operator_fatigue"] > 0.7:
            hidden["alarm_suppression_active"] = True
            hidden["procedural_drift"] = min(1.0, hidden["procedural_drift"] + 0.05)
        else:
            hidden["alarm_suppression_active"] = False
            hidden["procedural_drift"] = max(0.0, hidden["procedural_drift"] - 0.02)

        # 4. Panic Behavior and Delayed Reactions
        # Under extreme cognitive load (> 0.8), operators make mistakes or delay actions
        hidden["panic_mode"] = hidden["cognitive_load"] > 0.8
        
        # Log human actions
        if hidden["alarm_suppression_active"] and alarm_triggered:
            world_state.event_log.append({
                "tick": world_state.world_tick,
                "type": "human_action",
                "message": "Operator suppressed warning/alarm due to cognitive fatigue."
            })
