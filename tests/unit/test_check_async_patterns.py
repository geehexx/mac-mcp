"""Tests for check_async_patterns.py validation script."""

import ast
from pathlib import Path

import pytest

from scripts.hooks.check_async_patterns import AsyncBlockingChecker, check_file


def test_async_with_await_passes():
    """Test that async function with await passes validation."""
    code = """
import asyncio

async def load_data():
    await asyncio.sleep(1)
    return "data"
"""
    tree = ast.parse(code)
    checker = AsyncBlockingChecker()
    checker.visit(tree)
    assert len(checker.errors) == 0


def test_async_with_blocking_sleep_fails():
    """Test that async function with blocking sleep fails."""
    code = """
import time

async def load_data():
    sleep(1)  # Blocking call
    return "data"
"""
    tree = ast.parse(code)
    checker = AsyncBlockingChecker()
    checker.visit(tree)
    assert len(checker.errors) == 1
    assert "sleep" in checker.errors[0]


def test_async_with_blocking_open_fails():
    """Test that async function with blocking open fails."""
    code = """
async def load_file():
    with open("file.txt") as f:  # Blocking call
        return f.read()
"""
    tree = ast.parse(code)
    checker = AsyncBlockingChecker()
    checker.visit(tree)
    assert len(checker.errors) == 1
    assert "open" in checker.errors[0]


def test_sync_function_with_blocking_allowed():
    """Test that sync function with blocking calls is allowed."""
    code = """
def load_file():
    with open("file.txt") as f:
        return f.read()
"""
    tree = ast.parse(code)
    checker = AsyncBlockingChecker()
    checker.visit(tree)
    assert len(checker.errors) == 0


def test_check_file_with_valid_async(tmp_path: Path):
    """Test check_file with valid async patterns."""
    test_file = tmp_path / "async_code.py"
    test_file.write_text("""
import asyncio
import aiofiles

async def load_data():
    await asyncio.sleep(1)
    async with aiofiles.open("file.txt") as f:
        return await f.read()
""")
    errors = check_file(test_file)
    assert len(errors) == 0


def test_check_file_with_blocking_async(tmp_path: Path):
    """Test check_file with blocking calls in async."""
    test_file = tmp_path / "async_code.py"
    test_file.write_text("""
async def load_data():
    with open("file.txt") as f:
        return f.read()
""")
    errors = check_file(test_file)
    assert len(errors) >= 1  # open and read
