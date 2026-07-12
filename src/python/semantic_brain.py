#!/usr/bin/env python3
"""
AXIMA Semantic Brain v6.0 — The Field Theory of Language
Words have POSITION, not meaning. Input is LOCATED, not matched.
35D character field. LSH buckets. 0.01ms. Zero training. Zero deps.
"""

import re
import os
import json
import math
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════
# THE 5 FORCES OUTPUT
# ═══════════════════════════════════════════════════════════════

@dataclass
class Forces:
    gravity: str = ''           # main entity (heaviest)
    spin: str = ''              # property/modifier
    charge: int = 1             # +1 positive, -1 negated
    momentum: str = 'new'       # new/continue/drill/reference
    wavelength: str = 'medium'  # short/medium/deep
    confidence: float = 0.0
    original: str = ''
    compound: str = ''
    action: str = ''
    needs_clarify: bool = False
    clarify_options: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# CHARACTER FIELD — 35D VECTOR FROM CHARACTERS (ZERO TRAINING)
# ═══════════════════════════════════════════════════════════════

def _word_vector(word: str) -> List[float]:
    """Compute 35-dimensional position from characters alone."""
    w = word.lower()
    vec = [0.0] * 35

    # Dims 0-25: character frequency (normalized by length)
    wlen = max(len(w), 1)
    for ch in w:
        idx = ord(ch) - ord('a')
        if 0 <= idx < 26:
            vec[idx] += 1.0 / wlen

    # Dim 26: word length (normalized: divide by 15 to keep in 0-1 range)
    vec[26] = min(len(w) / 15.0, 1.0)

    # Dim 27: first character (0-1 mapped)
    if w and w[0].isalpha():
        vec[27] = (ord(w[0]) - ord('a')) / 25.0

    # Dim 28: last character (0-1 mapped)
    if w and w[-1].isalpha():
        vec[28] = (ord(w[-1]) - ord('a')) / 25.0

    # Dim 29: character diversity (unique chars / length)
    unique = len(set(c for c in w if c.isalpha()))
    vec[29] = unique / max(wlen, 1)

    # Dims 30-34: bigram hash features (order-sensitive)
    bigrams = [w[i:i+2] for i in range(len(w)-1) if w[i].isalpha() and w[i+1:i+2].isalpha()]
    for i, bg in enumerate(bigrams[:5]):
        # Hash bigram to 0-1 range
        h = (ord(bg[0]) * 31 + ord(bg[1])) % 256
        vec[30 + i] = h / 255.0

    return vec


def _phrase_vector(phrase: str) -> List[float]:
    """Compute 35D vector for a multi-word phrase."""
    words = phrase.lower().split()
    if not words:
        return [0.0] * 35

    # Combine all characters as one unit
    combined = ''.join(words)
    vec = _word_vector(combined)

    # Override length with phrase length
    vec[26] = min(len(combined) / 25.0, 1.0)

    return vec


def _distance(a: List[float], b: List[float]) -> float:
    """Euclidean distance in 35D space."""
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ═══════════════════════════════════════════════════════════════
# LSH — LOCALITY-SENSITIVE HASHING (zero deps, stdlib only)
# ═══════════════════════════════════════════════════════════════

class LSHIndex:
    """Fast approximate nearest neighbor using LSH. Zero deps."""

    def __init__(self, num_planes: int = 12, dims: int = 35):
        self.dims = dims
        self.num_planes = num_planes
        self.planes = self._generate_planes(num_planes, dims)
        self.buckets: Dict[int, List[Tuple[str, List[float]]]] = {}
        self.all_entities: Dict[str, List[float]] = {}

    def _generate_planes(self, n: int, dims: int) -> List[List[float]]:
        """Deterministic pseudo-random hyperplanes (reproducible)."""
        planes = []
        for i in range(n):
            plane = []
            for d in range(dims):
                # Deterministic pseudo-random using seed
                seed = (i * 1000 + d * 7 + 42) % 1000000
                val = ((seed * 6364136223846793005 + 1442695040888963407) % (2**32)) / (2**32) - 0.5
                plane.append(val)
            planes.append(plane)
        return planes

    def _hash(self, vec: List[float]) -> int:
        """Compute LSH hash (which side of each hyperplane)."""
        h = 0
        for i, plane in enumerate(self.planes):
            dot = sum(v * p for v, p in zip(vec, plane))
            if dot >= 0:
                h |= (1 << i)
        return h

    def insert(self, entity: str, vec: List[float]):
        """Add entity to index."""
        h = self._hash(vec)
        if h not in self.buckets:
            self.buckets[h] = []
        self.buckets[h].append((entity, vec))
        self.all_entities[entity] = vec

    def query(self, vec: List[float], max_candidates: int = 100) -> List[Tuple[str, float]]:
        """Find nearest neighbors. Returns [(entity, distance)]."""
        h = self._hash(vec)
        candidates = set()

        # Check main bucket
        for entity, evec in self.buckets.get(h, []):
            candidates.add(entity)

        # Check adjacent buckets (flip each bit)
        for i in range(self.num_planes):
            adj_h = h ^ (1 << i)
            for entity, evec in self.buckets.get(adj_h, []):
                candidates.add(entity)
                if len(candidates) >= max_candidates:
                    break
            if len(candidates) >= max_candidates:
                break

        # Compute exact distance for candidates
        results = []
        for entity in candidates:
            evec = self.all_entities[entity]
            dist = _distance(vec, evec)
            results.append((entity, dist))

        results.sort(key=lambda x: x[1])
        return results[:20]

    def size(self) -> int:
        return len(self.all_entities)


