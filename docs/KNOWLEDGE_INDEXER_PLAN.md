# AXIMA Knowledge Indexer — Build Plan

## Goal
Build a fast lookup system that indexes all knowledge files (2.1MB in src/data/)
and enables instant retrieval when user asks a question.

## Current Data Files
```
src/data/
  knowledge.cse          (53KB)  — CSE format triples
  unified_knowledge.triples (134KB) — Subject|Relation|Object triples
  knowledge.dat          (814KB) — Large knowledge dump
  wiki_knowledge.txt     (454KB) — Wikipedia extracted facts
  domain_knowledge.txt   (309KB) — Domain-specific knowledge
  causal_knowledge.json  (87KB)  — Cause-effect relationships
  seed_knowledge.txt     (69KB)  — Base seed facts
  cse_triples.txt        (43KB)  — More triples
  kfr_knowledge.txt      (29KB)  — KFR format knowledge
  kfr_import.txt         (32KB)  — KFR imports
  generated_knowledge.txt (20KB) — Generated facts
  rich_concepts.txt      (8.3KB) — Rich concept descriptions
  world_model.txt        (10KB)  — World model facts
  TOTAL: ~2.1MB
```

## Architecture

```
┌─────────────────────────────────────────────┐
│         KNOWLEDGE INDEXER                     │
├─────────────────────────────────────────────┤
│                                               │
│  STEP 1: PARSER                               │
│    Read ALL data files (any format)           │
│    Normalize to: (subject, relation, object)  │
│    Handle: triples, JSON, plain text, CSE     │
│                                               │
│  STEP 2: ENTITY INDEX                         │
│    For each unique entity → list of facts     │
│    "gravity" → [fact1, fact2, fact3...]       │
│    BM25-style term frequency scoring          │
│                                               │
│  STEP 3: RELATION INDEX                       │
│    For each relation type → list of facts     │
│    "causes" → [fact1, fact2...]              │
│    "is_a" → [fact1, fact2...]               │
│                                               │
│  STEP 4: COMPRESSED BINARY INDEX              │
│    Save as binary for instant load            │
│    Memory-mapped for phone compatibility      │
│    Target: <5MB for all indexes               │
│                                               │
│  STEP 5: QUERY ENGINE                         │
│    Input: "What is gravity?"                  │
│    → Extract keywords: ["gravity"]            │
│    → Search entity index                      │
│    → Rank by relevance (BM25)               │
│    → Return top-K facts                       │
│    Speed target: <10ms per query              │
│                                               │
└─────────────────────────────────────────────┘
```

## File to Create: src/python/knowledge_index.py

```python
class KnowledgeIndex:
    def __init__(self):
        self.facts = []           # All facts as (subj, rel, obj) tuples
        self.entity_index = {}    # entity → [fact_ids]
        self.relation_index = {}  # relation → [fact_ids]
        self.term_index = {}      # word → [fact_ids] (BM25)
    
    def build_from_data(self, data_dir="src/data/"):
        """Parse all files and build indexes."""
        pass
    
    def query(self, question: str, top_k=5) -> List[str]:
        """Find relevant facts for a question."""
        pass
    
    def save(self, path):
        """Save compressed index to disk."""
        pass
    
    def load(self, path):
        """Load pre-built index (instant startup)."""
        pass
```

## Wire into AXIMA Pipeline

```
User: "gravity ante enti"
  → Multilingual: detect Telugu, extract "What is gravity?"
  → KnowledgeIndex.query("gravity") → ["Gravity is the force...", "F=Gm1m2/r^2", ...]
  → ACES: explain the facts in requested mode
  → Shaper: format in user's language
  → Output: real answer with real knowledge
```

## Build Steps

1. Parse all data files into normalized (subject, relation, object) triples
2. Build term index (word → fact_ids) with BM25 scoring
3. Build entity index (entity → all facts about it)
4. Add query method with keyword extraction + ranking
5. Wire into axima.py unified engine
6. Test: "What is gravity?" returns real facts
7. Benchmark: query speed < 10ms

## Success Criteria
- [ ] All 2.1MB of data parsed and indexed
- [ ] Query "gravity" returns relevant gravity facts
- [ ] Query speed < 10ms
- [ ] Works with multilingual pipeline (Telugu/Hindi query → English facts → translated answer)
- [ ] Index loads in < 1 second at startup
