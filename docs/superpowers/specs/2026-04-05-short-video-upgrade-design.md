# Short Video Upgrade Design

> Gen-video short 版本全面升级：视觉设计、内容结构、动效节奏三维度提升至抖音/TikTok 级别。

**日期:** 2026-04-05
**状态:** 设计中
**影响范围:** Short 版本渲染和合成管线（Full 版本不变）

---

## 1. 问题诊断

当前 short 版本（60-90s 短视频）存在三个核心问题：

| 维度 | 现状 | 问题 |
|------|------|------|
| 视觉设计 | 纯文字居中 + 深蓝纯色背景，无装饰元素 | 像 teleprompter，不像短视频 |
| 内容结构 | 7 张 slide 用同一模板（除 rating_card） | 无差异化版式，信息层次扁平 |
| 动效节奏 | 0.4s crossfade 切换，slide 内完全静止 | 像幻灯片，缺乏短视频的动感和节奏 |

**目标:** 做出抖音/TikTok 级别的金融科技风格短视频。

---

## 2. 技术方案

### 2.1 方案选型

**选定方案：HTML/CSS 渲染 + FFmpeg 动效**

| 组件 | 旧方案 | 新方案 |
|------|--------|--------|
| Slide 渲染 | Pillow (`ImageDraw.text`) | HTML/CSS + Playwright 截图 |
| 视频合成 | MoviePy (`concatenate_videoclips`) | FFmpeg filter (xfade + zoompan) |
| 模板系统 | 无（硬编码绘图逻辑） | Jinja2 HTML 模板 |
| 字幕 | 无 | FFmpeg ASS 字幕（逐字高亮） |

**选型理由：**
- HTML/CSS 天然擅长排版（渐变、圆角、阴影、弹性布局），比 Pillow 手写坐标效率高 10 倍
- FFmpeg filter 覆盖了短视频 90% 的过渡效果需求，不需要引入重量级视频框架
- Jinja2 模板系统让新增 slide 类型只需加一个 HTML 文件
- 只改 short 版本内部实现，MCP 接口和 full 版本完全不变

---

## 3. 内容结构重构

### 3.1 Scriptwriter 升级

video-scriptwriter agent 从"文本提取器"升级为"短视频文案创作者"：

| 维度 | 旧行为 | 新行为 |
|------|--------|--------|
| headline | 直接用原文段落标题 | 重新提炼冲击力标题（如"研发支出削减34%"→"研发砍了三分之一，以未来换短期？"） |
| body | 压缩原文段落 | 口语化重写，保留关键数据，适合短视频传播 |
| 数字高亮 | 无 | 自动识别值得高亮的关键数字/百分比 |
| 语气 | 偏书面报告 | 抖音风格——简短、有力、制造好奇 |

### 3.2 新的输出格式

scriptwriter 的 JSON 输出从扁平文本升级为结构化数据：

```json
[
  {
    "type": "title",
    "headline": "蔚来汽车 NIO",
    "body": "AI交易分析报告 · 2026年4月4日",
    "tts_text": "蔚来汽车交易分析报告，2026年4月4日。"
  },
  {
    "type": "disclaimer",
    "headline": "免责声明",
    "body": "本报告由AI生成，仅供研究参考，不构成投资建议。",
    "tts_text": "免责声明：本报告由AI生成，仅供研究参考。"
  },
  {
    "type": "rating",
    "headline": "卖出",
    "body": "目标价 $4.80-$5.20，下行 17-24%",
    "highlights": ["$4.80-$5.20", "-17%~-24%"],
    "tts_text": "最终评级：卖出。目标价4.80到5.20美元，下行空间17到24个百分点。"
  },
  {
    "type": "point",
    "index": 1,
    "headline": "风险收益比极差",
    "body": "乐观上行仅3.7%，悲观下行-37%，不值得博",
    "highlights": ["+3.7%", "-37%"],
    "tts_text": "风险收益比极差。乐观情况下上行仅百分之三点七，悲观下行高达百分之三十七。"
  },
  {
    "type": "point",
    "index": 2,
    "headline": "盈利真实性存疑",
    "body": "首次GAAP盈利无法验证，可能含一次性项目",
    "highlights": ["GAAP"],
    "tts_text": "首次GAAP盈利无法验证，可能包含一次性项目，不应过度解读。"
  },
  {
    "type": "point",
    "index": 3,
    "headline": "研发砍了三分之一",
    "body": "竞争对手纷纷加大投入，NIO却选择削减，以未来换短期",
    "highlights": ["-34%"],
    "tts_text": "研发支出削减百分之三十四，竞争对手纷纷加大研发投入，蔚来却选择了削减。"
  },
  {
    "type": "conclusion",
    "headline": "趁强势卖出",
    "body": "等回调至$5区间重新评估",
    "highlights": ["$5"],
    "tts_text": "结论：趁强势卖出，等回调至5美元区间再重新评估。"
  }
]
```

