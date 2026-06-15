import json
import sys
from pathlib import Path


def load_config(config_path: str = "rules.json") -> dict:
    """Load and validate rules.json. Exits with a clear message on bad config."""
    path = Path(config_path)

    if not path.exists():
        print(f"[error] Config file not found: {path.resolve()}")
        sys.exit(1)

    try:
        with open(path, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[error] rules.json has invalid JSON: {e}")
        sys.exit(1)

    _validate(config, path)
    return config


def _validate(config: dict, path: Path) -> None:
    """Raise ValueError with a helpful message if config is malformed."""
    required_keys = ["watch_folder", "rules", "fallback_folder", "log_file"]
    for key in required_keys:
        if key not in config:
            print(f"[error] rules.json is missing required key: '{key}'")
            sys.exit(1)

    seen_extensions = {}
    for rule in config["rules"]:
        if "name" not in rule or "extensions" not in rule or "destination" not in rule:
            print(f"[error] Each rule needs 'name', 'extensions', and 'destination'. Check rule: {rule}")
            sys.exit(1)

        for ext in rule["extensions"]:
            if not ext.startswith("."):
                print(f"[error] Extension '{ext}' in rule '{rule['name']}' must start with a dot.")
                sys.exit(1)
            ext_lower = ext.lower()
            if ext_lower in seen_extensions:
                print(f"[warning] Extension '{ext}' appears in both '{seen_extensions[ext_lower]}' and '{rule['name']}'. First rule wins.")
            else:
                seen_extensions[ext_lower] = rule["name"]


def resolve_watch_folder(config: dict) -> Path:
    """Expand ~ and resolve the watch folder to an absolute path."""
    folder = Path(config["watch_folder"]).expanduser().resolve()
    if not folder.exists():
        print(f"[error] Watch folder does not exist: {folder}")
        sys.exit(1)
    return folder


def build_extension_map(config: dict) -> dict[str, str]:
    """
    Build a flat lookup: extension (lowercase) -> destination folder name.
    e.g. {'.pdf': 'Documents', '.jpg': 'Images', ...}
    First rule wins for duplicate extensions.
    """
    ext_map = {}
    for rule in config["rules"]:
        for ext in rule["extensions"]:
            ext_lower = ext.lower()
            if ext_lower not in ext_map:
                ext_map[ext_lower] = rule["destination"]
    return ext_map
