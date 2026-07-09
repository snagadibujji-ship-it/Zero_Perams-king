from typing import Dict, Any
from core.random.deterministic_rng import DeterministicRNG

class FailureEcologyEngine:
    """
    Engine 4: FAILURE ECOLOGY ENGINE
    Models cascading failures, latent damage, compound faults, contamination persistence,
    and hidden degradation accumulation.
    """
    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state

        # Initialize failure/degradation variables if not present
        if "microfracture_density" not in hidden:
            hidden["microfracture_density"] = 0.05
        if "lubricant_contamination" not in hidden:
            hidden["lubricant_contamination"] = 0.02
        if "bearing_wear" not in hidden:
            hidden["bearing_wear"] = 0.0
        if "cascading_risk_factor" not in hidden:
            hidden["cascading_risk_factor"] = 0.0
        if "failure_occurring" not in hidden:
            hidden["failure_occurring"] = False

        # Get relevant operational parameters
        vibration = hidden.get("vibration_level", 0.05)
        temperature = hidden.get("temperature_level", 50.0)
        stress = hidden.get("systemic_stress_level", 0.0)
        anomaly_active = hidden.get("anomaly_active", False)

        # 1. Microfracture Propagation
        # Microfractures grow with vibration and high temperature
        vib_stress = max(0.0, vibration - 0.05) * 2.0
        temp_stress = max(0.0, temperature - 70.0) * 0.005
        growth = (vib_stress + temp_stress) * 0.01
        
        # Scale by macro wear growth multiplier (tech diffusion / scarcity)
        macro_wear_mult = hidden.get("macro_wear_growth_multiplier", 1.0)
        growth *= macro_wear_mult
        
        # Exponential growth factor if already deteriorated
        if hidden["microfracture_density"] > 0.4:
            growth *= 1.5
            
        # Accelerate microfracture propagation under severe bearing wear (grinding races)
        if hidden.get("bearing_wear", 0.0) > 0.7:
            growth *= 4.5
        
        hidden["microfracture_density"] = min(1.0, hidden["microfracture_density"] + growth)

        # 2. Lubricant Contamination
        # Accumulates over time, accelerated by operating temperature and systemic stress
        contam_growth = 0.001
        if temperature > 80.0:
            contam_growth += 0.005
        if stress > 0.8:
            contam_growth += 0.01
        
        # Scale by macro contamination growth multiplier
        macro_contam_mult = hidden.get("macro_contamination_growth_multiplier", 1.0)
        contam_growth *= macro_contam_mult
        
        hidden["lubricant_contamination"] = min(1.0, hidden["lubricant_contamination"] + contam_growth)

        # 3. Bearing Wear Memory
        # Accelerated by both microfractures and contaminated lubricant (compound faults)
        compound_multiplier = 1.0 + (hidden["microfracture_density"] * 2.0) + (hidden["lubricant_contamination"] * 1.5)
        wear_growth = 0.002 * compound_multiplier * macro_wear_mult
        hidden["bearing_wear"] = min(1.0, hidden["bearing_wear"] + wear_growth)

        # 4. Cascading Failures Risk Factor
        # Likelihood of failure cascading to another subsystem
        hidden["cascading_risk_factor"] = round(
            (hidden["microfracture_density"] * 0.4) +
            (hidden["bearing_wear"] * 0.4) +
            (hidden["lubricant_contamination"] * 0.2), 3
        )

        # Check if a component failure is triggered
        if hidden["cascading_risk_factor"] > 0.75:
            # High probability of actual physical failure
            if rng.random() < 0.15:
                hidden["failure_occurring"] = True
                hidden["vibration_level"] = round(hidden.get("vibration_level", 0.05) + 0.1, 4)
                hidden["temperature_level"] = round(hidden.get("temperature_level", 50.0) + 15.0, 2)
                
                world_state.event_log.append({
                    "tick": world_state.world_tick,
                    "type": "mechanical_failure",
                    "message": "Subsystem wear triggered a bearing failure cascade."
                })
        else:
            hidden["failure_occurring"] = False
