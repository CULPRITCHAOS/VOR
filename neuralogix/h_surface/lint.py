"""NeuraLogix-H DSL Linter."""
import re
from typing import List, Dict, Any

class HLinter:
    """Linter for NeuraLogix-H DSL strings."""

    def lint(self, text: str) -> List[Dict[str, Any]]:
        """Run lint checks on DSL text.
        
        Returns:
            List of issue dicts: {"line": int, "type": str, "message": str}
        """
        issues = []
        lines = text.strip().split("\n")
        defined_nodes = set()
        
        # Pass 1: Collect definitions
        for i, line in enumerate(lines):
            line_num = i + 1
            node_match = re.match(r"^let\s+(\w+)", line.strip())
            if node_match:
                defined_nodes.add(node_match.group(1))
                
        # Pass 2: Check references
        for i, line in enumerate(lines):
            line_num = i + 1
            content = line.strip()
            if not content or content.startswith("#") or content.startswith("let"):
                continue
            
            # Check edge format: src type target
            edge_match = re.match(r"^(\w+)\s+([\w_]+)\s+(\w+)", content)
            if edge_match:
                src, _, target = edge_match.groups()
                if src not in defined_nodes:
                    issues.append({
                        "line": line_num,
                        "type": "ERROR",
                        "message": f"Reference to undefined node: '{src}'"
                    })
                if target not in defined_nodes:
                    issues.append({
                        "line": line_num,
                        "type": "ERROR",
                        "message": f"Reference to undefined node: '{target}'"
                    })
            elif "=" in content and "(" in content:
                # Assignment op: res = op(a, b)
                op_match = re.match(r"^(\w+)\s*=\s*(\w+)\(([^)]+)\)$", content)
                if op_match:
                    res, _, args_str = op_match.groups()
                    defined_nodes.add(res) # Define for future lines
                    args = [a.strip() for a in args_str.split(",")]
                    for arg in args:
                        if arg not in defined_nodes:
                            issues.append({
                                "line": line_num,
                                "type": "ERROR",
                                "message": f"Reference to undefined node in op: '{arg}'"
                            })
            else:
                issues.append({
                    "line": line_num,
                    "type": "WARNING",
                    "message": f"Line does not match recognized DSL patterns"
                })
                
        return issues
