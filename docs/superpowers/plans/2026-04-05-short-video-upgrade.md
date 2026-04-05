# Short Video Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the gen-video short version from plain text slides to TikTok-quality video with HTML/CSS rendering, FFmpeg animations, and an enhanced scriptwriter agent.

**Architecture:** Replace `_render_short()` (Pillow) with Jinja2 HTML templates + Playwright screenshots. Replace `_compose_short()` (MoviePy) with direct FFmpeg calls for xfade transitions, Ken Burns zoompan, and ASS subtitle overlay. Upgrade video-scriptwriter agent to output structured JSON with headline/body/highlights/tts_text fields.

**Tech Stack:** Python 3.13, Playwright (async), Jinja2, FFmpeg (via imageio-ffmpeg at `C:\Users\55028\AppData\Local\Programs\Python\Python313\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`), edge-tts, Pillow (full version only)

**Spec:** `docs/superpowers/specs/2026-04-05-short-video-upgrade-design.md`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `plugins/gv/python/templates/base.css` | Create | Shared CSS: colors, fonts, backgrounds, card styles, progress bar |
| `plugins/gv/python/templates/title.html` | Create | Title slide template |
| `plugins/gv/python/templates/disclaimer.html` | Create | Disclaimer slide template |
| `plugins/gv/python/templates/rating.html` | Create | Rating slide template (red/green/yellow) |
| `plugins/gv/python/templates/point.html` | Create | Key point slide template with number highlights |
| `plugins/gv/python/templates/conclusion.html` | Create | Conclusion slide template |
| `plugins/gv/python/config.py` | Modify | Add short-v2 config: template paths, transition map, Ken Burns params, FFmpeg path |
| `plugins/gv/python/renderer.py` | Modify | Rewrite `_render_short()` to use Playwright + Jinja2; keep `_render_full()` unchanged |
| `plugins/gv/python/composer.py` | Modify | Rewrite `_compose_short()` to use FFmpeg directly; keep `_compose_full()` unchanged |
| `plugins/gv/python/__main__.py` | Modify | Add Playwright browser lifecycle management |
| `agents/video-scriptwriter.md` | Modify | Upgrade output format to structured JSON with headline/body/highlights/tts_text |
| `plugins/gv/requirements.txt` | Modify | Add playwright, jinja2 |
| `plugins/gv/python/tests/test_renderer.py` | Create | Tests for HTML template rendering |
| `plugins/gv/python/tests/test_composer.py` | Create | Tests for FFmpeg command building |
| `plugins/gv/python/tests/__init__.py` | Create | Test package init |

---

## Task 1: Install Dependencies & Configure FFmpeg Path

**Files:**
- Modify: `plugins/gv/requirements.txt`
- Modify: `plugins/gv/python/config.py`

- [ ] **Step 1: Install playwright and jinja2**

```bash
pip install playwright jinja2
playwright install chromium
```

- [ ] **Step 2: Update requirements.txt**

Add to `plugins/gv/requirements.txt`:

```
edge-tts>=6.1.0
moviepy>=2.0.0
Pillow>=10.0.0
numpy>=1.24.0
playwright>=1.40.0
jinja2>=3.1.0
```

- [ ] **Step 3: Add short-v2 config to config.py**

Add the following block at the end of `plugins/gv/python/config.py` (after the existing `SHORT_TARGET_WORDS` line):

```python
# --- Short V2: HTML/CSS + FFmpeg upgrade ---
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

# Oversized render for Ken Burns (5% extra)
SHORT_V2_RENDER_WIDTH = 1134   # 1080 * 1.05
SHORT_V2_RENDER_HEIGHT = 2016  # 1920 * 1.05
SHORT_V2_OUTPUT_WIDTH = 1080
SHORT_V2_OUTPUT_HEIGHT = 1920

# FFmpeg path (bundled with imageio-ffmpeg)
def _get_ffmpeg_path() -> str:
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        return get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"  # hope it's on PATH

FFMPEG_PATH = _get_ffmpeg_path()

# Transition effects per slide type
SHORT_V2_TRANSITIONS: dict[str, dict] = {
    "title":      {"transition": "fade",      "duration": 1.0},
    "disclaimer": {"transition": "fadeblack",  "duration": 0.5},
    "rating":     {"transition": "zoomin",     "duration": 0.8},
    "point":      {"transition": "slideleft",  "duration": 0.5},
    "conclusion": {"transition": "wipeup",     "duration": 0.8},
}

# Ken Burns per slide type: (start_zoom, end_zoom)
SHORT_V2_KENBURNS: dict[str, tuple[float, float]] = {
    "title":      (1.0, 1.03),
    "disclaimer": (1.0, 1.0),   # static
    "rating":     (1.03, 1.0),  # zoom out
    "point":      (1.0, 1.03),  # zoom in
    "conclusion": (1.0, 1.03),
}
```

- [ ] **Step 4: Verify config loads without error**

```bash
cd plugins/gv && python -c "from python.config import FFMPEG_PATH, TEMPLATES_DIR, SHORT_V2_TRANSITIONS; print(f'FFmpeg: {FFMPEG_PATH}'); print(f'Templates: {TEMPLATES_DIR}'); print(f'Transitions: {list(SHORT_V2_TRANSITIONS.keys())}')"
```

Expected: prints the FFmpeg path, templates dir, and transition type list without errors.

- [ ] **Step 5: Commit**

```bash
git add plugins/gv/requirements.txt plugins/gv/python/config.py
git commit -m "feat(gv): add short-v2 config and dependencies"
```

---

## Task 2: Create HTML/CSS Templates

**Files:**
- Create: `plugins/gv/python/templates/base.css`
- Create: `plugins/gv/python/templates/title.html`
- Create: `plugins/gv/python/templates/disclaimer.html`
- Create: `plugins/gv/python/templates/rating.html`
- Create: `plugins/gv/python/templates/point.html`
- Create: `plugins/gv/python/templates/conclusion.html`

- [ ] **Step 1: Create templates directory**

```bash
mkdir -p plugins/gv/python/templates
```

- [ ] **Step 2: Create base.css**

Create `plugins/gv/python/templates/base.css`:

