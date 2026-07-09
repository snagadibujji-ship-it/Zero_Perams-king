"""
Metacognitive Reasoning System — Based on 2026 SOFAI-LM research:
"Language Models Coupled with Metacognition Can Outperform Reasoning Models"
Run 5 quality checks on answers. If any fail, improve before presenting.
"""
import re
from typing import Optional

class MetacognitiveReasoner:
    CAUSAL = {'because', 'due to', 'causes', 'result', 'since', 'therefore', 'reason'}
    TIME = {'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
            'september', 'october', 'november', 'december', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'yesterday',
            'today', 'tomorrow', 'morning', 'evening', 'year', 'month', 'week', 'ago'}
    HEDGE = {'maybe', 'perhaps', 'possibly', 'might', 'could be', 'i think',
             'probably', 'not sure', 'uncertain', 'arguably', 'seemingly'}
    VAGUE = {'thing', 'stuff', 'something', 'somehow', 'somewhere', 'whatever',
             'kind of', 'sort of', 'like', 'basically', 'generally', 'various'}
    AMBIGUOUS = {
        'python': 'Do you mean the programming language or the snake?',
        'java': 'Do you mean the programming language or the island?',
        'rust': 'Do you mean the programming language or the oxidation process?',
        'apple': 'Do you mean Apple the company or the fruit?',
        'mercury': 'Do you mean the planet, the element, or the Roman god?',
        'bat': 'Do you mean the animal or the sports equipment?',
    }
    STOPS = {'is', 'are', 'the', 'a', 'an', 'what', 'why', 'how', 'when', 'where',
             'do', 'does', 'did', 'can', 'could', 'would', 'should', 'will', 'of',
             'in', 'on', 'at', 'to', 'for', 'it', 'this', 'that', 'be', 'was', 'were'}

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.improvements_made = 0

    def evaluate_answer(self, question: str, answer: str, knowledge_context: Optional[str] = None):
        """Run 5 metacognitive checks. Returns quality report with optional improved answer."""
        issues = []
        q, a = question.lower().strip(), answer.lower().strip()
        for check in [self._completeness, self._consistency, self._confidence,
                      self._relevance, self._specificity]:
            issue = check(q, a) if check != self._relevance else check(q, a, knowledge_context)
            if issue:
                issues.append(issue)
        score = max(0.0, round(1.0 - len(issues) * 0.2, 2))
        passed = 5 - len(issues)
        self.checks_passed += passed
        self.checks_failed += len(issues)
        improved = None
        if issues:
            improved = self.improve_answer(question, answer, issues)
            if improved != answer:
                self.improvements_made += 1
        return {'quality_score': score, 'issues': issues,
                'improved_answer': improved, 'checks_passed': passed}

    def _completeness(self, q: str, a: str):
        if 'why' in q.split() or q.startswith('why'):
            if not any(w in a for w in self.CAUSAL):
                return {'type': 'incomplete', 'detail': 'Asks "why" but no causal language'}
        if 'how many' in q or 'how much' in q:
            if not re.search(r'\d+', a):
                return {'type': 'incomplete', 'detail': 'Asks quantity but no number given'}
        if 'when' in q.split() or q.startswith('when'):
            if not any(w in a for w in self.TIME) and not re.search(r'\d{4}|\d{1,2}/\d', a):
                return {'type': 'incomplete', 'detail': 'Asks "when" but no time reference'}
        if 'where' in q.split() or q.startswith('where'):
            if not re.search(r'in |at |on |near |inside |outside |between ', a):
                return {'type': 'incomplete', 'detail': 'Asks "where" but no location'}
        return None

    def _consistency(self, q: str, a: str):
        sentences = [s.strip() for s in re.split(r'[.!?]', a) if s.strip()]
        seen = {}
        for s in sentences:
            pos = re.findall(r'(\w+)\s+(?:is|are|was|were|can|will)\s+(\w+)', s)
            neg = re.findall(r'(\w+)\s+(?:is not|are not|isn\'t|aren\'t|cannot|can\'t|was not|weren\'t)\s+(\w+)', s)
            for subj, obj in pos:
                key = (subj, obj)
                if key in seen and seen[key] is False:
                    return {'type': 'contradiction', 'detail': f'Contradicts: "{subj}" being "{obj}"'}
                seen[key] = True
            for subj, obj in neg:
                key = (subj, obj)
                if key in seen and seen[key] is True:
                    return {'type': 'contradiction', 'detail': f'Contradicts: "{subj}" being "{obj}"'}
                seen[key] = False
        return None

    def _confidence(self, q: str, a: str):
        if len(a) < 20:
            return {'type': 'too_vague', 'detail': 'Answer too short to be substantive'}
        hedge_count = sum(1 for w in self.HEDGE if w in a)
        if hedge_count / max(len(a.split()), 1) > 0.1:
            return {'type': 'no_hedge', 'detail': 'Too many hedge words'}
        absolutes = {'always', 'never', 'everyone', 'nobody', 'impossible', 'guaranteed'}
        if hedge_count == 0 and any(m in a for m in absolutes):
            return {'type': 'overconfident', 'detail': 'Absolute claim without hedging'}
        return None

    def _relevance(self, q: str, a: str, ctx: Optional[str] = None):
        q_words = {w for w in re.findall(r'\w+', q) if len(w) > 2 and w not in self.STOPS}
        if not q_words:
            return None
        combined = a + ' ' + (ctx or '')
        matches = sum(1 for w in q_words if w in combined)
        if matches / len(q_words) < 0.3:
            return {'type': 'off_topic', 'detail': f'{matches}/{len(q_words)} key words matched'}
        return None

    def _specificity(self, q: str, a: str):
        words = re.findall(r'\w+', a)
        if not words:
            return {'type': 'too_vague', 'detail': 'Answer is empty'}
        concrete = sum(1 for w in words if w not in self.VAGUE and (len(w) > 3 or w.isdigit()))
        spec = min((concrete / len(words)) + (0.1 if re.search(r'\d', a) else 0), 1.0)
        if spec < 0.3:
            return {'type': 'too_vague', 'detail': f'Specificity {spec:.2f} — too vague'}
        return None

    def improve_answer(self, question: str, answer: str, issues: list) -> str:
        """Try to fix identified issues. Returns improved or original answer."""
        improved = answer
        for issue in issues:
            t = issue['type']
            if t == 'too_vague':
                improved += " (More specific information would be needed to elaborate.)"
            elif t == 'no_hedge':
                improved = "Based on available information, " + improved
            elif t == 'overconfident':
                improved = "Generally speaking, " + improved
            elif t == 'off_topic':
                improved += " [Note: this may not fully address the question asked.]"
            elif t == 'incomplete':
                d = issue.get('detail', '')
                if 'causal' in d:
                    improved += " This is likely because of underlying factors not yet detailed."
                elif 'quantity' in d or 'number' in d:
                    improved += " (Exact numbers are not available in this context.)"
                elif 'time' in d:
                    improved += " (The exact timing is not specified here.)"
                else:
                    improved += " However, I may be missing some details about this."
            elif t == 'contradiction':
                improved += " [Warning: may contain contradictory statements.]"
        return improved

    def should_ask_clarification(self, question: str):
        """Detect ambiguous questions. Returns (should_ask: bool, clarification: str)."""
        words = question.strip().split()
        if words and words[0].lower() in {'it', 'that', 'this', 'they', 'them', 'those'}:
            return (True, "Could you clarify what you're referring to?")
        if len(words) < 3:
            return (True, "Could you provide more context for your question?")
        q_lower = question.lower()
        for term, msg in self.AMBIGUOUS.items():
            if term in q_lower.split() and len(words) < 6:
                return (True, msg)
        return (False, "")

    def get_stats(self):
        total = self.checks_passed + self.checks_failed
        return {'total_evaluations': total,
                'pass_rate': round(self.checks_passed / max(total, 1), 2),
                'improvements_made': self.improvements_made}


