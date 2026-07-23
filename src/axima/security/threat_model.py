"""AXIMA Threat Model — structured threat vector documentation.

All known threat vectors are documented as typed dataclasses
and loaded from docs/threat-model/THREATS.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterator


class ThreatCategory(Enum):
    """Category of security threat."""

    CODE_INJECTION = auto()
    PATH_TRAVERSAL = auto()
    RESOURCE_EXHAUSTION = auto()
    DATA_EXFILTRATION = auto()
    PRIVILEGE_ESCALATION = auto()
    DENIAL_OF_SERVICE = auto()
    INPUT_MANIPULATION = auto()
    SANDBOX_ESCAPE = auto()


class ThreatSeverity(Enum):
    """Severity classification."""

    P0 = auto()  # Critical — must fix before any deployment
    P1 = auto()  # High — fix in next release
    P2 = auto()  # Medium — tracked for future fix
    P3 = auto()  # Low — acceptable risk with mitigation


class ThreatStatus(Enum):
    """Current mitigation status."""

    OPEN = auto()
    MITIGATED = auto()
    ACCEPTED = auto()
    RESOLVED = auto()


@dataclass(frozen=True)
class ThreatVector:
    """A documented security threat vector."""

    id: str
    category: ThreatCategory
    description: str
    severity: ThreatSeverity
    mitigation: str
    status: ThreatStatus

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "category": self.category.name,
            "description": self.description,
            "severity": self.severity.name,
            "mitigation": self.mitigation,
            "status": self.status.name,
        }


# ---------------------------------------------------------------------------
# Built-in P0 threats (always available even without THREATS.md)
# ---------------------------------------------------------------------------

BUILTIN_THREATS: list[ThreatVector] = [
    ThreatVector(
        id="T001",
        category=ThreatCategory.CODE_INJECTION,
        description="eval() used in math calculator path allows arbitrary code execution",
        severity=ThreatSeverity.P0,
        mitigation="Replace eval() with safe_math.py AST evaluator",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T002",
        category=ThreatCategory.CODE_INJECTION,
        description="exec() used to run generated code in-process",
        severity=ThreatSeverity.P0,
        mitigation="Replace with CodeSandbox subprocess execution",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T003",
        category=ThreatCategory.RESOURCE_EXHAUSTION,
        description="No time/memory limits on math evaluation allows DoS via complex expressions",
        severity=ThreatSeverity.P0,
        mitigation="MathEvaluator enforces recursion depth, value bounds, and expression length",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T004",
        category=ThreatCategory.PATH_TRAVERSAL,
        description="User input used in file paths without validation",
        severity=ThreatSeverity.P0,
        mitigation="InputShield detects path traversal patterns; sandbox restricts file access",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T005",
        category=ThreatCategory.SANDBOX_ESCAPE,
        description="Generated code has unrestricted filesystem and network access",
        severity=ThreatSeverity.P0,
        mitigation="CodeSandbox uses isolated temp dirs, network deny, and process limits",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T006",
        category=ThreatCategory.INPUT_MANIPULATION,
        description="No input length limits allows memory exhaustion via large inputs",
        severity=ThreatSeverity.P0,
        mitigation="InputShield enforces max_input_length and max_line_count",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T007",
        category=ThreatCategory.DENIAL_OF_SERVICE,
        description="No rate limiting allows flood attacks",
        severity=ThreatSeverity.P0,
        mitigation="InputShield implements token-bucket rate limiting",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T008",
        category=ThreatCategory.CODE_INJECTION,
        description="Shell metacharacters in user input passed to subprocess",
        severity=ThreatSeverity.P0,
        mitigation="InputShield detects shell metacharacters; sandbox uses safe quoting",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T009",
        category=ThreatCategory.DATA_EXFILTRATION,
        description="Generated code could read sensitive files and exfiltrate via output",
        severity=ThreatSeverity.P0,
        mitigation="Sandbox restricts file access to temp dir; output size limited",
        status=ThreatStatus.MITIGATED,
    ),
    ThreatVector(
        id="T010",
        category=ThreatCategory.PRIVILEGE_ESCALATION,
        description="No distinction between system and user operations",
        severity=ThreatSeverity.P0,
        mitigation="Sandbox runs with minimal env; no secrets passed; isolated processes",
        status=ThreatStatus.MITIGATED,
    ),
]


# ---------------------------------------------------------------------------
# Threat model loader from THREATS.md
# ---------------------------------------------------------------------------

# Default path relative to project root
_DEFAULT_THREATS_PATH = Path(__file__).resolve().parents[3] / "docs" / "threat-model" / "THREATS.md"


def load_threats(path: Path | None = None) -> list[ThreatVector]:
    """Load threat vectors from THREATS.md, falling back to builtins.

    The markdown file format uses sections like:
        ## T001 — CODE_INJECTION — P0
        **Description:** ...
        **Mitigation:** ...
        **Status:** MITIGATED
    """
    threats_path = path or _DEFAULT_THREATS_PATH

    if not threats_path.exists():
        return list(BUILTIN_THREATS)

    try:
        content = threats_path.read_text(encoding="utf-8")
        parsed = _parse_threats_md(content)
        return parsed if parsed else list(BUILTIN_THREATS)
    except (OSError, ValueError):
        return list(BUILTIN_THREATS)


def _parse_threats_md(content: str) -> list[ThreatVector]:
    """Parse THREATS.md into ThreatVector objects."""
    threats: list[ThreatVector] = []

    # Pattern: ## T001 — CATEGORY — SEVERITY
    header_re = re.compile(
        r"^##\s+(T\d+)\s*[—–-]\s*(\w+)\s*[—–-]\s*(P\d)\s*$", re.MULTILINE
    )

    for match in header_re.finditer(content):
        tid = match.group(1)
        cat_str = match.group(2).upper()
        sev_str = match.group(3).upper()

        # Extract body until next ## or end
        start = match.end()
        next_header = header_re.search(content, start)
        body = content[start : next_header.start() if next_header else len(content)]

        # Parse fields from body
        description = _extract_field(body, "Description") or "No description"
        mitigation = _extract_field(body, "Mitigation") or "No mitigation"
        status_str = _extract_field(body, "Status") or "OPEN"

        try:
            category = ThreatCategory[cat_str]
        except KeyError:
            category = ThreatCategory.CODE_INJECTION

        try:
            severity = ThreatSeverity[sev_str]
        except KeyError:
            severity = ThreatSeverity.P1

        try:
            status = ThreatStatus[status_str.upper().strip()]
        except KeyError:
            status = ThreatStatus.OPEN

        threats.append(ThreatVector(
            id=tid,
            category=category,
            description=description,
            severity=severity,
            mitigation=mitigation,
            status=status,
        ))

    return threats


def _extract_field(body: str, field_name: str) -> str | None:
    """Extract a **FieldName:** value from markdown body."""
    pattern = re.compile(
        rf"\*\*{field_name}:\*\*\s*(.+?)(?:\n\n|\n\*\*|\n##|\Z)", re.DOTALL
    )
    match = pattern.search(body)
    if match:
        # Strip whitespace, dashes, and newlines from extracted value
        value = match.group(1).strip().strip("-").strip()
        return value
    return None


def get_p0_threats() -> list[ThreatVector]:
    """Return only P0 (critical) threats."""
    return [t for t in load_threats() if t.severity == ThreatSeverity.P0]


def get_open_threats() -> list[ThreatVector]:
    """Return threats that are not yet resolved."""
    return [t for t in load_threats() if t.status != ThreatStatus.RESOLVED]
