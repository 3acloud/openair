## Description: <br>
易经64卦占卜分析；支持数字串解码、辞传呈现、朱熹/南怀瑾视角解读、日常事务建议及统计分析；当用户需要起卦、解读卦象、查询64卦卦辞爻辞或进行占卜分析时使用。 <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[qiuzijun-nm](https://clawhub.ai/user/qiuzijun-nm) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users can use this skill to interpret Yi Jing hexagram readings from six-digit coin-cast inputs, retrieve hexagram and line text, and receive plain-language divination analysis for everyday questions. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill keeps persistent local records of divination topics without clear consent, deletion, or retention controls. <br>
Mitigation: Before use, confirm where history is stored, how to delete it, and whether logging is acceptable for the intended users. <br>
Risk: Users may enter sensitive personal, health, legal, financial, relationship, or family details into divination prompts. <br>
Mitigation: Avoid sensitive details unless storage and deletion behavior has been reviewed and approved. <br>


## Reference(s): <br>
- [yijing-4096.csv](references/yijing-4096.csv) <br>
- [yijing-full.csv](references/yijing-full.csv) <br>
- [yijing-2026-calendar.csv](references/yijing-2026-calendar.csv) <br>
- [yijing-log.csv](references/yijing-log.csv) <br>
- [yijing-stats.json](references/yijing-stats.json) <br>
- [ClawHub skill page](https://clawhub.ai/qiuzijun-nm/yijing-64gua) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Analysis, Guidance] <br>
**Output Format:** [Markdown with structured sections and tables] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include hexagram lookup results, Chinese source text, plain-language interpretation, practical advice, and summary statistics.] <br>

## Skill Version(s): <br>
1.0.1 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
