"""Tests for short-v2 composer (FFmpeg direct calls)."""

import json
import tempfile
from pathlib import Path

import pytest


class TestBuildZoompanCmd:
    def test_zoom_in(self):
        from python.composer import _build_zoompan_cmd
        cmd = _build_zoompan_cmd(
            input_path="slide.png",
            output_path="segment.mp4",
            duration=10.0,
            start_zoom=1.0,
            end_zoom=1.03,
            fps=24,
            out_w=1080,
            out_h=1920,
        )
        assert "zoompan" in " ".join(cmd)
        assert "slide.png" in cmd
        assert "segment.mp4" in cmd

    def test_static(self):
        from python.composer import _build_zoompan_cmd
        cmd = _build_zoompan_cmd(
            input_path="slide.png",
            output_path="segment.mp4",
            duration=5.0,
            start_zoom=1.0,
            end_zoom=1.0,
            fps=24,
            out_w=1080,
            out_h=1920,
        )
        assert "segment.mp4" in cmd


class TestBuildXfadeCmd:
    def test_two_segments(self):
        from python.composer import _build_xfade_cmd
        cmd = _build_xfade_cmd(
            segment_paths=["a.mp4", "b.mp4"],
            segment_durations=[10.0, 8.0],
            transitions=[
                {"transition": "fade", "duration": 1.0},
                {"transition": "slideleft", "duration": 0.5},
            ],
            output_path="merged.mp4",
        )
        assert "xfade" in " ".join(cmd)
        assert "merged.mp4" in cmd

    def test_single_segment(self):
        from python.composer import _build_xfade_cmd
        cmd = _build_xfade_cmd(
            segment_paths=["a.mp4"],
            segment_durations=[10.0],
            transitions=[{"transition": "fade", "duration": 1.0}],
            output_path="merged.mp4",
        )
        assert "merged.mp4" in cmd


class TestCalcSlideDurations:
    def test_from_timestamps(self):
        from python.composer import _calc_slide_durations
        sections = [
            {"tts_text": "你好世界。"},
            {"tts_text": "这是测试。"},
        ]
        timestamps = [
            {"text": "你好", "offset_ms": 0, "duration_ms": 500},
            {"text": "世界", "offset_ms": 500, "duration_ms": 500},
            {"text": "。", "offset_ms": 1000, "duration_ms": 100},
            {"text": "这是", "offset_ms": 1200, "duration_ms": 400},
            {"text": "测试", "offset_ms": 1600, "duration_ms": 500},
            {"text": "。", "offset_ms": 2100, "duration_ms": 100},
        ]
        total_duration = 2.2
        durations = _calc_slide_durations(sections, timestamps, total_duration)
        assert len(durations) == 2
        assert abs(sum(durations) - total_duration) < 0.1
        assert durations[0] > 0
        assert durations[1] > 0

    def test_fallback_equal_split(self):
        from python.composer import _calc_slide_durations
        sections = [{"tts_text": "A"}, {"tts_text": "B"}, {"tts_text": "C"}]
        durations = _calc_slide_durations(sections, [], 12.0)
        assert len(durations) == 3
        assert all(abs(d - 4.0) < 0.01 for d in durations)

    def test_xfade_compensation(self):
        from python.composer import _calc_slide_durations
        sections = [
            {"tts_text": "你好世界。"},
            {"tts_text": "这是测试。"},
            {"tts_text": "再见世界。"},
        ]
        timestamps = [{"text": "x", "offset_ms": 0, "duration_ms": 100}]
        total_duration = 30.0
        durations = _calc_slide_durations(sections, timestamps, total_duration, xfade_overlap=1.0)
        assert sum(durations) > total_duration
        assert abs(sum(durations) - (total_duration + 1.0)) < 0.1


class TestBuildAssSubtitles:
    def test_generates_ass_content(self):
        from python.composer import _build_ass_subtitles
        timestamps = [
            {"text": "你好", "offset_ms": 100, "duration_ms": 500},
            {"text": "世界", "offset_ms": 600, "duration_ms": 400},
        ]
        ass = _build_ass_subtitles(timestamps, width=1080, height=1920)
        assert "[Script Info]" in ass
        assert "[V4+ Styles]" in ass
        assert "你好" in ass
        assert "世界" in ass


class TestWrapAssText:
    def test_short_text_no_wrap(self):
        from python.composer import _wrap_ass_text
        result = _wrap_ass_text("你好世界", max_chars=20)
        assert result == "你好世界"

    def test_long_text_wraps_at_punctuation(self):
        from python.composer import _wrap_ass_text
        text = "建议在六块三附近，把现有多头仓位的五到七成趁强势卖掉。"
        result = _wrap_ass_text(text, max_chars=20)
        assert "\\N" in result
        for line in result.split("\\N"):
            assert len(line) <= 22  # 20 + tolerance for punctuation at boundary

    def test_long_text_without_punctuation_wraps_at_max(self):
        from python.composer import _wrap_ass_text
        text = "一二三四五六七八九十一二三四五六七八九十一二三"  # 23 chars, no punctuation
        result = _wrap_ass_text(text, max_chars=20)
        assert "\\N" in result
        lines = result.split("\\N")
        assert len(lines[0]) == 20

    def test_wraps_at_comma(self):
        from python.composer import _wrap_ass_text
        text = "全年自由现金流负一百七十亿，现金跑道大约只剩一年半"
        result = _wrap_ass_text(text, max_chars=20)
        assert "\\N" in result
        assert result.startswith("全年自由现金流负一百七十亿，")
