"""
Document Plugin
===============

Handles document ingestion, structure parsing, table extraction,
and span-level citation. Supports PDF text, markdown, HTML, and plain text.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..base import PluginBase
from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor
from ...semantics.meaning_ir import MeaningIR


# ---------------------------------------------------------------------------
# Document data structures
# ---------------------------------------------------------------------------


class DocumentFormat(Enum):
    """Supported document formats."""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF_TEXT = "pdf_text"  # Pre-extracted text from PDF


class ElementType(Enum):
    """Types of document structural elements."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CODE_BLOCK = "code_block"
    BLOCKQUOTE = "blockquote"
    HORIZONTAL_RULE = "hr"
    IMAGE_REF = "image_ref"
    LINK = "link"


@dataclass
class DocumentElement:
    """A structural element within a document."""

    element_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    element_type: ElementType = ElementType.PARAGRAPH
    content: str = ""
    level: int = 0  # For headings (1-6), list depth, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    children: List["DocumentElement"] = field(default_factory=list)
    span: Tuple[int, int] = (0, 0)  # Character offsets in source


@dataclass
class TableCell:
    """A cell in a parsed table."""

    content: str = ""
    row: int = 0
    col: int = 0
    is_header: bool = False
    colspan: int = 1
    rowspan: int = 1


@dataclass
class ParsedTable:
    """A fully parsed table with cells."""

    table_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    cells: List[TableCell] = field(default_factory=list)
    caption: Optional[str] = None


@dataclass
class Citation:
    """A citation reference to a specific span in the document."""

    citation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    document_id: str = ""
    page: Optional[int] = None
    section: Optional[str] = None
    span: Tuple[int, int] = (0, 0)
    text: str = ""


@dataclass
class DocumentStructure:
    """Complete parsed structure of a document."""

    document_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    format: DocumentFormat = DocumentFormat.PLAIN_TEXT
    elements: List[DocumentElement] = field(default_factory=list)
    tables: List[ParsedTable] = field(default_factory=list)
    sections: List[str] = field(default_factory=list)
    word_count: int = 0
    content_hash: str = ""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_MD_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.+)$", re.MULTILINE)
_MD_CODE_BLOCK_RE = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
_MD_TABLE_RE = re.compile(
    r"(\|[^\n]+\|\n)(\|[-:\s|]+\|\n)((?:\|[^\n]+\|\n?)+)", re.MULTILINE
)
_MD_BLOCKQUOTE_RE = re.compile(r"^>\s+(.+)$", re.MULTILINE)
_MD_HR_RE = re.compile(r"^---+$", re.MULTILINE)

_HTML_TAG_RE = re.compile(r"<(\w+)([^>]*)>(.*?)</\1>", re.DOTALL)
_HTML_HEADING_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.DOTALL | re.I)
_HTML_TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.DOTALL | re.I)
_HTML_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.I)
_HTML_TD_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.DOTALL | re.I)
_HTML_TH_RE = re.compile(r"<th[^>]*>(.*?)</th>", re.DOTALL | re.I)
_HTML_STRIP_RE = re.compile(r"<[^>]+>")


def _detect_format(text: str) -> DocumentFormat:
    """Auto-detect document format from content."""
    if _HTML_TAG_RE.search(text):
        return DocumentFormat.HTML
    if _MD_HEADING_RE.search(text) or _MD_CODE_BLOCK_RE.search(text):
        return DocumentFormat.MARKDOWN
    # Check for PDF-extracted markers
    if "\x0c" in text or text.startswith("%PDF"):
        return DocumentFormat.PDF_TEXT
    return DocumentFormat.PLAIN_TEXT


# ---------------------------------------------------------------------------
# DocumentPlugin
# ---------------------------------------------------------------------------


