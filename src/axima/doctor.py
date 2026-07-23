"""AXIMA Doctor — system health diagnostics.

Checks:
- Python version compatibility
- Package install status
- Data directory existence and sizes
- Active source file count and parse status
- Plugin/engine health
- Memory/disk usage
- Security mode (safe evaluator status)
"""

from __future__ import annotations

import ast
import os
import platform
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence


class CheckStatus(Enum):
    """Status of a single health check."""

    OK = "OK"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True)
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    status: CheckStatus
    message: str
    details: str = ""


def _check_python_version() -> CheckResult:
    """Check Python version meets minimum requirement."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    if version >= (3, 11):
        return CheckResult("Python Version", CheckStatus.OK, f"{version_str} (>= 3.11)")
    elif version >= (3, 10):
        return CheckResult("Python Version", CheckStatus.WARN, f"{version_str} (3.11+ recommended)")
    else:
        return CheckResult("Python Version", CheckStatus.FAIL, f"{version_str} (requires >= 3.11)")


def _check_package_install() -> CheckResult:
    """Check if axima package is properly installed."""
    try:
        import axima
        version = getattr(axima, "__version__", "unknown")
        return CheckResult("Package Install", CheckStatus.OK, f"axima {version}")
    except ImportError:
        return CheckResult("Package Install", CheckStatus.WARN, "Not installed as package (running from source)")


def _dir_size_mb(path: Path) -> float:
    """Calculate total size of a directory in MB."""
    total = 0
    if path.is_dir():
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    return total / (1024 * 1024)


def _check_data_directories() -> CheckResult:
    """Check data directory existence and sizes."""
    from axima.config import DATA_DIR, USER_DATA_DIR, CACHE_DIR

    parts: list[str] = []
    all_ok = True

    for name, path in [("data", DATA_DIR), ("user_data", USER_DATA_DIR), ("cache", CACHE_DIR)]:
        if path.is_dir():
            size = _dir_size_mb(path)
            parts.append(f"{name}: {size:.1f}MB")
        else:
            parts.append(f"{name}: MISSING")
            if name == "data":
                all_ok = False

    status = CheckStatus.OK if all_ok else CheckStatus.WARN
    return CheckResult("Data Directories", status, " | ".join(parts))


def _check_source_files() -> CheckResult:
    """Check active source file count and parse status."""
    from axima.config import SRC_PYTHON_DIR

    if not SRC_PYTHON_DIR.is_dir():
        return CheckResult("Source Files", CheckStatus.FAIL, f"{SRC_PYTHON_DIR} not found")

    py_files = list(SRC_PYTHON_DIR.rglob("*.py"))
    total = len(py_files)
    parse_ok = 0
    parse_fail: list[str] = []

    for f in py_files:
        try:
            source = f.read_text(encoding="utf-8")
            ast.parse(source)
            parse_ok += 1
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_fail.append(f"{f.name}: {exc}")

    status = CheckStatus.OK if not parse_fail else CheckStatus.WARN
    message = f"{parse_ok}/{total} files parse OK"
    details = "\n".join(parse_fail[:5]) if parse_fail else ""

    return CheckResult("Source Files", status, message, details)


def _check_engines() -> CheckResult:
    """Check available engines (plugin health)."""
    from axima.config import SRC_PYTHON_DIR

    engines: dict[str, bool] = {
        "math (prometheus)": (SRC_PYTHON_DIR / "prometheus.py").is_file(),
        "physics": (SRC_PYTHON_DIR / "prometheus_physics.py").is_file(),
        "inference": (SRC_PYTHON_DIR / "inference_engine.py").is_file(),
        "coder": (SRC_PYTHON_DIR / "coder.py").is_file(),
        "codegen": (SRC_PYTHON_DIR / "codegen_engine.py").is_file(),
        "web_generator": (SRC_PYTHON_DIR / "web_generator.py").is_file(),
        "creator": (SRC_PYTHON_DIR / "creator").is_dir(),
        "multilingual": (SRC_PYTHON_DIR / "multilingual").is_dir(),
        "aces_v2": (SRC_PYTHON_DIR / "aces_v2").is_dir(),
        "brain": (SRC_PYTHON_DIR / "brain_ingest.py").is_file(),
    }

    available = [name for name, ok in engines.items() if ok]
    missing = [name for name, ok in engines.items() if not ok]

    if not missing:
        return CheckResult("Engines", CheckStatus.OK, f"{len(available)}/{len(engines)} available")
    elif len(available) > len(missing):
        return CheckResult(
            "Engines",
            CheckStatus.WARN,
            f"{len(available)}/{len(engines)} available",
            f"Missing: {', '.join(missing)}",
        )
    else:
        return CheckResult(
            "Engines",
            CheckStatus.FAIL,
            f"Only {len(available)}/{len(engines)} available",
            f"Missing: {', '.join(missing)}",
        )


def _check_memory_disk() -> CheckResult:
    """Check memory and disk usage."""
    import resource

    # Disk usage
    from axima.config import AXIMA_HOME
    disk = shutil.disk_usage(str(AXIMA_HOME))
    disk_free_gb = disk.free / (1024**3)
    disk_total_gb = disk.total / (1024**3)

    # Process memory (RSS)
    rusage = resource.getrusage(resource.RUSAGE_SELF)
    rss_mb = rusage.ru_maxrss / 1024  # Linux reports in KB

    parts = [
        f"disk: {disk_free_gb:.1f}/{disk_total_gb:.1f}GB free",
        f"RSS: {rss_mb:.1f}MB",
    ]

    status = CheckStatus.OK if disk_free_gb > 1.0 else CheckStatus.WARN
    return CheckResult("Memory/Disk", status, " | ".join(parts))


def _check_security_mode() -> CheckResult:
    """Check if safe evaluator is active (no raw eval usage)."""
    from axima.config import SRC_PYTHON_DIR

    if not SRC_PYTHON_DIR.is_dir():
        return CheckResult("Security Mode", CheckStatus.SKIP, "Source directory not found")

    # Scan for raw eval() usage
    eval_files: list[str] = []
    for f in SRC_PYTHON_DIR.rglob("*.py"):
        try:
            source = f.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id == "eval":
                        eval_files.append(f.name)
                        break
        except (SyntaxError, UnicodeDecodeError):
            pass

    if not eval_files:
        return CheckResult("Security Mode", CheckStatus.OK, "No raw eval() detected — safe mode")
    else:
        return CheckResult(
            "Security Mode",
            CheckStatus.WARN,
            f"eval() found in {len(eval_files)} file(s)",
            f"Files: {', '.join(sorted(set(eval_files))[:5])}",
        )


def collect_checks() -> Sequence[CheckResult]:
    """Run all diagnostic checks and return results."""
    checks: list[CheckResult] = [
        _check_python_version(),
        _check_package_install(),
        _check_data_directories(),
        _check_source_files(),
        _check_engines(),
        _check_memory_disk(),
        _check_security_mode(),
    ]
    return checks


def run_doctor() -> None:
    """Run all checks and print formatted output."""
    print("AXIMA Doctor")
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python:   {sys.executable}")
    print("=" * 60)

    checks = collect_checks()
    any_fail = False

    for check in checks:
        icon = {
            CheckStatus.OK: "✓",
            CheckStatus.WARN: "⚠",
            CheckStatus.FAIL: "✗",
            CheckStatus.SKIP: "–",
        }[check.status]

        print(f"  {icon} {check.name:20s} {check.message}")
        if check.details:
            for line in check.details.split("\n"):
                print(f"    {line}")
        if check.status == CheckStatus.FAIL:
            any_fail = True

    print("=" * 60)
    if any_fail:
        print("  Some checks FAILED. AXIMA may not function correctly.")
        raise SystemExit(1)
    else:
        print("  All checks passed.")


if __name__ == "__main__":
    run_doctor()