**关键设计决策：**
- `tts_text` 和视觉文本（headline + body）分离——TTS 需要连贯的朗读文本，视觉需要冲击力标题
- `highlights` 数组标识需要在视觉上高亮的数字/关键词
- `index` 字段仅 point 类型有，用于显示编号
- 总 tts_text 仍控制在 250-400 字，朗读 60-90 秒

---

## 4. 视觉设计系统

### 4.1 设计风格

**金融科技感 + 抖音动感：** 深色渐变背景 + 半透明磨砂卡片 + 渐变色高亮 + 清晰的信息层次。

### 4.2 每种 Slide Type 的版式设计

#### title slide
```
┌───────────────────────────┐
│                           │
│      ╔═══════════════╗    │  ← 几何装饰线条
│      ║               ║    │
│      ║  蔚来汽车 NIO ║    │  ← headline (36px bold, 白色)
│      ║               ║    │
│      ║  AI交易分析报告║    │  ← body (18px, 灰白)
│      ║  2026.04.04   ║    │
│      ╚═══════════════╝    │
│                           │
│                           │
│   NIO · AI Trading Report │  ← 底部品牌栏
└───────────────────────────┘
```
- 背景：深色径向渐变 + 微妙的网格纹理
- 中央区域有装饰性几何线条/光效

#### disclaimer slide
```
┌───────────────────────────┐
│                           │
│                           │
│      ⚠ 免责声明          │  ← headline (20px, 半透明白)
│                           │
│      本报告由AI生成，     │  ← body (16px, 40%透明度)
│      仅供研究参考，       │
│      不构成投资建议。     │
│                           │
│                           │
│   ❶━━○○○○○             │  ← 进度条
│   NIO · 2026.04.04       │
└───────────────────────────┘
```
- 视觉权重最低——弱化处理
- 快速过渡（停留时间短）

#### rating slide
```
┌───────────────────────────┐
│                           │
│      最终评级             │  ← label (16px, 灰色)
│                           │
│   ┌───────────────────┐   │
│   │                   │   │  ← 渐变色卡片
│   │      卖 出        │   │  ← headline (48px bold, 红色渐变)
│   │                   │   │
│   │  $4.80 - $5.20    │   │  ← 目标价 (24px, 高亮)
│   │  ▼ 17% ~ 24%     │   │  ← 下行空间 (红色)
│   │                   │   │
│   └───────────────────┘   │
│                           │
│   ❷━━━○○○○             │
│   NIO · 2026.04.04       │
└───────────────────────────┘
```
- 评级文字用大号加粗 + 颜色渐变
- 目标价和涨跌幅独立展示，有方向箭头
- 红色(卖出/减持) / 绿色(买入/增持) / 黄色(持有)

