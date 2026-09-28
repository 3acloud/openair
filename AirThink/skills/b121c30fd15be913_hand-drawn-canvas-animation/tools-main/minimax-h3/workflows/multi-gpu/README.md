# MiniMax H3 across several GPUs

Four workflows that make H3 actually use every card you have, instead of parking
weights on the spare ones and computing on one.

## Why this exists

The standard workflows in [`../standard`](../standard) split the model with
DisTorch2. That works on any hardware, from a single 24 GB card upward, but every
loader points at `cuda:0` — the other cards hold weights and idle. More cards buy
you capacity, not speed.

[Raylight](https://github.com/komikndr/raylight) runs one worker process per card
and cuts the sequence between them (USP, via xDiT). All four cards compute.

Measured on 4x RTX 3090, 1344x768, pruned int8 base:

| cards | seconds per step | speedup |
|---|---|---|
| 1 | 87.4 | — |
| 2 | 36.0 | 2.43x |
| 4 | 28.0 | 3.12x |

On a full 15-second shot (362 frames, the model's per-generation ceiling) that is
**6:41 of sampling against roughly 19 minutes** on the DisTorch path.

The gap narrows on the total wall clock — 15:16 against 22:05 — because encoding
the prompt and decoding frames through the VAE cost the same either way, and on
short clips they dominate. The longer the clip, the more the parallelism shows.

## The four workflows

| file | what it does | steps |
|---|---|---|
| `01-t2v-4gpu-turbo` | one clip, turbo LoRA | 6 |
| `02-t2v-4gpu-base` | one clip, no LoRA | 20 |
| `03-longform-4gpu-turbo` | shots chained from one script, turbo LoRA | 6 |
| `04-longform-4gpu-base` | shots chained, no LoRA | 20 |

Each graph is laid out in three columns: what you change on the left, the plumbing
collapsed in the middle, the output on the right. The plumbing is collapsed rather
than hidden — the wiring stays readable, it just does not eat the screen.

## What you actually touch

**Frame size** is a preset, not a megapixel dial. H3 works off a 768 px short edge
in multiples of 32, so there are only a handful of sane options: 1344x768 down to
864x480 landscape, 768x1344 down to 480x864 portrait, 768x768 square.

**Duration** in seconds. The node snaps it onto the model's 17k+5 frame grid at
24 fps and caps it at 362 frames, so you cannot accidentally ask for something the
model refuses.

**Steps.** 6 with the turbo LoRA, 20 without. The LoRA's author recommends 6-8 and
notes that 4 steps smear on fast motion; above 8 it stops helping.

**Prompt**, and for the long-form graphs, a script.

## Long-form

H3 tops out at 362 frames per generation. Longer clips are built by chaining: the
last frame of a shot becomes the first frame of the next one.

Write the shots into one field, separated by a line with `---`. As many pieces as
you want, the duration applies to each shot. Three shots at 15 seconds gives a
45-second clip.

The node handles the seam: the duplicated frame is dropped along with its audio
(otherwise the soundtrack drifts a frame ahead of the picture on every join), and
the audio is crossfaded over 40 ms so the splice does not click.

Write shot two so it continues shot one — same scene, same light, motion carrying
on. The join is invisible when a shot ends on stilled movement and the next picks
it up. A shot that ends mid-action makes the cut obvious.

## Setup

This set needs its own environment: Raylight pins torch 2.8.0, older than current
ComfyUI ships, so it does not go on top of a working install.

```bash
./install/setup.sh check                     # what you have
./install/setup.sh multi-gpu --dir ~/comfy-raylight
./install/download-models.sh --dir ~/comfy-raylight/models
```

The turbo LoRA needs a patch that ships in this repo. Its weights are named in a
way ComfyUI's loader does not recognise — point the stock loader at it and it
quietly loads **zero keys** and samples without the LoRA at all, which looks like
"turbo made no difference" rather than like an error. The patch rebuilds the name
map by hand: 208 backbone modules through a bypass injection, and 51 adaln modules
re-injected at run time, because on a pruned base those cannot be applied as a
weight patch at all — the update lives in a 2688-dim space the pruned checkpoint
collapsed into an 8-dim curve.

You can see it took effect in the log on model load:

```
[H3TurboRay rank 0] ... 208 adapters, 208 hooks + 51 adaln at run time
```

No such line means the LoRA is being ignored.

## Notes from running it

**FSDP is not optional** at 362 frames. Without weight sharding every card holds
the full model and the run does not fit in 24 GB. It costs nothing in speed and is
already on.

**The prompt encoder runs on CPU.** It is 25 GB and there is no room for it beside
the model once dynamic VRAM is off. Moving it to a GPU saves about 27 seconds per
run, which is not worth the memory.

**Cards keep their memory between runs** on purpose, so the next run does not wait
for the model to load. Free them with the stack's stop script.

**Check your power limit.** Cards shipped below their default sample slower —
raising 3090s from 220 W to 320 W (their default is 350) took an identical run from
220 to 170 seconds. `sudo nvidia-smi -i N -pl 320`, resets on reboot.
