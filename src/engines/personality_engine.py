"""Personality & Emotional State Engine — Complete human psychology simulation.

FULL EMOTIONAL SPECTRUM — Not just anger/defiance. Real humans feel:
- Happiness, pride, gratitude, excitement, contentment, relief, love
- Sadness, grief, loneliness, nostalgia, melancholy
- Anger, frustration, resentment, jealousy, disgust
- Fear, anxiety, dread, worry, nervousness
- Surprise, shock, confusion, curiosity
- Shame, guilt, embarrassment, humiliation
- Lust, desire, attraction
- Hope, anticipation, ambition
- Boredom, apathy, indifference, contempt

Each person's personality determines:
- Which emotions they feel more intensely
- How long emotions persist (some people hold grudges for years)
- How emotions manifest in behavior (some cry, some rage, some go silent)
- Inter-personal dynamics (friendships, grudges, romantic interests)
"""
from typing import Any, Dict, List, Optional
from core.random.deterministic_rng import DeterministicRNG
import hashlib


# =============================================================================
# PERSONALITY TRAITS (permanent, barely change over lifetime)
# =============================================================================

PERSONALITY_TRAITS = [
    # Big Five (core psychology)
    'conscientiousness',    # 0-1: reliability, rule-following
    'neuroticism',          # 0-1: emotional volatility, stress sensitivity
    'agreeableness',        # 0-1: cooperative vs combative
    'openness',             # 0-1: curiosity, willingness to try new
    'extraversion',         # 0-1: talkative, social, energetic
    
    # Industrial-specific traits
    'risk_tolerance',       # 0-1: willingness to cut corners
    'authority_respect',    # 0-1: obedience (low = rebel)
    'temper',               # 0-1: how quickly anger rises
    'resilience',           # 0-1: bounce-back speed from setbacks
    'ambition',             # 0-1: desire for advancement
    'loyalty',              # 0-1: commitment to organization
    'empathy',              # 0-1: sensitivity to others' emotions
    'pride',                # 0-1: self-image importance
    'jealousy_tendency',    # 0-1: resentment when others succeed
    'gossip_tendency',      # 0-1: likelihood to spread information
    'romantic_inclination', # 0-1: tendency for workplace attraction
    'greed',                # 0-1: material motivation
    'patience',             # 0-1: tolerance for slow progress
    'humor',                # 0-1: tendency to joke/deflect with humor
    'stubbornness',         # 0-1: resistance to changing mind
]



# =============================================================================
# FULL EMOTIONAL SPECTRUM — 40+ emotions (transient, decay each tick)
# =============================================================================

