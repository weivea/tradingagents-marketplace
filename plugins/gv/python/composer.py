"""Compose final video from rendered images and TTS audio using MoviePy."""

import json
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
        video = _compose_short(frames_dir, audio, timestamps, duration)

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
        bar_img[15:18, 0:bar_width] = ACCENT_COLOR
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
) -> CompositeVideoClip:
    """Compose short-version video: slides with fade transitions synced to audio."""
    frames_path = Path(frames_dir)
    slides = sorted(frames_path.glob("slide_*.png"))

    if not slides:
        bg = ColorClip(size=(WIDTH, HEIGHT), color=BG_COLOR).with_duration(duration)
        return bg.with_audio(audio)

    num_slides = len(slides)
    slide_duration = duration / num_slides
    fade = SHORT_TRANSITION_DURATION

    clips = []
    for i, slide_path in enumerate(slides):
        clip = ImageClip(str(slide_path)).with_duration(slide_duration)
        clips.append(clip)

    # Concatenate with crossfade padding
    video = concatenate_videoclips(clips, method="compose", padding=-fade)
    video = video.with_audio(audio)
    return video
