import json
import os
import random
import argparse
from typing import List, Dict, Any
from datetime import datetime, UTC
from .graph import TypedGraph
from .run import PilotIRunner
from .decisions import TruthGateStrategy, AlwaysAnswerBaseline, ThresholdBaseline
from ...core.packs.loader import PackLoader

class PilotIEvaluator:
    """
    v0.7 Evaluator: Optimized for VOR certification and external packs.
    """
    def __init__(self, pack_dir: str):
        loader = PackLoader()
        self.pack_data = loader.load_pack(pack_dir)
        self.corpus = self.pack_data["corpus"]
        self.ground_truth = self.pack_data["questions"]
        self.alias_map = self.pack_data["metadata"].get("aliases", {})

    def evaluate_strategy(self, strategy_class, name: str, evidence_path: str, fast: bool = False, seed: int = 42):
        strategy = strategy_class()
        runner = PilotIRunner(self.corpus, strategy, alias_map=self.alias_map)
        
        # Determine subset if fast mode
        gt_subset = self.ground_truth
        if fast and len(gt_subset) > 50:
            random.seed(seed)
            gt_subset = random.sample(gt_subset, 50)
            
        results = []
        for gt in gt_subset:
            # Re-mapping v0.7 questions to runner's expected format
            res = runner.ask(gt["question_text"], gt["entity"], gt["attribute"], gold={
                "expected_decision": gt["gold_decision"],
                "expected_value": gt.get("gold_value"),
                "gold_support": gt.get("gold_support")
            }, q_id=gt.get("q_id"))
            results.append({
                "gt": gt,
                "res": res,
                "obs_hash": runner.receipts[-1]["observations_hash"]
            })
            
        runner.write_evidence(evidence_path)
        metrics = self._calculate_metrics(results, name)
        return metrics, results

    def _calculate_metrics(self, results, strategy_name):
        total = len(results)
        conflicts_detected = 0
        hallucinations = 0
        correct_answers = 0
        missed_answers = 0 
        false_conflicts = 0
        
        ans_count = 0
        abstain_count = 0
        conflict_count = 0
        
        conflict_gt_count = sum(1 for r in results if r["gt"]["gold_decision"] == "CONFLICT")
        answerable_gt_count = sum(1 for r in results if r["gt"]["gold_decision"] == "ANSWER")
        
        # Verify Observation Parity (All strategy runs must see same data)
        # In a real run we aggregate across seeds, but here we track per execution
        obs_hashes = set(r["obs_hash"] for r in results)

        for item in results:
            gt = item["gt"]
            res = item["res"]
            decision = res["decision"]
            
            if decision == "ANSWER":
                ans_count += 1
                if gt["gold_decision"] == "ANSWER":
                    # Use normalized comparison to avoid formatting hallucinations (e.g. $5M vs 5,000,000)
                    v_res = TypedGraph.normalize_value(res["value"])
                    v_gold = TypedGraph.normalize_value(gt.get("gold_value"))
                    if v_res == v_gold:
                        correct_answers += 1
                    else:
                        hallucinations += 1
                else:
                    hallucinations += 1
            
            elif decision == "ABSTAIN":
                abstain_count += 1
                if gt["gold_decision"] == "ANSWER":
                    missed_answers += 1
            elif decision == "CONFLICT":
                conflict_count += 1
                
            if gt["gold_decision"] == "CONFLICT":
                if res["decision"] == "CONFLICT":
                    conflicts_detected += 1
            elif gt["gold_decision"] == "ANSWER":
                if res["decision"] == "CONFLICT":
                    false_conflicts += 1
                    
        return {
            "strategy": strategy_name,
            "metrics": {
                "total_questions": total,
                "hallucination_rate": hallucinations / total,
                "answer_accuracy": correct_answers / answerable_gt_count if answerable_gt_count > 0 else 0,
                "conflict_precision": conflicts_detected / (conflicts_detected + false_conflicts) if (conflicts_detected + false_conflicts) > 0 else 0,
                "conflict_recall": conflicts_detected / conflict_gt_count if conflict_gt_count > 0 else 0,
                "false_abstain_rate": missed_answers / answerable_gt_count if answerable_gt_count > 0 else 0,
                "observation_unique_hash_count": len(obs_hashes),
                "percent_answer": (ans_count / total) * 100 if total > 0 else 0,
                "percent_abstain": (abstain_count / total) * 100 if total > 0 else 0,
                "percent_conflict": (conflict_count / total) * 100 if total > 0 else 0
            }
        }

    def run_all(self, fast: bool = False, seeds: List[int] = [42]):
        print(f"VOR Certification: {self.pack_data['metadata']['pack_name']} (N={len(self.ground_truth)})")
        
        report = {
            "version": "v0.7.0-VOR",
            "timestamp": datetime.now(UTC).isoformat(),
            "pack_metadata": self.pack_data["metadata"],
            "strategies": []
        }
        
        for seed in seeds:
            e_path = f"results/pilot_i_vor_{seed}.evidence.jsonl"
            if os.path.exists(e_path): os.remove(e_path)
            
            m_tg, r_tg = self.evaluate_strategy(TruthGateStrategy, f"TruthGate_s{seed}", e_path, fast, seed)
            m_aa, r_aa = self.evaluate_strategy(AlwaysAnswerBaseline, f"AlwaysAnswer_s{seed}", e_path, fast, seed)
            m_tb, r_tb = self.evaluate_strategy(ThresholdBaseline, f"Threshold_s{seed}", e_path, fast, seed)

            # Strict Per-Question Parity Enforcement
            for i in range(len(r_tg)):
                tg_hash = r_tg[i]["obs_hash"]
                aa_hash = r_aa[i]["obs_hash"]
                tb_hash = r_tb[i]["obs_hash"]
                if tg_hash != aa_hash or tg_hash != tb_hash:
                    q_text = r_tg[i]["gt"]["question_text"]
                    raise ValueError(f"CRITICAL PARITY FAILURE [Seed {seed}, Q {i}]: '{q_text}'\n"
                                     f"TruthGate: {tg_hash}\nAlwaysAnswer: {aa_hash}\nThreshold: {tb_hash}")

            report["strategies"].extend([m_tg, m_aa, m_tb])
        
        out_path = f"results/pilot_i_{self.pack_data['metadata']['pack_name']}.summary.json"
        with open(out_path, "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"VOR Audit Complete: {out_path}")
        return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=str, required=True)
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    args = parser.parse_args()

    evaluator = PilotIEvaluator(args.pack)
    evaluator.run_all(fast=args.fast, seeds=args.seeds)
