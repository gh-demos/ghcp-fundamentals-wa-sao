#!/usr/bin/env python3
"""
rename.py — Recursively rename globex_ → chroma_ in file contents and filenames.

Usage:
    python rename.py [ROOT_DIR] [--dry-run]

    ROOT_DIR   Directory to walk (default: current working directory)
    --dry-run  Print what would change without writing anything

Skips: .git/, node_modules/, and binary files.
Prints a summary of all changes made (or planned in --dry-run mode).
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ── Substitution rules (order matters: longest / most-specific first) ────────
SUBSTITUTIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"GlobexService"),  "ChromaService"),
    (re.compile(r"Globex\b"),       "Chroma"),
    (re.compile(r"globex_"),        "chroma_"),
    (re.compile(r"\bglobex\b"),     "chroma"),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

# Heuristic: skip files that look binary (NUL byte in first 8 KB)
def _is_binary(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return b"\x00" in fh.read(8192)
    except OSError:
        return True


def apply_substitutions(text: str) -> str:
    for pattern, replacement in SUBSTITUTIONS:
        text = pattern.sub(replacement, text)
    return text


def collect_files(root: Path) -> list[Path]:
    """Walk root, yielding all non-skipped file paths (deepest first for safe rename)."""
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs in-place so os.walk won't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            results.append(Path(dirpath) / fname)
    # Sort deepest paths first so we rename leaf files before parent dirs
    results.sort(key=lambda p: len(p.parts), reverse=True)
    return results


def collect_dirs(root: Path) -> list[Path]:
    """Collect directories that need renaming (deepest first)."""
    results: list[Path] = []
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        p = Path(dirpath)
        if p != root and "globex_" in p.name.lower():
            results.append(p)
    results.sort(key=lambda p: len(p.parts), reverse=True)
    return results


def rename_contents(files: list[Path], dry_run: bool) -> list[str]:
    changed: list[str] = []
    for path in files:
        if _is_binary(path):
            continue
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated = apply_substitutions(original)
        if updated != original:
            if not dry_run:
                path.write_text(updated, encoding="utf-8")
            changed.append(str(path))
    return changed


def rename_paths(paths: list[Path], dry_run: bool) -> list[tuple[str, str]]:
    renamed: list[tuple[str, str]] = []
    for path in paths:
        new_name = apply_substitutions(path.name)
        if new_name == path.name:
            continue
        new_path = path.parent / new_name
        if not dry_run:
            path.rename(new_path)
        renamed.append((str(path), str(new_path)))
    return renamed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rename globex_ → chroma_ in file contents and filenames."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=None,
        type=Path,
        help="Root directory to process (default: current directory)",
    )
    parser.add_argument(
        "--path",
        dest="path",
        type=Path,
        default=None,
        help="Root directory to process (alias for positional root argument)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing anything",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Preview changes without writing anything (alias for --dry-run)",
    )
    args = parser.parse_args()

    # --path / --check are aliases; merge with positional root / --dry-run
    dry_run = args.dry_run or args.check
    root_path = args.path or args.root or Path(".")
    root = root_path.resolve()
    if not root.is_dir():
        print(f"ERROR: {root} is not a directory.", file=sys.stderr)
        sys.exit(1)

    dry_label = " [DRY RUN]" if dry_run else ""
    print(f"Root : {root}{dry_label}\n")

    # ── Step 1: rewrite file contents ────────────────────────────────────────
    files = collect_files(root)
    content_changes = rename_contents(files, dry_run)

    # ── Step 2: rename files ─────────────────────────────────────────────────
    file_renames = rename_paths(files, dry_run)

    # ── Step 3: rename directories (deepest first) ───────────────────────────
    dirs = collect_dirs(root)
    dir_renames = rename_paths(dirs, dry_run)

    # ── Summary ──────────────────────────────────────────────────────────────
    print("━" * 60)
    print(f"Content changes{dry_label}: {len(content_changes)}")
    for p in content_changes:
        print(f"  ✏  {p}")

    print()
    print(f"File renames{dry_label}: {len(file_renames)}")
    for old, new in file_renames:
        print(f"  ⇒  {old}")
        print(f"     {new}")

    print()
    print(f"Directory renames{dry_label}: {len(dir_renames)}")
    for old, new in dir_renames:
        print(f"  ⇒  {old}")
        print(f"     {new}")

    print("━" * 60)
    total = len(content_changes) + len(file_renames) + len(dir_renames)
    print(f"Total operations{dry_label}: {total}")

    if dry_run:
        print("\nRun without --dry-run / --check to apply changes.")


if __name__ == "__main__":
    main()
