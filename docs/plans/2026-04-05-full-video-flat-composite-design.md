# Full Video: Flatten CompositeVideoClip for 7.5x Speedup

**Date:** 2026-04-05
**Status:** Approved
**Scope:** `plugins/gv/python/composer.py` — `_compose_full` only

## Problem

`_compose_full` uses MoviePy `CompositeVideoClip` with 3 layers (background, scroll, progress bar).
CompositeVideoClip performs per-frame Python-level layer blending — 13.2ms per frame × 19,400 frames = **~257 seconds** for an 808-second video.

The `make_frame` callback itself and the libx264 encoder are fast; the bottleneck is entirely in CompositeVideoClip's per-frame composition loop.

## Solution

Replace `CompositeVideoClip([bg, scroll_clip, progress_clip])` with a single `VideoClip(make_frame)` that composites all layers via direct numpy array operations inside `make_frame`.

### Key changes

1. **Pre-decode** the scroll image into a numpy array once (14.5 MB for 720×7041).
2. **Pre-build a base frame** (`HEIGHT × WIDTH × 3`) with static elements (header area, rating card area) baked in.
3. In `make_frame(t)`:
   - Copy base frame (2.6 MB memcpy, ~0.03ms)
   - Blit scroll region via array slice assignment
   - Draw progress bar via array slice assignment
   - Return the complete frame
4. Create a single `VideoClip(make_frame)`, attach audio, and call `write_videofile`.

### What stays the same

- `y_map` keyframe interpolation for audio-synced scrolling — unchanged
- `scroll_y_at(t)` function — unchanged
- All visual elements (header zone, rating card zone, scroll area, progress bar) — unchanged
- MoviePy `write_videofile` with libx264 — unchanged
- Short video pipeline — untouched

### What this enables for the future

Since `make_frame` is pure Python/numpy, any overlay effect can be added:
- Fly-in/fly-out text overlays at keyframe timestamps
- Highlight flash effects on key sections
- Animated icons or badges
- Alpha-blended overlays

## Benchmarks

| Configuration | 10s video | Est. 808s |
|---------------|-----------|-----------|
| Current (CompositeVideoClip, 3 layers) | 3.2s | ~257s |
| Flat make_frame (numpy composite) | 0.4s | **~34s** |
| Speedup | 8x | **7.5x** |

## Implementation Steps

1. Refactor `_compose_full`: replace CompositeVideoClip with single VideoClip
2. Pre-decode scroll image to numpy array at function start
3. Pre-build base frame with BG color
4. Rewrite make_frame to composite all layers via numpy slicing
5. Update tests
6. Integration test: regenerate TSLA full video, verify quality + timing
