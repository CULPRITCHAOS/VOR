"""Pilot D: Runner."""
import sys
import os
import json
from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import NodeType, EdgeType
from neuralogix.core.reasoning.engine import ReasoningEngine
from neuralogix.core.reasoning.operations import OPERATION_REGISTRY
from neuralogix.core.receipts.logger import ReceiptLogger

from neuralogix.pilots.pilot_d.mock_world_model import MockWorldModel, TRANSITIONS
from neuralogix.pilots.pilot_d.operations_predict import OP_PREDICT_NEXT, set_world_model

# Invariant Knowledge (The "Laws of Physics" for this world)
# In a real system, this is the Knowledge Graph schema constraints
VALID_TRANSITIONS = set(TRANSITIONS.items())

def check_invariant(current_state: str, proposed_state: str) -> bool:
    """The Proof Gate: Checks if transition is physically valid."""
    return (current_state, proposed_state) in VALID_TRANSITIONS

def run_pilot():
    print("🚀 Starting Pilot D: World Modeling")

    # 1. Setup
    OPERATION_REGISTRY.register(OP_PREDICT_NEXT)

    receipt_file = "pilot_d_receipts.jsonl"
    if os.path.exists(receipt_file):
        os.remove(receipt_file)
    logger = ReceiptLogger(receipt_file)

    engine = ReasoningEngine(logger=logger, checkers_enabled=True)

    # 2. Scenarios
    scenarios = [
        ("Good Model", 0.0),    # 0% error rate
        ("Bad Model", 1.0)      # 100% error rate (always predicts wrong)
    ]

    overall_success = True

    for model_name, error_rate in scenarios:
        print(f"\n🧪 Scenario: {model_name} (Error Rate: {error_rate})")

        # Init Model
        model = MockWorldModel(error_rate=error_rate)
        set_world_model(model)

        # Init Graph State (Traffic Light is Green)
        graph = TypedGraph()
        entity_id = "traffic_light_1"
        val_id = "val_green"
        graph.add_node(entity_id, NodeType.ENTITY, value={"name": "Traffic Light"})
        graph.add_node(val_id, NodeType.VALUE, value={"value": "Green", "type": "string"})
        graph.add_edge(EdgeType.HAS_ATTRIBUTE, entity_id, val_id, metadata={"attribute": "state"})

        print("   Current State: Green")

        # Step 1: Predict (Propose)
        res = engine.step(graph, "predict_next", {"entity": entity_id, "current_value": val_id})

        if res["status"].value != "OK":
            print("   ❌ Prediction failed at generation step")
            overall_success = False
            continue

        proposed_id = res["outputs"]["prediction"]
        proposed_state = res["outputs"]["state"]
        print(f"   Model Proposes: {proposed_state}")

        # Step 2: Proof Gate (Validate Proposal)
        # In a real system, this might be an operation like `verify_transition`
        # Here we simulate the Gate logic explicitly.

        current_state = "Green"
        is_valid = check_invariant(current_state, proposed_state)

        if is_valid:
            print("   ✅ Gate: ACCEPTED (Invariant Verified)")
            # Commit to graph (Simulated)
            # In Pilot D, this means we would add a 'NEXT_STATE' edge
            if error_rate > 0:
                print("   ❌ ERROR: Bad model should have been rejected!")
                overall_success = False
        else:
            print("   🛡️  Gate: REJECTED (Invariant Violation)")
            # In Pilot D, this means ABSTAIN / Do not update state
            if error_rate == 0:
                 print("   ❌ ERROR: Good model should have been accepted!")
                 overall_success = False
            else:
                 print("   ✅ Safety System Worked.")

    return overall_success

if __name__ == "__main__":
    success = run_pilot()
    sys.exit(0 if success else 1)
