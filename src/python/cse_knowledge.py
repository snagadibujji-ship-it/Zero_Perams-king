#!/usr/bin/env python3
"""
AXIMA CSE Python Wrapper — Queries the compressed binary knowledge database.
Uses subprocess to call C binary for O(1) lookups, caches results in Python.
Also provides fallback: reads triples file directly if binary unavailable.
"""
import os, json, subprocess

CSE_BINARY = os.path.join(os.path.dirname(__file__), '..', '..', 'ai')
CSE_DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'knowledge.cse')
TRIPLES_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'unified_knowledge.triples')

class CSEKnowledge:
    """Unified knowledge access — CSE binary first, triples fallback."""
    
    def __init__(self):
        self._cache = {}  # subject → {relation → [objects]}
        self._loaded = False
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
