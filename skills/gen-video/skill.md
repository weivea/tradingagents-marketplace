---
name: gen-video
description: Generate narrated scrolling videos from Chinese analysis reports. Converts analysis/*_zh.md to MP4 with TTS narration and synchronized text animation. Produces full version (8-15 min scroll) and short version (60-90s slides).
---

# Gen-Video — Report to Video Pipeline

Generate narrated scrolling videos from Chinese analysis reports.

## When to Use

When the user asks to convert a report to video. Trigger phrases include:
- "为 NIO 报告生成视频"
- "generate video for the latest analysis"
- "把分析报告转成视频"
- "create video from report"

## Inputs

1. **Report path** (required) — path to a `*_zh.md` file in `analysis/`
2. **Version** (optional, default: "both") — "full", "short", or "both"

## Pipeline

### Step 1: Identify Report

If the user specifies a ticker but not a file path, find the latest matching report:

```bash
ls -t analysis/*_zh.md | head -5
```

Confirm with the user which report to use.

### Step 2: Parse Report

Call MCP tool:
> `parse_report(report_path="analysis/{TICKER}_{DATE}_zh.md")`

This returns structured JSON with ticker, date, rating, sections, and key_sections.

### Step 3: Generate Full Version

If version is "full" or "both":

1. Extract text from all sections for TTS
2. Call `generate_tts(text=<full_text>, output_dir="gen-video/temp/{TICKER}_{DATE}_full")`
3. Save sections to temp JSON file
4. Call `render_frames(sections_path=<temp_json>, layout="full", output_dir="gen-video/temp/{TICKER}_{DATE}_full_frames")`
5. Call `compose_video(frames_dir=<scroll_image_path>, audio_path=<audio>, timestamps_path=<timestamps>, layout="full", output_path="gen-video/output/{TICKER}_{DATE}_full.mp4")`

### Step 4: Generate Short Version

If version is "short" or "both":

1. Dispatch **video-scriptwriter** agent with the full report text to extract a 60-90 second narration script (250-400 characters, 7-9 sections: title → disclaimer → rating → 3 key points → conclusion)
2. Call `generate_tts(text=<script_text>, output_dir="gen-video/temp/{TICKER}_{DATE}_short", rate="+5%")`
3. Save script sections to temp JSON file
4. Call `render_frames(sections_path=<temp_json>, layout="short", output_dir="gen-video/temp/{TICKER}_{DATE}_short_frames")`
5. Call `compose_video(frames_dir=<frames_dir>, audio_path=<audio>, timestamps_path=<timestamps>, layout="short", output_path="gen-video/output/{TICKER}_{DATE}_short.mp4")`

### Step 5: Report Results

Present to the user:
> 视频生成完成！
> - 完整版: `gen-video/output/{TICKER}_{DATE}_full.mp4` (X分X秒)
> - 精华版: `gen-video/output/{TICKER}_{DATE}_short.mp4` (X秒)
> - 字幕: `gen-video/output/{TICKER}_{DATE}_full.srt`, `...short.srt`

## Alternative: One-Click

For simplicity, you can also use the single `generate_video` MCP tool:

> `generate_video(report_path="analysis/{TICKER}_{DATE}_zh.md", version="both")`

This runs the entire pipeline in one call.
