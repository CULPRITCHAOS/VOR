"""Pilot C: Reproducible Pipeline Logic."""
from __future__ import annotations

import hashlib
import json
import sys
import platform
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType, EdgeType
from neuralogix.core.reasoning.engine import ReasoningEngine
from neuralogix.core.receipts.logger import ReceiptLogger

# --- Pipeline Receipts Extensions (Conceptual) ---
# We reuse the core ReceiptEvent but enrich metadata for PipelineStart/End

def get_env_hash() -> str:
    """Capture environment fingerprint."""
    env_data = {
        "python": sys.version,
        "platform": platform.platform(),
        # In real system, would include pip freeze hash
    }
    s = json.dumps(env_data, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def get_input_hash(data: List[Dict]) -> str:
    """Capture input data fingerprint."""
    s = json.dumps(data, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# --- Pipeline Operations (Mock ETL) ---

def ingest_csv(graph: TypedGraph, data: List[Dict]) -> None:
    """Mock Ingest: List of Dicts -> Graph."""
    for row in data:
        # ID: row_id
        row_id = f"row_{row['id']}"
        graph.add_node(row_id, NodeType.ENTITY, value={"type": "Row"})

        for k, v in row.items():
            if k == "id": continue
            # Value node
            val_id = f"val_{row_id}_{k}"
            val_type = "number" if isinstance(v, (int, float)) else "string"
            graph.add_node(val_id, NodeType.VALUE, value={"value": v, "type": val_type})

            graph.add_edge(EdgeType.HAS_ATTRIBUTE, row_id, val_id, metadata={"attribute": k})

def transform_normalize(graph: TypedGraph, attribute: str, factor: float) -> None:
    """Mock Transform: Multiply numeric attribute by factor."""
    # Find all values for attribute
    for edge in graph.edges:
        if edge.edge_type == EdgeType.HAS_ATTRIBUTE and edge.metadata.get("attribute") == attribute:
            val_node = graph.nodes[edge.target]
            if val_node.value.get("type") == "number":
                # In-place update for this mock (Deterministic)
                val_node.value["value"] *= factor

def analyze_summary(graph: TypedGraph, attribute: str) -> float:
    """Mock Analysis: Sum of attribute."""
    total = 0.0
    for edge in graph.edges:
        if edge.edge_type == EdgeType.HAS_ATTRIBUTE and edge.metadata.get("attribute") == attribute:
            val_node = graph.nodes[edge.target]
            if val_node.value.get("type") == "number":
                total += val_node.value["value"]
    return total

# --- Pipeline Runner ---

class ReproduciblePipeline:
    def __init__(self, receipt_path: str):
        self.logger = ReceiptLogger(receipt_path)
        self.engine = ReasoningEngine(logger=self.logger, checkers_enabled=True)
        self.graph = TypedGraph()

    def run(self, input_data: List[Dict]) -> float:
        """Run the pipeline."""
        # 1. Pipeline Start Receipt
        env_hash = get_env_hash()
        input_hash = get_input_hash(input_data)

        # We manually log a "start" event using the engine's logger mechanism
        # by creating a mock "start" operation or just logging custom notes in first op
        # For strictness, let's treat "Ingest" as the start.

        # 2. Ingest
        # We wrap ingest in a verifiable step?
        # Ideally ingest is an operation. For Pilot C simplicity, we do python-side ingest
        # but log the state hash after.
        ingest_csv(self.graph, input_data)

        # Log Ingest Receipt (Mock op)
        # In real system, this would be engine.step("ingest", ...)
        # We'll stick to python logic for now, but log a marker.
        # Actually, let's make a dummy engine step for logging.
        # Use existing 'lookup' or similar? No, let's just proceed.
        # The goal is "Deterministic Replay".

        # 3. Transform
        transform_normalize(self.graph, "value", 1.5)

        # 4. Analyze
        result = analyze_summary(self.graph, "value")

        # 5. Pipeline End
        # Log final hash
        final_hash = self.graph.state_hash()

        # Return result and signatures
        return result, env_hash, input_hash, final_hash
