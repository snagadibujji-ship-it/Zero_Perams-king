#!/usr/bin/env python3
"""
PREDICT v3.0 — Dual Interpretation Engine + Smart Suggestions + Drilling

After every answer, shows 3 suggestions.
Pre-fetches answers for all 3.
When user responds, DIE interprets: is it about suggestions or new question?
Drilling: user can go 4 levels deep just by saying "yes" / "more" / "go on".

No word lists. No edge cases. Both interpretations scored. Higher wins.
"""

import re, time, os, sys
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(__file__))


# ═══════════════════════════════════════════════════════════════
# CONVERSATION STATE
# ═══════════════════════════════════════════════════════════════

class PredictState:
    """Tracks suggestion state across turns."""
    OPEN = 'open'           # No suggestions active
    SUGGESTING = 'suggest'  # Suggestions displayed, waiting for response
    DRILLING = 'drilling'   # User accepted, drilling deeper

    def __init__(self):
        self.state = self.OPEN
        self.suggestions = []       # List of {"question": str, "answer": str}
        self.drill_depth = 0        # How deep into a topic
        self.max_depth = 4
        self.current_topic = ''     # Main topic being discussed
        self.topic_history = []     # Last 10 topics
        self.last_answer = ''

    def clear(self):
        self.state = self.OPEN
        self.suggestions = []
        self.drill_depth = 0


# ═══════════════════════════════════════════════════════════════
# DUAL INTERPRETATION ENGINE (DIE)
# ═══════════════════════════════════════════════════════════════

