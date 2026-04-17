import pytest
from pathlib import Path
from python.journal import append_journal, read_journal


def test_append_creates_file(tmp_path):
    append_journal("aggressive", "2026-04-17", "Bought AAPL.", base_dir=tmp_path)
    f = tmp_path / "journals" / "aggressive-2026-04-17.md"
    assert f.exists()
    assert "Bought AAPL." in f.read_text()


def test_append_appends_not_overwrites(tmp_path):
    append_journal("aggressive", "2026-04-17", "Entry 1", base_dir=tmp_path)
    append_journal("aggressive", "2026-04-17", "Entry 2", base_dir=tmp_path)
    content = read_journal("aggressive", "2026-04-17", base_dir=tmp_path)
    assert "Entry 1" in content
    assert "Entry 2" in content


def test_read_missing_returns_empty(tmp_path):
    content = read_journal("neutral", "2026-04-17", base_dir=tmp_path)
    assert content == ""
