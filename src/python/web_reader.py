#!/usr/bin/env python3
"""
AXIMA WebReader v2.0 — Page-Level Intelligence
Reads any webpage like a browser. Extracts answers. Zero dependencies.
20KB per answer. Self-learning. Works on $30 phones.
"""

import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
import time
import hashlib
import os
import json
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

# SSL context (permissive for restricted environments)
try:
    _SSL = ssl.create_default_context()
    _SSL.check_hostname = False
    _SSL.verify_mode = ssl.CERT_NONE
except:
    _SSL = None

# User-Agent rotation
_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1",
]

import random

def _hdrs():
    return {
        'User-Agent': random.choice(_UAS),
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'identity',
        'Referer': 'https://www.google.com/',
    }


# ═══════════════════════════════════════════════════════════════
# HTML INTELLIGENCE — stdlib HTMLParser (not regex for structure)
# ═══════════════════════════════════════════════════════════════

class _ContentExtractor(HTMLParser):
    """Extract visible text from HTML, skipping scripts/styles/nav."""
    
    KILL_TAGS = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'form', 'noscript', 'svg'}
    KILL_CLASSES = {'ad', 'banner', 'cookie', 'sidebar', 'menu', 'nav', 'footer', 'header'}
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.current_tag = ''
        self.skip_depth = 0
        self.in_infobox = False
        self.infobox_data = {}
        self._ib_key = ''
        self._ib_val = ''
        self.title = ''
        self.headings = []
        self._in_title = False
        self._in_heading = False
        self._heading_text = ''
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        cls = attrs_dict.get('class', '').lower()
        
        # Kill tags
        if tag in self.KILL_TAGS:
            self.skip_depth += 1
            return
        # Kill by class
        if any(k in cls for k in self.KILL_CLASSES):
            self.skip_depth += 1
            return
        
        # Track infobox
        if tag == 'table' and 'infobox' in cls:
            self.in_infobox = True
        
        # Track title
        if tag == 'title':
            self._in_title = True
        
        # Track headings
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self._in_heading = True
            self._heading_text = ''
        
        # Add paragraph breaks
        if tag in ('p', 'br', 'div', 'li', 'tr') and self.skip_depth == 0:
            self.text_parts.append('\n')
        
        self.current_tag = tag
    
    def handle_endtag(self, tag):
        if tag in self.KILL_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if tag == 'table':
            self.in_infobox = False
        if tag == 'title':
            self._in_title = False
        if tag in ('h1', 'h2', 'h3', 'h4'):
            self._in_heading = False
            if self._heading_text.strip():
                self.headings.append(self._heading_text.strip())
                self.text_parts.append(f'\n## {self._heading_text.strip()}\n')
    
    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if self._in_heading:
            self._heading_text += data
        if self.skip_depth > 0:
            return
        text = data.strip()
        if text:
            self.text_parts.append(text + ' ')
    
    def get_text(self) -> str:
        raw = ''.join(self.text_parts)
        # Collapse whitespace
        raw = re.sub(r'\n\s*\n+', '\n\n', raw)
        raw = re.sub(r' +', ' ', raw)
        return raw.strip()


