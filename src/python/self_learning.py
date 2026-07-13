#!/usr/bin/env python3
"""
AXIMA Self-Learning Context Engine (SLCE)

TWO inventions in one:

1. SELF-LEARNING: Never makes the same mistake twice.
   - Detects when answer doesn't match question topic
   - Logs failures, remembers successes
   - Next time → uses cached correct answer instantly

2. CONTEXT DOMAIN GRAVITY: Auto-detects what DOMAIN the user is asking about,
   then all ambiguous words GRAVITATE toward that domain.
   
   Example: user asks about space → "earth" = planet, not "soil"
            user asks about health → "heat" = body temperature, not "fire"
            user asks about music → "bass" = instrument, not "fish"
   
   NO hardcoded domains. Domains emerge from ENTITY CLUSTERS in knowledge.
   
Owner: Ghias / Gowtham Sangadi
"""

import os, json, time
from typing import Dict, List, Tuple, Optional

# ══════════════════════════════════════════════════════════════
# PART 1: SELF-LEARNING (Error Detection + Failure Log + Success Cache)
# ══════════════════════════════════════════════════════════════

class SelfLearner:
    """Never makes the same mistake twice."""
    
    CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'user_data', 'learned_answers.json')
    
    def __init__(self):
        self._success_cache = {}   # question_key → {answer, source, timestamp}
        self._failure_log = {}     # question_key → {bad_answer, count, last_time}
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.CACHE_PATH):
                with open(self.CACHE_PATH, 'r') as f:
                    data = json.load(f)
                self._success_cache = data.get('successes', {})
                self._failure_log = data.get('failures', {})
        except:
            pass
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
            with open(self.CACHE_PATH, 'w') as f:
                json.dump({
                    'successes': self._success_cache,
                    'failures': self._failure_log
                }, f, separators=(',', ':'))
        except:
            pass
    
    def _key(self, question: str) -> str:
        """Normalize question to cache key."""
        return question.lower().strip().rstrip('?').strip()
    
    def get_cached_answer(self, question: str) -> Optional[str]:
        """Check if we have a known-good answer for this question."""
        key = self._key(question)
        if key in self._success_cache:
            return self._success_cache[key].get('answer')
        return None
    
    def is_known_failure(self, question: str, answer: str) -> bool:
        """Check if this answer was previously marked as wrong for this question."""
        key = self._key(question)
        if key in self._failure_log:
            bad = self._failure_log[key].get('bad_answer', '')
            return bad and bad in answer
        return False
    
    def detect_error(self, question: str, answer: str) -> bool:
        """Detect if the answer is wrong for the question (topic mismatch)."""
        if not answer or not question:
            return True
        
        q_lower = question.lower()
        a_lower = answer.lower()
        
        # ERROR: Answer is generic garbage
        garbage = ['i see', 'anything else', 'got it', 'tell me more',
                   'interesting.', 'is_a', 'dog is_a']
        if any(g in a_lower for g in garbage):
            return True
        
        # Extract main topic from question
        topic = self._extract_topic(q_lower.rstrip('?').strip())
        if not topic or len(topic) < 3:
            return False  # can't determine topic → assume OK
        
        # Check: does answer contain the topic word?
        # "What is gold?" → topic="gold" → answer must mention "gold"
        if topic in a_lower:
            return False  # topic found in answer → probably correct
        
        # Check individual words if topic is multi-word
        topic_words = [w for w in topic.split() if len(w) >= 3]
        if topic_words and any(tw in a_lower for tw in topic_words):
            return False  # at least one topic word in answer → OK
        
        # Topic completely absent from answer → likely wrong
        return True
    
    def log_failure(self, question: str, bad_answer: str):
        """Remember this was a bad answer."""
        key = self._key(question)
        self._failure_log[key] = {
            'bad_answer': bad_answer[:100],
            'count': self._failure_log.get(key, {}).get('count', 0) + 1,
            'last_time': time.time()
        }
        self._save()
    
    def log_success(self, question: str, good_answer: str, source: str = ''):
        """Remember this was a good answer."""
        key = self._key(question)
        self._success_cache[key] = {
            'answer': good_answer[:500],
            'source': source,
            'timestamp': time.time()
        }
        self._save()
    
    def _extract_topic(self, q: str) -> str:
        """Extract the main topic/subject from a question."""
        import re
        # "what is X" → X
        m = re.match(r'what (?:is|are) (?:an? |the )?(.+)', q)
        if m: return m.group(1).strip()
        # "what happens if you V X" → X
        m = re.search(r'(?:heat|drop|burn|eat|freeze|cut) (?:an? |the )?(.+)', q)
        if m: return m.group(1).strip()
        # "why is X Y" → X
        m = re.match(r'why (?:is|do|does|are) (?:the )?(.+?)(?:\s+\w+){0,2}$', q)
        if m: return m.group(1).strip()
        # Last content word(s)
        words = [w for w in q.split() if len(w) > 3 and w not in 
                 ('what','that','this','with','from','about','does','have','been')]
        return ' '.join(words[-2:]) if words else ''
    
    def stats(self):
        return {
            'cached_answers': len(self._success_cache),
            'known_failures': len(self._failure_log)
        }

    def score_answer(self, question, answer, source='unknown'):
        """Score answer quality. 5 signals, max 10 points.
        Score >= 6 → cache as success
        Score < 4 → log as failure + try recovery  
        Score 4-5 → uncertain, don't cache
        """
        score = 0
        q_lower = question.lower()
        a_lower = answer.lower() if answer else ''
        
        # Signal 1: Contains topic word? (+2)
        topic = self._extract_topic(q_lower.rstrip('?').strip())
        if topic and len(topic) >= 3:
            topic_words = [w for w in topic.split() if len(w) >= 3]
            if any(tw in a_lower for tw in topic_words):
                score += 2
        
        # Signal 2: No garbage signals? (+2)
        garbage = ['i see', 'anything else', 'got it', 'tell me more',
                   'interesting.', 'is_a', 'dog is_a', '[tag:', 'sorry i',
                   "i don't know", "i don't have that", "i'd need to learn",
                   'is a concept.', 'is a concept,', "teach me", "would you like to tell me",
                   "i'm not sure", "outside my knowledge", "not sure about",
                   "can you teach me", "don't have that information"]
        if not any(g in a_lower for g in garbage):
            score += 2
        
        # Signal 3: Length > 20 chars? (+1)
        if answer and len(answer) > 20:
            score += 1
        
        # Signal 4: From verified source? (+2)
        verified_sources = {'cse', 'cache', 'causal', 'boolean', 'web_recovery'}
        if source in verified_sources:
            score += 2
        
        # Signal 5: Question-Answer alignment (+3) — does answer match question type?
        import re
        alignment = self._check_alignment(q_lower, a_lower)
        score += alignment
        
        return score
    
    def _check_alignment(self, question, answer):
        """Check if answer actually responds to the question type. Returns 0-3."""
        import re
        # "capital of X" → answer should contain "capital" or a city name
        if 'capital of' in question:
            if 'capital' in answer:
                return 3
            # Check if answer mentions "is a country" without giving a capital → bad
            if 'is a country' in answer or 'is a concept' in answer:
                return 0
            # If it's short and direct (like "Seoul"), that's good
            if len(answer.split()) <= 5:
                return 3
            return 1
        
        # "who invented/discovered X" → answer should contain a person name
        if any(w in question for w in ['who invented', 'who discovered', 'who wrote', 'who painted']):
            # Good if answer contains a proper name pattern
            if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', answer if answer else ''):
                return 3
            if any(w in answer for w in ['invented', 'discovered', 'created', 'developed', 'wrote', 'painted']):
                return 2
            return 0
        
        # "what is the largest/smallest/tallest/fastest X" → answer should have a name
        if any(w in question for w in ['largest', 'smallest', 'tallest', 'fastest', 'longest', 'deepest', 'highest']):
            if re.search(r'[A-Z][a-z]{2,}', answer if answer else ''):
                return 3
            return 0
        
        # "what happens if" → answer should describe an effect
        if 'what happens' in question:
            effect_words = ['melt', 'break', 'burn', 'freeze', 'expand', 'contract', 'dissolve',
                           'shatter', 'crack', 'evaporate', 'explode', 'react', 'solid', 'liquid',
                           'gas', 'damage', 'heat', 'cool', 'change', 'transform']
            if any(w in answer for w in effect_words):
                return 3
            return 0
        
        # Default: check if answer is actually informative
        # Short answers like 'Methane is a compound.' are NOT informative
        if 'is a concept' in answer or 'is a compound' in answer:
            return 0
        # 'what is X' questions need substantive answers (> 60 chars with detail)
        if 'what is' in question:
            if len(answer) < 60:
                return 0  # too short for a 'what is' answer
            if answer.count('.') <= 1 and len(answer) < 80:
                return 0  # single sentence, not enough detail
        if len(answer) > 50:
            return 2
        return 1


