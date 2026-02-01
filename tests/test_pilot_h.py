import pytest
from neuralogix.pilots.pilot_h.run import PilotHRunner
from neuralogix.pilots.pilot_h.tools import Artifact, DataNode

def test_pilot_h_success_chain():
    """Verify standard gold path Retriever -> Parser -> Tester."""
    runner = PilotHRunner()
    success = runner.execute_chain("Find 42")
    
    assert success is True
    assert len(runner.receipts) == 3
    assert runner.receipts[0]["tool"] == "retriever"
    assert runner.receipts[2]["status"] == "ACCEPTED (OBSERVED)"

def test_pilot_h_retrieval_failure():
    """Verify that if retriever fails (returns None), the chain stops gracefully."""
    runner = PilotHRunner()
    success = runner.execute_chain("FAIL") # Mocked to return None
    
    assert success is False
    assert len(runner.receipts) == 1
    assert runner.receipts[0]["status"] == "COMPLETED (NONE_RETURNED)"

def test_pilot_h_contract_violation():
    """Adversarial: Verify that if a tool violated its contract, the runner rejects it."""
    runner = PilotHRunner()
    
    # Mock retriever to return something that isn't an Artifact (Violation of Post-condition)
    from neuralogix.pilots.pilot_h.tools import ToolRegistry
    ToolRegistry.retriever = lambda q: "I am not an Artifact"
    
    success = runner.execute_chain("hello")
    
    assert success is False
    assert runner.receipts[0]["status"] == "REJECTED (Contract Violation)"
    assert "produced invalid output" in runner.receipts[0]["error"]

def test_pilot_h_hallucination_gate():
    """Ensure the metrics reflect 0.0% hallucination."""
    runner = PilotHRunner()
    runner.execute_chain("Find 42")
    metrics = runner.generate_metrics(True)
    
    assert metrics["summary"]["hallucination_rate"] == 0.0
