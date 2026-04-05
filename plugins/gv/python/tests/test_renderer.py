"""Tests for short-v2 renderer (HTML templates + Playwright)."""

import json
import tempfile
from pathlib import Path

import pytest

# Skip all tests if playwright not installed
playwright = pytest.importorskip("playwright")


@pytest.fixture
def sample_sections():
    """Sample scriptwriter-v2 output for testing."""
    return [
        {"type": "title", "headline": "蔚来汽车 NIO", "body": "AI交易分析报告 · 2026年4月4日", "tts_text": "蔚来汽车交易分析报告，2026年4月4日。"},
        {"type": "disclaimer", "headline": "免责声明", "body": "本报告由AI生成，仅供研究参考，不构成投资建议。", "tts_text": "免责声明：本报告由AI生成，仅供研究参考。"},
        {"type": "rating", "headline": "卖出", "body": "目标价 $4.80-$5.20，下行 17-24%", "highlights": ["$4.80-$5.20", "-17%~-24%"], "tts_text": "最终评级：卖出。目标价4.80到5.20美元。"},
        {"type": "point", "index": 1, "headline": "风险收益比极差", "body": "乐观上行仅3.7%，悲观下行-37%", "highlights": ["+3.7%", "-37%"], "tts_text": "风险收益比极差。"},
        {"type": "point", "index": 2, "headline": "盈利真实性存疑", "body": "首次GAAP盈利无法验证", "highlights": ["GAAP"], "tts_text": "首次GAAP盈利无法验证。"},
        {"type": "point", "index": 3, "headline": "研发砍了三分之一", "body": "竞争对手纷纷加大投入", "highlights": ["-34%"], "tts_text": "研发支出削减百分之三十四。"},
        {"type": "conclusion", "headline": "趁强势卖出", "body": "等回调至$5区间重新评估", "highlights": ["$5"], "tts_text": "结论：趁强势卖出。"},
    ]


@pytest.fixture
def legacy_sections():
    """Legacy scriptwriter output (flat text format) for backward compat."""
    return [
        {"type": "title", "level": 1, "text": "蔚来汽车 NIO", "raw": "# 蔚来汽车 NIO"},
        {"type": "paragraph", "level": 0, "text": "免责声明：本报告由AI生成。", "raw": "免责声明：本报告由AI生成。"},
        {"type": "rating_card", "level": 1, "text": "卖出", "raw": "# **卖出**"},
    ]


class TestDetectFormat:
    def test_v2_format_detected(self, sample_sections):
        from python.renderer import _is_v2_format
        assert _is_v2_format(sample_sections) is True

    def test_legacy_format_detected(self, legacy_sections):
        from python.renderer import _is_v2_format
        assert _is_v2_format(legacy_sections) is False

    def test_empty_list(self):
        from python.renderer import _is_v2_format
        assert _is_v2_format([]) is False


class TestBuildTemplateContext:
    def test_title_context(self):
        from python.renderer import _build_template_context
        section = {"type": "title", "headline": "蔚来汽车 NIO", "body": "AI报告", "tts_text": "蔚来汽车"}
        ctx = _build_template_context(section, idx=0, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["headline"] == "蔚来汽车 NIO"
        assert ctx["ticker"] == "NIO"
        assert ctx["progress_pct"] > 0

    def test_rating_context_sell(self):
        from python.renderer import _build_template_context
        section = {"type": "rating", "headline": "卖出", "body": "目标价 $5", "highlights": ["-17%"], "tts_text": "卖出"}
        ctx = _build_template_context(section, idx=2, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["rating_class"] == "sell"

    def test_rating_context_buy(self):
        from python.renderer import _build_template_context
        section = {"type": "rating", "headline": "买入", "body": "目标价 $10", "highlights": [], "tts_text": "买入"}
        ctx = _build_template_context(section, idx=2, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["rating_class"] == "buy"

    def test_point_context_has_index(self):
        from python.renderer import _build_template_context
        section = {"type": "point", "index": 2, "headline": "Test", "body": "Body", "highlights": ["+5%"], "tts_text": "Test"}
        ctx = _build_template_context(section, idx=4, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["index"] == 2


class TestRenderShortV2Integration:
    """Integration test — requires Playwright chromium installed."""

    def test_renders_all_slides(self, sample_sections):
        from python.renderer import render_frames
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            sections_path = Path(tmpdir) / "sections.json"
            with open(sections_path, "w", encoding="utf-8") as f:
                json.dump(sample_sections, f, ensure_ascii=False)
            out_dir = Path(tmpdir) / "frames"
            result = render_frames(str(sections_path), "short", str(out_dir))
            paths = result["image_paths"]
            assert len(paths) == 7
            for p in paths:
                assert Path(p).exists()
                from PIL import Image
                img = Image.open(p)
                assert img.width == 1134
                assert img.height == 2016
