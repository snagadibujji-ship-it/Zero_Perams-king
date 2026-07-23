# AXIMA Threat Model — P0 Security Threats

> All critical (P0) security threats identified in the AXIMA system.
> These MUST be mitigated before any deployment, even internal.

---

## T001 — CODE_INJECTION — P0

**Description:** eval() used in math calculator path allows arbitrary code execution. Any user input passed to eval() can execute arbitrary Python code, including os.system(), file operations, or network calls.

**Mitigation:** Replace eval() with safe_math.py typed AST evaluator that only supports numeric operations and whitelisted functions. Never pass user strings to eval(), exec(), or compile().

**Status:** MITIGATED

---

## T002 — CODE_INJECTION — P0

**Description:** exec() used to run generated code in-process. The code generation engines (codegen_engine, axima_coder) could produce code that gets executed in the same process, with full access to AXIMA internals and the host system.

**Mitigation:** Replace with CodeSandbox subprocess execution. All generated code runs in isolated subprocess with resource limits, restricted filesystem, and network deny policy.

**Status:** MITIGATED

---

## T003 — RESOURCE_EXHAUSTION — P0

**Description:** No time/memory limits on math evaluation allows DoS via complex expressions. A crafted expression like `2**2**2**2**2**2**100` or deeply nested functions can hang the system or exhaust memory.

**Mitigation:** MathEvaluator enforces recursion depth limit (100), value bounds (1e308), expression length limit (2000 chars), token count limit (500), and exponent magnitude checks.

**Status:** MITIGATED

---

## T004 — PATH_TRAVERSAL — P0

**Description:** User input used in file paths without validation. Brain ingestion and knowledge indexing accept file paths from user input. A path like `../../etc/passwd` could read sensitive system files.

**Mitigation:** InputShield detects path traversal patterns (../, %2e%2e, etc.). Sandbox restricts all file operations to designated temp directory. Brain module validates paths against allowed directories.

**Status:** MITIGATED

---

## T005 — SANDBOX_ESCAPE — P0

**Description:** Generated code has unrestricted filesystem and network access. Code produced by the code generation engine runs with full privileges of the AXIMA process.

**Mitigation:** CodeSandbox uses: isolated temp directories (code can only read/write within), network DENY_ALL policy (via unshare --net when available), process count limits (max 1), memory limits (via ulimit), time limits (via subprocess timeout), and output size limits.

**Status:** MITIGATED

---

## T006 — INPUT_MANIPULATION — P0

**Description:** No input length limits allows memory exhaustion via large inputs. An attacker can send a multi-gigabyte input string to exhaust server memory.

**Mitigation:** InputShield enforces max_input_length (10,000 chars default), max_line_count (500 lines), and validates encoding before any processing occurs.

**Status:** MITIGATED

---

## T007 — DENIAL_OF_SERVICE — P0

**Description:** No rate limiting allows flood attacks. Without rate limiting, an attacker can send thousands of requests per second to overwhelm the system.

**Mitigation:** InputShield implements per-source token-bucket rate limiting (10 req/sec sustained, burst of 20). Can be configured per deployment.

**Status:** MITIGATED

---

## T008 — CODE_INJECTION — P0

**Description:** Shell metacharacters in user input passed to subprocess. If user input containing characters like `;`, `|`, `&`, `` ` ``, or `$()` reaches a shell command, it can inject arbitrary commands.

**Mitigation:** InputShield detects and blocks shell metacharacters. CodeSandbox uses proper shell quoting for all arguments. Never use `shell=True` with unsanitized user input.

**Status:** MITIGATED

---

## T009 — DATA_EXFILTRATION — P0

**Description:** Generated code could read sensitive files and exfiltrate via output. Even in a sandbox, code might read /etc/passwd or AXIMA data files and include them in stdout.

**Mitigation:** Sandbox HOME and TMPDIR point to isolated temp directory. Output size is limited (1MB). File access outside temp dir is blocked by directory restriction. Network deny prevents exfiltration via network.

**Status:** MITIGATED

---

## T010 — PRIVILEGE_ESCALATION — P0

**Description:** No distinction between system and user operations. All operations run with the same privileges, meaning a user query could trigger system-level operations.

**Mitigation:** Sandbox runs with minimal environment (no secrets in env vars, restricted PATH). Secret-like env var names are rejected. Process isolation separates user code from system code.

**Status:** MITIGATED

---

## Summary

| ID | Category | Severity | Status |
|----|----------|----------|--------|
| T001 | CODE_INJECTION | P0 | MITIGATED |
| T002 | CODE_INJECTION | P0 | MITIGATED |
| T003 | RESOURCE_EXHAUSTION | P0 | MITIGATED |
| T004 | PATH_TRAVERSAL | P0 | MITIGATED |
| T005 | SANDBOX_ESCAPE | P0 | MITIGATED |
| T006 | INPUT_MANIPULATION | P0 | MITIGATED |
| T007 | DENIAL_OF_SERVICE | P0 | MITIGATED |
| T008 | CODE_INJECTION | P0 | MITIGATED |
| T009 | DATA_EXFILTRATION | P0 | MITIGATED |
| T010 | PRIVILEGE_ESCALATION | P0 | MITIGATED |

All P0 threats mitigated by Phase R1 Security Architecture.
