"""Synthetic data generator for NeuraLogix training and testing."""
from __future__ import annotations

import random
from typing import List, Optional

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType


class SyntheticDataGenerator:
    """Generates synthetic graphs for arithmetic and family relations."""

    def __init__(self, seed: int = 42):
        """Initialize generator with a fixed seed for determinism.
        
        Args:
            seed: Random seed
        """
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_arithmetic_sequence(self, count: int = 20, max_val: int = 100) -> TypedGraph:
        """Generate a graph with numbers and ADD/GREATER_THAN relations.
        
        Args:
            count: Number of addition pairs to generate
            max_val: Maximum value for numbers
            
        Returns:
            TypedGraph with numbers and relationships
        """
        g = TypedGraph()
        
        for i in range(count):
            a_val = self.rng.randint(0, max_val // 2)
            b_val = self.rng.randint(0, max_val // 2)
            sum_val = a_val + b_val
            
            # Use value strings as IDs for uniqueness in this toy set
            id_a = f"num_{a_val}"
            id_b = f"num_{b_val}"
            id_sum = f"num_{sum_val}"
            
            if id_a not in g.nodes:
                g.add_node(id_a, NodeType.NUMBER, value=a_val)
            if id_b not in g.nodes:
                g.add_node(id_b, NodeType.NUMBER, value=b_val)
            if id_sum not in g.nodes:
                g.add_node(id_sum, NodeType.NUMBER, value=sum_val)
                
            # Add relationship
            g.add_edge(EdgeType.ADD, id_a, id_b, metadata={"result": id_sum})
            
            # Add comparison
            if a_val > b_val:
                g.add_edge(EdgeType.GREATER_THAN, id_a, id_b)
            elif b_val > a_val:
                g.add_edge(EdgeType.GREATER_THAN, id_b, id_a)
                
        return g

    def generate_family_tree(self, depth: int = 3, children_per_parent: int = 2) -> TypedGraph:
        """Generate a synthetic family tree.
        
        Args:
            depth: Depth of the tree (generations)
            children_per_parent: Number of children each parent has
            
        Returns:
            TypedGraph with PERSON nodes and PARENT_OF/SPOUSE_OF edges
        """
        g = TypedGraph()
        names = ["Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah", 
                 "Ian", "Julia", "Kevin", "Laura", "Mike", "Nora", "Oscar", "Paula"]
        
        name_idx = 0
        
        def get_next_name():
            nonlocal name_idx
            name = names[name_idx % len(names)]
            if name_idx >= len(names):
                name = f"{name}_{name_idx}"
            name_idx += 1
            return name

        def build_generation(parent_ids: List[str], current_depth: int):
            if current_depth >= depth:
                return
            
            for pid in parent_ids:
                # Add a spouse for each parent to keep it simple
                spouse_name = get_next_name()
                spouse_id = spouse_name.lower()
                
                if spouse_id not in g.nodes:
                    g.add_node(spouse_id, NodeType.PERSON, value={"name": spouse_name})
                    g.add_edge(EdgeType.SPOUSE_OF, pid, spouse_id)
                    g.add_edge(EdgeType.SPOUSE_OF, spouse_id, pid) # Symmetric
                
                # Add children
                children_ids = []
                for _ in range(children_per_parent):
                    child_name = get_next_name()
                    child_id = child_name.lower()
                    
                    if child_id not in g.nodes:
                        g.add_node(child_id, NodeType.PERSON, value={"name": child_name})
                        g.add_edge(EdgeType.PARENT_OF, pid, child_id)
                        g.add_edge(EdgeType.PARENT_OF, spouse_id, child_id)
                        children_ids.append(child_id)
                
                build_generation(children_ids, current_depth + 1)

        # Start with a root ancestor
        root_name = get_next_name()
        root_id = root_name.lower()
        g.add_node(root_id, NodeType.PERSON, value={"name": root_name})
        
        build_generation([root_id], 1)
        
        return g