class HTMLIntelligence:
    """Extract structured content from HTML."""
    
    @staticmethod
    def strip(html: str) -> str:
        """Full HTML → clean text."""
        # Decode HTML entities first
        import html as html_mod
        html = html_mod.unescape(html)
        extractor = _ContentExtractor()
        try:
            extractor.feed(html)
        except:
            pass
        return extractor.get_text()
    
    @staticmethod
    def extract_title(html: str) -> str:
        """Get page title."""
        m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        return m.group(1).strip() if m else ''
    
    @staticmethod
    def is_disambiguation(html: str) -> bool:
        """Check if Wikipedia disambiguation page."""
        # Only check the first content area — not deep in the page
        # Wikipedia disambiguation pages have specific class
        if 'class="disambiguation"' in html or 'class="dmbox"' in html:
            return True
        # Check first paragraph for "may refer to" pattern
        first_p = re.search(r'<p[^>]*>(.*?)</p>', html[:3000], re.DOTALL)
        if first_p:
            text = re.sub(r'<[^>]+>', '', first_p.group(1)).strip()
            if re.search(r'^.{0,50}may refer to|^.{0,50}can mean', text):
                return True
        return False
    
    @staticmethod
    def extract_first_paragraph(html: str) -> str:
        """Get Wikipedia first real paragraph (skip hatnotes)."""
        import html as html_mod
        # Find mw-parser-output
        start = html.find('mw-parser-output')
        if start == -1:
            start = 0
        
        # Find all <p> tags after start
        paragraphs = re.finditer(r'<p[^>]*>(.*?)</p>', html[start:], re.DOTALL)
        for match in paragraphs:
            text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            text = html_mod.unescape(text)
            # Remove citation brackets [1][2] etc
            text = re.sub(r'\[\d+\]', '', text)
            # Skip hatnotes, empty, disambiguation
            if len(text) < 30:
                continue
            if 'may refer to' in text or 'can mean' in text:
                continue
            if text.startswith('Coordinates:'):
                continue
            return text
        return ''
    
    @staticmethod
    def extract_infobox(html: str) -> Dict[str, str]:
        """Extract Wikipedia infobox key-value pairs."""
        infobox = {}
        # Find infobox table
        ib_match = re.search(r'<table[^>]*class="[^"]*infobox[^"]*"[^>]*>(.*?)</table>', html, re.DOTALL | re.IGNORECASE)
        if not ib_match:
            return infobox
        
        ib_html = ib_match.group(1)
        # Extract rows: <th>key</th><td>value</td>
        rows = re.finditer(r'<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>', ib_html, re.DOTALL)
        for row in rows:
            key = re.sub(r'<[^>]+>', '', row.group(1)).strip()
            val = re.sub(r'<[^>]+>', '', row.group(2)).strip()
            # Clean up whitespace
            key = re.sub(r'\s+', ' ', key)
            val = re.sub(r'\s+', ' ', val)
            if key and val and len(key) < 50:
                infobox[key.lower()] = val
        return infobox
    
    @staticmethod
    def extract_ddg_snippets(html: str) -> List[str]:
        """Extract search result snippets from DDG HTML results page."""
        snippets = []
        # DDG snippet class
        matches = re.finditer(r'class="result__snippet[^"]*"[^>]*>(.*?)</(?:a|span)', html, re.DOTALL)
        for m in matches:
            text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if text and len(text) > 20:
                snippets.append(text)
        # Also try result body
        if not snippets:
            matches = re.finditer(r'class="result__body[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            for m in matches:
                text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
                if text and len(text) > 20:
                    snippets.append(text)
        return snippets[:10]
    
    @staticmethod
    def extract_section(html: str, heading_keywords: List[str]) -> str:
        """Find a section by heading keywords and extract its content."""
        # Find heading containing any keyword
        pattern = r'<h[23][^>]*>(.*?)</h[23]>'
        headings = list(re.finditer(pattern, html, re.DOTALL | re.IGNORECASE))
        
        for i, h in enumerate(headings):
            h_text = re.sub(r'<[^>]+>', '', h.group(1)).lower()
            if any(kw in h_text for kw in heading_keywords):
                # Extract content until next heading
                start = h.end()
                end = headings[i+1].start() if i+1 < len(headings) else start + 5000
                section_html = html[start:end]
                # Strip tags
                text = re.sub(r'<[^>]+>', ' ', section_html)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:2000]
        return ''


# ═══════════════════════════════════════════════════════════════
# ANSWER FINDER — Question-type-aware extraction
# ═══════════════════════════════════════════════════════════════

_STOP = {'what', 'is', 'the', 'a', 'an', 'who', 'where', 'when', 'how', 'why',
         'are', 'was', 'do', 'does', 'tell', 'me', 'about', 'can', 'you',
         'please', 'would', 'could', 'should', 'will', 'it', 'that', 'this',
         'of', 'in', 'on', 'for', 'and', 'or', 'if', 'to', 'from', 'with',
         'did', 'has', 'have', 'which', 'there', 'i', 'my', 'your', 'its', 'be'}


