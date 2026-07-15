#!/usr/bin/env python3
"""
AXIMA Knowledge Indexer — Fast Full-Text Search + Relation-Aware Queries + Graph Traversal
Built by: Ghias + Kiro | July 2026

Features:
  - BM25 inverted index for full-text search (<10ms per query)
  - Relation-aware queries ("what causes X" → search cause edges)
  - Synonym expansion from knowledge itself
  - Graph traversal (2-3 hop inference)
  - Source quality weighting (wiki > domain > generated)
  - Incremental indexing (append without rebuild)

Indexes ALL data in src/data/ (~2.1MB):
  - unified_knowledge.triples (pipe-delimited)
  - cse_triples.txt (pipe-delimited)
  - causal_knowledge.json (JSON objects)
  - wiki_knowledge.txt (natural language sentences)
  - domain_knowledge.txt (term definitions)
  - seed_knowledge.txt (simple "X is Y" sentences)
  - generated_knowledge.txt, rich_concepts.txt, world_model.txt, etc.
"""

import os
import re
import json
import math
import time
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field


DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Source quality tiers (higher = more trusted)
SOURCE_WEIGHTS = {
    'wiki': 1.0,          # Wikipedia — community verified
    'domain': 0.9,        # Domain-specific expert knowledge
    'causal': 0.85,       # Causal knowledge (structured)
    'seed': 0.8,          # Seed facts (basic truths)
    'cse': 0.8,           # CSE triples (structured)
    'generated': 0.6,     # Generated knowledge (less verified)
    'rich': 0.7,          # Rich concepts
    'world': 0.7,         # World model
    'unknown': 0.5,       # Unknown source
}

# Stopwords for BM25 (minimal set — we don't want to filter too much)
STOPWORDS = frozenset([
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'and', 'but', 'or', 'nor', 'not', 'so', 'yet',
    'both', 'either', 'neither', 'each', 'every', 'all', 'any', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same',
    'than', 'too', 'very', 'just', 'also', 'it', 'its', 'this', 'that',
])

# Relation keywords for relation-aware search
RELATION_KEYWORDS = {
    'causes': ['cause', 'causes', 'caused', 'why', 'because', 'reason', 'leads'],
    'is_a': ['is', 'type', 'kind', 'category', 'class', 'what is'],
    'has_property': ['has', 'have', 'property', 'feature', 'characteristic'],
    'located_in': ['where', 'location', 'located', 'found', 'lives', 'country', 'city'],
    'part_of': ['part', 'component', 'belongs', 'member', 'contains'],
    'description': ['describe', 'explain', 'what', 'definition', 'meaning', 'about'],
    'melts_at': ['melts', 'melting', 'melt point', 'temperature'],
    'boils_at': ['boils', 'boiling', 'boil point', 'evaporate'],
}



@dataclass
class Fact:
    """A single knowledge fact."""
    subject: str
    relation: str
    obj: str
    confidence: int = 80
    source: str = 'unknown'
    fact_id: int = 0

    def as_text(self) -> str:
        """Convert to natural language representation."""
        if self.relation == 'description':
            return f"{self.subject}: {self.obj}"
        elif self.relation == 'is_a':
            return f"{self.subject} is a {self.obj}"
        elif self.relation == 'has_property':
            return f"{self.subject} has {self.obj}"
        elif self.relation == 'located_in':
            return f"{self.subject} is located in {self.obj}"
        elif self.relation == 'causes':
            return f"{self.subject} causes {self.obj}"
        elif self.relation == 'melts_at':
            return f"{self.subject} melts at {self.obj}°C"
        elif self.relation == 'boils_at':
            return f"{self.subject} boils at {self.obj}°C"
        elif self.relation == 'part_of':
            return f"{self.subject} is part of {self.obj}"
        else:
            return f"{self.subject} {self.relation} {self.obj}"



