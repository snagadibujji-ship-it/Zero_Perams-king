"""
AXIMA BRAIN — Module 1: Document Ingestion
Built by: Ghias + Kiro

Takes ANY text input (PDF extracted, pasted notes, URL content)
and builds a searchable, tagged, connected knowledge structure.

No LLM needed. Uses grammar patterns, term frequency, and structure detection.
"""

import re
import json
import os
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter


# ══════════════════════════════════════════════════════════════════════════════
# KNOWLEDGE CHUNK — atomic unit of stored knowledge
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Chunk:
    """A semantic unit of knowledge from a document."""
    id: str                                 # unique hash
    text: str                               # original text
    source: str                             # document name/path
    section: str = ""                       # section/chapter header
    page: int = 0                           # page number if known
    chunk_type: str = ""                    # definition|theorem|example|procedure|data|opinion|narrative
    key_terms: List[str] = field(default_factory=list)      # important nouns/terms
    relationships: List[Tuple[str,str,str]] = field(default_factory=list)  # (subject, relation, object)
    topic: str = ""                         # auto-detected topic cluster
    formulas: List[str] = field(default_factory=list)        # extracted equations


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT BRAIN — The ingestion engine
# ══════════════════════════════════════════════════════════════════════════════

class DocumentBrain:
    """Ingest, chunk, tag, index any document. No LLM required."""

    def __init__(self, storage_dir: str = "user_data/brain"):
        self.storage_dir = storage_dir
        self.chunks: Dict[str, Chunk] = {}          # id → Chunk
        self.term_index: Dict[str, Set[str]] = {}   # word → set of chunk_ids
        self.type_index: Dict[str, List[str]] = {}  # chunk_type → chunk_ids
        self.topic_index: Dict[str, List[str]] = {} # topic → chunk_ids
        self.formula_index: Dict[str, str] = {}     # formula_lhs → chunk_id
        self.sources: Dict[str, dict] = {}          # source_name → metadata
        self._load()

    # ──────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────

    def ingest(self, text: str, source_name: str = "untitled", page: int = 0) -> int:
        """Ingest a document. Returns number of chunks created."""
        # Step 1: Split into semantic chunks
        raw_chunks = self._chunk_text(text)

        # Step 2: Process each chunk
        count = 0
        current_section = ""
        for raw in raw_chunks:
            # Detect if this is a section header
            if self._is_header(raw):
                current_section = raw.strip()
                continue

            # Create chunk
            chunk_id = self._hash(raw + source_name)
            if chunk_id in self.chunks:
                continue  # already ingested

            chunk = Chunk(
                id=chunk_id,
                text=raw,
                source=source_name,
                section=current_section,
                page=page,
            )

            # Step 3: Tag the chunk
            chunk.chunk_type = self._detect_type(raw)
            chunk.key_terms = self._extract_key_terms(raw)
            chunk.relationships = self._extract_relationships(raw)
            chunk.formulas = self._extract_formulas(raw)
            chunk.topic = self._detect_topic(raw, current_section)

            # Step 4: Index
            self.chunks[chunk_id] = chunk
            self._index_chunk(chunk)
            count += 1

        # Save metadata
        self.sources[source_name] = {
            "chunks": count,
            "pages": page,
            "topics": list(set(c.topic for c in self.chunks.values() if c.source == source_name and c.topic)),
        }

        self._save()
        return count

    def search(self, query: str, top_k: int = 5) -> List[Chunk]:
        """Search for relevant chunks using BM25-style ranking + exact match boost."""
        query_terms = self._tokenize(query.lower())
        scores: Dict[str, float] = {}

        for term in query_terms:
            if term in self.term_index:
                # IDF-like weight: rare terms matter more
                idf = len(self.chunks) / (1 + len(self.term_index[term]))
                for chunk_id in self.term_index[term]:
                    scores[chunk_id] = scores.get(chunk_id, 0) + idf

        # BOOST: chunks that contain the EXACT multi-word query phrase
        query_lower = query.lower()
        for chunk_id, chunk in self.chunks.items():
            chunk_lower = chunk.text.lower()
            # Exact phrase match = big boost
            for term in query_terms:
                if len(term) >= 4 and term in chunk_lower:
                    # Term appears in this chunk's actual text
                    count = chunk_lower.count(term)
                    scores[chunk_id] = scores.get(chunk_id, 0) + count * 2.0

        # Boost by type match
        question_type = self._question_to_chunk_type(query)
        if question_type:
            for chunk_id in self.type_index.get(question_type, []):
                if chunk_id in scores:
                    scores[chunk_id] *= 1.5  # 50% boost for type match

        # Sort by score
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [self.chunks[cid] for cid, _ in ranked[:top_k] if cid in self.chunks]

    def get_definitions(self) -> List[Chunk]:
        """Get all definition chunks."""
        return [self.chunks[cid] for cid in self.type_index.get("definition", [])]

    def get_formulas(self) -> List[Tuple[str, str, str]]:
        """Get all formulas with their source: [(formula, source, section)]."""
        results = []
        for chunk in self.chunks.values():
            for f in chunk.formulas:
                results.append((f, chunk.source, chunk.section))
        return results

    def get_topics(self) -> Dict[str, int]:
        """Get all topics with chunk counts."""
        return {topic: len(cids) for topic, cids in self.topic_index.items()}

    def get_connections(self, term: str) -> List[Tuple[str, str, str]]:
        """Find all relationships involving a term across ALL sources."""
        term_lower = term.lower()
        connections = []
        for chunk in self.chunks.values():
            for subj, rel, obj in chunk.relationships:
                if term_lower in subj.lower() or term_lower in obj.lower():
                    connections.append((subj, rel, obj))
        return connections

    def cross_reference(self, term: str) -> Dict[str, List[str]]:
        """Find a term across ALL sources — shows how different docs discuss it."""
        term_lower = term.lower()
        by_source: Dict[str, List[str]] = {}
        for chunk in self.chunks.values():
            if term_lower in chunk.text.lower():
                src = chunk.source
                if src not in by_source:
                    by_source[src] = []
                # Extract the sentence containing the term
                for sent in chunk.text.split('.'):
                    if term_lower in sent.lower():
                        by_source[src].append(sent.strip())
                        break
        return by_source

    def stats(self) -> Dict:
        """Return statistics about ingested knowledge."""
        return {
            "total_chunks": len(self.chunks),
            "sources": len(self.sources),
            "topics": len(self.topic_index),
            "terms_indexed": len(self.term_index),
            "formulas": sum(len(c.formulas) for c in self.chunks.values()),
            "definitions": len(self.type_index.get("definition", [])),
            "theorems": len(self.type_index.get("theorem", [])),
            "examples": len(self.type_index.get("example", [])),
        }

    # ──────────────────────────────────────────────────────────────
    # CHUNKING — Split text into semantic units
    # ──────────────────────────────────────────────────────────────

    def _chunk_text(self, text: str) -> List[str]:
        """Split text into semantic chunks at natural boundaries."""
        chunks = []
        current = []

        lines = text.split('\n')
        for line in lines:
            stripped = line.strip()

            # Empty line = paragraph boundary
            if not stripped:
                if current:
                    chunks.append('\n'.join(current))
                    current = []
                continue

            # Header detection = new chunk
            if self._is_header(stripped):
                if current:
                    chunks.append('\n'.join(current))
                    current = []
                chunks.append(stripped)  # header as its own chunk
                continue

            # Bullet/numbered list items can be their own chunk
            if re.match(r'^[\d]+[\.\)]\s|^[•\-\*]\s', stripped):
                if current and not re.match(r'^[\d]+[\.\)]\s|^[•\-\*]\s', current[-1]):
                    chunks.append('\n'.join(current))
                    current = []

            current.append(stripped)

            # Long paragraphs: split at ~200 words
            if len(' '.join(current).split()) > 200:
                chunks.append('\n'.join(current))
                current = []

        if current:
            chunks.append('\n'.join(current))

        # Filter out tiny chunks
        return [c for c in chunks if len(c.split()) >= 5]

    def _is_header(self, line: str) -> bool:
        """Detect if a line is a section header."""
        # ALL CAPS
        if line.isupper() and len(line.split()) <= 10:
            return True
        # Starts with number + period + title case
        if re.match(r'^\d+\.\s+[A-Z]', line) and len(line.split()) <= 12:
            return True
        # Markdown headers
        if line.startswith('#'):
            return True
        # Short line that ends without period (likely title)
        if len(line.split()) <= 8 and not line.endswith('.') and line[0].isupper():
            return True
        return False

    # ──────────────────────────────────────────────────────────────
    # TAGGING — Detect chunk type and extract information
    # ──────────────────────────────────────────────────────────────

    def _detect_type(self, text: str) -> str:
        """Detect what type of content this chunk is."""
        t = text.lower()

        # Definition: formal OR informal
        # Formal: "X is defined as" / "X refers to"
        if re.search(r'\b(?:is defined as|refers to|is known as|means|is called)\b', t):
            return "definition"
        # Informal: "X is [article] Y" at start of sentence
        if re.search(r'^[A-Z]\w+\s+(?:is|are)\s+(?:a|an|the)\s+', text):
            return "definition"
        # Informal: "basically X is/are" / "so X is" / "X is basically"
        if re.search(r'\b(?:basically|essentially|simply put|in other words)\b.*\b(?:is|are|means)\b', t):
            return "definition"
        # "X is where/when/how" = definitional
        if re.search(r'\b\w+\s+(?:is|are)\s+(?:where|when|how|what)\b', t):
            return "definition"

        # Theorem/Law
        if re.search(r'\b(?:theorem|law|principle|postulate|axiom|lemma|corollary)\b', t):
            return "theorem"
        if re.search(r'\bstates?\s+that\b', t):
            return "theorem"

        # Example
        if re.search(r'\b(?:for example|e\.g\.|for instance|consider|suppose|imagine)\b', t):
            return "example"

        # Procedure/List: bullet points, numbered items, "steps"
        if re.search(r'\b(?:step\s+\d|first.*then|how to|procedure|method|algorithm)\b', t):
            return "procedure"
        # Detect bullet/dash lists as study material
        if text.count('\n-') >= 2 or text.count('\n•') >= 2:
            return "procedure"

        # Formula: contains equation (X = expression OR chemical →)
        if re.search(r'[a-zA-Z]\s*=\s*[a-zA-Z0-9\+\-\*\/\^]+', text):
            return "formula"
        # Chemical equation: contains →
        if '→' in text or '→' in text:
            return "formula"

        # Data: many numbers
        numbers = re.findall(r'\d+\.?\d*', t)
        if len(numbers) > 5:
            return "data"

        # Contrast/comparison: "opposite" / "unlike" / "vs"
        if re.search(r'\b(?:opposite|unlike|whereas|however|vs|versus|but|instead)\b', t):
            return "comparison"

        # Important/key fact: "important because" / "key point" / "remember"
        if re.search(r'\b(?:important|crucial|key|remember|note that|don.t forget)\b', t):
            return "key_fact"

        return "narrative"

    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract important terms (nouns, technical words, proper nouns)."""
        # Get all words that are capitalized (not at sentence start) or technical
        words = text.split()
        terms = []

        for i, word in enumerate(words):
            clean = re.sub(r'[^\w]', '', word)
            if not clean:
                continue

            # Proper nouns (capitalized, not sentence start)
            if clean[0].isupper() and i > 0 and words[i-1][-1] not in '.!?':
                terms.append(clean)

            # Technical terms (contain numbers or special patterns)
            if re.match(r'^[A-Z]{2,}$', clean):  # acronyms
                terms.append(clean)

        # Also extract frequent significant words (nouns likely)
        all_words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        # Remove common stop words
        stops = {'that', 'this', 'with', 'from', 'have', 'been', 'were', 'will',
                 'they', 'their', 'them', 'than', 'then', 'when', 'what', 'which',
                 'where', 'there', 'here', 'some', 'many', 'much', 'more', 'most',
                 'also', 'very', 'just', 'only', 'each', 'every', 'about', 'into',
                 'over', 'such', 'after', 'before', 'between', 'through', 'other'}
        significant = [w for w in all_words if w not in stops]
        freq = Counter(significant)
        # Top terms by frequency in this chunk
        for word, count in freq.most_common(10):
            if count >= 2 or len(word) >= 6:
                terms.append(word)

        return list(set(terms))[:15]

    def _extract_relationships(self, text: str) -> List[Tuple[str, str, str]]:
        """Extract subject-relation-object triples — handles formal AND informal."""
        relationships = []
        sentences = re.split(r'[.!?\n]', text)

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue

            # Pattern: "X is/are Y" (formal definition)
            m = re.match(r'^(.+?)\s+(?:is|are)\s+(.+?)$', sent, re.IGNORECASE)
            if m and len(m.group(1).split()) <= 5:
                relationships.append((m.group(1).strip(), "is", m.group(2).strip()[:80]))

            # Pattern: "X causes/produces/creates Y"
            m = re.search(r'(.{3,30})\s+(?:causes?|produces?|creates?|leads?\s+to|results?\s+in|makes?)\s+(.{3,50})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "causes", m.group(2).strip()))

            # Pattern: "X consists of / contains Y"
            m = re.search(r'(.{3,30})\s+(?:consists?\s+of|contains?|includes?|comprises?|has|have)\s+(.{3,50})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "has_parts", m.group(2).strip()))

            # Pattern: "X is used for Y" / "X is where Y happens"
            m = re.search(r'(.{3,30})\s+(?:is\s+used\s+for|is\s+used\s+to|serves?\s+to|functions?\s+as|is\s+where|is\s+responsible\s+for)\s+(.{3,50})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "purpose", m.group(2).strip()))

            # Pattern: "X is the opposite of Y" / "X is unlike Y"
            m = re.search(r'(.{3,30})\s+(?:is\s+the\s+opposite\s+of|is\s+opposite\s+to|is\s+unlike|contrasts?\s+with)\s+(.{3,30})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "opposite", m.group(2).strip()))

            # Informal: "basically X [verb] Y" / "X basically [verb] Y"
            m = re.search(r'(?:basically|essentially)\s+(.{3,20})\s+(\w+s?)\s+(.{3,40})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), m.group(2).strip(), m.group(3).strip()))

            # Pattern: "without X, Y wouldn't/couldn't"
            m = re.search(r'without\s+(.{3,20})\s*,?\s*(.{5,50})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "enables", m.group(2).strip()))

            # Pattern: "X needs/requires Y"
            m = re.search(r'(.{3,20})\s+(?:needs?|requires?|depends?\s+on)\s+(.{3,30})', sent, re.IGNORECASE)
            if m:
                relationships.append((m.group(1).strip(), "depends_on", m.group(2).strip()))

        return relationships[:15]

    def _extract_formulas(self, text: str) -> List[str]:
        """Extract mathematical AND chemical formulas from text."""
        formulas = []

        # Math: "X = expression"
        for m in re.finditer(r'([A-Za-z_]\w*)\s*=\s*([A-Za-z0-9\+\-\*\/\^\(\)\s\.\,½¼]+)', text):
            formula = f"{m.group(1)} = {m.group(2).strip()}"
            # Clean trailing descriptions
            formula = re.split(r'\s+(?:where|for|with|in which|measured)\s+', formula)[0].strip()
            formula = formula.rstrip('.,;')
            if 5 < len(formula) < 100:
                formulas.append(formula)

        # Chemical equations: "X → Y" or "X -> Y" or "X => Y"
        for m in re.finditer(r'(.+?)\s*(?:→|->|=>|⟶)\s*(.+?)(?:\n|$)', text):
            lhs = m.group(1).strip()
            rhs = m.group(2).strip()
            if len(lhs) > 2 and len(rhs) > 2:
                formulas.append(f"{lhs} → {rhs}")

        # Proportionality: "X ∝ Y" or "X is proportional to Y"
        for m in re.finditer(r'([A-Za-z_]\w*)\s*(?:∝|is\s+proportional\s+to)\s*(.+?)(?:[,.\n]|$)', text):
            formulas.append(f"{m.group(1)} ∝ {m.group(2).strip()}")

        return formulas

    def _detect_topic(self, text: str, section: str) -> str:
        """Auto-detect topic from content. Uses section header if available."""
        if section:
            # Clean section header
            topic = re.sub(r'^[\d\.\#\s]+', '', section).strip().lower()
            if topic:
                return topic[:50]

        # Otherwise use most frequent significant term
        terms = self._extract_key_terms(text)
        if terms:
            return terms[0].lower()
        return "general"

    # ──────────────────────────────────────────────────────────────
    # INDEXING
    # ──────────────────────────────────────────────────────────────

    def _index_chunk(self, chunk: Chunk):
        """Add chunk to all indices."""
        # Term index
        terms = self._tokenize(chunk.text.lower())
        for term in set(terms):
            if term not in self.term_index:
                self.term_index[term] = set()
            self.term_index[term].add(chunk.id)

        # Key terms also indexed
        for term in chunk.key_terms:
            t = term.lower()
            if t not in self.term_index:
                self.term_index[t] = set()
            self.term_index[t].add(chunk.id)

        # Type index
        if chunk.chunk_type:
            if chunk.chunk_type not in self.type_index:
                self.type_index[chunk.chunk_type] = []
            self.type_index[chunk.chunk_type].append(chunk.id)

        # Topic index
        if chunk.topic:
            if chunk.topic not in self.topic_index:
                self.topic_index[chunk.topic] = []
            self.topic_index[chunk.topic].append(chunk.id)

        # Formula index
        for formula in chunk.formulas:
            lhs = formula.split('=')[0].strip()
            self.formula_index[lhs] = chunk.id

    def _question_to_chunk_type(self, query: str) -> Optional[str]:
        """Map question type to expected chunk type."""
        q = query.lower()
        if re.search(r'\bwhat\s+is\b|\bdefine\b|\bmeaning\b', q):
            return "definition"
        if re.search(r'\bhow\s+to\b|\bsteps\b|\bprocedure\b', q):
            return "procedure"
        if re.search(r'\bexample\b|\bshow\s+me\b|\bsuch\s+as\b', q):
            return "example"
        if re.search(r'\bformula\b|\bequation\b|\bcalculate\b', q):
            return "formula"
        if re.search(r'\btheorem\b|\blaw\b|\bprinciple\b|\bstates\b', q):
            return "theorem"
        return None

    # ──────────────────────────────────────────────────────────────
    # UTILITIES
    # ──────────────────────────────────────────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer — split on non-alphanumeric."""
        return [w for w in re.findall(r'\b\w{3,}\b', text) if len(w) >= 3]

    def _hash(self, text: str) -> str:
        """Generate unique ID for a chunk."""
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def _save(self):
        """Persist to disk."""
        os.makedirs(self.storage_dir, exist_ok=True)
        data = {
            "chunks": {cid: {
                "text": c.text, "source": c.source, "section": c.section,
                "page": c.page, "chunk_type": c.chunk_type,
                "key_terms": c.key_terms, "topic": c.topic,
                "relationships": c.relationships, "formulas": c.formulas,
            } for cid, c in self.chunks.items()},
            "sources": self.sources,
        }
        with open(os.path.join(self.storage_dir, "brain.json"), 'w') as f:
            json.dump(data, f)

    def _load(self):
        """Load from disk."""
        path = os.path.join(self.storage_dir, "brain.json")
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
            for cid, cdata in data.get("chunks", {}).items():
                chunk = Chunk(
                    id=cid, text=cdata["text"], source=cdata["source"],
                    section=cdata.get("section", ""), page=cdata.get("page", 0),
                    chunk_type=cdata.get("chunk_type", ""),
                    key_terms=cdata.get("key_terms", []),
                    topic=cdata.get("topic", ""),
                    relationships=[tuple(r) for r in cdata.get("relationships", [])],
                    formulas=cdata.get("formulas", []),
                )
                self.chunks[cid] = chunk
                self._index_chunk(chunk)
            self.sources = data.get("sources", {})
        except:
            pass
