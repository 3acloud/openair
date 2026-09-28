# 运行时

本 skill **零外部依赖**：Agent 用 Read 读取 `data/decks/` 与 `data/results/` 即可。

## 自检

确认以下文件存在：

- `data/decks/quick-28.json`
- `data/decks/standard-93.json`
- `data/decks/full-200.json`
- `data/types-index.json`
- `data/results/` 下 16 个 `.md`

任一缺失 → skill 包不完整，不得开始出题。

## 数据格式

见 [data-format.md](data-format.md)。