class DualInterpretation:
    """Try both interpretations. Pick the one that makes more sense."""

    STOP_WORDS = {'what', 'is', 'the', 'a', 'an', 'who', 'where', 'when', 'how',
                  'why', 'are', 'was', 'do', 'does', 'tell', 'me', 'about',
                  'can', 'you', 'please', 'i', 'want', 'to', 'know', 'it', 'that',
                  'this', 'of', 'in', 'on', 'for', 'and', 'or', 'but', 'so'}

    QUESTION_WORDS = {'what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose'}

    def interpret(self, user_input: str, suggestions: List[Dict]) -> Dict:
        """
        Returns:
          {"action": "accept", "index": 0-2}    → trigger suggestion
          {"action": "new", "query": "..."}      → process as new question
          {"action": "reject"}                   → clear suggestions
          {"action": "ambiguous"}                → ask user to clarify
        """
        text = user_input.strip()
        text_lower = text.lower()
        words = text_lower.split()

        # Score both branches
        score_a = self._score_acceptance(text_lower, words, suggestions)
        score_b = self._score_new_question(text_lower, words, suggestions)

        # Explicit rejection
        if self._is_rejection(text_lower):
            return {"action": "reject"}

        # If tied within 0.2, ambiguous
        if abs(score_a['score'] - score_b['score']) < 0.2:
            # Tiebreaker: shorter inputs lean toward acceptance
            if len(words) <= 3:
                return {"action": "accept", "index": score_a['index']}
            else:
                return {"action": "ambiguous"}

        # Branch A wins: trigger suggestion
        if score_a['score'] > score_b['score']:
            return {"action": "accept", "index": score_a['index']}

        # Branch B wins: new question
        return {"action": "new", "query": text}

    def _score_acceptance(self, text: str, words: List[str], suggestions: List[Dict]) -> Dict:
        """Score: how likely is this input referring to suggestions?"""
        score = 0.0
        index = 0  # Which suggestion to trigger

        # Explicit number reference
        if text in ('1', '2', '3'):
            return {'score': 1.0, 'index': int(text) - 1}

        # Ordinal reference
        ordinals = {'first': 0, 'second': 1, 'third': 2, 'last': -1,
                    'first one': 0, 'second one': 1, 'third one': 2, 'last one': -1}
        for phrase, idx in ordinals.items():
            if phrase in text:
                actual_idx = idx if idx >= 0 else len(suggestions) - 1
                return {'score': 1.0, 'index': min(actual_idx, len(suggestions) - 1)}

        # Pure agreement (no real content beyond agreement)
        agreement = {'yes', 'yeah', 'yep', 'ok', 'okay', 'sure', 'go on', 'continue',
                     'more', 'tell me', 'go ahead', 'why not', 'alright', 'right',
                     'please', 'do it', 'show me'}
        if text in agreement or all(w in agreement | {'the', 'me', 'it', 'on'} for w in words):
            score += 0.8

        # Reactions (interested but not asking new thing)
        reactions = {'interesting', 'cool', 'wow', 'nice', 'great', 'huh',
                     'really', 'oh', 'fascinating', 'amazing'}
        if text in reactions or (len(words) == 1 and words[0] in reactions):
            score += 0.6

        # Input contains keywords from a specific suggestion
        if suggestions:
            for i, sug in enumerate(suggestions):
                sug_words = set(sug['question'].lower().split()) - self.STOP_WORDS
                input_words = set(words) - self.STOP_WORDS
                if sug_words and input_words:
                    overlap = len(sug_words & input_words) / len(sug_words)
                    if overlap > 0.3:
                        score += 0.5 + overlap * 0.3
                        index = i

        # Short input with no identifiable new topic
        content_words = set(words) - self.STOP_WORDS - agreement - reactions
        if len(content_words) == 0:
            score += 0.4

        # Penalty: contains a noun NOT in any suggestion (new topic signal)
        if suggestions:
            all_sug_words = set()
            for sug in suggestions:
                all_sug_words.update(sug['question'].lower().split())
            new_nouns = content_words - all_sug_words
            if new_nouns and len(new_nouns) >= 1:
                # Check if new noun is a real topic (more than 3 chars, not a filler)
                real_new = [w for w in new_nouns if len(w) > 3]
                if real_new:
                    score -= 0.5

        return {'score': max(0, score), 'index': index}

    def _score_new_question(self, text: str, words: List[str], suggestions: List[Dict]) -> Dict:
        """Score: how likely is this a standalone new question?"""
        score = 0.0

        # Has question word at start
        if words and words[0] in self.QUESTION_WORDS:
            score += 0.6

        # Has question word anywhere
        if any(w in self.QUESTION_WORDS for w in words):
            score += 0.3

        # Has real content words (potential new topic)
        content_words = set(words) - self.STOP_WORDS
        if len(content_words) >= 2:
            score += 0.4

        # Contains a noun NOT in suggestions (strong new-topic signal)
        if suggestions:
            all_sug_words = set()
            for sug in suggestions:
                all_sug_words.update(sug['question'].lower().split())
            new_nouns = content_words - all_sug_words
            real_new = [w for w in new_nouns if len(w) > 3]
            if real_new:
                score += 0.5

        # Long input (more likely a full question)
        if len(words) >= 6:
            score += 0.3

        # Can stand alone as a question (has subject)
        if len(content_words) >= 1 and (words[0] in self.QUESTION_WORDS or '?' in text):
            score += 0.3

        # Penalty: very short with no content = probably not a real question
        if len(words) <= 2 and len(content_words) == 0:
            score -= 0.5

        return {'score': max(0, score)}

    def _is_rejection(self, text: str) -> bool:
        """Explicit rejection of suggestions."""
        rejections = {'no', 'nope', 'skip', 'never mind', 'nevermind',
                      'something else', 'forget it', 'nah', 'pass',
                      'no thanks', 'not interested', 'different topic'}
        return text in rejections or any(r in text for r in ['something else', 'never mind', 'forget it'])


# ═══════════════════════════════════════════════════════════════
# SUGGESTION GENERATOR
# ═══════════════════════════════════════════════════════════════

