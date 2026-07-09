#!/usr/bin/env python3
"""Hybrid AI - Python Orchestrator (Phase 1)

User-facing interface that orchestrates the C inference engine.
Falls back to standalone Python mode if the C binary is unavailable.
"""

import argparse
import os
import signal
import subprocess
import sys
import time

__version__ = "0.1.0"

# ANSI color codes
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


def find_engine():
    """Locate the compiled C engine binary."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai"),
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "build", "ai"),
        "/usr/local/bin/hybrid-ai",
    ]
    for path in candidates:
        full = os.path.abspath(path)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


def colorize(text, color, use_color=True):
    """Wrap text in ANSI color codes."""
    if not use_color:
        return text
    return f"{color}{text}{RESET}"


def run_with_engine(engine_path, verbose=False, use_color=True):
    """Launch the C engine and pass through stdin/stdout."""
    print(colorize(f"[engine] {engine_path}", GREEN, use_color))
    try:
        proc = subprocess.Popen(
            [engine_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as e:
        print(f"Error launching engine: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            user_input = input(colorize("you> ", BOLD, use_color))
            if not user_input.strip():
                continue

            t0 = time.perf_counter()
            proc.stdin.write(user_input + "\n")
            proc.stdin.flush()

            response = proc.stdout.readline().rstrip("\n")
            elapsed = time.perf_counter() - t0

            print(colorize(f"ai> {response}", CYAN, use_color))
            if verbose:
                print(colorize(f"    [{elapsed*1000:.1f}ms]", YELLOW, use_color))
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        proc.terminate()
        proc.wait()


def run_standalone(verbose=False, use_color=True):
    """Fallback echo loop when C engine is unavailable."""
    print(colorize(
        "C engine not found. Running in Python-only mode (limited).",
        YELLOW, use_color,
    ))
    print(colorize("Type 'quit' to exit.\n", YELLOW, use_color))

    try:
        while True:
            user_input = input(colorize("you> ", BOLD, use_color))
            if user_input.strip().lower() in ("quit", "exit"):
                break
            if not user_input.strip():
                continue

            t0 = time.perf_counter()
            # Phase 1: simple echo response
            response = f"[echo] {user_input}"
            elapsed = time.perf_counter() - t0

            print(colorize(f"ai> {response}", CYAN, use_color))
            if verbose:
                print(colorize(f"    [{elapsed*1000:.1f}ms]", YELLOW, use_color))
    except (EOFError, KeyboardInterrupt):
        pass

    print(colorize("\nGoodbye.", GREEN, use_color))


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid AI - Python orchestrator for the C inference engine"
    )
    parser.add_argument("--verbose", action="store_true", help="Show timing info")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--version", action="version", version=f"hybrid-ai {__version__}")
    args = parser.parse_args()

    use_color = not args.no_color and sys.stdout.isatty()

    # Graceful Ctrl+C
    signal.signal(signal.SIGINT, lambda *_: None)

    print(colorize(f"Hybrid AI v{__version__}", BOLD, use_color))
    print(colorize("=" * 40, GREEN, use_color))

    engine = find_engine()
    if engine:
        run_with_engine(engine, verbose=args.verbose, use_color=use_color)
    else:
        run_standalone(verbose=args.verbose, use_color=use_color)


if __name__ == "__main__":
    main()