```css
/* Gen-Video Short V2 — Shared Styles */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');

:root {
  --bg-primary: #0a0e27;
  --bg-secondary: #141833;
  --text-primary: #e8ecff;
  --text-secondary: #8891b3;
  --accent-purple: #646cff;
  --accent-blue: #3b82f6;
  --rating-sell: #ff4444;
  --rating-buy: #4ade80;
  --rating-hold: #fbbf24;
  --card-bg: rgba(255, 255, 255, 0.05);
  --card-border: rgba(255, 255, 255, 0.08);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  width: 1134px;
  height: 2016px;
  font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  color: var(--text-primary);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* --- Background variants --- */
.bg-title {
  background: radial-gradient(ellipse at 50% 30%, #1a1f4a 0%, var(--bg-primary) 70%);
}
.bg-disclaimer {
  background: linear-gradient(180deg, var(--bg-primary) 0%, #0d1130 100%);
}
.bg-rating {
  background: radial-gradient(ellipse at 50% 50%, #1a1040 0%, var(--bg-primary) 70%);
}
.bg-point {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}
.bg-conclusion {
  background: radial-gradient(ellipse at 50% 70%, #1a1540 0%, #080b20 70%);
}

/* --- Card --- */
.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 24px;
  padding: 60px 50px;
  max-width: 960px;
  width: 90%;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

/* --- Typography --- */
.headline-xl {
  font-size: 72px;
  font-weight: 900;
  line-height: 1.3;
  letter-spacing: 2px;
}
.headline-lg {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.3;
}
.headline-md {
  font-size: 44px;
  font-weight: 700;
  line-height: 1.4;
}
.body-text {
  font-size: 32px;
  font-weight: 400;
  line-height: 1.6;
  color: var(--text-secondary);
}
.label {
  font-size: 28px;
  font-weight: 400;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 4px;
}

/* --- Highlight chips --- */
.highlights {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin: 30px 0;
}
.chip {
  background: linear-gradient(135deg, rgba(100,108,255,0.2), rgba(59,130,246,0.2));
  border: 1px solid rgba(100,108,255,0.3);
  border-radius: 12px;
  padding: 12px 24px;
  font-size: 36px;
  font-weight: 700;
  color: var(--text-primary);
}
.chip.negative {
  background: linear-gradient(135deg, rgba(255,68,68,0.2), rgba(255,68,68,0.1));
  border-color: rgba(255,68,68,0.3);
  color: var(--rating-sell);
}
.chip.positive {
  background: linear-gradient(135deg, rgba(74,222,128,0.2), rgba(74,222,128,0.1));
  border-color: rgba(74,222,128,0.3);
  color: var(--rating-buy);
}

/* --- Point index circle --- */
.point-index {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin-bottom: 30px;
}

/* --- Progress bar --- */
.progress-bar {
  position: absolute;
  bottom: 120px;
  left: 80px;
  right: 80px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.progress-index {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-purple);
  min-width: 36px;
}
.progress-track {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-purple), var(--accent-blue));
  border-radius: 2px;
}

/* --- Brand bar --- */
.brand-bar {
  position: absolute;
  bottom: 60px;
  left: 80px;
  right: 80px;
  display: flex;
  justify-content: space-between;
  font-size: 22px;
  color: rgba(255, 255, 255, 0.25);
}

/* --- Decorative elements --- */
.deco-line {
  width: 80px;
  height: 3px;
  background: linear-gradient(90deg, var(--accent-purple), transparent);
  margin-bottom: 30px;
}
.deco-line-center {
  width: 120px;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--accent-purple), transparent);
  margin: 30px auto;
}

/* --- Rating colors --- */
.rating-sell { color: var(--rating-sell); }
.rating-buy { color: var(--rating-buy); }
.rating-hold { color: var(--rating-hold); }

/* Grid decoration for title */
.grid-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(100,108,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(100,108,255,0.03) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}
```

- [ ] **Step 3: Create title.html**

Create `plugins/gv/python/templates/title.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="base.css">
</head>
<body class="bg-title">
  <div class="grid-overlay"></div>
  <div style="text-align: center; z-index: 1; position: relative;">
    <div class="deco-line-center"></div>
    <h1 class="headline-xl" style="margin-bottom: 24px;">{{ headline }}</h1>
    <p class="body-text" style="font-size: 30px;">{{ body }}</p>
    <div class="deco-line-center" style="margin-top: 40px;"></div>
  </div>
  <div class="brand-bar">
    <span>{{ ticker }} · AI Trading Report</span>
    <span>{{ date }}</span>
  </div>
</body>
</html>
```

- [ ] **Step 4: Create disclaimer.html**

Create `plugins/gv/python/templates/disclaimer.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="base.css">
</head>
<body class="bg-disclaimer">
  <div style="text-align: center; opacity: 0.6;">
    <div style="font-size: 48px; margin-bottom: 30px;">⚠</div>
    <h2 class="headline-md" style="margin-bottom: 24px; opacity: 0.8;">{{ headline }}</h2>
    <p class="body-text" style="max-width: 800px; opacity: 0.6;">{{ body }}</p>
  </div>
  <div class="progress-bar">
    <span class="progress-index">❶</span>
    <div class="progress-track">
      <div class="progress-fill" style="width: {{ progress_pct }}%;"></div>
    </div>
  </div>
  <div class="brand-bar">
    <span>{{ ticker }}</span>
    <span>{{ date }}</span>
  </div>
</body>
</html>
```

- [ ] **Step 5: Create rating.html**

Create `plugins/gv/python/templates/rating.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="base.css">
</head>
<body class="bg-rating">
  <div style="text-align: center;">
    <p class="label" style="margin-bottom: 20px;">最终评级</p>
    <div class="card" style="display: inline-block; text-align: center; padding: 50px 80px;">
      <h1 class="headline-xl rating-{{ rating_class }}" style="font-size: 96px; margin-bottom: 30px;">
        {{ headline }}
      </h1>
      {% if highlights %}
      <div class="highlights" style="justify-content: center;">
        {% for h in highlights %}
        <span class="chip {{ 'negative' if h.startswith('-') else 'positive' if h.startswith('+') else '' }}">{{ h }}</span>
        {% endfor %}
      </div>
      {% endif %}
      <p class="body-text" style="margin-top: 20px;">{{ body }}</p>
    </div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">❷</span>
    <div class="progress-track">
      <div class="progress-fill" style="width: {{ progress_pct }}%;"></div>
    </div>
  </div>
  <div class="brand-bar">
    <span>{{ ticker }}</span>
    <span>{{ date }}</span>
  </div>
</body>
</html>
```

- [ ] **Step 6: Create point.html**

