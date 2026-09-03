# Lancer Art Generator

A ComfyUI-driven batch art pipeline for a *Lancer* TTRPG campaign, extracted
from the [Lancer-TTRPG-GM-Hub](https://github.com/masterevan27/Lancer-TTRPG-GM-Hub)
campaign repository into its own standalone tool. Two entry points —
`generate-art.py` and `generate-npc.py` — turn prompt-table markdown into
batches of ComfyUI renders in the campaign's house style.

**This repository is a sibling clone of `Lancer-TTRPG-GM-Hub`, not a
submodule.** It has no dependency on the Hub at runtime or in its git history;
clone it anywhere. The sibling relationship only matters for humans keeping
both checked out side by side, and for the `npc-trait-import` skill note
below.

## Tooling

### `generate-art.py`

Batch-generates images from the art-prompt markdown files through ComfyUI's HTTP
API. It pulls every prompt block out of a prompts file, queues one job per prompt
against an API-format workflow, and writes results into ComfyUI's output folder
under a path mirroring the markdown headings. Standard library only — no pip
installs. Chain image-to-image passes with `--post` to take a mech from text to
image to transparent PNG in one run; those passes write to their own root
(`LancerFoundryTokens/` by default, same heading structure underneath), so the
finished transparent PNGs are a self-contained tree to import into Foundry.

```
python generate-art.py --list
python generate-art.py --dry-run
python generate-art.py --filter blackbeard --variants 3
```

Start with `--list` or `--dry-run`. Full documentation:
[`docs/generate-art.md`](docs/generate-art.md).

### `generate-npc.py`

Rolls random human NPCs — pilots, mechanics, dock hands, corpo liaisons — from
the tables in `prompts/npc-generator-tables.md` and generates each one a
matched pair of images in the campaign's house style: a 1024x1024 portrait
for the Foundry actor sheet, and a full-body token run through background
removal into a transparent PNG. Both come from the same roll, so they depict
the same person. Each NPC gets its own folder under the output root, holding
the two images and a markdown dossier recording the rolled traits, the seed,
and both prompts verbatim.

It's a separate entry point rather than a flag on `generate-art.py` because that
script's whole model — filtering, resuming, the manifest, the output tree — is
keyed to the headings of an authored prompt file, and a random NPC has no such
entry to key against. All the ComfyUI plumbing is imported from `generate-art.py`
rather than duplicated.

```
python generate-npc.py --dry-run --count 5
python generate-npc.py --count 3
```

Adding options to a table needs no code change — every `-` bullet under a `##`
heading in the tables file is one option. The exception is `GENDER_TRAITS` in the
script, a short clause the prompt asserts for every NPC of one gender rather than
rolling for it, since a single bullet in a pool of thirty rarely comes up. Full
documentation, including worked examples for rolling a whole group of related NPCs:
[`docs/generate-npc.md`](docs/generate-npc.md).

### Tests

Standard library `unittest`, no dependencies:

```
python -m unittest discover test
```

Tests load the generator by path (its hyphen makes it non-importable) and roll
against `test/fixtures/tables-minimal.md` rather than the live tables, so
authoring a bullet never breaks a test. The exceptions are the guards on where
a `@theme` tag may appear, which have to read the live tables file to say
anything at all.

Theme visibility is measured rather than asserted, because the number is a
property of the content and the content is authored over time:

```
python -m test.theme_visibility                  # the live tables
python -m test.theme_visibility --tables test/fixtures/tables-themed.md
```

That prints, per theme and per gated table, how much content the theme has and
how often a rolled NPC of that theme actually got one of its bullets rather
than a neutral one. Run it while tagging to watch a theme come up. It reports
zeroes today, which is the correct pre-tagging baseline.

### Output location

Both scripts write renders under ComfyUI's own output folder. Set
`COMFYUI_OUTPUT_DIR` to point at a ComfyUI install elsewhere on your machine;
if it's unset, they fall back to an `output/` folder beside the scripts (i.e.
at the repository root), so a fresh clone runs without any configuration.

### Workflow formats

<details>
<summary><strong><code>workflows/</code> keeps the same graphs twice, because ComfyUI uses two incompatible JSON shapes</strong></summary>

- **`workflows/editable/`** — UI format, with node positions and links. Drag these
  onto the ComfyUI canvas to edit them by hand.
- **`workflows/api/`** — API format, a flat map of node ids. This is what
  the `/prompt` endpoint accepts and what `generate-art.py` consumes.

Edit the editable copy, then re-export via **Workflow → Export (API)** to
refresh its API-format twin.

</details>

## Staged imports

`prompts/staged-imports/` is a working folder for candidate NPC-table entries
extracted from reference images (see the `npc-trait-import` skill below). Its
JSON files are gitignored so a run doesn't dirty the tree; `examples/` holds
three worked examples that stay tracked as a reference for the file shape.

## The `npc-trait-import` Claude Code skill

`.claude/skills/npc-trait-import/SKILL.md` extracts backdrops, poses, gear,
outfits, hair, expressions and similar traits out of reference images and
stages them as candidate entries for `prompts/npc-generator-tables.md`. It is
only picked up by Claude Code when Claude Code is run **from this
repository's root** — Claude Code discovers skills under the current
project's `.claude/skills/`, not from an arbitrary working directory. If you
want it available while working elsewhere (e.g. from the Hub), symlink it
into your user-level skills directory instead of copying it, so edits here
stay the single source of truth (adjust the source path if you cloned this
repository somewhere other than `/g/GIT-REPOS/lancer-art-generator`):

```
ln -s "/g/GIT-REPOS/lancer-art-generator/.claude/skills/npc-trait-import" ~/.claude/skills/npc-trait-import
```

## License

Dual-licensed, because this repository holds both prose and code:

- **Written material** — the prompt tables under `prompts/`, and other
  documentation — under
  [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
  See [`LICENSE`](LICENSE). The prompt tables are the headline content here —
  the house style people actually want — so this is the license that governs
  most of what you'd copy out of this repository.
- **Code** — `generate-art.py`, `generate-npc.py`, and the JSON presets,
  configs, and workflows — under the MIT license. See
  [`LICENSE-CODE`](LICENSE-CODE).

*Lancer* is a trademark of Massif Press. This is an unofficial fan project, not
affiliated with or endorsed by Massif Press, and contains no rulebook text.
