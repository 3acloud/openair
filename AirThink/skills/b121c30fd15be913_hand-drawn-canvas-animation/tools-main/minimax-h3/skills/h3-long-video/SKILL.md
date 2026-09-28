---
name: h3-long-video
description: Builds long videos (minutes) from a chain of 15-second MiniMax H3 clips while preserving characters, scene, voice, and style. Use when the user wants a video longer than 15 seconds, asks about stitching H3 clips, character consistency across generations, video continuation, extending runtime, or storyboarding a longer piece.
---

# MiniMax H3 — long videos: a chain of clips with consistency

H3 generates 4–15 seconds per pass. A long video = **a chain of clips**, where each next clip is generated with references that carry continuity. Your job in this skill is to help the user plan the chain and write the prompt for each link (use the rules from `h3-t2v-prompt` and `h3-ref-prompt`).

## What holds consistency (strongest first)

1. **Frame-to-frame seam (the main technique)**: the last frame of clip N becomes the first-frame anchor of clip N+1. The picture matches pixel-perfect at the seam, and the model develops the scene forward from that frame (I2VA: first-frame anchor → action onset → development → result).
2. **Character references**: up to 9 images per generation. Build a "character sheet" once (front, 3/4, full body) and attach it to EVERY clip as `<Subject N>` sources.
3. **Voice reference**: up to 3 audio clips. Cut a clean line of the character's speech from the first clip and attach it as an `<Audio N>` voice-timbre reference to every later clip with dialogue.
4. **Scene/style reference**: a location or style frame as a `<Subject N>` (environment/style).
5. **Video continuation**: the previous clip can be attached as `<Video N>` with the `video continuation` task type — H3 natively continues from the end of a source video (note: reference video seconds are billed in the API, and you get at most 3 video references).

Per-generation limits: 9 images + 3 videos + 3 audio, 12 files total; audio only together with an image or video.

## The "project bible" — a stable text block

The model does not remember past generations. Everything that must stay identical gets repeated **verbatim** in every prompt:

- Character descriptors: age, build, hair, face + **wardrobe always named in text** (H3 drifts wardrobe even with references).
- Environment: key location elements, time of day, lighting.
- Style prefix: `Cinematic, live-action, ... , vertical 9:16` — the same line in every clip.
- Sound: the same `non_diegetic_music` description (same instruments/tempo) and the same ambient bed in `overall_soundscape`.

Keep this bible as a file in the project (e.g. `project-bible.md`) and paste it into every prompt without rephrasing.

## Workflow

1. **Storyboard**: split the story into 10–15 second links. Plan seams **on action** (cut on action) or on a calm frame — not at the peak of complex motion: the seam reads cleaner and the last frame is sharper. Key beats go in the middle of each clip, not on the seams.
2. **Clip 1**: T2VA or full-reference from the source references. Generate 2–3 variants, pick the best — its final frame becomes the next link's anchor.
3. **Extract the last frame**:
   ```bash
   ffmpeg -sseof -0.1 -i clip1.mp4 -frames:v 1 -q:v 2 clip1_last.jpg
   ```
4. **Clip 2+**: a full-reference prompt (`h3-ref-prompt`) where:
   - `clip1_last.jpg` → `<Picture 1>` as `[Shot 1]`'s first frame (`keyframe completion`);
   - the character sheet → `<Subject N>` (`fully_preserved`);
   - the voice from clip 1 → `<Audio N>` (`reference`);
   - the project bible — verbatim in the text.
5. **Repeat** to the target runtime. Regenerate a weak link changing only that link — the chain allows it.
6. **Edit**: assemble in any editor. Frame-to-frame seams usually need no transition; for scene/time changes use a honest cut or a short cross-dissolve. A continuous score is easier to lay over the whole edit, with `non_diegetic_music: N/A` in the prompts (or an identical description if you want H3's native audio).

## Typical problems and fixes

- **Face/wardrobe drift by clip 3–4**: refresh the character sheet with fresh frames from the latest good clip, not the first one.
- **Jittery seam**: the last frame was at peak motion — regenerate the previous clip's tail with a calm ending, or place the seam at a shot change.
- **Voice drift**: strengthen the textual timbre description (pitch, timbre, rate, accent) + the audio reference; keep the speaker ID `(S1)` continuous across the whole project.
- **Lighting/time-of-day jumps**: fix it in the bible (`dusk, cool blue tones, sodium streetlights`) and never rephrase it.
- **A continuous action that won't fit 15s**: use the FL2VA style inside the clip (first+last frame) and seam on intermediate keyframes.

## Response format for the user

For a request like "I want a 2-minute video about X", deliver:

1. The chain plan: a list of links (clip 1: 0:00–0:15 — what happens, what the final frame is; clip 2: ...).
2. The project bible (a draft of the stable block).
3. The prompt for clip 1 following `h3-t2v-prompt` / `h3-ref-prompt` rules.
4. The instruction: send back the last frame (or the rendered clip) → I'll build the next link's prompt.

Do not write prompts for all links blindly up front: each next link depends on the actual final frame of the previous one.
