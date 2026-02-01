from typing import Any, Optional, Dict, NamedTuple

class Artifact(NamedTuple):
    id: str
    content: str

class DataNode(NamedTuple):
    raw: Artifact
    parsed_val: int

class ToolRegistry:
    """
    Mock tools for Pilot H that simulate observations.
    """
    @staticmethod
    def retriever(query: str) -> Optional[Artifact]:
        # Pre: len(query) > 0
        if not query: return None
        if query == "FAIL": return None
        return Artifact(id="art_001", content="Value is 42")

    @staticmethod
    def parser(artifact: Artifact) -> Optional[DataNode]:
        # Pre: artifact is not None
        if not artifact: return None
        try:
            val = int(artifact.content.split()[-1])
            return DataNode(raw=artifact, parsed_val=val)
        except:
            return None

    @staticmethod
    def tester(node: DataNode, threshold: int = 40) -> bool:
        # Pre: node is DataNode
        if not node: return False
        return node.parsed_val > threshold

class ToolContract:
    """
    Defines the verification logic for the tools.
    """
    @staticmethod
    def get_pre(tool_name: str):
        if tool_name == "retriever":
            return lambda q: isinstance(q, str) and len(q) > 0
        if tool_name == "parser":
            return lambda a: isinstance(a, Artifact)
        if tool_name == "tester":
            return lambda n: isinstance(n, DataNode)
        return lambda _: False

    @staticmethod
    def get_post(tool_name: str):
        if tool_name == "retriever":
            return lambda q, res: res is None or isinstance(res, Artifact)
        if tool_name == "parser":
            return lambda q, res: res is None or isinstance(res, DataNode)
        if tool_name == "tester":
            return lambda q, res: isinstance(res, bool)
        return lambda q, res: False
