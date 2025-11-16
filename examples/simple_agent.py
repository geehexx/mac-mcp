"""
Simple Example Agent for MAC MCP Server

This agent demonstrates best practices for building agents that connect
to the MAC MCP Server. It follows 2025 standards and includes:

- Proper registration with capabilities
- Heartbeat loop for liveness
- Task claiming and execution
- Progress reporting
- Error handling and retries
- Clean shutdown

Usage:
    python examples/simple_agent.py --agent-id my_agent --capabilities python,testing

Requirements:
    pip install anthropic mcp
"""

import asyncio
import argparse
import json
import logging
import signal
from datetime import UTC, datetime
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class SimpleAgent:
    """Example agent demonstrating MAC MCP Server integration.

    This agent can execute Python and testing tasks, demonstrating
    all key lifecycle operations and best practices.
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: list[str],
        max_concurrent_tasks: int = 3,
    ):
        """Initialize the agent.

        Args:
            agent_id: Unique agent identifier
            capabilities: List of capabilities (e.g., ["python", "testing"])
            max_concurrent_tasks: Maximum concurrent tasks to handle
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running = True
        self.current_tasks: set[str] = set()

        logger.info(
            f"Agent {agent_id} initialized with capabilities: {capabilities}"
        )

    async def connect_to_server(self):
        """Connect to MAC MCP Server.

        In a real implementation, this would establish an MCP connection
        using the MCP SDK. For this example, we use pseudocode.
        """
        # Pseudocode - replace with actual MCP SDK connection
        # from mcp import Client
        # self.mcp = Client("stdio") or Client("http://localhost:3000")
        logger.info("Connected to MAC MCP Server (pseudocode)")

    async def register(self):
        """Register agent with the orchestrator."""
        logger.info(f"Registering agent {self.agent_id}...")

        # Pseudocode MCP tool call
        # result = await self.mcp.call_tool(
        #     "register_agent",
        #     {
        #         "agent_id": self.agent_id,
        #         "capabilities": self.capabilities,
        #         "metadata": {
        #             "max_concurrent_tasks": self.max_concurrent_tasks,
        #             "version": "1.0.0",
        #             "registered_at": datetime.now(UTC).isoformat(),
        #         },
        #     }
        # )

        logger.info(f"✅ Agent {self.agent_id} registered successfully")

    async def heartbeat_loop(self):
        """Send heartbeat every 30 seconds to maintain liveness.

        The orchestrator expects heartbeats at least every 90 seconds.
        This loop sends them every 30 seconds for reliability.
        """
        logger.info("Starting heartbeat loop...")

        while self.running:
            try:
                # Calculate load (percentage of capacity used)
                load = len(self.current_tasks) / self.max_concurrent_tasks

                # Determine status
                if load < 0.7:
                    status = "healthy"
                elif load < 1.0:
                    status = "degraded"
                else:
                    status = "healthy"  # At capacity but not failing

                # Pseudocode MCP tool call
                # await self.mcp.call_tool(
                #     "heartbeat",
                #     {
                #         "agent_id": self.agent_id,
                #         "status": status,
                #         "current_tasks": list(self.current_tasks),
                #         "load": load,
                #     }
                # )

                logger.debug(
                    f"💓 Heartbeat sent (status={status}, load={load:.1%})"
                )

            except Exception as e:
                logger.error(f"⚠️  Heartbeat failed: {e}")

            # Sleep for 30 seconds before next heartbeat
            await asyncio.sleep(30)

    async def claim_task(self) -> dict[str, Any] | None:
        """Claim next available task matching agent capabilities.

        Returns:
            Task dict if one was claimed, None otherwise
        """
        # Don't claim if at capacity
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return None

        # Pseudocode MCP tool call
        # result = await self.mcp.call_tool(
        #     "claim_task",
        #     {
        #         "agent_id": self.agent_id,
        #         "capabilities": self.capabilities,
        #     }
        # )

        # Simulated task for example
        # In reality, parse result from MCP tool
        return None  # Replace with actual task from MCP

    async def execute_task(self, task: dict[str, Any]):
        """Execute a claimed task.

        Args:
            task: Task dict from claim_task
        """
        task_id = task["task_id"]
        description = task["description"]

        logger.info(f"🔨 Executing task {task_id}: {description}")
        self.current_tasks.add(task_id)

        try:
            # Report initial progress
            await self.report_progress(task_id, 0.1, "Task started...")

            # Simulate work (replace with actual task execution)
            await asyncio.sleep(2)

            # Report mid-progress
            await self.report_progress(task_id, 0.5, "Processing...")

            # Do actual work based on task type
            result = await self.do_work(task)

            # Report near-completion
            await self.report_progress(task_id, 0.9, "Finalizing...")

            # Complete the task
            await self.complete_task(task_id, result)

            logger.info(f"✅ Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"❌ Task {task_id} failed: {e}")
            await self.fail_task(task_id, e)

        finally:
            self.current_tasks.discard(task_id)

    async def do_work(self, task: dict[str, Any]) -> dict[str, Any]:
        """Perform the actual work for a task.

        Args:
            task: Task dict

        Returns:
            Task result dict
        """
        # Example: Generate Python code or run tests
        # In a real agent, this would call an LLM or execute code

        # Simulate work
        await asyncio.sleep(3)

        return {
            "artifacts": ["output.py", "tests.py"],
            "summary": f"Completed: {task['description']}",
            "metrics": {
                "execution_time_seconds": 5,
                "lines_of_code": 100,
            },
        }

    async def report_progress(
        self, task_id: str, progress: float, message: str
    ):
        """Report task progress.

        Args:
            task_id: Task identifier
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        # Pseudocode MCP tool call
        # await self.mcp.call_tool(
        #     "report_progress",
        #     {
        #         "task_id": task_id,
        #         "agent_id": self.agent_id,
        #         "progress": progress,
        #         "message": message,
        #     }
        # )

        logger.debug(f"📊 Progress {progress:.0%}: {message}")

    async def complete_task(self, task_id: str, result: dict[str, Any]):
        """Mark task as completed.

        Args:
            task_id: Task identifier
            result: Task result
        """
        # Pseudocode MCP tool call
        # await self.mcp.call_tool(
        #     "complete_task",
        #     {
        #         "task_id": task_id,
        #         "agent_id": self.agent_id,
        #         "result": result,
        #     }
        # )

        logger.info(f"✅ Task {task_id} completed")

    async def fail_task(self, task_id: str, error: Exception):
        """Report task failure.

        Args:
            task_id: Task identifier
            error: Exception that caused failure
        """
        # Determine if error is retryable
        retryable = not isinstance(
            error, (ValueError, TypeError)
        )  # Example logic

        # Pseudocode MCP tool call
        # await self.mcp.call_tool(
        #     "fail_task",
        #     {
        #         "task_id": task_id,
        #         "agent_id": self.agent_id,
        #         "error": {
        #             "type": type(error).__name__,
        #             "message": str(error),
        #             "retryable": retryable,
        #             "context": {},
        #         },
        #     }
        # )

        logger.error(f"❌ Task {task_id} failed: {error}")

    async def run(self):
        """Main agent loop."""
        logger.info(f"🤖 Agent {self.agent_id} starting...")

        try:
            # Connect to server
            await self.connect_to_server()

            # Register
            await self.register()

            # Start heartbeat loop in background
            heartbeat_task = asyncio.create_task(self.heartbeat_loop())

            # Main work loop
            logger.info("👷 Entering main work loop...")
            while self.running:
                # Try to claim a task
                task = await self.claim_task()

                if task:
                    # Execute task concurrently
                    asyncio.create_task(self.execute_task(task))
                else:
                    # No tasks available, wait before trying again
                    await asyncio.sleep(5)

            # Cleanup
            heartbeat_task.cancel()
            logger.info("👋 Agent shutting down...")

        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down gracefully...")
            self.running = False

        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            raise


def main():
    """Entry point for the example agent."""
    parser = argparse.ArgumentParser(
        description="Simple example agent for MAC MCP Server"
    )
    parser.add_argument(
        "--agent-id",
        default="simple_agent_001",
        help="Unique agent identifier",
    )
    parser.add_argument(
        "--capabilities",
        default="python,testing",
        help="Comma-separated list of capabilities",
    )
    parser.add_argument(
        "--max-concurrent-tasks",
        type=int,
        default=3,
        help="Maximum concurrent tasks",
    )

    args = parser.parse_args()

    # Parse capabilities
    capabilities = [c.strip() for c in args.capabilities.split(",")]

    # Create agent
    agent = SimpleAgent(
        agent_id=args.agent_id,
        capabilities=capabilities,
        max_concurrent_tasks=args.max_concurrent_tasks,
    )

    # Handle SIGINT gracefully
    def signal_handler(sig, frame):
        logger.info("\n👋 Received shutdown signal...")
        agent.running = False

    signal.signal(signal.SIGINT, signal_handler)

    # Run agent
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