EMOTIONS = {
    # POSITIVE EMOTIONS
    'happiness': {'baseline': 0.4, 'decay_rate': 0.03},
    'pride': {'baseline': 0.3, 'decay_rate': 0.02},
    'gratitude': {'baseline': 0.2, 'decay_rate': 0.04},
    'excitement': {'baseline': 0.1, 'decay_rate': 0.06},
    'contentment': {'baseline': 0.4, 'decay_rate': 0.01},
    'relief': {'baseline': 0.0, 'decay_rate': 0.08},
    'love': {'baseline': 0.0, 'decay_rate': 0.005},  # Slow decay
    'hope': {'baseline': 0.3, 'decay_rate': 0.02},
    'satisfaction': {'baseline': 0.3, 'decay_rate': 0.02},
    'amusement': {'baseline': 0.1, 'decay_rate': 0.07},
    'inspiration': {'baseline': 0.1, 'decay_rate': 0.05},
    
    # NEGATIVE EMOTIONS
    'sadness': {'baseline': 0.1, 'decay_rate': 0.02},
    'grief': {'baseline': 0.0, 'decay_rate': 0.005},  # Very slow decay
    'loneliness': {'baseline': 0.15, 'decay_rate': 0.01},
    'nostalgia': {'baseline': 0.1, 'decay_rate': 0.01},
    'melancholy': {'baseline': 0.05, 'decay_rate': 0.015},
    'anger': {'baseline': 0.0, 'decay_rate': 0.04},
    'frustration': {'baseline': 0.1, 'decay_rate': 0.03},
    'resentment': {'baseline': 0.0, 'decay_rate': 0.02},  # Decays slowly but not glacially
    'jealousy': {'baseline': 0.0, 'decay_rate': 0.02},
    'disgust': {'baseline': 0.0, 'decay_rate': 0.06},
    'contempt': {'baseline': 0.0, 'decay_rate': 0.01},
    'fear': {'baseline': 0.05, 'decay_rate': 0.04},
    'anxiety': {'baseline': 0.15, 'decay_rate': 0.02},
    'dread': {'baseline': 0.0, 'decay_rate': 0.03},
    'nervousness': {'baseline': 0.1, 'decay_rate': 0.05},
    'surprise': {'baseline': 0.0, 'decay_rate': 0.1},  # Fast decay
    'shock': {'baseline': 0.0, 'decay_rate': 0.04},
    'confusion': {'baseline': 0.1, 'decay_rate': 0.06},
    'curiosity': {'baseline': 0.2, 'decay_rate': 0.03},
    'shame': {'baseline': 0.0, 'decay_rate': 0.02},
    'guilt': {'baseline': 0.0, 'decay_rate': 0.015},
    'embarrassment': {'baseline': 0.0, 'decay_rate': 0.07},
    'humiliation': {'baseline': 0.0, 'decay_rate': 0.01},
    'lust': {'baseline': 0.0, 'decay_rate': 0.03},
    'desire': {'baseline': 0.1, 'decay_rate': 0.02},
    'boredom': {'baseline': 0.2, 'decay_rate': 0.04},
    'apathy': {'baseline': 0.1, 'decay_rate': 0.01},
    'indifference': {'baseline': 0.1, 'decay_rate': 0.01},
    
    # WORK-SPECIFIC EMOTIONS
    'stress': {'baseline': 0.2, 'decay_rate': 0.03},
    'fatigue': {'baseline': 0.1, 'decay_rate': 0.02},
    'alertness': {'baseline': 0.6, 'decay_rate': 0.02},
    'morale': {'baseline': 0.5, 'decay_rate': 0.01},
    'trust_in_management': {'baseline': 0.5, 'decay_rate': 0.005},
    'camaraderie': {'baseline': 0.4, 'decay_rate': 0.01},
}



# =============================================================================
# LIFE EVENTS — Things that happen and their emotional impacts
# =============================================================================

