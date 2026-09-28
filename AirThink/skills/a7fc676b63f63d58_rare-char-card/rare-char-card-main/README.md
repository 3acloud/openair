# rare-char-card 生僻字卡片生成器

生成「每日一组生僻字」风格的小红书科普卡片图（1080×1440，3:4）。

**纯代码渲染**：HTML/CSS 模板 + Chrome 无头截图，零 pip/npm 依赖，装饰元素全部为内联 SVG。

## 效果预览

| 风格 | 视觉 | 心理锚点示例 |
|---|---|---|
| `magnolia-blue` | 深蓝底 + 金字 + 玉兰花枝飘瓣 | 努力不被看见 |
| `magnolia-sage` | 灰绿底 + 米白字 + 玉兰枝 | 安静被误解 |
| `fan-orange` | 暖橙底 + 米色纸面板 + 折扇 | 情绪低谷 |
| `wave-beige` | 米色底 + 抽象色块 + 波浪 | 被现实压住仍想飞 |

## 快速开始

```bash
# JSON 数据驱动
python3 scripts/render.py --data assets/samples/yu.json \
  --style magnolia-blue --out card.png

# 命令行内联
python3 scripts/render.py --char 彧 --pinyin yù \
  --homophone "同「玉」，文采斐然" \
  --meaning "趣味高雅，谈吐文雅有教养的样子" \
  --copy "不爱表现的人" --copy "常常被误以为平庸" \
  --style fan-orange --out card.png

# 自定义背景图（图片模型生成背景 + 白字遮罩）
python3 scripts/render.py --data data.json --bg background.png \
  --overlay 0.35 --out card.png
```

要求：本机装有 Chrome / Chromium / Edge（自动探测）。

## 卡片结构

```
[可选标题]
拼音（衬线大字）
生 僻 字（超大衬线主体）
【谐音】同音常见字
【释义】一句话解释
情感文案 3~5 行（金句）
互动语（快试试你手机能打出来吗）
```

## 文案心法

字只是钩子，**情绪才是内容**。爆款逻辑 = 谐音破冰 → 心理共鸣 → 温柔肯定。

- 一张卡片只瞄准**一种**具体心理状态（努力不被看见 / 安静被误解 / 情绪低谷 / 内耗 / 讨好型人格 / 孤独不合群……）
- 三段式：第一行戳痛点 → 中间用字义翻转定义 → 收尾温柔留白，不说教
- 详见 `references/styles.md`（含 20 个高频生僻字释义速查表）

## 目录结构

```
├── SKILL.md              # Agent skill 定义（WorkBuddy / Claude 等可直接使用）
├── scripts/render.py     # 渲染脚本
├── templates/card.html   # 4 风格合一 HTML 模板
├── references/styles.md  # 风格速查 + 生僻字表 + 文案范例
└── assets/samples/       # 样例数据
```

## License

MIT
