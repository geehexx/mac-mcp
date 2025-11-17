#!/usr/bin/env python3
"""Check that all event models are immutable (frozen=True)."""

import ast
import sys
from pathlib import Path


class EventImmutabilityChecker(ast.NodeVisitor):
    """Check that event classes have frozen=True."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        # Check if class name ends with "Event"
        if node.name.endswith("Event"):
            has_frozen = False

            # Check for model_config with frozen=True
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "model_config":
                            # Check if frozen=True in dict
                            if isinstance(item.value, ast.Dict):
                                for key, value in zip(item.value.keys, item.value.values, strict=False):
                                    if (
                                        isinstance(key, ast.Constant)
                                        and key.value == "frozen"
                                        and isinstance(value, ast.Constant)
                                        and value.value is True
                                    ):
                                        has_frozen = True

            if not has_frozen:
                self.errors.append(
                    f"Line {node.lineno}: Event class '{node.name}' missing frozen=True"
                )

        self.generic_visit(node)


def check_file(path: Path) -> list[str]:
    """Check a single file for event immutability."""
    try:
        content = path.read_text()
        tree = ast.parse(content, filename=str(path))
        checker = EventImmutabilityChecker()
        checker.visit(tree)
        return [f"{path}:{error}" for error in checker.errors]
    except SyntaxError:
        return []


def main() -> int:
    """Check all Python files in src/mac_mcp/domain/."""
    domain_dir = Path("src/mac_mcp/domain")
    if not domain_dir.exists():
        return 0

    all_errors = []
    for py_file in domain_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        errors = check_file(py_file)
        all_errors.extend(errors)

    if all_errors:
        print("❌ Mutable event classes detected:")
        for error in all_errors:
            print(f"  {error}")
        print("\nAdd model_config = {'frozen': True} to event classes")
        return 1

    print("✅ All event classes are immutable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
