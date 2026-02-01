"""Tests for deterministic receipt replay."""
import pytest
from pathlib import Path

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.receipts.schema import ReceiptEvent
from neuralogix.core.receipts.logger import ReceiptLogger
from neuralogix.core.receipts.replayer import ReceiptReplayer, ReplayMismatch


def apply_simple_event(event: ReceiptEvent, graph: TypedGraph) -> None:
    """Simple event application hook for testing.
    
    Supports operations:
    - add_node: adds a node to the graph
    - add_edge: adds an edge to the graph
    """
    if event.op_name == "add_node":
        node_id = event.inputs["node_id"]
        node_type = NodeType(event.inputs["node_type"])
        value = event.inputs.get("value")
        graph.add_node(node_id, node_type, value=value)
    
    elif event.op_name == "add_edge":
        edge_type = EdgeType(event.inputs["edge_type"])
        source = event.inputs["source"]
        target = event.inputs["target"]
        metadata = event.inputs.get("metadata")
        graph.add_edge(edge_type, source, target, metadata=metadata)


class TestReplayDeterminism:
    """Tests for deterministic replay of receipts."""

    def test_replay_constructs_same_graph_hash(self, tmp_path):
        """Replaying receipts should reconstruct the exact same graph hash."""
        # Build a graph with operations
        g1 = TypedGraph()
        hash0 = g1.state_hash()
        
        g1.add_node("n1", NodeType.NUMBER, value=3)
        hash1 = g1.state_hash()
        
        g1.add_node("n2", NodeType.NUMBER, value=5)
        hash2 = g1.state_hash()
        
        g1.add_node("n3", NodeType.NUMBER, value=8)
        hash3 = g1.state_hash()
        
        g1.add_edge(EdgeType.ADD, "n1", "n2", metadata={"result": "n3"})
        hash4 = g1.state_hash()
        
        # Create receipts for each operation
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        event1 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n1", "node_type": "Number", "value": 3},
            outputs={"node_id": "n1"},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash0,
            graph_hash_after=hash1,
            prev_receipt_hash=logger.get_prev_receipt_hash(),
        )
        logger.append(event1)
        
        event2 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n2", "node_type": "Number", "value": 5},
            outputs={"node_id": "n2"},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash1,
            graph_hash_after=hash2,
            prev_receipt_hash=logger.get_prev_receipt_hash(),
        )
        logger.append(event2)
        
        event3 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n3", "node_type": "Number", "value": 8},
            outputs={"node_id": "n3"},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash2,
            graph_hash_after=hash3,
            prev_receipt_hash=logger.get_prev_receipt_hash(),
        )
        logger.append(event3)
        
        event4 = ReceiptEvent.create(
            op_name="add_edge",
            inputs={
                "edge_type": "add",
                "source": "n1",
                "target": "n2",
                "metadata": {"result": "n3"},
            },
            outputs={},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash3,
            graph_hash_after=hash4,
            prev_receipt_hash=logger.get_prev_receipt_hash(),
        )
        logger.append(event4)
        
        # Replay from scratch
        g2 = TypedGraph()
        receipts = logger.read_all()
        replayer = ReceiptReplayer(apply_simple_event)
        g2_final = replayer.replay(receipts, g2)
        
        # Final hash should match
        assert g2_final.state_hash() == hash4
        assert g2_final.state_hash() == g1.state_hash()

    def test_replay_multiple_times_same_result(self, tmp_path):
        """Replaying same receipts multiple times should yield identical results."""
        # Create simple receipt sequence
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        g_original = TypedGraph()
        hash0 = g_original.state_hash()
        
        g_original.add_node("alice", NodeType.PERSON, value={"name": "Alice"})
        hash1 = g_original.state_hash()
        
        event1 = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "alice", "node_type": "Person", "value": {"name": "Alice"}},
            outputs={"node_id": "alice"},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash0,
            graph_hash_after=hash1,
            prev_receipt_hash="genesis",
        )
        logger.append(event1)
        
        # Replay 3 times
        receipts = logger.read_all()
        replayer = ReceiptReplayer(apply_simple_event)
        
        hashes = []
        for _ in range(3):
            g = TypedGraph()
            g_final = replayer.replay(receipts, g)
            hashes.append(g_final.state_hash())
        
        # All replays should produce identical hash
        assert len(set(hashes)) == 1
        assert hashes[0] == hash1

    def test_replay_detects_graph_hash_mismatch(self, tmp_path):
        """Replayer should detect when graph hash doesn't match expectations."""
        # Create receipt with intentionally wrong graph_hash_after
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        g = TypedGraph()
        hash_before = g.state_hash()
        
        # Create event with WRONG graph_hash_after
        event = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "n1", "node_type": "Number", "value":1},
            outputs={"node_id": "n1"},
            checker_reports=[],
            status="OK",
            graph_hash_before=hash_before,
            graph_hash_after="INTENTIONALLY_WRONG_HASH",  # Wrong!
            prev_receipt_hash="genesis",
        )
        
        # Manually write to bypass logger validation
        with open(logfile, 'w') as f:
            import json
            f.write(json.dumps(event.to_dict()) + '\n')
        
        # Replay should fail with ReplayMismatch
        receipts = logger.read_all()
        replayer = ReceiptReplayer(apply_simple_event)
        
        with pytest.raises(ReplayMismatch, match="graph_hash_after mismatch"):
            replayer.replay(receipts, TypedGraph())


class TestReplayWithValidation:
    """Tests for replay including checker reports."""

    def test_replay_preserves_checker_reports(self, tmp_path):
        """Replaying should preserve checker report data."""
        from neuralogix.core.checkers.base import CheckStatus
        
        logfile = tmp_path / "receipts.jsonl"
        logger = ReceiptLogger(logfile)
        
        g = TypedGraph()
        hash0 = g.state_hash()
        g.add_node("alice", NodeType.PERSON)
        hash1 = g.state_hash()
        
        # Create receipt with checker reports
        checker_reports = [
            {
                "checker": "TypeChecker",
                "status": "OK",
                "issues": [],
            },
            {
                "checker": "ConsistencyChecker",
                "status": "OK",
                "issues": [],
            },
        ]
        
        event = ReceiptEvent.create(
            op_name="add_node",
            inputs={"node_id": "alice", "node_type": "Person"},
            outputs={"node_id": "alice"},
            checker_reports=checker_reports,
            status="OK",
            graph_hash_before=hash0,
            graph_hash_after=hash1,
            prev_receipt_hash="genesis",
        )
        logger.append(event)
        
        # Replay
        receipts = logger.read_all()
        replayer = ReceiptReplayer(apply_simple_event)
        g2 = replayer.replay(receipts, TypedGraph())
        
        # Verify checker reports preserved
        assert receipts[0].checker_reports == checker_reports

    def test_empty_receipt_log_replays_to_empty_graph(self, tmp_path):
        """Replaying empty receipt log should leave graph unchanged."""
        logfile = tmp_path / "empty.jsonl"
        logfile.touch()  # Create empty file
        
        g = TypedGraph()
        hash_before = g.state_hash()
        
        logger = ReceiptLogger(logfile)
        receipts = logger.read_all()
        
        replayer = ReceiptReplayer(apply_simple_event)
        g_final = replayer.replay(receipts, g)
        
        assert g_final.state_hash() == hash_before
