"""Pilot A: Verifiable Codegen - Runner."""
import sys
import json
import os
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType, EdgeType
from neuralogix.core.reasoning.engine import ReasoningEngine
from neuralogix.core.reasoning.operations import OPERATION_REGISTRY
from neuralogix.core.receipts.logger import ReceiptLogger
from neuralogix.pilots.pilot_a.operations import PILOT_A_OPERATIONS

SYSTEM_TEST_CONTENT = """
from solution import solution

def test_properties():
    # 1. Base cases
    assert solution(0) == 0
    assert solution(1) == 1

    # 2. Monotonicity for n >= 1
    prev = 1
    for i in range(2, 10):
        curr = solution(i)
        assert curr >= prev
        prev = curr

    # 3. Recurrence relation check
    assert solution(10) == solution(9) + solution(8)
"""

def run_pilot():
    print("🚀 Starting Pilot A: Verifiable Codegen (Real-World Mode)")

    # 1. Register Operations
    print("📋 Registering Pilot Operations...")
    for op in PILOT_A_OPERATIONS:
        OPERATION_REGISTRY.register(op)
        print(f"   - Registered {op.name}")

    # 2. Initialize Engine
    receipt_file = "pilot_a_receipts.jsonl"
    if os.path.exists(receipt_file):
        os.remove(receipt_file)
    logger = ReceiptLogger(receipt_file)

    engine = ReasoningEngine(logger=logger, checkers_enabled=True)
    graph = TypedGraph()

    # 3. Define Task (Spec)
    print("\n📝 Defining Task: Fibonacci Function")
    spec_id = "spec_fib"
    graph.add_node(
        spec_id,
        NodeType.SPEC,
        value={"text": "Write a python function to calculate the nth fibonacci number."}
    )

    # 4. Execute Workflow
    print("\n⚙️  Running Reasoning Chain...")

    # Step 1: Generate Code
    print("   [1/4] Generating Code...")
    res_code = engine.step(graph, "generate_code", {"spec": spec_id})
    if res_code["status"].value != "OK":
        print(f"❌ Failed to generate code: {res_code['message']}")
        return False
    code_id = res_code["outputs"]["code"]

    # Step 2: Inject System Test (Hidden Property Check)
    print("   [2/4] Injecting System Test (Anti-Tautology Check)...")
    system_test_id = "test_system_prop_01"
    graph.add_node(
        system_test_id,
        NodeType.TEST,
        value={
            "content": SYSTEM_TEST_CONTENT,
            "framework": "pytest",
            "origin": "system"  # Critical: This satisfies AntiTautologyChecker
        }
    )
    graph.add_edge(EdgeType.VERIFIES, system_test_id, code_id)

    # Step 3: Execute System Test
    print("   [3/4] Executing System Test...")
    res_exec_sys = engine.step(graph, "execute_test", {"code": code_id, "test": system_test_id})
    if res_exec_sys["status"].value != "OK":
        print(f"❌ Failed to execute system test: {res_exec_sys['message']}")
        return False

    # Step 4: Generate Proposer Test
    print("   [4/4] Generating Proposer Test...")
    res_test = engine.step(graph, "generate_test", {"spec": spec_id, "code": code_id})
    if res_test["status"].value != "OK":
        # This checks the Tautology rule implicitly:
        # If we hadn't run the system test first, and the proposer test passed,
        # the Checker would still only see proposer tests if we didn't have the system one.
        # But wait - checkers run AFTER the step.
        # So when we run execute_test for the PROPOSER test, the checker runs.
        # At that point, we must have a PASSING system test result in the graph.
        print(f"❌ Failed to generate proposer test: {res_test['message']}")
        return False
    test_id = res_test["outputs"]["test"]

    # Step 5: Execute Proposer Test
    print("   [5/5] Executing Proposer Test...")
    res_exec = engine.step(graph, "execute_test", {"code": code_id, "test": test_id})

    # If AntiTautologyChecker is working, this step will FAIL (HARD_FAIL)
    # IF we hadn't already executed the system test successfully.
    # Since we did, it should PASS.

    if res_exec["status"].value != "OK":
        print(f"❌ Failed to execute proposer test (or Tautology Check failed): {res_exec['message']}")
        if "TAUTOLOGY_DETECTED" in str(res_exec["receipt"].checker_reports):
            print("   -> 🛑 Anti-Tautology Rule Violated! (No system test proof found)")
        return False

    exec_result_id = res_exec["outputs"]["result"]
    exec_node = graph.nodes[exec_result_id]
    exec_status = exec_node.value["status"]

    print(f"\n📊 Execution Status: {exec_status}")
    if exec_status == "PASS":
        print("✅ SUCCESS: Code verified by test.")
    else:
        print("❌ FAILURE: Test failed.")
        print("Stdout:", exec_node.value["stdout"])
        print("Stderr:", exec_node.value["stderr"])

    # 5. Dump Receipts
    print("\n📜 Receipts (Audit Trail):")
    receipts = logger.read_all()
    for i, r in enumerate(receipts):
        print(f"   {i+1}. {r.op_name} -> {r.status} (Hash: {r.graph_hash_after[:8]})")

    # Save receipts to file for inspection
    with open("pilot_a_receipts.json", "w") as f:
        json.dump([r.to_dict() for r in receipts], f, indent=2)

    return exec_status == "PASS"

if __name__ == "__main__":
    success = run_pilot()
    sys.exit(0 if success else 1)
