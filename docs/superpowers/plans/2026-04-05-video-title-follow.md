# Video Title Standardization + Follow CTA Slide — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize video opening to "今日交易研报之<公司名>" for both short and full videos, and add a follow/CTA slide at the end of short videos.

**Architecture:** Four files modified: scriptwriter prompt (title format + 8-section structure + follow type), config (transitions/kenburns for follow), new follow.html template, and gen-video skill (full version TTS opening). No changes to renderer.py or composer.py.

**Tech Stack:** Jinja2 HTML templates, Python config, Markdown agent prompts

---

## File Map

| File | Change | Task |
|------|--------|------|
| `agents/video-scriptwriter.md` | Title format → "今日交易研报之<公司名>"；7→8 sections；add follow type | 1 |
| `plugins/gv/python/config.py` | Add `follow` to transitions + kenburns dicts | 2 |
| `plugins/gv/python/templates/follow.html` | New — CTA slide template | 2 |
| `skills/gen-video/skill.md` | Full version TTS opening prefix；short version 7→8 sections note | 3 |

---

## Task 1: Update Scriptwriter — Title Format + Follow Section

**Files:**
- Modify: `agents/video-scriptwriter.md`

- [ ] **Step 1: Update the title slide example in the JSON array**

In `agents/video-scriptwriter.md`, find the title object (lines 19-24):

```json
  {
    "type": "title",
    "headline": "蔚来汽车 NIO",
    "body": "AI交易分析报告 · 2026年4月4日",
    "tts_text": "蔚来汽车交易分析报告，2026年4月4日。"
  },
```

Replace with:

```json
  {
    "type": "title",
    "headline": "今日交易研报之蔚来汽车",
    "body": "2026年4月4日",
    "tts_text": "今日交易研报之蔚来汽车，2026年4月4日。"
  },
```

- [ ] **Step 2: Add the follow slide example at the end of the JSON array**

Find the conclusion object (the last element in the JSON array, lines 69-75):

```json
  {
    "type": "conclusion",
    "headline": "趁强势卖出",
    "body": "等回调至$5区间重新评估",
    "highlights": ["$5"],
    "tts_text": "结论：趁强势卖出，等回调至5美元区间再重新评估。"
  }
]
```

Replace with (add comma after conclusion, add follow object):

```json
  {
    "type": "conclusion",
    "headline": "趁强势卖出",
    "body": "等回调至$5区间重新评估",
    "highlights": ["$5"],
    "tts_text": "结论：趁强势卖出，等回调至5美元区间再重新评估。"
  },
  {
    "type": "follow",
    "headline": "关注我们",
    "body": "获取更详细的分析报告",
    "highlights": ["每日更新", "深度分析", "AI驱动"],
    "tts_text": "感谢收看，关注账号获取每日深度交易分析。"
  }
]
```

- [ ] **Step 3: Add `follow` to the Fields table**

After the `metrics` row in the Fields table, add:

```
| `follow` | — | The final CTA slide type. `headline` is always "关注我们", `highlights` always `["每日更新", "深度分析", "AI驱动"]`. |
```

- [ ] **Step 4: Update the `headline` field description**

Change the `headline` description from:

```
| `headline` | Yes | Punchy short text displayed prominently on the slide (max 15 chars) |
```

To:

```
| `headline` | Yes | Punchy short text displayed prominently on the slide. For title slide: must be "今日交易研报之<公司名>" format. |
```

