"""Document Specialist — citation-perfect answers from ingested documents.

Supports ingestion, query with exact citations (page/section/span),
conflicting source handling, and claim extraction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class DocumentType(Enum):
    ARTICLE = auto()
    BOOK = auto()
    PAPER = auto()
    REPORT = auto()
    WEBPAGE = auto()
    TRANSCRIPT = auto()
    OTHER = auto()


class ClaimStatus(Enum):
    SUPPORTED = auto()
    CONTRADICTED = auto()
    UNSUPPORTED = auto()
    AMBIGUOUS = auto()


@dataclass
class TextSpan:
    """A precise location within a document."""
    start_char: int
    end_char: int
    text: str


@dataclass
class DocumentLocation:
    """Full citation location."""
    page: Optional[int] = None
    section: Optional[str] = None
    paragraph: Optional[int] = None
    span: Optional[TextSpan] = None
    line: Optional[int] = None


@dataclass
class DocumentMetadata:
    """Metadata for an ingested document."""
    title: str
    author: Optional[str] = None
    date: Optional[datetime] = None
    doc_type: DocumentType = DocumentType.OTHER
    source_url: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class DocumentChunk:
    """A chunk of document content with location info."""
    doc_id: str
    content: str
    location: DocumentLocation
    metadata: Optional[DocumentMetadata] = None


@dataclass
class Citation:
    """A precise citation to a document location."""
    doc_id: str
    location: DocumentLocation
    verbatim_quote: str
    relevance_score: float = 0.0
    metadata: Optional[DocumentMetadata] = None


@dataclass
class CitedAnswer:
    """An answer with supporting citations."""
    query: str
    answer: str
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.0
    conflicts: List["SourceConflict"] = field(default_factory=list)
    truth_label: str = "direct_fact"


@dataclass
class SourceConflict:
    """A detected conflict between sources."""
    citation_a: Citation
    citation_b: Citation
    description: str
    resolution: Optional[str] = None


@dataclass
class Claim:
    """An extracted claim from a document."""
    statement: str
    source: Citation
    status: ClaimStatus = ClaimStatus.SUPPORTED
    supporting_citations: List[Citation] = field(default_factory=list)
    contradicting_citations: List[Citation] = field(default_factory=list)


@dataclass
class StudyWorkflow:
    """A study workflow for systematic document analysis."""
    name: str
    documents: List[str] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)
    claims: List[Claim] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None


class DocumentSpecialist:
    """Domain specialist for document-based Q&A with exact citations.

    - ingest: add documents to the knowledge base
    - query_with_citations: answer queries with page/section/span citations
    - extract_claims: extract and verify claims from documents
    """

    def __init__(self) -> None:
        self._documents: Dict[str, DocumentMetadata] = {}
        self._chunks: List[DocumentChunk] = []
        self._index: Dict[str, List[int]] = {}  # keyword -> chunk indices
        self._workflows: Dict[str, StudyWorkflow] = {}

    def ingest(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[DocumentMetadata] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> int:
        """Ingest a document, splitting into chunks with location tracking.

        Returns the number of chunks created.
        """
        if metadata is None:
            metadata = DocumentMetadata(title=doc_id)

        self._documents[doc_id] = metadata

        # Split into chunks with overlap
        chunks_created = 0
        lines = content.split("\n")
        current_chunk = ""
        current_page = 1
        current_section = ""
        current_para = 0
        char_offset = 0

        for line_num, line in enumerate(lines):
            # Detect section headers (simple heuristic)
            stripped = line.strip()
            if stripped and stripped[0] == "#":
                current_section = stripped.lstrip("#").strip()
            if stripped == "":
                current_para += 1
            # Page break heuristic
            if "---PAGE---" in line or "\f" in line:
                current_page += 1
                continue

            current_chunk += line + "\n"

            if len(current_chunk) >= chunk_size:
                chunk = DocumentChunk(
                    doc_id=doc_id,
                    content=current_chunk.strip(),
                    location=DocumentLocation(
                        page=current_page,
                        section=current_section or None,
                        paragraph=current_para,
                        span=TextSpan(
                            start_char=char_offset,
                            end_char=char_offset + len(current_chunk),
                            text=current_chunk[:100].strip(),
                        ),
                        line=line_num,
                    ),
                    metadata=metadata,
                )
                idx = len(self._chunks)
                self._chunks.append(chunk)
                self._index_chunk(idx, current_chunk)
                chunks_created += 1
                char_offset += len(current_chunk) - chunk_overlap
                # Keep overlap
                current_chunk = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else ""

        # Handle remaining content
        if current_chunk.strip():
            chunk = DocumentChunk(
                doc_id=doc_id,
                content=current_chunk.strip(),
                location=DocumentLocation(
                    page=current_page,
                    section=current_section or None,
                    paragraph=current_para,
                    span=TextSpan(
                        start_char=char_offset,
                        end_char=char_offset + len(current_chunk),
                        text=current_chunk[:100].strip(),
                    ),
                ),
                metadata=metadata,
            )
            idx = len(self._chunks)
            self._chunks.append(chunk)
            self._index_chunk(idx, current_chunk)
            chunks_created += 1

        return chunks_created

    def query_with_citations(
        self,
        query: str,
        max_citations: int = 5,
        doc_filter: Optional[List[str]] = None,
    ) -> CitedAnswer:
        """Answer a query with exact citations from ingested documents.

        Returns citation-perfect answer with page/section/span references.
        Detects and reports conflicting sources.
        """
        # Search for relevant chunks
        matching = self._search_chunks(query, doc_filter)

        if not matching:
            return CitedAnswer(
                query=query,
                answer="",
                confidence=0.0,
                truth_label="unsupported",
            )

        # Build citations from top matches
        citations: List[Citation] = []
        for score, chunk in matching[:max_citations]:
            citation = Citation(
                doc_id=chunk.doc_id,
                location=chunk.location,
                verbatim_quote=chunk.content[:200],
                relevance_score=score,
                metadata=chunk.metadata,
            )
            citations.append(citation)

        # Compose answer from best chunks
        answer_parts = [chunk.content for _, chunk in matching[:3]]
        answer = " ".join(answer_parts)

        # Detect conflicts between citations
        conflicts = self._detect_conflicts(citations)

        confidence = matching[0][0] if matching else 0.0
        truth_label = "direct_fact" if confidence > 0.5 else "heuristic"

        return CitedAnswer(
            query=query,
            answer=answer,
            citations=citations,
            confidence=confidence,
            conflicts=conflicts,
            truth_label=truth_label,
        )

    def extract_claims(
        self,
        doc_id: str,
        verify_against: Optional[List[str]] = None,
    ) -> List[Claim]:
        """Extract factual claims from a document and optionally verify them.

        Claims are sentences that make factual assertions.
        If verify_against is provided, checks claims against other documents.
        """
        # Get all chunks for this document
        doc_chunks = [c for c in self._chunks if c.doc_id == doc_id]
        if not doc_chunks:
            return []

        claims: List[Claim] = []

        for chunk in doc_chunks:
            # Extract sentences that look like factual claims
            sentences = self._split_sentences(chunk.content)
            for sentence in sentences:
                if self._is_factual_claim(sentence):
                    source_citation = Citation(
                        doc_id=doc_id,
                        location=chunk.location,
                        verbatim_quote=sentence,
                        relevance_score=1.0,
                        metadata=chunk.metadata,
                    )

                    claim = Claim(
                        statement=sentence,
                        source=source_citation,
                        status=ClaimStatus.SUPPORTED,
                    )

                    # Verify against other documents if requested
                    if verify_against:
                        claim = self._verify_claim(claim, verify_against)

                    claims.append(claim)

        return claims

    def create_workflow(self, name: str) -> StudyWorkflow:
        """Create a study workflow for systematic document analysis."""
        workflow = StudyWorkflow(name=name, created_at=datetime.now())
        self._workflows[name] = workflow
        return workflow

    def add_to_workflow(
        self,
        workflow_name: str,
        doc_ids: Optional[List[str]] = None,
        queries: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
    ) -> Optional[StudyWorkflow]:
        """Add documents, queries, or notes to a workflow."""
        workflow = self._workflows.get(workflow_name)
        if workflow is None:
            return None
        if doc_ids:
            workflow.documents.extend(doc_ids)
        if queries:
            workflow.queries.extend(queries)
        if notes:
            workflow.notes.extend(notes)
        return workflow

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _index_chunk(self, idx: int, content: str) -> None:
        """Index a chunk by keywords."""
        words = content.lower().split()
        seen: Set[str] = set()
        for word in words:
            clean = word.strip(".,;:!?()[]\"'`~")
            if len(clean) > 2 and clean not in seen:
                seen.add(clean)
                self._index.setdefault(clean, []).append(idx)

    def _search_chunks(
        self, query: str, doc_filter: Optional[List[str]] = None,
    ) -> List[Tuple[float, DocumentChunk]]:
        """Search chunks by keyword relevance."""
        query_words = set(
            w.lower().strip(".,;:!?()[]\"'") for w in query.split() if len(w) > 2
        )
        chunk_scores: Dict[int, float] = {}

        for word in query_words:
            if word in self._index:
                for idx in self._index[word]:
                    chunk_scores[idx] = chunk_scores.get(idx, 0) + 1.0

        results: List[Tuple[float, DocumentChunk]] = []
        for idx, score in chunk_scores.items():
            chunk = self._chunks[idx]
            if doc_filter and chunk.doc_id not in doc_filter:
                continue
            # Normalize score
            normalized = score / max(len(query_words), 1)
            results.append((normalized, chunk))

        results.sort(key=lambda x: x[0], reverse=True)
        return results[:20]

    def _detect_conflicts(self, citations: List[Citation]) -> List[SourceConflict]:
        """Detect potential conflicts between citations."""
        conflicts: List[SourceConflict] = []
        for i in range(len(citations)):
            for j in range(i + 1, len(citations)):
                a = citations[i]
                b = citations[j]
                # Simple conflict detection: different documents, contradictory keywords
                if a.doc_id != b.doc_id:
                    a_words = set(a.verbatim_quote.lower().split())
                    b_words = set(b.verbatim_quote.lower().split())
                    # Check for negation patterns
                    negations = {"not", "no", "never", "neither", "none", "false"}
                    a_has_neg = bool(a_words & negations)
                    b_has_neg = bool(b_words & negations)
                    # Overlap minus negation words
                    overlap = a_words & b_words - negations
                    if a_has_neg != b_has_neg and len(overlap) > 3:
                        conflicts.append(SourceConflict(
                            citation_a=a,
                            citation_b=b,
                            description="Potential contradiction: one source negates what the other affirms",
                        ))
        return conflicts

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split text into sentences (simple heuristic)."""
        sentences: List[str] = []
        current = ""
        for ch in text:
            current += ch
            if ch in ".!?" and len(current.strip()) > 10:
                sentences.append(current.strip())
                current = ""
        if current.strip() and len(current.strip()) > 10:
            sentences.append(current.strip())
        return sentences

    @staticmethod
    def _is_factual_claim(sentence: str) -> bool:
        """Heuristic: does this sentence make a factual assertion?"""
        claim_indicators = [
            " is ", " are ", " was ", " were ", " has ", " have ",
            " shows ", " demonstrates ", " proves ", " indicates ",
            " found ", " discovered ", " measured ", " observed ",
        ]
        lower = sentence.lower()
        # Exclude questions and commands
        if sentence.strip().endswith("?"):
            return False
        if lower.startswith(("how", "why", "what", "when", "where", "who")):
            return False
        return any(ind in lower for ind in claim_indicators)

    def _verify_claim(self, claim: Claim, verify_against: List[str]) -> Claim:
        """Verify a claim against other documents."""
        # Search for the claim statement in other documents
        results = self._search_chunks(claim.statement, doc_filter=verify_against)

        if not results:
            claim.status = ClaimStatus.UNSUPPORTED
            return claim

        # Check if supporting or contradicting
        for score, chunk in results[:5]:
            citation = Citation(
                doc_id=chunk.doc_id,
                location=chunk.location,
                verbatim_quote=chunk.content[:200],
                relevance_score=score,
                metadata=chunk.metadata,
            )

            # Simple heuristic: check for negation
            negations = {"not", "no", "never", "false", "incorrect", "wrong"}
            chunk_words = set(chunk.content.lower().split())
            claim_words = set(claim.statement.lower().split())
            overlap = chunk_words & claim_words

            if len(overlap) > 3:
                if chunk_words & negations and not (claim_words & negations):
                    claim.contradicting_citations.append(citation)
                else:
                    claim.supporting_citations.append(citation)

        if claim.contradicting_citations and not claim.supporting_citations:
            claim.status = ClaimStatus.CONTRADICTED
        elif claim.contradicting_citations and claim.supporting_citations:
            claim.status = ClaimStatus.AMBIGUOUS
        elif claim.supporting_citations:
            claim.status = ClaimStatus.SUPPORTED
        else:
            claim.status = ClaimStatus.UNSUPPORTED

        return claim
