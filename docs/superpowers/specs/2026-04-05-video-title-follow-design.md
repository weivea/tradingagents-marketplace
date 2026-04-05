# Short & Full Video: Title Standardization + Follow CTA Slide

## Context

用户希望短视频和长视频统一以「今日交易研报之<公司名>」开头，增强品牌识别度。同时在短视频末尾增加「关注」页，引导观众关注账号。

---

## Change 1: 统一开场标题

### 短视频

- `video-scriptwriter.md` 的 title slide:
  - `headline`: 固定格式 `今日交易研报之<公司名>`（例：`今日交易研报之快手科技`）
  - `body`: 保持日期信息，如 `2026年4月4日`
  - `tts_text`: `今日交易研报之<公司名>，<日期>。`（例：`今日交易研报之快手科技，2026年4月4日。`）
- 同步更新 JSON 示例中的 title 对象

### 长视频

- 在 gen-video skill (`skills/gen-video/skill.md`) 的 Step 3 中，描述 TTS 文本拼接时在最前面插入开场白：`今日交易研报之<公司名>。`
- 不修改 renderer/composer 底层代码，仅在 skill 编排层处理

---

## Change 2: 短视频增加「关注」结尾页

### 新模板 `follow.html`

- 风格与 `conclusion.html` 一致（居中布局、装饰线）
- 内容区域：
  - headline: `关注我们`
  - body: `获取更详细的分析报告`
  - highlights 标签: 3 个亮点 chip（例：`每日更新`, `深度分析`, `AI驱动`）
- 底部 progress bar 固定 100%
- 底部 brand bar 显示 ticker + date

### Scriptwriter 输出格式更新

- 结构从 **7 sections** 改为 **8 sections**：title → disclaimer → rating → point ×3 → conclusion → follow
- 新增 `follow` type 定义
- `tts_text`: `感谢收看，关注账号获取每日深度交易分析。`（约 15-20 字，增加约 3-4 秒朗读）
- follow slide 的 `highlights` 固定为 `["每日更新", "深度分析", "AI驱动"]`
- follow slide 不需要 `sub_body` 或 `metrics`

### Config 更新

- `plugins/gv/python/config.py`:
  - `SHORT_V2_TRANSITIONS` 增加 `"follow"` 条目（fade 过渡，0.5s）
  - `SHORT_V2_KENBURNS` 增加 `"follow"` 条目（static，1.0 → 1.0）

---

## 修改文件清单

| 文件 | 变更 |
|------|------|
| `agents/video-scriptwriter.md` | title headline 格式改为「今日交易研报之<公司名>」；结构从 7 → 8 sections；增加 follow type 定义和示例 |
| `plugins/gv/python/templates/follow.html` | 新建——关注引导 slide 模板 |
| `plugins/gv/python/config.py` | `SHORT_V2_TRANSITIONS` 和 `SHORT_V2_KENBURNS` 增加 `follow` 条目 |
| `skills/gen-video/skill.md` | Step 3 (full) 和 Step 4 (short) 增加开场白拼接说明 |

---

## 向后兼容

- 旧的 7-section JSON 仍可正常渲染，`follow.html` 只在 `type: "follow"` 时加载
- `_build_template_context` 已支持所有通用字段，无需修改 renderer.py
- 长视频仅在 skill 编排层插入 TTS 开场白，不改 composer/renderer 底层
- `follow.html` 用 `{% if highlights %}` 保持可选性

## 验证

1. 生成一个短视频，检查：
   - 第一页 headline 显示「今日交易研报之<公司名>」
   - TTS 以此开头
   - 最后一页为关注引导页，有亮点标签
   - 总计 8 个 slide
2. 生成一个长视频（或检查 TTS 文本），确认开头有「今日交易研报之<公司名>」
3. 运行 `python -m pytest plugins/gv/python/tests/ -v` 确保单元测试通过
