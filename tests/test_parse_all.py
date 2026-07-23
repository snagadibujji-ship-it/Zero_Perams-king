"""
Test that all .py files in the project parse without syntax errors.

Run with: python3 tests/test_parse_all.py
Or with pytest: pytest tests/test_parse_all.py -v
"""

import ast
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories to exclude from parsing checks
EXCLUDE_DIRS = {'.git', 'archive', '__pycache__', 'node_modules', '.venv', 'venv'}


def find_all_py_files(root):
    """Find all .py files in the project, excluding specified directories."""
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for filename in filenames:
            if filename.endswith('.py'):
                py_files.append(os.path.join(dirpath, filename))
    return sorted(py_files)


def check_parse(filepath):
    """Attempt to parse a Python file. Returns (success, error_message)."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def test_all_python_files_parse():
    """Test that every .py file in the project parses without errors."""
    py_files = find_all_py_files(PROJECT_ROOT)
    failures = []

    for filepath in py_files:
        success, error = check_parse(filepath)
        if not success:
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            failures.append((rel_path, error))

    if failures:
        msg_lines = [f"\n{len(failures)} file(s) failed to parse:\n"]
        for path, error in failures:
            msg_lines.append(f"  FAIL: {path}")
            msg_lines.append(f"        {error}")
        raise AssertionError("\n".join(msg_lines))


def main():
    """Run parse check and report results."""
    py_files = find_all_py_files(PROJECT_ROOT)
    print(f"Checking {len(py_files)} Python files in {PROJECT_ROOT}...\n")

    failures = []
    for filepath in py_files:
        rel_path = os.path.relpath(filepath, PROJECT_ROOT)
        success, error = check_parse(filepath)
        if success:
            print(f"  OK: {rel_path}")
        else:
            print(f"  FAIL: {rel_path} — {error}")
            failures.append((rel_path, error))

    print(f"\n{'='*60}")
    print(f"Results: {len(py_files) - len(failures)} passed, {len(failures)} failed")
    print(f"{'='*60}")

    if failures:
        print("\nFailed files:")
        for path, error in failures:
            print(f"  {path}: {error}")
        return 1
    else:
        print("\nAll files parse successfully.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
