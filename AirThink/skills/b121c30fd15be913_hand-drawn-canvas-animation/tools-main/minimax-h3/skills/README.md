# MiniMax H3 prompt-writing skills

Agent skills that turn a rough idea into a production prompt for
[MiniMax H3](https://huggingface.co/MiniMaxAI/MiniMax-H3), the model that
generates video **and synchronized audio in one pass**. They encode MiniMax's
own prompt-writing guides, so the output lands in the exact field format the
model was trained to read — shots, camera moves with amplitude and speed,
speaker IDs, soundscape, score.

Built from the official guides
([base](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md),
[full-reference](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md))
plus [Naxdy's prompt-enhancer notes](https://gist.github.com/Naxdy/43b7422a1e4a79fb8b0489c6c39eaace).

## The skills

| path | what it does |
|---|---|
| [`h3-t2v-prompt`](h3-t2v-prompt/SKILL.md) | text-only idea → T2VA prompt (three fields: `integrated_multimodal_description`, `overall_soundscape`, `non_diegetic_music`) |
| [`h3-ref-prompt`](h3-ref-prompt/SKILL.md) | idea + reference images/video/audio → six-section full-reference brief (`subject_definitions` → `summary` → `retention_analysis` → `detailed_description` → audio sections) |
| [`h3-long-video`](h3-long-video/SKILL.md) | plans a minutes-long video as a chain of 15-second clips with character, scene, and voice continuity |

All three are tuned for dynamic, lifelike material: timed beats with observable
end states, the key beat in the middle of the timeline (the model squeezes
endings), camera always specified explicitly (H3 drifts otherwise), emotion
translated into observable behavior.

## Install

Drop the skill folders where your agent looks for them — user scope:

```bash
cp -r h3-t2v-prompt h3-ref-prompt h3-long-video ~/.agents/skills/
```

or project scope, into `.agents/skills/` of the repo you work in.

## Using them

Describe the idea and the constraints in one message — duration (4–15 s,
default 15), orientation (16:9 or 9:16), any dialogue and its language:

> 15 seconds, vertical, a courier on a bike tearing through a night market in
> the rain, ends at a noodle stall, one line of dialogue in English.

- No attachments → `h3-t2v-prompt` writes the three-field prompt.
- Attach a first frame, a character sheet, a voice sample → `h3-ref-prompt`
  writes the six-section brief.
- Ask for anything longer than 15 seconds → `h3-long-video` plans the chain
  and writes clip 1.

## Making long videos (the short version)

H3 tops out at 15 seconds per generation and remembers nothing between runs.
Long pieces are a **chain of clips**, and continuity is your job, carried
through the reference inputs (up to 9 images, 3 videos, 3 audio, 12 files
total per generation):

1. **Seam frame-to-frame.** Extract the last frame of clip N and feed it as
   the first-frame anchor of clip N+1 — the seam matches pixel-perfect:
   ```bash
   ffmpeg -sseof -0.1 -i clip1.mp4 -frames:v 1 -q:v 2 clip1_last.jpg
   ```
2. **Character sheet, every time.** Build reference stills of each character
   once (front, 3/4, full body) and attach them to every clip. Name the
   wardrobe in the prompt text too — H3 drifts clothing even with pictures.
3. **Voice reference.** Cut one clean spoken line from the first clip and
   attach it as a voice-timbre audio reference in every later clip with
   dialogue. Keep the speaker ID `(S1)` continuous across the project.
4. **Project bible.** One stable text block — character descriptors, location,
   lighting, style prefix, music description — pasted **verbatim** into every
   prompt. Rephrase it and the look drifts.
5. **Seam placement.** Cut on action or on a calm frame, never at peak motion.
   Put the important beats mid-clip, not on the seams.
6. **Drift control.** By clip 3–4 faces slide — refresh the character sheet
   from the latest good clip, not from the first one.

`h3-long-video` walks this loop with you: chain plan → bible → clip 1 prompt →
you render and send back the result → next link's prompt from the real final
frame. Video continuation (feeding the previous clip back as a `<Video N>`
reference) also works, but reference video seconds are billed, so the
frame-to-frame seam is the cheaper default.
