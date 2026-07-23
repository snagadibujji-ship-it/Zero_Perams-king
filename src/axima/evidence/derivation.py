"""Derivation DAGs — replayable proof chains for derived claims."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class DerivationStep:
    """A single step in a derivation chain."""
    id: str
    rule: str
    inputs: List[str]
    output: str
    justification: str


@dataclass
class DerivationDAG:
    """Directed acyclic graph of derivation steps for a claim.

    Every derived claim must have a replayable derivation.
    """
    steps: Dict[str, DerivationStep] = field(default_factory=dict)
    root_claim_id: str = ""
    assumptions: List[str] = field(default_factory=list)

    def add_step(self, step: DerivationStep) -> None:
        """Add a derivation step. Inputs must reference existing step outputs or assumptions."""
        for inp in step.inputs:
            if inp not in self.assumptions and not any(
                s.output == inp for s in self.steps.values()
            ):
                raise ValueError(
                    f"Input '{inp}' not found in existing step outputs or assumptions"
                )
        if step.id in self.steps:
            raise ValueError(f"Step {step.id} already exists")
        self.steps[step.id] = step

    def verify_chain(self) -> bool:
        """Verify the derivation chain is well-formed (all inputs resolvable, no cycles)."""
        available_outputs: Set[str] = set(self.assumptions)
        # Topological check: process steps in dependency order
        remaining = dict(self.steps)
        progress = True
        while remaining and progress:
            progress = False
            to_remove = []
            for step_id, step in remaining.items():
                if all(inp in available_outputs for inp in step.inputs):
                    available_outputs.add(step.output)
                    to_remove.append(step_id)
                    progress = True
            for step_id in to_remove:
                del remaining[step_id]
        return len(remaining) == 0

    def get_assumptions(self) -> List[str]:
        """Return all assumptions required by this derivation."""
        return list(self.assumptions)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the DAG to a dictionary for storage/transmission."""
        return {
            "root_claim_id": self.root_claim_id,
            "assumptions": list(self.assumptions),
            "steps": {
                step_id: {
                    "id": step.id,
                    "rule": step.rule,
                    "inputs": step.inputs,
                    "output": step.output,
                    "justification": step.justification,
                }
                for step_id, step in self.steps.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DerivationDAG":
        """Reconstruct a DAG from a dictionary."""
        dag = cls(
            root_claim_id=data["root_claim_id"],
            assumptions=data.get("assumptions", []),
        )
        for step_id, step_data in data.get("steps", {}).items():
            dag.steps[step_id] = DerivationStep(
                id=step_data["id"],
                rule=step_data["rule"],
                inputs=step_data["inputs"],
                output=step_data["output"],
                justification=step_data["justification"],
            )
        return dag

    def replay(self, rule_registry: Optional[Dict[str, Callable]] = None) -> Dict[str, str]:
        """Replay the derivation to reproduce outputs.

        If rule_registry is provided, applies each rule function to its inputs.
        Otherwise, returns the stored outputs (dry replay).
        """
        results: Dict[str, str] = {}
        available: Dict[str, str] = {a: a for a in self.assumptions}

        remaining = dict(self.steps)
        progress = True
        while remaining and progress:
            progress = False
            to_remove = []
            for step_id, step in remaining.items():
                if all(inp in available for inp in step.inputs):
                    if rule_registry and step.rule in rule_registry:
                        input_values = [available[inp] for inp in step.inputs]
                        output = rule_registry[step.rule](*input_values)
                    else:
                        output = step.output
                    available[step.output] = output
                    results[step_id] = output
                    to_remove.append(step_id)
                    progress = True
            for step_id in to_remove:
                del remaining[step_id]

        if remaining:
            raise RuntimeError(f"Could not replay steps: {list(remaining.keys())}")
        return results
