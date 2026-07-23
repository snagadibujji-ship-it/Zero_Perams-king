"""Application lifecycle management: startup, shutdown, health, migration.

Manages the complete lifecycle of an AXIMA production instance:
- Graceful startup with plugin loading and dependency checks
- Graceful shutdown with state persistence
- Health and readiness checks
- Schema migration support
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol


class LifecycleState(Enum):
    """Application lifecycle states."""

    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class HealthStatus:
    """Health check result.

    Attributes:
        healthy: Overall health status.
        state: Current lifecycle state.
        checks: Individual subsystem checks.
        uptime_s: Seconds since startup.
        version: Application version.
    """

    healthy: bool
    state: LifecycleState
    checks: Dict[str, bool] = field(default_factory=dict)
    uptime_s: float = 0.0
    version: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "healthy": self.healthy,
            "state": self.state.value,
            "checks": self.checks,
            "uptime_s": self.uptime_s,
            "version": self.version,
        }


@dataclass
class MigrationStep:
    """A single schema migration step.

    Attributes:
        version: Target version after this migration.
        description: What this migration does.
        migrate_fn: Function that performs the migration.
        rollback_fn: Function to undo the migration (optional).
    """

    version: str
    description: str
    migrate_fn: Callable[[], bool]
    rollback_fn: Optional[Callable[[], bool]] = None


class PluginLoader(Protocol):
    """Protocol for plugin loading."""

    def load(self) -> bool: ...
    def name(self) -> str: ...


@dataclass
class PluginInfo:
    """Information about a loaded plugin.

    Attributes:
        name: Plugin name.
        loaded: Whether it loaded successfully.
        load_time_ms: Time taken to load.
        error: Error message if loading failed.
    """

    name: str
    loaded: bool
    load_time_ms: float = 0.0
    error: str = ""


class ApplicationLifecycle:
    """Manages AXIMA application lifecycle.

    Handles graceful startup (loading plugins, checking dependencies),
    health monitoring, graceful shutdown (persisting state), and
    schema migrations.
    """

    def __init__(
        self,
        version: str = "0.1.0",
        state_dir: Optional[Path] = None,
    ) -> None:
        """Initialize lifecycle manager.

        Args:
            version: Application version string.
            state_dir: Directory for persisting state during shutdown.
        """
        self._version = version
        self._state_dir = state_dir
        self._state = LifecycleState.CREATED
        self._start_time: Optional[float] = None
        self._plugins: List[PluginInfo] = []
        self._migrations: List[MigrationStep] = []
        self._applied_migrations: List[str] = []
        self._subsystem_health: Dict[str, bool] = {}
        self._shutdown_hooks: List[Callable[[], None]] = []
        self._startup_hooks: List[Callable[[], bool]] = []
        self._state_to_persist: Dict[str, Any] = {}

    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        return self._state

    @property
    def uptime_s(self) -> float:
        """Seconds since startup (0.0 if not started)."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def register_startup_hook(self, hook: Callable[[], bool]) -> None:
        """Register a function to run during startup.

        Args:
            hook: Function that returns True on success, False on failure.
        """
        self._startup_hooks.append(hook)

    def register_shutdown_hook(self, hook: Callable[[], None]) -> None:
        """Register a function to run during shutdown.

        Args:
            hook: Function to call during graceful shutdown.
        """
        self._shutdown_hooks.append(hook)

    def register_migration(self, migration: MigrationStep) -> None:
        """Register a schema migration step.

        Args:
            migration: The migration step to register.
        """
        self._migrations.append(migration)

    def startup(
        self,
        plugins: Optional[List[PluginLoader]] = None,
    ) -> bool:
        """Perform graceful startup.

        1. Set state to STARTING
        2. Run startup hooks
        3. Load plugins
        4. Run pending migrations
        5. Set state to READY (or DEGRADED if some plugins failed)

        Args:
            plugins: Optional list of plugins to load.

        Returns:
            True if startup completed (may be degraded), False on fatal failure.
        """
        self._state = LifecycleState.STARTING
        self._start_time = time.time()

        # Run startup hooks
        for hook in self._startup_hooks:
            try:
                if not hook():
                    self._state = LifecycleState.DEGRADED
                    self._subsystem_health["startup_hooks"] = False
                    return True  # Degraded but running
            except Exception:
                self._state = LifecycleState.DEGRADED
                self._subsystem_health["startup_hooks"] = False
                return True

        self._subsystem_health["startup_hooks"] = True

        # Load plugins
        if plugins:
            all_loaded = True
            for plugin in plugins:
                start = time.time()
                try:
                    success = plugin.load()
                    load_time = (time.time() - start) * 1000
                    info = PluginInfo(
                        name=plugin.name(),
                        loaded=success,
                        load_time_ms=load_time,
                    )
                    if not success:
                        all_loaded = False
                        info.error = "Plugin returned False"
                except Exception as e:
                    load_time = (time.time() - start) * 1000
                    info = PluginInfo(
                        name=plugin.name(),
                        loaded=False,
                        load_time_ms=load_time,
                        error=str(e),
                    )
                    all_loaded = False

                self._plugins.append(info)

            self._subsystem_health["plugins"] = all_loaded
            if not all_loaded:
                self._state = LifecycleState.DEGRADED
                return True

        # Run migrations
        migration_success = self._run_migrations()
        self._subsystem_health["migrations"] = migration_success

        if not migration_success:
            self._state = LifecycleState.DEGRADED
            return True

        self._state = LifecycleState.READY
        return True

    def shutdown(self) -> bool:
        """Perform graceful shutdown.

        1. Set state to SHUTTING_DOWN
        2. Persist state if state_dir is configured
        3. Run shutdown hooks in reverse order
        4. Set state to STOPPED

        Returns:
            True if shutdown completed cleanly.
        """
        self._state = LifecycleState.SHUTTING_DOWN

        # Persist state
        if self._state_dir and self._state_to_persist:
            self._persist_state()

        # Run shutdown hooks in reverse order (LIFO)
        errors: List[str] = []
        for hook in reversed(self._shutdown_hooks):
            try:
                hook()
            except Exception as e:
                errors.append(str(e))

        self._state = LifecycleState.STOPPED
        return len(errors) == 0

    def health_check(self) -> HealthStatus:
        """Run health check.

        Returns:
            HealthStatus with current state and subsystem checks.
        """
        healthy = self._state in (LifecycleState.READY, LifecycleState.DEGRADED)

        # Check all subsystems
        checks = dict(self._subsystem_health)
        checks["state"] = self._state == LifecycleState.READY

        return HealthStatus(
            healthy=healthy,
            state=self._state,
            checks=checks,
            uptime_s=self.uptime_s,
            version=self._version,
        )

    def ready_check(self) -> bool:
        """Check if the application is ready to serve requests.

        Returns:
            True if in READY state, False otherwise.
        """
        return self._state == LifecycleState.READY

    def set_subsystem_health(self, name: str, healthy: bool) -> None:
        """Update health status of a subsystem.

        Args:
            name: Subsystem name.
            healthy: Whether the subsystem is healthy.
        """
        self._subsystem_health[name] = healthy

        # If any subsystem is unhealthy and we're in READY, go DEGRADED
        if not healthy and self._state == LifecycleState.READY:
            self._state = LifecycleState.DEGRADED

    def set_state_to_persist(self, key: str, value: Any) -> None:
        """Register state to persist during shutdown.

        Args:
            key: State key.
            value: State value (must be JSON-serializable).
        """
        self._state_to_persist[key] = value

    def _run_migrations(self) -> bool:
        """Run pending migrations in order."""
        for migration in self._migrations:
            if migration.version in self._applied_migrations:
                continue

            try:
                success = migration.migrate_fn()
                if success:
                    self._applied_migrations.append(migration.version)
                else:
                    return False
            except Exception:
                return False

        return True

    def _persist_state(self) -> None:
        """Persist state to disk."""
        if self._state_dir is None:
            return

        import json

        self._state_dir.mkdir(parents=True, exist_ok=True)
        state_file = self._state_dir / "lifecycle_state.json"

        state = {
            "version": self._version,
            "applied_migrations": self._applied_migrations,
            "persisted_state": self._state_to_persist,
            "shutdown_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