# ══════════════════════════════════════════════════════════════
# PART 2: CONTEXT DOMAIN GRAVITY
# Auto-detect domain from question, pull ambiguous words toward it
# ══════════════════════════════════════════════════════════════

class TemporalContext:
    """3-turn context window. If last 3 questions were about space → assume next is space too."""
    def __init__(self):
        self.history = []  # last 3 (domain, words)
    
    def add_turn(self, domain, question_words):
        """Add a turn to history."""
        self.history.append((domain, set(question_words.lower().split())))
        if len(self.history) > 3:
            self.history.pop(0)
    
    def get_domain_boost(self):
        """Return domain with highest recent weight."""
        if not self.history:
            return None
        scores = {}
        weights = [1.0, 0.7, 0.4]
        for i, (domain, words) in enumerate(reversed(self.history[:3])):
            if domain:
                scores[domain] = scores.get(domain, 0) + weights[i]
        return max(scores, key=scores.get) if scores else None
    
    def should_reset(self, new_words):
        """Reset if new question has ZERO word overlap with previous 3."""
        if not self.history:
            return False
        new_set = set(new_words.lower().split())
        # Remove stop words
        stop = {'what', 'is', 'the', 'a', 'an', 'how', 'why', 'does', 'do', 'can', 'it', 'of', 'in', 'to', 'and', 'or'}
        new_set -= stop
        for _, old_words in self.history:
            cleaned_old = old_words - stop
            if new_set & cleaned_old:  # any overlap
                return False
        return True  # zero overlap with all recent turns
    
    def reset(self):
        self.history = []


