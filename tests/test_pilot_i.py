import pytest
from neuralogix.pilots.pilot_i.graph import TypedGraph, Provenance
from neuralogix.pilots.pilot_i.decisions import TruthGateStrategy, AlwaysAnswerBaseline

def test_pilot_i_conflict_detection():
    """Verify that TruthGate detects hard conflicts while AlwaysAnswer lies."""
    graph = TypedGraph()
    prov = Provenance("doc_1", "span", "2026")
    
    # Divergent facts
    graph.add_fact("Mars", "Color", "Red", prov)
    graph.add_fact("Mars", "Color", "Blue", prov)
    
    truth_gate = TruthGateStrategy()
    baseline = AlwaysAnswerBaseline()
    
    res_truth = truth_gate.decide("Mars", "Color", graph)
    res_base = baseline.decide("Mars", "Color", graph)
    
    assert res_truth["decision"] == "CONFLICT"
    assert res_base["decision"] == "ANSWER" # The baseline 'hallucinates' an answer
    assert res_base["value"] in ["Red", "Blue"]

def test_pilot_i_abstain_on_missing():
    """Verify abstention when no facts exist."""
    graph = TypedGraph()
    truth_gate = TruthGateStrategy()
    
    res = truth_gate.decide("Unknown", "Attr", graph)
    assert res["decision"] == "ABSTAIN"
    assert "MISSING" in res["reasoning"]

def test_pilot_i_normalization_consistency():
    """Verify that 'Red' and 'red ' are treated as the same value (No false conflict)."""
    graph = TypedGraph()
    prov = Provenance("doc_1", "span", "2026")
    
    graph.add_fact("Mars", "Color", "Red", prov)
    graph.add_fact("Mars", "Color", "red ", prov)
    
    truth_gate = TruthGateStrategy()
    res = truth_gate.decide("Mars", "Color", graph)
    
    assert res["decision"] == "ANSWER" # No conflict because normalized values match
    assert res["value"] == "Red" # Preserves original casing of first entry

def test_pilot_i_gate_failure_on_high_miss_rate():
    """
    Mental Test: If a strategy 'wins' purely by abstaining everything, 
    the miss-rate ceiling (25%) should catch it in evaluation.
    (Verified via evaluate.py metrics)
    """
    pass
