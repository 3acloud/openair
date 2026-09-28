---
name: z-xkcd-panda-comic
description: 当用户要求把文章、Markdown、笔记、链接内容或一个主题做成“xkcd 风格四格漫画”“四格漫画”“金馆长熊猫表情”“金教授熊猫脸”“熊猫梗图”“文章转四格漫画”“用幽默方式解释文章核心观点”“生成黑白熊猫漫画配图”时必须使用。本 skill 会读取内容、提炼核心表达和可幽默化冲突，产出 2x2 黑白手绘四格漫画；人物默认使用金馆长熊猫表情味更浓的熊猫 meme 角色，兼容金教授熊猫脸式夸张表情，优先生成黑白手绘风格 PNG，必要时再用 SVG 或文字叠加修正中文对白。
---

# XKCD 熊猫四格漫画

把一篇文章或一个观点，改写成一张能让读者会心一笑的四格漫画。默认风格是黑白手绘、2x2 分镜、xkcd 式冷幽默结构，但人物不用火柴人，统一换成金馆长熊猫表情味更浓的熊猫 meme 角色。

## 默认目标

- 输出一张 2x2 四格漫画 PNG。
- 画面像黑白手绘漫画：黑白线稿、桌面小道具、夸张熊猫脸、中文对白、梗图感强。
- 讲清文章核心表达，优先抓“反差、误会、过度承诺、危险动作前先确认、工具突然变成管家”这类可笑点。
- 漫画适合插入公众号/Obsidian 文章正文。

## 风格锚点

优先使用本 skill 自带参考图作为风格参考：

```text
assets/reference-codex-computer-housekeeper-panda-comic.png
```

如果当前环境支持查看本地图片，先用 `view_image` 打开这张参考图，再把它作为“参考图：金馆长熊猫四格漫画风格”。若图像生成工具支持参考图输入，就使用该图作为风格参考；若只能文本生成，就把参考图特征写入 prompt：

- 黑白线稿，2x2 四格，漫画边框清晰。
- 熊猫角色带夸张真人梗图表情：憋笑、震惊、坏笑、恍然大悟。
- 每格有短对白气泡和少量 UI/桌面道具。
- 画面密度中等，有生活化桌面细节，避免纯图标信息图。
- 文字是中文，尽量短句，减少生成乱码风险。

## 质量基准

- 最终图要接近参考图的完成度：真人梗脸表情明显、熊猫身体有黑白毛发质感、桌面/电脑/报告/界面等道具丰富，整体像一张可直接发公众号的黑白漫画。
- 禁止把简单几何熊猫、流程图、小图标、低密度线框图作为最终交付。
- 每格都要有具体场景和角色互动，不能只摆几个孤立元素。
- 中文对白优先短而准；小字号界面文字可以简化，但气泡文字必须清楚可读。
- 气泡里只写自然对白，不加说话人标签，也不用“角色名：对白”这种格式。
- 气泡对白句尾不加句号，不要为了显得完整而给每句话补“。”；问号和感叹号只在确实需要表达疑问或强情绪时使用。
- 如果本地脚本生成效果达不到参考图水准，应改用图像生成工具或参考图驱动的方式重做；只有经过查看确认后才能插入文章。

## 输入处理

用户通常会给：

- Markdown 文章路径，如 `1-Wechat/ing/xxx.md`
- 一段文章全文
- 一个链接或主题
- 已经生成过的漫画，希望沉淀成固定风格

先读取或获取完整内容。对于 Markdown 文章，至少读完标题、开头、主要小标题、结尾；如果文章不长，读全文。

## 创作流程

1. 提炼一句核心表达
   - 用 1 句话说明文章真正想让读者记住什么。
   - 找出一个最适合漫画化的反差：人类预期 vs 工具实际行为、旧方法 vs 新方法、表面功能 vs 真正价值。

2. 设计四格节奏
   - 第 1 格：设定痛点或误会。
   - 第 2 格：主角尝试普通办法，暴露笨拙或荒诞。
   - 第 3 格：熊猫角色给出聪明但克制的解决动作。
   - 第 4 格：反转收束，把文章核心观点讲出来。

3. 写分镜表
   - 每格包含：画面、角色表情、对白、隐藏笑点。
   - 每个气泡控制在 12-22 个汉字内。
   - 每格最多 2 个气泡。
   - 对白要像人说话，少用说明书语言。
   - 对白直接写内容，去掉说话人称呼和冒号前缀。
   - 对白末尾默认不加句号；短句停在文字本身即可。

4. 生成图片
   - 默认调用可用的图像生成工具生成 PNG，优先追求参考图级别的黑白漫画完成度。
   - 如果系统中有 `imagegen` skill 或 `image_gen` 工具，使用它。
   - 只有在本地绘图脚本能达到参考图完成度时，才允许用脚本生成最终图；否则脚本只能用于构图草拟和文字修补。
   - 输出优先保存到文章同级资源目录：

```text
文章目录/assets/<文章slug>-panda-comic/<文章slug>-four-panel-panda-comic.png
```

   - 如果没有文章路径，保存到：

