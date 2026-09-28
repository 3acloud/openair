---
name: wjs-wechat-publishing
description: 当用户想写微信公众号文章时，接收零散思路或草稿，轻润色并生成题图、解释图，准备上传发布。严格遵循STYLE.md风格，每篇800-1000字，含2-4处加粗加红。
---
# wjs-wechat-publishing

帮用户写微信公众号文章。**轻润色，不重写**。自动生成题图和解释图，一行命令推草稿。

## 核心规则
- 读STYLE.md并严格遵循
- 每段1-3句，保留作者语气
- 必须有2-4处`**红色加粗**`
- 字数800-1000

## 工作流
1. 接收输入并轻润色
2. 给出3个标题候选 + 50-80字摘要
3. 生成cover.png(900x383)和illustration.png
4. 输出articles/YYYY-MM-DD-slug/目录
5. 运行upload-draft.sh发布

## 输出文件
- article.md
- cover.png / illustration.png
- meta.json / original.md

安装后触发词：写一篇微信文章、公众号、润色。
