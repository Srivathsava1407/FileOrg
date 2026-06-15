import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from mover import move_file
from rich.console import Console

console = Console()


class FileOrganizerHandler(FileSystemEventHandler):
    """
    Watchdog event handler. Fires on any file created or moved into the watch folder.
    Ignores events inside subfolders (so it doesn't re-trigger on its own moves).
    """

    def __init__(self, watch_folder: Path, ext_map: dict, fallback_folder: str, dry_run: bool = False):
        self.watch_folder = watch_folder
        self.ext_map = ext_map
        self.fallback_folder = fallback_folder
        self.dry_run = dry_run
        super().__init__()

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(Path(event.src_path))

    def on_moved(self, event):
        # Fires when a browser finishes downloading (renames .crdownload → real file)
        if event.is_directory:
            return
        self._handle(Path(event.dest_path))

    def _handle(self, file_path: Path):
        # Only act on files directly inside the watch folder, not in subfolders
        if file_path.parent != self.watch_folder:
            return

        # Brief pause: let the OS finish writing before we move
        time.sleep(0.5)

        result = move_file(
            file_path=file_path,
            watch_folder=self.watch_folder,
            ext_map=self.ext_map,
            fallback_folder=self.fallback_folder,
            dry_run=self.dry_run,
        )

        if result["status"] == "moved":
            console.print(f"  [green]✓[/green] {result['message']}")
        elif result["status"] == "dry_run":
            console.print(f"  [blue]~[/blue] {result['message']}")
        elif result["status"] == "error":
            console.print(f"  [red]✗[/red] {result['message']}")


def start_watching(watch_folder: Path, ext_map: dict, fallback_folder: str, dry_run: bool = False):
    """Start the watchdog observer loop. Blocks until Ctrl+C."""
    handler = FileOrganizerHandler(
        watch_folder=watch_folder,
        ext_map=ext_map,
        fallback_folder=fallback_folder,
        dry_run=dry_run,
    )

    observer = Observer()
    observer.schedule(handler, str(watch_folder), recursive=False)
    observer.start()

    mode = "[yellow]DRY RUN[/yellow] — " if dry_run else ""
    console.print(f"\n  {mode}[bold]Watching:[/bold] {watch_folder}")
    console.print("  Press [bold]Ctrl+C[/bold] to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n  [dim]Stopping watcher...[/dim]")
        observer.stop()

    observer.join()
