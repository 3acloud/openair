# Long-form video: 30 to 60 seconds in one file

H3 tops out at 362 frames per generation, about 15 seconds. Past that it
extrapolates and the scene drifts. Longer clips are built by **chaining**: each
shot starts from the last frame of the previous one, the duplicated seam frame
is trimmed, and the pieces are joined with continuous audio.

Measured on 4x RTX 3090 at 1344x768 with the 4-step Turbo LoRA: **30 seconds in
33 minutes, 40 seconds in 44 minutes.** Without Turbo the same 40 seconds takes
roughly three hours.

Everything here is on top of [the main setup](README.md). Do that first.

## Setup, four commands

### 1. Install the multishot pack

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/jlucasmcrell/ComfyUI-H3-Multishot
```

### 2. Install the patch

The pack builds its sampler from a **name** out of `comfy.samplers.KSampler`, so
a SAMPLER made by another node cannot be plugged in. MiniMax H3 runs video and
audio on two different flow schedules, and the 4-step Turbo distill ships its
own sampler for exactly that; a stock sampler over-steps the audio at 4 steps
and breaks it. Without a way to connect the Turbo sampler, chaining is stuck at
20 steps.

This patch adds that input. It runs in memory at startup and **modifies nothing
on disk**, so `git pull` in the pack will not wipe it:

```bash
cd ComfyUI/custom_nodes
mkdir -p ComfyUI-H3-Multishot-Patch
curl -o ComfyUI-H3-Multishot-Patch/__init__.py \
  https://raw.githubusercontent.com/alesha-pro/tools/main/minimax-h3/custom-nodes/longform-patch/__init__.py
