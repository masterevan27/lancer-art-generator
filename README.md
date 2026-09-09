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

### `generate-spaceship.py`

Rolls random spaceships — patrol boats up to fleet carriers — from the tables in
`prompts/spaceship-generator-tables.md` and generates each one a matched portrait
and token, the same shape `generate-npc.py` produces for people. It shares that
script's markdown table parser, theme filters, glow subsystem and ComfyUI
plumbing by loading `generate-npc.py` by path rather than duplicating it — the
same technique `generate-3d.py` already uses for `DEFAULT_MANIFEST` — so it
changes zero lines of `generate-npc.py`, `generate-art.py` or `generate-3d.py`.
What a hull is allowed to carry (which sizes a Ship type can roll, which
equipment tables a given size may reach) lives in `ship_policy.py`.

Unlike an NPC, a ship's token is not one fixed size: Foundry draws it across
1 to 5 grid hexes depending on the rolled Size band, so the token's canvas, its
aspect and the framing language in its prompt all vary per ship, and the
manifest entry carries the grid width and height for the Foundry importer to
set `token.width`/`token.height` from.

```
python generate-spaceship.py --dry-run --count 20
python generate-spaceship.py --count 3
python generate-spaceship.py --ship-type carrier --size huge
python generate-spaceship.py --ship-catalogue
```

Start with `--dry-run`, same as the other two generators. See
[`docs/spaceship-render-notes.md`](docs/spaceship-render-notes.md) for notes
from the first real renders, including an open, unresolved framing issue on
the largest (multi-hex) hulls.

### `generate-3d.py`

Turns an NPC already in `.generated-npcs.json` into a printable 32 mm STL, a
cleaned 3D shell and four turnaround renders, by re-rendering its token in a
forced A-pose and reconstructing from that. Needs a running ComfyUI and
Blender 5.2. See [docs/generate-3d.md](docs/generate-3d.md).

```
python generate-3d.py --filter Sokolova
```

### `animate-portrait.py`

Turns any portrait image into a looping animated `.webp` — a slow blink, a
faint smile, a few degrees of head tilt — through Wan 2.2 image-to-video. It
takes an image rather than a rolled NPC, so it is not wired into the
generators; run it by hand on whatever portrait you like, or from the import
GUI's NPC page, whose Animated portrait panel runs it over a rolled NPC's
portrait. `--roll` draws the motion from the `## Animation` table in
`prompts/npc-generator-tables.md` — the one table there the NPC generator
never rolls, written to move hair, clothing and backdrop while the figure
holds still. Needs a running ComfyUI with the Wan 2.2 I2V models. See
[docs/animate-portrait.md](docs/animate-portrait.md).

```
python animate-portrait.py "Jules Sokolova Portrait.png"
python animate-portrait.py portrait.png -d "she laughs and looks away"
python animate-portrait.py portrait.png --roll --seed 7
```

### Tests

Standard library `unittest`, no dependencies:

```
python -m unittest discover test
```

Tests load the generator by path (its hyphen makes it non-importable) and roll
against `test/fixtures/tables-minimal.md` rather than the live tables, so
authoring a bullet never breaks a test. The exceptions are the guards that have
nothing to say about a fixture, and so read the live tables file: where a
`@theme` tag may appear, the Headgear register's classification, and the check
that the `npc-trait-import` skill documents every flag the tables actually use.
That last one exists because the skill's own handoff checklist refuses a staged
bullet whose flag is undocumented, which had quietly drifted five flags behind.

**Changing the tables means re-checking that skill, and two test files enforce
it rather than leaving it to habit.** The skill is documentation the generator
silently depends on: a staging run copies its shape lines to write bullets, and
`generate-npc.py` ignores an unrecognized flag rather than reporting one, so a
skill that has fallen behind produces bullets that fail quietly in the render.

- `test/test_import_skill_flags.py` — every flag the tables use appears in all
  **three** places the skill names flags: its §0 flag table, its §4 per-table
  shape lines, and its §3 routing rows. Add a flag and all three must follow.
  A flag a run must never author (`Weapon/none`, `Headgear/bare` — an image
  cannot show an absence) is exempted by name in `NEVER_STAGED`, with a reason.
- `test/test_import_skill_shape.py` — the two gaps that one leaves. Every table
  the generator rolls either has a shape line or is named in `NOT_STAGED` with
  a reason, so a **new table** cannot be added without a decision about whether
  the skill stages it; and each shape line's `||` **segment count** matches
  what the generator actually reads, so a bullet staged from it cannot put its
  flags where `flags_for()` reads prose. It also pins the three-segment table
  list against `flags_for()` itself, so a fourth added there fails here.

Between them: add a flag, add a table, or change a table's shape, and the suite
tells you exactly which part of the skill to update.

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

Prompt length is measured too, against Krea 2's 512-token ceiling — a prompt
that runs long silently loses its tail, which is where the palette and the
flat-white background instruction live:

```
python -m test.prompt_budget
```

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

## Staged imports, and table presets

Two folders under `prompts/` hold JSON written by tooling rather than by hand,
and they are tracked on opposite terms because they are opposite kinds of file.

`prompts/staged-imports/` is a working folder for candidate NPC-table entries
extracted from reference images (see the `npc-trait-import` skill below). Its
JSON files are gitignored so a run doesn't dirty the tree; `examples/` holds
three worked examples that stay tracked as a reference for the file shape.

`prompts/presets/` holds **table presets** — a snapshot of which bullet is
enabled in every table and at what roll weight, saved as one file. This is the
default location the Import GUI (below) writes them to; nothing in this
repository reads or writes them, and the generator itself is unaware of them,
since a preset is applied by editing `npc-generator-tables.md` in place rather
than by being passed to a run. They are **not** gitignored, unlike the staged
imports beside them: a preset is meant to be handed to another GM, so a named
one is content worth keeping in history. That does mean saving a preset leaves
the tree dirty until you commit it or throw it away.

## The Import GUI

The tool that edits the tables and turns a rolled NPC into a Foundry Actor
lives in a sibling clone at `G:\GIT-REPOS\lancer-npc-import-gui`. It reads
this repository directly — `.generated-npcs.json` for the run log,
`prompts/npc-generator-tables.md` for the tables, and the two folders above —
and shells out to `generate-npc.py` to roll new NPCs and re-roll single traits.

Nothing here depends on it: the generator runs standalone, and every table edit
it makes is an edit you could make in a text editor. It matters to this
repository only because it is a second writer of
`prompts/npc-generator-tables.md`, so a table's on-disk shape — the `- ` bullet
under a `##` heading, the `|| flag` suffixes, the `xN ` weight prefix — is a
contract between the two, not just a convention. See that repository's README.

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

## The `spaceship-trait-import` skill

`.agents/skills/spaceship-trait-import/SKILL.md` (Codex) and its matching
`.claude/skills/spaceship-trait-import/SKILL.md` extract spaceship traits from
reference images. Invoke `spaceship-trait-import` with images or a folder.
It stages candidates in `prompts/staged-imports-spaceship/` with reference
copies for the Import GUI's **Spaceships → Trait Imports** view. Hulls,
equipment, scenes and lighting follow the ship generator's type/size policies;
the skill leaves the live tables unchanged for selective review.

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