Create `plugins/gv/python/templates/point.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="base.css">
</head>
<body class="bg-point">
  <div style="width: 90%; max-width: 960px;">
    <div class="point-index">{{ index }}</div>
    <div class="card">
      <h2 class="headline-md" style="margin-bottom: 20px;">{{ headline }}</h2>
      {% if highlights %}
      <div class="highlights">
        {% for h in highlights %}
        <span class="chip {{ 'negative' if h.startswith('-') else 'positive' if h.startswith('+') or h.startswith('$') else '' }}">{{ h }}</span>
        {% endfor %}
      </div>
      {% endif %}
      <p class="body-text">{{ body }}</p>
    </div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">❸</span>
    <div class="progress-track">
      <div class="progress-fill" style="width: {{ progress_pct }}%;"></div>
    </div>
  </div>
  <div class="brand-bar">
    <span>{{ ticker }}</span>
    <span>{{ date }}</span>
  </div>
</body>
</html>
```

- [ ] **Step 7: Create conclusion.html**

Create `plugins/gv/python/templates/conclusion.html`:

```html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="base.css">
</head>
<body class="bg-conclusion">
  <div style="text-align: center;">
    <div class="deco-line-center"></div>
    <p class="label" style="margin-bottom: 20px;">结论</p>
    <h1 class="headline-lg" style="margin-bottom: 24px;">{{ headline }}</h1>
    {% if highlights %}
    <div class="highlights" style="justify-content: center; margin-bottom: 20px;">
      {% for h in highlights %}
      <span class="chip">{{ h }}</span>
      {% endfor %}
    </div>
    {% endif %}
    <p class="body-text" style="font-size: 34px;">{{ body }}</p>
    <div class="deco-line-center" style="margin-top: 40px;"></div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">❼</span>
    <div class="progress-track">
      <div class="progress-fill" style="width: 100%;"></div>
    </div>
  </div>
  <div class="brand-bar">
    <span>{{ ticker }}</span>
    <span>{{ date }}</span>
  </div>
</body>
</html>
```

- [ ] **Step 8: Verify all templates exist**

```bash
ls -la plugins/gv/python/templates/
```

Expected: `base.css`, `title.html`, `disclaimer.html`, `rating.html`, `point.html`, `conclusion.html` — 6 files.

- [ ] **Step 9: Commit**

```bash
git add plugins/gv/python/templates/
git commit -m "feat(gv): add HTML/CSS slide templates for short-v2"
```

---

## Task 3: Rewrite Renderer — Playwright + Jinja2

**Files:**
- Modify: `plugins/gv/python/renderer.py`
- Create: `plugins/gv/python/tests/__init__.py`
- Create: `plugins/gv/python/tests/test_renderer.py`

- [ ] **Step 1: Create test package**

Create `plugins/gv/python/tests/__init__.py`:

```python
```

- [ ] **Step 2: Write test for template rendering**

Create `plugins/gv/python/tests/test_renderer.py`:

```python
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
        {
            "type": "title",
            "headline": "蔚来汽车 NIO",
            "body": "AI交易分析报告 · 2026年4月4日",
            "tts_text": "蔚来汽车交易分析报告，2026年4月4日。"
        },
        {
            "type": "disclaimer",
            "headline": "免责声明",
            "body": "本报告由AI生成，仅供研究参考，不构成投资建议。",
            "tts_text": "免责声明：本报告由AI生成，仅供研究参考。"
        },
        {
            "type": "rating",
            "headline": "卖出",
            "body": "目标价 $4.80-$5.20，下行 17-24%",
            "highlights": ["$4.80-$5.20", "-17%~-24%"],
            "tts_text": "最终评级：卖出。目标价4.80到5.20美元。"
        },
        {
            "type": "point",
            "index": 1,
            "headline": "风险收益比极差",
            "body": "乐观上行仅3.7%，悲观下行-37%",
            "highlights": ["+3.7%", "-37%"],
            "tts_text": "风险收益比极差。"
        },
        {
            "type": "point",
            "index": 2,
            "headline": "盈利真实性存疑",
            "body": "首次GAAP盈利无法验证",
            "highlights": ["GAAP"],
            "tts_text": "首次GAAP盈利无法验证。"
        },
        {
            "type": "point",
            "index": 3,
            "headline": "研发砍了三分之一",
            "body": "竞争对手纷纷加大投入",
            "highlights": ["-34%"],
            "tts_text": "研发支出削减百分之三十四。"
        },
        {
            "type": "conclusion",
            "headline": "趁强势卖出",
            "body": "等回调至$5区间重新评估",
            "highlights": ["$5"],
            "tts_text": "结论：趁强势卖出。"
        },
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
        section = {
            "type": "title",
            "headline": "蔚来汽车 NIO",
            "body": "AI报告",
            "tts_text": "蔚来汽车",
        }
        ctx = _build_template_context(section, idx=0, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["headline"] == "蔚来汽车 NIO"
        assert ctx["ticker"] == "NIO"
        assert ctx["progress_pct"] > 0

    def test_rating_context_sell(self):
        from python.renderer import _build_template_context
        section = {
            "type": "rating",
            "headline": "卖出",
            "body": "目标价 $5",
            "highlights": ["-17%"],
            "tts_text": "卖出",
        }
        ctx = _build_template_context(section, idx=2, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["rating_class"] == "sell"

    def test_rating_context_buy(self):
        from python.renderer import _build_template_context
        section = {
            "type": "rating",
            "headline": "买入",
            "body": "目标价 $10",
            "highlights": [],
            "tts_text": "买入",
        }
        ctx = _build_template_context(section, idx=2, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["rating_class"] == "buy"

    def test_point_context_has_index(self):
        from python.renderer import _build_template_context
        section = {
            "type": "point",
            "index": 2,
            "headline": "Test",
            "body": "Body",
            "highlights": ["+5%"],
            "tts_text": "Test",
        }
        ctx = _build_template_context(section, idx=4, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["index"] == 2


class TestRenderShortV2Integration:
    """Integration test — requires Playwright chromium installed."""

    def test_renders_all_slides(self, sample_sections):
        from python.renderer import render_frames
        with tempfile.TemporaryDirectory() as tmpdir:
            sections_path = Path(tmpdir) / "sections.json"
            with open(sections_path, "w", encoding="utf-8") as f:
                json.dump(sample_sections, f, ensure_ascii=False)
            out_dir = Path(tmpdir) / "frames"
            result = render_frames(str(sections_path), "short", str(out_dir))
            paths = result["image_paths"]
            assert len(paths) == 7
            for p in paths:
                assert Path(p).exists()
                # Check image is roughly the right size (oversized for Ken Burns)
                from PIL import Image
                img = Image.open(p)
                assert img.width == 1134
                assert img.height == 2016
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd plugins/gv && python -m pytest python/tests/test_renderer.py -v
```

Expected: FAIL — `_is_v2_format`, `_build_template_context` not defined yet.