class DocumentPlugin(PluginBase):
    """Plugin for structured document parsing and citation.

    Capabilities:
    - Document ingestion and format detection
    - Structural parsing (sections, paragraphs, tables, lists)
    - Table extraction with headers and cells
    - Span-level citation for traceability
    """

    def __init__(self) -> None:
        self._documents: Dict[str, DocumentStructure] = {}

    def name(self) -> str:
        return "document_parser"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["document", "text", "markdown", "html"],
            produced_types=["document_structure", "table", "citation"],
            preconditions=["text_input_available"],
            postconditions=["structure_parsed", "citations_available"],
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Execute document parsing based on MeaningIR goals."""
        # Look for document content in the IR
        if ir.goals:
            for goal in ir.goals:
                if "parse" in goal.description.lower() or "document" in goal.description.lower():
                    return ExecutionResult(
                        answer="Document parsing requires direct text input via ingest()",
                        status="success",
                        engine="document_parser",
                    )

        return ExecutionResult(
            answer="No document parsing goal detected",
            status="success",
            engine="document_parser",
        )

    def health_check(self) -> bool:
        return True

    # ------------------------------------------------------------------
    # Core document operations
    # ------------------------------------------------------------------

    def ingest(
        self,
        text: str,
        title: Optional[str] = None,
        format_hint: Optional[DocumentFormat] = None,
    ) -> DocumentStructure:
        """Ingest a document and parse its structure.

        Args:
            text: Raw document text.
            title: Optional document title.
            format_hint: Optional format hint (auto-detected if None).

        Returns:
            Parsed DocumentStructure.
        """
        doc_format = format_hint or _detect_format(text)
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        structure = DocumentStructure(
            title=title,
            format=doc_format,
            word_count=len(text.split()),
            content_hash=content_hash,
        )

        if doc_format == DocumentFormat.MARKDOWN:
            structure.elements = self._parse_markdown(text)
        elif doc_format == DocumentFormat.HTML:
            structure.elements = self._parse_html(text)
        elif doc_format == DocumentFormat.PDF_TEXT:
            structure.elements = self._parse_pdf_text(text)
        else:
            structure.elements = self._parse_plain_text(text)

        # Extract sections from headings
        structure.sections = [
            el.content for el in structure.elements
            if el.element_type == ElementType.HEADING
        ]

        # Extract tables
        structure.tables = self.extract_tables(text, doc_format)

        # Store for citation
        self._documents[structure.document_id] = structure
        return structure

    def parse_structure(self, text: str) -> List[DocumentElement]:
        """Parse document structure without full ingestion.

        Args:
            text: Document text.

        Returns:
            List of DocumentElement.
        """
        doc_format = _detect_format(text)
        if doc_format == DocumentFormat.MARKDOWN:
            return self._parse_markdown(text)
        elif doc_format == DocumentFormat.HTML:
            return self._parse_html(text)
        else:
            return self._parse_plain_text(text)

    def extract_tables(
        self,
        text: str,
        format_hint: Optional[DocumentFormat] = None,
    ) -> List[ParsedTable]:
        """Extract tables from document text.

        Args:
            text: Document text containing tables.
            format_hint: Document format.

        Returns:
            List of ParsedTable instances.
        """
        doc_format = format_hint or _detect_format(text)
        tables: List[ParsedTable] = []

        if doc_format == DocumentFormat.MARKDOWN:
            tables = self._extract_markdown_tables(text)
        elif doc_format == DocumentFormat.HTML:
            tables = self._extract_html_tables(text)

        return tables

    def cite_spans(
        self,
        document_id: str,
        query: str,
    ) -> List[Citation]:
        """Find and cite spans in a document matching a query.

        Args:
            document_id: ID of an ingested document.
            query: Text to search for.

        Returns:
            List of Citation objects with span locations.
        """
        structure = self._documents.get(document_id)
        if structure is None:
            return []

        citations: List[Citation] = []
        query_lower = query.lower()

        for element in structure.elements:
            content_lower = element.content.lower()
            if query_lower in content_lower:
                # Find the section this element belongs to
                section = self._find_section_for_element(element, structure)
                start_idx = content_lower.index(query_lower)
                end_idx = start_idx + len(query)

                citations.append(Citation(
                    document_id=document_id,
                    section=section,
                    span=(element.span[0] + start_idx, element.span[0] + end_idx),
                    text=element.content[start_idx:end_idx],
                ))

        return citations

    # ------------------------------------------------------------------
    # Format-specific parsers
    # ------------------------------------------------------------------

    def _parse_markdown(self, text: str) -> List[DocumentElement]:
        """Parse markdown into structural elements."""
        elements: List[DocumentElement] = []
        pos = 0

        # Extract code blocks first (protect from other parsing)
        code_blocks: Dict[str, str] = {}
        for match in _MD_CODE_BLOCK_RE.finditer(text):
            key = f"__CODE_{len(code_blocks)}__"
            code_blocks[key] = match.group(0)
            elements.append(DocumentElement(
                element_type=ElementType.CODE_BLOCK,
                content=match.group(2).strip(),
                attributes={"language": match.group(1) or "text"},
                span=(match.start(), match.end()),
            ))

        # Headings
        for match in _MD_HEADING_RE.finditer(text):
            level = len(match.group(1))
            elements.append(DocumentElement(
                element_type=ElementType.HEADING,
                content=match.group(2).strip(),
                level=level,
                span=(match.start(), match.end()),
            ))

        # List items
        for match in _MD_LIST_RE.finditer(text):
            indent = len(match.group(1))
            elements.append(DocumentElement(
                element_type=ElementType.LIST_ITEM,
                content=match.group(3).strip(),
                level=indent // 2,
                span=(match.start(), match.end()),
            ))

        # Blockquotes
        for match in _MD_BLOCKQUOTE_RE.finditer(text):
            elements.append(DocumentElement(
                element_type=ElementType.BLOCKQUOTE,
                content=match.group(1).strip(),
                span=(match.start(), match.end()),
            ))

        # Horizontal rules
        for match in _MD_HR_RE.finditer(text):
            elements.append(DocumentElement(
                element_type=ElementType.HORIZONTAL_RULE,
                span=(match.start(), match.end()),
            ))

        # Remaining paragraphs (simple heuristic: non-empty lines not matched above)
        matched_spans = set()
        for el in elements:
            for i in range(el.span[0], el.span[1] + 1):
                matched_spans.add(i)

        lines = text.split("\n")
        line_pos = 0
        para_buffer: List[str] = []
        para_start = 0

        for line in lines:
            line_end = line_pos + len(line)
            if line.strip() and line_pos not in matched_spans:
                if not para_buffer:
                    para_start = line_pos
                para_buffer.append(line.strip())
            else:
                if para_buffer:
                    elements.append(DocumentElement(
                        element_type=ElementType.PARAGRAPH,
                        content=" ".join(para_buffer),
                        span=(para_start, line_pos),
                    ))
                    para_buffer = []
            line_pos = line_end + 1  # +1 for newline

        if para_buffer:
            elements.append(DocumentElement(
                element_type=ElementType.PARAGRAPH,
                content=" ".join(para_buffer),
                span=(para_start, len(text)),
            ))

        # Sort by position
        elements.sort(key=lambda e: e.span[0])
        return elements

    def _parse_html(self, text: str) -> List[DocumentElement]:
        """Parse HTML into structural elements."""
        elements: List[DocumentElement] = []

        # Headings
        for match in _HTML_HEADING_RE.finditer(text):
            level = int(match.group(1))
            content = _HTML_STRIP_RE.sub("", match.group(2)).strip()
            elements.append(DocumentElement(
                element_type=ElementType.HEADING,
                content=content,
                level=level,
                span=(match.start(), match.end()),
            ))

        # Paragraphs
        for match in re.finditer(r"<p[^>]*>(.*?)</p>", text, re.DOTALL | re.I):
            content = _HTML_STRIP_RE.sub("", match.group(1)).strip()
            if content:
                elements.append(DocumentElement(
                    element_type=ElementType.PARAGRAPH,
                    content=content,
                    span=(match.start(), match.end()),
                ))

        # List items
        for match in re.finditer(r"<li[^>]*>(.*?)</li>", text, re.DOTALL | re.I):
            content = _HTML_STRIP_RE.sub("", match.group(1)).strip()
            if content:
                elements.append(DocumentElement(
                    element_type=ElementType.LIST_ITEM,
                    content=content,
                    span=(match.start(), match.end()),
                ))

        elements.sort(key=lambda e: e.span[0])
        return elements

    def _parse_pdf_text(self, text: str) -> List[DocumentElement]:
        """Parse pre-extracted PDF text into structural elements."""
        elements: List[DocumentElement] = []

        # Split on form feed (page breaks)
        pages = text.split("\x0c")
        pos = 0

        for page_num, page in enumerate(pages):
            paragraphs = page.strip().split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Detect headings (ALL CAPS or short bold-like lines)
                if para.isupper() and len(para) < 100:
                    elements.append(DocumentElement(
                        element_type=ElementType.HEADING,
                        content=para,
                        level=1,
                        attributes={"page": page_num + 1},
                        span=(pos, pos + len(para)),
                    ))
                else:
                    elements.append(DocumentElement(
                        element_type=ElementType.PARAGRAPH,
                        content=para,
                        attributes={"page": page_num + 1},
                        span=(pos, pos + len(para)),
                    ))
                pos += len(para) + 2  # account for \n\n

            pos += 1  # account for \x0c

        return elements

    def _parse_plain_text(self, text: str) -> List[DocumentElement]:
        """Parse plain text into paragraph elements."""
        elements: List[DocumentElement] = []
        paragraphs = text.split("\n\n")
        pos = 0

        for para in paragraphs:
            para = para.strip()
            if para:
                elements.append(DocumentElement(
                    element_type=ElementType.PARAGRAPH,
                    content=para,
                    span=(pos, pos + len(para)),
                ))
            pos += len(para) + 2

        return elements

    # ------------------------------------------------------------------
    # Table extraction
    # ------------------------------------------------------------------

    def _extract_markdown_tables(self, text: str) -> List[ParsedTable]:
        """Extract tables from markdown text."""
        tables: List[ParsedTable] = []

        for match in _MD_TABLE_RE.finditer(text):
            header_line = match.group(1).strip()
            rows_text = match.group(3).strip()

            # Parse headers
            headers = [
                cell.strip() for cell in header_line.split("|")
                if cell.strip()
            ]

            # Parse rows
            rows: List[List[str]] = []
            for row_line in rows_text.split("\n"):
                row_line = row_line.strip()
                if row_line:
                    cells = [
                        cell.strip() for cell in row_line.split("|")
                        if cell.strip()
                    ]
                    rows.append(cells)

            tables.append(ParsedTable(
                headers=headers,
                rows=rows,
            ))

        return tables

    def _extract_html_tables(self, text: str) -> List[ParsedTable]:
        """Extract tables from HTML text."""
        tables: List[ParsedTable] = []

        for table_match in _HTML_TABLE_RE.finditer(text):
            table_html = table_match.group(1)
            headers: List[str] = []
            rows: List[List[str]] = []

            for tr_match in _HTML_TR_RE.finditer(table_html):
                tr_html = tr_match.group(1)

                # Check if this row has headers
                th_cells = [
                    _HTML_STRIP_RE.sub("", m.group(1)).strip()
                    for m in _HTML_TH_RE.finditer(tr_html)
                ]
                if th_cells:
                    headers = th_cells
                    continue

                # Regular row
                td_cells = [
                    _HTML_STRIP_RE.sub("", m.group(1)).strip()
                    for m in _HTML_TD_RE.finditer(tr_html)
                ]
                if td_cells:
                    rows.append(td_cells)

            tables.append(ParsedTable(
                headers=headers,
                rows=rows,
            ))

        return tables

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------

    def _find_section_for_element(
        self,
        element: DocumentElement,
        structure: DocumentStructure,
    ) -> Optional[str]:
        """Find which section a given element belongs to."""
        current_section: Optional[str] = None

        for el in structure.elements:
            if el.element_type == ElementType.HEADING:
                current_section = el.content
            if el.element_id == element.element_id:
                return current_section

        return current_section
