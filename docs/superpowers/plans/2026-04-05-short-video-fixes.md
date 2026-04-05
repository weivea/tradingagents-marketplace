# Short Video V2 Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 issues in the gen-video short v2 pipeline: ASS subtitle wrapping, audio truncation from xfade overlap, and sparse slide content.

**Architecture:** Three independent fixes touching `composer.py` (subtitles + duration), HTML templates + CSS (content), `renderer.py` (context passing), and `video-scriptwriter.md` (output format). Each fix can be tested independently.

**Tech Stack:** Python, FFmpeg ASS subtitles, Jinja2/HTML/CSS, edge-tts

---

## File Map

| File | Change | Task |
|------|--------|------|
| `plugins/gv/python/composer.py` | Fix subtitle wrapping + duration compensation | 1, 2 |
| `plugins/gv/python/tests/test_composer.py` | Add tests for wrapping + duration | 1, 2 |
| `plugins/gv/python/templates/base.css` | Add sub-body + metrics-grid styles | 3 |
| `plugins/gv/python/templates/point.html` | Add sub_body + metrics sections | 3 |
| `plugins/gv/python/templates/rating.html` | Add sub_body + metrics sections | 3 |
| `plugins/gv/python/templates/conclusion.html` | Add sub_body section | 3 |
| `plugins/gv/python/renderer.py` | Pass sub_body + metrics to templates | 3 |
| `plugins/gv/python/tests/test_renderer.py` | Test new context fields | 3 |
| `agents/video-scriptwriter.md` | Add sub_body + metrics to output format | 4 |

---

## Task 1: Fix ASS Subtitle Wrapping for Chinese Text

**Files:**
- Modify: `plugins/gv/python/composer.py` — `_build_ass_subtitles()`
- Modify: `plugins/gv/python/tests/test_composer.py` — add wrapping tests

- [ ] **Step 1: Write test for subtitle text wrapping**

In `plugins/gv/python/tests/test_composer.py`, add a new test class at the end of the file:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/test_composer.py::TestWrapAssText -v
```

Expected: FAIL — `_wrap_ass_text` does not exist.

- [ ] **Step 3: Implement `_wrap_ass_text` and update `_build_ass_subtitles`**

In `plugins/gv/python/composer.py`, add the `_wrap_ass_text` function just before `_build_ass_subtitles`:

```python
def _wrap_ass_text(text: str, max_chars: int = 20) -> str:
    """Wrap Chinese text for ASS subtitles using \\N line breaks.

    Breaks at Chinese punctuation when possible, otherwise at max_chars.
    """
    breakable = set("，。；：！？、")
    result = []
    current_line = ""

    for char in text:
        current_line += char
        if len(current_line) >= max_chars:
            result.append(current_line)
            current_line = ""
        elif char in breakable and len(current_line) >= 8:
            result.append(current_line)
            current_line = ""

    if current_line:
        result.append(current_line)

    return "\\N".join(result)
```

Then update `_build_ass_subtitles` — change the event-building loop. Replace:

```python
    events = []
    for ts in timestamps:
        start_ms = ts["offset_ms"]
        end_ms = start_ms + ts["duration_ms"]
        text = ts["text"].strip()
        if not text or text in ("，", "。", "、", "；", "：", "！", "？", "…"):
            continue
        start_t = ms_to_ass_time(start_ms)
        end_t = ms_to_ass_time(end_ms)
        events.append(f"Dialogue: 0,{start_t},{end_t},Highlight,,0,0,0,,{text}")
```

With:

```python
    events = []
    for ts in timestamps:
        start_ms = ts["offset_ms"]
        end_ms = start_ms + ts["duration_ms"]
        text = ts["text"].strip()
        if not text or text in ("，", "。", "、", "；", "：", "！", "？", "…"):
            continue
        wrapped = _wrap_ass_text(text, max_chars=20)
        start_t = ms_to_ass_time(start_ms)
        end_t = ms_to_ass_time(end_ms)
        events.append(f"Dialogue: 0,{start_t},{end_t},Highlight,,0,0,0,,{wrapped}")
```

Also change `WrapStyle: 0` to `WrapStyle: 2` in the header string (the line inside the f-string `header`).

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/test_composer.py -v
```

Expected: All tests PASS (including existing tests + 4 new wrapping tests).

- [ ] **Step 5: Commit**

```bash
git add plugins/gv/python/composer.py plugins/gv/python/tests/test_composer.py
git commit -m "fix(gv): wrap Chinese text in ASS subtitles to prevent overflow"
```

---

## Task 2: Fix Audio Truncation from Xfade Overlap

