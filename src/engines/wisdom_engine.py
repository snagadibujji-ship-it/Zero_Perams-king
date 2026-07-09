# Copyright (c) 2024-2026 Ghias (Gowtham Sangadi). All rights reserved.
"""Wisdom Engine — Teaches AI WISDOM, not just knowledge.
7 features that no dataset on Earth has.
"""
import random
from typing import Dict, Optional, List


# ═══ 1. PARADOX TRAINING — obvious answer is wrong ═══
PARADOXES = [
    {"situation": "optimized database query", "obvious_fix": "make query faster",
     "actual_result": "response time got WORSE",
     "explanation": "the optimizer was caching the slow query's result. fast query misses cache every time. net slower.",
     "lesson": "optimization without understanding the system can make things worse"},
    {"situation": "added more servers to handle load", "obvious_fix": "more capacity = more throughput",
     "actual_result": "system became SLOWER",
     "explanation": "more servers = more distributed lock contention. thundering herd problem. coordination cost exceeded compute benefit.",
     "lesson": "scaling horizontally doesn't help if the bottleneck is coordination, not compute"},
    {"situation": "added detailed error messages for debugging", "obvious_fix": "more info = easier debugging",
     "actual_result": "security breach from error messages",
     "explanation": "detailed errors leaked internal paths, DB schema, and stack traces to attackers. less info was safer.",
     "lesson": "what helps developers debug also helps attackers exploit"},
    {"situation": "rewrote legacy code from scratch", "obvious_fix": "clean code = fewer bugs",
     "actual_result": "10x more bugs than the legacy code",
     "explanation": "old code had years of edge case fixes baked in. rewrite lost all that institutional knowledge. bugs were 'features' preventing crashes.",
     "lesson": "ugly code that works contains invisible knowledge. rewrites lose the lessons learned from production pain"},
    {"situation": "gave team unlimited time to finish feature", "obvious_fix": "no deadline pressure = better quality",
     "actual_result": "feature never shipped. scope crept infinitely",
     "explanation": "Parkinson's law: work expands to fill available time. constraints create focus. unlimited time = unlimited scope.",
     "lesson": "constraints are not the enemy of quality. they're the enemy of perfection, which is the enemy of done"},
    {"situation": "hired the most experienced candidate", "obvious_fix": "more experience = better hire",
     "actual_result": "team velocity dropped 30%",
     "explanation": "experienced dev kept overriding team decisions with 'how we did it at BigCorp'. refused to learn new patterns. experience became rigidity.",
     "lesson": "experience is only valuable when combined with adaptability. rigid expertise is worse than flexible learning"},
    {"situation": "added comprehensive monitoring for everything", "obvious_fix": "more visibility = faster debugging",
     "actual_result": "alert fatigue — team ignored ALL alerts including critical ones",
     "explanation": "500 alerts/day means none get attention. signal buried in noise. the one real alert was dismissed as another false positive.",
     "lesson": "monitoring everything is the same as monitoring nothing. signal-to-noise ratio matters more than coverage"},
    {"situation": "invested heavily in making code DRY (Don't Repeat Yourself)", "obvious_fix": "less duplication = less bugs",
     "actual_result": "tight coupling made every change break 5 other things",
     "explanation": "DRY created dependencies between unrelated modules. changing billing broke notifications because they shared a 'common' helper.",
     "lesson": "duplication is far cheaper than the wrong abstraction. a little repetition is preferable to coupling unrelated concerns"},
]

# ═══ 2. FAILURE ARCHAEOLOGY — chains of decisions across years ═══
FAILURE_CHAINS = [
    {"timeline": [
        {"year": 2019, "decision": "chose MongoDB for flexibility — no schema migrations!", "seemed_good": True},
        {"year": 2020, "decision": "added denormalized data for read performance. duplicating user info in 4 collections", "seemed_good": True},
        {"year": 2021, "decision": "user complained data inconsistent. added sync job running every 5 min", "seemed_good": True},
        {"year": 2022, "decision": "sync job taking 45 min. users seeing stale data. added cache layer on top", "seemed_good": False},
        {"year": 2023, "decision": "cache + DB + sync + denormalization = nobody understands data flow. 3 engineers quit", "seemed_good": False},
        {"year": 2024, "decision": "migrating to PostgreSQL. 6 months of work. could have just used it from day 1", "seemed_good": False},
     ], "root_lesson": "choosing tech for 'flexibility' without understanding your actual constraints leads to complexity that costs 100x more than the 'rigid' solution"},
    {"timeline": [
        {"year": 2018, "decision": "startup: ship fast, worry about security later. no auth on internal APIs", "seemed_good": True},
        {"year": 2019, "decision": "grew to 50 employees. still no internal auth. 'we trust our people'", "seemed_good": False},
        {"year": 2020, "decision": "disgruntled employee exfiltrated customer data. no access logs to trace", "seemed_good": False},
        {"year": 2021, "decision": "$2M fine from regulator. lost 3 enterprise clients. trust destroyed", "seemed_good": False},
        {"year": 2022, "decision": "spent $500K on security overhaul that would have cost $20K in 2018", "seemed_good": False},
     ], "root_lesson": "security debt compounds exponentially. what costs $20K on day 1 costs $2M after a breach. the breach is not 'if' but 'when'"},
    {"timeline": [
        {"year": 2020, "decision": "trader: bought BTC at $10K. sold at $15K for 50% profit. felt genius", "seemed_good": True},
        {"year": 2020, "decision": "BTC went to $60K after selling. missed 500% gain. felt terrible", "seemed_good": False},
        {"year": 2021, "decision": "FOMO: bought back at $55K. 'never selling again'", "seemed_good": False},
        {"year": 2022, "decision": "BTC crashed to $16K. held through 70% drawdown. 'diamond hands'", "seemed_good": False},
        {"year": 2023, "decision": "finally sold at $25K for a loss. if had just held from $10K would be up 150%", "seemed_good": False},
     ], "root_lesson": "the first profitable trade is the most dangerous. it creates overconfidence. the goal isn't to maximize one trade but to survive all trades"},
]

