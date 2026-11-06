"""Test helpers: import the project's main.py module as `gbmain`.

pytest runs may share sys.modules with other skills, so the module is
loaded under a project-qualified name instead of the generic `main`.
"""
import importlib.util
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_DIR.parent.parent

MODULE_NAME = "giant_beads_main"


def load_main():
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(
        MODULE_NAME, PROJECT_DIR / "main.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = mod
    spec.loader.exec_module(mod)
    return mod
