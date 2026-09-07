# Spaceship Generation — Implementation Design

**Target repo:** `G:/GIT-REPOS/lancer-art-generator/.claude/worktrees/ultracode-spaceships/` (all unprefixed paths below are relative to it).
**Companion:** a separate GUI design covers `lancer-npc-import-gui`. §7 and §6 are the contract that design codes against.

---

## 0. What already exists in this worktree (read this first)

Two substantial artifacts are **already committed here and are unreferenced by anything**:

| file | lines | status |
|---|---|---|
| `ship_policy.py` | 676 | Complete, self-contained, hyphen-free, importable. Zero importers today. |
| `test/test_ship_policy.py` | 683 | Complete. Its last class self-skips until the tables file lands. |

`grep -rn "spaceship\|ship_policy\|Spaceship"` across `*.py *.js *.md *.json` finds **no reference to either** outside those two files and `prompts/scene-and-spaceship-tables.md`.

Three decisions are therefore **already made** and this design does not reopen them:

1. **The tables file is `prompts/spaceship-generator-tables.md`** — pinned at `test/test_ship_policy.py:53` (`LIVE_TABLES = REPO / "prompts" / "spaceship-generator-tables.md"`).
2. **The equipment tables are named `Weapon`, `Shield generator`, `Launch catapult`, `Command bridge`** — `ship_policy.py:72-77` (`EQUIPMENT_TABLES`), singular, exactly those strings.
3. **The type/size policy matrix is `ship_policy.EQUIPMENT_POLICY`** — `ship_policy.py:313-408`, ten types, four columns, five policies, plus `DEFAULT_EQUIPMENT_POLICY` (`:422-427`), `LIGHT_CAP` (`:449-454`), `SIZE_BANDS` (`:106-134`), `SHIP_TYPES` (`:215-256`).

`ship_policy.py` is **not to be edited** by this work. It is covered by 683 lines of tests that pass today; every constant it exports is consumed as-is.

---

## 1. CODE SHAPE

### Decision: a new `generate-spaceship.py` entry point that loads `generate-npc.py` by path for shared machinery, and imports `ship_policy.py` normally. **Zero lines of `generate-npc.py` change.**

This is not the "extracted shared library" the architectural map recommended. It is deliberately not, and the reason is the constraint you set: `generate-npc.py` is 4,544 lines covered by ~50 test files that must keep passing. An extraction touches `parse_tables`'s function-attribute trick (`generate-npc.py:1266`, `parse_tables.repeated`), the `_bullet_cache` identity that `test_trait_odds.py` pins (`:2526`, and the warning at `:2518-2522` that a cached function returning a list breaks it), and four module-level assignments the *sibling repo* regex-parses out of the source text (`lib/overrideTables.js:17-46`, anchored `^NAME\s*=`). Every one of those is a way to break fifty green tests for a ship feature that has not shipped yet.

**By-path loading is established house precedent, used twice already:**

- `generate-npc.py:77-97` `_load_generator()` loads `generate-art.py` by file location, registering in `sys.modules` before `exec_module` because `@dataclass` resolves annotations through `sys.modules[cls.__module__]`.
- `test/helpers.py:18-28` `load_generator()` loads `generate-npc.py` the same way.
- `generate-3d.py:1452,1456` **already imports `generate-npc.py` as `npc_gen`** for `DEFAULT_MANIFEST`. The precedent for one generator consuming another's module is live in this repo today.

The cost the map warned about — "drags in `ROLE_CATEGORIES`, `GENDER_TRAITS`, `PORTRAIT_TEMPLATE` and the pronoun machinery" — is a few hundred microseconds of module execution and some unused names in a namespace nothing iterates. That is not a real cost. The map's other objection ("an NPC-side edit can break ship rendering") is real, and §8 answers it with a pinning test rather than with a refactor.

### Import graph

```
generate-spaceship.py                      (new, ~750 lines, hyphenated, CLI entry point)
├── art  = _load_art()      -> generate-art.py        (by path; identical to generate-npc.py:77-97)
├── npc  = _load_npc()      -> generate-npc.py        (by path; identical to generate-3d.py:1452)
└── import ship_policy as sp                          (normal import; hyphen-free by design,
                                                       ship_policy.py:34-39 says so explicitly)
```

`generate-3d.py` is untouched. `generate-npc.py` is untouched. `generate-art.py` is untouched.

### The borrowed surface — exactly these 19 names, and nothing else

`generate-spaceship.py` may reference **only** the names below off `npc`. The list is pinned by `test/test_shared_surface.py` (§8.12), so an NPC-side rename fails at test time rather than at render time. Bind them to module-level aliases at the top of the file so every use site is one grep away:

**From `generate-npc.py` (`npc.*`) — used verbatim, no adaptation:**

| symbol | line | why it is subject-agnostic |
|---|---|---|
| `parse_tables` | `:1241` | `## Heading` / `- bullet` / `xN ` only. No NPC field names. |
| `variant_table` | `:1285` | `tables[name] + tables.get("%s (%s) +")`. The variant key is a caller-supplied string — ships pass the **size band** (`Hull (huge) +`) instead of a pronoun subject. **No code change required**; only a different key. |
| `heading_for` | `:1301` | The deliberate inverse of the above, same precedence order. Feeds `trait_choices`'s `"heading"` field. |
| `split_flags` | `:2529` | `partition("||")`. |
| `split_backdrop` | `:2558` | `shot \|\| scene \|\| flags`, defaults the shot at `:2582-2583`. Ships use the identical three-segment Backdrop shape. |
| `split_faction` | `:2611` | `name \|\| visual \|\| flags`. Ships use the identical shape — see §2's `## Faction` decision. |
| `flags_for` | `:2653` | **Reusable unchanged.** It dispatches on the literals `"Backdrop"`, `"Hair colour"`, `"Faction"`. Ships have `Backdrop` and `Faction` (same shapes) and no `Hair colour` (branch never taken). Verified at `:2665-2669`. |
| `themes_of` | `:2637` | `frozenset` of `@`-stripped tags. |
| `filter_by_theme` | `:1528` | Reads `@tags` + the neutral pool. Soft (`kept or options`). |
| `apply_theme_share` | `:1550` | `n = ceil(share*len(neutral) / ((1-share)*len(tagged)))`. |
| `THEME_SHARE` | `:1098` | `0.6`. |
| `has_light_source` | `:501` | Regex over `EMITTER_WORDS` (`:429`) — `glow`, `thrusters` are not in it but `glow\w*`, `readouts?`, `beacons?`, `flares?`, `strobes?` are. Nothing in it mentions a person. |
| `light_hues` | `:507` | Hue-near-light-word scan, `_NEAR_CHARS = 24`, `_CLAUSE_BREAK` guard. |
| `glow_hue_families` | `:524` | |
| `filter_by_hue` | `:531` | |
| `filter_by_placement_prop` | `:671` | Reads `PLACEMENT_REQUIRES` (`:625`) / `PLACEMENT_FORBIDS` (`:661`). Ships pass their own dicts? **No** — these are module globals it closes over. Ships get their own copy; see "adapted" below. |
| `estimate_tokens` | `:384` | `int(len(text)/4.5)`. |
| `TOKEN_LIMIT` / `CHARS_PER_TOKEN` | `:372-373` | `512` / `4.5`. |
| `Knobs` | `:2969` | The argparse slice `art.build_job` reads: `steps, cfg, sampler, scheduler, width, height, set, output_prefix`. Constructed as `Knobs(args, size, COMFY_PREFIX)` — `size` varies per image, which is exactly what §4 needs. |
| `entry_for` | `:2987` | Builds `art.Entry(name=slug, label=stage, path=[category, slug], ...)`. |
| `fetch` | `:2992` | `/view?filename&subfolder&type` straight to a named destination. |
| `_safe` | `:2866` | Strips `<>:"/\|?*`, collapses whitespace. |
| `next_run_folder` | `:3017` | `root/runN`, first non-existent N. |
| `npc_folder` | `:2881` | Rename at the call site only: ships call it as `asset_folder = npc.npc_folder`. It is `<root>/<category>/<Name>/` with `(2)…(99)` suffixing — no NPC content. |
| `trait_cascade` | `:305` | **Cannot be reused.** Closes over module-global `TRAIT_DEPENDENTS` and `REQUIRED_TABLES`. Duplicated — see below. |

**From `generate-art.py` (`art.*`) — identical to how `generate-npc.py` uses them:**
`WORKFLOW_DIR` (`:48`), `DEFAULT_WORKFLOW` (`:51`), `POST_ALIASES["rmbg"]` (`:55`), `Entry` (`:77`), `_slug` (`:96`), `parse_set` (`:218`), `locate_slots` (`:285`), `locate_post_slots` (`:335`), `image_ref` (`:367`), `build_post_job` (`:374`), `build_job` (`:421`), `Comfy` (`:476`), `find_server` (`:596`), `load_api_workflow` (`:619`), `load_manifest` / `save_manifest` (`:629`,`:638`), `WorkflowError`.

**From `ship_policy.py` (`sp.*`):**
`SIZE_BANDS`, `SIZE_ORDER`, `size_rank`, `size_of`, `size_bounds`, `SHIP_TYPES`, `SHIP_TYPE_ORDER`, `sizes_for`, `ship_type_of`, `EQUIPMENT_TABLES`, `EQUIPMENT_POLICY`, `DEFAULT_EQUIPMENT_POLICY`, `LIGHT_CAP`, `MINIMAL_NONE_COPIES`, `NO_EQUIPMENT`, `policy_for`, `filter_by_size`, `filter_by_ship_policy`, `roll_equipment`, `armament_sentence`, `bridge_sentence`.

### Duplicated-and-adapted (written fresh in `generate-spaceship.py`)

These five are **not** reusable because each closes over an NPC module global. Each is short; the total is ~120 lines.

