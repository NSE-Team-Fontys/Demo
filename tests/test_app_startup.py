from __future__ import annotations

import ast
from pathlib import Path
import unittest


class AppStartupTests(unittest.TestCase):
    def test_app_startup_has_no_eager_llm_activation(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        tree = ast.parse(app_path.read_text(encoding="utf-8"))

        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }

        self.assertNotIn("threading", imported_modules)
        self.assertNotIn("ensure_model_available", called_attributes)


if __name__ == "__main__":
    unittest.main()
