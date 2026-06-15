# FileOrg

A CLI tool that sorts files into subfolders by extension. Point it at a folder, run `sort` to organize everything in one shot, or run `watch` to sort new files automatically as they arrive.

Built for my own Downloads folder — moved 100+ files across 9 categories the first time I ran it on real data.

## Features

- **watch mode** — detects new files the moment they land, sorts them immediately
- **sort mode** — one-shot pass over everything already in the folder
- **dry-run** — prints exactly what would move without touching anything
- **duplicate handling** — appends a timestamp instead of overwriting (`report.pdf` → `report_2026-05-20_213643.pdf`)
- **custom rules** — add any extension → folder mapping in `rules.json`
- **safe skips** — ignores hidden files, `.tmp`, `.crdownload` (partial downloads)

## Quick start

```bash
pip install -r requirements.txt

# See your rules
python organizer.py list

# Preview without moving anything
python organizer.py --dry-run sort

# Sort everything in the folder
python organizer.py sort

# Watch for new files and sort them as they arrive
python organizer.py watch
```

## Customizing rules.json

```json
{
  "watch_folder": "~/Downloads",
  "rules": [
    {
      "name": "Images",
      "extensions": [".jpg", ".jpeg", ".png", ".gif"],
      "destination": "Images"
    },
    {
      "name": "Design",
      "extensions": [".sketch", ".fig"],
      "destination": "Design Files"
    }
  ],
  "fallback_folder": "Unsorted",
  "log_file": "fileorg.log"
}
```

`destination` can be nested: `"School/CPRG-213"` creates a subfolder inside a subfolder. First rule wins if an extension appears in multiple rules.

## Running tests

```bash
pytest tests/ -v
```

13 tests — covers extension lookup, duplicate renaming, dry-run behaviour, and config validation.

## Project structure

```
fileorg/
├── organizer.py     # CLI entry point (argparse)
├── watcher.py       # watchdog observer + event handler
├── mover.py         # core file move logic (pure functions, fully testable)
├── config.py        # loads and validates rules.json
├── rules.json       # your rules — edit this freely
├── requirements.txt
├── tests/
│   └── test_fileorg.py   # 13 pytest tests
└── README.md
```
