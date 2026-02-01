import pytest
from neuralogix.core.audit.outcome_verifier import OutcomeVerifier

def test_verifier_accepts_valid():
    """Verify standard support for a deterministic move."""
    allowed_fn = lambda s, a: { (s[0]+a[0], s[1]+a[1]) }
    
    # (0,0) + (1,0) -> (1,0)
    assert OutcomeVerifier.verify_support((0,0), (1,0), (1,0), allowed_fn) is True

def test_verifier_accepts_stochastic_variation():
    """Verify support for a slip in a stochastic world."""
    def slip_allowed(s, a):
        # MOVE(1,0) can result in (1,0), (0,0), or (0,1)
        return { (1,0), (0,0), (0,1) }
        
    # SLIP to (0,1) is valid in this model
    assert OutcomeVerifier.verify_support((0,0), (1,0), (0,1), slip_allowed) is True

def test_verifier_rejects_impossible_outcome():
    """Adversarial: Engine must reject a state not in the allowed set."""
    def slip_allowed(s, a):
        return { (1,0), (0,0) } # Only SUCCESS or STALL
        
    # (0,0) + MOVE(1,0) -> (9,9) (Teleportation/Lying Observation)
    with pytest.raises(ValueError, match="Unsupported outcome"):
        OutcomeVerifier.verify_support((0,0), (1,0), (9,9), slip_allowed)

def test_tool_contract_verification():
    """Test Pilot H style pre/post condition gating."""
    pre = lambda x: isinstance(x, str) and len(x) > 0
    post = lambda inp, out: out == len(inp)
    
    # Valid execution
    assert OutcomeVerifier.verify_tool_contract("hello", "LenTool", 5, pre, post) is True
    
    # Invalid Pre
    with pytest.raises(ValueError, match="rejected inputs"):
        OutcomeVerifier.verify_tool_contract(123, "LenTool", 5, pre, post)
        
    # Invalid Post
    with pytest.raises(ValueError, match="produced invalid output"):
        OutcomeVerifier.verify_tool_contract("hello", "LenTool", 99, pre, post)

def test_verifier_strict_gate_regression():
    """Ensure the OutcomeVerifier does not have 'slack' (exact membership required)."""
    # Define a world with narrow support
    def narrow_support(s, a):
        return { (1, 0) }
        
    # Valid
    assert OutcomeVerifier.verify_support((0,0), "MOVE", (1,0), narrow_support) is True
    
    # 0.0001 difference should still fail
    with pytest.raises(ValueError):
        OutcomeVerifier.verify_support((0,0), "MOVE", (1.0001, 0), narrow_support)
        
    # Empty support should fail everything
    with pytest.raises(ValueError):
        OutcomeVerifier.verify_support((0,0), "MOVE", (1,0), lambda s, a: set())