| function | NPC original | why it must be rewritten |
|---|---|---|
| `check_tables(tables, path, repeated=())` | `:1271-1282` | Line `:1276` reads the module-global `REQUIRED_TABLES`. 12 lines, copied with the ship list substituted. |
| `trait_cascade(name)` | `:305-362` | Closes over `TRAIT_DEPENDENTS` (`:168`) and orders by `REQUIRED_TABLES` (`:361`). Copy the worklist-over-a-`seen`-set body verbatim (`:356-362`) — explicitly not recursion, because the map is not promised acyclic (`:328-336`) — and the `ValueError` on an unknown name (`:353`), which exists because a caller feeds the result to `reroll_from_raw` as its free set and `()` would be a silent no-op. |
| `filter_by_placement_prop(options, scene)` | `:671-699` | Closes over `PLACEMENT_REQUIRES` / `PLACEMENT_FORBIDS` (`:625`, `:661`), whose prop vocabulary is `ground`/`wall`/`screens`/`signage`/`air` — human-scale props. Ships need `dock`/`vacuum`/`atmosphere`/`planetlight`/`hull`. Copy the 28-line body, supply ship dicts. |
| `roll_ship(...)` | `roll_npc` `:1737-2505` | **Not adapted — written fresh, ~200 lines.** `roll_npc` is 790 lines and its 25 in-loop `if name == …` branches (`:1905-2145`) are almost entirely wardrobe/anatomy pairings that have no ship analogue. Ships have 18 tables, two reverse-direction gates and one hard policy call. Writing 200 lines is cheaper and *far* lower-risk than parameterising 790. It reuses `roll_npc`'s **architecture** (ordered draw over `REQUIRED_TABLES`, per-table hook, `probe` recording, forced-override replacement after the draw, raw-bullet collection, flag strip, `{}` substitution) — not its code. |
| `reroll_from_raw` / `reroll_ship_trait` / `trait_choices` | `:3474`, `:3546`, `:3791` | The NPC versions call `roll_npc` by name and read `TRAIT_DEPENDENTS`. Ship versions are the same shape against `roll_ship`. `trait_choices`'s upstream-legality-from-`probe` and downstream-conflicts-by-re-probing logic (`:3839-3898`) copies almost line for line, minus the Weather exemption (`:3843`), which ships keep for the same reason (its edge is a render gate, not a filter). ~180 lines total. |

### Phase 2 (explicitly deferred, do not do it as part of this work)

Once ships have shipped and the shared surface is *empirically* known rather than guessed, extract `lancerlib/tables.py` and `lancerlib/render.py` as a **pure move with re-exports** from `generate-npc.py`, verify all ~50 test files green, and only then parameterise. `test/test_shared_surface.py` (§8.12) is what makes that later move safe: it is the written-down list of what the ship generator actually depends on.

**Hard constraint carried forward from the cross-repo contract:** `REQUIRED_TABLES`, `REROLLABLE_TRAITS`, `RAW_REROLLABLE_TRAITS` and `TRAIT_DEPENDENTS` must remain **literal top-level assignments at column 0** in *both* `generate-npc.py` (`:125`, `:3329`, `:3415`, `:168`) and the new `generate-spaceship.py`, because `server.js:976,1030` reads the source text and `lib/overrideTables.js:17-46` regex-parses it with `^NAME\s*=`-anchored patterns.

---

## 2. TABLES FILE

### Decision: a new `prompts/spaceship-generator-tables.md`. `prompts/scene-and-spaceship-tables.md` stays where it is and is not read by the generator.

**Why a new file, not growth of the staged one:**

1. `test/test_ship_policy.py:53` already names `prompts/spaceship-generator-tables.md`. Growing the other file means editing a passing test.
2. **The staged file is unparseable as-is.** Every one of its 41 bullets is hard-wrapped at ~72 columns. `parse_tables`'s bullet regex is `^-\s+(.*?)\s*$` (`generate-npc.py:1260`) — continuation lines never match and are silently dropped. Running the real parser over the file yields 20 + 21 bullets each truncated to its first physical line (`'A sleek matte-black and silver twin-boom gunship, forward-swept wings and a'`). Every bullet in `npc-generator-tables.md` is one physical line; the longest is 825 chars (`prompts/npc-generator-tables.md:2408`).
3. The staged file declares itself general-purpose and mech-facing (`scene-and-spaceship-tables.md:1-24`), and its `## Backdrop` bullets are deliberately subject-free with no `shot || scene || flags` split, no `xN` weights, and no `weather` gating (`:14-20`). The ship generator needs all three.

**What happens to its bullets:** they are an **authoring source**, mined into the new file, not moved.

- Its 20 `## Backdrop` bullets are **re-flowed to one line each** and rewritten into the new file's `## Backdrop` as three-segment `shot || scene || flags`, adding `xN` weights and role gates. Five are already ship-shaped and go in nearly as-is: `:54-58` derelict hangar, `:71-74` hangar bay, `:79-82` freighter hold, `:84-86` carrier flight deck, `:100-102` desert-grounded hauler.
- Its 21 `## Spaceships` bullets are **decomposed, not moved**. Each stacks silhouette + hardware + markings + lighting + *an embedded scene* into 32 words. Under a composed template that scene double-states the `## Backdrop` roll — verifiably so: `:172-174` duplicates Backdrop `:71-74`, `:145-147` duplicates `:104-105`, `:160-162` duplicates `:100-102`, `:142-144` duplicates `:90-92`. Mine each bullet for its vocabulary and distribute it across `## Hull`, `## Detail`, `## Weapon`, `## Command bridge`, `## Faction`, `## Markings`; discard the embedded environment.
- Add one line to `scene-and-spaceship-tables.md`'s header noting its `## Spaceships` table has been mined into `spaceship-generator-tables.md` and is no longer the ship source of truth. That is the only edit to that file.

### The 18 required tables

`REQUIRED_TABLES` in `generate-spaceship.py`, **in this order** — the order is the roll loop's iteration order, the cascade's canonical ordering, and the source of `RAW_REROLLABLE_TRAITS`:

```python
REQUIRED_TABLES = [
    "Name prefixes", "Ship names", "Theme", "Ship type", "Size", "Faction",
    "Hull", "Detail", "Weapon", "Shield generator", "Launch catapult",
    "Command bridge", "Markings", "Condition", "Backdrop", "Weather",
    "Glow colour", "Glow placement",
]
```

| # | `## Heading` | segments | flags it carries | min bullets | role |
|---|---|---|---|---|---|
| 1 | `Name prefixes` | 1 | — | 12 | Registry prefix (`ISV`, `UAD`, `Baronic`, `Free Trader`). Include a weighted empty bullet (`x8 `) so most ships have none. |
| 2 | `Ship names` | 1 | — | 120 | The proper name (`Vespertine`, `Hammerfall`, `Long Odds`). Direct analogue of `## Callsigns` (374 bullets, `npc-generator-tables.md:550`). |
| 3 | `Theme` | 1 | — | 8 | Bare names, `xN` weighted. Rolled first, honoured by every themed table. |
| 4 | **`Ship type`** | 2 | **exactly one `SHIP_TYPES` slug** + `civ`/`mil` | 20 | The identity slot, `{ship}` in both templates. Slug flag is mandatory and pinned (`test_ship_policy.py:607-626`). ~2 phrasings per slug so a type is not one sentence. |
| 5 | **`Size`** | 2 | **exactly one `SIZE_BANDS` band** | 16 | "Name the number" (`docs/generate-npc.md:450-477`): *"about forty metres bow to stern, a two-crew hull"*, never *"a small ship"*. ≥3 per band. |
| 6 | `Faction` | **3** | `civ` `mil` `palette` `unaffiliated` `dressy` | 13 | `NAME \|\| VISUAL \|\| flags`. **Named `Faction`, not `Operator`, deliberately** — `split_faction` (`:2611`) and `flags_for` (`:2665`) then work unchanged, *and* the GUI's `queueImport` reads `entry.traits.Faction` (`server.js:361-386`) so the Foundry importer's `faction` field populates with zero GUI change. Visual describes **livery, roundel, stencilling, patina — never a hull category** (the exact rule at `npc-generator-tables.md:1616-1624`). |
| 7 | `Hull` | 2 | `civ`/`mil`, form flags (`twinboom` `discspine` `slabside` `deltawing` `obelisk` `flatdeck`), `@theme` | **20** ⟵ *the user's "20 spaceship descriptions"* | Silhouette. Primary theme carrier. ~18 words. |
| 8 | `Detail` | 2 | form flags, `@theme` | 24 | The `## Feature` analogue — sensor masts, docking arms, solar wings, antennae. ~12 words. |
| 9 | **`Weapon`** | 2 | `none` `civ` `mil` `min-*` `max-*` `@theme` | 24 | `EQUIPMENT_TABLES[0]`. **Must carry a `none` bullet** whose text is `""` and which carries **no size flag** (`test_ship_policy.py:126-151`). |
| 10 | **`Shield generator`** | 2 | `none` `civ` `mil` `min-*` `max-*` | 16 | `EQUIPMENT_TABLES[1]`. Not themed (the `## Gear` argument, `npc-generator-tables.md:294-295`). Natural glow source — word bullets with `glow`/`lit`/`readout` vocabulary **deliberately**, since `has_light_source` reads them. |
| 11 | **`Launch catapult`** | 2 | `none` `min-*` `max-*` | 10 | `EQUIPMENT_TABLES[2]`. Overwhelmingly the `none` roll. |
| 12 | **`Command bridge`** | 2 | `none` `min-*` `max-*` `@theme` | 18 | `EQUIPMENT_TABLES[3]`. The `## Headgear` analogue: three registers — flush blister / raised tower / no visible bridge. |
| 13 | `Markings` | 2 | `civ`/`mil` | 20 | Hazard chevrons, stencilled hull numbers, sponsor logos, taped-over insignia. **Not themed** — the `## Gear` argument again. Must not restate the Faction visual. |
| 14 | `Condition` | 1 | — | 10 | Patina/wear. Exists so 20 `## Hull` bullets do not each restate "weathered". ~8 words. |
| 15 | `Backdrop` | **3** | `weather`, prop gates (`dock` `vacuum` `atmosphere` `planetlight` `hull`), type gates, `@theme` | **20** ⟵ *the user's "20 spaceship backdrop descriptions"* | `SHOT \|\| SCENE \|\| flags`. The two halves must agree, so they roll together (`npc-generator-tables.md:2330-2334`). Subject-first, environment-second (`docs/generate-npc.md:432-435`). |
| 16 | `Weather` | 2 | `clear` | 15 | Ported near-verbatim from `npc-generator-tables.md:2716`. Portrait-only, gated on the Backdrop's `weather` flag. |
| 17 | `Glow colour` | 1 | — | 11 | **Verbatim reuse** of `npc-generator-tables.md:2217-2241`. Names a HUE, never a phenomenon (`:2225-2229`). |
| 18 | `Glow placement` | 2 | `scene` + the five ship prop gates | 16 | Predicate of *"A faint {glow} glow ___."*, starts with a verb, never names the colour (`:2255-2259`). Ship predicates: *"traces the leading edge of the wing root and pools in the intake shadow"*. |

