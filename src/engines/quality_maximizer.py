# Copyright (c) 2024-2026 Ghias (Gowtham Sangadi). All rights reserved.
"""Quality Maximizer — applies research-backed quality improvements to all worlds.

KEY RESEARCH FINDINGS (2025-2026):
  - DeepSeek R1: 2K high-quality CoT traces > 100K low-quality examples
  - arxiv 2025: reasoning traces used as training data for smaller models
  - NeurIPS 2025: multi-turn agent data needs realistic human-agent dynamics
  - arxiv 2025: "behavioral fidelity" — preserving temporal/sequential patterns
  - arxiv 2025: "all current generative fidelity metrics are flawed"
  - LLMs forget in long dialogues — state-update prompting needed

QUALITY PRINCIPLES APPLIED:
  1. Every record must have a REASONING TRACE (not just data, but WHY)
  2. Multi-turn coherence (events reference previous events)
  3. Difficulty grading (easy → hard progression within episodes)
  4. Verification markers (can this answer be checked?)
  5. Behavioral fidelity (temporal patterns match real-world rhythms)
"""
import random
from typing import Dict, List


# ═══ REASONING TRACE TEMPLATES — every record gets one ═══
# DeepSeek showed 2K quality traces > 100K garbage. quality = explicit reasoning steps

REASONING_TEMPLATES = {
    "observation_hypothesis_action": {
        "structure": "I observe X → I hypothesize Y because Z → I will do A to verify → Expected outcome B",
        "example": "I observe server latency spiking → hypothesis: database connection pool exhausted because concurrent users doubled → action: check connection count → expect: count at or near max_pool_size",
    },
    "elimination_reasoning": {
        "structure": "possible causes: [A, B, C] → A eliminated because evidence_1 → B eliminated because evidence_2 → C most likely because remaining_evidence",
        "example": "patient has fever + cough: possible: pneumonia, flu, COVID, TB → flu eliminated (wrong season) → COVID eliminated (negative rapid test) → TB eliminated (no exposure) → pneumonia most likely (CXR shows infiltrate)",
    },
    "tradeoff_analysis": {
        "structure": "option A: benefit_a but cost_a → option B: benefit_b but cost_b → chose B because context_c makes cost_a unacceptable",
        "example": "ship by air: arrives 2 days, costs $5000, carbon 250kg → ship by rail: arrives 8 days, costs $800, carbon 30kg → chose rail because customer SLA is 14 days and sustainability pledge active",
    },
    "analogy_transfer": {
        "structure": "problem X in domain A is similar to solved problem Y in domain B because shared_structure → apply solution_Y adapted to context_X",
        "example": "hospital ER triage (limited beds, many patients, varying severity) is structurally identical to CPU scheduling (limited cores, many processes, varying priority) → apply priority queue with aging to prevent starvation of low-acuity patients",
    },
    "temporal_reasoning": {
        "structure": "at time T1 situation was S1 → event E occurred → at T2 situation became S2 → this means M for future T3",
        "example": "at 9am market was stable → at 9:15 large sell order hit → at 9:20 cascade triggered 5% drop → this means stop-losses were clustered at same level. for future: monitor order clustering at key levels",
    },
    "uncertainty_explicit": {
        "structure": "I am {confidence}% sure of X because {evidence}. what would change my mind: {falsification}. what I cannot know: {limitation}",
        "example": "I am 75% sure this is a phishing email because domain is 1 char off from legitimate. what would change my mind: if sender confirms via separate channel. what I cannot know: whether the link is actually malicious without detonating in sandbox",
    },
}

# ═══ DIFFICULTY GRADING — episodes should progress from easy to hard ═══
DIFFICULTY_LEVELS = {
    1: {"name": "basic", "description": "single concept, clear answer, no ambiguity",
        "reasoning_depth": 1, "example": "patient temp 101F → fever → give acetaminophen"},
    2: {"name": "intermediate", "description": "2-3 concepts interact, some ambiguity",
        "reasoning_depth": 2, "example": "patient temp 101F + recent surgery → could be normal post-op OR infection → check WBC and wound"},
    3: {"name": "advanced", "description": "multiple concepts, competing hypotheses, tradeoffs",
        "reasoning_depth": 3, "example": "patient temp 101F + recent surgery + on immunosuppressants → infection risk HIGH but also cant stop immunosuppressants → balance competing risks"},
    4: {"name": "expert", "description": "rare situations, conflicting evidence, no clear answer",
        "reasoning_depth": 4, "example": "patient temp 101F + recent surgery + immunosuppressed + culture positive for rare organism not in formulary → novel situation requiring literature review + infectious disease consult + experimental treatment consideration"},
    5: {"name": "frontier", "description": "unsolved problems, paradigm challenges, true uncertainty",
        "reasoning_depth": 5, "example": "same patient but AI suggests diagnosis with 92% confidence that contradicts experienced clinician's gut. who is right? how do you decide? what is the cost of each type of error?"},
}

# ═══ MULTI-TURN COHERENCE — events should reference previous events ═══
COHERENCE_CONNECTORS = [
    "following up on {prev_event}: {update}",
    "as predicted from {prev_event}, now seeing {consequence}",
    "contrary to expectations from {prev_event}, actual outcome is {surprise}",
    "escalation of {prev_event}: situation has {direction} since last assessment",
    "resolution of {prev_event}: {resolution}. lessons: {lesson}",
    "related to {prev_event} in {other_thread}: {connection}",
]

