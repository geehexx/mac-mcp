"""Tests for check_event_immutability.py validation script."""

import ast
from pathlib import Path

import pytest

from scripts.hooks.check_event_immutability import EventImmutabilityChecker, check_file


def test_frozen_event_passes():
    """Test that frozen event class passes validation."""
    code = """
from pydantic import BaseModel

class TaskCreatedEvent(BaseModel):
    model_config = {'frozen': True}
    task_id: str
"""
    tree = ast.parse(code)
    checker = EventImmutabilityChecker()
    checker.visit(tree)
    assert len(checker.errors) == 0


def test_mutable_event_fails():
    """Test that mutable event class fails validation."""
    code = """
from pydantic import BaseModel

class TaskCreatedEvent(BaseModel):
    task_id: str
"""
    tree = ast.parse(code)
    checker = EventImmutabilityChecker()
    checker.visit(tree)
    assert len(checker.errors) == 1
    assert "TaskCreatedEvent" in checker.errors[0]
    assert "frozen=True" in checker.errors[0]


def test_non_event_class_ignored():
    """Test that non-event classes are ignored."""
    code = """
from pydantic import BaseModel

class Task(BaseModel):
    task_id: str
"""
    tree = ast.parse(code)
    checker = EventImmutabilityChecker()
    checker.visit(tree)
    assert len(checker.errors) == 0


def test_check_file_with_valid_events(tmp_path: Path):
    """Test check_file with valid frozen events."""
    test_file = tmp_path / "events.py"
    test_file.write_text("""
from pydantic import BaseModel

class GoalSubmittedEvent(BaseModel):
    model_config = {'frozen': True}
    goal_id: str
""")
    errors = check_file(test_file)
    assert len(errors) == 0


def test_check_file_with_mutable_events(tmp_path: Path):
    """Test check_file with mutable events."""
    test_file = tmp_path / "events.py"
    test_file.write_text("""
from pydantic import BaseModel

class GoalSubmittedEvent(BaseModel):
    goal_id: str
""")
    errors = check_file(test_file)
    assert len(errors) == 1
    assert "GoalSubmittedEvent" in errors[0]
