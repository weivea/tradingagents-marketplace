"""Text-to-speech engine using edge-tts with word-level timestamps."""

import json
from pathlib import Path

import edge_tts

from .config import TTS_VOICE, TTS_RATE_FULL


async def generate_tts(
    text: str,
    output_dir: str,
    voice: str | None = None,
    rate: str | None = None,
) -> dict:
    """Generate TTS audio, timestamps, and SRT subtitles.

    Args:
        text: Chinese text to synthesize.
        output_dir: Directory to write output files.
        voice: TTS voice name (default: zh-CN-YunyangNeural).
        rate: Speech rate e.g. "+5%" (default: "+0%").

    Returns:
        dict with keys: audio_path, timestamps_path, srt_path, duration_seconds
    """
    voice = voice or TTS_VOICE
    rate = rate or TTS_RATE_FULL
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    audio_path = out / "audio.mp3"
    timestamps_path = out / "timestamps.json"
    srt_path = out / "subtitles.srt"

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    submaker = edge_tts.SubMaker()
    timestamps: list[dict] = []

    with open(audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
                timestamps.append({
                    "text": chunk["text"],
                    "offset_ms": chunk["offset"] // 10_000,  # 100ns ticks → ms
                    "duration_ms": chunk["duration"] // 10_000,
                })

    # Write timestamps JSON
    with open(timestamps_path, "w", encoding="utf-8") as f:
        json.dump(timestamps, f, ensure_ascii=False, indent=2)

    # Write SRT subtitles
    srt_content = submaker.get_srt()
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # Calculate duration from last timestamp
    duration_seconds = 0.0
    if timestamps:
        last = timestamps[-1]
        duration_seconds = (last["offset_ms"] + last["duration_ms"]) / 1000.0

    return {
        "audio_path": str(audio_path),
        "timestamps_path": str(timestamps_path),
        "srt_path": str(srt_path),
        "duration_seconds": round(duration_seconds, 2),
    }