#### point slide
```
┌───────────────────────────┐
│                           │
│   ❶                      │  ← 编号圆圈 (渐变紫)
│                           │
│   ┌───────────────────┐   │
│   │                   │   │  ← 半透明磨砂卡片
│   │  风险收益比极差    │   │  ← headline (28px bold, 白色)
│   │                   │   │
│   │  ┌──────┐┌──────┐ │   │  ← 数字高亮块
│   │  │+3.7% ││ -37% │ │   │    (渐变色块, 大字)
│   │  │ 上行 ││ 下行 │ │   │
│   │  └──────┘└──────┘ │   │
│   │                   │   │
│   │  乐观上行仅3.7%， │   │  ← body (16px, 灰白)
│   │  悲观下行-37%，   │   │
│   │  不值得博         │   │
│   └───────────────────┘   │
│                           │
│   ❸━━━━━━○○             │
│   NIO · 2026.04.04       │
└───────────────────────────┘
```
- 编号圆圈标识第几个论点
- headline 大字突出核心论点
- highlights 数字用渐变色块单独展示
- body 补充说明

#### conclusion slide
```
┌───────────────────────────┐
│                           │
│      ━━━━━━━━━━━━        │  ← 装饰分割线
│                           │
│      结论                 │  ← label (16px)
│                           │
│      趁强势卖出           │  ← headline (32px bold)
│                           │
│      等回调至 $5          │  ← body (20px)
│      区间重新评估         │
│                           │
│      ━━━━━━━━━━━━        │  ← 装饰分割线
│                           │
│   ❼━━━━━━━━━━━━━        │
│   NIO · 2026.04.04       │
└───────────────────────────┘
```
- 装饰线条收束感
- 渐变背景收尾（比其他 slide 颜色更深/更暖）
- 可以加"完整报告见..."引导

### 4.3 共享设计元素

| 元素 | 实现 |
|------|------|
| 背景 | CSS 线性/径向渐变，从 `#0a0e27` 到 `#141833`，每种 type 色调微调 |
| 磨砂卡片 | `backdrop-filter: blur(20px)` + `background: rgba(255,255,255,0.05)` + `border-radius: 16px` |
| 进度指示器 | 编号 + 进度条（CSS），当前位置高亮 |
| 品牌栏 | 底部固定，ticker + 日期，小号灰色 |
| 字体 | Noto Sans CJK SC（确保跨平台一致性，不依赖 msyh） |
| 高亮色块 | CSS 渐变背景的 inline-block，`border-radius: 8px` |

### 4.4 配色系统

```
--bg-primary:    #0a0e27    (深蓝背景)
--bg-secondary:  #141833    (稍浅背景)
--text-primary:  #e8ecff    (主文字，高亮白)
--text-secondary:#8891b3    (辅助文字，灰蓝)
--accent-purple: #646cff    (强调紫)
--accent-blue:   #3b82f6    (强调蓝)
--rating-sell:   #ff4444    (卖出红)
--rating-buy:    #4ade80    (买入绿)
--rating-hold:   #fbbf24    (持有黄)
--card-bg:       rgba(255,255,255,0.05)  (卡片背景)
--card-border:   rgba(255,255,255,0.08)  (卡片边框)
```

---

## 5. 动效与节奏系统

### 5.1 三层动效

#### 层级 1：Slide 过渡（FFmpeg xfade filter）

| 过渡类型 | FFmpeg transition | 时长 | 应用场景 |
|----------|-------------------|------|----------|
| 淡入 | `fade` | 1.0s | title 入场 |
| 左滑 | `slideleft` | 0.5s | point → point |
| 缩放入 | `zoomin` | 0.8s | rating 入场 |
| 向上擦除 | `wipeup` | 0.8s | conclusion 收尾 |
| 淡出 | `fadeblack` | 0.5s | disclaimer |

#### 层级 2：Slide 内微动效（FFmpeg zoompan filter）

每张 slide 展示期间不是静止的，而是有微妙的缓慢运动（Ken Burns 效果）：

```
zoompan=z='1.0+0.0003*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=fps*duration:s=1080x1920:fps=24
```

