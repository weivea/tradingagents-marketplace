# Gen-Video Plugin Design Spec

将 TradingAgents 中文分析报告（`analysis/*_zh.md`）自动转换为带语音朗读和文字滚动的竖屏短视频。

## 需求

- **输入：** `analysis/` 目录下的中文 Markdown 报告
- **输出：** 两个版本的 MP4 视频
  - 完整版（8-15 分钟）：全文朗读 + 全屏文字滚动
  - 精华版（60-90 秒）：AI 提取核心要点 + 逐段显现动画
- **使用场景：** 抖音/B站/小红书等社交媒体短视频平台
- **触发方式：** Claude Code skill 编排 或 命令行 CLI
- **技术约束：** 全免费方案，无需 API Key

## 技术栈

| 组件 | 技术 | 协议 | 职责 |
|------|------|------|------|
| MCP Server | Node.js + TypeScript | MIT | 暴露 MCP tools 给 Claude |
| 语音合成 | edge-tts | GPL-3.0 | 中文 TTS + 词级时间戳 |
| 画面渲染 | Pillow | HPND | 中文文字渲染为图片 |
| 视频合成 | MoviePy 2.x | MIT | 图片滚动动画 + 音频叠加 |
| 视频编码 | FFmpeg | LGPL/GPL | MoviePy 底层编码器 |

## 插件目录结构

```
ta/
├── plugins/
│   └── gv/                          ★ 视频生成插件
│       ├── .claude-plugin/
│       │   └── plugin.json          # 插件元数据
│       ├── .mcp.json                # MCP 服务器注册
│       ├── package.json             # Node.js 依赖
│       ├── tsconfig.json
│       ├── src/                     # TypeScript MCP Server
│       │   ├── index.ts             # MCP 入口，注册 tools
│       │   └── tools/
│       │       ├── parse.ts         # parse_report tool
│       │       ├── tts.ts           # generate_tts tool
│       │       ├── render.ts        # render_frames tool
│       │       ├── compose.ts       # compose_video tool
│       │       └── generate.ts      # generate_video tool (一键全流程)
│       ├── python/                  # Python 包 (python -m gv.python ...)
│       │   ├── __init__.py          # 包标识
│       │   ├── __main__.py          # CLI 入口: python -m gv.python
│       │   ├── md_parser.py         # Markdown 解析
│       │   ├── tts_engine.py        # edge-tts 语音合成
│       │   ├── renderer.py          # Pillow 渲染
│       │   ├── composer.py          # MoviePy 合成
│       │   └── config.py            # 配置常量
│       ├── fonts/                   # 中文字体文件
│       └── requirements.txt         # Python 依赖
│
├── skills/
│   └── gen-video/
│       └── skill.md                 # Claude Code skill 编排定义
│
├── agents/
│   └── video-scriptwriter.md        # 精华版脚本撰写 agent
│
├── analysis/                        # 输入：中文报告
└── gen-video/output/                # 输出：生成的视频
```

## 架构与数据流

### 调用链路

```
Claude Code skill (gen-video)
    │
    ▼
MCP Tool (Node.js/TypeScript)     ←── 与 t_mcp 同模式
    │ child_process.execFile()
    ▼
Python CLI (python -m gv)         ←── 实际执行
    │
    ▼
edge-tts / Pillow / MoviePy
```

### 完整版流水线

```
analysis/NIO_2026-04-04_zh.md
    │
    ▼
┌─────────────────────────────────┐
│  parse_report                   │  正则解析 Markdown → sections.json
│  (MCP tool → python -m gv parse)│  提取 ticker/date/rating/段落/表格
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  generate_tts                   │  edge-tts → audio.mp3
│  (MCP tool → python -m gv tts) │  + timestamps.json (词级时间戳)
│                                 │  + subtitles.srt
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  render_frames                  │  Pillow → 超长文字图片 (1080×N)
│  (MCP tool → python -m gv render)│ + y_map.json (段落→Y坐标映射)
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  compose_video                  │  MoviePy → MP4
│  (MCP tool → python -m gv compose)│ 图片按时间戳滚动 + 音频叠加
└──────────┬──────────────────────┘
           │
           ▼
gen-video/output/NIO_2026-04-04_full.mp4
gen-video/output/NIO_2026-04-04_full.srt
```

### 精华版流水线

```
analysis/NIO_2026-04-04_zh.md
    │
    ▼
┌─────────────────────────────────┐
│  video-scriptwriter agent       │  Claude 分析报告
│  (via Claude CLI)               │  → 提取 5-7 核心要点
│                                 │  → script.json (250-400字)
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  generate_tts                   │  edge-tts → audio_short.mp3
│                                 │  + timestamps.json
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  render_frames --layout short   │  Pillow → 每段一张独立画面
│                                 │  大字居中，深色背景
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  compose_video --layout short   │  MoviePy → MP4
│                                 │  逐段淡入淡出 + 音频叠加
└──────────┬──────────────────────┘
           │
           ▼
gen-video/output/NIO_2026-04-04_short.mp4
gen-video/output/NIO_2026-04-04_short.srt
```

