"""Consistency checker for global graph invariants."""
from __future__ import annotations

from typing import Dict, List, Set

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType
from neuralogix.core.checkers.base import CheckIssue, CheckReport, CheckStatus


class ConsistencyChecker:
    """Validates global graph invariants."""

    def check(self, graph: TypedGraph) -> CheckReport:
        """Validate global graph invariants.
        
        Checks:
        - parent_of edges must be acyclic (no cycles)
        - spouse_of edges must be symmetric (if A spouse_of B, then B spouse_of A)
        
        Args:
            graph: TypedGraph to validate
            
        Returns:
            CheckReport with OK or HARD_FAIL status
        """
        issues: List[CheckIssue] = []
        
        # Check parent_of acyclicity
        parent_cycles = self._find_cycles_in_edge_type(graph, EdgeType.PARENT_OF)
        for cycle in parent_cycles:
            issues.append(CheckIssue(
                code="PARENT_OF_CYCLE",
                message=f"Cycle detected in parent_of edges: {' -> '.join(cycle)}",
                status=CheckStatus.HARD_FAIL,
                node_ids=cycle,
                details={"cycle": cycle},
            ))
        
        # Check spouse_of symmetry
        spouse_asymmetries = self._find_asymmetric_spouse_edges(graph)
        for node_a, node_b in spouse_asymmetries:
            issues.append(CheckIssue(
                code="SPOUSE_OF_ASYMMETRIC",
                message=f"spouse_of is not symmetric: {node_a} -> {node_b} exists but not reverse",
                status=CheckStatus.HARD_FAIL,
                node_ids=[node_a, node_b],
                details={"source": node_a, "target": node_b},
            ))
        
        # Determine overall status
        status = CheckStatus.HARD_FAIL if issues else CheckStatus.OK
        
        return CheckReport(
            checker="ConsistencyChecker",
            status=status,
            issues=issues,
        )
    
    def _find_cycles_in_edge_type(self, graph: TypedGraph, edge_type: EdgeType) -> List[List[str]]:
        """Find cycles in a specific edge type using DFS.
        
        Args:
            graph: TypedGraph to check
            edge_type: Edge type to search for cycles
            
        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        # Build adjacency list for this edge type
        adj: Dict[str, List[str]] = {}
        for edge in graph.edges:
            if edge.edge_type == edge_type:
                if edge.source not in adj:
                    adj[edge.source] = []
                adj[edge.source].append(edge.target)
        
        # DFS to find cycles
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        
        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
            
            path.pop()
            rec_stack.remove(node)
        
        # Run DFS from all nodes
        for node_id in graph.nodes:
            if node_id not in visited:
                dfs(node_id)
        
        return cycles
    
    def _find_asymmetric_spouse_edges(self, graph: TypedGraph) -> List[tuple[str, str]]:
        """Find spouse_of edges that are not symmetric.
        
        Args:
            graph: TypedGraph to check
            
        Returns:
            List of (source, target) tuples where edge exists but reverse doesn't
        """
        spouse_edges: Set[tuple[str, str]] = set()
        for edge in graph.edges:
            if edge.edge_type == EdgeType.SPOUSE_OF:
                spouse_edges.add((edge.source, edge.target))
        
        asymmetries: List[tuple[str, str]] = []
        for src, tgt in spouse_edges:
            if (tgt, src) not in spouse_edges:
                asymmetries.append((src, tgt))
        
        return asymmetries
