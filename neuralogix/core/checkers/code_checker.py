"""Code checker for codec validation (stub for M5)."""
from __future__ import annotations

from typing import List

from neuralogix.core.checkers.base import CheckIssue, CheckReport, CheckStatus
from neuralogix.core.codec.base import CodeResult


class CodeChecker:
    """Checker for code validity (codec outputs).
    
    Validates codec outputs based on score and budget thresholds.
    """
    
    def __init__(self, min_score: float = 0.5, budget_checker: Optional[BudgetChecker] = None):
        """Initialize code checker.
        
        Args:
            min_score: Minimum acceptable score for OK status
            budget_checker: Optional BudgetChecker to delegate threshold checks
        """
        self.min_score = min_score
        self.budget_checker = budget_checker
    
    def check_code_result(self, code_result: CodeResult, node_type: Optional[str] = None) -> CheckReport:
        """Check a single CodeResult.
        
        Args:
            code_result: CodeResult from codec.encode()
            node_type: Optional node type for threshold selection
            
        Returns:
            CheckReport with status
        """
        issues: List[CheckIssue] = []
        
        # 1. Check score threshold
        if code_result.score < self.min_score:
            issues.append(CheckIssue(
                code="LOW_CODE_SCORE",
                message=f"CodeResult.score {code_result.score:.4f} below minimum {self.min_score}",
                status=CheckStatus.SOFT_FAIL,
                details={"score": code_result.score, "min_score": self.min_score},
            ))
            
        # 2. Delegate to BudgetChecker if available
        if self.budget_checker and "quantization_error" in code_result.metadata:
            error = code_result.metadata["quantization_error"]
            tau = self.budget_checker.thresholds.get(node_type, self.budget_checker.thresholds.get("default", 1.0))
            
            if error > 2 * tau:
                issues.append(CheckIssue(
                    code="BUDGET_EXCEEDED_HARD",
                    message=f"Quantization error {error:.4f} > 2τ ({2*tau:.4f})",
                    status=CheckStatus.HARD_FAIL,
                    details={"error": error, "tau": tau}
                ))
            elif error > tau:
                issues.append(CheckIssue(
                    code="BUDGET_EXCEEDED_SOFT",
                    message=f"Quantization error {error:.4f} > τ ({tau:.4f})",
                    status=CheckStatus.SOFT_FAIL,
                    details={"error": error, "tau": tau}
                ))
        
        # Determine overall status
        status = CheckStatus.OK
        if any(i.status == CheckStatus.HARD_FAIL for i in issues):
            status = CheckStatus.HARD_FAIL
        elif any(i.status == CheckStatus.SOFT_FAIL for i in issues):
            status = CheckStatus.SOFT_FAIL
        
        return CheckReport(
            checker="CodeChecker",
            status=status,
            issues=issues,
        )