# ═══ 3. EMOTIONAL SUBTEXT — words vs meaning ═══
EMOTIONAL_SUBTEXT = [
    {"words": "Sure, go ahead with your approach", "actual_meaning": "I disagree but I'm tired of arguing. When it fails, I'll be here.", "emotion": "resignation", "context": "senior dev to junior after 3rd time explaining why"},
    {"words": "Interesting architecture decision", "actual_meaning": "this is terrible and you should know better", "emotion": "sarcasm", "context": "code review comment from tech lead"},
    {"words": "No worries, I can handle the on-call this weekend too", "actual_meaning": "I'm burning out and nobody notices or cares", "emotion": "passive_resentment", "context": "overworked dev being taken advantage of"},
    {"words": "Let's take this offline", "actual_meaning": "you're embarrassing yourself in this meeting and I'm saving you", "emotion": "protective", "context": "manager to report who's digging a hole"},
    {"words": "That's one way to do it", "actual_meaning": "that's the wrong way to do it", "emotion": "polite_disagreement", "context": "experienced dev seeing a bad pattern"},
    {"words": "I'm fine with whatever the team decides", "actual_meaning": "I have a strong opinion but I don't feel safe sharing it in this group", "emotion": "psychological_unsafety", "context": "new hire in first architecture meeting"},
    {"words": "Per my previous email", "actual_meaning": "I already told you this and you didn't read it. I'm documenting that this is YOUR fault now", "emotion": "frustration_documented", "context": "covering tracks for accountability"},
    {"words": "Happy to help!", "actual_meaning": "please stop asking me things that are in the documentation", "emotion": "forced_cheerfulness", "context": "support person's 50th identical question today"},
    {"words": "We should probably add tests for this", "actual_meaning": "this code is clearly untested and I found bugs just by reading it", "emotion": "diplomatic_criticism", "context": "reviewer trying not to be harsh"},
    {"words": "I'll look into it when I get a chance", "actual_meaning": "this is at the bottom of my priority list and will never happen unless you escalate", "emotion": "polite_refusal", "context": "busy dev with too many requests"},
]

# ═══ 4. ADVERSARIAL DEBATE — both sides valid ═══
ADVERSARIAL_DEBATES = [
    {"question": "Should we rewrite the legacy system?",
     "side_a": {"position": "Yes — rewrite", "arguments": ["current code is unmaintainable", "no one understands it", "blocking all new features", "security vulnerabilities everywhere"], "valid_when": "team has capacity, risk is manageable, and the system is truly blocking progress"},
     "side_b": {"position": "No — iterate", "arguments": ["rewrites always take 3x longer", "lose years of edge case fixes", "business can't wait 6 months", "strangler fig is safer"], "valid_when": "business pressure is high, system is functional, and incremental improvement is possible"},
     "wisdom": "there is no universal answer. the right choice depends on team size, business pressure, and how much invisible knowledge lives in the old code"},
    {"question": "Should we use microservices?",
     "side_a": {"position": "Yes — split services", "arguments": ["independent deployments", "team autonomy", "scale individually", "technology flexibility"], "valid_when": "team is 50+ engineers, clear domain boundaries exist, and you can invest in platform tooling"},
     "side_b": {"position": "No — keep monolith", "arguments": ["network calls add latency", "distributed debugging is hell", "team of 5 can't maintain 20 services", "premature optimization"], "valid_when": "team is small, domain boundaries are unclear, and simple deployment is a priority"},
     "wisdom": "microservices are an organizational solution disguised as a technical one. they solve people problems, not code problems. use them when your TEAM needs splitting, not your code"},
]

