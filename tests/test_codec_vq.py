"""Tests for VQ codec."""
from __future__ import annotations

import json
import torch
import pytest
from neuralogix.core.codec.vq import VQCodec
from neuralogix.core.ir.schema import NodeType


def test_vq_codec_initialization():
    codec = VQCodec(dimension=16, codebook_size=32)
    assert codec.dimension == 16
    assert codec.codebook_size == 32
    assert NodeType.NUMBER.value in codec.codebooks
    assert codec.codebooks[NodeType.NUMBER.value].shape == (32, 16)


def test_vq_encoding_untrained():
    # Untrained codebook (all zeros)
    codec = VQCodec(dimension=8, codebook_size=10)
    target = {"type": NodeType.NUMBER.value, "value": 42}
    
    result = codec.encode(target)
    
    # Distance to zero vector for [42, 0, ...] is 42
    # score = 1 / (1 + 42) = 1/43 approx 0.023
    assert result.code == 0 # First index in all-zeros book
    assert result.score < 0.1
    assert result.valid_hint is False


def test_vq_encoding_trained_toy():
    codec = VQCodec(dimension=4, codebook_size=10)
    
    # Manually populate a codebook entry
    # Entry 3: [10, 0, 0, 0]
    codec.codebooks[NodeType.NUMBER.value][3] = torch.tensor([10.0, 0.0, 0.0, 0.0])
    
    # Target value 10
    target = {"type": NodeType.NUMBER.value, "value": 10}
    result = codec.encode(target)
    
    assert result.code == 3
    assert result.score == 1.0 # Exact match
    assert result.valid_hint is True


def test_vq_per_type_isolation():
    codec = VQCodec(dimension=4, codebook_size=10)
    
    # Entry 1 in NUMBER: [5, 0, 0, 0]
    # Entry 1 in PERSON: [1, 1, 1, 1]
    codec.codebooks[NodeType.NUMBER.value][1] = torch.tensor([5.0, 0.0, 0.0, 0.0])
    codec.codebooks[NodeType.PERSON.value][1] = torch.tensor([1.0, 1.0, 1.0, 1.0])
    
    # Same "value" but different type
    target_num = {"type": NodeType.NUMBER.value, "value": 5}
    target_person = {"type": NodeType.PERSON.value, "value": {"name": "Test"}} # Will hash to something else
    
    res_num = codec.encode(target_num)
    res_person = codec.encode(target_person)
    
    assert res_num.code == 1
    assert res_person.code != 1 or res_person.score < 1.0 # Unlikely to match exactly


def test_vq_json_serialization():
    codec = VQCodec(dimension=4, codebook_size=10)
    target = {"type": NodeType.NUMBER.value, "value": 5}
    result = codec.encode(target)
    
    d = result.to_dict()
    json_str = json.dumps(d)
    
    restored = json.loads(json_str)
    assert restored["code"] == result.code
    assert restored["score"] == result.score
    assert restored["metadata"]["node_type"] == NodeType.NUMBER.value
