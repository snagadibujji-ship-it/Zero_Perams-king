#!/usr/bin/env python3
"""
Metacognitive Reasoning System v3.0 — Maximum Level

Based on 2026 SOFAI-LM research: "Language Models Coupled with Metacognition
Can Outperform Reasoning Models"

8 quality checks on every answer. Self-correction before output.
Integrates with AST (Adversarial Self-Tribunal) and CUQ (Calibrated Uncertainty).

Checks:
  1. Completeness — does answer address the question fully?
  2. Consistency — does answer contradict itself?
  3. Confidence — is hedging language appropriate?
  4. Relevance — does answer match question topic?
  5. Specificity — is answer precise or vague?
  6. Factual grounding — does answer contain verifiable claims?
  7. Logical coherence — do sentences follow logically?
  8. Calibration — is stated confidence matching actual reliability?
"""

import re
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class QualityReport:
    score: float  # 0-1 overall quality
    issues: List[Dict]  # detected problems
    improved_answer: Optional[str]  # auto-improved version (or None)
    checks_passed: int
    checks_total: int = 8
    confidence_calibrated: float = 0.0  # calibrated confidence for this answer
    should_disclaim: bool = False  # should add uncertainty disclaimer?
    disambiguation_needed: bool = False
    disambiguation_question: str = ""