**Files:**
- Modify: `plugins/gv/python/composer.py` — `_calc_slide_durations()` and `_compose_short_v2()`
- Modify: `plugins/gv/python/tests/test_composer.py` — add duration compensation test

- [ ] **Step 1: Write test for xfade-compensated duration calculation**

In `plugins/gv/python/tests/test_composer.py`, add to the existing `TestCalcSlideDurations` class:

```python
    def test_xfade_compensation(self):
        from python.composer import _calc_slide_durations
        sections = [
            {"tts_text": "你好世界。"},
            {"tts_text": "这是测试。"},
            {"tts_text": "再见世界。"},
        ]
        timestamps = [{"text": "x", "offset_ms": 0, "duration_ms": 100}]
        total_duration = 30.0
        # 2 transitions × 0.5s each = 1.0s overlap
        durations = _calc_slide_durations(sections, timestamps, total_duration, xfade_overlap=1.0)
        # Each slide should be longer than 10.0 to compensate for overlap
        assert sum(durations) > total_duration
        assert abs(sum(durations) - (total_duration + 1.0)) < 0.1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/test_composer.py::TestCalcSlideDurations::test_xfade_compensation -v
```

Expected: FAIL — `_calc_slide_durations` does not accept `xfade_overlap` parameter.

- [ ] **Step 3: Update `_calc_slide_durations` to accept xfade compensation**

In `plugins/gv/python/composer.py`, change the function signature and re-normalization logic. Replace the entire function:

```python
def _calc_slide_durations(
    sections: list[dict],
    timestamps: list[dict],
    total_duration: float,
    xfade_overlap: float = 0.0,
) -> list[float]:
    """Calculate per-slide durations based on TTS text character count.

    Args:
        xfade_overlap: Total time lost to xfade transitions (sum of all
            transition durations). Slides are made longer to compensate.

    Falls back to equal split if no tts_text available.
    """
    n = len(sections)
    if n == 0:
        return []

    effective_duration = total_duration + xfade_overlap

    if not timestamps or not sections[0].get("tts_text"):
        return [effective_duration / n] * n

    tts_texts = [s.get("tts_text", "") for s in sections]
    total_chars = sum(len(t) for t in tts_texts)

    if total_chars == 0:
        return [effective_duration / n] * n

    # Proportional split by character count
    durations = [len(t) / total_chars * effective_duration for t in tts_texts]

    # Ensure minimum 2 seconds per slide
    for i in range(len(durations)):
        if durations[i] < 2.0:
            durations[i] = 2.0

    # Re-normalize to effective_duration
    s = sum(durations)
    if s > 0:
        durations = [d * effective_duration / s for d in durations]

    return durations
```

- [ ] **Step 4: Update `_compose_short_v2` to compute overlap and remove `-shortest`**

In `plugins/gv/python/composer.py`, in `_compose_short_v2`:

**4a.** After building the transitions list (step 2), compute total overlap and pass to `_calc_slide_durations`. Replace:

```python
    # 1. Calculate per-slide durations
    durations = _calc_slide_durations(sections, timestamps, total_duration)
```

With:

```python
    # 1. Calculate per-slide durations (compensate for xfade overlaps)
    # Must build transitions first to know overlap
```

Then move the transitions-building block (step 2) ABOVE the duration calculation. The new order becomes:

```python
    # 1. Build transitions list (needed to calculate overlap)
    transitions = []
    for i, section in enumerate(sections if sections else [{}] * n):
        stype = section.get("type", "point")
        t = SHORT_V2_TRANSITIONS.get(stype, SHORT_V2_TRANSITIONS["point"])
        transitions.append(t)
    while len(transitions) < n:
        transitions.append(SHORT_V2_TRANSITIONS["point"])

    # 2. Calculate per-slide durations with xfade compensation
    xfade_overlap = sum(transitions[i]["duration"] for i in range(1, n)) if n > 1 else 0.0
    durations = _calc_slide_durations(sections, timestamps, total_duration, xfade_overlap)
```

**4b.** In the final FFmpeg command (step 6), replace `-shortest` with `-t` to match audio duration exactly. Replace:

```python
        "-shortest",
        str(out),
```

With:

```python
        "-t", f"{total_duration:.3f}",
        str(out),
```

