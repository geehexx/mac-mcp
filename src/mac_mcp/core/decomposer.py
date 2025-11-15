"""Goal decomposer using LLM for autonomous task planning.

This module implements LLM-based goal decomposition that converts
high-level objectives into executable task DAGs without human intervention.
"""

import json
from typing import Any

from pydantic import BaseModel, Field

from mac_mcp.domain.tasks import Task, TaskDAG
from mac_mcp.llm.base import LLMProvider


class DecompositionResult(BaseModel):
    """Result of goal decomposition.

    Attributes:
        tasks: List of tasks created from the goal
        edges: Dependency edges (from_task_id, to_task_id)
        reasoning: Explanation of decomposition strategy
    """

    tasks: list[dict[str, Any]]
    edges: list[tuple[str, str]]
    reasoning: str = ""


class GoalDecomposer:
    """LLM-based goal decomposer for autonomous task planning.

    The decomposer uses an LLM to:
    - Analyze goal context and constraints
    - Break down complex objectives into executable tasks
    - Identify task dependencies and parallelization opportunities
    - Generate capability requirements for each task

    Attributes:
        llm_provider: LLM provider for decomposition
        max_tokens: Maximum tokens for LLM responses
        temperature: Temperature for LLM sampling
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> None:
        """Initialize the decomposer.

        Args:
            llm_provider: LLM provider instance
            max_tokens: Maximum tokens for LLM responses
            temperature: Temperature for LLM sampling
        """
        self.llm_provider = llm_provider
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def decompose(
        self,
        goal_id: str,
        description: str,
        context: dict[str, Any] | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> TaskDAG:
        """Decompose a goal into a task DAG.

        Args:
            goal_id: Goal identifier
            description: Goal description
            context: Additional context (language, framework, domain, etc.)
            constraints: Constraints (deadline, max_agents, etc.)

        Returns:
            TaskDAG with tasks and dependency edges

        Raises:
            ValueError: If decomposition fails or produces invalid DAG
        """
        # Build the decomposition prompt
        prompt = self._build_prompt(description, context or {}, constraints or {})

        # Call LLM provider
        content = await self.llm_provider.generate(
            prompt=prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        # Parse the response
        result = self._parse_response(content)

        # Create Task objects
        tasks: list[Task] = []
        for i, task_data in enumerate(result.tasks):
            task_id = task_data.get("id") or f"{goal_id}_t{i+1}"
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

        # Build task DAG
        dag = TaskDAG(tasks=tasks, edges=result.edges)

        # Validate acyclic property
        dag.validate_acyclic()

        return dag

    def _build_prompt(
        self,
        description: str,
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> str:
        """Build the decomposition prompt for Claude.

        Args:
            description: Goal description
            context: Goal context
            constraints: Goal constraints

        Returns:
            Formatted prompt string
        """
        context_str = "\n".join(f"- {k}: {v}" for k, v in context.items())
        constraints_str = "\n".join(f"- {k}: {v}" for k, v in constraints.items())

        return f"""You are a goal decomposition expert for multi-agent systems. Your task is to break down a high-level goal into executable tasks that can be assigned to specialized agents.

**Goal**: {description}

**Context**:
{context_str or "No additional context provided."}

**Constraints**:
{constraints_str or "No constraints specified."}

Decompose this goal into a structured task plan following these requirements:

1. **Task Identification**: Break down the goal into 3-10 concrete, executable tasks
2. **Dependencies**: Identify which tasks must complete before others can start
3. **Capabilities**: For each task, specify required capabilities (e.g., "python", "testing", "database", "api_design")
4. **Parallelization**: Identify tasks that can run in parallel
5. **Completeness**: Ensure the task plan fully accomplishes the goal

Respond with a JSON object in this exact format:

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
- Task IDs must be unique and referenced consistently
- Dependencies must form a DAG (no cycles)
- Each edge is [from_task_id, to_task_id] meaning from_task must complete before to_task starts
- Be specific about required capabilities to enable accurate agent matching
- Prioritize tasks appropriately

Respond with ONLY the JSON object, no additional text."""

    def _parse_response(self, response: str) -> DecompositionResult:
        """Parse Claude's response into structured result.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed decomposition result

        Raises:
            ValueError: If response cannot be parsed
        """
        # Extract JSON from response (handle markdown code blocks)
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

        # Validate required fields
        if "tasks" not in data:
            msg = "Response missing 'tasks' field"
            raise ValueError(msg)

        # Convert edges from nested lists to tuples
        edges = [tuple(edge) for edge in data.get("edges", [])]

        return DecompositionResult(
            tasks=data["tasks"],
            edges=edges,  # type: ignore[arg-type]
            reasoning=data.get("reasoning", ""),
        )
