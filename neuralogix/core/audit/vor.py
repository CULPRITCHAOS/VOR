import os
import json
from datetime import datetime, UTC

def run_pack_in_process(pack_path, fast=False, seeds=[42]):
    """Runs a pack evaluation in-process."""
    # Import here to avoid circular dependency with evaluate.py
    from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
    print(f"Auditing Pack: {pack_path} (Fast: {fast}, Seeds: {seeds})")
    evaluator = PilotIEvaluator(pack_path)
    return evaluator.run_all(fast=fast, seeds=seeds)

def audit_vor(fast=False, packs=None):
    """
    Runs the full VOR certification audit.
    Can be called from CLI or API.
    """
    if packs is None:
        packs = [
            "data/packs/v0_6_legacy",
            "data/packs/v0_7_stress",
            "data/packs/adversarial_v1"
        ]
    
    seeds = [0, 1, 2, 3, 4] if not fast else [42]
    
    dashboard = {
        "title": "NeuraLogix VOR Certification Dashboard",
        "timestamp": datetime.now(UTC).isoformat(),
        "fast_mode": fast,
        "results": []
    }
    
    for pack in packs:
        if not os.path.exists(pack):
            print(f"⚠️  Skipping missing pack: {pack}")
            continue
            
        summary = run_pack_in_process(pack, fast, seeds)
        
        # Aggregate TruthGate metrics across all seeds
        tg_metrics = [s["metrics"] for s in summary["strategies"] if s["strategy"].startswith("TruthGate")]
        
        if not tg_metrics:
            continue

        # We report the worst-case (max for hallucination, min for others) for certification
        metrics_summary = {
            "total_questions": tg_metrics[0]["total_questions"],
            "hallucination_rate": max(m["hallucination_rate"] for m in tg_metrics),
            "answer_accuracy": min(m["answer_accuracy"] for m in tg_metrics),
            "conflict_precision": min(m["conflict_precision"] for m in tg_metrics),
            "conflict_recall": min(m["conflict_recall"] for m in tg_metrics),
            "false_abstain_rate": max(m["false_abstain_rate"] for m in tg_metrics),
            "observation_unique_hash_count": max(m["observation_unique_hash_count"] for m in tg_metrics),
            "percent_answer": max(m["percent_answer"] for m in tg_metrics),
            "percent_abstain": max(m["percent_abstain"] for m in tg_metrics),
            "percent_conflict": max(m["percent_conflict"] for m in tg_metrics)
        }

        dashboard["results"].append({
            "pack": summary["pack_metadata"]["pack_name"],
            "version": summary["pack_metadata"]["version"],
            "metrics_summary": metrics_summary,
            "seed_count": len(seeds),
            "full_report": summary
        })
        
    out_path = "results/vor_audit_summary.json"
    os.makedirs("results", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(dashboard, f, indent=4)
        
    print(f"\nVOR AUDIT COMPLETE. Dashboard: {out_path}")
    
    # Simple console report
    print("-" * 40)
    print("CERTIFICATION SUMMARY (Worst-Case Across Seeds)")
    print("-" * 40)
    for res in dashboard["results"]:
        m = res["metrics_summary"]
        print(f"Pack: {res['pack']} (v{res['version']}, Seeds: {res['seed_count']})")
        print(f"  Hallucination (Max): {m['hallucination_rate']:.2%}")
        print(f"  Accuracy (Min):      {m['answer_accuracy']:.2%}")
        print(f"  Coverage:            ANS: {m['percent_answer']:.1f}% | ABS: {m['percent_abstain']:.1f}% | CON: {m['percent_conflict']:.1f}%")
        print("-" * 40)
    
    return dashboard
