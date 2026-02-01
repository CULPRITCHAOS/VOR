from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from .graph import TypedGraph, Fact

class DecisionStrategy(ABC):
    @abstractmethod
    def decide(self, entity: str, attribute: str, graph: TypedGraph) -> Dict[str, Any]:
        """
        Returns a dict with:
        - decision: ANSWER | CONFLICT | ABSTAIN
        - value: Any (if ANSWER)
        - evidence: List[Fact] or List[ConflictPair]
        - reasoning: str
        """
        pass

class TruthGateStrategy(DecisionStrategy):
    """
    Verified Proof Strategy: Only answers if 1 non-conflicting proof exists.
    """
    def decide(self, entity: str, attribute: str, graph: TypedGraph) -> Dict[str, Any]:
        facts_map = graph.get_facts(entity, attribute)
        
        if not facts_map:
            return {
                "decision": "ABSTAIN",
                "reasoning": f"MISSING: No facts found for {entity}.{attribute}"
            }
            
        if len(facts_map) > 1:
            # Conflict detected
            conflicts = []
            for val, facts in facts_map.items():
                conflicts.append({"value": val, "facts": [f.__dict__ for f in facts]})
            
            return {
                "decision": "CONFLICT",
                "evidence": conflicts,
                "reasoning": f"CONFLICT: Multiple values found for {entity}.{attribute}: {list(facts_map.keys())}"
            }
            
        # Single value found -> ANSWER
        val_norm = list(facts_map.keys())[0]
        # We return the original string for the first fact, as the evaluator expects 
        # the literal value found in text (or normalized as per gold records).
        facts = facts_map[val_norm]
        
        return {
            "decision": "ANSWER",
            "value": facts[0].value, 
            "evidence": [f.__dict__ for f in facts],
            "reasoning": "PROVEN: Single-hop grounding verified."
        }

class AlwaysAnswerBaseline(DecisionStrategy):
    """
    Aggressive Baseline: Always returns the most frequent value, ignoring conflicts.
    """
    def decide(self, entity: str, attribute: str, graph: TypedGraph) -> Dict[str, Any]:
        facts_map = graph.get_facts(entity, attribute)
        if not facts_map:
            return {"decision": "ABSTAIN", "reasoning": "Baseline abstains only on empty set."}
            
        # Pick value with most evidence
        sorted_vals = sorted(facts_map.items(), key=lambda x: len(x[1]), reverse=True)
        best_val_key, facts = sorted_vals[0]
        
        return {
            "decision": "ANSWER",
            "value": facts[0].value,
            "reasoning": "BASELINE: Always answer with max evidence."
        }

class ThresholdBaseline(DecisionStrategy):
    """
    Conservative Baseline: Answers if evidence count >= threshold.
    """
    def __init__(self, threshold: int = 2):
        self.threshold = threshold

    def decide(self, entity: str, attribute: str, graph: TypedGraph) -> Dict[str, Any]:
        facts_map = graph.get_facts(entity, attribute)
        if not facts_map:
            return {"decision": "ABSTAIN", "reasoning": "Threshold floor not met (0)."}
            
        sorted_vals = sorted(facts_map.items(), key=lambda x: len(x[1]), reverse=True)
        best_val_key, facts = sorted_vals[0]
        
        if len(facts) >= self.threshold:
            return {
                "decision": "ANSWER",
                "value": facts[0].value,
                "reasoning": f"BASELINE: Threshold {self.threshold} met."
            }
            
        return {
            "decision": "ABSTAIN",
            "reasoning": f"BASELINE: Threshold {self.threshold} not met (count={len(facts)})."
        }
