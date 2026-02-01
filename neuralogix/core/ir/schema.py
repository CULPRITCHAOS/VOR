"""Typed Graph IR schema definitions (M0 stubs)."""
from __future__ import annotations

from enum import Enum

SCHEMA_VERSION = "0.0.0"


class NodeType(str, Enum):
    NUMBER = "Number"
    PERSON = "Person"
    RELATION = "Relation"
    OPERATION = "Operation"
    BOOLEAN = "Boolean"
    # Pilot A types
    SPEC = "Spec"
    CODE = "Code"
    TEST = "Test"
    EXECUTION_RESULT = "ExecutionResult"
    # Pilot B types
    ENTITY = "Entity"
    VALUE = "Value"
    VALUE_SET = "ValueSet"


class EdgeType(str, Enum):
    PARENT_OF = "parent_of"
    SPOUSE_OF = "spouse_of"
    ADD = "add"
    GREATER_THAN = "greater_than"
    # Pilot A types
    IMPLEMENTS = "implements"
    VERIFIES = "verifies"
    RESULTS_FROM = "results_from"
    # Pilot B types
    HAS_ATTRIBUTE = "has_attribute"
    CONTAINS = "contains"
