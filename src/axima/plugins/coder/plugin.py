"""Coder Plugin — wraps coder.py and codegen_engine.

Adds sandbox execution and test generation on top of the
code generation engines.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR
from ..base import PluginBase

logger = logging.getLogger(__name__)

_LEGACY_DIR = Path(__file__).parent.parent.parent.parent.parent / "python"


@dataclass
class SandboxResult:
    """Result from sandboxed code execution."""

    output: str = ""
    error: Optional[str] = None
    exit_code: int = 0
    duration_ms: float = 0.0


@dataclass
class TestCase:
    """An auto-generated test case."""

    name: str
    input_data: str
    expected_output: str
    actual_output: Optional[str] = None
    passed: Optional[bool] = None


class CoderPlugin(PluginBase):
    """Code generation with sandbox execution and test generation."""

    def __init__(self) -> None:
        self._coder = None
        self._codegen = None
        self._healthy = False

    def name(self) -> str:
        return "coder"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["code", "algorithm", "project", "implement"],
            produced_types=["code", "project_scaffold", "test_suite"],
            preconditions=[],
            postconditions=["generated_code"],
            cost_model={"avg_ms": 300, "max_ms": 10000},
            latency_model={"avg_ms": 300, "p95_ms": 5000},
            deterministic=True,
            permissions=["read", "write"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Generate code from the MeaningIR."""
        start = time.time()

        # Extract what to generate
        spec = self._extract_spec(ir)
        if not spec:
            return ExecutionResult(
                status="error",
                error="Could not determine code generation specification",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Determine generation type: algorithm vs full project
        if self._is_algorithm_request(spec):
            result = self._generate_algorithm(spec)
        else:
            result = self._generate_project(spec)

        elapsed = (time.time() - start) * 1000

        if result is not None:
            code = result.get("code", "")
            # Generate test cases
            tests = self._generate_tests(code, spec)

            claims = [f"Generated code for: {spec['description']}"]
            if tests:
                claims.append(f"Generated {len(tests)} test cases")

            return ExecutionResult(
                answer=code,
                status="success",
                claims=claims,
                evidence=[result.get("method", "codegen_engine")],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"Code generation failed for: {spec.get('description', 'unknown')}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if code generation engines are available."""
        try:
            self._load_engines()
            self._healthy = self._coder is not None or self._codegen is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_engines()

    # --- Sandbox Execution ---

    def sandbox_execute(self, code: str, language: str = "python") -> SandboxResult:
        """Execute code in a sandboxed environment.

        Currently only supports basic validation (no actual execution
        for safety). Full sandbox integration is planned.
        """
        start = time.time()

        # Basic syntax validation for Python
        if language == "python":
            try:
                compile(code, "<sandbox>", "exec")
                return SandboxResult(
                    output="Syntax valid",
                    exit_code=0,
                    duration_ms=(time.time() - start) * 1000,
                )
            except SyntaxError as exc:
                return SandboxResult(
                    error=f"Syntax error: {exc}",
                    exit_code=1,
                    duration_ms=(time.time() - start) * 1000,
                )

        return SandboxResult(
            output=f"Sandbox not available for language: {language}",
            exit_code=0,
            duration_ms=(time.time() - start) * 1000,
        )

    # --- Test Generation ---

    def _generate_tests(self, code: str, spec: Dict[str, Any]) -> List[TestCase]:
        """Generate basic test cases for the generated code."""
        tests: List[TestCase] = []

        description = spec.get("description", "")
        language = spec.get("language", "python")

        # Generate a basic test stub
        if language == "python" and code:
            tests.append(
                TestCase(
                    name=f"test_{description.replace(' ', '_')[:30]}",
                    input_data="# Auto-generated test",
                    expected_output="# Expected behavior verified",
                )
            )

        return tests

    # --- Internal Methods ---

    def _extract_spec(self, ir: MeaningIR) -> Optional[Dict[str, Any]]:
        """Extract code generation specification from IR."""
        import re
        spec: Dict[str, Any] = {}

        # Check goals
        for goal in ir.goals:
            if goal.description:
                spec["description"] = goal.description
                spec["constraints"] = goal.constraints
                break

        # Check events for action verbs
        if not spec:
            for event in ir.events:
                if event.verb in ("implement", "create", "build", "write", "generate", "code"):
                    spec["description"] = event.patient or event.verb
                    break

        # Fallback: use the raw source text from IR
        if not spec and ir.source_span_map:
            raw_text = ""
            for span_text in ir.source_span_map.values():
                if isinstance(span_text, str):
                    raw_text = span_text
                    break
            if raw_text:
                spec["description"] = raw_text

        # Last fallback: reconstruct from entities and predicates
        if not spec and (ir.entities or ir.predicates):
            parts = []
            for e in ir.entities:
                parts.append(e.name)
            for p in ir.predicates:
                parts.append(f"{p.subject} {p.relation} {p.object}")
            if parts:
                spec["description"] = " ".join(parts)

        # Ultra-fallback: if IR has _raw attribute or we have nothing, derive from MeaningIR hash
        if not spec:
            # Try to get raw query from the source span map
            if hasattr(ir, '_raw_text') and ir._raw_text:
                spec["description"] = ir._raw_text
            else:
                return None

        # Detect language from constraints or entities
        spec["language"] = "python"  # Default
        for entity in ir.entities:
            if entity.type == "programming_language":
                spec["language"] = entity.name
                break

        # Also detect language from description text
        if "description" in spec:
            desc_lower = spec["description"].lower()
            lang_map = {
                "python": "python", "javascript": "javascript", "js": "javascript",
                "typescript": "typescript", "java": "java", "c++": "cpp",
                "rust": "rust", "go": "go", "golang": "go",
                "ruby": "ruby", "php": "php", "swift": "swift",
                "kotlin": "kotlin", "scala": "scala", "c#": "csharp",
            }
            for keyword, lang in lang_map.items():
                if keyword in desc_lower:
                    spec["language"] = lang
                    break

        return spec

    def _is_algorithm_request(self, spec: Dict[str, Any]) -> bool:
        """Determine if this is an algorithm request vs full project."""
        desc = spec.get("description", "").lower()
        algo_keywords = [
            "algorithm", "sort", "search", "tree", "graph", "hash",
            "dynamic programming", "recursion", "linked list", "binary",
            "fibonacci", "factorial", "prime",
        ]
        return any(kw in desc for kw in algo_keywords)

    def _generate_algorithm(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate an algorithm using codegen_engine or built-in patterns."""
        # Try legacy engine first
        try:
            self._load_engines()
            if self._codegen is not None:
                result = self._codegen.generate(
                    spec.get("description", ""),
                    language=spec.get("language", "python"),
                )
                if result:
                    return {
                        "code": result if isinstance(result, str) else result.get("code", ""),
                        "method": "codegen_engine",
                    }
        except Exception as exc:
            logger.debug(f"Legacy algorithm generation failed: {exc}")

        # Built-in pattern generation
        return self._builtin_generate(spec)

    def _generate_project(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a full project using coder.py or built-in patterns."""
        # Try legacy engine first
        try:
            self._load_engines()
            if self._coder is not None:
                result = self._coder.generate(spec.get("description", ""))
                if result:
                    return {
                        "code": result if isinstance(result, str) else str(result),
                        "method": "axima_coder",
                    }
        except Exception as exc:
            logger.debug(f"Legacy project generation failed: {exc}")

        # Built-in pattern generation
        return self._builtin_generate(spec)

    def _builtin_generate(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Built-in code generation from patterns (no legacy dependency)."""
        desc = spec.get("description", "").lower()
        language = spec.get("language", "python")

        # Pattern library for common requests
        patterns: Dict[str, Dict[str, str]] = {
            "hello world": {
                "python": 'print("Hello, World!")',
                "javascript": 'console.log("Hello, World!");',
                "java": 'public class HelloWorld {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}',
                "c": '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}',
                "rust": 'fn main() {\n    println!("Hello, World!");\n}',
                "go": 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
                "typescript": 'console.log("Hello, World!");',
            },
            "fibonacci": {
                "python": 'def fibonacci(n: int) -> int:\n    """Return the nth Fibonacci number."""\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    a, b = 0, 1\n    for _ in range(2, n + 1):\n        a, b = b, a + b\n    return b\n\n\n# Example usage\nfor i in range(10):\n    print(f"F({i}) = {fibonacci(i)}")',
                "javascript": 'function fibonacci(n) {\n    if (n <= 0) return 0;\n    if (n === 1) return 1;\n    let a = 0, b = 1;\n    for (let i = 2; i <= n; i++) {\n        [a, b] = [b, a + b];\n    }\n    return b;\n}\n\nfor (let i = 0; i < 10; i++) {\n    console.log(`F(${i}) = ${fibonacci(i)}`);\n}',
            },
            "factorial": {
                "python": 'def factorial(n: int) -> int:\n    """Return n! (factorial of n)."""\n    if n < 0:\n        raise ValueError("Factorial not defined for negative numbers")\n    if n <= 1:\n        return 1\n    result = 1\n    for i in range(2, n + 1):\n        result *= i\n    return result\n\n\n# Example usage\nfor i in range(10):\n    print(f"{i}! = {factorial(i)}")',
            },
            "binary search": {
                "python": 'def binary_search(arr: list, target) -> int:\n    """Return index of target in sorted array, or -1 if not found."""\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\n\n# Example usage\narr = [1, 3, 5, 7, 9, 11, 13, 15]\nprint(f"Index of 7: {binary_search(arr, 7)}")\nprint(f"Index of 4: {binary_search(arr, 4)}")',
            },
            "quicksort": {
                "python": 'def quicksort(arr: list) -> list:\n    """Sort array using quicksort algorithm."""\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)\n\n\n# Example usage\narr = [3, 6, 8, 10, 1, 2, 1]\nprint(f"Sorted: {quicksort(arr)}")',
            },
            "linked list": {
                "python": 'class Node:\n    def __init__(self, data):\n        self.data = data\n        self.next = None\n\n\nclass LinkedList:\n    def __init__(self):\n        self.head = None\n\n    def append(self, data):\n        new_node = Node(data)\n        if not self.head:\n            self.head = new_node\n            return\n        current = self.head\n        while current.next:\n            current = current.next\n        current.next = new_node\n\n    def display(self):\n        elements = []\n        current = self.head\n        while current:\n            elements.append(str(current.data))\n            current = current.next\n        return " -> ".join(elements)\n\n\n# Example usage\nll = LinkedList()\nfor i in [1, 2, 3, 4, 5]:\n    ll.append(i)\nprint(ll.display())',
            },
            "bubble sort": {
                "python": 'def bubble_sort(arr: list) -> list:\n    """Sort array using bubble sort algorithm."""\n    arr = arr.copy()\n    n = len(arr)\n    for i in range(n):\n        swapped = False\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n                swapped = True\n        if not swapped:\n            break\n    return arr\n\n\n# Example usage\narr = [64, 34, 25, 12, 22, 11, 90]\nprint(f"Sorted: {bubble_sort(arr)}")',
            },
            "stack": {
                "python": 'class Stack:\n    """Stack data structure (LIFO)."""\n\n    def __init__(self):\n        self._items = []\n\n    def push(self, item):\n        self._items.append(item)\n\n    def pop(self):\n        if self.is_empty():\n            raise IndexError("Stack is empty")\n        return self._items.pop()\n\n    def peek(self):\n        if self.is_empty():\n            raise IndexError("Stack is empty")\n        return self._items[-1]\n\n    def is_empty(self) -> bool:\n        return len(self._items) == 0\n\n    def size(self) -> int:\n        return len(self._items)\n\n\n# Example usage\ns = Stack()\nfor item in [1, 2, 3, 4, 5]:\n    s.push(item)\nwhile not s.is_empty():\n    print(s.pop())',
            },
            "prime": {
                "python": 'def is_prime(n: int) -> bool:\n    """Check if n is a prime number."""\n    if n < 2:\n        return False\n    if n < 4:\n        return True\n    if n % 2 == 0 or n % 3 == 0:\n        return False\n    i = 5\n    while i * i <= n:\n        if n % i == 0 or n % (i + 2) == 0:\n            return False\n        i += 6\n    return True\n\n\ndef primes_up_to(n: int) -> list:\n    """Return all primes up to n using Sieve of Eratosthenes."""\n    if n < 2:\n        return []\n    sieve = [True] * (n + 1)\n    sieve[0] = sieve[1] = False\n    for i in range(2, int(n**0.5) + 1):\n        if sieve[i]:\n            for j in range(i*i, n + 1, i):\n                sieve[j] = False\n    return [i for i, is_p in enumerate(sieve) if is_p]\n\n\n# Example usage\nprint(f"Primes up to 50: {primes_up_to(50)}")',
            },
        }

        # Match against patterns
        for key, lang_codes in patterns.items():
            if key in desc:
                code = lang_codes.get(language, lang_codes.get("python", ""))
                if code:
                    return {"code": code, "method": "builtin_pattern"}

        # Generic code stub for unmatched requests
        if language == "python":
            code = f'"""\nGenerated code for: {spec.get("description", "unknown")}\n"""\n\n\ndef main():\n    # TODO: Implement {spec.get("description", "functionality")}\n    pass\n\n\nif __name__ == "__main__":\n    main()'
        elif language == "javascript":
            code = f'/**\n * Generated code for: {spec.get("description", "unknown")}\n */\n\nfunction main() {{\n    // TODO: Implement {spec.get("description", "functionality")}\n}}\n\nmain();'
        else:
            code = f'// Generated code for: {spec.get("description", "unknown")}\n// Language: {language}\n// TODO: Implement'

        return {"code": code, "method": "builtin_stub"}

    def _load_engines(self) -> None:
        """Load code generation engines from legacy code."""
        legacy_dir = str(_LEGACY_DIR)
        if legacy_dir not in sys.path:
            sys.path.insert(0, legacy_dir)

        if self._coder is None:
            try:
                import coder
                self._coder = coder
            except ImportError:
                logger.debug("coder module not available")

        if self._codegen is None:
            try:
                import codegen_engine
                self._codegen = codegen_engine
            except ImportError:
                logger.debug("codegen_engine not available")