```python
THEMED_TABLES = ("Hull", "Detail", "Weapon", "Command bridge", "Backdrop")
```

Five tables and five only, stated in the file's own header and pinned by `test/test_ship_theme.py` (§8.11) — the ship equivalent of `npc-generator-tables.md:296-304` and `test_theme_tag_placement.py`. A `@tag` on a single-segment table (`Size`, `Condition`, `Glow colour`, `Ship names`) would ship the literal `|| @cyberpunk` to the image model.

**Per-pronoun variants become per-band variants.** `variant_table` (`:1285`) and `heading_for` (`:1301`) take a caller-supplied key. Ships pass the **size band**: `## Hull (huge)` replaces, `## Command bridge (small) +` adds. No code change; the tables file decides which traits are band-varying.

**The file must carry its own format header**, per `docs/generate-npc.md:57-62` — `xN` weights, the `||` shapes, the five themed tables, the size flag vocabulary, the `none`-bullet contract, and the per-table word budgets from §5.

**Placeholder set.** No pronouns. `pronoun_fields()` (`:1714`) is replaced by a nine-line `ship_fields(ship)` returning `{ship, Ship, name, size, is_are: "is"}`. The `{...}` substitution pass (`roll_npc:2496-2504`) is kept verbatim in shape, including the `SystemExit` naming the offending table/option on `KeyError`, so a typo fails loudly.

---

## 3. THE TYPE/SIZE CONSTRAINT SYSTEM

**This is already implemented in `ship_policy.py` and requires no new design.** What follows is the resolved matrix and the two things `generate-spaceship.py` must do to honour it.

### The mechanisms, and how they map onto the NPC ones

| NPC mechanism | ship equivalent | where |
|---|---|---|
| `WEAPON_POLICY` / `DRESS_POLICY` — a policy per bucket, one filter reads it, plus a default | `EQUIPMENT_POLICY` + `DEFAULT_EQUIPMENT_POLICY` | `ship_policy.py:313`, `:422` |
| `ROLE_LOCKS` — the one shape that does **not** hand the pool back | policy `'none'`, and `filter_by_size`'s floor/ceiling | `ship_policy.py:565-570`, `:488-520` |
| `CIVILIAN_UNARMED_COPIES = 3` — the "(if any)" weighting dial | `MINIMAL_NONE_COPIES = 4` | `ship_policy.py:462` |
| `filter_by_mil`'s `civ`/`mil` flags | reused unchanged | `ship_policy.py:585-586` |
| `apply_weapon_policy`'s tiering | the five policies `none < minimal < light < any < heavy` | `ship_policy.py:290-308` |
| `ROLE_CATEGORIES`' text keying | **deliberately not copied** — keyed on a slug *flag*, because a type has several possible sentences | `ship_policy.py:200-207` |

### The full policy matrix

`EQUIPMENT_POLICY`, `ship_policy.py:313-408`. Ten types — exactly the ten the brief names.

| type (slug) | bands `sizes_for()` | Weapon | Shield generator | Launch catapult | Command bridge |
|---|---|---|---|---|---|
| Carrier `carrier` | large, huge | `any` | `heavy` | **`heavy`** | `heavy` |
| Battleship `battleship` | large, huge | `heavy` | `heavy` | `light` | `heavy` |
| Cruiser `cruiser` | medium, large | `heavy` | `heavy` | **`none`** | `heavy` |
| Destroyer `destroyer` | small, medium | `heavy` | `any` | **`none`** | `any` |
| Patrol boat `patrol` | small | `light` | `light` | **`none`** | `light` |
| Stealth ship `stealth` | small, medium | `light` | `any` | **`none`** | `light` |
| Recon ship `recon` | small, medium | `minimal` | `light` | **`none`** | `light` |
| Smuggler ship `smuggler` | small, medium | `light` | `minimal` | **`none`** | `light` |
| **Cargo ship `cargo`** | medium, large, huge | **`minimal`** | **`minimal`** | **`none`** | `any` |
| Support ship `support` | medium, large | `minimal` | `light` | **`none`** | `any` |

The policies, `ship_policy.py:290-308`:

- **`none`** — always the `none` bullet; the real pool is never consulted, filtered, weighted, or fallen back to. **Hard lock.** Where the table has no `none` bullet it synthesises `NO_EQUIPMENT` (`""`) rather than yielding (`:565-570`).
- **`minimal`** — `civ`-flagged bullets or the `none` bullet, with `none` stacked `MINIMAL_NONE_COPIES=4` deep so *"if any"* reads as *"usually not"*. **Preference** — falls back to the whole size-filtered pool with a stderr warning if the table has no `civ` bullets (`:582-597`).
- **`light`** — the real pool capped to `LIGHT_CAP[size]`, which is **one band below the hull, floored at small** (`:449-454`: small→small, medium→small, large→medium, huge→large). One below, not equal, because a cap equal to the hull is what `any` already means and would make the row a silent no-op (`:432-436`).
- **`any`** — the size-filtered pool, `none` bullet included: **usually fitted, not always**.
- **`heavy`** — the `none` bullet is excluded; the ship always has one. **Hard.**

### The resolved (type × band) equipment matrix

Combining the policy with `LIGHT_CAP` and the hull's own band. "F" = forbidden outright, "O" = optional (`none` reachable), "R" = required (always fitted). The parenthesised band is the effective hardware ceiling.

| type | band | Weapon | Shield | Catapult | Bridge |
|---|---|---|---|---|---|
| carrier | large | O (large) | **R** (large) | **R** (large) | **R** (large) |
| carrier | huge | O (huge) | **R** (huge) | **R** (huge) | **R** (huge) |
| battleship | large | **R** (large) | **R** (large) | **F** *(cap medium, no catapult is below large)* | **R** (large) |
| battleship | huge | **R** (huge) | **R** (huge) | O (large) — *the single recessed rail only* | **R** (huge) |
| cruiser | medium | **R** (medium) | **R** (medium) | **F** | **R** (medium) |
| cruiser | large | **R** (large) | **R** (large) | **F** | **R** (large) |
| destroyer | small | **R** (small) | O (small) | **F** | O (small) |
| destroyer | medium | **R** (medium) | O (medium) | **F** | O (medium) |
| patrol | small | O (small) | O (small) | **F** | O (small) |
| stealth | small | O (small) | O (small) | **F** | O (small) |
| stealth | medium | O (small) | O (medium) | **F** | O (small) |
| recon | small | O, civ-only (small) | O (small) | **F** | O (small) |
| recon | medium | O, civ-only (medium) | O (small) | **F** | O (small) |
| smuggler | small | O (small) | O, civ-only (small) | **F** | O (small) |
| smuggler | medium | O (small) | O, civ-only (medium) | **F** | O (small) |
| **cargo** | medium | O, **civ-only** (medium) | O, **civ-only** (medium) | **F** | O (medium) |
| **cargo** | large | O, **civ-only** (large) | O, **civ-only** (large) | **F** | O (large) |
| **cargo** | huge | O, **civ-only** (huge) | O, **civ-only** (huge) | **F** | O (huge) |
| support | medium | O, civ-only (medium) | O (small) | **F** | O (medium) |
| support | large | O, civ-only (large) | O (medium) | **F** | O (large) |

Three things worth reading off that table, each pinned by an existing test:

- **Size is not a licence.** A five-hex bulk freighter is the largest hull in the tables and still rolls civilian-grade hardware, because the type gate ran first (`ship_policy.py:15-18`, `test_ship_policy.py:279-290`).
- **Only carriers and the largest battleships ever reach a catapult**, and the battleship reaches only the short recessed rail, never a full flight deck — a `LIGHT_CAP` consequence rather than a row of its own, and pinned as such (`test_ship_policy.py:368-378`).
- **An unlisted type gets no catapult.** `DEFAULT_EQUIPMENT_POLICY["Launch catapult"] = "none"` (`ship_policy.py:425`), because the direction an accident must fail in is *away* from the brief's prohibition. The NPC file learned this the hard way with `DEFAULT_WEAPON_POLICY` (`ship_policy.py:412-421`, `test_ship_policy.py:482-490`).

### The size-flag vocabulary

`SIZE_BANDS`, `ship_policy.py:106-134`. Two flags per band, answering different questions (`:92-100`):

| band | hexes | floor flag | ceiling flag | gloss (`ship_policy.py:114,120,126,132`) |
|---|---|---|---|---|
| small | 1 | `min-small` | `max-small` | one hex — a patrol boat, a courier, a single-crew hull |
| medium | 2 | `min-medium` | `max-medium` | two hexes — a destroyer, a working freighter, a corvette |
| large | 3 | `min-large` | `max-large` | three hexes — a cruiser, a light carrier, a bulk hauler |
| huge | 5 | `min-huge` | `max-huge` | five hexes — a fleet carrier, a battleship, a cathedral hull |

Widths are 1, 2, 3, **5** — not linear, because the top band is the 40k cathedral hull and the fleet carrier, and *"the gap is the point"* (`:87-90`). Multiple flags **intersect**: `min-medium max-large` is hardware for the two middle bands (`:180-182`). **A bullet with neither flag is neutral and reachable by every hull, and most bullets must stay that way** — that neutral pool is what makes the hard size filter safe to run without a fallback (`:102-105`), and `test_ship_policy.py:577-590` fails if fewer than three neutral bullets remain in any equipment table.

### What `generate-spaceship.py` must do

**(a) Roll order.** `Ship type` → `Size` → the four equipment tables, and nothing else in between that reads them. In the roll loop:

