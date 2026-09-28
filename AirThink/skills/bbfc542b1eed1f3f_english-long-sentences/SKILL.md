---
name: english-long-sentences
description: 考研英语长难句分析PDF生成器。当用户需要创建考研英语长难句练习材料、语法分析文档、备考笔记等PDF文档时使用此技能。支持句子结构分析、词汇注释、语法点标注和精美排版。
---

# 考研英语长难句分析 - PDF生成器

生成专业排版的考研英语长难句分析PDF文档，包含句子结构分析、词汇注释、语法点讲解和参考译文。

## 工作流程

### 步骤1：收集长难句信息

向用户确认以下信息：
- 标题（如"考研英语长难句精练"、"长难句30句突破"等）
- 副标题（如"核心语法突破"、"历年真题精选"等）
- 句子数量和来源（如考研真题、外刊同源句等）
- 每个句子的内容：英文原句、词汇注释、结构分析、参考译文

### 步骤2：生成HTML文档

1. 复制 `assets/long_sentence_template.html` 作为基础
2. 替换封面信息（标题、副标题、适用年份）
3. 按要求添加长难句内容
4. 保存为 .html 文件
5. 运行 `python scripts/html_to_pdf.py <文件名>.html` 生成PDF

### 步骤3：输出PDF

使用脚本将HTML转换为PDF格式

## 文件结构

```
english-long-sentences/
├── SKILL.md                    # 技能说明文档
├── assets/
│   └── long_sentence_template.html  # 长难句HTML模板
└── scripts/
    └── html_to_pdf.py          # HTML转PDF脚本
```

## 长难句格式规范

### 句子结构

每个长难句包含以下部分：

```
### 句子N [语法类型]
英文原句

#### 词汇注释
- 单词1: 中文释义
- 单词2: 中文释义

#### 结构分析
句子成分分析、语法点讲解

#### 参考译文
中文译文
```

### 语法类型标签

- 定语从句
- 状语从句
- 名词性从句
- 非谓语动词
- 倒装句
- 强调句
- 独立主格
- 省略句

### 词汇注释格式

```
<div class="vocab-item">
    <span class="vocab-word">word</span> <span class="phonetic">/ˈwɜːrd/</span> 词性 释义
</div>
```

## 模板使用示例

### 封面信息替换

```html
<div class="cover-badge">考研英语</div>
<h1 class="cover-title">长难句精练</h1>
<p class="cover-subtitle">20句核心语法突破</p>
```

### 添加新句子

```html
<div class="sentence-block">
    <div class="sentence-title">
        <span class="sentence-number">1</span>
        定语从句嵌套
        <span class="sentence-source">（2010年考研真题）</span>
    </div>
    
    <div class="sentence-en">
        英文原句...
    </div>
    
    <div class="sentence-section">
        <div class="section-label">词汇注释</div>
        <div class="vocab-list">
            <div class="vocab-item"><span class="vocab-word">word</span>: 释义</div>
        </div>
    </div>
    
    <div class="sentence-section">
        <div class="section-label">结构分析</div>
        <div class="analysis-content">
            <p>分析内容...</p>
        </div>
    </div>
    
    <div class="sentence-section">
        <div class="section-label">参考译文</div>
        <div class="translation">
            译文内容...
        </div>
    </div>
</div>
```

## 示例输出

```
考研英语长难句精练
20句核心语法突破

1. 定语从句嵌套（2010年考研真题）
【英文原句】
...

【词汇注释】
- ...
【结构分析】
- ...
【参考译文】
- ...
```

## 依赖要求

- HTML转PDF: Microsoft Edge浏览器（Windows自带）
