# Generate Video Call Chain Analysis
## Full Call Stack from MCP Handler to Video Generation

Generated: 2026-04-12

---

## 1. MCP Tool Handler
**File:** `./plugins/gv/src/index.ts`
**Lines:** 82-94

```typescript
server.registerTool(
  "generate_video",
  {
    description: "One-click: convert a Chinese analysis report to narrated scrolling video (full, short, or both versions)",
    inputSchema: {
      report_path: z.string().describe("Path to *_zh.md report file"),
      version: z.enum(["full", "short", "both"]).optional().default("both").describe("Which version(s) to generate"),
    },
  },
  async (params) => ({
    content: [{ type: "text", text: await generateVideo(params) }],
  })
);
```

**Key Points:**
- MCP tool named `generate_video`
- Accepts `report_path` (string) and optional `version` (enum: "full", "short", "both")
- Calls TypeScript `generateVideo()` function
- Returns content object with plain text output

---

## 2. TypeScript Tool Implementation (generateVideo)
**File:** `./plugins/gv/src/tools/generate.ts`
**Lines:** 1-18

```typescript
import { callPython } from "./call-python.js";

export interface GenerateVideoParams {
  report_path: string;
  version?: "full" | "short" | "both";
}

export async function generateVideo(params: GenerateVideoParams): Promise<string> {
  const { report_path, version } = params;
  const args = ["generate", report_path];
  if (version) args.push("--version", version);
  try {
    return await callPython(args);
  } catch (error: any) {
    return JSON.stringify({ error: error.message });
  }
}
```

**Key Points:**
- Builds command line arguments: `["generate", report_path, "--version", version]`
- Delegates to Python via `callPython()` function
- Returns raw stdout (JSON string) or error JSON

---

## 3. TypeScript-to-Python Bridge (callPython)
**File:** `./plugins/gv/src/tools/call-python.ts`
**Lines:** 1-31

```typescript
import { execFile } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PLUGIN_DIR = path.resolve(__dirname, "../..");  // plugins/gv/

export function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "uv",
      ["run", "--project", PLUGIN_DIR, "python", "-m", "python", ...args],
      {
        cwd: PLUGIN_DIR,
        timeout: 3_600_000,  // 60 min
        maxBuffer: 50 * 1024 * 1024,  // 50MB for large JSON output
        encoding: "utf-8",
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      },
      (err, stdout, stderr) => {
        if (err) {
          reject(new Error(`Python error: ${stderr || err.message}`));
        } else {
          resolve(stdout);
        }
      }
    );
  });
}
```

**Key Points:**
- Uses `uv run` to execute Python in the `plugins/gv` project
- Runs: `uv run --project ./plugins/gv python -m python generate <report_path> --version <version>`
- 60-minute timeout (needed for full video encoding)
- 50MB stdout buffer

---

## 4. Python CLI Entry Point (cmd_generate)
**File:** `./plugins/gv/python/__main__.py`
**Lines:** 60-134

The CLI main dispatcher accepts the `generate` command and routes it:

```python
def cmd_generate(args: argparse.Namespace) -> None:
    from .md_parser import parse_report
    from .tts_engine import generate_tts
    from .renderer import render_frames
    from .composer import compose_video
    from .config import OUTPUT_DIR, TEMP_DIR

    import asyncio

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = parse_report(args.report_path)
    ticker = report["ticker"]
    date = report["date"]
    version = args.version
    results: dict = {}

    if version in ("full", "both"):
        # Generate full version...
    if version in ("short", "both"):
        # Generate short version...

    print(json.dumps(results, ensure_ascii=False, indent=2))
```

**Entry Point Registration:**
**Lines:** 169-173
```python
p_gen = sub.add_parser("generate", help="One-click: report → video")
p_gen.add_argument("report_path", help="Path to *_zh.md file")
p_gen.add_argument("--version", choices=["full", "short", "both"], default="both")
p_gen.set_defaults(func=cmd_generate)
```

---

## 5. Pipeline Step 1: Parse Report
**File:** `./plugins/gv/python/md_parser.py`
**Lines:** 7-153 (main function)

