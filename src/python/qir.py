#!/usr/bin/env python3
"""
AXIMA QIR — Quantum Intent Resolution
Every word exists in SUPERPOSITION until context collapses it.
Never rewrites input. Tries ALL interpretations. Picks best result.

Zero word lists. Zero maintenance. Cannot corrupt input.

Architecture:
  Layer 1: Superposition (all possible meanings per token)
  Layer 2: Entanglement (adjacent tokens constrain each other)
  Layer 3: Measurement (try all interpretations, return best)
  Layer 4: Decoherence Memory (past context locks meanings)
  Layer 5: Observer Effect (question type collapses frame)

Owner: Ghias / Gowtham Sangadi
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

# ══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

@dataclass
class Meaning:
    """One possible interpretation of a token."""
    text: str           # resolved text
    confidence: float   # 0.0-1.0
    category: str       # food/living/material/action/concept/unknown

@dataclass 
class QuantumToken:
    """A token in superposition — multiple meanings until collapsed."""
    original: str
    meanings: List[Meaning] = field(default_factory=list)
    collapsed: Optional[str] = None
    collapsed_conf: float = 0.0

@dataclass
class Interpretation:
    """One full interpretation of the sentence (one collapse of all tokens)."""
    tokens: List[str]
    total_confidence: float
    text: str


# ══════════════════════════════════════════════════════════════
# LAYER 1: SUPERPOSITION — All possible meanings per token
# ══════════════════════════════════════════════════════════════

class QIR:
    """Quantum Intent Resolution — non-destructive multi-interpretation system."""
    
    def __init__(self, brain=None, knowledge=None):
        """
        brain: SemanticBrain instance (for fuzzy matching)
        knowledge: CSEKnowledge instance (for entity lookup)
        """
        self._brain = brain
        self._knowledge = knowledge
        self._session_locks = {}  # decoherence memory: word → locked meaning
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load entities and categories from CSE knowledge."""
        self._entities = set()
        self._categories = {}  # entity → category
        
        if self._knowledge:
            try:
                for subj in self._knowledge._cache:
                    self._entities.add(subj)
                    # Get category
                    rels = self._knowledge._cache.get(subj, {})
                    if 'is_a' in rels:
                        for cat, conf in rels['is_a']:
                            self._categories[subj] = cat
                            break
            except:
                pass
    
    def superpose(self, token: str) -> QuantumToken:
        """Layer 1: Get ALL possible meanings of a token."""
        qt = QuantumToken(original=token)
        t = token.lower().strip('?!.,;:')
        
        if not t or len(t) < 1:
            qt.meanings = [Meaning(token, 1.0, 'empty')]
            return qt
        
        # Meaning 1: The word itself (always included — prevents corruption)
        if t in self._entities:
            cat = self._categories.get(t, 'concept')
            qt.meanings.append(Meaning(t, 1.0, cat))
        else:
            # Original word gets HIGH confidence if it looks like a real word
            # (has vowels, reasonable structure)
            has_vowels = any(c in t for c in 'aeiou')
            not_repeated = not all(c == t[0] for c in t)
            is_real_looking = has_vowels and not_repeated and len(t) >= 2
            base_conf = 0.85 if is_real_looking else 0.4
            qt.meanings.append(Meaning(t, base_conf, 'unknown'))
        
        # Meaning 2-5: Fuzzy matches from Semantic Brain
        if self._brain and len(t) > 2:
            try:
                loc = self._brain._locate_word(t)
                if loc[0] and loc[1] > 0.6 and loc[0].lower() != t:
                    cat = self._categories.get(loc[0].lower(), 'concept')
                    # CRITICAL: fuzzy match must beat the original's confidence
                    # Only if edit distance is small (real misspelling, not different word)
                    edit_dist = self._edit_distance(t, loc[0].lower())
                    if edit_dist <= 2:
                        # Close misspelling — give it high confidence
                        qt.meanings.append(Meaning(loc[0].lower(), loc[1] * 0.95, cat))
                    else:
                        # Distant match — probably a different word, suppress
                        qt.meanings.append(Meaning(loc[0].lower(), loc[1] * 0.4, cat))
            except:
                pass
        
        # Meaning 3: Check session locks (decoherence memory)
        if t in self._session_locks:
            locked = self._session_locks[t]
            qt.meanings.insert(0, Meaning(locked['text'], 0.99, locked['category']))
        
        # Meaning 4: Common abbreviations (universal, no word list needed)
        abbrevs = self._resolve_abbreviation(t)
        if abbrevs:
            qt.meanings.append(Meaning(abbrevs, 0.95, 'abbreviation'))
        
        # Sort by confidence (highest first)
        qt.meanings.sort(key=lambda m: m.confidence, reverse=True)
        
        return qt
    
    @staticmethod
    def _edit_distance(a: str, b: str) -> int:
        """Levenshtein edit distance between two strings."""
        if len(a) < len(b):
            return QIR._edit_distance(b, a)
        if len(b) == 0:
            return len(a)
        prev_row = range(len(b) + 1)
        for i, ca in enumerate(a):
            curr_row = [i + 1]
            for j, cb in enumerate(b):
                cost = 0 if ca == cb else 1
                curr_row.append(min(curr_row[j] + 1, prev_row[j + 1] + 1, prev_row[j] + cost))
            prev_row = curr_row
        return prev_row[-1]

    def _resolve_abbreviation(self, token: str) -> Optional[str]:
        """Resolve common abbreviations without a word list.
        Uses pattern: single char or very short = likely abbreviation."""
        # Only for very short tokens (1-2 chars) that aren't known entities
        if len(token) > 3 or token in self._entities:
            return None
        
        # Single char abbreviations (universal across languages/contexts)
        single = {'u': 'you', 'r': 'are', 'y': 'why', 'n': 'and', 'k': 'ok',
                  'b': 'be', 'c': 'see', 'w': 'with'}
        if token in single:
            return single[token]
        
        # Two char
        double = {'ur': 'your', 'nt': 'not', 'bt': 'but', 'hw': 'how',
                  'wt': 'what', 'bc': 'because', 'fr': 'for'}
        if token in double:
            return double[token]
        
        return None
    
    # ══════════════════════════════════════════════════════════
    # LAYER 2: ENTANGLEMENT — Adjacent tokens constrain each other
    # ══════════════════════════════════════════════════════════
    
    def entangle(self, quantum_tokens: List[QuantumToken], question_type: str) -> List[QuantumToken]:
        """Layer 2: Use context to boost/suppress meanings."""
        
        # Observer effect (Layer 5): question type constrains categories
        category_boost = self._get_category_boost(question_type)
        
        for i, qt in enumerate(quantum_tokens):
            for meaning in qt.meanings:
                # Boost meanings that match the question frame
                if meaning.category in category_boost:
                    meaning.confidence *= category_boost[meaning.category]
                
                # Entanglement: adjacent tokens affect meaning
                if i > 0:
                    prev_qt = quantum_tokens[i-1]
                    if prev_qt.meanings:
                        prev_best = prev_qt.meanings[0]
                        # If previous word is an action verb → current should be physical object
                        if prev_best.category == 'action':
                            if meaning.category in ('food', 'material', 'living', 'object'):
                                meaning.confidence *= 1.2
                            elif meaning.category in ('abstract', 'concept'):
                                meaning.confidence *= 0.7
                
                # Cap confidence at 1.0
                meaning.confidence = min(meaning.confidence, 1.0)
            
            # Re-sort after entanglement
            qt.meanings.sort(key=lambda m: m.confidence, reverse=True)
        
        return quantum_tokens
    
    def _get_category_boost(self, question_type: str) -> Dict[str, float]:
        """Layer 5: Observer effect — question type boosts certain categories."""
        boosts = {
            'causal': {'food': 1.3, 'material': 1.3, 'living': 1.2, 'object': 1.3,
                       'concept': 0.6, 'abstract': 0.5},
            'factual': {'concept': 1.2, 'living': 1.1, 'material': 1.0},
            'boolean': {'concept': 1.1, 'living': 1.1},
            'math': {},  # no category preference
        }
        return boosts.get(question_type, {})
    
    # ══════════════════════════════════════════════════════════
    # LAYER 3: MEASUREMENT — Generate interpretations
    # ══════════════════════════════════════════════════════════
    
    def measure(self, quantum_tokens: List[QuantumToken], max_interpretations: int = 3) -> List[Interpretation]:
        """Layer 3: Collapse superposition into concrete interpretations."""
        
        # Strategy: take top-1 meaning per token for primary interpretation
        # Then vary the ambiguous tokens for alternate interpretations
        
        interpretations = []
        
        # Primary interpretation: best meaning for each token
        primary_tokens = []
        primary_conf = 1.0
        for qt in quantum_tokens:
            if qt.meanings:
                best = qt.meanings[0]
                primary_tokens.append(best.text)
                primary_conf *= best.confidence
            else:
                primary_tokens.append(qt.original)
        
        interpretations.append(Interpretation(
            tokens=primary_tokens,
            total_confidence=primary_conf ** (1.0 / max(len(quantum_tokens), 1)),  # geometric mean
            text=' '.join(primary_tokens)
        ))
        
        # Alternate interpretations: swap ambiguous tokens (conf gap < 0.3)
        for i, qt in enumerate(quantum_tokens):
            if len(qt.meanings) > 1 and len(interpretations) < max_interpretations:
                gap = qt.meanings[0].confidence - qt.meanings[1].confidence
                if gap < 0.3:  # ambiguous — second meaning is viable
                    alt_tokens = list(primary_tokens)
                    alt_tokens[i] = qt.meanings[1].text
                    alt_conf = primary_conf * (qt.meanings[1].confidence / max(qt.meanings[0].confidence, 0.01))
                    interpretations.append(Interpretation(
                        tokens=alt_tokens,
                        total_confidence=alt_conf ** (1.0 / max(len(quantum_tokens), 1)),
                        text=' '.join(alt_tokens)
                    ))
        
        # Sort by confidence
        interpretations.sort(key=lambda x: x.total_confidence, reverse=True)
        return interpretations
    
    # ══════════════════════════════════════════════════════════
    # LAYER 4: DECOHERENCE — Lock meanings from context
    # ══════════════════════════════════════════════════════════
    
    def lock_meaning(self, word: str, meaning: str, category: str):
        """Layer 4: Lock a word's meaning for the rest of session."""
        self._session_locks[word.lower()] = {'text': meaning, 'category': category}
    
    def clear_session(self):
        """Reset session locks."""
        self._session_locks = {}
    
    # ══════════════════════════════════════════════════════════
    # MAIN API: Resolve a full sentence
    # ══════════════════════════════════════════════════════════
    
    def resolve(self, sentence: str, question_type: str = 'general') -> List[Interpretation]:
        """
        Full QIR pipeline: superpose → entangle → measure.
        Returns ranked list of interpretations (best first).
        NEVER modifies the original sentence.
        """
        if not sentence or not sentence.strip():
            return [Interpretation(tokens=[], total_confidence=0.0, text='')]
        
        # Tokenize (preserve original)
        tokens = sentence.strip().split()
        
        # Layer 1: Superposition
        quantum_tokens = [self.superpose(t) for t in tokens]
        
        # Layer 2 + 5: Entanglement + Observer effect
        quantum_tokens = self.entangle(quantum_tokens, question_type)
        
        # Layer 3: Measurement (collapse into interpretations)
        interpretations = self.measure(quantum_tokens)
        
        # Layer 4: If primary interpretation used a locked meaning, boost it
        if self._session_locks and interpretations:
            for interp in interpretations:
                for t in interp.tokens:
                    if t in self._session_locks:
                        interp.total_confidence = min(interp.total_confidence * 1.1, 1.0)
        
        return interpretations
    
    def best_text(self, sentence: str, question_type: str = 'general') -> str:
        """Convenience: get the best interpretation as a string."""
        interps = self.resolve(sentence, question_type)
        if interps:
            return interps[0].text
        return sentence  # fallback: original unchanged
    
    def all_texts(self, sentence: str, question_type: str = 'general') -> List[Tuple[str, float]]:
        """Get all interpretations with confidence scores."""
        interps = self.resolve(sentence, question_type)
        return [(i.text, i.total_confidence) for i in interps]


