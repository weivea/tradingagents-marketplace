# Gen-Video 短视频质量全面升级设计

## 问题

通过 gen-video 管线生成的短视频被抖音平台判定为"低质量重复内容"。

根因分析：

1. **画面太静态** — 整体以静态图片 + 缓慢 Ken Burns 缩放为主，缺少元素级动画
2. **视觉模板化严重** — 每期视频配色、布局、背景完全相同，平台算法判定为批量生产
3. **内容结构千篇一律** — 固定 8 段（标题→免责→评级→3论点→结论→关注），节奏完全相同
4. **色带明显** — 8-bit H.264 编码 + 渐变背景导致色阶过渡可见

## 方案概述

- **渲染引擎**：从 Playwright 截图 + FFmpeg 拼接切换到 **Remotion**（React 逐帧渲染）
- **视觉风格**：从固定深蓝模板切换到 **动态玻璃态（Glass Morphism）+ 随机变体系统**
- **内容结构**：从固定 8 段切换到 **动态 5-10 段**（AI 根据报告内容自动决定段数和类型）
- **动画系统**：全元素级动画（数字滚动、标签飞入、卡片弹出、光斑漂移等）
- **编码质量**：10-bit H.265 + CRF 18 + 30fps，彻底消除色带

## 架构

### 管线流程

```
报告 (Markdown)
    │
    ▼
parse_report()              ← 现有 Python MCP 工具，不变
    │
    ▼
Scriptwriter Agent          ← 升级：动态结构、新增内容类型
    │
    ▼
sections JSON
    │
    ▼
generate_tts()              ← 现有 TTS 引擎，不变
    │
    ▼
audio.mp3 + timestamps.json
    │
    ▼
Python 计算段时间分配        ← 新增：sections_timing.json
    │
    ▼
Remotion Render             ← 新增：React 组件逐帧渲染
    │
    ▼
MP4 (10-bit H.265, 1080x1920, 30fps)
```

### 保留不变

- `plugins/gv/python/md_parser.py` — Markdown 解析
- `plugins/gv/python/tts_engine.py` — Edge TTS 语音合成
- MCP 工具接口签名（parse_report, generate_tts, compose_video, generate_video）
- full 版本渲染管线（MoviePy scroll）

### 新增

- `plugins/gv/remotion/` — Remotion 项目（React 组件 + 动画）
- `plugins/gv/python/composer.py` 中新增 `_compose_short_v3()` 调用 Remotion CLI
- `agents/video-scriptwriter.md` — 升级为动态结构

### 替换

- short 版本的 Playwright 截图 + FFmpeg zoompan/xfade 管线被 Remotion 完全替换

## 视觉风格：动态玻璃态

### 基础元素

- **背景**：深色渐变（`#0f172a` → `#1e1b4b` → `#172554`），角度随机
- **光斑**：3-5 个模糊光斑（`radial-gradient` + `blur(20-40px)`），Perlin noise 路径漂移
- **卡片**：毛玻璃效果（`background: rgba(255,255,255,0.08)` + `backdrop-filter: blur(20px)` + `border: 1px solid rgba(255,255,255,0.12)`）
- **噪点**：极淡 film grain 叠层（opacity 0.02-0.04），兼做 anti-banding dithering
- **色彩**：
  - 文字主色 `#f1f5f9`
  - 文字次色 `#8891b3`
  - 强调色 `#8b5cf6`（紫）/ `#3b82f6`（蓝）
  - 买入 `#4ade80`（绿）
  - 卖出 `#f87171`（红）
  - 持有 `#fbbf24`（黄）

## 随机变体系统

每期视频生成时，以 `ticker + date` 为 seed 生成确定性随机数，从以下维度随机组合：

| 维度 | 变体范围 | 说明 |
|------|---------|------|
| 色相偏移 | 基准色调 ±30° | 整体色彩感受不同 |
| 渐变方向 | [120°, 135°, 150°, 160°, 180°] | 背景渐变角度 |
| 光斑配置 | 数量 3-5、大小 60-150px、模糊 20-40px | 漂移路径由 Perlin seed 决定 |
| 排版微调 | 字重 700/800/900、圆角 16/20/24px、内边距 ±8px | 微妙但可感知的差异 |
| 转场组合 | 从 5 种中随机选 2-3 种 | 转场时长 0.4-0.8s 微调 |
| 动画时序 | 入场延迟 ±0.1s、Spring damping 10-15、stagger 0.1-0.2s | 节奏感差异 |