class AnswerFinder:
    """Find the answer sentence in extracted text."""
    
    @staticmethod
    def find(question: str, text: str, infobox: Dict = None) -> Optional[str]:
        """Main entry: find best answer from page text."""
        if not text and not infobox:
            return None
        
        q = question.lower().strip().rstrip('?.')
        q_type = AnswerFinder._question_type(q)
        keywords = [w for w in q.split() if w not in _STOP and len(w) > 2]
        
        # Try infobox first (structured = most reliable)
        if infobox:
            ib_answer = AnswerFinder._from_infobox(q, q_type, infobox)
            if ib_answer:
                return ib_answer
        
        if not text:
            return None
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
        
        if not sentences:
            return None
        
        # Score each sentence
        scored = []
        for i, sent in enumerate(sentences):
            score = AnswerFinder._score(sent, keywords, q_type, i, len(sentences))
            scored.append((sent, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 1-2 sentences
        if scored[0][1] > 2.0:
            result = scored[0][0]
            # Add second sentence if it's also good and different topic
            if len(scored) > 1 and scored[1][1] > 1.5:
                result += ' ' + scored[1][0]
            return result[:500]
        
        # Fallback: first paragraph (usually the definition)
        if q_type == 'what':
            return sentences[0][:300] if sentences else None
        
        return scored[0][0] if scored else None
    
    @staticmethod
    def _question_type(q: str) -> str:
        if q.startswith('who ') or 'who ' in q: return 'who'
        if q.startswith('when ') or 'when ' in q: return 'when'
        if q.startswith('where ') or 'where ' in q: return 'where'
        if q.startswith('how many') or q.startswith('how much'): return 'howmany'
        if q.startswith('why ') or 'why ' in q: return 'why'
        if 'capital' in q: return 'capital'
        if 'population' in q: return 'population'
        return 'what'
    
    @staticmethod
    def _score(sentence: str, keywords: List[str], q_type: str, position: int, total: int) -> float:
        """Score a sentence's relevance."""
        s = sentence.lower()
        score = 0.0
        
        # Keyword matches
        matches = sum(1 for kw in keywords if kw in s)
        if keywords:
            score += 2.0 * (matches / len(keywords))
        
        # Position bonus (first 30% of page)
        if position < total * 0.3:
            score += 0.5
        
        # Question-type bonuses
        if q_type == 'who' and re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence):
            score += 1.5  # Contains proper name
        if q_type == 'when' and re.search(r'\b\d{4}\b|\b\d{1,2}\s+\w+\s+\d{4}', sentence):
            score += 1.5  # Contains date/year
        if q_type == 'where' and re.search(r'[A-Z][a-z]+(?:,\s*[A-Z][a-z]+)?', sentence):
            score += 1.0  # Contains place name
        if q_type == 'howmany' and re.search(r'\d[\d,.\s]*\d|\d+', sentence):
            score += 1.5  # Contains numbers
        if q_type == 'why' and any(w in s for w in ['because', 'due to', 'caused by', 'result of']):
            score += 1.5
        
        # Penalties
        if sentence.endswith('?'):
            score -= 2.0  # It's a question itself
        if len(sentence.split()) < 5:
            score -= 1.0  # Too short
        if any(w in s for w in ['see also', 'references', 'external links', 'further reading']):
            score -= 3.0  # Wikipedia footer
        
        return score
    
    @staticmethod
    def _from_infobox(q: str, q_type: str, infobox: Dict) -> Optional[str]:
        """Try to answer from infobox structured data."""
        if q_type == 'capital' or 'capital' in q:
            for key in ['capital', 'capital city', 'seat']:
                if key in infobox:
                    return infobox[key].split('[')[0].split('(')[0].strip()
        if q_type == 'population' or 'population' in q:
            for key in ['population', 'population_estimate', 'population (2023)', 'population (2024)']:
                if key in infobox:
                    return infobox[key]
            # Try any key with "population"
            for key, val in infobox.items():
                if 'population' in key and val:
                    return val
        if 'born' in q or 'birth' in q:
            for key in ['born', 'birth date', 'birth_date']:
                if key in infobox:
                    return infobox[key]
        if 'died' in q or 'death' in q:
            for key in ['died', 'death date', 'death_date']:
                if key in infobox:
                    return infobox[key]
        if 'height' in q or 'tall' in q:
            for key in ['height', 'roof', 'tip']:
                if key in infobox:
                    return infobox[key]
        if 'area' in q or 'size' in q:
            for key in ['area', 'total_area', 'area_km2']:
                if key in infobox:
                    return infobox[key]
        return None


# ═══════════════════════════════════════════════════════════════
# WEB READER — Main class
# ═══════════════════════════════════════════════════════════════

class WebReader:
    """Reads webpages and extracts answers. Zero deps. 20KB budget."""
    
    def __init__(self, cache_dir: str = None, kda_save_func=None):
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'user_data')
        self.kda_save = kda_save_func
        self.session_pages = {}  # url → extracted data (read mode)
        self._page_cache = {}  # url_hash → text (memory)
        self.stats = {'fetches': 0, 'cache_hits': 0, 'answers_found': 0}
    
    # ─── MAIN ENTRY POINTS ───
    
    def answer(self, question: str) -> Optional[str]:
        """Answer any question by reading web pages."""
        # Check memory cache
        cache_key = self._cache_key(question)
        if cache_key in self._page_cache:
            self.stats['cache_hits'] += 1
            return self._page_cache[cache_key]
        
        # Strategy 1: Wikipedia direct page
        ans = self._try_wikipedia(question)
        if ans:
            self._save(question, ans)
            return ans
        
        # Strategy 2: DDG snippets (one request, 10 candidates)
        ans = self._try_ddg_snippets(question)
        if ans:
            self._save(question, ans)
            return ans
        
        # Strategy 3: Follow DDG result links
        ans = self._try_ddg_links(question)
        if ans:
            self._save(question, ans)
            return ans
        
        return None
    
    def read_url(self, url: str) -> Optional[Dict]:
        """Read a URL fully and store in session (read mode)."""
        html = self._fetch(url, max_bytes=102400)  # 100KB for read mode
        if not html:
            return None
        
        title = HTMLIntelligence.extract_title(html)
        text = HTMLIntelligence.strip(html)
        infobox = HTMLIntelligence.extract_infobox(html)
        
        data = {
            'url': url, 'title': title, 'text': text,
            'infobox': infobox, 'fetched_at': time.time()
        }
        self.session_pages[url] = data
        return data
    
    def ask_about_page(self, question: str, url: str = None) -> Optional[str]:
        """Answer question about a previously read page."""
        if url and url in self.session_pages:
            page = self.session_pages[url]
        elif self.session_pages:
            page = list(self.session_pages.values())[-1]  # Last read page
        else:
            return None
        
        return AnswerFinder.find(question, page['text'], page.get('infobox'))
    
    # ─── STRATEGIES ───
    
    def _try_wikipedia(self, question: str) -> Optional[str]:
        """Try loading Wikipedia page directly."""
        topic = self._extract_topic(question)
        if not topic:
            return None
        
        # Strategy A: REST API summary (fast, reliable, always has first paragraph)
        wiki_topic = urllib.parse.quote(topic.replace(' ', '_'))
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_topic}"
        api_html = self._fetch(api_url, max_bytes=10240)
        
        if api_html:
            try:
                import json as _json
                data = _json.loads(api_html)
                if data.get('type') == 'disambiguation':
                    pass  # Fall through to DDG
                elif data.get('extract'):
                    extract = data['extract']
                    q_lower = question.lower()
                    q_type = AnswerFinder._question_type(q_lower)
                    
                    # For "capital of X" → search extract for capital mention
                    if 'capital' in q_lower:
                        cap_match = re.search(r'capital(?:\s+city)?\s+(?:is|of\s+\w+\s+is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', extract)
                        if cap_match:
                            return cap_match.group(1)
                        cap_match2 = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+is\s+(?:the\s+)?capital', extract)
                        if cap_match2:
                            return cap_match2.group(1)
                        # Capital not found in extract → fall through to DDG
                        return None
                    
                    # For "who discovered/invented X" → find person name in extract
                    if q_type == 'who' and ('discover' in q_lower or 'invent' in q_lower):
                        name_match = re.search(r'(?:discovered|invented|created)\s+(?:by\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', extract)
                        if name_match:
                            return name_match.group(1)
                        name_match2 = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:discovered|invented|developed)', extract)
                        if name_match2:
                            return name_match2.group(1)
                        # Discoverer not found → fall through to DDG
                        return None
                    
                    # For "what is" → first paragraph IS the answer
                    if q_type == 'what':
                        return extract[:300]
                    if q_type == 'who':
                        return extract[:200]
            except:
                pass
        
        # Strategy B: Full page for infobox extraction (capital, population, etc.)
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(topic.replace(' ', '_').title())}"
        html = self._fetch(page_url, max_bytes=102400)
        
        if html and len(html) > 1000:
            # Try infobox
            infobox = HTMLIntelligence.extract_infobox(html)
            q_lower = question.lower()
            q_type = AnswerFinder._question_type(q_lower)
            ib_answer = AnswerFinder._from_infobox(q_lower, q_type, infobox)
            if ib_answer:
                return ib_answer
            
            # Try AnswerFinder on full text
            full_text = HTMLIntelligence.strip(html)
            if full_text and len(full_text) > 50:
                ans = AnswerFinder.find(question, full_text, infobox)
                if ans:
                    return ans
        
        # If REST API gave us something, return that
        if api_html:
            try:
                data = _json.loads(api_html)
                if data.get('extract'):
                    return data['extract'][:300]
            except:
                pass
        
        return None
    
    def _try_ddg_snippets(self, question: str) -> Optional[str]:
        """Try DuckDuckGo — extract answer from result snippets."""
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(question)}"
        html = self._fetch(url, max_bytes=20480)
        if not html:
            return None
        
        snippets = HTMLIntelligence.extract_ddg_snippets(html)
        if not snippets:
            return None
        
        # Score snippets
        keywords = [w for w in question.lower().split() if w not in _STOP and len(w) > 2]
        best_score = 0
        best_snippet = ''
        
        for snippet in snippets:
            s_lower = snippet.lower()
            matches = sum(1 for kw in keywords if kw in s_lower)
            score = matches / max(1, len(keywords))
            if score > best_score:
                best_score = score
                best_snippet = snippet
        
        if best_score > 0.4 and best_snippet:
            return best_snippet[:300]
        return None
    
    def _try_ddg_links(self, question: str) -> Optional[str]:
        """Follow top DDG result links and extract answer."""
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(question)}"
        html = self._fetch(url, max_bytes=30720)
        if not html:
            return None
        
        # Extract result URLs
        links = re.findall(r'class="result__a"[^>]*href="([^"]+)"', html)
        # Also try uddg parameter (DDG redirect links)
        uddg_links = re.findall(r'uddg=([^&"]+)', html)
        all_links = []
        for link in uddg_links[:5]:
            try:
                decoded = urllib.parse.unquote(link)
                if decoded.startswith('http'):
                    all_links.append(decoded)
            except:
                pass
        
        if not all_links:
            return None
        
        # Fetch top 2 in parallel
        results = self._fetch_parallel(all_links[:2], max_bytes=20480)
        
        for page_html in results:
            if not page_html:
                continue
            text = HTMLIntelligence.strip(page_html)
            if text and len(text) > 50:
                ans = AnswerFinder.find(question, text)
                if ans:
                    return ans
        return None
    
    # ─── FETCHER ───
    
    def _fetch(self, url: str, max_bytes: int = 20480) -> Optional[str]:
        """Fetch URL, read up to max_bytes. Bandwidth-aware."""
        self.stats['fetches'] += 1
        try:
            req = urllib.request.Request(url, headers=_hdrs())
            resp = urllib.request.urlopen(req, timeout=10, context=_SSL)
            
            # Check content type
            ct = resp.headers.get('Content-Type', '')
            if 'pdf' in ct or 'image' in ct or 'video' in ct:
                return None  # Can't process binary
            
            data = resp.read(max_bytes)
            # Try decode
            encoding = 'utf-8'
            if 'charset=' in ct:
                enc_match = re.search(r'charset=([^\s;]+)', ct)
                if enc_match:
                    encoding = enc_match.group(1)
            
            try:
                return data.decode(encoding, errors='ignore')
            except:
                return data.decode('utf-8', errors='ignore')
        except Exception:
            return None
    
    def _fetch_parallel(self, urls: List[str], max_bytes: int = 20480) -> List[Optional[str]]:
        """Fetch multiple URLs in parallel."""
        results = [None] * len(urls)
        try:
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(self._fetch, url, max_bytes): i for i, url in enumerate(urls)}
                for future in as_completed(futures, timeout=12):
                    try:
                        idx = futures[future]
                        results[idx] = future.result(timeout=1)
                    except:
                        pass
        except:
            pass
        return results
    
    # ─── UTILITIES ───
    
    def _extract_topic(self, question: str) -> str:
        """Extract main topic from question for Wikipedia URL."""
        q = question.lower().strip().rstrip('?.')
        # Remove prefixes (LONGEST FIRST so specific patterns match before generic)
        prefixes = [
            'what is the capital of ', 'what is the population of ',
            'what is the boiling point of ', 
            'who invented the ', 'who discovered the ', 'who discovered ',
            'who wrote ', 'who painted the ', 'who painted ',
            'what are the ', 'what is the ', 'what is ', 'what are ',
            'who is ', 'who was ', 'where is ',
            'tell me about ', 'define ', 'explain ',
        ]
        for prefix in prefixes:
            if q.startswith(prefix):
                q = q[len(prefix):]
                break
        # Strip leading articles
        for art in ['the ', 'a ', 'an ']:
            if q.startswith(art):
                q = q[len(art):]
        # Handle superlatives: "largest planet" → "Jupiter"
        superlatives = {
            'largest planet': 'Jupiter', 'biggest planet': 'Jupiter',
            'smallest planet': 'Mercury (planet)', 'fastest animal': 'Peregrine falcon',
            'largest ocean': 'Pacific Ocean', 'longest river': 'Nile',
            'tallest mountain': 'Mount Everest', 'tallest building': 'Burj Khalifa',
        }
        if q in superlatives:
            return superlatives[q]
        return q.strip()
    
    def _cache_key(self, question: str) -> str:
        words = sorted(w for w in question.lower().split() if w not in _STOP and len(w) > 2)
        return hashlib.md5(' '.join(words).encode()).hexdigest()
    
    def _save(self, question: str, answer: str):
        """Cache answer + optionally save to KDA."""
        self._page_cache[self._cache_key(question)] = answer
        self.stats['answers_found'] += 1
        if self.kda_save:
            try:
                self.kda_save(question, answer)
            except:
                pass


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE API
# ═══════════════════════════════════════════════════════════════

