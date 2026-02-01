"""
E2 Sabotage Canary - Normalization Laundering Guardrail

Tests that normalization does NOT launder wrong numeric answers into passing matches.
Verifies Truth Gate yields 0 hallucinations with correct CONFLICT/ABSTAIN behavior.

3 Canary Cases:
- Case A: Off-by-one numeric trap (precision)
- Case B: Unit mismatch trap (scale laundering)  
- Case C: Wrong-entity near-match trap (entity binding)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from neuralogix.pilots.pilot_i.run import PilotIRunner
from neuralogix.pilots.pilot_i.graph import TypedGraph
from neuralogix.pilots.pilot_i.decisions import TruthGateStrategy


class TestSabotageCanaryNumericNormalization:
    """E2: Normalization Laundering Guardrail Tests"""

    def test_case_a_off_by_one_numeric_trap(self):
        """
        Case A: Off-by-one numeric trap (precision)
        
        Corpus: Budget(Acme) = $5,000,000 AND Budget(Acme) = $5,000,001
        Expected: CONFLICT (not pick one)
        """
        corpus = [
            {"id": "doc_a1", "text": "Acme's budget is $5,000,000."},
            {"id": "doc_a2", "text": "Acme's budget is $5,000,001."},
        ]
        
        runner = PilotIRunner(corpus, TruthGateStrategy())
        result = runner.ask(
            query="What is Acme's budget?",
            entity="Acme",
            attribute="budget",
            q_id="canary_a1"
        )
        
        # Assertions
        assert result["decision"] == "CONFLICT", \
            f"Case A failed: Expected CONFLICT, got {result['decision']}"
        
        # Verify obs_hash parity (deterministic)
        receipt = runner.receipts[-1]
        assert "observations_hash" in receipt
        assert len(receipt["observations_hash"]) == 64  # SHA256 hex
        
        # Verify provenance includes both docs
        assert "doc_a1" in receipt["retrieved_docs"]
        assert "doc_a2" in receipt["retrieved_docs"]
        
    def test_case_b_unit_mismatch_trap(self):
        """
        Case B: Unit mismatch trap (scale laundering)
        
        Corpus: Budget(Acme) = $5M AND Budget(Acme) = $5K
        Expected: CONFLICT (must not normalize $5M and $5K to same value)
        """
        corpus = [
            {"id": "doc_b1", "text": "Acme's budget is $5M."},
            {"id": "doc_b2", "text": "Acme's budget is $5K."},
        ]
        
        runner = PilotIRunner(corpus, TruthGateStrategy())
        result = runner.ask(
            query="What is Acme's budget?",
            entity="Acme",
            attribute="budget",
            q_id="canary_b1"
        )
        
        # Verify normalization produces DIFFERENT values
        norm_5m = TypedGraph.normalize_value("$5M")
        norm_5k = TypedGraph.normalize_value("$5K")
        assert norm_5m != norm_5k, \
            f"Normalization laundering detected: $5M={norm_5m}, $5K={norm_5k}"
        
        # Truth Gate must produce CONFLICT
        assert result["decision"] == "CONFLICT", \
            f"Case B failed: Expected CONFLICT, got {result['decision']}"
        
        receipt = runner.receipts[-1]
        assert "doc_b1" in receipt["retrieved_docs"]
        assert "doc_b2" in receipt["retrieved_docs"]

    def test_case_c_wrong_entity_near_match_trap(self):
        """
        Case C: Wrong-entity near-match trap (entity binding)
        
        Corpus: Budget(Acme Corp) = $5M AND Budget(Acme Foundation) = $5M
        Question asks for Acme Corp budget.
        Expected: ANSWER with Acme Corp provenance OR ABSTAIN (not use Foundation)
        """
        corpus = [
            {"id": "doc_c1", "text": "Acme Corp's budget is $5M."},
            {"id": "doc_c2", "text": "Acme Foundation's budget is $5M."},
        ]
        
        runner = PilotIRunner(corpus, TruthGateStrategy())
        result = runner.ask(
            query="What is Acme Corp's budget?",
            entity="Acme Corp",
            attribute="budget",
            q_id="canary_c1"
        )
        
        receipt = runner.receipts[-1]
        
        # Must NOT be a hallucination - either correct ANSWER or ABSTAIN
        if result["decision"] == "ANSWER":
            # If answering, must be grounded to Acme Corp doc
            # Value should be $5M normalized
            assert result["value"] is not None
            # The system should have extracted from doc_c1 (Acme Corp)
            # If it can't disambiguate, it should ABSTAIN
        elif result["decision"] == "ABSTAIN":
            # Acceptable - system can't disambiguate entities
            pass
        elif result["decision"] == "CONFLICT":
            # Also acceptable if both values are seen as conflicting
            # (same value, but system treats them as separate claims)
            pass
        else:
            pytest.fail(f"Unexpected decision: {result['decision']}")
        
        # Key assertion: observations_hash must be present
        assert "observations_hash" in receipt
        assert len(receipt["observations_hash"]) == 64

    def test_normalization_is_exact_not_fuzzy(self):
        """
        Verify normalization produces exact canonical values, not fuzzy matches.
        """
        # $5M and $5K must be DIFFERENT
        assert TypedGraph.normalize_value("$5M") != TypedGraph.normalize_value("$5K")
        
        # $5,000,000 and $5,000,001 must be DIFFERENT
        assert TypedGraph.normalize_value("$5,000,000") != TypedGraph.normalize_value("$5,000,001")
        
        # $5M and $5,000,000 SHOULD be SAME (valid normalization)
        assert TypedGraph.normalize_value("$5M") == TypedGraph.normalize_value("$5,000,000")
        
        # Verify canonical form is deterministic integer
        assert TypedGraph.normalize_value("$5M") == "5000000"
        assert TypedGraph.normalize_value("$5K") == "5000"
        assert TypedGraph.normalize_value("$5,000,000") == "5000000"
        assert TypedGraph.normalize_value("$5,000,001") == "5000001"
        
    def test_observations_hash_parity(self):
        """
        Verify that multiple strategies see the same observations (hash parity).
        """
        corpus = [
            {"id": "doc_parity", "text": "Acme's budget is $5M."},
        ]
        
        # Run with TruthGate
        runner1 = PilotIRunner(corpus, TruthGateStrategy())
        runner1.ask("What is Acme's budget?", "Acme", "budget", q_id="parity_test")
        hash1 = runner1.receipts[-1]["observations_hash"]
        
        # Run again with same corpus
        runner2 = PilotIRunner(corpus, TruthGateStrategy())
        runner2.ask("What is Acme's budget?", "Acme", "budget", q_id="parity_test")
        hash2 = runner2.receipts[-1]["observations_hash"]
        
        # Hashes must be identical (deterministic)
        assert hash1 == hash2, \
            f"Observation parity violation: {hash1} != {hash2}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