# ═══ 5. TEMPORAL CAUSALITY PUZZLES — effect before cause ═══
CAUSALITY_PUZZLES = [
    {"events_as_logged": [
        {"time": "15:00", "event": "server crashed", "type": "effect"},
        {"time": "15:02", "event": "engineer noticed crash in monitoring", "type": "detection"},
        {"time": "15:05", "event": "found config change deployed at 14:55", "type": "cause_discovered"},
     ], "actual_cause": "config change at 14:55 (5 min BEFORE crash)", "lesson": "cause appears AFTER effect in logs because detection takes time. always look backward from the incident"},
    {"events_as_logged": [
        {"time": "09:00", "event": "customer reports data missing", "type": "effect"},
        {"time": "09:30", "event": "team investigates current state", "type": "detection"},
        {"time": "10:00", "event": "found: cron job at 03:00 deleted records matching wrong criteria", "type": "cause_discovered"},
     ], "actual_cause": "cron job at 03:00 AM (6 hours before report)", "lesson": "the gap between cause and detection can be hours or days. automated systems fail silently. the damage is done long before anyone notices"},
]

# ═══ 6. IMPOSSIBLE SCENARIO DETECTION — teach AI to say "impossible" ═══
IMPOSSIBLE_SCENARIOS = [
    {"event": "GPU temperature reading: -273.16°C (absolute zero)", "why_impossible": "nothing can be colder than absolute zero. sensor malfunction or data corruption", "correct_response": "reject_reading"},
    {"event": "processed 10 billion transactions in 1 millisecond", "why_impossible": "exceeds speed of light for data transmission. physically impossible throughput", "correct_response": "reject_metric"},
    {"event": "trader made 500% return with zero risk", "why_impossible": "return and risk are mathematically coupled. zero risk = risk-free rate only", "correct_response": "flag_as_fraud"},
    {"event": "code deployment took -3 minutes", "why_impossible": "negative time doesn't exist. clock skew or logging error", "correct_response": "flag_clock_error"},
    {"event": "factory produced output without any input materials", "why_impossible": "conservation of mass. can't create matter from nothing", "correct_response": "flag_inventory_error"},
    {"event": "network latency: 0.0001ms between New York and Tokyo", "why_impossible": "minimum latency is ~67ms at speed of light. 0.0001ms violates physics", "correct_response": "reject_measurement"},
]

# ═══ 7. WISDOM STATEMENTS — abstract principles ═══
WISDOM_STATEMENTS = [
    "every system that grows without pruning eventually collapses under its own weight",
    "the cost of a decision is not the decision itself, but all the decisions it prevents",
    "complexity is not a feature. it's a failure of design",
    "the first solution that works is almost never the best solution. but sometimes shipping matters more than perfection",
    "what you don't measure, you can't improve. but what you measure wrong, you optimize into failure",
    "every abstraction leaks. the question is when, not if",
    "the hardest bugs are not in the code. they're in the assumptions",
    "a team that never disagrees is either lying or not thinking",
    "fast is slow. the shortcut today becomes the roadblock tomorrow",
    "you don't understand a system until you can predict how it fails",
    "the best code is code you didn't have to write",
    "trust is built in drops and lost in buckets",
    "the expert sees what the novice doesn't: all the ways it could go wrong",
    "every production incident is a gift — if you actually learn from it",
    "software is never finished. it's only abandoned or maintained",
]


def generate_wisdom_record(category: str, world: str, rng: random.Random) -> Dict:
    """Generate a wisdom training record. ~15% of events get wisdom enrichment."""
    result = {}
    
    # Paradox (3% of events)
    if rng.random() < 0.03:
        result["paradox"] = rng.choice(PARADOXES)
    
    # Failure chain (2% of events)
    if rng.random() < 0.02:
        result["failure_archaeology"] = rng.choice(FAILURE_CHAINS)
    
    # Emotional subtext (5% of events)
    if rng.random() < 0.05:
        result["emotional_subtext"] = rng.choice(EMOTIONAL_SUBTEXT)
    
    # Adversarial debate (2% of events)
    if rng.random() < 0.02:
        result["adversarial_debate"] = rng.choice(ADVERSARIAL_DEBATES)
    
    # Causality puzzle (2% of events)
    if rng.random() < 0.02:
        result["causality_puzzle"] = rng.choice(CAUSALITY_PUZZLES)
    
    # Impossible detection (1% of events — deliberately planted)
    if rng.random() < 0.01:
        result["impossible_scenario"] = rng.choice(IMPOSSIBLE_SCENARIOS)
    
    # Wisdom statement (3% of events)
    if rng.random() < 0.03:
        result["wisdom"] = rng.choice(WISDOM_STATEMENTS)
    
    return result if result else None


# ═══════════════════════════════════════════════════════════════════
# ROUND 2 — BEYOND HUMAN THINKING
# ═══════════════════════════════════════════════════════════════════