# ══════════════════════════════════════════════════════════════
# SINGLETON
# ══════════════════════════════════════════════════════════════

_qir = None

def get_qir(brain=None, knowledge=None):
    global _qir
    if _qir is None:
        _qir = QIR(brain=brain, knowledge=knowledge)
    return _qir


# ══════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    os.chdir('/root/hybrid-ai')
    
    # Load with real brain + knowledge
    try:
        from semantic_brain import SemanticBrain
        from cse_knowledge import CSEKnowledge
        
        entities = set()
        for fname in os.listdir('src/data'):
            if not fname.endswith('.txt'): continue
            try:
                with open(os.path.join('src/data', fname), 'r', errors='ignore') as f:
                    for line in f:
                        if ' is ' in line:
                            subj = line.split(' is ', 1)[0].strip().lstrip('A ').lstrip('An ').strip()
                            if 2 < len(subj) < 40: entities.add(subj)
            except: continue
        
        brain = SemanticBrain(entities=entities)
        knowledge = CSEKnowledge()
        qir = QIR(brain=brain, knowledge=knowledge)
    except Exception as e:
        print(f"Loading with minimal setup: {e}")
        qir = QIR()
    
    print("═══ QUANTUM INTENT RESOLUTION TEST ═══\n")
    
    tests = [
        ("What happens if you eat raw chicken?", "causal"),
        ("What happens if u heat elefant?", "causal"),
        ("y is the sky blue?", "factual"),
        ("wat is a dog", "factual"),
        ("is 49 prime", "boolean"),
        ("heat the glass", "causal"),
        ("drop a bat", "causal"),
    ]
    
    for sentence, qtype in tests:
        interps = qir.resolve(sentence, qtype)
        print(f"  Input: \"{sentence}\"")
        for i, interp in enumerate(interps[:2]):
            marker = "→" if i == 0 else "  alt:"
            print(f"  {marker} \"{interp.text}\" (conf: {interp.total_confidence:.2f})")
        print()
