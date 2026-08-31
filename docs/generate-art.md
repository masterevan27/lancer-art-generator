# generate-art.py — batch art generation through ComfyUI

Reads an art-prompt markdown file, pulls every prompt block out of it, and queues
one ComfyUI job per prompt against an API-format workflow. Results land in
ComfyUI's own output folder under a path mirroring the markdown headings, so the
mech catalogue's 67 prompts come back already sorted by manufacturer and role.

Standard library only — no `pip install` step. It talks to ComfyUI over plain
HTTP (`/prompt`, `/history`, `/view`).

## Requirements

- Python 3 on `PATH`.
- ComfyUI running. The script probes `127.0.0.1:8000-8015` — the same range
  `StackLauncher.ps1` watches, since Comfy Desktop walks upward when 8000 is
  busy — and exits with a clear message if nothing answers. Use `--server` for
  anything else.
- The models the workflow references. The default template wants
  `krea2TurboOfficialComfy_krea2TurboInt8`, `qwen3vl_4b_bf16`,
  `qwen_image_vae`, and the `detail_slider_krea2` LoRA.

## Quick start

Look before you leap — neither of these queues anything:

```
python generate-art.py --list
python generate-art.py --dry-run
```

Then the full catalogue:

```
python generate-art.py --steps 8 --post rmbg --resume
```

That is 67 prompts at roughly 50 seconds each on an RTX 3080 (8 steps,
1024×1280), plus about 15 seconds per image for background removal — call it an
hour. `--steps 8` matches the "Shared settings" section of the prompt files; the
saved workflow is at 10.

Paths resolve relative to the script itself, so this works from the repository
root or anywhere else.

## What it reads

`--prompts` accepts any of the collections in `../Art Prompts/`:

| File | Prompts |
| --- | --- |
| `mech-catalogue-art-prompts.md` (default) | 67 |
| `battlemap-art-prompts.md` | 6 |
| `equipment-art-prompts.md` | 4 |
| `scene-background-art-prompts.md` | 1 |

A prompt block is either a fenced code block or a blockquote — the mech and
equipment files use fences, the battlemap and background files use `>`. Whichever
heading sits closest above the block names the entry, and the headings above that
become its folder path. Blocks shorter than 200 characters and those under
`Settings` / `Foundry note` headings are skipped, which is how the shared-settings
blocks stay out of the run.

The mech catalogue's 67 comes from 65 chassis plus the two `**Alternate look…**`
prompts (Assault and Cataphract). Alternates take the bold lead-in as a filename
suffix and can be isolated or excluded with `--only-alternates` /
`--skip-alternates`.

## What it writes

Into ComfyUI's output folder, under two roots: generated images go beneath
`--output-prefix` (default `LancerMechs`), post-processed ones beneath
`--post-prefix` (default `LancerFoundryTokens`). The folder path below the root
is the same in both — the markdown headings, so manufacturer and class survive:

```
LancerMechs/Player-Frames/IPS-Northstar/Blackbeard_00001_.png
LancerMechs/NPC-Mech-Classes/Striker/Cataphract_Alternate-look-heavy-cavalry_00001_.png

LancerFoundryTokens/Player-Frames/IPS-Northstar/Blackbeard_rmbg_00001_.png
LancerFoundryTokens/NPC-Mech-Classes/Striker/Cataphract_Alternate-look-heavy-cavalry_rmbg_00001_.png
```

Splitting the roots makes `LancerFoundryTokens/` a self-contained tree of
transparent PNGs to hand to Foundry, with no raw generations mixed in to strip
out first.
`--post-prefix LancerMechs` puts the two side by side again, the way earlier runs
wrote them.

ComfyUI treats `/` in a `filename_prefix` as subfolders and appends its own
counter. `--download-to` copies results somewhere else as well; ComfyUI always
keeps its own copy either way.

## Options

Nothing is required — a bare `python generate-art.py` generates the whole mech
catalogue at the workflow's saved settings.

**Sources**

| Option | |
| --- | --- |
| `--prompts PATH` | Art-prompts markdown file. Default: the mech catalogue. |
| `--workflow PATH` | API-format workflow template. Default: `Lancer_Scene_Workflow_v1.json`. |

**Selection**

