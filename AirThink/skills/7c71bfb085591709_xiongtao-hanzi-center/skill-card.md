## Description: <br>
Analyzes the visual center of Chinese characters using a pixel-level model for stroke weight, distance, and slant, with support for multiple fonts, comparison mode, JSON output, and optional PNG visualizations. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[xtoyun](https://clawhub.ai/user/xtoyun) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users, calligraphy learners, and agents use this skill to analyze the perceived balance, visual center, and structure of individual Chinese characters or small comparison sets across supported fonts. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Default analysis can create PNG image artifacts in the current workspace. <br>
Mitigation: Run the skill only where generated image files are acceptable, disable PNG output when images are not needed, and clean up generated artifacts after review. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/xtoyun/hanzi-center) <br>
- [Online demo](http://shufa.xtocn.com/汉字视觉重心.html) <br>


## Skill Output: <br>
**Output Type(s):** [Text, Markdown, Shell commands, Configuration, Files] <br>
**Output Format:** [Markdown guidance with bash command examples, text reports, optional JSON data, and optional PNG image files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Runs locally with Node.js and can generate a PNG file in the workspace unless PNG output is disabled.] <br>

## Skill Version(s): <br>
1.0.1 (source: server release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