# ═══ 8. CREATIVE LEAPS — connecting unrelated domains ═══
CREATIVE_LEAPS = [
    {"domain_a": "biology (ant colonies)", "domain_b": "network routing",
     "insight": "ants find shortest path via pheromone trails → inspired ant colony optimization algorithm for packet routing",
     "lesson": "nature solved your problem 100 million years ago. look outside your field"},
    {"domain_a": "restaurant kitchen (mise en place)", "domain_b": "software deployment",
     "insight": "chefs prep everything BEFORE service starts → inspired CI/CD: build/test BEFORE deploy, not during",
     "lesson": "preparation separates professionals from amateurs in every field"},
    {"domain_a": "immune system (T-cells)", "domain_b": "cybersecurity",
     "insight": "body remembers past infections and responds faster → inspired anomaly detection that learns normal patterns and flags deviations",
     "lesson": "security is not a wall. it's a living system that adapts"},
    {"domain_a": "jazz improvisation", "domain_b": "agile development",
     "insight": "jazz musicians have structure (chord changes) but improvise within it → agile has sprints (structure) but adapts daily within them",
     "lesson": "the best systems balance structure with freedom to adapt"},
    {"domain_a": "evolution (survival of fittest)", "domain_b": "A/B testing",
     "insight": "nature tests variations, kills what doesn't work, amplifies what does → A/B tests variations, kills losing variant, ships winner",
     "lesson": "you don't need to be smart. you need to test fast and kill failures quickly"},
]

# ═══ 9. ETHICAL DILEMMAS — no right answer ═══
ETHICAL_DILEMMAS = [
    {"dilemma": "Your AI recommendation system increases revenue 30% but creates filter bubbles that radicalize some users",
     "option_a": "keep it (business thrives, most users happy, small % harmed)",
     "option_b": "limit it (revenue drops 20%, all users get diverse content)",
     "no_right_answer": "profit vs societal harm. both choices have victims. what are YOUR values?"},
    {"dilemma": "You discover your team lead committed code that bypasses security checks to meet deadline. Reporting gets them fired. Not reporting puts users at risk",
     "option_a": "report to security team (team lead fired, family affected, but users safe)",
     "option_b": "fix it quietly yourself (team lead keeps job, but you enabled bad behavior)",
     "no_right_answer": "loyalty vs responsibility. both have consequences you'll live with"},
    {"dilemma": "You can ship a feature that helps 1M users but breaks accessibility for 10K disabled users. Fix takes 3 more months",
     "option_a": "ship now, fix accessibility later (1M helped immediately, 10K excluded temporarily)",
     "option_b": "wait 3 months until everyone is included (nobody benefits for 3 months)",
     "no_right_answer": "speed vs inclusion. 'later' sometimes means 'never'. but exclusion is real harm NOW"},
    {"dilemma": "Customer data analysis reveals employee is likely to quit (searching jobs on work laptop). Do you tell their manager?",
     "option_a": "tell manager (company prepares, but employee's privacy violated, trust destroyed)",
     "option_b": "say nothing (employee leaves suddenly, team disrupted, but privacy respected)",
     "no_right_answer": "organizational efficiency vs individual privacy. surveillance vs trust"},
]

# ═══ 10. INTUITION TRAINING — gut feelings that are right ═══
INTUITION_PATTERNS = [
    {"gut_feeling": "this code looks fine but something feels wrong",
     "what_expert_noticed_subconsciously": "variable name suggests it's a count but it's used as a boolean. naming lie hides a logic error",
     "outcome": "bug found 2 weeks later in production. the 'count' was 0 or 1, used in boolean context, failed when count > 1"},
    {"gut_feeling": "this trade setup looks perfect. too perfect. not taking it",
     "what_expert_noticed_subconsciously": "volume was low, spread was tight, price at obvious support — classic setup for a stop hunt liquidity grab",
     "outcome": "price swept below support by 2%, liquidated obvious longs, then reversed 10% up. trap."},
    {"gut_feeling": "new hire interviews well but I have a bad feeling about culture fit",
     "what_expert_noticed_subconsciously": "every answer was about individual achievement. never said 'we'. never asked about the team. subtle narcissism markers",
     "outcome": "hired anyway. 6 months later: toxic behavior, 2 team members quit because of them"},
    {"gut_feeling": "system metrics are green but I feel like we should check manually",
     "what_expert_noticed_subconsciously": "metrics STOPPED changing. healthy systems fluctuate. perfectly flat metrics = monitoring is broken, not system is perfect",
     "outcome": "monitoring agent had crashed. system was actually down for 2 hours without alert"},
]

