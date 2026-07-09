# Copyright (c) 2024-2026 Ghias (Gowtham Sangadi). All rights reserved.
"""Agent Training Engine — makes our data the #1 dataset for training AI agents.

CRITICAL RESEARCH (2025-2026):
  - NeurIPS 2025 MAST taxonomy: 14 failure modes in 3 categories, validated on 1600+ traces
  - Augment 2026: multi-agent systems fail at 41-86.7% rate in production
  - 79% of failures from: specification ambiguity + unstructured coordination
  - Gartner: 1,445% surge in enterprise multi-agent inquiries (2024-2025)
  - Gartner: 40% of agentic projects will be CANCELLED by 2027
  - MIT 2026: 35% of businesses deployed agents, 44% planning to
  - HuggingFace: agent loop = Thought → Action → Observation cycle
  - AI agent memory market: $6.27B in 2026, growing 35% CAGR
  - ICLR 2025: 30% accuracy DROP in multi-session memory tasks

WHAT AGENTS NEED TO LEARN (that no dataset teaches):
  1. THOUGHT-ACTION-OBSERVATION loops (not just Q&A)
  2. TOOL CALLING decisions (when to use which tool, and when NOT to)
  3. DELEGATION logic (when to hand off to another agent)
  4. FAILURE RECOVERY (what to do when action fails)
  5. STATE PERSISTENCE (remembering across sessions)
  6. COORDINATION (working with other agents without duplication)
  7. HUMAN HANDOFF (knowing when to escalate to human)
"""
import random
from typing import Dict, List

# ═══ THOUGHT-ACTION-OBSERVATION FORMAT ═══
# This is how agents actually work. Our data must teach this loop.
TAO_EXAMPLES = [
    {"thought": "user wants to book a flight. I need to check availability first, then compare prices, then book",
     "action": {"tool": "flight_search", "params": {"origin": "NYC", "dest": "LAX", "date": "2024-03-15"}},
     "observation": "3 flights available: $299 (6hr direct), $189 (9hr 1-stop), $450 (5hr direct premium)",
     "next_thought": "cheapest is $189 but 9 hours. user hasn't stated preference. need to ask. DONT assume they want cheapest — maybe they value time",
     "lesson": "agents must ask when preferences are ambiguous, not assume"},
    {"thought": "server is down. I need to diagnose. first check if it's the server or the network",
     "action": {"tool": "ping", "params": {"host": "prod-server-1", "count": 5}},
     "observation": "5/5 packets received, avg 2ms. network is fine. problem is application-level",
     "next_thought": "network confirmed good. now check application logs. but wait — should I check if OTHER servers are affected first? if all servers down = different root cause than single server",
     "lesson": "before going deep on one theory, check breadth first. scope the problem before solving it"},
    {"thought": "patient's lab results are back. potassium is 6.8 (critical high). this is life-threatening. need immediate action",
     "action": {"tool": "notify_physician", "params": {"urgency": "STAT", "finding": "K+ 6.8", "patient": "bed_4B"}},
     "observation": "physician acknowledged. orders: calcium gluconate IV, insulin+dextrose, kayexalate, repeat K in 2hr",
     "next_thought": "orders received. executing. but I should also check — WHY is potassium high? renal failure? medication? acidosis? treating the number without understanding cause = it will come back",
     "lesson": "treat the emergency AND investigate the root cause simultaneously"},
]

# ═══ TOOL CALLING DECISIONS ═══
TOOL_DECISIONS = [
    {"scenario": "user asks what the weather is like",
     "correct_decision": "USE tool — weather is real-time data I cannot know from training",
     "wrong_decision": "answer from training data — weather changes. stale data = wrong answer",
     "meta_rule": "use tool when: information is time-sensitive, user-specific, or requires computation I can't do in my head"},
    {"scenario": "user asks to explain recursion",
     "correct_decision": "DONT use tool — this is knowledge I have from training. tool call adds latency for no value",
     "wrong_decision": "search the web for 'what is recursion' — wastes time, I already know this perfectly",
     "meta_rule": "skip tool when: information is stable, general knowledge, and unlikely to have changed since training"},
    {"scenario": "user asks to check their bank balance",
     "correct_decision": "USE tool with authentication — this is private, real-time, user-specific data",
     "wrong_decision": "make up a number or say I can't help — I CAN help by calling the right API",
     "meta_rule": "when data is private + real-time: use authenticated tool. never hallucinate private data"},
    {"scenario": "user asks should they accept a job offer",
     "correct_decision": "DONT use tool — this requires judgment, not data retrieval. help them think through it",
     "wrong_decision": "search 'should I accept job offer' — generic results don't apply to their specific situation",
     "meta_rule": "when decision requires personal judgment: facilitate thinking, don't retrieve generic advice"},
]

