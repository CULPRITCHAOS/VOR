"""Predictive Operations for Pilot D."""
from __future__ import annotations

from typing import Any, Dict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OperationSignature
from neuralogix.core.checkers.base import CheckStatus

# Global reference to World Model
WORLD_MODEL: Any = None

def set_world_model(model: Any):
    global WORLD_MODEL
    WORLD_MODEL = model

def _apply_predict_next(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Predict and propose the next state.

    Args:
        inputs: {"entity": entity_id, "current_value": value_node_id}

    Returns:
        {"prediction": proposed_value_node_id, "confidence": float}
    """
    if WORLD_MODEL is None:
        raise RuntimeError("World Model not initialized")

    entity_id = inputs["entity"]
    current_val_id = inputs["current_value"]

    # Get current value string
    current_node = graph.nodes[current_val_id]
    current_state = str(current_node.value.get("value"))

    # Ask World Model
    predicted_state = WORLD_MODEL.predict_next(current_state)

    # Create PROPOSAL node (using VALUE type but marked as proposal)
    # ID: prop_val_ENTITY_NEXT
    # Note: In a real system, we might have a specific PROPOSAL type
    # For now, we use VALUE with metadata.

    prop_id = f"prop_{entity_id}_{predicted_state}"
    if prop_id not in graph.nodes:
        graph.add_node(
            prop_id,
            NodeType.VALUE,
            value={
                "value": predicted_state,
                "type": "string",
                "origin": "prediction"
            }
        )

    return {"prediction": prop_id, "state": predicted_state}

OP_PREDICT_NEXT = OperationSignature(
    name="predict_next",
    input_types=[NodeType.ENTITY, NodeType.VALUE],
    output_type=NodeType.VALUE,
    apply=_apply_predict_next,
    description="Propose next state based on world model"
)
