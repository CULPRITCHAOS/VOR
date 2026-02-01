"""Tests for TypeChecker."""
import pytest

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.checkers.type_checker import TypeChecker
from neuralogix.core.checkers.base import CheckStatus


class TestTypeCheckerValid:
    """Tests for valid graphs that should pass type checking."""

    def test_arithmetic_example_validates(self):
        """M1 arithmetic example (3 + 5 -> 8) should validate OK."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=3)
        g.add_node("n2", NodeType.NUMBER, value=5)
        g.add_node("n3", NodeType.NUMBER, value=8)
        g.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0

    def test_family_example_validates(self):
        """M1 family example (Alice parent_of Bob) should validate OK."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0

    def test_empty_graph_validates(self):
        """Empty graph should validate OK."""
        g = TypedGraph()
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0


class TestTypeCheckerInvalidNodes:
    """Tests for invalid node types."""

    def test_invalid_node_type_fails(self):
        """Invalid node type should produce HARD_FAIL."""
        g = TypedGraph()
        # Manually construct invalid node (bypass add_node validation)
        from neuralogix.core.ir.graph import Node
        g.nodes["bad"] = Node(node_id="bad", node_type="InvalidType", value=None)
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert len(report.issues) == 1
        assert report.issues[0].code == "INVALID_NODE_TYPE"
        assert "bad" in report.issues[0].node_ids


class TestTypeCheckerInvalidEdges:
    """Tests for invalid edge types and constraints."""

    def test_invalid_edge_type_fails(self):
        """Invalid edge type should produce HARD_FAIL."""
        g = TypedGraph()
        g.add_node("a", NodeType.PERSON)
        g.add_node("b", NodeType.PERSON)
        # Manually add invalid edge
        from neuralogix.core.ir.graph import Edge
        g.edges.append(Edge(edge_type="InvalidEdge", source="a", target="b"))
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "INVALID_EDGE_TYPE" for issue in report.issues)

    def test_parent_of_wrong_source_type_fails(self):
        """parent_of with Number source should fail."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=5)
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        # Manually add edge to bypass validation
        from neuralogix.core.ir.graph import Edge
        g.edges.append(Edge(edge_type=EdgeType.PARENT_OF, source="n1", target="alice"))
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "INVALID_EDGE_SOURCE_TYPE" for issue in report.issues)

    def test_parent_of_wrong_target_type_fails(self):
        """parent_of with Number target should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("n1", NodeType.NUMBER, value=5)
        # Manually add edge to bypass validation
        from neuralogix.core.ir.graph import Edge
        g.edges.append(Edge(edge_type=EdgeType.PARENT_OF, source="alice", target="n1"))
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "INVALID_EDGE_TARGET_TYPE" for issue in report.issues)

    def test_add_wrong_types_fails(self):
        """ADD edge with PERSON nodes should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        # Manually add edge to bypass validation
        from neuralogix.core.ir.graph import Edge
        g.edges.append(Edge(edge_type=EdgeType.ADD, source="alice", target="bob"))
        
        checker = TypeChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        # Should have violations for both source and target
        assert len(report.issues) >= 2


class TestTypeCheckerDeterminism:
    """Tests for deterministic validation across insertion orders."""

    def test_validation_deterministic_across_insertion_orders(self):
        """Validation result should be identical regardless of insertion order."""
        # Graph 1: nodes in order a, b, c
        g1 = TypedGraph()
        g1.add_node("a", NodeType.PERSON)
        g1.add_node("b", NodeType.PERSON)
        g1.add_node("c", NodeType.PERSON)
        g1.add_edge(EdgeType.PARENT_OF, "a", "b")
        g1.add_edge(EdgeType.PARENT_OF, "b", "c")
        
        # Graph 2: nodes in reverse order c, b, a
        g2 = TypedGraph()
        g2.add_node("c", NodeType.PERSON)
        g2.add_node("b", NodeType.PERSON)
        g2.add_node("a", NodeType.PERSON)
        g2.add_edge(EdgeType.PARENT_OF, "a", "b")
        g2.add_edge(EdgeType.PARENT_OF, "b", "c")
        
        checker = TypeChecker()
        report1 = checker.check(g1)
        report2 = checker.check(g2)
        
        assert report1.status == report2.status
        assert len(report1.issues) == len(report2.issues)


class TestCheckReportSerialization:
    """Tests for CheckReport JSON serialization."""

    def test_report_to_dict_valid_graph(self):
        """Report for valid graph should serialize correctly."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON)
        g.add_node("bob", NodeType.PERSON)
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        
        checker = TypeChecker()
        report = checker.check(g)
        data = report.to_dict()
        
        assert data["checker"] == "TypeChecker"
        assert data["status"] == "OK"
        assert data["issues"] == []

    def test_report_to_dict_invalid_graph(self):
        """Report for invalid graph should serialize with issue details."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=5)
        g.add_node("alice", NodeType.PERSON)
        from neuralogix.core.ir.graph import Edge
        g.edges.append(Edge(edge_type=EdgeType.PARENT_OF, source="n1", target="alice"))
        
        checker = TypeChecker()
        report = checker.check(g)
        data = report.to_dict()
        
        assert data["checker"] == "TypeChecker"
        assert data["status"] == "HARD_FAIL"
        assert len(data["issues"]) > 0
        assert all("code" in issue for issue in data["issues"])
        assert all("message" in issue for issue in data["issues"])
