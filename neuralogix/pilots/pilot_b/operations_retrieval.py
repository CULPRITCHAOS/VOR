"""Retrieval Operations for Pilot B.3."""
from __future__ import annotations

from typing import Any, Dict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OperationSignature
from neuralogix.pilots.pilot_b.retrieval import MockEmbeddingRetriever, RetrievedFact

# Global retriever reference
RETRIEVER: MockEmbeddingRetriever | None = None

def set_retriever(retriever: MockEmbeddingRetriever):
    global RETRIEVER
    RETRIEVER = retriever

def _apply_retrieve_candidates(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve candidate facts and add to graph.

    Args:
        inputs: {"query": str}

    Returns:
        {"count": int} (number of facts added)
    """
    if RETRIEVER is None:
        raise RuntimeError("Retriever not initialized")

    query = inputs["query"]
    facts = RETRIEVER.retrieve(query, k=5)

    added_count = 0
    for fact in facts:
        # Materialize fact into graph
        # 1. Entity
        entity_id = fact.entity.lower().replace(" ", "_")
        if entity_id not in graph.nodes:
            graph.add_node(entity_id, NodeType.ENTITY, value={"name": fact.entity})

        # 2. Value
        val_str = str(fact.value).lower().replace(" ", "_")
        val_id = f"val_{entity_id}_{fact.attribute}_{fact.source}"

        # Check if value node exists, if not create
        if val_id not in graph.nodes:
            if isinstance(fact.value, int):
                graph.add_node(val_id, NodeType.VALUE, value={"value": fact.value, "type": "number", "source": fact.source})
            else:
                graph.add_node(val_id, NodeType.VALUE, value={"value": fact.value, "type": "string", "source": fact.source})

        # 3. Edge
        # Add edge (idempotent logic ideally, graph.add_edge allows dupes unless we check)
        # We'll just add it. The index/lookup logic handles dupes or multiple paths.
        graph.add_edge(
            EdgeType.HAS_ATTRIBUTE,
            entity_id,
            val_id,
            metadata={"attribute": fact.attribute, "source": fact.source, "retrieval_score": fact.score}
        )
        added_count += 1

    return {"count": added_count}

OP_RETRIEVE = OperationSignature(
    name="retrieve_candidates",
    input_types=[], # No node inputs, pure context/query input
    output_type=NodeType.OPERATION, # Dummy output type
    apply=_apply_retrieve_candidates,
    description="Retrieve facts from latent store -> Graph"
)
