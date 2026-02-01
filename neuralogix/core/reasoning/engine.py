"""Reasoning engine for single-step inference."""
from __future__ import annotations

import copy
from typing import Any, Dict, Optional

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.checkers import validate
from neuralogix.core.checkers.base import CheckStatus
from neuralogix.core.receipts.schema import ReceiptEvent
from neuralogix.core.receipts.logger import ReceiptLogger
from neuralogix.core.reasoning.operations import OPERATION_REGISTRY, OperationSignature


class ReasoningEngine:
    """Single-step reasoning engine with receipts.
    
    Executes one operation at a time:
    1. Capture graph_hash_before
    2. Apply operation to graph
    3. Run checkers
    4. Capture graph_hash_after
    5. Emit receipt
    6. Rollback on HARD_FAIL or ABSTAIN
    """
    
    def __init__(self, logger: Optional[ReceiptLogger] = None, rollback_enabled: bool = False, checkers_enabled: bool = True):
        """Initialize reasoning engine.
        
        Args:
            logger: Optional receipt logger (if None, receipts not logged)
            rollback_enabled: Whether to rollback graph on HARD_FAIL/ABSTAIN (Phase A: default False)
            checkers_enabled: Whether to run checkers on every step (default True)
        """
        self.logger = logger
        self.rollback_enabled = rollback_enabled
        self.checkers_enabled = checkers_enabled
        self.operation_registry = OPERATION_REGISTRY
    
    def step(
        self,
        graph: TypedGraph,
        operation: str,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single reasoning step.
        
        Args:
            graph: Graph to reason over (will be mutated on success)
            operation: Operation name from registry
            inputs: Operation-specific inputs (node IDs, etc.)
            
        Returns:
            Dict with:
                - status: CheckStatus
                - outputs: Operation outputs (if successful)
                - receipt: ReceiptEvent
                - message: Human-readable result
                
        Raises:
            KeyError: If operation not in registry
            ValueError: If operation inputs invalid
        """
        # Get operation
        op_sig = self.operation_registry.get(operation)
        
        # Capture state before
        hash_before = graph.state_hash()
        graph_backup = copy.deepcopy(graph)
        
        # Apply operation
        try:
            outputs = op_sig.apply(graph, inputs)
        except (ValueError, KeyError) as e:
            # Operation failed (invalid inputs, missing nodes, etc.)
            # Emit receipt and return failure
            hash_after = graph.state_hash()  # Should be same as before
            
            receipt = self._create_receipt(
                op_name=operation,
                inputs=inputs,
                outputs={},
                status=CheckStatus.HARD_FAIL,
                hash_before=hash_before,
                hash_after=hash_after,
                checker_reports=[],
                notes={"error": str(e)},
            )
            
            if self.logger:
                self.logger.append(receipt)
            
            return {
                "status": CheckStatus.HARD_FAIL,
                "outputs": {},
                "receipt": receipt,
                "message": f"Operation failed: {e}",
            }
        
        # Validate graph
        if self.checkers_enabled:
            overall_status, reports = validate(graph)
            checker_reports = [r.to_dict() for r in reports]
        else:
            overall_status = CheckStatus.OK
            checker_reports = []
        
        # Capture state after
        hash_after = graph.state_hash()
        
        # Create receipt
        receipt = self._create_receipt(
            op_name=operation,
            inputs=inputs,
            outputs=outputs,
            status=overall_status,
            hash_before=hash_before,
            hash_after=hash_after,
            checker_reports=checker_reports,
            notes={},
        )
        
        # Handle validation result
        if overall_status in (CheckStatus.HARD_FAIL, CheckStatus.ABSTAIN):
            # Rollback graph to previous state iff enabled
            if self.rollback_enabled:
                graph.nodes = graph_backup.nodes
                graph.edges = graph_backup.edges
                msg_suffix = ", step rolled back"
                notes = {"rollback": True}
            else:
                msg_suffix = ", rollback disabled"
                notes = {"rollback_refused": True}
            
            # Log receipt (even though we might have rolled back)
            if self.logger:
                # Update hash_after to reflect state iff rolled back
                h_after = hash_before if self.rollback_enabled else hash_after
                receipt = self._create_receipt(
                    op_name=operation,
                    inputs=inputs,
                    outputs={},
                    status=overall_status,
                    hash_before=hash_before,
                    hash_after=h_after,
                    checker_reports=checker_reports,
                    notes=notes,
                )
                self.logger.append(receipt)
            
            return {
                "status": overall_status,
                "outputs": {},
                "receipt": receipt,
                "message": f"Validation {overall_status.value}{msg_suffix}",
            }
        
        # Success - log receipt
        if self.logger:
            self.logger.append(receipt)
        
        return {
            "status": overall_status,
            "outputs": outputs,
            "receipt": receipt,
            "message": f"Step completed with {overall_status.value}",
        }
    
    def _create_receipt(
        self,
        op_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        status: CheckStatus,
        hash_before: str,
        hash_after: str,
        checker_reports: list,
        notes: Dict[str, Any],
    ) -> ReceiptEvent:
        """Create a receipt for this reasoning step."""
        prev_hash = self.logger.get_prev_receipt_hash() if self.logger else "genesis"
        
        return ReceiptEvent.create(
            op_name=op_name,
            inputs=inputs,
            outputs=outputs,
            checker_reports=checker_reports,
            status=status.value,
            graph_hash_before=hash_before,
            graph_hash_after=hash_after,
            prev_receipt_hash=prev_hash,
            notes=notes,
        )
