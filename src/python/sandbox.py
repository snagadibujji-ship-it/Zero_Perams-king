"""Sandboxed code execution — tests generated code before showing to user."""
import subprocess, tempfile, os, re, time

MAX_OUTPUT = 4096

def sandbox_run(code: str, language: str = "python", timeout: int = 5) -> dict:
    """Execute code safely in a subprocess with timeout and output limits."""
    ext = {"python": ".py", "bash": ".sh", "javascript": ".js"}.get(language)
    if not ext:
        return {"success": False, "output": "", "error": f"Unsupported language: {language}", "duration_ms": 0.0}
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=ext, prefix="ai_sandbox_", dir="/tmp", delete=False)
    tmp.write(code); tmp.close()
    cmd = {"python": ["python3", tmp.name], "bash": ["bash", tmp.name], "javascript": ["node", tmp.name]}[language]
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              env={**os.environ, "NO_PROXY": "*", "http_proxy": "", "https_proxy": ""})
        dur = (time.time() - start) * 1000
        return {"success": proc.returncode == 0, "output": proc.stdout[:MAX_OUTPUT],
                "error": proc.stderr[:MAX_OUTPUT], "duration_ms": round(dur, 2)}
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": f"Timeout after {timeout}s",
                "duration_ms": round((time.time() - start) * 1000, 2)}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e),
                "duration_ms": round((time.time() - start) * 1000, 2)}
    finally:
        os.unlink(tmp.name)

def _detect_function(code: str, language: str) -> str | None:
    """Detect the first function name from code."""
    patterns = {"python": r"def\s+(\w+)\s*\(", "javascript": r"function\s+(\w+)\s*\(", "bash": r"^(\w+)\s*\(\)"}
    m = re.search(patterns.get(language, ""), code, re.MULTILINE)
    return m.group(1) if m else None

def _generate_tests(func_name: str, language: str) -> str:
    """Generate 3 basic test calls for a detected function."""
    f = func_name
    if language == "python":
        t = ""
        for i, arg in enumerate(["", "0", '""'], 1):
            t += f'try:\n    r = {f}({arg})\n    print(f"TEST{i} PASS: {{r}}")\n'
            t += f'except Exception as e:\n    print(f"TEST{i} FAIL: {{e}}")\n'
        return t
    elif language == "javascript":
        lines = []
        for i, arg in enumerate(["", "0", '""'], 1):
            lines.append(f'try {{ let r = {f}({arg}); console.log("TEST{i} PASS: " + r); }}'
                         f' catch(e) {{ console.log("TEST{i} FAIL: " + e.message); }}')
        return "\n".join(lines) + "\n"
    elif language == "bash":
        lines = []
        for i, arg in enumerate(["", "0", '""'], 1):
            lines.append(f'if {f} {arg}; then echo "TEST{i} PASS"; else echo "TEST{i} FAIL"; fi')
        return "\n".join(lines) + "\n"
    return ""

def sandbox_test_function(code: str, language: str = "python") -> dict:
    """Detect function in code, generate test calls, run and report pass/fail."""
    func_name = _detect_function(code, language)
    if not func_name:
        return {"success": False, "function": None, "tests": [], "error": "No function detected"}
    test_code = code + "\n" + _generate_tests(func_name, language)
    result = sandbox_run(test_code, language)
    lines = (result["output"] + result["error"]).splitlines()
    tests = []
    for line in lines:
        if line.startswith("TEST"):
            tests.append({"name": line.split(":")[0].strip(), "passed": "PASS" in line, "detail": line})
    return {"success": result["success"], "function": func_name, "tests": tests,
            "error": result["error"] if not result["success"] and not tests else ""}

if __name__ == "__main__":
    print("=== Sandbox Tests ===")
    r = sandbox_run("print('hello sandbox')", "python")
    assert r["success"] and "hello sandbox" in r["output"], f"FAIL: {r}"
    print(f"[PASS] Python exec: {r['duration_ms']}ms")

    r = sandbox_run("echo 'bash works'", "bash")
    assert r["success"] and "bash works" in r["output"], f"FAIL: {r}"
    print(f"[PASS] Bash exec: {r['duration_ms']}ms")

    r = sandbox_run("console.log('js works')", "javascript")
    assert r["success"] and "js works" in r["output"], f"FAIL: {r}"
    print(f"[PASS] JS exec: {r['duration_ms']}ms")

    r = sandbox_run("import time; time.sleep(10)", "python", timeout=1)
    assert not r["success"] and "Timeout" in r["error"], f"FAIL: {r}"
    print(f"[PASS] Timeout enforced: {r['duration_ms']}ms")

    r = sandbox_test_function("def add(a, b=1):\n    return a + b\n", "python")
    assert r["function"] == "add" and len(r["tests"]) == 3, f"FAIL: {r}"
    print(f"[PASS] Function test: {r['function']}, {len(r['tests'])} tests run")

    r = sandbox_run("code", "ruby")
    assert not r["success"] and "Unsupported" in r["error"]
    print("[PASS] Unsupported language rejected")
    print("\n=== All tests passed ===")
