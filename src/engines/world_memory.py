from typing import Dict, Any, List
from core.random.deterministic_rng import DeterministicRNG

class WorldMemoryEngine:
    """
    Engine 8: WORLD MEMORY ENGINE
    Maintains long-term persistent subsystem memory.
    Ensures past failures leave permanent "scars" that affect future operational states.
    """
    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state
        
        # Initialize memory structures if not present
        if "historical_scars" not in hidden:
            hidden["historical_scars"] = []
        if "base_failure_rate" not in hidden:
            hidden["base_failure_rate"] = 0.01

        # Initialize cached wear penalty if not present
        if "historical_wear_penalty" not in hidden:
            hidden["historical_wear_penalty"] = round(sum(s["permanent_wear_penalty"] for s in hidden["historical_scars"]), 3)

        # Check if a mechanical failure occurred in this tick (using O(1) state tracker)
        failure_logged = hidden.get("failure_occurring", False)

        # 1. If a failure happened, record a permanent "scar"
        if failure_logged:
            scar = {
                "failed_at_tick": world_state.world_tick,
                "degradation_severity": hidden.get("cascading_risk_factor", 0.8),
                "permanent_wear_penalty": 0.05  # Permanent wear added to the baseline
            }
            hidden["historical_scars"].append(scar)
            hidden["historical_wear_penalty"] = round(hidden["historical_wear_penalty"] + 0.05, 3)
            
            # Increase baseline risk permanently
            hidden["base_failure_rate"] = round(hidden["base_failure_rate"] + 0.02, 3)

            # Log scar creation
            world_state.event_log.append({
                "tick": world_state.world_tick,
                "type": "scar_recorded",
                "message": f"Historical scar recorded at tick {world_state.world_tick}. Base failure rate increased to {hidden['base_failure_rate']}."
            })

        # 2. Condition future states based on history
        # Bearing wear and microfractures have a baseline increase derived from historical scars
        wear_penalty = hidden["historical_wear_penalty"]

        # Wear cannot drop below wear_penalty, even after repairs (imperfect repairs logic integration)
        hidden["bearing_wear"] = max(wear_penalty, hidden.get("bearing_wear", 0.0))
        hidden["microfracture_density"] = max(wear_penalty * 0.8, hidden.get("microfracture_density", 0.05))
