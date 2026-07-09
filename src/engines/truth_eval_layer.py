# Copyright (c) 2024-2026 Ghias (Gowtham Sangadi). All rights reserved.
"""Truth & Eval Layer — ground truth, noisy observation, hidden state, verification.

For every record:
  1. Clean ground-truth state (what ACTUALLY happened)
  2. Noisy observation layer (what agents/humans THINK happened)
  3. Hidden causal state (invisible forces driving events)
  4. Verifier (checks if record is internally plausible)
"""
import random, math
from typing import Dict, List, Tuple, Optional


class TruthLayer:
    """Maintains ground truth separate from observations.
    
    The key insight: in real life, what happened and what people
    THINK happened are different. AI must learn to navigate this gap.
    """

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_truth_observation_pair(self, record: Dict) -> Dict:
        """For any record, generate the truth AND the noisy observation."""
        
        # Ground truth (what actually happened — complete, accurate)
        truth = self._extract_truth(record)
        
        # Noisy observation (what was recorded/perceived — incomplete, biased)
        observation = self._corrupt_observation(truth)
        
        # Hidden causal state (invisible forces that caused this event)
        hidden_state = self._generate_hidden_state(record)
        
        # Verification (is this record internally consistent?)
        verification = self._verify_plausibility(record, truth)
        
        return {
            "ground_truth": truth,
            "noisy_observation": observation,
            "hidden_causal_state": hidden_state,
            "verification": verification,
            "observation_gap": self._measure_gap(truth, observation),
        }

    def _extract_truth(self, record: Dict) -> Dict:
        """What ACTUALLY happened (complete information)."""
        return {
            "actual_event": record.get("event_subtype"),
            "actual_severity": record.get("urgency_score", 0.5),
            "actual_timestamp": record.get("timestamp"),
            "actual_cause": self._true_cause(record),
            "actual_outcome": self._true_outcome(record),
            "actors_involved": self._true_actors(record),
            "resources_consumed": self._true_resources(record),
        }

    def _corrupt_observation(self, truth: Dict) -> Dict:
        """What was PERCEIVED/RECORDED (incomplete, delayed, biased)."""
        observation = {}
        
        # Some fields observed accurately
        observation["observed_event"] = truth["actual_event"]
        
        # Severity often misjudged (over or underestimated)
        severity_bias = self.rng.gauss(0, 0.2)
        observation["perceived_severity"] = max(0, min(1, truth["actual_severity"] + severity_bias))
        observation["severity_bias"] = round(severity_bias, 3)
        
        # Timestamp may be delayed (logged later than happened)
        delay_minutes = self.rng.choices([0, 5, 15, 60, 240], weights=[50, 20, 15, 10, 5])[0]
        observation["reporting_delay_minutes"] = delay_minutes
        
        # Cause often misattributed
        if self.rng.random() < 0.25:
            observation["attributed_cause"] = self._wrong_cause(truth["actual_cause"])
            observation["cause_correct"] = False
        else:
            observation["attributed_cause"] = truth["actual_cause"]
            observation["cause_correct"] = True
        
        # Some information simply missing
        observation["information_completeness"] = round(self.rng.uniform(0.4, 1.0), 2)
        
        # Observer bias
        observation["observer_bias"] = self.rng.choice([
            "none", "recency_bias", "confirmation_bias", "anchoring",
            "availability_heuristic", "optimism_bias", "authority_deference"
        ])
        
        return observation

    def _generate_hidden_state(self, record: Dict) -> Dict:
        """Invisible forces driving events (not directly observable)."""
        hidden_forces = []
        
        # Organizational politics
        if self.rng.random() < 0.3:
            hidden_forces.append({
                "force": "political_pressure",
                "description": self.rng.choice([
                    "budget deadline pressure causing shortcuts",
                    "new manager proving themselves by changing everything",
                    "team conflict causing communication breakdown",
                    "upcoming audit causing documentation theater",
                ]),
                "observable_symptom": "rushed decisions, incomplete documentation",
            })
        
        # Resource exhaustion (invisible until crisis)
        if self.rng.random() < 0.25:
            hidden_forces.append({
                "force": "resource_depletion",
                "description": self.rng.choice([
                    "team has been running at 120% for 3 months",
                    "key person silently job-searching (checked out)",
                    "technical debt accumulated past breaking point",
                    "budget already spent, borrowing from next quarter",
                ]),
                "observable_symptom": "increasing error rates, slower response",
            })
        
        # Accumulated small problems (invisible individually)
        if self.rng.random() < 0.2:
            hidden_forces.append({
                "force": "accumulated_minor_issues",
                "description": "12 small problems individually below threshold, collectively creating systemic fragility",
                "observable_symptom": "system appears healthy by metrics but feels brittle to experienced staff",
            })
        
        # External forces not yet visible
        if self.rng.random() < 0.15:
            hidden_forces.append({
                "force": "approaching_external_shock",
                "description": self.rng.choice([
                    "competitor about to launch disrupting product",
                    "regulation change in 30-day comment period",
                    "key supplier about to go bankrupt",
                    "weather system forming that will impact operations in 72hrs",
                ]),
                "observable_symptom": "none yet — this is truly hidden",
            })
        
        return {
            "hidden_forces": hidden_forces if hidden_forces else [{"force": "none_identified", "description": "situation appears as observed", "observable_symptom": "N/A"}],
            "partial_observability_level": round(self.rng.uniform(0.3, 0.9), 2),
            "what_agents_cannot_see": self._what_is_invisible(record),
        }

    def _verify_plausibility(self, record: Dict, truth: Dict) -> Dict:
        """Check if record is internally consistent."""
        issues = []
        
        # Timestamp consistency
        if record.get("previous_event_gap_minutes", 0) < 0:
            issues.append("negative time gap — impossible")
        
        # Score range checks
        for field in ["urgency_score", "confidence_score"]:
            val = record.get(field)
            if val is not None and (val < 0 or val > 1):
                issues.append(f"{field} out of [0,1] range: {val}")
        
        # Logical consistency
        if record.get("priority_level") == "critical" and record.get("urgency_score", 0) < 0.5:
            issues.append("critical priority but low urgency score — inconsistent")
        
        return {
            "plausible": len(issues) == 0,
            "issues_found": issues,
            "consistency_score": round(1.0 - len(issues) * 0.2, 2),
            "verifiable_claims": self._count_verifiable(record),
        }

    def _measure_gap(self, truth: Dict, observation: Dict) -> Dict:
        """Quantify the gap between truth and observation."""
        severity_gap = abs(truth["actual_severity"] - observation["perceived_severity"])
        cause_correct = observation["cause_correct"]
        
        return {
            "severity_gap": round(severity_gap, 3),
            "cause_attribution_correct": cause_correct,
            "information_loss": round(1 - observation["information_completeness"], 2),
            "reporting_delay": observation["reporting_delay_minutes"],
            "total_distortion_score": round(
                severity_gap * 0.3 + 
                (0 if cause_correct else 0.4) + 
                (1 - observation["information_completeness"]) * 0.3, 3
            ),
            "training_value": "AI must learn: what is RECORDED is not what HAPPENED. always account for observation gap",
        }

    def _true_cause(self, record: Dict) -> str:
        causes = [
            "accumulated fatigue over multiple shifts",
            "process deviation that was normalized over time",
            "resource constraint forcing suboptimal decision",
            "communication failure between teams",
            "equipment degradation below detection threshold",
            "human error under time pressure",
            "system interaction that was not in any manual",
            "environmental factor outside normal parameters",
        ]
        return self.rng.choice(causes)

    def _true_outcome(self, record: Dict) -> str:
        outcomes = [
            "resolved within expected parameters",
            "resolved but with hidden secondary damage",
            "partially resolved — root cause still active",
            "resolved on surface but will recur in 2-4 weeks",
            "fully resolved with process improvement",
        ]
        return self.rng.choice(outcomes)

    def _true_actors(self, record: Dict) -> List[str]:
        return [record.get("primary_actor", "unknown")] + (
            [self.rng.choice(["supervisor_unaware", "colleague_who_noticed", "system_that_logged"])]
            if self.rng.random() < 0.5 else []
        )

    def _true_resources(self, record: Dict) -> Dict:
        return {
            "time_hours": round(self.rng.uniform(0.1, 8), 1),
            "cost_usd": record.get("cost_impact_usd", self.rng.randint(50, 5000)),
            "attention_units": self.rng.randint(1, 10),
            "trust_impact": self.rng.choice(["none", "minor_erosion", "significant_damage", "trust_built"]),
        }

    def _wrong_cause(self, actual_cause: str) -> str:
        wrong_causes = [
            "blamed on individual when system was at fault",
            "attributed to external factor when internal failure",
            "confused symptom with cause",
            "most recent change blamed (recency bias) but actual cause was older",
            "official cause (for report) differs from actual cause (known but unwritten)",
        ]
        return self.rng.choice(wrong_causes)

    def _what_is_invisible(self, record: Dict) -> List[str]:
        invisible = [
            "emotional state of key decision-maker",
            "3 near-misses in past week that went unreported",
            "informal workaround that bypasses safety check",
            "team morale trajectory over past 3 months",
            "competing priorities that forced this corner-cut",
        ]
        return self.rng.sample(invisible, self.rng.randint(1, 3))

    def _count_verifiable(self, record: Dict) -> int:
        """How many claims in this record could be independently verified."""
        verifiable = 0
        if record.get("timestamp"): verifiable += 1
        if record.get("cost_impact_usd"): verifiable += 1
        if record.get("urgency_score"): verifiable += 1
        if record.get("message"): verifiable += 1
        return verifiable


