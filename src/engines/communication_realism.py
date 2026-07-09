import random
from typing import Dict, Any, List
from core.random.deterministic_rng import DeterministicRNG

class CommunicationRealismEngine:
    """
    Engine 7: COMMUNICATION REALISM ENGINE
    Generates realistic, dynamic, and unique technical dialogues by parameterizing templates with sensor readings.
    """
    OPERATORS = ["OPS-Alpha", "OPS-Beta", "TECH-Schmidt", "TECH-Patel", "FIELD-1", "FIELD-2"]

    TEMPLATES = {
        "stable": [
            "{op1}: Nominal operations at tick {tick}. Temp stable at {temp}C. No actions required.",
            "{op1}: Pressures holding at {press} bar. Vibs at {vib} mm/s. SCADA status is green.",
            "{op1}: Log entry for shift at tick {tick}. System is in stable state."
        ],
        "thermal_drift": [
            "{op1}: Temp drift detected on bearing 2. Reading is {temp}C. Check cooling loop.",
            "{op1}: German/English shorthand: Throttle valve is sticky. Filter ist schmutzig.",
            "{op1}: High heat alert at tick {tick}: {temp}C. Requesting field inspection."
        ],
        "cavitation_escalation": [
            "{op1}: High vibs on pump. SCADA: {vib} mm/s. Suction press down to {press} bar.",
            "{op1}: Cavitation warning active at tick {tick}. Listen for popping noises.",
            "{op1}: Heavy vibration reported by {op2} on Sector 4. Level: {vib}."
        ],
        "maintenance_recovery": [
            "{op1}: Maintenance crew on-site. Last tech: {tech}. Repairing seals.",
            "{op1}: Wear reduction action completed. Re-engaging driver at tick {tick}.",
            "{op1}: Tweak calibration offset. Post-repair instability expected."
        ],
        "AI_disagreement": [
            "{op1}: AI recommendations state shutdown pump. Trust score is low.",
            "{op1}: Local temp reading is {temp}C. AI is calling for veto. Disagree.",
            "{op1}: Ignoring AI shutdown advice at tick {tick}. Keep running manually."
        ],
        "suppressed_anomaly": [
            "{op1}: Fatigue level high at {fatigue}. Ignoring Sector 3 oil alarm.",
            "{op1}: Warning active at tick {tick}, but operator is too busy to process.",
            "{op1}: Acknowledging warning but postponing intervention. Overload."
        ],
        "false_stability": [
            "{op1}: SCADA shows stable {temp}C, but local gauge reads otherwise.",
            "{op1}: Sensor discrepancy at tick {tick}. Observed {temp}C vs local reality.",
            "{op1}: SCADA values frozen. High projection gap detected by {op2}."
        ],
        "overload_spiral": [
            "{op1}: EMERGENCY: Temp {temp}C, Vibs {vib} mm/s! Overload spiral!",
            "{op1}: Scheisse! Trip breaker at tick {tick}! High stress cascade!",
            "{op1}: Driver is failing! Shut down driver immediately! Operator panic!"
        ]
    }

    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        hidden = world_state.hidden_state
        communication = world_state.communication_state

        regime = hidden.get("active_regime", "stable")
        
        # Get dialogues matching the active regime
        templates = self.TEMPLATES.get(regime, self.TEMPLATES["stable"])
        template = rng.choice(templates)

        # Retrieve variables
        tick = world_state.world_tick
        temp = hidden.get("temperature_level", 50.0)
        vib = hidden.get("vibration_level", 0.05)
        press = hidden.get("pressure_level", 1.0)
        fatigue = round(hidden.get("operator_fatigue", 0.1), 2)
        tech = hidden.get("last_technician_skill", "medium")

        op1 = rng.choice(self.OPERATORS)
        op2 = rng.choice([o for o in self.OPERATORS if o != op1])

        # Interpolate variables to create unique string
        dialogue_line = template.format(
            tick=tick,
            temp=temp,
            vib=vib,
            press=press,
            fatigue=fatigue,
            tech=tech,
            op1=op1,
            op2=op2
        )
        
        # Ensure complete uniqueness with a dynamic reference ID
        dialogue_line += f" (REF-{tick})"

        # Apply high fatigue corruption
        if fatigue > 0.6:
            dialogue_line += f" [static/garbled at tick {tick}]"

        # Update communication state
        communication["last_message"] = dialogue_line
        
        # Initialize log if not present
        if "conversation_history" not in communication:
            communication["conversation_history"] = []
        
        # Store log
        communication["conversation_history"].append({
            "tick": tick,
            "message": dialogue_line,
            "regime": regime
        })
        
        if len(communication["conversation_history"]) > 20:
            communication["conversation_history"].pop(0)

