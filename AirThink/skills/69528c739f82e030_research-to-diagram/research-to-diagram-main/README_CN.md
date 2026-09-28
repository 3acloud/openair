# Research to Diagram - 深度调研自动绘图

[English](README.md) | [中文](README_CN.md)

深度调研主题并自动生成知识关系图谱PDF。从研究到可视化的一站式工具。

## 问题背景

当你想要理解复杂主题时，比如：
- 文学作品人物关系（如《红楼梦》）
- 技术架构（如 Kubernetes 架构）
- 历史事件（如春秋战国时期）
- 概念图谱（如机器学习算法分类）

你通常需要：
1. 花费数小时从多个来源调研资料
2. 手动整理信息和梳理关系结构
3. 学习图表工具如 Graphviz、PlantUML
4. 设计布局和视觉层次
5. 生成并反复迭代图表

**这需要花费数小时甚至数天的时间。**

## 解决方案

`research-to-diagram` 是一个**研究驱动的知识可视化工具**，自动化整个流程：

```
你提供：主题/研究问题
        ↓
Skill 处理：调研 → 整理 → 设计 → 生成
        ↓
你得到：专业 PDF 图谱 + 参考资料来源
```

**节省时间：10倍效率提升** - 从数小时的工作量缩短到 2-5 分钟的自动化处理。

### 核心特性

- ✅ **自动调研**：使用 WebSearch 进行多轮深度调研
- ✅ **智能整理**：自动提取、分类、结构化信息
- ✅ **专业设计**：根据主题特点选择最佳可视化方案
- ✅ **高质量输出**：生成矢量 PDF，可无限缩放
- ✅ **来源追溯**：记录所有参考资料链接

### 与 structure-to-pdf 的对比

| 特性 | research-to-diagram | structure-to-pdf |
|------|---------------------|------------------|
| **输入** | 仅需主题/问题 | 需要结构化数据 |
| **调研** | ✅ 自动调研 | ❌ 无 |
| **应用场景** | 知识探索 | 快速数据转换 |
| **时间** | 2-5 分钟 | <1 分钟 |
| **参考资料** | ✅ 提供来源 | ❌ |

**黄金法则**：
> 没数据找 research-to-diagram，有数据用 structure-to-pdf！

## 环境要求

- **Graphviz**：`brew install graphviz`（macOS）或 `apt-get install graphviz`（Linux）
- **Claude Code**：内置 WebSearch 功能
- **网络连接**：用于调研和信息收集

## 安装方法

### 方式 1：Git Clone（推荐）

```bash
# 克隆仓库
git clone https://github.com/wshuyi/research-to-diagram.git

# 复制 skill 到 Claude Code skills 目录
cp -r research-to-diagram/skills/research-to-diagram ~/.claude/skills/

# 如果还没安装 Graphviz
brew install graphviz
```

### 方式 2：插件市场

```bash
# 添加插件市场
/plugin marketplace add wshuyi/research-to-diagram

# 安装 skill
/plugin install research-to-diagram@wshuyi/research-to-diagram
```

## 使用方法

直接用自然语言向 Claude Code 描述你的研究主题：

### 示例 1：文学作品人物关系

```
深度调查《红楼梦》里人物之间的关系，然后做个结构图 PDF
```

**输出结果**：
- 50+ 人物节点
- 7 个家族分组
- 多种关系类型（血缘、婚姻、联姻）
- 152KB 专业 PDF
- 7 个权威参考来源

### 示例 2：技术架构研究

```
研究 Kubernetes 架构并生成可视化图谱
```

**预期输出**：
- 控制平面组件
- 数据平面组件
- 插件生态
- 组件间交互关系

### 示例 3：历史事件分析

```
分析春秋战国时期各国关系，做成关系图
```

**预期输出**：
- 战国七雄
- 合纵连横策略
- 重要战役
- 统一过程时间线

## 工作流程

Skill 遵循系统化的工作流程：

```
1. 任务规划（TodoWrite）
   ↓
2. 深度调研阶段
   - 多轮 WebSearch
   - 信息源记录
   - 知识提取
   ↓
3. 结构设计阶段
   - 选择图谱类型
   - 设计层次结构
   - 规划视觉布局
   ↓
4. 可视化实现
   - 生成 Graphviz DOT
   - 配置样式
   - 优化布局
   ↓
5. PDF 生成
   - 编译为矢量 PDF
   - 验证输出质量
   ↓
6. 文档整理
   - 提供参考资料来源
   - 生成使用说明
```

## 图谱类型

### 人物关系图
- 家族谱系
- 社会网络
- 组织架构

**模板**：`examples/character_relationships.dot`

### 概念图谱
- 知识分类
- 层次概念
- 思维导图

**模板**：`examples/concept_map.dot`

### 技术架构图
- 系统组件
- 依赖关系
- 分层架构

**模板**：`examples/tech_architecture.dot`

## 输出文件

生成的文件保存到 `~/` 或用户指定目录：

- `<主题>_relations.dot` - Graphviz 源文件
- `<主题>_relations.pdf` - 最终 PDF 图谱
- `<主题>_sources.md` - 参考资料（可选）

## 高级功能

### 自定义布局方向

```
研究公司发展历程并生成时间线图（从左到右布局）
```

### 指定详细程度

```
快速研究 React Hooks 并生成简单图谱
```

```
深度研究 React Hooks 实现原理并生成详细图谱
```

### 指定输出位置

```
研究量子计算发展史并生成图谱，保存到 ~/Documents/
```

## 常见问题

**Q: 需要多长时间？**
A: 通常 2-5 分钟，取决于主题复杂度和调研深度。

**Q: 调研的信息准确吗？**
A: Skill 会：
- 从多个来源交叉验证
- 提供所有参考资料链接
- 使用最新的 WebSearch 结果

**Q: 可以修改生成的图谱吗？**
A: 可以！`.dot` 源文件可以手动编辑：
```
帮我修改 hongloumeng_relations.dot，增加更多关系细节
```

**Q: 可以生成其他格式吗？**
A: 可以：
```
生成 PNG 图片版本
同时生成 PDF 和 SVG 格式
```

**Q: 图谱太复杂怎么办？**
A: 可以请求分步生成：
```
先生成主要人物和家族总览图，
然后我们再深入某个家族的详细关系
```

## 示例展示

查看 [USAGE_EXAMPLES.md](skills/research-to-diagram/USAGE_EXAMPLES.md) 了解 7 个详细示例，包括：
- 文学作品
- 技术概念
- 历史事件
- 生物分类
- 地理关系
- 等等...

## 文档资料

- [SKILL.md](skills/research-to-diagram/SKILL.md) - 核心 Skill 指令
- [README.md](skills/research-to-diagram/README.md) - 完整使用指南
- [COMPARISON.md](skills/research-to-diagram/COMPARISON.md) - 与 structure-to-pdf 对比
- [USAGE_EXAMPLES.md](skills/research-to-diagram/USAGE_EXAMPLES.md) - 详细使用示例

## 贡献

欢迎贡献！请随时提交：
- 新的图谱模板
- 最佳实践示例
- Bug 报告
- 功能建议

## 许可证

MIT License - 查看 [LICENSE](LICENSE) 了解详情

## 作者

由 [wshuyi](https://github.com/wshuyi) 创建

使用 [Claude Code](https://claude.com/claude-code) 构建

## 致谢

- 基于《红楼梦》人物关系图项目的经验总结
- 受高效知识可视化需求的启发
- 感谢 Graphviz 社区提供优秀的图表工具
