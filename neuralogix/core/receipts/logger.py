"""Append-only receipt logger."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from neuralogix.core.receipts.schema import ReceiptEvent


class ReceiptLogger:
    """Append-only logger for receipt events.
    
    Writes receipts to a JSONL file (one JSON object per line).
    Never rewrites history - append only.
    """
    
    def __init__(self, filepath: Path | str):
        """Initialize logger with file path.
        
        Args:
            filepath: Path to JSONL file for receipts
        """
        self.filepath = Path(filepath)
        self.last_receipt_hash: Optional[str] = None
        
        # Load last receipt hash if file exists
        if self.filepath.exists():
            self._load_last_receipt_hash()
    
    def _load_last_receipt_hash(self) -> None:
        """Load the last receipt hash from existing file."""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                if lines:
                    last_line = lines[-1]
                    last_event = json.loads(last_line)
                    self.last_receipt_hash = last_event["receipt_hash"]
        except (IOError, json.JSONDecodeError, KeyError):
            self.last_receipt_hash = None
    
    def append(self, event: ReceiptEvent) -> None:
        """Append a receipt event to the log.
        
        Validates hash chain before appending.
        
        Args:
            event: ReceiptEvent to append
            
        Raises:
            ValueError: If hash chain is broken
        """
        # Validate hash chain
        expected_prev_hash = self.last_receipt_hash or "genesis"
        if event.prev_receipt_hash != expected_prev_hash:
            raise ValueError(
                f"Hash chain broken: expected prev_receipt_hash='{expected_prev_hash}', "
                f"got '{event.prev_receipt_hash}'"
            )
        
        # Validate receipt hash
        computed_hash = event.compute_receipt_hash()
        if event.receipt_hash != computed_hash:
            raise ValueError(
                f"Receipt hash mismatch: stored='{event.receipt_hash}', "
                f"computed='{computed_hash}'"
            )
        
        # Append to file (create if doesn't exist)
        with open(self.filepath, 'a', encoding='utf-8') as f:
            json_line = json.dumps(event.to_dict(), sort_keys=True, separators=(',', ':'))
            f.write(json_line + '\n')
        
        # Update last hash
        self.last_receipt_hash = event.receipt_hash
    
    def read_all(self) -> List[ReceiptEvent]:
        """Read all receipts from the log.
        
        Returns:
            List of ReceiptEvents in chronological order
            
        Raises:
            IOError: If file doesn't exist or can't be read
        """
        if not self.filepath.exists():
            return []
        
        events: List[ReceiptEvent] = []
        with open(self.filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                event_dict = json.loads(line)
                event = ReceiptEvent(**event_dict)
                events.append(event)
        
        return events
    
    def get_prev_receipt_hash(self) -> str:
        """Get the hash to use for the next receipt's prev_receipt_hash field.
        
        Returns:
            "genesis" if no receipts exist, otherwise last receipt's hash
        """
        return self.last_receipt_hash or "genesis"
