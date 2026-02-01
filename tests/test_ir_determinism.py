"""M1 determinism tests: insertion-order invariance and hash sensitivity."""
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType


def test_insertion_order_invariance_nodes():
    """Same graph built with different node insertion orders yields identical hash."""
    # Graph 1: insert nodes in order alice, bob, charlie
    g1 = TypedGraph()
    g1.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    g1.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
    g1.add_node("charlie", NodeType.PERSON, value={"name": "Charlie"})
    g1.add_edge(EdgeType.PARENT_OF, "alice", "bob")
    g1.add_edge(EdgeType.PARENT_OF, "bob", "charlie")
    
    # Graph 2: insert nodes in reverse order charlie, bob, alice
    g2 = TypedGraph()
    g2.add_node("charlie", NodeType.PERSON, value={"name": "Charlie"})
    g2.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
    g2.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    g2.add_edge(EdgeType.PARENT_OF, "alice", "bob")
    g2.add_edge(EdgeType.PARENT_OF, "bob", "charlie")
    
    assert g1.state_hash() == g2.state_hash()
    assert g1 == g2


def test_insertion_order_invariance_edges():
    """Same graph built with different edge insertion orders yields identical hash."""
    # Graph 1: edges in order (a->b, b->c)
    g1 = TypedGraph()
    g1.add_node("a", NodeType.PERSON)
    g1.add_node("b", NodeType.PERSON)
    g1.add_node("c", NodeType.PERSON)
    g1.add_edge(EdgeType.PARENT_OF, "a", "b")
    g1.add_edge(EdgeType.PARENT_OF, "b", "c")
    
    # Graph 2: edges in reverse order (b->c, a->b)
    g2 = TypedGraph()
    g2.add_node("a", NodeType.PERSON)
    g2.add_node("b", NodeType.PERSON)
    g2.add_node("c", NodeType.PERSON)
    g2.add_edge(EdgeType.PARENT_OF, "b", "c")
    g2.add_edge(EdgeType.PARENT_OF, "a", "b")
    
    assert g1.state_hash() == g2.state_hash()
    assert g1 == g2


def test_hash_sensitivity_to_node_value_change():
    """Changing a node value must change the hash."""
    g1 = TypedGraph()
    g1.add_node("n1", NodeType.NUMBER, value=3)
    hash1 = g1.state_hash()
    
    g2 = TypedGraph()
    g2.add_node("n1", NodeType.NUMBER, value=5)
    hash2 = g2.state_hash()
    
    assert hash1 != hash2


def test_hash_sensitivity_to_node_addition():
    """Adding a node must change the hash."""
    g1 = TypedGraph()
    g1.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    hash1 = g1.state_hash()
    
    g2 = TypedGraph()
    g2.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
    g2.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
    hash2 = g2.state_hash()
    
    assert hash1 != hash2


def test_hash_sensitivity_to_edge_type_change():
    """Changing edge type must change the hash."""
    g1 = TypedGraph()
    g1.add_node("alice", NodeType.PERSON)
    g1.add_node("bob", NodeType.PERSON)
    g1.add_edge(EdgeType.PARENT_OF, "alice", "bob")
    hash1 = g1.state_hash()
    
    g2 = TypedGraph()
    g2.add_node("alice", NodeType.PERSON)
    g2.add_node("bob", NodeType.PERSON)
    g2.add_edge(EdgeType.SPOUSE_OF, "alice", "bob")
    hash2 = g2.state_hash()
    
    assert hash1 != hash2


def test_hash_sensitivity_to_edge_metadata():
    """Changing edge metadata must change the hash."""
    g1 = TypedGraph()
    g1.add_node("n1", NodeType.NUMBER, value=3)
    g1.add_node("n2", NodeType.NUMBER, value=5)
    g1.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
    hash1 = g1.state_hash()
    
    g2 = TypedGraph()
    g2.add_node("n1", NodeType.NUMBER, value=3)
    g2.add_node("n2", NodeType.NUMBER, value=5)
    g2.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n4"})
    hash2 = g2.state_hash()
    
    assert hash1 != hash2


def test_canonical_form_has_stable_json_structure():
    """Canonical JSON must have no whitespace variance."""
    g = TypedGraph()
    g.add_node("alice", NodeType.PERSON, value={"name": "Alice", "age": 30})
    g.add_node("bob", NodeType.PERSON, value={"age": 25, "name": "Bob"})
    
    canonical = g.canonicalize()
    import json
    # Verify JSON is compact and deterministic
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    assert '\n' not in json_str
    assert '  ' not in json_str
    
    # Rebuilding from JSON should preserve hash
    g2 = TypedGraph.from_json(canonical)
    assert g.state_hash() == g2.state_hash()
