"""Compose final video from rendered images and TTS audio using MoviePy."""

import json
import subprocess
from pathlib import Path

import numpy as np
from moviepy import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    ColorClip,
    concatenate_videoclips,
)

from .config import (
    WIDTH, HEIGHT, FPS, CODEC,
    BG_COLOR,
    HEADER_HEIGHT, RATING_CARD_HEIGHT, SCROLL_AREA_HEIGHT, PROGRESS_BAR_HEIGHT,
    SHORT_TRANSITION_DURATION,
    ACCENT_COLOR,
    FFMPEG_PATH, SHORT_V2_OUTPUT_WIDTH, SHORT_V2_OUTPUT_HEIGHT,
    SHORT_V2_TRANSITIONS, SHORT_V2_KENBURNS,
)


def compose_video(
    frames_dir: str,
    audio_path: str,
    timestamps_path: str,
    layout: str,
    output_path: str,
) -> dict:
    """Compose MP4 video from frames + audio.

    Args:
        frames_dir: Path to frames directory (short) or scroll image path (full).
        audio_path: Path to TTS audio file.
        timestamps_path: Path to timestamps JSON.
        layout: "full" or "short".
        output_path: Output MP4 file path.

    Returns:
        dict with keys: video_path, duration_seconds
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(timestamps_path, "r", encoding="utf-8") as f:
        timestamps = json.load(f)

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if layout == "full":
        video = _compose_full(frames_dir, audio, timestamps, duration)
    else:
        video = _compose_short(frames_dir, audio, timestamps, duration, audio_path)

    video.write_videofile(
        output_path,
        fps=FPS,
        codec=CODEC,
        audio_codec="aac",
        logger="bar",
    )

    audio.close()
    video.close()

    return {
        "video_path": output_path,
        "duration_seconds": round(duration, 2),
    }


def _compose_full(
    scroll_image_path: str,
    audio: AudioFileClip,
    timestamps: list[dict],
    duration: float,
) -> CompositeVideoClip:
    """Compose full-version video: scroll image moves up in sync with audio."""
    # Load the y_map from the same directory as the scroll image
    scroll_path = Path(scroll_image_path)
    y_map_path = scroll_path.parent / "y_map.json"

    with open(y_map_path, "r", encoding="utf-8") as f:
        y_map = json.load(f)

    scroll_img = ImageClip(str(scroll_path))
    scroll_height = scroll_img.size[1]

    # Maximum scroll offset: scroll_height - visible area
    fixed_top = HEADER_HEIGHT + RATING_CARD_HEIGHT
    max_scroll = max(0, scroll_height - SCROLL_AREA_HEIGHT)

    # Build time → y_offset keyframes from timestamps + y_map
    keyframes: list[tuple[float, float]] = [(0.0, 0.0)]

    if y_map and timestamps:
        total_ts_ms = timestamps[-1]["offset_ms"] + timestamps[-1]["duration_ms"] if timestamps else 1
        for entry in y_map:
            section_y = entry["y_start"]
            progress = section_y / max(scroll_height, 1)
            t = progress * duration
            y_offset = min(section_y, max_scroll)
            keyframes.append((t, y_offset))
        keyframes.append((duration, max_scroll))

    # Remove duplicates and sort
    keyframes = sorted(set(keyframes), key=lambda k: k[0])

    def scroll_y_at(t: float) -> float:
        """Linearly interpolate y offset at time t."""
        if t <= keyframes[0][0]:
            return keyframes[0][1]
        if t >= keyframes[-1][0]:
            return keyframes[-1][1]
        for i in range(len(keyframes) - 1):
            t0, y0 = keyframes[i]
            t1, y1 = keyframes[i + 1]
            if t0 <= t <= t1:
                frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
                return y0 + frac * (y1 - y0)
        return keyframes[-1][1]

    # Background
    bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR).with_duration(duration)

    # Scroll clip: crop visible portion that shifts over time
    def make_frame(t):
        y_off = int(scroll_y_at(t))
        frame = np.array(scroll_img.get_frame(0))
        y_end = min(y_off + SCROLL_AREA_HEIGHT, scroll_height)
        crop = frame[y_off:y_end, :, :]
        if crop.shape[0] < SCROLL_AREA_HEIGHT:
            pad_h = SCROLL_AREA_HEIGHT - crop.shape[0]
            pad = np.full((pad_h, WIDTH, 3), BG_COLOR, dtype=np.uint8)
            crop = np.concatenate([crop, pad], axis=0)
        return crop

    from moviepy import VideoClip
    scroll_clip = VideoClip(make_frame, duration=duration).with_position((0, fixed_top))

    # Progress bar
    def make_progress_frame(t):
        bar_img = np.full((PROGRESS_BAR_HEIGHT, WIDTH, 3), BG_COLOR, dtype=np.uint8)
        progress = t / duration if duration > 0 else 0
        bar_width = int(WIDTH * progress)
        bar_img[10:12, 0:bar_width] = ACCENT_COLOR
        return bar_img

    progress_clip = VideoClip(make_progress_frame, duration=duration).with_position((0, HEIGHT - PROGRESS_BAR_HEIGHT))

    video = CompositeVideoClip([bg, scroll_clip, progress_clip], size=(WIDTH, HEIGHT))
    video = video.with_audio(audio)
    return video


def _compose_short(
    frames_dir: str,
    audio: AudioFileClip,
    timestamps: list[dict],
    duration: float,
    audio_file_path: str = "",
) -> CompositeVideoClip:
    """Compose short video — v2 (FFmpeg) if oversized frames detected, else legacy."""
    frames_path = Path(frames_dir)
    slides = sorted(frames_path.glob("slide_*.png"))

    if not slides:
        bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR).with_duration(duration)
        return bg.with_audio(audio)

    # Detect v2 by checking for _sections.json (written by v2 renderer)
    sections_json = frames_path / "_sections.json"
    is_v2 = sections_json.exists()

    if is_v2:
        # Read the sections JSON to get tts_text for duration calc
        sections = []
        if sections_json.exists():
            with open(sections_json, "r", encoding="utf-8") as f:
                sections = json.load(f)

        output_path = str(frames_path / "_v2_composed.mp4")
        _compose_short_v2(
            slide_paths=[str(s) for s in slides],
            sections=sections,
            timestamps=timestamps,
            audio_path=audio_file_path,
            total_duration=duration,
            output_path=output_path,
        )
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
    xfade_overlap: float = 0.0,
) -> list[float]:
    """Calculate per-slide durations based on TTS text character count.

    Falls back to equal split if no tts_text available.

    Args:
        xfade_overlap: Total seconds lost to xfade transitions between slides.
            Slide durations are inflated by this amount so the final composed
            video (after xfade compression) matches total_duration.
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
WrapStyle: 2

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
        if not text or text in ("，", "。", "、", "；", "：", "！", "？", "…"):
            continue
        wrapped = _wrap_ass_text(text, max_chars=20)
        start_t = ms_to_ass_time(start_ms)
        end_t = ms_to_ass_time(end_ms)
        events.append(f"Dialogue: 0,{start_t},{end_t},Highlight,,0,0,0,,{wrapped}")

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

    # 3. Generate zoompan segments
    segment_paths: list[str] = []
    for i, slide_path in enumerate(slide_paths):
        stype = sections[i].get("type", "point") if i < len(sections) else "point"
        sz, ez = SHORT_V2_KENBURNS.get(stype, (1.0, 1.03))
        seg_path = str(tmp_dir / f"_seg_{i:02d}.mp4")
        cmd = _build_zoompan_cmd(slide_path, seg_path, durations[i], sz, ez, FPS, out_w, out_h)
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        segment_paths.append(seg_path)

    # 4. Merge segments with xfade
    merged_path = str(tmp_dir / "_merged.mp4")
    cmd = _build_xfade_cmd(segment_paths, durations, transitions, merged_path)
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)

    # 5. Generate ASS subtitles
    ass_path = str(tmp_dir / "_subtitles.ass")
    ass_content = _build_ass_subtitles(timestamps, out_w, out_h)
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)

    # 6. Overlay subtitles + add audio
    # FFmpeg filter expressions treat ':' as option separator, which breaks
    # Windows absolute paths like C:/... — escape with backslash-colon.
    ass_path_fwd = ass_path.replace("\\", "/").replace(":", "\\:")
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", merged_path,
        "-i", audio_path,
        "-vf", f"ass={ass_path_fwd}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-t", f"{total_duration:.3f}",
        str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=180)

    # 7. Cleanup temp files
    for seg in segment_paths:
        Path(seg).unlink(missing_ok=True)
    Path(merged_path).unlink(missing_ok=True)
    Path(ass_path).unlink(missing_ok=True)

