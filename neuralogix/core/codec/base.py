"""Codec interface for discrete substrates."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CodeResult:
    """Result of encoding operation.
    
    Represents encoded data with validity and quality metrics.
    """
    code: Any  # The encoded representation (e.g., hypervector, quantized vector)
    score: float  # Quality/similarity score (higher = better match)
    valid_hint: bool  # True if encoding is considered valid/on-manifold
    residual: Optional[Any] = None  # Optional residual vector ε
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        result = {
            "code": self._serialize_code(self.code),
            "score": self.score,
            "valid_hint": self.valid_hint,
            "residual": self._serialize_code(self.residual) if self.residual is not None else None,
            "metadata": self.metadata,
        }
        return result
    
    def _serialize_code(self, code: Any) -> Any:
        """Serialize code for JSON storage.
        
        Handles common code types:
        - bytes/bytearray -> hex string
        - list of ints -> list
        - dict -> dict
        - other -> str representation
        """
        if isinstance(code, (bytes, bytearray)):
            return code.hex()
        elif isinstance(code, (list, tuple)):
            return list(code)
        elif isinstance(code, (dict, int, float, bool)):
            return code
        else:
            return str(code)


class Codec:
    """Abstract codec interface for discrete substrates.
    
    Codecs provide encode/decode operations for mapping structured data
    to/from discrete representations (e.g., hypervectors, quantized vectors).
    
    All codecs must be:
    - Deterministic: same input -> same output
    - Serializable: outputs can be JSON-serialized
    - Validatable: provide validity metrics
    """
    
    def encode(self, target: Any) -> CodeResult:
        """Encode target into discrete representation.
        
        Args:
            target: Data to encode (e.g., graph node, subgraph)
            
        Returns:
            CodeResult with code, score, and validity
            
        Raises:
            NotImplementedError: If codec not implemented
        """
        raise NotImplementedError("Codec.encode not implemented")
    
    def decode(self, code: Any) -> Any:
        """Decode discrete representation back to target.
        
        Args:
            code: Encoded representation
            
        Returns:
            Decoded target (best-effort reconstruction)
            
        Raises:
            NotImplementedError: If codec not implemented
        """
        raise NotImplementedError("Codec.decode not implemented")
    
    def similarity(self, code_a: Any, code_b: Any) -> float:
        """Compute similarity between two codes.
        
        Args:
            code_a: First encoded representation
            code_b: Second encoded representation
            
        Returns:
            Similarity score (0.0 to 1.0, higher = more similar)
            
        Raises:
            NotImplementedError: If codec doesn't support similarity
        """
        raise NotImplementedError("Codec.similarity not implemented")
