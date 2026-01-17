"""
Terminal display components for JmemCreator CLI.

Uses rich library for beautiful terminal output.
"""

from datetime import datetime
from typing import List, Dict, Optional
from collections import deque

from rich.console import Console, Group
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TaskProgressColumn
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text


class TrainingDisplay:
    """
    Live training display with progress bar, worker table, and log output.

    Usage:
        display = TrainingDisplay()
        display.start()

        # Update during training:
        display.update_progress(current=100, total=1000, lesson="Lesson 1")
        display.update_stats(accuracy=0.85, correct=85, total=100)
        display.update_workers(worker_stats)
        display.log("Training started")

        display.stop()
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.live: Optional[Live] = None

        # State
        self.title = "JmemCreator Training"
        self.current = 0
        self.total = 0
        self.lesson = ""
        self.accuracy = 0.0
        self.correct = 0
        self.total_items = 0
        self.elapsed_seconds = 0
        self.start_time: Optional[datetime] = None
        self.worker_stats: List[Dict] = []
        self.log_messages: deque = deque(maxlen=8)  # Keep last 8 messages
        self.running = False

    def start(self):
        """Start the live display."""
        self.start_time = datetime.now()
        self.running = True
        self.live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=2,
            transient=False,
        )
        self.live.start()

    def stop(self):
        """Stop the live display."""
        self.running = False
        if self.live:
            self.live.stop()
            self.live = None

    def update_progress(self, current: int, total: int, lesson: str = ""):
        """Update progress bar."""
        self.current = current
        self.total = total
        if lesson:
            self.lesson = lesson
        self._refresh()

    def update_stats(self, accuracy: float, correct: int, total: int):
        """Update accuracy statistics."""
        self.accuracy = accuracy
        self.correct = correct
        self.total_items = total
        self._refresh()

    def update_workers(self, worker_stats: List[Dict]):
        """Update worker status table."""
        self.worker_stats = worker_stats
        self._refresh()

    def log(self, message: str):
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[dim][{timestamp}][/dim] {message}")
        self._refresh()

    def _refresh(self):
        """Refresh the display."""
        if self.live and self.running:
            self.live.update(self._render())

    def _format_elapsed(self) -> str:
        """Format elapsed time as HH:MM:SS."""
        if self.start_time:
            delta = datetime.now() - self.start_time
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"

    def _render_progress_section(self) -> Panel:
        """Render the progress section."""
        # Progress bar
        if self.total > 0:
            pct = self.current / self.total
            filled = int(pct * 30)
            bar = "[green]" + "█" * filled + "[/green]" + "░" * (30 - filled)
            progress_text = f"Progress: [{bar}] {self.current:,} / {self.total:,} ({pct:.1%})"
        else:
            progress_text = "Progress: [dim]Waiting...[/dim]"

        # Stats line
        elapsed = self._format_elapsed()
        if self.total_items > 0:
            stats_text = f"Elapsed: {elapsed}  |  Accuracy: {self.accuracy:.1%} ({self.correct:,}/{self.total_items:,})"
        else:
            stats_text = f"Elapsed: {elapsed}  |  Accuracy: --"

        content = f"{progress_text}\n{stats_text}"
        if self.lesson:
            content = f"[bold]{self.lesson}[/bold]\n{content}"

        return Panel(content, title=self.title, border_style="blue")

    def _render_worker_table(self) -> Table:
        """Render the worker status table."""
        table = Table(title="Workers", border_style="dim")
        table.add_column("ID", style="dim", width=4)
        table.add_column("Device", style="cyan", width=8)
        table.add_column("Neurons", width=8)
        table.add_column("Type", width=8)
        table.add_column("Status", width=30)
        table.add_column("Attempts", width=10)

        for i, w in enumerate(self.worker_stats):
            device = w.get('device', 'unknown')
            neurons = w.get('neurons', 0)
            neurons_str = f"{neurons // 1000}K" if neurons >= 1000 else str(neurons)
            is_big = w.get('is_big_brain', False)
            type_str = "[yellow]Big[/yellow]" if is_big else "Normal"
            status = w.get('status', 'Idle')
            current_item = w.get('current_item', '')
            if current_item:
                # Truncate long items
                if len(current_item) > 25:
                    current_item = current_item[:22] + "..."
                status = f'"{current_item}"'

            local_attempts = w.get('current_attempts', 0)
            global_attempts = w.get('current_global_attempts', 0)
            attempts_str = f"{local_attempts}/{global_attempts}" if global_attempts else str(local_attempts)

            table.add_row(str(i), device, neurons_str, type_str, status, attempts_str)

        return table

    def _render_log_section(self) -> Panel:
        """Render the log output section."""
        if self.log_messages:
            log_text = "\n".join(self.log_messages)
        else:
            log_text = "[dim]No messages yet...[/dim]"

        return Panel(
            log_text,
            title="Log",
            border_style="dim",
            height=10,
        )

    def _render(self) -> Group:
        """Render the full display."""
        elements = [
            self._render_progress_section(),
        ]

        if self.worker_stats:
            elements.append(self._render_worker_table())

        elements.append(self._render_log_section())
        elements.append(Text("Press Ctrl+C to stop training", style="dim italic"))

        return Group(*elements)


class SimpleProgress:
    """
    Simple progress display without live updates.

    For non-interactive or log-based output.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.start_time: Optional[datetime] = None

    def start(self, title: str = "Training"):
        """Start progress tracking."""
        self.start_time = datetime.now()
        self.console.print(f"\n[bold blue]{title}[/bold blue]")
        self.console.print("─" * 50)

    def update(self, current: int, total: int, message: str = ""):
        """Print progress update."""
        if total > 0:
            pct = current / total
            timestamp = datetime.now().strftime("%H:%M:%S")
            msg = f"[{timestamp}] {current:,}/{total:,} ({pct:.1%})"
            if message:
                msg += f" - {message}"
            self.console.print(msg)

    def log(self, message: str):
        """Print a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[{timestamp}] {message}")

    def finish(self, message: str = "Complete"):
        """Print completion message."""
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            self.console.print("─" * 50)
            self.console.print(f"[bold green]{message}[/bold green] (elapsed: {elapsed})")