class KnowledgeIndex:
    """
    Fast knowledge retrieval engine.
    BM25 inverted index + relation index + entity index + graph traversal.
    """

    def __init__(self):
        self.facts: List[Fact] = []
        self.entity_index: Dict[str, List[int]] = defaultdict(list)   # entity → [fact_ids]
        self.relation_index: Dict[str, List[int]] = defaultdict(list)  # relation → [fact_ids]
        self.term_index: Dict[str, List[int]] = defaultdict(list)      # word → [fact_ids]
        self.synonym_map: Dict[str, Set[str]] = defaultdict(set)       # word → synonyms
        self.adjacency: Dict[str, List[int]] = defaultdict(list)       # entity → [fact_ids as edges]
        # BM25 params
        self.k1 = 1.5
        self.b = 0.75
        self.avg_doc_len = 0
        self.doc_count = 0
        self.doc_lengths: Dict[int, int] = {}
        self.df: Dict[str, int] = defaultdict(int)  # document frequency per term
        self._built = False

    def build(self, data_dir: str = None):
        """Parse all data files and build all indexes."""
        if data_dir is None:
            data_dir = DATA_DIR
        t0 = time.time()

        # Parse all files
        self._parse_triples(os.path.join(data_dir, 'unified_knowledge.triples'), 'seed')
        self._parse_triples(os.path.join(data_dir, 'cse_triples.txt'), 'cse')
        self._parse_causal_json(os.path.join(data_dir, 'causal_knowledge.json'))
        self._parse_text_file(os.path.join(data_dir, 'wiki_knowledge.txt'), 'wiki')
        self._parse_definitions(os.path.join(data_dir, 'domain_knowledge.txt'), 'domain')
        self._parse_simple(os.path.join(data_dir, 'seed_knowledge.txt'), 'seed')
        self._parse_text_file(os.path.join(data_dir, 'generated_knowledge.txt'), 'generated')
        self._parse_text_file(os.path.join(data_dir, 'rich_concepts.txt'), 'rich')
        self._parse_text_file(os.path.join(data_dir, 'world_model.txt'), 'world')
        self._parse_triples(os.path.join(data_dir, 'kfr_knowledge.txt'), 'generated')
        self._parse_triples(os.path.join(data_dir, 'kfr_import.txt'), 'generated')

        # Build indexes
        self._build_indexes()
        self._build_synonyms()
        self._built = True

        elapsed = (time.time() - t0) * 1000
        return {'facts': len(self.facts), 'entities': len(self.entity_index),
                'terms': len(self.term_index), 'build_ms': round(elapsed, 1)}


    # ═══════════════════════════════════════════════════════════════
    # PARSERS — Handle all data formats
    # ═══════════════════════════════════════════════════════════════

    def _parse_triples(self, filepath: str, source: str):
        """Parse pipe-delimited triple files: subject|relation|object|confidence"""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('|')
                if len(parts) >= 3:
                    subj = parts[0].strip().lower()
                    rel = parts[1].strip().lower()
                    obj = parts[2].strip()
                    conf = int(parts[3]) if len(parts) > 3 and parts[3].strip().isdigit() else 80
                    self._add_fact(subj, rel, obj, conf, source)

    def _parse_causal_json(self, filepath: str):
        """Parse causal_knowledge.json: {entity: {property: value, ...}, ...}"""
        if not os.path.exists(filepath):
            return
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            for entity, props in data.items():
                entity_lower = entity.lower()
                for prop, value in props.items():
                    if prop == 'category':
                        self._add_fact(entity_lower, 'is_a', str(value), 85, 'causal')
                    elif prop == 'state':
                        self._add_fact(entity_lower, 'has_state', str(value), 90, 'causal')
                    elif prop == 'melt_temp':
                        self._add_fact(entity_lower, 'melts_at', str(value), 95, 'causal')
                    elif prop == 'boil_temp':
                        self._add_fact(entity_lower, 'boils_at', str(value), 95, 'causal')
                    elif prop == 'cook_temp':
                        self._add_fact(entity_lower, 'cooks_at', str(value), 90, 'causal')
                    elif isinstance(value, bool) and value:
                        self._add_fact(entity_lower, f'is_{prop}', 'true', 90, 'causal')
        except (json.JSONDecodeError, IOError):
            pass


    def _parse_text_file(self, filepath: str, source: str):
        """Parse natural language text files — each line becomes a description fact."""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or len(line) < 10:
                    continue
                # Try to extract subject from first clause
                subject = self._extract_subject(line)
                if subject:
                    self._add_fact(subject, 'description', line, 75, source)
                else:
                    # Store with generic subject derived from first words
                    words = line.split()[:3]
                    subj = ' '.join(words).lower().rstrip(',.')
                    self._add_fact(subj, 'description', line, 70, source)

    def _parse_definitions(self, filepath: str, source: str):
        """Parse domain definitions: 'term is definition' format."""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Format: "term is definition"
                match = re.match(r'^(.+?)\s+is\s+(.+)$', line, re.IGNORECASE)
                if match:
                    term = match.group(1).strip().lower()
                    defn = match.group(2).strip()
                    self._add_fact(term, 'description', defn, 85, source)
                else:
                    # Fallback: first word/phrase is subject
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        self._add_fact(parts[0].lower(), 'description', parts[1], 75, source)

    def _parse_simple(self, filepath: str, source: str):
        """Parse simple 'X is a Y' sentences."""
        if not os.path.exists(filepath):
            return
        with open(filepath, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # "A dog is a mammal" → (dog, is_a, mammal)
                match = re.match(r'^(?:A|An|The)?\s*(.+?)\s+is\s+(?:a|an)\s+(.+)$', line, re.I)
                if match:
                    subj = match.group(1).strip().lower()
                    obj = match.group(2).strip().lower()
                    self._add_fact(subj, 'is_a', obj, 85, source)
                else:
                    # "X has Y" pattern
                    match = re.match(r'^(?:A|An|The)?\s*(.+?)\s+(?:has|have)\s+(.+)$', line, re.I)
                    if match:
                        subj = match.group(1).strip().lower()
                        obj = match.group(2).strip().lower()
                        self._add_fact(subj, 'has_property', obj, 80, source)


    def _extract_subject(self, text: str) -> Optional[str]:
        """Extract the subject entity from a sentence."""
        # Try common patterns
        patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # Proper noun at start
            r'^The\s+(.+?)\s+(?:is|are|was|were|has|have)\b',
            r'^([A-Za-z]+(?:\s+[a-z]+)?)\s+(?:is|are)\b',
        ]
        for pat in patterns:
            m = re.match(pat, text)
            if m:
                subj = m.group(1).strip().lower()
                if len(subj) > 2 and subj not in STOPWORDS:
                    return subj
        return None

    def _add_fact(self, subject: str, relation: str, obj: str, confidence: int, source: str):
        """Add a fact to the store."""
        fact_id = len(self.facts)
        fact = Fact(subject=subject, relation=relation, obj=obj,
                   confidence=confidence, source=source, fact_id=fact_id)
        self.facts.append(fact)

    # ═══════════════════════════════════════════════════════════════
    # INDEX BUILDING
    # ═══════════════════════════════════════════════════════════════

    def _build_indexes(self):
        """Build all indexes from parsed facts."""
        total_len = 0
        for fact in self.facts:
            fid = fact.fact_id
            # Entity index
            self.entity_index[fact.subject].append(fid)
            obj_lower = fact.obj.lower()
            if len(obj_lower) < 50:  # Don't index long descriptions as entities
                self.entity_index[obj_lower].append(fid)
            # Relation index
            self.relation_index[fact.relation].append(fid)
            # Adjacency (graph edges)
            self.adjacency[fact.subject].append(fid)
            # Term index (BM25)
            text = f"{fact.subject} {fact.relation} {fact.obj}".lower()
            terms = self._tokenize(text)
            self.doc_lengths[fid] = len(terms)
            total_len += len(terms)
            seen_terms = set()
            for term in terms:
                self.term_index[term].append(fid)
                if term not in seen_terms:
                    self.df[term] += 1
                    seen_terms.add(term)

        self.doc_count = len(self.facts)
        self.avg_doc_len = total_len / max(self.doc_count, 1)


    def _build_synonyms(self):
        """Build synonym map from knowledge itself (if 'car is_a automobile' → link them)."""
        # From is_a relationships: if A is_a B, they share meaning
        for fact in self.facts:
            if fact.relation == 'is_a':
                self.synonym_map[fact.subject].add(fact.obj.lower())
                self.synonym_map[fact.obj.lower()].add(fact.subject)
            # From description containing "also known as"
            elif fact.relation == 'description':
                m = re.search(r'also (?:known|called) as (.+?)(?:\.|,|$)', fact.obj, re.I)
                if m:
                    alias = m.group(1).strip().lower()
                    self.synonym_map[fact.subject].add(alias)
                    self.synonym_map[alias].add(fact.subject)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing/querying."""
        text = text.lower()
        # Split on non-alphanumeric
        tokens = re.findall(r'[a-z0-9]+', text)
        # Filter stopwords for BM25
        return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    # ═══════════════════════════════════════════════════════════════
    # QUERY ENGINE
    # ═══════════════════════════════════════════════════════════════

    def query(self, question: str, top_k: int = 10) -> List[Tuple[Fact, float]]:
        """
        Main query method. Returns ranked list of (fact, score).
        Combines: BM25 text search + relation-aware boost + source weighting.
        """
        if not self._built:
            self.build()

        question_lower = question.lower()
        terms = self._tokenize(question_lower)
        if not terms:
            return []

        # Expand with synonyms
        expanded_terms = set(terms)
        for t in terms:
            if t in self.synonym_map:
                expanded_terms.update(self.synonym_map[t])

        # Detect target relation from question
        target_relation = self._detect_relation(question_lower)

        # Score all candidate facts
        candidates: Dict[int, float] = defaultdict(float)

        # BM25 scoring
        for term in expanded_terms:
            if term not in self.term_index:
                continue
            idf = self._idf(term)
            for fid in self.term_index[term]:
                tf = self.term_index[term].count(fid) if len(self.term_index[term]) < 1000 else 1
                dl = self.doc_lengths.get(fid, self.avg_doc_len)
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_len))
                candidates[fid] += idf * tf_norm

        # Entity exact match boost
        for term in terms:
            if term in self.entity_index:
                for fid in self.entity_index[term]:
                    candidates[fid] += 3.0  # Strong boost for exact entity match

        # Relation boost
        if target_relation and target_relation in self.relation_index:
            for fid in self.relation_index[target_relation]:
                if fid in candidates:
                    candidates[fid] *= 1.5  # 50% boost for matching relation

        # Source quality weighting
        scored = []
        for fid, score in candidates.items():
            fact = self.facts[fid]
            source_weight = SOURCE_WEIGHTS.get(fact.source, 0.5)
            conf_weight = fact.confidence / 100.0
            final_score = score * source_weight * conf_weight
            scored.append((fact, final_score))

        # Sort by score descending
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]


    def query_entity(self, entity: str, relation: str = None, top_k: int = 20) -> List[Fact]:
        """Direct entity lookup — O(1). Returns all facts about an entity."""
        if not self._built:
            self.build()
        entity_lower = entity.lower()
        fact_ids = self.entity_index.get(entity_lower, [])
        results = []
        for fid in fact_ids:
            fact = self.facts[fid]
            if fact.subject == entity_lower:
                if relation is None or fact.relation == relation:
                    results.append(fact)
        # Sort by confidence
        results.sort(key=lambda f: -f.confidence)
        return results[:top_k]

    def query_relation(self, relation: str, top_k: int = 50) -> List[Fact]:
        """Get all facts with a specific relation type."""
        if not self._built:
            self.build()
        fact_ids = self.relation_index.get(relation, [])
        results = [self.facts[fid] for fid in fact_ids[:top_k]]
        return results

    def graph_traverse(self, start_entity: str, max_hops: int = 3, 
                       relation_filter: str = None) -> List[Tuple[Fact, int]]:
        """
        Graph traversal from an entity. Returns (fact, hop_distance).
        Follows edges up to max_hops.
        """
        if not self._built:
            self.build()
        start = start_entity.lower()
        visited = set()
        results = []
        frontier = [(start, 0)]

        while frontier:
            entity, depth = frontier.pop(0)
            if entity in visited or depth > max_hops:
                continue
            visited.add(entity)

            for fid in self.adjacency.get(entity, []):
                fact = self.facts[fid]
                if relation_filter and fact.relation != relation_filter:
                    continue
                results.append((fact, depth))
                # Add object as next frontier node
                obj_lower = fact.obj.lower()
                if obj_lower not in visited and len(obj_lower) < 40:
                    frontier.append((obj_lower, depth + 1))

        return results

    def get_words_for_topic(self, topic: str, max_words: int = 30) -> List[str]:
        """
        Get associated words for a topic — used by Creator V2 Word Harvester.
        Returns words from knowledge that are related to the topic.
        """
        if not self._built:
            self.build()
        words = set()
        topic_lower = topic.lower()

        # Direct entity facts
        for fact in self.query_entity(topic_lower, top_k=10):
            # Extract words from objects
            obj_words = re.findall(r'[a-z]+', fact.obj.lower())
            words.update(w for w in obj_words if w not in STOPWORDS and len(w) > 2)

        # BM25 search for related
        results = self.query(topic, top_k=15)
        for fact, score in results:
            obj_words = re.findall(r'[a-z]+', fact.obj.lower())
            subj_words = re.findall(r'[a-z]+', fact.subject)
            words.update(w for w in obj_words if w not in STOPWORDS and len(w) > 2)
            words.update(w for w in subj_words if w not in STOPWORDS and len(w) > 2)

        # Graph traversal 1-hop for more context
        for fact, hop in self.graph_traverse(topic_lower, max_hops=1):
            obj_words = re.findall(r'[a-z]+', fact.obj.lower())
            words.update(w for w in obj_words if w not in STOPWORDS and len(w) > 2)

        # Remove the topic itself
        topic_words = set(re.findall(r'[a-z]+', topic_lower))
        words -= topic_words

        return list(words)[:max_words]


    # ═══════════════════════════════════════════════════════════════
    # INCREMENTAL INDEXING
    # ═══════════════════════════════════════════════════════════════

    def add_fact(self, subject: str, relation: str, obj: str,
                 confidence: int = 80, source: str = 'unknown'):
        """Add a single fact incrementally without rebuilding."""
        fid = len(self.facts)
        fact = Fact(subject=subject.lower(), relation=relation, obj=obj,
                   confidence=confidence, source=source, fact_id=fid)
        self.facts.append(fact)

        # Update entity index
        self.entity_index[fact.subject].append(fid)
        obj_lower = fact.obj.lower()
        if len(obj_lower) < 50:
            self.entity_index[obj_lower].append(fid)

        # Update relation index
        self.relation_index[fact.relation].append(fid)

        # Update adjacency
        self.adjacency[fact.subject].append(fid)

        # Update term index
        text = f"{fact.subject} {fact.relation} {fact.obj}".lower()
        terms = self._tokenize(text)
        self.doc_lengths[fid] = len(terms)
        self.doc_count += 1
        for term in terms:
            self.term_index[term].append(fid)
            self.df[term] += 1

        # Update avg doc len
        total = sum(self.doc_lengths.values())
        self.avg_doc_len = total / max(self.doc_count, 1)

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _idf(self, term: str) -> float:
        """Inverse document frequency for BM25."""
        n = self.df.get(term, 0)
        if n == 0:
            return 0
        return math.log((self.doc_count - n + 0.5) / (n + 0.5) + 1)

    def _detect_relation(self, question: str) -> Optional[str]:
        """Detect which relation the question is asking about."""
        for relation, keywords in RELATION_KEYWORDS.items():
            for kw in keywords:
                if kw in question:
                    return relation
        return None

    def stats(self) -> Dict:
        """Return index statistics."""
        return {
            'facts': len(self.facts),
            'entities': len(self.entity_index),
            'relations': len(self.relation_index),
            'terms': len(self.term_index),
            'synonyms': sum(len(v) for v in self.synonym_map.values()),
            'built': self._built,
        }


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_instance: Optional[KnowledgeIndex] = None

def get_index() -> KnowledgeIndex:
    """Get or create the singleton knowledge index."""
    global _instance
    if _instance is None:
        _instance = KnowledgeIndex()
        _instance.build()
    return _instance



# ═══════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ AXIMA Knowledge Indexer — Build & Test ═══\n")

    idx = KnowledgeIndex()
    result = idx.build()
    print(f"  Built in {result['build_ms']}ms")
    print(f"  Facts:    {result['facts']}")
    print(f"  Entities: {result['entities']}")
    print(f"  Terms:    {result['terms']}")
    print()

    # Test queries
    test_queries = [
        "What is gravity?",
        "What is iron?",
        "What melts at high temperature?",
        "What is a dog?",
        "Where is Paris?",
        "What causes rain?",
        "What properties does gold have?",
    ]

    for q in test_queries:
        t0 = time.time()
        results = idx.query(q, top_k=3)
        elapsed = (time.time() - t0) * 1000
        print(f"  Q: {q}")
        print(f"     ({elapsed:.2f}ms, {len(results)} results)")
        for fact, score in results:
            print(f"     [{score:.2f}] {fact.as_text()[:80]}")
        print()

    # Test entity lookup
    print("  --- Entity Lookup ---")
    for entity in ['iron', 'dog', 'water']:
        facts = idx.query_entity(entity, top_k=5)
        print(f"  {entity}: {len(facts)} facts")
        for f in facts[:3]:
            print(f"    {f.relation} = {f.obj[:50]}")
        print()

    # Test graph traversal
    print("  --- Graph Traversal (iron, 2 hops) ---")
    for fact, hop in idx.graph_traverse('iron', max_hops=2)[:8]:
        print(f"    [hop {hop}] {fact.subject} → {fact.relation} → {fact.obj[:40]}")
    print()

    # Test word harvesting (for Creator V2)
    print("  --- Word Harvester (topic: 'cooking') ---")
    words = idx.get_words_for_topic('cooking')
    print(f"    Words: {words[:15]}")
    print()

    print("  ✅ Knowledge Indexer ready!")
