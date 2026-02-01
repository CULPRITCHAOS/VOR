"""Operations for Pilot A: Verifiable Codegen."""
from __future__ import annotations

import os
import sys
import subprocess
import tempfile
from typing import Any, Dict

from neuralogix.core.ir.graph import TypedGraph
from neuralogix.core.ir.schema import EdgeType, NodeType
from neuralogix.core.reasoning.operations import OperationSignature


def _apply_generate_code(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code from spec (Mocked for Pilot).

    Args:
        inputs: {"spec": spec_node_id}
    """
    spec_id = inputs["spec"]
    result_id = inputs.get("result_id", f"code_for_{spec_id}")

    spec_node = graph.nodes[spec_id]
    if spec_node.node_type != NodeType.SPEC:
        raise ValueError(f"generate_code requires SPEC input, got {spec_node.node_type}")

    # Mock generation logic based on spec content
    spec_text = spec_node.value.get("text", "").lower()

    if "fibonacci" in spec_text:
        code_content = (
            "def solution(n):\n"
            "    if n <= 1: return n\n"
            "    return solution(n-1) + solution(n-2)\n"
        )
    else:
        # Default mock
        code_content = "def solution(x): return x"

    if result_id not in graph.nodes:
        graph.add_node(result_id, NodeType.CODE, value={"content": code_content, "language": "python"})

    graph.add_edge(EdgeType.IMPLEMENTS, result_id, spec_id)

    return {"code": result_id}


def _apply_generate_test(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate test from spec and code (Mocked for Pilot).

    Args:
        inputs: {"spec": spec_node_id, "code": code_node_id}
    """
    spec_id = inputs["spec"]
    code_id = inputs["code"]
    result_id = inputs.get("result_id", f"test_for_{code_id}")

    spec_node = graph.nodes[spec_id]
    code_node = graph.nodes[code_id]

    if spec_node.node_type != NodeType.SPEC:
        raise ValueError("generate_test requires SPEC input")
    if code_node.node_type != NodeType.CODE:
        raise ValueError("generate_test requires CODE input")

    # Mock generation logic
    spec_text = spec_node.value.get("text", "").lower()

    if "fibonacci" in spec_text:
        test_content = (
            "from solution import solution\n"
            "def test_solution():\n"
            "    assert solution(0) == 0\n"
            "    assert solution(1) == 1\n"
            "    assert solution(5) == 5\n"  # 0,1,1,2,3,5
        )
    else:
        test_content = (
            "from solution import solution\n"
            "def test_solution():\n"
            "    assert solution(1) == 1\n"
        )

    if result_id not in graph.nodes:
        graph.add_node(
            result_id,
            NodeType.TEST,
            value={
                "content": test_content,
                "framework": "pytest",
                "origin": "proposer"  # Explicitly mark as proposer-generated
            }
        )

    graph.add_edge(EdgeType.VERIFIES, result_id, code_id)

    return {"test": result_id}


def _apply_execute_test(graph: TypedGraph, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Execute test against code.

    Args:
        inputs: {"code": code_node_id, "test": test_node_id}
    """
    code_id = inputs["code"]
    test_id = inputs["test"]
    result_id = inputs.get("result_id", f"exec_{test_id}_{code_id}")

    code_node = graph.nodes[code_id]
    test_node = graph.nodes[test_id]

    if code_node.node_type != NodeType.CODE or test_node.node_type != NodeType.TEST:
        raise ValueError("execute_test requires CODE and TEST inputs")

    code_content = code_node.value["content"]
    test_content = test_node.value["content"]

    # Execution Sandbox
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write files
        with open(os.path.join(tmpdir, "solution.py"), "w") as f:
            f.write(code_content)
        with open(os.path.join(tmpdir, "test_solution.py"), "w") as f:
            f.write(test_content)

        # Run pytest
        # We run it as a subprocess to capture output and exit code
        cmd = [sys.executable, "-m", "pytest", "test_solution.py"]

        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=10 # Security timeout
            )
            stdout = proc.stdout
            stderr = proc.stderr
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            stdout = ""
            stderr = "Timeout expired"
            returncode = -1

    status = "PASS" if returncode == 0 else "FAIL"

    if result_id not in graph.nodes:
        graph.add_node(
            result_id,
            NodeType.EXECUTION_RESULT,
            value={
                "status": status,
                "exit_code": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "env": {
                    "python": sys.version,
                    "platform": sys.platform
                }
            }
        )

    graph.add_edge(EdgeType.RESULTS_FROM, result_id, test_id)

    return {"result": result_id, "status": status}


# Operation Signatures
OP_GENERATE_CODE = OperationSignature(
    name="generate_code",
    input_types=[NodeType.SPEC],
    output_type=NodeType.CODE,
    apply=_apply_generate_code,
    description="Generate code from spec"
)

OP_GENERATE_TEST = OperationSignature(
    name="generate_test",
    input_types=[NodeType.SPEC, NodeType.CODE],
    output_type=NodeType.TEST,
    apply=_apply_generate_test,
    description="Generate test from spec and code"
)

OP_EXECUTE_TEST = OperationSignature(
    name="execute_test",
    input_types=[NodeType.CODE, NodeType.TEST],
    output_type=NodeType.EXECUTION_RESULT,
    apply=_apply_execute_test,
    description="Execute test against code in sandbox"
)

PILOT_A_OPERATIONS = [
    OP_GENERATE_CODE,
    OP_GENERATE_TEST,
    OP_EXECUTE_TEST
]