同一报告重复生成结果一致（确定性 seed）。不同报告视觉必然不同。

## 动画系统

### 每种幻灯片的动画编排

**Title Slide（约 5-8 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 背景渐变从黑色淡入 + 光斑开始漂移 |
| 0.3s | 网格线从中心向外扩散 (scale 0→1, opacity 0→0.06) |
| 0.6s | 装饰线从中心向两侧展开 (width 0→120px) |
| 0.9s | "今日交易研报" 标签逐字打出 (typewriter effect) |
| 1.5s | 公司名大标题从底部弹入 (spring, damping: 12) |
| 2.2s | 日期文字淡入 (opacity 0→1, 0.5s) |
| 2.8s | 下方装饰线展开 |
| 3.0s | 品牌信息淡入底部 |

**Rating Slide（约 6-10 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 页面从右侧滑入 (translateX 100%→0, spring) |
| 0.3s | "最终评级" 标签淡入 |
| 0.6s | 毛玻璃卡片从缩小弹出 (scale 0.8→1, spring) |
| 1.0s | 评级文字放大弹入 (scale 0→1, overshoot) + 颜色光晕脉冲 |
| 1.8s | highlight chips 依次飞入 (stagger 0.15s) |
| 2.5s | body 文字淡入 |
| 3.0s | metrics 网格逐个翻入 (stagger 0.2s, flip-Y) + 数字 countUp |
| 4.5s | 进度条从左向右填充 |

**Point Slide（约 8-12 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 序号圆圈弹入 (scale 0→1, bounce) |
| 0.3s | 毛玻璃卡片从底部滑入 (translateY 60px→0) |
| 0.6s | 标题文字淡入 + 左侧装饰线展开 |
| 1.0s | highlight chips 依次弹入 (stagger 0.12s) |
| 1.5s | body 正文逐行淡入 (stagger 0.1s per line) |
| 2.5s | sub_body 淡入 |
| 3.0s | metrics 卡片依次滑入 (stagger 0.2s) + 数字 countUp |
| 4.5s | 进度条更新 |

变体：奇数论点从左入场，偶数论点从右入场。

**Disclaimer Slide（约 3-4 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 页面淡入 |
| 0.3s | ⚠ 图标缩放弹入 (scale 0→1) |
| 0.6s | 标题淡入 |
| 1.0s | 免责正文淡入 (opacity, 0.5s) |
| 1.5s | 进度条填充 |

**Conclusion Slide（约 5-7 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 光斑聚拢到中心 |
| 0.5s | 装饰线从中心展开 |
| 0.8s | "结论" 标签淡入 |
| 1.2s | 结论标题从模糊到清晰 (blur 20px→0 + scale 1.1→1) |
| 2.0s | chips 淡入 |
| 2.5s | body 文字淡入 |
| 3.5s | 进度条填充到 100% |

**Follow Slide（约 3-4 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 页面淡入 |
| 0.3s | 装饰线展开 |
| 0.5s | "关注我们" 标签淡入 |
| 0.8s | 标题弹入 (spring) |
| 1.2s | chips 依次弹入 (stagger 0.15s) |
| 1.8s | body 文字淡入 |

### 新增场景类型动画

**Comparison Slide（约 8-12 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 标题淡入 |
| 0.5s | 左侧牛方卡片从左滑入 |
| 0.8s | 右侧熊方卡片从右滑入 |
| 1.2s | 牛方论点依次淡入 (stagger 0.2s) |
| 2.0s | 熊方论点依次淡入 (stagger 0.2s) |
| 3.5s | verdict 高亮闪烁 |

**DataHighlight Slide（约 5-8 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 标签淡入 |
| 0.3s | 大数字从 0 countUp 到目标值 (1.5s) |
| 1.8s | 上下文文字淡入 |
| 2.5s | 信号色光晕脉冲 |

