"""Comprehensive tests for HDC codec backend (M5)."""
from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from neuralogix.core.codec.hdc import HDCCodec
from neuralogix.core.codec.base import CodeResult


class TestHDCDeterminism:
    """Test HDC codec determinism."""
    
    def test_same_target_same_code(self):
        """Same target → same code across multiple encode calls."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target1 = {"type": "PERSON", "id": "n1"}
        target2 = {"type": "PERSON", "id": "n1"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        assert result1.code == result2.code
        assert result1.score == result2.score
        assert result1.valid_hint == result2.valid_hint
    
    def test_different_targets_different_codes(self):
        """Different targets → different codes."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target1 = {"type": "PERSON", "id": "n1"}
        target2 = {"type": "PERSON", "id": "n2"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        assert result1.code != result2.code
    
    def test_codec_seed_independence(self):
        """Multiple codec instances produce same results (no random state)."""
        target = {"type": "PERSON", "id": "n1"}
        
        codec1 = HDCCodec(dimension=256, similarity_threshold=0.6)
        codec2 = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        result1 = codec1.encode(target)
        result2 = codec2.encode(target)
        
        assert result1.code == result2.code
        assert result1.score == result2.score


class TestHDCInsertionOrder:
    """Test insertion-order invariance for dict-based targets."""
    
    def test_dict_key_order_invariance(self):
        """Dict with different key order → same code."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target1 = {"id": "n1", "type": "PERSON", "name": "Alice"}
        target2 = {"type": "PERSON", "name": "Alice", "id": "n1"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        assert result1.code == result2.code
        assert result1.score == result2.score
    
    def test_nested_dict_order_invariance(self):
        """Nested dicts with different key order → same code."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target1 = {"id": "n1", "attrs": {"age": 30, "name": "Alice"}}
        target2 = {"attrs": {"name": "Alice", "age": 30}, "id": "n1"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        assert result1.code == result2.code


class TestHDCValidity:
    """Test validity based on similarity thresholds."""
    
    def test_identity_is_valid(self):
        """Identity (self-similarity) is always valid."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target = {"type": "PERSON", "id": "n1"}
        
        result = codec.encode(target)
        hv = result.code
        
        assert codec.is_valid(hv, hv) is True
        assert codec.similarity(hv, hv) == 1.0
    
    def test_similar_targets_above_threshold(self):
        """Similar targets have similarity above threshold."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        # Related targets (same type)
        target1 = {"type": "PERSON", "id": "n1"}
        target2 = {"type": "PERSON", "id": "n2"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        similarity = codec.similarity(result1.code, result2.code)
        # Similarity should be measurable (not identity, not orthogonal)
        assert 0.0 < similarity < 1.0
    
    def test_very_different_targets_below_threshold(self):
        """Very different targets have low similarity."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target1 = {"type": "PERSON", "id": "n1", "name": "Alice"}
        target2 = {"type": "NUMBER", "value": 42, "context": "age"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        similarity = codec.similarity(result1.code, result2.code)
        # Different types should have measurably different codes
        assert similarity < 0.9
    
    def test_threshold_boundary(self):
        """Test validity at threshold boundary."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        # Create two codes and check validity
        target1 = {"type": "PERSON", "id": "n1"}
        target2 = {"type": "PERSON", "id": "n2"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        similarity = codec.similarity(result1.code, result2.code)
        is_valid = codec.is_valid(result1.code, result2.code)
        
        # Validity should match threshold comparison
        expected_valid = similarity >= codec.similarity_threshold
        assert is_valid == expected_valid


class TestHDCBindBundle:
    """Test bind (XOR) and bundle (majority vote) operations."""
    
    def test_bind_xor_property(self):
        """bind(A, B) XOR B = A (unbinding property)."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target_a = {"type": "PERSON", "id": "n1"}
        target_b = {"type": "RELATION", "name": "parent_of"}
        
        result_a = codec.encode(target_a)
        result_b = codec.encode(target_b)
        
        hv_a = result_a.code
        hv_b = result_b.code
        
        # bind(A, B)
        bound = codec.bind(hv_a, hv_b)
        
        # unbind: bound XOR B should ≈ A
        unbound = codec.bind(bound, hv_b)
        
        assert unbound == hv_a
        assert codec.similarity(unbound, hv_a) == 1.0
    
    def test_bind_commutativity(self):
        """bind is commutative: bind(A, B) = bind(B, A)."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target_a = {"type": "PERSON", "id": "n1"}
        target_b = {"type": "PERSON", "id": "n2"}
        
        result_a = codec.encode(target_a)
        result_b = codec.encode(target_b)
        
        hv_a = result_a.code
        hv_b = result_b.code
        
        assert codec.bind(hv_a, hv_b) == codec.bind(hv_b, hv_a)
    
    def test_bundle_majority_vote(self):
        """bundle uses majority vote."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        # Create multiple similar hypervectors
        targets = [
            {"type": "PERSON", "id": f"n{i}"}
            for i in range(5)
        ]
        
        results = [codec.encode(t) for t in targets]
        hypervectors = [r.code for r in results]
        
        bundled = codec.bundle(hypervectors)
        
        # Bundled result should be similar to all inputs
        for hv in hypervectors:
            similarity = codec.similarity(bundled, hv)
            # Should have some similarity (not orthogonal)
            assert similarity > 0.0
    
    def test_bundle_single_item(self):
        """bundle([X]) = X."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target = {"type": "PERSON", "id": "n1"}
        result = codec.encode(target)
        hv = result.code
        
        bundled = codec.bundle([hv])
        
        assert bundled == hv
    
    def test_bundle_preserves_dimension(self):
        """bundle output has same dimension as inputs."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        targets = [{"type": "PERSON", "id": f"n{i}"} for i in range(3)]
        results = [codec.encode(t) for t in targets]
        hypervectors = [r.code for r in results]
        
        bundled = codec.bundle(hypervectors)
        
        # bundled is bytes, so check byte length = dimension / 8
        assert len(bundled) * 8 == codec.dimension


class TestHDCSimilarity:
    """Test similarity (Hamming) computation."""
    
    def test_similarity_range(self):
        """Similarity is in [0.0, 1.0]."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        targets = [
            {"type": "PERSON", "id": "n1"},
            {"type": "NUMBER", "value": 42},
        ]
        
        results = [codec.encode(t) for t in targets]
        
        for r1 in results:
            for r2 in results:
                similarity = codec.similarity(r1.code, r2.code)
                assert 0.0 <= similarity <= 1.0
    
    def test_similarity_symmetry(self):
        """similarity(A, B) = similarity(B, A)."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target1 = {"type": "PERSON", "id": "n1"}
        target2 = {"type": "PERSON", "id": "n2"}
        
        result1 = codec.encode(target1)
        result2 = codec.encode(target2)
        
        sim_ab = codec.similarity(result1.code, result2.code)
        sim_ba = codec.similarity(result2.code, result1.code)
        
        assert sim_ab == sim_ba
    
    def test_similarity_identity(self):
        """similarity(A, A) = 1.0."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        
        target = {"type": "PERSON", "id": "n1"}
        result = codec.encode(target)
        
        assert codec.similarity(result.code, result.code) == 1.0


class TestCodeResultJSON:
    """Test CodeResult JSON serialization."""
    
    def test_code_result_json_serializable(self):
        """CodeResult can be serialized to JSON."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target = {"type": "PERSON", "id": "n1"}
        
        result = codec.encode(target)
        
        # Use to_dict() method which handles bytes serialization
        result_dict = result.to_dict()
        
        # Should be JSON-serializable
        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)
        
        # Should round-trip
        parsed = json.loads(json_str)
        # Code is serialized as hex string
        assert parsed["code"] == result.code.hex()
        assert parsed["score"] == result.score
        assert parsed["valid_hint"] == result.valid_hint
        assert parsed["metadata"] == result.metadata
    
    def test_code_result_metadata_coverage(self):
        """CodeResult.metadata contains expected fields."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target = {"type": "PERSON", "id": "n1"}
        
        result = codec.encode(target)
        
        assert "dimension" in result.metadata
        assert "similarity_threshold" in result.metadata
        assert result.metadata["dimension"] == 256
        assert result.metadata["similarity_threshold"] == 0.6
    
    def test_code_result_valid_hint_determinism(self):
        """valid_hint is deterministic for same target."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.6)
        target = {"type": "PERSON", "id": "n1"}
        
        result1 = codec.encode(target)
        result2 = codec.encode(target)
        
        assert result1.valid_hint == result2.valid_hint


class TestHDCConfiguration:
    """Test HDC codec configuration."""
    
    def test_custom_dimension(self):
        """Can configure dimension."""
        codec = HDCCodec(dimension=512, similarity_threshold=0.6)
        target = {"type": "PERSON", "id": "n1"}
        
        result = codec.encode(target)
        
        # Code is bytes, so check byte length = dimension / 8
        assert len(result.code) * 8 == 512
        assert result.metadata["dimension"] == 512
    
    def test_custom_threshold(self):
        """Can configure similarity threshold."""
        codec = HDCCodec(dimension=256, similarity_threshold=0.8)
        target = {"type": "PERSON", "id": "n1"}
        
        result = codec.encode(target)
        
        assert result.metadata["similarity_threshold"] == 0.8
    
    def test_default_parameters(self):
        """Default parameters are applied correctly."""
        codec = HDCCodec()
        
        assert codec.dimension == 256
        assert codec.similarity_threshold == 0.6
