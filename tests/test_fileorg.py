"""
tests/test_fileorg.py
Run with: pytest tests/ -v
"""
import json
import pytest
from pathlib import Path
from mover import get_destination, resolve_destination_path, make_unique_path, move_file
from config import load_config, build_extension_map, resolve_watch_folder


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def ext_map():
    return {
        ".pdf":  "Documents",
        ".jpg":  "Images",
        ".png":  "Images",
        ".mp4":  "Videos",
        ".zip":  "Archives",
        ".py":   "Code",
        ".xlsx": "Spreadsheets",
    }


@pytest.fixture
def watch_folder(tmp_path):
    return tmp_path


@pytest.fixture
def sample_config(tmp_path):
    config = {
        "watch_folder": str(tmp_path),
        "rules": [
            {"name": "Images", "extensions": [".jpg", ".png"], "destination": "Images"},
            {"name": "Documents", "extensions": [".pdf"], "destination": "Documents"},
        ],
        "fallback_folder": "Unsorted",
        "log_file": str(tmp_path / "fileorg.log"),
    }
    config_path = tmp_path / "rules.json"
    config_path.write_text(json.dumps(config))
    return config_path, config


# ── get_destination ───────────────────────────────────────────────────────────

class TestGetDestination:
    def test_known_extension_returns_folder(self, ext_map):
        f = Path("report.pdf")
        assert get_destination(f, ext_map, "Unsorted") == "Documents"

    def test_unknown_extension_returns_fallback(self, ext_map):
        f = Path("mystery.xyz")
        assert get_destination(f, ext_map, "Unsorted") == "Unsorted"

    def test_case_insensitive_extension(self, ext_map):
        assert get_destination(Path("photo.JPG"), ext_map, "Unsorted") == "Images"
        assert get_destination(Path("photo.PNG"), ext_map, "Unsorted") == "Images"

    def test_no_extension_goes_to_fallback(self, ext_map):
        assert get_destination(Path("Makefile"), ext_map, "Unsorted") == "Unsorted"


# ── make_unique_path ──────────────────────────────────────────────────────────

class TestMakeUniquePath:
    def test_returns_original_if_not_exists(self, tmp_path):
        p = tmp_path / "file.pdf"
        assert make_unique_path(p) == p

    def test_returns_new_name_if_exists(self, tmp_path):
        p = tmp_path / "file.pdf"
        p.touch()
        unique = make_unique_path(p)
        assert unique != p
        assert unique.suffix == ".pdf"
        assert "file_" in unique.stem


# ── move_file ─────────────────────────────────────────────────────────────────

class TestMoveFile:
    def test_moves_file_to_correct_folder(self, watch_folder, ext_map):
        src = watch_folder / "report.pdf"
        src.write_text("dummy content")

        result = move_file(src, watch_folder, ext_map, "Unsorted")

        assert result["status"] == "moved"
        assert result["folder"] == "Documents"
        assert not src.exists()
        assert (watch_folder / "Documents" / "report.pdf").exists()

    def test_dry_run_does_not_move(self, watch_folder, ext_map):
        src = watch_folder / "photo.jpg"
        src.write_text("fake image")

        result = move_file(src, watch_folder, ext_map, "Unsorted", dry_run=True)

        assert result["status"] == "dry_run"
        assert src.exists()  # file still in place
        assert not (watch_folder / "Images" / "photo.jpg").exists()

    def test_unknown_extension_goes_to_unsorted(self, watch_folder, ext_map):
        src = watch_folder / "weird.abc"
        src.write_text("who knows")

        result = move_file(src, watch_folder, ext_map, "Unsorted")

        assert result["status"] == "moved"
        assert result["folder"] == "Unsorted"

    def test_skips_hidden_files(self, watch_folder, ext_map):
        src = watch_folder / ".DS_Store"
        src.write_text("")

        result = move_file(src, watch_folder, ext_map, "Unsorted")
        assert result["status"] == "skipped"

    def test_skips_temp_files(self, watch_folder, ext_map):
        src = watch_folder / "download.crdownload"
        src.write_text("")

        result = move_file(src, watch_folder, ext_map, "Unsorted")
        assert result["status"] == "skipped"

    def test_duplicate_file_gets_unique_name(self, watch_folder, ext_map):
        (watch_folder / "Documents").mkdir()
        existing = watch_folder / "Documents" / "report.pdf"
        existing.write_text("old version")

        src = watch_folder / "report.pdf"
        src.write_text("new version")

        result = move_file(src, watch_folder, ext_map, "Unsorted")
        assert result["status"] == "moved"
        assert existing.exists()  # original preserved
        assert not src.exists()


# ── config loading ────────────────────────────────────────────────────────────

class TestConfig:
    def test_load_valid_config(self, sample_config):
        config_path, expected = sample_config
        config = load_config(str(config_path))
        assert config["fallback_folder"] == "Unsorted"
        assert len(config["rules"]) == 2

    def test_build_extension_map(self, sample_config):
        config_path, config = sample_config
        ext_map = build_extension_map(config)
        assert ext_map[".jpg"] == "Images"
        assert ext_map[".pdf"] == "Documents"

    def test_first_rule_wins_duplicate_extension(self):
        config = {
            "rules": [
                {"name": "First", "extensions": [".dat"], "destination": "FolderA"},
                {"name": "Second", "extensions": [".dat"], "destination": "FolderB"},
            ]
        }
        ext_map = build_extension_map(config)
        assert ext_map[".dat"] == "FolderA"