- 缩放范围：1.00x → 1.03x（3% zoom，12秒内几乎不察觉但画面"活"的）
- 不同 slide 可以有不同的运动方向（zoom in / zoom out / 平移）
- 需要将 slide 渲染为比 1080x1920 稍大的图（如 1134x2016，多出 5%），给 zoom/pan 留空间

#### 层级 3：字幕同步（FFmpeg ASS 字幕）

利用 edge-tts 的 word-level timestamps 生成 ASS 字幕：

```ass
[V4+ Styles]
Style: Default,Noto Sans CJK SC,24,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,20,20,40,1
Style: Highlight,Noto Sans CJK SC,24,&H0000D4FF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,0,2,20,20,40,1

[Events]
Dialogue: 0,0:00:01.20,0:00:02.00,Highlight,,0,0,0,,蔚来汽车
Dialogue: 0,0:00:01.20,0:00:02.00,Default,,0,0,0,,蔚来汽车
```

- 字幕位置：视频底部 1/4 处
- 当前朗读词高亮（白色→黄色/金色）
- 半透明黑色底条保证可读性

### 5.2 节奏分配

**关键改变：** slide 时长不再平均分配，而是根据每段 `tts_text` 的实际朗读时长确定。

实现方式：
1. TTS 生成后得到 timestamps.json（word-level）
2. 根据 scriptwriter 输出的每段 tts_text，在 timestamps.json 中定位起止时间
3. 每张 slide 的展示时长 = 对应 tts_text 的朗读时长 + 过渡时间的一半

| Slide | 预估时长 | 过渡效果 | 内动效 |
|-------|---------|---------|--------|
| title | 8-10s | fade in (1.0s) | 缓慢 zoom in |
| disclaimer | 4-5s | fadeblack (0.5s) | 静止 |
| rating | 10-12s | zoomin (0.8s) | 微微 zoom out |
| point 1 | 10-12s | slideleft (0.5s) | Ken Burns 右移 |
| point 2 | 10-12s | slideleft (0.5s) | Ken Burns 左移 |
| point 3 | 10-12s | slideleft (0.5s) | Ken Burns zoom in |
| conclusion | 8-10s | wipeup (0.8s) | 缓慢 zoom in |

---

## 6. 架构改造

### 6.1 改动范围

| 文件 | 改动程度 | 说明 |
|------|---------|------|
| `plugins/gv/python/renderer.py` | 重写 `_render_short()` | Pillow → Playwright 截图 |
| `plugins/gv/python/composer.py` | 重写 `_compose_short()` | MoviePy → FFmpeg 直接调用 |
| `plugins/gv/python/config.py` | 新增配置 | HTML 模板路径、过渡效果映射、Ken Burns 参数 |
| `plugins/gv/python/templates/` | 新增目录 | 6 个 HTML 模板 + 1 个共享 CSS |
| `agents/video-scriptwriter.md` | 升级 | 输出格式从扁平文本升级为结构化 JSON |
| `plugins/gv/python/__main__.py` | 微调 | 新增 Playwright 初始化/清理 |

**不变的部分：**
| 文件 | 状态 |
|------|------|
| `plugins/gv/python/md_parser.py` | 不变 |
| `plugins/gv/python/tts_engine.py` | 不变 |
| `plugins/gv/src/**` (所有 TypeScript) | 不变（MCP 接口不变） |
| `skills/gen-video/skill.md` | 不变（编排流程不变） |
| Full 版本的渲染和合成 | 不变 |

### 6.2 新增依赖

| 依赖 | 用途 | 安装 |
|------|------|------|
| `playwright` | HTML 截图 | `pip install playwright && playwright install chromium` |
| `jinja2` | HTML 模板渲染 | `pip install jinja2` |

**移除依赖（short 版本）：** MoviePy 不再用于 short 版本合成，改为 FFmpeg 直接调用。但 full 版本仍依赖 MoviePy，所以不从 requirements 中移除。

### 6.3 模板目录结构

