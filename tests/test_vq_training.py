"""Tests for VQ trainer."""
from __future__ import annotations

import pytest
import torch
from neuralogix.core.data.generator import SyntheticDataGenerator
from neuralogix.core.codec.vq import VQCodec
from neuralogix.core.codec.vq_trainer import VQTrainer
from neuralogix.core.ir.schema import NodeType


def test_vq_training_convergence():
    # 1. Generate data (simple numbers)
    gen = SyntheticDataGenerator(seed=42)
    graph = gen.generate_arithmetic_sequence(count=50, max_val=10)
    
    # 2. Setup codec and trainer
    # Low dimension and small book to ensure overlap
    codec = VQCodec(dimension=4, codebook_size=5)
    trainer = VQTrainer(codec)
    
    # 3. Train
    # Initial codebook is all zeros
    assert torch.all(codec.codebooks[NodeType.NUMBER.value] == 0)
    
    trainer.train([graph], iterations=5)
    
    # 4. Verify book is populated
    # Should not be all zeros anymore
    book = codec.codebooks[NodeType.NUMBER.value]
    assert not torch.all(book == 0)
    
    # 5. Verify encoding quality
    # Should find near-perfect matches for numbers used in training
    target = {"type": NodeType.NUMBER.value, "value": 5}
    result = codec.encode(target)
    
    # With 5 clusters for numbers 0-10, we might have error around 1.0
    assert result.score >= 0.5 # Reasonable match


def test_vq_training_save_load():
    import tempfile
    import os
    
    codec = VQCodec(dimension=4, codebook_size=5)
    codec.codebooks[NodeType.NUMBER.value][0] = torch.tensor([1.0, 2.0, 3.0, 4.0])
    
    with tempfile.NamedTemporaryFile(suffix='.pth', delete=False) as f:
        path = f.name
        
    try:
        codec.save_codebooks(path)
        
        new_codec = VQCodec(dimension=4, codebook_size=5)
        new_codec.load_codebooks(path)
        
        assert torch.all(new_codec.codebooks[NodeType.NUMBER.value][0] == codec.codebooks[NodeType.NUMBER.value][0])
    finally:
        if os.path.exists(path):
            os.remove(path)
