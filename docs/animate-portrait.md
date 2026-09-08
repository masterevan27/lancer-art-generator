# animate-portrait.py

Turns a portrait image into a looping animated `.webp` — the same face, alive:
a slow blink, a few degrees of head tilt, the start of a smile. Point it at any
image on disk and it writes the animation next to it.

It is a standalone entry point rather than a flag on `generate-npc.py` because
it takes an image, not a rolled NPC. It has no use for the tables, the manifest
or the output tree, and it never writes to any of them. The only thing it
borrows is `generate-art.py`'s ComfyUI plumbing — the client and the port
probe.

`generate-npc.py` never calls it. `lancer-npc-import-gui`'s NPC page does -
its Animated portrait panel runs this script over the NPC's portrait with a
description chosen from the `## Animation` table - and it is equally a tool
you run by hand on any image.

## Requirements

- A running ComfyUI (the same one the other scripts use; probed on ports
  8000–8015).
- Three models, all of which the campaign stack already has:
  - `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` and
    `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` in `models/diffusion_models`
  - `wan_2.1_vae.safetensors` in `models/vae`
  - `umt5_xxl_fp8_e4m3fn_scaled.safetensors` in `models/text_encoders`
- **KJNodes**, for the ping-pong loop only. `--no-pingpong` drops those three
  nodes from the graph and runs on stock ComfyUI nodes alone.

The VAE is the Wan **2.1** one on purpose. `wan2.2_vae` belongs to the 5B TI2V
checkpoint; the 14B high/low-noise I2V pair this workflow uses is a 2.1-VAE
model, and pairing it with the wrong VAE decodes to noise without anything
upstream complaining.

## Usage

```
# the default idle animation, written beside the source image
python animate-portrait.py "Jules Sokolova Portrait.png"

# say what the character should do
python animate-portrait.py portrait.png -d "she laughs and looks away"

# pick the output, and pin the seed so a good result is repeatable
python animate-portrait.py portrait.png --out G:\art\jules.webp --seed 12345

# longer and larger - costs render time roughly linearly
python animate-portrait.py portrait.png --frames 49 --size 640

# draw the description from the tables file's ## Animation table
python animate-portrait.py portrait.png --roll --seed 7

# build the job and print the graph without queueing anything
python animate-portrait.py portrait.png --dry-run
```

The output defaults to `<image name>-animated.webp` in the same folder as the
source.

## The description

`-d/--describe` is the whole positive prompt, so it replaces the default rather
than adding to it. The shipped default is:

> The character breathes gently and holds the viewer's gaze. They blink slowly,
> their head tilts a few degrees, and the corner of their mouth lifts into a
> faint, subtle smile. Hair and clothing shift very slightly. The camera is
> locked off and does not move.

Two things about it are load-bearing, and worth keeping in anything you write
to replace it:

- **Every clause moves the face.** Wan animates what the prompt talks about. A
  description that mentions the room animates the room.
- **The camera is nailed down explicitly.** Given the chance Wan will invent a
  slow dolly-in, and a portrait that drifts is no longer a portrait of the
  thing it started as.

### The `## Animation` table

`--roll` draws the description from the `## Animation` table in
`prompts/npc-generator-tables.md` instead - a pool of prompts written for NPC
portraits specifically, each of which keeps the figure still and spends its
motion on what they wear and what is behind them: hair and coat tails in a
breeze, smoke, rain, snow, neon, a starfield, a ship crossing the sky. Every
bullet ends by locking the camera, for the reason above. `--seed` pins the
draw as well as the render, so `--roll --seed 7` is the same animation twice;
`--tables` points it at another file with the same heading. `--roll` and `-d`
are refused together, since each is the whole prompt.

The NPC generator never rolls that table - nothing in its two image prompts
reads it - so adding bullets there changes no portrait or token. The import
GUI's Tables tab edits it like any other, and its NPC page's Animated portrait
panel offers the same list with a re-roll, which is the ordinary way to reach
this script from a rolled NPC.

Restraint reads better than instruction here. "Smiles warmly" tends to produce
a face working through a whole expression in two seconds; "the corner of their
mouth lifts into a faint smile" produces something you can loop.

The default assumes the face is visible. On a portrait shot from behind or in
hard profile — the over-the-shoulder framing the NPC generator sometimes
rolls — the blink and the smile have little to land on, and what you get is
the head turn and the hair moving. That still reads as alive, but if you want
the motion to be about the expression, either say so in `-d` or animate a
portrait that shows the face.

## The loop

The animation is generated forward, then played forward and back — so it ends
on exactly the frame it started on and loops with no visible cut. The reversed
half skips one frame at each end, because those two frames are already on
screen: without that trim the loop stutters on a doubled frame at the
turnaround and again at the seam.

This doubles playback length for free. The default 33 generated frames become a
64-frame, 4-second loop at 16 fps.

`--no-pingpong` plays forward once. Half the file size, and the only reason to
use it is if the motion you asked for genuinely ends somewhere other than where
it began.

## Options

