# AXIMA Upgrade Plan — QIR + Self-Learning + CSE Knowledge

> Status: PLANNED (not yet built)
> Priority: Build in order #1-#10
> Pre-requisites: All 52 audit fixes done, QIR live, Self-Learning built but basic

---

## UPGRADE #1: Auto-Import from Web (cse_knowledge.py) — 30 min

When web search finds an answer, extract triples and store permanently.

**Rules:**
- Only store if answer was VERIFIED (self-learning confirmed good)
- Extract format: subject|relation|object|confidence
- Confidence must be ≥70% to store
- Tag with SOURCE so bad facts can be traced
- Relations allowed: is_a, has_property, description, melts_at, boils_at, located_in

**Implementation:**
```python
def auto_import(question, answer, source='web'):
    """Extract and store facts from a verified answer."""
    triples = extract_triples(answer)  # regex-based extraction
    for subj, rel, obj, conf in triples:
        if conf >= 0.7 and rel in ALLOWED_RELATIONS:
            store.store_triple(subj, rel, obj, conf, source=source, timestamp=now)
```

---

## UPGRADE #2: Temporal Context (self_learning.py) — 15 min

3-turn context window. If last 3 questions were about space → assume next is space too.

**Rules:**
- Window = last 3 turns only (not whole session)
- Reset if new question has ZERO word overlap with previous 3
- Decay: turn N-1 = 1.0 weight, N-2 = 0.7, N-3 = 0.4
- Explicit reset on topic-switch signals (question type changes)

**Implementation:**
```python
class TemporalContext:
    def __init__(self):
        self.history = []  # last 3 (domain, words)
    
    def get_domain_boost(self):
        """Return domain with highest recent weight."""
        if not self.history: return None
        scores = {}
        weights = [1.0, 0.7, 0.4]
        for i, (domain, words) in enumerate(reversed(self.history[-3:])):
            if domain:
                scores[domain] = scores.get(domain, 0) + weights[i]
        return max(scores, key=scores.get) if scores else None
```

---

## UPGRADE #3: Multi-Word Entity from CSE (qir.py) — 15 min

Check if consecutive tokens form a known compound entity in CSE.

**Rules:**
- Only check pairs (2 consecutive words) — not 3+
- Must exist as EXACT match in CSE knowledge store
- If found → merge into single QuantumToken with confidence 1.0
- Zero word lists — purely CSE lookup

**Implementation:**
```python
# In QIR.resolve(), after superposition:
for i in range(len(quantum_tokens) - 1):
    pair = f"{quantum_tokens[i].original} {quantum_tokens[i+1].original}".lower()
    if self._knowledge and self._knowledge.has(pair):
        # Merge into single token
        merged = QuantumToken(original=pair)
        merged.meanings = [Meaning(pair, 1.0, 'compound')]
        quantum_tokens[i] = merged
        quantum_tokens.pop(i+1)
```

---

## UPGRADE #4: Relation Inference — Transitive Whitelist (cse_knowledge.py) — 20 min

Derive new facts from existing via transitivity. Only for SAFE relations.

