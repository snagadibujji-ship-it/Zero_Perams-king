"""
Worker Personality System — Advanced
=====================================
Real workers aren't stereotypes. This system models:

1. INDEPENDENT TRAITS — 9 dimensions, not determined by experience
2. STATE CHANGES — Personality shifts based on events (accident → careful)
3. HIDDEN BEHAVIORS — Time theft, fake logs, covering for friends
4. RELATIONSHIP DYNAMICS — Mentor/mentee, rivalry, cliques, corruption chains
5. FATIGUE-PERSONALITY INTERACTION — Tired + low honesty = dangerous
6. CONTEXT-AWARE MESSAGES — Same person speaks differently to boss vs peer
"""
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PersonalityProfile:
    """Multi-dimensional personality — all traits independent."""
    competence: float       # 0-1: skill level (NOT = experience)
    honesty: float          # 0-1: truthful vs hides/lies
    motivation: float       # 0-1: goes beyond vs bare minimum
    risk_tolerance: float   # 0-1: shortcuts vs follows every rule
    communication: float    # 0-1: clear/detailed vs unclear/lazy
    stress_resilience: float  # 0-1: calm under fire vs panics
    social_influence: float   # 0-1: follower vs leader/manipulator
    corruption: float       # 0-1: honest vs steals/fakes/bribes
    fatigue_resistance: float  # 0-1: sharp after 12h vs zombie after 4h
    
    # Communication style traits (consistent per person)
    emoji_tendency: float = 0.0    # 0-1: never uses emoji vs uses in every msg
    punctuation_care: float = 0.5  # 0-1: no caps/periods vs perfect grammar
    verbosity: float = 0.5         # 0-1: "done" vs writes paragraphs
    response_speed: float = 0.5    # 0-1: delayed responder vs instant
    humor_tendency: float = 0.0    # 0-1: always serious vs cracks jokes often
    formality: float = 0.5         # 0-1: "yo bro" vs "sir, please note that"
    personal_sharing: float = 0.0  # 0-1: never mentions home vs overshares
    
    # Dynamic state (changes during episode)
    current_stress: float = 0.0
    current_mood: str = "neutral"
    consecutive_shifts: int = 1
    recent_mistake: bool = False
    recently_praised: bool = False
    hours_into_shift: float = 0.0  # Affects alertness-personality interaction
    messages_sent: int = 0         # Track how much this person has spoken
    
    def get_effective_honesty(self) -> float:
        """Honesty drops when stressed or after making a mistake."""
        h = self.honesty
        if self.recent_mistake:
            h *= 0.6  # Much more likely to lie after making an error
        if self.current_stress > 0.7:
            h *= 0.85  # Stress reduces honesty slightly
        return max(0.05, h)
    
    def get_effective_motivation(self) -> float:
        """Motivation affected by mood and consecutive shifts."""
        m = self.motivation
        if self.current_mood == "frustrated":
            m *= 0.5
        elif self.current_mood == "happy":
            m *= 1.2
        if self.consecutive_shifts > 3:
            m *= 0.7  # Consecutive shifts kill motivation
        if self.recently_praised:
            m *= 1.3
        return max(0.05, min(1.0, m))
    
    def get_effective_risk_tolerance(self) -> float:
        """Risk tolerance increases when tired or pressured."""
        r = self.risk_tolerance
        if self.current_stress > 0.6:
            r *= 1.3  # Stressed people take more shortcuts
        if self.consecutive_shifts > 4:
            r *= 1.2  # Exhausted = careless
        return min(0.95, r)


