---
name: "whiteboard-animation-maker"
description: "把一个概念、一份写好的口播稿，或一条要对标的社媒视频，变成 1080×1920 竖屏白板手绘讲解片（白底黑线）。这个白板动画制作工具支持汉字与英文单词逐笔手绘、流程卡片等多种画面，支持口播配音与声音克隆，还能先读取小红书、抖音、TikTok、YouTube、Instagram 或 X 上的对标视频再拆解结构。适用于白板动画、手绘讲解视频、手绘视频、概念科普、什么是 X、口播配音等需求。"
---

# 白板动画制作

每次只做一条竖屏白板片：1080×1920，白底黑线手绘，一个声音口播。输入是一个概念、一份写好的口播稿，或一条要对标的视频。一条片子只用一种模式。本包在本地成片，不负责发布。

`$SKILL` 是本 `SKILL.md` 所在目录。脚本、模板和文案规则都在这里。

**本连接上的 Beatra MCP 是口播合成、声音克隆和对标社媒读取的唯一接口。** 不要改用其他 TTS 或克隆服务，不要让用户自己去下载对标视频，也不要通过 REST、无头浏览器或其他 skill 去抓社媒。每一个远程 Beatra 工具都只通过随包 `scripts/mcp_client.py` 调用。宿主 Agent 不得配置或调用宿主 Beatra Connector，也不得使用 REST/OpenAPI 作为降级。

## 适用范围与相邻路线

本路线是：一个主题进，一条手绘讲解片出——拆解概念、写口播、分镜、逐笔手绘、可选口播、本地渲染。提示词生成视频走 AI 视频工作室；课堂实录走课程工作室；往平台发布不属于本包。

## 开始前先收集（缺了再问）

至少要有一项：**要讲什么**、**一份写好的稿**，或 **一条对标视频链接**。

- **要讲什么。** 一个概念、一组对比、或一个要讲清楚的故事，就够开工。
- **对标。** 小红书 / 抖音 / TikTok / YouTube / Instagram / X 链接，或「拆这条」：先按 [the benchmark lookup](references/benchmark-lookup.md) 读完，再拆结构。
- **受众和平台。** 默认做成竖屏知识短片；不要编造人设。
- **不能说的。** 公司名、未公开数字。没有禁说清单时，不要编数字，也不要把没跑过的工作说成已验证。
- **输出目录。** 默认在当前工作目录下新建 `<slug>/`。
- **口播和时长。** 没说就问。默认 1–3 分钟。声音只给两条路：Beatra 库内声，或克隆（本人声音或已声明授权）。不要列举其他 TTS 厂商。

text 还是 program 在 Gate A 决定；更早不要建草稿。

## 创作（过闸之前不要画）

按 [the workflow](references/workflow.md) 走；两道闸都要明确通过。

1. **拆主题。** 一个记住点、常见混淆、3–5 步、一个可画的例子、一条边界、砍掉清单。太多就提议做成系列。对标要在拆解前读完：只借双文字轨和一句一物，拒绝彩色剪贴画、真人手部照片和关注引导。
2. **Gate A · 方向。** 一张卡写清理解、受众假设、角度、时长、模式、是否口播、砍掉清单和诚实等级；停下来等：通过 / 改角度 / 时长 / 模式 / 去掉口播 / 这次不做。
3. **写口播和分镜。** 按 [script copywriting](references/script-copywriting.md)：先诊断开头，用冲突做钩子，再证据，再落地，再收束动作。分镜上的画面字和物件按 [visual rules](references/visual-rules.md)；一场一个想法。
4. **Gate B · 稿和分镜。** 完整口播加分镜表和时长估计；停下来等：通过 / 改场 / 删场 / 重写 / 回到 Gate A。

「你看着办」不算通过。Gate B 通过后，「按这张表画」才开工。角度变了重开 Gate A；口播变了重开 Gate B。

## 选模式

- **text**：字逐笔写出来——汉字和英文短词一样——再画对应物件。社交白板讲解默认这条。[text mode](references/mode-text.md)。
- **program**：流程卡片、关系图、必须读准的标签。[program mode](references/mode-program.md)。

拉丁专有名词两种模式都用 Georgia。字幕和画面字是两条轨；人默认不入画；见 [visual rules](references/visual-rules.md)。

## 成片（Gate B 通过之后）

前置和完整命令序列见 [pipeline commands](references/pipeline-commands.md)（Node 18+、npm、ffmpeg）：

1. 建草稿，写入已通过的 `script.txt` 和 `DESIGN.md`。
2. 按模式参考画 `<outdir>/index.html`。
3. 画面字来自笔顺数据，不用系统字体——汉字和英文短词都一样：

   ```bash
   python3 "$SKILL/scripts/text_svg.py" '目标' --id goalText --cx 540 --cy 280 --size 80
   ```
