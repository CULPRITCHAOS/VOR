"""Unit test for HTTP inline JSON endpoint."""
import pytest
from fastapi.testclient import TestClient
from neuralogix.api.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_api_inline_json_basic(client):
    """
    Test: POST /v1/qa/run with inline JSON must return 200.
    This test has no xfail escape hatch - it must pass cleanly.
    """
    payload = {
        "corpus": [
            {"id": "d1", "text": "Project Alpha is on track."},
            {"id": "d2", "text": "Project Beta was delayed to Q2."}
        ],
        "questions": [
            {
                "q_id": "q1", 
                "question_text": "What is the status of Project Alpha?",
                "entity": "Project Alpha", 
                "attribute": "status", 
                "gold_decision": "ANSWER", 
                "gold_value": "on track"
            }
        ],
        "metadata": {"pack_name": "test_inline"},
        "seed": 42,
        "fast": True
    }
    
    response = client.post("/v1/qa/run", json=payload)
    
    # Must be 200 - no xfail allowed
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "run_id" in data
    assert "summary" in data