- [ ] **Step 5: Run all tests to verify they pass**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/test_composer.py -v
```

Expected: All tests PASS. The existing `test_from_timestamps` and `test_fallback_equal_split` tests still pass because `xfade_overlap` defaults to `0.0`.

- [ ] **Step 6: Commit**

```bash
git add plugins/gv/python/composer.py plugins/gv/python/tests/test_composer.py
git commit -m "fix(gv): compensate xfade overlap in slide durations and remove -shortest"
```

---

## Task 3: Enrich Slide Content — Templates, CSS, Renderer

**Files:**
- Modify: `plugins/gv/python/templates/base.css` — add sub-body + metrics styles
- Modify: `plugins/gv/python/templates/point.html` — add sub_body + metrics
- Modify: `plugins/gv/python/templates/rating.html` — add sub_body + metrics
- Modify: `plugins/gv/python/templates/conclusion.html` — add sub_body
- Modify: `plugins/gv/python/renderer.py` — pass sub_body + metrics to context
- Modify: `plugins/gv/python/tests/test_renderer.py` — test new fields

- [ ] **Step 1: Add CSS styles for sub-body and metrics-grid**

In `plugins/gv/python/templates/base.css`, add the following after the `.label` block (after line 94):

```css
.sub-body {
  font-size: 24px;
  font-weight: 400;
  line-height: 1.7;
  color: var(--text-secondary);
  opacity: 0.8;
  margin-top: 16px;
}

/* --- Metrics grid --- */
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 24px;
}
.metric-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
}
.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}
.metric-value.positive { color: var(--rating-buy); }
.metric-value.negative { color: var(--rating-sell); }
.metric-value.neutral { color: var(--rating-hold); }
.metric-label {
  font-size: 20px;
  color: var(--text-secondary);
  margin-top: 4px;
}
```

Also reduce card padding from `60px 50px` to `40px 40px`. Change line 58:

```css
  padding: 40px 40px;
```

- [ ] **Step 2: Update point.html template**

Replace the full content of `plugins/gv/python/templates/point.html`:

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
      {% if sub_body %}
      <p class="sub-body">{{ sub_body }}</p>
      {% endif %}
      {% if metrics %}
      <div class="metrics-grid">
        {% for m in metrics %}
        <div class="metric-item">
          <div class="metric-value {{ m.signal }}">{{ m.value }}</div>
          <div class="metric-label">{{ m.label }}</div>
        </div>
        {% endfor %}
      </div>
      {% endif %}
    </div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">{{ progress_icon }}</span>
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

- [ ] **Step 3: Update rating.html template**

Replace the full content of `plugins/gv/python/templates/rating.html`:

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
    <div class="card" style="display: inline-block; text-align: center; padding: 40px 80px;">
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
      {% if sub_body %}
      <p class="sub-body" style="text-align: center;">{{ sub_body }}</p>
      {% endif %}
      {% if metrics %}
      <div class="metrics-grid" style="text-align: center;">
        {% for m in metrics %}
        <div class="metric-item">
          <div class="metric-value {{ m.signal }}">{{ m.value }}</div>
          <div class="metric-label">{{ m.label }}</div>
        </div>
        {% endfor %}
      </div>
      {% endif %}
    </div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">{{ progress_icon }}</span>
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

- [ ] **Step 4: Update conclusion.html template**

Replace the full content of `plugins/gv/python/templates/conclusion.html`:

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
    {% if sub_body %}
    <p class="sub-body" style="text-align: center; margin-top: 20px;">{{ sub_body }}</p>
    {% endif %}
    <div class="deco-line-center" style="margin-top: 40px;"></div>
  </div>
  <div class="progress-bar">
    <span class="progress-index">{{ progress_icon }}</span>
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

- [ ] **Step 5: Update `_build_template_context` in renderer.py to pass new fields**

In `plugins/gv/python/renderer.py`, in the `_build_template_context` function, add `sub_body` and `metrics` to the context dict. After the line `"index": section.get("index", idx),` add:

```python
        "sub_body": section.get("sub_body", ""),
        "metrics": section.get("metrics", []),
```

The context dict becomes:

```python
    ctx = {
        "headline": section.get("headline", ""),
        "body": section.get("body", ""),
        "highlights": section.get("highlights", []),
        "ticker": ticker,
        "date": date,
        "progress_pct": progress_pct,
        "index": section.get("index", idx),
        "sub_body": section.get("sub_body", ""),
        "metrics": section.get("metrics", []),
    }
