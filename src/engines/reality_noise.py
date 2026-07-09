from typing import Dict, Any
from core.random.deterministic_rng import DeterministicRNG

class RealityNoiseEngine:
    """
    Engine 10: REALITY NOISE ENGINE
    Ensures realistic operational profile:
    - 93% ordinary ticks
    - 6% minor anomalies
    - 1% major events
    Uses closed-loop feedback control to stabilize the target distribution over long runs.
    """
    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state

        # Initialize event variables if not present
        if "systemic_stress_level" not in hidden:
            hidden["systemic_stress_level"] = 0.1
        if "anomaly_active" not in hidden:
            hidden["anomaly_active"] = False
        if "major_event_active" not in hidden:
            hidden["major_event_active"] = False
        if "alarm_triggered" not in hidden:
            hidden["alarm_triggered"] = False
        if "vibration_level" not in hidden:
            hidden["vibration_level"] = 0.05
        if "pressure_level" not in hidden:
            hidden["pressure_level"] = 1.0

        # Dynamic feedback tracking
        if "counts_ordinary" not in hidden:
            hidden["counts_ordinary"] = 0
            hidden["counts_minor"] = 0
            hidden["counts_major"] = 0

        total_ticks = max(1, hidden["counts_ordinary"] + hidden["counts_minor"] + hidden["counts_major"])
        
        # Calculate current ratios
        ratio_minor = hidden["counts_minor"] / total_ticks
        ratio_major = hidden["counts_major"] / total_ticks

        # Feedback adjustments to the base thresholds (target: 6% minor, 1% major)
        threshold_major = 0.01
        threshold_minor = 0.07

        if ratio_major < 0.01:
            threshold_major += 0.008
        elif ratio_major > 0.01:
            threshold_major -= 0.008

        if ratio_minor < 0.06:
            threshold_minor += 0.019
        elif ratio_minor > 0.06:
            threshold_minor -= 0.019

        # Roll to determine tick type
        roll = rng.random()

        if roll < threshold_major:
            # Major event
            hidden["major_event_active"] = True
            hidden["anomaly_active"] = False
            hidden["alarm_triggered"] = True
            hidden["counts_major"] += 1
            
            # Subsystem perturbations
            hidden["systemic_stress_level"] = min(1.0, hidden["systemic_stress_level"] + rng.uniform(0.3, 0.5))
            hidden["vibration_level"] = round(hidden.get("vibration_level", 0.05) + rng.uniform(0.05, 0.12), 4)
            hidden["pressure_level"] = round(max(0.1, hidden.get("pressure_level", 1.0) - rng.uniform(0.2, 0.5)), 3)

            world_state.event_log.append({
                "tick": world_state.world_tick,
                "type": "major_incident",
                "message": "Major facility event: sudden line pressure drop and heavy structural vibration."
            })
            
        elif roll < threshold_minor:
            # Minor anomaly
            hidden["major_event_active"] = False
            hidden["anomaly_active"] = True
            hidden["alarm_triggered"] = rng.random() < 0.7  # 70% chance warning triggers
            hidden["counts_minor"] += 1
            
            hidden["systemic_stress_level"] = min(0.6, hidden["systemic_stress_level"] + rng.uniform(0.08, 0.2))
            hidden["vibration_level"] = round(hidden.get("vibration_level", 0.05) + rng.uniform(0.01, 0.03), 4)
            
            world_state.event_log.append({
                "tick": world_state.world_tick,
                "type": "minor_anomaly",
                "message": "Minor operational anomaly: slight vibration increase on driver bearing."
            })
            
        else:
            # Ordinary low-drama tick
            hidden["major_event_active"] = False
            hidden["anomaly_active"] = False
            hidden["alarm_triggered"] = False
            hidden["counts_ordinary"] += 1
            
            hidden["systemic_stress_level"] = max(0.1, round(hidden["systemic_stress_level"] - rng.uniform(0.02, 0.06), 2))
            
            # Vibration level is coupled dynamically to bearing wear, systemic stress, and infrastructure bottlenecks
            bottleneck = hidden.get("macro_bottleneck_index", 0.0)
            expected_vib = 0.04 + (hidden.get("bearing_wear", 0.0) * 0.15) + (hidden.get("systemic_stress_level", 0.1) * 0.05) + bottleneck * 0.35
            new_vib = hidden.get("vibration_level", 0.05) + (expected_vib - hidden.get("vibration_level", 0.05)) * 0.15 + rng.uniform(-0.002, 0.002)
            hidden["vibration_level"] = round(max(0.03, new_vib), 4)
            
            prev_press = hidden.get("pressure_level", 1.0)
            if prev_press < 0.8:
                new_press = prev_press + rng.uniform(0.02, 0.05)
            else:
                new_press = prev_press + rng.uniform(-0.01, 0.01)
            hidden["pressure_level"] = round(max(0.1, min(1.2, new_press)), 3)

