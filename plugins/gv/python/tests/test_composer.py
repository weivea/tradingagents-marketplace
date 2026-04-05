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
