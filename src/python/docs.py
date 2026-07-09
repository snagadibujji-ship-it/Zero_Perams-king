"""Offline documentation and help system for Hybrid AI."""

COMMANDS = {
    "/help": ("Show help overview or help for a command", "Usage: /help [command]"),
    "/stats": ("Display session statistics", "Shows queries, teaches, hits, uptime."),
    "/do": ("Execute a shell command", "Usage: /do <command>. Runs locally, returns output."),
    "/learn": ("Teach the system a new fact", "Usage: /learn <key> = <value>"),
    "/export": ("Export knowledge base to JSON", "Usage: /export [filename]. Default: knowledge.json"),
    "/selftest": ("Run internal self-test suite", "Validates all subsystems and reports status."),
    "/dashboard": ("Show live dashboard with metrics", "Displays memory, performance, and health."),
    "/profile": ("Show or set user profile", "Usage: /profile [key=value]"),
    "/health": ("System health check", "Reports status of all engines and memory."),
    "/explain": ("Explain how the last answer was derived", "Shows reasoning chain and sources used."),
    "/quit": ("Exit the assistant", "Saves state before exiting."),
    "/memory": ("Browse or search memory", "Usage: /memory [search term]"),
    "/status": ("Show system status summary", "Engines loaded, memory usage, uptime."),
    "/undo": ("Undo last teach or action", "Reverts the most recent modification."),
    "/script": ("Run a script of commands", "Usage: /script <filename>. One command per line."),
    "/clear": ("Clear conversation history", "Resets session context, keeps knowledge."),
}

TUTORIALS = {
    1: ("Ask a question", "Try typing: What is a dog?\n"
        "The system searches its knowledge base and web if needed."),
    2: ("Teach it something", "Try typing: Remember that cats purr\n"
        "This stores a new fact in persistent memory."),
    3: ("Run a command", "Try typing: /do echo hello\n"
        "Executes shell commands and returns output."),
    4: ("Search the web", "Ask something it doesn't know yet.\n"
        "The system auto-detects gaps and searches online."),
    5: ("Check stats", "Try typing: /stats\n"
        "See how many queries, teaches, and cache hits you have."),
}

FAQS = {
    1: ("How does it work without neural networks?",
        "It uses pattern matching, TF-IDF ranking, and rule-based reasoning.\n"
        "Knowledge is stored as structured data, not weights."),
    2: ("Is my data private?",
        "Yes. All data stays local on your machine. No external APIs are\n"
        "required for core functionality. Web search is opt-in only."),
    3: ("How do I teach it new things?",
        "Say 'Remember that ...' or use /learn key = value.\n"
        "Facts persist across sessions in local storage."),
    4: ("Can it run offline?",
        "Yes. Core Q&A, learning, commands, and scripting work fully offline.\n"
        "Only web search requires connectivity."),
    5: ("How do I export my knowledge?",
        "Use /export to save your knowledge base as JSON.\n"
        "You can back it up, share it, or import it elsewhere."),
}


def help_overview():
    """Show all available commands."""
    print("=" * 50)
    print("  HYBRID AI — Command Reference")
    print("=" * 50)
    for cmd, (desc, _) in sorted(COMMANDS.items()):
        print(f"  {cmd:<12} {desc}")
    print("-" * 50)
    print("  Type /help <command> for details.")
    print("  Type 'tutorial' to start the guided tutorial.\n")


def help_command(cmd):
    """Show detailed help for a specific command."""
    key = cmd if cmd.startswith("/") else f"/{cmd}"
    if key in COMMANDS:
        desc, detail = COMMANDS[key]
        print(f"\n  {key} — {desc}\n  {detail}\n")
    else:
        print(f"  Unknown command: {key}. Try /help for list.")


def tutorial(step=1):
    """Show an interactive tutorial step (1-5)."""
    step = max(1, min(5, int(step)))
    title, body = TUTORIALS[step]
    print(f"\n  === Tutorial Step {step}/5: {title} ===")
    print(f"  {body}")
    if step < 5:
        print(f"  Next: tutorial({step + 1})\n")
    else:
        print("  🎉 Tutorial complete! You're ready to go.\n")


def faq(n=1):
    """Show a FAQ item by number (1-5)."""
    n = max(1, min(5, int(n)))
    question, answer = FAQS[n]
    print(f"\n  Q{n}: {question}")
    print(f"  A: {answer}\n")


if __name__ == "__main__":
    help_overview()
