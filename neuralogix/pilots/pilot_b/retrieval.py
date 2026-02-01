"""Mock Learned Retriever for Pilot B.3."""
import random
from typing import List, Tuple, Dict
from dataclasses import dataclass

@dataclass
class RetrievedFact:
    entity: str
    attribute: str
    value: str | int
    source: str
    score: float

class MockEmbeddingRetriever:
    """Simulates an embedding-based retriever."""

    def __init__(self, all_facts: List[Tuple]):
        """Initialize with full knowledge base.

        Args:
            all_facts: List of (entity, attr, value, source) tuples
        """
        self.kb = all_facts
        self.noise_facts = [
            ("Atlantis", "location", "Atlantic", "myth"),
            ("Moon", "made_of", "Cheese", "fable"),
            ("Earth", "shape", "Flat", "conspiracy"),
        ]

    def retrieve(self, query: str, k: int = 3) -> List[RetrievedFact]:
        """Retrieve top-K facts relevant to query.

        Simulates:
        1. Keyword matching (high score)
        2. Semantic drift / Hallucination injection (low score/noise)
        """
        query_lower = query.lower()
        results = []

        # 1. Simple Keyword Match (True Retrieval)
        for ent, attr, val, src in self.kb:
            # If entity name in query
            if ent.lower() in query_lower:
                # High score match
                results.append(RetrievedFact(ent, attr, val, src, 0.95))
            # If attribute in query
            elif attr.lower() in query_lower:
                # Medium score match
                results.append(RetrievedFact(ent, attr, val, src, 0.75))

        # 2. Inject Noise (Simulating retrieval errors)
        # Randomly pick a noise fact
        noise = random.choice(self.noise_facts)
        results.append(RetrievedFact(*noise, score=0.45))

        # Sort by score desc
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:k]