| Option | |
| --- | --- |
| `--filter REGEX` | Only entries matching, case-insensitive, against name and section path — `--filter HORUS`, `--filter "NPC-Mech-Classes/Support"`. |
| `--exclude REGEX` | Skip entries matching. |
| `--skip-alternates` | Primary prompt per mech only. |
| `--only-alternates` | Just the "Alternate look" prompts. |
| `--limit N` | Stop after N entries. |
| `--start-at NAME` | Skip forward until an entry matches. |

**Generation**

| Option | |
| --- | --- |
| `--variants N` | Images per prompt, each with its own seed. Multiplies runtime. |
| `--seed N` | Base seed; variants use N, N+1, … Default is random per image. |
| `--steps` `--cfg` `--sampler` `--scheduler` | Override the sampler. |
| `--width` `--height` | Override the latent size. |
| `--set NODE.input=value` | Patch any input of the generation workflow — `--set 181.strength_model=0.4`. Repeatable. Generation workflow only; post workflows aren't covered. |

**Post-processing**

| Option | |
| --- | --- |
| `--post WORKFLOW` | Run an image→image workflow on each result. Repeatable, runs in order. Takes a path or the shorthand `rmbg`. |
| `--post-only` | Skip generation; run the chain over images already in the manifest. |
| `--post-output NODE` | Node id to save from, when a post workflow has no SaveImage. |

**Output**

| Option | |
| --- | --- |
| `--output-prefix NAME` | Top-level subfolder for generated images. Default `LancerMechs`. |
| `--post-prefix NAME` | Top-level subfolder for `--post` results. Default `LancerFoundryTokens`. |
| `--download-to DIR` | Also copy finished images here. |
| `--manifest PATH` | Run log. Default `.generated-manifest.json` beside the script. |
| `--resume` | Skip entries already in the manifest. |

**Run mode**

| Option | |
| --- | --- |
| `--server ADDR` | ComfyUI address, e.g. `127.0.0.1:8000`. Default: probe 8000–8015. |
| `--list` | List what would run, then exit. |
| `--inspect` | Print each workflow's nodes and the inputs the script writes, then exit. |
| `--dry-run` | Build and validate every job, queue nothing. |
| `--dump-job PATH` | With `--dry-run`, write the first built job out for inspection. |
| `--timeout SECONDS` | Per-image ceiling. Default 1800. |

## Post-processing passes

`--post` feeds each finished image into an image→image workflow, and chains if
given more than once — stage two receives stage one's output. `rmbg` is shorthand
for `Util_RemoveBackground_makeTransparent.json`, which returns the transparent
PNGs the Foundry token pipeline wants:

```
python generate-art.py --steps 8 --post rmbg
```

Outputs are suffixed with the stage name and written under `--post-prefix`, so
`LancerMechs/…/Blackbeard_00001_.png` is joined by
`LancerFoundryTokens/…/Blackbeard_rmbg_00001_.png` at the same sub-path.

To run a pass over images generated earlier, without regenerating them:

```
python generate-art.py --post rmbg --post-only
```

That reads the manifest and reuses each entry's stage-0 images, so a chain is
never re-fed its own output.

A post workflow needs a `LoadImage` node, which receives the previous stage's
image. If it has no `SaveImage`, the script promotes the `PreviewImage` at the end
of the longest chain — the finished pass rather than a debug tap — strips the
spare previews so they don't each write a temp file, and prints what it chose.
`--post-output` overrides that pick.

## Which workflows it runs

Everything lives in `../Workflows/ComfyUI API runnable/`, resolved relative to
the script rather than the working directory. A default run touches exactly one
file; the second only appears if you ask for a post pass:

| File | When |
| --- | --- |
| `Lancer_Scene_Workflow_v1.json` | Every run. The `--workflow` default. |
| `Util_RemoveBackground_makeTransparent.json` | Only with `--post rmbg`, the shorthand this maps to. |
| `Util_Krea2_Inpaint_v1.json` | Never on its own — pass the path to `--workflow` or `--post`. |
| `lancer-scene-workflow-with-vars.json` | Never on its own — but works as a `--workflow` drop-in. Same graph with `%prompt%` / `%seed%` placeholders, in the two nodes the script overwrites anyway. |
| `Lancer_Scene_Workflow_for_girls_v1.json` | Never from this script. `generate-npc.py` routes NPCs who read as women through it automatically — see [generate-npc.md](generate-npc.md#women-render-through-their-own-workflow). Valid as a `--workflow` value here if you want it. |

The sibling `ComfyUI Importable/` folder holds the UI-format exports for opening
in ComfyUI itself. Those won't run here — see below.

## Inspecting and patching a workflow

`--inspect` lists every node in the workflows this run would use, tagged with the
inputs the script writes:

```
python generate-art.py --inspect --post rmbg
```

```
   51  CLIPTextEncode      [CLIP Text Encode (Prompt] <- prompt text
   54  KSampler            [KSampler]                 <- seed, steps, cfg, sampler_name, scheduler
   57  EmptyLatentImage    [Token Image Size]         <- width, height
   69  SaveImage           [Save Image]               <- filename_prefix
  181  LoraLoader          [Load LoRA (Model and CLI]
```

Anything untagged is left at whatever the workflow was exported with. `--set`
reaches those — LoRA strength, denoise, a different checkpoint — without editing
and re-exporting the file:

```
python generate-art.py --set 181.strength_model=0.4 --set 54.denoise=0.85 --dry-run
```

Values parse as JSON when they can (`0.4` is a number, `true` a boolean) and stay
plain text otherwise, which is what a `.safetensors` filename needs. `--set` is
applied last, so it beats `--steps` and friends. An unknown node id fails before
anything is queued. It patches the generation workflow only — post workflows have
their own node ids and aren't covered.

## The workflow template

Must be **API format** (**Workflow → Export (API)**), not the UI format with
`nodes` and `links`; the script says so plainly if handed the wrong one. See the
root README for why both copies exist.

Rather than relying on placeholder strings, the script walks the graph from
`SaveImage` back through `KSampler` to its positive `CLIPTextEncode` and
`EmptyLatentImage`, and writes those nodes directly. A re-export with different
node ids still works. It also drops nodes nothing consumes — spare
`EmptyLatentImage` nodes left over from editing, for instance — and refuses to
run if a `%placeholder%` it cannot fill survives into the job.

## Resuming

Every finished entry is appended to `.generated-manifest.json` (gitignored) with
its seed, timestamp, and output filenames. Ctrl-C is safe: the manifest is
flushed after each image, and `--resume` picks up from there. The recorded seed is
what lets you reproduce or re-roll one specific mech later.

Ctrl-C also tells ComfyUI to stop — it POSTs `/interrupt` and clears the queue, so
the job in progress doesn't keep running on the server after the script is gone.

A job that vanishes from ComfyUI's queue without landing in its history — the
server restarted, or you cancelled it from the web UI — is detected within a few
seconds rather than stalling until `--timeout`. And if ComfyUI accepts a job but
reports per-node complaints, those are printed as `! node_errors` instead of
turning up later as a bad image.

A failed job reports ComfyUI's own validation detail and the run continues to the
next entry, so one bad mech doesn't abort the batch. The exit code is 1 if
anything failed.

## Troubleshooting

| Message | Cause |
| --- | --- |
| `No ComfyUI found on 127.0.0.1:8000-8015` | Server isn't up, or it's on another host — start the stack, or pass `--server`. |
| `looks like a UI-format workflow` | Point at the copy in `ComfyUI API runnable/`, or re-export. |
| `value_not_in_list … sampler_name` | An override naming something this install doesn't have. |
| `no SaveImage or PreviewImage node` | A post workflow with no output node; add one and re-export. |
| `left the queue without finishing` | ComfyUI restarted, or the job was cancelled from the web UI. The entry is marked failed and the run moves on. |
| `--set: node N is not in this workflow` | Run `--inspect` for the node ids this workflow actually has. |
| `still has unfilled placeholders` | The template has `%vars%` in nodes the script doesn't patch. Give them real values before exporting. |

Note that ComfyUI's `%date:…%` and `%Node Title.widget%` filename substitutions
are applied by its web frontend, not the server, so they pass through literally on
anything submitted over the API. The script sets each `filename_prefix` itself, so
this only matters if you add such tokens to a workflow by hand.

---

## generate-npc.py

A companion script that rolls random human NPCs from
`../Art Prompts/npc-generator-tables.md` and gives each one a matched portrait
and transparent token. It imports this script's ComfyUI plumbing rather than
duplicating it, so the server discovery, workflow overrides and post-processing
described above apply to it unchanged.

One difference worth knowing before reading it: `generate-npc.py` does not run a
single workflow per invocation the way this script does. NPCs who read as women
render through `Lancer_Scene_Workflow_for_girls_v1.json` and everyone else
through the `--workflow` default, so a mixed run queues against both.

It has its own doc: **[generate-npc.md](generate-npc.md)**.