# ═══ DELAYED CONSEQUENCES — actions that pay off or fail LATER ═══
DELAYED_CONSEQUENCES = [
    {"action_now": "skip unit tests to meet deadline",
     "delay": "2-6 weeks", "consequence": "bug reaches production, costs 50x more to fix than writing test would have",
     "hidden_until": "customer reports issue or monitoring catches it",
     "training_value": "AI must learn: speed now = cost later. discount rate for technical debt is NOT zero"},
    {"action_now": "promote fastest performer regardless of team dynamics",
     "delay": "3-6 months", "consequence": "team morale collapses, 3 people quit, institutional knowledge lost",
     "hidden_until": "exit interviews reveal pattern. by then damage is permanent",
     "training_value": "AI must learn: optimizing one metric (individual performance) destroys another (team health)"},
    {"action_now": "defer maintenance because machine still running",
     "delay": "1-12 months", "consequence": "catastrophic failure during peak production. cost: 100x preventive maintenance",
     "hidden_until": "P-F curve reaches functional failure point. warning signs existed but were ignored",
     "training_value": "AI must learn: 'still working' is not 'healthy'. degradation is invisible until catastrophic"},
    {"action_now": "accept slightly lower quality from cheaper supplier",
     "delay": "6-18 months", "consequence": "quality variance creates downstream defects. customer trust erodes. recalls possible",
     "hidden_until": "defect rate crosses threshold OR major customer complains OR regulatory audit finds issue",
     "training_value": "AI must learn: cost savings that reduce quality are LOANS not savings. repaid with interest"},
    {"action_now": "ignore junior team member's concern because too busy",
     "delay": "1-4 weeks", "consequence": "junior was right. problem grows. now requires senior attention (10x cost) that could have been prevented",
     "hidden_until": "problem escalates beyond junior's ability to contain. they stop raising concerns (learned helplessness)",
     "training_value": "AI must learn: dismissing low-status signal is the most expensive mistake in organizations"},
]

