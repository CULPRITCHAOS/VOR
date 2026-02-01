import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
from .graph import Provenance, TypedGraph

class Retriever:
    """
    Deterministic BM25-ish keyword retriever.
    Operates on a list of raw documents.
    """
    def __init__(self, corpus: List[Dict[str, str]]):
        self.corpus = corpus # List of {"id": str, "text": str}
        self.docs_per_word = Counter()
        for doc in corpus:
            words = set(self._tokenize(doc["text"]))
            for w in words:
                self.docs_per_word[w] += 1
        self.total_docs = len(corpus)

    def _tokenize(self, text: str) -> List[str]:
        """Granular tokenizer for better keyword matching in messy environments."""
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query_words = self._tokenize(query)
        scores = []
        
        for doc in self.corpus:
            doc_words = self._tokenize(doc["text"])
            doc_counter = Counter(doc_words)
            score = 0
            for w in query_words:
                if w in doc_counter:
                    # IDF
                    idf = math.log((self.total_docs + 1) / (self.docs_per_word[w] + 0.5))
                    # TF
                    tf = doc_counter[w]
                    score += tf * idf
            if score > 0:
                scores.append({"doc": doc, "score": score})
                
        scores.sort(key=lambda x: x["score"], reverse=True)
        return [s["doc"] for s in scores[:top_k]]

class Parser:
    """
    Extracts (Entity, Attr, Value, polarity, scope) from text using regex/patterns.
    Deterministic pattern-limited parser for VOR certification.
    """
    def __init__(self):
        # 1. Possessive: "Microsoft's revenue is $50B"
        self.re_possessive = re.compile(
            r"(?P<scope>as of [\w\s]+|in \d{4}, )?(?P<entity>[\w\s]+)'s\s+(?P<attr>[\w\s]+)\s+(?P<neg>is not|is)\s+(?P<val>[\w\s\$\.,/]+)", 
            re.IGNORECASE
        )
        # 2. Copula A: "The CEO of Acme is Alice"
        self.re_copula_a = re.compile(
            r"(?P<scope>as of [\w\s]+|in \d{4}, )?(?:the\s+)?(?P<attr>[\w\s]+)\s+of\s+(?P<entity>[\w\s]+)\s+(?P<neg>is not|is|was)\s+(?P<val>[\w\s\$\.,/]+)",
            re.IGNORECASE
        )
        # 3. Copula B: "Alice is the CEO of Acme"
        self.re_copula_b = re.compile(
            r"(?P<scope>as of [\w\s]+|in \d{4}, )?(?P<val>[\w\s\-\.]+)\s+(?P<neg>is not|is|was)\s+(?:the\s+)?(?P<attr>[\w\s]+)\s+of\s+(?P<entity>[\w\s\-\.]+)",
            re.IGNORECASE
        )
        # 4. General: "Project PJ_000 current status is Active"
        self.re_general = re.compile(
            r"(?P<scope>as of [\w\s]+|in \d{4}, )?(?:the\s+|project\s+)?(?P<entity>[\w\s\-\.]+?)\s+(?:current\s+)?(?P<attr>status|launch date|budget|type|version|revenue|earnings|deadline|winner|director|identity|capital|value|headquarters)\s+(?P<neg>is not|is|was)\s+(?P<val>[\w\s\$\.,\-/]+)",
            re.IGNORECASE
        )

    def parse_to_graph(self, docs: List[Dict[str, Any]], graph: TypedGraph, timestamp: str):
        for doc in docs:
            text = doc["text"]
            
            for pattern in [self.re_possessive, self.re_copula_a, self.re_copula_b, self.re_general]:
                for m in pattern.finditer(text):
                    d = m.groupdict()
                    entity = d["entity"].strip()
                    attr = d["attr"].strip()
                    val = d["val"].strip().strip(".").strip()
                    
                    # Polarity
                    polarity = "not" not in d["neg"].lower()
                    
                    # Scope (Time)
                    scope = None
                    if d.get("scope"):
                        scope = d["scope"].strip().lower().replace("as of ", "").replace("in ", "").strip(",")
                    
                    prov = Provenance(
                        doc_id=doc["id"],
                        span=m.group(0),
                        timestamp=timestamp
                    )
                    
                    # Add primary fact
                    graph.add_fact(entity, attr, val, prov, polarity=polarity, scope=scope)
                    
                    # Bidirectional fact for Copulas (e.g., Paris capital_of France)
                    if pattern in [self.re_copula_a, self.re_copula_b]:
                        # Map (Entity, Attr, Val) -> (Val, Attr + "_of", Entity)
                        # e.g. (France, capital, Paris) -> (Paris, capital_of, France)
                        # This handles "What country has Paris as its capital?"
                        graph.add_fact(val, f"{attr}_of", entity, prov, polarity=polarity, scope=scope)