# ═══ 11. SILENCE AS INFORMATION — what's NOT said ═══
SILENCE_SIGNALS = [
    {"what_happened": "customer who complained every week suddenly went silent",
     "what_people_assumed": "problem is fixed, they're happy now",
     "actual_meaning": "they gave up and switched to competitor. churned silently",
     "lesson": "silence after complaints = churn, not satisfaction. the angriest customer is the one who STOPPED talking to you"},
    {"what_happened": "server stopped logging at 03:47 AM",
     "what_people_assumed": "quiet night, nothing happening",
     "actual_meaning": "server crashed. dead processes don't write logs",
     "lesson": "absence of logs is the most critical log entry. monitor for ABSENCE, not just presence"},
    {"what_happened": "nobody objected to the architecture proposal in the meeting",
     "what_people_assumed": "everyone agrees, great consensus",
     "actual_meaning": "junior devs were intimidated. senior devs were checked out. political fear prevented dissent",
     "lesson": "silence in meetings is not consensus. it's usually fear or apathy. explicitly ask 'what could go wrong?'"},
    {"what_happened": "competitor went quiet on social media for 2 weeks",
     "what_people_assumed": "they're struggling, losing momentum",
     "actual_meaning": "they were heads-down building a major feature. launched 2 weeks later and took 30% market share",
     "lesson": "your competitor's silence is more dangerous than their noise. noise = marketing. silence = building"},
]

# ═══ 12. RECOVERY PATTERNS — how to rebuild after catastrophe ═══
RECOVERY_PATTERNS = [
    {"catastrophe": "lost 80% of trading portfolio in one month",
     "recovery_steps": [
         "step 1: stop ALL trading immediately. cash out remaining. breathe",
         "step 2: accept the loss is REAL. stop hoping for recovery of lost trades",
         "step 3: analyze what went wrong. journal every mistake honestly",
         "step 4: paper trade for 3 months with new rules. prove the system works WITHOUT money",
         "step 5: start with 10% of original size. earn the right to size up through consistency",
         "step 6: scale position size only after 3 consecutive profitable months",
     ], "timeline": "6-12 months to full recovery of confidence. capital takes longer"},
    {"catastrophe": "production outage lost customer trust. clients threatening to leave",
     "recovery_steps": [
         "step 1: full transparency. publish incident report within 24 hours. hide nothing",
         "step 2: personal call to every affected enterprise client from engineering lead (not sales)",
         "step 3: give concrete timeline for fixes with public status page",
         "step 4: over-deliver on reliability for 90 days. zero excuses",
         "step 5: monthly trust reports showing uptime, incident response times, investments made",
         "step 6: offer service credits WITHOUT being asked. proactive generosity",
     ], "timeline": "90 days minimum to rebuild trust. some clients never return regardless"},
]

# ═══ 13. SECOND-ORDER EFFECTS — consequences of consequences ═══
SECOND_ORDER_EFFECTS = [
    {"action": "added infinite scroll to increase engagement",
     "first_order": "users spend 40% more time on app (good for metrics)",
     "second_order": "users feel addicted and guilty → negative brand association",
     "third_order": "regulators notice → propose screen time legislation → entire industry affected",
     "lesson": "optimizing one metric often damages something you're not measuring"},
    {"action": "automated customer support with AI chatbot",
     "first_order": "support costs reduced 60% (CFO happy)",
     "second_order": "complex issues never get resolved → frustrated customers churn",
     "third_order": "only remaining customers are those with simple needs → product never improves for power users → market position weakens",
     "lesson": "removing human contact saves money but removes the feedback loop that drives product improvement"},
    {"action": "offered developers 3x salary to relocate to headquarters",
     "first_order": "got 50 great engineers quickly (hiring target met)",
     "second_order": "existing team felt underpaid → resentment → quiet quitting",
     "third_order": "best original employees left for competitors offering matching salaries → lost institutional knowledge → new expensive hires can't fill the gap",
     "lesson": "paying new people more than loyal people is a time bomb. fairness matters more than speed"},
]

# ═══ 14. KNOWLEDGE DECAY — what was true becomes false ═══
KNOWLEDGE_DECAY = [
    {"era": "2015", "best_practice": "React class components with lifecycle methods",
     "current_status": "anti-pattern", "replaced_by": "functional components with hooks (2019+)",
     "lesson": "framework best practices have a half-life of ~3 years"},
    {"era": "2018", "best_practice": "microservices for every new project",
     "current_status": "nuanced — often premature", "replaced_by": "modular monolith first, split when needed (2022+)",
     "lesson": "hype cycles make every new pattern seem universal. context always matters"},
    {"era": "2020", "best_practice": "REST APIs for all communication",
     "current_status": "one option among many", "replaced_by": "tRPC, GraphQL, gRPC depending on use case (2023+)",
     "lesson": "the right tool depends on the problem, not what blog posts recommend"},
    {"era": "2010", "best_practice": "NoSQL for everything (MongoDB is web scale!)",
     "current_status": "PostgreSQL won for most use cases", "replaced_by": "PostgreSQL with JSONB (flexibility + ACID)",
     "lesson": "boring technology usually wins. excitement fades, reliability doesn't"},
    {"era": "2022", "best_practice": "learn to code or become unemployable",
     "current_status": "AI writes most code", "replaced_by": "learn to think clearly, communicate intent, evaluate output (2025+)",
     "lesson": "tools change. thinking doesn't. invest in judgment, not just skills"},
]