def generate_personality(experience_years: float, rng: random.Random) -> PersonalityProfile:
    """Generate personality with WEAK correlation to experience.
    
    A junior can be a prodigy. A senior can be a deadweight.
    Traits are mostly random with slight experience bias.
    """
    # Competence: slight positive bias with experience, HIGH variance
    exp_bias = min(0.15, experience_years * 0.007)
    competence = max(0.1, min(1.0, rng.gauss(0.55 + exp_bias, 0.2)))
    
    # Honesty: most people are somewhat honest (right-skewed)
    honesty = max(0.1, min(1.0, rng.betavariate(4, 2)))  # Beta distribution skews honest
    
    # Motivation: bell curve with burnout for very experienced
    burnout = -0.08 if experience_years > 18 else 0.0
    motivation = max(0.1, min(1.0, rng.gauss(0.6 + burnout, 0.2)))
    
    # Risk tolerance: decreases with experience (seen bad outcomes)
    risk_bias = max(-0.2, -experience_years * 0.01)
    risk_tolerance = max(0.05, min(0.95, rng.gauss(0.5 + risk_bias, 0.18)))
    
    # Communication: slight improvement with experience
    comm_bias = min(0.1, experience_years * 0.005)
    communication = max(0.1, min(1.0, rng.gauss(0.5 + comm_bias, 0.2)))
    
    # Stress resilience: moderate improvement with experience
    stress_bias = min(0.15, experience_years * 0.008)
    stress_resilience = max(0.1, min(1.0, rng.gauss(0.5 + stress_bias, 0.2)))
    
    # Social influence: peaks mid-career (established but not yet "old guard")
    if experience_years < 2:
        social_base = 0.25
    elif experience_years < 8:
        social_base = 0.5
    elif experience_years < 20:
        social_base = 0.65
    else:
        social_base = 0.55  # Slightly drops (some disengage)
    social_influence = max(0.1, min(1.0, rng.gauss(social_base, 0.18)))
    
    # Corruption: RARE but exists. Left-skewed (most people honest)
    # Higher in mid-career (access + opportunity)
    corr_base = 0.08 if experience_years < 5 else 0.15 if experience_years < 20 else 0.1
    corruption = max(0.0, min(0.9, rng.expovariate(1.0 / corr_base)))
    corruption = min(0.9, corruption)
    
    # Fatigue resistance: random, slight decrease with age
    age_factor = -0.04 if experience_years > 25 else 0.0
    fatigue_resistance = max(0.15, min(1.0, rng.gauss(0.6 + age_factor, 0.18)))
    
    return PersonalityProfile(
        competence=round(competence, 2),
        honesty=round(honesty, 2),
        motivation=round(motivation, 2),
        risk_tolerance=round(risk_tolerance, 2),
        communication=round(communication, 2),
        stress_resilience=round(stress_resilience, 2),
        social_influence=round(social_influence, 2),
        corruption=round(min(corruption, 0.9), 2),
        fatigue_resistance=round(fatigue_resistance, 2),
        # Communication style — fully random, no experience correlation
        emoji_tendency=round(rng.betavariate(1.5, 4), 2),  # Most people low emoji
        punctuation_care=round(rng.betavariate(2, 3), 2),   # Skews toward casual
        verbosity=round(rng.gauss(0.5, 0.2), 2),
        response_speed=round(rng.uniform(0.2, 0.9), 2),
        humor_tendency=round(rng.betavariate(2, 5), 2),     # Most people somewhat serious
        formality=round(max(0.1, min(0.95, rng.gauss(0.4, 0.2))), 2),
        personal_sharing=round(rng.betavariate(1.5, 5), 2),  # Most people don't overshare
    )


# ═══════════════════════════════════════════════════════════════════
# STATE CHANGES — Events modify personality temporarily
# ═══════════════════════════════════════════════════════════════════

def update_personality_state(personality: PersonalityProfile, event_category: str,
                             rng: random.Random):
    """Update personality state based on what just happened.
    
    Called after each event to simulate psychological responses.
    """
    # Stress accumulation
    stress_events = {"crisis": 0.3, "safety_accidents": 0.2, "mistakes_failures": 0.15}
    if event_category in stress_events:
        personality.current_stress = min(1.0,
            personality.current_stress + stress_events[event_category] * (1.0 - personality.stress_resilience))
    else:
        # Stress slowly recovers
        personality.current_stress = max(0.0, personality.current_stress - 0.02)
    
    # Mood changes
    if event_category == "crisis":
        personality.current_mood = "scared" if personality.stress_resilience < 0.5 else "focused"
    elif event_category == "mistakes_failures":
        personality.recent_mistake = True
        personality.current_mood = "frustrated"
    elif event_category in ("human_relations", "holidays_breaks"):
        personality.current_mood = "happy"
        personality.recent_mistake = False  # Social time resets
    elif event_category == "leadership" and rng.random() < 0.3:
        personality.recently_praised = True
    
    # Recovery over time (neutral drift)
    if rng.random() < 0.1:
        personality.current_mood = "neutral"
        personality.recently_praised = False