## MCP Tools

Node.js MCP server 注册以下 5 个 tools，每个 tool 内部通过 `child_process.execFile` 调用 Python CLI。

### parse_report

解析 Markdown 报告为结构化数据。

- **输入：** `{ report_path: string }`
- **输出：** JSON — `{ ticker, company, date, rating, sections: Section[], key_sections: Section[] }`
- **Python 调用：** `python -m gv parse <report_path>`

Section 数据结构：
```typescript
interface Section {
  type: "title" | "heading" | "paragraph" | "table" | "rating_card" | "divider";
  level: number;      // 标题级别 (1-3)，非标题为 0
  text: string;       // 纯文本（供 TTS 朗读）
  raw: string;        // 原始 Markdown
  rows?: string[][];  // 表格行数据（仅 table 类型）
}
```

### generate_tts

生成语音音频和时间戳。

- **输入：** `{ text: string, voice?: string, rate?: string, output_dir: string }`
- **输出：** JSON — `{ audio_path, timestamps_path, srt_path, duration_seconds }`
- **Python 调用：** `python -m gv tts --text <text> --voice <voice> --output-dir <dir>`
- **默认音色：** `zh-CN-YunyangNeural`（新闻播报风格）
- **默认语速：** `+0%`（完整版），`+5%`（精华版）

时间戳格式：
```json
[
  { "text": "蔚来汽车", "offset_ms": 1200, "duration_ms": 800 },
  { "text": "交易分析", "offset_ms": 2000, "duration_ms": 700 }
]
```

### render_frames

将文本渲染为图片。

- **输入：** `{ sections_path: string, layout: "full" | "short", output_dir: string }`
- **输出：** JSON — `{ image_paths: string[], y_map_path?: string }`
- **Python 调用：** `python -m gv render --sections <path> --layout <layout> --output-dir <dir>`

完整版（layout=full）：输出一张 1080×N 超长图 + y_map.json（段落→Y坐标映射）。
精华版（layout=short）：输出 5-7 张独立画面（1080×1920 每张）。

### compose_video

合成最终视频。

- **输入：** `{ frames_dir: string, audio_path: string, timestamps_path: string, layout: "full" | "short", output_path: string }`
- **输出：** JSON — `{ video_path, duration_seconds }`
- **Python 调用：** `python -m gv compose --frames-dir <dir> --audio <path> --timestamps <path> --layout <layout> --output <path>`

### generate_video

一键全流程。

- **输入：** `{ report_path: string, version: "full" | "short" | "both" }`
- **输出：** JSON — `{ full_video_path?, short_video_path?, full_srt_path?, short_srt_path? }`
- **Python 调用：** `python -m gv generate <report_path> --version <version>`

## Node.js 调用 Python 的方式

```typescript
import { execFile } from "child_process";
import path from "path";

const PYTHON_DIR = path.resolve(__dirname, "../../python");

function callPython(args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(
      "python",
      ["-m", "gv", ...args],
      { cwd: PYTHON_DIR, timeout: 600_000 },  // 10 分钟超时（视频生成耗时）
      (err, stdout, stderr) => {
        if (err) reject(new Error(`Python error: ${stderr || err.message}`));
        else resolve(stdout);
      }
    );
  });
}
```

## 视频渲染规格

### 完整版（布局 A：全屏滚动）

| 参数 | 值 |
|------|-----|
| 分辨率 | 1080×1920（竖屏 9:16） |
| FPS | 30 |
| 编码 | H.264 |
| 背景色 | #0a0e27（深蓝） |
| 正文字体 | 微软雅黑 / Noto Sans CJK SC，28px |
| 标题字体 | 同上加粗，36-48px |
| 行距 | 1.8 倍 |
| 边距 | 左右 60px |

画面布局：
```
┌──────────────────────────────┐
│  TRADINGAGENTS 分析报告       │ ← 固定标题栏 (约 120px)
│  NIO · 蔚来汽车 · 2026-04-04 │
├──────────────────────────────┤
│  ┌──────────────────────┐    │
│  │ 卖出（Sell）          │    │ ← 固定评级卡片 (约 100px)
│  │ 目标价 $4.80-$5.20   │    │
│  └──────────────────────┘    │
├──────────────────────────────┤
│                              │
│  ## 投资论点                  │ ← 滚动区域 (约 1520px 可视)
│  1. 风险收益比极差...         │    根据 TTS 时间戳同步滚动
│  2. "首次GAAP盈利"无法验证... │    当前朗读段落高亮背景
│  3. 研发支出削减34%...        │
│                              │
├──────────────────────────────┤
│  ━━━━━━━━━━━━━━━━ 35%       │ ← 固定进度条 (约 40px)
│                   01:12/03:25│
└──────────────────────────────┘
```