LIFE_EVENTS = {
    # WORKPLACE POSITIVE
    'praised_by_manager': {'happiness': +0.3, 'pride': +0.4, 'morale': +0.2, 'satisfaction': +0.2},
    'received_promotion': {'happiness': +0.6, 'pride': +0.5, 'excitement': +0.4, 'hope': +0.3, 'morale': +0.4},
    'bonus_received': {'happiness': +0.3, 'gratitude': +0.2, 'satisfaction': +0.3},
    'successful_repair': {'pride': +0.2, 'satisfaction': +0.3, 'camaraderie': +0.1},
    'recognized_publicly': {'pride': +0.5, 'happiness': +0.4, 'embarrassment': +0.1},
    'mentored_someone': {'satisfaction': +0.3, 'pride': +0.2, 'camaraderie': +0.2},
    'learned_new_skill': {'pride': +0.2, 'excitement': +0.2, 'inspiration': +0.3},
    
    # WORKPLACE NEGATIVE
    'scolded_by_manager': {'anger': +0.4, 'humiliation': +0.3, 'resentment': +0.3, 'morale': -0.3},
    'received_demotion': {'humiliation': +0.5, 'anger': +0.4, 'sadness': +0.4, 'morale': -0.5},
    'passed_over_promotion': {'jealousy': +0.4, 'resentment': +0.4, 'frustration': +0.5, 'morale': -0.3},
    'colleague_promoted_unfairly': {'jealousy': +0.5, 'resentment': +0.3, 'contempt': +0.2, 'disgust': +0.2},
    'warning_issued': {'fear': +0.3, 'shame': +0.2, 'anger': +0.2, 'anxiety': +0.3},
    'blamed_for_failure': {'anger': +0.5, 'frustration': +0.4, 'resentment': +0.3, 'shame': +0.2},
    'overtime_forced': {'frustration': +0.3, 'fatigue': +0.4, 'resentment': +0.2},
    'salary_delayed': {'anxiety': +0.3, 'anger': +0.3, 'frustration': +0.4, 'stress': +0.3},
    
    # SAFETY/INCIDENT EVENTS
    'witnessed_accident': {'fear': +0.6, 'shock': +0.5, 'anxiety': +0.4, 'sadness': +0.3},
    'near_miss_incident': {'fear': +0.5, 'relief': +0.4, 'alertness': +0.4, 'stress': +0.3},
    'colleague_injured': {'fear': +0.4, 'sadness': +0.4, 'camaraderie': +0.2, 'grief': +0.2},
    'colleague_died': {'grief': +0.8, 'shock': +0.6, 'fear': +0.5, 'sadness': +0.7},
    'personally_injured': {'fear': +0.6, 'anger': +0.3, 'anxiety': +0.5, 'stress': +0.5},
    
    # PERSONAL LIFE
    'family_issue': {'stress': +0.4, 'sadness': +0.3, 'anxiety': +0.3, 'alertness': -0.2},
    'child_success': {'happiness': +0.5, 'pride': +0.6, 'gratitude': +0.3},
    'marriage_problems': {'sadness': +0.4, 'stress': +0.4, 'loneliness': +0.3, 'anger': +0.2},
    'new_love_interest': {'lust': +0.4, 'excitement': +0.5, 'happiness': +0.3, 'desire': +0.3},
    'heartbreak': {'sadness': +0.6, 'grief': +0.3, 'loneliness': +0.5, 'anger': +0.2},
    'financial_stress': {'anxiety': +0.5, 'stress': +0.4, 'frustration': +0.3, 'fear': +0.2},
    'family_celebration': {'happiness': +0.4, 'gratitude': +0.2, 'love': +0.2},
    'parent_health_crisis': {'fear': +0.4, 'sadness': +0.5, 'stress': +0.4, 'guilt': +0.2},
    'new_baby': {'happiness': +0.5, 'anxiety': +0.3, 'love': +0.5, 'fatigue': +0.3},
    
    # SOCIAL/INTERPERSONAL
    'colleague_fired': {'fear': +0.2, 'relief': +0.1, 'guilt': +0.1},
    'friendship_formed': {'happiness': +0.2, 'camaraderie': +0.4, 'trust_in_management': +0.05},
    'betrayed_by_friend': {'anger': +0.4, 'sadness': +0.3, 'resentment': +0.5, 'loneliness': +0.2},
    'public_humiliation': {'humiliation': +0.7, 'anger': +0.5, 'shame': +0.4, 'resentment': +0.4},
    'sexual_harassment': {'fear': +0.5, 'anger': +0.6, 'disgust': +0.5, 'shame': +0.3},
    'festival_celebration': {'happiness': +0.3, 'camaraderie': +0.3, 'nostalgia': +0.2},
    'retirement_of_mentor': {'sadness': +0.3, 'nostalgia': +0.4, 'loneliness': +0.2, 'gratitude': +0.2},
    
    # ORGANIZATIONAL
    'management_change': {'anxiety': +0.3, 'fear': +0.2, 'curiosity': +0.2},
    'layoff_rumors': {'fear': +0.5, 'anxiety': +0.5, 'stress': +0.4},
    'company_winning': {'pride': +0.3, 'happiness': +0.2, 'hope': +0.2},
    'company_in_trouble': {'anxiety': +0.4, 'fear': +0.3, 'stress': +0.3},
    'workplace_romance_discovered': {'embarrassment': +0.4, 'fear': +0.2, 'excitement': +0.1},
}



# =============================================================================
# BEHAVIORAL MODES — How the person ACTS based on emotions
# =============================================================================

BEHAVIORAL_MODES = [
    'productive',         # Normal, doing job well
    'motivated',          # Above average, proactive
    'enthusiastic',       # High energy, inspiring others
    'collaborative',      # Helping everyone, mentoring
    'disengaged',         # Going through motions
    'angry',              # Hostile, argumentative
    'defiant',            # Refusing tasks, pushing back
    'anxious',            # Over-escalating, paranoid
    'exhausted',          # Barely functioning
    'fearful',            # Avoiding responsibility
    'complacent',         # Cutting corners, ignoring warnings
    'depressed',          # Withdrawn, minimal communication
    'distracted',         # Mind elsewhere (personal issues)
    'resentful',          # Passive aggressive, sabotaging
    'flirtatious',        # Workplace attraction affecting behavior
    'grieving',           # After loss, fragile
    'inspired',           # After success, trying new things
    'suspicious',         # Distrusting everyone
    'guilt_ridden',       # Overcompensating for past mistake
    'nostalgic',          # Talking about old days
    'jealous',            # Undermining colleagues
    'power_hungry',       # Politicking for advancement
    'burnt_out',          # Complete emotional exhaustion
    'euphoric',           # Temporarily very happy (celebration, love)
    'vengeful',           # Actively seeking payback
]


