#!/usr/bin/env python3
"""Simple .ai scripting engine for automation scripts."""

import re
import sys
import time
import threading


class AIRuntime:
    """Provides ai.* commands available inside .ai scripts."""

    def __init__(self):
        self.memory = []

    def ask(self, question):
        """Simulate asking AI a question."""
        print(f"[AI Ask] {question}")
        return f"(simulated answer to: {question})"

    def search(self, query):
        """Simulate a web search."""
        print(f"[AI Search] {query}")
        return f"(simulated search results for: {query})"

    def remember(self, fact):
        """Store a fact in memory."""
        self.memory.append(fact)
        print(f"[AI Remember] {fact}")

    def notify(self, message):
        """Print a notification."""
        print(f"[Notify] {message}")


class ScriptEngine:
    """Manages and executes .ai automation scripts."""

    def __init__(self):
        self.ai = AIRuntime()
        self.scripts = {}
        self.scheduled = []

    def load(self, filepath):
        """Load and parse a .ai script file."""
        with open(filepath, "r") as f:
            raw = f.read()
        self.scripts[filepath] = raw
        return raw

    def parse_directives(self, source):
        """Extract @schedule and @trigger directives from source."""
        triggers = []
        schedule = None
        lines = []
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("@trigger"):
                triggers.append(stripped.split(None, 1)[1] if " " in stripped else "")
            elif stripped.startswith("@schedule"):
                match = re.search(r"every\s+(\d+)m", stripped)
                if match:
                    schedule = int(match.group(1))
            else:
                lines.append(line)
        return triggers, schedule, "\n".join(lines)

    def build_globals(self):
        """Build the safe globals dict for script execution."""
        return {
            "__builtins__": {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "True": True,
                "False": False,
                "None": None,
            },
            "ai": self.ai,
            "wait": lambda seconds: time.sleep(seconds),
        }

    def execute(self, source):
        """Execute script source code with safe globals."""
        exec(source, self.build_globals())

    def run(self, filepath, respect_triggers=True):
        """Load and run a .ai script file."""
        source = self.load(filepath)
        triggers, schedule, code = self.parse_directives(source)

        if respect_triggers and "on-start" in triggers:
            print(f"[Engine] Running on-start script: {filepath}")

        self.execute(code)

        if schedule:
            print(f"[Engine] Scheduling {filepath} every {schedule}m (simulated)")
            self._simulate_schedule(code, schedule)

    def _simulate_schedule(self, code, interval_min):
        """Simulate scheduled execution (runs once after delay in background)."""
        def _run():
            time.sleep(min(interval_min * 60, 5))  # cap at 5s for demo
            print(f"[Scheduled] Running scheduled iteration...")
            self.execute(code)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        self.scheduled.append(t)


def run_script(filepath):
    """Convenience function to execute a .ai script file."""
    engine = ScriptEngine()
    engine.run(filepath)
    return engine


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripting.py <script.ai>")
        sys.exit(1)
    run_script(sys.argv[1])