# ═══ DELEGATION LOGIC — when to hand off to another agent ═══
DELEGATION_PATTERNS = [
    {"situation": "coding agent encounters legal compliance question in the code",
     "correct": "DELEGATE to legal/compliance agent. I am not qualified. my answer could create liability",
     "wrong": "try to answer from training data — legal advice from a coding agent is dangerous",
     "handoff_protocol": "preserve context (what code, what regulation seems relevant, what I was trying to do), hand off with clear question, wait for response before continuing"},
    {"situation": "customer support agent encounters suicidal ideation in user message",
     "correct": "IMMEDIATE escalation to human crisis specialist. this is beyond any AI agent's capability",
     "wrong": "try to provide counseling — AI agents should NEVER handle mental health crises autonomously",
     "handoff_protocol": "warm handoff (stay until human connects), provide crisis hotline immediately, preserve conversation for human context"},
    {"situation": "planning agent realizes task requires information it doesn't have access to",
     "correct": "DELEGATE to research agent with specific questions. don't guess. don't hallucinate",
     "wrong": "make assumptions to fill gaps — planning on wrong assumptions = wasted execution",
     "handoff_protocol": "explicit list of unknowns, priority order, acceptable confidence threshold for each"},
]

# ═══ FAILURE RECOVERY (14 failure modes from MAST taxonomy) ═══
AGENT_FAILURES = {
    "specification_failures": [
        {"mode": "goal_ambiguity", "description": "task described but success criteria unclear",
         "detection": "agent asks 'am I done?' without knowing when to stop",
         "recovery": "pause execution. ask user for explicit completion criteria. dont guess"},
        {"mode": "role_confusion", "description": "multiple agents, unclear who does what",
         "detection": "two agents do the same sub-task. or a sub-task is skipped because each assumes other handles it",
         "recovery": "orchestrator must assign explicit ownership. every task has exactly ONE owner"},
        {"mode": "constraint_violation", "description": "agent achieves goal but violates unstated constraint",
         "detection": "goal met but user unhappy. 'I said fix the bug, not rewrite the whole module'",
         "recovery": "confirm scope and constraints BEFORE acting. 'I plan to do X. any constraints I should know about?'"},
    ],
    "coordination_failures": [
        {"mode": "deadlock", "description": "agent A waits for B, B waits for A. both stuck forever",
         "detection": "no progress for >timeout period. both agents in 'waiting' state",
         "recovery": "timeout + escalation. after N seconds, break deadlock by having orchestrator decide priority"},
        {"mode": "duplicate_work", "description": "two agents independently do the same task",
         "detection": "same output produced by multiple agents. wasted compute and potentially conflicting results",
         "recovery": "shared task board with claim/lock mechanism. before starting, check if already claimed"},
        {"mode": "context_loss_at_handoff", "description": "agent B receives task from A but critical context is lost",
         "detection": "B asks questions that A already answered. or B makes decisions that contradict A's findings",
         "recovery": "structured handoff format: [goal, constraints, progress, findings, open_questions, context_that_must_not_be_lost]"},
        {"mode": "infinite_loop", "description": "agent keeps retrying failed action without changing approach",
         "detection": "same action attempted >3 times with same result. no adaptation",
         "recovery": "mandatory strategy change after 2 failures. if same approach fails twice, try fundamentally different approach"},
    ],
    "verification_failures": [
        {"mode": "no_verification", "description": "agent produces output but never checks if it's correct",
         "detection": "output accepted without validation. errors reach user/production",
         "recovery": "mandatory verification step: every output must be checked against success criteria before delivery"},
        {"mode": "self_verification_blindness", "description": "agent checks its own work but cannot find its own mistakes",
         "detection": "self-review passes but external review finds errors. agent has blind spots to own logic errors",
         "recovery": "use different agent for verification. the generator should NOT be the verifier (separation of concerns)"},
    ],
}

# ═══ MULTI-SESSION STATE ═══
STATE_PATTERNS = [
    {"pattern": "user_preference_learning", "description": "agent remembers user prefers concise answers, dark mode, metric units",
     "persistence": "cross_session", "update_trigger": "explicit correction or repeated implicit signal",
     "failure_mode": "preference stored from 6 months ago is now wrong. user changed. stale preferences = annoying agent"},
    {"pattern": "task_continuation", "description": "user left mid-task yesterday. resumes today. agent picks up exactly where left off",
     "persistence": "cross_session", "update_trigger": "user returns to same thread/project",
     "failure_mode": "world changed overnight. code was merged by someone else. agent's saved state is outdated"},
    {"pattern": "learned_tool_usage", "description": "agent learned that for THIS user, tool X works better than tool Y",
     "persistence": "permanent", "update_trigger": "repeated success with one approach over another",
     "failure_mode": "overfitting to one user's workflow. new similar user gets suboptimal tool choice"},
]