**Catalyst Slide（约 6-10 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 标题淡入 |
| 0.5s | 时间线轴线从上到下绘制 (1s) |
| 1.0s | 第一个事件节点弹入 + 文字淡入 |
| 1.8s | 第二个事件节点弹入 |
| 2.6s | 第三个事件节点弹入 |

**Quote Slide（约 5-7 秒）：**

| 时间 | 动画 |
|------|------|
| 0.0s | 大引号 " 淡入 (scale 0.5→1) |
| 0.5s | 引用文字逐行打出 (typewriter, stagger 0.3s) |
| 2.0s | 署名淡入 |

### 页面间转场效果库

| 效果 | 描述 | 时长 |
|------|------|------|
| fade-through | 当前页淡出 + 下页淡入 | 0.5s |
| slide-left | 整页向左推出 | 0.6s |
| zoom-dissolve | 当前页放大模糊 + 下页从小到大 | 0.7s |
| wipe-up | 下页从底部擦出 | 0.5s |
| morph-blur | 双页同时模糊交叉溶解 | 0.6s |

每期从库中随机选择 2-3 种组合。

### 持续动效层（全程运行）

- **光斑漂移** — 3-5 个模糊光斑缓慢随机移动（Perlin noise 路径）
- **光斑呼吸** — 大小周期性微缩放（±10%, 3-5s 周期）
- **噪点纹理** — 极淡 film grain overlay（opacity 0.02-0.04）
- **渐变偏移** — 背景渐变角度缓慢旋转（每 20s 转 5°）

## Scriptwriter Agent 升级

### 结构变化

从固定 8 段变为动态 5-10 段：

**必选段（5 个）：**
- `title` — 标题页
- `disclaimer` — 免责声明
- `rating` — 最终评级
- `conclusion` — 结论
- `follow` — 关注引导

**动态内容段（1-5 个，AI 根据报告内容选择）：**

| 类型 | 用途 | 适用场景 |
|------|------|---------|
| `point` | 核心论点 | 通用 |
| `comparison` | 牛熊对比/多空 PK | 报告中有明显多空分歧 |
| `data-highlight` | 关键数据大字报（单个大数字 + 上下文） | 有特别突出的数据点 |
| `catalyst` | 催化剂/事件时间线 | 有近期重要事件节点 |
| `quote` | 分析师金句引用 | 分析中有特别精辟的判断 |
| `risk-matrix` | 风险概率矩阵 | 风险分析是报告重点 |

### TTS 总字数

维持 250-500 字（60-120 秒），段数增加但单段内容更聚焦。

### 新增 JSON 字段

每个 section 新增可选字段：

```json
{
  "type": "comparison",
  "headline": "多空激战",
  "bull_points": ["云增长 +32%", "AI 领先", "分红增加"],
  "bear_points": ["估值过高", "监管风险", "增速放缓"],
  "tts_text": "多空双方激烈交锋。看多方认为...",
  "verdict": "bull"
}
```

```json
{
  "type": "data-highlight",
  "headline": "营收同比增长",
  "value": "+32.7%",
  "context": "超预期 ↑ 市场预估 +28%",
  "signal": "positive",
  "tts_text": "营收同比增长百分之三十二点七，超出市场预期。"
}
```

```json
{
  "type": "catalyst",
  "headline": "近期催化剂",
  "events": [
    {"date": "4月15日", "event": "财报发布"},
    {"date": "5月1日", "event": "Build 大会"},
    {"date": "6月", "event": "反垄断裁决"}
  ],
  "tts_text": "三个关键催化剂需要关注..."
}
```

```json
{
  "type": "quote",
  "headline": "风险团队判断",
  "quote_text": "风险收益比是投资的核心，当下行远超上行时，最好的操作就是离场",
  "attribution": "风险评估团队",
  "tts_text": "风险评估团队指出..."
}
```

```json
{
  "type": "risk-matrix",
  "headline": "风险概率矩阵",
  "scenarios": [
    {"label": "乐观", "probability": "25%", "target": "$520", "return": "+18%", "signal": "positive"},
    {"label": "基准", "probability": "50%", "target": "$460", "return": "+4%", "signal": "neutral"},
    {"label": "悲观", "probability": "25%", "target": "$380", "return": "-14%", "signal": "negative"}
  ],
  "tts_text": "从风险概率矩阵来看，乐观情景概率百分之二十五..."
}
```