```python
if name == "Ship type":
    options = filter_by_forced_band(options, forced_band)     # reverse gate (b)
    options = filter_by_forced_catapult(options, forced_cat)  # reverse gate (b)
elif name == "Size":
    band = rng.choice(sp.sizes_for(ship_type))                # the TYPE gates the SIZE
    options = [b for b in options if sp.size_of(b) == band]
elif name in sp.EQUIPMENT_TABLES:
    options = sp.filter_by_ship_policy(options, ship_type, band, name)   # HARD, runs first
    if name in THEMED_TABLES:                                            # SOFT, runs second
        options = npc.apply_theme_share(
            npc.filter_by_theme(options, theme, name), theme, name, npc.THEME_SHARE)
```

**Policy runs before theme, and this ordering is load-bearing.** `filter_by_ship_policy` is hard and can return a one-element pool; `filter_by_theme` is soft and ends `kept or options`. Running theme first hands policy a pre-narrowed pool and raises the odds of a starved hard filter; running policy first means the theme filter's own fallback can only ever re-widen to a policy-legal set. Pinned by `test/test_ship_theme.py::TestPolicyRunsBeforeTheme`.

**(b) Two reverse-direction gates**, computed before the loop, exactly the shape of `roll_npc`'s `forced_figure` (`:1787`) and `forced_carried_helmet` (`:1817`) — each exists because the pinned trait is rolled *later* than the trait it must constrain:

1. **Forced `Size`** (`--set-trait Size=…`, or a pinned Size on a reroll) → narrow `## Ship type` to slugs whose `sizes_for()` contains `sp.size_of(forced_bullet)`. Without this, forcing "five hexes" on a patrol boat is unsatisfiable.
2. **Forced non-`none` `Launch catapult`** → narrow `## Ship type` to `("carrier", "battleship")` and `## Size` to bands whose policy admits a catapult. Without this, the hard `'none'` lock silently discards the user's own `--set-trait`.

Both are **preferences with fallback** (`kept or options`) plus a stderr note, matching `filter_by_affiliation`'s trade (`:1443-1451`): the pool is small and GUI-editable, and a refused `--set-trait` is worse than a warned-about one.

**(c) `TRAIT_DEPENDENTS`.** Every key in `RAW_REROLLABLE_TRAITS` must appear, `()` for leaves, or `trait_cascade` raises (`:353`):

```python
TRAIT_DEPENDENTS = {
    "Theme": THEMED_TABLES,
    "Ship type": ("Size", "Faction", "Weapon", "Shield generator",
                  "Launch catapult", "Command bridge", "Markings"),
    "Size": ("Hull", "Weapon", "Shield generator", "Launch catapult",
             "Command bridge"),
    "Faction": ("Markings",),
    "Hull": ("Detail", "Command bridge"),
    "Detail": (),
    "Weapon": (),
    "Shield generator": ("Glow colour", "Glow placement"),
    "Launch catapult": (),
    "Command bridge": (),
    "Markings": (),
    "Condition": (),
    "Backdrop": ("Weather", "Glow colour", "Glow placement"),
    "Weather": (),
    "Glow colour": (),
    "Glow placement": (),
    "Ship names": (),
    "Name prefixes": (),
}
```

`Shield generator → Glow colour/placement` is the ship's version of the NPC's `Backdrop → Glow colour` edge: a shield emitter is a light source that `has_light_source` reads (`:501`), so re-rolling it can invalidate a glow that was only reachable because the old emitter was there.

---

## 4. TOKEN SIZING

### Constants

```python
# Portrait: one size for every hull. Deliberately landscape where the NPC's is
# square (generate-npc.py:1109) - a ship in a scene is a landscape composition,
# and every '## Backdrop' bullet in the file is written as one.
PORTRAIT_SIZE = (1216, 832)          # 3:2, 1.01 MP, both dims a multiple of 64

# Token: the Foundry grid footprint, and the canvas that matches its aspect.
#   grid_w  == sp.SIZE_BANDS[band]["hexes"] - derived, never typed twice
#   px_hex   declines as the hull grows, because a bigger token is DISPLAYED
#            bigger on the map but the VRAM budget is finite.
TOKEN_GRID = {                       # band -> (grid width, grid height) in hexes
    "small":  (1, 1),
    "medium": (2, 1),
    "large":  (3, 2),
    "huge":   (5, 3),
}
TOKEN_PX_PER_HEX = {"small": 1024, "medium": 768, "large": 576, "huge": 384}
MAX_TOKEN_PX = 2_400_000             # --max-token-px default
```

Resolved:

| band | grid w × h | canvas | megapixels | vs NPC token (1024×1280) |
|---|---|---|---|---|
| small | 1 × 1 | 1024 × 1024 | 1.05 | 0.80× |
| medium | 2 × 1 | 1536 × 768 | 1.18 | 0.90× |
| large | 3 × 2 | 1728 × 1152 | 1.99 | 1.52× |
| huge | 5 × 3 | 1920 × 1152 | 2.21 | 1.69× |

Every dimension is a multiple of 64 by construction (1024, 768, 576, 384 all are), which the latent needs. Canvas aspect equals grid aspect exactly in every band, so Foundry stretching the image into the token rectangle introduces no distortion. Worst case is 1.69× the NPC token's cost, not the 5× a naive `512px × 5 hexes = 2560` would have been.

```python
def token_size(band, max_px=MAX_TOKEN_PX):
    """(width, height) for a token of this hull band, snapped to 64 and clamped."""
    gw, gh = TOKEN_GRID[band]
    px = TOKEN_PX_PER_HEX[band]
    w, h = gw * px, gh * px
    if w * h > max_px:                       # preserve aspect, snap both to 64
        scale = (max_px / (w * h)) ** 0.5
        w, h = (max(64, int(v * scale) // 64 * 64) for v in (w, h))
    return w, h
```

### How the size reaches ComfyUI

`TOKEN_SIZE` in the NPC script is a constant read at exactly five call sites and reaches ComfyUI through one path: `Knobs(args, size, COMFY_PREFIX)` (`generate-npc.py:2969-2984`) → `art.build_job` (`generate-art.py:439-444`) → the `EmptyLatentImage` node `locate_slots` found wired to the KSampler's `latent_image` (`generate-art.py:302-305`). `Knobs.__init__` already takes `size` as a parameter (`generate-npc.py:2977`) *precisely so it can vary per image*. So per-ship sizing is:

```python
size = token_size(band, args.max_token_px)
knobs = npc.Knobs(args, size, COMFY_PREFIX)        # render pass
```

**Pass the same `size` to the RMBG `Knobs` too.** The NPC script builds the background-removal `Knobs` with the fixed `TOKEN_SIZE` (`generate-npc.py:4413`, `:4197`) — harmless there because it never varies, and harmless in general because `art.build_post_job` (`generate-art.py:374-395`) reads nothing off `args` at all. Pass the real size anyway rather than leave a stale constant.

### New ComfyUI workflow JSON: **not needed for the render pass.**

`Lancer_Scene_Workflow_v1.json` (`art.DEFAULT_WORKFLOW`, `generate-art.py:51`) has five `EmptyLatentImage` nodes; node `57` (`"Token Image Size"`, 1024×1280) is the one wired to KSampler `54`'s `latent_image`, so `locate_slots` picks it and `build_job` overwrites its `width`/`height`. The other four are pruned by `art.prune_orphans` (`generate-art.py:394`). Verified by inspection of the graph. Model stack is Krea 2 Turbo int8 + Qwen3-VL CLIP + Qwen image VAE (nodes `52`/`53`/`58`), CFG 1.0, 10 steps, euler/simple — unchanged.

Ships use `art.DEFAULT_WORKFLOW` and **do not** use `Lancer_Scene_Workflow_for_girls_v1.json`. `GENDER_WORKFLOWS` (`generate-npc.py:1105`), `workflow_for` (`:3242`) and `--workflow-woman` are all dropped; ships have one workflow and `load_workflows` collapses to a single `load_api_workflow` + `locate_slots` + the missing-latent check.

**Promote that check to an error.** `load_workflows` currently warns on stderr when `slots.latent` is absent (`generate-npc.py:3304-3307`, *"portrait and token will share the workflow's own size"*). For ships that is not a cosmetic degradation: a 5-hex carrier silently rendered at the workflow's own 1024×1280 is an unusable token. `generate-spaceship.py` raises `SystemExit` instead.

### The transparent-background pass for a wide token

`Util_RemoveBackground_makeTransparent.json` is `LoadImage → AILab_ColorInput(preset=white) → RMBG(model=RMBG-2.0, process_res=1024, background=Alpha) → SaveImage`. It has **no latent and no size node**, so a 1920×1152 input passes through structurally unchanged and the alpha PNG comes back at full resolution.

**The one real risk is `process_res: 1024`.** RMBG-2.0 resizes the input to a square inference resolution, infers the mask, and resizes the mask back. At 1:1 that is lossless in aspect; at the `huge` band's 5:3 it squashes by 1.67×, and thin high-frequency structures — antenna masts, sensor booms, catapult rails, wingtip stencilling — are exactly what a squashed 1024 inference drops from the mask, leaving them cut off the token.

**Fix: a `--rmbg-res` flag, default 1536, patched onto the post template before the job is built.** Five lines, no change to `generate-art.py` (whose `build_post_job` reads nothing off `args`), no new workflow file:

```python
post_template = art.load_api_workflow(args.rmbg)
for node in post_template.values():                      # RMBG-2.0 infers at a square
    if node.get("class_type") == "RMBG":                 # process_res and resizes the mask
        node.setdefault("inputs", {})["process_res"] = args.rmbg_res
post_slots = art.locate_post_slots(post_template)
```

Alternative if a code-free option is preferred later: ship `workflows/api/Util_RemoveBackground_Wide_v1.json` with `process_res: 1536` and default `--rmbg` to it for ships. The flag is preferred because it keeps one RMBG graph in the repo.

### Prompt-side framing

Token sizing is asserted in the prompt as well as in the latent, because at CFG 1.0 the latent aspect alone does not stop the model anchoring the hull at portrait scale and cropping the stern — the same failure `generate-npc.py:1148-1155` documents for the NPC token's feet. The `{plan}` slot carries a per-band phrase:

```python
PLAN_FRAMING = {
    "small":  "the whole hull roughly as long as it is wide across the wings",
    "medium": "a lean hull about twice as long as it is wide",
    "large":  "a long hull about half again as long as it is broad",
    "huge":   "a vast hull filling the frame bow to stern, half again as long "
              "as it is broad",
}
```

`{plan}` states **framing**; scale is `{size}`'s job — the rolled `## Size` bullet, which names the number (`docs/generate-npc.md:450-477`). Keeping those two apart is why `{size}` is not allowed to say "huge".

### Metadata for the GUI / Foundry importer

The generator's obligation is to write these into the manifest entry (§6). The GUI/Foundry design consumes them:

| field | value | consumer |
|---|---|---|
| `sizeBand` | `"small"` \| `"medium"` \| `"large"` \| `"huge"` | dossier, GUI badge |
| `hexes` | `sp.SIZE_BANDS[band]["hexes"]` — 1 / 2 / 3 / 5 | human-readable |
| **`gridWidth`** | `TOKEN_GRID[band][0]` — **integer**, `== hexes` | **Foundry `token.width`** |
| **`gridHeight`** | `TOKEN_GRID[band][1]` — integer | **Foundry `token.height`** |
| `tokenWidth` / `tokenHeight` | the rendered canvas, post-clamp | GUI preview aspect, regen reproducibility |

`gridWidth == hexes` is derived from `ship_policy.SIZE_BANDS`, never typed twice, and pinned by `test/test_ship_size.py`.

**GUI-side note (for the other design, not this one):** `GET /importer/pending` (`A/docs/foundry-importer-contract.md`) currently returns `{jobId,itemId,kind,name,callsign,role,faction,portraitPath,tokenPath,status,queuedAt,sentAt}`. `kind` is already on the wire, so a `kind:"spaceship"` job arrives with no server change; `gridWidth`/`gridHeight` are two **additive** fields on an existing route — weaker than the contract doc's own "add a route rather than alter one" rule, and safe for the pinned `A/test/importerContract.test.js`.

---

## 5. PROMPT TEMPLATES

Style register is the **painterly** one (`mech-catalogue-art-prompts.md:3`), not the cel-shaded equipment register (`equipment-art-prompts.md:3-5`). Slot order follows the fixed order of all 65 mech blocks: *silhouette → framing → style clause → distinguishing feature → mounted systems → glow → stance/plan → background → closing tag block* (`mech-catalogue-art-prompts.md:28-30`, `:38-40`).

```python
# The ship's own {} slots. No pronouns; ship_fields() supplies {ship}, {Ship},
# {name}, {size}, {is_are}. Everything else is a rolled bullet or a
# pre-formatted line, because str.format is single-pass and a clause that has
# to be able to vanish cannot be a bare slot (the faction_line/gear_line
# argument, generate-npc.py:2671-2699).
PORTRAIT_TEMPLATE = (
    "{shot} of {ship}, {size}, rendered in a detailed painterly illustration "
    "style with fine grain texture, clean linework and halftone dot shading "
    "worked into the shadows, moody cinematic lighting. The hull is {hull}, "
    "{detail}. {armament_line}{bridge_line}{faction_line}{markings}, "
    "{condition}. "
    "{backdrop} {weather_line}{glow_line} "
    "Shallow depth of field, high detail, atmospheric sci-fi vessel "
    "illustration, painterly brushwork with heavy grain and dense halftone "
    "screentone worked into every shadow."
)

# The token asserts FRAMING three times, in the three places that move it, for
# the reason generate-npc.py:1148-1155 gives about the NPC token's feet: at CFG
# 1.0 "the whole hull in frame" alone loses to the detail the rest of the
# prompt asks for, and the stern is the first thing cropped. Once in the
# opening sentence (whole hull, margin on all four sides), once as {plan} (the
# aspect the latent is already shaped to), and once opening the closing tag
# block, which is the position a diffusion model weights hardest.
#
# The background sentence is positive-only, deliberately. The NPC token's
# "no texture, no gradient, no shadow, no environment" was removed because
# every flattening word in it has a direct contradiction in the same prompt's
# grain/halftone tail, and scoping is what a diffusion text encoder is worst at
# (generate-npc.py:1156-1169). It exists for the RMBG pass, not for style.
TOKEN_TEMPLATE = (
    "A top-down orthographic illustration of {ship}, {size}, seen from "
    "directly above with the bow toward the top of the frame, the whole hull "
    "in frame from bow to stern and wingtip to wingtip with clear empty space "
    "on all four sides, rendered in a detailed painterly illustration style "
    "with fine grain texture, clean linework and halftone dot shading worked "
    "into the shadows, moody cinematic lighting on the hull. "
    "The hull is {hull}, {detail}. {armament_line}{bridge_line}"
    "{faction_line}{markings}, {condition}. "
    "{glow_line} Around the hull the background is an empty plain white void. "
    "{plan}, a single vessel centered in frame and clear of the frame edge, "
    "dramatic lighting, high detail, isolated vehicle illustration, clean "
    "silhouette, painterly brushwork with heavy grain and dense halftone "
    "screentone worked into every shadow."
)

# Glow lines. Same two dimensions as the NPC's four constants plus one {other}
# slot (generate-npc.py:1191-1200): does anything on this ship cast light, and
# does the rolled Faction assert pigment of its own. Reworded off the face and
# onto the hull; GLOW_NONE and GLOW_NONE_PIGMENT are reused from
# generate-npc.py:1225-1233 verbatim, since neither mentions a subject.
GLOW_PORTRAIT = (
    "A faint {glow} glow {placement}. Keep the palette restrained - greys, "
    "olive drab and rust - with {glow} the only {other}saturated color in the "
    "frame."
)
GLOW_TOKEN = (
    "Keep the palette restrained - greys, olive drab and rust - with a single "
    "{glow} glow the only {other}saturated color."
)
```

### Pre-formatted lines (each returns `""` or ends with a trailing space)

| slot | source | note |
|---|---|---|
| `{armament_line}` | **`sp.armament_sentence(ship)`**, `ship_policy.py:640-663` | *"The hull carries X and Y. "* over `Weapon`, `Shield generator`, `Launch catapult`; `""` when all three are `NO_EQUIPMENT`. Comma-joins instead of `" and "` when any part is already compound — `carry_sentence`'s measured rule (`generate-npc.py:2717`). **Already written and tested** (`test_ship_policy.py:408-455`). |
| `{bridge_line}` | **`sp.bridge_sentence(ship)`**, `ship_policy.py:666-680` | Separate from armament because a bridge is silhouette, not payload. |
| `{faction_line}` | `npc.split_faction(ship["Faction"])[1]`, formatted | `""` for the two `unaffiliated` bullets with empty visuals; a `dressy` Faction under a workaday hull keeps its **name** for the dossier and loses only its **visual** (`generate-npc.py:2798-2814`). |
| `{weather_line}` | portrait only, gated on the Backdrop's `weather` flag and the Weather bullet's `clear` flag | `weather_sentence` (`generate-npc.py:2701-2715`), copied. |
| `{glow_line}` | `GLOW_PORTRAIT` / `GLOW_TOKEN` / `GLOW_NONE` / `GLOW_NONE_PIGMENT` | `equipped_glow = npc.has_light_source(weapon, shield, catapult, bridge, detail, hull)`; `portrait_glow = equipped_glow or npc.has_light_source(scene)`. **The token gets no scene light** — it has no backdrop (`generate-npc.py:2830-2833`). |
| `{shot}` / `{backdrop}` | `npc.split_backdrop(ship["Backdrop"])` | Portrait only. |
| `{plan}` | `PLAN_FRAMING[band]` | Token only. §4. |

### Budget

`TOKEN_LIMIT = 512`, `CHARS_PER_TOKEN = 4.5` (`generate-npc.py:372-373`) — deliberately pessimistic against a measured 4.8 over 9,000 prompts. Ceiling ≈ 2,300 chars.

| component | budget (chars) |
|---|---|
| template scaffolding (portrait) | 640 |
| `{size}` | ≤ 90 |
| `{hull}` | ≤ 130 (≈18 words) |
| `{detail}` | ≤ 90 (≈12 words) |
| `{armament_line}` (three bullets + join) | ≤ 300 |
| `{bridge_line}` | ≤ 95 |
| `{faction_line}` | ≤ 90 (*"about a dozen words"*, `npc-generator-tables.md:1668-1670`) |
| `{markings}` + `{condition}` | ≤ 130 |
| `{backdrop}` scene | ≤ 320 |
| `{weather_line}` + `{glow_line}` | ≤ 210 |
| **portrait total** | **≈ 2,095 chars ≈ 466 tokens** |

The token prompt drops `{shot}`, `{backdrop}` and `{weather_line}` (−400) and adds `{plan}` and a longer framing preamble (+230), landing lower. Both must be enforced at **p99, not max** — one pathological combination should be fixed at the bullet, not hold the suite red (`test/test_prompt_budget.py:23-32`). §8.5.

---

## 6. OUTPUT + MANIFEST

### Constants

```python
DEFAULT_TABLES   = SCRIPT_DIR / "prompts" / "spaceship-generator-tables.md"
DEFAULT_MANIFEST = SCRIPT_DIR / ".generated-npcs.json"   # shared - see below
COMFY_PREFIX     = "LancerSpaceships"
DEFAULT_OUTPUT_ROOT = (Path(os.environ["COMFYUI_OUTPUT_DIR"]) if ... else
                       SCRIPT_DIR / "output") / COMFY_PREFIX
```

`COMFY_PREFIX` mirrors `generate-npc.py:106` and flows into both `DEFAULT_OUTPUT_ROOT` and every ComfyUI `filename_prefix` (via `Knobs.output_prefix`). Its GUI counterpart is `config.foundryNpcSubdir` (`A/server.js:83`), which the GUI design must make per-kind.

### **Decision: ships write into the same `.generated-npcs.json` as NPCs.**

This is the single highest-leverage decision for GUI integration. `A/server.js:1670-1683` groups manifest items by `item.kind` for `/api/categories` and `/api/items?category=` **generically**, and `A/public/app.js:3` `CATEGORY_LABELS` **already contains `spaceship: 'Spaceships'`**. A `kind:"spaceship"` entry in that one file appears in the grid with **zero server change**. A second manifest would need a new config key, a merge in `loadManifest` (`A/server.js:156-175`), and a matching change to `sortKeysDeep` (`:225-234`) and `deleteItem` (`:296-322`).