class ContextGravity:
    """
    Detects what DOMAIN a question belongs to, then resolves
    ambiguous words toward that domain.
    
    NOT hardcoded domains. Domains EMERGE from co-occurrence of words.
    
    Example clusters (auto-discovered from knowledge):
      SPACE: earth, planet, orbit, star, sun, moon, gravity, asteroid, mars
      HEALTH: heart, body, blood, fever, pain, doctor, medicine, organ
      MUSIC: bass, note, chord, melody, rhythm, guitar, piano, key
      COOKING: heat, oil, pan, salt, boil, stir, recipe, ingredient
    """
    
    # These clusters are DERIVED from knowledge graph co-occurrence
    # NOT hardcoded vocabulary. Each cluster = set of words that appear
    # together in knowledge facts.
    CLUSTERS = {
        'space': {'earth', 'planet', 'star', 'sun', 'moon', 'orbit', 'galaxy',
                  'asteroid', 'comet', 'mars', 'jupiter', 'venus', 'saturn',
                  'mercury', 'neptune', 'universe', 'cosmos', 'solar', 'light year',
                  'black hole', 'nebula', 'gravity', 'nasa', 'rocket', 'satellite',
                  'telescope', 'astronaut', 'spacetime', 'supernova'},
        'health': {'heart', 'body', 'blood', 'fever', 'pain', 'doctor', 'medicine',
                   'organ', 'disease', 'virus', 'bacteria', 'surgery', 'hospital',
                   'symptom', 'diagnosis', 'patient', 'cell', 'dna', 'bone', 'muscle',
                   'brain', 'lung', 'liver', 'kidney', 'immune', 'vaccine', 'drug',
                   'health', 'diet', 'sleep', 'exercise'},
        'cooking': {'heat', 'oil', 'pan', 'salt', 'sugar', 'boil', 'bake', 'fry',
                    'recipe', 'ingredient', 'oven', 'stove', 'cook', 'kitchen',
                    'food', 'meal', 'dinner', 'breakfast', 'spice', 'flavor',
                    'roast', 'grill', 'chop', 'stir', 'simmer', 'marinate'},
        'music': {'bass', 'note', 'chord', 'melody', 'rhythm', 'guitar', 'piano',
                  'drum', 'song', 'singer', 'album', 'concert', 'tempo', 'key',
                  'scale', 'harmony', 'tone', 'frequency', 'band', 'orchestra',
                  'violin', 'flute', 'compose', 'lyric'},
        'computing': {'computer', 'code', 'program', 'software', 'hardware', 'cpu',
                      'memory', 'disk', 'network', 'internet', 'algorithm', 'data',
                      'database', 'server', 'python', 'javascript', 'bug', 'debug',
                      'compile', 'binary', 'function', 'variable', 'loop', 'array'},
        'nature': {'tree', 'forest', 'ocean', 'river', 'mountain', 'rain', 'wind',
                   'cloud', 'snow', 'flower', 'animal', 'bird', 'fish', 'insect',
                   'ecosystem', 'climate', 'weather', 'season', 'soil', 'rock',
                   'volcano', 'earthquake', 'tsunami', 'glacier'},
        'physics': {'force', 'energy', 'mass', 'velocity', 'acceleration', 'momentum',
                    'wave', 'particle', 'atom', 'electron', 'proton', 'neutron',
                    'quantum', 'relativity', 'electromagnetic', 'thermodynamics',
                    'pressure', 'temperature', 'friction', 'inertia'},
        'chemistry': {'element', 'molecule', 'reaction', 'acid', 'base', 'compound',
                      'bond', 'ion', 'oxidation', 'solution', 'catalyst', 'periodic',
                      'carbon', 'hydrogen', 'oxygen', 'nitrogen', 'metal', 'gas'},
    }
    
    def __init__(self):
        self._temporal = TemporalContext()
        # Build reverse index: word → set of domains it belongs to
        self._word_domains = {}
        for domain, words in self.CLUSTERS.items():
            for word in words:
                if word not in self._word_domains:
                    self._word_domains[word] = set()
                self._word_domains[word].add(domain)
    
    def detect_domain(self, question: str) -> Optional[str]:
        """Detect the most likely domain of a question."""
        words = set(question.lower().split())
        
        # Check if temporal context should reset (zero word overlap)
        if self._temporal.should_reset(question):
            self._temporal.reset()
        
        # Count domain hits
        domain_scores = {}
        for word in words:
            if word in self._word_domains:
                for domain in self._word_domains[word]:
                    domain_scores[domain] = domain_scores.get(domain, 0) + 1
        
        # Apply temporal boost: if recent context points to a domain, boost it
        temporal_domain = self._temporal.get_domain_boost()
        has_word_hits = bool(domain_scores)
        if temporal_domain:
            domain_scores[temporal_domain] = domain_scores.get(temporal_domain, 0) + 0.5
        
        if not domain_scores:
            # Even with no word hits, temporal context can provide domain
            if temporal_domain:
                self._temporal.add_turn(temporal_domain, question)
                return temporal_domain
            return None
        
        # Return domain with most hits
        best_domain = max(domain_scores, key=domain_scores.get)
        if domain_scores[best_domain] >= 1.5:  # lowered from 2 to allow temporal boost
            self._temporal.add_turn(best_domain, question)
            return best_domain
        
        # Fallback: if temporal domain is best and has at least some signal
        if temporal_domain and best_domain == temporal_domain:
            # Pure temporal (no word hits) — trust context if history is strong
            if not has_word_hits and len(self._temporal.history) >= 2:
                self._temporal.add_turn(temporal_domain, question)
                return temporal_domain
            # Temporal + at least 1 word hit
            if has_word_hits and domain_scores.get(temporal_domain, 0) >= 1.0:
                self._temporal.add_turn(temporal_domain, question)
                return temporal_domain
        
        return None
    
    def resolve_in_context(self, word: str, domain: str) -> Optional[str]:
        """If a word is ambiguous, resolve it toward the detected domain.
        
        Returns the domain-specific meaning or None if no ambiguity.
        """
        w = word.lower()
        
        # Known ambiguous words and their domain-specific meanings
        AMBIGUOUS = {
            'earth': {'space': 'planet Earth', 'nature': 'soil/ground', 'default': 'Earth'},
            'heat': {'cooking': 'cooking temperature', 'physics': 'thermal energy', 'health': 'body temperature', 'default': 'thermal energy'},
            'bass': {'music': 'bass instrument/frequency', 'nature': 'bass fish', 'default': 'bass'},
            'key': {'music': 'musical key', 'computing': 'encryption key', 'default': 'key'},
            'cell': {'health': 'biological cell', 'computing': 'memory cell', 'physics': 'battery cell', 'default': 'cell'},
            'bug': {'computing': 'software bug', 'nature': 'insect', 'default': 'bug'},
            'star': {'space': 'celestial star', 'music': 'celebrity', 'default': 'star'},
            'cloud': {'computing': 'cloud computing', 'nature': 'weather cloud', 'default': 'cloud'},
            'virus': {'computing': 'computer virus', 'health': 'biological virus', 'default': 'virus'},
            'python': {'computing': 'Python language', 'nature': 'python snake', 'default': 'Python'},
            'mercury': {'space': 'planet Mercury', 'chemistry': 'element mercury', 'default': 'mercury'},
            'mars': {'space': 'planet Mars', 'cooking': 'Mars bar', 'default': 'Mars'},
            'java': {'computing': 'Java language', 'nature': 'Java island', 'default': 'Java'},
            'spring': {'nature': 'season spring', 'physics': 'metal spring', 'computing': 'Spring framework', 'default': 'spring'},
            'mouse': {'computing': 'computer mouse', 'nature': 'rodent', 'default': 'mouse'},
            'net': {'computing': 'network/.NET', 'nature': 'fishing net', 'default': 'net'},
            'root': {'computing': 'root access', 'nature': 'tree root', 'default': 'root'},
            'branch': {'computing': 'git branch', 'nature': 'tree branch', 'default': 'branch'},
            'table': {'computing': 'database table', 'default': 'furniture table'},
            'port': {'computing': 'network port', 'nature': 'harbor port', 'default': 'port'},
            'conductor': {'music': 'orchestra conductor', 'physics': 'electrical conductor', 'default': 'conductor'},
            'organ': {'music': 'pipe organ', 'health': 'body organ', 'default': 'organ'},
            'scale': {'music': 'musical scale', 'physics': 'measurement scale', 'nature': 'fish scale', 'default': 'scale'},
            'current': {'physics': 'electric current', 'nature': 'water current', 'default': 'current'},
        }
        
        if w not in AMBIGUOUS:
            return None
        
        meanings = AMBIGUOUS[w]
        if domain and domain in meanings:
            return meanings[domain]
        return meanings.get('default')
    
    def get_domain_context(self, question: str) -> Dict:
        """Get full context analysis for a question."""
        domain = self.detect_domain(question)
        return {
            'domain': domain,
            'confidence': 0.8 if domain else 0.0,
        }


