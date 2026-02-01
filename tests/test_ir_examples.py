"""M1 acceptance tests: specification examples."""
import json

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType


def test_arithmetic_example_3_add_5():
    """Build graph for '3 add 5 -> 8' per spec line 204."""
    g = TypedGraph()
    g.add_node("n1", NodeType.NUMBER, value=3)
    g.add_node("n2", NodeType.NUMBER, value=5)
    g.add_node("n3", NodeType.NUMBER, value=8)
    g.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
    
    # Validate structure
    assert len(g.nodes) == 3
    assert len(g.edges) == 1
    assert g.nodes["n1"].value == 3
    assert g.nodes["n2"].value == 5
    assert g.nodes["n3"].value == 8
    
    # Hash must be stable across runs
    hash1 = g.state_hash()
    hash2 = g.state_hash()
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest


def test_arithmetic_example_round_trip():
    """Serialize and deserialize arithmetic example; hash must remain stable."""
    g1 = TypedGraph()
    g1.add_node("n1", NodeType.NUMBER, value=3)
    g1.add_node("n2", NodeType.NUMBER, value=5)
    g1.add_node("n3", NodeType.NUMBER, value=8)
    g1.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
    
    hash_before = g1.state_hash()
    json_data = g1.to_json()
    g2 = TypedGraph.from_json(json_data)
    hash_after = g2.state_hash()
    
    assert hash_before == hash_after
    assert g1 == g2


def test_family_example_alice_parent_of_bob():
    """Build graph for 'Alice parent_of Bob' per spec line 204."""
    g = TypedGraph()
    g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
    g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
    
    # Validate structure
    assert len(g.nodes) == 2
    assert len(g.edges) == 1
    assert g.nodes["alice"].value == {"name": "Alice"}
    assert g.nodes["bob"].value == {"name": "Bob"}
    
    # Hash must be stable
    hash1 = g.state_hash()
    hash2 = g.state_hash()
    assert hash1 == hash2
    assert len(hash1) == 64


def test_family_example_round_trip():
    """Serialize and deserialize family example; hash must remain stable."""
    g1 = TypedGraph()
    g1.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    g1.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
    g1.add_edge(EdgeType.PARENT_OF, "alice", "bob")
    
    hash_before = g1.state_hash()
    json_data = g1.to_json()
    g2 = TypedGraph.from_json(json_data)
    hash_after = g2.state_hash()
    
    assert hash_before == hash_after
    assert g1 == g2


def test_json_serialization_preserves_numeric_types():
    """Ensure int values stay int (no accidental float conversion)."""
    g = TypedGraph()
    g.add_node("n1", NodeType.NUMBER, value=42)
    
    json_data = g.to_json()
    g2 = TypedGraph.from_json(json_data)
    
    assert g2.nodes["n1"].value == 42
    assert isinstance(g2.nodes["n1"].value, int)