### Function: `parse_report(report_path: str) -> dict`

**What it does:**
- Parses `*_zh.md` Markdown analysis reports
- Extracts metadata: ticker, date, company name, rating
- Splits document into structured `sections`

**Output Structure (Legacy v1 format):**
```python
{
    "ticker": "NIO",           # from filename NIO_2026-04-04_zh.md
    "company": "蔚来汽车",      # from H1 title pattern
    "date": "2026-04-04",      # from filename
    "rating": "卖出",           # from "# **卖出**" pattern
    "sections": [              # Full version content
        {
            "type": "title" | "heading" | "paragraph" | "table" | "divider" | "rating_card",
            "level": 0 | 1 | 2 | 3,
            "text": "Clean TTS text (markdown formatting stripped)",
            "raw": "Original markdown line(s)",
            "rows": []  # For tables only
        },
        ...
    ],
    "key_sections": [          # Short version content
        # Same structure as sections, subset for short video
    ]
}
```

**Section Types:**
- `title`: First H1 heading
- `heading`: H2, H3 headings with accent bar
- `rating_card`: Headings containing 卖出/买入/持有/增持/减持
- `paragraph`: Regular text blocks, blockquotes
- `table`: Markdown tables → rows array
- `divider`: Horizontal rules (---)

**Section Text Processing:**
- Strips markdown formatting: `**bold**` → `bold`, `*italic*` → `italic`, `[link](url)` → `link`
- Preserves Chinese punctuation
- Used for TTS narration

**Key Sections Extraction:**
**Lines:** 170-217
- Selects: title, disclaimer (first "免责声明"), rating, top 3 investment argument paragraphs, conclusion
- Cuts full report down to ~250-400 Chinese characters for short videos

---

## 6. Pipeline Step 2A: Generate TTS (Full Version)
**File:** `./plugins/gv/python/tts_engine.py`
**Lines:** 11-73

### Function: `generate_tts(text: str, output_dir: str, voice: str | None, rate: str | None) -> dict`

**Called from:** `__main__.py` lines 80-85 (full) and 107-113 (short)

**Input (Full Version):**
- **text**: `"\n".join(s["text"] for s in report["sections"] if s["text"].strip())`
  - Full concatenation of all section texts
  - Line breaks between sections

- **output_dir**: `str(TEMP_DIR / f"{ticker}_{date}_full")`
  - e.g., `gen-video/temp/NIO_2026-04-04_full`

- **voice**: `None` (uses default `zh-CN-YunyangNeural`)

- **rate**: `None` (uses `+0%` normal speed)

**Input (Short Version):**
- **text**: `"\n".join(s["text"] for s in report["key_sections"] if s["text"].strip())`
  - Only key sections

- **output_dir**: `str(TEMP_DIR / f"{ticker}_{date}_short")`
  - e.g., `gen-video/temp/NIO_2026-04-04_short`

- **rate**: `"+5%"` (5% speed increase for TikTok pacing)

**Processing:**
```python
communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
submaker = edge_tts.SubMaker()
timestamps: list[dict] = []

# Stream audio chunks + word boundaries
with open(audio_path, "wb") as audio_file:
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_file.write(chunk["data"])
        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
            submaker.feed(chunk)
            timestamps.append({
                "text": chunk["text"],
                "offset_ms": chunk["offset"] // 10_000,  # 100ns → ms
                "duration_ms": chunk["duration"] // 10_000,
            })
```

**Output Files:**
```
gen-video/temp/{ticker}_{date}_{layout}/
├── audio.mp3                  # TTS audio (edge-tts)
├── timestamps.json            # Word-level timing data
└── subtitles.srt             # SRT subtitle file
```

**Timestamps JSON Structure:**
```json
[
  {"text": "今日", "offset_ms": 0, "duration_ms": 320},
  {"text": "交易", "offset_ms": 320, "duration_ms": 240},
  ...
]
```

---

## 7. Pipeline Step 2B: Parse & Save Sections JSON
**File:** `./plugins/gv/python/__main__.py`
**Lines:** 86-88 (full), 114-116 (short)