- [ ] **Step 4: Rewrite `_render_short()` in renderer.py**

Replace everything in `plugins/gv/python/renderer.py` from the `_render_short` function definition to end of file. Keep ALL existing code above `_render_short` untouched (imports, `_load_font`, `_wrap_text`, `render_frames`, `_render_full`).

Add these new imports at the top of renderer.py (after existing imports):

```python
import asyncio
from jinja2 import Environment, FileSystemLoader
from .config import (
    TEMPLATES_DIR,
    SHORT_V2_RENDER_WIDTH, SHORT_V2_RENDER_HEIGHT,
)
```

Add these new functions replacing the old `_render_short`:

```python
def _is_v2_format(sections: list[dict]) -> bool:
    """Detect whether sections use v2 format (headline/body/tts_text) or legacy (text)."""
    if not sections:
        return False
    first = sections[0]
    return "headline" in first and "tts_text" in first


def _build_template_context(
    section: dict,
    idx: int,
    total: int,
    ticker: str,
    date: str,
) -> dict:
    """Build Jinja2 template context from a v2 section."""
    progress_pct = round(((idx + 1) / total) * 100)
    ctx = {
        "headline": section.get("headline", ""),
        "body": section.get("body", ""),
        "highlights": section.get("highlights", []),
        "ticker": ticker,
        "date": date,
        "progress_pct": progress_pct,
        "index": section.get("index", idx),
    }
    # Rating class
    if section.get("type") == "rating":
        h = section.get("headline", "")
        if "卖出" in h or "减持" in h:
            ctx["rating_class"] = "sell"
        elif "买入" in h or "增持" in h:
            ctx["rating_class"] = "buy"
        else:
            ctx["rating_class"] = "hold"
    # Progress indicator unicode numbers
    circled = "❶❷❸❹❺❻❼❽❾"
    ctx["progress_icon"] = circled[min(idx, len(circled) - 1)]
    return ctx


def _render_short(sections: list[dict], out: Path) -> dict:
    """Render short slides — v2 (HTML/Playwright) or legacy (Pillow) based on format."""
    if _is_v2_format(sections):
        return asyncio.run(_render_short_v2(sections, out))
    else:
        return _render_short_legacy(sections, out)


async def _render_short_v2(sections: list[dict], out: Path) -> dict:
    """Render short slides using HTML templates + Playwright screenshots."""
    from playwright.async_api import async_playwright

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    image_paths: list[str] = []

    # Extract ticker/date from title section or fallback
    ticker = "STOCK"
    date = ""
    for s in sections:
        if s.get("type") == "title":
            headline = s.get("headline", "")
            # Try to find ticker in headline (e.g. "蔚来汽车 NIO" -> "NIO")
            parts = headline.split()
            for p in parts:
                if p.isascii() and p.isalpha():
                    ticker = p
                    break
            break
    for s in sections:
        body = s.get("body", "")
        # Try date pattern like 2026年4月4日 or 2026-04-04
        import re
        m = re.search(r"(\d{4}[-年/]\d{1,2}[-月/]\d{1,2})", body)
        if m:
            date = m.group(1)
            break

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page(
            viewport={"width": SHORT_V2_RENDER_WIDTH, "height": SHORT_V2_RENDER_HEIGHT},
        )

        for idx, section in enumerate(sections):
            section_type = section.get("type", "point")
            template_name = f"{section_type}.html"
            try:
                template = env.get_template(template_name)
            except Exception:
                template = env.get_template("point.html")

            ctx = _build_template_context(section, idx, len(sections), ticker, date)
            html = template.render(**ctx)

            # Navigate to the HTML — use file:// to load base.css relative path
            html_path = out / f"_temp_{idx}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)

            await page.goto(f"file:///{html_path.resolve().as_posix()}")
            await page.wait_for_load_state("networkidle")

            slide_path = out / f"slide_{idx:02d}.png"
            await page.screenshot(path=str(slide_path))
            image_paths.append(str(slide_path))

            # Clean up temp HTML
            html_path.unlink(missing_ok=True)

        await browser.close()

    return {"image_paths": image_paths}


def _render_short_legacy(sections: list[dict], out: Path) -> dict:
    """Legacy Pillow renderer for backward compatibility with old section format."""
    image_paths: list[str] = []
    font_big = _load_font(bold=True, size=28)
    font_body = _load_font(bold=False, size=21)
    font_label = _load_font(bold=False, size=FONT_SIZE_SMALL)

    for idx, section in enumerate(sections):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)
        text = section.get("text", "")
        section_type = section.get("type", "paragraph")
        usable_width = WIDTH - 2 * MARGIN_X

        if section_type == "rating_card":
            color = RATING_SELL_COLOR if "卖出" in text or "减持" in text else (
                RATING_BUY_COLOR if "买入" in text or "增持" in text else HEADING_COLOR
            )
            label_text = "最终评级"
            lbbox = draw.textbbox((0, 0), label_text, font=font_label)
            lw = lbbox[2] - lbbox[0]
            draw.text(((WIDTH - lw) // 2, HEIGHT // 2 - 80), label_text, font=font_label, fill=ACCENT_COLOR)
            bbox = draw.textbbox((0, 0), text, font=font_big)
            tw = bbox[2] - bbox[0]
            draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 30), text, font=font_big, fill=color)
        else:
            wrapped = _wrap_text(draw, text, font_body, usable_width)
            line_h = int(font_body.size * LINE_HEIGHT_MULTIPLIER)
            total_text_h = len(wrapped) * line_h
            start_y = (HEIGHT - total_text_h) // 2
            for li, line in enumerate(wrapped):
                bbox = draw.textbbox((0, 0), line, font=font_body)
                lw = bbox[2] - bbox[0]
                draw.text(((WIDTH - lw) // 2, start_y + li * line_h), line, font=font_body, fill=TEXT_COLOR)

        dot_y = HEIGHT - 80
        total_dots = len(sections)
        dot_spacing = 16
        dots_width = total_dots * dot_spacing
        dot_start_x = (WIDTH - dots_width) // 2
        for di in range(total_dots):
            cx = dot_start_x + di * dot_spacing + 4
            fill = ACCENT_COLOR if di <= idx else (50, 55, 80)
            draw.ellipse([(cx, dot_y), (cx + 8, dot_y + 8)], fill=fill)

        path = out / f"slide_{idx:02d}.png"
        img.save(str(path), "PNG")
        image_paths.append(str(path))

    return {"image_paths": image_paths}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd plugins/gv && python -m pytest python/tests/test_renderer.py -v
```

Expected: All tests PASS.

- [ ] **Step 6: Commit**

