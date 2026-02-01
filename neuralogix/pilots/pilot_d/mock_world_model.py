"""Mock World Model for Pilot D."""
import random
from typing import List, Tuple, Dict

# Simple Traffic Light Transition Matrix
# Green -> Yellow -> Red -> Green
TRANSITIONS = {
    "Green": "Yellow",
    "Yellow": "Red",
    "Red": "Green"
}

class MockWorldModel:
    """Simulates a learned world model."""

    def __init__(self, error_rate: float = 0.0):
        self.error_rate = error_rate

    def predict_next(self, current_state: str) -> str:
        """Predict next state given current state."""
        true_next = TRANSITIONS.get(current_state)

        if not true_next:
            return "Unknown"

        # Simulate model error/hallucination
        if random.random() < self.error_rate:
            # Pick a wrong state
            options = [s for s in TRANSITIONS.keys() if s != true_next]
            return random.choice(options)

        return true_next
