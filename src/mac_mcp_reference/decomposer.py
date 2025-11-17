"""Simple LLM-based goal decomposer implementation.

This module provides a basic but functional implementation of the
AbstractGoalDecomposer interface using LLM prompting.
"""

import asyncio
import json
import re
from typing import Any

from pydantic import BaseModel

from mac_mcp_core.domain.tasks import Task, TaskDAG
from mac_mcp_core.interfaces.decomposer import AbstractGoalDecomposer
from mac_mcp_reference.llm.base import LLMProvider


# Task ID validation pattern
TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class DecompositionResult(BaseModel):
    """Result of goal decomposition."""

    tasks: list[dict[str, Any]]
    edges: list[tuple[str, str]]
    reasoning: str = ""


class SimpleDecomposer(AbstractGoalDecomposer):
    """Simple LLM-based goal decomposer.

    Uses an LLM to analyze goals and generate task DAGs.
    This is the reference implementation suitable for most use cases.

    For production optimization, consider:
    - DSPyDecomposer: Self-optimizing via DSPy
    - TemplateDecomposer: Pattern-based for common workflows
    - MCPRemoteDecomposer: Delegate to external MCP service
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the simple decomposer.

        Args:
            llm_provider: LLM provider instance
            max_tokens: Maximum tokens for LLM responses
            temperature: Temperature for LLM sampling
        """
        self.llm_provider = llm_provider
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def decompose_goal(
        self,
        goal_id: str,
        user_prompt: str,
        context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> TaskDAG:
        """Decompose a goal into a task DAG with retry logic.

        Args:
            goal_id: Goal identifier
            user_prompt: Goal description
            context: Additional context
            constraints: Constraints

        Returns:
            TaskDAG with tasks and dependency edges

        Raises:
            ValueError: If decomposition fails after all retries
        """
        prompt = self._build_prompt(user_prompt, context or {}, constraints or {})

        # Retry loop with exponential backoff
        max_retries = 3
        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                content = await self.llm_provider.generate(
                    prompt=prompt,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )

                if not content or len(content.strip()) < 10:
                    msg = f"LLM returned empty response (length: {len(content)})"
                    raise ValueError(msg)  # noqa: TRY301

                result = self._parse_response(content)
                self._validate_decomposition_result(result)
                break

            except (ValueError, json.JSONDecodeError, TimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                msg = f"Goal decomposition failed after {max_retries} attempts: {last_error}"
                raise ValueError(msg) from last_error
        else:
            msg = f"Goal decomposition failed: {last_error}"
            raise ValueError(msg) from last_error

        # Create Task objects
        tasks: list[Task] = []
        for i, task_data in enumerate(result.tasks):
            task_id = task_data.get("id") or f"{goal_id}_t{i + 1}"
            task = Task(
                id=task_id,
                goal_id=goal_id,
                description=task_data["description"],
                required_capabilities=task_data.get("required_capabilities", []),
                dependencies=task_data.get("dependencies", []),
                metadata={
                    "reasoning": result.reasoning,
                    "estimated_duration": task_data.get("estimated_duration"),
                    "priority": task_data.get("priority", "normal"),
                },
            )
            tasks.append(task)

        dag = TaskDAG(tasks=tasks, edges=result.edges)
        dag.validate_acyclic()

        return dag

    def get_implementation_name(self) -> str:
        """Get the implementation name."""
        return "simple_llm"

    def _build_prompt(
        self,
        description: str,
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        """Build the decomposition prompt."""
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        constraints_str = "\n".join(f"- {k}: {v}" for k, v in constraints.items())

        return f"""You are a goal decomposition expert for multi-agent systems. Break down a high-level goal into executable tasks.

**Goal**: {description}

**Context**:
{context_str or "No additional context provided."}

**Constraints**:
{constraints_str or "No constraints specified."}

Decompose this goal into a structured task plan:

1. **Task Identification**: Break down into 3-10 concrete tasks
2. **Dependencies**: Identify task ordering requirements
3. **Capabilities**: Specify required capabilities for each task
4. **Parallelization**: Identify tasks that can run in parallel

Respond with JSON in this format:

```json
{{
  "reasoning": "Brief explanation of decomposition strategy",
  "tasks": [
    {{
      "id": "task_1",
      "description": "Clear, actionable task description",
      "required_capabilities": ["capability1", "capability2"],
      "dependencies": [],
      "estimated_duration": "short|medium|long",
      "priority": "high|normal|low"
    }}
  ],
  "edges": [
    ["task_1", "task_2"]
  ]
}}
```

**Important**:
- Task IDs must be unique
- Dependencies must form a DAG (no cycles)
- Each edge is [from_task_id, to_task_id]

Respond with ONLY the JSON object."""

    def _parse_response(self, response: str) -> DecompositionResult:
        """Parse LLM response into structured result."""
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            msg = f"Failed to parse decomposition response: {e}"
            raise ValueError(msg) from e

        if "tasks" not in data:
            msg = "Response missing 'tasks' field"
            raise ValueError(msg)

        edges = [tuple(edge) for edge in data.get("edges", [])]

        return DecompositionResult(
            tasks=data["tasks"],
            edges=edges,  # type: ignore[arg-type]
            reasoning=data.get("reasoning", ""),
        )

    def _validate_decomposition_result(self, result: DecompositionResult) -> None:
        """Validate decomposition result."""
        if not result.tasks:
            msg = "Decomposition produced zero tasks"
            raise ValueError(msg)

        if len(result.tasks) > 50:
            msg = f"Too many tasks generated: {len(result.tasks)} (max 50)"
            raise ValueError(msg)

        task_ids: set[str] = set()
        for task_data in result.tasks:
            task_id = task_data.get("id", "")
            if not TASK_ID_PATTERN.match(task_id):
                msg = f"Invalid task ID format: {task_id}"
                raise ValueError(msg)

            if task_id in task_ids:
                msg = f"Duplicate task ID: {task_id}"
                raise ValueError(msg)
            task_ids.add(task_id)

            description = task_data.get("description", "")
            if not description or len(description) < 5:
                msg = f"Task {task_id} has invalid description"
                raise ValueError(msg)
            if len(description) > 500:
                msg = f"Task {task_id} description too long"
                raise ValueError(msg)

            caps = task_data.get("required_capabilities", [])
            if not isinstance(caps, list):
                msg = f"Task {task_id} capabilities must be a list"
                raise ValueError(msg)  # noqa: TRY004

        # Validate dependencies reference existing tasks
        for task_data in result.tasks:
            dependencies = task_data.get("dependencies", [])
            for dep_id in dependencies:
                if dep_id not in task_ids:
                    msg = f"Task {task_data.get('id')} depends on non-existent task: {dep_id}"
                    raise ValueError(msg)
