"""
AXIMA BRAIN — Module 5: Cross-Brain Connections
Built by: Ghias + Kiro

Finds hidden connections between concepts across ALL sources.
Physics mentions "energy" → Chemistry mentions "energy" → AUTO-LINK.
Math defines "derivative" → Physics uses "dx/dt" → AUTO-LINK.

NotebookLM can't do this — each notebook is isolated.
AXIMA sees ALL your knowledge as ONE unified graph.
"""

import re
from typing import Dict, List, Set, Tuple, Optional
from brain_ingest import DocumentBrain, Chunk


class CrossBrain:
    """Find connections between concepts across all ingested sources."""

    def __init__(self, brain: DocumentBrain):
        self.brain = brain

    def find_connections(self, term: str) -> Dict[str, List[str]]:
        """Find how a term appears across different sources.
        Returns: {source_name: [sentences mentioning term]}"""
        return self.brain.cross_reference(term)

    def find_shared_concepts(self) -> List[Tuple[str, List[str]]]:
        """Find terms that appear in MULTIPLE sources — these are bridges.
        Returns: [(term, [source1, source2, ...])]"""
        term_sources: Dict[str, Set[str]] = {}

        for chunk in self.brain.chunks.values():
            for term in chunk.key_terms:
                t = term.lower()
                if t not in term_sources:
                    term_sources[t] = set()
                term_sources[t].add(chunk.source)

        # Only return terms in 2+ sources
        bridges = [(term, sorted(sources)) for term, sources in term_sources.items()
                   if len(sources) >= 2]
        return sorted(bridges, key=lambda x: -len(x[1]))

    def find_dependency_chain(self, concept: str) -> List[Tuple[str, str, str]]:
        """Find the chain: concept DEFINED in source A, USED in source B.
        Shows how knowledge from one subject enables another."""
        concept_lower = concept.lower()
        chain = []

        # Find where it's DEFINED (definition chunks)
        defined_in = []
        used_in = []

        for chunk in self.brain.chunks.values():
            text_lower = chunk.text.lower()
            if concept_lower in text_lower:
                if chunk.chunk_type == "definition":
                    defined_in.append(chunk)
                elif concept_lower in [t.lower() for t in chunk.key_terms]:
                    used_in.append(chunk)

        for d in defined_in:
            for u in used_in:
                if d.source != u.source:
                    chain.append((
                        f"Defined in: {d.source} ({d.section})",
                        concept,
                        f"Used in: {u.source} ({u.section})"
                    ))

        return chain

    def find_contradictions(self) -> List[Tuple[str, str, str, str]]:
        """Find cases where two sources say different things about same concept.
        Returns: [(concept, claim1, source1, claim2, source2)]"""
        contradictions = []

        # Group relationships by subject
        claims: Dict[str, List[Tuple[str, str, str]]] = {}  # subject → [(rel, obj, source)]
        for chunk in self.brain.chunks.values():
            for subj, rel, obj in chunk.relationships:
                key = subj.lower()
                if key not in claims:
                    claims[key] = []
                claims[key].append((rel, obj, chunk.source))

        # Look for same subject, same relation type, different objects from different sources
        for subject, claim_list in claims.items():
            if len(claim_list) < 2:
                continue
            for i in range(len(claim_list)):
                for j in range(i+1, len(claim_list)):
                    rel1, obj1, src1 = claim_list[i]
                    rel2, obj2, src2 = claim_list[j]
                    if rel1 == rel2 and src1 != src2 and obj1.lower() != obj2.lower():
                        contradictions.append((subject, f"{obj1} [{src1}]", f"{obj2} [{src2}]"))

        return contradictions

    def suggest_connections(self) -> List[str]:
        """Generate human-readable connection suggestions."""
        suggestions = []

        # Shared concepts
        shared = self.find_shared_concepts()
        for term, sources in shared[:10]:
            if len(sources) >= 2:
                suggestions.append(
                    f"'{term}' connects {' ↔ '.join(sources)} — "
                    f"same concept appears in {len(sources)} of your sources"
                )

        # Dependency chains
        for chunk in self.brain.chunks.values():
            if chunk.chunk_type == "definition":
                for subj, rel, obj in chunk.relationships:
                    if rel == "is":
                        chains = self.find_dependency_chain(subj)
                        for defined, concept, used in chains[:3]:
                            suggestions.append(f"Your {defined} is applied in {used}")

        return suggestions[:20]

    def concept_map(self) -> str:
        """Generate a text-based concept map showing all connections."""
        shared = self.find_shared_concepts()
        if not shared:
            return "No cross-source connections found yet. Ingest more sources!"

        lines = ["CONCEPT MAP — Cross-Source Connections", "═"*50]

        for term, sources in shared[:15]:
            lines.append(f"\n  [{term}]")
            refs = self.brain.cross_reference(term)
            for src, sentences in refs.items():
                for sent in sentences[:1]:
                    lines.append(f"    ├── {src}: {sent[:60]}")

        contradictions = self.find_contradictions()
        if contradictions:
            lines.append(f"\n\n  ⚠️  CONTRADICTIONS FOUND:")
            for subj, claim1, claim2 in contradictions[:5]:
                lines.append(f"    {subj}: {claim1} vs {claim2}")

        return '\n'.join(lines)
