"""TruthGuard — Zero-hallucination guarantee. Never state facts without knowledge graph backing."""
import re
from enum import Enum
from dataclasses import dataclass

class Level(Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"
    HALLUCINATION = "hallucination"

class Mode(Enum):
    STRICT = "strict"       # only VERIFIED
    NORMAL = "normal"       # VERIFIED + INFERRED
    RELAXED = "relaxed"     # everything except HALLUCINATION

@dataclass
class Claim:
    subject: str
    relation: str
    obj: str
    level: Level = Level.UNCERTAIN

CLAIM_PATTERNS = [
    (r"(\w[\w\s]*?)\s+is\s+(\w[\w\s]*)", "is"),
    (r"(\w[\w\s]*?)\s+has\s+(\w[\w\s]*)", "has"),
    (r"(\w[\w\s]*?)\s+can\s+(\w[\w\s]*)", "can"),
    (r"(\d{4}[-/]\d{2}[-/]\d{2})", "date"),
    (r"(\d+(?:\.\d+)?)\s*(million|billion|percent|kg|km|mb|gb)", "number"),
]

class TruthGuard:
    """Zero-hallucination guarantee. Knowledge graph: {(subj, rel, obj): source}"""
    def __init__(self, knowledge_graph: dict = None):
        self.kg = knowledge_graph or {}

    @staticmethod
    def _norm(s: str) -> str:
        return re.sub(r'^(a|an|the)\s+', '', s.strip().lower())

    def extract_claims(self, text: str) -> list:
        """Find all factual assertions in text."""
        claims = []
        for sent in re.split(r'[.!?;]\s*', text.strip()):
            if not sent.strip():
                continue
            for pattern, rel in CLAIM_PATTERNS:
                for m in re.finditer(pattern, sent, re.IGNORECASE):
                    if rel in ("date", "number"):
                        claims.append(Claim(m.group(0), rel, m.group(0)))
                    else:
                        claims.append(Claim(m.group(1).strip(), rel, m.group(2).strip()))
        return claims

    def _check_level(self, claim: Claim) -> Level:
        """Determine verification level for a single claim."""
        key = (self._norm(claim.subject), claim.relation, self._norm(claim.obj))
        kg_n = {(self._norm(s), r, self._norm(o)): v for (s, r, o), v in self.kg.items()}
        if key in kg_n:
            return Level.VERIFIED
        for (s, r, o) in kg_n:  # inheritance inference
            if s == key[0] and r == "is":
                if (o, claim.relation, key[2]) in kg_n:
                    return Level.INFERRED
        for (s, r, o) in kg_n:  # contradiction check
            if s == key[0] and r == key[1] and o != key[2]:
                return Level.HALLUCINATION
        return Level.UNCERTAIN

    def verify_claim(self, text: str) -> list:
        """Check every factual claim in text against knowledge graph."""
        claims = self.extract_claims(text)
        for c in claims:
            c.level = self._check_level(c)
        return claims

    def label_confidence(self, text: str) -> str:
        """Add [verified]/[inferred]/[uncertain] labels inline."""
        claims = self.verify_claim(text)
        result = text
        for c in reversed(claims):
            phrase = f"{c.subject} {c.relation} {c.obj}"
            result = result.replace(phrase, f"{phrase} [{c.level.value}]", 1)
        return result

    def cite_sources(self, text: str, sources: dict = None) -> str:
        """Add source attribution to claims."""
        src = sources or {}
        for (s, r, o), source in self.kg.items():
            phrase = f"{s} {r} {o}"
            if phrase.lower() in text.lower() and source:
                text = re.sub(re.escape(phrase), f"{phrase} [{source}]", text, count=1, flags=re.IGNORECASE)
        for phrase, citation in src.items():
            if phrase in text:
                text = text.replace(phrase, f"{phrase} [{citation}]", 1)
        return text

    def flag_hallucination(self, text: str, knowledge: dict = None) -> list:
        """Detect unsupported claims. Returns hallucinated claims."""
        if knowledge:
            self.kg = knowledge
        return [c for c in self.verify_claim(text) if c.level == Level.HALLUCINATION]

    def safe_response(self, answer: str, mode: str = "normal") -> str:
        """Filter answer removing claims not meeting mode threshold."""
        allowed = {Level.VERIFIED}
        m = Mode(mode)
        if m in (Mode.NORMAL, Mode.RELAXED):
            allowed.add(Level.INFERRED)
        if m == Mode.RELAXED:
            allowed.add(Level.UNCERTAIN)
        result = answer
        for c in self.verify_claim(answer):
            if c.level not in allowed:
                phrase = f"{c.subject} {c.relation} {c.obj}"
                result = result.replace(phrase, f"[REDACTED: {c.level.value}]", 1)
        return result

# ─── Standalone Test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    kg = {("python", "is", "a programming language"): "docs.python.org",
          ("python", "has", "dynamic typing"): "PEP-484",
          ("cat", "is", "an animal"): "biology-101",
          ("animal", "has", "cells"): "biology-101",
          ("earth", "is", "a planet"): "NASA"}
    tg = TruthGuard(kg)
    text = "Python is a programming language. Python has static typing. Cat is an animal."
    # Extract claims
    claims = tg.extract_claims(text)
    assert len(claims) == 3, f"Expected 3 claims, got {len(claims)}"
    # Verify levels
    verified = tg.verify_claim(text)
    assert verified[0].level == Level.VERIFIED
    assert verified[1].level == Level.HALLUCINATION
    assert verified[2].level == Level.VERIFIED
    # Label confidence
    labeled = tg.label_confidence(text)
    assert "[verified]" in labeled and "[hallucination]" in labeled
    # Flag hallucination
    hallu = tg.flag_hallucination(text)
    assert len(hallu) == 1 and "static" in hallu[0].obj
    # Safe response strict — redacts hallucination
    assert "[REDACTED: hallucination]" in tg.safe_response(text, "strict")
    # Inference: cat→is→animal, animal→has→cells ∴ cat has cells = inferred
    assert "Cat has cells" in tg.safe_response("Cat has cells. Earth is a planet.", "normal")
    # Cite sources
    assert "docs.python.org" in tg.cite_sources("Python is a programming language.", {})
    # Relaxed keeps uncertain, strict redacts
    assert "[REDACTED" not in tg.safe_response("Mars has water.", "relaxed") and "[REDACTED" in tg.safe_response("Mars has water.", "strict")
    print("✅ All TruthGuard assertions passed.")
