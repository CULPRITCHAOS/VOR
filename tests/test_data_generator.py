"""Tests for synthetic data generator."""
from __future__ import annotations

import pytest
from neuralogix.core.data.generator import SyntheticDataGenerator
from neuralogix.core.ir.schema import NodeType, EdgeType


def test_arithmetic_generator_determinism():
    gen1 = SyntheticDataGenerator(seed=42)
    gen2 = SyntheticDataGenerator(seed=42)
    
    g1 = gen1.generate_arithmetic_sequence(count=10)
    g2 = gen2.generate_arithmetic_sequence(count=10)
    
    assert g1.state_hash() == g2.state_hash()


def test_arithmetic_generator_structure():
    gen = SyntheticDataGenerator(seed=42)
    g = gen.generate_arithmetic_sequence(count=5)
    
    # Should have numbers and add/greater_than relations
    assert len(g.nodes) > 0
    for node in g.nodes.values():
        assert node.node_type == NodeType.NUMBER
        assert node.value is not None
        
    # Check edges
    add_edges = g.find_edges(edge_type=EdgeType.ADD)
    assert len(add_edges) == 5


def test_family_generator_determinism():
    gen1 = SyntheticDataGenerator(seed=42)
    gen2 = SyntheticDataGenerator(seed=42)
    
    g1 = gen1.generate_family_tree(depth=2)
    g2 = gen2.generate_family_tree(depth=2)
    
    assert g1.state_hash() == g2.state_hash()


def test_family_generator_structure():
    gen = SyntheticDataGenerator(seed=42)
    g = gen.generate_family_tree(depth=2, children_per_parent=2)
    
    # Root + spouse + 2 children = 4 nodes? 
    # Let's check node types
    person_nodes = [n for n in g.nodes.values() if n.node_type == NodeType.PERSON]
    assert len(person_nodes) > 0
    
    # Should have parent_of and spouse_of edges
    parent_edges = g.find_edges(edge_type=EdgeType.PARENT_OF)
    spouse_edges = g.find_edges(edge_type=EdgeType.SPOUSE_OF)
    
    assert len(parent_edges) > 0
    assert len(spouse_edges) > 0
