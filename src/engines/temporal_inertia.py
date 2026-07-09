from typing import Dict, Any, List
from core.random.deterministic_rng import DeterministicRNG

class TemporalInertiaEngine:
    """
    Engine 1: TEMPORAL INERTIA ENGINE
    Handles delayed causality, rolling state memory, hysteresis, and persistence decay.
    """
    def __init__(self, history_limit: int = 10):
        self.history_limit = history_limit

    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state
        
        # Initialize temporal structures if not present
        if "temporal_history" not in hidden:
            hidden["temporal_history"] = []
        if "lagged_effects" not in hidden:
            hidden["lagged_effects"] = []
        if "recovery_debt" not in hidden:
            hidden["recovery_debt"] = 0.0
        if "inertia_momentum" not in hidden:
            hidden["inertia_momentum"] = {}

        # Capture a snapshot of current core variables for the rolling memory
        snapshot = {
            "tick": world_state.world_tick,
            "stress": hidden.get("systemic_stress_level", 0.0),
            "vibration": hidden.get("vibration_level", 0.0),
            "temperature": hidden.get("temperature_level", 0.0)
        }
        hidden["temporal_history"].append(snapshot)
        if len(hidden["temporal_history"]) > self.history_limit:
            hidden["temporal_history"].pop(0)

        # 1. Hysteresis (Sticky States)
        # State transitions lag behind stimulus. For example, if stress rises, temperature rises immediately.
        # But if stress falls, temperature stays elevated and decays slowly (hysteresis).
        current_stress = hidden.get("systemic_stress_level", 0.0)
        prev_stress = 0.0
        if len(hidden["temporal_history"]) > 1:
            prev_stress = hidden["temporal_history"][-2]["stress"]

        # Baseline temperature model coupled to systemic stress, friction from bearing wear, and infrastructure bottlenecks
        bottleneck = hidden.get("macro_bottleneck_index", 0.0)
        target_temp = 50.0 + (current_stress * 25.0) + (hidden.get("bearing_wear", 0.0) * 35.0) + bottleneck * 45.0
        current_temp = hidden.get("temperature_level", 50.0)

        if current_stress < prev_stress:
            # Hysteresis decay rate: cooling down is slower than heating up
            cooldown_rate = 0.08 - (hidden["recovery_debt"] * 0.05)
            cooldown_rate = max(0.01, cooldown_rate)
            new_temp = current_temp - (current_temp - target_temp) * cooldown_rate
        else:
            # Heating up is rapid
            new_temp = current_temp + (target_temp - current_temp) * 0.35

        hidden["temperature_level"] = round(new_temp, 2)

        # 2. Lag Propagation / Delayed Subsystem Response
        # Events placed in lagged_effects are evaluated when their target tick arrives
        current_tick = world_state.world_tick
        active_effects = []
        remaining_effects = []
        for effect in hidden["lagged_effects"]:
            if effect["trigger_tick"] <= current_tick:
                active_effects.append(effect)
            else:
                remaining_effects.append(effect)
        hidden["lagged_effects"] = remaining_effects

        # Process triggers
        for effect in active_effects:
            source = effect["source"]
            target_var = effect["target_var"]
            magnitude = effect["magnitude"]
            # Apply delayed effect to hidden state
            hidden[target_var] = round(hidden.get(target_var, 0.0) + magnitude, 3)
            # Log as a causal trace event
            world_state.event_log.append({
                "tick": current_tick,
                "type": "lagged_causal_effect",
                "message": f"Delayed effect from {source} triggered on {target_var} with magnitude {magnitude}"
            })

        # 3. Persistence Decay & Recovery Debt
        # Higher stress builds recovery debt which slows down recovery of mechanical components
        if current_stress > 0.7:
            hidden["recovery_debt"] = min(1.0, hidden["recovery_debt"] + 0.05)
        else:
            hidden["recovery_debt"] = max(0.0, hidden["recovery_debt"] - 0.02)
