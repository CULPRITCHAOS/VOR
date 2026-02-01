"""Operations for Pilot B: Grounded QA."""
from __future__ import annotations

from typing import Any, Dict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OperationSignature


def _apply_lookup(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Lookup an attribute of an entity.

    Returns a VALUE_SET node containing all found values.

    Args:
        inputs: {
            "entity": entity_node_id,
            "attribute": attribute_name
        }
    """
    entity_id = inputs["entity"]
    attr_name = inputs["attribute"]
    result_id = inputs.get("result_id", f"set_{entity_id}_{attr_name}")

    # Verify entity
    if entity_id not in graph.nodes:
        raise ValueError(f"Entity {entity_id} not found")

    # Search for all HAS_ATTRIBUTE edges
    found_val_ids = []
    for edge in graph.edges:
        if (edge.edge_type == EdgeType.HAS_ATTRIBUTE and
            edge.source == entity_id and
            edge.metadata.get("attribute") == attr_name):
            found_val_ids.append(edge.target)

    # Create VALUE_SET node
    # Even if empty (to handle incomplete data gracefully within the pipeline)
    if result_id not in graph.nodes:
        graph.add_node(result_id, NodeType.VALUE_SET, value={"count": len(found_val_ids)})

    # Add CONTAINS edges
    for val_id in found_val_ids:
        graph.add_edge(EdgeType.CONTAINS, result_id, val_id)

    return {"value_set": result_id}


def _apply_filter_gt(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Filter generic values > threshold.

    Args:
        inputs: {
            "value": value_node_id,
            "threshold": number
        }
    """
    val_id = inputs["value"]
    threshold = inputs["threshold"]

    node = graph.nodes[val_id]
    if node.node_type != NodeType.VALUE:
        raise ValueError(f"Expected VALUE node, got {node.node_type}")

    val_data = node.value.get("value")

    if not isinstance(val_data, (int, float)):
        raise ValueError(f"Cannot compare non-numeric value {val_data}")

    result = val_data > threshold

    # Store result in a transient boolean node?
    # Or just return the boolean in outputs for the engine to decide flow?
    # IR operations usually return node IDs.
    # For Pilot B, let's create a Boolean node.

    res_id = f"bool_{val_id}_gt_{threshold}"
    if res_id not in graph.nodes:
        graph.add_node(res_id, NodeType.BOOLEAN, value=result)

    return {"result": res_id, "is_true": result}


# Operation Signatures
OP_LOOKUP = OperationSignature(
    name="lookup",
    input_types=[NodeType.ENTITY],
    output_type=NodeType.VALUE_SET,
    apply=_apply_lookup,
    description="Lookup attribute: entity.attr -> value_set"
)

OP_FILTER_GT = OperationSignature(
    name="filter_gt",
    input_types=[NodeType.VALUE],
    output_type=NodeType.BOOLEAN,
    apply=_apply_filter_gt,
    description="Check if value > threshold"
)

PILOT_B_OPERATIONS = [
    OP_LOOKUP,
    OP_FILTER_GT
]
