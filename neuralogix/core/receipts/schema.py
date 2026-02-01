"""Receipt schema for tamper-evident audit logging."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReceiptEvent:
    """Single receipt event in the audit log.
    
    A receipt captures a complete reasoning step with tamper-evident hashing.
    """
    # Event identification
    event_id: str  # UUID or monotonic int
    timestamp: str  # ISO8601 format
    actor: str  # "system" for MVP
    
    # Operation details
    op_name: str  # e.g., "add_node", "validate"
    inputs: Dict[str, Any]  # node_ids/edge_ids + optional values
    outputs: Dict[str, Any]  # node_ids/edge_ids + optional values
    
    # Validation
    checker_reports: List[Dict[str, Any]]  # JSON-serialized CheckReports from M2
    status: str  # OK, SOFT_FAIL, HARD_FAIL, ABSTAIN
    
    # Graph state tracking
    graph_hash_before: str  # TypedGraph.state_hash() before operation
    graph_hash_after: str  # TypedGraph.state_hash() after operation
    
    # Hash chain for tamper evidence
    prev_receipt_hash: str  # Hash of previous receipt (or "genesis" for first)
    receipt_hash: str  # SHA-256 of this receipt's canonical JSON
    
    # Additional metadata
    notes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)
    
    def compute_receipt_hash(self) -> str:
        """Compute SHA-256 hash of this receipt's canonical JSON.
        
        Hash is computed over all fields EXCEPT receipt_hash itself.
        Uses stable JSON serialization (sort_keys, no whitespace).
        
        Returns:
            64-character hex SHA-256 digest
        """
        # Create dict without receipt_hash field
        data = self.to_dict()
        data_without_hash = {k: v for k, v in data.items() if k != "receipt_hash"}
        
        # Canonical JSON: sorted keys, compact separators
        canonical_json = json.dumps(data_without_hash, sort_keys=True, separators=(',', ':'))
        
        # SHA-256 hex digest
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    @classmethod
    def create(
        cls,
        op_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        checker_reports: List[Dict[str, Any]],
        status: str,
        graph_hash_before: str,
        graph_hash_after: str,
        prev_receipt_hash: str,
        actor: str = "system",
        notes: Optional[Dict[str, Any]] = None,
    ) -> ReceiptEvent:
        """Create a new receipt event with computed hash.
        
        Args:
            op_name: Operation name
            inputs: Input node/edge IDs and values
            outputs: Output node/edge IDs and values
            checker_reports: List of CheckReport.to_dict() results
            status: Overall status (OK/SOFT_FAIL/HARD_FAIL/ABSTAIN)
            graph_hash_before: Graph hash before operation
            graph_hash_after: Graph hash after operation
            prev_receipt_hash: Previous receipt hash ("genesis" for first)
            actor: Who performed the operation (default: "system")
            notes: Additional metadata
            
        Returns:
            ReceiptEvent with computed receipt_hash
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Create event without hash first
        temp_event = cls(
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            op_name=op_name,
            inputs=inputs,
            outputs=outputs,
            checker_reports=checker_reports,
            status=status,
            graph_hash_before=graph_hash_before,
            graph_hash_after=graph_hash_after,
            prev_receipt_hash=prev_receipt_hash,
            receipt_hash="",  # Placeholder
            notes=notes or {},
        )
        
        # Compute hash
        receipt_hash = temp_event.compute_receipt_hash()
        
        # Return final event with hash
        return cls(
            event_id=event_id,
            timestamp=timestamp,
            actor=actor,
            op_name=op_name,
            inputs=inputs,
            outputs=outputs,
            checker_reports=checker_reports,
            status=status,
            graph_hash_before=graph_hash_before,
            graph_hash_after=graph_hash_after,
            prev_receipt_hash=prev_receipt_hash,
            receipt_hash=receipt_hash,
            notes=notes or {},
        )
