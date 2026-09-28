# 数据格式

题库、题卷与报告均为 **JSON / Markdown**，Agent 用 Read 直接读取，**无需 Node**。

## 文件清单

| 路径 | 说明 |
|------|------|
| `data/decks/quick-28.json` | 28 题快测卷（预生成） |
| `data/decks/standard-93.json` | 93 题标准卷 |
| `data/decks/full-200.json` | 200 题完整卷 |
| `data/questions-93.json` | 原始题库（维护用） |
| `data/questions-200.json` | 原始题库（维护用） |
| `data/types-index.json` | 16 型索引：`typeName`、`tagline`、`file` |
| `data/results/<TYPE>.md` | 各类型中文报告 |

## 题卷 JSON 结构

```json
{
  "deckId": "quick-28",
  "testCount": 28,
  "source": "questions-93.json",
  "seed": 20260917,
  "questions": [ { "id": 1, "text": "…", "options": […] } ]
}
```

测试时 **只 Read 题卷**，使用其中的 `questions` 数组，不要读原始题库再 shuffle。

## 题目字段

```json
{
  "id": 1,
  "text": "当你要外出一整天，你会",
  "options": [
    { "code": "A", "text": "…", "characterType": "J" },
    { "code": "B", "text": "…", "characterType": "P" }
  ]
}
```

## 题卷映射

| 用户选择 | 文件 |
|----------|------|
| 28 / 快测 | `data/decks/quick-28.json` |
| 93 / 标准 | `data/decks/standard-93.json` |
| 200 / 完整 | `data/decks/full-200.json` |

## 维护

重新生成题卷（改题库后）：`node scripts/build-decks.mjs`  
清洗报告 MD：`node scripts/clean-results.mjs`
