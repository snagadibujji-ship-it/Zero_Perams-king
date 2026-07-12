#!/usr/bin/env python3
"""
Auto-Learn Engine v3.0 — Maximum Level

When AI hits a knowledge gap:
  1. Searches web (Wikipedia + DuckDuckGo + Wikidata — parallel)
  2. Extracts structured triples (subject, relation, object)
  3. Validates facts (contradiction check, confidence scoring)
  4. Saves to persistent knowledge (both text + triples format)
  5. Feeds into C engine on next rebuild
  6. Tracks learning history + statistics

Growth: every gap filled = 3-8 new facts permanently stored.
After 100 conversations: ~500-1000 new facts learned organically.
"""

import os
import sys
import json
import time
import re

sys.path.insert(0, os.path.dirname(__file__))
from web_search import extract_facts, extract_triples, detect_category, _clean_query
try:
    from online_search import search_web
except ImportError:
    from web_search import search_web

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
LEARNED_FILE = os.path.join(DATA_DIR, 'web_learned.txt')
TRIPLES_FILE = os.path.join(DATA_DIR, 'learned_triples.jsonl')
STATS_FILE = os.path.join(DATA_DIR, 'learn_stats.json')
HISTORY_FILE = os.path.join(DATA_DIR, 'learn_history.jsonl')


