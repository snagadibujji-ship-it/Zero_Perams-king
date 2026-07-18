"""
AXIMA Understanding Pipeline — Framework for knowledge abstraction.

Pipeline: Fact → Pattern → Rule → Principle

Each level represents increasing abstraction:
  Fact:      "Water boils at 100°C at sea level"
  Pattern:   "Boiling points decrease with altitude"
  Rule:      "Lower pressure → lower boiling point"
  Principle: "Phase transitions depend on thermodynamic conditions"

This module defines the INTERFACES only. Future systems will implement
the actual intelligence (pattern detection, rule extraction, etc.)

Usage:
    from core.understanding import UnderstandingPipeline, Fact, Pattern, Rule, Principle

    pipeline = UnderstandingPipeline(graph=reality_graph)
    
    # Register facts
    fact = pipeline.register_fact("Water boils at 100°C", source="chemistry", confidence=1.0)
    
    # Promote when patterns emerge
    pattern = pipeline.promote_to_pattern([fact1, fact2, fact3], "Boiling points vary with pressure")
    
    # Derive rules from patterns
    rule = pipeline.derive_rule([pattern1, pattern2], "Lower pressure → lower boiling point")
    
    # Synthesize principles from rules
    principle = pipeline.synthesize_principle([rule1, rule2], "Phase transitions are pressure-dependent")
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from abc import ABC, abstractmethod

from core.reality_graph import get_reality_graph, RealityGraph


# ═══════════════════════════════════════════════════════════════
# ABSTRACTION LEVELS
# ═══════════════════════════════════════════════════════════════

class AbstractionLevel(str, Enum):
    """Levels of understanding, from concrete to abstract."""
    FACT = "fact"            # Raw observation or data point
    PATTERN = "pattern"      # Recurring regularity across facts
    RULE = "rule"            # Causal/conditional relationship
    PRINCIPLE = "principle"  # Deep structural truth


# ═══════════════════════════════════════════════════════════════
# KNOWLEDGE ITEMS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Fact:
    """A concrete, verifiable observation.
    
    Facts are the ground truth. They come from:
    - Knowledge base lookups
    - User corrections
    - Verified computations
    - External data
    """
    id: str = ""
    content: str = ""               # The fact statement
    source: str = ""                # Where it came from
    domain: str = ""                # Topic area
    confidence: float = 1.0         # How reliable (0-1)
    verified: bool = False          # Independently verified?
    created_at: float = 0.0
    used_count: int = 0             # Times this fact was used
    tags: List[str] = field(default_factory=list)


@dataclass
class Pattern:
    """A recurring regularity observed across multiple facts.
    
    Patterns emerge when the system notices:
    - Similar structures in different facts
    - Repeated relationships
    - Statistical regularities
    """
    id: str = ""
    description: str = ""           # What the pattern is
    supporting_facts: List[str] = field(default_factory=list)  # Fact IDs
    occurrences: int = 0            # How many times observed
    confidence: float = 0.0         # Based on evidence strength
    domain: str = ""
    created_at: float = 0.0
    contradictions: List[str] = field(default_factory=list)  # Fact IDs that contradict


@dataclass
class Rule:
    """A causal or conditional relationship derived from patterns.
    
    Rules express: IF condition THEN consequence (with confidence).
    They are derived from patterns and validated against facts.
    """
    id: str = ""
    statement: str = ""             # "IF X THEN Y" or "X causes Y"
    condition: str = ""             # The IF part
    consequence: str = ""           # The THEN part
    supporting_patterns: List[str] = field(default_factory=list)  # Pattern IDs
    confidence: float = 0.0
    domain: str = ""
    exceptions: List[str] = field(default_factory=list)  # Known exceptions
    created_at: float = 0.0
    validated: bool = False         # Tested against new data?


@dataclass
class Principle:
    """A deep structural truth synthesized from rules.
    
    Principles are the highest level of understanding:
    - They generalize across domains
    - They explain WHY rules work
    - They predict new rules
    """
    id: str = ""
    statement: str = ""             # The principle
    supporting_rules: List[str] = field(default_factory=list)  # Rule IDs
    scope: str = ""                 # How broadly applicable
    confidence: float = 0.0
    domain: str = ""
    created_at: float = 0.0
    predictions: List[str] = field(default_factory=list)  # What this principle predicts


# ═══════════════════════════════════════════════════════════════
# PIPELINE STAGES (Interfaces for future implementation)
# ═══════════════════════════════════════════════════════════════

class PatternDetector(ABC):
    """Interface: Detects patterns in collections of facts.
    
    Future implementations might use:
    - Structural similarity
    - Co-occurrence analysis
    - Clustering
    - Statistical tests
    """

    @abstractmethod
    def detect(self, facts: List[Fact], min_occurrences: int = 3) -> List[Pattern]:
        """Find patterns in a set of facts."""
        ...


class RuleExtractor(ABC):
    """Interface: Extracts causal rules from patterns.
    
    Future implementations might use:
    - Conditional logic extraction
    - Causal graph analysis
    - Counterfactual reasoning
    """

    @abstractmethod
    def extract(self, patterns: List[Pattern]) -> List[Rule]:
        """Derive rules from observed patterns."""
        ...


class PrincipleSynthesizer(ABC):
    """Interface: Synthesizes principles from rules.
    
    Future implementations might use:
    - Abstraction/generalization
    - Cross-domain analogy
    - Compression (minimum description length)
    """

    @abstractmethod
    def synthesize(self, rules: List[Rule]) -> List[Principle]:
        """Synthesize high-level principles from rules."""
        ...


# ═══════════════════════════════════════════════════════════════
# UNDERSTANDING PIPELINE
# ═══════════════════════════════════════════════════════════════

class UnderstandingPipeline:
    """Orchestrates the Fact → Pattern → Rule → Principle pipeline.
    
    This is the FRAMEWORK. Actual intelligence will be plugged in
    via PatternDetector, RuleExtractor, and PrincipleSynthesizer
    implementations in future phases.
    """

    def __init__(self, graph: Optional[RealityGraph] = None):
        self._graph = graph or get_reality_graph()
        self._pattern_detector: Optional[PatternDetector] = None
        self._rule_extractor: Optional[RuleExtractor] = None
        self._principle_synthesizer: Optional[PrincipleSynthesizer] = None

    # ─── Plugin slots ───

    def set_pattern_detector(self, detector: PatternDetector):
        """Plug in a pattern detection implementation."""
        self._pattern_detector = detector

    def set_rule_extractor(self, extractor: RuleExtractor):
        """Plug in a rule extraction implementation."""
        self._rule_extractor = extractor

    def set_principle_synthesizer(self, synthesizer: PrincipleSynthesizer):
        """Plug in a principle synthesis implementation."""
        self._principle_synthesizer = synthesizer

    # ─── Fact registration ───

    def register_fact(self, content: str, source: str = "",
                      domain: str = "", confidence: float = 1.0,
                      tags: Optional[List[str]] = None) -> str:
        """Register a new fact in the reality graph. Returns fact node ID."""
        props = {
            "content": content,
            "source": source,
            "domain": domain,
            "confidence": confidence,
            "verified": False,
            "used_count": 0,
            "tags": tags or [],
            "level": AbstractionLevel.FACT.value,
        }
        fact_id = self._graph.add_node("fact", content[:80], props)
        self._graph.save()
        return fact_id

    # ─── Manual promotion (until detectors are implemented) ───

    def promote_to_pattern(self, fact_ids: List[str], description: str,
                           domain: str = "") -> str:
        """Manually promote a set of facts to a pattern. Returns pattern node ID."""
        props = {
            "description": description,
            "domain": domain,
            "occurrences": len(fact_ids),
            "confidence": min(0.9, 0.3 + len(fact_ids) * 0.1),
            "level": AbstractionLevel.PATTERN.value,
        }
        pattern_id = self._graph.add_node("concept", description[:80], props)

        # Link supporting facts
        for fid in fact_ids:
            self._graph.add_edge(pattern_id, fid, "derived_from")
            self._graph.add_edge(fid, pattern_id, "supports")

        self._graph.save()
        return pattern_id

    def derive_rule(self, pattern_ids: List[str], statement: str,
                    condition: str = "", consequence: str = "",
                    domain: str = "") -> str:
        """Manually derive a rule from patterns. Returns rule node ID."""
        props = {
            "statement": statement,
            "condition": condition,
            "consequence": consequence,
            "domain": domain,
            "confidence": min(0.85, 0.4 + len(pattern_ids) * 0.15),
            "validated": False,
            "level": AbstractionLevel.RULE.value,
        }
        rule_id = self._graph.add_node("theory", statement[:80], props)

        # Link supporting patterns
        for pid in pattern_ids:
            self._graph.add_edge(rule_id, pid, "derived_from")
            self._graph.add_edge(pid, rule_id, "supports")

        self._graph.save()
        return rule_id

    def synthesize_principle(self, rule_ids: List[str], statement: str,
                             scope: str = "", domain: str = "") -> str:
        """Manually synthesize a principle from rules. Returns principle node ID."""
        props = {
            "statement": statement,
            "scope": scope,
            "domain": domain,
            "confidence": min(0.8, 0.3 + len(rule_ids) * 0.1),
            "level": AbstractionLevel.PRINCIPLE.value,
        }
        principle_id = self._graph.add_node("theory", statement[:80], props)

        # Link supporting rules
        for rid in rule_ids:
            self._graph.add_edge(principle_id, rid, "derived_from")
            self._graph.add_edge(rid, principle_id, "supports")

        self._graph.save()
        return principle_id

    # ─── Automated pipeline (uses plugged-in implementations) ───

    def run_pipeline(self, domain: Optional[str] = None) -> Dict[str, int]:
        """Run the full pipeline on accumulated facts.
        
        Returns counts of newly created items at each level.
        Only works if detector/extractor/synthesizer are plugged in.
        """
        results = {"patterns": 0, "rules": 0, "principles": 0}

        # Get facts
        facts = self._get_facts(domain)
        if not facts:
            return results

        # Stage 1: Detect patterns
        if self._pattern_detector:
            fact_objects = [self._node_to_fact(f) for f in facts]
            new_patterns = self._pattern_detector.detect(fact_objects)
            for p in new_patterns:
                self.promote_to_pattern(
                    [f.id for f in p.supporting_facts] if hasattr(p, 'supporting_facts') else [],
                    p.description, p.domain
                )
                results["patterns"] += 1

        # Stage 2: Extract rules
        patterns = self._get_patterns(domain)
        if self._rule_extractor and patterns:
            pattern_objects = [self._node_to_pattern(p) for p in patterns]
            new_rules = self._rule_extractor.extract(pattern_objects)
            for r in new_rules:
                self.derive_rule([], r.statement, r.condition, r.consequence, r.domain)
                results["rules"] += 1

        # Stage 3: Synthesize principles
        rules = self._get_rules(domain)
        if self._principle_synthesizer and rules:
            rule_objects = [self._node_to_rule(r) for r in rules]
            new_principles = self._principle_synthesizer.synthesize(rule_objects)
            for p in new_principles:
                self.synthesize_principle([], p.statement, p.scope, p.domain)
                results["principles"] += 1

        return results

    # ─── Query ───

    def get_understanding(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get current understanding state for a domain."""
        facts = self._get_facts(domain)
        patterns = self._get_patterns(domain)
        rules = self._get_rules(domain)
        principles = self._get_principles(domain)

        return {
            "domain": domain or "all",
            "facts": len(facts),
            "patterns": len(patterns),
            "rules": len(rules),
            "principles": len(principles),
            "depth": (
                "principle" if principles else
                "rule" if rules else
                "pattern" if patterns else
                "fact" if facts else
                "empty"
            ),
        }

    # ─── Internal helpers ───

    def _get_facts(self, domain: Optional[str] = None) -> List:
        nodes = self._graph.find_nodes(node_type="fact")
        if domain:
            nodes = [n for n in nodes if n.properties.get("domain") == domain]
        return nodes

    def _get_patterns(self, domain: Optional[str] = None) -> List:
        nodes = self._graph.find_nodes(node_type="concept")
        nodes = [n for n in nodes if n.properties.get("level") == AbstractionLevel.PATTERN.value]
        if domain:
            nodes = [n for n in nodes if n.properties.get("domain") == domain]
        return nodes

    def _get_rules(self, domain: Optional[str] = None) -> List:
        nodes = self._graph.find_nodes(node_type="theory")
        nodes = [n for n in nodes if n.properties.get("level") == AbstractionLevel.RULE.value]
        if domain:
            nodes = [n for n in nodes if n.properties.get("domain") == domain]
        return nodes

    def _get_principles(self, domain: Optional[str] = None) -> List:
        nodes = self._graph.find_nodes(node_type="theory")
        nodes = [n for n in nodes if n.properties.get("level") == AbstractionLevel.PRINCIPLE.value]
        if domain:
            nodes = [n for n in nodes if n.properties.get("domain") == domain]
        return nodes

    def _node_to_fact(self, node) -> Fact:
        return Fact(
            id=node.id,
            content=node.properties.get("content", node.label),
            source=node.properties.get("source", ""),
            domain=node.properties.get("domain", ""),
            confidence=node.properties.get("confidence", 1.0),
        )

    def _node_to_pattern(self, node) -> Pattern:
        return Pattern(
            id=node.id,
            description=node.properties.get("description", node.label),
            domain=node.properties.get("domain", ""),
            confidence=node.properties.get("confidence", 0.5),
        )

    def _node_to_rule(self, node) -> Rule:
        return Rule(
            id=node.id,
            statement=node.properties.get("statement", node.label),
            condition=node.properties.get("condition", ""),
            consequence=node.properties.get("consequence", ""),
            domain=node.properties.get("domain", ""),
            confidence=node.properties.get("confidence", 0.5),
        )


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_pipeline: Optional[UnderstandingPipeline] = None


def get_understanding_pipeline(graph: Optional[RealityGraph] = None) -> UnderstandingPipeline:
    """Get the global understanding pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = UnderstandingPipeline(graph=graph)
    return _pipeline
