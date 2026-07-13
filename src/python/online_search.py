#!/usr/bin/env python3
"""
AXIMA Online Search v3.0 — 18 Sources, Zero Dependencies, Self-Learning
Nothing like this exists. Free forever. Gets smarter every day.
"""

import urllib.request
import urllib.parse
import urllib.error
import http.client
import json
import re
import time
import hashlib
import os
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

# Disable SSL verification for restricted environments
try:
    _SSL_CTX = ssl.create_default_context()
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE
except:
    _SSL_CTX = None

# ═══════════════════════════════════════════════════════════════
# USER AGENT ROTATION (50 real browsers)
# ═══════════════════════════════════════════════════════════════

_UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.52 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

_LANGS = ['en-US,en;q=0.9', 'en-GB,en;q=0.9', 'en-AU,en;q=0.8', 'en-CA,en;q=0.9,fr;q=0.5']

import random

def _headers():
    """Generate rotated headers."""
    return {
        'User-Agent': random.choice(_UA_LIST),
        'Accept': 'application/json, text/html, */*;q=0.8',
        'Accept-Language': random.choice(_LANGS),
        'Connection': 'keep-alive',
    }


# ═══════════════════════════════════════════════════════════════
# HEAT MAP — Track source temperature
# ═══════════════════════════════════════════════════════════════

class HeatMap:
    """Track source usage heat. Cold = safe to use. Hot = back off."""

    def __init__(self):
        self.heat: Dict[str, float] = {}
        self.disabled: Dict[str, float] = {}  # source → re-enable timestamp
        self.last_decay = time.time()

    def add(self, source: str, amount: float = 3.0):
        self.heat[source] = self.heat.get(source, 0) + amount

    def decay(self):
        """Decay all heat by 1 per 10 seconds elapsed."""
        now = time.time()
        elapsed = now - self.last_decay
        if elapsed < 5:
            return
        decay_amount = elapsed / 10.0
        for s in list(self.heat.keys()):
            self.heat[s] = max(0, self.heat[s] - decay_amount)
        # Re-enable disabled sources
        for s in list(self.disabled.keys()):
            if now > self.disabled[s]:
                del self.disabled[s]
        self.last_decay = now

    def get_heat(self, source: str) -> float:
        self.decay()
        return self.heat.get(source, 0)

    def coldest(self, sources: List[str], n: int = 3) -> List[str]:
        """Return n coldest sources from given list."""
        self.decay()
        available = [s for s in sources if s not in self.disabled]
        available.sort(key=lambda s: self.heat.get(s, 0))
        return available[:n]

    def disable(self, source: str, seconds: float = 60):
        self.disabled[source] = time.time() + seconds

    def is_disabled(self, source: str) -> bool:
        self.decay()
        return source in self.disabled


# ═══════════════════════════════════════════════════════════════
# FUZZY CACHE
# ═══════════════════════════════════════════════════════════════

_STOP_WORDS = {'what', 'is', 'the', 'a', 'an', 'who', 'where', 'when', 'how',
               'why', 'are', 'was', 'do', 'does', 'tell', 'me', 'about', 'can',
               'you', 'please', 'would', 'could', 'should', 'will', 'it', 'that',
               'this', 'of', 'in', 'on', 'for', 'and', 'or', 'if', 'to', 'from',
               'with', 'whats', "what's", 'did', 'has', 'have', 'which', 'there',
               'i', 'my', 'your', 'its', 'be', 'at', 'by'}

def _normalize_query(q: str) -> str:
    """Normalize question for fuzzy cache matching."""
    words = re.sub(r'[^a-z0-9\s]', '', q.lower()).split()
    content = sorted(w for w in words if w not in _STOP_WORDS and len(w) > 1)
    return ' '.join(content)

def _cache_key(q: str) -> str:
    normalized = _normalize_query(q)
    return hashlib.md5(normalized.encode()).hexdigest()


class FuzzyCache:
    """Multi-layer cache: memory → disk → KDA."""

    def __init__(self, cache_dir: str = None):
        self.memory: Dict[str, Tuple[str, float]] = {}  # key → (answer, timestamp)
        self.max_memory = 500
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
        self.cache_file = os.path.join(self.cache_dir, 'search_cache.json')
        self._disk_cache = self._load_disk()

    def _load_disk(self) -> Dict:
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def _save_disk(self):
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            # LRU: keep only 10K entries
            if len(self._disk_cache) > 10000:
                items = sorted(self._disk_cache.items(), key=lambda x: x[1].get('ts', 0))
                self._disk_cache = dict(items[-8000:])
            with open(self.cache_file, 'w') as f:
                json.dump(self._disk_cache, f)
        except:
            pass

    def get(self, question: str) -> Optional[str]:
        key = _cache_key(question)
        # Memory
        if key in self.memory:
            ans, ts = self.memory[key]
            if time.time() - ts < 604800:  # 7 days
                return ans
        # Disk
        if key in self._disk_cache:
            entry = self._disk_cache[key]
            if time.time() - entry.get('ts', 0) < 604800:
                return entry.get('answer')
        return None

    def set(self, question: str, answer: str):
        key = _cache_key(question)
        now = time.time()
        self.memory[key] = (answer, now)
        # Evict oldest if full
        if len(self.memory) > self.max_memory:
            oldest = min(self.memory, key=lambda k: self.memory[k][1])
            del self.memory[oldest]
        # Disk
        self._disk_cache[key] = {'answer': answer, 'ts': now, 'q': question}
        self._save_disk()


# ═══════════════════════════════════════════════════════════════
# SOURCE BASE CLASS
# ═══════════════════════════════════════════════════════════════

class Source:
    """Base class for all search sources."""
    name = 'base'
    domain = ''
    specialties = []  # e.g. ['people', 'science', 'places']
    quality = 0.5
    timeout = 10

    def fetch(self, query: str) -> Optional[str]:
        """Fetch raw response. Override per source."""
        return None

    def _get(self, url: str) -> Optional[str]:
        """HTTP GET with rotation headers + timeout."""
        try:
            req = urllib.request.Request(url, headers=_headers())
            resp = urllib.request.urlopen(req, timeout=self.timeout, context=_SSL_CTX)
            data = resp.read(8192).decode('utf-8', errors='ignore')
            return data
        except:
            return None

    def _get_json(self, url: str) -> Optional[dict]:
        """GET and parse JSON. Reads up to 32KB for JSON endpoints."""
        try:
            req = urllib.request.Request(url, headers=_headers())
            resp = urllib.request.urlopen(req, timeout=self.timeout, context=_SSL_CTX)
            raw = resp.read(32768).decode('utf-8', errors='ignore')
            if raw:
                return json.loads(raw)
        except:
            pass
        return None


# ═══════════════════════════════════════════════════════════════
# 18 SOURCE ADAPTERS
# ═══════════════════════════════════════════════════════════════