```
plugins/gv/python/templates/
├── base.css              ← 共享样式
├── title.html            ← 标题 slide 模板
├── disclaimer.html       ← 免责声明模板
├── rating.html           ← 评级模板
├── point.html            ← 论点模板
└── conclusion.html       ← 结论模板
```

每个 HTML 模板是自包含的（内联 CSS 或 link 到 base.css），接受 Jinja2 变量填充。

### 6.4 渲染流程（新）

```
scriptwriter JSON
       │
       ▼
  Jinja2 渲染 HTML（按 type 选模板）
       │
       ▼
  Playwright 截图 1134×2016 PNG（多 5% 给 Ken Burns 留空间）
       │
       ▼
  FFmpeg zoompan（逐张生成带微动效的 .mp4 片段）
       │
       ▼
  FFmpeg xfade（串联所有片段 + 过渡效果）
       │
       ▼
  FFmpeg 叠加 ASS 字幕 + 混入音频
       │
       ▼
  最终 .mp4 输出
```

### 6.5 向后兼容

- MCP 工具接口完全不变：`render_frames(sections_path, layout, output_dir)` 和 `compose_video(...)` 的参数签名不变
- `sections_path` 的 JSON 格式需要兼容旧格式（type + text）和新格式（type + headline + body + ...）
- Full 版本的 `_render_full()` 和 `_compose_full()` 完全不动
- `generate_video` one-click 工具不变，内部会走新的 short 管线

---

## 7. Scriptwriter Agent 升级

### 7.1 角色转变

从"报告内容提取器"升级为"短视频文案创作者"。

### 7.2 新的指令要点

- **headline 创作：** 不要照搬原文标题，要重新提炼有冲击力的短句（如问句、反转句）
- **body 重写：** 用口语化方式重写，保留关键数据但更有说服力
- **highlights 提取：** 自动识别最具冲击力的 1-2 个数字/百分比
- **tts_text 独立：** 为朗读优化的连贯文本，避免特殊符号和缩写
- **总字数控制：** 所有 tts_text 合计 250-400 字

### 7.3 输出校验

renderer 需要对 scriptwriter 的输出做基础校验：
- 每个 section 必须有 type、headline、tts_text
- type 必须是 title/disclaimer/rating/point/conclusion 之一
- highlights 是可选的字符串数组
- index 仅 point 类型需要

---

## 8. 测试策略

### 8.1 单元测试

- HTML 模板渲染：验证每种 type 的模板能正确填充数据
- ASS 字幕生成：验证 timestamps 到 ASS 格式的转换正确性
- FFmpeg 命令构建：验证生成的 FFmpeg 命令参数正确

### 8.2 集成测试

- 用现有 NIO 报告跑完整 short 版本管线，对比新旧输出
- 验证 MCP 工具接口向后兼容（旧格式 sections JSON 仍能工作）

### 8.3 视觉验收

- 人工审查每种 slide type 的截图质量
- 人工审查视频过渡效果和字幕同步

---

## 9. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Playwright 安装 chromium 失败（网络/权限） | 无法渲染 | 提供 fallback 到 Pillow 旧方案 |
| FFmpeg filter 复杂度高，调试困难 | 开发效率低 | 逐步构建：先做基础过渡，再加 Ken Burns，最后加字幕 |
| 字体在 Playwright 中渲染不一致 | 视觉效果差 | 使用 Google Noto Sans CJK SC，确保字体文件内置 |
| Scriptwriter 输出格式不稳定 | 渲染失败 | 严格 JSON schema 校验 + fallback 到基础文本 |
| Ken Burns 需要 oversized 图片 | 多 5% 渲染量 | 影响很小，可接受 |

---

## 10. 不做的事情（YAGNI）

- 不改 full 版本的渲染/合成
- 不做视频模板选择功能（只做一套高质量模板）
- 不做自定义配色/品牌定制（硬编码一套好看的即可）
- 不引入背景音乐（后续可考虑，但不在本次范围内）
- 不做 Remotion 级别的逐帧动画（FFmpeg filter 够用）
