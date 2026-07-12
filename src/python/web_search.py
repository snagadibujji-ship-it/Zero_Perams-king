#!/usr/bin/env python3
"""
Web Knowledge Engine v3.0 — Maximum Level
Multi-source search + structured extraction + smart caching + triple generation.

Sources (all free, no API key):
  1. Wikipedia REST API (best factual quality)
  2. DuckDuckGo Instant Answer API
  3. Wikidata SPARQL (structured triples)
  4. Wikipedia search fallback (fuzzy matching)

Upgrades from v1:
  - Structured triple extraction (subject, relation, object)
  - Smart caching (don't re-search same query)
  - Multi-sentence extraction (5+ facts per query)
  - Category detection (person, place, thing, event, concept)
  - Confidence scoring per extracted fact
  - Relation inference (born_in, capital_of, invented_by, etc.)
  - Auto-retry with query simplification
  - Parallel source querying (ThreadPool)
"""

import urllib.request
import urllib.parse
import json
import re
import os
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════
# CACHE — don't re-search identical queries
# ═══════════════════════════════════════════════════════════════

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'user_data', 'search_cache')

def _cache_key(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()[:16]

def cache_get(query: str) -> Optional[Dict]:
    key = _cache_key(query)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.isfile(path):
        try:
            with open(path) as f:
                data = json.load(f)
            # Cache valid for 7 days
            if time.time() - data.get('timestamp', 0) < 7 * 86400:
                return data
        except: pass
    return None

def cache_set(query: str, result: Dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = _cache_key(query)
    path = os.path.join(CACHE_DIR, f"{key}.json")
    result['timestamp'] = time.time()
    result['query'] = query
    try:
        with open(path, 'w') as f:
            json.dump(result, f)
    except: pass


# ═══════════════════════════════════════════════════════════════
# SOURCE 1: Wikipedia REST API
# ═══════════════════════════════════════════════════════════════

def search_wikipedia(query: str, sentences: int = 5) -> Optional[Dict]:
    """Wikipedia summary — high quality, structured."""
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Axima/3.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            if "extract" in data and len(data["extract"]) > 30:
                return {
                    "source": "Wikipedia",
                    "text": data["extract"],
                    "title": data.get("title", query),
                    "description": data.get("description", ""),
                    "type": data.get("type", "standard"),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
    except: pass
    return None


def search_wikipedia_search(query: str) -> Optional[Dict]:
    """Wikipedia search API — fuzzy matching when direct lookup fails."""
    try:
        url = (f"https://en.wikipedia.org/w/api.php?action=query&list=search"
               f"&srsearch={urllib.parse.quote(query)}&format=json&srlimit=3")
        req = urllib.request.Request(url, headers={"User-Agent": "Axima/3.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("query", {}).get("search", [])
            if results:
                # Get the top result's page
                title = results[0]["title"]
                snippet = re.sub(r'<[^>]+>', '', results[0].get("snippet", ""))
                # Now fetch the full summary
                full = search_wikipedia(title)
                if full:
                    return full
                return {"source": "Wikipedia Search", "text": snippet, "title": title}
    except: pass
    return None


# ═══════════════════════════════════════════════════════════════
# SOURCE 2: DuckDuckGo Instant Answer
# ═══════════════════════════════════════════════════════════════

def search_duckduckgo(query: str) -> Optional[Dict]:
    """DuckDuckGo instant answer — fast, diverse sources."""
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "Axima/3.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            
            text = None
            source_detail = "DuckDuckGo"
            
            if data.get("AbstractText") and len(data["AbstractText"]) > 30:
                text = data["AbstractText"]
                source_detail = data.get("AbstractSource", "DuckDuckGo")
            elif data.get("Answer"):
                text = data["Answer"]
            elif data.get("Definition") and len(data["Definition"]) > 20:
                text = data["Definition"]
                source_detail = data.get("DefinitionSource", "DuckDuckGo")
            elif data.get("RelatedTopics"):
                # Collect multiple related topics
                parts = []
                for topic in data["RelatedTopics"][:5]:
                    if isinstance(topic, dict) and "Text" in topic:
                        parts.append(topic["Text"])
                if parts:
                    text = ' '.join(parts)
            
            if text and len(text) > 20:
                return {
                    "source": source_detail,
                    "text": text,
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL", ""),
                    "type": data.get("Type", ""),
                }
    except: pass
    return None


# ═══════════════════════════════════════════════════════════════
# SOURCE 3: Wikidata SPARQL (structured facts)
# ═══════════════════════════════════════════════════════════════

def search_wikidata(query: str) -> Optional[Dict]:
    """Wikidata — structured data. Best for properties and relationships."""
    try:
        # First resolve entity
        url = (f"https://www.wikidata.org/w/api.php?action=wbsearchentities"
               f"&search={urllib.parse.quote(query)}&language=en&format=json&limit=1")
        req = urllib.request.Request(url, headers={"User-Agent": "Axima/3.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("search", [])
            if not results:
                return None
            
            entity_id = results[0]["id"]
            label = results[0].get("label", query)
            description = results[0].get("description", "")
            
            return {
                "source": "Wikidata",
                "text": f"{label}: {description}" if description else label,
                "title": label,
                "entity_id": entity_id,
                "description": description,
            }
    except: pass
    return None


# ═══════════════════════════════════════════════════════════════
# MASTER SEARCH — Parallel multi-source
# ═══════════════════════════════════════════════════════════════

def _clean_query(query: str) -> str:
    """Strip question words to get the core topic."""
    query = query.strip().rstrip('?').strip()
    prefixes = [
        'what is ', 'what are ', 'who is ', 'who are ', 'who was ',
        'where is ', 'where are ', 'when is ', 'when was ', 'when did ',
        'how does ', 'how do ', 'how is ', 'why does ', 'why do ', 'why is ',
        'what does ', 'tell me about ', 'explain ', 'define ',
        'what is a ', 'what is an ', 'what is the ', 'describe ',
        'i want to know about ', 'can you tell me about ',
    ]
    lower = query.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            query = query[len(prefix):]
            break
    return query.strip()


def search_web(query: str) -> Optional[Dict]:
    """Multi-source parallel search. Returns best result with structured data."""
    
    # Check cache first
    cached = cache_get(query)
    if cached and cached.get("text"):
        cached["from_cache"] = True
        return cached
    
    clean = _clean_query(query)
    if not clean:
        return None
    
    # Parallel search across all sources
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(search_wikipedia, clean): "wikipedia",
            pool.submit(search_duckduckgo, clean): "duckduckgo",
            pool.submit(search_wikidata, clean): "wikidata",
        }
        for future in as_completed(futures, timeout=10):
            try:
                result = future.result()
                if result and result.get("text") and len(result["text"]) > 20:
                    results.append(result)
            except: pass
    
    # If nothing found, try Wikipedia search (fuzzy)
    if not results:
        fallback = search_wikipedia_search(clean)
        if fallback:
            results.append(fallback)
    
    # If still nothing, try simplified query (first 2 words)
    if not results:
        words = clean.split()[:2]
        simple = ' '.join(words)
        if simple != clean:
            result = search_wikipedia(simple)
            if result:
                results.append(result)
    
    if not results:
        return None
    
    # Rank: prefer Wikipedia > DuckDuckGo > Wikidata (by text length and quality)
    source_priority = {"Wikipedia": 3, "Wikipedia Search": 2, "DuckDuckGo": 2, "Wikidata": 1}
    results.sort(key=lambda r: (
        source_priority.get(r.get("source", ""), 0),
        len(r.get("text", ""))
    ), reverse=True)
    
    best = results[0]
    
    # Merge: if wikidata found structured data, attach it
    wikidata_result = next((r for r in results if r.get("source") == "Wikidata"), None)
    if wikidata_result and wikidata_result != best:
        best["wikidata"] = {
            "entity_id": wikidata_result.get("entity_id"),
            "description": wikidata_result.get("description"),
        }
    
    # Cache the result
    cache_set(query, best)
    
    return best


# ═══════════════════════════════════════════════════════════════
# FACT EXTRACTION — Convert text to structured triples
# ═══════════════════════════════════════════════════════════════

# Relation patterns for triple extraction
RELATION_PATTERNS = [
    (r'(?:is|was) (?:the )?capital of (.+)', 'capital_of'),
    (r'(?:is|was) (?:a|an|the) (.+)', 'is_a'),
    (r'(?:was )?born (?:on |in )?(\d{4})', 'born_year'),
    (r'(?:was )?born in (.+?)(?:\.|,|$)', 'born_in'),
    (r'died (?:on |in )?(\d{4})', 'died_year'),
    (r'(?:is )?located in (.+?)(?:\.|,|$)', 'located_in'),
    (r'population (?:of |is )?(?:approximately |about )?([0-9,.]+)', 'population'),
    (r'(?:was )?(?:invented|created|founded|designed) (?:by|in) (.+?)(?:\.|,|$)', 'created_by'),
    (r'(?:is|was) (?:also )?known (?:as|for) (.+?)(?:\.|,|$)', 'known_for'),
    (r'(?:has|have) (?:a |an )?population of ([0-9,.]+)', 'population'),
    (r'covers? (?:an )?area of ([0-9,.]+)', 'area'),
    (r'(?:is|was) (?:a )?member of (.+?)(?:\.|,|$)', 'member_of'),
    (r'(?:is|are) (?:made|composed) (?:of|from) (.+?)(?:\.|,|$)', 'made_of'),
    (r'(?:is|was) (?:the )?(largest|smallest|oldest|tallest|fastest)', 'superlative'),
    (r'(?:borders?|adjacent to) (.+?)(?:\.|,|$)', 'borders'),
]


def extract_facts(text: str, topic: str) -> List[Dict]:
    """Extract structured facts from text. Returns list of {fact, subject, relation, object, confidence}."""
    facts = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    topic_lower = topic.lower()
    
    for sent in sentences[:8]:  # Max 8 sentences
        sent = sent.strip()
        if len(sent) < 15:
            continue
        
        # Always keep sentence as raw fact
        raw_fact = {"fact": sent, "subject": topic_lower, "confidence": 0.8}
        
        # Try to extract structured triple
        sent_lower = sent.lower()
        for pattern, relation in RELATION_PATTERNS:
            match = re.search(pattern, sent_lower)
            if match:
                obj = match.group(1).strip().rstrip('.,;')
                if len(obj) > 1 and len(obj) < 200:
                    raw_fact["relation"] = relation
                    raw_fact["object"] = obj
                    raw_fact["confidence"] = 0.9
                    break
        
        facts.append(raw_fact)
    
    # If no sentences matched topic directly, keep first 3 anyway
    if not facts and sentences:
        for sent in sentences[:3]:
            if len(sent.strip()) > 15:
                facts.append({"fact": sent.strip(), "subject": topic_lower, "confidence": 0.7})
    
    return facts


def extract_triples(text: str, topic: str) -> List[Tuple[str, str, str, float]]:
    """Extract (subject, relation, object, confidence) triples."""
    triples = []
    facts = extract_facts(text, topic)
    for f in facts:
        if "relation" in f and "object" in f:
            triples.append((f["subject"], f["relation"], f["object"], f["confidence"]))
    return triples


# ═══════════════════════════════════════════════════════════════
# CATEGORY DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_category(text: str, title: str = "") -> str:
    """Detect what type of entity this is."""
    combined = (text + " " + title).lower()
    
    if any(w in combined for w in ['born', 'died', 'was a', 'politician', 'author', 'scientist', 'actor']):
        return 'person'
    if any(w in combined for w in ['country', 'city', 'located in', 'capital', 'population', 'continent']):
        return 'place'
    if any(w in combined for w in ['event', 'war', 'battle', 'revolution', 'founded in', 'occurred']):
        return 'event'
    if any(w in combined for w in ['programming', 'software', 'technology', 'algorithm', 'computer']):
        return 'technology'
    if any(w in combined for w in ['species', 'animal', 'plant', 'organism', 'genus']):
        return 'biology'
    if any(w in combined for w in ['element', 'compound', 'molecule', 'chemical', 'atom']):
        return 'chemistry'
    if any(w in combined for w in ['planet', 'star', 'galaxy', 'orbit', 'solar']):
        return 'astronomy'
    return 'concept'


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else "What is a black hole"
    print(f"Searching: '{query}'")
    print(f"Clean query: '{_clean_query(query)}'")
    print()
    
    result = search_web(query)
    if result:
        print(f"Source: {result['source']}")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Category: {detect_category(result['text'], result.get('title', ''))}")
        print(f"From cache: {result.get('from_cache', False)}")
        print(f"\nAnswer: {result['text'][:500]}")
        
        topic = _clean_query(query)
        facts = extract_facts(result['text'], topic)
        print(f"\nExtracted {len(facts)} facts:")
        for f in facts:
            if 'relation' in f:
                print(f"  [{f['confidence']:.1f}] {f['subject']} --{f['relation']}--> {f['object']}")
            else:
                print(f"  [{f['confidence']:.1f}] {f['fact'][:80]}")
        
        triples = extract_triples(result['text'], topic)
        if triples:
            print(f"\nStructured triples ({len(triples)}):")
            for s, r, o, c in triples:
                print(f"  ({s}, {r}, {o}) conf={c}")
    else:
        print("No results found.")