```python
sections_path = str(TEMP_DIR / f"{ticker}_{date}_{layout}_sections.json")
with open(sections_path, "w", encoding="utf-8") as f:
    json.dump(report["sections"] or report["key_sections"], f, ensure_ascii=False)
```

**Purpose:** Cache parsed sections for renderer and composer

---

## 8. Pipeline Step 3: Render Frames
**File:** `./plugins/gv/python/renderer.py`
**Lines:** 97-121

### Function: `render_frames(sections_path: str, layout: str, output_dir: str) -> dict`

**Called from:** `__main__.py` lines 89-93 (full), 117-121 (short)

### For Full Layout:
**Function:** `_render_full(sections: list[dict], out: Path) -> dict`
**Lines:** 124-241

**Output:** Single tall scroll image (1080 × N pixels)

1. **First pass** (lines 134-166): Calculate section positions
   - Iterates through all sections
   - Calculates pixel heights based on content
   - Builds `y_map.json`: position of each section in the scroll

2. **Second pass** (lines 170-227): Render to PIL Image
   - Draws headings with accent bars
   - Renders paragraph text wrapped to width
   - Draws tables with alternating row backgrounds
   - Applies dither noise to smooth gradients

**Output Files:**
```
gen-video/temp/{ticker}_{date}_full_frames/
├── scroll.png              # 1080 × (height) PNG image
└── y_map.json             # Section position mapping
```

**y_map.json Example:**
```json
[
  {
    "section_index": 0,
    "y_start": 40,
    "y_end": 120,
    "type": "title",
    "text_preview": "NIO 交易研报"
  },
  {
    "section_index": 1,
    "y_start": 120,
    "y_end": 200,
    "type": "heading",
    "text_preview": "投资论点"
  },
  ...
]
```

### For Short Layout:
**Function:** `_render_short(sections: list[dict], out: Path) -> dict`
**Lines:** 287-292

**Dispatches to either:**

#### Option A: V2 Format Renderer (`_render_short_v2`)
**Lines:** 244-363

**Detects V2 Format:**
```python
def _is_v2_format(sections: list[dict]) -> bool:
    """Detect if sections use v2 format (headline/body/tts_text)."""
    if not sections:
        return False
    first = sections[0]
    return "headline" in first and "tts_text" in first
```

**V2 Section Structure (from video-scriptwriter):**
```json
{
  "type": "title|rating|point|comparison|data-highlight|catalyst|quote|risk-matrix|conclusion|follow",
  "headline": "Punchy short title for display",
  "body": "Supporting text (30-60 chars)",
  "tts_text": "Narration text (no symbols, numbers spelled out)",
  "index": 1,
  "sub_body": "Optional: display-only supporting detail",
  "highlights": ["$4.80", "-24%"],
  "metrics": [
    {"label": "Target", "value": "$5.20", "signal": "negative"}
  ]
}
```

**V2 Rendering Process:**
1. **Template Selection** (lines 327-333):
   - Loads Jinja2 templates from `plugins/gv/python/templates/`
   - Maps section.type → `{type}.html` template
   - Fallback to `point.html`

2. **Template Rendering** (lines 335-344):
   - Builds context with `_build_template_context()`
   - Renders HTML from template
   - Converts relative base.css to absolute file:/// URL for Playwright

3. **Playwright Screenshots** (lines 346-356):
   - Launches Chromium
   - Navigates to HTML file
   - Takes 1080×1920 screenshot
   - Applies dither noise
   - Saves as `slide_XX.png`

4. **Sections JSON Caching** (lines 359-361):
   - Saves original v2 sections to `_sections.json`
   - Used later by composer to calculate slide durations

**Output Files:**
```
gen-video/temp/{ticker}_{date}_short_frames/
├── slide_00.png            # 1080 × 1920 per slide
├── slide_01.png
├── slide_02.png
├── ...
└── _sections.json         # V2 sections metadata
```

#### Option B: Legacy Pillow Renderer (`_render_short_legacy`)
**Lines:** 366-416

