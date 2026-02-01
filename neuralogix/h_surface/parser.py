"""NeuraLogix-H DSL Parser."""
import re
from typing import List, Optional
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType, EdgeType

class HParser:
    """Parses NeuraLogix-H DSL into TypedGraph IR."""

    def parse(self, text: str) -> TypedGraph:
        """Parse multiple lines of DSL.
        
        Args:
            text: Batch as a string
            
        Returns:
            TypedGraph
        """
        graph = TypedGraph()
        lines = text.strip().split("\n")
        
        for line in lines:
            self._parse_line(graph, line.strip())
            
        return graph

    def _parse_line(self, graph: TypedGraph, line: str):
        """Parse a single line of DSL."""
        line = line.strip()
        if not line or line.startswith("#"):
            return

        # Helper to ensure node exists
        def ensure_node(nid, ntype=NodeType.NUMBER):
            if nid not in graph.nodes:
                graph.add_node(nid, ntype)

        # 1. Node definition: let <id>[: <type>] = <value>
        # 1. Node definition: let <id>[: <type>] = <value>
        node_match = re.match(r"^let\s+(\w+)(?:\s*:\s*(\w+))?\s*=\s*(.+)$", line)
        if node_match:
            node_id, node_type_str, value_str = node_match.groups()
            value_str = value_str.strip()
            
            # Robust value parsing
            if value_str.lower() in ("null", "none"):
                value = None
            else:
                try:
                    import json
                    value = json.loads(value_str.replace("'", '"'))
                except Exception:
                    try:
                        import ast
                        value = ast.literal_eval(value_str)
                    except Exception:
                        value = value_str
            
            node_type = NodeType.NUMBER
            if node_type_str:
                try:
                    node_type = NodeType(node_type_str)
                except ValueError:
                    pass
            elif isinstance(value, (int, float)):
                node_type = NodeType.NUMBER
            elif isinstance(value, dict):
                node_type = NodeType.PERSON
            
            if node_id in graph.nodes:
                from neuralogix.core.ir.graph import Node
                graph.nodes[node_id] = Node(node_id, node_type, value)
            else:
                graph.add_node(node_id, node_type, value=value)
            return

        # 2. Edge relationship: <id1> <edge_type> <id2>
        edge_match = re.match(r"^(\w+)\s+([\w_]+)\s+(\w+)(?:\s*->\s*(\w+))?$", line)
        if edge_match:
            src, edge_type_str, target, res_id = edge_match.groups()
            ensure_node(src)
            ensure_node(target)
            if res_id: ensure_node(res_id)
            
            edge_type = None
            # Case-insensitive match for EdgeType
            for et in EdgeType:
                if et.value.lower() == edge_type_str.lower():
                    edge_type = et
                    break
            
            if edge_type is None:
                edge_type = edge_type_str
                
            metadata = {"result": res_id} if res_id else None
            graph.add_edge(edge_type, src, target, metadata=metadata)
            return
            
        # 3. Op assignment: <id3> = <op>(<id1>, <id2>)
        op_match = re.match(r"^(\w+)\s*=\s*(\w+)\(([^)]+)\)$", line)
        if op_match:
            res_id, op_name, args_str = op_match.groups()
            args = [a.strip() for a in args_str.split(",")]
            
            if op_name == "add" and len(args) == 2:
                ensure_node(args[0])
                ensure_node(args[1])
                ensure_node(res_id)
                graph.add_edge(EdgeType.ADD, args[0], args[1], metadata={"result": res_id})
            elif op_name == "parent_of" and len(args) == 1:
                ensure_node(res_id, NodeType.PERSON)
                ensure_node(args[0], NodeType.PERSON)
                graph.add_edge(EdgeType.PARENT_OF, res_id, args[0])
            return

        raise ValueError(f"H-Parser: Unrecognized line format: '{line}'")
