<p align="center">
  <img src="docs/images/banner.svg" alt="openair — 把 Skill 做成应用，由 AirThink、AirCode 和本机 Agent 驱动" width="100%">
</p>

<p align="center">
  <a href="README.md"><img src="docs/images/language-zh.svg" alt="简体中文" width="112" height="32"></a>
  <a href="README.en.md"><img src="docs/images/language-en.svg" alt="English" width="112" height="32"></a>
</p>

# openair

**把 Skill 做成应用，让 AI 能力更容易使用和管理。**

通常，我们在 Agent 中通过对话使用 Skill。openair 希望将这些能力变成可以直接打开的应用：用户在浏览器中选择工具、输入内容、获取结果，并在自己的应用集中管理和扩展它们。

openair 由 **AirCode** 和 **AirThink** 两个本地服务组成。AirCode 让应用通过本机 Claude Code、Codex、Grok Build、DeepSeek Harness 使用 AI；AirThink 提供应用集页面，收集了几百个应用，也可以接收从 iThinkAir 部署到内网的自建应用。

![openair 首页截图](docs/images/screenshot.png)

## 为什么做 openair

- **让 Skill 有应用界面**：把任务流程做成可操作的页面，方便日常使用。
- **使用自己的 Agent**：应用通过 AirCode 调用本机 Agent CLI，使用用户自己的登录环境。
- **利用订阅服务**：希望借助 Agent 订阅降低日常使用成本，减少按量调用模型 API 的开销；实际成本与可用额度取决于用户的订阅和使用情况。
- **集中发现和管理应用**：在同一个页面搜索应用、按分类浏览，并访问自己的应用。
- **按需定制**：在 [iThinkAir](https://www.ithinkair.com) 开发应用，在应用详情页点击「部署到内网」，将应用部署到自己的内网应用集。

## 工作原理

```text
浏览器中的应用
      │
      ▼
AirThink（3130）
应用页面、文件和应用管理
      │
      ▼
AirCode（3131）
任务与工作流执行
      │
      ▼
本机 Agent CLI
      │
      ▼
AI 处理任务，结果返回应用
```

AirCode 通过 Agent CLI 执行 AI 任务。因此，运行应用前，需要让启动服务的 Windows 用户能够在命令行中正常使用 Agent。

## 快速开始

### 1. 准备环境

当前启动脚本面向 **Windows**。请准备：

- Python 3，且 `python`、`pip` 可以正常使用。
- 已安装、登录并可正常执行任务的 Agent CLI。
- 现代浏览器，以及安装依赖和访问 AI 服务所需的网络连接。

在 PowerShell 中检查环境：

```powershell
python --version
python -m pip --version
```

两个服务会在启动时检查并通过 pip 安装缺失的 Python 依赖。首次启动可能需要较长时间，请留意服务窗口中的输出。部分应用还可能需要额外的工具或运行环境。

### 2. 启动服务

进入 `openair` 目录后运行：

```powershell
cd openair
.\start.bat
```

也可以在资源管理器中打开 `openair` 文件夹，双击 `start.bat`。

脚本会启动 AirThink 和 AirCode，在检测到 `3130` 端口开始监听后，自动打开：

**[http://127.0.0.1:3130/index.html](http://127.0.0.1:3130/index.html)**

使用期间请保留两个服务窗口。页面打开时，AirCode 可能仍在安装依赖，请等它完成启动后再执行 AI 任务。结束使用时，关闭两个服务窗口即可停止服务。

> 启动脚本会先强制结束占用 `3130`、`3131` 端口的进程，请确认这两个端口没有用于其他需要保留的服务。

### 3. 打开应用

在应用集页面搜索关键词，或按分类浏览应用，点击应用卡片即可打开。

直接访问本机 `127.0.0.1` 服务时，应用集会直接打开应用；访问其他内网服务器时，请按页面提示输入 **用户密钥（User Key）**。这是 AirThink 的本地访问密钥，与 iThinkAir 用于连接内网服务的 API Key、Agent 登录凭据和模型 API Key 不同：

- 密钥保存在 `AirThink/apps/userkey.json` 中，格式为 JSON 字符串数组。使用前可将其设置为自己的密钥，例如 `["your-own-local-key"]`。
- 如果该文件不存在，首次提交的非空密钥会被保存为本地密钥。
- 验证成功后，浏览器会保存密钥，方便后续打开应用。

## 内置应用

应用集收集了上百个应用，按应用集页面中的 10 个分类组织：

| 分类 | 使用方向 |
| --- | --- |
| 演示与图解 | 演示文稿、信息图、流程图、思维导图与数据可视化 |
| 图像与设计 | 图片生成与编辑、海报封面、SVG 插画与视觉设计 |
| 视频与动画 | 视频脚本、分镜故事板、漫画、动画与视频制作 |
| 文案与写作 | 文章与小说、营销文案、内容润色与结构化写作 |
| 社媒与卡片 | 小红书图文、社媒长图、知识卡片与发布素材 |
| 学习与教学 | 题目讲解、学习笔记、课堂材料、作业与作文批改 |
| 语言与翻译 | 文本与文档翻译、双语学习、语音识别与合成 |
| 研究与办公 | 主题研究、资料整理、文档处理、办公自动化与分析报告 |
| 生活与成长 | 日常记录、物品识别、计划复盘与个人成长 |
| 传统与人文 | 传统文化、书画文物、易学研习与人文内容 |

这些应用可以从本地应用集直接打开，AI 任务由自己的 Agent CLI 执行。

## 创建应用并部署到内网

1. 访问 [iThinkAir](https://www.ithinkair.com)，也可以点击应用集右侧的 Logo +「iThinkAir」入口。
2. 根据自己的需求创建应用，完成后进入自己应用的详情页。
3. 保持内网电脑上的 OpenAir（AirThink 和 AirCode）运行。在同一台电脑上运行 ThinkClaw，并使用 iThinkAir「API Key 管理」中添加、复制的 API Key 建立内网连接。Windows 版 ThinkClaw 可从 iThinkAir 的「API Key 管理」窗口下载。
4. 在应用详情页点击「部署到内网」。页面会先检查内网服务是否在线；若提示「内网服务离线」，请恢复服务并通过「检查连接」确认后，再重试部署。
5. 看到「部署成功」后，重新打开或手动刷新内网应用集，在「我的应用」中查看并运行该应用；若提示「部署失败」，可按下方常见问题排查。

部署由 iThinkAir 直接发送到当前账户连接的内网服务。

## 项目结构

```text
openair/
├── start.bat              # 启动两个服务并打开浏览器
├── AirCode/
│   ├── app.py             # 任务服务入口
│   ├── startweb.py         # HTTP 服务启动入口（3131）
│   ├── run.bat
│   ├── worker/            # 工作流、AI 调用与任务执行
│   ├── utilities/         # 文件处理和通信等工具
│   └── SERVERFILES/       # 任务文件与 Agent CLI 工作目录
└── AirThink/
    ├── app.py             # 应用、文件和通信服务
    ├── startweb.py         # HTTP 服务启动入口（3130）
    ├── run.bat
    ├── apps/              # 应用集页面、应用源码和本地配置
    ├── files/             # 应用资源及上传文件
    └── skills/            # Skill 文件和资源
```

AirThink 还使用 `3133` 端口提供 WebSocket 服务。

## 常见问题

**浏览器没有自动打开，或者页面无法访问？**

检查 AirThink 窗口中的输出，确认依赖安装完成、服务成功启动。随后手动访问 [应用集页面](http://127.0.0.1:3130/index.html)。从命令行启动时，务必先进入 `openair` 目录，因为启动脚本使用相对路径。

**页面能打开，但 AI 任务没有结果？**

检查 AirCode 窗口中的输出，确认服务已启动，并确认同一个 Windows 用户可以在终端中正常运行 Agent 任务。

**部署时提示「内网服务离线」或「部署失败」？**

确认内网电脑已开机联网，OpenAir 的 AirThink、AirCode 和 ThinkClaw 均在运行，且 ThinkClaw 使用的是当前 iThinkAir 账户下的 API Key。服务恢复后，点击「检查连接」，再回到应用详情页重试「部署到内网」。如仍失败，请查看 AirThink 和 ThinkClaw 窗口中的具体错误。

## 运行说明

当前服务监听 `0.0.0.0`；AirCode 执行 Agent 任务时使用 `danger-full-access`，并关闭逐次审批。请在可信的个人环境中运行服务和部署应用，不要直接将服务暴露到公网。

## 参与贡献

欢迎提交问题反馈、改进建议和代码贡献。反馈问题时，请附上复现步骤、相关服务的报错信息，以及 Python 和 Agent CLI 版本；分享日志前请移除密钥和个人数据。
