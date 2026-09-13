# Expression sprites

`generate-expressions.py` turns one original portrait into static WebP sprites
for SillyTavern's Character Expressions extension. It can read a generated NPC
from `.generated-npcs.json`, or work directly from any PNG, JPEG or WebP.

Every sprite is a separate Qwen image edit of the original portrait. The
script never chains one generated expression into another, which prevents a
poor result from changing the identity of every later sprite.

## Requirements

- A running ComfyUI, discovered on `127.0.0.1:8000-8015` unless `--server` is
  supplied.
- The Qwen Image Edit model, Lightning LoRA, CLIP and VAE named in
  `workflows/api/Util_Expression_QwenEdit_RMBG_v1.json`.
- The `RMBG` custom node and its `RMBG-2.0` model for the default transparent
  output.

The script uses only Python's standard library. Pillow is not required. A live
probe on ComfyUI 0.35.1 confirmed that `RMBG` output 0 is RGBA and that a
one-frame `SaveAnimatedWEBP` at lossy quality 90 preserves its alpha channel.
The graph therefore connects those nodes directly.

## Common recipes

```powershell
# Preview all missing default labels for one manifest NPC; queue nothing.
python generate-expressions.py --id npc-jules-sokolova-40213 --dry-run

# Generate all missing defaults for every NPC matching a name/category/path.
python generate-expressions.py --filter Sokolova

# Add two new joy variants to an NPC.
python generate-expressions.py --id npc-jules-sokolova-40213 -e joy --count 2

# Replace every existing joy sprite, but only after the first new render works.
python generate-expressions.py --id npc-jules-sokolova-40213 -e joy --count 2 --replace

# Redo precisely one existing sprite.
python generate-expressions.py --id npc-jules-sokolova-40213 --file joy-1.webp

# Use an arbitrary portrait and choose the output folder.
python generate-expressions.py --image portrait.png --out G:\art\hero-expressions -e joy,anger

# One custom expression, with a reproducible render seed.
python generate-expressions.py --image portrait.png --custom "battle focus=cold focused determination" --seed 90
```

NPC selection accepts repeatable `--id`, plus `--manifest`, `--filter`,
`--exclude` and `--limit`. Supplying any of those selects NPC mode. Image mode
uses `--image`; `--out` defaults to `<image stem>-expressions/` beside the
source, and `--name` supplies its display name. Exactly one source mode is
required.

## Labels and prompt tables

With no expression flags, the script walks the 28 SillyTavern/GoEmotions
labels in their declared order. A full `all` run skips a label when any sprite
already exists. An explicit subset such as `-e joy,anger` adds variants even
when those labels already exist.

`prompts/expression-tables.md` has one weighted `## label` pool per default.
`--tables PATH` selects another file, including the path configured as
`expressionTablesPath` by the import GUI. Tables use the NPC generator's
parser: `xN` weights are expanded, repeated heading blocks form one pool, and
GUI-disabled `<!-- - ... -->` bullets do not roll. `--describe TEXT` replaces
the roll for every selected label.

`--custom "label=prompt"` may be repeated. Labels are lowercased; whitespace
and non-`[a-z0-9_]` characters become underscores. Omit `=prompt` when that
custom label already has a table. A custom-only command generates only its
custom labels; explicit `-e all` generates all defaults plus the customs.

SillyTavern does not discover arbitrary label names from files. Add every
custom label to the Character Expressions extension's custom-expression list
before expecting it to select that sprite.

The companion Import GUI sends the NPC's configured manifest and expression
tables as explicit `--manifest` and `--tables` arguments. This keeps a
relocated manifest or tables file consistent between its Expressions editor and
the render job. A GUI request with only custom chips sends only those customs;
it does not silently expand to all default labels.

## Prompts and identity

Every instruction fixes the character, face, hairstyle, outfit, colours, art
style, framing and pose, then asks only for a facial expression and small body
language. NPC mode adds the recorded Hair, Hair colour, Feature, Outfit and
Headgear as identity anchors. Demeanor, weapons, gear, backdrop and stance are
deliberately excluded because they can conflict with the requested emotion or
alter the composition. Image mode has no manifest traits and uses the fixed
identity instruction plus the selected expression.

## Variants, replace and redo safety

The first sprite is `<label>.webp`; later numeric variants take the lowest
free `<label>-N.webp`. Existing dot variants such as
`joy.expressive.webp` are recognized as the same label.

- Add mode is the default. Explicit labels/customs get `--count` new files.
- `--replace` removes every base, numeric and dot variant for each selected
  label, then writes fresh files from the base name. The first new WebP is
  rendered and held before anything old is deleted. If it fails, old images
  and metadata remain byte-for-byte intact; later labels still run.
- `--file NAME.webp` overwrites exactly one existing classified basename and
  rejects multi-sprite options. A custom sprite with no current table reuses
  its saved full prompt from `expressions.json`; a supplied `--describe` or a
  current table produces a fresh prompt instead.

Both sprite files and `expressions/expressions.json` are installed through
sibling temporary files and atomic renames. The sidecar records label, full
prompt, seed, background mode, source path and source modification time in Unix
milliseconds, plus generation time. The GUI uses that source timestamp to mark
sprites made from an older portrait.

## Rendering and quality

Transparency is the default. `--keep-background` bypasses and removes the
unused RMBG node from the queued graph. `--quality` is WebP quality from 0 to
100 (default 90); `--steps` defaults to the Lightning workflow's 4. A seed is
random per sprite unless `--seed S` is supplied, in which case plans use
`S`, `S+1`, and so on in render order.

`--dry-run` prints each destination, label and complete prompt. It does not
probe ComfyUI, upload the source, create the output folder, or change the
sidecar. Rendering failures are reported and do not stop remaining sprites.
Exit status is 0 for success, 1 when any render fails, and 2 for invalid usage
or input.

Treat a successful render as a candidate, not identity proof. A live Qwen/RMBG
smoke render produced a transparent 1024×1024 RGBA WebP, but lost the source
portrait's spectacles. Inspect sprites before importing them and use an
exact-file redo when a face, accessory, or other identity detail is wrong.

Run `python generate-expressions.py --help` for the complete option list.