**Rules:**
- TRANSITIVE relations: is_a, located_in, part_of
- NOT transitive: has_property, causes, melts_at, description
- Max chain depth: 3 hops (dog→mammal→animal→living_thing, stop)
- Derived facts get confidence = product of chain (0.9 × 0.9 = 0.81)
- Cache derived results (don't recompute)

**Implementation:**
```python
TRANSITIVE = {'is_a', 'located_in', 'part_of'}

def query_with_inference(self, subject, relation):
    """Query with transitive inference if relation allows."""
    direct = self.query(subject, relation)
    if direct or relation not in TRANSITIVE:
        return direct
    # Try 1-hop inference
    parents = self.query(subject, relation)  # dog → mammal
    for _, parent, conf1 in parents:
        grandparents = self.query(parent, relation)  # mammal → animal
        for _, gp, conf2 in grandparents:
            inferred_conf = conf1/100 * conf2/100 * 100
            if inferred_conf > 50:
                direct.append((relation, gp, inferred_conf))
    return direct
```

---

## UPGRADE #5: Self-Verifying Corrections (qir.py) — 15 min

Only store a user's typo→correction mapping if it LED TO SUCCESS.

**Rules:**
- When QIR resolves "teh"→"the" and final answer is GOOD → store correction
- When resolution led to ERROR (self-learning detected) → DON'T store
- Corrections stored in user_data/corrections.json
- Max 5000 entries (LRU eviction)
- On next occurrence of "teh" → instantly resolve to "the" (conf 0.99)

**Implementation:**
```python
# After self-learning confirms good answer:
if qir_changed_words:
    for original, resolved in qir_changed_words:
        corrections.store(original, resolved)  # verified typo mapping

# In QIR superpose(), check corrections FIRST:
if token in self._corrections:
    qt.meanings.insert(0, Meaning(self._corrections[token], 0.99, 'learned'))
```

---

## UPGRADE #6: LRU Hot Cache (cse_knowledge.py) — 10 min

Most-queried entities stay in fast dict. Bounded RAM.

**Rules:**
- Max 500 entities in hot cache
- Every query bumps entity to front
- Not queried in last 100 queries → evicted
- Cache holds full property dict (not just existence)
- RAM bounded: ~50KB max

**Implementation:**
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, max_size=500):
        self._cache = OrderedDict()
        self._max = max_size
    
    def get(self, key):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def put(self, key, value):
        self._cache[key] = value
        self._cache.move_to_end(key)
        if len(self._cache) > self._max:
            self._cache.popitem(last=False)
```

---

## UPGRADE #7: Answer Quality Score (self_learning.py) — 10 min

4 objective signals, max score 8. Threshold ≥5 = good answer.

**Rules:**
- Signal 1: Contains topic word? (+3)
- Signal 2: No garbage signals? (+2)  
- Signal 3: Length > 20 chars? (+1)
- Signal 4: From verified source (CSE/cache vs unknown)? (+2)
- Score ≥ 5 → cache as success
- Score < 3 → log as failure + try recovery
- Score 3-4 → uncertain, don't cache either way

---

## UPGRADE #8: Session Confidence Decay (qir.py) — 10 min

If an interpretation fails, slightly suppress it for rest of session.

**Rules:**
- Decay = 0.95x per failure (slow)
- Takes 5+ failures to drop below 0.7 threshold
- PER-SESSION only (resets on restart)
- Applied to the specific (word → meaning) pair that failed
- Stored in QIR._session_decay = {(word, meaning): decay_factor}

---

## UPGRADE #9: User Profile Distribution (self_learning.py) — 15 min

Track domain preferences as probability distribution, not hard lock.

**Rules:**
- Count queries per domain over last 100 questions
- Normalize to distribution: {coding: 0.4, science: 0.3, general: 0.3}
- Apply as BOOST in QIR entanglement (not override)
- Decay weekly (multiply all counts by 0.9 each week)
- Stored in user_data/profile.json
- Max effect: 1.3x boost for top domain (never more)

---

## UPGRADE #10: Contradiction Flagging (cse_knowledge.py) — 10 min

Detect when new fact contradicts existing. Don't delete — flag both.

**Rules:**
- Only check for SAME subject + SAME relation with DIFFERENT object
- If conflict: store BOTH with timestamps
- Query returns NEWEST value by default
- Old value archived (not deleted)
- Log contradiction for review
- Math/science facts: never override (immutable)
- Technology/politics: newer wins

---

## TOTAL TIME: ~2.5 hours for all 10 upgrades

## PRINCIPLES (apply to ALL upgrades):
1. Zero word lists — use CSE/knowledge for everything
2. Self-verifying — only store what WORKS
3. Bounded — LRU, max counts, time decay prevents unbounded growth
4. Non-destructive — flags don't delete, decay doesn't kill
5. Session-safe — decay resets on restart, profiles degrade gracefully
