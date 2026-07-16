"""
AXIMA Truth Layer — Tags every response with its confidence source.

Categories:
  direct_fact  — Found verbatim in knowledge base
  derived      — Inferred through reasoning rules (may be wrong)
  heuristic    — Best guess from pattern matching
  template     — Generated from structural patterns/templates
  unsupported  — Could not find reliable answer

Usage:
  from truth import TruthLabel, tag_response
  
  result = tag_response(answer, source="knowledge", confidence=0.95)
  print(result.label)  # "direct_fact"
  print(result.explanation)  # "Found in knowledge base with 95% match"
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TruthLabel:
    """Truth metadata for any AXIMA response."""
    label: str          # direct_fact / derived / heuristic / template / unsupported
    confidence: float   # 0.0 to 1.0
    source: str         # which engine produced this
    explanation: str    # human-readable reason for this label
    caveats: str = ""   # what could be wrong


def tag_response(answer: str, source: str, confidence: float = 0.5,
                 hops: int = 0, is_template: bool = False) -> TruthLabel:
    """
    Tag a response with truth metadata based on how it was produced.
    
    Args:
        answer: The response text
        source: Which engine produced it (knowledge, math, physics, aces, coder, creator, web)
        confidence: How confident the engine is (0-1)
        hops: Number of inference steps (0 = direct lookup)
        is_template: Whether this came from a fixed template/pattern
    """
    if not answer or answer.strip() == "":
        return TruthLabel(
            label="unsupported",
            confidence=0.0,
            source=source,
            explanation="No answer could be produced",
            caveats="Query may be outside system capabilities"
        )

    # Direct fact: high confidence, from knowledge base, 0 hops
    if source == "knowledge" and confidence > 0.8 and hops == 0:
        return TruthLabel(
            label="direct_fact",
            confidence=confidence,
            source=source,
            explanation=f"Found directly in knowledge base ({confidence:.0%} match)",
            caveats="Knowledge base may be outdated or incomplete"
        )

    # Derived: from inference engine with reasoning steps
    if source == "knowledge" and hops > 0:
        return TruthLabel(
            label="derived",
            confidence=confidence * (0.9 ** hops),  # confidence decreases per hop
            source=source,
            explanation=f"Derived through {hops}-step reasoning chain",
            caveats=f"Each reasoning step may introduce error. {hops} steps = {confidence * (0.9**hops):.0%} effective confidence"
        )

    # Math/Physics: derived from equations (high reliability if solved)
    if source in ("math", "physics"):
        if confidence > 0.9:
            return TruthLabel(
                label="derived",
                confidence=confidence,
                source=source,
                explanation=f"Computed from {source} equations",
                caveats="Assumes correct problem interpretation"
            )
        else:
            return TruthLabel(
                label="heuristic",
                confidence=confidence,
                source=source,
                explanation=f"Partial {source} solution (some steps uncertain)",
                caveats="May have misinterpreted the problem format"
            )

    # Template: code generation, web generation, content generation
    if is_template or source in ("coder", "web", "creator"):
        return TruthLabel(
            label="template",
            confidence=confidence,
            source=source,
            explanation=f"Generated from structural patterns ({source} engine)",
            caveats="Output follows fixed patterns; may not match specific requirements"
        )

    # ACES explanations: heuristic (pattern-matched understanding)
    if source == "aces":
        return TruthLabel(
            label="heuristic",
            confidence=confidence,
            source=source,
            explanation="Explanation generated from structural analysis",
            caveats="Based on pattern matching, not deep understanding"
        )

    # Default: heuristic guess
    if confidence > 0.5:
        return TruthLabel(
            label="heuristic",
            confidence=confidence,
            source=source,
            explanation=f"Best-effort answer from {source}",
            caveats="Low confidence; may be incorrect"
        )

    return TruthLabel(
        label="unsupported",
        confidence=confidence,
        source=source,
        explanation=f"Insufficient data to answer reliably (source: {source})",
        caveats="Consider this unreliable"
    )


def format_truth(label: TruthLabel) -> str:
    """Format truth label for display."""
    icons = {
        "direct_fact": "✓",
        "derived": "⟶",
        "heuristic": "~",
        "template": "⊞",
        "unsupported": "✗",
    }
    icon = icons.get(label.label, "?")
    return f"[{icon} {label.label} | {label.confidence:.0%} | {label.source}] {label.caveats}"
