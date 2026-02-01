"""HDC (Hyperdimensional Computing) codec implementation.

Uses content-addressed binary hypervectors derived from SHA256 hashing.
NO randomness - all hypervectors deterministically derived from content.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from neuralogix.core.codec.base import Codec, CodeResult


class HDCCodec(Codec):
    """HDC codec with deterministic binary hypervectors.
    
    Uses SHA256-based content addressing to generate hypervectors:
    - No random seeds
    - Same content always produces same hypervector
    - Bit operations: XOR (bind), majority vote (bundle)
    """
    
    def __init__(self, dimension: int = 256, similarity_threshold: float = 0.6):
        """Initialize HDC codec.
        
        Args:
            dimension: Hypervector dimension (must be multiple of 8 for byte alignment)
            similarity_threshold: Minimum similarity for valid_hint (0.0 to 1.0)
        """
        if dimension % 8 != 0:
            raise ValueError(f"Dimension must be multiple of 8, got {dimension}")
        if not 0.0 <= similarity_threshold <= 1.0:
            raise ValueError(f"Threshold must be in [0, 1], got {similarity_threshold}")
        
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self._codebook: Dict[str, bytes] = {}  # Cache for derived hypervectors
    
    def encode(self, target: Any) -> CodeResult:
        """Encode target into binary hypervector.
        
        Generates a deterministic hypervector from the canonical JSON of the target.
        
        Args:
            target: Data to encode (dict, str, number, etc.)
            
        Returns:
            CodeResult with binary hypervector
        """
        # Generate hypervector from content
        hv = self._derive_hypervector(target)
        
        # For encoding, similarity to self is 1.0
        score = 1.0
        valid_hint = True
        
        metadata = {
            "dimension": self.dimension,
            "similarity_threshold": self.similarity_threshold,
            "num_ones": bin(int.from_bytes(hv, 'big')).count('1'),
        }
        
        return CodeResult(
            code=hv,
            score=score,
            valid_hint=valid_hint,
            metadata=metadata,
        )
    
    def decode(self, code: Any) -> Any:
        """Decode hypervector (best-effort).
        
        HDC encoding is lossy - perfect decoding not guaranteed.
        Returns the code itself as bytes.
        
        Args:
            code: Binary hypervector (bytes or hex string)
            
        Returns:
            Hypervector as bytes
        """
        if isinstance(code, str):
            return bytes.fromhex(code)
        elif isinstance(code, bytes):
            return code
        else:
            raise ValueError(f"Code must be bytes or hex string, got {type(code)}")
    
    def similarity(self, code_a: Any, code_b: Any) -> float:
        """Compute Hamming similarity between hypervectors.
        
        Similarity = 1 - (hamming_distance / dimension)
        
        Args:
            code_a: First hypervector
            code_b: Second hypervector
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Ensure both are bytes
        if isinstance(code_a, str):
            code_a = bytes.fromhex(code_a)
        if isinstance(code_b, str):
            code_b = bytes.fromhex(code_b)
        
        if len(code_a) != len(code_b):
            raise ValueError(f"Hypervector length mismatch: {len(code_a)} vs {len(code_b)}")
        
        # Compute Hamming distance
        hamming_dist = sum(bin(a ^ b).count('1') for a, b in zip(code_a, code_b))
        
        # Convert to similarity (1.0 = identical, 0.0 = completely different)
        similarity = 1.0 - (hamming_dist / self.dimension)
        
        return similarity
    
    def bind(self, hv_a: bytes, hv_b: bytes) -> bytes:
        """Bind two hypervectors using XOR.
        
        Binding is invertible: bind(bind(a, b), b) == a
        
        Args:
            hv_a: First hypervector
            hv_b: Second hypervector
            
        Returns:
            Bound hypervector
        """
        if len(hv_a) != len(hv_b):
            raise ValueError(f"Hypervector length mismatch: {len(hv_a)} vs {len(hv_b)}")
        
        return bytes(a ^ b for a, b in zip(hv_a, hv_b))
    
    def bundle(self, hypervectors: List[bytes]) -> bytes:
        """Bundle multiple hypervectors using majority vote.
        
        For each bit position, take the majority value across all vectors.
        
        Args:
            hypervectors: List of hypervectors to bundle
            
        Returns:
            Bundled hypervector
        """
        if not hypervectors:
            raise ValueError("Cannot bundle empty list")
        
        dimension_bytes = len(hypervectors[0])
        if any(len(hv) != dimension_bytes for hv in hypervectors):
            raise ValueError("All hypervectors must have same dimension")
        
        # Convert to bits for easier majority vote
        bit_counts = [0] * (dimension_bytes * 8)
        
        for hv in hypervectors:
            bits = bin(int.from_bytes(hv, 'big'))[2:].zfill(dimension_bytes * 8)
            for i, bit in enumerate(bits):
                if bit == '1':
                    bit_counts[i] += 1
        
        # Majority vote
        threshold = len(hypervectors) / 2.0
        result_bits = ''.join('1' if count > threshold else '0' for count in bit_counts)
        
        # Convert back to bytes
        result_int = int(result_bits, 2)
        result_bytes = result_int.to_bytes(dimension_bytes, 'big')
        
        return result_bytes
    
    def is_valid(self, code: bytes, reference: Optional[bytes] = None) -> bool:
        """Check if code is valid based on similarity threshold.
        
        Args:
            code: Hypervector to validate
            reference: Optional reference hypervector (if None, always returns True)
            
        Returns:
            True if similarity >= threshold or no reference provided
        """
        if reference is None:
            return True
        
        sim = self.similarity(code, reference)
        return sim >= self.similarity_threshold
    
    def _derive_hypervector(self, target: Any) -> bytes:
        """Derive deterministic hypervector from target content.
        
        Uses SHA256 hash of canonical JSON to generate bits.
        Expands hash to desired dimension by repeatedly hashing.
        
        Args:
            target: Content to derive from
            
        Returns:
            Binary hypervector
        """
        # Create canonical representation
        canonical = self._canonicalize(target)
        
        # Check cache
        if canonical in self._codebook:
            return self._codebook[canonical]
        
        # Generate hypervector by expanding SHA256 hash
        dimension_bytes = self.dimension // 8
        hv_bytes = bytearray()
        
        seed = canonical.encode('utf-8')
        counter = 0
        
        while len(hv_bytes) < dimension_bytes:
            # Hash with counter to generate more bits
            h = hashlib.sha256(seed + str(counter).encode()).digest()
            hv_bytes.extend(h[:min(32, dimension_bytes - len(hv_bytes))])
            counter += 1
        
        result = bytes(hv_bytes[:dimension_bytes])
        
        # Cache result
        self._codebook[canonical] = result
        
        return result
    
    def _canonicalize(self, target: Any) -> str:
        """Create canonical string representation of target.
        
        Args:
            target: Data to canonicalize
            
        Returns:
            Canonical JSON string
        """
        if isinstance(target, (dict, list)):
            return json.dumps(target, sort_keys=True, separators=(',', ':'))
        elif isinstance(target, str):
            return target
        elif isinstance(target, (int, float, bool)):
            return str(target)
        elif target is None:
            return "null"
        else:
            # Fallback to string representation
            return str(target)
