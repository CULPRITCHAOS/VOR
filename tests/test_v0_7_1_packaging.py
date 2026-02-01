import pytest
from click.testing import CliRunner
from neuralogix.cli.main import cli
from fastapi.testclient import TestClient
from neuralogix.api.server import app
import os
import json

@pytest.fixture
def runner():
    return CliRunner()

def test_cli_qa_fast(runner):
    pack_path = "data/packs/public_demo_v0_7_1"
    if not os.path.exists(pack_path):
        pytest.skip("Public demo pack not found")
        
    result = runner.invoke(cli, ["qa", "--pack", pack_path, "--fast"])
    assert result.exit_code == 0
    assert "VOR Audit Complete" in result.output

def test_cli_audit_fast(runner):
    result = runner.invoke(cli, ["audit", "--fast"])
    assert result.exit_code == 0
    assert "VOR AUDIT COMPLETE" in result.output

def test_cli_pack_validate(runner):
    pack_path = "data/packs/public_demo_v0_7_1"
    result = runner.invoke(cli, ["pack", "validate", "--pack", pack_path])
    assert result.exit_code == 0
    assert "Pack validated: public_demo_v0_7_1" in result.output
    assert "corpus.jsonl" in result.output

@pytest.fixture
def api_client():
    return TestClient(app)

def test_api_health(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "0.7.1"

def test_api_qa_run_inline(api_client):
    """Test inline JSON endpoint - must pass cleanly, no xfail allowed."""
    payload = {
        "corpus": [{"id": "d1", "text": "Project X is green."}],
        "questions": [{"q_id": "q1", "entity": "Project X", "attribute": "status", "question_text": "status?", "gold_decision": "ANSWER", "gold_value": "green"}],
        "metadata": {"pack_name": "test_api"},
        "seed": 42,
        "fast": True
    }
    response = api_client.post("/v1/qa/run", json=payload)
    # No xfail - must pass
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert "run_id" in data
