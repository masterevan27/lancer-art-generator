# animate-portrait.py

Turns an image into a looping animated `.webp`. Point it at a portrait and you
get the same face, alive: a slow blink, a few degrees of head tilt, the start of
a smile. Point it at a scene with `--background` and you get a living
establishing shot instead — drifting smoke, moving cloud, flickering lights —
sized for a SillyTavern chat background. Either way it writes the animation next
to the source image.

It is a standalone entry point rather than a flag on `generate-npc.py` because
it takes an image, not a rolled NPC. It has no use for the tables, the manifest
or the output tree, and it never writes to any of them. The only thing it
borrows is `generate-art.py`'s ComfyUI plumbing — the client and the port
probe.

The name is now narrower than the script. `--background` is a flag rather than a
second script because everything below the defaults — the upload, the graph, the
two-stage denoise, the ping-pong loop, the download — is one job either way, and
because the filename is referenced from `lancer-npc-import-gui`'s settings.

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
- **KJNodes**, for the ping-pong loop only. `--no-pingpong` renders a second
  checked-in workflow that has no such nodes in it, so that mode runs on stock
  ComfyUI alone.

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

# a background that runs once forward instead of ping-ponging, same length
python animate-portrait.py canyon.png --background --no-pingpong

# build the job and print the graph without queueing anything
python animate-portrait.py portrait.png --dry-run

# animate a background instead: widescreen, scene motion, scene table
python animate-portrait.py canyon.png --background
python animate-portrait.py canyon.png --background --roll --seed 7
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

## Backgrounds

`--background` swaps one bundle of defaults as a set. Nothing else about the
run changes.

| | portrait | `--background` |
|---|---|---|
| render size | 480×480 | 832×480 |
| motion prompt | breathe, blink, faint smile | smoke, cloud, lights, wind |
| negative prompt | guards the face's identity | guards the geometry from crawling |
| `--roll` reads | `## Animation` in `npc-generator-tables.md` | `## Background Animation` in `scene-and-spaceship-tables.md` |
| ComfyUI output folder | `AnimatedPortraits/` | `AnimatedBackgrounds/` |
| `--quality` | 90 | 80 |

Every one of those is still overridable. `--background --size 640` renders
square, `--background -d "..."` writes its own motion, `--background --tables
other.md` reads someone else's pool.

832×480 is Wan 2.2's native landscape bucket, and SillyTavern scales a
background to the window with CSS, so rendering larger buys render time and
nothing else. Quality drops to 80 for the same kind of reason: the chat UI
fetches this file on every page load, and a 64-frame 832×480 webp at quality 90
is several megabytes of wallpaper.

### The `## Background Animation` table

The scene-side twin of `## Animation`, living in
`prompts/scene-and-spaceship-tables.md` because scene motion is not an NPC
trait. Same format, same `--seed` reproducibility, edited by the import GUI's
Tables tab like any other.

Its bullets follow one extra rule the portrait table does not need: **none of
them names a subject.** No character, no figure, no pronoun, no face or hair.
A background has nobody in it, and a clause about a person is an invitation for
Wan to draw one into an empty frame. What the bullets do name is weather, light,
machinery and sky — smoke, cloud, rain, snow, embers, neon, holographic
readouts, searchlights, a dropship crossing the far distance — plus a clause
saying the buildings and terrain hold still, because the way an animated
establishing shot fails is geometry that crawls. A test enforces the
subject-free rule and the camera-lock clause, so a bullet that breaks either
fails the suite rather than a render.

### If you have no background to animate yet

`--background` takes an image, same as the portrait path. To get one, render
the `Default Animated Background` section of
`prompts/scene-background-art-prompts.md` first — a wide dusk landing yard
composed for this job, with a quiet middle where the chat panel sits and plenty
of smoke, dust, cloud and lights at the edges for the Wan pass to move.

```
python generate-art.py --prompts prompts/scene-background-art-prompts.md --filter Default-Animated-Background --width 1920 --height 1080 --download-to G:\art\backgrounds
python animate-portrait.py "G:\art\backgrounds\<the rendered png>" --background --roll --seed 7
```

Two commands rather than one because the still is a Krea 2 job and the
animation is a Wan job. Any wide image works here; the shipped prompt is a
starting point, not a requirement.

### Installing it in SillyTavern

Copy the finished `.webp` into SillyTavern's backgrounds folder, which for the
default profile is:

```
<SillyTavern>/data/default-user/backgrounds/
```

Then open **User Settings**, find the **Character Handling** group in the
right-hand column, and tick **Animated background thumbnails**. That checkbox
matters more than its tooltip admits: with it off, SillyTavern substitutes a
frozen still frame for the applied background, not just for the picker grid.
Refresh the page, open the background menu, and pick the new file. Use the lock
button there while you are in a particular chat to pin it to that chat rather
than globally.

Character avatars are a different story and no file you produce here will help
with them. SillyTavern re-encodes every uploaded avatar to a static PNG,
because the character card format stores its JSON in a PNG text chunk. An
animated avatar is flattened to its first frame on upload. The nearest
equivalent is an expression sprite, which is served from disk untouched: drop
the `.webp` into `data/default-user/characters/<Character Name>/` as
`neutral.webp` and enable the Character Expressions extension.

## The loop

The animation is generated forward, then played forward and back — so it ends
on exactly the frame it started on and loops with no visible cut. The reversed
half skips one frame at each end, because those two frames are already on
screen: without that trim the loop stutters on a doubled frame at the
turnaround and again at the seam.

