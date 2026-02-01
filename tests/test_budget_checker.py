"""Unit tests for BudgetChecker."""
import pytest
from neuralogix.core.ir.graph import Node, TypedGraph
from neuralogix.core.ir.schema import NodeType
from neuralogix.core.checkers.budget_checker import BudgetChecker
from neuralogix.core.checkers.base import CheckStatus
from neuralogix.core.codec.base import CodeResult

def test_budget_checker_ok():
    """Verify OK status when error is below τ."""
    checker = BudgetChecker(thresholds={"Number": 1.0})
    g = TypedGraph()
    # Correct error: 0.5 < 1.0 (τ)
    cr = CodeResult(code=0, score=0.66, valid_hint=True, metadata={"quantization_error": 0.5})
    g.add_node("n1", NodeType.NUMBER, value=cr)
    
    report = checker.check(g)
    assert report.status == CheckStatus.OK
    assert len(report.issues) == 0

def test_budget_checker_soft_fail():
    """Verify SOFT_FAIL status when error is between τ and 2τ."""
    checker = BudgetChecker(thresholds={"Number": 1.0})
    g = TypedGraph()
    # Soft fail: 1.5 is between 1.0 and 2.0
    cr = CodeResult(code=0, score=0.4, valid_hint=True, metadata={"quantization_error": 1.5})
    g.add_node("n1", NodeType.NUMBER, value=cr)
    
    report = checker.check(g)
    assert report.status == CheckStatus.SOFT_FAIL
    assert len(report.issues) == 1
    assert report.issues[0].code == "BUDGET_EXCEEDED_SOFT"

def test_budget_checker_hard_fail():
    """Verify HARD_FAIL status when error exceeds 2τ."""
    checker = BudgetChecker(thresholds={"Number": 1.0})
    g = TypedGraph()
    # Hard fail: 2.5 > 2.0
    cr = CodeResult(code=0, score=0.2, valid_hint=False, metadata={"quantization_error": 2.5})
    g.add_node("n1", NodeType.NUMBER, value=cr)
    
    report = checker.check(g)
    assert report.status == CheckStatus.HARD_FAIL
    assert len(report.issues) == 1
    assert report.issues[0].code == "BUDGET_EXCEEDED_HARD"

def test_budget_checker_per_type_thresholds():
    """Verify that different types use their respective thresholds."""
    checker = BudgetChecker(thresholds={"Number": 1.0, "Person": 0.1})
    g = TypedGraph()
    
    # n1: Number error 0.5 < tau 1.0 (OK)
    cr1 = CodeResult(code=0, score=0.6, valid_hint=True, metadata={"quantization_error": 0.5})
    g.add_node("n1", NodeType.NUMBER, value=cr1)
    
    # n2: Person error 0.5 > tau 0.1 (SOFT/HARD fail)
    # 0.5 > 2*0.1=0.2 => HARD_FAIL
    cr2 = CodeResult(code=0, score=0.6, valid_hint=True, metadata={"quantization_error": 0.5})
    g.add_node("n2", NodeType.PERSON, value=cr2)
    
    report = checker.check(g)
    assert report.status == CheckStatus.HARD_FAIL
    # Should only have issue for n2
    assert len(report.issues) == 1
    assert report.issues[0].node_ids == ["n2"]

def test_budget_checker_from_dict():
    """Verify it works with serialized dicts too."""
    checker = BudgetChecker(thresholds={"Number": 1.0})
    g = TypedGraph()
    val = {
        "code": 0,
        "score": 0.2,
        "valid_hint": False,
        "metadata": {"quantization_error": 2.5}
    }
    g.add_node("n1", NodeType.NUMBER, value=val)
    
    report = checker.check(g)
    assert report.status == CheckStatus.HARD_FAIL
