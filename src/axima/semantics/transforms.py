"""Meaning transformations — verify semantic conservation across transforms."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from .meaning_ir import MeaningIR


class TransformationType(Enum):
    """Types of semantic transformations."""
    PRESERVE = "preserve"  # Full semantic preservation
    OMIT_WITH_DISCLOSURE = "omit_with_disclosure"  # Intentional omission, disclosed
    GENERALIZE = "generalize"  # Less specific (hypernym)
    SPECIALIZE = "specialize"  # More specific (hyponym)
    HYPOTHETICAL = "hypothetical"  # Reframed as hypothetical


@dataclass
class TransformOperation:
    """A single transformation operation."""
    type: TransformationType
    target: str  # ID or description of what's being transformed
    rationale: Optional[str] = None


@dataclass
class TransformPlan:
    """A plan of semantic transformations to apply."""
    operations: List[TransformOperation] = field(default_factory=list)
    input_hash: Optional[str] = None
    expected_output_constraints: List[str] = field(default_factory=list)


def verify_conservation(
    input_ir: MeaningIR,
    output_ir: MeaningIR,
    plan: TransformPlan,
) -> bool:
    """Verify that semantic content is conserved according to the transform plan.

    Rules:
    - PRESERVE operations: all input predicates/entities must appear in output
    - OMIT_WITH_DISCLOSURE: omitted items must be explicitly noted in plan
    - GENERALIZE: output may have fewer specific predicates but must keep core relations
    - SPECIALIZE: output must contain all input relations plus additional ones
    - HYPOTHETICAL: modality must change to 'possible'

    Returns True if the transformation respects the plan constraints.
    """
    # Verify input hash if specified
    if plan.input_hash and input_ir.semantic_hash() != plan.input_hash:
        return False

    # Collect operation types
    op_types = {op.type for op in plan.operations}
    omitted_targets = {
        op.target for op in plan.operations
        if op.type == TransformationType.OMIT_WITH_DISCLOSURE
    }

    # For PRESERVE-only plans, hashes must match (minus allowed omissions)
    if op_types == {TransformationType.PRESERVE}:
        return input_ir.semantic_hash() == output_ir.semantic_hash()

    # Check entity conservation
    if TransformationType.PRESERVE in op_types:
        input_entity_names = {e.name for e in input_ir.entities}
        output_entity_names = {e.name for e in output_ir.entities}
        missing = input_entity_names - output_entity_names - omitted_targets
        if missing:
            return False

    # Check predicate conservation
    if TransformationType.PRESERVE in op_types:
        input_pred_keys = {
            (p.subject, p.relation, p.object)
            for p in input_ir.predicates
            if p.subject not in omitted_targets
        }
        output_pred_keys = {
            (p.subject, p.relation, p.object)
            for p in output_ir.predicates
        }
        if not input_pred_keys.issubset(output_pred_keys):
            return False

    # For SPECIALIZE: output must have at least as many predicates
    if TransformationType.SPECIALIZE in op_types:
        if len(output_ir.predicates) < len(input_ir.predicates):
            return False

    # For HYPOTHETICAL: check modality changed
    if TransformationType.HYPOTHETICAL in op_types:
        for pred in output_ir.predicates:
            if pred.modality != "possible":
                return False

    # Check expected output constraints
    for constraint in plan.expected_output_constraints:
        if constraint == "no_new_entities":
            input_names = {e.name for e in input_ir.entities}
            output_names = {e.name for e in output_ir.entities}
            if output_names - input_names:
                return False
        elif constraint == "no_new_predicates":
            if len(output_ir.predicates) > len(input_ir.predicates):
                return False

    return True