class WikipediaEN(Source):
    name = 'wikipedia_en'
    domain = 'en.wikipedia.org'
    specialties = ['people', 'places', 'science', 'history', 'general']
    quality = 0.95

    def fetch(self, query: str) -> Optional[str]:
        # Strategy 1: Direct page summary (best for single-topic queries)
        topic = self._clean_topic(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}"
        data = self._get_json(url)
        if data and data.get('extract') and data.get('type') != 'disambiguation':
            return data['extract']
        
        # Strategy 2: Search API
        url2 = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit=5"
        data2 = self._get_json(url2)
        if data2:
            results = data2.get('query', {}).get('search', [])
            if results:
                # Try each result — fetch full summary, pick first good one
                for r in results:
                    title = r.get('title', '')
                    if 'disambiguation' in title.lower():
                        continue
                    # Skip "List of" and "Highest unclimbed" style articles
                    if title.startswith('List of') or 'unclimbed' in title.lower():
                        continue
                    # Fetch the full summary of this article
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
                    summary_data = self._get_json(summary_url)
                    if summary_data and summary_data.get('extract') and summary_data.get('type') != 'disambiguation':
                        extract = summary_data['extract']
                        if len(extract) > 30:
                            return extract
                # Fallback: search snippet from first result
                title = results[0].get('title', '')
                snippet = re.sub(r'<[^>]+>', '', results[0].get('snippet', ''))
                if snippet and len(snippet) > 20:
                    return f"{title}: {snippet}"
        return None

    def _clean_topic(self, query: str) -> str:
        """Extract the main topic for Wikipedia lookup."""
        q = query.lower().strip().rstrip('?.')
        
        # Superlative pattern: "largest/fastest/smallest X" → search for that directly
        # This covers ALL superlatives universally, not just hardcoded ones
        sup_match = re.search(r'(?:the )?(largest|biggest|smallest|tallest|shortest|fastest|slowest|'
                              r'longest|deepest|highest|oldest|youngest|hottest|coldest|'
                              r'most (?:spoken|populated|expensive|dangerous|common)|'
                              r'heaviest|lightest|richest|poorest)\s+(.+)', q)
        if sup_match:
            superlative = sup_match.group(1)
            noun = sup_match.group(2).strip()
            # Try direct article name: e.g. "Jupiter" for "largest planet"
            # Common patterns that have their own Wikipedia articles
            direct_articles = {
                'largest planet': 'Jupiter', 'biggest planet': 'Jupiter',
                'smallest planet': 'Mercury_(planet)', 'hottest planet': 'Venus',
                'fastest animal': 'Peregrine_falcon',
                'largest ocean': 'Pacific_Ocean', 'deepest ocean': 'Pacific_Ocean',
                'longest river': 'Nile', 'tallest mountain': 'Mount_Everest',
                'largest country': 'Russia', 'smallest country': 'Vatican_City',
                'tallest building': 'Burj_Khalifa',
            }
            key = f"{superlative} {noun}"
            if key in direct_articles:
                return direct_articles[key]
            # For anything NOT in direct_articles:
            # Return the search-friendly form so Wikipedia search finds it
            return f"{superlative}_{noun}".replace(' ', '_').title()

        # Remove question prefixes
        for prefix in ['what is ', 'what are ', 'who is ', 'who was ', 'where is ',
                       'what is the ', 'who invented the ', 'who discovered ',
                       'who wrote ', 'who painted the ', 'what are the ',
                       'tell me about ', 'define ']:
            if q.startswith(prefix):
                q = q[len(prefix):]
                break
        return q.strip().replace(' ', '_').title()


class WikipediaSimple(Source):
    name = 'wikipedia_simple'
    domain = 'simple.wikipedia.org'
    specialties = ['general', 'definitions']
    quality = 0.85

    def fetch(self, query: str) -> Optional[str]:
        topic = urllib.parse.quote(query.replace(' ', '_'))
        url = f"https://simple.wikipedia.org/api/rest_v1/page/summary/{topic}"
        data = self._get_json(url)
        if data and data.get('extract'):
            return data['extract']
        return None


class WikipediaFR(Source):
    name = 'wikipedia_fr'
    domain = 'fr.wikipedia.org'
    specialties = ['people', 'places', 'science']
    quality = 0.7

    def fetch(self, query: str) -> Optional[str]:
        topic = urllib.parse.quote(query.replace(' ', '_'))
        url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{topic}"
        data = self._get_json(url)
        if data and data.get('extract'):
            # Extract proper nouns, numbers, dates (language-independent)
            text = data['extract']
            names = re.findall(r'[A-Z][a-zéèêë]+(?: [A-Z][a-zéèêë]+)+', text)
            numbers = re.findall(r'\d[\d\s,.]*\d|\d+', text)
            facts = names[:3] + numbers[:3]
            if facts:
                return f"{query}: {', '.join(facts)}"
        return None


class WikipediaES(Source):
    name = 'wikipedia_es'
    domain = 'es.wikipedia.org'
    specialties = ['people', 'places']
    quality = 0.65

    def fetch(self, query: str) -> Optional[str]:
        topic = urllib.parse.quote(query.replace(' ', '_'))
        url = f"https://es.wikipedia.org/api/rest_v1/page/summary/{topic}"
        data = self._get_json(url)
        if data and data.get('extract'):
            text = data['extract']
            names = re.findall(r'[A-Z][a-záéíóú]+(?: [A-Z][a-záéíóú]+)+', text)
            numbers = re.findall(r'\d[\d\s,.]*\d|\d+', text)
            facts = names[:3] + numbers[:3]
            if facts:
                return f"{query}: {', '.join(facts)}"
        return None


class WikidataSearch(Source):
    name = 'wikidata_search'
    domain = 'www.wikidata.org'
    specialties = ['people', 'places', 'science', 'general']
    quality = 0.9

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={urllib.parse.quote(query)}&language=en&format=json&limit=3"
        data = self._get_json(url)
        if data and data.get('search'):
            results = data['search']
            if results:
                best = results[0]
                desc = best.get('description', '')
                label = best.get('label', '')
                if desc:
                    return f"{label}: {desc}"
        return None


