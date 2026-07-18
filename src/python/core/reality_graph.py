"""
AXIMA Reality Graph — Persistent knowledge graph for the cognitive system.

Stores: Users, Projects, Goals, Tasks, Facts, Concepts, Theories.
Relates them: depends_on, contains, supports, contradicts, extends.
Persists to JSON. Lightweight. No external dependencies.

Usage:
    from core.reality_graph import get_reality_graph

    graph = get_reality_graph()
    
    # Create nodes
    user = graph.add_node("user", "ghias", {"role": "architect"})
    goal = graph.add_node("goal", "Fix math router", {"priority": 1})
    
    # Create relationships
    graph.add_edge(user, goal, "owns")
    
    # Query
    goals = graph.find_nodes(node_type="goal")
    related = graph.neighbors(user, relation="owns")
    
    # Persistence
    graph.save()  # → ~/.axima/reality_graph.json
"""

import os
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Set, Tuple
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# NODE TYPES
# ═══════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    """Types of nodes in the reality graph."""
    USER = "user"
    PROJECT = "project"
    GOAL = "goal"
    TASK = "task"
    FACT = "fact"
    CONCEPT = "concept"
    THEORY = "theory"
    MEMORY = "memory"
    SESSION = "session"


# ═══════════════════════════════════════════════════════════════
# RELATIONSHIP TYPES
# ═══════════════════════════════════════════════════════════════

class RelationType(str, Enum):
    """Types of edges between nodes."""
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    EXTENDS = "extends"
    OWNS = "owns"
    CREATED = "created"
    BLOCKED_BY = "blocked_by"
    RELATES_TO = "relates_to"
    DERIVED_FROM = "derived_from"


# ═══════════════════════════════════════════════════════════════
# GRAPH PRIMITIVES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Node:
    """A node in the reality graph."""
    id: str
    node_type: str                      # NodeType value
    label: str                          # Human-readable name
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.node_type,
            "label": self.label,
            "properties": self.properties,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Node':
        return cls(
            id=data["id"],
            node_type=data["type"],
            label=data["label"],
            properties=data.get("properties", {}),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )


@dataclass
class Edge:
    """A directed relationship between two nodes."""
    source_id: str
    target_id: str
    relation: str                       # RelationType value
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0                 # Strength of relationship
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation": self.relation,
            "properties": self.properties,
            "weight": self.weight,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Edge':
        return cls(
            source_id=data["source"],
            target_id=data["target"],
            relation=data["relation"],
            properties=data.get("properties", {}),
            weight=data.get("weight", 1.0),
            created_at=data.get("created_at", 0),
        )


# ═══════════════════════════════════════════════════════════════
# REALITY GRAPH
# ═══════════════════════════════════════════════════════════════