**Falls back for old section format** (no headline/body/tts_text fields)
- Creates per-slide 1080×1920 images using PIL
- Renders section.text centered on each slide
- Progress dots at bottom

**Output Files:**
```
gen-video/temp/{ticker}_{date}_short_frames/
├── slide_00.png
├── slide_01.png
└── ...
```

---

## 9. Pipeline Step 4: Compose Video
**File:** `./plugins/gv/python/composer.py`
**Lines:** 29-76

### Function: `compose_video(frames_dir: str, audio_path: str, timestamps_path: str, layout: str, output_path: str) -> dict`

**Called from:** `__main__.py` lines 95-101 (full), 123-129 (short)

### For Full Layout:
**Function:** `_compose_full(scroll_image_path, audio, timestamps, duration)`
**Lines:** 79-162

**Key Algorithm: Smooth Scrolling with Keyframe Interpolation**

1. **Load y_map** (lines 94-98):
   - Reads y_map.json to get section positions
   - Pre-decodes scroll image to numpy array (no per-frame PNG I/O)

2. **Build Keyframes** (lines 111-120):
   - Maps section positions to audio timeline
   - Creates (time, y_offset) keyframe pairs
   - Linearly interpolates between keyframes

3. **Per-Frame Rendering** (lines 142-158):
   - For each video frame at time t:
     - Calculate scroll y_offset via keyframe interpolation
     - Composite: background + scrolling text region + progress bar
     - Uses NumPy slicing (no Python layer overhead)

4. **Video Output**:
   - Uses MoviePy to write MP4 with audio
   - FFmpeg deband filter to smooth gradients

**Output:** `{ticker}_{date}_full.mp4`

### For Short Layout - Detection:
**Function:** `_compose_short(frames_dir, audio, timestamps, duration)`
**Lines:** 165-232

**Priority:**
1. **Try Remotion V3** (lines 185-211) - if available and v2 format
2. **Fall back to V2 FFmpeg** (lines 213-230) - if v2 format detected
3. **Fall back to Legacy** (lines 231-232) - for old format

**V2 Detection:**
```python
sections_json = frames_path / "_sections.json"
is_v2 = sections_json.exists()
```

### For Short Layout - V2 FFmpeg Composition:
**Function:** `_compose_short_v2(slide_paths, sections, timestamps, audio_path, duration, output_path)`
**Lines:** 465-541

**5-Step Process:**

1. **Build Transitions** (lines 480-487):
   - Maps section.type → transition effect
   - From config: `SHORT_V2_TRANSITIONS` (fade, zoomin, wipeup, etc.)

2. **Calculate Durations** (lines 489-491):
   - `_calc_slide_durations()` (lines 255-296)
   - **By default**: Equal split across slides
   - **If v2 sections have tts_text**: Proportional to text character count
   ```python
   durations = [len(t) / total_chars * effective_duration for t in tts_texts]
   ```

3. **Generate Ken Burns Zoompan** (lines 494-501):
   - For each slide, applies subtle zoom animation
   - Ken Burns start/end zoom per type (from `SHORT_V2_KENBURNS`)
   - Example: title (1.0 → 1.03), rating (1.03 → 1.0 zoom-out)
   - FFmpeg zoompan filter with frame interpolation

4. **Merge Segments with Transitions** (lines 504-506):
   - FFmpeg xfade filter chains slides
   - Applies transition overlaps (fade, zoomin, wipeup, etc.)
   - Maintains total duration

5. **Overlay Subtitles + Audio** (lines 509-534):
   - Generates ASS subtitle file with word-level highlighting
   - Overlays on video using FFmpeg ass filter
   - Mixes audio track (AAC 192k)
   - Applies deband filter

**Output:** `{ticker}_{date}_short.mp4`

**Cleanup:** Removes temp segments (lines 536-540)

---

## 10. Final Output Structure
**From:** `__main__.py` lines 76-133