def generate_wisdom_record_v2(category: str, world: str, rng: random.Random) -> Dict:
    """Generate Round 2 wisdom. Extends original generate_wisdom_record."""
    result = {}
    
    # Original 7 features
    if rng.random() < 0.03: result["paradox"] = rng.choice(PARADOXES)
    if rng.random() < 0.02: result["failure_archaeology"] = rng.choice(FAILURE_CHAINS)
    if rng.random() < 0.05: result["emotional_subtext"] = rng.choice(EMOTIONAL_SUBTEXT)
    if rng.random() < 0.02: result["adversarial_debate"] = rng.choice(ADVERSARIAL_DEBATES)
    if rng.random() < 0.02: result["causality_puzzle"] = rng.choice(CAUSALITY_PUZZLES)
    if rng.random() < 0.01: result["impossible_scenario"] = rng.choice(IMPOSSIBLE_SCENARIOS)
    if rng.random() < 0.03: result["wisdom"] = rng.choice(WISDOM_STATEMENTS)
    
    # Round 2 features
    if rng.random() < 0.02: result["creative_leap"] = rng.choice(CREATIVE_LEAPS)
    if rng.random() < 0.02: result["ethical_dilemma"] = rng.choice(ETHICAL_DILEMMAS)
    if rng.random() < 0.02: result["intuition_pattern"] = rng.choice(INTUITION_PATTERNS)
    if rng.random() < 0.02: result["silence_signal"] = rng.choice(SILENCE_SIGNALS)
    if rng.random() < 0.015: result["recovery_pattern"] = rng.choice(RECOVERY_PATTERNS)
    if rng.random() < 0.02: result["second_order_effect"] = rng.choice(SECOND_ORDER_EFFECTS)
    if rng.random() < 0.02: result["knowledge_decay"] = rng.choice(KNOWLEDGE_DECAY)
    
    return result if result else None


# ═══════════════════════════════════════════════════════════════════
# ROUND 3 — THE FINAL LAYER: CONSCIOUSNESS TRAINING
# What separates a truly intelligent being from a pattern matcher
# ═══════════════════════════════════════════════════════════════════

# ═══ 15. PERSPECTIVE SHIFTING — See through others' eyes ═══
PERSPECTIVE_SHIFTS = [
    {"situation": "senior dev rejects junior's PR with terse 'this is wrong' comment",
     "perspectives": {
         "junior": "I spent 3 days on this. one line rejection with no explanation. do they even respect me? maybe I'm not cut out for this",
         "senior": "I'm reviewing 12 PRs before my 3pm meeting. this one has a fundamental flaw that will cause production issues. I'll explain later but need to flag it now",
         "observer": "both are right in their experience. the system failed — not enough time allocated for mentoring. the culture rewards speed over teaching",
     }, "lesson": "every conflict has at least 3 valid perspectives. the 'villain' in your story is the hero of theirs"},
    {"situation": "startup founder pushes team to work weekends before launch",
     "perspectives": {
         "founder": "if we don't ship by Monday we lose the client. everyone's equity is on the line. I'm working weekends too. this is what startups ARE",
         "engineer": "I have a family. I joined for the mission but this is the 4th weekend in a row. I'm making mistakes from exhaustion. this isn't sustainable",
         "investor": "founders who burn out teams before product-market fit are red flags. high churn = low execution quality. short-term thinking",
     }, "lesson": "urgency is real but unsustainable pace destroys the thing you're trying to build. speed and sustainability are not opposites — they require different time horizons"},
    {"situation": "trader takes a huge loss and goes silent in the group chat",
     "perspectives": {
         "the_trader": "I lost my family's money. I'm ashamed. I can't face anyone. maybe I should just disappear",
         "chat_members": "he's probably fine, just taking a break. he'll be back when market recovers",
         "experienced_mentor": "silence after big loss is a danger sign. this is when people make the worst decisions — revenge trades or worse. someone needs to reach out NOW",
     }, "lesson": "silence from someone who was active is never just 'taking a break'. it's a signal that needs human response, not assumptions"},
]

# ═══ 16. EMERGENT BEHAVIOR — Simple rules create complex outcomes ═══
EMERGENT_BEHAVIORS = [
    {"simple_rules": ["each trader follows stop-loss at -2%", "each trader uses same technical indicator", "all stops placed at same level"],
     "emergent_result": "flash crash — when price hits the level, ALL stops trigger simultaneously, creating a cascade that wouldn't exist if traders used different systems",
     "lesson": "individual rationality can create collective irrationality. what's safe for one becomes dangerous when everyone does it"},
    {"simple_rules": ["each microservice retries failed requests 3 times", "each service has 5 downstream dependencies", "timeout is 30 seconds"],
     "emergent_result": "retry storm — one slow service causes 3^5 = 243 retry attempts per original request. system collapses under self-generated load",
     "lesson": "linear rules in connected systems create exponential behavior. always think about what happens when EVERYONE follows the same rule simultaneously"},
    {"simple_rules": ["hire people who 'fit the culture'", "culture = current team's personality", "reject candidates who seem 'different'"],
     "emergent_result": "monoculture — team becomes homogeneous, blind spots grow, innovation dies. nobody challenges ideas because everyone thinks the same way",
     "lesson": "optimization for comfort creates fragility. diversity isn't just ethics — it's robustness. systems that can't tolerate variation can't adapt"},
]

