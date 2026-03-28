# Project Instructions

## Web Search Policy

**禁止使用内置 `WebSearch` 工具。** 所有网络搜索必须通过 Copilot CLI 完成。

当需要搜索网络信息时，使用以下 Bash 命令：

```bash
copilot -p "Search the web for: <你的搜索查询>" --allow-all-tools
```

示例：

```bash
# 搜索最新的 Python 3.13 特性
copilot -p "Search the web for: Python 3.13 new features 2026" --allow-all-tools

# 搜索某个库的文档
copilot -p "Search the web for: LangGraph documentation agent orchestration" --allow-all-tools

# 搜索错误信息
copilot -p "Search the web for: TypeError cannot unpack non-sequence NoneType Python fix" --allow-all-tools
```

规则：
- **永远不要** 调用 `WebSearch` 工具（已在 permissions 中被 deny）
- **始终** 使用 `copilot -p` 命令来执行网络搜索
- 搜索查询使用英文以获得更好的结果
- 将 copilot 返回的结果整理后呈现给用户
