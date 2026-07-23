"""AXIMA CLI — entry point for the cosmic pipeline.

Usage:
    axima              → interactive REPL
    axima doctor       → system health check
    axima ledger       → capability ledger
    axima version      → print version
    axima <query>      → process a single query
"""

from __future__ import annotations

import sys
import time


def _print_version() -> None:
    from axima import __version__
    print(f"axima {__version__}")


def _run_doctor() -> None:
    from axima.doctor import run_doctor
    run_doctor()


def _run_ledger() -> None:
    from axima.capability_ledger import print_ledger
    print_ledger()


def _format_response(result) -> str:
    """Format an AximaResponseV2 for terminal display."""
    lines = []

    # Main answer
    if result.answer:
        lines.append(result.answer)
    else:
        lines.append("(no answer)")

    # Metadata line
    meta_parts = []
    if result.truth_level:
        meta_parts.append(f"[{result.truth_level.value}]")
    if result.engine and result.engine != "unknown":
        meta_parts.append(f"via {result.engine}")
    if result.calibrated_confidence > 0:
        meta_parts.append(f"confidence={result.calibrated_confidence:.0%}")
    if result.latency_ms > 0:
        meta_parts.append(f"{result.latency_ms:.0f}ms")

    if meta_parts:
        lines.append("  " + " | ".join(meta_parts))

    # Claims
    if result.claims:
        for claim in result.claims[:3]:
            lines.append(f"  ⊢ {claim}")

    # Caveats
    if result.caveats:
        for caveat in result.caveats[:2]:
            lines.append(f"  ⚠ {caveat}")

    return "\n".join(lines)


def _run_query(query: str) -> None:
    """Process a single query through the cosmic pipeline."""
    from axima.api import Axima
    ax = Axima()
    result = ax.query(query)
    print(_format_response(result))


def _run_repl() -> None:
    """Interactive REPL using the cosmic pipeline."""
    from axima.api import Axima
    ax = Axima()

    print("AXIMA Symbolic Intelligence Engine (Cosmic)")
    print("Type 'quit' or Ctrl+C to exit. Type 'trace' to see last trace.\n")

    while True:
        try:
            query = input("axima> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Bye.")
            break
        if query.lower() == "trace":
            last_trace = ax.get_last_trace()
            if last_trace:
                _print_trace(last_trace)
            else:
                print("  No traces yet.")
            print()
            continue
        if query.lower() == "plugins":
            plugins = ax.plugins_loaded
            if plugins:
                print(f"  Loaded plugins ({len(plugins)}):")
                for name in sorted(plugins):
                    print(f"    • {name}")
            else:
                print("  No plugins loaded.")
            print()
            continue

        result = ax.query(query)
        print(_format_response(result))
        print()


def _print_trace(trace: dict) -> None:
    """Pretty-print a trace dict."""
    print(f"  Trace: {trace.get('trace_id', '?')}")
    print(f"  Duration: {trace.get('total_duration_ms', 0):.1f}ms")
    print(f"  Events ({trace.get('event_count', 0)}):")
    for event in trace.get("events", [])[:10]:
        stage = event.get("stage", "?")
        data = event.get("data", {})
        duration = event.get("duration_ms", 0)
        summary = ", ".join(f"{k}={v}" for k, v in list(data.items())[:3])
        if duration > 0:
            print(f"    [{stage}] {summary} ({duration:.1f}ms)")
        else:
            print(f"    [{stage}] {summary}")


def main() -> None:
    """Main CLI entry point."""
    args = sys.argv[1:]

    if not args:
        _run_repl()
        return

    command = args[0].lower()

    if command in ("--version", "-V", "version"):
        _print_version()
    elif command == "doctor":
        _run_doctor()
    elif command == "ledger":
        _run_ledger()
    elif command in ("--help", "-h", "help"):
        print(__doc__ or "")
    else:
        # Treat all remaining args as a query
        query = " ".join(args)
        _run_query(query)


if __name__ == "__main__":
    main()
