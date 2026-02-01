import time
import json
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from .graph import TypedGraph
from .tools import Retriever, Parser
from .decisions import DecisionStrategy
from ...core.audit.outcome_verifier import OutcomeVerifier

class PilotIRunner:
    """
    The main orchestrator for Pilot I Grounded QA.
    """
    def __init__(self, corpus: List[Dict[str, str]], strategy: DecisionStrategy, alias_map: Optional[Dict[str, str]] = None):
        self.corpus = corpus
        self.retriever = Retriever(corpus)
        self.parser = Parser()
        self.strategy = strategy
        self.alias_map = alias_map
        self.receipts = []

    def ask(self, query: str, entity: str, attribute: str, gold: Optional[Dict[str, Any]] = None, q_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the grounded QA loop: Retrieve -> Parse -> Decide.
        """
        timestamp = datetime.now(UTC).isoformat()
        
        # 1. Retrieve (Observation)
        docs = self.retriever.retrieve(query)
        
        # 2. Parse (Observation)
        graph = TypedGraph(alias_map=self.alias_map)
        self.parser.parse_to_graph(docs, graph, timestamp)
        
        # 3. Canonical Observations Hash (The 'Patched' VOR requirement)
        # Hash doc IDs + normalized facts in order
        obs_payload = {
            "docs": sorted([doc["id"] for doc in docs]),
            "facts": sorted([f"{e}|{a}|{graph.normalize_value(v)}" 
                            for (e, a), vals in graph.nodes.items() 
                            for v in vals])
        }
        import hashlib
        obs_hash = hashlib.sha256(json.dumps(obs_payload, sort_keys=True).encode()).hexdigest()

        # 4. Decide (The Strategy)
        result = self.strategy.decide(entity, attribute, graph)
        
        # 5. Receipt (Traceability)
        receipt = {
            "q_id": q_id,
            "query": query,
            "target": f"{entity}.{attribute}",
            "retrieved_docs": obs_payload["docs"],
            "observations_hash": obs_hash,
            "extracted_facts_count": len(obs_payload["facts"]),
            "decision": result["decision"],
            "value": result.get("value"),
            "strategy": self.strategy.__class__.__name__,
            "timestamp": timestamp
        }
        
        if gold:
            receipt["gold_decision"] = gold.get("expected_decision")
            receipt["gold_value"] = gold.get("expected_value")
            # Link to gold support for audit
            if "gold_support" in gold:
                receipt["gold_support"] = gold["gold_support"]
            
        self.receipts.append(receipt)
        
        return result

    def write_evidence(self, path: str = "results/pilot_i.evidence.jsonl"):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            for r in self.receipts:
                f.write(json.dumps(r) + "\n")
        self.receipts = [] # Clear after write
