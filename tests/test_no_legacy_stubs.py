"""Guardrail tests to prevent legacy stubs or banned patterns from regressing."""
import os
import pytest

BANNED_TERMS = [
    "CheckerOutcome",
    "checkersbase",
    "TODO: remove stub",
    "test_combined.py",
]

BANNED_FILES = [
    "ops_arith.py",
    "ops_family.py",
    "op_checker.py",
]

def test_no_banned_terms_in_repo():
    """Fail if any banned terms are found in the source or tests."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    for root, dirs, files in os.walk(root_dir):
        # Skip pycache and git
        if ".git" in root or "__pycache__" in root or ".pytest_cache" in root:
            continue
            
        for file in files:
            if not file.endswith((".py", ".md", ".txt")):
                continue
                
            file_path = os.path.join(root, file)
            
            # Skip this file itself
            if file == "test_no_legacy_stubs.py" or file == "hygiene_scan.py":
                continue
                
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                for term in BANNED_TERMS:
                    assert term not in content, f"Banned term '{term}' found in {file_path}"

def test_no_banned_files_exist():
    """Fail if any known stale files still exist."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            for banned in BANNED_FILES:
                assert file != banned, f"Banned stale file '{banned}' still exists at {root}"