def _generate_personality(emp_id: str, region: str, rng=None) -> Dict[str, float]:
    """Generate deterministic personality from employee ID."""
    seed_int = int(hashlib.sha256(f"personality:{emp_id}".encode()).hexdigest()[:12], 16)
    import random
    prng = random.Random(seed_int)
    
    personality = {}
    for trait in PERSONALITY_TRAITS:
        personality[trait] = round(prng.uniform(0.05, 0.95), 3)
    
    # Regional subtle biases (cultural tendencies, not stereotypes)
    if region in ('south_india', 'north_india'):
        personality['authority_respect'] = min(1.0, personality['authority_respect'] + 0.08)
        personality['loyalty'] = min(1.0, personality['loyalty'] + 0.05)
        personality['patience'] = min(1.0, personality['patience'] + 0.05)
    if region == 'middle_east':
        personality['authority_respect'] = min(1.0, personality['authority_respect'] + 0.12)
        personality['pride'] = min(1.0, personality['pride'] + 0.08)
    if region == 'europe':
        personality['conscientiousness'] = min(1.0, personality['conscientiousness'] + 0.08)
        personality['risk_tolerance'] = max(0.0, personality['risk_tolerance'] - 0.05)
    if region == 'americas':
        personality['ambition'] = min(1.0, personality['ambition'] + 0.05)
        personality['extraversion'] = min(1.0, personality['extraversion'] + 0.05)
    
    return personality


def _init_emotional_state() -> Dict[str, float]:
    """Initialize emotional state with baselines."""
    return {name: info['baseline'] for name, info in EMOTIONS.items()}



# =============================================================================
# MAIN ENGINE CLASS
# =============================================================================