## Remotion 项目结构

```
plugins/gv/remotion/
├── package.json
├── tsconfig.json
├── remotion.config.ts              ← 编码参数、分辨率
├── src/
│   ├── Root.tsx                    ← Composition 入口
│   ├── ShortVideo.tsx              ← 主组件：编排所有场景
│   ├── scenes/
│   │   ├── TitleScene.tsx
│   │   ├── DisclaimerScene.tsx
│   │   ├── RatingScene.tsx
│   │   ├── PointScene.tsx
│   │   ├── ComparisonScene.tsx
│   │   ├── DataHighlightScene.tsx
│   │   ├── CatalystScene.tsx
│   │   ├── QuoteScene.tsx
│   │   ├── ConclusionScene.tsx
│   │   └── FollowScene.tsx
│   ├── components/
│   │   ├── GlassCard.tsx           ← 毛玻璃卡片
│   │   ├── FloatingOrbs.tsx        ← 漂移光斑
│   │   ├── CountUp.tsx             ← 数字滚动
│   │   ├── HighlightChip.tsx       ← 标签气泡
│   │   ├── ProgressBar.tsx         ← 进度条
│   │   ├── FilmGrain.tsx           ← 噪点纹理叠层
│   │   └── Subtitle.tsx            ← 字幕渲染（逐字高亮）
│   ├── theme/
│   │   ├── variants.ts             ← 随机变体生成器（seed-based）
│   │   ├── colors.ts               ← 色彩系统
│   │   └── transitions.ts          ← 转场效果库
│   └── utils/
│       ├── audio-sync.ts           ← TTS 时间戳 → 帧映射
│       ├── noise.ts                ← Perlin noise
│       └── seeded-random.ts        ← 确定性随机
```

## 编码参数

| 参数 | 当前值 | 新值 | 说明 |
|------|--------|------|------|
| 分辨率 | 1080×1920 | 1080×1920 | 不变 |
| FPS | 24 | 30 | 动画更流畅 |
| 编码 | H.264 8-bit | H.265 10-bit | 消除色带 |
| CRF | 未设置（默认） | 18 | 视觉无损 |
| 像素格式 | yuv420p | yuv420p10le | 10-bit 色深 |
| 音频码率 | 128k | 192k | 提升音质 |

备选方案（如遇抖音 H.265 兼容问题）：H.264 + CRF 15 高码率 + film grain dithering。

## 音频同步

1. Python `generate_tts()` 生成 `audio.mp3` + `timestamps.json`（不变）
2. Python 新增段时间分配计算：根据每段 `tts_text` 字数按比例分配时长，输出 `sections_timing.json`
3. Remotion 读取 timing，每个 Scene 通过 `useCurrentFrame()` + `interpolate()` 精确同步
4. 字幕由 Remotion `Subtitle` 组件内置渲染（逐字高亮），不再依赖 ASS 外挂字幕

## Python → Remotion 调用

`composer.py` 新增 `_compose_short_v3()`：

```python
def _compose_short_v3(sections, timestamps, audio_path, total_duration, output_path, seed):
    """Compose short video using Remotion React rendering."""
    tmp_dir = Path(output_path).parent
    
    # 1. 准备输入 JSON
    input_data = {
        "sections": sections,
        "timestamps": timestamps,
        "audioPath": audio_path,
        "totalDuration": total_duration,
        "seed": seed,
    }
    input_path = tmp_dir / "_remotion_input.json"
    write_json(input_path, input_data)
    
    # 2. 调用 Remotion CLI
    remotion_dir = Path(__file__).parent.parent / "remotion"
    cmd = [
        "npx", "remotion", "render",
        "ShortVideo",
        "--props", str(input_path),
        "--output", output_path,
        "--codec", "h265",
        "--crf", "18",
    ]
    subprocess.run(cmd, cwd=str(remotion_dir), check=True, timeout=300)
    
    # 3. 清理
    input_path.unlink(missing_ok=True)
```

MCP 工具接口签名完全不变，对外透明。

## 不在范围内

- full 版本（长视频）的渲染管线不变
- TTS 引擎不变（仍使用 Edge TTS）
- Markdown 解析器不变
- MCP 工具接口签名不变
