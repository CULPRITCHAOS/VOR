"""Integrity checkers for verifying reasoning validity (Pilot A.3)."""
from __future__ import annotations

from typing import List

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.checkers.base import CheckIssue, CheckReport, CheckStatus, Checker


class AntiTautologyChecker(Checker):
    """Enforce the Anti-Tautology Rule.

    Rule: "Tests authored by the proposer cannot be the only verifier."

    Implementation:
    For every CODE node that has passing execution results:
    - It must have at least one passing result from a TEST with origin="system".
    - If it only has passing results from origin="proposer" (or unspecified), HARD_FAIL.
    """

    def check(self, graph: TypedGraph) -> CheckReport:
        issues: List[CheckIssue] = []

        # 1. Find all CODE nodes
        code_nodes = {nid: n for nid, n in graph.nodes.items() if n.node_type == NodeType.CODE}

        for code_id, code_node in code_nodes.items():
            # Find all TESTs verifying this CODE
            # Pattern: TEST --verifies--> CODE
            verifying_tests = []
            for edge in graph.edges:
                if edge.edge_type == EdgeType.VERIFIES and edge.target == code_id:
                    verifying_tests.append(edge.source)

            if not verifying_tests:
                continue

            # Find all Passing Execution Results for these tests
            # Pattern: EXECUTION_RESULT --results_from--> TEST
            passing_results = []
            for test_id in verifying_tests:
                for edge in graph.edges:
                    if (edge.edge_type == EdgeType.RESULTS_FROM and
                        edge.target == test_id):

                        res_node = graph.nodes.get(edge.source)
                        if res_node and res_node.value.get("status") == "PASS":
                            passing_results.append({
                                "result_id": edge.source,
                                "test_id": test_id,
                                "origin": graph.nodes[test_id].value.get("origin", "unknown")
                            })

            # If no passing results, we don't care (the code isn't "proven" yet)
            if not passing_results:
                continue

            # Check for Independent Signal
            has_system_proof = any(r["origin"] == "system" for r in passing_results)

            if not has_system_proof:
                issues.append(CheckIssue(
                    code="TAUTOLOGY_DETECTED",
                    message=(
                        f"Code '{code_id}' verified ONLY by proposer-authored tests. "
                        "Must include at least one independent verifier signal (origin='system')."
                    ),
                    status=CheckStatus.HARD_FAIL,
                    node_ids=[code_id] + [r["test_id"] for r in passing_results],
                    details={
                        "code_id": code_id,
                        "passing_tests": [r["test_id"] for r in passing_results],
                        "origins": [r["origin"] for r in passing_results]
                    }
                ))

        status = CheckStatus.HARD_FAIL if issues else CheckStatus.OK

        return CheckReport(
            checker="AntiTautologyChecker",
            status=status,
            issues=issues,
        )