class MetacognitiveReasoner:
    """8-check quality system with auto-improvement and calibration."""

    CAUSAL_WORDS = {'because', 'due to', 'causes', 'caused by', 'result of',
                    'since', 'therefore', 'reason', 'leads to', 'consequence',
                    'as a result', 'owing to', 'thanks to', 'on account of'}

    HEDGE_WORDS = {'maybe', 'perhaps', 'possibly', 'might', 'could be', 'i think',
                   'probably', 'not sure', 'uncertain', 'arguably', 'seemingly',
                   'it seems', 'appears to', 'likely', 'unlikely'}

    VAGUE_WORDS = {'thing', 'stuff', 'something', 'somehow', 'somewhere', 'whatever',
                   'kind of', 'sort of', 'like', 'basically', 'generally', 'various',
                   'many', 'some', 'often', 'sometimes', 'usually'}

    STRONG_CLAIMS = {'always', 'never', 'all', 'none', 'every', 'impossible',
                     'guaranteed', 'certainly', 'definitely', 'absolutely', 'proven'}

    TIME_WORDS = {'january', 'february', 'march', 'april', 'may', 'june', 'july',
                  'august', 'september', 'october', 'november', 'december',
                  'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                  'saturday', 'sunday', 'yesterday', 'today', 'tomorrow',
                  'morning', 'evening', 'year', 'month', 'week', 'ago', 'since'}

    AMBIGUOUS_TERMS = {
        'python': 'Do you mean the programming language or the snake?',
        'java': 'Do you mean the programming language or the island?',
        'rust': 'Do you mean the programming language or the oxidation?',
        'apple': 'Do you mean Apple the company or the fruit?',
        'mercury': 'Do you mean the planet, the element, or the Roman god?',
        'bat': 'Do you mean the animal or the sports equipment?',
        'cell': 'Do you mean a biological cell or a prison cell?',
        'spring': 'Do you mean the season, a water spring, or a mechanical spring?',
        'bass': 'Do you mean the fish or the musical term?',
        'crane': 'Do you mean the bird or the construction machine?',
        'mars': 'Do you mean the planet or the Roman god?',
        'saturn': 'Do you mean the planet or the Roman god?',
        'iris': 'Do you mean the eye part, the flower, or the Greek goddess?',
    }

    QUESTION_EXPECTS = {
        'why': 'causal',    # Answer should explain cause
        'how': 'mechanism', # Answer should explain process
        'when': 'temporal', # Answer should include time
        'where': 'spatial', # Answer should include location
        'who': 'person',    # Answer should name someone
        'which': 'choice',  # Answer should pick from options
        'how many': 'number',  # Answer should include a count
        'how much': 'number',
    }

    STOPS = {'is', 'are', 'the', 'a', 'an', 'what', 'why', 'how', 'when', 'where',
             'do', 'does', 'did', 'can', 'could', 'would', 'should', 'will', 'of',
             'in', 'on', 'at', 'to', 'for', 'it', 'this', 'that', 'be', 'was', 'were'}

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.improvements_made = 0
        self.calibration_history = []  # (stated_conf, was_correct) for calibration

    def evaluate(self, question: str, answer: str,
                 knowledge_context: Optional[str] = None,
                 stated_confidence: float = 0.8) -> QualityReport:
        """Run all 8 metacognitive checks. Returns quality report."""
        if not answer or len(answer.strip()) < 3:
            return QualityReport(score=0, issues=[{'type': 'empty', 'detail': 'No answer'}],
                                 improved_answer=None, checks_passed=0)

        issues = []
        q = question.lower().strip()
        a = answer.lower().strip()

        # Run 8 checks
        checks = [
            self._check_completeness,
            self._check_consistency,
            self._check_confidence,
            self._check_relevance,
            self._check_specificity,
            self._check_factual_grounding,
            self._check_logical_coherence,
            self._check_calibration,
        ]

        for check in checks:
            issue = check(q, a, knowledge_context, stated_confidence)
            if issue:
                issues.append(issue)

        # Score
        passed = 8 - len(issues)
        score = max(0.0, round(passed / 8.0, 2))
        self.checks_passed += passed
        self.checks_failed += len(issues)

        # Auto-improve if issues found
        improved = None
        if issues and score < 0.75:
            improved = self._improve_answer(question, answer, issues)
            if improved and improved != answer:
                self.improvements_made += 1

        # Check disambiguation
        disambig_needed, disambig_q = self._check_disambiguation(question)

        # Calibrate confidence
        calibrated_conf = self._calibrate_confidence(stated_confidence, score, len(issues))
        should_disclaim = calibrated_conf < 0.5

        return QualityReport(
            score=score, issues=issues, improved_answer=improved,
            checks_passed=passed, confidence_calibrated=calibrated_conf,
            should_disclaim=should_disclaim,
            disambiguation_needed=disambig_needed,
            disambiguation_question=disambig_q,
        )

    # ═══════════════════════════════════════════════════════════
    # THE 8 CHECKS
    # ═══════════════════════════════════════════════════════════

    def _check_completeness(self, q, a, ctx, conf):
        """Does the answer address what was asked?"""
        # Why questions need causal language
        if q.startswith('why') or 'why ' in q:
            if not any(w in a for w in self.CAUSAL_WORDS):
                return {'type': 'incomplete', 'detail': 'Why-question needs causal explanation',
                        'fix': 'Add because/due to/caused by'}

        # When questions need time reference
        if q.startswith('when') or 'when ' in q:
            if not any(w in a for w in self.TIME_WORDS) and not re.search(r'\d{4}|\d{1,2}(st|nd|rd|th)', a):
                return {'type': 'incomplete', 'detail': 'When-question needs time reference'}

        # How-many needs a number
        if 'how many' in q or 'how much' in q:
            if not re.search(r'\d+', a):
                return {'type': 'incomplete', 'detail': 'Quantitative question needs a number'}

        # Very short answer for long question
        if len(q) > 50 and len(a) < 20:
            return {'type': 'incomplete', 'detail': 'Answer too brief for complex question'}

        return None

    def _check_consistency(self, q, a, ctx, conf):
        """Does the answer contradict itself?"""
        sentences = re.split(r'[.!?]\s+', a)
        if len(sentences) < 2:
            return None

        # Look for "X is Y" ... "X is not Y" patterns
        claims = {}
        for sent in sentences:
            # Extract "X is/are Y"
            match = re.search(r'(\w+)\s+(?:is|are)\s+(?:not\s+)?(.+)', sent)
            if match:
                subj = match.group(1)
                is_negative = ' not ' in sent or "n't" in sent
                obj = match.group(2).strip().rstrip('.,')
                key = subj.lower()
                if key in claims:
                    prev_neg = claims[key][1]
                    if prev_neg != is_negative:
                        return {'type': 'contradiction', 'detail': f'Contradicts itself about "{subj}"'}
                claims[key] = (obj, is_negative)

        return None

    def _check_confidence(self, q, a, ctx, conf):
        """Is hedging language appropriate?"""
        hedge_count = sum(1 for w in self.HEDGE_WORDS if w in a)
        strong_count = sum(1 for w in self.STRONG_CLAIMS if w in a)

        # Over-hedging on factual questions
        if hedge_count >= 3 and q.startswith(('what is', 'who is', 'where is')):
            return {'type': 'over_hedging', 'detail': 'Too much uncertainty for factual question',
                    'fix': 'Remove hedging if fact is known'}

        # Over-confident with strong claims
        if strong_count >= 2 and conf < 0.9:
            return {'type': 'over_confident', 'detail': 'Using absolute language without high confidence',
                    'fix': 'Replace "always/never" with "typically/rarely"'}

        return None

    def _check_relevance(self, q, a, ctx, conf):
        """Does answer match question topic?"""
        # Extract key content words from question
        q_words = set(q.split()) - self.STOPS
        a_words = set(a.split()) - self.STOPS

        if not q_words:
            return None

        # At least some overlap expected
        overlap = q_words & a_words
        if len(overlap) == 0 and len(q_words) >= 3:
            return {'type': 'off_topic', 'detail': 'Answer shares no keywords with question',
                    'fix': 'Answer should reference the topic asked about'}

        return None

    def _check_specificity(self, q, a, ctx, conf):
        """Is answer specific or too vague?"""
        vague_count = sum(1 for w in self.VAGUE_WORDS if w in a)

        if vague_count >= 3:
            return {'type': 'vague', 'detail': f'Answer uses {vague_count} vague terms',
                    'fix': 'Replace vague words with specific details'}

        # "It is a concept" style non-answers
        if re.search(r'is a concept|is a thing|is something', a):
            return {'type': 'non_answer', 'detail': 'Answer is a tautology (X is a concept)',
                    'fix': 'Provide actual defining information'}

        return None

    def _check_factual_grounding(self, q, a, ctx, conf):
        """Does answer contain verifiable claims vs hand-waving?"""
        # Short factual answers are fine
        if len(a) < 50:
            return None

        # Long answers should have some concrete details
        has_numbers = bool(re.search(r'\d+', a))
        has_names = bool(re.search(r'[A-Z][a-z]{2,}', a))  # Proper nouns
        has_specific = has_numbers or has_names

        if len(a) > 100 and not has_specific:
            return {'type': 'ungrounded', 'detail': 'Long answer without specific facts/names/numbers',
                    'fix': 'Add concrete details, dates, or names'}

        return None

    def _check_logical_coherence(self, q, a, ctx, conf):
        """Do sentences follow logically?"""
        sentences = re.split(r'[.!?]\s+', a)
        if len(sentences) < 3:
            return None

        # Check for non-sequiturs (sudden topic changes)
        prev_words = set()
        for sent in sentences:
            curr_words = set(sent.lower().split()) - self.STOPS
            if prev_words and curr_words:
                shared = prev_words & curr_words
                if len(shared) == 0 and len(prev_words) > 3 and len(curr_words) > 3:
                    return {'type': 'non_sequitur', 'detail': 'Sudden topic change between sentences'}
            prev_words = curr_words

        return None

    def _check_calibration(self, q, a, ctx, conf):
        """Is stated confidence realistic?"""
        # Very high confidence on speculative topics
        speculative = {'future', 'predict', 'will happen', 'might', 'could', 'opinion'}
        if conf > 0.9 and any(w in q for w in speculative):
            return {'type': 'miscalibrated', 'detail': 'High confidence on speculative question',
                    'fix': 'Lower confidence for prediction/opinion questions'}

        return None

    # ═══════════════════════════════════════════════════════════
    # IMPROVEMENT + DISAMBIGUATION
    # ═══════════════════════════════════════════════════════════

    def _improve_answer(self, question: str, answer: str, issues: List[Dict]) -> Optional[str]:
        """Try to fix the answer based on detected issues."""
        improved = answer

        for issue in issues:
            if issue['type'] == 'non_answer' and 'is a concept' in answer.lower():
                # Strip "X is a concept" non-answers
                improved = re.sub(r'.*?is a concept\.?\s*', '', improved, flags=re.IGNORECASE).strip()

            elif issue['type'] == 'over_hedging':
                # Remove excessive hedging
                for hedge in ['maybe', 'perhaps', 'possibly', 'I think']:
                    improved = improved.replace(hedge, '').replace(hedge.capitalize(), '')
                improved = re.sub(r'\s+', ' ', improved).strip()

            elif issue['type'] == 'over_confident':
                # Soften absolutes
                improved = improved.replace('always', 'typically').replace('never', 'rarely')
                improved = improved.replace('Always', 'Typically').replace('Never', 'Rarely')

        return improved if improved != answer and len(improved) > 10 else None

    def _check_disambiguation(self, question: str) -> Tuple[bool, str]:
        """Check if question has ambiguous terms."""
        words = question.lower().split()
        for word in words:
            word_clean = word.strip('?.,!').lower()
            if word_clean in self.AMBIGUOUS_TERMS:
                return True, self.AMBIGUOUS_TERMS[word_clean]
        return False, ""

    def _calibrate_confidence(self, stated: float, quality_score: float, num_issues: int) -> float:
        """Produce calibrated confidence based on answer quality."""
        # Start with stated confidence
        calibrated = stated
        # Reduce if quality checks failed
        calibrated *= (0.7 + 0.3 * quality_score)
        # Reduce further if many issues
        calibrated *= (1.0 - num_issues * 0.05)
        return max(0.1, min(0.99, calibrated))

    # ═══════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════

    def get_stats(self) -> Dict:
        total = self.checks_passed + self.checks_failed
        return {
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'pass_rate': round(self.checks_passed / max(1, total) * 100, 1),
            'improvements_made': self.improvements_made,
        }

    # Legacy API compatibility
    def evaluate_answer(self, question: str, answer: str, knowledge_context=None):
        """Legacy wrapper."""
        report = self.evaluate(question, answer, knowledge_context)
        return {
            'quality_score': report.score,
            'issues': report.issues,
            'improved_answer': report.improved_answer,
            'checks_passed': report.checks_passed,
        }
