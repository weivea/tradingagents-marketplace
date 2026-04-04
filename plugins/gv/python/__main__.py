"""CLI entry point: python -m python <command> [args]"""

import argparse
import json
import sys


def cmd_parse(args: argparse.Namespace) -> None:
    from .md_parser import parse_report

    result = parse_report(args.report_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_tts(args: argparse.Namespace) -> None:
    from .tts_engine import generate_tts

    import asyncio

    result = asyncio.run(
        generate_tts(
            text=args.text,
            output_dir=args.output_dir,
            voice=args.voice,
            rate=args.rate,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_render(args: argparse.Namespace) -> None:
    from .renderer import render_frames

    result = render_frames(
        sections_path=args.sections,
        layout=args.layout,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_compose(args: argparse.Namespace) -> None:
    from .composer import compose_video

    result = compose_video(
        frames_dir=args.frames_dir,
        audio_path=args.audio,
        timestamps_path=args.timestamps,
        layout=args.layout,
        output_path=args.output,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


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
        full_text = "\n".join(s["text"] for s in report["sections"] if s["text"].strip())
        tts_result = asyncio.run(
            generate_tts(
                text=full_text,
                output_dir=str(TEMP_DIR / f"{ticker}_{date}_full"),
            )
        )
        sections_path = str(TEMP_DIR / f"{ticker}_{date}_full_sections.json")
        with open(sections_path, "w", encoding="utf-8") as f:
            json.dump(report["sections"], f, ensure_ascii=False)
        render_result = render_frames(
            sections_path=sections_path,
            layout="full",
            output_dir=str(TEMP_DIR / f"{ticker}_{date}_full_frames"),
        )
        full_output = str(OUTPUT_DIR / f"{ticker}_{date}_full.mp4")
        compose_result = compose_video(
            frames_dir=render_result["image_paths"][0] if render_result["image_paths"] else "",
            audio_path=tts_result["audio_path"],
            timestamps_path=tts_result["timestamps_path"],
            layout="full",
            output_path=full_output,
        )
        results["full_video_path"] = compose_result["video_path"]
        results["full_srt_path"] = tts_result["srt_path"]

    if version in ("short", "both"):
        short_text = "\n".join(s["text"] for s in report["key_sections"] if s["text"].strip())
        tts_result = asyncio.run(
            generate_tts(
                text=short_text,
                output_dir=str(TEMP_DIR / f"{ticker}_{date}_short"),
                rate="+5%",
            )
        )
        sections_path = str(TEMP_DIR / f"{ticker}_{date}_short_sections.json")
        with open(sections_path, "w", encoding="utf-8") as f:
            json.dump(report["key_sections"], f, ensure_ascii=False)
        render_result = render_frames(
            sections_path=sections_path,
            layout="short",
            output_dir=str(TEMP_DIR / f"{ticker}_{date}_short_frames"),
        )
        short_output = str(OUTPUT_DIR / f"{ticker}_{date}_short.mp4")
        compose_result = compose_video(
            frames_dir=str(TEMP_DIR / f"{ticker}_{date}_short_frames"),
            audio_path=tts_result["audio_path"],
            timestamps_path=tts_result["timestamps_path"],
            layout="short",
            output_path=short_output,
        )
        results["short_video_path"] = compose_result["video_path"]
        results["short_srt_path"] = tts_result["srt_path"]

    print(json.dumps(results, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(prog="gv", description="Gen-Video CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # parse
    p_parse = sub.add_parser("parse", help="Parse a Markdown report")
    p_parse.add_argument("report_path", help="Path to *_zh.md file")
    p_parse.set_defaults(func=cmd_parse)

    # tts
    p_tts = sub.add_parser("tts", help="Generate TTS audio + timestamps")
    p_tts.add_argument("--text", required=True, help="Text to synthesize")
    p_tts.add_argument("--output-dir", required=True, help="Output directory")
    p_tts.add_argument("--voice", default=None, help="TTS voice name")
    p_tts.add_argument("--rate", default=None, help="TTS rate e.g. +5%%")
    p_tts.set_defaults(func=cmd_tts)

    # render
    p_render = sub.add_parser("render", help="Render text frames as images")
    p_render.add_argument("--sections", required=True, help="Path to sections JSON")
    p_render.add_argument("--layout", choices=["full", "short"], required=True)
    p_render.add_argument("--output-dir", required=True, help="Output directory")
    p_render.set_defaults(func=cmd_render)

    # compose
    p_compose = sub.add_parser("compose", help="Compose video from frames + audio")
    p_compose.add_argument("--frames-dir", required=True, help="Frames directory or image path")
    p_compose.add_argument("--audio", required=True, help="Audio file path")
    p_compose.add_argument("--timestamps", required=True, help="Timestamps JSON path")
    p_compose.add_argument("--layout", choices=["full", "short"], required=True)
    p_compose.add_argument("--output", required=True, help="Output MP4 path")
    p_compose.set_defaults(func=cmd_compose)

    # generate (one-click)
    p_gen = sub.add_parser("generate", help="One-click: report → video")
    p_gen.add_argument("report_path", help="Path to *_zh.md file")
    p_gen.add_argument("--version", choices=["full", "short", "both"], default="both")
    p_gen.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