# ═══ VERIFICATION MARKERS — can this be checked? ═══
VERIFIABILITY = {
    "verifiable_numeric": {"description": "claim can be checked against objective measurement",
        "example": "server response time is 450ms → CHECK: run benchmark, compare to SLA threshold of 200ms"},
    "verifiable_logical": {"description": "reasoning chain can be validated step by step",
        "example": "if A→B and B→C then A→C. each step checkable independently"},
    "partially_verifiable": {"description": "some aspects checkable, others require judgment",
        "example": "code has no bugs (testable) AND is well-designed (judgment)"},
    "unverifiable_judgment": {"description": "requires human expertise, no objective test",
        "example": "is this the RIGHT architectural choice for 5 years from now?"},
    "falsifiable": {"description": "specific prediction that future will prove/disprove",
        "example": "if we dont fix this tech debt, we will have outage within 3 months"},
}

# ═══ BEHAVIORAL FIDELITY — real-world temporal patterns ═══
TEMPORAL_PATTERNS = {
    "burst_then_quiet": "real work comes in bursts. 10 events in 5 minutes then nothing for 2 hours. not evenly distributed",
    "end_of_day_rush": "decisions pile up at 4:30pm because people avoid them all day then cant leave without resolving",
    "monday_catchup": "first hour of Monday is processing everything that accumulated over weekend",
    "pre_deadline_panic": "2-3 days before deadline, activity 5x normal. quality drops. errors spike",
    "post_incident_flood": "after major incident, 48 hours of follow-up, documentation, post-mortems, blame",
    "seasonal_rhythm": "Q4 is always rushed (budget year end). Q1 is planning. Q2-Q3 is execution",
}


class QualityMaximizer:
    """Applies DeepSeek-level quality improvements to any world's records."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.episode_position = 0
        self.prev_events = []

    def enhance_record(self, record: Dict, episode_length: int) -> Dict:
        """Add quality markers that make training data DeepSeek-tier."""
        ai = record.get("_ai_training", {})

        # 1. Add explicit reasoning trace (MOST IMPORTANT — DeepSeek proved this)
        ai["reasoning_trace"] = self._generate_reasoning_trace(record)

        # 2. Difficulty grading (progressive within episode)
        progress = self.episode_position / max(1, episode_length)
        difficulty = min(5, 1 + int(progress * 4) + self.rng.randint(0, 1))
        ai["difficulty_level"] = DIFFICULTY_LEVELS[difficulty]["name"]
        ai["reasoning_depth"] = DIFFICULTY_LEVELS[difficulty]["reasoning_depth"]

        # 3. Multi-turn coherence (reference previous events)
        if self.prev_events and self.rng.random() < 0.3:
            prev = self.rng.choice(self.prev_events[-5:])
            ai["coherence_link"] = {
                "references_event": prev,
                "relationship": self.rng.choice(["consequence_of", "escalation_of", "resolution_of", "contradicts", "confirms"]),
            }

        # 4. Verification marker
        ai["verifiability"] = self.rng.choice(list(VERIFIABILITY.keys()))

        # 5. Falsifiable prediction (teaches AI to make testable claims)
        if self.rng.random() < 0.2:
            ai["prediction"] = {
                "claim": self._generate_prediction(record),
                "testable_by": self.rng.choice(["24_hours", "1_week", "1_month", "end_of_quarter"]),
                "confidence": round(self.rng.uniform(0.5, 0.95), 2),
            }

        # Update state
        self.prev_events.append(record.get("event_subtype", "unknown"))
        self.episode_position += 1
        record["_ai_training"] = ai
        return record

    def _generate_reasoning_trace(self, record: Dict) -> Dict:
        """Generate explicit step-by-step reasoning for this record."""
        template_name = self.rng.choice(list(REASONING_TEMPLATES.keys()))
        template = REASONING_TEMPLATES[template_name]

        event = record.get("event_subtype", "event")
        msg = record.get("message", "")[:50]

        return {
            "type": template_name,
            "structure": template["structure"],
            "applied": f"for {event}: {msg}",
            "steps": self._build_steps(template_name, record),
        }

    def _build_steps(self, template: str, record: Dict) -> List[str]:
        """Build reasoning steps specific to this event."""
        event = record.get("event_subtype", "event")
        if template == "observation_hypothesis_action":
            return [
                f"step 1: observe — {event} occurred",
                f"step 2: hypothesize — most likely cause based on context",
                f"step 3: verify — check specific indicator to confirm/deny",
                f"step 4: act — based on verified hypothesis",
            ]
        elif template == "elimination_reasoning":
            return [
                f"step 1: list all possible explanations for {event}",
                f"step 2: eliminate impossible based on available evidence",
                f"step 3: rank remaining by likelihood",
                f"step 4: test most likely first (optimize for expected information gain)",
            ]
        elif template == "tradeoff_analysis":
            return [
                f"step 1: identify competing options for handling {event}",
                f"step 2: list costs and benefits of each",
                f"step 3: weight by context (what matters MOST right now?)",
                f"step 4: decide and document WHY (for future reference)",
            ]
        else:
            return [
                f"step 1: understand situation ({event})",
                f"step 2: reason about implications",
                f"step 3: decide on action",
                f"step 4: predict outcome",
            ]

    def _generate_prediction(self, record: Dict) -> str:
        """Generate a falsifiable prediction from current state."""
        predictions = [
            "if current trend continues, threshold will be breached within predicted timeframe",
            "intervention taken will show measurable effect within observation window",
            "without action, situation will deteriorate by estimated percentage",
            "pattern observed will repeat next cycle based on historical frequency",
        ]
        return self.rng.choice(predictions)
