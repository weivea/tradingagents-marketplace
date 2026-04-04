"""Configuration constants for video generation."""

from pathlib import Path

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # ta/
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
OUTPUT_DIR = PROJECT_ROOT / "gen-video" / "output"
TEMP_DIR = PROJECT_ROOT / "gen-video" / "temp"

# --- Video ---
WIDTH = 720
HEIGHT = 1280
FPS = 24
CODEC = "libx264"

# --- Colors (RGB tuples) ---
BG_COLOR = (10, 14, 39)           # #0a0e27 deep blue
TEXT_COLOR = (192, 200, 224)      # #c0c8e0 light grey-blue
HEADING_COLOR = (224, 230, 255)   # #e0e6ff bright white-blue
ACCENT_COLOR = (100, 108, 255)    # #646cff purple-blue
RATING_SELL_COLOR = (255, 68, 68) # #ff4444 red
RATING_BUY_COLOR = (74, 222, 128) # #4ade80 green
HIGHLIGHT_BG = (100, 108, 255, 20)  # accent with low alpha

# --- Typography (scaled for 720p) ---
FONT_REGULAR = "msyh.ttc"   # 微软雅黑 (Windows), fallback to Noto Sans CJK SC
FONT_BOLD = "msyhbd.ttc"    # 微软雅黑 Bold
FONT_SIZE_BODY = 19
FONT_SIZE_H1 = 32
FONT_SIZE_H2 = 24
FONT_SIZE_H3 = 21
FONT_SIZE_SMALL = 15
LINE_HEIGHT_MULTIPLIER = 1.8
MARGIN_X = 40

# --- Layout zones (full version, scaled for 720p) ---
HEADER_HEIGHT = 80
RATING_CARD_HEIGHT = 67
PROGRESS_BAR_HEIGHT = 27
SCROLL_AREA_HEIGHT = HEIGHT - HEADER_HEIGHT - RATING_CARD_HEIGHT - PROGRESS_BAR_HEIGHT  # 1106px

# --- TTS ---
TTS_VOICE = "zh-CN-YunyangNeural"
TTS_RATE_FULL = "+0%"
TTS_RATE_SHORT = "+5%"

# --- Short version ---
SHORT_TRANSITION_DURATION = 0.4  # seconds for fade in/out
SHORT_MAX_SECTIONS = 7
SHORT_TARGET_WORDS = 350  # target ~250-400 Chinese characters