| Flag | Default | |
|---|---|---|
| `-d`, `--describe` | the idle motion above | the positive prompt |
| `--roll` | off | draw the prompt from the tables file's `## Animation` table instead of `-d` |
| `--tables` | `prompts/npc-generator-tables.md` | the file `--roll` reads |
| `--negative` | a static/identity-drift guard | the negative prompt |
| `--out` | `<image>-animated.webp` | output path |
| `--size` | `480` | square render size, snapped down to a multiple of 16 |
| `--width`, `--height` | — | override `--size` for a non-square render |
| `--frames` | `33` | frames generated, snapped down to `4n+1` |
| `--fps` | `16` | playback rate written into the webp |
| `--steps` | `20` | total sampler steps, split evenly between the two passes |
| `--cfg` | `3.5` | |
| `--seed` | `-1` (roll one) | pin it to reproduce a result |
| `--quality` | `90` | webp quality, 0–100 |
| `--no-pingpong` | off | play forward only |
| `--dry-run` | off | print the job, queue nothing |
| `--server` | probe 8000–8015 | e.g. `127.0.0.1:8000` |
| `--timeout` | `3600` | seconds to wait for the render |

`--frames` and `--size` are snapped rather than rejected: Wan's latent is four
frames per step plus a leading one, and its grid is 16 pixels. Passing `30`
frames gets you 29 and a printed note, not a validation error from the server.

## Cost

This is a 14B model run twice over every frame, and it is the slowest thing in
this repo per output. On a 12 GB card the two UNets do not both fit in VRAM, so
ComfyUI swaps them at the handover and the first run of a session also pays to
load them from disk.

Expect **minutes, not seconds**, at the defaults. Measured on the campaign
stack — an RTX 3080 12 GB with 32 GB of system RAM, ~13 GB of it free — a
default 480x480 / 33-frame render took **198 seconds**, both model loads
included. Raising `--frames` or `--size` raises it roughly in proportion.
Start at the defaults, find a description and a seed you like, and only then
turn the quality up on that seed.

## Troubleshooting

### `hostbuf_file_reader_read failed`

The job validates, runs a few nodes, then dies inside `KSamplerAdvanced` or
`CLIPTextEncode` with:

```
RuntimeError: hostbuf_file_reader_read failed
```

**This is ComfyUI running out of system RAM, not a problem with the
workflow.** ComfyUI 0.34's DynamicVRAM (`comfy-aimdo`) streams weights
straight from the safetensors file to the GPU when it cannot hold them in
RAM, and that reader fails when memory is tight. Which node dies is
incidental — it is whichever large model got loaded first.

Confirmed on this stack: with ~4.6 GB of 31 GB physical RAM free, the same
graph failed at three different nodes across three runs, and pushing further
produced the plain-language version of the same problem —
`DefaultCPUAllocator: not enough memory: you tried to allocate 15925248
bytes`, i.e. ComfyUI could not allocate 15 MB.

Freeing memory fixed it: the same portrait, the same seed, with ~13 GB free
instead of ~4.6 GB, rendered in 198 seconds. Somewhere between those two
figures is the floor for a default run on a 32 GB machine.

**The fix is to free RAM**, in rough order of effort:

1. Restart ComfyUI. It caches every model it has loaded this session, and
   `POST /free` releases VRAM but not the host-side cache.
2. Close other memory-heavy applications (browsers, mostly).
3. Failing that, start ComfyUI with `--disable-mmap`, which takes the
   ordinary load path instead of the streaming one.

Two Wan 2.2 UNets at 14.3 GB each do not both fit alongside a text encoder
in 32 GB, so ComfyUI swaps them at the handover between passes. That is
normal and it is why the render is slow; it only becomes an error when
there is no headroom left at all.

Note that the size of a model is not what decides this. The 11 GB
`umt5_xxl_fp16` text encoder loaded cleanly in a state where the 6.7 GB
`umt5_xxl_fp8_e4m3fn_scaled` failed — the failing path is the one for
quantized (fp8-scaled) tensors. If the text encoder alone is the sticking
point, swapping the `CLIPLoader` to `umt5_xxl_fp16.safetensors` is a
workaround, at the cost of 4 GB more RAM. The Wan UNets ship only as
fp8-scaled, so they have no such alternative.

## How it works

`workflows/api/Util_Portrait_to_AnimatedWEBP_Wan22_v1.json` is the graph; the
script patches it and queues it.

1. The portrait is uploaded to ComfyUI's input folder (rather than referenced
   by path — the server may not share a filesystem with this script).
2. `WanImageToVideo` builds a video latent with the portrait as its first
   frame.
3. Two `KSamplerAdvanced` passes denoise that one latent: the high-noise UNet
   runs the first half of the steps and hands over its leftover noise, the
   low-noise UNet finishes. Same seed, same step count, handover at the
   midpoint — it is one denoise across two models, not two renders.
4. The decoded frames are reversed, trimmed and rejoined into the ping-pong
   loop.
5. `SaveAnimatedWEBP` writes it, and the script downloads it to `--out`.

## Tests

```
python -m unittest test.test_animate_portrait
```

The graph half runs anywhere. The live half re-derives every required input
from a running ComfyUI's `/object_info`, so a renamed model or a moved input
fails there rather than three minutes into a render; it skips when no server
answers.
