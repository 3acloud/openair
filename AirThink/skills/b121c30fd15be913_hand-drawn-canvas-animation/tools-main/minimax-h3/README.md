<div align="center">

# MiniMax H3 on your own hardware

**Video and synchronized audio in one pass.** Voice, effects and music get
generated together with the picture, not layered on afterwards.

Eleven ComfyUI workflows, the custom nodes they need, and an installer that sets
it all up. Built and measured on 4x RTX 3090.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](../LICENSE)
[![Model](https://img.shields.io/badge/model-MiniMax%20H3-black.svg)](https://huggingface.co/Comfy-Org/MiniMax-H3)
[![Benchmarks](https://img.shields.io/badge/measured%20on-4x%20RTX%203090-76b900.svg)](https://x.com/superalesha)

</div>

---

## Install

```bash
./install/setup.sh check                              # what you have, what is missing
./install/setup.sh standard --comfy /path/to/ComfyUI  # or: multi-gpu --dir ~/comfy-raylight
./install/download-models.sh --dir /path/to/ComfyUI/models
```

`check` installs nothing. It reads your cards, your CUDA and your power limits,
then tells you which of the two sets fits your machine.

---

## Two sets

<table>
<tr>
<td width="50%" valign="top">

### standard

**Any single card, 24 GB and up.**

Seven workflows: text-to-video, image-to-video, reference-to-video, 1080p
upscale, and long-form chaining.

DisTorch2 spreads the weights across whatever cards you have, so big models fit
on small boxes. Every loader still points at `cuda:0`, so extra cards give you room for
bigger models while the speed stays the same.

[→ workflows/standard](workflows/standard)

</td>
<td width="50%" valign="top">

### multi-gpu

**Two cards or more.**

Four workflows where every card actually computes. One Raylight worker per GPU,
sequence split between them.

**3.12x on four cards.** A 15-second shot samples in 6:41 instead of 19 minutes.

Installs into its own directory, because Raylight pins an older torch than
current ComfyUI ships with.

[→ workflows/multi-gpu](workflows/multi-gpu)

</td>
</tr>
</table>

---

## Speed

4x RTX 3090, 1344x768, pruned int8 base, 320 W per card.

| | standard | multi-gpu |
|---|---:|---:|
| seconds per step, 5-second clip | 87.4 | **28.0** |
| sampling, 15-second shot | ~19 min | **6:41** |
| whole run, 15-second shot | 22:05 | **15:16** |

Scaling across cards on the same clip and prompt:

| cards | s/step | speedup |
|---:|---:|---:|
| 1 | 87.4 | 1x |
| 2 | 36.0 | 2.43x |
| 4 | **28.0** | **3.12x** |

<details>
<summary>Why the whole-run gap is smaller than the sampling gap</summary>

Encoding the prompt and decoding frames through the VAE cost the same either
way, and on short clips they dominate the clock. The longer the shot, the more
the parallelism shows. On a 5-second clip you barely notice it. On 15 seconds it
is the difference between one coffee and three.

</details>

---

## The turbo LoRA

The [turbo LoRA](https://huggingface.co/larryvrh/MiniMax-H3-Turbo-Lora) takes
sampling from 20 steps down to 6, which is what makes H3 practical at home.

Use **`v4_step600_ema`**. It fixes the over-sharpened, plastic look of the older
v1 line and is much better on static and small-motion shots. The old `ckpt850` still wins in one
case, because v4 smears at 4 steps with fast motion, so the installer fetches
both files. The author recommends 6 to 8 steps at strength
exactly 1.0, and says it stops helping past 8.

> **The multi-gpu set needs a patch that ships here.** The LoRA's tensors are
> named in a way ComfyUI's loader does not recognise, so the stock loader loads
> **zero keys** and samples without it. Nothing errors out. It just looks like
> turbo made no difference at all.

<details>
<summary>What the patch actually does</summary>

It rebuilds the name map by hand, the way the reference node does, and splits
the LoRA down two paths.

The 208 backbone modules go through a bypass injection, `out = base(x) +
lora(x)`, which never touches the weights. That keeps int8 quantization and FSDP
weight sharding working.

The 51 adaln modules get re-injected at run time instead. On a pruned base they
cannot be a weight patch at all, because their update lives in a 2688-dim space
that the pruned checkpoint collapsed into an 8-dim curve, leaving the layer 8
wide against the LoRA's 2688.

You can see it took effect in the log on model load:

```
[H3TurboRay rank 0] ... 208 adapters, 208 hooks + 51 adaln at run time
```

If that line is missing, the LoRA is being ignored.

</details>

---

## Clips longer than 15 seconds

H3 tops out at 362 frames per generation. Longer clips get chained together, so
the last frame of one shot becomes the first frame of the next.

Write the shots into one field, separated by a line with `---`:

```
A rain-soaked container port at night, the camera walks forward and stops.

---

The same port. A steel door swings open ahead, light spilling across wet ground.
```

Use as many shots as you want. The duration applies to each one, so three shots
at 15 seconds gives you a 45-second clip. The node handles the seam by dropping
the duplicated frame along with its audio and crossfading the join over 40 ms.

Write shot two so it continues shot one, with the same scene, the same light and
the motion carrying on. The join stays invisible when a shot ends on stilled
movement and the next one picks it up.

---

## Contents

| | |
|---|---|
| [`workflows/standard`](workflows/standard) | seven workflows, any hardware |
| [`workflows/multi-gpu`](workflows/multi-gpu) | four workflows, two cards and up |
| [`custom-nodes/h3-ray-kit`](custom-nodes/h3-ray-kit) | frame-size presets including portrait, duration in seconds snapped to the model's frame grid, shot chaining from one script |
| [`custom-nodes/h3-turbo-ray`](custom-nodes/h3-turbo-ray) | the turbo sampler as an importable module, so Ray can ship it to workers |
| [`custom-nodes/longform-patch`](custom-nodes/longform-patch) | keeps the chaining node from fighting MultiGPU over memory |
| [`patches`](patches) | the turbo LoRA name-map rebuild |
| [`skills`](skills) | agent skills that turn a rough idea into a proper H3 prompt |

Every graph carries its own guide cards on the canvas: what each knob does, what
it costs, and which values I actually run.

---

## Things that waste your afternoon

Check your power limit first. Cards ship at whatever the vendor set, and it is
often well under the default. Mine were at 220 W against a 350 W default, and
raising them to 320 took an identical run from 220 seconds down to 170.

```bash
nvidia-smi --query-gpu=name,power.limit,power.default_limit --format=csv
```

System RAM matters more than you expect. ComfyUI pins most of it while loading,
and the kernel can kill the process without leaving a useful message anywhere.
On 32 GB, `--disable-pinned-memory` is what stands between a working install and
a silent exit code 0.

The prompt encoder is 25 GB and already int8, so there is nothing left to
squeeze out of it. Running it on CPU costs about 27 seconds per run and frees up
the room the model needs.

---

<div align="center">

Measured on 4x RTX 3090, 96 GB total, PCIe 3.0 x16, no NVLink, Ubuntu.
Numbers come from real runs, not datasheets.
Absolute times will differ on your machine, the ratios usually hold.

I post the benchmarks behind all of this, with the argv and raw logs attached:
**[@superalesha](https://x.com/superalesha)**

</div>
