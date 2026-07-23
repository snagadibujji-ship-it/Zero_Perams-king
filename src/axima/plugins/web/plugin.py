"""Web Plugin — wraps web_generator for website generation.

Adds project persistence on top of the component-based
website generation engine.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...contracts.query import ExecutionResult
from ...epistemics.contracts import EpistemicContract
from ...kernel.registry import CapabilityDescriptor, HealthStatus
from ...semantics.meaning_ir import MeaningIR
from ..base import PluginBase

logger = logging.getLogger(__name__)

_LEGACY_DIR = Path(__file__).parent.parent.parent.parent.parent / "python"


@dataclass
class WebProject:
    """A persisted web project."""

    id: str
    name: str
    framework: str  # "vanilla", "react", "threejs"
    pages: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "framework": self.framework,
            "pages": self.pages,
            "assets": self.assets,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


class WebPlugin(PluginBase):
    """Website generation with project persistence."""

    def __init__(self) -> None:
        self._generator = None
        self._healthy = False
        self._projects: Dict[str, WebProject] = {}

    def name(self) -> str:
        return "web_builder"

    def version(self) -> str:
        return "1.0.0"

    def describe(self) -> CapabilityDescriptor:
        return CapabilityDescriptor(
            name=self.name(),
            version=self.version(),
            accepted_types=["web", "website", "html", "react", "threejs"],
            produced_types=["html", "css", "javascript", "project"],
            preconditions=[],
            postconditions=["web_project"],
            cost_model={"avg_ms": 500, "max_ms": 10000},
            latency_model={"avg_ms": 500, "p95_ms": 5000},
            deterministic=True,
            permissions=["read", "write"],
            health=HealthStatus.HEALTHY if self._healthy else HealthStatus.UNKNOWN,
        )

    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Generate a website from the MeaningIR."""
        start = time.time()

        # Extract website specification
        spec = self._extract_spec(ir)
        if not spec:
            return ExecutionResult(
                status="error",
                error="Could not determine website specification",
                engine=self.name(),
                cost_ms=(time.time() - start) * 1000,
            )

        # Generate the website
        result = self._generate(spec)
        elapsed = (time.time() - start) * 1000

        if result is not None:
            # Persist the project
            project = WebProject(
                id=f"web_{int(time.time())}",
                name=spec.get("name", "untitled"),
                framework=spec.get("framework", "vanilla"),
                pages=result.get("pages", []),
            )
            self._projects[project.id] = project

            return ExecutionResult(
                answer=result.get("html", result.get("code", "")),
                status="success",
                claims=[
                    f"Generated {spec.get('framework', 'vanilla')} website: {spec.get('name', 'untitled')}",
                    f"Project ID: {project.id}",
                ],
                evidence=["web_generator"],
                engine=self.name(),
                cost_ms=elapsed,
            )

        return ExecutionResult(
            status="error",
            error=f"Website generation failed for: {spec.get('name', 'unknown')}",
            engine=self.name(),
            cost_ms=elapsed,
        )

    def health_check(self) -> bool:
        """Check if the web generator is available."""
        try:
            self._load_engine()
            self._healthy = self._generator is not None
            return self._healthy
        except Exception:
            self._healthy = False
            return False

    def initialize(self) -> None:
        self._load_engine()

    # --- Project Persistence ---

    def get_project(self, project_id: str) -> Optional[WebProject]:
        """Retrieve a persisted web project."""
        return self._projects.get(project_id)

    def list_projects(self) -> List[WebProject]:
        """List all persisted projects."""
        return list(self._projects.values())

    def delete_project(self, project_id: str) -> bool:
        """Delete a persisted project."""
        if project_id in self._projects:
            del self._projects[project_id]
            return True
        return False

    # --- Internal Methods ---

    def _extract_spec(self, ir: MeaningIR) -> Optional[Dict[str, Any]]:
        """Extract website specification from IR."""
        spec: Dict[str, Any] = {}

        # Detect framework from entities or keywords
        for entity in ir.entities:
            if entity.name.lower() in ("react", "vue", "angular"):
                spec["framework"] = entity.name.lower()
            elif entity.name.lower() in ("threejs", "three.js", "3d"):
                spec["framework"] = "threejs"

        if "framework" not in spec:
            spec["framework"] = "vanilla"

        # Get website name/description from goals
        for goal in ir.goals:
            spec["name"] = goal.description
            spec["constraints"] = goal.constraints
            break

        # Check events
        if "name" not in spec:
            for event in ir.events:
                if event.verb in ("build", "create", "generate", "make"):
                    spec["name"] = event.patient or "website"
                    break

        if "name" not in spec:
            return None

        return spec

    def _generate(self, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate website using web_generator."""
        try:
            self._load_engine()
            if self._generator is not None:
                result = self._generator.generate(
                    spec.get("name", "website"),
                    framework=spec.get("framework", "vanilla"),
                )
                if result:
                    if isinstance(result, str):
                        return {"html": result, "pages": ["index.html"]}
                    return result
        except Exception as exc:
            logger.debug(f"Web generation failed: {exc}")
        return None

    def _load_engine(self) -> None:
        """Load the web generator from legacy code."""
        if self._generator is not None:
            return
        try:
            legacy_dir = str(_LEGACY_DIR)
            if legacy_dir not in sys.path:
                sys.path.insert(0, legacy_dir)
            import web_generator
            self._generator = web_generator
        except ImportError:
            logger.debug("web_generator not available")
