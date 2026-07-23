"""Plugin base class and loader.

All AXIMA plugins inherit from PluginBase and implement:
- name() -> str
- version() -> str
- describe() -> CapabilityDescriptor
- execute(ir, contract) -> ExecutionResult
- health_check() -> bool
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ..contracts.query import ExecutionResult
from ..epistemics.contracts import EpistemicContract
from ..kernel.registry import CapabilityDescriptor
from ..semantics.meaning_ir import MeaningIR

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Abstract base class for all AXIMA plugins.

    A plugin wraps a specific engine (math, physics, coder, etc.) and
    provides a uniform interface for the planner and executor.
    """

    @abstractmethod
    def name(self) -> str:
        """Unique plugin name (e.g., 'math_solver')."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Semantic version string (e.g., '1.0.0')."""
        ...

    @abstractmethod
    def describe(self) -> CapabilityDescriptor:
        """Return a CapabilityDescriptor for registration in the registry."""
        ...

    @abstractmethod
    def execute(self, ir: MeaningIR, contract: EpistemicContract) -> ExecutionResult:
        """Execute the plugin against the given MeaningIR.

        Args:
            ir: The parsed semantic representation of the query.
            contract: The epistemic contract specifying requirements.

        Returns:
            ExecutionResult with answer, evidence, and status.
        """
        ...

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if the plugin is operational."""
        ...

    def initialize(self) -> None:
        """Optional initialization hook. Called after construction."""
        pass

    def shutdown(self) -> None:
        """Optional cleanup hook. Called before unloading."""
        pass


class PluginLoader:
    """Discovers and loads plugins from the plugins directory.

    Scans for subpackages with a `plugin.py` module that defines a class
    inheriting from PluginBase.
    """

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        self._plugins_dir = plugins_dir or str(
            Path(__file__).parent
        )
        self._plugins: Dict[str, PluginBase] = {}

    def discover(self) -> List[str]:
        """Discover available plugin packages.

        Returns:
            List of discovered plugin names (directory names).
        """
        discovered: List[str] = []
        plugins_path = Path(self._plugins_dir)

        if not plugins_path.is_dir():
            return discovered

        for entry in sorted(plugins_path.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_"):
                continue
            plugin_file = entry / "plugin.py"
            if plugin_file.exists():
                discovered.append(entry.name)

        return discovered

    def load_all(self) -> Dict[str, PluginBase]:
        """Discover and load all available plugins.

        Returns:
            Dict mapping plugin name to plugin instance.
        """
        names = self.discover()
        for name in names:
            try:
                plugin = self._load_one(name)
                if plugin is not None:
                    self._plugins[plugin.name()] = plugin
                    plugin.initialize()
                    logger.info(f"Loaded plugin: {plugin.name()} v{plugin.version()}")
            except Exception as exc:
                logger.warning(f"Failed to load plugin '{name}': {exc}")

        return dict(self._plugins)

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    @property
    def loaded_plugins(self) -> Dict[str, PluginBase]:
        """All currently loaded plugins."""
        return dict(self._plugins)

    def _load_one(self, dir_name: str) -> Optional[PluginBase]:
        """Load a single plugin from its directory."""
        plugin_path = Path(self._plugins_dir) / dir_name / "plugin.py"
        if not plugin_path.exists():
            return None

        module_name = f"axima.plugins.{dir_name}.plugin"
        spec = importlib.util.spec_from_file_location(module_name, str(plugin_path))
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        # Register in sys.modules BEFORE execution so dataclass decorator works (Python 3.14+)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            # Clean up on failure
            sys.modules.pop(module_name, None)
            raise

        # Find the PluginBase subclass in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginBase)
                and attr is not PluginBase
            ):
                return attr()

        return None
