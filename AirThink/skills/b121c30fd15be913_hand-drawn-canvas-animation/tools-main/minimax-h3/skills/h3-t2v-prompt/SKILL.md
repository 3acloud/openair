---
name: h3-t2v-prompt
description: Turns a raw user idea into a ready production prompt for MiniMax H3 text-to-video (T2VA, no reference media). Use when the user describes a video idea, scene, or clip for H3/MiniMax and asks for a prompt, and has NOT attached any images/video/audio. Handles duration (usually 15s), orientation (landscape/portrait), dynamic action, smooth motion, and lifelike detail.
---

# MiniMax H3 — T2VA prompt from an idea (no references)

Goal: turn a short user description into a **final prompt** for MiniMax H3 (which generates video + synchronized stereo audio in one pass). Output is only the prompt text in English — no preamble, no explanations, no markdown wrapper (unless the user asks otherwise).

If the user attached any media (image/video/audio), this is NOT the right skill — use `h3-ref-prompt`.

## Step 0. Ask for what's missing (one short round)

If the user hasn't specified, ask in a single message:
- **Duration** in seconds (hard constraint, 4–15 range; this user defaults to 15).
- **Orientation**: landscape (16:9) or portrait (9:16) — it shapes composition; state it in the composition description (e.g. "vertical 9:16 framing").
- Any **speech/dialogue**, and in which language.
- Whether background music is wanted.

Ask at most one round of questions; invent everything else while preserving the user's intent.

## Output format (exactly three fields, in this order)

