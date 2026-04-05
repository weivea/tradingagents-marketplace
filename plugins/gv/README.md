# gv - Gen-Video Plugin

将中文分析报告（`analysis/*_zh.md`）自动转换为带语音朗读的竖屏短视频。

## 产出

| 版本 | 时长 | 说明 |
|------|------|------|
| 完整版 `*_full.mp4` | 8-15 分钟 | 全文朗读 + 文字滚动 |
| 精华版 `*_short.mp4` | 60-90 秒 | AI 提取核心要点 + 逐段切换 |

视频规格：720x1280（竖屏 9:16），24 FPS，H.264，中文语音（zh-CN-YunyangNeural）。

## 前置条件

- Python 3.10+
- Node.js 18+
- FFmpeg（需在 PATH 中，或由 `imageio_ffmpeg` 自动提供）
- 中文字体：Windows 自带微软雅黑，Linux/macOS 需安装 Noto Sans CJK SC
- 网络连接（edge-tts 需要调用 Microsoft TTS API）

## 安装

```bash
cd plugins/gv
npm run setup    # 一键初始化（Node + TypeScript + Python 虚拟环境 + Playwright）
```

或分步执行：

```bash
npm install                # Node.js 依赖
npm run build              # 编译 TypeScript
npm run setup:python       # 创建 Python 虚拟环境（uv）+ 安装依赖 + Playwright
```

> 需要预装 [uv](https://docs.astral.sh/uv/)（Python 包管理器）和 Node.js 18+。

## 使用方式

### 方式一：Python CLI（直接使用）

在 `plugins/gv/` 目录下运行：

```bash
# 一键生成两个版本
python -m python generate "../../analysis/NIO_2026-04-04_zh.md" --version both

# 仅生成精华版（快）
python -m python generate "../../analysis/NIO_2026-04-04_zh.md" --version short

# 仅生成完整版（慢，8-15分钟报告约需30-90分钟编码）
python -m python generate "../../analysis/NIO_2026-04-04_zh.md" --version full
```

输出文件在 `gen-video/output/` 目录：

```
gen-video/output/
├── NIO_2026-04-04_full.mp4
├── NIO_2026-04-04_short.mp4
├── NIO_2026-04-04_full.srt
└── NIO_2026-04-04_short.srt
```

### 方式二：Claude Code Skill（推荐）

在 Claude Code 中直接对话：

```
为 NIO 报告生成视频
把最新的分析报告转成视频
generate video for the latest analysis
```

Skill 会自动编排整个流程，精华版还会调用 `video-scriptwriter` agent 智能提取口语化脚本。

### 方式三：MCP Tools（编程调用）

MCP server 注册了 5 个工具，可逐步调用：

| Tool | 说明 |
|------|------|
| `parse_report` | 解析 Markdown 报告为结构化 JSON |
| `generate_tts` | 生成中文语音 + 时间戳 + SRT 字幕 |
| `render_frames` | 渲染文字图片（长图或逐页幻灯片）|
| `compose_video` | 合成最终 MP4 视频 |
| `generate_video` | 一键全流程 |

## 分步命令

CLI 也支持分步调用，方便调试：

```bash
# 1. 解析报告
python -m python parse "../../analysis/NIO_2026-04-04_zh.md"

# 2. 生成语音（需要网络）
python -m python tts --text "测试文本" --output-dir "../../gen-video/temp/test"

# 3. 渲染图片
python -m python render --sections sections.json --layout full --output-dir "../../gen-video/temp/frames"

# 4. 合成视频
python -m python compose --frames-dir "../../gen-video/temp/frames/scroll.png" --audio audio.mp3 --timestamps timestamps.json --layout full --output "../../gen-video/output/test.mp4"
```

## 目录结构

```
plugins/gv/
├── src/                    # TypeScript MCP Server
│   ├── index.ts            # 入口，注册 5 个 tools
│   └── tools/
│       ├── call-python.ts  # 调用 Python 子进程
│       ├── parse.ts        # parse_report
│       ├── tts.ts          # generate_tts
│       ├── render.ts       # render_frames
│       ├── compose.ts      # compose_video
│       └── generate.ts     # generate_video
├── python/                 # Python 实现
│   ├── __main__.py         # CLI 入口
│   ├── config.py           # 配置常量（分辨率/颜色/字体）
│   ├── md_parser.py        # Markdown 解析
│   ├── tts_engine.py       # edge-tts 语音合成
│   ├── renderer.py         # Pillow 文字渲染
│   └── composer.py         # MoviePy 视频合成
├── .claude-plugin/
│   └── plugin.json         # 插件元数据
├── .mcp.json               # MCP server 注册
├── package.json
├── tsconfig.json
└── requirements.txt
```

## 技术栈

| 组件 | 技术 | 职责 |
|------|------|------|
| MCP Server | Node.js + TypeScript | 暴露 MCP tools 给 Claude |
| 语音合成 | edge-tts | 中文 TTS + 句级时间戳 |
| 画面渲染 | Pillow | 中文文字渲染为图片 |
| 视频合成 | MoviePy 2.x | 图片滚动动画 + 音频叠加 |
| 视频编码 | FFmpeg | MoviePy 底层编码器 |

## 注意事项

- **完整版编码很慢**：13 分钟的报告约需 60-90 分钟编码（受限于逐帧 numpy 裁剪），精华版通常 3-5 分钟完成
- **Windows 编码问题**：运行时建议加 `python -X utf8` 避免中文输出乱码
- **网络依赖**：edge-tts 需要联网调用 Microsoft TTS API，国内网络如果 pip 安装慢可用清华镜像 `-i https://pypi.tuna.tsinghua.edu.cn/simple`