class AutoLearnEngine:
    """Manages all knowledge acquisition from web sources."""
    
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.stats = self._load_stats()
        self._known_facts = self._load_known_hashes()
    
    def _load_stats(self) -> Dict:
        try:
            if os.path.isfile(STATS_FILE):
                with open(STATS_FILE) as f:
                    return json.load(f)
        except: pass
        return {
            'total_searches': 0,
            'successful_searches': 0,
            'facts_saved': 0,
            'triples_saved': 0,
            'topics_learned': [],
            'sources': {'Wikipedia': 0, 'DuckDuckGo': 0, 'Wikidata': 0},
            'categories': {},
            'last_search': None,
        }
    
    def _save_stats(self):
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except: pass
    
    def _load_known_hashes(self) -> set:
        """Load hashes of already-known facts to avoid duplicates."""
        hashes = set()
        if os.path.isfile(LEARNED_FILE):
            try:
                with open(LEARNED_FILE) as f:
                    for line in f:
                        hashes.add(hash(line.strip().lower()))
            except: pass
        return hashes
    
    def _is_duplicate(self, fact: str) -> bool:
        h = hash(fact.strip().lower())
        if h in self._known_facts:
            return True
        self._known_facts.add(h)
        return False
    
    # ═══════════════════════════════════════════════════════════
    # MAIN API
    # ═══════════════════════════════════════════════════════════
    
    def offer_search(self, query: str) -> Optional[Dict]:
        """Search web for a query. Returns structured result or None."""
        self.stats['total_searches'] += 1
        self.stats['last_search'] = query
        
        result = search_web(query)
        if not result or not result.get("text"):
            self._save_stats()
            return None
        
        self.stats['successful_searches'] += 1
        source = result.get('source', 'Unknown')
        self.stats['sources'][source] = self.stats['sources'].get(source, 0) + 1
        
        # Extract structured data
        topic = _clean_query(query)
        facts = extract_facts(result['text'], topic)
        triples = extract_triples(result['text'], topic)
        category = detect_category(result['text'], result.get('title', ''))
        
        self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
        self._save_stats()
        
        return {
            "answer": result["text"],
            "source": source,
            "title": result.get("title", topic),
            "url": result.get("url", ""),
            "facts": facts,
            "triples": triples,
            "category": category,
            "topic": topic,
            "from_cache": result.get("from_cache", False),
        }
    
    def save_learned(self, result: Dict) -> int:
        """Save learned facts permanently with KDA compression."""
        if not result:
            return 0
        
        facts = result.get("facts", [])
        triples = result.get("triples", [])
        topic = result.get("topic", "unknown")
        source = result.get("source", "web")
        
        saved_count = 0
        
        # ═══ KDA INTEGRATION: Save via Knowledge Distillation by Abstraction ═══
        try:
            from kda_manager import save_with_kda, save_batch_with_kda
            
            # Save structured triples through KDA (compressed)
            if triples:
                kda_triples = [(s, r, o, int(c * 100)) for s, r, o, c in triples]
                kda_result = save_batch_with_kda(kda_triples)
                saved_count += sum(v for k, v in kda_result.items() if k != 'duplicate')
            
            # Extract triples from raw facts and save via KDA
            for fact_dict in facts:
                if isinstance(fact_dict, dict) and 'relation' in fact_dict and 'object' in fact_dict:
                    save_with_kda(
                        fact_dict.get('subject', topic),
                        fact_dict['relation'],
                        fact_dict['object'],
                        int(fact_dict.get('confidence', 0.85) * 100)
                    )
                    saved_count += 1
        except ImportError:
            pass  # KDA not available, fall through to legacy
        
        # Legacy: Save raw text facts (backward compatible)
        with open(LEARNED_FILE, 'a') as f:
            for fact_dict in facts:
                fact_text = fact_dict.get("fact", "") if isinstance(fact_dict, dict) else str(fact_dict)
                if fact_text and len(fact_text) > 10 and not self._is_duplicate(fact_text):
                    f.write(fact_text.strip().rstrip('.') + '\n')
        
        # Save structured triples to JSONL (for CSE import)
        if triples:
            with open(TRIPLES_FILE, 'a') as f:
                for subj, rel, obj, conf in triples:
                    entry = {"subject": subj, "relation": rel, "object": obj,
                             "confidence": conf, "source": source, "timestamp": time.time()}
                    f.write(json.dumps(entry) + '\n')
            self.stats['triples_saved'] += len(triples)
        
        # Log + stats
        self._log_history(topic, source, saved_count, len(triples))
        self.stats['facts_saved'] += saved_count
        if topic not in self.stats['topics_learned']:
            self.stats['topics_learned'].append(topic)
            if len(self.stats['topics_learned']) > 500:
                self.stats['topics_learned'] = self.stats['topics_learned'][-500:]
        self._save_stats()
        return saved_count
    
    def _log_history(self, topic: str, source: str, facts: int, triples: int):
        """Log learning event for analytics."""
        try:
            with open(HISTORY_FILE, 'a') as f:
                entry = {
                    "timestamp": time.time(),
                    "topic": topic,
                    "source": source,
                    "facts_saved": facts,
                    "triples_saved": triples,
                }
                f.write(json.dumps(entry) + '\n')
        except: pass
    
    # ═══════════════════════════════════════════════════════════
    # BULK LEARNING
    # ═══════════════════════════════════════════════════════════
    
    def bulk_learn(self, topics: List[str], auto_save: bool = True) -> Dict:
        """Learn about multiple topics at once. Great for bootstrapping."""
        results = {'searched': 0, 'found': 0, 'saved': 0, 'failed': []}
        
        for topic in topics:
            results['searched'] += 1
            result = self.offer_search(topic)
            if result:
                results['found'] += 1
                if auto_save:
                    n = self.save_learned(result)
                    results['saved'] += n
            else:
                results['failed'].append(topic)
            
            # Rate limit: 1 request per second
            time.sleep(1.0)
        
        return results
    
    def bootstrap_essentials(self) -> Dict:
        """Learn the most commonly asked topics. Run once on first install."""
        essential_topics = [
            # Countries & capitals
            "France", "Japan", "Germany", "Brazil", "India", "China",
            "United Kingdom", "Australia", "Canada", "Russia",
            # Science
            "photosynthesis", "gravity", "DNA", "evolution", "black hole",
            "quantum mechanics", "speed of light", "periodic table",
            # Technology
            "Python programming", "artificial intelligence", "internet",
            "blockchain", "machine learning",
            # History
            "World War 2", "French Revolution", "Industrial Revolution",
            "Ancient Rome", "Space Race",
            # People
            "Albert Einstein", "Isaac Newton", "Marie Curie",
            "Leonardo da Vinci", "Nikola Tesla",
        ]
        return self.bulk_learn(essential_topics)
    
    # ═══════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════
    
    def get_stats(self) -> Dict:
        """Return learning statistics."""
        return {
            **self.stats,
            'total_known_facts': get_learned_count(),
            'total_triples': self._count_triples(),
            'success_rate': (self.stats['successful_searches'] / max(1, self.stats['total_searches'])) * 100,
        }
    
    def _count_triples(self) -> int:
        if os.path.isfile(TRIPLES_FILE):
            try:
                with open(TRIPLES_FILE) as f:
                    return sum(1 for _ in f)
            except: pass
        return 0