Keys are absolute folder paths and the two trees are disjoint (`…/LancerNPCs/…` vs `…/LancerSpaceships/…`), so collisions are impossible. `art.save_manifest` writes `indent=2, sort_keys=True` (`generate-art.py:638`), which is what the GUI's own rewrites mirror.

**Known limitation to state in the docs:** `art.load_manifest` / `save_manifest` rewrite the whole file, so a concurrent NPC batch and ship batch clobber each other. `generate-npc.py` already has this race with itself; the GUI serialises jobs. `--manifest` remains available for anyone who wants them separated.

### Folder layout

```
<DEFAULT_OUTPUT_ROOT>/run<N>/<Category>/<Name>/
    <Name> Portrait.png
    <Name> Token.png
    <Name> Token (raw).png       # only with --keep-raw-token
    <Name>.md
```

The **two-level `<Category>/<Name>` nesting is load-bearing** and must not be flattened: `A/server.js:1570-1573` recovers the category as `basename(dirname(folderPath))`, and `foundryDestFolder` (`A/server.js:242-246`) copies into `foundryDataRoot/<subdir>/<category>/<name>/`. A flat `runN/<Name>/` would make every import land under a category named `runN`.

`<Category>` comes from a `SHIP_FOLDERS` dict in `generate-spaceship.py` (**not** in `ship_policy.py`, which is not to be edited), keyed on the type slug and pluralised for parity with the NPC's `Pilots`/`Soldiers`:

```python
SHIP_FOLDERS = {
    "carrier": "Carriers", "battleship": "Battleships", "cruiser": "Cruisers",
    "destroyer": "Destroyers", "patrol": "Patrol boats",
    "stealth": "Stealth ships", "recon": "Reconnaissance ships",
    "smuggler": "Smuggler ships", "cargo": "Cargo ships",
    "support": "Support ships",
}
UNCATEGORIZED_SHIP = "Other"        # mirrors UNCATEGORIZED_ROLE, generate-npc.py:758
```

A test pins `set(SHIP_FOLDERS) == set(sp.SHIP_TYPES)` (§8.9). Path building reuses `npc._safe` (`:2866`), `npc.npc_folder` (`:2881`, with its `(2)…(99)` collision suffixing) and `npc.next_run_folder` (`:3017`).

### Name and identifiers

```python
name     = ("%s %s" % (prefix, ship_name)).strip()      # "ISV Vespertine", or "Vespertine"
callsign = hull_code(rng)                               # "IST-4471" - stencilled hull code
slug     = art._slug(name)
id       = "ship-%s-%d" % (slug, seed)
```

`hull_code` is generated **in code from the seeded rng**, not tabled — a serial is a number, and a table of numbers is the wrong shape. `id` is deterministic from name+seed exactly as the NPC's is (`generate-npc.py:4484`), because the Foundry importer's `.imported.json` keys on it (`A/server.js:339`) and an `--overwrite` rerun must reuse rather than mint. The `ship-` prefix guarantees no collision with `npc-…` ids in the shared manifest.

`callsign` populates the GUI grid's subtitle (`itemView`, `A/server.js:1552-1626`) for free.

### Manifest entry shape

```jsonc
"<absolute folder path>": {
  "id":        "ship-isv-vespertine-1743098221",
  "kind":      "spaceship",
  "name":      "ISV Vespertine",
  "callsign":  "IST-4471",
  "seed":      1743098221,
  "tables":    "<abs path to spaceship-generator-tables.md>",
  "workflow":  "<abs path to Lancer_Scene_Workflow_v1.json>",

  "traits":    { "<every REQUIRED_TABLES name>": "<rendered text>" },
  "rawTraits": { "<same keys>": "<the bullet, flags intact>" },

  "shipType":   "cruiser",          // the sp.SHIP_TYPES slug
  "sizeBand":   "large",
  "hexes":      3,
  "gridWidth":  3,                  // Foundry token.width
  "gridHeight": 2,                  // Foundry token.height
  "tokenWidth": 1728,
  "tokenHeight":1152,

  "files":         ["ISV Vespertine Portrait.png", "ISV Vespertine Token.png",
                    "ISV Vespertine.md"],
  "portrait":      "ISV Vespertine Portrait.png",
  "portraitPrompt":"...",
  "token":         "ISV Vespertine Token.png",
  "tokenPrompt":   "...",
  "dossier":       "ISV Vespertine.md",
  "when":          "2026-09-06 14:22:07"
}
```

Everything `A/server.js` reads is present: `itemView` needs `id, kind, name, callsign, traits, seed, when, portrait, token, portraitPrompt, tokenPrompt, rawTraits`; `manifestItemsFrom` (`:186-194`) **skips any entry without `id`**; `copyIntoFoundry` reads `files`; `queueImport` (`:361-386`) reads `traits.Role` and `traits.Faction` — `traits.Faction` populates (§2), `traits.Role` arrives `undefined` and the importer's `role` is `null`, which the Foundry contract tolerates. The GUI design's one-line fix is `role: item.traits.Role || item.traits['Ship type'] || null`.

Ship entries deliberately carry **none** of the NPC's seven derived booleans (`young`, `outfit_notac`, `gear_helmet`, `hair_updo`, `headgear_helmet`, `headgear_crown`, `hair_covered`, `headgear_bare`, `generate-npc.py:4501-4520`) — every ship pairing is rebuildable from `rawTraits`, because `ship_policy` filters on the bullets' own flags rather than on a stripped value.

### Regeneration

Identical to the NPC path (`regenerate_one`, `generate-npc.py:4046-4286`): locate by `--regen-id`, **reuse the entry's own folder with no suffixing**, rewrite `seed`, `files`, `portrait`, `portraitPrompt`, `token`, `tokenPrompt`, `when` in place, `art.save_manifest`, return 130 on `KeyboardInterrupt` after `comfy.cancel_all()`.

**Fix the NPC script's bug rather than inherit it.** `regenerate_one` rewrites `traits`/`rawTraits` only when `rerolled is not None` (`generate-npc.py:4273-4280`), and `rerolled` is assigned only on the `--reroll-trait` path (`:4080`). The `--set-trait` path (`:4098-4152`) renders the new value but **never persists it**, so `A/server.js:1919` (`/api/set-trait`) shows stale traits after a successful set. `generate-spaceship.py` writes `traits`/`rawTraits` after **either** path. Pinned by `test/test_ship_manifest.py::TestSetTraitPersists`.

A regen also re-derives `sizeBand`/`gridWidth`/`gridHeight`/`tokenWidth`/`tokenHeight` from the (possibly re-rolled) `Size` trait, so a `--set-trait Size=…` changes the token's canvas and the Foundry footprint together.

### "Seen"

`.npc-seen.json` is GUI-private (`A/server.js:467`), lives **beside the manifest**, and keys on item `id`. Because ships share the manifest and their ids are globally unique, the new-badge machinery works for ships with no generator involvement and no GUI change.

### Dossier

`<Name>.md`, written by a ship `write_dossier` mirroring `generate-npc.py:2894-2961`:

```
# ISV Vespertine

"IST-4471" - Cruiser, Union Administrative Department
Rolled from spaceship-generator-tables.md with seed 1743098221.

## Traits
| Trait | Value |
| ... 20 rows: Registry prefix, Ship name, Theme, Ship type, Size, Size band,
  Grid footprint (3 x 2 hexes), Faction, Affiliation, Hull, Detail, Weapon,
  Shield generator, Launch catapult, Command bridge, Markings, Condition,
  Portrait shot, Portrait scene, Portrait weather, Glow colour, Glow placement |

## Art
- ISV Vespertine Portrait.png
- ISV Vespertine Token.png

### Portrait prompt
```…```

### Token prompt
```…```
```

`Affiliation` is `npc.split_faction(...)[0]`; `Portrait shot`/`Portrait scene` are `npc.split_backdrop(...)`; `Grid footprint` is the §4 metadata rendered for a human. The GUI never reads the dossier (`grep -rn dossier` over `server.js`, `public/app.js`, `lib/*.js` returns nothing) — it is recorded in `files`/`dossier` and copied into Foundry.

---

## 7. CLI CONTRACT

`parse_args(argv=None)` in `generate-spaceship.py`, mirroring `generate-npc.py:3030-3239` group for group.

### the roll

| flag | type | notes |
|---|---|---|
| `--count N` | int, default 1 | |
| `--seed S` | int | `base_seed = args.seed or random.randint(0, 2**32-1)`; ship *n* uses `random.Random(base_seed + n)`, and the **same** seed goes to ComfyUI so a seed reproduces roll and noise alike (`generate-npc.py:4350-4360`, `:4444`) |
| `--tables PATH` | Path, default `DEFAULT_TABLES` | |
| `--name TEXT` | str | requires `--count 1` |
| `--type SLUG` | choice over `sp.SHIP_TYPE_ORDER` | sugar for `--set-trait`-style forcing; narrows `## Ship type` to bullets carrying that slug |
| `--size BAND` | choice over `sp.SIZE_ORDER` | forces the band; triggers reverse gate (b1) of §3 |
| `--theme NAME` | str | forces `Theme` |
| `--set-trait Table=value` | repeatable | verbatim bullet, flags included; duplicate-table is an error (`generate-npc.py:3186-3196`) |

**`--pronouns` and `--unarmed` are not accepted** and produce argparse's exit-2 error on stderr. A silent no-op would hide a GUI that has not been updated per-kind; the GUI design must not emit them for `kind:"spaceship"`. (`A/server.js:1117,1122` emits them today for NPCs only.)

### generation

`--workflow PATH` (default `art.DEFAULT_WORKFLOW`), `--rmbg PATH` (default `art.POST_ALIASES["rmbg"]`), **`--rmbg-res N`** (default 1536, §4), `--no-portrait`, `--no-token`, `--keep-raw-token`, `--steps`, `--cfg`, `--sampler`, `--scheduler`, `--set NODE.input=value` (via `art.parse_set`), **`--max-token-px N`** (default 2400000, §4). No `--workflow-woman`.

### output

