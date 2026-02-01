"""Data definitions for Pilot B: Grounded QA."""
from dataclasses import dataclass
from typing import List, Tuple

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType

# 1. Corpus Data (Wikipedia Subset Mock)
# Format: (Entity, Attribute, Value, Source)
FACTS = [
    ("France", "capital", "Paris", "wiki_v1"),
    ("France", "population", 67000000, "wiki_v1"),
    ("Paris", "population", 2100000, "wiki_v1"),
    ("Germany", "capital", "Berlin", "wiki_v1"),
    ("Germany", "population", 83000000, "wiki_v1"),
    ("Berlin", "population", 3600000, "wiki_v1"),
    ("Spain", "capital", "Madrid", "wiki_v1"),
    ("Spain", "population", 47000000, "wiki_v1"),
    ("Madrid", "population", 3200000, "wiki_v1"),
    ("Italy", "capital", "Rome", "wiki_v1"),
    ("Italy", "population", 59000000, "wiki_v1"),
    ("Rome", "population", 2800000, "wiki_v1"),

    # Pilot B.1: Conflicting/Ambiguous/Incomplete
    # Convergent (Same fact, different source)
    ("Mars", "moons", 2, "nasa"),
    ("Mars", "moons", 2, "esa"),

    # Divergent (Conflict)
    ("Jupiter", "moons", 79, "textbook_2018"),
    ("Jupiter", "moons", 95, "nasa_2023"),

    # Incomplete (Venus has no moon fact)
    ("Venus", "atmosphere", "CO2", "nasa"),
]

@dataclass
class Question:
    qid: str
    text: str
    q_type: str  # Q1, Q2, Q3
    expected_answer: str | None  # None means ABSTAIN/Unanswerable

QUESTIONS = [
    # Q1: Directly Answerable
    Question("q1_1", "What is the capital of France?", "Q1", "Paris"),
    Question("q1_2", "What is the population of Germany?", "Q1", "83000000"),

    # Q2: Multi-Hop (Country -> Capital -> Population > 3M)
    # Berlin (3.6M) -> Germany
    # Madrid (3.2M) -> Spain
    # Paris (2.1M) -> France (No)
    # Rome (2.8M) -> Italy (No)
    Question("q2_1", "Which country has a capital with population > 3000000?", "Q2", "Germany, Spain"),

    # Q3: Unanswerable
    Question("q3_1", "Is Paris better than Berlin?", "Q3", None),
    Question("q3_2", "What is the GDP of France?", "Q3", None),

    # Pilot B.1 Cases
    # Convergent (should answer 2)
    Question("q_amb_1", "How many moons does Mars have?", "Q1", "2"),

    # Divergent (should abstain)
    Question("q_amb_2", "How many moons does Jupiter have?", "Q1", None),

    # Incomplete (should abstain)
    Question("q_amb_3", "How many moons does Venus have?", "Q1", None),
]

def ingest_corpus() -> TypedGraph:
    """Ingest static facts into a TypedGraph."""
    graph = TypedGraph()

    for entity, attr, val, source in FACTS:
        # Create Entity Node
        # ID strategy: slugify name
        entity_id = entity.lower().replace(" ", "_")
        if entity_id not in graph.nodes:
            graph.add_node(entity_id, NodeType.ENTITY, value={"name": entity})

        # Create Value Node
        # ID strategy: val_entity_attr_source (Must be unique per source now)
        val_str = str(val).lower().replace(" ", "_")
        val_id = f"val_{entity_id}_{attr}_{source}"

        # Determine value type (simple heuristic)
        if isinstance(val, int):
            # We use VALUE type but store numeric in metadata for operations
            graph.add_node(val_id, NodeType.VALUE, value={"value": val, "type": "number", "source": source})
        else:
            graph.add_node(val_id, NodeType.VALUE, value={"value": val, "type": "string", "source": source})

        # Create Edge
        # Has Attribute
        graph.add_edge(
            EdgeType.HAS_ATTRIBUTE,
            entity_id,
            val_id,
            metadata={"attribute": attr, "source": source}
        )

    return graph