class SuggestionGenerator:
    """Generates smart follow-up suggestions based on topic + depth."""

    def generate(self, topic: str, answer: str, depth: int = 0,
                 topic_history: List[str] = None) -> List[Dict]:
        """Generate 3 suggestions with pre-fetchable questions."""
        suggestions = []
        topic_clean = topic.lower().strip()

        if depth == 0:
            # Level 0: Basic follow-ups
            suggestions = [
                {"question": f"Why is {topic_clean} important?", "type": "why"},
                {"question": f"How does {topic_clean} work?", "type": "how"},
                {"question": f"Tell me more about {topic_clean}", "type": "more"},
            ]
            # If we have history, suggest comparison
            if topic_history and len(topic_history) >= 2:
                prev = topic_history[-2]
                if prev != topic_clean:
                    suggestions[2] = {"question": f"What is the difference between {prev} and {topic_clean}?", "type": "compare"}

        elif depth == 1:
            # Level 1: Deeper
            suggestions = [
                {"question": f"What causes {topic_clean}?", "type": "cause"},
                {"question": f"What are examples of {topic_clean}?", "type": "examples"},
                {"question": f"What is {topic_clean} used for?", "type": "purpose"},
            ]

        elif depth == 2:
            # Level 2: Expert
            suggestions = [
                {"question": f"What are the limitations of {topic_clean}?", "type": "limits"},
                {"question": f"What is the history of {topic_clean}?", "type": "history"},
                {"question": f"What is the future of {topic_clean}?", "type": "future"},
            ]

        elif depth >= 3:
            # Level 3+: Connections
            suggestions = [
                {"question": f"What is related to {topic_clean}?", "type": "related"},
                {"question": f"What is the opposite of {topic_clean}?", "type": "opposite"},
                {"question": f"Summarize everything about {topic_clean}", "type": "summary"},
            ]

        return suggestions


# ═══════════════════════════════════════════════════════════════
# PREDICT ENGINE (ties everything together)
# ═══════════════════════════════════════════════════════════════