# ═══════════════════════════════════════════════════════════════
# LEGACY API (backward compatible with old auto_learn.py)
# ═══════════════════════════════════════════════════════════════

_engine = None

def _get_engine():
    global _engine
    if _engine is None:
        _engine = AutoLearnEngine()
    return _engine

def offer_search(query: str) -> Optional[Dict]:
    """Legacy API: search web for query."""
    return _get_engine().offer_search(query)

def save_facts(facts) -> int:
    """Legacy API: save facts list."""
    if isinstance(facts, list) and facts:
        # Convert old-style list of strings to new format
        if isinstance(facts[0], str):
            result = {"facts": [{"fact": f} for f in facts], "topic": "unknown", "source": "web"}
        else:
            result = {"facts": facts, "topic": "unknown", "source": "web"}
        return _get_engine().save_learned(result)
    return 0

def get_learned_count() -> int:
    """How many web-learned facts stored."""
    if os.path.isfile(LEARNED_FILE):
        try:
            with open(LEARNED_FILE) as f:
                return sum(1 for line in f if line.strip())
        except: pass
    return 0


# ═══════════════════════════════════════════════════════════════
# TYPE ANNOTATIONS (for older Python)
# ═══════════════════════════════════════════════════════════════

from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    engine = AutoLearnEngine()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'bootstrap':
            print("Bootstrapping essential knowledge...")
            result = engine.bootstrap_essentials()
            print(f"Done: searched {result['searched']}, found {result['found']}, saved {result['saved']} facts")
            if result['failed']:
                print(f"Failed: {', '.join(result['failed'][:10])}")
        elif sys.argv[1] == 'stats':
            stats = engine.get_stats()
            print(f"Learning Statistics:")
            print(f"  Total searches:   {stats['total_searches']}")
            print(f"  Successful:       {stats['successful_searches']} ({stats['success_rate']:.0f}%)")
            print(f"  Facts saved:      {stats['facts_saved']}")
            print(f"  Triples saved:    {stats['triples_saved']}")
            print(f"  Total known:      {stats['total_known_facts']}")
            print(f"  Topics learned:   {len(stats['topics_learned'])}")
            print(f"  Top sources:      {stats['sources']}")
            print(f"  Categories:       {stats['categories']}")
        elif sys.argv[1] == 'learn':
            topics = sys.argv[2:]
            if topics:
                result = engine.bulk_learn(topics)
                print(f"Learned: {result['saved']} facts from {result['found']}/{result['searched']} topics")
            else:
                print("Usage: python auto_learn.py learn topic1 topic2 ...")
        else:
            query = ' '.join(sys.argv[1:])
            result = engine.offer_search(query)
            if result:
                print(f"[{result['source']}] {result['answer'][:300]}")
                print(f"\nCategory: {result['category']}")
                print(f"Facts: {len(result['facts'])}, Triples: {len(result['triples'])}")
                n = engine.save_learned(result)
                print(f"Auto-saved: {n} facts")
            else:
                print("Not found.")
    else:
        print("Usage:")
        print("  python auto_learn.py <query>        — Search and save")
        print("  python auto_learn.py bootstrap      — Learn essential topics")
        print("  python auto_learn.py learn t1 t2    — Bulk learn topics")
        print("  python auto_learn.py stats          — Show statistics")