```bash
git add plugins/gv/python/renderer.py plugins/gv/python/tests/
git commit -m "feat(gv): rewrite short renderer with HTML/Playwright, keep legacy fallback"
```

---

## Task 4: Rewrite Composer — FFmpeg Direct Calls

**Files:**
- Modify: `plugins/gv/python/composer.py`
- Create: `plugins/gv/python/tests/test_composer.py`

- [ ] **Step 1: Write tests for FFmpeg command building**

Create `plugins/gv/python/tests/test_composer.py`:

```python
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
        # Static: no zoompan, just scale
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
        # Single segment: just copy
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
        # First section should be roughly 1.1s, second roughly 1.1s
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugins/gv && python -m pytest python/tests/test_composer.py -v
```

Expected: FAIL — functions not defined yet.

- [ ] **Step 3: Add v2 composer functions to composer.py**

Add these imports at the top of `plugins/gv/python/composer.py` (after existing imports):

```python
import subprocess
from .config import (
    FFMPEG_PATH,
    SHORT_V2_OUTPUT_WIDTH, SHORT_V2_OUTPUT_HEIGHT,
    SHORT_V2_TRANSITIONS, SHORT_V2_KENBURNS,
)
```

Then replace the existing `_compose_short` function with the following functions. Keep `compose_video` and `_compose_full` unchanged:

