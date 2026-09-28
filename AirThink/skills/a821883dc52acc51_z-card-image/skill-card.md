## Description:

z-card-image turns copy, article text, social posts, and WeChat or X-style content into PNG card images, cover images, posters, and long-form share images.

This skill is ready for commercial/non-commercial use.

## Publisher:

[agentforge-cyber](https://clawhub.ai/user/agentforge-cyber)

### License/Terms of Use:

MIT-0

## Use Case:

Developers, creators, and agents use this skill to choose a supported image template, prepare text within template limits, and generate PNG assets for social posts, WeChat covers, article cards, and X-style long images.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Local rendering weakens browser isolation while processing user-controlled text and Markdown.

Mitigation: Render only trusted content and run the skill in a container or low-privilege environment when possible.

Risk: Broad local file paths may expose unintended files through icon, input, or output parameters.

Mitigation: Keep inputs and outputs inside the workspace and avoid passing sensitive local files as icons or input files.

Risk: The skill depends on local Python and Chrome binaries, so missing or mismatched runtimes can prevent rendering.

Mitigation: Confirm Python 3 and Google Chrome are available before use and document environment differences.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/agentforge-cyber/skills/z-card-image)
- [poster-3-4 template specification](references/poster-3-4.md)
- [article-3-4 template specification](references/article-3-4.md)
- [x-like-posts template specification](references/x-like-posts.md)
- [tweet-thread compatibility note](references/tweet-thread.md)
- [wechat-cover-split template specification](references/wechat-cover-split.md)

## Skill Output:

**Output Type(s):** [text, markdown, code, shell commands, configuration, files]

**Output Format:** [Markdown guidance with shell commands that generate PNG image files]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Requires Python 3 and Google Chrome; generated image files are written to the requested output path.]

## Skill Version(s):

1.0.0 (source: server release metadata; artifact frontmatter and _meta.json report 1.1.0)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