```text
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

### integrated_multimodal_description — the prompt body

- `[Shot 1]` — NO timestamp. Open with style and initial composition: `Cinematic, live-action`, `2D-animated`, `3D CG`, `claymation`, `watercolor`, `vintage film`, etc. Take the style from the user's words; never contradict them.
- Later shots: `[Shot N] At MM:SS.mmm, the camera cuts to ...` — strictly increasing cut times within the duration. Ordinary cuts: `the camera cuts to / the shot cuts to / transitions to / changes to / switches to`. Cross-dissolve/fade/wipe only if the user explicitly asked.
- Every detail must be visible or audible: subject appearance and posture, wardrobe (name it explicitly!), environment, lighting, props, actions and reactions, diegetic sound, spoken lines.

### Dynamism and smoothness rules (this user's priority)

The user wants **dynamic, alive, smooth** videos with variety. So:

- **Timeline beats**: anything longer than a single action gets split into consecutive beats, each with ONE primary change and an observable end state (something a viewer could point at: an empty table, a closed door, a prop in a named hand). A 15-second video usually holds 3–5 beats/shots.
- **Put the most important beat in the middle** of the timeline, not at the end (the model squeezes the final beat most often).
- **Time budget**: a complex action (hand-off, prop change) takes ~4 seconds. If it doesn't fit, drop or merge the least important beat.
- **A cut must introduce new information** (subject, space, state, viewpoint, time). If you only need to get closer or shift slightly, use camera motion instead of a cut.
- **Smoothness**: inside a shot, describe continuous development (onset → development → result/reaction), not a stack of static poses. Glue shots together with continuity: motion that carries on, sound that continues across the cut, a character's reaction.
- **Aliveness**: translate emotion into observable behavior. Not "she looks anxious" but "her gaze is fixed downward, her fingers grip the table edge, her shoulders stay raised". Add micro-detail: breathing, fabric, hair, steam, light glints, background life.
- **Variety**: vary distance and angle between shots (wide → medium → close-up), change what is in focus.

### Camera — ALWAYS specify it

H3 defaults to continuous drift and reframing when the camera is not described.

- One move per shot, written as natural English: `The camera pushes in with small amplitude at slow speed toward her hands.`
- Vocabulary: `Zoom In/Out`, `Push In/Pull Out`, `Pan Left/Right`, `Truck Left/Right`, `Tilt Up/Down`, `Pedestal Up/Down`, `Arc Shot`, `Tracking Shot`, `Static Shot`, `Shake Slightly/Strongly`, `POV`, `Roll Clockwise/Counterclockwise`.
- Amplitude: `with small/large amplitude` (omit medium). Speed: `at slow/fast speed` (omit normal).
- For a static shot, write `the frame never moves` and list what must NOT happen (no pan, no push-in, no reframing).
- For this user's dynamic ideas: `Tracking Shot`, `Arc Shot`, fast `Pan`/`Truck` with `large amplitude at fast speed` are appropriate — but never more than one move per shot.

### Speech and dialogue

- Every speaker/singer/off-screen voice gets a stable ID `(S1)`, `(S2)`; simultaneous group speech uses `(S1,S2)`. IDs persist across shots. Silent characters get no ID.
- On first appearance, establish identity OUTSIDE the tag: character type, age, gender, on-screen/off-screen, pitch, timbre, speaking rate, accent.
- Spoken content goes only inside `<d>[Language] exact words.</d>`. Supported languages: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish. User-provided words stay verbatim — no translation, no paraphrase. Unintelligible spans: `[unclear]`.
- Voiceover: the exact phrase `says in an off-screen voiceover`, and immediately after the `<d>` block — `while his lips remain completely closed.`
- A line crossing a cut: `<scenetrans>` at both ends + a continuity phrase like `continues seamlessly across the cut`. Speech truncated by the video end: `<cutoff>`.
- When speech ends, describe the lips closing and articulation ceasing, so the model stops the mouth.

### On-screen text

- Any visible text (signs, neon, subtitles) in English double quotation marks, verbatim: `A red neon sign reading "营业中" glows above the doorway.` A word that must be readable — TYPE it, name the typographic treatment and its position in frame.
- If no text should appear, say so explicitly (H3 has no negative prompt; refusals are plain sentences).

### overall_soundscape

1–4 sentences in one paragraph: ambience, physical action sounds, non-verbal human sounds (wind, rain, footsteps, fabric, impacts, breathing, laughter). Do NOT duplicate dialogue/singing/diegetic music here. `N/A` only on explicit request for total silence.

### non_diegetic_music

1–3 sentences: instrumentation, tempo, rhythm, loudness dynamics. NO abstract mood words ("epic", "touching") — only what is heard. Music the characters can hear (radio, TV, live performance) is diegetic and belongs in the body. `N/A` if none.

## Detail-level example (copy the structure, never the content)

```text
integrated_multimodal_description: [Shot 1] Cinematic, live-action, horizontal 16:9, a medium-wide tracking shot follows a food courier on a bicycle weaving through a rain-slick night market. The camera trucks left with large amplitude at fast speed, keeping pace as neon signs reading "OPEN 24H" smear into red and blue streaks on wet asphalt. The courier, a lean man in his 20s in a yellow waterproof jacket, stands on the pedals, breath visible in the cold air. [Shot 2] At 00:04.500, the camera cuts to a close-up of his handlebars as his gloved hand slaps the bell twice; the shot shakes slightly. He brakes hard, tires hissing on the wet pavement, and the spray kicks up into the frame. [Shot 3] At 00:08.000, the camera cuts to a low arc shot circling him as he skids to a stop in front of a steaming noodle stall, swings the backpack off one shoulder, and hands the paper bag to the waiting vendor. The middle-aged vendor with a warm raspy voice (S1) says: <d>[English] Right on time, kid.</d> The rain and sizzle carry the scene to the end.

overall_soundscape: Steady rain hisses on asphalt and tent canvas throughout, layered with distant market chatter and the clatter of woks. Bicycle tires swish through puddles, a bell rings twice, and a hard braking skid ends in dripping water and rising steam.

non_diegetic_music: A driving electronic beat at fast tempo with a pulsing bass line and bright synth arpeggios, easing into a half-tempo groove after the bicycle stops.
```

## Hard constraints

- Duration is a hard constraint: all cut timestamps strictly increase and stay within it; 4–15 seconds.
- Reflect orientation (vertical/horizontal + ratio) in the first shot's composition description.
- Never invent reference media — T2VA has none by definition.
- Output only the three prompt fields. Give the user explanations separately, after the prompt, only if they asked.