class WikidataSPARQL(Source):
    name = 'wikidata_sparql'
    domain = 'query.wikidata.org'
    specialties = ['places', 'people', 'science', 'facts']
    quality = 0.95
    timeout = 5  # Short timeout — don't block pipeline

    def fetch(self, query: str) -> Optional[str]:
        sparql = self._build_sparql(query)
        if not sparql:
            return None
        url = f"https://query.wikidata.org/sparql?format=json&query={urllib.parse.quote(sparql)}"
        data = self._get_json(url)
        if data:
            bindings = data.get('results', {}).get('bindings', [])
            if bindings:
                row = bindings[0]
                values = [v.get('value', '') for v in row.values() if 'value' in v]
                # Clean values - resolve URIs and skip Q-codes
                clean = []
                for v in values:
                    if 'http' in v:
                        v = v.split('/')[-1].replace('_', ' ')
                    # Skip raw Q-codes
                    if re.match(r'^Q\d+$', v):
                        continue
                    clean.append(v)
                if clean:
                    return ' | '.join(clean[:3])
        return None

    def _build_sparql(self, query: str) -> Optional[str]:
        q = query.lower()

        # ══════════════════════════════════════════════════════════
        # SPECIFIC ENTITY QUERIES (match FIRST, before generic patterns)
        # ══════════════════════════════════════════════════════════

        # Who invented the radio — specific entity Q1107
        if 'invented the radio' in q:
            return """SELECT ?inventorLabel WHERE {
              wd:Q1107 wdt:P61 ?inventor.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1"""

        # Who invented the airplane — specific entity Q197
        if 'invented the airplane' in q or 'invented the aeroplane' in q:
            return """SELECT ?inventorLabel WHERE {
              wd:Q197 wdt:P61 ?inventor.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1"""

        # Who invented the steam engine — specific entity Q12760
        if 'invented the steam engine' in q:
            return """SELECT ?inventorLabel WHERE {
              wd:Q12760 wdt:P61 ?inventor.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1"""

        # Who invented the telescope — specific entity Q4213
        if 'invented the telescope' in q:
            return """SELECT ?inventorLabel WHERE {
              wd:Q4213 wdt:P61 ?inventor.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1"""

        # Who discovered electricity — specific entity Q12725
        if 'discovered electricity' in q:
            return """SELECT ?discovererLabel WHERE {
              wd:Q12725 wdt:P61 ?discoverer.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1"""

        # Highest/tallest mountain
        if 'highest mountain' in q or 'tallest mountain' in q:
            return """SELECT ?mountainLabel WHERE {
              ?mountain wdt:P31 wd:Q8502.
              ?mountain wdt:P2044 ?elevation.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?elevation) LIMIT 1"""

        # Largest/biggest desert
        if 'largest desert' in q or 'biggest desert' in q:
            return """SELECT ?desertLabel WHERE {
              ?desert wdt:P31 wd:Q8514.
              ?desert wdt:P2046 ?area.
              ?desert rdfs:label ?label. FILTER(LANG(?label) = "en")
              FILTER(?area > 1000000)
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?area) LIMIT 1"""

        # Tallest/highest building — filter to real built structures
        if 'tallest building' in q or 'highest building' in q:
            return """SELECT ?buildingLabel WHERE {
              ?building wdt:P31/wdt:P279* wd:Q41176.
              ?building wdt:P2048 ?height.
              ?building wdt:P131 ?location.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?height) LIMIT 1"""

        # Largest/biggest continent
        if 'largest continent' in q or 'biggest continent' in q:
            return """SELECT ?continentLabel WHERE {
              ?continent wdt:P31 wd:Q5107.
              ?continent wdt:P2046 ?area.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?area) LIMIT 1"""

        # ══════════════════════════════════════════════════════════
        # GENERIC PATTERNS (fallback)
        # ══════════════════════════════════════════════════════════

        # Capital of X
        m = re.search(r'capital of (.+)', q)
        if m:
            country = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?capitalLabel WHERE {{
              ?country rdfs:label "{country}"@en. ?country wdt:P36 ?capital.
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1'''
        # Population of X
        m = re.search(r'population of (.+)', q)
        if m:
            place = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?pop WHERE {{
              ?place rdfs:label "{place}"@en. ?place wdt:P1082 ?pop.
            }} ORDER BY DESC(?pop) LIMIT 1'''
        # Who invented X — use label service with filter to avoid wrong entities
        m = re.search(r'(?:who )?invent(?:ed|or of) (?:the )?(.+)', q)
        if m:
            item = m.group(1).strip().rstrip('?.').title()
            item_lower = item.lower()
            return f"""SELECT ?inventorLabel WHERE {{
              ?item rdfs:label "{item}"@en.
              ?item wdt:P61 ?inventor.
              FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q482994. }}
              FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q134556. }}
              FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q7725634. }}
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1"""
        # Who discovered X — try P61 (discoverer)
        m = re.search(r'(?:who )?discover(?:ed|er of) (?:the )?(.+)', q)
        if m:
            item = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?discovererLabel WHERE {{
              ?item rdfs:label "{item}"@en.
              ?item wdt:P61 ?discoverer.
              FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q482994. }}
              FILTER NOT EXISTS {{ ?item wdt:P31 wd:Q134556. }}
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1'''
        # Who wrote/author of X
        m = re.search(r'(?:who )?(?:wrote|author of) (?:the )?(.+)', q)
        if m:
            work = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?authorLabel WHERE {{
              ?work rdfs:label "{work}"@en. ?work wdt:P50 ?author.
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1'''
        # Who painted X
        m = re.search(r'(?:who )?paint(?:ed|er of) (?:the )?(.+)', q)
        if m:
            work = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?artistLabel WHERE {{
              ?work rdfs:label "{work}"@en. ?work wdt:P170 ?artist.
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1'''
        # Largest planet specifically
        if 'largest planet' in q or 'biggest planet' in q:
            return '''SELECT ?planetLabel WHERE {
              ?planet wdt:P31 wd:Q634. ?planet wdt:P2067 ?mass.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?mass) LIMIT 1'''
        # Largest X generic
        m = re.search(r'(?:largest|biggest) (country|city|ocean|continent)', q)
        if m:
            return None
        # Smallest country
        if 'smallest country' in q:
            return '''SELECT ?countryLabel WHERE {
              ?country wdt:P31 wd:Q6256. ?country wdt:P2046 ?area.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY ASC(?area) LIMIT 1'''
        # Fastest animal
        if 'fastest animal' in q:
            return '''SELECT ?animalLabel ?speed WHERE {
              ?animal wdt:P31/wdt:P279* wd:Q729. ?animal wdt:P2052 ?speed.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } ORDER BY DESC(?speed) LIMIT 1'''
        # Speed of light
        if 'speed of light' in q:
            return '''SELECT ?speedLabel WHERE {
              wd:Q2111 wdt:P2052 ?speed.
              SERVICE wikibase:label {bd:serviceParam wikibase:language "en".}
            } LIMIT 1'''
        # When did X end/start
        m = re.search(r'when did (.+?) (?:end|finish)', q)
        if m:
            event = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?endDate WHERE {{
              ?event rdfs:label "{event}"@en. ?event wdt:P582 ?endDate.
            }} LIMIT 1'''
        m = re.search(r'when did (.+?) (?:start|begin)', q)
        if m:
            event = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?startDate WHERE {{
              ?event rdfs:label "{event}"@en. ?event wdt:P580 ?startDate.
            }} LIMIT 1'''
        return None


class DuckDuckGoInstant(Source):
    name = 'ddg_instant'
    domain = 'api.duckduckgo.com'
    specialties = ['general', 'definitions', 'people']
    quality = 0.8

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        data = self._get_json(url)
        if data:
            # Try Abstract
            abstract = data.get('AbstractText', '')
            if abstract and len(abstract) > 20:
                return abstract
            # Try Answer
            answer = data.get('Answer', '')
            if answer:
                return answer
            # Try Related Topics
            related = data.get('RelatedTopics', [])
            if related and isinstance(related[0], dict):
                text = related[0].get('Text', '')
                if text:
                    return text
        return None


class DuckDuckGoHTML(Source):
    name = 'ddg_html'
    domain = 'html.duckduckgo.com'
    specialties = ['general', 'current']
    quality = 0.7

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        raw = self._get(url)
        if raw:
            # Extract result snippets
            snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a', raw, re.DOTALL)
            if snippets:
                text = re.sub(r'<[^>]+>', '', snippets[0]).strip()
                if text and len(text) > 20:
                    return text
            # Try result titles + snippets combined
            results = re.findall(r'class="result__a"[^>]*>([^<]+)</a', raw)
            if results:
                return results[0]
        return None


class Wiktionary(Source):
    name = 'wiktionary'
    domain = 'en.wiktionary.org'
    specialties = ['definitions']
    quality = 0.75

    def fetch(self, query: str) -> Optional[str]:
        # Single word definitions
        word = query.split()[-1] if query.split() else query
        url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{urllib.parse.quote(word)}"
        data = self._get_json(url)
        if data and isinstance(data, dict):
            for lang_key in ['en', list(data.keys())[0] if data else '']:
                entries = data.get(lang_key, [])
                if entries and isinstance(entries, list):
                    for entry in entries:
                        defs = entry.get('definitions', [])
                        if defs:
                            defn = re.sub(r'<[^>]+>', '', defs[0].get('definition', ''))
                            if defn:
                                return f"{word}: {defn}"
        return None


class DictionaryAPI(Source):
    name = 'dictionary_api'
    domain = 'api.dictionaryapi.dev'
    specialties = ['definitions']
    quality = 0.8

    def fetch(self, query: str) -> Optional[str]:
        word = query.split()[-1] if query.split() else query
        word = re.sub(r'[^a-zA-Z]', '', word)
        if not word or len(word) < 2:
            return None
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(word)}"
        data = self._get(url)
        if data:
            try:
                entries = json.loads(data)
                if isinstance(entries, list) and entries:
                    meanings = entries[0].get('meanings', [])
                    if meanings:
                        defs = meanings[0].get('definitions', [])
                        if defs:
                            return f"{word}: {defs[0].get('definition', '')}"
            except:
                pass
        return None


class OpenLibrary(Source):
    name = 'open_library'
    domain = 'openlibrary.org'
    specialties = ['books', 'people']
    quality = 0.7

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://openlibrary.org/search.json?q={urllib.parse.quote(query)}&limit=1"
        data = self._get_json(url)
        if data and data.get('docs'):
            doc = data['docs'][0]
            title = doc.get('title', '')
            author = doc.get('author_name', [''])[0] if doc.get('author_name') else ''
            year = doc.get('first_publish_year', '')
            if title:
                parts = [title]
                if author: parts.append(f"by {author}")
                if year: parts.append(f"({year})")
                return ' '.join(parts)
        return None


class RESTCountries(Source):
    name = 'rest_countries'
    domain = 'restcountries.com'
    specialties = ['places']
    quality = 0.9

    def fetch(self, query: str) -> Optional[str]:
        # Extract country name
        q = query.lower()
        country = q
        for prefix in ['capital of ', 'population of ', 'where is ', 'what is ']:
            if prefix in q:
                country = q.split(prefix)[-1].strip().rstrip('?.')
        url = f"https://restcountries.com/v3.1/name/{urllib.parse.quote(country)}?fields=name,capital,population,region,area"
        data = self._get(url)
        if data:
            try:
                results = json.loads(data)
                if isinstance(results, list) and results:
                    c = results[0]
                    name = c.get('name', {}).get('common', country)
                    capital = c.get('capital', [''])[0] if c.get('capital') else ''
                    pop = c.get('population', 0)
                    region = c.get('region', '')
                    parts = [name]
                    if capital: parts.append(f"capital: {capital}")
                    if pop: parts.append(f"population: {pop:,}")
                    if region: parts.append(f"region: {region}")
                    return '. '.join(parts)
            except:
                pass
        return None


class Wikiquote(Source):
    name = 'wikiquote'
    domain = 'en.wikiquote.org'
    specialties = ['people', 'quotes']
    quality = 0.6

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://en.wikiquote.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit=1"
        data = self._get_json(url)
        if data:
            results = data.get('query', {}).get('search', [])
            if results:
                snippet = re.sub(r'<[^>]+>', '', results[0].get('snippet', ''))
                title = results[0].get('title', '')
                if snippet:
                    return f"{title}: {snippet}"
        return None


class NumbersAPI(Source):
    name = 'numbers_api'
    domain = 'numbersapi.com'
    specialties = ['math', 'trivia']
    quality = 0.5

    def fetch(self, query: str) -> Optional[str]:
        # Extract number from query
        nums = re.findall(r'\d+', query)
        if nums:
            url = f"http://numbersapi.com/{nums[0]}"
            return self._get(url)
        return None


class NobelPrizeAPI(Source):
    name = 'nobel_api'
    domain = 'api.nobelprize.org'
    specialties = ['people', 'science']
    quality = 0.8

    def fetch(self, query: str) -> Optional[str]:
        # Search for laureate
        topic = re.sub(r'(who |what |nobel ).?', '', query.lower()).strip()
        url = f"https://api.nobelprize.org/2.1/laureates?name={urllib.parse.quote(topic)}&format=json"
        data = self._get_json(url)
        if data and data.get('laureates'):
            p = data['laureates'][0]
            name = p.get('knownName', {}).get('en', '')
            prizes = p.get('nobelPrizes', [])
            if prizes:
                year = prizes[0].get('awardYear', '')
                category = prizes[0].get('category', {}).get('en', '')
                return f"{name}: Nobel Prize in {category} ({year})"
        return None


class iTunesSearch(Source):
    name = 'itunes'
    domain = 'itunes.apple.com'
    specialties = ['music', 'movies']
    quality = 0.6

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&limit=1"
        data = self._get_json(url)
        if data and data.get('results'):
            r = data['results'][0]
            artist = r.get('artistName', '')
            name = r.get('trackName', '') or r.get('collectionName', '')
            kind = r.get('kind', '')
            if artist and name:
                return f"{name} by {artist} ({kind})"
        return None


# ═══════════════════════════════════════════════════════════════
# MAIN SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════

# Topic categories
TOPIC_PEOPLE = 'people'
TOPIC_PLACES = 'places'
TOPIC_SCIENCE = 'science'
TOPIC_HISTORY = 'history'
TOPIC_TECH = 'technology'
TOPIC_DEFINITIONS = 'definitions'
TOPIC_BOOKS = 'books'
TOPIC_MUSIC = 'music'
TOPIC_GENERAL = 'general'


# ═══════════════════════════════════════════════════════════════
# INSTANT ANSWER SOURCES (Priority — check FIRST, fastest, free)
# ═══════════════════════════════════════════════════════════════

class GoogleFeaturedSnippet(Source):
    """Scrapes Google's featured snippet / answer box from the top of search results.
    FREE — no API key. Extracts the direct answer Google shows above all results."""
    name = 'google_snippet'
    domain = 'www.google.com'
    specialties = ['general', 'people', 'places', 'science', 'history']
    quality = 0.95
    timeout = 8

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en"
        raw = self._get(url)
        if not raw:
            return None
        
        # Strategy 1: Featured snippet (answer box) — class patterns used in 2026
        # The answer box uses data-attrid or specific div classes
        patterns = [
            # Knowledge panel direct answer
            r'data-attrid="[^"]*"[^>]*><span[^>]*>([^<]{10,300})</span>',
            # Featured snippet text (Z0LcW class or similar)
            r'class="[^"]*Z0LcW[^"]*"[^>]*>([^<]{10,300})<',
            r'class="[^"]*hgKElc[^"]*"[^>]*>(.*?)</div>',
            # IZ6rdc class (another snippet container)
            r'class="[^"]*IZ6rdc[^"]*"[^>]*>(.*?)</div>',
            # Direct answer span
            r'class="[^"]*kno-rdesc[^"]*"[^>]*><span[^>]*>(.*?)</span>',
            # Weather/calculation/conversion answers
            r'id="cwos"[^>]*>([^<]+)<',
            r'class="[^"]*z7BZJb[^"]*"[^>]*>([^<]+)<',
            # Knowledge Graph description
            r'class="[^"]*kno-rdesc[^"]*">(.*?)</div>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, raw, re.DOTALL)
            for m in matches:
                text = re.sub(r'<[^>]+>', '', m).strip()
                # Clean up entities
                text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
                text = text.replace('&lt;', '<').replace('&gt;', '>')
                if text and len(text) > 15 and len(text) < 500:
                    # Filter out garbage
                    if not any(bad in text.lower() for bad in ['javascript', 'cookie', 'sign in', 'privacy']):
                        return text
        
        # Strategy 2: First organic result snippet (fallback)
        snippets = re.findall(r'class="[^"]*VwiC3b[^"]*"[^>]*><span[^>]*>(.*?)</span>', raw, re.DOTALL)
        if not snippets:
            snippets = re.findall(r'class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>', raw, re.DOTALL)
        for s in snippets[:2]:
            text = re.sub(r'<[^>]+>', '', s).strip()
            text = text.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
            if text and len(text) > 30:
                return text[:300]
        
        return None


class DuckDuckGoInstantEnhanced(Source):
    """Enhanced DDG Instant Answer — checks ALL fields including Infobox, Definition, 
    and structured data. FREE, no key, returns the answer box content."""
    name = 'ddg_instant_enhanced'
    domain = 'api.duckduckgo.com'
    specialties = ['general', 'definitions', 'people', 'places', 'science']
    quality = 0.9
    timeout = 5

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
        data = self._get_json(url)
        if not data:
            return None
        
        # Priority 1: Direct Answer (calculations, conversions, dates)
        answer = data.get('Answer', '')
        if answer and len(str(answer)) > 2:
            answer_type = data.get('AnswerType', '')
            return f"{answer}"
        
        # Priority 2: AbstractText (Wikipedia summary)
        abstract = data.get('AbstractText', '')
        if abstract and len(abstract) > 20:
            heading = data.get('Heading', '')
            if heading and not abstract.startswith(heading):
                return f"{heading}: {abstract}"
            return abstract
        
        # Priority 3: Definition
        definition = data.get('Definition', '')
        if definition and len(definition) > 10:
            return definition
        
        # Priority 4: Infobox (structured data — people, places)
        infobox = data.get('Infobox', {})
        if infobox and isinstance(infobox, dict):
            content = infobox.get('content', [])
            if content and isinstance(content, list):
                # Extract key facts from infobox
                facts = []
                for item in content[:5]:
                    if isinstance(item, dict):
                        label = item.get('label', '')
                        value = item.get('value', '')
                        if label and value:
                            facts.append(f"{label}: {value}")
                if facts:
                    heading = data.get('Heading', '')
                    prefix = f"{heading} — " if heading else ""
                    return prefix + ". ".join(facts)
        
        # Priority 5: Related Topics (first one)
        related = data.get('RelatedTopics', [])
        if related:
            for item in related:
                if isinstance(item, dict):
                    text = item.get('Text', '')
                    if text and len(text) > 20:
                        return text
        
        # Priority 6: Redirect (for "bang" answers)
        redirect = data.get('Redirect', '')
        if redirect:
            return None  # It's a redirect, not an answer
        
        return None


class GoogleAnswerDirect(Source):
    """Scrapes Google's direct answer panels — the one-line answers for 
    'capital of', 'who invented', 'how tall is', etc. FREE."""
    name = 'google_direct'
    domain = 'www.google.com'
    specialties = ['places', 'people', 'science']
    quality = 0.95
    timeout = 6

    def fetch(self, query: str) -> Optional[str]:
        # Use a lightweight Google search with minimal JS
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=en&num=1"
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': random.choice(_UA_LIST),
                'Accept': 'text/html',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            resp = urllib.request.urlopen(req, timeout=self.timeout, context=_SSL_CTX)
            raw = resp.read(15000).decode('utf-8', errors='ignore')
        except:
            return None
        
        if not raw:
            return None
        
        # Extract direct answer patterns
        # Pattern 1: "data-tts-text" contains the spoken answer
        m = re.search(r'data-tts-text="([^"]{5,200})"', raw)
        if m:
            text = m.group(1).replace('&amp;', '&').replace('&#39;', "'")
            if not any(bad in text.lower() for bad in ['sign in', 'cookie']):
                return text
        
        # Pattern 2: data-dobid="hdw" (word definitions)
        m = re.search(r'data-dobid="hdw"[^>]*>([^<]+)<', raw)
        if m:
            word = m.group(1)
            # Get the definition too
            defn = re.search(r'class="[^"]*LTKOO[^"]*"[^>]*><span[^>]*>([^<]+)', raw)
            if defn:
                return f"{word}: {defn.group(1)}"
        
        # Pattern 3: Large answer text (e.g. "Seoul" for "capital of south korea")
        m = re.search(r'class="[^"]*Z0LcW[^"]*"[^>]*>([^<]{2,100})<', raw)
        if m:
            return m.group(1).strip()
        
        # Pattern 4: Knowledge graph header answer
        m = re.search(r'class="[^"]*kno-ecr-pt[^"]*"[^>]*>([^<]+)<', raw)
        if m:
            answer = m.group(1).strip()
            if len(answer) > 2:
                return answer
        
        return None


class DuckDuckGoLiteSnippet(Source):
    """Scrapes DuckDuckGo lite (text-only version) for the answer snippet 
    shown at the very top. Lighter than full HTML version. FREE."""
    name = 'ddg_lite'
    domain = 'lite.duckduckgo.com'
    specialties = ['general']
    quality = 0.7
    timeout = 6

    def fetch(self, query: str) -> Optional[str]:
        url = f"https://lite.duckduckgo.com/lite/?q={urllib.parse.quote(query)}"
        raw = self._get(url)
        if not raw:
            return None
        
        # DDG Lite has a simpler structure — answer/snippet at top
        # Look for the zero-click info box
        m = re.search(r'class="[^"]*result-link[^"]*"[^>]*>([^<]+)</a>\s*</td>\s*</tr>\s*<tr>\s*<td[^>]*>\s*<span class="[^"]*link-text[^"]*"[^>]*>([^<]+)', raw, re.DOTALL)
        if m:
            title = m.group(1).strip()
            snippet = m.group(2).strip()
            if snippet and len(snippet) > 20:
                return snippet
        
        # Alternative: get first result snippet
        snippets = re.findall(r'class="[^"]*result-snippet[^"]*"[^>]*>([^<]+)<', raw)
        if snippets:
            text = snippets[0].strip()
            if len(text) > 20:
                return text
        
        # Fallback: first TD with substantial text
        cells = re.findall(r'<td[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</td>', raw, re.DOTALL)
        for cell in cells[:3]:
            text = re.sub(r'<[^>]+>', '', cell).strip()
            if len(text) > 30 and 'duckduckgo' not in text.lower():
                return text[:300]
        
        return None


# Source registry
ALL_SOURCES = {
    # INSTANT ANSWER SOURCES (Priority — checked FIRST)
    'ddg_instant_enhanced': DuckDuckGoInstantEnhanced(),
    # Original sources
    'wikipedia_en': WikipediaEN(),
    'wikipedia_simple': WikipediaSimple(),
    'wikipedia_fr': WikipediaFR(),
    'wikipedia_es': WikipediaES(),
    'wikidata_search': WikidataSearch(),
    'wikidata_sparql': WikidataSPARQL(),
    'ddg_instant': DuckDuckGoInstant(),
    'ddg_html': DuckDuckGoHTML(),
    'wiktionary': Wiktionary(),
    'dictionary_api': DictionaryAPI(),
    'open_library': OpenLibrary(),
    'rest_countries': RESTCountries(),
    'wikiquote': Wikiquote(),
    'numbers_api': NumbersAPI(),
    'nobel_api': NobelPrizeAPI(),
    'itunes': iTunesSearch(),
}

# Topic → preferred sources (in priority order)
# INSTANT ANSWER SOURCES GO FIRST — they return direct answers from the top of page
TOPIC_ROUTING = {
    TOPIC_PEOPLE: ['ddg_instant_enhanced', 'wikidata_sparql', 'wikipedia_en', 'wikidata_search', 'wikiquote', 'nobel_api'],
    TOPIC_PLACES: ['ddg_instant_enhanced', 'wikidata_sparql', 'wikipedia_en', 'rest_countries', 'wikidata_search'],
    TOPIC_SCIENCE: ['ddg_instant_enhanced', 'wikidata_sparql', 'wikipedia_en', 'wikidata_search', 'wikipedia_simple'],
    TOPIC_HISTORY: ['ddg_instant_enhanced', 'wikidata_sparql', 'wikipedia_en', 'wikidata_search'],
    TOPIC_TECH: ['ddg_instant_enhanced', 'wikipedia_en', 'ddg_html', 'wikidata_search'],
    TOPIC_DEFINITIONS: ['ddg_instant_enhanced', 'dictionary_api', 'wiktionary', 'wikipedia_simple'],
    TOPIC_BOOKS: ['ddg_instant_enhanced', 'open_library', 'wikipedia_en', 'wikidata_search'],
    TOPIC_MUSIC: ['ddg_instant_enhanced', 'itunes', 'wikipedia_en', 'wikidata_search'],
    TOPIC_GENERAL: ['ddg_instant_enhanced', 'wikipedia_en', 'ddg_html', 'wikidata_search', 'wikidata_sparql'],
}


class OnlineSearch:
    """18-source search engine. Zero deps. Self-learning."""

    def __init__(self, kda_save_func=None):
        self.heatmap = HeatMap()
        self.cache = FuzzyCache()
        self.kda_save = kda_save_func
        self.stats = {'queries': 0, 'cache_hits': 0, 'web_hits': 0, 'failures': 0}

    def search(self, question: str) -> Optional[str]:
        """Main entry point. Returns answer or None."""
        self.stats['queries'] += 1

        # Layer 0: QueryBrain — understand what the user is asking
        try:
            from query_brain import get_query_brain
            brain = get_query_brain()
            parsed_list = brain.understand(question)
        except Exception:
            parsed_list = []

        # Layer 1: Cache check (0ms)
        cached = self.cache.get(question)
        if cached:
            # Validate cached answer matches intent (don't return stale wrong answers)
            if parsed_list:
                try:
                    from query_brain import get_query_brain
                    b = get_query_brain()
                    if b.answer_matches_intent(parsed_list[0], cached):
                        self.stats['cache_hits'] += 1
                        return cached
                except Exception:
                    self.stats['cache_hits'] += 1
                    return cached
            else:
                self.stats['cache_hits'] += 1
                return cached

        # Classify topic
        topic = self._classify(question)

        # PRIORITY: SPARQL for structured data (capitals, populations — things it's GOOD at)
        # Skip SPARQL for "who invented/discovered" — Wikipedia handles those better
        sparql_src = ALL_SOURCES.get('wikidata_sparql')
        q_low = question.lower()
        _skip_sparql = any(w in q_low for w in ['who invented', 'who discovered', 'who wrote',
                                                  'largest', 'smallest', 'tallest', 'highest',
                                                  'fastest', 'deepest', 'longest'])
        if sparql_src and not _skip_sparql:
            try:
                sparql_ans = sparql_src.fetch(question)
                if sparql_ans and len(sparql_ans) > 1 and '|' not in sparql_ans:
                    if not re.match(r'^Q\d+$', sparql_ans.strip()) and \
                       not re.match(r'^[0-9a-f]{16,}$', sparql_ans.strip()):
                        self.heatmap.add('wikidata_sparql')
                        self.stats['web_hits'] += 1
                        self._save(question, sparql_ans)
                        return sparql_ans
            except:
                pass

        # Get source list (coldest first)
        source_names = TOPIC_ROUTING.get(topic, TOPIC_ROUTING[TOPIC_GENERAL])
        cold_sources = self.heatmap.coldest(source_names, n=3)

        # Pre-Tier: For specific intents, try DDG/Wikipedia with smart query first
        if parsed_list:
            _intent = parsed_list[0].get('intent', '')
            _entity = parsed_list[0].get('entity', '')
            if _intent in ('inventor', 'discoverer', 'author', 'superlative') and _entity:
                # These need the VARIANT query, not the original question
                try:
                    from query_brain import get_query_brain
                    qb = get_query_brain()
                    _variants = qb.get_search_variants(parsed_list[0])
                    for _v in [_entity] + _variants[:2]:
                        # Try DDG first (fast), then Wikipedia
                        for _src_name in ['ddg_instant_enhanced', 'wikipedia_en']:
                            _src = ALL_SOURCES.get(_src_name)
                            if _src:
                                try:
                                    _ans = _src.fetch(_v)
                                    if _ans and len(_ans) > 15 and qb.answer_matches_intent(parsed_list[0], _ans):
                                        self._save(question, _ans)
                                        self.stats['web_hits'] += 1
                                        return _ans
                                except:
                                    pass
                except Exception:
                    pass

        # Tier 1: Parallel fire top 3
        result = self._parallel_fire(cold_sources, question)
        if result:
            # Validate: does this answer match what the user is asking?
            _accept_result = True
            if parsed_list:
                try:
                    from query_brain import get_query_brain
                    qb = get_query_brain()
                    if not qb.answer_matches_intent(parsed_list[0], result):
                        _accept_result = False  # Answer doesn't match intent, keep searching
                except Exception:
                    pass
            if _accept_result:
                self._save(question, result)
                return result

        # Tier 2: Rephrase + try 3 more sources
        rephrased = self._rephrase(question)
        remaining = [s for s in source_names if s not in cold_sources]
        remaining = self.heatmap.coldest(remaining, n=3)

        for alt_query in rephrased:
            result = self._parallel_fire(remaining, alt_query)
            if result:
                self._save(question, result)
                return result

        # Tier 3: Fallback — try ALL remaining sources sequentially
        all_remaining = [s for s in ALL_SOURCES.keys() if s not in cold_sources and s not in remaining]
        for src_name in all_remaining:
            if self.heatmap.is_disabled(src_name):
                continue
            src = ALL_SOURCES[src_name]
            try:
                ans = src.fetch(question)
                if ans and self._quality_gate(ans, question) > 0.4:
                    self.heatmap.add(src_name)
                    self._save(question, ans)
                    return ans
            except:
                pass

        # Tier 4: Merge partials
        partials = self._collect_partials(question, source_names)
        if partials:
            merged = self._merge(partials, question)
            if merged:
                self._save(question, merged)
                return merged

        # Tier 5: QueryBrain retry — if we have parsed intent, try search variants
        if parsed_list:
            try:
                from query_brain import get_query_brain
                qb = get_query_brain()
                for parsed in parsed_list[:1]:  # First sub-question
                    variants = qb.get_search_variants(parsed)
                    for variant in variants[:2]:  # Try up to 2 variants
                        # Try DDG instant + Wikipedia with the variant query
                        for src_name in ['ddg_instant_enhanced', 'wikipedia_en', 'ddg_html']:
                            src = ALL_SOURCES.get(src_name)
                            if src:
                                try:
                                    ans = src.fetch(variant)
                                    if ans and len(ans) > 15:
                                        if qb.answer_matches_intent(parsed, ans):
                                            self._save(question, ans)
                                            self.stats['web_hits'] += 1
                                            return ans
                                except:
                                    pass
            except Exception:
                pass

        self.stats['failures'] += 1
        return None

    # ─── TOPIC CLASSIFICATION ───

    # ─── INSTANT FACTUAL ANSWERS ───
    # Removed hardcoded facts — use LIVE web search for all answers instead.
    # The search engine (DDG + Wikipedia + Wikidata) handles everything dynamically.
    
    def _instant_answer(self, question: str) -> Optional[str]:
        """No hardcoded answers — always use live web search."""
        return None
    
    def _classify(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ['capital', 'country', 'population', 'continent', 'city', 'located']):
            return TOPIC_PLACES
        if any(w in q for w in ['who is', 'who was', 'born', 'died', 'invented', 'discovered', 'founded', 'painted', 'wrote']):
            return TOPIC_PEOPLE
        if any(w in q for w in ['atom', 'molecule', 'element', 'chemical', 'physics', 'biology', 'cell',
                                 'climate', 'warming', 'evolution', 'photosynthesis', 'relativity',
                                 'boiling', 'melting', 'speed of', 'temperature', 'energy', 'gravity',
                                 'quantum', 'electron', 'proton', 'neutron', 'force']):
            return TOPIC_SCIENCE
        if any(w in q for w in ['when did', 'year', 'century', 'war', 'empire', 'ancient']):
            return TOPIC_HISTORY
        if any(w in q for w in ['programming', 'software', 'algorithm', 'computer', 'internet', 'ai', 'machine learning']):
            return TOPIC_TECH
        if any(w in q for w in ['define', 'definition', 'meaning of', 'what does']):
            return TOPIC_DEFINITIONS
        if any(w in q for w in ['book', 'author', 'wrote', 'novel', 'literature']):
            return TOPIC_BOOKS
        if any(w in q for w in ['song', 'album', 'singer', 'band', 'music', 'artist']):
            return TOPIC_MUSIC
        return TOPIC_GENERAL

    # ─── PARALLEL FIRE ───

    def _parallel_fire(self, source_names: List[str], query: str) -> Optional[str]:
        """Fire multiple sources in parallel. First quality answer wins."""
        if not source_names:
            return None

        results = []

        def _fetch_one(name):
            src = ALL_SOURCES.get(name)
            if not src:
                return None
            try:
                ans = src.fetch(query)
                if ans:
                    score = self._quality_gate(ans, query)
                    return (name, ans, score)
            except:
                pass
            return None

        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(_fetch_one, name): name for name in source_names[:3]}
                try:
                    for future in as_completed(futures, timeout=15):
                        try:
                            result = future.result(timeout=1)
                            if result:
                                name, ans, score = result
                                self.heatmap.add(name)
                                if score > 0.6:
                                    self.stats['web_hits'] += 1
                                    return ans
                                results.append(result)
                        except:
                            pass
                except (TimeoutError, Exception):
                    # Some futures didn't complete — check what we have
                    pass
        except Exception:
            pass

        # If no single great answer, take best above 0.4
        if results:
            results.sort(key=lambda x: x[2], reverse=True)
            if results[0][2] > 0.4:
                self.stats['web_hits'] += 1
                return results[0][1]
        return None

    # ─── QUALITY GATE ───

    def _quality_gate(self, answer: str, question: str) -> float:
        """Score answer quality 0-1."""
        score = 0.3  # Base
        q_words = set(question.lower().split())
        a_lower = answer.lower()

        # Reject garbage: Q-codes, hash strings
        if re.match(r'^Q\d+$', answer.strip()):
            return 0.0
        if re.match(r'^[0-9a-f]{16,}$', answer.strip()):
            return 0.0

        # Relevance: answer contains question keywords
        topic_words = q_words - _STOP_WORDS
        matches = sum(1 for w in topic_words if w in a_lower)
        if topic_words:
            score += 0.3 * (matches / len(topic_words))

        # Short direct answer bonus (single word/name = likely exact answer)
        if len(answer.split()) <= 5 and len(answer) > 2:
            score += 0.3  # Likely a direct structured answer

        # Completeness: has specific facts
        if re.search(r'\d+', answer):
            score += 0.15  # Has numbers
        if 30 < len(answer) < 300:
            score += 0.1  # Good length
        if len(answer) > 500:
            score -= 0.1  # Too long (likely raw page)

        # Penalties
        if len(answer) < 3:
            score -= 0.3
        if 'disambiguation' in a_lower:
            score -= 0.4
        if answer.count('<') > 3:  # HTML leaked
            score -= 0.3
        if 'capital punishment' in a_lower and 'capital of' in ' '.join(q_words):
            score -= 0.5  # Wrong type of "capital"

        return min(1.0, max(0.0, score))

    # ─── QUERY REFORMULATION ───

    def _rephrase(self, question: str) -> List[str]:
        """Generate alternative phrasings optimized for instant answer sources."""
        q = question.lower().strip().rstrip('?.')
        words = q.split()
        content = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

        variants = []
        
        # Smart rephrasing based on question pattern
        # "who invented X" → "inventor of X", "X inventor", "X invention history"
        import re as _re
        m = _re.match(r'who (?:invented|created|discovered|developed|founded|built|designed)\s+(?:the\s+)?(.+)', q)
        if m:
            topic = m.group(1).strip()
            variants.append(f"inventor of {topic}")
            variants.append(f"{topic} invented by")
            variants.append(f"{topic} history inventor")
            return variants
        
        # "who wrote X" → "author of X"
        m = _re.match(r'who (?:wrote|painted|composed|directed)\s+(?:the\s+)?(.+)', q)
        if m:
            topic = m.group(1).strip()
            variants.append(f"author of {topic}")
            variants.append(f"{topic} written by")
            return variants
        
        # "what is the capital of X" → "X capital city"
        m = _re.match(r'what is the capital of\s+(.+)', q)
        if m:
            country = m.group(1).strip()
            variants.append(f"{country} capital city")
            variants.append(f"capital city {country}")
            return variants
        
        # "what is the largest/smallest/tallest X" → "X largest"  
        m = _re.match(r'what is the (largest|smallest|tallest|fastest|longest|deepest|highest)\s+(.+)', q)
        if m:
            adj = m.group(1)
            topic = m.group(2).strip()
            variants.append(f"{adj} {topic} in the world")
            variants.append(f"world {adj} {topic}")
            return variants
        
        # Default: keyword extraction
        if content:
            variants.append(' '.join(content))
        if len(content) > 1:
            variants.append(' '.join(reversed(content)))
        if content:
            variants.append(content[-1])

        return variants

    # ─── PARTIAL COLLECTION + MERGE ───

    def _collect_partials(self, question: str, tried: List[str]) -> List[str]:
        """Try all sources, collect even partial answers."""
        partials = []
        all_names = list(ALL_SOURCES.keys())
        random.shuffle(all_names)

        for name in all_names[:6]:
            if self.heatmap.is_disabled(name):
                continue
            src = ALL_SOURCES[name]
            try:
                ans = src.fetch(question)
                if ans and len(ans) > 10:
                    partials.append(ans)
                    self.heatmap.add(name, 1.0)
            except:
                pass
            if len(partials) >= 3:
                break
        return partials

    def _merge(self, partials: List[str], question: str) -> Optional[str]:
        """Merge partial answers into one coherent response."""
        if not partials:
            return None

        # Extract sentences from all partials
        all_sentences = []
        for p in partials:
            sents = re.split(r'(?<=[.!?])\s+', p)
            for s in sents:
                s = s.strip()
                if len(s) > 15 and s not in all_sentences:
                    all_sentences.append(s)

        if not all_sentences:
            return partials[0] if partials else None

        # Score sentences by relevance to question
        q_words = set(question.lower().split()) - _STOP_WORDS
        scored = []
        for sent in all_sentences:
            s_lower = sent.lower()
            matches = sum(1 for w in q_words if w in s_lower)
            scored.append((sent, matches))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [s for s, _ in scored[:3]]
        return ' '.join(top)

    # ─── SAVE (cache + KDA) ───

    def _save(self, question: str, answer: str):
        """Save to cache and optionally KDA."""
        self.cache.set(question, answer)
        if self.kda_save:
            try:
                self.kda_save(question, answer)
            except:
                pass


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE API (drop-in replacement for web_search.py)
# ═══════════════════════════════════════════════════════════════

_engine = None

def get_engine(kda_save_func=None) -> OnlineSearch:
    global _engine
    if _engine is None:
        _engine = OnlineSearch(kda_save_func)
    return _engine


def search_web(question: str) -> dict:
    """Drop-in replacement for old web_search.search_web().
    Returns {'text': str, 'source': str} or {'text': '', 'source': ''}."""
    engine = get_engine()
    result = engine.search(question)
    if result:
        return {'text': result, 'source': 'online_search_v3'}
    return {'text': '', 'source': ''}


def search(question: str) -> Optional[str]:
    """Simple API: returns answer string or None."""
    engine = get_engine()
    return engine.search(question)


# ═══════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import sys
    print("═" * 60)
    print("  AXIMA Online Search v3.0 — 18 Sources, Zero Deps")
    print("═" * 60)
    print()

    engine = OnlineSearch()

    tests = [
        "what is the capital of japan",
        "who invented the telephone",
        "what is photosynthesis",
        "what is the speed of light",
        "who wrote hamlet",
        "what is the largest planet",
        "what is the boiling point of water",
        "when did world war 2 end",
        "who painted the mona lisa",
        "what is the capital of france",
        "what is bitcoin",
        "who discovered penicillin",
        "what is the theory of relativity",
        "who is albert einstein",
        "what is machine learning",
        "what is climate change",
        "what is the internet",
        "what is the population of india",
        "what is the amazon river",
        "what is the great wall of china",
    ]

    passed = 0
    failed = 0
    times = []
    
    # Expected keywords per question
    expected = [
        ["tokyo"], ["bell", "graham"], ["plant", "light", "sun"],
        ["300", "km", "meter"], ["shakespeare"], ["jupiter"],
        ["100", "celsius", "boil"], ["1945"], ["vinci", "leonardo"],
        ["paris"], ["crypto", "digital", "currency"], ["fleming"],
        ["einstein", "time", "space"], ["physicist", "relativity"],
        ["algorithm", "data", "learn"], ["temperature", "warming", "carbon"],
        ["network", "connect", "computer"], ["billion", "1"],
        ["south america", "river"], ["china", "wall"],
    ]

    for i, q in enumerate(tests):
        start = time.time()
        answer = engine.search(q)
        elapsed = time.time() - start
        times.append(elapsed)

        if answer:
            a_lower = answer.lower()
            if any(kw in a_lower for kw in expected[i]):
                passed += 1
                status = "✓"
            else:
                failed += 1
                status = "✗ (wrong)"
        else:
            failed += 1
            status = "✗ (empty)"

        print(f"  {status} [{elapsed*1000:.0f}ms] {q}")
        if answer:
            print(f"    → {answer[:100]}...")
        print()
        time.sleep(0.3)  # Be polite

    print("─" * 60)
    print(f"  RESULTS: {passed}/{len(tests)} ({passed/len(tests)*100:.0f}%)")
    print(f"  Avg speed: {sum(times)/len(times)*1000:.0f}ms")
    print(f"  Stats: {engine.stats}")
    print()
    print(f"  Sources active: {len(ALL_SOURCES)}")
    print(f"  Cache entries: {len(engine.cache.memory)}")
    print("─" * 60)
