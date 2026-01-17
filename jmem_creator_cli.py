#!/usr/bin/env python3
"""
JMEM Creator CLI - Train JCUR curricula to generate JMEM packs.

Command-line interface for creating photographic memory packs from curricula.
Supports both interactive mode (menus) and direct mode (command-line arguments).

Usage:
    # Interactive mode (menu-driven)
    python jmem_creator_cli.py

    # First-time training (specify all options)
    python jmem_creator_cli.py train \\
        --jcur curricula/english_core.jcur \\
        --output ~/JiYouBrain/jmem_packs/english_core \\
        --worker cuda:400000 \\
        --worker cpu:200000:big

    # Continue training (uses last curriculum, output, and workers)
    python jmem_creator_cli.py train

    # List available curricula
    python jmem_creator_cli.py list

    # Show configuration
    python jmem_creator_cli.py config
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table


def main():
    parser = argparse.ArgumentParser(
        description="JMEM Creator CLI - Train JCUR curricula to generate JMEM packs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python jmem_creator_cli.py

  # Train with specific workers
  python jmem_creator_cli.py train \\
    --jcur curricula/english_core.jcur \\
    --output ~/JiYouBrain/jmem_packs/english_core \\
    --worker cuda:400000 \\
    --worker cpu:200000:big

  # Train with recalibration (don't skip existing)
  python jmem_creator_cli.py train \\
    --jcur curricula/tools.jcur \\
    --output ~/JiYouBrain/jmem_packs/tools \\
    --worker cuda:400000 \\
    --recalibrate
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train a JMEM from curriculum')
    train_parser.add_argument(
        '--jcur', '-j',
        type=Path,
        help='Path to JCUR curriculum directory (uses last trained if not specified)'
    )
    train_parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output JMEM directory path (uses last output if not specified)'
    )
    train_parser.add_argument(
        '--worker', '-w',
        action='append',
        dest='workers',
        help='Worker spec: device:neurons[:big] (e.g., cuda:400000, cpu:200000:big). Uses saved workers if not specified.'
    )
    train_parser.add_argument(
        '--base-jmem', '-b',
        action='append',
        dest='base_jmems',
        type=Path,
        help='Base JMEM path(s) for read-only context'
    )
    train_parser.add_argument(
        '--recalibrate', '-r',
        action='store_true',
        help='Recalibration mode: train all items (don\'t skip existing)'
    )
    train_parser.add_argument(
        '--brain-dir',
        type=Path,
        help='Path to JiYouBrain directory (uses saved setting if not specified)'
    )
    train_parser.add_argument(
        '--no-interactive',
        action='store_true',
        help='Disable live display (simple progress output)'
    )

    # List command
    list_parser = subparsers.add_parser('list', help='List available curricula and JMEMs')

    # Config command
    config_parser = subparsers.add_parser('config', help='Show current configuration')
    config_parser.add_argument(
        '--set-brain',
        type=Path,
        help='Set brain directory path'
    )

    args = parser.parse_args()
    console = Console()

    # Import CLI modules (after parsing to avoid import errors on --help)
    from cli.app import JmemCreatorCLI, parse_worker_config
    from cli.config import Config, load_settings, save_settings, find_jcur_packs, find_jmem_packs, load_brain_modules

    if args.command == 'train':
        # Direct training mode
        config = load_settings()

        # Override brain dir if specified
        if args.brain_dir:
            if not load_brain_modules(args.brain_dir):
                console.print(f"[red]Error: Invalid brain directory: {args.brain_dir}[/red]")
                sys.exit(1)
            config.brain_dir = args.brain_dir
            save_settings(config)
        elif not config.brain_dir:
            console.print("[red]Error: Brain directory not configured. Use --brain-dir or run interactive mode.[/red]")
            sys.exit(1)
        else:
            # Load brain modules from saved config
            if not load_brain_modules(config.brain_dir):
                console.print(f"[red]Error: Could not load brain from {config.brain_dir}[/red]")
                sys.exit(1)

        # Use last paths if not specified
        jcur_path = args.jcur
        output_path = args.output

        if jcur_path is None:
            if config.last_jcur_path and config.last_jcur_path.exists():
                jcur_path = config.last_jcur_path
                console.print(f"[dim]Using last curriculum: {jcur_path}[/dim]")
            else:
                console.print("[red]Error: No --jcur specified and no last curriculum saved.[/red]")
                sys.exit(1)

        if output_path is None:
            if config.last_output_path:
                output_path = config.last_output_path
                console.print(f"[dim]Using last output: {output_path}[/dim]")
            else:
                console.print("[red]Error: No --output specified and no last output saved.[/red]")
                sys.exit(1)

        # Validate JCUR path
        if not jcur_path.exists():
            console.print(f"[red]Error: JCUR not found: {jcur_path}[/red]")
            sys.exit(1)

        # Save paths immediately so they persist even if training is interrupted
        config.last_jcur_path = jcur_path.resolve()
        config.last_output_path = output_path.expanduser().resolve()
        save_settings(config)

        # Parse worker configs (use saved if not specified)
        if args.workers:
            try:
                worker_configs = [parse_worker_config(w) for w in args.workers]
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
        elif config.worker_configs:
            worker_configs = config.worker_configs
            console.print(f"[dim]Using saved workers: {len(worker_configs)} worker(s)[/dim]")
        else:
            console.print("[red]Error: No --worker specified and no saved workers.[/red]")
            sys.exit(1)

        # Create CLI and run training
        cli = JmemCreatorCLI(console)
        cli.train(
            jcur_path=jcur_path,
            output_path=output_path.expanduser(),
            worker_configs=worker_configs,
            base_jmems=[p.expanduser() for p in (args.base_jmems or [])],
            skip_trained=not args.recalibrate,
            interactive=not args.no_interactive,
        )

    elif args.command == 'list':
        # List available curricula and JMEMs
        config = load_settings()

        # List JCUR packs
        jcur_packs = find_jcur_packs()
        if jcur_packs:
            table = Table(title="Available JCUR Curricula")
            table.add_column("Name", style="cyan")
            table.add_column("Items", justify="right")
            table.add_column("Path")

            for pack in jcur_packs:
                table.add_row(pack['name'], f"{pack['total_items']:,}", str(pack['path']))

            console.print(table)
        else:
            console.print("[yellow]No JCUR packs found in curricula/[/yellow]")

        # List JMEM packs
        if config.brain_dir:
            jmem_packs = find_jmem_packs(config.brain_dir)
            if jmem_packs:
                console.print()
                table = Table(title="Available JMEM Packs")
                table.add_column("Name", style="green")
                table.add_column("Memories", justify="right")
                table.add_column("Path")

                for pack in jmem_packs:
                    table.add_row(pack['name'], f"{pack['total_memories']:,}", str(pack['path']))

                console.print(table)
        else:
            console.print("[dim]Configure brain directory to see JMEM packs[/dim]")

    elif args.command == 'config':
        config = load_settings()

        if args.set_brain:
            # Set brain directory
            if not load_brain_modules(args.set_brain):
                console.print(f"[red]Error: Invalid brain directory: {args.set_brain}[/red]")
                sys.exit(1)
            config.brain_dir = args.set_brain
            save_settings(config)
            console.print(f"[green]Brain directory set: {args.set_brain}[/green]")
        else:
            # Show current config
            console.print("[bold]Current Configuration:[/bold]")
            console.print()

            table = Table(show_header=False, box=None)
            table.add_column("Key", style="dim")
            table.add_column("Value")

            if config.brain_dir:
                table.add_row("Brain Directory:", f"[green]{config.brain_dir}[/green]")
            else:
                table.add_row("Brain Directory:", "[red]Not configured[/red]")

            table.add_row("Workers:", f"{len(config.worker_configs)} configured")
            table.add_row("Presets:", f"{len(config.worker_presets)} saved")

            console.print(table)

            # Show workers
            if config.worker_configs:
                console.print()
                worker_table = Table(title="Saved Workers")
                worker_table.add_column("#", style="dim")
                worker_table.add_column("Device")
                worker_table.add_column("Neurons", justify="right")
                worker_table.add_column("Type")

                for i, (device, neurons, is_big) in enumerate(config.worker_configs, 1):
                    type_str = "Big Brain" if is_big else "Normal"
                    worker_table.add_row(str(i), device, f"{neurons:,}", type_str)

                console.print(worker_table)

    else:
        # Interactive mode (no command specified)
        cli = JmemCreatorCLI(console)
        cli.run()


if __name__ == '__main__':
    main()
