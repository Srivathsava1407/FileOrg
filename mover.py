import shutil
import logging
from pathlib import Path
from datetime import datetime


def get_destination(file_path: Path, ext_map: dict, fallback_folder: str) -> str:
    """
    Look up which destination folder a file belongs in.
    Returns the folder name (not full path) — e.g. 'Documents'.
    """
    ext = file_path.suffix.lower()
    return ext_map.get(ext, fallback_folder)


def resolve_destination_path(file_path: Path, dest_folder_name: str, watch_folder: Path) -> Path:
    """
    Build the full destination path for a file.
    Destination subfolders are always created inside the watch folder.
    """
    return watch_folder / dest_folder_name / file_path.name


def make_unique_path(dest_path: Path) -> Path:
    """
    If dest_path already exists, append a timestamp to the stem to avoid overwriting.
    e.g. report.pdf -> report_2025-06-01_143022.pdf
    """
    if not dest_path.exists():
        return dest_path

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    new_name = f"{dest_path.stem}_{timestamp}{dest_path.suffix}"
    return dest_path.parent / new_name


def move_file(
    file_path: Path,
    watch_folder: Path,
    ext_map: dict,
    fallback_folder: str,
    dry_run: bool = False,
) -> dict:
    """
    Move a single file to its destination folder.

    Returns a result dict:
      {
        "file": str,
        "destination": str,
        "folder": str,
        "status": "moved" | "skipped" | "dry_run",
        "message": str,
      }
    """
    file_path = Path(file_path)

    # Skip folders, hidden files (e.g. .DS_Store), and temp files
    if not file_path.is_file():
        return _result(file_path, "", "", "skipped", "Not a file")

    if file_path.name.startswith("."):
        return _result(file_path, "", "", "skipped", "Hidden file, ignored")

    if file_path.suffix.lower() in (".tmp", ".part", ".crdownload"):
        return _result(file_path, "", "", "skipped", "Temp/incomplete download, ignored")

    folder_name = get_destination(file_path, ext_map, fallback_folder)
    dest_dir = watch_folder / folder_name
    dest_path = make_unique_path(dest_dir / file_path.name)

    if dry_run:
        msg = f"[dry-run] Would move to {dest_path.relative_to(watch_folder.parent)}"
        logging.info(msg)
        return _result(file_path, str(dest_path), folder_name, "dry_run", msg)

    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(dest_path))
        msg = f"Moved '{file_path.name}' → {folder_name}/"
        logging.info(msg)
        return _result(file_path, str(dest_path), folder_name, "moved", msg)
    except PermissionError:
        msg = f"Permission denied moving '{file_path.name}'"
        logging.warning(msg)
        return _result(file_path, str(dest_path), folder_name, "error", msg)
    except Exception as e:
        msg = f"Failed to move '{file_path.name}': {e}"
        logging.error(msg)
        return _result(file_path, str(dest_path), folder_name, "error", msg)


def _result(file_path, destination, folder, status, message):
    return {
        "file": str(file_path),
        "destination": destination,
        "folder": folder,
        "status": status,
        "message": message,
    }
