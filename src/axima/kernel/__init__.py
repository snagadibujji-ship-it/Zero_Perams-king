"""AXIMA Kernel — Unified Cognitive Runtime.

The kernel provides:
- CosmicMicrokernel: single entry point for all queries
- CapabilityRegistry: plugin discovery and routing
- CognitiveScheduler: resource budget enforcement
- QueryTrace / EventLedger: full observability
- LegacyAdapter: backward-compatible bridge to axima.py
"""

from .runtime import CosmicMicrokernel
from .registry import CapabilityRegistry, CapabilityDescriptor
from .scheduler import CognitiveScheduler, ResourceBudget
from .trace import QueryTrace, TraceEvent
from .event_ledger import EventLedger
from .legacy_adapter import LegacyAdapter

__all__ = [
    "CosmicMicrokernel",
    "CapabilityRegistry",
    "CapabilityDescriptor",
    "CognitiveScheduler",
    "ResourceBudget",
    "QueryTrace",
    "TraceEvent",
    "EventLedger",
    "LegacyAdapter",
]
