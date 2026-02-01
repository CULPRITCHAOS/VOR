"""Budget checker for enforcing quantization and residual limits."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType
from neuralogix.core.checkers.base import Checker, CheckIssue, CheckReport, CheckStatus


class BudgetChecker(Checker):
    """Checker that enforces error budgets on nodes.
    
    Threshold Policy:
    - error <= τ          => OK
    - τ < error <= 2τ     => SOFT_FAIL (uncertain)
    - error > 2τ          => HARD_FAIL (off-manifold)
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """Initialize BudgetChecker.
        
        Args:
            thresholds: Dict mapping node type or 'default' to τ value.
        """
        self.thresholds = thresholds or {"default": 1.0}

    def check(self, graph: TypedGraph) -> CheckReport:
        """Evaluate budget status of all nodes in the graph.
        
        Expects nodes/codec results to have 'quantization_error' or 'residual_norm'
        stored in metadata or node value if previously encoded.
        
        NOTE: In this implementation, we assume the reasoning engine or codec
        attaches these metrics to the nodes or provides them in a context.
        For MVP, we check node 'value' if it's a CodeResult dict or if metadata is present.
        """
        issues: List[CheckIssue] = []
        
        for node_id, node in graph.nodes.items():
            # Try to find error metrics
            error = self._extract_error(node)
            if error is None:
                continue
                
            # Determine threshold τ for this node type
            node_type_val = node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type)
            tau = self.thresholds.get(node_type_val, self.thresholds.get("default", 1.0))
            
            # Apply policy
            if error > 2 * tau:
                issues.append(CheckIssue(
                    code="BUDGET_EXCEEDED_HARD",
                    message=f"Node '{node_id}' error {error:.4f} > 2τ ({2*tau:.4f})",
                    status=CheckStatus.HARD_FAIL,
                    node_ids=[node_id],
                    details={"error": error, "tau": tau}
                ))
            elif error > tau:
                issues.append(CheckIssue(
                    code="BUDGET_EXCEEDED_SOFT",
                    message=f"Node '{node_id}' error {error:.4f} > τ ({tau:.4f})",
                    status=CheckStatus.SOFT_FAIL,
                    node_ids=[node_id],
                    details={"error": error, "tau": tau}
                ))
                
        # Determine overall status
        status = CheckStatus.OK
        if any(i.status == CheckStatus.HARD_FAIL for i in issues):
            status = CheckStatus.HARD_FAIL
        elif any(i.status == CheckStatus.SOFT_FAIL for i in issues):
            status = CheckStatus.SOFT_FAIL
            
        return CheckReport(
            checker="BudgetChecker",
            status=status,
            issues=issues
        )

    def _extract_error(self, node: Any) -> Optional[float]:
        """Extract quantization/residual error from node."""
        from neuralogix.core.codec.base import CodeResult
        
        # 1. Check if node.value is a CodeResult object
        if isinstance(node.value, CodeResult):
            if "quantization_error" in node.value.metadata:
                return float(node.value.metadata["quantization_error"])
            if "residual_norm" in node.value.metadata:
                return float(node.value.metadata["residual_norm"])
        
        # 2. Check if node.value is a CodeResult-like dict
        if isinstance(node.value, dict):
            # Check metadata
            meta = node.value.get("metadata", {})
            if "quantization_error" in meta:
                return float(meta["quantization_error"])
            if "residual_norm" in meta:
                return float(meta["residual_norm"])
            if "error" in node.value:
                return float(node.value["error"])
                
        # 3. Check if node has metadata attribute
        if hasattr(node, "node_metadata") and node.node_metadata:
            if "quantization_error" in node.node_metadata:
                return float(node.node_metadata["quantization_error"])
                
        return None

