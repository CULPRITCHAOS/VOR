"""Tests for reasoning operations."""
import pytest

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OPERATION_REGISTRY


class TestArithmeticAdd:
    """Tests for add operation."""

    def test_add_valid_numbers(self):
        """Add operation should compute sum correctly."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=3)
        g.add_node("n2", NodeType.NUMBER, value=5)
        
        op = OPERATION_REGISTRY.get("add")
        result = op.apply(g, {"a": "n1", "b": "n2", "result_id": "sum"})
        
        assert result["result"] == "sum"
        assert "sum" in g.nodes
        assert g.nodes["sum"].value == 8
        
        # Check edge was added
        assert any(e.edge_type == EdgeType.ADD and e.source == "n1" and e.target == "n2" 
                  for e in g.edges)

    def test_add_invalid_types_fails(self):
        """Add with non-NUMBER types should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        
        op = OPERATION_REGISTRY.get("add")
        with pytest.raises(ValueError, match="add requires NUMBER inputs"):
            op.apply(g, {"a": "alice", "b": "bob"})

    def test_add_missing_node_fails(self):
        """Add with missing node should fail."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=3)
        
        op = OPERATION_REGISTRY.get("add")
        with pytest.raises(KeyError):
            op.apply(g, {"a": "n1", "b": "nonexistent"})


class TestArithmeticGreaterThan:
    """Tests for greater_than operation."""

    def test_greater_than_true(self):
        """greater_than should return True when a > b."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=10)
        g.add_node("n2", NodeType.NUMBER, value=5)
        
        op = OPERATION_REGISTRY.get("greater_than")
        result = op.apply(g, {"a": "n1", "b": "n2", "result_id": "gt"})
        
        assert result["result"] == "gt"
        assert g.nodes["gt"].value is True

    def test_greater_than_false(self):
        """greater_than should return False when a <= b."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=3)
        g.add_node("n2", NodeType.NUMBER, value=5)
        
        op = OPERATION_REGISTRY.get("greater_than")
        result = op.apply(g, {"a": "n1", "b": "n2", "result_id": "gt"})
        
        assert g.nodes["gt"].value is False

    def test_greater_than_invalid_types_fails(self):
        """greater_than with non-NUMBER types should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON)
        g.add_node("bob", NodeType.PERSON)
        
        op = OPERATION_REGISTRY.get("greater_than")
        with pytest.raises(ValueError, match="greater_than requires NUMBER inputs"):
            op.apply(g, {"a": "alice", "b": "bob"})


class TestDeriveGrandparent:
    """Tests for derive_grandparent operation."""

    def test_derive_grandparent_valid_chain(self):
        """derive_grandparent should find valid parent_of chain."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_node("carol", NodeType.PERSON, value={"name": "Carol"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        g.add_edge(EdgeType.PARENT_OF, "bob", "carol")
        
        op = OPERATION_REGISTRY.get("derive_grandparent")
        result = op.apply(g, {"grandparent": "alice", "grandchild": "carol"})
        
        assert "result" in result
        relation_id = result["result"]
        assert relation_id in g.nodes
        assert g.nodes[relation_id].node_type == NodeType.RELATION
        assert g.nodes[relation_id].value["type"] == "grandparent_of"
        assert result["intermediate"] == "bob"

    def test_derive_grandparent_no_chain_fails(self):
        """derive_grandparent should fail if no parent_of chain exists."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON)
        g.add_node("bob", NodeType.PERSON)
        g.add_node("carol", NodeType.PERSON)
        # No edges
        
        op = OPERATION_REGISTRY.get("derive_grandparent")
        with pytest.raises(ValueError, match="No parent_of chain found"):
            op.apply(g, {"grandparent": "alice", "grandchild": "carol"})

    def test_derive_grandparent_invalid_types_fails(self):
        """derive_grandparent with non-PERSON types should fail."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=1)
        g.add_node("n2", NodeType.NUMBER, value=2)
        
        op = OPERATION_REGISTRY.get("derive_grandparent")
        with pytest.raises(ValueError, match="derive_grandparent requires PERSON inputs"):
            op.apply(g, {"grandparent": "n1", "grandchild": "n2"})


class TestOperationRegistry:
    """Tests for operation registry."""

    def test_registry_lists_builtins(self):
        """Registry should list all built-in operations."""
        ops = OPERATION_REGISTRY.list_operations()
        
        assert "add" in ops
        assert "greater_than" in ops
        assert "derive_grandparent" in ops

    def test_registry_get_operation(self):
        """Registry should retrieve operation by name."""
        op = OPERATION_REGISTRY.get("add")
        
        assert op.name == "add"
        assert op.input_types == [NodeType.NUMBER, NodeType.NUMBER]
        assert op.output_type == NodeType.NUMBER

    def test_registry_get_unknown_fails(self):
        """Registry should raise KeyError for unknown operation."""
        with pytest.raises(KeyError):
            OPERATION_REGISTRY.get("unknown_op")
