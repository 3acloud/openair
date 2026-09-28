## Description: <br>
Generates single-file HTML study notes with a handwritten notebook style for technical notes, vulnerability analysis, and knowledge summaries. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[unclecheng-li](https://clawhub.ai/user/unclecheng-li) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers, technical writers, learners, and security researchers use this skill to turn structured content into styled HTML notes that resemble a handwritten notebook. It is best suited for study notes, technical summaries, vulnerability notes, and shareable knowledge writeups rather than formal reports or dense tabular documents. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Generated HTML notes may load remote assets from Google Fonts and unpkg when opened. <br>
Mitigation: Use the skill only where those network requests are acceptable, or remove or replace remote assets when offline or private notes are required. <br>
Risk: Broad note-related trigger words may route unrelated note requests to this specialized handwritten HTML workflow. <br>
Mitigation: Narrow trigger words or invoke the skill explicitly when the handwritten notebook output is desired. <br>


## Reference(s): <br>
- [ClawHub release page](https://clawhub.ai/unclecheng-li/note-skill) <br>
- [Layouts reference](references/layouts.md) <br>
- [Components reference](references/components.md) <br>
- [Quality checklist](references/checklist.md) <br>
- [HTML note template](assets/template.html) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, guidance] <br>
**Output Format:** [Markdown guidance with HTML, CSS, and shell command snippets] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces browser-openable, single-file HTML note pages using the bundled template and reference materials.] <br>

## Skill Version(s): <br>
1.0.0 (source: server-resolved release metadata) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
