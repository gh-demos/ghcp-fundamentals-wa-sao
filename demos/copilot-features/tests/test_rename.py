"""Tests for rename.py — content rewrite, binary-skip, dry-run, and file/dir rename."""

import subprocess
import sys
from pathlib import Path

import os

import pytest

# ---------------------------------------------------------------------------
# Import helpers from rename.py (located one level up)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent.parent))
from rename import (
    apply_substitutions,
    collect_files,
    collect_dirs,
    rename_contents,
    rename_paths,
    _is_binary,
    SKIP_DIRS,
)


# ── apply_substitutions ─────────────────────────────────────────────────────

class TestApplySubstitutions:
    def test_globex_prefix_replaced(self):
        assert apply_substitutions("globex_service") == "chroma_service"

    def test_class_name_replaced(self):
        assert apply_substitutions("class GlobexService:") == "class ChromaService:"

    def test_title_case_replaced(self):
        assert apply_substitutions("Globex Inc.") == "Chroma Inc."

    def test_bare_word_replaced(self):
        assert apply_substitutions("from globex import") == "from chroma import"

    def test_no_false_positive(self):
        # "globextra" should NOT be changed (word boundary on bare globex)
        assert apply_substitutions("globextra") == "globextra"

    def test_multiple_occurrences(self):
        text = "globex_utils.GlobexService.globex_add"
        result = apply_substitutions(text)
        assert "globex" not in result
        assert "chroma_utils.ChromaService.chroma_add" == result

    def test_already_chroma_untouched(self):
        text = "chroma_service.ChromaService"
        assert apply_substitutions(text) == text

    def test_empty_string(self):
        assert apply_substitutions("") == ""


# ── _is_binary ──────────────────────────────────────────────────────────────

class TestIsBinary:
    def test_text_file_not_binary(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world\n", encoding="utf-8")
        assert _is_binary(f) is False

    def test_file_with_nul_byte_is_binary(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"some\x00data")
        assert _is_binary(f) is True

    def test_python_source_not_binary(self, tmp_path):
        f = tmp_path / "module.py"
        f.write_text("class GlobexService:\n    pass\n", encoding="utf-8")
        assert _is_binary(f) is False


# ── collect_files / collect_dirs — skip logic ───────────────────────────────

class TestCollect:
    def _make_tree(self, tmp_path: Path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "pkg.js").write_text("// js\n")
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "globex_service.py").write_text("class GlobexService: pass\n")
        (tmp_path / "app" / "globex_utils.py").write_text("def globex_slugify(): pass\n")

    def test_skips_git_dir(self, tmp_path):
        self._make_tree(tmp_path)
        files = collect_files(tmp_path)
        paths = [str(f) for f in files]
        assert not any(".git" in p for p in paths)

    def test_skips_node_modules(self, tmp_path):
        self._make_tree(tmp_path)
        files = collect_files(tmp_path)
        # Use path parts relative to tmp_path to avoid the pytest tmp dir name
        # (e.g. 'test_skips_node_modules0') containing the substring 'node_modules'.
        assert not any(
            "node_modules" in Path(f).relative_to(tmp_path).parts
            for f in files
        )

    def test_collects_app_files(self, tmp_path):
        self._make_tree(tmp_path)
        files = collect_files(tmp_path)
        names = [f.name for f in files]
        assert "globex_service.py" in names
        assert "globex_utils.py" in names

    def test_collect_dirs_detects_globex_dir(self, tmp_path):
        (tmp_path / "globex_module").mkdir()
        (tmp_path / "globex_module" / "init.py").write_text("")
        dirs = collect_dirs(tmp_path)
        assert any("globex_module" in str(d) for d in dirs)

    def test_collect_dirs_skips_git(self, tmp_path):
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "globex_ref").mkdir()
        dirs = collect_dirs(tmp_path)
        assert not any(".git" in str(d) for d in dirs)


# ── rename_contents ──────────────────────────────────────────────────────────