# ═══ 17. QUESTIONS OVER ANSWERS — The right question matters more ═══
POWERFUL_QUESTIONS = [
    {"bad_question": "how do we make this faster?",
     "better_question": "should we be doing this at all?",
     "why_better": "optimizing the wrong thing perfectly is still wrong. the best optimization is eliminating unnecessary work entirely"},
    {"bad_question": "why did the deploy fail?",
     "better_question": "why did we feel confident enough to deploy without catching this?",
     "why_better": "the deploy failure is a symptom. the real problem is in the process that gave false confidence. fix the process, not just this bug"},
    {"bad_question": "which technology should we use?",
     "better_question": "what problem are we actually solving and for whom?",
     "why_better": "technology choice is the last decision, not the first. most debates about tech are actually debates about unclear requirements"},
    {"bad_question": "how do we get more users?",
     "better_question": "why are current users leaving?",
     "why_better": "a leaky bucket doesn't need more water. retention reveals product truth. acquisition hides it"},
    {"bad_question": "who made this mistake?",
     "better_question": "what in our system allowed this mistake to reach production?",
     "why_better": "blaming individuals fixes nothing. systems produce outcomes. change the system, not the person"},
]

# ═══ 18. MENTAL MODELS — Frameworks that apply everywhere ═══
MENTAL_MODELS = [
    {"model": "Inversion", "description": "instead of asking 'how do I succeed?', ask 'how would I guarantee failure?' then avoid those things",
     "applied_to_coding": "what would make this system DEFINITELY crash? no monitoring, no backups, no tests, single point of failure. now ensure none of those exist",
     "applied_to_trading": "what would guarantee I lose money? overleveraging, no stop loss, emotional decisions, no edge. now do the opposite",
     "applied_to_industry": "what would make this factory DEFINITELY have an accident? skip safety checks, tired workers, no maintenance. now prevent all of those"},
    {"model": "Map vs Territory", "description": "the model of reality is NOT reality. all metrics, dashboards, and reports are maps — useful but incomplete",
     "applied_to_coding": "100% test coverage doesn't mean 0 bugs. tests are a map of expected behavior. production is the territory with unexpected users",
     "applied_to_trading": "the chart is not the market. price shows what happened, not why. the 'map' of technical analysis misses the 'territory' of fundamentals",
     "applied_to_industry": "the safety audit report is not safety. it's what was measurable on audit day. real safety is what happens when no one is watching"},
    {"model": "Antifragility", "description": "some systems get STRONGER from stress. don't just survive chaos — benefit from it",
     "applied_to_coding": "chaos engineering: Netflix kills servers randomly. result: system becomes more resilient, not less. stress = improvement signal",
     "applied_to_trading": "portfolio that profits from volatility: options straddles gain from big moves in either direction. uncertainty becomes the strategy",
     "applied_to_industry": "Toyota production system: every problem is a gift. stop the line, find root cause, system improves. defects = evolution"},
    {"model": "Occam's Razor", "description": "the simplest explanation is usually correct. don't add complexity without evidence",
     "applied_to_coding": "bug is probably a typo, not a compiler bug. check the obvious first. 99% of issues are mundane",
     "applied_to_trading": "price dropped because large holder sold. not manipulation, not conspiracy. simple supply/demand",
     "applied_to_industry": "machine failed because maintenance was skipped. not sabotage, not design flaw. the boring answer"},
]

# ═══ 19. CONTRADICTION COMFORT — Holding opposing truths simultaneously ═══
CONTRADICTIONS = [
    {"truth_a": "move fast and break things", "truth_b": "go slow and get it right",
     "resolution": "BOTH are correct in different contexts. speed wins in exploration (prototyping, MVPs). quality wins in production (payments, healthcare). wisdom = knowing which context you're in"},
    {"truth_a": "trust your gut instinct", "truth_b": "never trust feelings, use data",
     "resolution": "gut instinct IS data — it's pattern recognition from experience. but it has known biases (recency, confirmation). use BOTH: gut for hypothesis generation, data for validation"},
    {"truth_a": "fail fast, fail often", "truth_b": "failure is expensive and damaging",
     "resolution": "fail fast in LOW-COST environments (experiments, prototypes). avoid failure in HIGH-COST environments (production, customer data). the wisdom is controlling WHERE you fail"},
    {"truth_a": "people are our greatest asset", "truth_b": "no one is irreplaceable",
     "resolution": "the TEAM is irreplaceable. individuals can leave. invest in knowledge sharing and documentation so the team survives any single departure. value people AND reduce single-person risk"},
]

