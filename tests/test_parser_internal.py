import pytest
from neuralogix.pilots.pilot_i.tools import Parser
from neuralogix.pilots.pilot_i.graph import TypedGraph, Provenance

def test_numeric_normalization():
    assert TypedGraph.normalize_value("$5M") == "5000000"
    assert TypedGraph.normalize_value("5,000,000") == "5000000"
    assert TypedGraph.normalize_value("5k") == "5000"
    assert TypedGraph.normalize_value("1.5B") == "1500000000"
    assert TypedGraph.normalize_value("123") == "123"

def test_parser_possessive():
    parser = Parser()
    graph = TypedGraph()
    docs = [{"id": "d1", "text": "Acme's budget is $5M"}]
    parser.parse_to_graph(docs, graph, "2026-01-31")
    
    facts = graph.get_facts("Acme", "budget")
    assert "5000000|True|" in facts
    assert facts["5000000|True|"][0].value == "$5M"
    assert facts["5000000|True|"][0].provenance.doc_id == "d1"

def test_parser_copula_a():
    parser = Parser()
    graph = TypedGraph()
    docs = [{"id": "d1", "text": "The CEO of Acme is Alice"}]
    parser.parse_to_graph(docs, graph, "2026-01-31")
    
    facts = graph.get_facts("Acme", "CEO")
    assert "alice|True|" in facts

def test_parser_copula_b():
    parser = Parser()
    graph = TypedGraph()
    docs = [{"id": "d1", "text": "Alice is the CEO of Acme"}]
    parser.parse_to_graph(docs, graph, "2026-01-31")
    
    facts = graph.get_facts("Acme", "CEO")
    assert "alice|True|" in facts

def test_parser_negation():
    parser = Parser()
    graph = TypedGraph()
    docs = [{"id": "d1", "text": "Alice is not the CEO of Acme"}]
    parser.parse_to_graph(docs, graph, "2026-01-31")
    
    facts = graph.get_facts("Acme", "CEO")
    assert "alice|False|" in facts

def test_parser_time_scope():
    parser = Parser()
    graph = TypedGraph()
    docs = [{"id": "d1", "text": "In 2020, CEO of Acme was Bob"}]
    parser.parse_to_graph(docs, graph, "2026-01-31")
    
    facts = graph.get_facts("Acme", "CEO")
    assert "bob|True|2020" in facts

def test_parser_determinism():
    parser = Parser()
    text = "In 2020, CEO of Acme was Bob. Acme's budget is $5M."
    docs = [{"id": "d1", "text": text}]
    
    graph1 = TypedGraph()
    parser.parse_to_graph(docs, graph1, "ts")
    
    graph2 = TypedGraph()
    parser.parse_to_graph(docs, graph2, "ts")
    
    assert list(graph1.nodes.keys()) == list(graph2.nodes.keys())
    for key in graph1.nodes:
        assert list(graph1.nodes[key].keys()) == list(graph2.nodes[key].keys())
