"""Data generator for Pilot B.2: Scale & Recall Optimization."""
import random
from typing import Tuple, List, Dict, Any

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType

# Scale Parameters
DEFAULT_SCALE = 10000
ATTRIBUTES = ["population", "gdp", "area", "code"]
SOURCES = ["src_a", "src_b"]

def generate_synthetic_facts(n_entities: int) -> List[Tuple[str, str, Any, str]]:
    """Generate deterministic synthetic facts.

    Format: (Entity, Attribute, Value, Source)
    """
    facts = []
    # Seed random for determinism
    rng = random.Random(42)

    for i in range(n_entities):
        entity_name = f"Entity_{i:05d}"

        # 1. Guaranteed Attribute (Population)
        # Value is deterministic based on ID so we can verify
        pop = 1000 + i
        facts.append((entity_name, "population", pop, "src_gen"))

        # 2. Random Attributes
        if rng.random() > 0.5:
            facts.append((entity_name, "gdp", i * 100, "src_gen"))

        # 3. Conflict Injection (1% chance)
        if rng.random() < 0.01:
            # Create divergence
            facts.append((entity_name, "area", 500, "src_a"))
            facts.append((entity_name, "area", 600, "src_b"))
        else:
            # Create convergence (10% chance)
            if rng.random() < 0.1:
                facts.append((entity_name, "area", 100, "src_a"))
                facts.append((entity_name, "area", 100, "src_b"))

    return facts

class Index:
    """In-memory index for O(1) attribute lookup."""
    def __init__(self):
        # Map (entity_id, attribute_name) -> List[value_node_id]
        self._map: Dict[Tuple[str, str], List[str]] = {}

    def add(self, entity_id: str, attr_name: str, val_id: str):
        key = (entity_id, attr_name)
        if key not in self._map:
            self._map[key] = []
        self._map[key].append(val_id)

    def get(self, entity_id: str, attr_name: str) -> List[str]:
        return self._map.get((entity_id, attr_name), [])

def ingest_large_corpus(n_entities: int = DEFAULT_SCALE) -> Tuple[TypedGraph, Index]:
    """Ingest large synthetic corpus and build index."""
    graph = TypedGraph()
    index = Index()

    facts = generate_synthetic_facts(n_entities)

    for entity, attr, val, source in facts:
        # Create Entity Node
        entity_id = entity.lower().replace(" ", "_")
        if entity_id not in graph.nodes:
            graph.add_node(entity_id, NodeType.ENTITY, value={"name": entity})

        # Create Value Node
        val_str = str(val).lower().replace(" ", "_")
        val_id = f"val_{entity_id}_{attr}_{source}"

        if isinstance(val, int):
            graph.add_node(val_id, NodeType.VALUE, value={"value": val, "type": "number", "source": source})
        else:
            graph.add_node(val_id, NodeType.VALUE, value={"value": val, "type": "string", "source": source})

        # Create Edge
        graph.add_edge(
            EdgeType.HAS_ATTRIBUTE,
            entity_id,
            val_id,
            metadata={"attribute": attr, "source": source}
        )

        # Add to Index
        index.add(entity_id, attr, val_id)

    return graph, index
