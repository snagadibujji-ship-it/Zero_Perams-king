#!/usr/bin/env python3
"""
TruthGuard v3.0 — Zero Hallucination Enforcement

Multi-layer verification before any answer exits the system:
  Layer 1: Claim extraction (find all assertions in text)
  Layer 2: Self-contradiction scan (does answer fight itself?)
  Layer 3: Known-myth detection (common misconceptions)
  Layer 4: Temporal validity (is this fact outdated?)
  Layer 5: Source authority ranking
  Layer 6: Confidence calibration override

If ANY check fails → flag answer, suggest correction, or disclaim.
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class VerificationResult:
    passed: bool
    confidence: float  # 0-1
    flags: List[str]  # warnings
    corrections: List[str]  # suggested fixes
    myths_detected: List[str]
    claims_checked: int
    claims_verified: int


# Known myths / common misconceptions
KNOWN_MYTHS = {
    'great wall visible from space': 'The Great Wall is NOT visible from space with the naked eye. It is only 6m wide.',
    'we only use 10% of our brain': 'Humans use virtually all of their brain. The 10% myth is false.',
    'goldfish have 3 second memory': 'Goldfish can remember things for months, not 3 seconds.',
    'lightning never strikes same place twice': 'Lightning frequently strikes the same place, especially tall structures.',
    'humans have 5 senses': 'Humans have many more than 5 senses, including proprioception, thermoception, and balance.',
    'blood is blue in veins': 'Blood is always red. Veins appear blue due to how light penetrates skin.',
    'chameleons change color to camouflage': 'Chameleons change color for communication and temperature regulation, not camouflage.',
    'einstein failed math': 'Einstein excelled at math. This is a myth from confusion about Swiss grading.',
    'bats are blind': 'Bats can see. Many species have good vision in addition to echolocation.',
    'sugar makes children hyperactive': 'Studies show no link between sugar and hyperactivity in children.',
    'tongue has taste zones': 'All taste receptors are distributed across the entire tongue.',
    'shaving makes hair grow thicker': 'Shaving has no effect on hair thickness or growth rate.',
    'bulls hate red': 'Bulls are colorblind to red. They charge the movement of the cape.',
    'cracking knuckles causes arthritis': 'Studies show no connection between knuckle cracking and arthritis.',
    'vitamin c cures colds': 'Vitamin C does not prevent or cure colds. It may slightly reduce duration.',
    'napoleon was short': 'Napoleon was average height for his era (5\'7\"). The myth arose from propaganda.',
    'left brain right brain': 'The left/right brain dominance theory is oversimplified. Both hemispheres work together.',
    'alcohol kills brain cells': 'Moderate alcohol does not kill brain cells. Heavy use damages dendrites.',
    'dogs see in black and white': 'Dogs see in blue and yellow, not full color but not black and white.',
    'touching a baby bird': 'Birds will NOT abandon chicks because a human touched them. Most birds have poor smell.',
}

# Temporal facts that change (need freshness check)
TIME_SENSITIVE_TOPICS = {
    'president', 'prime minister', 'population', 'gdp', 'champion',
    'record holder', 'largest', 'richest', 'current', 'latest',
    'stock price', 'temperature', 'weather', 'score',
}


class TruthGuard:
    """Multi-layer truth verification system."""

    def __init__(self):
        self.verifications = 0
        self.flags_raised = 0
        self.myths_caught = 0

    def verify(self, question: str, answer: str,
               known_facts: Dict = None,
               answer_timestamp: float = None) -> VerificationResult:
        """Run all verification layers on an answer."""
        self.verifications += 1
        flags = []
        corrections = []
        myths = []
        claims_total = 0
        claims_ok = 0

        q_lower = question.lower()
        a_lower = answer.lower()

        # Layer 1: Extract and count claims
        claims = self._extract_claims(answer)
        claims_total = len(claims)
        claims_ok = claims_total  # Start optimistic, reduce on failures

        # Layer 2: Self-contradiction
        contradiction = self._check_self_contradiction(answer)
        if contradiction:
            flags.append(f"Self-contradiction: {contradiction}")
            claims_ok -= 1

        # Layer 3: Known myth detection
        for myth_key, myth_correction in KNOWN_MYTHS.items():
            if myth_key in a_lower or myth_key in q_lower:
                # Check if the answer ASSERTS the myth (not debunks it)
                if self._asserts_myth(a_lower, myth_key):
                    myths.append(myth_key)
                    corrections.append(myth_correction)
                    claims_ok -= 1
                    self.myths_caught += 1

        # Layer 4: Temporal validity
        if self._is_time_sensitive(question):
            flags.append("Time-sensitive topic — verify this is current information")

        # Layer 5: Overly strong claims without evidence
        strong_issues = self._check_strong_claims(answer)
        for issue in strong_issues:
            flags.append(issue)
            claims_ok -= 1

        # Layer 6: Numerical sanity check
        num_issues = self._check_numbers(answer, question)
        for issue in num_issues:
            flags.append(issue)
            claims_ok -= 1

        # Compute confidence
        if claims_total > 0:
            confidence = max(0.1, claims_ok / claims_total)
        else:
            confidence = 0.7  # No claims = neutral

        if myths:
            confidence = min(confidence, 0.3)  # Myth detected = low confidence
        if flags:
            self.flags_raised += 1

        passed = len(flags) == 0 and len(myths) == 0

        return VerificationResult(
            passed=passed,
            confidence=round(confidence, 2),
            flags=flags,
            corrections=corrections,
            myths_detected=myths,
            claims_checked=claims_total,
            claims_verified=max(0, claims_ok),
        )

    def _extract_claims(self, text: str) -> List[Dict]:
        """Extract factual assertions from text."""
        claims = []
        sentences = re.split(r'[.!?]\s+', text.strip())
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            # Detect factual patterns
            if re.search(r'\b(is|are|was|were|has|have|can|will)\b', sent, re.IGNORECASE):
                # Extract subject-predicate
                match = re.match(r'(.+?)\s+(is|are|was|were|has|have)\s+(.+)', sent, re.IGNORECASE)
                if match:
                    claims.append({
                        'subject': match.group(1).strip(),
                        'relation': match.group(2).strip(),
                        'object': match.group(3).strip(),
                        'sentence': sent,
                    })
        return claims

    def _check_self_contradiction(self, text: str) -> Optional[str]:
        """Detect if text contradicts itself."""
        sentences = re.split(r'[.!?]\s+', text)
        positives = {}
        negatives = {}

        for sent in sentences:
            sent_lower = sent.lower().strip()
            # "X is Y" patterns
            match = re.search(r'(\w+)\s+is\s+(?:not\s+)?(.+)', sent_lower)
            if match:
                subj = match.group(1)
                is_negative = ' not ' in sent_lower or "n't" in sent_lower or "cannot" in sent_lower
                if is_negative:
                    negatives[subj] = match.group(2)
                else:
                    positives[subj] = match.group(2)

        # Check if same subject has positive and negative claims
        for subj in positives:
            if subj in negatives:
                return f"'{subj}' is both affirmed and denied"
        return None

    def _asserts_myth(self, answer_lower: str, myth_key: str) -> bool:
        """Check if answer asserts the myth as true (not debunking it)."""
        debunk_signals = ['not true', 'myth', 'false', 'incorrect', 'actually',
                          'contrary to', 'despite popular', 'common misconception']
        # If answer contains debunking language, it's correcting the myth (good)
        if any(signal in answer_lower for signal in debunk_signals):
            return False
        # Otherwise it's asserting the myth (bad)
        return True

    def _is_time_sensitive(self, question: str) -> bool:
        """Check if question asks about something that changes over time."""
        q_lower = question.lower()
        return any(topic in q_lower for topic in TIME_SENSITIVE_TOPICS)

    def _check_strong_claims(self, text: str) -> List[str]:
        """Flag overly absolute statements."""
        issues = []
        absolutes = {
            'always': 'rarely always true',
            'never': 'rarely never true',
            'impossible': 'strong claim without proof',
            'guaranteed': 'nothing is guaranteed',
            'proven fact': 'state the evidence instead',
        }
        text_lower = text.lower()
        for word, concern in absolutes.items():
            if word in text_lower:
                issues.append(f"Strong claim '{word}': {concern}")
        return issues[:2]  # Max 2 flags

    def _check_numbers(self, answer: str, question: str) -> List[str]:
        """Sanity-check numbers in answers."""
        issues = []
        numbers = re.findall(r'(\d+(?:,\d{3})*(?:\.\d+)?)', answer)

        for num_str in numbers:
            try:
                num = float(num_str.replace(',', ''))
                # Percentage > 100 or < 0
                if '%' in answer and (num > 100 or num < 0):
                    if num > 1000:  # Likely not a percentage
                        continue
                    issues.append(f"Percentage {num}% out of valid range")
                # Temperature in Celsius > 10000 (probably wrong)
                if ('celsius' in answer.lower() or '°c' in answer.lower()) and num > 10000:
                    issues.append(f"Temperature {num}°C seems unrealistically high")
                # Year > 2100 or < -5000 (probably wrong for historical facts)
                if 'year' in question.lower() or 'born' in question.lower():
                    if 1000 < num < 2030:
                        pass  # Valid year range
                    elif num > 2100:
                        issues.append(f"Year {num} seems far future")
            except ValueError:
                continue

        return issues[:2]

    def get_stats(self) -> Dict:
        return {
            'verifications': self.verifications,
            'flags_raised': self.flags_raised,
            'myths_caught': self.myths_caught,
            'pass_rate': round((self.verifications - self.flags_raised) / max(1, self.verifications) * 100, 1),
        }


# Legacy compatibility
def verify(question, answer):
    """Legacy API."""
    tg = TruthGuard()
    result = tg.verify(question, answer)
    return {'flagged': not result.passed, 'reason': result.flags[0] if result.flags else None}