**Results Dictionary:**
```python
results: dict = {}

if version in ("full", "both"):
    results["full_video_path"] = str  # gen-video/output/{ticker}_{date}_full.mp4
    results["full_srt_path"] = str    # gen-video/temp/{ticker}_{date}_full/subtitles.srt

if version in ("short", "both"):
    results["short_video_path"] = str # gen-video/output/{ticker}_{date}_short.mp4
    results["short_srt_path"] = str   # gen-video/temp/{ticker}_{date}_short/subtitles.srt

print(json.dumps(results, ensure_ascii=False, indent=2))
```

**Printed Output (stdout from Python):**
```json
{
  "full_video_path": "/path/to/gen-video/output/NIO_2026-04-04_full.mp4",
  "full_srt_path": "/path/to/gen-video/temp/NIO_2026-04-04_full/subtitles.srt",
  "short_video_path": "/path/to/gen-video/output/NIO_2026-04-04_short.mp4",
  "short_srt_path": "/path/to/gen-video/temp/NIO_2026-04-04_short/subtitles.srt"
}
```

**Returned to MCP Client:** Wrapped in content object

---

## VIDEO-SCRIPTWRITER (Agent/Template)
**File:** `./agents/video-scriptwriter.md`
**Lines:** 1-219

**Status:** This is an **agent prompt/specification** (not yet integrated into code)

### Purpose
Generate v2-format sections with headline/body/tts_text fields from Chinese trading analysis reports

### Input
Full analysis report markdown file

### Output Format (V2 JSON)
```json
[
  {
    "type": "title|rating|point|comparison|...",
    "headline": "Short punchy title for display",
    "body": "Supporting context (30-60 chars)",
    "tts_text": "Narration for TTS (250-500 chars total)",
    "index": 1,
    "sub_body": "Optional display-only detail",
    "highlights": ["$5.20", "-24%"],
    "metrics": [{"label": "...", "value": "...", "signal": "..."}]
  },
  ...
]
```

### V2 Types
- `title` - Stock name + date
- `disclaimer` - Legal notice
- `rating` - Rating + target price
- `point` - Key investment argument (1-3 per report)
- `comparison` - Bull vs Bear debate
- `data-highlight` - Single impactful number
- `catalyst` - Upcoming catalysts
- `quote` - Memorable analyst quote
- `risk-matrix` - Probability-weighted scenarios
- `conclusion` - Final recommendation
- `follow` - Call to action

### Field Reference

| Field | Type | Required | Example |
|-------|------|----------|---------|
| `type` | string | Yes | "point", "rating", etc. |
| `headline` | string | Yes | "研发砍了三分之一" |
| `body` | string | Yes | "竞争对手纷纷加大投入，NIO削减研发" |
| `tts_text` | string | Yes | "研发支出削减三十四个百分点…" |
| `index` | int | No (point only) | 1, 2, 3 |
| `sub_body` | string | No | "长期竞争力受限" |
| `highlights` | array | No | ["$5.20", "-24%"] |
| `metrics` | array | No | `[{label, value, signal}]` |
| `highlights` | array | No | `["$5", "-24%"]` |

### Integration Point
**Where it connects:** Renderer v2 detection
- File: `./plugins/gv/python/renderer.py`
- Lines: 244-249
- Once sections have headline/body/tts_text, they trigger:
  - V2 HTML template rendering (Playwright)
  - V2 composition (FFmpeg Ken Burns + xfade)
  - Slide duration calculation by tts_text character count

---

## Summary: Full Call Chain

