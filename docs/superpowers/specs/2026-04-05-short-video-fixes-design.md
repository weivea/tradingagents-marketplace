# Short Video V2 Bug Fixes & Content Enhancement Design

## Context

首次使用 v2 pipeline 为 NIO 报告生成短视频后发现三个问题：
1. ASS 字幕不换行，中文长句超出视频宽度
2. 视频比音频短约 3 秒，音频末尾被截断
3. slide 内容太单薄，85% 画布空间为空白

三个问题互相独立，不影响 full 版本和 legacy 兼容性。

---

## Fix 1: ASS 字幕换行

### 根因

- `_build_ass_subtitles()` 的 ASS header 设置 `WrapStyle: 0`（智能换行），依赖空格做断行点
- 中文没有空格，整句话变成一个不可断开的长行
- edge-tts 返回句子级时间戳（非逐字），单条 Dialogue 事件包含 30-45 个字

### 修复方案

1. **WrapStyle 改为 2**（不自动换行）+ 手动按字符数插入 `\N` 换行符
2. 按最大行宽（约 20 个中文字 × 42px ≈ 840px，留 120px 双侧边距）在中文标点或每 20 字处强制换行
3. 字幕居下方显示，`Alignment: 2`（底部居中）保持不变

### 修改文件

- `plugins/gv/python/composer.py` — `_build_ass_subtitles()` 函数

### 实现细节

在 `_build_ass_subtitles` 中新增 `_wrap_ass_text(text, max_chars=20)` 辅助函数：
- 遍历字符，在 `，。；：！？、` 后或满 `max_chars` 时插入 `\N`
- 保留原有的标点跳过逻辑
- `WrapStyle` 改为 `2`

---

## Fix 2: 音频截断

### 根因

xfade 转场导致视频总时长缩短。7 段视频之间有 6 次 xfade，每次 0.5s 重叠，总计损失 3s：
- 音频 77.5s，视频实际仅 74.5s
- `-shortest` 标志选取较短者 → 音频被截断

### 修复方案

1. **`_calc_slide_durations` 补偿 xfade 损失**：计算 `total_overlap = (n-1) * avg_transition_duration`，将 `total_duration + total_overlap` 作为 slide 总时长分配基数
2. **移除 `-shortest`**，改用 `-t <total_duration>` 精确控制输出时长等于音频时长
3. **修复 `tts_text` 字段传递**：当前 `_sections.json` 已包含 `tts_text`（v2 格式），但 `_calc_slide_durations` 的 fallback 逻辑在 `timestamps` 为空时直接走 equal split。确保 sections 有 `tts_text` 时优先使用字符比例分配。

### 修改文件

- `plugins/gv/python/composer.py` — `_calc_slide_durations()` 和 `_compose_short_v2()`

### 实现细节

`_calc_slide_durations` 新增参数 `xfade_total_overlap: float = 0.0`：
```
effective_duration = total_duration + xfade_total_overlap
durations = [proportion * effective_duration for each section]
```

`_compose_short_v2` 计算 overlap 后传给 `_calc_slide_durations`：
```
n_transitions = n - 1
avg_t_dur = mean of transition durations (typically 0.5s)
total_overlap = n_transitions * avg_t_dur
```

最终 FFmpeg 命令去掉 `-shortest`，加 `-t {total_duration}`。

---

## Fix 3: Slide 内容丰富化

### 根因

- 模板只支持 headline + chips + body 三层，body 限制约 30 字
- 2016px 画布上 card 仅 300px 高，85% 空白
- scriptwriter 没有输出补充说明和结构化指标

### 修复方案

**Scriptwriter 输出格式扩展**：每个 section 增加两个可选字段：
- `sub_body`: string — 2-3 句补充说明（60-100 字），24px 小字显示
- `metrics`: array of `{label, value, signal}` — 结构化指标（2-4 个），如 `{label: "RSI", value: "64", signal: "warn"}`
  - `signal` 取值: `"positive"`, `"negative"`, `"neutral"`

**模板扩展**：
- `point.html`: card 内 headline 下方增加 sub_body 段落 + metrics 网格
- `rating.html`: card 内增加 sub_body + metrics
- `conclusion.html`: 增加 sub_body
- `base.css`: 新增 `.sub-body`（24px, text-secondary, 80% opacity）和 `.metrics-grid`（2 列 grid）样式
- card padding 从 `60px 50px` 缩减为 `40px 40px`，让内容区更大

**Scriptwriter prompt 更新**：
- 放宽 body 限制到 40-60 字
- 增加 `sub_body` 字段说明（60-100 字，偏说明性，用于视觉展示不用于 TTS）
- 增加 `metrics` 字段说明（2-4 个关键指标，有 label/value/signal）

### 修改文件

- `plugins/gv/python/templates/base.css` — 新增 `.sub-body`, `.metrics-grid`, `.metric-item`, `.metric-value`, `.metric-label` 样式
- `plugins/gv/python/templates/point.html` — card 内增加 sub_body + metrics 区
- `plugins/gv/python/templates/rating.html` — card 内增加 sub_body + metrics 区
- `plugins/gv/python/templates/conclusion.html` — 增加 sub_body
- `agents/video-scriptwriter.md` — 更新输出格式、放宽限制
- `plugins/gv/python/renderer.py` — `_build_template_context()` 透传 `sub_body` 和 `metrics`

### metrics-grid CSS 设计

```css
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 24px;
}
.metric-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
  text-align: center;
}
.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}
.metric-value.positive { color: var(--rating-buy); }
.metric-value.negative { color: var(--rating-sell); }
.metric-value.neutral { color: var(--rating-hold); }
.metric-label {
  font-size: 20px;
  color: var(--text-secondary);
  margin-top: 4px;
}
```

### point.html 模板结构（修改后）

```html
<div class="point-index">{{ index }}</div>
<div class="card">
  <h2 class="headline-md">{{ headline }}</h2>
  {% if highlights %}
  <div class="highlights">...</div>
  {% endif %}
  <p class="body-text">{{ body }}</p>
  {% if sub_body %}
  <p class="sub-body">{{ sub_body }}</p>
  {% endif %}
  {% if metrics %}
  <div class="metrics-grid">
    {% for m in metrics %}
    <div class="metric-item">
      <div class="metric-value {{ m.signal }}">{{ m.value }}</div>
      <div class="metric-label">{{ m.label }}</div>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>
```

---

## 向后兼容性

- `sub_body` 和 `metrics` 字段都是可选的（`{% if ... %}`），旧格式的 sections JSON 不受影响
- `_build_template_context` 透传时使用 `.get()` 带默认值
- ASS 字幕换行是纯输出格式变化，不影响时间戳数据结构
- 时长补偿只影响 v2 路径，legacy 路径不变

## 验证

1. 用同一个 NIO 报告重新生成短视频
2. 检查字幕是否在视频宽度内正确换行
3. 检查视频时长是否与音频时长匹配（±0.5s）
4. 检查 point/rating slide 是否包含 sub_body 和 metrics
5. 运行 `python -m pytest plugins/gv/python/tests/ -v` 确保单元测试通过