`--out PATH` (defaults to `next_run_folder(DEFAULT_OUTPUT_ROOT)` unless regen or `--trait-odds`), `--overwrite`, `--manifest PATH` (default `DEFAULT_MANIFEST`).

### regenerate

`--regen-manifest PATH`, `--regen-id ID`, `--new-seed INT`, `--reroll-trait TABLE`, `--trait-choices TABLE`, `--release A,B`.

### run mode

`--trait-odds [N]` (`nargs="?"`, `const=20000`), `--server HOST:PORT`, `--dry-run`, `--json`, `--timeout` (default 1800), `--pause` (default 2.0).

### Validation (the GUI relies on each of these)

`--no-portrait` + `--no-token` refused; `--regen-manifest` and `--regen-id` required together; `--count`/`--seed`/`--name`/`--type`/`--size`/`--theme` refused with regen (`--set-trait` deliberately **not** in that list, `generate-npc.py:3158-3162`); `--new-seed` requires regen; `--name` requires `--count 1`; `--trait-choices` is report-only; `--reroll-trait` xor `--set-trait`; `--release` names must be gated by a set trait and validated against `TRAIT_DEPENDENTS` (not the transitive closure, `generate-npc.py:3213-3227`).

### Invocation invariants (all five GUI spawn shapes)

Invoked as `python <script> …`; cwd is the script's own directory; environment inherited (this is how `COMFYUI_OUTPUT_DIR` reaches the generator); **exit code 0 is the only success signal for render modes**; stdout and stderr are merged into the job log for render modes; for the two query modes **stdout is parsed whole and must contain nothing but JSON**, with every diagnostic on stderr.

### The four JSON-on-stdout shapes

**`--trait-odds N`** — validated field by field at `A/lib/traitOdds.js:66-83`, including the probability range:

```json
{ "samples": 20000,
  "tables": { "Weapon": { "<bullet text>": 0.0417, "...": 0.0 } } }
```

Printed **before the run banner**, exactly as `generate-npc.py:4305-4307` orders it, so nothing else reaches stdout.

**`--regen-manifest P --regen-id I --trait-choices T`** — every one of the six choice keys must be present or `A/lib/traitChoices.js:41` makes the GUI return 502:

```json
{ "trait": "Weapon",
  "current": "rows of turret batteries stepped along both flanks || mil min-medium",
  "dependents": [],
  "choices": [
    { "value":     "a spinal lance running the full length of the hull || mil min-huge",
      "heading":   "Weapon",
      "allowed":   false,
      "current":   false,
      "conflicts": ["Size"],
      "releases":  ["Size"] }
  ] }
```

Semantics copied exactly from `trait_choices` (`generate-npc.py:3791-3918`): upstream legality is `probe[name]` from a fully pinned roll; downstream `conflicts` come from re-probing with the candidate forced and comparing each dependent's kept value against the new pool; **nothing is dropped** — a ruled-out value is greyed but still selectable, mirroring `--set-trait`. `random.Random(0)` is hardcoded inside (`:3840`), so a read-only query can never consume a caller's stream.

**`--dry-run`** (no `--json`) — human-readable, not parsed. Per ship: name, callsign, seed, `Ship type` + `Faction`, target folder, workflow basename, band and grid footprint, both prompts with their canvas sizes and token estimates. Ends `dry run OK - N job(s) would be queued`.

**`--dry-run --json`** (new; ships only) — everything human goes to **stderr**, and stdout carries only:

```json
{ "ships": [
    { "name": "ISV Vespertine", "callsign": "IST-4471", "seed": 1743098221,
      "id": "ship-isv-vespertine-1743098221",
      "shipType": "cruiser", "sizeBand": "large",
      "hexes": 3, "gridWidth": 3, "gridHeight": 2,
      "tokenWidth": 1728, "tokenHeight": 1152,
      "folder": "<abs path>",
      "traits": { "...": "..." },
      "rawTraits": { "...": "..." },
      "portraitPrompt": "...", "portraitTokens": 466,
      "tokenPrompt": "...",    "tokenTokens": 401 } ] }
```

`--json` without `--dry-run` is an argparse error. This mode exists for the test suite and for a future GUI preview; the create path itself still learns what was produced by **diffing manifest folder keys** (`A/server.js:1128-1129`, `1164-1180`), so every produced ship must add a new key.

### Source-readable constants (R5)

Declared at **column 0, top level**, in the shapes `A/lib/overrideTables.js:17-46` regex-parses:

```python
REQUIRED_TABLES = [ ... ]                    # ^REQUIRED_TABLES\s*=\s*\[ ... \]
TRAIT_DEPENDENTS = { ... }                   # ^TRAIT_DEPENDENTS\s*=\s*\{ ... newline-}
REROLLABLE_TRAITS = ( ... )                  # multi-line literal tuple
RAW_REROLLABLE_TRAITS = tuple( ... )         # ^RAW_REROLLABLE_TRAITS\s*=\s*tuple\(
```

`RAW_REROLLABLE_TRAITS = tuple(t for t in REQUIRED_TABLES if t not in ("Name prefixes", "Ship names"))`.

`REROLLABLE_TRAITS` is written as a **literal multi-line tuple listing the same 16 names**, not as an alias and not as `()`. Every ship entry carries `rawTraits` from day one so the raw path always wins in practice, but `A/lib/overrideTables.js`'s pattern needs bullet-shaped content between the parens, and an empty tuple would make the GUI hide every reroll button on a parse quirk.

`UNREROLLABLE_REASONS` carries three verbatim refusal strings — `Ship names`, `Name prefixes`, and a `"this entry predates rawTraits"` catch-all — printed rather than hidden (`generate-npc.py:3345-3392`).

---

## 8. TEST PLAN

All under `test/`, `unittest`-style classes run by pytest, loading modules the way `test/helpers.py:18-28` does. Add `load_ship_generator()` to `test/helpers.py` alongside `load_generator()` and `load_3d()` — a 12-line copy, the only edit to an existing test file besides §8.1.

### 8.1 `test/test_ship_policy.py` — **exists (683 lines). One edit.**

Delete the skip guard at `:551-556`. The file says so itself (`:36-40`): *"The live-tables class skips itself until prompts/spaceship-generator-tables.md exists. Delete that skip the day it lands — a skipping guard is a guard that is not guarding."* `TestTheLiveTables` then asserts, against the real file: every equipment table exists; each carries a `none` bullet; each carries **≥3 neutral bullets** (the margin that makes the hard size filter safe); every `min-*`/`max-*` flag in the file is one the module reads; every `SHIP_TYPES` slug is carried by a live `## Ship type` bullet; every such bullet carries **exactly one** slug; every `heavy` cell has ≥2 bullets to roll at every band of its type; every `minimal` cell yields no `mil` bullet; and 60 seeds × every (type, band) never puts capital hardware on a small hull.

### 8.2 `test/test_ship_tables.py` — the tables file's own shape

- **`test_every_bullet_is_one_physical_line`** — the blocking defect in the staged file. Re-parse the raw text: no line begins with two spaces immediately under a `- ` bullet, and every `- ` line ends a complete thought. (Catches the exact failure that would silently truncate 41 bullets at `generate-npc.py:1260`.)
- Every `REQUIRED_TABLES` heading exists; `check_tables` does not `SystemExit`.
- `parse_tables.repeated` is empty — no duplicate `## Heading`.
- Segment counts per table match the declared shape: `Faction` and `Backdrop` are three-segment, everything else two or one.
- Every flag in the file is in a known vocabulary set; **no near-miss spellings** (`min-massive`, `Civ`, `hand`) — the "flags are matched literally and an unrecognized one is ignored" trap (`npc-generator-tables.md:306-309`).
- Every `## Size` bullet carries **exactly one** `SIZE_BANDS` band flag; every band in `SIZE_BANDS` is reachable from ≥3 Size bullets and from ≥1 `## Ship type`'s `sizes_for()`.
- Minimum bullet counts per §2, so the user's "20 spaceship descriptions / 20 backdrop descriptions" is enforced rather than remembered: `len(Hull) >= 20`, `len(Backdrop) >= 20`.
- Every `{...}` placeholder in the file is in the `ship_fields()` key set.
- The file's own header contains the format spec (grep for `## How the script reads this file`).

### 8.3 `test/test_ship_roll.py` — `roll_ship()`

- Determinism: two rolls at the same seed are `==`.
- **Probe inertness**: a probed roll and an unprobed roll at the same seed produce the same ship (mirrors `test_set_trait_value.py::ProbeIsInert`) — the guarantee that makes `trait_choices` safe.
- Every `REQUIRED_TABLES` name is a key of the returned dict; `_raw` carries the same keys with flags intact.
- No `||` and no bare flag token survives into any value.
- No `{` survives into any value.
- `--set-trait` overrides **replace** the drawn value and appear in `_raw` (`generate-npc.py:2180-2183`, `:2362-2363`).
- The two reverse gates of §3(b): forcing `Size` to a `huge` bullet never yields a `patrol` type; forcing a non-`none` `Launch catapult` yields only `carrier`/`battleship`.
- `trait_cascade("Ship type")` is the transitive closure ordered by `REQUIRED_TABLES` and raises `ValueError` on an unknown name.

### 8.4 `test/test_ship_size.py` — token sizing

- `TOKEN_GRID[band][0] == sp.SIZE_BANDS[band]["hexes"]` for all four bands — the derivation, not a second typing.
- `set(TOKEN_GRID) == set(TOKEN_PX_PER_HEX) == set(sp.SIZE_ORDER)`.
- Every `token_size(band)` dimension is `% 64 == 0`.
- Every `token_size(band)` area `<= MAX_TOKEN_PX`.
- Canvas aspect equals grid aspect exactly for every band.
- `token_size(band, max_px=1_000_000)` preserves aspect within 2%, snaps both dims to 64, and never returns a dimension below 64.
- Grid widths across the bands are `[1, 2, 3, 5]` and strictly increasing (the "the gap is the point" invariant, `ship_policy.py:87-90`).
- `set(PLAN_FRAMING) == set(sp.SIZE_ORDER)` and every phrase is non-empty.
- **`Knobs` receives the per-band size**: build a `Knobs` for each band and assert `(knobs.width, knobs.height) == token_size(band)`, and that the RMBG `Knobs` gets the same pair rather than a constant.

