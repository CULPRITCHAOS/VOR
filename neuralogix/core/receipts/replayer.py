"""Receipt replayer for deterministic IR reconstruction."""
from __future__ import annotations

from typing import Callable, List

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.receipts.schema import ReceiptEvent


class TamperDetected(Exception):
    """Raised when receipt tampering is detected."""
    pass


class ReplayMismatch(Exception):
    """Raised when replay state doesn't match receipt expectations."""
    pass


class ReceiptReplayer:
    """Replays receipts to reconstruct IR state deterministically.
    
    Verifies:
    - Hash chain integrity
    - Graph hash consistency
    - Receipt hash validity
    """
    
    def __init__(self, apply_event_hook: Callable[[ReceiptEvent, TypedGraph], None]):
        """Initialize replayer with event application hook.
        
        Args:
            apply_event_hook: Function that applies a receipt event to a graph.
                             Signature: (event, graph) -> None (mutates graph)
        """
        self.apply_event = apply_event_hook
    
    def replay(self, receipts: List[ReceiptEvent], initial_graph: TypedGraph) -> TypedGraph:
        """Replay receipts onto an initial graph state.
        
        Args:
            receipts: List of ReceiptEvents in chronological order
            initial_graph: Starting graph state (should be empty for full replay)
            
        Returns:
            Final graph state after all receipts applied
            
        Raises:
            TamperDetected: If hash chain or receipt hashes are invalid
            ReplayMismatch: If graph hashes don't match expectations
        """
        graph = initial_graph
        prev_hash = "genesis"
        
        for i, event in enumerate(receipts):
            # Verify hash chain
            if event.prev_receipt_hash != prev_hash:
                raise TamperDetected(
                    f"Receipt {i} (id={event.event_id}): Hash chain broken. "
                    f"Expected prev_receipt_hash='{prev_hash}', got '{event.prev_receipt_hash}'"
                )
            
            # Verify receipt hash
            computed_hash = event.compute_receipt_hash()
            if event.receipt_hash != computed_hash:
                raise TamperDetected(
                    f"Receipt {i} (id={event.event_id}): Receipt hash mismatch. "
                    f"Stored='{event.receipt_hash}', computed='{computed_hash}'"
                )
            
            # Verify graph_hash_before
            current_graph_hash = graph.state_hash()
            if event.graph_hash_before != current_graph_hash:
                raise ReplayMismatch(
                    f"Receipt {i} (id={event.event_id}): graph_hash_before mismatch. "
                    f"Expected='{event.graph_hash_before}', actual='{current_graph_hash}'"
                )
            
            # Apply event to graph
            self.apply_event(event, graph)
            
            # Verify graph_hash_after
            new_graph_hash = graph.state_hash()
            if event.graph_hash_after != new_graph_hash:
                raise ReplayMismatch(
                    f"Receipt {i} (id={event.event_id}): graph_hash_after mismatch. "
                    f"Expected='{event.graph_hash_after}', actual='{new_graph_hash}'"
                )
            
            # Update prev_hash for next iteration
            prev_hash = event.receipt_hash
        
        return graph
    
    def verify_chain(self, receipts: List[ReceiptEvent]) -> bool:
        """Verify hash chain integrity without replaying operations.
        
        Args:
            receipts: List of ReceiptEvents to verify
            
        Returns:
            True if chain is valid
            
        Raises:
            TamperDetected: If any hash is invalid
        """
        prev_hash = "genesis"
        
        for i, event in enumerate(receipts):
            # Verify hash chain
            if event.prev_receipt_hash != prev_hash:
                raise TamperDetected(
                    f"Receipt {i}: Hash chain broken at prev_receipt_hash"
                )
            
            # Verify receipt hash
            computed_hash = event.compute_receipt_hash()
            if event.receipt_hash != computed_hash:
                raise TamperDetected(
                    f"Receipt {i}: Receipt hash tampered"
                )
            
            prev_hash = event.receipt_hash
        
        return True
