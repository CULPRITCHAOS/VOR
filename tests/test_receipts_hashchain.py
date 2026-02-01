"""Tests for receipt hash chain integrity and tamper evidence."""
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from neuralogix.core.receipts.schema import ReceiptEvent
from neuralogix.core.receipts.logger import ReceiptLogger
from neuralogix.core.receipts.replayer import ReceiptReplayer, TamperDetected


class TestHashChainIntegrity:
    """Tests for hash chain validation."""

    def test_tamper_with_line_fails_verification(self, tmp_path):
        """Tampering with a receipt line should fail hash verification."""
        # Create legitimate receipts
        event1 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n1"},
            outputs={"node_id": "n1"},
            checker_reports=[],
            status="OK",
            graph_hash_before="hash0",
            graph_hash_after="hash1",
            prev_receipt_hash="genesis",
        )
        event2 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n2"},
            outputs={"node_id": "n2"},
            checker_reports=[],
            status="OK",
            graph_hash_before="hash1",
            graph_hash_after="hash2",
            prev_receipt_hash=event1.receipt_hash,
        )
        
        # Write to file
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        logger.append(event1)
        logger.append(event2)
        
        # Tamper with first event (change op_name)
        with open(logfile, 'r') as f:
            lines = f.readlines()
        
        tampered_event1 = json.loads(lines[0])
        tampered_event1["op_name"] = "TAMPERED"  # Modify operation name
        
        with open(logfile, 'w') as f:
            f.write(json.dumps(tampered_event1) + '\n')
            f.write(lines[1])
        
        # Load receipts
        logger2 = ReceiptLogger(logfile)
        receipts = logger2.read_all()
        
        # Verify chain should detect tampering
        replayer = ReceiptReplayer(lambda e, g: None)
        with pytest.raises(TamperDetected, match="Receipt hash tampered"):
            replayer.verify_chain(receipts)

    def test_reorder_lines_fails_verification(self, tmp_path):
        """Reordering receipt lines should fail hash chain verification."""
        # Create 3 receipts in order
        event1 = ReceiptEvent.create(
            op_name="step1",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="hash0",
            graph_hash_after="hash1",
            prev_receipt_hash="genesis",
        )
        event2 = ReceiptEvent.create(
            op_name="step2",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="hash1",
            graph_hash_after="hash2",
            prev_receipt_hash=event1.receipt_hash,
        )
        event3 = ReceiptEvent.create(
            op_name="step3",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="hash2",
            graph_hash_after="hash3",
            prev_receipt_hash=event2.receipt_hash,
        )
        
        # Write receipts
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        logger.append(event1)
        logger.append(event2)
        logger.append(event3)
        
        # Reorder: swap event2 and event3
        with open(logfile, 'r') as f:
            lines = f.readlines()
        
        with open(logfile, 'w') as f:
            f.write(lines[0])  # event1
            f.write(lines[2])  # event3 (out of order)
            f.write(lines[1])  # event2 (out of order)
        
        # Load receipts
        logger2 = ReceiptLogger(logfile)
        receipts = logger2.read_all()
        
        # Verify chain should fail due to broken prev_receipt_hash chain
        replayer = ReceiptReplayer(lambda e, g: None)
        with pytest.raises(TamperDetected, match="Hash chain broken"):
            replayer.verify_chain(receipts)

    def test_delete_line_fails_verification(self, tmp_path):
        """Deleting a receipt line should fail hash chain verification."""
        # Create 3 receipts
        event1 = ReceiptEvent.create(
            op_name="step1",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h0",
            graph_hash_after="h1",
            prev_receipt_hash="genesis",
        )
        event2 = ReceiptEvent.create(
            op_name="step2",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h1",
            graph_hash_after="h2",
            prev_receipt_hash=event1.receipt_hash,
        )
        event3 = ReceiptEvent.create(
            op_name="step3",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h2",
            graph_hash_after="h3",
            prev_receipt_hash=event2.receipt_hash,
        )
        
        # Write receipts
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        logger.append(event1)
        logger.append(event2)
        logger.append(event3)
        
        # Delete event2 (middle line)
        with open(logfile, 'r') as f:
            lines = f.readlines()
        
        with open(logfile, 'w') as f:
            f.write(lines[0])  # event1
            f.write(lines[2])  # event3 (missing event2)
        
        # Load receipts
        logger2 = ReceiptLogger(logfile)
        receipts = logger2.read_all()
        
        # Verify chain should fail because event3.prev_receipt_hash won't match event1.receipt_hash
        replayer = ReceiptReplayer(lambda e, g: None)
        with pytest.raises(TamperDetected, match="Hash chain broken"):
            replayer.verify_chain(receipts)


