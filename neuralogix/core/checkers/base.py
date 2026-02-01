"""Checker framework base classes and utilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class CheckStatus(str, Enum):
    """Status outcome for a checker."""
    OK = "OK"
    SOFT_FAIL = "SOFT_FAIL"
    HARD_FAIL = "HARD_FAIL"
    ABSTAIN = "ABSTAIN"


class Checker:
    """Base class for graph checkers."""
    def check(self, graph: Any) -> CheckReport:
        raise NotImplementedError("Checker.check not implemented")


@dataclass(frozen=True)
class CheckIssue:
    """Individual issue found by a checker."""
    code: str
    message: str
    status: CheckStatus
    node_ids: List[str] = field(default_factory=list)
    edge_ids: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "code": self.code,
            "message": self.message,
            "status": self.status.value,
            "node_ids": self.node_ids,
            "edge_ids": self.edge_ids,
            "details": self.details,
        }


@dataclass(frozen=True)
class CheckReport:
    """Report from a single checker."""
    checker: str
    status: CheckStatus
    issues: List[CheckIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "checker": self.checker,
            "status": self.status.value,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def combine_reports(reports: List[CheckReport]) -> CheckStatus:
    """Combine multiple check reports into overall status.
    
    Rules:
    - If any HARD_FAIL => HARD_FAIL
    - Else if any ABSTAIN => ABSTAIN
    - Else if any SOFT_FAIL => SOFT_FAIL
    - Else OK
    
    Args:
        reports: List of check reports from different checkers
        
    Returns:
        Overall status
    """
    if not reports:
        return CheckStatus.OK
    
    statuses = [report.status for report in reports]
    
    if CheckStatus.HARD_FAIL in statuses:
        return CheckStatus.HARD_FAIL
    if CheckStatus.ABSTAIN in statuses:
        return CheckStatus.ABSTAIN
    if CheckStatus.SOFT_FAIL in statuses:
        return CheckStatus.SOFT_FAIL
    return CheckStatus.OK
