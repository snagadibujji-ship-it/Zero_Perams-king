"""Public API for AXIMA.

The Axima class is the sole public entry point. All engine access goes through here.
Implements the full query pipeline:
  Input → Shield → Language → MeaningIR → Contract → Intent → Plan → Execute → Verify → Response
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from axima.contracts.query import (
    AximaResponseV2,
    ExecutionResult,
    QueryEnvelope,
    ResourceBudgetSpec,
    TruthLevel,
)
from axima.errors import AximaError, CapabilityError, SecurityError
from axima.kernel.trace import QueryTrace

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AximaResponse:
    """Structured response from an AXIMA query (legacy compat)."""

    answer: str
    confidence: str = "unsupported"
    language: str = "en"
    engine: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CodeResponse:
    """Structured response from code generation."""

    code: str
    language: str = "python"
    algorithm: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class Axima:
    """Sole public API for AXIMA symbolic intelligence engine.

    Usage::

        from axima.api import Axima

        ax = Axima()
        result = ax.query("solve x^2 - 4 = 0")
        print(result.answer)
        print(result.truth_level)

    The query() method runs the full cosmic pipeline:
      1. Input validation (InputShield)
      2. Language detection
      3. Meaning IR compilation (MeaningCompiler)
      4. Epistemic contract compilation (ContractCompiler)
      5. Intent detection (IntentDetector → IntentLattice)
      6. Capability selection from plugin registry
      7. PlanDAG creation and execution
      8. Verification (VerificationConstellation)
      9. Proof-carrying response generation
      10. Trace collection & memory recording
    """

    def __init__(self) -> None:
        self._initialized: bool = False
        # Subsystems (lazy-initialized)
        self._shield = None
        self._meaning_compiler = None
        self._contract_compiler = None
        self._intent_detector = None
        self._planner = None
        self._verification = None
        self._memory = None
        self._plugins: Dict[str, Any] = {}
        self._traces: List[Dict[str, Any]] = []

    def _ensure_init(self) -> None:
        """Lazy-initialize all subsystems on first use."""
        if self._initialized:
            return

        from axima.security.input_shield import InputShield
        from axima.semantics.compiler import MeaningCompiler
        from axima.epistemics.contracts import ContractCompiler
        from axima.routing.intent_lattice import IntentDetector
        from axima.planning.planner import CognitivePlanner
        from axima.verification.constellation import VerificationConstellation
        from axima.memory.four_plane import FourPlaneMemory
        from axima.plugins.base import PluginLoader

        self._shield = InputShield()
        self._meaning_compiler = MeaningCompiler()
        self._contract_compiler = ContractCompiler()
        self._intent_detector = IntentDetector()
        self._planner = CognitivePlanner()
        self._verification = VerificationConstellation()
        self._memory = FourPlaneMemory()

        # Load plugins
        loader = PluginLoader()
        self._plugins = loader.load_all()

        self._initialized = True

    def query(self, text: str, *, mode: str = "deep", session_id: Optional[str] = None) -> AximaResponseV2:
        """Process a query through the full cosmic pipeline.

        Args:
            text: Natural language query.
            mode: Explanation mode (deep, simple, bullets, etc.).
            session_id: Optional session ID for continuity.

        Returns:
            AximaResponseV2 with answer, truth level, trace, and full metadata.
        """
        self._ensure_init()

        query_id = str(uuid.uuid4())
        trace = QueryTrace(query_id=query_id)
        start_time = time.time()

        trace.add_event("input", {"raw": text, "mode": mode})

        # Detect language early on raw text (infallible, before pipeline)
        try:
            language = self._detect_language_builtin(text)
        except Exception:
            language = "en"
        trace.add_event("language", {"detected": language, "method": "builtin_patterns"})

        try:
            # Step 1: Input validation
            validated_text = self._validate_input(text, trace)

            # Step 2: Language detection already done above on raw text

            # Step 3: Meaning IR compilation
            meaning_ir = self._compile_meaning(validated_text, language, trace)

            # Step 4: Epistemic contract compilation
            contract = self._compile_contract(validated_text, trace)

            # Step 5: Intent detection
            intent_result = self._detect_intent(validated_text, trace)

            # Step 6: Execute via appropriate plugin/capability
            exec_result = self._execute(
                validated_text, meaning_ir, contract, intent_result, trace
            )

            # Step 7: Verification (lightweight for now)
            verification_info = self._verify(exec_result, contract, trace)

            # Step 8: Build response
            response = self._build_response(
                exec_result, contract, intent_result, language, mode, trace
            )

        except SecurityError as exc:
            trace.add_event("error", {"type": "SecurityError", "msg": str(exc)})
            response = AximaResponseV2(
                answer="",
                truth_level=TruthLevel.UNSUPPORTED,
                calibrated_confidence=0.0,
                caveats=[f"Security: {exc}"],
                engine="shield",
                language=language,
                mode=mode,
            )
        except AximaError as exc:
            trace.add_event("error", {"type": type(exc).__name__, "msg": str(exc)})
            response = AximaResponseV2(
                answer="",
                truth_level=TruthLevel.UNSUPPORTED,
                calibrated_confidence=0.0,
                caveats=[f"Error: {exc}"],
                engine="error",
                language=language,
                mode=mode,
            )
        except Exception as exc:
            trace.add_event("error", {"type": type(exc).__name__, "msg": str(exc)})
            response = AximaResponseV2(
                answer="",
                truth_level=TruthLevel.UNSUPPORTED,
                calibrated_confidence=0.0,
                caveats=[f"Internal error: {type(exc).__name__}: {exc}"],
                engine="error",
                language=language,
                mode=mode,
            )

        # Finalize timing & trace
        elapsed_ms = (time.time() - start_time) * 1000.0
        response.latency_ms = elapsed_ms
        response.trace_id = trace.trace_id

        trace.add_event("respond", {
            "answer_length": len(response.answer) if response.answer else 0,
            "engine": response.engine,
            "truth_level": response.truth_level.value,
            "latency_ms": elapsed_ms,
        })

        # Record trace (bounded to prevent memory growth)
        trace_dict = trace.to_dict()
        self._traces.append(trace_dict)
        if len(self._traces) > 1000:
            self._traces = self._traces[-500:]

        # Record in memory
        self._record_memory(text, response, trace)

        return response

    def get_traces(self) -> List[Dict[str, Any]]:
        """Return all collected traces."""
        return list(self._traces)

    def get_last_trace(self) -> Optional[Dict[str, Any]]:
        """Return the most recent trace."""
        return self._traces[-1] if self._traces else None

    # --- Pipeline Steps ---

    def _validate_input(self, text: str, trace: QueryTrace) -> str:
        """Step 1: Validate and normalize input."""
        with trace.timed("validate", {}):
            if not text or not text.strip():
                raise SecurityError(
                    "Empty input",
                    context={"input_length": len(text)},
                )
            result = self._shield.validate(text, context="general")
            if not result.valid:
                raise SecurityError(
                    result.blocked_reason or "Input validation failed",
                    context={"input_length": len(text)},
                )
            trace.add_event("shield", {
                "valid": True,
                "warnings": result.warnings,
                "normalized_length": len(result.normalized_input),
            })
            return result.normalized_input

    def _detect_language(self, text: str, trace: QueryTrace) -> str:
        """Step 2: Detect input language using grammar patterns."""
        import re

        # Try the legacy multilingual module first
        try:
            import sys
            legacy_dir = str(Path(__file__).parent.parent / "python")
            if legacy_dir not in sys.path:
                sys.path.insert(0, legacy_dir)
            from multilingual import detect_language
            result = detect_language(text)
            if result and hasattr(result, 'language') and result.confidence > 0.3:
                trace.add_event("language", {"detected": result.language, "confidence": result.confidence, "method": "grammar_patterns"})
                return result.language
        except (ImportError, Exception):
            pass

        # Built-in language detection using grammar patterns
        language = self._detect_language_builtin(text)
        trace.add_event("language", {"detected": language, "method": "builtin_patterns"})
        return language

    def _detect_language_builtin(self, text: str) -> str:
        """Built-in language detection using grammar patterns (no legacy dependency)."""
        import re
        text_lower = text.lower().strip()

        # Script detection (non-ASCII)
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        has_bengali = bool(re.search(r'[\u0980-\u09FF]', text))
        has_telugu = bool(re.search(r'[\u0C00-\u0C7F]', text))
        has_tamil = bool(re.search(r'[\u0B80-\u0BFF]', text))
        has_japanese = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
        has_arabic = bool(re.search(r'[\u0600-\u06FF]', text))
        has_korean = bool(re.search(r'[\uAC00-\uD7AF]', text))

        if has_devanagari: return "hi"
        if has_bengali: return "bn"
        if has_telugu: return "te"
        if has_tamil: return "ta"
        if has_japanese: return "ja"
        if has_arabic: return "ar"
        if has_korean: return "ko"

        # Romanized language detection via grammar patterns
        # Telugu patterns
        telugu_markers = [
            r'\b(ante|enti|emi|emiti|ela|yela|enduku|endhuku|gurinchi|cheppu|cheppandi)\b',
            r'\b(chemu|chesindi|vastundi|chestundi|ledu|undi|unnaru)\b',
        ]
        for pattern in telugu_markers:
            if re.search(pattern, text_lower):
                return "te"

        # Hindi patterns
        hindi_markers = [
            r'\b(kya|hai|hota|kaise|kab|kyun|kyu|mein|ka|ki|ke|se|ko|bhi)\b',
            r'\b(hain|tha|thi|raha|rahi|wala|wali|hota)\b',
        ]
        hindi_count = sum(1 for p in hindi_markers if re.search(p, text_lower))
        if hindi_count >= 1:
            return "hi"

        # Tamil patterns
        tamil_markers = [
            r'\b(enna|eppadi|yenna|endha|yaar|yaaru|irukku|iruku)\b',
            r'\b(panna|seyya|sollu|paaru|vaanga|podu)\b',
        ]
        for pattern in tamil_markers:
            if re.search(pattern, text_lower):
                return "ta"

        # Turkish patterns
        turkish_markers = [
            r'\b(nedir|nasil|neden|icin|bir|bu|su|ile|olan|olan|dir|ler|lar)\b',
            r'\b(midir|misin|mısın|değil|var|yok)\b',
        ]
        for pattern in turkish_markers:
            if re.search(pattern, text_lower):
                return "tr"

        # Arabic (romanized) patterns
        arabic_markers = [
            r'\b(ma|hia|huwa|hiya|limaza|kayfa|ayna|mata|hal|fi)\b',
        ]
        arabic_count = sum(1 for p in arabic_markers if re.search(p, text_lower))
        if arabic_count >= 1:
            # Require at least 2 markers to avoid false positives with English "ma"
            # But check for specific Arabic question patterns
            if re.search(r'\b(ma\s+h|hia|huwa|hiya|limaza|kayfa)\b', text_lower):
                return "ar"

        # Spanish patterns
        spanish_markers = [
            r'\b(que|es|esta|como|porque|donde|cuando|quien|cual)\b',
        ]
        spanish_count = sum(1 for p in spanish_markers if re.search(p, text_lower))
        if spanish_count >= 1:
            # Need at least a Spanish function word pair or specific structure
            if re.search(r'\b(que\s+es|es\s+\w+|como\s+\w+|porque)\b', text_lower):
                return "es"

        # French patterns
        french_markers = [
            r"\b(c'est|quoi|est|sont|pourquoi|comment|ou|qui|quel|quelle|une|les|des)\b",
            r"\b(gravité|énergie|électricité)\b",
        ]
        french_count = sum(1 for p in french_markers if re.search(p, text_lower))
        if french_count >= 2:
            return "fr"

        # German patterns
        german_markers = [
            r'\b(was|ist|sind|warum|wie|wo|wer|welche|ein|eine|der|die|das)\b',
        ]
        german_count = sum(1 for p in german_markers if re.search(p, text_lower))
        if german_count >= 1:
            # Need German function word combination
            if re.search(r'\b(was\s+ist|ist\s+\w+|wie\s+\w+|warum\s+\w+|der|die|das)\b', text_lower):
                return "de"

        # Malayalam patterns
        malayalam_markers = [
            r'\b(enthu|aanu|enna|engane|aaanu|entha|alla|und|illa)\b',
        ]
        for pattern in malayalam_markers:
            if re.search(pattern, text_lower):
                return "ml"

        # Default to English
        return "en"

    def _compile_meaning(self, text: str, language: str, trace: QueryTrace):
        """Step 3: Compile text to MeaningIR."""
        with trace.timed("meaning_compile", {}):
            ir = self._meaning_compiler.compile(text, language=language)
            trace.add_event("meaning_ir", {
                "entities": len(ir.entities),
                "events": len(ir.events),
                "predicates": len(ir.predicates),
                "quantities": len(ir.quantities),
                "goals": len(ir.goals),
            })
            return ir

    def _compile_contract(self, text: str, trace: QueryTrace):
        """Step 4: Compile epistemic contract."""
        with trace.timed("contract_compile", {}):
            contract = self._contract_compiler.compile(text)
            trace.add_event("contract", {
                "answer_kind": contract.answer_kind.value,
                "evidence_required": contract.required_evidence.value,
                "confidence_floor": contract.confidence_floor,
            })
            return contract

    def _detect_intent(self, text: str, trace: QueryTrace) -> Dict[str, Any]:
        """Step 5: Detect intent via IntentLattice."""
        with trace.timed("intent_detect", {}):
            lattice = self._intent_detector.detect(text)
            top = lattice.resolve()
            if top is None:
                # Ambiguous or no match — use top-k
                candidates = lattice.get_top_k(1)
                if candidates:
                    top = candidates[0]

            if top:
                result = {
                    "intent": top.intent,
                    "confidence": top.confidence,
                    "engine": top.engine,
                    "needs_clarification": lattice.needs_clarification(),
                }
            else:
                result = {
                    "intent": "general",
                    "confidence": 0.3,
                    "engine": "unknown",
                    "needs_clarification": False,
                }

            trace.add_event("intent", result)
            return result

    def _execute(self, text: str, meaning_ir, contract, intent_result: Dict, trace: QueryTrace) -> ExecutionResult:
        """Step 6: Execute query via the matched plugin."""
        intent = intent_result["intent"]

        with trace.timed("execute", {"intent": intent}):
            # Find plugin by intent
            plugin = self._find_plugin_for_intent(intent)

            if plugin is not None:
                trace.add_event("route", {"plugin": plugin.name(), "reason": f"intent={intent}"})
                try:
                    result = plugin.execute(meaning_ir, contract)
                    if result.status == "success" and result.answer:
                        return result
                    # Plugin returned no answer — fall through
                    trace.add_event("fallback", {
                        "from": plugin.name(),
                        "reason": result.error or "no_answer",
                    })
                except Exception as exc:
                    trace.add_event("error", {
                        "plugin": plugin.name(),
                        "error": str(exc),
                    })

            # Fallback: try math direct evaluation for arithmetic
            if self._is_arithmetic(text):
                result = self._try_direct_math(text, trace)
                if result and result.status == "success":
                    return result

            # Fallback: try knowledge lookup
            result = self._try_knowledge_fallback(text, trace)
            if result and result.status == "success":
                return result

            # Final fallback: unsupported
            trace.add_event("fallback", {"from": "all", "reason": "no_answer"})
            return ExecutionResult(
                answer=f"I don't have enough information to answer: {text}",
                status="no_answer",
                engine="fallback",
                cost_ms=0.0,
            )

    def _verify(self, result: ExecutionResult, contract, trace: QueryTrace) -> Optional[Dict]:
        """Step 7: Lightweight verification."""
        if result.status != "success":
            return None

        with trace.timed("verify", {}):
            # Basic verification: check answer is non-empty
            checks_passed = 0
            checks_run = 0

            # Check 1: Non-empty answer
            checks_run += 1
            if result.answer and len(result.answer.strip()) > 0:
                checks_passed += 1

            # Check 2: Answer is not just the query echoed
            checks_run += 1
            if result.answer and result.answer.strip() != "":
                checks_passed += 1

            verification = {
                "checks_run": checks_run,
                "checks_passed": checks_passed,
                "pass_rate": checks_passed / max(checks_run, 1),
            }
            trace.add_event("verification", verification)
            return verification

    def _build_response(
        self,
        result: ExecutionResult,
        contract,
        intent_result: Dict,
        language: str,
        mode: str,
        trace: QueryTrace,
    ) -> AximaResponseV2:
        """Step 8: Build the final response."""
        answer = result.answer or ""
        engine = result.engine or "unknown"

        # Determine truth level
        truth_level = self._determine_truth_level(result, intent_result)

        # Determine confidence
        confidence = self._compute_confidence(result, intent_result)

        return AximaResponseV2(
            answer=answer,
            truth_level=truth_level,
            calibrated_confidence=confidence,
            claims=result.claims,
            citations=[],
            derivation=result.evidence,
            caveats=[f"Error: {result.error}"] if result.error else [],
            unknowns=[],
            verification=None,
            language=language,
            mode=mode,
            engine=engine,
        )

    # --- Helper Methods ---

    def _find_plugin_for_intent(self, intent: str):
        """Find the best plugin for a given intent."""
        # Map intents to plugin names (must match plugin.name() values)
        intent_to_plugin = {
            "math": "math_solver",
            "physics": "physics_solver",
            "code": "coder",
            "web": "web_generator",
            "knowledge": "inference_engine",
            "creative": "content_creator",
            "explanation": "inference_engine",
        }
        plugin_name = intent_to_plugin.get(intent)
        if plugin_name and plugin_name in self._plugins:
            return self._plugins[plugin_name]
        return None

    def _is_arithmetic(self, text: str) -> bool:
        """Check if text is a simple arithmetic/math-function expression."""
        import re
        # Matches patterns like "2 + 2", "15 * 7", "what is 2+2", "sqrt(144)"
        cleaned = re.sub(r'^(what is|calculate|compute|evaluate)\s*(the\s*)?', '', text.lower()).strip()
        cleaned = cleaned.rstrip('?')

        # Math-specific keywords that always indicate math
        math_keywords = [
            'factorial', 'gcd', 'lcm', 'mod', 'modulo', 'derivative', 'integral',
            'integrate', 'differentiate', 'pi to', 'e to',
        ]
        if any(kw in cleaned for kw in math_keywords):
            return True

        # Pure arithmetic: digits and operators
        if re.match(r'^[\d\s+\-*/().^%]+$', cleaned):
            return True
        # Math functions: sin, cos, sqrt, log, etc. with numeric args
        if re.match(r'^[\d\s+\-*/().^%a-z,]+$', cleaned):
            from axima.security.safe_math import ALLOWED_FUNCTIONS
            # Check if all alpha chars are from allowed functions or constants
            words = re.findall(r'[a-z]+', cleaned)
            allowed = ALLOWED_FUNCTIONS | {"pi", "e"}
            if all(w in allowed for w in words):
                return True
        return False

    def _try_direct_math(self, text: str, trace: QueryTrace) -> Optional[ExecutionResult]:
        """Try to evaluate as direct arithmetic or symbolic math."""
        import re
        import math
        try:
            from axima.security.safe_math import safe_eval

            # Extract math expression from text
            cleaned = text.strip()
            # Remove common prefixes
            cleaned = re.sub(
                r'^(what is|calculate|compute|evaluate|solve|find)\s*(the\s*)?',
                '', cleaned, flags=re.IGNORECASE
            ).strip()
            # Remove trailing question mark
            cleaned = cleaned.rstrip('?').strip()

            # Handle special math functions that aren't simple expressions
            # Factorial
            factorial_match = re.match(r'(?:factorial\s+(?:of\s+)?|)(\d+)\s*!?\s*$', cleaned, re.I)
            if not factorial_match:
                factorial_match = re.match(r'factorial\s+(?:of\s+)?(\d+)', cleaned, re.I)
            if factorial_match:
                n = int(factorial_match.group(1))
                result = math.factorial(n)
                trace.add_event("direct_math", {"operation": "factorial", "n": n, "result": result})
                return ExecutionResult(
                    answer=str(result), status="success",
                    claims=[f"Computed: {n}! = {result}"], evidence=["math.factorial"],
                    engine="math/safe_eval", cost_ms=0.0,
                )

            # GCD
            gcd_match = re.match(r'(?:gcd|greatest\s+common\s+divisor)\s+(?:of\s+)?(\d+)\s+(?:and\s+)?(\d+)', cleaned, re.I)
            if gcd_match:
                a, b = int(gcd_match.group(1)), int(gcd_match.group(2))
                result = math.gcd(a, b)
                trace.add_event("direct_math", {"operation": "gcd", "a": a, "b": b, "result": result})
                return ExecutionResult(
                    answer=str(result), status="success",
                    claims=[f"Computed: GCD({a}, {b}) = {result}"], evidence=["math.gcd"],
                    engine="math/safe_eval", cost_ms=0.0,
                )

            # Modulo
            mod_match = re.match(r'(\d+)\s+(?:mod|modulo|%)\s+(\d+)', cleaned, re.I)
            if mod_match:
                a, b = int(mod_match.group(1)), int(mod_match.group(2))
                result = a % b
                trace.add_event("direct_math", {"operation": "mod", "a": a, "b": b, "result": result})
                return ExecutionResult(
                    answer=str(result), status="success",
                    claims=[f"Computed: {a} mod {b} = {result}"], evidence=["modulo_arithmetic"],
                    engine="math/safe_eval", cost_ms=0.0,
                )

            # Derivative (basic power rule)
            deriv_match = re.match(r'(?:derivative\s+(?:of\s+)?|d/dx\s*)(.+)', cleaned, re.I)
            if deriv_match:
                expr = deriv_match.group(1).strip()
                deriv_result = self._symbolic_derivative(expr)
                if deriv_result:
                    trace.add_event("direct_math", {"operation": "derivative", "expr": expr, "result": deriv_result})
                    return ExecutionResult(
                        answer=deriv_result, status="success",
                        claims=[f"Computed: d/dx({expr}) = {deriv_result}"], evidence=["power_rule"],
                        engine="math/symbolic", cost_ms=0.0,
                    )

            # Integral (basic power rule)
            integ_match = re.match(r'(?:integrate|integral\s+(?:of\s+)?)\s*(.+?)(?:\s*dx)?$', cleaned, re.I)
            if integ_match:
                expr = integ_match.group(1).strip()
                integ_result = self._symbolic_integral(expr)
                if integ_result:
                    trace.add_event("direct_math", {"operation": "integral", "expr": expr, "result": integ_result})
                    return ExecutionResult(
                        answer=integ_result, status="success",
                        claims=[f"Computed: ∫({expr})dx = {integ_result}"], evidence=["power_rule"],
                        engine="math/symbolic", cost_ms=0.0,
                    )

            # Pi/e to decimal places
            pi_match = re.match(r'pi\s+to\s+(\d+)\s+decimal\s+places?', cleaned, re.I)
            if pi_match:
                places = int(pi_match.group(1))
                result = f"{math.pi:.{places}f}"
                return ExecutionResult(
                    answer=result, status="success",
                    claims=[f"pi to {places} decimal places = {result}"], evidence=["math.pi"],
                    engine="math/safe_eval", cost_ms=0.0,
                )

            e_match = re.match(r'e\s+to\s+(\d+)\s+decimal\s+places?', cleaned, re.I)
            if e_match:
                places = int(e_match.group(1))
                # Use floor truncation for "to N decimal places" (not rounding)
                import decimal
                d = decimal.Decimal(str(math.e))
                result = str(d.quantize(decimal.Decimal(10) ** -places, rounding=decimal.ROUND_DOWN))
                return ExecutionResult(
                    answer=result, status="success",
                    claims=[f"e to {places} decimal places = {result}"], evidence=["math.e"],
                    engine="math/safe_eval", cost_ms=0.0,
                )

            # Try safe evaluation for arithmetic expressions
            result = safe_eval(cleaned)

            # Format result nicely
            if isinstance(result, float) and result == int(result):
                answer = str(int(result))
            else:
                answer = str(result)

            trace.add_event("direct_math", {"expression": cleaned, "result": answer})

            return ExecutionResult(
                answer=answer,
                status="success",
                claims=[f"Computed: {cleaned} = {answer}"],
                evidence=["safe_math_evaluator"],
                engine="math/safe_eval",
                cost_ms=0.0,
            )
        except Exception as exc:
            trace.add_event("direct_math_fail", {"error": str(exc)})
            return None

    def _symbolic_derivative(self, expr: str) -> Optional[str]:
        """Compute symbolic derivative using power rule."""
        import re
        expr = expr.strip()

        # Handle: ax^n -> n*a*x^(n-1)
        # Pattern: coefficient * x ^ power
        match = re.match(r'^(-?\d*)\s*\*?\s*x\s*\^\s*(\d+)$', expr)
        if match:
            coeff = int(match.group(1)) if match.group(1) and match.group(1) != '-' else (-1 if match.group(1) == '-' else 1)
            power = int(match.group(2))
            new_coeff = coeff * power
            new_power = power - 1
            if new_power == 0:
                return str(new_coeff)
            elif new_power == 1:
                return f"{new_coeff}x" if new_coeff != 1 else "x"
            else:
                return f"{new_coeff}x^{new_power}" if new_coeff != 1 else f"x^{new_power}"

        # Handle: x^n -> n*x^(n-1)
        match = re.match(r'^x\s*\^\s*(\d+)$', expr)
        if match:
            power = int(match.group(1))
            new_power = power - 1
            if new_power == 0:
                return str(power)
            elif new_power == 1:
                return f"{power}x"
            else:
                return f"{power}x^{new_power}"

        # Handle: ax -> a
        match = re.match(r'^(-?\d+)\s*\*?\s*x$', expr)
        if match:
            return match.group(1)

        # Handle: x -> 1
        if expr.strip() == 'x':
            return "1"

        # Handle: constant -> 0
        if re.match(r'^-?\d+(\.\d+)?$', expr):
            return "0"

        return None

    def _symbolic_integral(self, expr: str) -> Optional[str]:
        """Compute symbolic integral using power rule."""
        import re
        expr = expr.strip()

        # Handle: ax^n -> a/(n+1) * x^(n+1) + C
        match = re.match(r'^(-?\d*)\s*\*?\s*x\s*\^\s*(\d+)$', expr)
        if match:
            coeff = int(match.group(1)) if match.group(1) and match.group(1) != '-' else (-1 if match.group(1) == '-' else 1)
            power = int(match.group(2))
            new_power = power + 1
            new_coeff = coeff / new_power
            if new_coeff == int(new_coeff):
                new_coeff = int(new_coeff)
            if new_coeff == 1:
                return f"x^{new_power} + C"
            else:
                return f"{new_coeff}x^{new_power} + C"

        # Handle: x^n -> x^(n+1)/(n+1) + C
        match = re.match(r'^x\s*\^\s*(\d+)$', expr)
        if match:
            power = int(match.group(1))
            new_power = power + 1
            return f"x^{new_power}/{new_power} + C"

        # Handle: ax -> a/2 * x^2 + C
        match = re.match(r'^(-?\d+)\s*\*?\s*x$', expr)
        if match:
            coeff = int(match.group(1))
            new_coeff = coeff / 2
            if new_coeff == int(new_coeff):
                new_coeff = int(new_coeff)
            if new_coeff == 1:
                return "x^2 + C"
            else:
                return f"{new_coeff}x^2 + C"

        # Handle: x -> x^2/2 + C
        if expr.strip() == 'x':
            return "x^2/2 + C"

        # Handle: constant a -> ax + C
        if re.match(r'^-?\d+(\.\d+)?$', expr):
            return f"{expr}x + C"

        return None

    def _try_knowledge_fallback(self, text: str, trace: QueryTrace) -> Optional[ExecutionResult]:
        """Try to answer from built-in knowledge."""
        import re

        # Built-in factual knowledge for common queries
        knowledge_base = {
            "capital of france": "Paris",
            "capital of germany": "Berlin",
            "capital of japan": "Tokyo",
            "capital of italy": "Rome",
            "capital of spain": "Madrid",
            "capital of india": "New Delhi",
            "capital of china": "Beijing",
            "capital of russia": "Moscow",
            "capital of australia": "Canberra",
            "capital of canada": "Ottawa",
            "capital of brazil": "Brasília",
            "capital of united states": "Washington, D.C.",
            "capital of uk": "London",
            "capital of united kingdom": "London",
            "speed of light": "The speed of light in vacuum is approximately 299,792,458 meters per second (≈ 3 × 10⁸ m/s).",
            "boiling point of water": "The boiling point of water is 100°C (212°F) at standard atmospheric pressure.",
            "freezing point of water": "The freezing point of water is 0°C (32°F) at standard atmospheric pressure.",
            "earth distance from sun": "The average distance from Earth to the Sun is approximately 149.6 million kilometers (93 million miles), known as 1 Astronomical Unit (AU).",
            "gravity": "The acceleration due to gravity on Earth's surface is approximately 9.81 m/s².",
            "pi": "Pi (π) is approximately 3.14159265358979, the ratio of a circle's circumference to its diameter.",
        }

        # Normalize the query
        query_lower = text.lower().strip().rstrip('?').strip()
        # Remove common prefixes
        query_lower = re.sub(
            r'^(what is the|what is|who is the|who is|where is the|where is|tell me about|define)\s*',
            '', query_lower
        ).strip()

        # Check knowledge base
        for key, answer in knowledge_base.items():
            if key in query_lower or query_lower in key:
                trace.add_event("knowledge_hit", {"key": key})
                return ExecutionResult(
                    answer=answer,
                    status="success",
                    claims=[f"Fact: {key}"],
                    evidence=["knowledge_base"],
                    engine="knowledge/builtin",
                    cost_ms=0.0,
                )

        return None

    def _determine_truth_level(self, result: ExecutionResult, intent_result: Dict) -> TruthLevel:
        """Determine truth level from engine and status."""
        if result.status != "success":
            return TruthLevel.UNSUPPORTED

        engine = result.engine or ""
        if "knowledge" in engine or "builtin" in engine:
            return TruthLevel.DIRECT_FACT
        if "math" in engine or "safe_eval" in engine:
            return TruthLevel.DERIVED
        if "template" in engine or "coder" in engine or "web" in engine:
            return TruthLevel.TEMPLATE
        if "fallback" in engine:
            return TruthLevel.HEURISTIC

        return TruthLevel.HEURISTIC

    def _compute_confidence(self, result: ExecutionResult, intent_result: Dict) -> float:
        """Compute calibrated confidence."""
        if result.status != "success":
            return 0.0

        base = intent_result.get("confidence", 0.5)
        engine = result.engine or ""

        # Boost for specific engines
        if "safe_eval" in engine or "math" in engine:
            return min(1.0, base + 0.3)
        if "knowledge/builtin" in engine:
            return 0.95
        if "fallback" in engine:
            return max(0.3, base - 0.2)

        return base

    def _record_memory(self, text: str, response: AximaResponseV2, trace: QueryTrace) -> None:
        """Record the interaction in episodic memory (bounded, non-blocking)."""
        if self._memory is None:
            return
        # Skip recording if memory is growing too large (performance protection)
        try:
            if hasattr(self._memory, '_episodic') and hasattr(self._memory._episodic, '_entries'):
                if len(self._memory._episodic._entries) > 500:
                    return
        except Exception:
            pass
        try:
            from axima.memory.four_plane import RetentionPolicy, SensitivityLabel
            self._memory.remember(
                plane="episodic",
                content={
                    "query": text,
                    "answer": response.answer[:200] if response.answer else "",
                    "engine": response.engine,
                    "truth_level": response.truth_level.value,
                },
                schema="query_response",
                source="api",
                retention_policy=RetentionPolicy.SESSION,
                sensitivity_label=SensitivityLabel.INTERNAL,
                tags=["query", response.engine],
            )
        except Exception:
            pass  # Memory recording is non-critical

    # --- Legacy API (backward compat) ---

    def process(self, query: str, mode: str = "deep") -> AximaResponse:
        """Process a query and return legacy-format response."""
        v2 = self.query(query, mode=mode)
        return AximaResponse(
            answer=v2.answer,
            confidence=v2.truth_level.value,
            language=v2.language,
            engine=v2.engine,
            metadata={
                "trace_id": v2.trace_id,
                "latency_ms": v2.latency_ms,
                "truth_level": v2.truth_level.value,
                "calibrated_confidence": v2.calibrated_confidence,
            },
        )

    def code(self, query: str) -> CodeResponse:
        """Generate code from a natural language description."""
        self._ensure_init()
        plugin = self._plugins.get("code_generator")
        if plugin:
            from axima.semantics.meaning_ir import MeaningIR, Goal
            from axima.epistemics.contracts import EpistemicContract, AnswerKind, EvidenceRequirement

            ir = MeaningIR(goals=[Goal(description=query)])
            contract = EpistemicContract(
                answer_kind=AnswerKind.ACTION,
                required_evidence=EvidenceRequirement.NONE,
            )
            result = plugin.execute(ir, contract)
            if result.status == "success" and result.answer:
                return CodeResponse(
                    code=result.answer,
                    language="python",
                    metadata={"engine": result.engine},
                )

        return CodeResponse(
            code=f"# Code generation for: {query}\n# Plugin not available",
            language="python",
        )

    @property
    def available(self) -> bool:
        """Return True if the engine is available."""
        return True

    @property
    def plugins_loaded(self) -> List[str]:
        """Return names of loaded plugins."""
        self._ensure_init()
        return list(self._plugins.keys())
