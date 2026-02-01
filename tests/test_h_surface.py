"""Unit tests for NeuraLogix-H Surface."""
import pytest
from neuralogix.h_surface.parser import HParser
from neuralogix.h_surface.printer import HPrinter
from neuralogix.h_surface.lint import HLinter
from neuralogix.core.ir.schema import NodeType

def test_h_surface_roundtrip():
    """Verify that IR -> DSL -> IR preserves structure."""
    parser = HParser()
    printer = HPrinter()
    
    # Original Graph
    from neuralogix.core.ir.graph import TypedGraph
    g1 = TypedGraph()
    g1.add_node("n1", NodeType.NUMBER, value=10)
    g1.add_node("n2", NodeType.NUMBER, value=20)
    from neuralogix.core.ir.schema import EdgeType
    g1.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
    
    # IR -> DSL
    dsl = printer.print_graph(g1)
    
    # DSL -> IR
    g2 = parser.parse(dsl)
    
    # Assert nodes
    assert "n1" in g2.nodes
    assert g2.nodes["n1"].value == 10
    
    # Assert edge
    assert len(g2.edges) == 1
    assert g2.edges[0].edge_type == EdgeType.ADD
    assert g2.edges[0].metadata["result"] == "n3"

def test_h_surface_parser_extended():
    """Verify H-specific assignment parsing."""
    parser = HParser()
    dsl = """
    let alice: Person = {"name": "Alice"}
    let bob: Person = {"name": "Bob"}
    bob = parent_of(alice)
    """
    g = parser.parse(dsl)
    assert "alice" in g.nodes
    assert "bob" in g.nodes
    # Op parsing logic in parser.py maps bob = parent_of(alice) to bob parent_of alice
    assert any(e.source == "bob" and e.target == "alice" for e in g.edges)

def test_h_linter_finds_errors():
    """Verify that the linter catches undefined nodes."""
    linter = HLinter()
    dsl = """
    let a = 1
    a add b
    """
    issues = linter.lint(dsl)
    assert any("undefined node" in i["message"] and "b" in i["message"] for i in issues)
