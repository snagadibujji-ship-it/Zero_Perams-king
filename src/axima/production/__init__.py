"""AXIMA Production System: API, lifecycle, and backup management.

Provides:
- AximaAPI: Local HTTP-like API contract with health/readiness/diagnostics
- ApplicationLifecycle: Startup, shutdown, health checks, migration
- BackupManager: Backup, restore, and verify system state
"""

from __future__ import annotations

from .api import AximaAPI, Request, Response, Route
from .lifecycle import ApplicationLifecycle
from .backup import BackupManager

__all__ = [
    "AximaAPI",
    "Request",
    "Response",
    "Route",
    "ApplicationLifecycle",
    "BackupManager",
]