### 8.5 `test/ship_prompt_budget.py` (instrument) + `test/test_ship_prompt_budget.py`

The instrument is deliberately **not** named `test_*`, mirroring `test/prompt_budget.py`. `measure(tables, count=1500, seed=0)` rolls ships, calls `build_prompts`, records both token counts, and swallows stderr via `contextlib.redirect_stderr`. The test asserts:

- **p99 of both prompts < `TOKEN_LIMIT` (512)** — p99, not max, for the reason `test/test_prompt_budget.py:23-32` gives.
- Non-vacuity: `len(results) == 1500` and `min > 200`.
- Per-band: the `huge` band's p99 (the longest hardware) is also under the limit, since a `heavy`/`heavy`/`heavy`/`heavy` carrier is the worst case.

### 8.6 `test/test_ship_prompts.py` — assembly

- No empty clause ever reaches a prompt over every (type, band) × 120 seeds: no `" ,"`, no `"  "`, no `". ."`, no `"carries ."`. (`sp.armament_sentence`'s own guarantee, extended to the full template.)
- No `"||"` and no bare flag token in either prompt.
- The portrait carries `{backdrop}` and the token does not; the token carries the white-void sentence and `{plan}` and the portrait carries neither.
- An unarmed cargo ship's portrait **omits** the armament sentence rather than printing an empty one.
- `{faction_line}` is `""` for both `unaffiliated` bullets, and a `dressy` Faction under a workaday hull keeps its name in `traits` while dropping its visual from the prompt.
- Token-only glow: a ship whose only light is in the Backdrop scene gets `GLOW_NONE`-family text on the **token** and `GLOW_PORTRAIT` on the **portrait** (`generate-npc.py:2830-2833`).

### 8.7 `test/test_ship_cli.py` — argparse surface

Every flag the GUI emits parses; `--no-portrait` + `--no-token` refused; regen pair required together; roll flags refused with regen while `--set-trait` is allowed; `--reroll-trait` xor `--set-trait`; `--release` without `--set-trait` refused; `--release` naming a table absent from `TRAIT_DEPENDENTS` refused; duplicate `--set-trait Table=` refused; `--name` with `--count 2` refused; **`--pronouns` and `--unarmed` exit 2**; `--json` without `--dry-run` refused; `--out` defaults to `next_run_folder` unless regen or `--trait-odds`.

Plus, by capturing stdout: `--trait-odds` prints **valid JSON and nothing else**, and `--dry-run --json` prints valid JSON and nothing else.

### 8.8 `test/test_ship_trait_choices.py` — the GUI's JSON contract

- All four top-level keys present; `choices` is a list.
- **Every choice object has all six keys** `value, heading, allowed, current, conflicts, releases` — the exact set `A/lib/traitChoices.js:41` requires; a missing key is a 502 in the GUI.
- `allowed` and `current` are booleans; `conflicts` and `releases` are lists of strings drawn from `REQUIRED_TABLES`.
- Exactly one choice has `current: true`, and its `value` equals the top-level `current`.
- Nothing is dropped: `len(choices) == len(set(tables[T]))`.
- `--trait-choices` consumes no randomness — running it twice returns byte-identical JSON.
- `--trait-choices` on `Ship names` returns the `UNREROLLABLE_REASONS` refusal rather than JSON, and does so on **stderr** with a non-zero exit.

### 8.9 `test/test_ship_manifest.py` — entry shape and folder layout

- `set(SHIP_FOLDERS) == set(sp.SHIP_TYPES)`, every value non-empty and `_safe`-stable.
- The written entry carries every key of §6; `kind == "spaceship"`; `id` matches `^ship-[a-z0-9-]+-\d+$`; `gridWidth`/`gridHeight`/`hexes`/`tokenWidth`/`tokenHeight` are `int`.
- Folder is `<out>/<Category>/<Name>` with `<Category>` in `SHIP_FOLDERS.values()` — two levels, so `basename(dirname(folder))` recovers the category the way `A/server.js:1570` does.
- The manifest round-trips through `art.save_manifest`/`load_manifest` with `sort_keys=True` and no key collision when NPC entries are present in the same dict.
- **`TestSetTraitPersists`** — after a `--set-trait` regen, `entry["traits"]` and `entry["rawTraits"]` reflect the new value. This is the NPC bug (`generate-npc.py:4273-4280`) that ships must not inherit.
- After a regen, `sizeBand`/`gridWidth`/`gridHeight`/`tokenWidth`/`tokenHeight` are re-derived from the current `Size` trait.

### 8.10 `test/test_ship_glow.py` — the borrowed light subsystem

- A `## Shield generator` bullet reading *"a ring of heavy shield emitters glowing along the prow"* registers under `npc.has_light_source`.
- A Backdrop scene committing to a hue (*"lit crimson"*, *"amber floodlights"*) constrains `Glow colour` via `npc.filter_by_hue` + `npc.light_hues`.
- Over 400 rolls, a ship whose scene names a hue never pairs it with a `Glow colour` from a contradicting family (the two-contradictory-light-sources failure `filter_by_hue` exists to stop).
- The ship's own `PLACEMENT_REQUIRES`/`PLACEMENT_FORBIDS` prop gates fire: a `dock`-gated placement never lands on a vacuum scene.
- `has_light_source(scene)` reaching the portrait but not the token.

### 8.11 `test/test_ship_theme.py`

- **`test_theme_tags_only_on_the_five_themed_tables`** — a `@tag` anywhere else fails, the ship's `test_theme_tag_placement.py`. A tag on a single-segment table would ship literal `|| @cyberpunk` to the image model and print it in the dossier.
- Every `@tag` in the file names a live `## Theme` bullet.
- **`TestPolicyRunsBeforeTheme`** — for every (type, band, themed equipment table), the pool after policy-then-theme is a subset of the pool after policy alone; and over 400 rolls no themed equipment roll ever violates the policy. Constructed against a fixture where theme-first would demonstrably leak, so the assertion is not vacuous.
- Each of the 8 themes is reachable and, over 2000 rolls, each themed table's realized tagged share is within the drift band `apply_theme_share` documents (`generate-npc.py:1571-1585`).

### 8.12 `test/test_shared_surface.py` — the churn guard

The written-down list of §1's borrowed surface, asserted by name:

```python
NPC_SURFACE = ("parse_tables", "variant_table", "heading_for", "split_flags",
               "split_backdrop", "split_faction", "flags_for", "themes_of",
               "filter_by_theme", "apply_theme_share", "THEME_SHARE",
               "has_light_source", "light_hues", "glow_hue_families",
               "filter_by_hue", "estimate_tokens", "TOKEN_LIMIT",
               "CHARS_PER_TOKEN", "Knobs", "entry_for", "fetch", "_safe",
               "next_run_folder", "npc_folder")
ART_SURFACE = ("WORKFLOW_DIR", "DEFAULT_WORKFLOW", "POST_ALIASES", "Entry",
               "_slug", "parse_set", "locate_slots", "locate_post_slots",
               "image_ref", "build_post_job", "build_job", "Comfy",
               "find_server", "load_api_workflow", "load_manifest",
               "save_manifest", "WorkflowError")
```

Assert each exists and is callable/of the expected kind; assert `flags_for("Faction", b)` and `flags_for("Backdrop", b)` still return the third segment; assert `Knobs(args, (W, H), prefix)` still sets `.width`/`.height`. An NPC-side rename then fails here, loudly, at test time — which is the guarantee that makes zero-churn by-path loading safe, and the input to the Phase-2 library extraction.

### 8.13 `test/test_ship_workflows.py`

- `art.DEFAULT_WORKFLOW` still yields `slots.latent is not None` — if it ever does not, ship tokens silently render at the workflow's own size, so this must be an error and not a warning.
- `art.build_job` with a `Knobs` at each band writes the right `width`/`height` into that latent node.
- The RMBG template has exactly one node of `class_type == "RMBG"`, and after the `--rmbg-res` patch its `process_res` is `args.rmbg_res`.
- `art.locate_post_slots` finds the RMBG graph's `LoadImage` and `SaveImage` unchanged.

*(Fold into `test/workflow_schema.py`'s existing conventions if it already covers the first two for NPCs.)*

### 8.14 `test/fixtures/ship-tables-minimal.md`

The ship counterpart of `test/fixtures/tables-minimal.md`: every `REQUIRED_TABLES` heading, a `none` bullet plus ≥3 neutral bullets plus one bullet at each band in each equipment table, ≥1 bullet carrying each `SHIP_TYPES` slug, one `@tag` on each of the five themed tables, and one bullet per table carrying a `{...}` placeholder. Small enough that a full 1500-roll budget run is fast, complete enough that no assertion is vacuous.

**Not** added to `test/fixtures/roll-snapshot.json` — that file is the NPC baseline and `test/test_ship_policy.py:30-34` already explains why the ship tests build their own fixture instead.

---

## Build order

1. Delete the skip at `test/test_ship_policy.py:551-556` **last**, not first — it is the acceptance gate for step 3.
2. Author `prompts/spaceship-generator-tables.md`, header first, mining `scene-and-spaceship-tables.md` per §2. Write `test/test_ship_tables.py` and `test/fixtures/ship-tables-minimal.md` alongside it.
3. Run `test_ship_policy.py` with the skip removed. It is 683 lines of already-written acceptance criteria for the tables file, and it is the cheapest available proof that §3's matrix is satisfiable by the content just authored. Do not proceed until it is green.
4. `generate-spaceship.py`: bootstrap + constants + `roll_ship` + `check_tables` + `trait_cascade`. Tests §8.3, §8.4, §8.11, §8.12.
5. Prompt templates + `build_prompts`. Tests §8.5, §8.6, §8.10.
6. Render loop, manifest, dossier, CLI. Tests §8.7, §8.8, §8.9, §8.13.
7. Hand §6 and §7 to the GUI design.

At no point in steps 1-7 is a line of `generate-npc.py`, `generate-art.py`, `generate-3d.py` or `ship_policy.py` modified. The only pre-existing file edited is `test/helpers.py` (a 12-line `load_ship_generator()`), plus the one-line skip deletion and the one-line header note in `prompts/scene-and-spaceship-tables.md`.