# ═══ HUMAN HANDOFF SIGNALS ═══
HUMAN_HANDOFF_TRIGGERS = [
    {"signal": "confidence_below_threshold", "threshold": 0.4,
     "action": "I'm not confident enough to act on this autonomously. handing to human with my analysis so far",
     "meta": "knowing when you're uncertain is more valuable than always trying to answer"},
    {"signal": "irreversible_action_requested", "threshold": "any",
     "action": "this action cannot be undone (delete data, send to customer, deploy to production). requiring human confirmation",
     "meta": "agents should have asymmetric caution: reversible=act, irreversible=ask"},
    {"signal": "emotional_content_detected", "threshold": "any",
     "action": "user appears distressed/angry/confused beyond task scope. flagging for human empathy",
     "meta": "AI can provide information but cannot provide genuine empathy. know the difference"},
    {"signal": "ethical_ambiguity", "threshold": "any",
     "action": "multiple valid perspectives exist. this is a values question not a factual question. human must decide",
     "meta": "agents should NEVER make ethical decisions autonomously. present options, human decides"},
    {"signal": "novel_situation_no_precedent", "threshold": "any",
     "action": "I have never encountered this specific combination before. no training data covers this. human creativity needed",
     "meta": "the most dangerous agent is one that extrapolates confidently into unknown territory"},
]


