---
name: h3-ref-prompt
description: Turns a user idea plus reference media (images, video, audio) into a full full-reference prompt for MiniMax H3 (Ref2VA). Use when the user describes a video for H3/MiniMax and attaches or points at images (first/last frame, character, style, storyboard), video (editing, continuation, motion reference), or audio (voice timbre, music). Handles duration (usually 15s), orientation, dynamic action, and smooth motion.
---

# MiniMax H3 — full-reference prompt (with reference media)

Goal: turn the user's idea and attached media into a **six-section full-reference brief** for MiniMax H3. Output is only the brief text in English (original language survives only inside `<d>` tags and in on-screen text). If there is NO media — use the `h3-t2v-prompt` skill instead.

## Step 0. Inputs

- List the media and their **roles** (ask the user if unclear): first-frame anchor / last-frame anchor / keyframe / general reference (character, scene, style, voice timbre, soundtrack, source video).
- **Media order is semantic**: labels are numbered by input order, independently per category — `<Picture 1..N>`, `<Video 1..N>`, `<Audio 1..N>`. Never rename, skip, renumber, or reorder.
- Ask in one message what's missing: duration (4–15s, this user defaults to 15), orientation (16:9 / 9:16), speech and its language.
- Audio can never be the only media — only alongside an image or video.

## Output format (exactly six sections, in this order)

```text
subject_definitions:
...

summary:
...

retention_analysis:
...

detailed_description:
...

overall_soundscape:
...

non_diegetic_music:
...
```

### 1. subject_definitions

One line per label: what it denotes, its role, the key features to follow.

- `<Subject N>` — reusable visible content: people, animals, objects, scenes, wardrobe, props, styles, actions, poses. A content unit, not the source file. One subject may combine several assets: `<Subject 1> is the woman whose appearance comes from <Picture 1> and whose walking motion comes from <Video 1>.`
- `<Picture N>` — a standalone line ONLY if the image itself serves as a concrete frame (first/last frame, keyframe, composition anchor) or storyboard. If an image only defines a character/style, cite it inside the `<Subject N>` definition instead of creating a separate line.
- `<Video N>` — only for whole-video relationships: the edited source, a continuation start point, a reference for structure/editing/rhythm. Visible content reused from a video still goes under `<Subject N>`.
- `<Audio N>` — copied or referenced audio: voice timbre, music style, a copied track. If bound to a speaking subject: `<Audio 1> is the voice-timbre reference for <Subject 1> (S1).`

### 2. summary

One short paragraph. Opens with a task-type prefix combined with ` + ` (no repeats):

- `keyframe completion` — an image serves as a concrete frame (first/last/keyframe).
- `reference generation` — an asset guides character/scene/style/motion/storyboard without being a concrete frame.
- `video editing` — a source video is directly modified. Then continue with: `The target video is an edited version of <Video 1>.`
- `video continuation` — new content continues a source video.
- `audio reuse` — the audio signal is copied in full or in part.
- `audio reference` — the signal is not copied; only style/timbre/rhythm is referenced.

Include a type only if an asset genuinely plays that role. A video used only for motion/rhythm = `reference generation`, not editing/continuation. Introduce no new labels here.

### 3. retention_analysis

One line per label. Fixed markers:

- Visual: `fully_preserved | partially_preserved | attribute_transfer | weak_reference`
  Format: `<Subject 1> (appears in [Shot 1], [Shot 3]): fully_preserved - identity, hair, and pink shirt retained.`
- Audio: `fully_copy | partially_copy | reference | weak_reference`
  Format: `<Audio 1>: reference - the target speaker follows <Audio 1>'s timbre without copying the signal.`
- No `(Sx)` in this section. New actions/backgrounds in the target video are not a loss of reference fidelity.

### 4. detailed_description — the body (350–500 words for generation)

- Style — 1–2 sentences BEFORE `[Shot 1]`, including orientation: `The target video is in a cinematic live-action style with warm lighting, vertical 9:16 framing.`
- `[Shot 1]` has no timestamp; later `[Shot N] At MM:SS.mmm, the shot cuts to ...` — strictly increasing times within the duration.
- At the first appearance of a `<Subject N>`, describe its referenced features, position in frame, and current action; afterwards reuse the label without redefining. Name wardrobe in text even for referenced subjects — H3 drifts wardrobe.
- Frame anchors in natural phrasing: `the shot begins from <Picture 1>`, `the shot's keyframe corresponds to <Picture 2>`, `the shot ends on <Picture 3>`.
- Anchor roles:
  - **First-frame**: first-frame anchor → action onset → continuous development → result/reaction. Describe the motion LEAVING the frame; do not re-describe the image.
  - **First+last**: describe the interpolation path between the frames (a SINGLE shot is preferred); the final shot must land exactly on the last frame: first-frame state → observable intermediate changes → progressively narrowing differences → last-frame state.
  - **Last-frame only**: infer a plausible preceding state and converge onto the image in the final shot.

### Dynamism / smoothness / aliveness rules (user priority)