class PredictEngine:
    """Full prediction system with DIE + state machine + pre-fetching."""

    def __init__(self, answer_func=None):
        self.state = PredictState()
        self.die = DualInterpretation()
        self.generator = SuggestionGenerator()
        self.answer_func = answer_func  # Function to get answers: f(question) → str

    def after_answer(self, question: str, answer: str) -> List[Dict]:
        """Called after every answer. Generates suggestions and pre-fetches."""
        # Extract topic
        stop = {'what', 'is', 'the', 'a', 'an', 'who', 'where', 'when', 'how', 'why',
                'are', 'was', 'do', 'does', 'tell', 'me', 'about', 'can', 'you'}
        words = [w for w in question.lower().split() if w not in stop and len(w) > 2]
        topic = words[-1] if words else question.split()[-1] if question.split() else ''

        self.state.current_topic = topic
        if topic and (not self.state.topic_history or self.state.topic_history[-1] != topic):
            self.state.topic_history.append(topic)
            if len(self.state.topic_history) > 20:
                self.state.topic_history = self.state.topic_history[-20:]

        self.state.last_answer = answer

        # Generate suggestions
        suggestions = self.generator.generate(
            topic, answer, self.state.drill_depth, self.state.topic_history
        )

        # Pre-fetch answers
        if self.answer_func:
            for sug in suggestions:
                try:
                    sug['answer'] = self.answer_func(sug['question'])
                except:
                    sug['answer'] = None

        self.state.suggestions = suggestions
        self.state.state = PredictState.SUGGESTING
        return suggestions

    def process_input(self, user_input: str) -> Dict:
        """
        Process user input when suggestions are active.
        Returns:
          {"handled": True, "answer": "...", "suggestions": [...]}  → suggestion triggered
          {"handled": False}  → not about suggestions, process normally
        """
        if self.state.state == PredictState.OPEN or not self.state.suggestions:
            return {"handled": False}

        # Run Dual Interpretation Engine
        result = self.die.interpret(user_input, self.state.suggestions)

        if result['action'] == 'accept':
            # Trigger suggestion
            idx = min(result['index'], len(self.state.suggestions) - 1)
            suggestion = self.state.suggestions[idx]
            answer = suggestion.get('answer', '')

            # If no pre-fetched answer, fetch now
            if not answer and self.answer_func:
                try:
                    answer = self.answer_func(suggestion['question'])
                except:
                    answer = f"Let me look into: {suggestion['question']}"

            # Drill deeper
            self.state.drill_depth += 1
            if self.state.drill_depth >= self.state.max_depth:
                self.state.clear()
                next_suggestions = []
            else:
                self.state.state = PredictState.DRILLING
                next_suggestions = self.generator.generate(
                    self.state.current_topic, answer or '',
                    self.state.drill_depth, self.state.topic_history
                )
                # Pre-fetch next level
                if self.answer_func:
                    for sug in next_suggestions:
                        try:
                            sug['answer'] = self.answer_func(sug['question'])
                        except:
                            sug['answer'] = None
                self.state.suggestions = next_suggestions

            return {
                "handled": True,
                "question": suggestion['question'],
                "answer": answer,
                "suggestions": next_suggestions,
                "depth": self.state.drill_depth,
            }

        elif result['action'] == 'reject':
            self.state.clear()
            return {"handled": False}

        elif result['action'] == 'ambiguous':
            # Ask for clarification
            return {
                "handled": True,
                "answer": "Did you mean one of the suggestions above, or are you asking something new?",
                "suggestions": self.state.suggestions,
                "depth": self.state.drill_depth,
            }

        else:  # 'new'
            self.state.clear()
            return {"handled": False}

    def format_suggestions(self, suggestions: List[Dict]) -> str:
        """Format suggestions for display."""
        if not suggestions:
            return ""
        lines = []
        for i, sug in enumerate(suggestions, 1):
            lines.append(f"    {i}. {sug['question']}")
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("PREDICT v3.0 — Dual Interpretation Engine Test")
    print()

    # Mock answer function
    def mock_answer(q):
        return f"[Answer to: {q}]"

    engine = PredictEngine(answer_func=mock_answer)

    # Simulate conversation
    print("Turn 1: User asks about gravity")
    suggestions = engine.after_answer("what is gravity", "Gravity is a fundamental force.")
    print(f"  Suggestions:")
    print(engine.format_suggestions(suggestions))

    print("\nTurn 2: User says 'yes'")
    result = engine.process_input("yes")
    print(f"  Action: {'ACCEPT' if result['handled'] else 'NEW'}")
    if result['handled']:
        print(f"  Triggered: {result['question']}")
        print(f"  Answer: {result['answer']}")
        print(f"  Depth: {result['depth']}")
        print(f"  Next suggestions:")
        print(engine.format_suggestions(result.get('suggestions', [])))

    print("\nTurn 3: User says 'what about photosynthesis'")
    result = engine.process_input("what about photosynthesis")
    print(f"  Action: {'ACCEPT' if result['handled'] else 'NEW (process as new question)'}")

    print("\nTurn 4: After new answer, user says '2'")
    suggestions = engine.after_answer("what is photosynthesis", "Plants convert sunlight.")
    result = engine.process_input("2")
    print(f"  Action: {'ACCEPT' if result['handled'] else 'NEW'}")
    if result['handled']:
        print(f"  Triggered: {result['question']}")

    print("\nTurn 5: User says 'never mind'")
    suggestions = engine.after_answer("test", "test answer")
    result = engine.process_input("never mind")
    print(f"  Action: REJECT (suggestions cleared)")

    # Test edge cases
    print("\n── EDGE CASE TESTS ──")
    engine.state.clear()
    suggestions = engine.after_answer("gravity", "Gravity pulls things down")

    cases = [
        ("yes", "ACCEPT"),
        ("tell me more", "ACCEPT"),
        ("the second one", "ACCEPT"),
        ("what about dogs", "NEW"),
        ("yes but what about mars", "NEW"),
        ("interesting", "ACCEPT"),
        ("cool", "ACCEPT"),
        ("no", "REJECT"),
        ("3", "ACCEPT"),
        ("how does quantum physics work", "NEW"),
    ]
    for inp, expected in cases:
        engine.state.suggestions = suggestions  # Reset
        engine.state.state = PredictState.SUGGESTING
        result = engine.process_input(inp)
        actual = "ACCEPT" if result.get('handled') and result.get('answer') and 'Did you mean' not in str(result.get('answer','')) else "NEW" if not result.get('handled') else "REJECT/AMBIG"
        status = "✓" if expected in actual else "✗"
        print(f"  {status} '{inp}' → {actual} (expected {expected})")