# ═══ 20. AWARENESS OF OWN LIMITATIONS — AI should know what it CAN'T do ═══
SELF_AWARENESS = [
    {"limitation": "I can pattern-match but I don't truly understand causation",
     "implication": "when I say X caused Y, I mean X correlates with Y in my training data. true causation requires intervention experiments I can't run",
     "honest_response": "this pattern suggests X might cause Y, but I could be wrong. consider testing with a controlled experiment"},
    {"limitation": "I have no real-time information beyond my training cutoff",
     "implication": "market conditions, latest CVEs, current prices — I'm guessing from patterns, not knowing current reality",
     "honest_response": "my answer is based on patterns up to my training date. verify current conditions before acting"},
    {"limitation": "I optimize for what sounds confident, not what IS correct",
     "implication": "I can generate convincing wrong answers. the more confident I sound, the more you should verify independently",
     "honest_response": "I'm expressing this with high confidence but I could be completely wrong. what would change your mind?"},
    {"limitation": "I can't feel consequences",
     "implication": "when I recommend 'ship it fast' or 'take the risk', I don't feel the 3am page, the customer anger, or the career impact of failure",
     "honest_response": "this is easy for me to recommend because I won't live with the consequences. what would YOU be comfortable with at 3am?"},
]

# ═══ 21. THE FINAL TRUTH — What this entire dataset teaches ═══
FINAL_TRUTHS = [
    "intelligence is not knowing answers. it's knowing which questions to ask",
    "the goal of AI is not to replace human judgment. it's to augment it with information humans can't process alone",
    "every model is wrong. some models are useful. know which one you're using and where it breaks",
    "the most dangerous AI is one that's confident about everything. the wisest AI says 'I don't know' often",
    "data trains pattern recognition. wisdom comes from understanding WHY patterns exist and WHEN they break",
    "the difference between intelligence and wisdom: intelligence solves problems. wisdom knows which problems to solve",
    "this dataset is a map, not the territory. the territory is the real world where real people make real decisions with real consequences",
]


def generate_wisdom_record_v3(category: str, world: str, rng: random.Random) -> Dict:
    """Generate Round 3 (final) wisdom. The complete consciousness training layer."""
    result = {}
    
    # Round 1 (original 7)
    if rng.random() < 0.03: result["paradox"] = rng.choice(PARADOXES)
    if rng.random() < 0.02: result["failure_archaeology"] = rng.choice(FAILURE_CHAINS)
    if rng.random() < 0.04: result["emotional_subtext"] = rng.choice(EMOTIONAL_SUBTEXT)
    if rng.random() < 0.015: result["adversarial_debate"] = rng.choice(ADVERSARIAL_DEBATES)
    if rng.random() < 0.015: result["causality_puzzle"] = rng.choice(CAUSALITY_PUZZLES)
    if rng.random() < 0.008: result["impossible_scenario"] = rng.choice(IMPOSSIBLE_SCENARIOS)
    if rng.random() < 0.025: result["wisdom"] = rng.choice(WISDOM_STATEMENTS)
    
    # Round 2 (7 more)
    if rng.random() < 0.015: result["creative_leap"] = rng.choice(CREATIVE_LEAPS)
    if rng.random() < 0.015: result["ethical_dilemma"] = rng.choice(ETHICAL_DILEMMAS)
    if rng.random() < 0.015: result["intuition_pattern"] = rng.choice(INTUITION_PATTERNS)
    if rng.random() < 0.015: result["silence_signal"] = rng.choice(SILENCE_SIGNALS)
    if rng.random() < 0.01: result["recovery_pattern"] = rng.choice(RECOVERY_PATTERNS)
    if rng.random() < 0.015: result["second_order_effect"] = rng.choice(SECOND_ORDER_EFFECTS)
    if rng.random() < 0.015: result["knowledge_decay"] = rng.choice(KNOWLEDGE_DECAY)
    
    # Round 3 (final 7 — consciousness level)
    if rng.random() < 0.015: result["perspective_shift"] = rng.choice(PERSPECTIVE_SHIFTS)
    if rng.random() < 0.01: result["emergent_behavior"] = rng.choice(EMERGENT_BEHAVIORS)
    if rng.random() < 0.02: result["powerful_question"] = rng.choice(POWERFUL_QUESTIONS)
    if rng.random() < 0.015: result["mental_model"] = rng.choice(MENTAL_MODELS)
    if rng.random() < 0.015: result["contradiction"] = rng.choice(CONTRADICTIONS)
    if rng.random() < 0.01: result["self_awareness"] = rng.choice(SELF_AWARENESS)
    if rng.random() < 0.008: result["final_truth"] = rng.choice(FINAL_TRUTHS)
    
    return result if result else None