滚动同步机制：
1. edge-tts `WordBoundary` 事件提供每个词的 `offset_ms`
2. Pillow 渲染时记录每个 Section 在长图中的 Y 坐标 → `y_map.json`
3. 将 TTS 时间戳映射到 Y 坐标：`timestamp → section_index → y_offset`
4. MoviePy 使用 `with_position(lambda t: scroll_fn(t))` 实现平滑滚动
5. 在关键点之间使用线性插值，避免跳跃

### 精华版（布局 B：逐段显现）

| 参数 | 值 |
|------|-----|
| 分辨率 | 1080×1920（竖屏 9:16） |
| FPS | 30 |
| 段落数 | 5-7 段 |
| 转场 | 淡入淡出，0.3-0.5 秒 |
| 每段停留 | = 该段 TTS 朗读时长 |

画面布局：
```
┌──────────────────────────────┐
│        TRADINGAGENTS         │ ← 固定顶部
│     蔚来汽车 NIO             │
│       [ 卖出 ]               │ ← 评级标签
├──────────────────────────────┤
│                              │
│    为何在$6.30建议卖出        │ ← 小标题
│                              │
│    风险收益比极差             │ ← 大字核心观点
│    乐观上行仅3.7%            │ ← 补充说明
│    悲观下行-17%至-37%        │
│                              │
│    ┌──────┐  ┌──────┐       │ ← 数据亮点卡片
│    │+3.7% │  │-37%  │       │
│    │ 上行  │  │ 下行  │       │
│    └──────┘  └──────┘       │
│                              │
│  ● ● ● ○ ○ ○               │ ← 进度指示器
├──────────────────────────────┤
│            01:12 / 01:25     │ ← 时间
└──────────────────────────────┘
```

## Skill 定义

`skills/gen-video/skill.md` 编排整个流程：

触发词：
- "为 NIO 报告生成视频"
- "generate video for the latest analysis"
- "把分析报告转成视频"

执行步骤：
1. 确认输入报告文件（指定路径或自动选最新的 `*_zh.md`）
2. 调用 `parse_report` 解析报告
3. 完整版：`generate_tts` → `render_frames --layout full` → `compose_video --layout full`
4. 精华版：调度 `video-scriptwriter` agent 提取脚本 → `generate_tts` → `render_frames --layout short` → `compose_video --layout short`
5. 输出视频路径

## Agent 定义

`agents/video-scriptwriter.md` — 精华版脚本撰写专用：

职责：从完整中文报告中提取 60-90 秒朗读脚本（250-400 字）。

提取规则：
1. 保留最终评级和评级结论
2. 从投资论点中选取最重要的 3 个理由（每个精简为 1-2 句话）
3. 一句话总结
4. 输出 JSON 格式，每段标注 type（rating / point / conclusion）

## TTS 配置

| 参数 | 完整版 | 精华版 |
|------|--------|--------|
| 音色 | zh-CN-YunyangNeural | zh-CN-YunyangNeural |
| 语速 | +0% | +5% |
| 输出格式 | mp3 | mp3 |
| 附加输出 | SRT 字幕 + timestamps.json | SRT 字幕 + timestamps.json |

## 输出文件

```
gen-video/output/
├── NIO_2026-04-04_full.mp4       # 完整版视频
├── NIO_2026-04-04_short.mp4      # 精华版视频
├── NIO_2026-04-04_full.srt       # 完整版字幕
└── NIO_2026-04-04_short.srt      # 精华版字幕
```

命名规则：`{TICKER}_{DATE}_{version}.{ext}`

## Python 依赖

```
edge-tts>=6.1.0
moviepy>=2.0.0
Pillow>=10.0.0
numpy>=1.24.0
```

系统依赖：
- FFmpeg（需在 PATH 中）
- Python 3.10+
- 中文字体：Windows 自带微软雅黑，Linux/macOS 需安装 Noto Sans CJK SC

## Node.js 依赖

```json
{
  "@modelcontextprotocol/sdk": "^1.12.1",
  "zod": "^3.24.0"
}
```

## 预估性能

| 指标 | 完整版 | 精华版 |
|------|--------|--------|
| 视频时长 | 8-15 分钟 | 60-90 秒 |
| 生成耗时 | 2-5 分钟 | 30-60 秒 |
| 文件大小 | 30-80 MB | 5-15 MB |
| TTS 耗时 | 30-60 秒 | 5-10 秒 |
| 渲染耗时 | 1-3 分钟 | 10-30 秒 |