class RealityGraph:
    """The AXIMA Reality Graph — persistent knowledge structure.
    
    Lightweight graph with typed nodes and relationships.
    Persists to JSON file. No external dependencies.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._nodes: Dict[str, Node] = {}
        self._edges: List[Edge] = []
        # Indexes for fast lookup
        self._type_index: Dict[str, Set[str]] = {}     # type → {node_ids}
        self._outgoing: Dict[str, List[int]] = {}      # node_id → [edge_indices]
        self._incoming: Dict[str, List[int]] = {}      # node_id → [edge_indices]

        # Storage
        self._storage_path = storage_path or os.path.expanduser("~/.axima/reality_graph.json")
        self._dirty = False

        # Try to load existing graph
        self._load()

    # ─── NODE OPERATIONS ───

    def add_node(self, node_type: str, label: str,
                 properties: Optional[Dict] = None,
                 node_id: Optional[str] = None) -> str:
        """Add a node to the graph. Returns node ID."""
        nid = node_id or str(uuid.uuid4())[:8]
        node = Node(
            id=nid,
            node_type=node_type,
            label=label,
            properties=properties or {},
        )
        self._nodes[nid] = node
        self._type_index.setdefault(node_type, set()).add(nid)
        self._dirty = True
        return nid

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def update_node(self, node_id: str, properties: Optional[Dict] = None,
                    label: Optional[str] = None) -> bool:
        """Update a node's properties or label."""
        node = self._nodes.get(node_id)
        if not node:
            return False
        if properties:
            node.properties.update(properties)
        if label:
            node.label = label
        node.updated_at = time.time()
        self._dirty = True
        return True

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        if node_id not in self._nodes:
            return False
        node = self._nodes.pop(node_id)
        self._type_index.get(node.node_type, set()).discard(node_id)
        # Remove edges involving this node
        self._edges = [e for e in self._edges
                      if e.source_id != node_id and e.target_id != node_id]
        self._rebuild_edge_index()
        self._dirty = True
        return True

    def find_nodes(self, node_type: Optional[str] = None,
                   label_contains: Optional[str] = None,
                   **prop_filters) -> List[Node]:
        """Find nodes by type, label, or properties."""
        if node_type:
            ids = self._type_index.get(node_type, set())
            candidates = [self._nodes[nid] for nid in ids if nid in self._nodes]
        else:
            candidates = list(self._nodes.values())

        if label_contains:
            lc = label_contains.lower()
            candidates = [n for n in candidates if lc in n.label.lower()]

        if prop_filters:
            filtered = []
            for node in candidates:
                match = all(
                    node.properties.get(k) == v
                    for k, v in prop_filters.items()
                )
                if match:
                    filtered.append(node)
            candidates = filtered

        return candidates

    # ─── EDGE OPERATIONS ───

    def add_edge(self, source_id: str, target_id: str, relation: str,
                 properties: Optional[Dict] = None, weight: float = 1.0) -> bool:
        """Add a directed edge between two nodes."""
        if source_id not in self._nodes or target_id not in self._nodes:
            return False
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            properties=properties or {},
            weight=weight,
        )
        idx = len(self._edges)
        self._edges.append(edge)
        self._outgoing.setdefault(source_id, []).append(idx)
        self._incoming.setdefault(target_id, []).append(idx)
        self._dirty = True
        return True

    def remove_edge(self, source_id: str, target_id: str,
                    relation: Optional[str] = None) -> int:
        """Remove edges between source and target. Returns count removed."""
        before = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (e.source_id == source_id and e.target_id == target_id
                    and (relation is None or e.relation == relation))
        ]
        removed = before - len(self._edges)
        if removed:
            self._rebuild_edge_index()
            self._dirty = True
        return removed

    def neighbors(self, node_id: str, relation: Optional[str] = None,
                  direction: str = "out") -> List[Tuple[str, str, Edge]]:
        """Get neighbors of a node.
        
        Returns: [(neighbor_id, relation, edge), ...]
        direction: "out" | "in" | "both"
        """
        results = []
        if direction in ("out", "both"):
            for idx in self._outgoing.get(node_id, []):
                edge = self._edges[idx]
                if relation is None or edge.relation == relation:
                    results.append((edge.target_id, edge.relation, edge))
        if direction in ("in", "both"):
            for idx in self._incoming.get(node_id, []):
                edge = self._edges[idx]
                if relation is None or edge.relation == relation:
                    results.append((edge.source_id, edge.relation, edge))
        return results

    def find_edges(self, relation: Optional[str] = None,
                   source_type: Optional[str] = None,
                   target_type: Optional[str] = None) -> List[Edge]:
        """Find edges by relation and/or node types."""
        results = []
        for edge in self._edges:
            if relation and edge.relation != relation:
                continue
            if source_type:
                src = self._nodes.get(edge.source_id)
                if not src or src.node_type != source_type:
                    continue
            if target_type:
                tgt = self._nodes.get(edge.target_id)
                if not tgt or tgt.node_type != target_type:
                    continue
            results.append(edge)
        return results

    # ─── TRAVERSAL ───

    def path_between(self, start_id: str, end_id: str,
                     max_depth: int = 5) -> Optional[List[str]]:
        """BFS to find path between two nodes. Returns node IDs or None."""
        if start_id not in self._nodes or end_id not in self._nodes:
            return None
        if start_id == end_id:
            return [start_id]

        visited = {start_id}
        queue = [(start_id, [start_id])]

        for _ in range(max_depth * len(self._nodes)):
            if not queue:
                break
            current, path = queue.pop(0)
            for neighbor_id, _, _ in self.neighbors(current, direction="both"):
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return None

    # ─── PERSISTENCE ───

    def save(self):
        """Save graph to disk."""
        os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
        }
        with open(self._storage_path, 'w') as f:
            json.dump(data, f, indent=2)
        self._dirty = False

    def _load(self):
        """Load graph from disk if exists."""
        if not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            for node_data in data.get("nodes", []):
                node = Node.from_dict(node_data)
                self._nodes[node.id] = node
                self._type_index.setdefault(node.node_type, set()).add(node.id)
            for edge_data in data.get("edges", []):
                edge = Edge.from_dict(edge_data)
                self._edges.append(edge)
            self._rebuild_edge_index()
        except (json.JSONDecodeError, IOError, KeyError):
            pass  # Start fresh if corrupt

    def _rebuild_edge_index(self):
        """Rebuild edge indexes from edge list."""
        self._outgoing.clear()
        self._incoming.clear()
        for idx, edge in enumerate(self._edges):
            self._outgoing.setdefault(edge.source_id, []).append(idx)
            self._incoming.setdefault(edge.target_id, []).append(idx)

    # ─── STATS ───

    def stats(self) -> Dict[str, Any]:
        """Graph statistics."""
        return {
            "nodes": len(self._nodes),
            "edges": len(self._edges),
            "types": {t: len(ids) for t, ids in self._type_index.items()},
            "dirty": self._dirty,
            "storage": self._storage_path,
        }

    def clear(self):
        """Clear the entire graph."""
        self._nodes.clear()
        self._edges.clear()
        self._type_index.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._dirty = True


# ═══════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════

_graph: Optional[RealityGraph] = None


def get_reality_graph(storage_path: Optional[str] = None) -> RealityGraph:
    """Get the global reality graph instance."""
    global _graph
    if _graph is None:
        _graph = RealityGraph(storage_path=storage_path)
    return _graph
