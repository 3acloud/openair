# meishi-buddy 🍳

泛美食账号内容创作 Skill（WorkBuddy / Claude Code 类智能体助手均可使用）。

一句话：给菜名或人群，产出「本地步骤图 + 照着能做的做法 + 一篇贴图短文」，中间该停的地方停下来等你确认。

## 账号定位

泛美食号，不细分垂类。养生餐、儿童餐、养颜餐、减脂减肥餐、家庭餐、一日三餐、10 分钟快手菜——全在一个号里，**不因主题切换人设**。产出形态只做「贴图 + 短文」，不写长文。

## 三个触发入口

| 入口 | 你说 | 它做 |
|---|---|---|
| A 给菜名 | 「我想发乌鸡汤」 | 抓图 → 给做法 → 出 2-3 个文案角度 → 等你选定 → 初稿 → 按意见改 |
| B 给人群/场景 | 「受众是学生，推荐几道菜」「夏至吃什么」 | 推荐 3-5 道菜（说清为什么适合）→ ⛔ 停，等你选 → 转入口 A |
| C 一周批量 | 「这周排 7 天减脂餐」 | 出 7 天选题清单 → ⛔ 停，等你确认 → 逐篇按入口 A 展开 |

## 图片抓取

首选下厨房（xiachufang.com）：

```bash
# 完整菜谱：成品图 + 步骤图 + 用料 + 步骤文案
python3 scripts/xcf_recipe.py 乌鸡汤            # 默认选搜索结果第 1 个
python3 scripts/xcf_recipe.py 乌鸡汤 --pick 3   # 换第 3 个菜谱

# 批量成品图（备选封面）
python3 scripts/xcf_crawler.py 乌鸡汤 8
```

- 详情页用 iPhone UA + 移动版域名绕过人机验证，图片取 `i2.chuimg.com` 原图
- 输出：`outputs/food-content/<菜名>_recipe/`（`00_成品图.jpg`、`step_NN.jpg`、`菜谱.md`、`recipe.json`）
- 兜底：小红书 / 公众号搜索参考（只拆结构，不照搬）

## 仓库结构

```
meishi-buddy/
├── SKILL.md                    # 主流程：三入口 + 强制确认节点 + 交付规范
├── scripts/
│   ├── xcf_recipe.py           # 下厨房完整菜谱抓取
│   └── xcf_crawler.py          # 下厨房成品图批量抓取
└── references/
    ├── writing-guide.md        # 文案语气规范 + 各主题侧重 + 合规红线
    └── food-knowledge.md       # 人群/节气/功效食材对应表 + 一周排期原则
```

## 安装

复制到你的 skill 目录（WorkBuddy 用户）：

```bash
git clone https://github.com/zephyrwang6/meishi-buddy.git
cp -r meishi-buddy/{SKILL.md,scripts,references} ~/.workbuddy/skills/meishi-buddy/
```

脚本无第三方依赖，Python 3.8+ 直接跑。

## License

MIT
