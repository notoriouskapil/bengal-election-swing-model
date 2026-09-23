"""Smoke test for the Streamlit app.

Importing it properly needs a Streamlit runtime, so this checks the two things
that actually break: that the file parses, and that every name it pulls out of
src/ still exists. Renaming a function in models.py and forgetting the app is
the realistic failure here.
"""

import ast
import importlib
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def test_app_parses():
    ast.parse(APP.read_text())


def test_every_name_the_app_imports_from_src_exists():
    tree = ast.parse(APP.read_text())
    checked = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src"):
            module = importlib.import_module(node.module)
            for alias in node.names:
                assert hasattr(module, alias.name), f"{node.module}.{alias.name} is gone"
                checked += 1
    assert checked > 0, "expected the app to import something from src/"
