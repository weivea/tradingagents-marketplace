import pytest
from python.discussion import (
    init_discussion, read_discussion, append_discussion,
    parse_last_next_speaker,
)


def test_init_creates_file_with_header(tmp_path):
    pnl = {"aggressive": 2.3, "neutral": 0.5, "conservative": -0.1}
    res = init_discussion("2026-04-17", pnl_summary=pnl, base_dir=tmp_path)
    assert res["ok"] is True
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "2026-04-17" in content
    assert "激进" in content
    assert "+2.3" in content


def test_init_refuses_if_exists(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    res = init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    assert res["ok"] is False
    assert res["error_code"] == "DISCUSSION_EXISTS"


def test_init_force_overwrites(tmp_path):
    init_discussion("2026-04-17", pnl_summary={"aggressive": 1.0}, base_dir=tmp_path)
    res = init_discussion("2026-04-17", pnl_summary={"aggressive": 2.0},
                         base_dir=tmp_path, force=True)
    assert res["ok"] is True
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "+2.0" in content


def test_append_with_next_speaker_comment(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    append_discussion(
        "2026-04-17", speaker="aggressive",
        markdown="I crushed it today.",
        next_speaker="conservative",
        reason="want to provoke the coward",
        base_dir=tmp_path,
    )
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert "**激进选手：**" in content
    assert "crushed it" in content
    assert "next_speaker: conservative" in content
    assert "want to provoke" in content


def test_parse_last_next_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    append_discussion("2026-04-17", speaker="aggressive", markdown="line 1",
                     next_speaker="neutral", reason="r", base_dir=tmp_path)
    append_discussion("2026-04-17", speaker="neutral", markdown="line 2",
                     next_speaker="conservative", reason="r", base_dir=tmp_path)
    content = read_discussion("2026-04-17", base_dir=tmp_path)
    assert parse_last_next_speaker(content) == "conservative"


def test_parse_returns_none_when_missing(tmp_path):
    assert parse_last_next_speaker("no comments here") is None


def test_append_rejects_invalid_next_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    with pytest.raises(ValueError):
        append_discussion("2026-04-17", speaker="aggressive", markdown="x",
                         next_speaker="random_user", reason="r", base_dir=tmp_path)


def test_append_rejects_invalid_speaker(tmp_path):
    init_discussion("2026-04-17", pnl_summary={}, base_dir=tmp_path)
    with pytest.raises(ValueError):
        append_discussion("2026-04-17", speaker="ghost", markdown="x",
                         next_speaker="neutral", reason="r", base_dir=tmp_path)