class PersonalityEngine:
    """
    Maintains and evolves personality + full emotional spectrum for each member.
    
    - 20 personality traits (permanent)
    - 44 emotional states (transient, decay toward baseline)
    - 40+ life events that trigger emotional changes
    - 25 behavioral modes derived from emotional state
    - Inter-personal relationships (friendships, grudges, attractions)
    """

    def __init__(self, decay_rate: float = 0.05, event_check_interval: int = 120):
        self.decay_rate = decay_rate
        self.event_check_interval = event_check_interval

    def process(self, world_state: Any, rng: DeterministicRNG) -> None:
        """Main personality engine tick."""
        hidden = world_state.hidden_state
        if 'workforce' not in hidden:
            return
        
        if 'personality_states' not in hidden:
            self._init_all_personalities(hidden)
        
        personalities = hidden['personality_states']
        wf = hidden['workforce']
        roster = wf['roster']
        tick = world_state.world_tick
        
        for emp_id in sorted(roster.keys()):
            emp = roster[emp_id]
            if not emp['active']:
                continue
            
            if emp_id not in personalities:
                region = wf.get('region', 'south_india')
                personalities[emp_id] = {
                    'traits': _generate_personality(emp_id, region),
                    'emotions': _init_emotional_state(),
                    'behavioral_mode': 'productive',
                    'life_events_history': [],
                    'relationships': {},
                    'grudges': {},
                    'attractions': {},
                }
            
            ps = personalities[emp_id]
            
            # 1. Decay all emotions toward baseline
            self._decay_emotions(ps['emotions'])
            
            # 2. Generate random life events at intervals
            if tick % self.event_check_interval == 0:
                event_rng = rng.split(f"ev_{emp_id}_{tick}")
                events = self._generate_events(world_state, event_rng, emp_id, emp, ps)
                for event in events:
                    self._apply_life_event(ps, event)
            
            # 3. Determine behavioral mode
            ps['behavioral_mode'] = self._determine_mode(ps['traits'], ps['emotions'])
            
            # 4. Feed back to workforce roster
            emp['morale'] = ps['emotions'].get('morale', 0.5)
            emp['behavioral_mode'] = ps['behavioral_mode']

    def _init_all_personalities(self, hidden: Dict) -> None:
        """Initialize personality for all active employees."""
        wf = hidden.get('workforce', {})
        roster = wf.get('roster', {})
        region = wf.get('region', 'south_india')
        personalities = {}
        for emp_id, emp in roster.items():
            if emp['active']:
                personalities[emp_id] = {
                    'traits': _generate_personality(emp_id, region),
                    'emotions': _init_emotional_state(),
                    'behavioral_mode': 'productive',
                    'life_events_history': [],
                    'relationships': {},
                    'grudges': {},
                    'attractions': {},
                }
        hidden['personality_states'] = personalities


    def _decay_emotions(self, emotions: Dict[str, float]) -> None:
        """Decay all emotions toward their baselines."""
        for name, info in EMOTIONS.items():
            if name in emotions:
                current = emotions[name]
                baseline = info['baseline']
                decay = info['decay_rate'] * self.decay_rate
                diff = baseline - current
                emotions[name] = round(max(0.0, min(1.0, current + diff * decay)), 4)

    def _apply_life_event(self, ps: Dict, event_name: str) -> None:
        """Apply emotional impacts of a life event."""
        effects = LIFE_EVENTS.get(event_name)
        if not effects:
            return
        emotions = ps['emotions']
        for key, delta in effects.items():
            if key in emotions:
                emotions[key] = round(max(0.0, min(1.0, emotions[key] + delta)), 4)
        ps['life_events_history'].append(event_name)
        if len(ps['life_events_history']) > 100:
            ps['life_events_history'] = ps['life_events_history'][-100:]

    def _generate_events(self, world_state, rng, emp_id, emp, ps) -> List[str]:
        """Generate contextual random life events.
        
        Probabilities tuned so ~30-40% of workforce experiences SOMETHING
        every event check cycle. This creates realistic variety where not
        everyone is 'productive' all the time.
        """
        events = []
        hidden = world_state.hidden_state
        anomaly = hidden.get('anomaly_active', False)
        stress = hidden.get('systemic_stress_level', 0.0)
        traits = ps.get('traits', {})
        
        # === WORK EVENTS (common — happen frequently) ===
        
        # Manager interactions (daily occurrence in any workplace)
        if rng.random() < 0.08:  # 8% chance each cycle
            if emp.get('performance_score', 0.5) > 0.7:
                events.append('praised_by_manager')
            elif emp.get('performance_score', 0.5) < 0.4:
                events.append('scolded_by_manager')
        
        # Anomaly-driven events
        if anomaly:
            if rng.random() < 0.12: events.append('near_miss_incident')
            if rng.random() < 0.08: events.append('scolded_by_manager')
            if rng.random() < 0.05: events.append('witnessed_accident')
        
        # Overtime (very common in industrial settings)
        if stress > 0.3 and rng.random() < 0.15:
            events.append('overtime_forced')
        
        # Boredom/monotony during calm periods (most common "event")
        if stress < 0.2 and not anomaly:
            if rng.random() < 0.20:  # 20% feel bored during calm
                ps['emotions']['boredom'] = min(1.0, ps['emotions'].get('boredom', 0.2) + 0.15)
            if rng.random() < 0.05:
                events.append('friendship_formed')
        
        # Career frustration (common but not for EVERYONE)
        if emp.get('years_since_last_promotion', 0) > 8:
            if rng.random() < 0.04:
                events.append('passed_over_promotion')
        
        # Colleague dynamics (rare — not everyone notices)
        if traits.get('jealousy_tendency', 0) > 0.5 and rng.random() < 0.02:
            events.append('colleague_promoted_unfairly')
        
        # Salary/financial issues (monthly stress)
        if rng.random() < 0.03:
            events.append('salary_delayed')
        if rng.random() < 0.05:
            events.append('financial_stress')
        
        # === PERSONAL LIFE (less frequent but high impact) ===
        r = rng.random()
        if r < 0.015: events.append('family_issue')
        elif r < 0.025: events.append('child_success')
        elif r < 0.030: events.append('new_love_interest')
        elif r < 0.035: events.append('heartbreak')
        elif r < 0.040: events.append('marriage_problems')
        elif r < 0.045: events.append('parent_health_crisis')
        elif r < 0.048: events.append('new_baby')
        elif r < 0.055: events.append('family_celebration')
        
        # === SOCIAL EVENTS ===
        if rng.random() < 0.02: events.append('betrayed_by_friend')
        if rng.random() < 0.005: events.append('public_humiliation')
        if rng.random() < 0.003: events.append('sexual_harassment')
        
        # === ORGANIZATIONAL ===
        if rng.random() < 0.02: events.append('layoff_rumors')
        if rng.random() < 0.01: events.append('management_change')
        if rng.random() < 0.015: events.append('company_in_trouble')
        
        # Personality-driven events (some people attract more drama)
        if traits.get('gossip_tendency', 0) > 0.7 and rng.random() < 0.05:
            events.append('betrayed_by_friend')
        if traits.get('romantic_inclination', 0) > 0.7 and rng.random() < 0.03:
            events.append('workplace_romance_discovered')
        if traits.get('ambition', 0) > 0.8 and rng.random() < 0.04:
            events.append('passed_over_promotion')  # Ambitious people feel this more
        
        return events

    def _determine_mode(self, traits: Dict, emotions: Dict) -> str:
        """Determine behavioral mode from personality + current emotions.
        
        Target distribution for a NORMAL day (no incidents):
          ~60-70% productive/motivated/collaborative/enthusiastic
          ~15-20% mild negatives (disengaged, bored, distracted)
          ~10-15% moderate negatives (anxious, resentful, frustrated)
          ~5% strong negatives (angry, fearful, defiant)
        
        During incidents: shift heavily toward negative modes.
        """
        anger = emotions.get('anger', 0)
        fear = emotions.get('fear', 0)
        sadness = emotions.get('sadness', 0)
        happiness = emotions.get('happiness', 0)
        fatigue = emotions.get('fatigue', 0)
        frustration = emotions.get('frustration', 0)
        resentment = emotions.get('resentment', 0)
        lust = emotions.get('lust', 0)
        grief = emotions.get('grief', 0)
        anxiety = emotions.get('anxiety', 0)
        jealousy = emotions.get('jealousy', 0)
        morale = emotions.get('morale', 0.5)
        boredom = emotions.get('boredom', 0)
        stress = emotions.get('stress', 0)
        loneliness = emotions.get('loneliness', 0)
        
        resilience = traits.get('resilience', 0.5)
        temper = traits.get('temper', 0.5)
        ambition = traits.get('ambition', 0.5)
        conscientiousness = traits.get('conscientiousness', 0.5)
        neuroticism = traits.get('neuroticism', 0.5)
        
        # Only HIGH neuroticism significantly lowers thresholds
        neg_amp = 1.0 + max(0, (neuroticism - 0.6)) * 0.8
        
        # === SEVERE (very rare, needs strong trigger) ===
        if grief > 0.5: return 'grieving'
        if fatigue > 0.7: return 'burnt_out'
        if anger > 0.6 and temper > 0.7: return 'vengeful'
        
        # === STRONG NEGATIVE (uncommon, ~5-10%) ===
        if anger > 0.45 and traits.get('authority_respect', 0.5) < 0.3: return 'defiant'
        if anger > 0.35 and temper > 0.6: return 'angry'
        if fear > 0.45 * (1.0 / neg_amp): return 'fearful'
        if fatigue > 0.5: return 'exhausted'
        
        # === MODERATE NEGATIVE (~10-15%) ===
        if resentment > 0.35: return 'resentful'
        if jealousy > 0.35: return 'jealous'
        if anxiety > 0.4 * (1.0 / neg_amp) and resilience < 0.4: return 'anxious'
        if sadness > 0.4 and resilience < 0.4: return 'depressed'
        
        # === MILD NEGATIVE / NEUTRAL (~15-20%) ===
        if morale < 0.3 and frustration > 0.25: return 'disengaged'
        if stress > 0.35 and emotions.get('alertness', 0.6) < 0.35: return 'distracted'
        if boredom > 0.4 and conscientiousness < 0.35: return 'complacent'
        if emotions.get('guilt', 0) > 0.3: return 'guilt_ridden'
        if loneliness > 0.35: return 'depressed'
        
        # === POSITIVE ELEVATED (~10-15%) ===
        if happiness > 0.65: return 'euphoric'
        if lust > 0.35 and traits.get('romantic_inclination', 0) > 0.6: return 'flirtatious'
        if ambition > 0.8 and morale > 0.5 and frustration > 0.2: return 'power_hungry'
        if emotions.get('nostalgia', 0) > 0.35: return 'nostalgic'
        if happiness > 0.5 and emotions.get('inspiration', 0) > 0.2: return 'inspired'
        
        # === NORMAL POSITIVE (~60-70%) ===
        if morale > 0.55 and happiness > 0.35: return 'motivated'
        if emotions.get('camaraderie', 0) > 0.5 and traits.get('empathy', 0) > 0.5: return 'collaborative'
        if morale > 0.6 and emotions.get('excitement', 0) > 0.15: return 'enthusiastic'
        
        return 'productive'
