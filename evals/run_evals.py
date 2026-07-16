"""
AXIMA Eval Harness — Reproducible benchmarks.

Run: python3 evals/run_evals.py
Output: pass/fail per test, summary stats, error breakdown.
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'python'))


def load_eval(path: str):
    """Load eval cases from JSON file."""
    with open(path) as f:
        return json.load(f)


def run_eval_suite(suite_path: str, runner_fn):
    """Run an eval suite and return results."""
    cases = load_eval(suite_path)
    results = []
    
    for case in cases:
        input_text = case["input"]
        expected = case["expected"]
        start = time.time()
        
        try:
            actual = runner_fn(input_text)
            elapsed = time.time() - start
            
            # Score: check if expected is in actual (flexible matching)
            if isinstance(expected, list):
                passed = any(exp.lower() in actual.lower() for exp in expected)
            else:
                passed = expected.lower() in actual.lower()
            
            results.append({
                "input": input_text,
                "expected": expected,
                "actual": actual[:200],
                "passed": passed,
                "time_ms": round(elapsed * 1000, 1),
                "error": None
            })
        except Exception as e:
            results.append({
                "input": input_text,
                "expected": expected,
                "actual": None,
                "passed": False,
                "time_ms": 0,
                "error": str(e)
            })
    
    return results


def print_results(name: str, results: list):
    """Print eval results."""
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    errors = sum(1 for r in results if r["error"])
    avg_time = sum(r["time_ms"] for r in results) / max(1, total)
    
    print(f"\n{'═' * 60}")
    print(f"  {name}: {passed}/{total} passed ({passed/max(1,total)*100:.0f}%) | {errors} errors | avg {avg_time:.0f}ms")
    print(f"{'═' * 60}")
    
    # Show failures
    failures = [r for r in results if not r["passed"]]
    if failures:
        print(f"\n  Failures ({len(failures)}):")
        for f in failures[:5]:
            print(f"    Input: {f['input'][:60]}")
            if f['error']:
                print(f"    Error: {f['error'][:80]}")
            else:
                print(f"    Expected: {f['expected']}")
                print(f"    Got: {f['actual'][:80] if f['actual'] else 'None'}")
            print()


def main():
    print("AXIMA EVAL HARNESS")
    print("=" * 60)
    
    eval_dir = os.path.dirname(__file__)
    all_results = {}
    
    # Math eval
    math_path = os.path.join(eval_dir, "math", "cases.json")
    if os.path.exists(math_path):
        from axima import get_axima
        ax = get_axima()
        results = run_eval_suite(math_path, lambda q: ax.process(q).answer)
        print_results("MATH", results)
        all_results["math"] = results
    
    # Multilingual eval
    multi_path = os.path.join(eval_dir, "multilingual", "cases.json")
    if os.path.exists(multi_path):
        from axima import get_axima
        ax = get_axima()
        results = run_eval_suite(multi_path, lambda q: ax.process(q).language)
        print_results("MULTILINGUAL", results)
        all_results["multilingual"] = results
    
    # Codegen eval
    code_path = os.path.join(eval_dir, "codegen", "cases.json")
    if os.path.exists(code_path):
        from axima import get_axima
        ax = get_axima()
        results = run_eval_suite(code_path, lambda q: ax.code(q).code)
        print_results("CODEGEN", results)
        all_results["codegen"] = results
    
    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    total_passed = sum(sum(1 for r in v if r["passed"]) for v in all_results.values())
    total_cases = sum(len(v) for v in all_results.values())
    print(f"  Total: {total_passed}/{total_cases} ({total_passed/max(1,total_cases)*100:.0f}%)")
    print()


if __name__ == "__main__":
    main()
