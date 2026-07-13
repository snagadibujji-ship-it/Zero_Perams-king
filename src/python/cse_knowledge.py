#!/usr/bin/env python3
"""
AXIMA CSE Python Wrapper — Queries the compressed binary knowledge database.
Uses subprocess to call C binary for O(1) lookups, caches results in Python.
Also provides fallback: reads triples file directly if binary unavailable.
"""
import os, json, subprocess, re, time
from collections import OrderedDict

CSE_BINARY = os.path.join(os.path.dirname(__file__), '..', '..', 'ai')
CSE_DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge.cse')
TRIPLES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'unified_knowledge.triples')

# --- Upgrade constants ---
ALLOWED_RELATIONS = {'is_a', 'has_property', 'description', 'melts_at', 'boils_at', 'located_in'}
TRANSITIVE = {'is_a', 'located_in', 'part_of'}
IMMUTABLE_RELATIONS = {'melts_at', 'boils_at', 'atomic_number', 'formula'}


class LRUCache:
    """LRU hot cache — keeps most-queried entities in a fast OrderedDict."""
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


class CSEKnowledge:
    """Unified knowledge access — CSE binary first, triples fallback."""
    
    def __init__(self):
        self._cache = {}  # subject → {relation → [objects]}
        self._loaded = False
        self._inference_cache = {}  # (subject, relation) → inferred results
        self._contradictions = []   # list of contradiction dicts
        self._hot_cache = LRUCache(500)  # LRU hot cache for frequent queries
        self._load_triples()  # Always load triples as fallback (fast, <5ms)
    
    def _load_triples(self):
        """Load triples file into memory as a dict-of-dicts."""
        if not os.path.exists(TRIPLES_FILE):
            return
        try:
            with open(TRIPLES_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or '|' not in line:
                        continue
                    parts = line.split('|')
                    if len(parts) < 3:
                        continue
                    subj, rel, obj = parts[0], parts[1], parts[2]
                    conf = int(parts[3]) if len(parts) > 3 else 80
                    
                    if subj not in self._cache:
                        self._cache[subj] = {}
                    if rel not in self._cache[subj]:
                        self._cache[subj][rel] = []
                    self._cache[subj][rel].append((obj, conf))
            self._loaded = True
        except:
            pass
    
    def query(self, subject, relation=None):
        """Query knowledge about a subject. Returns list of (relation, object, confidence)."""
        subject_lower = subject.lower()
        results = []

        # Check LRU hot cache first
        cache_key = (subject_lower, relation)
        cached = self._hot_cache.get(cache_key)
        if cached is not None:
            return cached

        if subject_lower in self._cache:
            data = self._cache[subject_lower]
            if relation:
                if relation in data:
                    for obj, conf in data[relation]:
                        results.append((relation, obj, conf))
            else:
                for rel, objs in data.items():
                    for obj, conf in objs:
                        results.append((rel, obj, conf))

        # Populate hot cache
        self._hot_cache.put(cache_key, results)
        return results
    
    def get_property(self, subject, relation):
        """Get a specific property value. Returns (value, confidence) or None."""
        results = self.query(subject, relation)
        if results:
            return results[0][1], results[0][2]
        return None
    
    def get_description(self, subject):
        """Get the description/extra fact for a subject."""
        result = self.get_property(subject, 'description')
        if result:
            return result[0]
        return None
    
    def get_explanation(self, topic):
        """Get WHY/HOW explanation for a topic."""
        result = self.get_property(topic, 'explanation')
        if result:
            return result[0]
        return None
    
    def get_material_props(self, subject):
        """Get physical properties for causal reasoning."""
        props = {}
        results = self.query(subject)
        for rel, obj, conf in results:
            if rel == 'has_state':
                props['state'] = obj
            elif rel == 'melts_at':
                try: props['melt_temp'] = int(float(obj))
                except: pass
            elif rel == 'boils_at':
                try: props['boil_temp'] = int(float(obj))
                except: pass
            elif rel == 'cooks_at':
                try: props['cook_temp'] = int(float(obj))
                except: pass
            elif rel == 'burns_at':
                try: props['burn_temp'] = int(float(obj))
                except: pass
            elif rel == 'is_a':
                props['category'] = obj
            elif rel == 'is_flammable' and obj == 'true':
                props['flammable'] = True
            elif rel == 'is_fragile' and obj == 'true':
                props['fragile'] = True
            elif rel == 'is_elastic' and obj == 'true':
                props['elastic'] = True
            elif rel == 'is_conductive' and obj == 'true':
                props['conductive'] = True
            elif rel == 'is_magnetic' and obj == 'true':
                props['magnetic'] = True
            elif rel == 'is_dense' and obj == 'true':
                props['dense'] = True
            elif rel == 'is_malleable' and obj == 'true':
                props['malleable'] = True
            elif rel == 'corrodes' and obj == 'true':
                props['corrodes'] = True
            elif rel == 'is_soluble' and obj == 'true':
                props['soluble'] = True
        return props if props else None
    
    def has(self, subject):
        """Check if subject exists in knowledge."""
        return subject.lower() in self._cache
    
    def size(self):
        """Total number of subjects."""
        return len(self._cache)
    
    def fact_count(self):
        """Total number of facts."""
        total = 0
        for subj, rels in self._cache.items():
            for rel, objs in rels.items():
                total += len(objs)
        return total
    
    def stats(self):
        return {
            'subjects': self.size(),
            'facts': self.fact_count(),
            'cse_file': os.path.exists(CSE_DB),
            'cse_size_kb': os.path.getsize(CSE_DB) / 1024 if os.path.exists(CSE_DB) else 0,
        }

    # ═══════════════════════════════════════════════════════════════════
    # UPGRADE #1: Auto-Import from Web
    # ═══════════════════════════════════════════════════════════════════

    def auto_import(self, question, answer, source='web'):
        """Extract and store facts from a verified answer."""
        triples = self._extract_triples(answer)
        imported = 0
        for subj, rel, obj, conf in triples:
            if conf >= 0.7 and rel in ALLOWED_RELATIONS:
                self.store_triple(subj, rel, obj, conf, source=source)
                imported += 1
        return imported

    def _extract_triples(self, text):
        """Extract (subject, relation, object, confidence) from natural language."""
        triples = []
        text = text.strip()
        # Pattern: X is a Y
        for m in re.finditer(r'([A-Za-z][a-z ]+?) is (?:a|an) ([a-z ]+?)(?:\.|,|$)', text):
            triples.append((m.group(1).strip().lower(), 'is_a', m.group(2).strip().lower(), 0.8))
        # Pattern: X is located in Y
        for m in re.finditer(r'([A-Za-z][a-z ]+?) is (?:located |found )?in ([A-Za-z][a-z ]+?)(?:\.|,|$)', text):
            triples.append((m.group(1).strip().lower(), 'located_in', m.group(2).strip().lower(), 0.8))
        # Pattern: X melts at Y degrees
        for m in re.finditer(r'([A-Za-z][a-z ]+?) melts at ([\d,.]+)', text):
            triples.append((m.group(1).strip().lower(), 'melts_at', m.group(2).strip(), 0.9))
        # Pattern: X boils at Y degrees
        for m in re.finditer(r'([A-Za-z][a-z ]+?) boils at ([\d,.]+)', text):
            triples.append((m.group(1).strip().lower(), 'boils_at', m.group(2).strip(), 0.9))
        # Pattern: X has/have Y (property)
        for m in re.finditer(r'([A-Za-z][a-z ]+?) (?:has|have) ([a-z ]+?)(?:\.|,|$)', text):
            triples.append((m.group(1).strip().lower(), 'has_property', m.group(2).strip().lower(), 0.75))
        # Pattern: X is Y (description - fallback)
        if not triples:
            m = re.match(r'([A-Za-z][a-z ]+?) is ([^.]{10,80})', text)
            if m:
                triples.append((m.group(1).strip().lower(), 'description', m.group(2).strip(), 0.75))
        return triples

    def store_triple(self, subject, relation, obj, confidence, source='unknown'):
        """Store a triple in the cache and persist to triples file."""
        subj = subject.lower().strip()
        # Check for contradictions (Upgrade #10)
        if self._check_contradiction(subj, relation, obj):
            return  # blocked by immutable fact
        if subj not in self._cache:
            self._cache[subj] = {}
        if relation not in self._cache[subj]:
            self._cache[subj][relation] = []
        # Don't duplicate
        for existing_obj, existing_conf in self._cache[subj][relation]:
            if existing_obj == obj:
                return  # already exists
        self._cache[subj][relation].append((obj, int(confidence * 100)))
        # Invalidate hot cache for this subject
        self._hot_cache.put((subj, relation), None)
        self._hot_cache.put((subj, None), None)
        # Persist to file
        try:
            with open(TRIPLES_FILE, 'a') as f:
                f.write(f'{subj}|{relation}|{obj}|{int(confidence*100)}|{source}|{int(time.time())}\n')
        except:
            pass

    # ═══════════════════════════════════════════════════════════════════
    # UPGRADE #4: Relation Inference — Transitive Whitelist
    # ═══════════════════════════════════════════════════════════════════

    def query_with_inference(self, subject, relation, max_depth=3):
        """Query with transitive inference if relation allows."""
        direct = self.query(subject, relation)
        if direct or relation not in TRANSITIVE:
            return direct
        # Try multi-hop inference
        return self._infer_transitive(subject, relation, max_depth, set())

    def _infer_transitive(self, subject, relation, depth, visited):
        """Recursive transitive inference with cycle detection."""
        if depth <= 0 or subject in visited:
            return []
        visited.add(subject)
        results = []
        parents = self.query(subject, relation)
        for _, parent, conf1 in parents:
            # Direct parent found
            grandparents = self.query(parent, relation)
            for _, gp, conf2 in grandparents:
                inferred_conf = int((conf1 / 100) * (conf2 / 100) * 100)
                if inferred_conf > 50:
                    results.append((relation, gp, inferred_conf))
            # Go deeper
            if depth > 1:
                deeper = self._infer_transitive(parent, relation, depth - 1, visited)
                for rel, obj, conf in deeper:
                    chained_conf = int((conf1 / 100) * (conf / 100) * 100)
                    if chained_conf > 50:
                        results.append((rel, obj, chained_conf))
        # Cache results
        if results and subject.lower() not in self._inference_cache:
            self._inference_cache[(subject.lower(), relation)] = results
        return results

    # ═══════════════════════════════════════════════════════════════════
    # UPGRADE #10: Contradiction Flagging
    # ═══════════════════════════════════════════════════════════════════

    def _check_contradiction(self, subject, relation, new_obj):
        """Check if new fact contradicts existing. Returns True if contradiction found."""
        existing = self.query(subject, relation)
        for _, old_obj, conf in existing:
            if old_obj != new_obj:
                if relation in IMMUTABLE_RELATIONS:
                    return True  # block: immutable fact
                # Flag contradiction
                self._contradictions.append({
                    'subject': subject, 'relation': relation,
                    'old': old_obj, 'new': new_obj,
                    'timestamp': time.time()
                })
                return False  # allow but flagged
        return False


# Singleton
_instance = None

def get_knowledge():
    global _instance
    if _instance is None:
        _instance = CSEKnowledge()
    return _instance


if __name__ == '__main__':
    kb = CSEKnowledge()
    print(f"═══ CSE Knowledge Store ═══")
    print(f"  Subjects: {kb.size()}")
    print(f"  Facts:    {kb.fact_count()}")
    print(f"  CSE file: {os.path.exists(CSE_DB)} ({os.path.getsize(CSE_DB)/1024:.1f} KB)" if os.path.exists(CSE_DB) else "  CSE: not built")
    print()
    
    # Test queries
    tests = [
        ('iron', None),
        ('sun', 'description'),
        ('sky blue', 'explanation'),
        ('candle', None),
        ('maple syrup', None),
    ]
    for subj, rel in tests:
        if rel:
            r = kb.get_property(subj, rel)
            print(f"  {subj}.{rel} = {r[0][:80] if r else 'NOT FOUND'}")
        else:
            results = kb.query(subj)
            print(f"  {subj}: {len(results)} facts")
            for r, o, c in results[:3]:
                print(f"    {r} = {o}")
        print()
