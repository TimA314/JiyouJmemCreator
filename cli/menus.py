"""
Interactive menu system for JmemCreator CLI.

Uses rich library for styled prompts and displays.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable

import torch
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from .config import Config, find_jcur_packs, find_jmem_packs, save_settings


class MainMenu:
    """
    Main interactive menu for JmemCreator CLI.

    Usage:
        menu = MainMenu(config, console)
        menu.run()  # Blocking loop until exit or start training
    """

    def __init__(self, config: Config, console: Optional[Console] = None):
        self.config = config
        self.console = console or Console()

        # Restore last-used paths if available
        if self.config.last_jcur_path and self.config.last_jcur_path.exists():
            self.config.jcur_path = self.config.last_jcur_path
        if self.config.last_output_path:
            self.config.output_path = self.config.last_output_path

    def run(self) -> Optional[str]:
        """
        Run the main menu loop.

        Returns:
            'train' if user wants to start training
            'exit' if user wants to exit
            None if interrupted
        """
        while True:
            self._show_header()
            self._show_status()

            choice = self._show_main_options()

            if choice == '1':
                self._select_source()
            elif choice == '2':
                self._configure_workers()
            elif choice == '3':
                self._select_base_jmems()
            elif choice == '4':
                self._set_output_path()
            elif choice == '5':
                if self._validate_config():
                    return 'train'
            elif choice == '6':
                self._settings_menu()
            elif choice == '0':
                if Confirm.ask("Exit JmemCreator?", default=True):
                    return 'exit'

    def _show_header(self):
        """Show the header."""
        self.console.clear()
        self.console.print(Panel(
            "[bold cyan]JmemCreator CLI[/bold cyan] v1.0\n"
            "[dim]Train JCUR curricula to generate JMEM packs[/dim]",
            border_style="blue"
        ))

    def _show_status(self):
        """Show current configuration status."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Label", style="dim")
        table.add_column("Value")

        # Brain directory
        if self.config.brain_dir:
            table.add_row("Brain:", f"[green]{self.config.brain_dir.name}[/green]")
        else:
            table.add_row("Brain:", "[red]Not configured[/red]")

        # Source
        if self.config.jcur_path:
            table.add_row("Source:", f"[green]JCUR: {self.config.jcur_path.name}[/green]")
        elif self.config.book_path:
            table.add_row("Source:", f"[green]Book: {self.config.book_path.name}[/green]")
        else:
            table.add_row("Source:", "[yellow]Not selected[/yellow]")

        # Output
        if self.config.output_path:
            table.add_row("Output:", f"[green]{self.config.output_path}[/green]")
        else:
            table.add_row("Output:", "[yellow]Not set[/yellow]")

        # Workers
        worker_count = len(self.config.worker_configs)
        if worker_count > 0:
            gpu_count = sum(1 for w in self.config.worker_configs if w[0] == 'GPU')
            cpu_count = worker_count - gpu_count
            table.add_row("Workers:", f"[green]{worker_count} ({gpu_count} GPU, {cpu_count} CPU)[/green]")
        else:
            table.add_row("Workers:", "[yellow]None configured[/yellow]")

        # Base JMEMs
        base_count = len(self.config.base_jmems)
        if base_count > 0:
            table.add_row("Base JMEMs:", f"[green]{base_count} loaded[/green]")
        else:
            table.add_row("Base JMEMs:", "[dim]None[/dim]")

        self.console.print(table)
        self.console.print()

    def _show_main_options(self) -> str:
        """Show main menu options and get choice."""
        self.console.print("[bold]Options:[/bold]")
        self.console.print("  [cyan]1[/cyan] Select Source (JCUR/Book)")
        self.console.print("  [cyan]2[/cyan] Configure Workers")
        self.console.print("  [cyan]3[/cyan] Select Base JMEMs")
        self.console.print("  [cyan]4[/cyan] Set Output Path")

        # Highlight start option if ready
        if self._validate_config(silent=True):
            self.console.print("  [bold green]5[/bold green] [bold]Start Training[/bold]")
        else:
            self.console.print("  [dim]5[/dim] Start Training [dim](configure first)[/dim]")

        self.console.print("  [cyan]6[/cyan] Settings")
        self.console.print("  [cyan]0[/cyan] Exit")
        self.console.print()

        return Prompt.ask("Select option", choices=['0', '1', '2', '3', '4', '5', '6'], default='5')

    def _select_source(self):
        """Source selection menu."""
        self.console.print("\n[bold]Select Source Type:[/bold]")
        self.console.print("  [cyan]1[/cyan] JCUR Curriculum")
        self.console.print("  [cyan]2[/cyan] PDF/TXT Book")
        self.console.print("  [cyan]0[/cyan] Back")

        choice = Prompt.ask("Select", choices=['0', '1', '2'], default='1')

        if choice == '1':
            self._select_jcur()
        elif choice == '2':
            self._select_book()

    def _select_jcur(self):
        """JCUR curriculum selection."""
        packs = find_jcur_packs()

        if not packs:
            self.console.print("[red]No JCUR packs found in curricula/[/red]")
            Prompt.ask("Press Enter to continue")
            return

        self.console.print("\n[bold]Available JCUR Packs:[/bold]")
        for i, pack in enumerate(packs, 1):
            self.console.print(f"  [cyan]{i}[/cyan] {pack['name']} ({pack['total_items']:,} items)")
        self.console.print("  [cyan]0[/cyan] Back")

        choices = ['0'] + [str(i) for i in range(1, len(packs) + 1)]
        choice = Prompt.ask("Select pack", choices=choices)

        if choice != '0':
            pack = packs[int(choice) - 1]
            self.config.jcur_path = pack['path']
            self.config.book_path = None

            # Auto-set output path
            if self.config.brain_dir:
                self.config.output_path = self.config.brain_dir / "jmem_packs" / pack['domain']

            self.console.print(f"[green]Selected: {pack['name']}[/green]")

    def _select_book(self):
        """Book file selection."""
        path_str = Prompt.ask("Enter path to PDF or TXT file")
        path = Path(path_str).expanduser()

        if not path.exists():
            self.console.print(f"[red]File not found: {path}[/red]")
            return

        if path.suffix.lower() not in ['.pdf', '.txt']:
            self.console.print("[red]File must be .pdf or .txt[/red]")
            return

        self.config.book_path = path
        self.config.jcur_path = None

        # Auto-set output path
        if self.config.brain_dir:
            name = path.stem.lower().replace(' ', '_').replace('-', '_')
            self.config.output_path = self.config.brain_dir / "jmem_packs" / name

        self.console.print(f"[green]Selected: {path.name}[/green]")

    def _configure_workers(self):
        """Worker configuration menu."""
        while True:
            self.console.print("\n[bold]Worker Configuration:[/bold]")

            # Show current workers
            if self.config.worker_configs:
                table = Table(title="Current Workers")
                table.add_column("#", style="dim", width=3)
                table.add_column("Device", width=8)
                table.add_column("Neurons", width=10)
                table.add_column("Type", width=10)

                for i, (device, neurons, is_big) in enumerate(self.config.worker_configs, 1):
                    neurons_str = f"{neurons:,}"
                    type_str = "Big Brain" if is_big else "Normal"
                    table.add_row(str(i), device, neurons_str, type_str)

                self.console.print(table)
            else:
                self.console.print("[dim]No workers configured[/dim]")

            self.console.print("\n  [cyan]1[/cyan] Add Worker")
            self.console.print("  [cyan]2[/cyan] Remove Worker")
            self.console.print("  [cyan]3[/cyan] Clear All")
            self.console.print("  [cyan]4[/cyan] Load Preset")
            self.console.print("  [cyan]5[/cyan] Save Preset")
            self.console.print("  [cyan]0[/cyan] Back")

            choice = Prompt.ask("Select", choices=['0', '1', '2', '3', '4', '5'])

            if choice == '0':
                break
            elif choice == '1':
                self._add_worker()
            elif choice == '2':
                self._remove_worker()
            elif choice == '3':
                if Confirm.ask("Clear all workers?"):
                    self.config.worker_configs.clear()
            elif choice == '4':
                self._load_preset()
            elif choice == '5':
                self._save_preset()

    def _add_worker(self):
        """Add a new worker."""
        # Device selection
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            self.console.print("\n[bold]Select Device:[/bold]")
            self.console.print("  [cyan]1[/cyan] GPU (CUDA)")
            self.console.print("  [cyan]2[/cyan] CPU")
            device_choice = Prompt.ask("Select", choices=['1', '2'], default='1')
            device = 'GPU' if device_choice == '1' else 'CPU'
        else:
            self.console.print("[yellow]GPU not available, using CPU[/yellow]")
            device = 'CPU'

        # Neuron count
        default_neurons = 400000 if device == 'GPU' else 200000
        neurons = IntPrompt.ask(
            "Neuron count",
            default=default_neurons,
        )
        neurons = max(50000, min(2000000, neurons))  # Clamp to valid range

        # Big brain option
        is_big_brain = Confirm.ask("Big Brain worker? (handles difficult items)", default=False)

        self.config.worker_configs.append((device, neurons, is_big_brain))
        self.console.print(f"[green]Added {device} worker with {neurons:,} neurons[/green]")

    def _remove_worker(self):
        """Remove a worker."""
        if not self.config.worker_configs:
            self.console.print("[yellow]No workers to remove[/yellow]")
            return

        choices = ['0'] + [str(i) for i in range(1, len(self.config.worker_configs) + 1)]
        choice = Prompt.ask("Worker # to remove (0 to cancel)", choices=choices)

        if choice != '0':
            idx = int(choice) - 1
            removed = self.config.worker_configs.pop(idx)
            self.console.print(f"[green]Removed worker {idx + 1}[/green]")

    def _load_preset(self):
        """Load a worker preset."""
        if not self.config.worker_presets:
            self.console.print("[yellow]No presets saved[/yellow]")
            return

        self.console.print("\n[bold]Available Presets:[/bold]")
        preset_names = list(self.config.worker_presets.keys())
        for i, name in enumerate(preset_names, 1):
            configs = self.config.worker_presets[name]
            self.console.print(f"  [cyan]{i}[/cyan] {name} ({len(configs)} workers)")
        self.console.print("  [cyan]0[/cyan] Cancel")

        choices = ['0'] + [str(i) for i in range(1, len(preset_names) + 1)]
        choice = Prompt.ask("Select preset", choices=choices)

        if choice != '0':
            name = preset_names[int(choice) - 1]
            self.config.worker_configs = [
                tuple(cfg) for cfg in self.config.worker_presets[name]
            ]
            self.console.print(f"[green]Loaded preset: {name}[/green]")

    def _save_preset(self):
        """Save current workers as a preset."""
        if not self.config.worker_configs:
            self.console.print("[yellow]No workers to save[/yellow]")
            return

        name = Prompt.ask("Preset name")
        if name:
            self.config.worker_presets[name] = list(self.config.worker_configs)
            save_settings(self.config)
            self.console.print(f"[green]Saved preset: {name}[/green]")

    def _select_base_jmems(self):
        """Base JMEM selection menu."""
        if not self.config.brain_dir:
            self.console.print("[red]Configure brain directory first[/red]")
            Prompt.ask("Press Enter to continue")
            return

        packs = find_jmem_packs(self.config.brain_dir)

        if not packs:
            self.console.print("[yellow]No JMEM packs found[/yellow]")
            Prompt.ask("Press Enter to continue")
            return

        # Filter out current output path
        if self.config.output_path:
            packs = [p for p in packs if p['path'] != self.config.output_path]

        self.console.print("\n[bold]Available JMEM Packs:[/bold]")
        for i, pack in enumerate(packs, 1):
            selected = pack['path'] in self.config.base_jmems
            marker = "[green]✓[/green]" if selected else " "
            self.console.print(f"  {marker} [cyan]{i}[/cyan] {pack['name']} ({pack['total_memories']:,} memories)")

        self.console.print("\n  [cyan]a[/cyan] Add all")
        self.console.print("  [cyan]c[/cyan] Clear all")
        self.console.print("  [cyan]0[/cyan] Back")

        choices = ['0', 'a', 'c'] + [str(i) for i in range(1, len(packs) + 1)]
        choice = Prompt.ask("Toggle pack", choices=choices)

        if choice == 'a':
            self.config.base_jmems = [p['path'] for p in packs]
            self.console.print(f"[green]Added all {len(packs)} packs[/green]")
        elif choice == 'c':
            self.config.base_jmems.clear()
            self.console.print("[green]Cleared base JMEMs[/green]")
        elif choice != '0':
            pack = packs[int(choice) - 1]
            if pack['path'] in self.config.base_jmems:
                self.config.base_jmems.remove(pack['path'])
                self.console.print(f"[yellow]Removed: {pack['name']}[/yellow]")
            else:
                self.config.base_jmems.append(pack['path'])
                self.console.print(f"[green]Added: {pack['name']}[/green]")

    def _set_output_path(self):
        """Set output JMEM path."""
        current = str(self.config.output_path) if self.config.output_path else ""
        path_str = Prompt.ask("Output JMEM path", default=current)

        if path_str:
            self.config.output_path = Path(path_str).expanduser()
            self.console.print(f"[green]Output path set: {self.config.output_path}[/green]")

    def _settings_menu(self):
        """Settings menu."""
        while True:
            self.console.print("\n[bold]Settings:[/bold]")
            self.console.print("  [cyan]1[/cyan] Change Brain Directory")
            self.console.print("  [cyan]2[/cyan] Start Fresh (delete existing): " +
                             ("[green]YES[/green]" if self.config.recalibrate else "[yellow]NO (resume)[/yellow]"))
            self.console.print("  [cyan]0[/cyan] Back")

            choice = Prompt.ask("Select", choices=['0', '1', '2'])

            if choice == '0':
                break
            elif choice == '1':
                self._select_brain_dir()
            elif choice == '2':
                self.config.recalibrate = not self.config.recalibrate
                if self.config.recalibrate:
                    self.console.print("[green]Will start fresh (delete existing JMEM)[/green]")
                else:
                    self.console.print("[yellow]Will resume (skip existing items)[/yellow]")

    def _select_brain_dir(self):
        """Select brain directory."""
        from .config import load_brain_modules

        path_str = Prompt.ask("Enter path to JiYouBrain directory")
        path = Path(path_str).expanduser()

        if not path.exists():
            self.console.print(f"[red]Directory not found: {path}[/red]")
            return

        if not (path / "api.py").exists():
            self.console.print("[red]Invalid brain directory (api.py not found)[/red]")
            return

        if load_brain_modules(path):
            self.config.brain_dir = path
            save_settings(self.config)
            self.console.print(f"[green]Brain loaded: {path.name}[/green]")
        else:
            self.console.print("[red]Failed to load brain modules[/red]")

    def _validate_config(self, silent: bool = False) -> bool:
        """Validate configuration is ready for training."""
        errors = []

        if not self.config.brain_dir:
            errors.append("Brain directory not configured")

        if not self.config.jcur_path and not self.config.book_path:
            errors.append("No source selected")

        if not self.config.output_path:
            errors.append("Output path not set")

        if not self.config.worker_configs:
            errors.append("No workers configured")

        if errors and not silent:
            self.console.print("\n[red]Cannot start training:[/red]")
            for error in errors:
                self.console.print(f"  [red]•[/red] {error}")
            Prompt.ask("Press Enter to continue")

        return len(errors) == 0
