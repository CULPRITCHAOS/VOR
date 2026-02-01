"""NeuraLogix-H DSL Pretty-printer."""
import json
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType

class HPrinter:
    """Converts TypedGraph IR into NeuraLogix-H DSL."""

    def print_graph(self, graph: TypedGraph) -> str:
        """Generate human-writable H-DSL from graph.
        
        Args:
            graph: TypedGraph to print
            
        Returns:
            String of DSL lines
        """
        lines = []
        
        # 1. Nodes
        for node_id, node in graph.nodes.items():
            val_str = json.dumps(node.value)
            type_str = f": {node.node_type.value}" if hasattr(node.node_type, "value") else f": {node.node_type}"
            lines.append(f"let {node_id}{type_str} = {val_str}")
            
        # Separator
        if graph.nodes and graph.edges:
            lines.append("")
            
        # 2. Edges
        for edge in graph.edges:
            edge_type_str = edge.edge_type.value if hasattr(edge.edge_type, "value") else str(edge.edge_type)
            line = f"{edge.source} {edge_type_str} {edge.target}"
            
            if edge.metadata and "result" in edge.metadata:
                line += f" -> {edge.metadata['result']}"
                
            lines.append(line)
            
        return "\n".join(lines)