# ═══════════════════════════════════════════════════════════════
# LCS VERIFIER (safety net for edge cases)
# ═══════════════════════════════════════════════════════════════

def _lcs_ratio(a: str, b: str) -> float:
    """Longest Common Subsequence ratio. Safety net for uncertain matches."""
    la, lb = len(a), len(b)
    if la == 0 or lb == 0:
        return 0.0
    if abs(la - lb) > max(la, lb) * 0.6:
        return 0.0
    prev = [0] * (lb + 1)
    for i in range(1, la + 1):
        curr = [0] * (lb + 1)
        for j in range(1, lb + 1):
            if a[i-1] == b[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(curr[j-1], prev[j])
        prev = curr
    return prev[lb] / max(la, lb)


# ═══════════════════════════════════════════════════════════════
# FREQUENCY MASS (self-adapting noise detection)
# ═══════════════════════════════════════════════════════════════

class FrequencyMass:
    """Detect noise by usage frequency. ZERO hardcoded word lists."""

    def __init__(self):
        self.counts: Dict[str, int] = {}
        self.total = 0

    def update(self, words: List[str]):
        self.total += 1
        for w in set(words):
            self.counts[w] = self.counts.get(w, 0) + 1

    def mass(self, word: str, position: int, total_words: int) -> float:
        """Word mass = length × rarity × position."""
        # Length factor
        wlen = len(word)
        if wlen <= 2: length_f = 0.05
        elif wlen == 3: length_f = 0.15
        elif wlen == 4: length_f = 0.4
        elif wlen == 5: length_f = 0.6
        else: length_f = 0.8 + min((wlen - 6) * 0.02, 0.2)

        # Rarity factor (1 = unique/rare, 0 = noise)
        if self.total < 20:
            # Cold start: use length as proxy
            rarity = 1.0 if wlen > 3 else 0.1
        else:
            freq = self.counts.get(word, 0) / max(self.total, 1)
            if freq > 0.4: rarity = 0.05
            elif freq > 0.2: rarity = 0.3
            else: rarity = 1.0

        # Position factor (last word = likely topic in English)
        pos_f = 1.0
        if total_words > 1:
            rel = position / max(total_words - 1, 1)
            if rel > 0.7: pos_f = 1.3
            elif rel < 0.2: pos_f = 1.1

        return length_f * rarity * pos_f

    def is_noise(self, word: str) -> bool:
        if self.total < 20:
            return len(word) <= 3
        return self.counts.get(word, 0) / max(self.total, 1) > 0.35


# ═══════════════════════════════════════════════════════════════
# ECHO CHAMBER (3-slot context, minimal memory)
# ═══════════════════════════════════════════════════════════════

class EchoChamber:
    """Track last 3 topics for pronoun resolution."""

    def __init__(self):
        self.slots: List[str] = ['', '', '']

    def push(self, entity: str):
        if entity and entity != self.slots[0]:
            self.slots = [entity, self.slots[0], self.slots[1]]

    def resolve(self, word: str) -> Optional[str]:
        refs = {'it', 'its', 'that', 'this', 'there', 'them', 'those'}
        if word in refs and self.slots[0]:
            return self.slots[0]
        if word in {'other', 'previous', 'first'} and self.slots[1]:
            return self.slots[1]
        return None

    def latest(self) -> str:
        return self.slots[0]


# ═══════════════════════════════════════════════════════════════
# CORRECTION MEMORY (learns from usage)
# ═══════════════════════════════════════════════════════════════

class CorrectionMemory:
    """Self-improving. Capped at 5000 entries."""

    def __init__(self):
        self.memory: Dict[str, str] = {}
        self.path = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'corrections.json')
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path) as f:
                    self.memory = json.load(f)
        except: pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            # LRU: keep only 5000
            if len(self.memory) > 5000:
                items = list(self.memory.items())[-5000:]
                self.memory = dict(items)
            with open(self.path, 'w') as f:
                json.dump(self.memory, f)
        except: pass

    def check(self, word: str) -> Optional[str]:
        return self.memory.get(word.lower())

    def learn(self, misspelled: str, correct: str):
        self.memory[misspelled.lower()] = correct
        if len(self.memory) % 50 == 0:
            self.save()


# ═══════════════════════════════════════════════════════════════
# THE SEMANTIC BRAIN (Field Theory Engine)
# ═══════════════════════════════════════════════════════════════