# ═══ STATE FIDELITY ENGINE — long memory + partial observability ═══
class StateFidelityEngine:
    """Makes worlds stateful — previous events CHANGE future behavior."""
    
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.history = []  # rolling memory of past events
        self.trust_level = 0.7  # organizational trust (degrades with failures)
        self.resource_pressure = 0.3  # increases over time without relief
        self.accumulated_debt = 0.0  # technical/organizational debt
        self.morale = 0.7
        
    def tick(self, event: Dict) -> Dict:
        """Update state based on event, return state-aware context."""
        # Update internal state
        self._update_state(event)
        
        # Store in history (bounded)
        self.history.append({
            "event": event.get("event_subtype"),
            "severity": event.get("urgency_score", 0.5),
            "timestamp": event.get("timestamp"),
        })
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        # Generate state-aware context
        return {
            "long_memory": {
                "events_in_memory": len(self.history),
                "recurring_pattern": self._detect_pattern(),
                "trend": self._detect_trend(),
            },
            "organizational_state": {
                "trust_level": round(self.trust_level, 2),
                "resource_pressure": round(self.resource_pressure, 2),
                "accumulated_debt": round(self.accumulated_debt, 2),
                "morale": round(self.morale, 2),
                "stability": "stable" if self.trust_level > 0.6 and self.morale > 0.5 else "fragile" if self.trust_level > 0.4 else "crisis",
            },
            "delayed_consequence": self._check_delayed_consequences(),
            "state_affects_current": self._how_state_affects_now(event),
        }
    
    def _update_state(self, event: Dict):
        severity = event.get("urgency_score", 0.5)
        
        # Failures erode trust
        if severity > 0.7:
            self.trust_level = max(0.1, self.trust_level - 0.05)
            self.morale = max(0.1, self.morale - 0.03)
        
        # Success rebuilds slowly
        if severity < 0.3:
            self.trust_level = min(0.95, self.trust_level + 0.01)
            self.morale = min(0.95, self.morale + 0.01)
        
        # Resource pressure accumulates
        self.resource_pressure = min(0.95, self.resource_pressure + 0.005)
        
        # Debt accumulates from shortcuts
        if self.resource_pressure > 0.7:
            self.accumulated_debt += 0.02  # pressure causes shortcuts
    
    def _detect_pattern(self) -> Optional[str]:
        if len(self.history) < 5:
            return None
        recent = [h["event"] for h in self.history[-10:]]
        from collections import Counter
        common = Counter(recent).most_common(1)
        if common and common[0][1] >= 3:
            return f"recurring: {common[0][0]} appeared {common[0][1]} times in last 10 events"
        return None
    
    def _detect_trend(self) -> str:
        if len(self.history) < 5:
            return "insufficient_data"
        recent_severity = [h["severity"] for h in self.history[-10:]]
        first_half = sum(recent_severity[:5]) / 5
        second_half = sum(recent_severity[5:]) / max(1, len(recent_severity[5:]))
        if second_half > first_half + 0.1:
            return "deteriorating"
        elif second_half < first_half - 0.1:
            return "improving"
        return "stable"
    
    def _check_delayed_consequences(self) -> Optional[Dict]:
        if self.accumulated_debt > 0.3 and self.rng.random() < 0.1:
            consequence = self.rng.choice(DELAYED_CONSEQUENCES)
            self.accumulated_debt -= 0.1  # debt partially discharged
            return consequence
        return None
    
    def _how_state_affects_now(self, event: Dict) -> str:
        effects = []
        if self.trust_level < 0.5:
            effects.append("low trust means more verification needed, slower decisions")
        if self.resource_pressure > 0.7:
            effects.append("high resource pressure means corners being cut, quality declining")
        if self.morale < 0.4:
            effects.append("low morale means people not speaking up about problems")
        if self.accumulated_debt > 0.5:
            effects.append("high debt means any new stress could trigger cascade failure")
        return " | ".join(effects) if effects else "system operating within normal parameters"