This doubles playback length for free. The default 33 generated frames become a
64-frame, 4-second loop at 16 fps.

### Playing forward instead

Ping-pong is wrong for some motion. Smoke that drifts left and then, visibly,
right again reads as a video being scrubbed rather than as weather; so does
cloud crossing a sky, a rotating fan, or anything else with a direction. That
is a background problem more often than a portrait one, because a blink and a
head tilt genuinely do return to where they started and drifting weather never
does.

`--no-pingpong` renders a second workflow —
`Util_Portrait_to_AnimatedWEBP_Wan22_Forward_v1.json` — which is the same graph
with the reverse-trim-rejoin tail replaced by a save node wired straight to the
decode. Same models, same seed, same two-stage denoise; only the saving
differs. It is a separate file rather than three deletions at run time because
those three nodes are the only KJNodes in the graph, and as a file of its own
it opens and runs on stock ComfyUI.

The loop is the same length either way. `--frames` defaults to `33` when the
loop doubles it and `65` when it does not, so both modes produce a roughly
4-second animation at 16 fps. They land one frame apart, not exactly equal: a
ping-pong total is always even and a Wan length is always odd, so 64 played
frames become 65.

That length is not free the second time. Ping-pong buys its second half by
replaying frames that are already rendered; forward-only has to render them,
so the same 4 seconds costs roughly twice the time and produces roughly twice
the file. Passing `--frames` yourself overrides the default in both modes, and
means frames generated in both — `--no-pingpong --frames 33` is a 2-second
animation, not a 4-second one.

## Options

| Flag | Default | |
|---|---|---|
| `--background` | off | animate a scene rather than a face; swaps every default marked below |
| `-d`, `--describe` | the idle motion above | the positive prompt |
| `--roll` | off | draw the prompt from the preset's table instead of `-d` |
| `--tables` | `prompts/npc-generator-tables.md` | the file `--roll` reads; `scene-and-spaceship-tables.md` with `--background` |
| `--negative` | a static/identity-drift guard | the negative prompt; a static/crawling-geometry guard with `--background` |
| `--out` | `<image>-animated.webp` | output path |
| `--size` | `480` | square render size, snapped down to a multiple of 16 |
| `--width`, `--height` | — | override `--size`; `832`×`480` with `--background` |
| `--frames` | `33` | frames generated, snapped down to `4n+1`; `65` with `--no-pingpong` |
| `--fps` | `16` | playback rate written into the webp |
| `--steps` | `20` | total sampler steps, split evenly between the two passes |
| `--cfg` | `3.5` | |
| `--seed` | `-1` (roll one) | pin it to reproduce a result |
| `--quality` | `90` | webp quality, 0–100; `80` with `--background` |
| `--no-pingpong` | off | play forward only, at the same length and about twice the render |
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
stack — an RTX 3080 12 GB with 32 GB of system RAM — both model loads included:

| preset | render | output |
|---|---|---|
| portrait, 480×480, 33 frames | 198 s (~13 GB RAM free) | — |
| `--background`, 832×480, 33 frames | 364 s (~4.9 GB RAM free) | 3.9 MB |

Raising `--frames` or `--size` raises the render time roughly in proportion.
Start at the defaults, find a description and a seed you like, and only then
turn the quality up on that seed.

`--no-pingpong` roughly doubles both numbers at the shipped defaults, because
it renders the frames ping-pong gets by replaying.

The background number is worth a second look for a different reason: 3.9 MB is
a lot of wallpaper for a page that fetches it on every load. `--quality` is a
weak lever here — dropping it from 80 to 50 saves under a third — so if the
file needs to be smaller, cut `--frames` instead. 25 frames still ping-pongs
into a 48-frame, 3-second loop. A forward-only background is the expensive
choice on both counts, and worth it only when the motion has a direction the
reverse would give away.

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
figures is the floor for a default run on a 32 GB machine, and it is a narrow
gap — an 832×480 `--background` render later completed cleanly with ~4.9 GB
free. Treat anything under ~5 GB as a coin flip rather than a hard failure.

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
script patches it and queues it. `--no-pingpong` patches and queues
`Util_Portrait_to_AnimatedWEBP_Wan22_Forward_v1.json` instead, which is the
same file through step 3 and skips step 4.

1. The portrait is uploaded to ComfyUI's input folder (rather than referenced
   by path — the server may not share a filesystem with this script).
2. `WanImageToVideo` builds a video latent with the portrait as its first
   frame.
3. Two `KSamplerAdvanced` passes denoise that one latent: the high-noise UNet
   runs the first half of the steps and hands over its leftover noise, the
   low-noise UNet finishes. Same seed, same step count, handover at the
   midpoint — it is one denoise across two models, not two renders.
4. The decoded frames are reversed, trimmed and rejoined into the ping-pong
   loop. `--no-pingpong` has no such nodes; the decode feeds the save directly.
5. `SaveAnimatedWEBP` writes it, and the script downloads it to `--out`.

## Tests

```
python -m unittest test.test_animate_portrait
python -m unittest test.test_animation_table
python -m unittest test.test_background_animation_table
```

The graph half runs anywhere. The live half re-derives every required input
from a running ComfyUI's `/object_info`, so a renamed model or a moved input
fails there rather than three minutes into a render; it skips when no server
answers.
