---
name: mbti-test
version: 1.2.0
description: 引导用户完成 MBTI 十六型人格测试，并解读测试结果与人格类型。在用户要求 MBTI 测试、性格测试、十六型人格、测 MBTI、/mbti-test，或询问 INTJ/ENFP 等人格类型时使用。
---

# MBTI 十六型人格测试

> Skill 标识：`mbti-test`　·　版本：`1.2.0`　·　命令：`/mbti-test`  
> 题卷与报告：**内置** `data/decks/` + `data/results/`  
> **零依赖：** 无需 Node；Agent 用 Read 读取预生成题卷并按 reference 计分。

在对话中完成 **标准 MBTI 四维度十六型** 测试并生成中文报告。

## 用户能力（意图不明时先展示）

Read [references/user-menu.md](references/user-menu.md) 开场菜单。能力摘要：

| 功能 | 用户怎么说 |
|------|-----------|
| 快测 28 题 | `28` / `快测` |
| 标准 93 题 | `93` / `标准`（推荐） |
| 完整 200 题 | `200` / `完整` |
| 查类型 | `解读 INFJ` |
| 对比 | `INFJ 和 INFP 区别` |
| 16 型一览 | `有哪些类型` |

## 架构（强制顺序）

```text
菜单(可选) → 选题量 → Read 题卷 → 逐批出题 → 收齐答案 → 计分 → 分层报告
```

题卷映射：`quick-28` · `standard-93` · `full-200`（见 [references/data-format.md](references/data-format.md)）。

## 进度清单

- [ ] **0. 数据自检** — Read [references/runtime.md](references/runtime.md)
- [ ] **1. 确认模式** — 菜单 / 测试 / 查型 / 对比 / 一览 → [references/session-flow.md](references/session-flow.md)
- [ ] **2. 选题量** — 未说明时展示 [user-menu.md](references/user-menu.md)；已说明则跳过
- [ ] **3. 加载题卷** — Read `data/decks/<deck>.json`；**禁止**运行时 shuffle
- [ ] **4. 逐批出题** — 每批 5 题；答题格式见 session-flow（支持 `A B A` 简写、大小写不敏感）
- [ ] **5. 收齐答案** — 未答完禁止计分
- [ ] **6. 计分** — [references/scoring.md](references/scoring.md)
- [ ] **7. 分层报告** — L1 默认 / L2 详细 / L3 完整；边界维度与快测 disclaimer → [references/result-format.md](references/result-format.md)

## 出题格式（硬规则）

```markdown
### 第 1 批（1–5 / 28） · 进度 5/28

**1.** 当你要外出一整天，你会
- A. 计划你要做什么和在什么时候做
- B. 说去就去

回复方式（任选）：`A B A B A` · `1A 2B 3A` · 大小写均可
```

## 计分要点

- 选 A → `options[0].characterType`；选 B → `options[1].characterType`
- 四组：`E≥I→E`，`S≥N→S`，`T≥F→T`，`J≥P→J`（**相等取左**）

## 边界

| 属于本 skill | 不属于本 skill |
|--------------|----------------|
| 标准 MBTI 16 型 | SBTI 十五维测试 |
| 28 / 93 / 200 题卷 | 宠物 MBTI、临床诊断 |

## 附加资源

- [references/user-menu.md](references/user-menu.md) — 开场菜单
- [references/session-flow.md](references/session-flow.md) — 流程、答题、续测
- [references/result-format.md](references/result-format.md) — L1/L2/L3、边界提示
- [references/type-compare.md](references/type-compare.md) — 类型对比
- [references/types-overview.md](references/types-overview.md) — 16 型一览
- [references/data-format.md](references/data-format.md) — 数据结构
- [references/scoring.md](references/scoring.md) — 计分
- [references/runtime.md](references/runtime.md) — 自检
