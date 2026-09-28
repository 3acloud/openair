# 题目打乱（已废弃）

v1.2.0 起使用 **预生成题卷**（`data/decks/*.json`），Agent **禁止**在运行时 shuffle。

题卷由维护脚本 `scripts/build-decks.mjs` 离线生成；`seed` 与 `deckId` 仅用于续测时定位同一卷。

历史算法（mulberry32 + Fisher-Yates）见 git 历史 v1.1.0。
