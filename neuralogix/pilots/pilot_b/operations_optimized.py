"""Optimized Operations for Pilot B.2: Scale."""
from __future__ import annotations

from typing import Any, Dict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OperationSignature
from neuralogix.pilots.pilot_b.data_scale import Index

# Global index reference (in real system, this would be injected via Context)
# For this pilot, we'll set it at runtime
GLOBAL_INDEX: Index | None = None

def set_global_index(index: Index):
    global GLOBAL_INDEX
    GLOBAL_INDEX = index

def _apply_lookup_indexed(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Lookup an attribute of an entity using O(1) Index.

    Returns a VALUE_SET node containing all found values.
    """
    if GLOBAL_INDEX is None:
        raise RuntimeError("Global Index not initialized")

    entity_id = inputs["entity"]
    attr_name = inputs["attribute"]
    result_id = inputs.get("result_id", f"set_{entity_id}_{attr_name}")

    # Verify entity (Index lookup handles non-existence gracefully, but good to check graph)
    if entity_id not in graph.nodes:
        raise ValueError(f"Entity {entity_id} not found")

    # O(1) Lookup
    found_val_ids = GLOBAL_INDEX.get(entity_id, attr_name)

    # Create VALUE_SET node
    if result_id not in graph.nodes:
        graph.add_node(result_id, NodeType.VALUE_SET, value={"count": len(found_val_ids)})

    # Add CONTAINS edges
    # Note: The edges might already exist if we re-run, but graph.add_edge handles that or we don't care for this pilot
    for val_id in found_val_ids:
        # Check if edge exists to avoid duplicates? Graph IR allows multiple edges usually unless constrained
        # Simple check
        exists = False
        for edge in graph.edges:
            if (edge.edge_type == EdgeType.CONTAINS and
                edge.source == result_id and
                edge.target == val_id):
                exists = True
                break
        if not exists:
            graph.add_edge(EdgeType.CONTAINS, result_id, val_id)

    return {"value_set": result_id}

OP_LOOKUP_INDEXED = OperationSignature(
    name="lookup_indexed",
    input_types=[NodeType.ENTITY],
    output_type=NodeType.VALUE_SET,
    apply=_apply_lookup_indexed,
    description="Indexed Lookup: entity.attr -> value_set (O(1))"
)