- [ ] **Step 5: Update structure rule (Creative Rule #6)**

Change rule 6 from:

```
6. **Structure: 7 sections exactly** — title → disclaimer → rating → point ×3 → conclusion
```

To:

```
6. **Structure: 8 sections exactly** — title → disclaimer → rating → point ×3 → conclusion → follow
```

- [ ] **Step 6: Add Creative Rule #11 for title format**

After rule 10, add:

```
11. **Title headline is branded.** Always use "今日交易研报之<公司名>" format. Example: "今日交易研报之蔚来汽车". Do NOT use the ticker symbol in the headline — use the Chinese company name.
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/55028/repo/ta && git add agents/video-scriptwriter.md && git commit -m "feat(gv): standardize title to 今日交易研报 + add follow slide type

Update scriptwriter: title headline uses '今日交易研报之<公司名>' format,
structure changed from 7 to 8 sections with new follow CTA type.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Add Follow Template + Config

**Files:**
- Create: `plugins/gv/python/templates/follow.html`
- Modify: `plugins/gv/python/config.py`

- [ ] **Step 1: Create `follow.html` template**

Create new file `plugins/gv/python/templates/follow.html` with this content:

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
    <p class="label" style="margin-bottom: 20px;">关注我们</p>
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

- [ ] **Step 2: Add `follow` entries to config.py**

In `plugins/gv/python/config.py`, add `follow` to `SHORT_V2_TRANSITIONS`. Find:

```python
    "conclusion": {"transition": "wipeup",     "duration": 0.8},
}
```

Replace with:

```python
    "conclusion": {"transition": "wipeup",     "duration": 0.8},
    "follow":     {"transition": "fade",       "duration": 0.5},
}
```

Then add `follow` to `SHORT_V2_KENBURNS`. Find:

```python
    "conclusion": (1.0, 1.03),
}
```

Replace with:

```python
    "conclusion": (1.0, 1.03),
    "follow":     (1.0, 1.0),   # static
}
```

- [ ] **Step 3: Run tests to verify nothing broke**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 4: Commit**

```bash
cd C:/Users/55028/repo/ta && git add plugins/gv/python/templates/follow.html plugins/gv/python/config.py && git commit -m "feat(gv): add follow CTA slide template and config entries

New follow.html template for end-of-video CTA. Add follow type to
SHORT_V2_TRANSITIONS (fade, 0.5s) and SHORT_V2_KENBURNS (static).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Update Gen-Video Skill — Full Version TTS Opening

**Files:**
- Modify: `skills/gen-video/skill.md`

- [ ] **Step 1: Update Step 3 (full version) to include TTS opening**

In `skills/gen-video/skill.md`, find Step 3 (lines 44-50):

```markdown
### Step 3: Generate Full Version

If version is "full" or "both":

1. Extract text from all sections for TTS
2. Call `generate_tts(text=<full_text>, output_dir="gen-video/temp/{TICKER}_{DATE}_full")`
```

Replace with:

```markdown
### Step 3: Generate Full Version

If version is "full" or "both":

1. Extract text from all sections for TTS. **Prepend the opening line** `今日交易研报之<公司名>。` before the report text (use the Chinese company name from the report title, not the ticker symbol).
2. Call `generate_tts(text=<full_text>, output_dir="gen-video/temp/{TICKER}_{DATE}_full")`
```

- [ ] **Step 2: Update Step 4 (short version) to reflect 8 sections**

In `skills/gen-video/skill.md`, find Step 4 item 1 (line 56):

```markdown
1. Dispatch **video-scriptwriter** agent with the full report text. The agent returns structured JSON with 7 sections, each having `type`, `headline`, `body`, `tts_text`, and optional `highlights`/`index` fields. Save this JSON to a temp file for the render step.
```

Replace with:

```markdown
1. Dispatch **video-scriptwriter** agent with the full report text. The agent returns structured JSON with 8 sections (title → disclaimer → rating → point ×3 → conclusion → follow), each having `type`, `headline`, `body`, `tts_text`, and optional `highlights`/`index`/`sub_body`/`metrics` fields. The title slide headline uses "今日交易研报之<公司名>" format. Save this JSON to a temp file for the render step.
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/55028/repo/ta && git add skills/gen-video/skill.md && git commit -m "docs(gv): update skill with TTS opening prefix and 8-section structure

Full version prepends '今日交易研报之<公司名>' to TTS text.
Short version now expects 8 sections including follow CTA.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: End-to-End Verification

- [ ] **Step 1: Run all unit tests**

```bash
cd C:/Users/55028/repo/ta/plugins/gv && python -m pytest python/tests/ -v
```

Expected: All tests PASS.

- [ ] **Step 2: Generate a short video to verify all changes**

Use the gen-video skill pipeline for a report:
1. Dispatch scriptwriter agent (verify it outputs 8 sections with "今日交易研报之" title and follow slide)
2. Generate TTS
3. Render frames (verify 8 slides, check title and follow slides visually)
4. Compose video

- [ ] **Step 3: Verify title slide** — headline shows "今日交易研报之<公司名>", TTS starts with this phrase
- [ ] **Step 4: Verify follow slide** — last slide shows "关注我们" with 3 highlight chips, TTS ends with CTA
- [ ] **Step 5: Verify 8 total slides** — title, disclaimer, rating, point×3, conclusion, follow