4. 口播按 [voiceover and sync](references/voiceover-and-sync.md)：提交、轮询 `beatra.tasks.get`、收取。口播没变就不要再合成。
5. `node "$SKILL/scripts/render.mjs" <outdir>`；交付前用 `renders/preview/sN.jpg` 对照口播里的名词。

## 付费变更、恢复和取消

规划免费：Gate A 卡片和 Gate B 的稿加分镜在扣费前交付。规划不是批准。付费调用一共三种。每一种都有自己的六字段当前生产卡，每个逻辑请求一个 `client_request_id`。不要把查找折进合成。

口播合成前，调用 `beatra.models.list` 获取 `text_to_speech`：

```json
{"capability": "text_to_speech"}
```

出示合成卡并等待：

1. 做什么 — 本片口播（`beatra.speech.synthesize`）。
2. 积分 — 刚读到的 `text_to_speech` 价格。不要复用记忆中的数字。
3. 几笔 — 整份 `script.txt` 一次付费合成。
4. 身份 — 一个新的不透明 `client_request_id`。
5. 若停在这里 — Gate A 方向和 Gate B 的稿加分镜仍然可用。
6. 若余额不足 — 原样转达官方说明和充值链接。翻译正文，保留链接。用户说已充值之前不要重试。

克隆前，调用 `beatra.models.list` 获取 `voice_clone`：

```json
{"capability": "voice_clone"}
```

只有用户声明这是本人声音或说话人已授权时才克隆。通过带守卫的 voice.mjs clone-submit --consent 子命令提交，没有同意声明就拒绝运行。出示克隆卡并等待：

1. 做什么 — 一份已授权的声音样本（`beatra.voices.clone`）。
2. 积分 — 刚读到的 `voice_clone` 价格。不要复用记忆中的数字。
3. 几笔 — 这份样本一次付费克隆。
4. 身份 — 一个新的不透明 `client_request_id`。
5. 若停在这里 — Gate A/B 计划仍然可用；库内声仍可口播。
6. 若余额不足 — 原样转达官方说明和充值链接。翻译正文，保留链接。用户说已充值之前不要重试。

对标查找（`beatra.social.execute`）是另一张卡。出示后等待：

1. 做什么 — 用用户的话写出链接，并映射到一个 `operation_key`。
2. 积分 — `beatra.social.tools.get` 刚返回的实时价格。
3. 几笔 — 这条链接一次付费查找。
4. 身份 — 一个新的不透明 `client_request_id`。
5. 若停在这里 — 不查找也能走概念路线成片。
6. 若余额不足 — 原样转达官方说明和充值链接。翻译正文，保留链接。用户说已充值之前不要重试。

稿、声音或语速变了就是新卡、新标识。完全相同的再提交复用原标识。提交结果不确定时，先用 `beatra.tasks.list` 和 `beatra.tasks.get` 对账，再按完全相同的参数用同一标识重放；不要自动重试。

工具返回积分不足时：把工具返回的原文整段交给用户，链接一个字不改。其余可以译成中文。不要改写成自己的充值说明。引导用户按原文去充值。

## 账户余额

用户问还剩多少积分，或某次实时估价够不够时，调用 `beatra.wallet.get`。问已经扣了多少时，调用 `beatra.wallet.ledger`。口播和克隆的实时价格来自 `beatra.models.list`，参数是 `{"capability": "text_to_speech"}` 或 `{"capability": "voice_clone"}`；查找价格来自 `beatra.social.tools.get`。不要从流水行里读价格。

## 按任务查阅的参考

用 [the workflow](references/workflow.md)、
[script copywriting](references/script-copywriting.md)、
[visual rules](references/visual-rules.md)、[text mode](references/mode-text.md)、
[program mode](references/mode-program.md)、
[voiceover and sync](references/voiceover-and-sync.md)、
[the benchmark lookup](references/benchmark-lookup.md) 和
[pipeline commands](references/pipeline-commands.md)。连接本身用
[installation and authentication](references/installation-and-auth.md)、
[随包 MCP Client 连接诊断](references/mcp-connection.md)、
[tasks and results](references/tasks-and-results.md)、
[billing, errors, and recovery](references/billing-errors-and-recovery.md)
和 [uninstall and disconnect](references/uninstall-and-disconnect.md)。

## 运行时与安全的自动更新

随包客户端会在每个安装中静默检查更新，最多每 24 小时一次。发现更高版本时，不另行确认地自动安装。它只从本包、渠道和语言环境固定的官方 Beatra 发现地址和不可变 CDN 路径下载，校验发现信息、压缩包、清单和每个随包文件，并且只替换本包拥有的文件。

更新检查、下载、校验、替换、回滚和恢复失败时会 fail open：当前安装仍可使用，原本请求的命令会继续执行。这个设置会在本安装中持续生效。见 [automatic updates and safety](references/automatic-updates-and-safety.md)。

```text
python3 scripts/mcp_client.py update --auto off
python3 scripts/mcp_client.py update --auto on
python3 scripts/mcp_client.py update --check
```
