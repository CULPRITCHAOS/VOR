from typing import Any, Set, Tuple, List, Callable
import logging

class OutcomeVerifier:
    """
    Shared utility for v0.4 'Stochastic Outcomes, Verified Support' contract.
    Ensures that an observed outcome is within the allowed set for a given (state, action).
    """
    
    @staticmethod
    def verify_support(
        state_before: Any,
        action: Any,
        state_after: Any,
        allowed_outcomes_fn: Callable[[Any, Any], Set[Any]],
        context: str = "World Model"
    ) -> bool:
        """
        Returns True if state_after is in the set of allowed outcomes for action applied to state_before.
        Raises ValueError if support is not found.
        """
        allowed = allowed_outcomes_fn(state_before, action)
        
        if state_after in allowed:
            return True
            
        error_msg = (
            f"❌ [INTEGRITY_VIOLATION] Unsupported outcome in {context}.\n"
            f"   State Before: {state_before}\n"
            f"   Action: {action}\n"
            f"   State After (Observed): {state_after}\n"
            f"   Allowed Outcomes: {allowed}"
        )
        logging.error(error_msg)
        raise ValueError(error_msg)

    @staticmethod
    def verify_tool_contract(
        inputs: Any,
        tool_name: str,
        output: Any,
        pre_condition_fn: Callable[[Any], bool],
        post_condition_fn: Callable[[Any, Any], bool]
    ) -> bool:
        """
        Verifies a tool execution sequence for Pilot H.
        """
        if not pre_condition_fn(inputs):
            raise ValueError(f"❌ [PRECONDITION_FAILED] Tool {tool_name} rejected inputs: {inputs}")
            
        if not post_condition_fn(inputs, output):
            raise ValueError(f"❌ [POSTCONDITION_FAILED] Tool {tool_name} produced invalid output: {output}")
            
        return True