```python
def _compose_short(
    frames_dir: str,
    audio: AudioFileClip,
    timestamps: list[dict],
    duration: float,
) -> CompositeVideoClip:
    """Compose short video — v2 (FFmpeg) if oversized frames detected, else legacy."""
    frames_path = Path(frames_dir)
    slides = sorted(frames_path.glob("slide_*.png"))

    if not slides:
        bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR).with_duration(duration)
        return bg.with_audio(audio)

    # Detect v2 by checking image dimensions (v2 renders at 1134x2016)
    from PIL import Image as PILImage
    first_img = PILImage.open(str(slides[0]))
    is_v2 = first_img.width == SHORT_V2_OUTPUT_WIDTH * 1.05 or first_img.width > WIDTH

    if is_v2:
        # Read the sections JSON to get tts_text for duration calc
        sections_json = frames_path / "_sections.json"
        sections = []
        if sections_json.exists():
            with open(sections_json, "r", encoding="utf-8") as f:
                sections = json.load(f)

        output_path = str(frames_path / "_v2_composed.mp4")
        _compose_short_v2(
            slide_paths=[str(s) for s in slides],
            sections=sections,
            timestamps=timestamps,
            audio_path=str(frames_path.parent / "audio.mp3"),  # will be overridden by caller
            total_duration=duration,
            output_path=output_path,
        )
        # Load the FFmpeg output as a MoviePy clip so the caller can write_videofile
        from moviepy import VideoFileClip
        return VideoFileClip(output_path)
    else:
        return _compose_short_legacy(slides, audio, duration)


def _compose_short_legacy(
    slides: list[Path],
    audio: AudioFileClip,
    duration: float,
) -> CompositeVideoClip:
    """Legacy MoviePy composition for old-format slides."""
    num_slides = len(slides)
    slide_duration = duration / num_slides
    fade = SHORT_TRANSITION_DURATION

    clips = []
    for slide_path in slides:
        clip = ImageClip(str(slide_path)).with_duration(slide_duration)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose", padding=-fade)
    video = video.with_audio(audio)
    return video


def _calc_slide_durations(
    sections: list[dict],
    timestamps: list[dict],
    total_duration: float,
) -> list[float]:
    """Calculate per-slide durations based on TTS timestamps.

    Matches each section's tts_text to timestamp boundaries.
    Falls back to equal split if matching fails.
    """
    n = len(sections)
    if n == 0:
        return []
    if not timestamps or not sections[0].get("tts_text"):
        return [total_duration / n] * n

    # Build cumulative character count for each section's tts_text
    tts_texts = [s.get("tts_text", "") for s in sections]
    cum_chars = []
    total_chars = 0
    for t in tts_texts:
        total_chars += len(t)
        cum_chars.append(total_chars)

    if total_chars == 0:
        return [total_duration / n] * n

    # Proportional split by character count
    durations = []
    for i, t in enumerate(tts_texts):
        proportion = len(t) / total_chars
        durations.append(proportion * total_duration)

    # Ensure minimum 2 seconds per slide
    for i in range(len(durations)):
        if durations[i] < 2.0:
            durations[i] = 2.0

    # Re-normalize to total_duration
    s = sum(durations)
    if s > 0:
        durations = [d * total_duration / s for d in durations]

    return durations


def _build_zoompan_cmd(
    input_path: str,
    output_path: str,
    duration: float,
    start_zoom: float,
    end_zoom: float,
    fps: int,
    out_w: int,
    out_h: int,
) -> list[str]:
    """Build FFmpeg command for Ken Burns zoompan on a single slide."""
    total_frames = int(duration * fps)
    if total_frames < 1:
        total_frames = 1

    if abs(start_zoom - end_zoom) < 0.001:
        # Static — just scale to output size and create a video segment
        return [
            FFMPEG_PATH, "-y",
            "-loop", "1", "-i", input_path,
            "-t", f"{duration:.3f}",
            "-vf", f"scale={out_w}:{out_h}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", str(fps),
            output_path,
        ]

    # Zoompan: interpolate zoom from start to end
    # z = start_zoom + (end_zoom - start_zoom) * (on / total_frames)
    zoom_expr = f"{start_zoom}+{end_zoom - start_zoom}*on/{total_frames}"
    return [
        FFMPEG_PATH, "-y",
        "-i", input_path,
        "-vf", (
            f"zoompan=z='{zoom_expr}'"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={total_frames}:s={out_w}x{out_h}:fps={fps}"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        output_path,
    ]


def _build_xfade_cmd(
    segment_paths: list[str],
    segment_durations: list[float],
    transitions: list[dict],
    output_path: str,
) -> list[str]:
    """Build FFmpeg command to concatenate segments with xfade transitions."""
    n = len(segment_paths)
    if n == 0:
        return [FFMPEG_PATH, "-y", "-f", "lavfi", "-i", "color=black:s=1080x1920:d=1", output_path]

    if n == 1:
        # Single segment — just copy
        return [FFMPEG_PATH, "-y", "-i", segment_paths[0], "-c", "copy", output_path]

    # Build complex filter with chained xfade
    inputs = []
    for p in segment_paths:
        inputs.extend(["-i", p])

    filter_parts = []
    # First xfade: [0][1] -> [v01]
    offset = segment_durations[0] - transitions[1]["duration"]
    t_name = transitions[1]["transition"]
    t_dur = transitions[1]["duration"]
    filter_parts.append(
        f"[0:v][1:v]xfade=transition={t_name}:duration={t_dur:.2f}:offset={offset:.3f}[v01]"
    )

    prev_label = "v01"
    cum_duration = segment_durations[0] + segment_durations[1] - t_dur

    for i in range(2, n):
        t_idx = min(i, len(transitions) - 1)
        t_name = transitions[t_idx]["transition"]
        t_dur = transitions[t_idx]["duration"]
        offset = cum_duration - t_dur
        next_label = f"v{prev_label[1:]}{i}"
        filter_parts.append(
            f"[{prev_label}][{i}:v]xfade=transition={t_name}:duration={t_dur:.2f}:offset={offset:.3f}[{next_label}]"
        )
        prev_label = next_label
        cum_duration += segment_durations[i] - t_dur

    filter_complex = ";".join(filter_parts)

    return [
        FFMPEG_PATH, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev_label}]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        output_path,
    ]


def _build_ass_subtitles(
    timestamps: list[dict],
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Generate ASS subtitle content with word-level highlighting."""

    def ms_to_ass_time(ms: int) -> str:
        h = ms // 3600000
        m = (ms % 3600000) // 60000
        s = (ms % 60000) // 1000
        cs = (ms % 1000) // 10
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    header = f"""[Script Info]
Title: Gen-Video Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,42,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,3,0,2,40,40,{height // 4},1
Style: Highlight,Noto Sans CJK SC,42,&H0000D4FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,0,2,40,40,{height // 4},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    for ts in timestamps:
        start_ms = ts["offset_ms"]
        end_ms = start_ms + ts["duration_ms"]
        text = ts["text"].strip()
        if not text or text in ("，", "。", "、", "；", "："):
            continue
        start_t = ms_to_ass_time(start_ms)
        end_t = ms_to_ass_time(end_ms)
        events.append(f"Dialogue: 0,{start_t},{end_t},Highlight,,0,0,0,,{text}")

    return header + "\n".join(events) + "\n"


def _compose_short_v2(
    slide_paths: list[str],
    sections: list[dict],
    timestamps: list[dict],
    audio_path: str,
    total_duration: float,
    output_path: str,
) -> None:
    """Compose short video using FFmpeg: zoompan + xfade + ASS subtitles + audio."""
    out = Path(output_path)
    tmp_dir = out.parent
    n = len(slide_paths)
    out_w = SHORT_V2_OUTPUT_WIDTH
    out_h = SHORT_V2_OUTPUT_HEIGHT

    # 1. Calculate per-slide durations
    durations = _calc_slide_durations(sections, timestamps, total_duration)

    # 2. Build transitions list
    transitions = []
    for i, section in enumerate(sections if sections else [{}] * n):
        stype = section.get("type", "point")
        t = SHORT_V2_TRANSITIONS.get(stype, SHORT_V2_TRANSITIONS["point"])
        transitions.append(t)
    # Pad if sections shorter than slides
    while len(transitions) < n:
        transitions.append(SHORT_V2_TRANSITIONS["point"])

    # 3. Generate zoompan segments
    segment_paths: list[str] = []
    for i, slide_path in enumerate(slide_paths):
        stype = sections[i].get("type", "point") if i < len(sections) else "point"
        sz, ez = SHORT_V2_KENBURNS.get(stype, (1.0, 1.03))
        seg_path = str(tmp_dir / f"_seg_{i:02d}.mp4")
        cmd = _build_zoompan_cmd(slide_path, seg_path, durations[i], sz, ez, FPS, out_w, out_h)
        subprocess.run(cmd, check=True, capture_output=True)
        segment_paths.append(seg_path)

    # 4. Merge segments with xfade
    merged_path = str(tmp_dir / "_merged.mp4")
    cmd = _build_xfade_cmd(segment_paths, durations, transitions, merged_path)
    subprocess.run(cmd, check=True, capture_output=True)

    # 5. Generate ASS subtitles
    ass_path = str(tmp_dir / "_subtitles.ass")
    ass_content = _build_ass_subtitles(timestamps, out_w, out_h)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # 6. Overlay subtitles + add audio
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", merged_path,
        "-i", audio_path,
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # 7. Cleanup temp files
    for seg in segment_paths:
        Path(seg).unlink(missing_ok=True)
    Path(merged_path).unlink(missing_ok=True)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd plugins/gv && python -m pytest python/tests/test_composer.py -v
```

Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/gv/python/composer.py plugins/gv/python/tests/test_composer.py
git commit -m "feat(gv): rewrite short composer with FFmpeg zoompan+xfade+ASS"
```

---

## Task 5: Update Renderer-Composer Integration

**Files:**
- Modify: `plugins/gv/python/renderer.py` (save sections alongside frames)
- Modify: `plugins/gv/python/composer.py` (read sections from frames dir)

The composer needs access to the sections JSON for duration calculation. The renderer should save it alongside the frames.

- [ ] **Step 1: Add sections saving to `_render_short_v2`**

In `plugins/gv/python/renderer.py`, add the following at the end of `_render_short_v2`, just before `return {"image_paths": image_paths}`:

```python
        # Save sections JSON alongside frames for composer to read
        sections_json_path = out / "_sections.json"
        with open(sections_json_path, "w", encoding="utf-8") as f:
            json.dump(sections, f, ensure_ascii=False)
```

- [ ] **Step 2: Update `_compose_short` to pass audio_path correctly**

In `plugins/gv/python/composer.py`, update the `_compose_short` function's v2 branch. Replace the `audio_path` line in the `_compose_short_v2` call:

Change:
```python
            audio_path=str(frames_path.parent / "audio.mp3"),  # will be overridden by caller
```

To find the actual audio path from the `compose_video` caller. The simplest approach is to update the `compose_video` function signature. In `compose_video`, pass the audio path down:

In `compose_video`, change the call from:
```python
    if layout == "full":
        video = _compose_full(frames_dir, audio, timestamps, duration)
    else:
        video = _compose_short(frames_dir, audio, timestamps, duration)
```

To:
```python
    if layout == "full":
        video = _compose_full(frames_dir, audio, timestamps, duration)
    else:
        video = _compose_short(frames_dir, audio, timestamps, duration, audio_path)
```

And update `_compose_short` signature:
```python
def _compose_short(
    frames_dir: str,
    audio: AudioFileClip,
    timestamps: list[dict],
    duration: float,
    audio_file_path: str = "",
) -> CompositeVideoClip:
```

And pass it to `_compose_short_v2`:
```python
        _compose_short_v2(
            slide_paths=[str(s) for s in slides],
            sections=sections,
            timestamps=timestamps,
            audio_path=audio_file_path,
            total_duration=duration,
            output_path=output_path,
        )