```

### 3. Restart ComfyUI and confirm

```bash
grep H3MultishotPatch path/to/comfyui.log
```

Expected:

```
[H3MultishotPatch] H3MultishotSampler: added sampler_opt and evict_text_encoder
[H3MultishotPatch] H3MultishotMemorySampler: added sampler_opt and evict_text_encoder
```

If instead you see a warning that the pack is not installed, the patch loaded
before it. Rename the folder so it sorts after (any name later in the alphabet
than `ComfyUI-H3-Multishot` works, `-Patch` already does).

### 4. Load the workflow

Drag [`07-long-form-chained-shots.json`](07-long-form-chained-shots.json) onto
the canvas. It ships with a working four-shot script already filled in.

## What the patch adds

**`sampler_opt` (SAMPLER).** Connect the Turbo sampler here. When connected it
overrides `sampler_name`, so the chain runs at 4 steps. The log line
`[H3MultishotPatch] using the connected SAMPLER` confirms it took effect.

**`evict_text_encoder` (BOOLEAN, default ON).** Before every shot the pack
pushes the text encoder to CPU and calls `free_memory` on 90% of the default
device. On a single card that is the whole point: it stops the DiT loading
partially and streaming weights from RAM, which the pack author measured as 60
minutes against 15 on one render. On a multi-GPU split it backfires: if the DiT
runs on cuda:0 and cuda:1 while the encoder runs on cuda:2 and cuda:3 they never
compete for memory, and the purge evicts the DiT instead, which then reloads
every shot. **Single card: leave it ON. Split across cards: turn it OFF.**

Both defaults keep stock behaviour, so existing graphs are unaffected.

## Writing the script

One prompt per shot, separated by a line of three dashes. Same three-field
format as the single-shot workflows.

⚠️ **A prompt must not start with a square bracket.** The parser reads it as
JSON and the run dies with a JSON error. Markers like `[Shot 1]` are pointless
here anyway, since each prompt is already its own generation.

### Three beats per shot, and this is the whole game

The most common failure is not a broken setup, it is an overloaded prompt.
Smears trailing behind moving objects and ripples across the background come
from asking for too much at once.

Measured on the same 124-frame slice, one seed, six events against two:

| prompt | steps | LoRA | frames changing |
|---|---|---|---|
| six events | 4 | turbo | 30.4% |
| six events | 8 | turbo | 31.3% |
| six events | 20 | none | 29.1% |
| **two events** | **4** | **turbo** | **8.7%** |

⚠️ That last column counts pixels changing between neighbouring frames, so it
measures **motion, not blur**. A sharp fast pan and a smeared one score the
same, which is why the three top rows look identical. Do not read the third row
as "Turbo is free": watch those two clips side by side and the 20-step run
without the LoRA is clearly cleaner, keeping skin texture on faces and readable
edges on anything moving fast.

What the table does show is the gap between six events and two. The model
cannot resolve that many things happening at once, so it smears whatever it
cannot place, and cutting events helps at any step count.

Keep it to three beats per ten seconds and one camera move per shot. Six
shooters plus return fire plus two bodies over a railing plus a magazine change
plus a vault, in one shot, is a guaranteed smear.

### Keeping the character

Re-describe the same identifying details in every prompt: clothing, gear,
distinguishing marks. The chain carries the last frame forward, but the encoder
reads each prompt fresh.

**A first-person view removes the main Turbo risk**, since the distill damages
skin on close-ups and there are no faces in frame. If you do shoot faces close,
keep `low_vram` ON in the Turbo LoRA node, which is the default. The workflow
[README](README.md#turbo-lora-notes) has the measurements behind that.

**Describe open space explicitly in the sound**, for example flat gunshots with
no echo. Otherwise H3 adds room reverb in the middle of a desert.

### Hide the seam in the writing

End every shot but the last on a held frame, and open the next one from that
same held frame. One sentence at the end of the prompt does it: *the camera
settles on the canyon ahead, the frame going still for a beat.* Then start the
next prompt with *continuing from the exact first frame,* plus the pose the
character was left in.

This works because the seam is only visible where motion jumps across it.
Measured on a 30-second port chase: movement on the five frames around the joint
was 0.2 to 2.2 against a median of 13.1 for the clip, and the audio level
stepped by 0.025 where a typical transition in the same track steps by 0.127.
Nothing to see and nothing to hear.

The reverse is what produces the classic click: a shot ending mid-gunfire
against one opening on rain. On an earlier desert clip that seam jumped 0.65
against a 0.21 threshold. The 40 ms crossfade is too short to cover it, so
handle it in the prompt rather than in the editor.

## Settings

**SHOT DURATION** is in seconds on the green node, frames are computed for you.
The model only takes lengths of the form 17k+5, so it rounds up to the nearest
valid one: 10 seconds becomes 243 frames, 5 becomes 124, 15 becomes 362.

**Short shots are cheaper than long ones for the same total length.** Attention
cost grows faster than frame count, so cutting a clip into more, shorter shots
wins. Measured at 1344x768 on 4x RTX 3090:

| shot length | frames | seconds per step | per shot |
|---|---|---|---|
| 10 s | 243 | ~135 s | ~11 min |
| 15 s | 362 | ~290 s | ~20 min |

A 50% longer shot costs more than twice as much. Thirty seconds as three shots
of 10 seconds takes 33 minutes; the same thirty seconds as two shots of 15 takes
about 42. Reach for 15-second shots when a single continuous take matters, not
to save time.

**Total length runs slightly under the sum of the shots**, because each seam
drops the duplicated frame. Four shots of 243 frames give 969, not 972, so 40.4
seconds instead of 40.5.

**shot_count 0** means one shot per prompt. A number from 1 to 8 forces the
count: extra prompts are dropped, missing ones repeat the last.

**seed_per_shot ON.** The pack author measured that a single seed across all
shots makes both the face and the voice drift. Identity lives in the
conditioning, not the seed.

## Known limits

**Audio seams.** The crossfade is hardcoded at 40 ms, too short to cover a loud
shot meeting a quiet one. Write the seam quiet instead of fixing it afterwards,
see [Hide the seam in the writing](#hide-the-seam-in-the-writing).

**Inherited damage.** The last frame of a shot conditions the next one, so any
defect crosses the seam and sets in. A bad first shot means a bad chain.
Regenerate instead of pushing on.

**Encoder cost.** The prompt is re-encoded once per shot, roughly a minute on a
25 GB int8 encoder split across two cards. It does not scale with clip length,
so on short drafts it is a large share of the total and on full renders it is
around 10%.

## Longer than a minute

For 12 to 30 shot chains the pack ships `H3 Multishot Sampler + Memory`. Plain
chaining shows each shot exactly one image, the previous last frame, so identity
error compounds hop by hop. The memory sampler keeps a persistent anchor from
the start of the piece and shows it to the encoder on every shot, so drift
cannot accumulate. The patch covers that node too. I have not tested it: at four
shots there is nothing to drift.
