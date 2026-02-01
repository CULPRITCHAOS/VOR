"""Type checker for validating graph structure against IR schema."""
from __future__ import annotations

from typing import Dict, List, Set

from neuralogix.core.ir.graph import Edge, TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.checkers.base import CheckIssue, CheckReport, CheckStatus


# Define allowed edge type mappings: edge_type -> (allowed_source_types, allowed_target_types)
EDGE_TYPE_CONSTRAINTS: Dict[EdgeType, tuple[Set[NodeType], Set[NodeType]]] = {
    EdgeType.PARENT_OF: ({NodeType.PERSON}, {NodeType.PERSON}),
    EdgeType.SPOUSE_OF: ({NodeType.PERSON}, {NodeType.PERSON}),
    EdgeType.ADD: ({NodeType.NUMBER}, {NodeType.NUMBER}),
    EdgeType.GREATER_THAN: ({NodeType.NUMBER}, {NodeType.NUMBER}),
    # Pilot A
    EdgeType.IMPLEMENTS: ({NodeType.CODE}, {NodeType.SPEC}),
    EdgeType.VERIFIES: ({NodeType.TEST}, {NodeType.CODE}),
    EdgeType.RESULTS_FROM: ({NodeType.EXECUTION_RESULT}, {NodeType.TEST}),
    # Pilot B
    EdgeType.HAS_ATTRIBUTE: ({NodeType.ENTITY}, {NodeType.VALUE}),
    EdgeType.CONTAINS: ({NodeType.VALUE_SET}, {NodeType.VALUE}),
}


class TypeChecker:
    """Validates graph structure against IR schema."""

    def check(self, graph: TypedGraph) -> CheckReport:
        """Validate graph structure.
        
        Checks:
        - All node types are valid schema types
        - All edge types are valid schema types
        - Edge source/target node types match allowed types per edge definition
        
        Args:
            graph: TypedGraph to validate
            
        Returns:
            CheckReport with OK or HARD_FAIL status
        """
        issues: List[CheckIssue] = []
        
        # Check node types
        valid_node_types = set(NodeType)
        for node_id, node in graph.nodes.items():
            if node.node_type not in valid_node_types:
                issues.append(CheckIssue(
                    code="INVALID_NODE_TYPE",
                    message=f"Node '{node_id}' has invalid type '{node.node_type}'",
                    status=CheckStatus.HARD_FAIL,
                    node_ids=[node_id],
                    details={"node_type": str(node.node_type)},
                ))
        
        # Check edge types and constraints
        valid_edge_types = set(EdgeType)
        for i, edge in enumerate(graph.edges):
            edge_id = f"edge_{i}"  # Edges don't have IDs, use index
            
            # Validate edge type exists
            if edge.edge_type not in valid_edge_types:
                issues.append(CheckIssue(
                    code="INVALID_EDGE_TYPE",
                    message=f"Edge has invalid type '{edge.edge_type}'",
                    status=CheckStatus.HARD_FAIL,
                    edge_ids=[edge_id],
                    details={"edge_type": str(edge.edge_type)},
                ))
                continue
            
            # Validate source/target node types match edge constraints
            if edge.edge_type in EDGE_TYPE_CONSTRAINTS:
                allowed_src_types, allowed_tgt_types = EDGE_TYPE_CONSTRAINTS[edge.edge_type]
                
                src_node = graph.nodes.get(edge.source)
                tgt_node = graph.nodes.get(edge.target)
                
                if src_node and src_node.node_type not in allowed_src_types:
                    issues.append(CheckIssue(
                        code="INVALID_EDGE_SOURCE_TYPE",
                        message=f"Edge '{edge.edge_type}' requires source type in {allowed_src_types}, got {src_node.node_type}",
                        status=CheckStatus.HARD_FAIL,
                        edge_ids=[edge_id],
                        node_ids=[edge.source],
                        details={
                            "edge_type": str(edge.edge_type),
                            "source_node_type": str(src_node.node_type),
                            "allowed_types": [str(t) for t in allowed_src_types],
                        },
                    ))
                
                if tgt_node and tgt_node.node_type not in allowed_tgt_types:
                    issues.append(CheckIssue(
                        code="INVALID_EDGE_TARGET_TYPE",
                        message=f"Edge '{edge.edge_type}' requires target type in {allowed_tgt_types}, got {tgt_node.node_type}",
                        status=CheckStatus.HARD_FAIL,
                        edge_ids=[edge_id],
                        node_ids=[edge.target],
                        details={
                            "edge_type": str(edge.edge_type),
                            "target_node_type": str(tgt_node.node_type),
                            "allowed_types": [str(t) for t in allowed_tgt_types],
                        },
                    ))
        
        # Determine overall status
        status = CheckStatus.HARD_FAIL if issues else CheckStatus.OK
        
        return CheckReport(
            checker="TypeChecker",
            status=status,
            issues=issues,
        )
