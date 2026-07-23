# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in AXIMA, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email: security@axima-project.dev (or contact the maintainer directly)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

We aim to acknowledge reports within 48 hours and provide a fix within 7 days for critical issues.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Current |
| < 0.1   | ❌ Legacy (archived) |

## Security Design Principles

AXIMA's security model follows four core principles:

### 1. No Unsafe Eval

`eval()`, `exec()`, and `compile()` are **banned** from all code paths. Mathematical expressions are evaluated through a typed AST evaluator (`safe_math.py`) that:

- Parses expressions into an AST with whitelisted node types only
- Supports only numeric operations and approved mathematical functions
- Enforces recursion depth limits (100), value bounds (±1e308), expression length limits (2000 chars)
- Rejects any construct that could produce side effects

See [ADR-003](docs/decisions/ADR-003-no-eval.md) for full rationale.

### 2. Default-Deny

All operations start from a deny-all posture:

- **Network:** Generated code runs with `DENY_ALL` network policy (via `unshare --net` when available)
- **Filesystem:** Code execution restricted to isolated temp directories; no access to AXIMA internals or host filesystem
- **Permissions:** `QueryEnvelope.user_permissions` defaults to `["read"]` only
- **Input:** All user input passes through `InputShield` validation before reaching any engine

### 3. Capability Tokens

Operations require explicit capability grants:

- Each plugin declares required capabilities in its manifest
- The kernel grants only the minimum capabilities needed for each query
- Capabilities are scoped per-request and non-transferable
- The `capability_ledger.py` tracks all grants for audit

### 4. Sandbox Isolation

All generated code executes in a restricted subprocess sandbox:

- **Process isolation:** Separate subprocess with resource limits
- **Memory limits:** Enforced via `ulimit`
- **Time limits:** Hard deadline via `subprocess.timeout`
- **Output limits:** 1MB max output size
- **Environment:** Minimal env vars, no secrets, restricted PATH
- **Process count:** Max 1 child process

## Threat Model

See [docs/threat-model/THREATS.md](docs/threat-model/THREATS.md) for the complete threat analysis with 10 identified P0 threats and their mitigations.

## Security Testing

Security tests live in `tests/security/` and are run as part of the standard test suite:

```bash
pytest tests/security/ -v
```

These tests verify:
- Safe math evaluator rejects all injection attempts
- Input validation blocks path traversal, shell metacharacters, oversized inputs
- Sandbox isolation prevents escape attempts
- Rate limiting functions correctly
