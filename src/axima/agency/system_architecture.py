"""System Architecture IR — bidirectional mapping between requirements, model, and code.

Represents systems as entities with interfaces, state machines, and invariants,
connected by typed relations with protocols and data flow.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple


class EntityType(Enum):
    SERVICE = auto()
    DATABASE = auto()
    QUEUE = auto()
    CACHE = auto()
    GATEWAY = auto()
    FUNCTION = auto()
    MODULE = auto()
    EXTERNAL = auto()


class RelationshipType(Enum):
    CALLS = auto()
    SUBSCRIBES = auto()
    PUBLISHES = auto()
    READS = auto()
    WRITES = auto()
    DEPENDS_ON = auto()
    EXTENDS = auto()
    IMPLEMENTS = auto()


class Protocol(Enum):
    HTTP = auto()
    GRPC = auto()
    WEBSOCKET = auto()
    TCP = auto()
    UDP = auto()
    AMQP = auto()
    INTERNAL = auto()


@dataclass
class StateTransition:
    """A state machine transition."""
    from_state: str
    to_state: str
    trigger: str
    guard: Optional[str] = None
    action: Optional[str] = None


@dataclass
class StateMachine:
    """A finite state machine for an entity."""
    states: List[str] = field(default_factory=list)
    initial_state: str = ""
    transitions: List[StateTransition] = field(default_factory=list)
    terminal_states: List[str] = field(default_factory=list)


@dataclass
class Interface:
    """An interface exposed or consumed by an entity."""
    name: str
    methods: List[str] = field(default_factory=list)
    protocol: Protocol = Protocol.INTERNAL
    version: str = ""


@dataclass
class Invariant:
    """A system invariant that must always hold."""
    description: str
    scope: str = ""  # which entity/relation it applies to
    formal: Optional[str] = None  # formal expression if available
    verified: bool = False


@dataclass
class Constraint:
    """A system constraint (performance, resource, etc.)."""
    description: str
    metric: str = ""
    threshold: Optional[float] = None
    unit: str = ""


@dataclass
class Threat:
    """A security threat in the threat model."""
    description: str
    category: str = ""  # e.g., "STRIDE" category
    target: str = ""    # which entity/relation
    mitigation: Optional[str] = None
    severity: str = "medium"


@dataclass
class DataFlow:
    """Data flow between entities."""
    data_type: str
    direction: str = "unidirectional"  # or "bidirectional"
    encrypted: bool = False
    classification: str = "internal"  # internal, confidential, public


@dataclass
class Operation:
    """A system-level operation spanning multiple entities."""
    name: str
    steps: List[str] = field(default_factory=list)
    entities_involved: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)


@dataclass
class SystemEntity:
    """An entity in the system architecture."""
    name: str
    type: EntityType
    interfaces: List[Interface] = field(default_factory=list)
    state_machine: Optional[StateMachine] = None
    invariants: List[Invariant] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemRelation:
    """A relationship between two system entities."""
    source: str
    target: str
    type: RelationshipType
    protocol: Protocol = Protocol.INTERNAL
    data_flow: Optional[DataFlow] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemArchitectureIR:
    """Intermediate representation of a complete system architecture.

    This is the central model that connects requirements, design, and code.
    """
    entities: List[SystemEntity] = field(default_factory=list)
    relations: List[SystemRelation] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    invariants: List[Invariant] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    threats: List[Threat] = field(default_factory=list)
    name: str = ""
    version: str = ""

    def get_entity(self, name: str) -> Optional[SystemEntity]:
        """Get entity by name."""
        for e in self.entities:
            if e.name == name:
                return e
        return None

    def get_relations_from(self, entity_name: str) -> List[SystemRelation]:
        """Get all relations originating from an entity."""
        return [r for r in self.relations if r.source == entity_name]

    def get_relations_to(self, entity_name: str) -> List[SystemRelation]:
        """Get all relations targeting an entity."""
        return [r for r in self.relations if r.target == entity_name]

    def entity_names(self) -> List[str]:
        """Get all entity names."""
        return [e.name for e in self.entities]


@dataclass
class SemanticDiff:
    """Semantic difference between two architecture IRs."""
    added_entities: List[str] = field(default_factory=list)
    removed_entities: List[str] = field(default_factory=list)
    modified_entities: List[str] = field(default_factory=list)
    added_relations: List[Tuple[str, str]] = field(default_factory=list)
    removed_relations: List[Tuple[str, str]] = field(default_factory=list)
    added_invariants: List[str] = field(default_factory=list)
    removed_invariants: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)

    @property
    def has_breaking_changes(self) -> bool:
        return len(self.breaking_changes) > 0

    @property
    def is_empty(self) -> bool:
        return not any([
            self.added_entities, self.removed_entities, self.modified_entities,
            self.added_relations, self.removed_relations,
            self.added_invariants, self.removed_invariants,
        ])


@dataclass
class Requirement:
    """A system requirement."""
    id: str
    description: str
    type: str = "functional"  # functional, non-functional, constraint
    priority: str = "medium"
    traces_to: List[str] = field(default_factory=list)  # entity/operation names


class ArchitectureCompiler:
    """Bidirectional compiler: requirements <-> architecture IR <-> code.

    - from_requirements: build IR from requirements
    - from_code: infer IR from source code
    - to_code: generate code stubs from IR
    - semantic_diff: compare two IRs
    """

    def __init__(self) -> None:
        self._ir: Optional[SystemArchitectureIR] = None

    @property
    def current_ir(self) -> Optional[SystemArchitectureIR]:
        return self._ir

    def from_requirements(self, requirements: List[Requirement]) -> SystemArchitectureIR:
        """Build a SystemArchitectureIR from a list of requirements.

        Infers entities from nouns, relations from verbs, constraints from non-functional reqs.
        """
        ir = SystemArchitectureIR(name="generated", version="0.1")
        entity_names: Set[str] = set()

        for req in requirements:
            if req.type == "functional":
                # Extract entities from traces_to or description
                for entity_name in req.traces_to:
                    if entity_name not in entity_names:
                        entity = SystemEntity(
                            name=entity_name,
                            type=EntityType.SERVICE,
                            invariants=[],
                        )
                        ir.entities.append(entity)
                        entity_names.add(entity_name)

                # Create operation from requirement
                if req.traces_to:
                    op = Operation(
                        name=f"op_{req.id}",
                        entities_involved=req.traces_to,
                        preconditions=[],
                        postconditions=[req.description],
                    )
                    ir.operations.append(op)

            elif req.type == "non-functional":
                constraint = Constraint(
                    description=req.description,
                    metric=req.id,
                )
                ir.constraints.append(constraint)

            elif req.type == "constraint":
                invariant = Invariant(
                    description=req.description,
                    scope="system",
                )
                ir.invariants.append(invariant)

        # Infer relations between entities that share operations
        for op in ir.operations:
            entities = op.entities_involved
            for i in range(len(entities) - 1):
                rel = SystemRelation(
                    source=entities[i],
                    target=entities[i + 1],
                    type=RelationshipType.CALLS,
                )
                ir.relations.append(rel)

        self._ir = ir
        return ir

    def from_code(self, root_path: str) -> SystemArchitectureIR:
        """Infer a SystemArchitectureIR from source code.

        Parses Python files to find classes (entities), imports (relations),
        and docstrings (invariants/constraints).
        """
        ir = SystemArchitectureIR(name="inferred", version="0.1")
        root = os.path.abspath(root_path)

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv")
            ]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                full_path = os.path.join(dirpath, fname)
                self._extract_from_python(full_path, ir)

        self._ir = ir
        return ir

    def to_code(self, ir: SystemArchitectureIR, output_dir: str) -> Dict[str, str]:
        """Generate code stubs from a SystemArchitectureIR.

        Returns dict of file_path -> generated code.
        """
        generated: Dict[str, str] = {}

        for entity in ir.entities:
            file_name = f"{entity.name.lower().replace(' ', '_')}.py"
            file_path = os.path.join(output_dir, file_name)

            lines: List[str] = []
            lines.append(f'"""Module for {entity.name} ({entity.type.name})."""')
            lines.append("")
            lines.append("from __future__ import annotations")
            lines.append("from dataclasses import dataclass")
            lines.append("from typing import Any, Dict, List, Optional")
            lines.append("")
            lines.append("")

            # Generate class
            class_name = entity.name.replace(" ", "").replace("-", "").replace("_", " ").title().replace(" ", "")
            lines.append(f"class {class_name}:")
            doc = f'    """Entity: {entity.name} (type: {entity.type.name}).'
            lines.append(doc)
            if entity.invariants:
                lines.append("")
                lines.append("    Invariants:")
                for inv in entity.invariants:
                    lines.append(f"        - {inv.description}")
            lines.append('    """')
            lines.append("")

            # Generate interface methods
            for iface in entity.interfaces:
                for method in iface.methods:
                    lines.append(f"    def {method}(self) -> Any:")
                    lines.append(f'        """Interface: {iface.name}."""')
                    lines.append("        raise NotImplementedError")
                    lines.append("")

            # State machine methods
            if entity.state_machine:
                sm = entity.state_machine
                lines.append(f"    # State machine: states={sm.states}")
                lines.append(f"    _state: str = '{sm.initial_state}'")
                lines.append("")
                for transition in sm.transitions:
                    method_name = f"transition_{transition.trigger}".lower().replace(" ", "_")
                    lines.append(f"    def {method_name}(self) -> None:")
                    lines.append(f'        """Transition: {transition.from_state} -> {transition.to_state}."""')
                    guard = f" if {transition.guard}" if transition.guard else ""
                    lines.append(f"        assert self._state == '{transition.from_state}'{guard}")
                    lines.append(f"        self._state = '{transition.to_state}'")
                    lines.append("")

            if not entity.interfaces and not entity.state_machine:
                lines.append("    pass")
                lines.append("")

            generated[file_path] = "\n".join(lines)

        return generated

    def semantic_diff(self, old: SystemArchitectureIR, new: SystemArchitectureIR) -> SemanticDiff:
        """Compute semantic difference between two architecture IRs."""
        old_entities = set(e.name for e in old.entities)
        new_entities = set(e.name for e in new.entities)

        old_relations = set((r.source, r.target) for r in old.relations)
        new_relations = set((r.source, r.target) for r in new.relations)

        old_invariants = set(i.description for i in old.invariants)
        new_invariants = set(i.description for i in new.invariants)

        # Detect modified entities (same name, different properties)
        modified: List[str] = []
        for name in old_entities & new_entities:
            old_e = old.get_entity(name)
            new_e = new.get_entity(name)
            if old_e and new_e:
                if (old_e.type != new_e.type or
                        len(old_e.interfaces) != len(new_e.interfaces) or
                        old_e.state_machine != new_e.state_machine):
                    modified.append(name)

        # Detect breaking changes
        breaking: List[str] = []
        removed_ents = old_entities - new_entities
        for name in removed_ents:
            # Check if any other entity depends on it
            for r in old.relations:
                if r.target == name:
                    breaking.append(f"Removed entity '{name}' which is depended on by '{r.source}'")
                    break

        removed_rels = old_relations - new_relations
        for src, tgt in removed_rels:
            breaking.append(f"Removed relation: {src} -> {tgt}")

        return SemanticDiff(
            added_entities=list(new_entities - old_entities),
            removed_entities=list(removed_ents),
            modified_entities=modified,
            added_relations=list(new_relations - old_relations),
            removed_relations=list(removed_rels),
            added_invariants=list(new_invariants - old_invariants),
            removed_invariants=list(old_invariants - new_invariants),
            breaking_changes=breaking,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_from_python(self, file_path: str, ir: SystemArchitectureIR) -> None:
        """Extract architecture elements from a Python file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            tree = ast.parse(source)
        except (SyntaxError, OSError):
            return

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                # Each class becomes a potential entity
                methods = [
                    n.name for n in ast.iter_child_nodes(node)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not n.name.startswith("_")
                ]

                interfaces = []
                if methods:
                    interfaces.append(Interface(
                        name=f"{node.name}_interface",
                        methods=methods,
                    ))

                entity = SystemEntity(
                    name=node.name,
                    type=EntityType.MODULE,
                    interfaces=interfaces,
                )
                ir.entities.append(entity)

                # Check for base classes -> EXTENDS relations
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        ir.relations.append(SystemRelation(
                            source=node.name,
                            target=base.id,
                            type=RelationshipType.EXTENDS,
                        ))
