"""VQ (Vector Quantization) codec implementation."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

import torch
from neuralogix.core.codec.base import Codec, CodeResult
from neuralogix.core.ir.schema import NodeType


class VQCodec(Codec):
    """Codec using Vector Quantization with per-type codebooks."""

    def __init__(self, dimension: int = 32, codebook_size: int = 64):
        """Initialize VQ codec.
        
        Args:
            dimension: Dimension of the continuous embeddings
            codebook_size: Number of entries in each per-type codebook
        """
        self.dimension = dimension
        self.codebook_size = codebook_size
        
        # Per-type codebooks: NodeType -> Tensor [codebook_size, dimension]
        self.codebooks: Dict[str, torch.Tensor] = {}
        
        # Initialize default codebooks with zeros (must be trained/populated)
        for node_type in NodeType:
            self.codebooks[node_type.value] = torch.zeros((codebook_size, dimension))

    def encode(self, target: Any) -> CodeResult:
        """Encode target by mapping to nearest codebook entry.
        
        Args:
            target: Node data (Node object or dict)
            
        Returns:
            CodeResult
        """
        # Determine type
        if hasattr(target, "node_type"):
            node_type = target.node_type.value if hasattr(target.node_type, "value") else str(target.node_type)
        else:
            node_type = target.get("type", target.get("node_type", "UNKNOWN"))
            
        embedding = self._embed(target)
        
        # 2. Vector Quantization
        codebook = self.codebooks.get(node_type)
        if codebook is None:
            return CodeResult(code=-1, score=0.0, valid_hint=False)
            
        # Compute Euclidean distance
        # embedding: [dim], codebook: [book_size, dim]
        distances = torch.norm(codebook - embedding, dim=1)
        min_idx = torch.argmin(distances).item()
        min_dist = distances[min_idx].item()
        
        # 3. Compute residual vector ε = embedding - codeword
        codeword = codebook[min_idx]
        residual = (embedding - codeword).tolist()
        
        # 4. Compute score
        score = 1.0 / (1.0 + min_dist)
        valid_hint = score > 0.5
        
        metadata = {
            "node_type": node_type,
            "dimension": self.dimension,
            "quantization_error": min_dist,
            "residual_norm": min_dist, # Euclidean norm of ε
        }
        
        return CodeResult(
            code=int(min_idx),
            score=score,
            valid_hint=valid_hint,
            residual=residual,
            metadata=metadata
        )

    def decode(self, code: Any) -> Any:
        """Decode index back to vector (best-effort).
        
        Note: Requires knowing the type to select the right codebook.
        For general decoding, code could be a tuple (type, index).
        
        Args:
            code: Index or (type, index) tuple
            
        Returns:
            Reconstructed vector as list
        """
        if isinstance(code, (list, tuple)) and len(code) == 2:
            node_type, idx = code
        else:
            # Fallback for simple index (logic incomplete without type)
            return None
            
        codebook = self.codebooks.get(node_type)
        if codebook is None or idx < 0 or idx >= self.codebook_size:
            return None
            
        return codebook[idx].tolist()

    def similarity(self, code_a: Any, code_b: Any) -> float:
        """Compute similarity between two codes.
        
        In VQ, similarity is 1.0 if indices match, or based on codebook distance.
        Simplified version: 1.0 if identical, 0.0 otherwise (discrete).
        
        Args:
            code_a: First code (index)
            code_b: Second code (index)
            
        Returns:
            1.0 if identical, 0.0 otherwise
        """
        return 1.0 if code_a == code_b else 0.0

    def _embed(self, target: Any) -> torch.Tensor:
        """Map target content to a continuous embedding vector."""
        if hasattr(target, "node_type"):
            node_type = target.node_type.value if hasattr(target.node_type, "value") else str(target.node_type)
            value = target.value
        else:
            node_type = target.get("type", target.get("node_type"))
            value = target.get("value")
        
        vec = torch.zeros(self.dimension)
        
        if node_type == NodeType.NUMBER.value:
            if isinstance(value, (int, float)):
                vec[0] = float(value)
        elif node_type == NodeType.PERSON.value:
            canonical = json.dumps(value, sort_keys=True)
            h = hashlib.sha256(canonical.encode()).digest()
            for i in range(min(len(h), self.dimension)):
                vec[i] = float(h[i]) / 255.0
        else:
            canonical = str(target)
            h = hashlib.sha256(canonical.encode()).digest()
            for i in range(min(len(h), self.dimension)):
                vec[i] = float(h[i]) / 255.0
                
        return vec

    def save_codebooks(self, path: str):
        """Save codebooks to disk."""
        torch.save(self.codebooks, path)
        
    def load_codebooks(self, path: str):
        """Load codebooks from disk."""
        self.codebooks = torch.load(path)
