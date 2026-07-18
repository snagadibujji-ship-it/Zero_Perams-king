"""
AXIMA — Unified Intelligence Engine
Built by: Ghias + Kiro | 2026

ONE entry point for EVERYTHING:
  axima.process("gravity ante enti") → detects Telugu → explains gravity → responds in Telugu
  axima.process("solve x^2+2x+1=0") → detects math → solves → shows steps
  axima.process("compare DNA and RNA") → detects biology → ACES explains → formatted output

Pipeline:
  Input → Multilingual → Router → Math/Physics/ACES/Brain → Response Shaper → Output
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataclasses import dataclass
from typing import Optional
from tracer import get_tracer


@dataclass
class AximaResponse:
    """Unified response from AXIMA."""
    answer: str                  # The main answer text
    language: str = "en"         # Response language
    intent: str = "general"      # What was asked
    source: str = "aces"         # Which engine answered (math/physics/aces/brain)
    confidence: float = 0.8
    topic: str = ""
    mode: str = "deep"           # Explanation mode used
    has_formula: bool = False
    steps: list = None           # Step-by-step if available
    truth: object = None         # TruthLabel — what kind of answer this is


class Axima:
    """The AXIMA Unified Engine. One call does everything."""

    def __init__(self):
        # Multilingual
        from multilingual import MultilingualEngine
        from multilingual.shaper import ResponseShaper
        self.lang_engine = MultilingualEngine()
        self.shaper = ResponseShaper()

        # ACES v2
        from aces_v2.engine import ACESV2
        self.aces = ACESV2()

        # Math (lazy load)
        self._math = None
        # Physics (lazy load)
        self._physics = None
        # Brain (lazy load)
        self._brain = None
        # Inference Engine (lazy load)
        self._inference = None

    def process(self, text: str, mode: str = "deep") -> AximaResponse:
        """Process ANY input in ANY language.
        
        Args:
            text: User input (any language, any format, any mess)
            mode: Explanation mode (one-line/bullets/steps/deep/expert/simple/teach/exam)
            
        Returns:
            AximaResponse with answer in user's language and style
        """
        tracer = get_tracer()

        with tracer.trace(text) as t:
            # Step 1: Detect language + extract intent
            lang_result = self.lang_engine.process(text)
            t.record_detection(
                language=lang_result.language,
                confidence=lang_result.confidence,
                english_query=lang_result.english_query,
                intent=lang_result.intent
            )

            # Step 2: Get English query
            # For English input, use original text (multilingual parser can mangle math/code)
            if lang_result.language == 'en':
                english_q = text
            else:
                english_q = lang_result.english_query or text

            # Step 3: Route to the right engine
            answer, source, steps = self._route_and_solve(english_q, lang_result.intent, mode, t)

            # Step 4: Shape response in user's language/style
            if lang_result.language != 'en' and answer:
                shaped = self.shaper.shape(
                    answer, lang_result.language, lang_result.style,
                    lang_result.intent, lang_result.topic
                )
            else:
                shaped = answer

            # Tag with truth label
            from truth import tag_response
            truth = tag_response(
                shaped, source=source, confidence=lang_result.confidence,
                hops=0, is_template=(source in ('coder', 'web', 'creator'))
            )

            # Record final result in trace
            t.record_result(
                answer=shaped or "",
                status="success" if shaped else "no_answer",
                source=source,
                confidence=lang_result.confidence
            )

        return AximaResponse(
            answer=shaped,
            language=lang_result.language,
            intent=lang_result.intent,
            source=source,
            confidence=lang_result.confidence,
            topic=lang_result.topic,
            mode=mode,
            has_formula='=' in answer if answer else False,
            steps=steps,
            truth=truth,
        )

    def _route_and_solve(self, query: str, intent: str, mode: str, trace=None):
        """Route query to the right engine and get answer."""
        answer = ""
        source = "aces"
        steps = None

        # Try Math first (if it looks like math)
        if intent == 'calculate' or self._looks_like_math(query):
            if trace:
                trace.record_routing(engine="math", reason=f"intent={intent}" if intent == 'calculate' else "regex match")
            result = self._try_math(query)
            if result:
                answer = result
                source = "math"
                return answer, source, steps
            if trace:
                trace.record_fallback("math", "physics", reason="math returned None")

        # Try Physics (if physics terms detected)
        if self._looks_like_physics(query):
            if trace:
                trace.record_routing(engine="physics", reason="physics keywords detected")
            result = self._try_physics(query)
            if result:
                answer = result
                source = "physics"
                return answer, source, steps
            if trace:
                trace.record_fallback("physics", "inference", reason="physics returned None")

        # Try Inference Engine (knowledge base — 4.8M facts)
        if trace:
            trace.record_routing(engine="inference", reason="default knowledge lookup")
        result = self._try_inference(query)
        if result:
            answer = result
            source = "knowledge"
            return answer, source, steps

        # Try Brain (if documents are loaded)
        if self._brain:
            if trace:
                trace.record_fallback("inference", "brain", reason="inference returned None")
            result = self._try_brain(query)
            if result:
                answer = result
                source = "brain"
                return answer, source, steps

        # Default: ACES explanation
        if trace:
            trace.record_fallback("inference", "aces", reason="all engines returned None")
            trace.record_routing(engine="aces", reason="default fallback")
        aces_result = self.aces.explain(query, mode=mode)
        answer = aces_result.text
        source = "aces"

        return answer, source, steps

    def _try_math(self, query: str) -> Optional[str]:
        """Try to solve with math engine."""
        try:
            if self._math is None:
                from prometheus import get_prometheus
                self._math = get_prometheus()
            
            import re
            import math as _math_mod
            expr = query.rstrip('?').strip()
            lower_expr = expr.lower()

            # ─── Special case: constant to N decimal places ───
            const_match = re.match(
                r'(?:what\s+is\s+)?(\w+)\s+to\s+(\d+)\s+decimal\s+places?',
                lower_expr, re.IGNORECASE
            )
            if const_match:
                const_name = const_match.group(1).lower()
                places = int(const_match.group(2))
                constants = {
                    'pi': _math_mod.pi,
                    'e': _math_mod.e,
                    'tau': _math_mod.tau,
                    'phi': (1 + 5**0.5) / 2,
                }
                if const_name in constants:
                    # Truncate to N decimal places (not round)
                    value = constants[const_name]
                    factor = 10 ** places
                    truncated = int(value * factor) / factor
                    return str(truncated)
            
            # Structural rule: strip everything before the math expression
            # Math starts at: a digit, a variable (x,y,z), a function name (sin,sqrt,log), or operator
            match = re.search(r'(\d|[xyz]\s*[+\-*/^=]|sqrt|sin|cos|tan|log|ln|factorial|integrate|derivative|GCD|LCM|\d+\s*mod)', expr, re.IGNORECASE)
            if match:
                # Keep from where math starts
                math_start = match.start()
                # But also keep keyword before it (like "derivative of", "factorial of")
                before = expr[:math_start].lower().strip()
                if before.endswith(' of'):
                    expr = expr[math_start - 3:].strip()  # keep "of X"
                    expr = re.sub(r'^of\s+', '', expr)
                    # Prepend the math keyword
                    keyword_match = re.search(r'(derivative|integral|integrate|factorial|gcd|lcm)', before)
                    if keyword_match:
                        expr = keyword_match.group(1) + ' of ' + expr
                else:
                    expr = expr[math_start:]
            
            # Try expression
            result = self._math.process(expr)
            if result:
                r = str(result).strip()
                first_line = r.split('\n')[0]
                # Validate: must not be just echoing a word, must contain useful content
                if first_line and len(first_line) > 0 and first_line != expr.split()[0]:
                    return r
            
            # Fallback: try full query
            result = self._math.process(query)
            if result:
                r = str(result).strip()
                first_line = r.split('\n')[0]
                if first_line and first_line != query.split()[0]:
                    return r
        except Exception as e:
            tracer = get_tracer()
            if tracer.current:
                tracer.current.record_error("math", type(e).__name__, str(e))
        return None

    def _try_physics(self, query: str) -> Optional[str]:
        """Try to solve with physics engine."""
        try:
            if self._physics is None:
                from prometheus_physics import PhysicsIdentifier
                self._physics = PhysicsIdentifier()
            result = self._physics.identify(query)
            if result:
                if isinstance(result, dict):
                    law = result.get('law', '')
                    formula = result.get('formula', '')
                    explanation = result.get('explanation', '')
                    parts = [p for p in [law, formula, explanation] if p]
                    return '\n'.join(parts) if parts else None
                elif isinstance(result, list) and result:
                    # PhysicsIdentifier returns list of (domain, score)
                    top = result[0] if result else None
                    if top and isinstance(top, tuple):
                        domain, score = top
                        if domain != 'unknown' and score > 0:
                            return f"Domain: {domain} (confidence: {score})"
                    return None
                return str(result) if str(result) != 'None' else None
        except Exception as e:
            tracer = get_tracer()
            if tracer.current:
                tracer.current.record_error("physics", type(e).__name__, str(e))
        return None

    def _try_brain(self, query: str) -> Optional[str]:
        """Try to find answer in BRAIN knowledge base."""
        try:
            results = self._brain.search(query, top_k=1)
            if results:
                return results[0].text
        except Exception as e:
            tracer = get_tracer()
            if tracer.current:
                tracer.current.record_error("brain", type(e).__name__, str(e))
        return None

    def _try_inference(self, query: str) -> Optional[str]:
        """Try inference engine — 4.8M facts with 7 reasoning rules."""
        try:
            if self._inference is None:
                from inference_engine import get_inference_engine
                self._inference = get_inference_engine('src/data')
            result = self._inference.answer(query, max_hops=3)
            if result and result.answer and len(result.answer) > 10:
                # Format nicely
                answer = result.answer
                if result.hops > 1:
                    answer += f"\n\n[Derived through {result.hops}-step reasoning]"
                return answer
        except Exception as e:
            tracer = get_tracer()
            if tracer.current:
                tracer.current.record_error("inference", type(e).__name__, str(e))
        return None

    def _looks_like_math(self, text: str) -> bool:
        """Quick check if input is math."""
        import re
        low = text.lower()
        # Direct arithmetic: "15 * 7", "2^10"
        if re.search(r'\d+\s*[+\-*/^%]\s*\d+', text):
            return True
        # Math keywords
        if re.search(r'\b(solve|calculate|compute|integral|integrate|derivative|factor|simplify)\b', low):
            return True
        # Math functions: sqrt, sin, cos, log, factorial, gcd
        if re.search(r'\b(sqrt|sin|cos|tan|log|ln|factorial|gcd|lcm|mod)\b', low):
            return True
        # "what is X" where X looks numeric/mathematical
        if re.match(r'what\s+is\s+', low):
            after = re.sub(r'^what\s+is\s+(the\s+)?', '', low)
            if re.search(r'\d|[+\-*/^]|sqrt|sin|cos|log|pi|factorial|gcd|derivative|integral', after):
                return True
        # Contains equation markers
        if '=' in text and re.search(r'[xyz]\s*[+\-*/^=]', low):
            return True
        return False

    def _looks_like_physics(self, text: str) -> bool:
        """Quick check if input is physics."""
        import re
        physics_words = r'\b(force|energy|velocity|acceleration|gravity|momentum|wave|quantum|newton|einstein)\b'
        return bool(re.search(physics_words, text.lower()))

    def load_brain(self, text: str, source_name: str = "User Document"):
        """Load a document into BRAIN for Q&A."""
        if self._brain is None:
            from brain_ingest import DocumentBrain
            self._brain = DocumentBrain()
        self._brain.ingest(text, source_name)

    def voices(self):
        """Voice module removed — being rebuilt separately."""
        return []

    def speak(self, text: str, voice: str = 'nova', emotion: str = 'neutral'):
        """Voice module removed — being rebuilt separately."""
        return []

    def create(self, request: str) -> str:
        """Create content: stories, songs, poems, rap, essays.
        
        Examples:
            ax.create("Write a story about a detective")
            ax.create("Write a song about heartbreak")
            ax.create("Write a 1000 word story about time travel")
        """
        from creator.engine_v3 import get_creator_v3
        creator = get_creator_v3()
        return creator.create(request)

    def code(self, request: str):
        """Generate code: algorithms, full projects, explain, debug.
        
        Examples:
            ax.code("binary search in python")
            ax.code("build a todo app with React")
            ax.code("explain: def fib(n)...")
            ax.code("fix: TypeError...")
        
        Returns CodeResult with: kind, code, language, files, explanation
        """
        from coder import get_coder
        return get_coder().code(request)


# Singleton
_instance = None

def get_axima() -> Axima:
    """Get the AXIMA engine singleton."""
    global _instance
    if _instance is None:
        _instance = Axima()
    return _instance
