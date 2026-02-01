"""Typed Graph IR storage."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from neuralogix.core.ir.schema import SCHEMA_VERSION, EdgeType, NodeType


@dataclass(frozen=True)
class Node:
    node_id: str
    node_type: NodeType
    value: Optional[Any] = None


@dataclass(frozen=True)
class Edge:
    edge_type: EdgeType
    source: str
    target: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TypedGraph:
    """Typed graph storage with deterministic serialization."""

    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node_id: str, node_type: NodeType, value: Optional[Any] = None) -> Node:
        if node_id in self.nodes:
            raise ValueError(f"Node '{node_id}' already exists")
        node = Node(node_id=node_id, node_type=node_type, value=value)
        self.nodes[node_id] = node
        return node

    def get_node(self, node_id: str) -> Node:
        """Get node by ID."""
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found")
        return self.nodes[node_id]

    def find_edges(
        self,
        edge_type: Optional[EdgeType] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
    ) -> List[Edge]:
        """Find edges matching filters."""
        return [
            e for e in self.edges
            if (edge_type is None or e.edge_type == edge_type)
            and (source is None or e.source == source)
            and (target is None or e.target == target)
        ]

    def add_edge(
        self,
        edge_type: EdgeType,
        source: str,
        target: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Edge:
        if source not in self.nodes or target not in self.nodes:
            raise KeyError("Both source and target nodes must exist before adding an edge")
        edge = Edge(edge_type=edge_type, source=source, target=target, metadata=metadata)
        self.edges.append(edge)
        return edge

    def to_json(self) -> Dict[str, Any]:
        nodes_sorted = [self.nodes[node_id] for node_id in sorted(self.nodes)]
        edges_sorted = sorted(
            self.edges,
            key=lambda edge: (edge.edge_type.value, edge.source, edge.target),
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "nodes": [asdict(node) for node in nodes_sorted],
            "edges": [asdict(edge) for edge in edges_sorted],
        }

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "TypedGraph":
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported schema version")
        graph = cls()
        for node_data in payload.get("nodes", []):
            graph.add_node(
                node_id=node_data["node_id"],
                node_type=NodeType(node_data["node_type"]),
                value=node_data.get("value"),
            )
        for edge_data in payload.get("edges", []):
            graph.add_edge(
                edge_type=EdgeType(edge_data["edge_type"]),
                source=edge_data["source"],
                target=edge_data["target"],
                metadata=edge_data.get("metadata"),
            )
        return graph

    def canonicalize(self) -> Dict[str, Any]:
        """Return canonical dict representation with deterministic ordering."""
        return self.to_json()

    def state_hash(self) -> str:
        """Compute SHA-256 hash of canonical JSON representation.
        
        Returns:
            64-character hex string representing the graph state.
        """
        canonical = self.canonicalize()
        canonical_json = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def __eq__(self, other: object) -> bool:
        """Compare graphs based on canonical form."""
        if not isinstance(other, TypedGraph):
            return NotImplemented
        return self.state_hash() == other.state_hash()

    def __repr__(self) -> str:
        return f"TypedGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, hash={self.state_hash()[:8]}...)"