# ═══════════════════════════════════════════════════════════════════
# MESSAGE MODIFIERS — Personality affects HOW people communicate
# ═══════════════════════════════════════════════════════════════════

def modify_message_by_personality(message: str, personality: PersonalityProfile,
                                  category: str, rng: random.Random) -> str:
    """Modify a message based on worker personality and current state.
    
    CRITICAL: Personality must be UNDETECTABLE in individual messages.
    It only shows as statistical patterns over many messages:
    - Low motivation → shorter messages, less detail
    - High competence → more technical precision
    - Low honesty → omits negative details, passive voice
    - High risk → skips safety mentions
    - Low communication → grammar errors, incomplete sentences
    
    NO template injection. Only style modification of existing message.
    """
    # Update state based on this event
    update_personality_state(personality, category, rng)
    
    # Only modify ~20% of messages (rest pass through unchanged)
    if rng.random() > 0.20:
        return message
    
    eff_motivation = personality.get_effective_motivation()
    eff_honesty = personality.get_effective_honesty()
    eff_risk = personality.get_effective_risk_tolerance()
    
    words = message.split()
    if not words:
        return message
    
    # === LOW MOTIVATION: truncate messages, less effort ===
    if eff_motivation < 0.35 and len(words) > 5:
        # Cut message short (lazy people don't write full details)
        cut_point = max(3, int(len(words) * rng.uniform(0.3, 0.6)))
        message = " ".join(words[:cut_point])
        # Sometimes don't even finish the sentence
        if rng.random() < 0.3:
            message = message.rstrip(".,!") + "..."
    
    # === HIGH MOTIVATION: add follow-up actions ===
    elif eff_motivation > 0.85 and rng.random() < 0.3:
        follow_ups = [
            ". will monitor and update",
            ". informing next shift as well",
            ". documenting for reference",
            ". already started on next step",
            ". following up with vendor today",
            ". checked twice to be sure",
        ]
        message = message.rstrip(".") + rng.choice(follow_ups)
    
    # === LOW HONESTY + PROBLEM EVENT: soften/minimize ===
    if eff_honesty < 0.4 and category in ("mistakes_failures", "quality", "safety_accidents"):
        # Replace strong negative words with softer ones
        replacements = {
            "failed": "didn't fully meet spec",
            "broken": "needs attention",
            "leak": "minor seepage",
            "error": "deviation",
            "wrong": "different than expected",
            "damage": "wear marks",
            "accident": "incident",
            "serious": "notable",
            "urgent": "should be looked at",
            "critical": "important",
            "crashed": "stopped unexpectedly",
            "contaminated": "needs verification",
        }
        msg_lower = message.lower()
        for bad, soft in replacements.items():
            if bad in msg_lower:
                message = message.replace(bad, soft, 1)
                message = message.replace(bad.capitalize(), soft.capitalize(), 1)
                break  # Only soften one word per message
    
    # === HIGH RISK TOLERANCE: remove safety qualifiers ===
    elif eff_risk > 0.75 and rng.random() < 0.25:
        # Strip safety-related phrases (risky workers don't mention precautions)
        safety_phrases = [
            "wearing PPE", "safety check", "following procedure",
            "as per SOP", "with proper", "after verification",
            "with caution", "carefully", "safety first",
            "with clearance", "after isolation", "with permit",
        ]
        for phrase in safety_phrases:
            if phrase.lower() in message.lower():
                message = message.replace(phrase, "").replace("  ", " ").strip()
                break
    
    # === LOW COMMUNICATION: grammar issues, incomplete ===
    if personality.communication < 0.3 and len(words) > 4:
        # Drop articles and connectors (how unclear speakers write)
        drop_words = {"the", "a", "an", "is", "are", "was", "were", "has", "have", "been"}
        if rng.random() < 0.3:
            words = [w for w in words if w.lower() not in drop_words or rng.random() > 0.5]
            message = " ".join(words)
    
    # === HIGH COMPETENCE: add technical precision ===
    elif personality.competence > 0.85 and rng.random() < 0.2:
        precision_additions = [
            f" (reading: {rng.randint(10,99)}.{rng.randint(0,9)})",
            f" — confirmed at {rng.randint(1,12)}:{rng.randint(0,5)}{rng.randint(0,9)}",
            f" ref: logbook entry #{rng.randint(100,999)}",
            f" within ±{rng.uniform(0.1, 2.0):.1f}% tolerance",
        ]
        message = message.rstrip(".") + rng.choice(precision_additions)
    
    # === FATIGUE (consecutive shifts): typos increase, shorter msgs ===
    if personality.consecutive_shifts > 3 and personality.fatigue_resistance < 0.4:
        if len(words) > 6:
            # Tired people write shorter
            message = " ".join(words[:max(4, len(words)//2)])
    
    # === STRESS: caps and urgency markers when stressed ===
    if personality.current_stress > 0.7 and category in ("crisis", "safety_accidents"):
        if rng.random() < 0.3:
            # Stressed people sometimes ALL CAPS fragments
            first_word = words[0].upper()
            message = first_word + " " + " ".join(words[1:])
    
    return message


# ═══════════════════════════════════════════════════════════════════
# STYLE LAYER — Applies consistent communication quirks per person
# This runs AFTER the main personality modifier
# ═══════════════════════════════════════════════════════════════════

def apply_communication_style(message: str, personality: PersonalityProfile,
                              hour: int, rng: random.Random) -> str:
    """Apply personal communication style to message.
    
    Makes SAME person sound consistent across all messages:
    - Some people always use emoji
    - Some never capitalize
    - Some write novels, others write single words
    - Some are formal, others casual
    - Time of day affects everyone differently
    
    Runs on ~40% of messages for visible but natural style.
    """
    if rng.random() > 0.40:
        return message
    
    personality.messages_sent += 1
    words = message.split()
    
    # === VERBOSITY ===
    if personality.verbosity < 0.25 and len(words) > 6:
        message = " ".join(words[:max(3, int(len(words) * 0.5))])
    elif personality.verbosity > 0.8 and len(words) > 3 and rng.random() < 0.3:
        fillers = [
            " — just to let everyone know",
            " if that makes sense",
            " but yeah that's the situation",
            " so basically that's what happened",
            " anyway moving on",
        ]
        message = message.rstrip(".") + rng.choice(fillers)
    
    # === EMOJI TENDENCY ===
    if personality.emoji_tendency > 0.7 and rng.random() < 0.4:
        emojis = ["👍", "✅", "💪", "🙏", "😤", "😂", "👀", "🔥", "⚡", "☕"]
        message = message + " " + rng.choice(emojis)
    
    # === PUNCTUATION CARE ===
    if personality.punctuation_care < 0.2:
        message = message.lower().rstrip(".,!?")
    elif personality.punctuation_care > 0.85 and rng.random() < 0.3:
        if message and message[-1] not in ".!?":
            message = message + "."
        if message:
            message = message[0].upper() + message[1:]
    
    # === FORMALITY ===
    if personality.formality > 0.8 and rng.random() < 0.2:
        formal_starts = ["Please note: ", "For your information: ", "Kindly note — ", "Update: "]
        message = rng.choice(formal_starts) + message
    elif personality.formality < 0.2 and rng.random() < 0.15:
        casual_starts = ["yo ", "bro ", "guys ", "dude ", "boss "]
        message = rng.choice(casual_starts) + message
    
    # === TIME-OF-DAY EFFECT ===
    if (hour >= 22 or hour <= 5) and rng.random() < 0.25:
        if len(words) > 8:
            message = " ".join(words[:max(4, len(words)//2)])
        if rng.random() < 0.2:
            message = message + ".."
    
    # === PERSONAL LIFE BLEED ===
    if personality.personal_sharing > 0.7 and rng.random() < 0.03:
        bleeds = [
            ". btw kid has exam tomorrow might leave early",
            ". sorry distracted, family called",
            ". headache since morning. managing",
            ". back pain acting up today",
            ". didn't sleep well last night",
        ]
        message = message.rstrip(".") + rng.choice(bleeds)
    
    # === HUMOR TENDENCY ===
    if personality.humor_tendency > 0.7 and rng.random() < 0.04:
        humor = [" 😂", " (as usual)", " ...surprise surprise", " 💀", " lol"]
        message = message.rstrip(".") + rng.choice(humor)
    
    return message


# ═══════════════════════════════════════════════════════════════════
# HIDDEN BEHAVIORS — Things workers do that aren't in the SOP
# Injected rarely but make data realistic for fraud detection
# ═══════════════════════════════════════════════════════════════════

HIDDEN_BEHAVIORS = {
    "time_theft": [
        # Shows up in timing patterns (message at 9:05 saying "reached at 8:30")
        "reached site at 8:30",  # actually came at 9:00
        "stuck in traffic. will be 10 min late",  # every Monday...
        "leaving at 5 sharp today. personal work",  # left at 4:30
        "was in warehouse doing inventory",  # was on phone for 45 min
    ],
    "fake_inspection": [
        # Impossibly fast completion times
        "full safety check done ✅ all 47 points clear",  # in 3 minutes?
        "hourly round complete. all equipment normal",  # didn't leave the office
        "fire extinguisher check done. all 23 units OK",  # checked 5 max
        "tool inspection complete. all accounted for",  # didn't open the box
    ],
    "buddy_system": [
        # Covering for absent friends
        "Ramesh is on site. he went to check transformer",  # he's not here
        "he's in the washroom. will be back in 5",  # been gone 40 minutes
        "she had to step out for family emergency. covering her area",  # sleeping in car
    ],
    "material_misuse": [
        # Subtle signs of theft/misuse
        "paint consumption this month is higher than expected. wastage during application",
        "fuel reading doesn't match distance. might be meter calibration issue",
        "consumable usage up 20% this month. will investigate",
        "spare parts inventory count short by 3 units. checking records",
    ],
}


def inject_hidden_behavior(personality: PersonalityProfile, category: str,
                           rng: random.Random) -> Optional[str]:
    """Inject subtle signs of hidden behaviors.
    
    NOT obvious templates. Just subtle timing/detail anomalies:
    - Corrupt worker: reports are suspiciously perfect/fast
    - Lazy worker: messages have less detail than expected
    - Time thief: timing inconsistencies
    
    Rate: ~0.3% — extremely rare, only detectable with statistical analysis.
    """
    if rng.random() > 0.003:
        return None
    
    # Corrupt + quality/maintenance: suspiciously perfect quick reports
    if personality.corruption > 0.4 and category in ("quality", "maintenance"):
        quick_fakes = [
            "all points checked. everything within limits",
            "complete. no deviations found",
            "verified. all parameters normal. signed off",
            "done. all OK",
            "checked and cleared",
        ]
        return rng.choice(quick_fakes)
    
    # Low motivation + any: minimal effort evident
    if personality.motivation < 0.3:
        minimal = [
            "done",
            "ok",
            "noted",
            "checked",
            "see above",
        ]
        return rng.choice(minimal)
    
    return None


# ═══════════════════════════════════════════════════════════════════
# PERSONALITY CACHE — Persistent per episode
# ═══════════════════════════════════════════════════════════════════

_personality_cache: Dict[str, PersonalityProfile] = {}


def get_worker_personality(worker_id: str, experience_years: float,
                           rng: random.Random) -> PersonalityProfile:
    """Get or create a persistent personality for a worker."""
    if worker_id not in _personality_cache:
        p_rng = random.Random(hash(worker_id) % (2**32))
        _personality_cache[worker_id] = generate_personality(experience_years, p_rng)
    return _personality_cache[worker_id]


def clear_personality_cache():
    """Clear cache between episodes."""
    _personality_cache.clear()
