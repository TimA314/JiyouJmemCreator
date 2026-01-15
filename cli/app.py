"""
Main CLI application for JmemCreator.

Handles training workflow and integrates with BrainPool.
"""

import gc
import shutil
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List, Tuple

import torch
from rich.console import Console

from .config import Config, load_settings, save_settings, load_brain_modules
from .display import TrainingDisplay, SimpleProgress
from .menus import MainMenu


class JmemCreatorCLI:
    """
    Main CLI application class.

    Usage:
        cli = JmemCreatorCLI()
        cli.run()  # Interactive mode

        # Or direct training:
        cli.train(jcur_path, output_path, worker_configs)
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config = load_settings()
        self.display: Optional[TrainingDisplay] = None
        self._stop_flag = False
        self._pool = None

        # Load brain modules if configured
        if self.config.brain_dir:
            if not load_brain_modules(self.config.brain_dir):
                self.console.print(f"[yellow]Warning: Could not load brain from {self.config.brain_dir}[/yellow]")
                self.config.brain_dir = None

    def run(self):
        """Run interactive mode with menu."""
        # Set up signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

        menu = MainMenu(self.config, self.console)
        result = menu.run()

        if result == 'train':
            self._start_training()
        elif result == 'exit':
            save_settings(self.config)
            self.console.print("[dim]Goodbye![/dim]")

    def train(
        self,
        jcur_path: Path,
        output_path: Path,
        worker_configs: List[Tuple[str, int, bool]],
        base_jmems: Optional[List[Path]] = None,
        skip_trained: bool = True,
        interactive: bool = True,
    ):
        """
        Run training directly without menu.

        Args:
            jcur_path: Path to JCUR curriculum
            output_path: Output JMEM directory path
            worker_configs: List of (device, neurons, is_big_brain) tuples
            base_jmems: Optional list of base JMEM paths
            skip_trained: Skip items already in JMEM
            interactive: Show live display (False for non-interactive)
        """
        self.config.jcur_path = jcur_path
        self.config.output_path = output_path
        self.config.worker_configs = worker_configs
        self.config.base_jmems = base_jmems or []
        self.config.recalibrate = not skip_trained

        # Set up signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

        self._start_training(interactive=interactive)

    def _start_training(self, interactive: bool = True):
        """Start the training process."""
        self._stop_flag = False

        # Validate config
        if not self.config.brain_dir:
            self.console.print("[red]Error: Brain directory not configured[/red]")
            return

        if not self.config.jcur_path:
            self.console.print("[red]Error: No JCUR curriculum selected[/red]")
            return

        if not self.config.output_path:
            self.console.print("[red]Error: Output path not set[/red]")
            return

        if not self.config.worker_configs:
            self.console.print("[red]Error: No workers configured[/red]")
            return

        # Create output directory
        self.config.output_path.mkdir(parents=True, exist_ok=True)

        # Import BrainPool
        try:
            module_name = self.config.brain_dir.name
            pool_module = __import__(f"{module_name}.pool", fromlist=['BrainPool'])
            BrainPool = pool_module.BrainPool
        except ImportError as e:
            self.console.print(f"[red]Error: Could not import BrainPool: {e}[/red]")
            return

        # Create display
        if interactive:
            self.display = TrainingDisplay(self.console)
            self.display.title = f"Training: {self.config.jcur_path.name}"
            self.display.start()
        else:
            self.display = None
            progress = SimpleProgress(self.console)
            progress.start(f"Training: {self.config.jcur_path.name}")

        try:
            # Create pool
            shard_dir = self.config.output_path / 'shards'
            self._pool = BrainPool(output_dir=str(shard_dir))

            # Add workers
            for device, neurons, is_big_brain in self.config.worker_configs:
                device_str = 'cuda' if device == 'GPU' else 'cpu'
                self._pool.add_worker(device=device_str, neurons=neurons, is_big_brain=is_big_brain)
                worker_type = "Big Brain" if is_big_brain else "Regular"
                self._log(f"Added {worker_type} worker: {device}, {neurons:,} neurons")

            self._log(f"Starting {len(self.config.worker_configs)} workers...")

            # Determine base JMEM
            output_jmem = self.config.output_path / 'index.jmem'
            if output_jmem.exists():
                base_jmem = str(output_jmem)
                self._log(f"Continuing from existing JMEM")
            elif self.config.base_jmems:
                # Find first base JMEM with index.jmem
                base_jmem = None
                for base_path in self.config.base_jmems:
                    jmem_file = base_path / 'index.jmem'
                    if jmem_file.exists():
                        base_jmem = str(jmem_file)
                        self._log(f"Using base JMEM: {base_path.name}")
                        break
            else:
                base_jmem = None
                self._log("Starting fresh (no base JMEM)")

            # Progress callback
            def on_progress(progress_pct: float, stats: dict):
                if self._stop_flag:
                    return

                total = stats.get('queue', {}).get('total', 0)
                completed = stats.get('queue', {}).get('completed', 0)
                success = stats.get('success', 0)
                failed = stats.get('failed', 0)

                # Calculate accuracy
                total_items = success + failed
                accuracy = success / total_items if total_items > 0 else 0.0

                if self.display:
                    self.display.update_progress(completed, total)
                    self.display.update_stats(accuracy, success, total_items)

                    # Update worker stats
                    worker_stats = stats.get('per_worker', [])
                    self.display.update_workers(worker_stats)
                elif not interactive:
                    # Simple progress output every 10%
                    if completed % max(1, total // 10) == 0:
                        progress.update(completed, total, f"{accuracy:.1%} accuracy")

            # Run training
            skip_trained = not self.config.recalibrate
            stats = self._pool.train_curriculum(
                jcur_path=str(self.config.jcur_path),
                output_path=str(output_jmem),
                base_jmem=base_jmem,
                on_progress=on_progress,
                progress_interval=0.5,
                skip_trained=skip_trained,
            )

            self._log(f"Training complete: {stats['success']}/{stats['total']} items ({stats.get('accuracy', 0):.1%})")

            # Copy shard to index.jmem
            shard_file = shard_dir / 'shard_0.jmem'
            if shard_file.exists():
                shutil.copy2(shard_file, output_jmem)
                self._log(f"Saved to {output_jmem.name}")

        except KeyboardInterrupt:
            self._log("Training interrupted by user")
        except Exception as e:
            import traceback
            self._log(f"Error: {e}")
            self.console.print(traceback.format_exc())
        finally:
            # Copy shard on any exit
            try:
                shard_file = self.config.output_path / 'shards' / 'shard_0.jmem'
                output_jmem = self.config.output_path / 'index.jmem'
                if shard_file.exists():
                    shutil.copy2(shard_file, output_jmem)
            except Exception:
                pass

            self._cleanup()

            if self.display:
                self.display.stop()
            elif not interactive:
                progress.finish("Training finished")

    def stop(self):
        """Request graceful stop."""
        self._stop_flag = True
        if self._pool:
            self._pool.stop_all()
        self._log("Stop requested...")

    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl+C)."""
        if self._stop_flag:
            # Second Ctrl+C - force exit
            self.console.print("\n[red]Force exit[/red]")
            sys.exit(1)
        else:
            self.console.print("\n[yellow]Stopping gracefully... (Ctrl+C again to force)[/yellow]")
            self.stop()

    def _log(self, message: str):
        """Log a message to display or console."""
        if self.display:
            self.display.log(message)
        else:
            self.console.print(f"[dim]{message}[/dim]")

    def _cleanup(self):
        """Clean up resources."""
        self._pool = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


def parse_worker_config(spec: str) -> Tuple[str, int, bool]:
    """
    Parse worker specification string.

    Format: device:neurons[:big]
    Examples:
        cuda:400000
        cpu:200000:big
        gpu:300000

    Returns:
        (device, neurons, is_big_brain) tuple
    """
    parts = spec.lower().split(':')

    if len(parts) < 2:
        raise ValueError(f"Invalid worker spec: {spec} (expected device:neurons)")

    device = parts[0]
    if device in ('cuda', 'gpu'):
        device = 'GPU'
    elif device == 'cpu':
        device = 'CPU'
    else:
        raise ValueError(f"Invalid device: {device} (expected cuda/gpu/cpu)")

    try:
        neurons = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid neuron count: {parts[1]}")

    is_big_brain = len(parts) > 2 and parts[2] == 'big'

    return (device, neurons, is_big_brain)