if __name__ == '__main__':
    r = MetacognitiveReasoner()
    print("=== Metacognitive Reasoner Self-Test ===\n")

    tests = [
        ("Why is the sky blue?", "The sky is blue.", lambda res: res['checks_passed'] < 5,
         "Check 1: detected missing causal language"),
        ("Why is the sky blue?", "The sky is blue because of Rayleigh scattering.", lambda res: res['quality_score'] >= 0.8,
         "Check 1: good causal answer passes"),
        ("Tell me about cats", "A cat is friendly. A cat is not friendly.", lambda res: any(i['type'] == 'contradiction' for i in res['issues']),
         "Check 2: detected contradiction"),
        ("Explain quantum physics", "It's stuff.", lambda res: any(i['type'] == 'too_vague' for i in res['issues']),
         "Check 3/5: detected vague answer"),
        ("What is photosynthesis?", "Basketball is played with five players.", lambda res: any(i['type'] == 'off_topic' for i in res['issues']),
         "Check 4: detected off-topic answer"),
        ("Is this approach good?", "This is always the best approach and never fails.", lambda res: any(i['type'] == 'overconfident' for i in res['issues']),
         "Check 3: detected overconfidence"),
    ]
    for q, a, check, label in tests:
        res = r.evaluate_answer(q, a)
        assert check(res), f"FAIL: {label}"
        print(f"[PASS] {label} — score={res['quality_score']}")

    # Clarification tests
    for q, expected, label in [
        ("It doesn't work", True, "pronoun without antecedent"),
        ("Tell me about Python", True, "ambiguous term"),
        ("Help me", True, "short question"),
        ("How does photosynthesis convert sunlight into energy?", False, "clear question"),
    ]:
        ask, msg = r.should_ask_clarification(q)
        assert ask == expected, f"FAIL: {label}"
        print(f"[PASS] Clarification: {label}" + (f" — '{msg}'" if msg else ""))

    # Improvement test
    res = r.evaluate_answer("Why do birds fly?", "Birds fly.")
    assert res['improved_answer'] and res['improved_answer'] != "Birds fly."
    print(f"[PASS] Improvement applied: '{res['improved_answer'][:60]}...'")

    print(f"\n=== Stats: {r.get_stats()} ===")
    print(f"\nAll 11 tests passed. Metacognitive reasoner is operational.")
