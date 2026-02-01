import json
import hashlib
import os
from typing import List, Dict, Any

class PackLoader:
    """
    Loads and verifies standardized VOR Corpus Packs.
    Enforces byte-level binary integrity.
    """
    @staticmethod
    def compute_sha256(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def load_pack(self, pack_dir: str) -> Dict[str, Any]:
        manifest_path = os.path.join(pack_dir, "manifest.json")
        corpus_path = os.path.join(pack_dir, "corpus.jsonl")
        questions_path = os.path.join(pack_dir, "questions.jsonl")

        # 1. Verify Manifest
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        for file_info in manifest["files"]:
            f_path = os.path.join(pack_dir, file_info["path"])
            actual_hash = self.compute_sha256(f_path)
            if actual_hash != file_info["sha256"]:
                raise ValueError(f"Integrity check failed for {file_info['path']}. \nExpected: {file_info['sha256']}\nActual:   {actual_hash}")

        # 2. Load Data (Preserving binary stability by parsing line-by-line)
        corpus = []
        with open(corpus_path, "rb") as f:
            for line in f:
                if line.strip():
                    corpus.append(json.loads(line))

        questions = []
        with open(questions_path, "rb") as f:
            for line in f:
                if line.strip():
                    questions.append(json.loads(line))

        return {
            "metadata": manifest,
            "corpus": corpus,
            "questions": questions
        }

    @staticmethod
    def validate_question(q: Dict[str, Any]):
        """Strict schema enforcement for VOR questions."""
        required = ["q_id", "question_text", "entity", "attribute", "gold_decision"]
        for r in required:
            if r not in q:
                raise KeyError(f"Missing required field '{r}' in question {q.get('q_id')}")
        
        # Optional gold_support validation
        if "gold_support" in q:
            for s in q["gold_support"]:
                if "doc_id" not in s:
                    raise KeyError(f"gold_support missing 'doc_id' in question {q['q_id']}")
