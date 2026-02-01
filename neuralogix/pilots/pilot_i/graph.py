from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
import json
import re

@dataclass(frozen=True)
class Provenance:
    doc_id: str
    span: str
    timestamp: str

@dataclass(frozen=True)
class Fact:
    entity: str
    attribute: str
    value: Any
    provenance: Provenance
    polarity: bool = True
    scope: Optional[str] = None

class TypedGraph:
    """
    A single-hop in-memory fact graph for Pilot I.
    Enforces hard-conflict detection with aliasing support.
    """
    def __init__(self, alias_map: Optional[Dict[str, str]] = None):
        # (entity, attr) -> { normalized_value -> [Facts] }
        self.nodes: Dict[Tuple[str, str], Dict[str, List[Fact]]] = {}
        # Simple alias normalization (alias -> canonical)
        self.alias_map = {}
        if alias_map:
            for canonical, aliases in alias_map.items():
                c_norm = self.normalize_raw(canonical)
                for alias in aliases:
                    self.alias_map[self.normalize_raw(alias)] = c_norm

    @staticmethod
    def normalize_raw(text: str) -> str:
        return text.strip().lower()

    def normalize_key(self, text: str) -> str:
        norm = self.normalize_raw(text)
        return self.alias_map.get(norm, norm)

    @staticmethod
    def normalize_value(val: Any) -> str:
        if val is None:
            return "none"
        s = str(val).strip().lower()
        
        # Numeric normalization: Target "$5M", "5,000,000", but avoid "v2.0"
        # Rule: Must have $ or end with K/M/B or be purely digits+commas
        is_currency = s.startswith("$")
        has_suffix = any(s.endswith(suffix) for suffix in ["k", "m", "b"])
        is_pure_num = re.match(r"^[\d,.]+$", s) is not None
        
        if is_currency or has_suffix or is_pure_num:
            num_str = s.replace("$", "").replace(",", "").replace(" ", "")
            multipliers = {"k": 1000, "m": 1000000, "b": 1000000000}
            for char, mult in multipliers.items():
                if num_str.endswith(char):
                    try:
                        base_str = num_str[:-1]
                        base = float(base_str)
                        return str(int(base * mult))
                    except ValueError:
                        pass
            try:
                # Only if it's purely a number
                if re.match(r"^[\d.]+$", num_str):
                    return str(int(float(num_str)))
            except ValueError:
                pass
        return s

    def add_fact(self, entity: str, attribute: str, value: Any, provenance: Provenance, polarity: bool = True, scope: Optional[str] = None):
        e_norm = self.normalize_key(entity)
        a_norm = self.normalize_raw(attribute)
        v_norm = self.normalize_value(value)
        
        # Include polarity and scope in the key for conflict detection?
        # No, the logic for TruthGate is "1 non-conflicting proof".
        # If we have (X, CEO, Bob, scope=2020) and (X, CEO, Alice, scope=2024), 
        # the strategy needs to decide. For now, we store them together.
        key = (e_norm, a_norm)
        if key not in self.nodes:
            self.nodes[key] = {}
            
        val_key = f"{v_norm}|{polarity}|{scope or ''}"
        if val_key not in self.nodes[key]:
            self.nodes[key][val_key] = []
            
        self.nodes[key][val_key].append(Fact(e_norm, a_norm, value, provenance, polarity, scope))

    def get_facts(self, entity: str, attribute: str) -> Dict[str, List[Fact]]:
        """Returns map of normalized_value -> List[Facts]"""
        return self.nodes.get((self.normalize_key(entity), self.normalize_raw(attribute)), {})

    def get_provenance(self, entity: str, attribute: str, value: Any) -> List[Provenance]:
        facts = self.get_facts(entity, attribute).get(self.normalize_value(value), [])
        return [f.provenance for f in facts]

    def has_conflict(self, entity: str, attribute: str) -> bool:
        """Returns True if there are >1 distinct normalized values for this (entity, attr)."""
        return len(self.get_facts(entity, attribute)) > 1