```

- [ ] **Step 6: Add test for new context fields**

In `plugins/gv/python/tests/test_renderer.py`, add to the `TestBuildTemplateContext` class:

```python
    def test_sub_body_and_metrics_passed(self):
        from python.renderer import _build_template_context
        section = {
            "type": "point",
            "index": 1,
            "headline": "Test",
            "body": "Body",
            "tts_text": "Test",
            "sub_body": "补充说明文字",
            "metrics": [{"label": "RSI", "value": "64", "signal": "neutral"}],
        }
        ctx = _build_template_context(section, idx=3, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["sub_body"] == "补充说明文字"
        assert len(ctx["metrics"]) == 1
        assert ctx["metrics"][0]["label"] == "RSI"

    def test_missing_sub_body_defaults_empty(self):
        from python.renderer import _build_template_context
        section = {"type": "point", "index": 1, "headline": "Test", "body": "Body", "tts_text": "Test"}
        ctx = _build_template_context(section, idx=3, total=7, ticker="NIO", date="2026-04-04")
        assert ctx["sub_body"] == ""
        assert ctx["metrics"] == []
```

- [ ] **Step 7: Run all tests**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 8: Commit**

```bash
git add plugins/gv/python/templates/base.css plugins/gv/python/templates/point.html plugins/gv/python/templates/rating.html plugins/gv/python/templates/conclusion.html plugins/gv/python/renderer.py plugins/gv/python/tests/test_renderer.py
git commit -m "feat(gv): add sub_body and metrics grid to slide templates"
```

---

## Task 4: Upgrade Scriptwriter to Output Richer Content

**Files:**
- Modify: `agents/video-scriptwriter.md`

- [ ] **Step 1: Update the scriptwriter agent prompt**

In `agents/video-scriptwriter.md`, make these changes:

**1a.** Update the JSON example in the Output Format section. Replace the `point` example at index 1 (the one with `"headline": "风险收益比极差"`) with:

```json
  {
    "type": "point",
    "index": 1,
    "headline": "风险收益比极差",
    "body": "乐观上行仅3.7%至分析师目标$6.53，悲观下行-17%至-37%",
    "sub_body": "概率加权期望收益约为-5%至-17%。即使按最乐观假设，上行空间也远不足以补偿下行风险。",
    "highlights": ["+3.7%", "-37%"],
    "metrics": [
      {"label": "上行空间", "value": "+3.7%", "signal": "negative"},
      {"label": "下行风险", "value": "-37%", "signal": "negative"},
      {"label": "期望收益", "value": "-11%", "signal": "negative"},
      {"label": "目标价", "value": "$6.53", "signal": "neutral"}
    ],
    "tts_text": "风险收益比极差。乐观情况下上行仅百分之三点七，悲观下行高达百分之三十七。"
  },
```

**1b.** Update the Fields table. Add two new rows:

```
| `sub_body` | No | 2-3 sentences of supporting detail for visual display (60-100 chars). NOT read aloud — display only. |
| `metrics` | No | Array of 2-4 key metrics: `{label, value, signal}` where signal is `"positive"`, `"negative"`, or `"neutral"` |
```

**1c.** Update the `body` field description from `Supporting text displayed below the headline (1-2 sentences)` to `Supporting text displayed below the headline (1-2 sentences, 30-60 chars)`.

**1d.** Update the `highlights` field description from `Array of 1-2 key numbers/percentages` to `Array of 2-4 key numbers/percentages to visually emphasize`.

**1e.** Add a new Creative Rule #9:

```
9. **sub_body fills the card.** Write 2-3 sentences that add context the headline and body don't cover. Think "what would make the viewer pause and read?" This is display-only text, NOT narrated.
10. **metrics are dashboard data.** Pick 2-4 numbers that tell the story at a glance. Each metric has a label (≤6 chars), value (the number), and signal (positive/negative/neutral for color coding).
```

- [ ] **Step 2: Commit**

```bash
git add agents/video-scriptwriter.md
git commit -m "feat(gv): add sub_body and metrics to scriptwriter output format"
```

---

## Task 5: End-to-End Verification

- [ ] **Step 1: Run all unit tests**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: Generate a new short video for NIO to verify all 3 fixes**

Use the gen-video skill pipeline:
1. Dispatch scriptwriter agent (now with `sub_body` + `metrics`)
2. Generate TTS
3. Render frames (check slides visually for richer content)
4. Compose video (check subtitle wrapping + audio not truncated)

- [ ] **Step 3: Verify subtitle wrapping** — subtitles should wrap within video width
- [ ] **Step 4: Verify audio duration** — video should match audio length (±0.5s)
- [ ] **Step 5: Verify slide content** — point/rating slides should show sub_body + metrics grid

- [ ] **Step 6: Clean up temp files**

```bash
cd C:/Users/55028/repo/ta && rm -rf gen-video/temp/NIO_2026-04-04_short* gen-video/output/NIO_2026-04-04_short*
```
