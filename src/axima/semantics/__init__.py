"""AXIMA Semantics — Universal Meaning IR and compilation."""

from .meaning_ir import (
    Entity,
    Event,
    Quantity,
    Predicate,
    Condition,
    Goal,
    MeaningIR,
)
from .compiler import MeaningCompiler
from .transforms import TransformationType, TransformPlan, verify_conservation
from .checksum import semantic_hash, verify_checksum

__all__ = [
    "Entity",
    "Event",
    "Quantity",
    "Predicate",
    "Condition",
    "Goal",
    "MeaningIR",
    "MeaningCompiler",
    "TransformationType",
    "TransformPlan",
    "verify_conservation",
    "semantic_hash",
    "verify_checksum",
]