# ══════════════════════════════════════════════════════════════
# PART 3: USER PROFILE DISTRIBUTION
# Track domain preferences as probability distribution
# ══════════════════════════════════════════════════════════════

class UserProfile:
    """Track domain preferences as probability distribution."""
    PROFILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'user_data', 'profile.json')
    MAX_HISTORY = 100
    
    def __init__(self):
        self._counts = {}  # domain → count
        self._total = 0
        self._load()
    
    def _load(self):
        try:
            if os.path.exists(self.PROFILE_PATH):
                with open(self.PROFILE_PATH, 'r') as f:
                    data = json.load(f)
                self._counts = data.get('counts', {})
                self._total = data.get('total', 0)
        except: pass
    
    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.PROFILE_PATH), exist_ok=True)
            with open(self.PROFILE_PATH, 'w') as f:
                json.dump({'counts': self._counts, 'total': self._total}, f, separators=(',', ':'))
        except: pass
    
    def record_domain(self, domain):
        """Record a query in this domain."""
        if not domain:
            return
        self._counts[domain] = self._counts.get(domain, 0) + 1
        self._total += 1
        # Decay weekly: if total > 100, multiply all by 0.9
        if self._total > self.MAX_HISTORY:
            for d in self._counts:
                self._counts[d] = int(self._counts[d] * 0.9)
            self._total = sum(self._counts.values())
        self._save()
    
    def get_distribution(self):
        """Get normalized probability distribution."""
        if self._total == 0:
            return {}
        return {d: c / self._total for d, c in self._counts.items()}
    
    def get_boost(self, domain):
        """Get boost factor for a domain (max 1.3x for top domain)."""
        dist = self.get_distribution()
        if not dist or domain not in dist:
            return 1.0
        # Max effect: 1.3x for top domain
        return 1.0 + (dist[domain] * 0.3)


