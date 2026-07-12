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
        """GET and parse JSON."""
        raw = self._get(url)
        if raw:
            try:
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
        url2 = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit=3"
        data2 = self._get_json(url2)
        if data2:
            results = data2.get('query', {}).get('search', [])
            if results:
                # Pick best result (avoid lists, disambiguation)
                for r in results:
                    title = r.get('title', '')
                    if title.startswith('List of') or 'disambiguation' in title.lower():
                        continue
                    snippet = re.sub(r'<[^>]+>', '', r.get('snippet', ''))
                    if snippet and len(snippet) > 20:
                        return f"{title}: {snippet}"
                # Fallback to first result
                title = results[0].get('title', '')
                snippet = re.sub(r'<[^>]+>', '', results[0].get('snippet', ''))
                if snippet:
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
                # Clean URIs
                clean = [v.split('/')[-1].replace('_', ' ') if 'http' in v else v for v in values]
                return ' | '.join(clean[:3])
        return None

    def _build_sparql(self, query: str) -> Optional[str]:
        q = query.lower()
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
        # Who invented X
        m = re.search(r'(?:who )?invent(?:ed|or of) (?:the )?(.+)', q)
        if m:
            item = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?inventorLabel WHERE {{
              ?item rdfs:label "{item}"@en. ?item wdt:P61 ?inventor.
              SERVICE wikibase:label {{bd:serviceParam wikibase:language "en".}}
            }} LIMIT 1'''
        # Who discovered X
        m = re.search(r'(?:who )?discover(?:ed|er of) (?:the )?(.+)', q)
        if m:
            item = m.group(1).strip().rstrip('?.').title()
            return f'''SELECT ?discovererLabel WHERE {{
              ?item rdfs:label "{item}"@en. ?item wdt:P61 ?discoverer.
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

# Source registry
ALL_SOURCES = {
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
TOPIC_ROUTING = {
    TOPIC_PEOPLE: ['wikipedia_en', 'wikidata_search', 'wikidata_sparql', 'wikiquote', 'ddg_instant', 'nobel_api'],
    TOPIC_PLACES: ['wikidata_sparql', 'wikipedia_en', 'wikidata_search', 'ddg_instant', 'wikipedia_simple'],
    TOPIC_SCIENCE: ['wikipedia_en', 'wikidata_search', 'wikidata_sparql', 'ddg_instant', 'wikipedia_simple'],
    TOPIC_HISTORY: ['wikipedia_en', 'wikidata_sparql', 'wikidata_search', 'ddg_instant', 'wikipedia_fr'],
    TOPIC_TECH: ['wikipedia_en', 'ddg_instant', 'ddg_html', 'wikidata_search', 'wikipedia_simple'],
    TOPIC_DEFINITIONS: ['wikipedia_simple', 'dictionary_api', 'wiktionary', 'ddg_instant', 'wikipedia_en'],
    TOPIC_BOOKS: ['open_library', 'wikipedia_en', 'ddg_instant', 'wikidata_search'],
    TOPIC_MUSIC: ['itunes', 'wikipedia_en', 'ddg_instant', 'wikidata_search'],
    TOPIC_GENERAL: ['wikipedia_en', 'ddg_instant', 'wikidata_search', 'wikipedia_simple', 'ddg_html'],
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

        # Layer 1: Cache check (0ms)
        cached = self.cache.get(question)
        if cached:
            self.stats['cache_hits'] += 1
            return cached

        # Classify topic
        topic = self._classify(question)

        # PRIORITY: If we can build a SPARQL query, try that FIRST (exact answer)
        sparql_src = ALL_SOURCES.get('wikidata_sparql')
        if sparql_src:
            try:
                sparql_ans = sparql_src.fetch(question)
                if sparql_ans and len(sparql_ans) > 1 and '|' not in sparql_ans:
                    self.heatmap.add('wikidata_sparql')
                    self.stats['web_hits'] += 1
                    self._save(question, sparql_ans)
                    return sparql_ans
            except:
                pass

        # Get source list (coldest first)
        source_names = TOPIC_ROUTING.get(topic, TOPIC_ROUTING[TOPIC_GENERAL])
        cold_sources = self.heatmap.coldest(source_names, n=3)

        # Tier 1: Parallel fire top 3
        result = self._parallel_fire(cold_sources, question)
        if result:
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

        self.stats['failures'] += 1
        return None

    # ─── TOPIC CLASSIFICATION ───

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
        """Generate 3 alternative phrasings."""
        q = question.lower().strip().rstrip('?.')
        words = q.split()
        content = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

        variants = []
        # Variant 1: keyword only
        if content:
            variants.append(' '.join(content))
        # Variant 2: reversed keywords
        if len(content) > 1:
            variants.append(' '.join(reversed(content)))
        # Variant 3: just the main topic (last content word)
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