```text
output/xkcd-panda-comic/YYYY-MM-DD-主题/<主题>-four-panel-panda-comic.png
```

5. 质量检查
   - 生成后用图片查看工具检查。
   - 确认是 2x2 四格。
   - 确认角色是熊猫 meme 表情，不能变成火柴人。
   - 确认中文对白大体可读。
   - 确认第四格能落到文章核心观点。

6. 处理中文乱码
   - 如果中文明显乱码，先用更短对白重新生成一次。
   - 如果仍然乱码，保留生成图的表情和构图，同时创建 SVG/HTML/PNG 文字修正版，或在最终回复里给出可叠加的中文对白。
   - 用户明确要黑白手绘感时，优先保留生成图的梗图气质。

7. 命名与汇报口径
   - 不要把图片或文章称为试做品，也不要使用带有“还没交付完成”暗示的版本化说法。
   - 如果修过图或重做过，只说“已生成”“已修正”“已更新”，并说明最终结果。
   - 文件名使用稳定成品命名，如 `four-panel-panda-comic.png`，避免英文试验版标记。

## 图像生成 Prompt 模板

把下面模板中的方括号内容替换成当前文章信息：

```text
Use case: illustration-story
Asset type: 2x2 four-panel comic for a Chinese tech article
Primary request: Turn the article's core idea into a funny four-panel comic. Core idea: [一句核心表达]

Style/medium: black-and-white hand-drawn webcomic, xkcd-like dry humor and simple panel rhythm, but no stick figures. Use panda meme characters with a strong Chinese “金馆长熊猫表情 / 金教授熊猫脸” vibe: round panda heads, black ears, exaggerated human-like meme facial expressions, smug grin, shocked crying face, sly laugh, and sudden enlightenment.

Composition/framing: 2x2 panel grid, clear panel borders, each panel has one joke beat. Add speech bubbles with short clean Chinese text. Include small props related to the article: [道具列表].

Characters:
- Main human/user: panda at a messy desk, emotionally dramatic.
- Smart tool/agent: confident panda helper with clipboard or laptop, calm and slightly smug.
- Optional old-method foil: overdramatic panda selling scary one-click optimization.

Panel script:
1. [第一格画面和对白]
2. [第二格画面和对白]
3. [第三格画面和对白]
4. [第四格画面和对白]

Text (verbatim, Chinese; no sentence-final full stop in speech bubbles):
Title: “[短标题]”
Panel 1: “[对白 1，不带句末句号]” “[对白 2，不带句末句号]”
Panel 2: “[对白 1，不带句末句号]” “[对白 2，不带句末句号]”
Panel 3: “[对白 1，不带句末句号]” “[对白 2，不带句末句号]”
Panel 4: “[对白 1，不带句末句号]” “[对白 2，不带句末句号]”

Constraints: Chinese text should be clean and legible; speech bubbles should contain direct dialogue only, with no speaker-name prefix or name-colon format; do not add Chinese full stops “。” at the end of speech-bubble sentences; keep sentences short; black, white, and light gray only; no watermark; no logo; no photorealistic scene; no stick figures; no colorful cute cartoon; no dense paragraphs.
Avoid: malformed Chinese text, extra panels, brand logos, realistic celebrity likeness, horror, violent imagery, insulting real people.
```

## 分镜写作技巧

- 优先把文章中的“功能列表”变成角色行动，不要把列表原样塞进画面。
- 旧工具可以负责夸张和误导，新工具负责证据、流程和克制。
- 第四格最好有一句能被单独截图传播的话。
- 技术文章常见笑点：
  - “我只想清个缓存，你给我装全家桶”
  - “真正靠谱的管家，先拿证据，再动手”
  - “工具越强，越要懂得停下来等确认”
  - “开发不到 1%，已经开始管我的电脑了”

## 交付格式

完成后回复用户：

```text
老板，已生成四格漫画：
- 图片：[绝对路径]
- 风格：金馆长熊猫表情 / 黑白四格
- 核心梗：[一句话]
- 是否已插入文章：[是/否]

可插入 Markdown：
![](相对路径)
```

如果修改了 `.md` 文件且其中包含非 `r2blog.zhanglearning.com` / `r2.zhanglearning.com` 的 `http(s)` 外链图片，收尾阶段调用 `1-upload-images-to-picgo` 做图床迁移。只生成本地 PNG 并用相对路径插入时，无需迁移。

## 示例

输入：

```text
我有文章，需要生成 xkcd 风格四格漫画，人物换成金馆长熊猫表情。
文章：1-Wechat/ing/2026-06-23-Codex 是最好的电脑管家.md
```

输出思路：

```text
核心梗：传统电脑管家先吓人，Codex 先查证、列风险、等确认。

四格：
1. 老板电脑空间红了，传统管家跳出来喊“99999 个风险，先装全家桶”。
2. 老板让 Codex 清理 uv 缓存，Codex 先统计目录和运行任务。
3. Codex 递出清理报告：可删 2.5GiB，危险动作等确认。
4. Codex 展示卸载残留、启动项、大文件、巡检，老板感叹“我只开发了不到 1%”。
```
