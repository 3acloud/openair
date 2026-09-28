## Description:

Guides users through Stoic practice sessions, records local practice history, summarizes progress, exports reports, and provides daily Stoic quotations when users explicitly ask for Stoic coaching or practice.

This skill is ready for commercial/non-commercial use.

## Publisher:

[bonniegeng-max](https://clawhub.ai/user/bonniegeng-max)

### License/Terms of Use:

MIT-0

## Use Case:

External users and developers use this skill as a Stoic coaching assistant for guided reflection, practice tracking, progress review, insight reports, daily quotations, and Markdown or JSON exports. It is intended for explicit Stoic practice requests and is not a substitute for professional mental-health support.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Practice notes, distress scores, tags, and exported reports may contain sensitive reflections stored as local plaintext.

Mitigation: Tell users where records are stored, avoid uploading or committing them, and recommend encrypted storage for sensitive notes or exports.

Risk: Some exercises involve death, grief, loss, discomfort exposure, food restriction, or emotionally intense reflection that may be destabilizing.

Mitigation: Invite users to skip or stop any exercise that feels unsafe, avoid diagnostic claims, and suggest professional support for severe distress or crisis signals.

## Reference(s):

- [ClawHub Skill Page](https://clawhub.ai/bonniegeng-max/skills/stoic-coach)
- [Coach Guide](references/coach-guide.md)
- [Stoic Exercise Library](references/exercises.md)
- [Stoic Quote Library](references/quotes.md)

## Skill Output:

**Output Type(s):** [Text, Markdown, Shell commands, Configuration, Guidance]

**Output Format:** [Conversational Markdown with optional local script command output and Markdown or JSON exports]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Uses local plaintext JSONL practice records by default and can export practice history as Markdown or JSON.]

## Skill Version(s):

1.0.2 (source: server release metadata and skill frontmatter)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