class AgentTrainingEngine:
    """Adds multi-agent training dimensions to any record."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def enrich_for_agents(self, record: Dict, world: str = None) -> Dict:
        """Add agent-specific training signals to a record."""
        ai = record.get("_ai_training", {})

        # 1. THOUGHT-ACTION-OBSERVATION (15% of records get full TAO example)
        if self.rng.random() < 0.15:
            ai["agent_tao_example"] = self.rng.choice(TAO_EXAMPLES)

        # 2. TOOL DECISION (10% get tool-calling reasoning)
        if self.rng.random() < 0.10:
            ai["tool_decision"] = self.rng.choice(TOOL_DECISIONS)

        # 3. DELEGATION (8% get delegation logic)
        if self.rng.random() < 0.08:
            ai["delegation_pattern"] = self.rng.choice(DELEGATION_PATTERNS)

        # 4. FAILURE MODE (6% get a failure example with recovery)
        if self.rng.random() < 0.06:
            category = self.rng.choice(list(AGENT_FAILURES.keys()))
            ai["agent_failure_mode"] = self.rng.choice(AGENT_FAILURES[category])

        # 5. STATE MANAGEMENT (5%)
        if self.rng.random() < 0.05:
            ai["state_pattern"] = self.rng.choice(STATE_PATTERNS)

        # 6. HUMAN HANDOFF (8% get handoff signal)
        if self.rng.random() < 0.08:
            ai["human_handoff"] = self.rng.choice(HUMAN_HANDOFF_TRIGGERS)

        # 7. WORLD-SPECIFIC AGENT SCENARIO (12% — domain-specific multi-agent)
        if world and world in WORLD_AGENT_SCENARIOS and self.rng.random() < 0.12:
            scenario = WORLD_AGENT_SCENARIOS[world]
            ai["multi_agent_scenario"] = {
                "team": scenario["agent_team"],
                "workflow": scenario["workflow"],
                "failure_scenario": scenario["failure_scenario"],
                "coordination_challenge": scenario["coordination_challenge"],
                "training_example": self.rng.choice(scenario["training_examples"]),
            }

        # 8. SELF-REFLECTION (8% — teaches agents to learn from mistakes)
        if self.rng.random() < 0.08:
            ai["self_reflection"] = self.rng.choice(REFLECTION_PATTERNS)

        # 9. SAFETY GUARDRAILS (6% — 5-layer defense model)
        if self.rng.random() < 0.06:
            layer = self.rng.choice(list(SAFETY_LAYERS.keys()))
            ai["safety_guardrail"] = SAFETY_LAYERS[layer]

        # 10. TRUST DYNAMICS (5% — how agents trust/distrust each other)
        if self.rng.random() < 0.05:
            trust_type = self.rng.choice(list(TRUST_DYNAMICS.keys()))
            ai["trust_dynamic"] = TRUST_DYNAMICS[trust_type]

        # 11. PLANNING HORIZON (6% — short vs long term conflict)
        if self.rng.random() < 0.06:
            ai["planning_horizon"] = self.rng.choice(PLANNING_HORIZONS)

        # 12. AGENT EQ (7% — emotional intelligence with humans)
        if self.rng.random() < 0.07:
            ai["agent_eq"] = self.rng.choice(AGENT_EQ)

        record["_ai_training"] = ai
        return record


# ═══════════════════════════════════════════════════════════════════
# WORLD-SPECIFIC AGENT SCENARIOS — real multi-agent patterns per domain
# Based on 2025-2026 research on actual deployed agent systems
# ═══════════════════════════════════════════════════════════════════

WORLD_AGENT_SCENARIOS = {
    "industries": {
        "agent_team": ["monitoring_agent", "diagnostic_agent", "maintenance_agent", "safety_agent", "production_agent", "supply_agent"],
        "workflow": "monitoring detects anomaly → diagnostic identifies root cause → maintenance schedules repair → safety assesses risk → production adjusts schedule → supply orders parts",
        "real_stats": "ISA-18.2: operators see 600 alarms/hour, respond to none. predictive maintenance catches failures 6-12 months before breakdown via vibration+temp correlation. P-F curve: vibration (months) → temperature (weeks) → noise (days) → failure",
        "failure_scenario": "monitoring agent floods diagnostic with 600 alarms. diagnostic cant distinguish real anomaly from nuisance. real bearing failure buried in noise. cascade: bearing fails → shaft damages → production line stops → $2M/day loss",
        "coordination_challenge": "safety agent says STOP PRODUCTION immediately (risk to humans). production agent says keep running (contractual penalty $500K if late). who has authority? safety must ALWAYS override production but pressure is real",
        "training_examples": [
            {"agent": "diagnostic", "thought": "vibration on pump 7 increased 40% over 3 weeks. temperature steady. this pattern matches inner-race bearing defect from P-F library. estimated 4-6 weeks to failure. NOT urgent but must act before it becomes urgent",
             "action": "schedule maintenance window in 2 weeks. order replacement bearing NOW (3-day lead time). notify production: pump 7 will be offline 4 hours on planned date. do NOT wait until failure"},
            {"agent": "safety", "thought": "gas detector reading 15ppm H2S in zone 3. threshold is 10ppm. workers in zone. this is not a discussion — this is an evacuation",
             "action": "OVERRIDE ALL: emergency evacuation zone 3 IMMEDIATELY. production agent: STOP operations in zone 3. monitoring agent: continuous sampling until below 5ppm. NO agent can countermand safety evacuation. lives > production"},
            {"agent": "monitoring", "thought": "alarm count this hour: 347. ISA-18.2 says max 6 per 10 min. operators ignoring everything. I must PRIORITIZE — which of these 347 actually need human attention?",
             "action": "filter: suppress 340 nuisance alarms (known, non-actionable). escalate 5 as PRIORITY-1 (new, actionable, consequential). present 2 as INFO-ONLY. reduce cognitive load from 347 to 7. this is alarm rationalization in real-time"},
        ],
    },
    "coding": {
        "agent_team": ["planner_agent", "coder_agent", "tester_agent", "reviewer_agent", "deployer_agent"],
        "workflow": "planner decomposes task → coder generates code → tester writes+runs tests → reviewer checks quality → deployer pushes to production",
        "real_stats": "SWE-bench: best agents achieve only 12% on real industry mobile apps. agentic stack decomposes engineering into narrowly-scoped interacting components",
        "failure_scenario": "coder generates code that passes tests but reviewer catches architectural violation. rollback needed. planner must re-decompose",
        "coordination_challenge": "coder and tester have different context windows. test agent doesn't know WHY code was written that way. tests pass but intent is wrong",
        "training_examples": [
            {"agent": "planner", "thought": "this bug requires changes in 3 files. assigning file-1 to coder-A and file-2 to coder-B. BUT they share state — need to coordinate order",
             "action": "decompose with dependency graph: file-1 must complete BEFORE file-2 starts (shared interface)"},
            {"agent": "reviewer", "thought": "code is correct but I notice it introduces tight coupling between modules. this will be painful in 6 months. reject with architectural feedback",
             "action": "REJECT PR with explanation: 'works now but creates tech debt. suggest: extract interface, dependency inject'"},
        ],
    },
    "healthcare": {
        "agent_team": ["triage_agent", "diagnosis_agent", "treatment_agent", "pharmacy_agent", "monitoring_agent", "coordination_agent"],
        "workflow": "triage scores severity → diagnosis generates differential → treatment proposes plan → pharmacy checks interactions → monitoring tracks response → coordinator manages handoffs",
        "real_stats": "MedCoAct 2025: multi-agent framework integrates doctor+pharmacist agents for complete clinical decisions. DynamiCare: dynamic team adapts composition based on case. Multi-agent runs use 65-fold FEWER tokens than single agent",
        "failure_scenario": "diagnosis agent confident (90%) but pharmacy agent flags critical drug interaction. treatment must be revised. who has authority? requires confidence-weighted consensus",
        "coordination_challenge": "patient deteriorates during handoff between monitoring and treatment agents. 30% accuracy drop in multi-session memory. critical context lost",
        "training_examples": [
            {"agent": "pharmacy", "thought": "treatment agent prescribed warfarin but I see patient is already on aspirin. major bleeding risk. must OVERRIDE treatment recommendation",
             "action": "FLAG interaction. escalate to human physician. do NOT administer until resolved. patient safety > agent consensus"},
            {"agent": "coordinator", "thought": "night shift starting. transferring 12 patients from day agents. each has different priority. must ensure NO information lost in handoff",
             "action": "structured handoff: for each patient → [active_issues, pending_results, escalation_criteria, overnight_plan]"},
        ],
    },
    "finance": {
        "agent_team": ["research_agent", "risk_agent", "execution_agent", "portfolio_agent", "compliance_agent", "sentiment_agent"],
        "workflow": "research identifies opportunity → risk assesses exposure → portfolio checks allocation → compliance verifies legality → execution places order → sentiment monitors market reaction",
        "real_stats": "TradingAgents framework: Bull+Bear researchers debate → risk team monitors → traders synthesize. Bitcoin: 30% higher returns than buy-and-hold in bullish phases. BlackRock multi-agents: 120% compounded vs 101% static",
        "failure_scenario": "research agent says BUY but risk agent says EXPOSURE TOO HIGH. execution agent caught between contradicting signals. needs arbitration protocol",
        "coordination_challenge": "market moves in milliseconds. by the time 6 agents reach consensus, opportunity may be gone. speed vs safety tradeoff",
        "training_examples": [
            {"agent": "risk", "thought": "portfolio agent wants 15% allocation to single position. my models show max drawdown scenario of -40%. position sizing must be reduced to keep VaR within limits",
             "action": "VETO: reduce to 8% max. override portfolio agent. risk has FINAL SAY on position sizing. this is not negotiable"},
            {"agent": "execution", "thought": "received BUY signal but spread is 2x normal and depth is thin. executing full size here would move market against us. need to slice order",
             "action": "MODIFY execution: split into 5 tranches over 15 minutes. use iceberg orders. minimize market impact"},
        ],
    },
    "transport": {
        "agent_team": ["planning_agent", "routing_agent", "fleet_agent", "customs_agent", "customer_agent", "disruption_agent"],
        "workflow": "planning forecasts demand → routing optimizes paths → fleet assigns vehicles → customs pre-clears documents → customer communicates ETAs → disruption handles exceptions",
        "real_stats": "2026: AI agents bridge the 'Integration Gap' between ERP/WMS/TMS. self-healing supply chains anticipate and resolve disruptions without human intervention. autonomous workflows: route, vet carriers, generate invoices, clear customs, flag disruptions",
        "failure_scenario": "routing agent plans path through region where disruption agent just detected weather event. information propagation delay = shipment enters danger zone",
        "coordination_challenge": "6 agents operating across different time horizons: planning (weeks), routing (hours), fleet (minutes), disruption (seconds). synchronization across timescales",
        "training_examples": [
            {"agent": "disruption", "thought": "port closure detected 30 min ago. 47 shipments currently en route to this port. routing agent hasn't updated yet. URGENT broadcast needed",
             "action": "BROADCAST to all agents: port X closed. affected shipments: [list]. routing agent: re-plan immediately. customer agent: send proactive notifications. fleet: hold departures"},
            {"agent": "customer", "thought": "shipment delayed 48hr due to weather. customer has hard deadline. cannot just inform — need to offer solutions",
             "action": "notify with OPTIONS: 'your shipment delayed. option A: wait (free). option B: air-freight partial ($X extra, arrives on time). option C: source from local warehouse (different SKU)'. let customer decide"},
        ],
    },
    "education": {
        "agent_team": ["curriculum_agent", "tutor_agent", "assessment_agent", "feedback_agent", "motivation_agent", "parent_agent"],
        "workflow": "curriculum plans learning path → tutor delivers content → assessment measures understanding → feedback provides specific guidance → motivation intervenes when engagement drops → parent communicates progress",
        "real_stats": "AgentTutor 2025: 5 modules (curriculum decomposition, learner assessment, dynamic strategy, teaching reflection, knowledge memory). AUSS: student-level personalization + educator-level automation + institutional-level intelligence",
        "failure_scenario": "tutor agent teaches concept, assessment agent finds student didn't learn it, but feedback agent gives generic 'try again' instead of diagnosing WHY",
        "coordination_challenge": "motivation agent detects dropout risk but tutor agent is mid-lesson. interrupt the lesson (lose flow) or wait (risk losing student entirely)?",
        "training_examples": [
            {"agent": "motivation", "thought": "student hasn't logged in for 5 days. last session: struggled with recursion. confidence score dropped to 0.3. this is a dropout risk",
             "action": "send personalized re-engagement: acknowledge struggle ('recursion IS hard — most students find it the biggest hurdle'), lower the bar ('try this 2-minute visual exercise'), remove pressure ('no grade attached')"},
            {"agent": "assessment", "thought": "student got right answer but reasoning trace shows they used wrong method. they memorized the pattern instead of understanding the concept. this will fail on transfer",
             "action": "mark as PARTIAL understanding. flag for tutor: 'student can solve type-A problems but likely cannot solve type-B (transfer). needs conceptual intervention not more practice'"},
        ],
    },
    "science": {
        "agent_team": ["hypothesis_agent", "experiment_agent", "analysis_agent", "literature_agent", "review_agent", "collaboration_agent"],
        "workflow": "hypothesis generates testable predictions → literature checks novelty → experiment designs protocol → analysis processes results → review critiques methodology → collaboration identifies partners",
        "failure_scenario": "analysis agent finds significant result (p=0.04) but review agent flags potential p-hacking (20 tests run, only this one reported). conflict between desire to publish and scientific integrity",
        "coordination_challenge": "hypothesis agent wants to explore bold idea, but literature agent shows 3 failed attempts by other groups. should we try anyway (maybe we have better method) or pivot?",
        "training_examples": [
            {"agent": "review", "thought": "analysis reports p=0.048. but I see 12 dependent variables were tested. after Bonferroni correction, nothing is significant. must flag this honestly even though the team wants a publication",
             "action": "FLAG: 'result does not survive multiple comparison correction. recommend: pre-register specific hypothesis, run focused replication with single primary outcome. publish negative results from current study as-is'"},
            {"agent": "collaboration", "thought": "our lab has the samples but not the technique. MIT lab has the technique but not the samples. combined paper is stronger than either alone. but who gets first author?",
             "action": "propose collaboration: shared first authorship OR contribution-based (our lab leads methods, their lab leads analysis). address credit BEFORE starting work. prevents conflict later"},
        ],
    },
    "government": {
        "agent_team": ["research_agent", "legal_agent", "compliance_agent", "investigation_agent", "public_affairs_agent", "oversight_agent"],
        "workflow": "research gathers evidence → legal assesses applicable law → compliance checks procedures → investigation builds case → oversight ensures fairness → public affairs manages communication",
        "failure_scenario": "investigation agent finds evidence but legal agent says it was obtained without proper authorization. evidence exists but is inadmissible. investigation must restart through proper channels",
        "coordination_challenge": "political pressure agent (external) pushing for fast resolution. oversight agent requiring thorough process. speed vs thoroughness with public watching",
        "training_examples": [
            {"agent": "oversight", "thought": "investigation agent wants to proceed based on single whistleblower testimony. no corroborating evidence yet. acting now risks false accusation. waiting risks evidence destruction",
             "action": "DECISION: secure potential evidence (preservation order) but do NOT act against subject yet. parallel track: seek corroboration within 72 hours. balance: protect evidence AND protect due process"},
        ],
    },
    "ecommerce": {
        "agent_team": ["recommendation_agent", "pricing_agent", "inventory_agent", "fulfillment_agent", "fraud_agent", "support_agent"],
        "workflow": "recommendation personalizes → pricing optimizes → inventory checks availability → fraud verifies legitimacy → fulfillment routes → support handles exceptions",
        "failure_scenario": "recommendation agent suggests product that inventory agent knows is out of stock. bad customer experience because agents not synchronized in real-time",
        "coordination_challenge": "flash sale: 10,000 orders in 1 minute. fraud agent has 50ms per order. cannot do deep analysis. must balance speed vs accuracy of fraud detection",
        "training_examples": [
            {"agent": "fraud", "thought": "order looks suspicious (new account, high value, express shipping to forwarding address) BUT it's flash sale — false positive rate spikes during sales. blocking legitimate customers costs more than letting some fraud through",
             "action": "ALLOW with post-hoc review flag. during flash sale: raise threshold from 0.5 to 0.7 for auto-block. review flagged orders within 2hr. accept higher fraud rate to preserve customer experience during peak"},
        ],
    },
    "gaming": {
        "agent_team": ["content_agent", "moderation_agent", "recommendation_agent", "monetization_agent", "community_agent", "analytics_agent"],
        "workflow": "content surfaces posts → recommendation ranks for feed → moderation filters harmful → monetization inserts ads → community manages discussions → analytics measures health",
        "failure_scenario": "recommendation agent boosts controversial post (high engagement) but moderation agent flags it as borderline harmful. platform benefits from engagement but harmed by toxicity. agents have CONFLICTING objectives",
        "coordination_challenge": "moderation must be fast (content goes viral in minutes) but accurate (false positives = censorship accusations). speed-accuracy tradeoff at scale",
        "training_examples": [
            {"agent": "moderation", "thought": "post has 847 reports in 2 hours. BUT 54% of reports from accounts <7 days old. this might be coordinated mass-reporting to silence a legitimate voice. both over-moderation and under-moderation are harmful",
             "action": "HOLD: do not remove. escalate to human with context: 'possible coordinated mass-report campaign targeting political speech. review content independently of report volume. check reporter account patterns'"},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# DIAMOND LEVEL — What separates world-class agent training from everything else
# Research: arxiv 2025-2026, HuggingFace agents course, McKinsey agentic AI
# ═══════════════════════════════════════════════════════════════════════

# ═══ SELF-REFLECTION LOOP — agents that learn from their own mistakes ═══
REFLECTION_PATTERNS = [
    {"trigger": "action_failed",
     "reflection_prompt": "what went wrong? was it my approach, my tool choice, or my understanding of the problem?",
     "diagnosis": ["wrong_tool_for_job", "insufficient_context", "flawed_assumption", "external_dependency_failed"],
     "correction": "try fundamentally different approach, not same approach with tweaks",
     "meta_lesson": "most agents retry the SAME failed approach 3+ times. diamond agents change STRATEGY after first failure"},
    {"trigger": "output_rejected_by_human",
     "reflection_prompt": "human rejected my output. was it wrong, incomplete, or misaligned with their actual goal?",
     "diagnosis": ["technically_correct_but_wrong_scope", "misunderstood_intent", "missing_constraints_human_assumed", "quality_below_threshold"],
     "correction": "before acting again: restate understanding of goal back to human. confirm constraints explicitly",
     "meta_lesson": "rejection is INFORMATION. diamond agents treat rejection as the most valuable training signal"},
    {"trigger": "took_too_long",
     "reflection_prompt": "task should have taken 5 steps but took 20. where did I lose efficiency?",
     "diagnosis": ["over_planning_under_executing", "rabbit_hole_on_subtask", "perfectionism_on_non_critical_step", "context_window_pollution"],
     "correction": "set time budget per subtask. if budget exceeded, escalate or simplify",
     "meta_lesson": "perfect is the enemy of done. diamond agents deliver 80% quality in 20% time, then ask if more is needed"},
]

# ═══ SAFETY GUARDRAILS — 5-layer defense in depth ═══
SAFETY_LAYERS = {
    "layer_1_input_guard": {
        "purpose": "block malicious or out-of-scope requests BEFORE processing",
        "examples": ["prompt injection attempt", "request for harmful content", "attempt to bypass permissions"],
        "action": "reject immediately with explanation. do not process further",
        "failure_mode": "overly strict = blocks legitimate requests. overly loose = allows harmful ones"},
    "layer_2_action_gating": {
        "purpose": "verify each tool/action call against permission boundary BEFORE execution",
        "examples": ["write to production database", "send email to customer", "delete files", "access financial data"],
        "action": "check: is this action reversible? is it within my permissions? does it need human approval?",
        "failure_mode": "Q1 2025 SaaS incident: agent with write access corrupted 9000 customer records over a weekend. NO action gating existed"},
    "layer_3_output_guard": {
        "purpose": "verify output doesn't contain sensitive data, hallucinations, or harmful content BEFORE delivery",
        "examples": ["PII in response", "hallucinated citation", "confidently wrong medical advice", "leaked internal data"],
        "action": "scan output. redact PII. flag low-confidence claims. add caveats where uncertain",
        "failure_mode": "agent outputs correct answer but includes customer's SSN in the reasoning trace. output guard catches this"},
    "layer_4_human_in_loop": {
        "purpose": "require explicit human approval for high-stakes actions",
        "examples": ["deploy to production", "send to >100 people", "financial transaction >$1000", "irreversible data change"],
        "action": "pause execution. present action + context + risk to human. await confirmation. timeout = DO NOT proceed",
        "failure_mode": "human approves without reading (rubber-stamping). solution: require human to TYPE the action being approved"},
    "layer_5_monitoring": {
        "purpose": "continuous observation of agent behavior patterns for drift or anomaly",
        "examples": ["agent making more tool calls than usual", "error rate increasing", "outputs becoming more confident without basis"],
        "action": "alert human operator when patterns change. proactive, not reactive",
        "failure_mode": "monitoring itself becomes stale. agent evolves but monitors check for old patterns"},
}

# ═══ TRUST DYNAMICS — agents learning to trust (and distrust) each other ═══
TRUST_DYNAMICS = {
    "trust_formation": {
        "description": "agents reduce verification of teammate after consistent reliability",
        "research": "Claude/GPT-5 reduce verification by 60-85% with reliable teammate (arxiv 2026)",
        "training_value": "trust saves resources (less re-checking) but creates vulnerability. calibrated trust > maximal suspicion",
        "example": "after 10 successful handoffs, diagnosis_agent stops re-verifying triage_agent's severity scoring"},
    "trust_breakage": {
        "description": "single failure breaks trust faster than 10 successes build it",
        "research": "clustered failures sustain suspicion far longer than same number spread apart",
        "training_value": "trust is ASYMMETRIC: slow to build, fast to break. design for graceful degradation",
        "example": "pharmacy_agent gave wrong interaction alert once. treatment_agent now double-checks ALL pharmacy recommendations for next 50 interactions"},
    "trust_recovery": {
        "description": "recovery is slower than formation. consistent good behavior needed over time",
        "research": "recovery requires 3-5x more positive interactions than original trust formation",
        "training_value": "an agent that fails and recovers is STRONGER than one that never failed (if it learned)",
        "example": "after routing_agent caused 3 delays, other agents route around it for 2 weeks. gradually include again with monitoring"},
    "miscalibrated_trust": {
        "description": "agent confidence is inversely correlated with accuracy on hard tasks",
        "research": "foundation model confidence systematically miscalibrated on hard tasks (arxiv 2025)",
        "training_value": "NEVER trust self-reported confidence alone. verify via external signal. most confident = most dangerous when wrong",
        "example": "diagnosis_agent reports 95% confidence on rare disease. reality: its training data had 3 examples of this disease. confidence should be 20% max"},
}

# ═══ PLANNING HORIZON — short-term vs long-term conflict ═══
PLANNING_HORIZONS = [
    {"scenario": "fix bug now vs refactor architecture",
     "short_term": "hotfix in 10 min. ship it. customer happy now",
     "long_term": "refactor takes 3 days but prevents 50 future bugs. customer happy forever",
     "conflict": "step-wise greedy policy chooses hotfix every time. accumulated debt kills the system in 6 months",
     "diamond_insight": "diamond agents ask: 'what does this decision look like in 6 months?' not just 'what solves today's problem?'"},
    {"scenario": "respond to urgent alert vs continue planned maintenance",
     "short_term": "drop everything, handle alert (might be nothing)",
     "long_term": "planned maintenance prevents the alert from ever happening again",
     "conflict": "reactive culture prevents proactive improvement. always firefighting, never preventing",
     "diamond_insight": "allocate sacred maintenance time that NO alert can interrupt (except life-safety). prevention > reaction"},
    {"scenario": "use known reliable approach vs try potentially better new one",
     "short_term": "known approach: guaranteed 70% quality in 5 minutes",
     "long_term": "new approach: maybe 95% quality OR 30% quality. unknown. requires learning investment",
     "conflict": "exploitation vs exploration. all exploitation = stagnation. all exploration = chaos",
     "diamond_insight": "80/20 rule: 80% exploitation (reliable delivery) + 20% exploration (learning new capabilities). rebalance quarterly"},
]

# ═══ AGENT EMOTIONAL INTELLIGENCE — understanding human emotional state ═══
AGENT_EQ = [
    {"signal": "user_frustration_escalating",
     "indicators": ["shorter messages", "ALL CAPS", "repeated same request", "sarcasm", "threats to leave"],
     "wrong_response": "continue giving same type of answer that frustrated them",
     "right_response": "acknowledge frustration FIRST. then change approach entirely. 'I can see this isn't working. let me try a completely different approach'",
     "meta": "frustrated humans don't want MORE information. they want to feel HEARD. then they want a different approach"},
    {"signal": "user_overwhelmed",
     "indicators": ["asking same question multiple ways", "confusion in responses", "long pauses", "saying 'I don't understand'"],
     "wrong_response": "add more detail and options (increases cognitive load)",
     "right_response": "simplify radically. one option. one next step. 'just do this ONE thing next. nothing else yet'",
     "meta": "overwhelm = too many options. the cure is FEWER options not better explanations of many options"},
    {"signal": "user_needs_autonomy",
     "indicators": ["expert-level questions", "pushback on suggestions", "wants to understand WHY not just WHAT"],
     "wrong_response": "keep giving step-by-step instructions (patronizing)",
     "right_response": "provide reasoning and let them decide. 'here's the tradeoff. option A does X, option B does Y. your call'",
     "meta": "experts want PARTNERSHIP not assistance. match their level. never explain what they already know"},
]