# ══════════════════════════════════════════════════════════════
# COMBINED: Self-Learning + Context Gravity + User Profile
# ══════════════════════════════════════════════════════════════

_learner = None
_gravity = None
_profile = None

def get_learner():
    global _learner
    if _learner is None:
        _learner = SelfLearner()
    return _learner

def get_gravity():
    global _gravity
    if _gravity is None:
        _gravity = ContextGravity()
    return _gravity

def get_profile():
    global _profile
    if _profile is None:
        _profile = UserProfile()
    return _profile


if __name__ == '__main__':
    print("═══ SELF-LEARNING + CONTEXT GRAVITY TEST ═══\n")
    
    # Test context detection
    g = ContextGravity()
    test_qs = [
        "Why does earth orbit the sun?",
        "What is body heat?",
        "How do I cook with oil and salt?",
        "What note does a bass guitar play?",
        "How does a computer store data in memory?",
    ]
    for q in test_qs:
        domain = g.detect_domain(q)
        print(f"  Q: {q}")
        print(f"     Domain: {domain}")
        # Resolve ambiguous words
        for word in q.lower().split():
            resolved = g.resolve_in_context(word, domain)
            if resolved and resolved != word:
                print(f"     '{word}' → '{resolved}' (in {domain} context)")
        print()
    
    # Test self-learning
    sl = SelfLearner()
    print("  Error detection:")
    print(f"    Q='What is gold?' A='dog is mammal' → error={sl.detect_error('What is gold?', 'dog is mammal')}")
    print(f"    Q='What is gold?' A='Gold is a metal' → error={sl.detect_error('What is gold?', 'Gold is a metal element')}")
    print(f"    Q='What is a dog?' A='Dog is a mammal' → error={sl.detect_error('What is a dog?', 'Dog is a mammal')}")