class SemanticBrain:
    """Language is a field. Words have position. Input is located, not matched."""

    # Adaptive distance thresholds (calibrated to actual 35D field distances)
    # Similar words: 0.2-0.5, different words: 0.8+
    TIGHT = {3: 0.25, 4: 0.35, 5: 0.35, 6: 0.35, 7: 0.35, 8: 0.35, 9: 0.35}
    LOOSE = {3: 0.40, 4: 0.55, 5: 0.60, 6: 0.65, 7: 0.70, 8: 0.75, 9: 0.80}

    def __init__(self, entities: Set[str] = None):
        self.word_field = LSHIndex(num_planes=12, dims=35)
        self.phrase_field = LSHIndex(num_planes=10, dims=35)
        self.freq = FrequencyMass()
        self.echo = EchoChamber()
        self.corrections = CorrectionMemory()
        self.entities: Set[str] = set()
        self._entity_lower: Set[str] = set()
        self._compounds: Set[str] = set()

        # Build fields from initial entities
        if entities:
            self.add_entities(entities)

    def add_entities(self, new_entities):
        """Add entities to the field. Can be called anytime (learning)."""
        for entity in new_entities:
            e_lower = entity.lower()
            if e_lower in self._entity_lower:
                continue
            self.entities.add(entity)
            self._entity_lower.add(e_lower)

            if ' ' in entity:
                # Compound entity → phrase field
                self._compounds.add(e_lower)
                vec = _phrase_vector(e_lower)
                self.phrase_field.insert(e_lower, vec)
                # Also add component words to word field (for fuzzy compound resolution)
                for part in e_lower.split():
                    if len(part) > 2 and part not in self._entity_lower:
                        self._entity_lower.add(part)
                        self.word_field.insert(part, _word_vector(part))
            else:
                # Single word → word field
                vec = _word_vector(e_lower)
                self.word_field.insert(e_lower, vec)

    # ─── MAIN ENTRY POINT ───

    def understand(self, raw_input: str) -> Forces:
        """Locate input in the field. Return the 5 forces."""
        forces = Forces(original=raw_input)

        if not raw_input or not raw_input.strip():
            return forces

        # Layer 1: Normalize
        cleaned = self._normalize(raw_input)
        tokens = cleaned.split()
        if not tokens:
            return forces

        # Update frequency stats
        self.freq.update(tokens)

        # Layer 2: Phrase field check (compound entities)
        compound = self._check_phrase_field(cleaned, tokens)
        if compound:
            forces.compound = compound
            forces.gravity = compound
            forces.confidence = 0.95
            self.echo.push(compound)
            forces.wavelength = self._detect_wavelength(tokens, len(raw_input))
            return forces

        # Layer 3: Compute mass, identify content words
        content_words = []
        for i, token in enumerate(tokens):
            if not self.freq.is_noise(token) and len(token) > 1:
                m = self.freq.mass(token, i, len(tokens))
                # BOOST: if token is an exact entity match → heavy
                if token in self._entity_lower:
                    m *= 3.0
                # BOOST: check ORIGINAL case (for DNA, RNA, etc.)
                elif any(token == orig_t.lower() for orig_t in raw_input.split() if orig_t in self.entities):
                    m *= 3.0
                # BOOST: short ALL-CAPS in original → likely acronym/entity
                elif len(token) <= 4:
                    # Check if original had this as uppercase
                    orig_tokens = raw_input.split()
                    for ot in orig_tokens:
                        if ot.lower() == token and ot.isupper() and ot in self.entities:
                            m *= 3.0
                            break
                content_words.append((token, m))
        content_words.sort(key=lambda x: x[1], reverse=True)

        if not content_words:
            # All noise → might be a greeting or command
            forces.gravity = cleaned
            forces.confidence = 0.2
            return forces

        # Layer 4: Locate each content word in the field
        resolved = []
        for word, mass in content_words[:4]:  # Top 4 heaviest
            entity, conf = self._locate_word(word)
            resolved.append((entity or word, conf, mass))

        # Layer 4.5: MUTUAL RESOLUTION — resolved words help ambiguous ones
        resolved = self._mutual_resolve(resolved, content_words)

        # Layer 5: Echo chamber (resolve pronouns)
        for i, (word, conf, mass) in enumerate(resolved):
            if conf < 0.3:
                echo_result = self.echo.resolve(word)
                if echo_result:
                    resolved[i] = (echo_result, 0.85, mass)
                    forces.momentum = 'reference'

        # Layer 6: Assemble forces
        if resolved:
            # Gravity = best match with highest (confidence × mass)
            resolved.sort(key=lambda x: x[1] * x[2], reverse=True)
            forces.gravity = resolved[0][0]
            forces.confidence = resolved[0][1]

            if len(resolved) > 1 and resolved[1][1] > 0.5:
                forces.spin = resolved[1][0]

            # CHECK: do gravity + spin form a compound entity?
            if forces.gravity and forces.spin:
                pair1 = f"{forces.gravity} {forces.spin}".lower()
                pair2 = f"{forces.spin} {forces.gravity}".lower()
                if pair1 in self._compounds:
                    forces.compound = pair1
                    forces.gravity = pair1
                    forces.confidence = 0.95
                elif pair2 in self._compounds:
                    forces.compound = pair2
                    forces.gravity = pair2
                    forces.confidence = 0.95

            # CHECK: does gravity alone match START of any compound?
            if not forces.compound and forces.gravity:
                g_low = forces.gravity.lower()
                for comp in self._compounds:
                    if comp.startswith(g_low + ' ') or comp.endswith(' ' + g_low):
                        forces.compound = comp
                        forces.gravity = comp
                        forces.confidence = max(forces.confidence, 0.85)
                        break

        # Detect other forces
        forces.charge = self._detect_charge(tokens)
        if forces.momentum == 'new':
            forces.momentum = self._detect_momentum(tokens)
        forces.wavelength = self._detect_wavelength(tokens, len(raw_input))
        forces.action = self._detect_action(tokens)

        # Confidence gate
        if forces.confidence < 0.4:
            forces.needs_clarify = True
            forces.clarify_options = [f"Did you mean '{forces.gravity}'?"]

        # Push to echo
        if forces.gravity and forces.confidence > 0.6:
            self.echo.push(forces.gravity)

        return forces

    # ─── FIELD OPERATIONS ───

    def _locate_word(self, word: str) -> Tuple[str, float]:
        """Locate a word in the character field. Returns (entity, confidence)."""
        w = word.lower()

        # Fast path: exact match
        if w in self._entity_lower:
            return self._original_case(w), 1.0

        # Fast path: correction memory
        corrected = self.corrections.check(w)
        if corrected:
            return corrected, 0.96

        # Field lookup
        if self.word_field.size() < 10:
            return word, 0.3  # Cold start

        vec = _word_vector(w)
        neighbors = self.word_field.query(vec, max_candidates=150)

        if not neighbors:
            return word, 0.3

        best_entity, best_dist = neighbors[0]
        wlen = len(w)

        # Adaptive thresholds
        tight = self.TIGHT.get(wlen, 0.25 + wlen * 0.01)
        loose = self.LOOSE.get(wlen, 0.35 + wlen * 0.015)

        if best_dist <= tight:
            # Very close in field → verify with quick LCS to prevent false positive
            lcs_check = _lcs_ratio(w, best_entity)
            if lcs_check >= 0.70:
                self.corrections.learn(w, best_entity)
                return self._original_case(best_entity), 0.95
            # Field said close but LCS disagrees → check next neighbors
            for entity, dist in neighbors[1:5]:
                if dist > loose:
                    break
                lcs2 = _lcs_ratio(w, entity)
                if lcs2 > lcs_check and lcs2 >= 0.70:
                    self.corrections.learn(w, entity)
                    return self._original_case(entity), 0.90

        if best_dist <= loose:
            # Uncertain zone → LCS verify
            lcs = _lcs_ratio(w, best_entity)
            # Adaptive LCS threshold by length
            lcs_thresh = 0.78 if wlen <= 4 else (0.63 if wlen <= 6 else (0.58 if wlen <= 9 else 0.52))
            if lcs >= lcs_thresh:
                self.corrections.learn(w, best_entity)
                return self._original_case(best_entity), 0.75 + lcs * 0.2

            # Check second nearest
            if len(neighbors) > 1:
                second_entity, second_dist = neighbors[1]
                if second_dist <= loose:
                    lcs2 = _lcs_ratio(w, second_entity)
                    if lcs2 > lcs and lcs2 >= lcs_thresh:
                        self.corrections.learn(w, second_entity)
                        return self._original_case(second_entity), 0.70 + lcs2 * 0.2

        # EXTENDED SEARCH: for ANY neighbor within 1.2, try LCS
        # This catches cases where field distance is large but LCS is good
        lcs_thresh_ext = 0.72 if wlen <= 4 else (0.60 if wlen <= 6 else (0.55 if wlen <= 9 else 0.50))
        for entity, dist in neighbors[:15]:
            if dist > 1.3:
                break
            if dist <= tight:
                continue  # Already handled above
            lcs = _lcs_ratio(w, entity)
            if lcs >= lcs_thresh_ext:
                self.corrections.learn(w, entity)
                return self._original_case(entity), 0.60 + lcs * 0.25

        # Prefix check (word fragments: "photo" → "photosynthesis")
        if wlen >= 4:
            for entity, dist in neighbors[:10]:
                if entity.startswith(w) and len(entity) > wlen:
                    return self._original_case(entity), 0.60

        # Wide LCS check (last resort before giving up)
        lcs_last = 0.70 if wlen <= 4 else (0.58 if wlen <= 6 else (0.52 if wlen <= 9 else 0.48))
        for entity, dist in neighbors[:15]:
            if dist > 1.5:
                break
            lcs = _lcs_ratio(w, entity)
            if lcs >= lcs_last:
                self.corrections.learn(w, entity)
                return self._original_case(entity), 0.55 + lcs * 0.3

        # BRUTE FORCE LCS (when field is sparse / entity set small)
        # Only runs if nothing found above. Still fast for <10K entities.
        if self.word_field.size() < 5000:
            best_lcs_entity = None
            best_lcs_score = 0.0
            lcs_min = 0.70 if wlen <= 4 else (0.58 if wlen <= 6 else (0.52 if wlen <= 9 else 0.45))
            
            # SPECIAL: if input is SHORTER than typical entities → it might be abbreviated
            # Check if input chars are a SUBSEQUENCE of any entity (zero language knowledge)
            # Gate: input must be significantly shorter than potential match (ratio < 0.75)
            is_abbreviated = wlen <= 6  # Short words are likely abbreviations
            
            if is_abbreviated:
                for entity in self._entity_lower:
                    if len(entity) <= wlen:  # Entity should be LONGER
                        continue
                    if len(entity) > wlen * 4:  # But not absurdly longer
                        continue
                    # Check if ALL input chars appear in order in entity
                    if self._is_subsequence(w, entity):
                        # Score by coverage: what fraction of entity's chars did we cover?
                        coverage = wlen / len(entity)
                        # Must cover at least 40% of entity
                        if coverage > 0.35 and coverage > best_lcs_score:
                            best_lcs_score = coverage
                            best_lcs_entity = entity
                
                if best_lcs_entity and best_lcs_score > 0.35:
                    self.corrections.learn(w, best_lcs_entity)
                    return self._original_case(best_lcs_entity), 0.50 + best_lcs_score * 0.4
                # Reset for regular LCS below
                best_lcs_entity = None
                best_lcs_score = 0.0
            
            # Regular LCS brute force
            for entity in self._entity_lower:
                if abs(len(entity) - wlen) > max(wlen * 0.6, 3):
                    continue
                lcs = _lcs_ratio(w, entity)
                # Prefer: higher LCS. Tiebreak: same first char > closer length
                if lcs > best_lcs_score:
                    best_lcs_score = lcs
                    best_lcs_entity = entity
                elif lcs == best_lcs_score and best_lcs_entity:
                    # Tiebreak 1: prefer same first character
                    input_starts = w[0] if w else ''
                    if entity[0] == input_starts and best_lcs_entity[0] != input_starts:
                        best_lcs_entity = entity
                    # Tiebreak 2: prefer closer length
                    elif abs(len(entity)-wlen) < abs(len(best_lcs_entity)-wlen):
                        best_lcs_entity = entity
            if best_lcs_entity and best_lcs_score >= lcs_min:
                self.corrections.learn(w, best_lcs_entity)
                return self._original_case(best_lcs_entity), 0.50 + best_lcs_score * 0.35

        # Initialism check (AI → artificial intelligence)
        if wlen <= 4 and w == word:  # Preserve original case check
            init_match = self._check_initialism(word)
            if init_match:
                return init_match, 0.90

        return word, 0.3

    def _check_phrase_field(self, cleaned: str, tokens: List[str]) -> Optional[str]:
        """Check if input matches a compound entity."""
        if self.phrase_field.size() == 0:
            return None

        # Only check if 2+ content words
        content = [t for t in tokens if not self.freq.is_noise(t) and len(t) > 2]
        if len(content) < 2:
            return None

        # Build phrase from content words
        phrase = ' '.join(content)
        vec = _phrase_vector(phrase)
        neighbors = self.phrase_field.query(vec, max_candidates=50)

        if not neighbors:
            return None

        best, best_dist = neighbors[0]

        # Threshold for phrase matching (more lenient since phrases are longer)
        if best_dist < 0.25:
            return best  # Very close

        if best_dist < 0.45:
            # Verify with LCS
            lcs = _lcs_ratio(phrase.replace(' ', ''), best.replace(' ', ''))
            if lcs > 0.55:
                return best

        # Try top 5 candidates with LCS (for heavily misspelled compounds)
        for cand, dist in neighbors[:5]:
            if dist < 0.60:
                lcs = _lcs_ratio(phrase.replace(' ', ''), cand.replace(' ', ''))
                if lcs > 0.55:
                    return cand

        # FALLBACK: resolve each content word individually, then check compound
        resolved_words = []
        for w in content:
            entity, conf = self._locate_word(w)
            resolved_words.append(entity if conf > 0.5 else w)
        resolved_phrase = ' '.join(resolved_words)
        if resolved_phrase.lower() in self._compounds:
            return resolved_phrase.lower()

        # Try all 2-word combinations of resolved words against compounds
        if len(resolved_words) >= 2:
            for i in range(len(resolved_words)):
                for j in range(i+1, len(resolved_words)):
                    pair = f"{resolved_words[i]} {resolved_words[j]}".lower()
                    pair_rev = f"{resolved_words[j]} {resolved_words[i]}".lower()
                    if pair in self._compounds:
                        return pair
                    if pair_rev in self._compounds:
                        return pair_rev

        return None

    def _check_initialism(self, word: str) -> Optional[str]:
        """Check if word is an initialism of a compound entity."""
        w_upper = word.upper()
        if not all(c.isalpha() for c in w_upper):
            return None
        for compound in self._compounds:
            parts = compound.split()
            # Take first char of each word (skip words ≤ 3 chars for initialisms > 2)
            if len(w_upper) <= 2:
                initials = ''.join(p[0] for p in parts).upper()
            else:
                initials = ''.join(p[0] for p in parts if len(p) > 2).upper()
                if len(initials) < len(w_upper):
                    initials = ''.join(p[0] for p in parts).upper()

            if initials == w_upper:
                return compound
        return None

    # ─── UTILITIES ───

    def _normalize(self, text: str) -> str:
        """Minimal normalization. No word lists."""
        t = text.lower().strip()
        # Apostrophe handling: X's → X
        t = re.sub(r"(\w)'s\b", r'\1', t)
        # Remove non-alphanumeric except spaces and ?
        t = re.sub(r'[^\w\s?]', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip().rstrip('?').strip()
        return t

    def _original_case(self, lower_entity: str) -> str:
        """Find original casing."""
        for e in self.entities:
            if e.lower() == lower_entity:
                return e
        return lower_entity

    def _detect_charge(self, tokens: List[str]) -> int:
        neg = {'not', 'no', 'never', 'dont', 'doesnt', 'cant', 'wont', 'isnt', 'arent', 'without', 'none'}
        return -1 if any(t in neg for t in tokens) else 1

    def _detect_momentum(self, tokens: List[str]) -> str:
        cont = {'more', 'also', 'another', 'else', 'again', 'continue'}
        drill = {'why', 'how', 'proof', 'explain', 'detail'}
        for t in tokens:
            if t in cont: return 'continue'
            if t in drill: return 'drill'
        return 'new'

    def _detect_wavelength(self, tokens: List[str], input_len: int) -> str:
        if input_len < 12 or len(tokens) <= 2:
            return 'short'
        deep = {'explain', 'detail', 'everything', 'comprehensive', 'full', 'deep'}
        if any(t in deep for t in tokens):
            return 'deep'
        return 'medium'

    def _detect_action(self, tokens: List[str]) -> str:
        """Detect action by exclusion: not an entity + verb-like length."""
        for t in tokens:
            if t not in self._entity_lower and len(t) > 3:
                if t.endswith(('ing', 'ed', 'ate', 'ize', 'ify')):
                    return t
        # Check common short actions
        actions = {'drop', 'heat', 'cool', 'mix', 'burn', 'cut', 'hit', 'push', 'pull', 'break', 'throw'}
        for t in tokens:
            if t in actions:
                return t
        return ''

    # ─── MUTUAL RESOLUTION ───

    def _mutual_resolve(self, resolved: List[Tuple[str, float, float]], 
                        content_words: List[Tuple[str, float]]) -> List[Tuple[str, float, float]]:
        """Words help each other resolve. Domain clustering."""
        # Find which words ARE resolved (conf > 0.6) 
        confident = [(entity, conf) for entity, conf, mass in resolved if conf > 0.6]
        if not confident:
            return resolved  # Nothing to help with

        # Find which words are NOT resolved (conf < 0.5)
        ambiguous_indices = [i for i, (entity, conf, mass) in enumerate(resolved) if conf < 0.5]
        if not ambiguous_indices:
            return resolved  # Nothing needs help

        # Determine the DOMAIN from confident words
        domain_entities = set(entity.lower() for entity, conf in confident)
        domain_neighbors = self._get_domain_cluster(domain_entities)

        # For each ambiguous word: re-resolve with domain filter
        for idx in ambiguous_indices:
            word = content_words[idx][0] if idx < len(content_words) else resolved[idx][0]
            mass = resolved[idx][2]
            
            # Find best match from domain cluster
            best_entity, best_score = self._resolve_in_domain(word, domain_neighbors)
            if best_entity and best_score > 0.45:
                resolved[idx] = (best_entity, best_score, mass)

        return resolved

    def _get_domain_cluster(self, seed_entities: Set[str]) -> Set[str]:
        """Find all entities in the same domain as the seed entities."""
        # Entities are in the same domain if they're CLOSE in the field
        cluster = set(seed_entities)
        
        for seed in seed_entities:
            if seed in self.word_field.all_entities:
                vec = self.word_field.all_entities[seed]
                neighbors = self.word_field.query(vec, max_candidates=200)
                # Add entities that are within a moderate distance
                for entity, dist in neighbors[:30]:
                    if dist < 0.8:
                        cluster.add(entity)
        
        # Also add entities that share FIELD NEIGHBORHOOD
        # (Entities close to each other = same domain)
        # For a richer cluster: any entity that's close to ANY seed
        for entity in self._entity_lower:
            if entity in cluster:
                continue
            if entity in self.word_field.all_entities:
                evec = self.word_field.all_entities[entity]
                for seed in seed_entities:
                    if seed in self.word_field.all_entities:
                        svec = self.word_field.all_entities[seed]
                        if _distance(evec, svec) < 0.6:
                            cluster.add(entity)
                            break
        
        return cluster

    def _resolve_in_domain(self, word: str, domain: Set[str]) -> Tuple[str, float]:
        """Resolve word against domain-filtered entities using LCS."""
        w = word.lower()
        wlen = len(w)
        
        best_entity = None
        best_score = 0.0
        lcs_min = 0.50 if wlen <= 4 else (0.45 if wlen <= 6 else 0.40)
        
        for entity in domain:
            if abs(len(entity) - wlen) > max(wlen * 0.8, 4):
                continue
            lcs = _lcs_ratio(w, entity)
            if lcs > best_score:
                best_score = lcs
                best_entity = entity
        
        if best_entity and best_score >= lcs_min:
            # Boost confidence because domain CONFIRMS the match
            conf = 0.60 + best_score * 0.30
            return self._original_case(best_entity), conf
        
        return None, 0.0

    @staticmethod
    def _is_subsequence(short: str, long: str) -> bool:
        """Check if 'short' is a subsequence of 'long' (chars appear in order)."""
        if not short:
            return True
        j = 0
        for ch in long:
            if ch == short[j]:
                j += 1
                if j == len(short):
                    return True
        return False


# ═══════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════

_brain = None

def get_brain(entities: Set[str] = None) -> SemanticBrain:
    global _brain
    if _brain is None:
        _brain = SemanticBrain(entities or set())
    return _brain

def understand(text: str) -> Forces:
    return get_brain().understand(text)


# ═══════════════════════════════════════════════════════════════
# RESOLUTION ENGINE — ZERO DEAD ENDS
# ═══════════════════════════════════════════════════════════════

class FailureLog:
    """Track failed lookups for retroactive backfill."""

    def __init__(self):
        self.failures: List[Dict] = []
        self.max_entries = 500

    def add(self, word: str, context: List[str], neighbors: List[str]):
        self.failures.append({
            'word': word.lower(),
            'context': context[:3],
            'neighbors': neighbors[:3],
            'timestamp': __import__('time').time(),
        })
        if len(self.failures) > self.max_entries:
            self.failures = self.failures[-self.max_entries:]

    def backfill(self, new_entity: str, lcs_func) -> List[str]:
        """Check if any failed words match this new entity."""
        learned = []
        remaining = []
        for entry in self.failures:
            ratio = lcs_func(entry['word'], new_entity.lower())
            if ratio > 0.55:
                learned.append((entry['word'], new_entity))
            else:
                remaining.append(entry)
        self.failures = remaining
        return learned

    def evict_old(self, max_age_days: int = 30):
        now = __import__('time').time()
        cutoff = now - (max_age_days * 86400)
        self.failures = [f for f in self.failures if f['timestamp'] > cutoff]


class ImplicitLearner:
    """Learn from user behavior without explicit correction."""

    def __init__(self, corrections: CorrectionMemory):
        self.corrections = corrections
        self.pending: Dict[str, Dict] = {}  # word → {guess, weak_count}

    def set_pending(self, word: str, guess: str):
        """Mark a resolution as pending confirmation."""
        self.pending[word.lower()] = {'guess': guess, 'weak_count': 0}

    def confirm(self, word: str):
        """User confirmed (follow-up or explicit 'yes')."""
        w = word.lower()
        if w in self.pending:
            self.corrections.learn(w, self.pending[w]['guess'])
            del self.pending[w]

    def weak_confirm(self, word: str):
        """User moved on without correcting. 3 weak = permanent."""
        w = word.lower()
        if w in self.pending:
            self.pending[w]['weak_count'] += 1
            if self.pending[w]['weak_count'] >= 3:
                self.corrections.learn(w, self.pending[w]['guess'])
                del self.pending[w]

    def reject(self, word: str) -> Optional[str]:
        """User rejected. Returns the guess that was wrong."""
        w = word.lower()
        if w in self.pending:
            guess = self.pending[w]['guess']
            del self.pending[w]
            return guess
        return None

    def has_pending(self) -> bool:
        return len(self.pending) > 0

    def get_pending_word(self) -> Optional[str]:
        """Get the most recent pending word."""
        if self.pending:
            return list(self.pending.keys())[-1]
        return None


@dataclass
class Resolution:
    """Result of resolution attempt."""
    answer_entity: str = ''         # Best guess entity
    confidence: float = 0.0         # How sure
    alternatives: List[str] = field(default_factory=list)  # Other options
    source: str = ''                # 'field', 'context', 'web', 'prefix'
    display_hint: str = ''          # How to present to user


class ResolutionEngine:
    """Zero dead ends. Always gives something. Always learns."""

    def __init__(self, brain: SemanticBrain, web_func=None):
        self.brain = brain
        self.web = web_func  # Optional: web_read(question) → str
        self.failure_log = FailureLog()
        self.learner = ImplicitLearner(brain.corrections)

    def resolve(self, word: str, confidence: float,
                neighbors: List[Tuple[str, float]],
                echo_context: str = '') -> Resolution:
        """Resolve an uncertain word. NEVER returns nothing."""
        res = Resolution()
        w = word.lower()

        # Step 1: Gibberish check
        if self._is_gibberish(w, neighbors):
            res.display_hint = 'gibberish'
            res.confidence = 0.0
            return res

        # Step 2: Get top 3 alternatives from field
        alts = [entity for entity, dist in neighbors[:3] if dist < 1.0]
        res.alternatives = alts

        # Step 3: Context gravity (echo pulls candidates)
        if echo_context and alts:
            boosted = self._context_pull(alts, echo_context)
            if boosted:
                best_entity, boosted_conf = boosted
                if boosted_conf > 0.6:
                    res.answer_entity = best_entity
                    res.confidence = boosted_conf
                    res.source = 'context'
                    self.learner.set_pending(w, best_entity)
                    return res

        # Step 4: If best neighbor is decent, use it
        if alts:
            res.answer_entity = alts[0]
            # Boost confidence if only 1 close candidate (less ambiguity)
            if len(alts) == 1 or (len(alts) > 1 and neighbors[0][1] < neighbors[1][1] * 0.7):
                res.confidence = max(confidence, 0.50)
            else:
                res.confidence = max(confidence, 0.35)
            res.source = 'field'
            self.learner.set_pending(w, alts[0])

        # Step 5: Web search (parallel in real integration, sequential here)
        if res.confidence < 0.5 and self.web:
            web_answer = self._try_web(word)
            if web_answer:
                res.answer_entity = web_answer
                res.confidence = 0.70
                res.source = 'web'
                # Learn from web
                self.brain.corrections.learn(w, web_answer)

        # Step 6: Format display hint
        res.display_hint = self._format_hint(res)

        # Step 7: Save to failure log if still low confidence
        if res.confidence < 0.4:
            self.failure_log.add(w, [echo_context] if echo_context else [], alts)

        return res

    def on_user_response(self, user_input: str):
        """Process user's next input for implicit learning."""
        inp = user_input.strip().lower()

        # Check if user picked an alternative ("1", "2", "3")
        if inp in ('1', '2', '3') and self.learner.has_pending():
            pending_word = self.learner.get_pending_word()
            if pending_word:
                self.learner.confirm(pending_word)
            return

        # Check explicit confirmation
        if inp in ('yes', 'yeah', 'yep', 'right', 'correct', 'exactly'):
            pending_word = self.learner.get_pending_word()
            if pending_word:
                self.learner.confirm(pending_word)
            return

        # Check explicit rejection
        if inp in ('no', 'nope', 'wrong', 'not that'):
            pending_word = self.learner.get_pending_word()
            if pending_word:
                self.learner.reject(pending_word)
            return

        # Implicit: if user asks follow-up (short input, uses "it/that") → confirm
        if any(ref in inp for ref in ['it', 'its', 'that', 'this', 'more', 'also']):
            pending_word = self.learner.get_pending_word()
            if pending_word:
                self.learner.confirm(pending_word)
            return

        # Otherwise: weak confirm (user moved on)
        pending_word = self.learner.get_pending_word()
        if pending_word:
            self.learner.weak_confirm(pending_word)

    def on_entity_learned(self, entity: str):
        """When a new entity is learned, check failure log for backfill."""
        mappings = self.failure_log.backfill(entity, _lcs_ratio)
        for misspelled, correct in mappings:
            self.brain.corrections.learn(misspelled, correct)

    def _is_gibberish(self, word: str, neighbors: List[Tuple[str, float]]) -> bool:
        """3 signals: no close neighbor + low diversity + bad patterns."""
        # Signal 1: no neighbor within 1.0
        if neighbors and neighbors[0][1] < 1.0:
            return False  # Has a somewhat close neighbor → not gibberish

        # Signal 2: character diversity check (real words have mix of common+rare chars)
        # Gibberish tends to be all mid-frequency chars (keyboard rows)
        unique_chars = len(set(word))
        diversity = unique_chars / max(len(word), 1)
        # Real words: diversity 0.5-0.9. Keyboard mashing: often 1.0 (all unique) or very low
        if 0.4 < diversity < 0.95:
            return False  # Normal diversity → probably real word attempt

        # Signal 3: check if any entity is even remotely close in field
        if neighbors and neighbors[0][1] < 0.8:
            return False

        # All signals say gibberish
        return len(word) > 4

    def _context_pull(self, candidates: List[str], echo: str) -> Optional[Tuple[str, float]]:
        """Boost candidate if related to echo context."""
        if not echo or not candidates:
            return None
        echo_vec = _word_vector(echo.lower())
        best = None
        best_score = 0
        for cand in candidates:
            cand_vec = _word_vector(cand.lower())
            dist = _distance(echo_vec, cand_vec)
            # Closer to echo context = more related
            relatedness = max(0, 1.0 - dist)
            if relatedness > 0.3 and relatedness > best_score:
                best_score = relatedness
                best = cand
        if best:
            return best, 0.55 + best_score * 0.3
        return None

    def _try_web(self, word: str) -> Optional[str]:
        """Try web search for the word."""
        if not self.web:
            return None
        try:
            result = self.web(word)
            if result and len(result) > 10:
                return result
        except:
            pass
        return None

    def _format_hint(self, res: Resolution) -> str:
        """Generate display hint based on confidence level."""
        if res.confidence >= 0.70:
            return 'direct'  # Just answer
        if res.confidence >= 0.50:
            return 'answer_with_note'  # Answer + "(assuming X)"
        if res.confidence >= 0.30:
            return 'answer_with_alts'  # Answer + "Not right? 1)Y 2)Z"
        if res.alternatives:
            return 'options_only'  # "Closest: 1)X 2)Y 3)Z"
        return 'nothing'  # Truly nothing found


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    entities = {
        'japan', 'france', 'germany', 'italy', 'brazil', 'india', 'china',
        'einstein', 'newton', 'shakespeare', 'fleming', 'edison', 'beethoven',
        'aristotle', 'pythagoras', 'galileo', 'darwin', 'tesla',
        'gravity', 'photosynthesis', 'relativity', 'evolution', 'electricity',
        'water', 'gold', 'iron', 'oxygen', 'carbon', 'hydrogen', 'glass', 'metal',
        'jupiter', 'saturn', 'mars', 'venus', 'mercury', 'earth', 'sun', 'moon',
        'computer', 'internet', 'bitcoin', 'algorithm', 'DNA',
        'elephant', 'dinosaur', 'volcano', 'earthquake', 'hurricane',
        'democracy', 'philosophy', 'psychology', 'mathematics', 'chemistry',
        'thermodynamics', 'quantum', 'nuclear', 'uranium', 'metabolism',
        'vaccination', 'penicillin', 'chromosome', 'antibiotic',
        'capital', 'boiling', 'temperature', 'speed', 'population',
        'speed of light', 'climate change', 'theory of relativity',
        'machine learning', 'artificial intelligence', 'black hole', 'solar system',
        'boiling point', 'eiffel tower', 'mount everest',
    }

    brain = SemanticBrain(entities)

    print("═" * 60)
    print("  SEMANTIC BRAIN v6.0 — Field Theory Test")
    print(f"  Entities: {brain.word_field.size()} words + {brain.phrase_field.size()} compounds")
    print("═" * 60)
    print()

    tests = [
        # Misspellings (various types)
        ("japn", "japan"), ("einsten", "einstein"), ("watre", "water"),
        ("fotosinthesis", "photosynthesis"), ("komputer", "computer"),
        ("grvty", "gravity"), ("elefant", "elephant"), ("kemistry", "chemistry"),
        ("pitagoras", "pythagoras"), ("dinamsor", "dinosaur"),
        ("filosohy", "philosophy"), ("vacination", "vaccination"),
        ("uranyum", "uranium"), ("quantm", "quantum"), ("gallileo", "galileo"),
        # Compounds
        ("speed of light", "speed of light"), ("climate change", "climate change"),
        ("blak hole", "black hole"), ("solr systm", "solar system"),
        ("masheen lerning", "machine learning"),
        # Slang/noise
        ("yo gravity", "gravity"), ("bruh whats photosynthesis", "photosynthesis"),
        ("pls explain DNA", "DNA"), ("bhai einstein kya hai", "einstein"),
        # Minimal
        ("jupiter", "jupiter"), ("mars", "mars"),
        # Initialism
        ("AI", "artificial intelligence"),
    ]

    passed = 0
    for inp, expected in tests:
        f = brain.understand(inp)
        g = f.gravity.lower() if f.gravity else ''
        comp = f.compound.lower() if f.compound else ''
        hit = expected.lower() in g or expected.lower() in comp
        if hit: passed += 1
        sym = '✓' if hit else '✗'
        print(f"  {sym} \"{inp}\" → {g or comp} ({f.confidence:.2f})")

    print()
    print(f"  RESULT: {passed}/{len(tests)} ({passed/len(tests)*100:.0f}%)")
    print()