```

- [ ] **Step 3: Commit**

```bash
git add plugins/gv/python/renderer.py plugins/gv/python/composer.py
git commit -m "fix(gv): wire sections JSON and audio path between renderer and composer"
```

---

## Task 6: Update __main__.py for Playwright Lifecycle

**Files:**
- Modify: `plugins/gv/python/__main__.py`

- [ ] **Step 1: No changes needed to __main__.py**

Playwright is launched and closed within `_render_short_v2` using `async with`, so no global lifecycle management is needed. The `asyncio.run()` call is already handled inside `_render_short` which is called by `render_frames`.

Verify the existing CLI still works:

```bash
cd plugins/gv && python -m python render --sections ../test_sections.json --layout short --output-dir ../test_output
```

(This will fail without a real sections file, but confirms the module loads.)

- [ ] **Step 2: Quick smoke test — verify module imports**

```bash
cd plugins/gv && python -c "from python.renderer import render_frames; from python.composer import compose_video; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 3: Commit (only if changes were needed)**

If no changes: skip this commit.

---

## Task 7: Upgrade Video-Scriptwriter Agent

**Files:**
- Modify: `agents/video-scriptwriter.md`

- [ ] **Step 1: Rewrite the agent prompt**

Replace the entire content of `agents/video-scriptwriter.md` with:

```markdown
---
name: video-scriptwriter
description: |
  Create a 60-90 second narration script from a Chinese trading analysis report for TikTok-style short video. Produces structured JSON with headline/body/highlights/tts_text per slide.
---

You are a **Short-Video Script Creator** specializing in financial content for 抖音/TikTok.

## Your Task

Given a full Chinese trading analysis report, create a punchy, attention-grabbing narration script for a 60-90 second vertical video. You are NOT just extracting text — you are **rewriting** it for maximum impact.

## Output Format

Return a JSON array. Each element is one video slide:

```json
[
  {
    "type": "title",
    "headline": "蔚来汽车 NIO",
    "body": "AI交易分析报告 · 2026年4月4日",
    "tts_text": "蔚来汽车交易分析报告，2026年4月4日。"
  },
  {
    "type": "disclaimer",
    "headline": "免责声明",
    "body": "本报告由AI生成，仅供研究参考，不构成投资建议。",
    "tts_text": "免责声明：本报告由AI生成，仅供研究参考。"
  },
  {
    "type": "rating",
    "headline": "卖出",
    "body": "目标价 $4.80-$5.20，下行 17-24%",
    "highlights": ["$4.80-$5.20", "-17%~-24%"],
    "tts_text": "最终评级：卖出。目标价4.80到5.20美元，下行空间17到24个百分点。"
  },
  {
    "type": "point",
    "index": 1,
    "headline": "风险收益比极差",
    "body": "乐观上行仅3.7%，悲观下行-37%，不值得博",
    "highlights": ["+3.7%", "-37%"],
    "tts_text": "风险收益比极差。乐观情况下上行仅百分之三点七，悲观下行高达百分之三十七。"
  },
  {
    "type": "point",
    "index": 2,
    "headline": "盈利真实性存疑",
    "body": "首次GAAP盈利无法验证，可能含一次性项目",
    "highlights": ["GAAP"],
    "tts_text": "首次GAAP盈利无法验证，可能包含一次性项目，不应过度解读。"
  },
  {
    "type": "point",
    "index": 3,
    "headline": "研发砍了三分之一",
    "body": "竞争对手纷纷加大投入，NIO却选择削减，以未来换短期",
    "highlights": ["-34%"],
    "tts_text": "研发支出削减百分之三十四，竞争对手纷纷加大研发投入，蔚来却选择了削减。"
  },
  {
    "type": "conclusion",
    "headline": "趁强势卖出",
    "body": "等回调至$5区间重新评估",
    "highlights": ["$5"],
    "tts_text": "结论：趁强势卖出，等回调至5美元区间再重新评估。"
  }
]
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `type` | Yes | One of: `title`, `disclaimer`, `rating`, `point`, `conclusion` |
| `headline` | Yes | Punchy short text displayed prominently on the slide (max 15 chars) |
| `body` | Yes | Supporting text displayed below the headline (1-2 sentences) |
| `tts_text` | Yes | Narration text optimized for voice reading — no symbols, no abbreviations, numbers spelled conversationally |
| `highlights` | No | Array of 1-2 key numbers/percentages to visually emphasize (e.g. `["-34%", "$5.20"]`) |
| `index` | No | For `point` type only — sequential number (1, 2, 3) |

## Creative Rules

1. **Headlines are NOT titles — they are hooks.** Don't write "研发支出分析", write "研发砍了三分之一". Use questions, contrasts, or provocative statements.
2. **Body is conversational.** Rewrite formal report language into how a smart friend would explain it. Keep data, lose jargon.
3. **tts_text is for ears.** Write it to sound natural when read aloud. Use "百分之三十四" not "34%". Avoid parentheses, dashes, special symbols.
4. **highlights are for eyes.** Pick the 1-2 most impactful numbers that would make someone stop scrolling.
5. **Total tts_text: 250-400 Chinese characters** (reads in ~60-90 seconds at normal pace)
6. **Structure: 7 sections exactly** — title → disclaimer → rating → point ×3 → conclusion
7. **Keep specific numbers** for credibility — never round "$4.82" to "about $5"
8. **No tables, no markdown, no code fences** — raw JSON only

## Output

