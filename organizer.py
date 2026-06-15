"""
fileorg — Smart File Organizer CLI
===================================
Usage:
  python organizer.py watch                  Watch the folder and auto-sort new files
  python organizer.py watch --dry-run        Preview what would move, nothing actually moves
  python organizer.py sort                   One-shot sort of all existing files right now
  python organizer.py sort --dry-run         Preview the one-shot sort
  python organizer.py list                   Print upcoming rules and extension mappings
  python organizer.py --config my.json watch Use a custom config file
"""

import argparse
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

from config import load_config, resolve_watch_folder, build_extension_map
from mover import move_file
from watcher import start_watching

console = Console()


def setup_logging(log_file: str) -> None:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def cmd_watch(args, config, watch_folder, ext_map):
    """Watch the folder in real time."""
    start_watching(
        watch_folder=watch_folder,
        ext_map=ext_map,
        fallback_folder=config["fallback_folder"],
        dry_run=args.dry_run,
    )


def cmd_sort(args, config, watch_folder, ext_map):
    """One-shot: sort every existing file in the watch folder right now."""
    files = [f for f in watch_folder.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not files:
        console.print(f"  [dim]No files found in {watch_folder}[/dim]")
        return

    mode = " [yellow](dry run)[/yellow]" if args.dry_run else ""
    console.print(f"\n  Sorting [bold]{len(files)}[/bold] file(s){mode}...\n")

    counts = {"moved": 0, "skipped": 0, "dry_run": 0, "error": 0}

    for file_path in sorted(files):
        result = move_file(
            file_path=file_path,
            watch_folder=watch_folder,
            ext_map=ext_map,
            fallback_folder=config["fallback_folder"],
            dry_run=args.dry_run,
        )
        status = result["status"]
        counts[status] = counts.get(status, 0) + 1

        if status == "moved":
            console.print(f"  [green]✓[/green] {result['message']}")
        elif status == "dry_run":
            console.print(f"  [blue]~[/blue] {result['message']}")
        elif status == "skipped":
            console.print(f"  [dim]−  Skipped: {Path(result['file']).name}[/dim]")
        elif status == "error":
            console.print(f"  [red]✗[/red] {result['message']}")

    console.print()
    if args.dry_run:
        console.print(f"  [blue]Dry run complete.[/blue] {counts.get('dry_run', 0)} file(s) would be moved.")
    else:
        console.print(f"  [green]Done.[/green] {counts['moved']} moved, {counts.get('error', 0)} errors, {counts['skipped']} skipped.")


def cmd_list(args, config, watch_folder, ext_map):
    """Print a formatted table of all rules and extensions."""
    console.print(f"\n  [bold]Watch folder:[/bold] {watch_folder}\n")

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Rule", style="bold", min_width=16)
    table.add_column("Destination folder", min_width=16)
    table.add_column("Extensions", style="dim")

    for rule in config["rules"]:
        exts = "  ".join(rule["extensions"])
        table.add_row(rule["name"], rule["destination"], exts)

    table.add_row(
        "[dim]Everything else[/dim]",
        config["fallback_folder"],
        "[dim](no matching extension)[/dim]",
    )

    console.print(table)
    console.print(f"  [dim]Log file: {config['log_file']}[/dim]\n")


def main():
    parser = argparse.ArgumentParser(
        prog="fileorg",
        description="Smart file organizer — auto-sorts files by extension.",
    )
    parser.add_argument(
        "--config", default="rules.json", metavar="FILE",
        help="Path to rules config (default: rules.json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would happen without moving any files",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("watch", help="Watch folder and auto-sort new files")
    subparsers.add_parser("sort",  help="One-shot sort of all existing files now")
    subparsers.add_parser("list",  help="Show current rules and extension mappings")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    config = load_config(args.config)
    setup_logging(config["log_file"])
    watch_folder = resolve_watch_folder(config)
    ext_map = build_extension_map(config)

    console.print(f"\n  [bold]fileorg[/bold] — Smart File Organizer")
    console.print(f"  [dim]Config: {args.config}[/dim]")

    if args.command == "watch":
        cmd_watch(args, config, watch_folder, ext_map)
    elif args.command == "sort":
        cmd_sort(args, config, watch_folder, ext_map)
    elif args.command == "list":
        cmd_list(args, config, watch_folder, ext_map)


if __name__ == "__main__":
    main()