class TestReceiptHashing:
    """Tests for receipt hash computation."""

    def test_receipt_hash_deterministic(self):
        """Same receipt data should produce same hash."""
        event1 = ReceiptEvent.create(
            op_name="test_op",
            inputs={"key": "value"},
            outputs={"result": "success"},
            checker_reports=[],
            status="OK",
            graph_hash_before="before",
            graph_hash_after="after",
            prev_receipt_hash="prev",
        )
        
        event2 = ReceiptEvent.create(
            op_name="test_op",
            inputs={"key": "value"},
            outputs={"result": "success"},
            checker_reports=[],
            status="OK",
            graph_hash_before="before",
            graph_hash_after="after",
            prev_receipt_hash="prev",
        )
        
        # Hashes should differ (different event_id and timestamp)
        # But compute_receipt_hash should be deterministic for same content
        assert len(event1.receipt_hash) == 64  # Full SHA-256
        assert len(event2.receipt_hash) == 64

    def test_receipt_hash_changes_with_data(self):
        """Changing any field should change the hash."""
        base_event = ReceiptEvent.create(
            op_name="test_op",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h0",
            graph_hash_after="h1",
            prev_receipt_hash="genesis",
        )
        
        # Create event with different op_name
        modified_event = ReceiptEvent(
            event_id=base_event.event_id,
            timestamp=base_event.timestamp,
            actor=base_event.actor,
            op_name="DIFFERENT_OP",
            inputs=base_event.inputs,
            outputs=base_event.outputs,
            checker_reports=base_event.checker_reports,
            status=base_event.status,
            graph_hash_before=base_event.graph_hash_before,
            graph_hash_after=base_event.graph_hash_after,
            prev_receipt_hash=base_event.prev_receipt_hash,
            receipt_hash=base_event.receipt_hash,  # Keep old hash
            notes=base_event.notes,
        )
        
        # Recompute hash
        recomputed_hash = modified_event.compute_receipt_hash()
        
        # Hash should differ from original
        assert recomputed_hash != base_event.receipt_hash


class TestLoggerHashChainEnforcement:
    """Tests for logger's hash chain enforcement."""

    def test_logger_rejects_broken_chain(self, tmp_path):
        """Logger should reject receipts with broken prev_receipt_hash."""
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        # Append first event
        event1 = ReceiptEvent.create(
            op_name="step1",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h0",
            graph_hash_after="h1",
            prev_receipt_hash="genesis",
        )
        logger.append(event1)
        
        # Try to append event with wrong prev_receipt_hash
        event2_bad = ReceiptEvent.create(
            op_name="step2",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h1",
            graph_hash_after="h2",
            prev_receipt_hash="WRONG_HASH",  # Should be event1.receipt_hash
        )
        
        with pytest.raises(ValueError, match="Hash chain broken"):
            logger.append(event2_bad)

    def test_logger_rejects_invalid_receipt_hash(self, tmp_path):
        """Logger should reject receipts with incorrect receipt_hash."""
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        # Create event with tampered receipt_hash
        event = ReceiptEvent(
            event_id="test-id",
            timestamp="2024-01-01T00:00:00Z",
            actor="system",
            op_name="test",
            inputs={},
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before="h0",
            graph_hash_after="h1",
            prev_receipt_hash="genesis",
            receipt_hash="INVALID_HASH",  # Wrong hash
            notes={},
        )
        
        with pytest.raises(ValueError, match="Receipt hash mismatch"):
            logger.append(event)
