"""Tests for ConsistencyChecker."""
import pytest

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.checkers.consistency import ConsistencyChecker
from neuralogix.core.checkers.base import CheckStatus


class TestConsistencyCheckerValid:
    """Tests for valid graphs that should pass consistency checking."""

    def test_arithmetic_example_validates(self):
        """M1 arithmetic example should have no consistency issues."""
        g = TypedGraph()
        g.add_node("n1", NodeType.NUMBER, value=3)
        g.add_node("n2", NodeType.NUMBER, value=5)
        g.add_node("n3", NodeType.NUMBER, value=8)
        g.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0

    def test_family_example_validates(self):
        """M1 family example should have no consistency issues."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0

    def test_acyclic_parent_chain_validates(self):
        """Acyclic parent_of chain should validate OK."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_node("charlie", NodeType.PERSON, value={"name": "Charlie"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        g.add_edge(EdgeType.PARENT_OF, "bob", "charlie")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0

    def test_symmetric_spouse_edges_validate(self):
        """Symmetric spouse_of edges should validate OK."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_edge(EdgeType.SPOUSE_OF, "alice", "bob")
        g.add_edge(EdgeType.SPOUSE_OF, "bob", "alice")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.OK
        assert len(report.issues) == 0


class TestConsistencyCheckerParentCycles:
    """Tests for parent_of cycle detection."""

    def test_self_cycle_fails(self):
        """Self-referential parent_of should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "alice")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "PARENT_OF_CYCLE" for issue in report.issues)
        assert any("alice" in issue.node_ids for issue in report.issues)

    def test_two_node_cycle_fails(self):
        """Two-node parent_of cycle should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_edge(EdgeType.PARENT_OF, "alice", "bob")
        g.add_edge(EdgeType.PARENT_OF, "bob", "alice")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "PARENT_OF_CYCLE" for issue in report.issues)

    def test_three_node_cycle_fails(self):
        """Three-node parent_of cycle should fail."""
        g = TypedGraph()
        g.add_node("a", NodeType.PERSON)
        g.add_node("b", NodeType.PERSON)
        g.add_node("c", NodeType.PERSON)
        g.add_edge(EdgeType.PARENT_OF, "a", "b")
        g.add_edge(EdgeType.PARENT_OF, "b", "c")
        g.add_edge(EdgeType.PARENT_OF, "c", "a")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "PARENT_OF_CYCLE" for issue in report.issues)


class TestConsistencyCheckerSpouseSymmetry:
    """Tests for spouse_of symmetry checking."""

    def test_asymmetric_spouse_fails(self):
        """Asymmetric spouse_of should fail."""
        g = TypedGraph()
        g.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        g.add_node("bob", NodeType.PERSON, value={"name": "Bob"})
        g.add_edge(EdgeType.SPOUSE_OF, "alice", "bob")
        # Missing reverse edge bob -> alice
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        assert any(issue.code == "SPOUSE_OF_ASYMMETRIC" for issue in report.issues)

    def test_multiple_asymmetric_spouses_detected(self):
        """Multiple asymmetric spouse edges should all be detected."""
        g = TypedGraph()
        g.add_node("a", NodeType.PERSON)
        g.add_node("b", NodeType.PERSON)
        g.add_node("c", NodeType.PERSON)
        g.add_node("d", NodeType.PERSON)
        g.add_edge(EdgeType.SPOUSE_OF, "a", "b")  # Missing b->a
        g.add_edge(EdgeType.SPOUSE_OF, "c", "d")  # Missing d->c
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        
        assert report.status == CheckStatus.HARD_FAIL
        asymmetric_issues = [i for i in report.issues if i.code == "SPOUSE_OF_ASYMMETRIC"]
        assert len(asymmetric_issues) == 2


class TestConsistencyCheckerDeterminism:
    """Tests for deterministic validation."""

    def test_validation_deterministic_across_insertion_orders(self):
        """Validation should be deterministic regardless of insertion order."""
        # Graph 1: nodes in order a, b, c
        g1 = TypedGraph()
        g1.add_node("a", NodeType.PERSON)
        g1.add_node("b", NodeType.PERSON)
        g1.add_node("c", NodeType.PERSON)
        g1.add_edge(EdgeType.PARENT_OF, "a", "b")
        g1.add_edge(EdgeType.PARENT_OF, "b", "c")
        
        # Graph 2: nodes in reverse order
        g2 = TypedGraph()
        g2.add_node("c", NodeType.PERSON)
        g2.add_node("b", NodeType.PERSON)
        g2.add_node("a", NodeType.PERSON)
        g2.add_edge(EdgeType.PARENT_OF, "b", "c")
        g2.add_edge(EdgeType.PARENT_OF, "a", "b")
        
        checker = ConsistencyChecker()
        report1 = checker.check(g1)
        report2 = checker.check(g2)
        
        assert report1.status == report2.status
        assert len(report1.issues) == len(report2.issues)


class TestConsistencyCheckerSerialization:
    """Tests for CheckReport JSON serialization."""

    def test_report_to_dict_with_cycle(self):
        """Report with cycle should serialize correctly."""
        g = TypedGraph()
        g.add_node("a", NodeType.PERSON)
        g.add_node("b", NodeType.PERSON)
        g.add_edge(EdgeType.PARENT_OF, "a", "b")
        g.add_edge(EdgeType.PARENT_OF, "b", "a")
        
        checker = ConsistencyChecker()
        report = checker.check(g)
        data = report.to_dict()
        
        assert data["checker"] == "ConsistencyChecker"
        assert data["status"] == "HARD_FAIL"
        assert len(data["issues"]) > 0
        assert any(issue["code"] == "PARENT_OF_CYCLE" for issue in data["issues"])
