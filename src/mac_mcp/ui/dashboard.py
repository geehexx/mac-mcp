"""Rich-based TUI dashboard for monitoring MAC MCP Server.

This module provides a beautiful terminal user interface for monitoring:
- Goal status and progress
- Task execution state
- Agent health and activity
- Event stream (optional)
- Performance metrics (optional)
"""

import asyncio
from datetime import datetime
from typing import Any

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from mac_mcp.config import UIConfig
from mac_mcp.core.orchestrator import Orchestrator
from mac_mcp.domain.goals import GoalState
from mac_mcp.domain.tasks import TaskState


class Dashboard:
    """TUI dashboard for MAC MCP Server.

    Provides real-time visualization of system state including goals,
    tasks, agents, and events.

    Attributes:
        orchestrator: The orchestrator to monitor
        config: UI configuration
        console: Rich console
        refresh_interval: Update interval in seconds
    """

    def __init__(
        self,
        orchestrator: Orchestrator,
        config: UIConfig | None = None,
    ) -> None:
        """Initialize the dashboard.

        Args:
            orchestrator: Orchestrator instance to monitor
            config: UI configuration (uses defaults if None)
        """
        self.orchestrator = orchestrator
        self.config = config or UIConfig()
        self.console = Console()
        self.refresh_interval = self.config.refresh_interval

    def create_layout(self) -> Layout:
        """Create the dashboard layout.

        Returns:
            Configured Rich Layout
        """
        layout = Layout()

        # Main layout: header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        # Body layout: left (goals/tasks) and right (agents/events)
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right"),
        )

        # Left column: goals and tasks
        layout["left"].split_column(
            Layout(name="goals", ratio=1),
            Layout(name="tasks", ratio=2),
        )

        # Right column: agents and events
        layout["right"].split_column(
            Layout(name="agents", ratio=1),
            Layout(name="events", ratio=1) if self.config.show_events else Layout(name="empty"),
        )

        return layout

    def render_header(self) -> Panel:
        """Render the dashboard header.

        Returns:
            Rich Panel with header content
        """
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")

        grid.add_row(
            "[bold cyan]Multi-Agent Coordination Server[/]",
            "[bold]MAC MCP Dashboard[/]",
            f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]",
        )

        return Panel(grid, style="bold white on blue")

    def render_footer(self) -> Panel:
        """Render the dashboard footer.

        Returns:
            Rich Panel with footer content
        """
        text = Text()
        text.append("Press ", style="dim")
        text.append("Ctrl+C", style="bold red")
        text.append(" to exit  •  ", style="dim")
        text.append(f"Refresh: {self.refresh_interval}s", style="dim")

        return Panel(text, style="dim")

    def render_goals(self) -> Panel:
        """Render goals table.

        Returns:
            Rich Panel with goals table
        """
        table = Table(title="Goals", expand=True, show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("State", justify="center")
        table.add_column("Tasks", justify="right")
        table.add_column("Progress", justify="right")

        goals = list(self.orchestrator._goals.values())

        if not goals:
            table.add_row("—", "[dim]No goals submitted[/]", "—", "—", "—")
        else:
            for goal in goals:
                # Get task states for progress calculation
                task_states = {
                    task_id: self.orchestrator._tasks[task_id].state.value
                    if task_id in self.orchestrator._tasks
                    else "UNKNOWN"
                    for task_id in goal.task_ids
                }

                progress = goal.calculate_progress(task_states)
                state_style = self._get_state_style(goal.state.value)

                table.add_row(
                    goal.id[:20],
                    goal.description[:40],
                    f"[{state_style}]{goal.state.value}[/]",
                    str(len(goal.task_ids)),
                    f"{progress:.0%}",
                )

        return Panel(table, border_style="green")

    def render_tasks(self) -> Panel:
        """Render tasks table.

        Returns:
            Rich Panel with tasks table
        """
        table = Table(title="Tasks", expand=True, show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("State", justify="center")
        table.add_column("Agent", style="yellow")
        table.add_column("Progress", justify="right")

        tasks = list(self.orchestrator._tasks.values())

        if not tasks:
            table.add_row("—", "[dim]No tasks created[/]", "—", "—", "—")
        else:
            # Show only last 10 tasks for readability
            for task in tasks[-10:]:
                state_style = self._get_state_style(task.state.value)
                agent = task.assigned_agent or "—"

                table.add_row(
                    task.id[:15],
                    task.description[:35],
                    f"[{state_style}]{task.state.value}[/]",
                    agent[:15],
                    f"{task.progress:.0%}" if task.progress else "0%",
                )

        return Panel(table, border_style="blue")

    def render_agents(self) -> Panel:
        """Render agents table.

        Returns:
            Rich Panel with agents table
        """
        table = Table(title="Agents", expand=True, show_header=True)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Tasks", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Capabilities")

        agents = self.orchestrator.supervisor.get_all_agents()

        if not agents:
            table.add_row("—", "—", "—", "—", "[dim]No agents registered[/]")
        else:
            for agent in agents:
                status_style = self._get_status_style(agent.status.value)
                caps = ", ".join(agent.capabilities[:3])
                if len(agent.capabilities) > 3:
                    caps += "..."

                table.add_row(
                    agent.id[:15],
                    f"[{status_style}]{agent.status.value}[/]",
                    str(len(agent.current_tasks)),
                    f"{agent.success_rate():.0%}",
                    caps[:30],
                )

        return Panel(table, border_style="magenta")

    def render_events(self) -> Panel:
        """Render recent events.

        Returns:
            Rich Panel with event log
        """
        if not self.config.show_events:
            return Panel("[dim]Events disabled[/]", title="Events", border_style="yellow")

        text = Text()
        # This would require adding event history to orchestrator
        # For now, show placeholder
        text.append("Event stream not yet implemented\n", style="dim")
        text.append("Enable event history in orchestrator to see live events", style="dim italic")

        return Panel(text, title="Recent Events", border_style="yellow")

    def _get_state_style(self, state: str) -> str:
        """Get Rich style for task/goal state.

        Args:
            state: State value

        Returns:
            Rich color style
        """
        state_colors = {
            "SUBMITTED": "cyan",
            "DECOMPOSING": "blue",
            "READY": "blue",
            "EXECUTING": "yellow",
            "PENDING": "white",
            "RUNNING": "yellow",
            "AWAITING": "magenta",
            "SUCCESS": "green",
            "COMPLETED": "green",
            "ERROR": "red",
            "FAILED": "red",
            "BLOCKED": "red",
        }
        return state_colors.get(state, "white")

    def _get_status_style(self, status: str) -> str:
        """Get Rich style for agent status.

        Args:
            status: Status value

        Returns:
            Rich color style
        """
        status_colors = {
            "ACTIVE": "green",
            "IDLE": "cyan",
            "BUSY": "yellow",
            "OFFLINE": "red",
            "FAILED": "red",
            "QUARANTINED": "red",
        }
        return status_colors.get(status, "white")

    def render(self) -> Layout:
        """Render the complete dashboard.

        Returns:
            Complete rendered layout
        """
        layout = self.create_layout()

        layout["header"].update(self.render_header())
        layout["footer"].update(self.render_footer())
        layout["goals"].update(self.render_goals())
        layout["tasks"].update(self.render_tasks())
        layout["agents"].update(self.render_agents())
        layout["events"].update(self.render_events())

        return layout

    async def run(self) -> None:
        """Run the dashboard in TUI mode.

        This starts a live-updating terminal UI that refreshes at the
        configured interval. Press Ctrl+C to exit.
        """
        with Live(
            self.render(),
            console=self.console,
            refresh_per_second=int(1 / self.refresh_interval),
            screen=True,
        ) as live:
            try:
                while True:
                    await asyncio.sleep(self.refresh_interval)
                    live.update(self.render())
            except KeyboardInterrupt:
                pass

    def print_snapshot(self) -> None:
        """Print a one-time snapshot of the dashboard.

        Useful for headless mode or debugging.
        """
        self.console.print(self.render())