class TestRenameContents:
    def test_rewrites_matching_file(self, tmp_path):
        f = tmp_path / "globex_service.py"
        f.write_text("class GlobexService:\n    def globex_add(self): pass\n", encoding="utf-8")
        changed = rename_contents([f], dry_run=False)
        assert str(f) in changed
        content = f.read_text(encoding="utf-8")
        assert "chroma" in content.lower()
        assert "globex" not in content.lower()

    def test_dry_run_does_not_write(self, tmp_path):
        f = tmp_path / "globex_utils.py"
        original = "def globex_slugify(): pass\n"
        f.write_text(original, encoding="utf-8")
        changed = rename_contents([f], dry_run=True)
        assert str(f) in changed          # still reported
        assert f.read_text(encoding="utf-8") == original  # NOT written

    def test_skips_binary_file(self, tmp_path):
        f = tmp_path / "globex_data.bin"
        f.write_bytes(b"globex_\x00binary")
        changed = rename_contents([f], dry_run=False)
        assert str(f) not in changed
        assert f.read_bytes() == b"globex_\x00binary"  # untouched

    def test_unchanged_file_not_reported(self, tmp_path):
        f = tmp_path / "readme.txt"
        f.write_text("No matches here.\n", encoding="utf-8")
        changed = rename_contents([f], dry_run=False)
        assert changed == []


# ── rename_paths (files) ─────────────────────────────────────────────────────

class TestRenamePaths:
    def test_renames_file(self, tmp_path):
        f = tmp_path / "globex_service.py"
        f.write_text("")
        renames = rename_paths([f], dry_run=False)
        assert len(renames) == 1
        old, new = renames[0]
        assert "globex_service" in old
        assert "chroma_service" in new
        assert (tmp_path / "chroma_service.py").exists()
        assert not f.exists()

    def test_dry_run_does_not_rename(self, tmp_path):
        f = tmp_path / "globex_utils.py"
        f.write_text("")
        renames = rename_paths([f], dry_run=True)
        assert len(renames) == 1  # reported
        assert f.exists()         # still exists
        assert not (tmp_path / "chroma_utils.py").exists()

    def test_non_matching_file_untouched(self, tmp_path):
        f = tmp_path / "other.py"
        f.write_text("")
        renames = rename_paths([f], dry_run=False)
        assert renames == []
        assert f.exists()


# ── CLI integration (--dry-run flag) ─────────────────────────────────────────

class TestCLI:
    _RENAME_SCRIPT = str(
        Path(__file__).parent.parent / "rename.py"
    )

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        return subprocess.run(
            [sys.executable, self._RENAME_SCRIPT] + args,
            capture_output=True,
            encoding="utf-8",  # decode captured bytes as UTF-8, not cp1252
            env=env,
        )

    def test_dry_run_exits_zero(self, tmp_path):
        (tmp_path / "globex_service.py").write_text("class GlobexService: pass\n")
        result = self._run([str(tmp_path), "--dry-run"])
        assert result.returncode == 0

    def test_dry_run_outputs_dry_run_label(self, tmp_path):
        (tmp_path / "globex_service.py").write_text("class GlobexService: pass\n")
        result = self._run([str(tmp_path), "--dry-run"])
        assert "[DRY RUN]" in result.stdout

    def test_dry_run_does_not_modify_files(self, tmp_path):
        f = tmp_path / "globex_service.py"
        original = "class GlobexService: pass\n"
        f.write_text(original)
        self._run([str(tmp_path), "--dry-run"])
        assert f.read_text() == original
        assert not (tmp_path / "chroma_service.py").exists()

    def test_live_run_renames_and_rewrites(self, tmp_path):
        f = tmp_path / "globex_service.py"
        f.write_text("class GlobexService: pass\n")
        result = self._run([str(tmp_path)])
        assert result.returncode == 0
        assert not f.exists()
        new_f = tmp_path / "chroma_service.py"
        assert new_f.exists()
        assert "ChromaService" in new_f.read_text()

    def test_live_run_reports_totals(self, tmp_path):
        (tmp_path / "globex_utils.py").write_text("def globex_slugify(): pass\n")
        result = self._run([str(tmp_path)])
        assert "Total operations" in result.stdout

    def test_invalid_root_exits_nonzero(self, tmp_path):
        result = self._run([str(tmp_path / "nonexistent")])
        assert result.returncode != 0

    def test_check_flag_is_alias_for_dry_run(self, tmp_path):
        f = tmp_path / "globex_service.py"
        original = "class GlobexService: pass\n"
        f.write_text(original)
        result = self._run(["--path", str(tmp_path), "--check"])
        assert result.returncode == 0
        assert "[DRY RUN]" in result.stdout
        assert f.read_text() == original           # nothing written
        assert not (tmp_path / "chroma_service.py").exists()

    def test_path_flag_is_alias_for_positional(self, tmp_path):
        f = tmp_path / "globex_utils.py"
        f.write_text("def globex_slugify(): pass\n")
        result = self._run(["--path", str(tmp_path)])
        assert result.returncode == 0
        assert not f.exists()
        assert (tmp_path / "chroma_utils.py").exists()