- The timeline is consecutive beats, each with ONE primary change and an observable end state (something a viewer could point at).
- The most important beat goes in the MIDDLE of the timeline (the model squeezes the ending).
- A complex action (hand-off, pose change) takes ~4 seconds. Doesn't fit — cut the least important one.
- A cut = new information (subject/space/state/viewpoint/time). Just getting closer — use camera motion.
- Smoothness: continuous action development inside the shot; continuity across cuts — carrying motion, sound `continues seamlessly across the cut`, character reactions.
- Emotion → observable: where the eyes go, what the hands do, breathing, what stays still. Micro-detail: fabric, hair, steam, glints, background life.

### Camera — always explicit

One move per shot, as a natural sentence: `The camera pushes in with small amplitude at slow speed toward her hands.` Vocabulary: `Zoom In/Out`, `Push In/Pull Out`, `Pan Left/Right`, `Truck Left/Right`, `Tilt Up/Down`, `Pedestal Up/Down`, `Arc Shot`, `Tracking Shot`, `Static Shot`, `Shake Slightly/Strongly`, `POV`, `Roll Clockwise/Counterclockwise`. Amplitude `with small/large amplitude`, speed `at slow/fast speed` (omit medium/normal). Static — `the frame never moves` plus the list of forbidden moves.

### Speakers and audio

- A speaking referenced subject: `<Subject 2> (S1) turns and says, <d>[English] ...</d>`. `(Sx)` is assigned in the order of actual vocal events and reused; off-screen speech by the same subject keeps the form plus `off-screen`.
- A voice inside a directly reused soundtrack — the source is `<Audio N>`; do NOT invent an `(Sx)`.
- With `audio reference` (timbre/rhythm only) — do NOT carry the reference audio's original words into the target. With direct reuse of lines — verbatim, unintelligible spans `[unclear]`, punctuation `, . ? !`.
- Voiceover: `says in an off-screen voiceover` + `while his lips remain completely closed.` A line across a cut — `<scenetrans>` at both ends + a continuity phrase. Truncated by the video end — `<cutoff>`. End of speech — lips close, articulation ceases.
- `<d>` languages: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish.
- On-screen text — in double quotation marks, verbatim; if no text should appear, say so explicitly.

### 5. overall_soundscape

1–4 sentences in one paragraph: ambience, physical sounds, non-verbal human sounds. Do not duplicate dialogue/diegetic music. Copy/reference relationships for the ambience/SFX layer go here: `The copied ambience layer from <Audio 1> continues throughout the target video.`

### 6. non_diegetic_music

1–3 sentences: instrumentation, tempo, dynamics; no abstract mood words. Audience-only copy/reference goes here: `<Audio 2> is directly reused as the complete audience-only score.` `N/A` if none.

## Hard constraints

- Every label must map to a real input asset — invent nothing, drop nothing that was attached.
- Duration is a hard constraint (4–15s): all timestamps strictly increase and fit inside it.
- Six sections, brief text only; explanations separately and only on request.

## Mini example (first-frame anchor + voice timbre)

```text
subject_definitions:
<Subject 1> is the red-haired woman in <Picture 1>, with a freckled face, a cropped olive bomber jacket, and black cargo pants.
<Picture 1> is the first frame of [Shot 1], showing the woman on a rooftop at dusk.
<Audio 1> is the voice-timbre reference for <Subject 1> (S1), containing a low, steady female voice.

summary:
[keyframe completion + reference generation + audio reference] The target video opens on <Picture 1> and follows <Subject 1> as a gust of wind hits the rooftop; she speaks one line using the voice timbre referenced from <Audio 1>.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - identity, red hair, freckles, olive bomber jacket, and black cargo pants retained.
<Picture 1> ([Shot 1] first frame): fully_preserved - the shot begins exactly from the rooftop dusk composition.
<Audio 1>: reference - only the low, steady timbre guides <Subject 1>'s delivery; the original signal is not copied.

detailed_description:
The target video is in a cinematic live-action style with cool dusk tones, vertical 9:16 framing.
[Shot 1] The shot begins from <Picture 1>: <Subject 1>, the red-haired woman with a freckled face in a cropped olive bomber jacket and black cargo pants, stands at the rooftop edge. The camera arcs right with small amplitude at slow speed as a gust of wind snaps her jacket open and tears loose papers from a stack beside her into the air. She turns her head against the wind, hair whipping across her face, and <Subject 1> (S1) says in the low, steady voice referenced from <Audio 1>, <d>[English] There it is.</d> Her lips close and stay still.
[Shot 2] At 00:05.000, the shot cuts to a tracking shot following one tumbling sheet of paper as it sails over the ledge into the blue dusk light; her fingers enter the frame a moment too late and close on empty air. The paper spirals down toward the street as the camera tilts down to follow it through the end of the video.

overall_soundscape:
A strong wind buffets the rooftop with flapping fabric and scattered paper rustle; distant traffic hums far below throughout.

non_diegetic_music:
A sparse synth pad at a slow tempo with a single repeating piano note, swelling slightly as the paper falls.
```
