#!/usr/bin/env python3
"""Check for blocking I/O in async functions."""

import ast
import sys
from pathlib import Path


BLOCKING_CALLS = {
    "open",  # Use aiofiles.open
    "read",  # Use await f.read()
    "write",  # Use await f.write()
    "sleep",  # Use asyncio.sleep
}


class AsyncBlockingChecker(ast.NodeVisitor):
    """Check for blocking calls in async functions."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.in_async = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self.in_async = True
        self.generic_visit(node)
        self.in_async = False

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        if self.in_async and isinstance(node.func, ast.Name):
            if node.func.id in BLOCKING_CALLS:
                self.errors.append(
                    f"Line {node.lineno}: Blocking call '{node.func.id}' in async function"
                )
        self.generic_visit(node)


def check_file(path: Path) -> list[str]:
    """Check a single file for async violations."""
    try:
        content = path.read_text()
        tree = ast.parse(content, filename=str(path))
        checker = AsyncBlockingChecker()
        checker.visit(tree)
        return [f"{path}:{error}" for error in checker.errors]
    except SyntaxError:
        return []


def main() -> int:
    """Check all Python files in src/."""
    src_dir = Path("src")
    if not src_dir.exists():
        return 0

    all_errors = []
    for py_file in src_dir.rglob("*.py"):
        errors = check_file(py_file)
        all_errors.extend(errors)

    if all_errors:
        print("❌ Blocking I/O detected in async functions:")
        for error in all_errors:
            print(f"  {error}")
        return 1

    print("✅ No blocking I/O in async functions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