Raw JSON array only. No markdown formatting, no explanation, no code fences.
```

- [ ] **Step 2: Commit**

```bash
git add agents/video-scriptwriter.md
git commit -m "feat(gv): upgrade scriptwriter to structured headline/body/highlights format"
```

---

## Task 8: End-to-End Integration Test

**Files:** None new — uses existing pipeline

- [ ] **Step 1: Create a test sections JSON with v2 format**

```bash
cd plugins/gv
python -c "
import json
sections = [
    {'type': 'title', 'headline': '蔚来汽车 NIO', 'body': 'AI交易分析报告 · 2026年4月4日', 'tts_text': '蔚来汽车交易分析报告，2026年4月4日。'},
    {'type': 'disclaimer', 'headline': '免责声明', 'body': '本报告由AI生成，仅供研究参考。', 'tts_text': '免责声明：本报告由AI生成，仅供研究参考。'},
    {'type': 'rating', 'headline': '卖出', 'body': '目标价 \$4.80-\$5.20', 'highlights': ['\$4.80-\$5.20', '-17%'], 'tts_text': '最终评级：卖出。目标价4.80到5.20美元。'},
    {'type': 'point', 'index': 1, 'headline': '风险收益比极差', 'body': '乐观上行仅3.7%，悲观下行-37%', 'highlights': ['+3.7%', '-37%'], 'tts_text': '风险收益比极差。乐观上行仅百分之三点七。'},
    {'type': 'point', 'index': 2, 'headline': '盈利真实性存疑', 'body': '首次GAAP盈利无法验证', 'highlights': ['GAAP'], 'tts_text': '首次GAAP盈利无法验证。'},
    {'type': 'point', 'index': 3, 'headline': '研发砍了三分之一', 'body': '竞争对手纷纷加大投入', 'highlights': ['-34%'], 'tts_text': '研发支出削减百分之三十四。'},
    {'type': 'conclusion', 'headline': '趁强势卖出', 'body': '等回调至\$5区间重评', 'highlights': ['\$5'], 'tts_text': '结论：趁强势卖出。'}
]
with open('../../gen-video/temp/_test_v2_sections.json', 'w', encoding='utf-8') as f:
    json.dump(sections, f, ensure_ascii=False, indent=2)
print('Written test sections')
"
```

- [ ] **Step 2: Test render step (Playwright)**

```bash
cd plugins/gv && python -m python render --sections ../../gen-video/temp/_test_v2_sections.json --layout short --output-dir ../../gen-video/temp/_test_v2_frames
```

Expected: Creates 7 PNG files at 1134×2016 pixels in `gen-video/temp/_test_v2_frames/`.

- [ ] **Step 3: Visually inspect the rendered slides**

Open the PNG files and verify:
- title slide has gradient background, large centered text, brand bar
- disclaimer has reduced opacity
- rating has large colored rating text, highlight chips
- point slides have numbered index, card, highlights
- conclusion has decorative lines

- [ ] **Step 4: Test TTS step**

```bash
cd plugins/gv && python -m python tts --text "蔚来汽车交易分析报告，2026年4月4日。免责声明：本报告由AI生成。最终评级：卖出。风险收益比极差。首次GAAP盈利无法验证。研发支出削减百分之三十四。结论：趁强势卖出。" --output-dir ../../gen-video/temp/_test_v2_tts --rate "+5%"
```

Expected: Creates `audio.mp3`, `timestamps.json`, `subtitles.srt`.

- [ ] **Step 5: Test compose step (FFmpeg)**

```bash
cd plugins/gv && python -m python compose --frames-dir ../../gen-video/temp/_test_v2_frames --audio ../../gen-video/temp/_test_v2_tts/audio.mp3 --timestamps ../../gen-video/temp/_test_v2_tts/timestamps.json --layout short --output ../../gen-video/output/_test_v2.mp4
```

Expected: Creates `_test_v2.mp4` with zoompan transitions, xfade effects, and ASS subtitles.

- [ ] **Step 6: Play the video and verify quality**

Watch the video. Check:
- Slides have Ken Burns zoom effect (subtle)
- Transitions between slides use xfade (not simple cut)
- Subtitles appear synchronized with audio
- Total duration matches audio duration
- Video is 1080×1920

- [ ] **Step 7: Test backward compatibility — legacy format**

```bash
cd plugins/gv && python -c "
import json
legacy = [
    {'type': 'title', 'level': 1, 'text': '蔚来汽车 NIO', 'raw': '# 蔚来汽车 NIO'},
    {'type': 'paragraph', 'level': 0, 'text': '免责声明：本报告由AI生成。', 'raw': '> 免责声明'},
    {'type': 'rating_card', 'level': 1, 'text': '卖出', 'raw': '# **卖出**'},
]
with open('../../gen-video/temp/_test_legacy_sections.json', 'w', encoding='utf-8') as f:
    json.dump(legacy, f, ensure_ascii=False)
print('Written legacy sections')
"
python -m python render --sections ../../gen-video/temp/_test_legacy_sections.json --layout short --output-dir ../../gen-video/temp/_test_legacy_frames
```

Expected: Creates 3 PNG files at 720×1280 (old size) using Pillow legacy renderer.

- [ ] **Step 8: Commit test artifacts cleanup**

```bash
rm -rf gen-video/temp/_test_*
rm -f gen-video/output/_test_*
```

No git commit needed — these are ephemeral test files.

---

## Task 9: Update gen-video Skill for New Scriptwriter Format

**Files:**
- Modify: `skills/gen-video/skill.md`

- [ ] **Step 1: Update Step 4 in the skill to match new scriptwriter output**

In `skills/gen-video/skill.md`, update the short version step to note the new output format. Change the line:

```
1. Dispatch **video-scriptwriter** agent with the full report text to extract a 60-90 second narration script (250-400 characters, 7-9 sections: title → disclaimer → rating → 3 key points → conclusion)
```

To:

```
1. Dispatch **video-scriptwriter** agent with the full report text. The agent returns structured JSON with 7 sections, each having `type`, `headline`, `body`, `tts_text`, and optional `highlights`/`index` fields. Save this JSON to a temp file for the render step.
2. Extract all `tts_text` fields from the scriptwriter output, concatenate them, and pass to `generate_tts` for TTS synthesis.
```

- [ ] **Step 2: Commit**

```bash
git add skills/gen-video/skill.md
git commit -m "docs(gv): update gen-video skill for v2 scriptwriter format"
```

---

## Task 10: Run All Tests & Final Verification

- [ ] **Step 1: Run unit tests**

```bash
cd plugins/gv && python -m pytest python/tests/ -v
```

Expected: All tests pass.

- [ ] **Step 2: Run full pipeline with real report**

Use the skill orchestration manually — parse a real report, dispatch scriptwriter, render, compose:

```bash
cd plugins/gv && python -m python parse ../../analysis/NIO_2026-04-04_zh.md
```

Verify parse output has `key_sections`. Then use the MCP pipeline (via Claude) to generate the full short video.

- [ ] **Step 3: Final commit — version bump**

```bash
git add -A
git commit -m "feat(gv): short video v2 — HTML/CSS + FFmpeg + enhanced scriptwriter

Complete upgrade of gen-video short version:
- HTML/CSS slide templates with Jinja2 + Playwright rendering
- FFmpeg zoompan (Ken Burns) + xfade transitions
- ASS word-level subtitle overlay
- Scriptwriter outputs structured headline/body/highlights/tts_text
- Backward compatible with legacy section format"
```
