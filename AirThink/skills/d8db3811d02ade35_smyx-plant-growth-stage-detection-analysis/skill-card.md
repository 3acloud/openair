## Description: <br>
AI-powered plant growth stage detection for plant images, videos, or URLs that classifies phenological stage, reports confidence, and returns a structured analysis report. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[smyx-sunjinhui](https://clawhub.ai/user/smyx-sunjinhui) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
External users and developers use this skill to analyze plant images or videos from smart pots, home grow boxes, greenhouses, and plant factories, then determine the current growth stage and confidence. It can also query cloud-stored historical growth-stage reports for the resolved user identity. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Plant images, videos, and submitted URLs are processed by the LifeEmergence cloud service. <br>
Mitigation: Avoid sensitive media and private or internal URLs unless cloud processing, retention, and deletion expectations are acceptable. <br>
Risk: Historical report lookup queries cloud-stored report history associated with the resolved user identity. <br>
Mitigation: Use only with accounts and workspaces where cloud report history access is expected and authorized. <br>
Risk: The skill creates or reuses a local identity and stores backend session tokens locally. <br>
Mitigation: Review local storage handling before deployment, restrict workspace access, and clear stored tokens when they are no longer needed. <br>
Risk: Growth-stage analysis and care direction may be incomplete for ambiguous images, transitional stages, or plant-specific conditions. <br>
Mitigation: Treat outputs as reference guidance, review confidence values, and avoid using the result as a specific agriculture operation plan without domain review. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/smyx-sunjinhui/skills/smyx-plant-growth-stage-detection-analysis) <br>
- [Skill demo](https://lifeemergence.com/sample.html) <br>
- [Plant growth stage API documentation](references/api_doc.md) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, JSON, shell commands, guidance] <br>
**Output Format:** [Markdown or JSON structured analysis text, with optional report export links] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May write the rendered result to a caller-specified output file; supports basic, standard, and json detail modes.] <br>

## Skill Version(s): <br>
1.0.3 (source: ClawHub release evidence) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
