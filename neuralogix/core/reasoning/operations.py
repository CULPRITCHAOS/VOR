"""Operation registry for reasoning engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType


@dataclass(frozen=True)
class OperationSignature:
    """Signature for a reasoning operation.
    
    Defines inputs, outputs, and the pure apply function.
    """
    name: str
    input_types: List[NodeType]  # Expected input node types
    output_type: NodeType  # Output node type
    apply: Callable[[TypedGraph, Dict[str, Any]], Dict[str, Any]]
    description: str = ""


class OperationRegistry:
    """Registry of allowed reasoning operations.
    
    All operations are pure functions that:
    1. Take a graph and input node IDs
    2. Create new nodes/edges (don't modify existing)
    3. Return output node IDs
    """
    
    def __init__(self):
        self._operations: Dict[str, OperationSignature] = {}
        self._register_builtin_operations()
    
    def _register_builtin_operations(self):
        """Register built-in MVP operations."""
        # Arithmetic: add
        self.register(OperationSignature(
            name="add",
            input_types=[NodeType.NUMBER, NodeType.NUMBER],
            output_type=NodeType.NUMBER,
            apply=self._apply_add,
            description="Add two numbers: a + b -> sum",
        ))
        
        # Arithmetic: greater_than
        self.register(OperationSignature(
            name="greater_than",
            input_types=[NodeType.NUMBER, NodeType.NUMBER],
            output_type=NodeType.BOOLEAN,
            apply=self._apply_greater_than,
            description="Compare numbers: a > b -> boolean",
        ))
        
        # Relations: derive_grandparent
        self.register(OperationSignature(
            name="derive_grandparent",
            input_types=[NodeType.PERSON, NodeType.PERSON],
            output_type=NodeType.RELATION,
            apply=self._apply_derive_grandparent,
            description="Derive grandparent relation from parent_of chain",
        ))
    
    def register(self, op: OperationSignature):
        """Register an operation."""
        self._operations[op.name] = op
    
    def get(self, name: str) -> OperationSignature:
        """Get operation by name.
        
        Raises:
            KeyError: If operation not found
        """
        return self._operations[name]
    
    def list_operations(self) -> List[str]:
        """List all registered operation names."""
        return list(self._operations.keys())
    
    # Built-in operation implementations
    
    @staticmethod
    def _apply_add(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply add operation: a + b -> sum.
        
        Args:
            graph: Graph to mutate
            inputs: {"a": node_id, "b": node_id, "result_id": node_id}
            
        Returns:
            {"result": node_id}
        """
        a_id = inputs["a"]
        b_id = inputs["b"]
        result_id = inputs.get("result_id", f"add_{a_id}_{b_id}")
        
        # Get values
        a_node = graph.nodes[a_id]
        b_node = graph.nodes[b_id]
        
        if a_node.node_type != NodeType.NUMBER or b_node.node_type != NodeType.NUMBER:
            raise ValueError(f"add requires NUMBER inputs, got {a_node.node_type}, {b_node.node_type}")
        
        # Compute sum
        result_value = a_node.value + b_node.value
        
        # Create result node if it doesn't exist
        if result_id not in graph.nodes:
            graph.add_node(result_id, NodeType.NUMBER, value=result_value)
        
        # Add edges
        graph.add_edge(EdgeType.ADD, a_id, b_id, metadata={"result": result_id})
        
        return {"result": result_id}
    
    @staticmethod
    def _apply_greater_than(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply greater_than operation: a > b -> boolean.
        
        Args:
            graph: Graph to mutate
            inputs: {"a": node_id, "b": node_id, "result_id": node_id}
            
        Returns:
            {"result": node_id}
        """
        a_id = inputs["a"]
        b_id = inputs["b"]
        result_id = inputs.get("result_id", f"gt_{a_id}_{b_id}")
        
        # Get values
        a_node = graph.nodes[a_id]
        b_node = graph.nodes[b_id]
        
        if a_node.node_type != NodeType.NUMBER or b_node.node_type != NodeType.NUMBER:
            raise ValueError(f"greater_than requires NUMBER inputs, got {a_node.node_type}, {b_node.node_type}")
        
        # Compute comparison
        result_value = a_node.value > b_node.value
        
        # Create result node
        if result_id not in graph.nodes:
            graph.add_node(result_id, NodeType.BOOLEAN, value=result_value)
        
        # Add edges
        graph.add_edge(EdgeType.GREATER_THAN, a_id, b_id, metadata={"result": result_id})
        
        return {"result": result_id}
    
    @staticmethod
    def _apply_derive_grandparent(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Derive grandparent relation from parent_of chain.
        
        Finds: grandparent parent_of parent, parent parent_of grandchild
        Creates: grandparent_of relation node
        
        Args:
            graph: Graph to mutate
            inputs: {"grandparent": node_id, "grandchild": node_id}
            
        Returns:
            {"result": relation_node_id}
        """
        grandparent_id = inputs["grandparent"]
        grandchild_id = inputs["grandchild"]
        result_id = inputs.get("result_id", f"grandparent_of_{grandparent_id}_{grandchild_id}")
        
        # Verify nodes are PERSON type
        gp_node = graph.nodes[grandparent_id]
        gc_node = graph.nodes[grandchild_id]
        
        if gp_node.node_type != NodeType.PERSON or gc_node.node_type != NodeType.PERSON:
            raise ValueError(f"derive_grandparent requires PERSON inputs, got {gp_node.node_type}, {gc_node.node_type}")
        
        # Find intermediate parent
        # Look for: grandparent parent_of X, X parent_of grandchild
        parent_id = None
        for edge in graph.edges:
            if edge.edge_type == EdgeType.PARENT_OF and edge.source == grandparent_id:
                # Found grandparent -> candidate parent
                candidate = edge.target
                # Check if candidate -> grandchild exists
                for edge2 in graph.edges:
                    if (edge2.edge_type == EdgeType.PARENT_OF and 
                        edge2.source == candidate and 
                        edge2.target == grandchild_id):
                        parent_id = candidate
                        break
                if parent_id:
                    break
        
        if not parent_id:
            raise ValueError(
                f"No parent_of chain found: {grandparent_id} -> X -> {grandchild_id}"
            )
        
        # Create relation node
        if result_id not in graph.nodes:
            graph.add_node(
                result_id,
                NodeType.RELATION,
                value={
                    "type": "grandparent_of",
                    "subject": grandparent_id,
                    "object": grandchild_id,
                    "derived_via": parent_id,
                }
            )
        
        return {"result": result_id, "intermediate": parent_id}


# Global registry instance
OPERATION_REGISTRY = OperationRegistry()