```
MCP Tool: generate_video
    │
    └─> generateVideo() [TypeScript]
            │
            └─> callPython(["generate", report_path, "--version", version])
                    │
                    └─> uv run --project ./plugins/gv python -m python generate ...
                            │
                            └─> cmd_generate() [Python __main__.py]
                                    │
                                    ├─> parse_report() [md_parser.py]
                                    │   Returns: {ticker, date, sections, key_sections}
                                    │
                                    ├─> generate_tts() [tts_engine.py]
                                    │   Returns: {audio_path, timestamps_path, srt_path}
                                    │
                                    ├─> render_frames() [renderer.py]
                                    │   • Full: _render_full() → scroll.png + y_map.json
                                    │   • Short: _render_short()
                                    │     ├─> _render_short_v2() [if v2 format]
                                    │     │   Uses Playwright + HTML templates
                                    │     │   Returns: slide_00.png, slide_01.png, ...
                                    │     └─> _render_short_legacy() [if v1 format]
                                    │
                                    └─> compose_video() [composer.py]
                                        • Full: _compose_full() [MoviePy scrolling]
                                        • Short: _compose_short()
                                          ├─> _compose_short_v3() [Remotion React]
                                          ├─> _compose_short_v2() [FFmpeg Ken Burns + xfade]
                                          │   1. Build transitions
                                          │   2. Calculate durations (by tts_text length)
                                          │   3. Zoompan effect
                                          │   4. xfade merge
                                          │   5. ASS subtitles
                                          │   6. Overlay + audio
                                          └─> _compose_short_legacy() [MoviePy fade]
                                              Returns: video_path

                                    JSON output → stdout → MCP response
```

---

## Key Data Structures

### Parser Output (sections)
```python
sections[i] = {
    "type": "title|heading|paragraph|table|divider|rating_card",
    "level": 0|1|2|3,
    "text": str,              # TTS text (markdown stripped)
    "raw": str,               # Original markdown
    "rows": list[list[str]]   # For tables only
}
```

### V2 Sections (with video-scriptwriter)
```python
sections[i] = {
    "type": "title|rating|point|comparison|data-highlight|catalyst|quote|risk-matrix|conclusion|follow",
    "headline": str,          # Visual title
    "body": str,              # Visual subtitle
    "tts_text": str,          # Narration text
    "index": int,             # For points/items
    "sub_body": str,          # Optional: display-only detail
    "highlights": list[str],  # Visual emphasis items
    "metrics": list[dict],    # Dashboard metrics
    ...type-specific fields...
}
```

### Timestamps (from edge-tts)
```python
timestamps[i] = {
    "text": str,              # Word or phrase
    "offset_ms": int,         # Start time
    "duration_ms": int        # Duration
}
```

### Y-Map (full version scroll positions)
```python
y_map[i] = {
    "section_index": int,
    "y_start": int,
    "y_end": int,
    "type": str,
    "text_preview": str
}
```

---

## Configuration & Constants
**File:** `./plugins/gv/python/config.py`

### Output Paths
- `ANALYSIS_DIR`: Where markdown reports come from
- `OUTPUT_DIR`: Where final .mp4 files go: `gen-video/output/`
- `TEMP_DIR`: Intermediate files: `gen-video/temp/`

### Video Dimensions
- Full: 720×1280 px
- Short: 1080×1920 px (vertical mobile)

### V2 Rendering (Short Videos)
- Templates: `plugins/gv/python/templates/`
- Playwright render size: 1134×2016 (5% overscan for Ken Burns)
- FFmpeg output: 1080×1920
- Transitions: fade, fadeblack, zoomin, slideleft, wipeup (per type)
- Ken Burns: subtle zoom animations (1.0 to 1.03, type-specific)

### TTS
- Voice: zh-CN-YunyangNeural
- Full rate: +0% (normal)
- Short rate: +5% (faster pacing)

---

## Connection to Video-Scriptwriter

**The video-scriptwriter is a SPECIFICATION for how to generate v2-format sections.**

Currently, the pipeline:
1. ✅ Accepts v1 sections (legacy format) from `parse_report()`
2. ✅ Can render both v1 (legacy Pillow) and v2 (Playwright + templates)
3. ❓ Does NOT yet have code to call video-scriptwriter and generate v2 sections from v1
4. ✅ When v2 sections ARE provided, it renders them beautifully with dynamic templates

**To fully integrate video-scriptwriter:**
- Add a new step in `cmd_generate()` after `parse_report()`
- Call an LLM-based scriptwriter function to convert v1 sections → v2 sections
- Pass v2 sections to renderer/composer pipeline
- Renderer detects v2 format via `_is_v2_format()` check
- Proceeds with template rendering + Playwright + FFmpeg

This would enable: **Full markdown report → AI-powered script → Dynamic video slides → Polished TikTok-ready MP4**