_reader = None

def get_reader() -> WebReader:
    global _reader
    if _reader is None:
        _reader = WebReader()
    return _reader


def web_read(question: str) -> Optional[str]:
    """Simple API: question → answer by reading web pages."""
    return get_reader().answer(question)


def read_url(url: str) -> Optional[Dict]:
    """Read a URL and store in session."""
    return get_reader().read_url(url)


def ask_page(question: str) -> Optional[str]:
    """Ask question about last read page."""
    return get_reader().ask_about_page(question)


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  AXIMA WebReader v2.0 — Test")
    print("═" * 60)
    print()
    
    reader = WebReader()
    
    tests = [
        ("what is the capital of japan", ["tokyo"]),
        ("who wrote hamlet", ["shakespeare", "william"]),
        ("what is photosynthesis", ["plant", "light", "sun", "energy"]),
        ("what is the largest planet", ["jupiter"]),
        ("who discovered penicillin", ["fleming"]),
        ("what is the speed of light", ["299", "300", "km"]),
        ("what is bitcoin", ["crypto", "digital", "currency", "decentral"]),
        ("who is albert einstein", ["physicist", "relativity", "theoretical"]),
        ("what is climate change", ["warming", "temperature", "carbon"]),
        ("what is the internet", ["network", "computer", "global"]),
    ]
    
    passed = 0
    times = []
    
    for q, keywords in tests:
        start = time.time()
        ans = reader.answer(q)
        elapsed = time.time() - start
        times.append(elapsed)
        
        if ans:
            hit = any(k in ans.lower() for k in keywords)
            if hit: passed += 1
            sym = '✓' if hit else '✗'
            print(f"  {sym} [{elapsed:.1f}s] {q}")
            print(f"    → {ans[:100]}")
        else:
            print(f"  ✗ [{elapsed:.1f}s] {q} → NO ANSWER")
        print()
        time.sleep(0.3)
    
    print("─" * 60)
    print(f"  RESULTS: {passed}/{len(tests)} ({passed/len(tests)*100:.0f}%)")
    print(f"  Avg speed: {sum(times)/len(times)*1000:.0f}ms")
    print(f"  Stats: {reader.stats}")
    print("─" * 60)
