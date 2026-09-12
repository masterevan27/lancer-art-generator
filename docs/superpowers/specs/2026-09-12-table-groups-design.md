# Table groups: one slot for a family of near-duplicate bullets

**Date:** 2026-09-12
**Status:** approved in discussion, awaiting review of this document
**Repositories:** `lancer-art-generator` (the mechanism, the tables file, the
skill), `lancer-npc-import-gui` (the Tables tab and everything that reads the
same file)

## 1. The problem

`prompts/npc-generator-tables.md` rolls each trait from a flat list: every
`- ` bullet under a `## Heading` is one option, an `xN` prefix repeats it N
times, and `random.choice` picks one. Weight is list length and nothing else.

That works until a table accumulates families of near-duplicates. The Outfit
table holds 117 bullets, its women-only additive table another 75, and among
them are eleven flight suits, nine combat uniforms with plate carriers, eight
open jackets over a glowing bodysuit, and so on. Each variant is a legitimate
entry, but together a family of eleven is eleven times as likely as one
distinct look, and the roll reads as "flight suit again".

The fix asked for is a two-stage roll: a family becomes one slot in the parent
table, and the specific variant is rolled second, inside the family. This
document specifies that mechanism, its effect on every consumer of the tables
file, and a first pass that applies it to Outfit.

## 2. What exists today, and why it constrains the design

Four independent parsers read the tables file, and all four agree on the same
three facts: `## ` starts a table, `- ` is a bullet, `xN ` is a weight.

- `generate-npc.py` `parse_tables()` returns `{heading: [bullet, ...]}` with
  weights expanded into repeats. `generate-spaceship.py` aliases it.
- `animate-portrait.py` re-implements it for one heading.
- `lancer-npc-import-gui/lib/tableBullets.js` mirrors it, adds the disabled
  bullet convention `<!-- - text -->`, and only ever rewrites a line in place.

The generator has no reference syntax between tables. `{possessive}` and
`{colour}` are string-format slots filled after the pick, not table lookups.
There is no validation of unknown headings or of bullet contents, so the file
already carries headings the roller never reads.

Three properties of the roller shape this design:

1. **The raw bullet is the record.** `npc["_raw"][name]` holds the verbatim
   line drawn, and it is what every re-roll pins, what `--set-trait` validates
   against, what the odds sampler counts, and what `heading_for()` reverse
   looks up by text. Its key set is contractually exactly `REQUIRED_TABLES`.
2. **One draw site does the work.** All but four tables are drawn at one place
   in `roll_npc()`, immediately after the per-table filter chain and the probe
   record that `--trait-choices` reads back.
3. **The random stream is a contract.** `test/fixtures/roll-snapshot.json`
   pins every trait of every seed, and the probe must be inert. An extra draw
   shifts every later draw for that seed.

The GUI side parses the file itself for the Tables tab, the Create form's
override dropdown, presets and the trait-import append, and asks the generator
for the odds and the Set… choices.

## 3. The contract in the tables file

A group is an ordinary `##` table. A parent table enters it through a
reference bullet:

```
## Outfit
- a heavy work jacket over a stained undersuit, sleeves shoved to the elbow || civ
- x2 => Flight suits
- => Black dresses
- => Black dresses (gundam) || @gundam

## Flight suits
- a fitted flight suit with the top half unzipped and knotted at the waist
- a tan and beige flight suit with rust-red accents and padded shoulders || mil

## Flight suits (she) +
- a flight suit tailored close through the bust, waist and hips

## Black dresses (gundam)
- a fitted black dress with a segmented crimson shoulder guard
- a black slip dress under a cropped crimson-piped jacket
```

Rules. Each is enforced by `check_tables()` so a bad file fails at startup,
with the heading and line named, rather than in a prompt.

- **Syntax.** A reference is `=> Name`, optionally after an `xN` weight. The
  name is the exact heading of the group table. Nothing else may follow the
  name except a flag segment holding theme tags.
- **Flags.** A reference carries no `civ`, `mil`, `notac`, `dressy` or other
  flag. Those stay on the members, since one group can legitimately hold a
  mil flight suit and a civ one. A reference may carry `@theme` tags, which
  describe the whole group (see below).
- **Existence and level.** The named table must exist and have at least one
  bullet. It must not be a `REQUIRED_TABLES` name or a pronoun variant of one,
  and it must not itself contain a reference. One level only.
- **One reference per group per family.** A table and its pronoun variants
  reference a given group at most once between them; weight is expressed with
  `xN` on that one bullet. A family rather than a table, because a woman's
  pool is the base table and her variant together - two references to one
  group across them would leave the odds report crediting a group's draws to
  whichever bullet it found first. This is what lets it attribute them back to
  the reference row exactly.
- **Variants.** A group may have `Name (she)` and `Name (she) +` tables, in
  `variant_table()`'s own two forms and with its meanings: `Name (she)`
  replaces the group for that subject, `Name (she) +` is added to it. A
  women-only member goes in `## Flight suits (she) +`; a whole feminine
  rewrite of a group goes in `## Flight suits (she)`; and a reference in
  `## Outfit (she) +` makes the group itself women-only. `group_headings()`
  mirrors `variant_table()` so that the draw site, `heading_for()`,
  `trait_odds()` and `trait_choices()` all read the same pool.
- **Themed groups.** A reference tagged `|| @gundam` behaves at the parent
  level exactly as a tagged bullet does today: dropped for other themes, and
  duplicated up to `THEME_SHARE` for its own. Members of a themed group carry
  no theme tags; the check refuses one. A neutral group (untagged reference)
  is reachable from every theme, and its members may carry their own tags,
  which are filtered and weighted inside the group only. The `(gundam)` suffix
  on a themed group's name is a naming convention for readability, not
  syntax.
- **Placeholders.** Members may use `{possessive}` and the other pronoun
  slots exactly as parent bullets do, because resolution happens before the
  substitution pass.

The preamble section `## How the script reads this file` documents the
reference syntax alongside the bullet and weight syntax, with the rules above
in the same voice, and names the Callsigns `###` convention as the cosmetic
alternative that does not change odds.

## 4. The generator

### 4.1 Parsing and checking

`parse_tables()` is unchanged: a reference is just a bullet whose text starts
with `=> `, and `xN` expansion applies to it like any other. A small pure
helper family beside `split_flags()` does the reading:

- `is_reference(bullet)` and `reference_target(bullet)` return whether a
  bullet is a reference and the group name it points at, flags stripped.
- `group_tables(tables)` returns the set of headings referenced from any table
  (with their variants), for the checks and for the odds report.

`check_tables()` gains the rules in section 3. Each failure is a
`SystemExit` naming the parent heading, the reference text and the rule.

### 4.2 The filter chain becomes a function

The body of the `REQUIRED_TABLES` loop in `roll_npc()` that turns
`variant_table(tables, name, subject)` into the drawn-from `options` list is
extracted into a nested function `narrow(name, options)` defined inside
`roll_npc()`, which closes over the loop's state (`young`, `role_mil`, the
forced-trait flags and so on) rather than threading it through a context
object. It contains every filter the loop applies today for that table,
named functions and the inlined ones alike, in the same order, and it never
touches `rng`. The loop calls it once per table exactly where the inlined
code was, so the roll snapshot is byte-identical before any group exists.
That is the first regression gate.

### 4.3 Resolution at the draw site

Nearly every filter in the chain hands the whole pool back rather than empty
it. Filtering a group's members on their own would therefore re-admit, say,
a civ-only group for a mil NPC the moment the mil filter emptied it, which
is a flag-semantics change the flat list never had. So the drop filters run
over the members and the parent pool together, as one union, exactly as they
sit in the flat list today:

1. For each distinct reference in `options`, collect the member list
   `variant_table(tables, target, subject)`. Build the union: `options`
   followed by every member list.
2. Run the drop filters over the union once - `narrow(name, union,
   theme_share=False)`. Each group's member pool is the survivors that are its
   members. The parent pool is the parent list narrowed on its own,
   `narrow(name, options)`, which is byte-for-byte the pre-feature chain with
   each reference sitting in it as one flagless slot. Multiplicities are
   preserved either way, so `xN` weights behave as they do now.

   The theme share is the one step that cannot run over the union.
   `apply_theme_share()` duplicates a theme's own bullets until they hold
   `THEME_SHARE` of the pool it is handed, so a multiplier sized against
   parent-plus-members leaves every copy behind in the parent when the members
   are split back out - measured on the live file at 0.80 tagged against a
   0.60 target, 192 copies of one bullet in a 230-entry pool. It therefore
   runs once per side: inside the parent's own `narrow()` call, and again over
   each group's member pool. A tagged reference is then dropped or duplicated
   against the parent's own size, which is what §3's "Themed groups" intends,
   and a tagged member of a neutral group is weighted against its own group's
   size, which is §3's "filtered and weighted inside the group only". It is
   not lifted out of `narrow()` to run after the split on both sides: that
   would reorder the share behind the civ/mil and weapon-policy filters, which
   `apply_theme_share()`'s own docstring says not to trade for.
3. Remove from the parent pool every reference whose member pool is empty,
   unless that would empty the parent pool, in which case leave it (the
   "never filter to nothing" convention every filter here follows).
4. Record each member pool in the probe under the group's heading and the
   parent pool under `name`, then draw `value = rng.choice(parent pool)`.
5. If `value` is a reference, draw again from its member pool (falling back
   to the unfiltered member list if that pool is somehow empty).

With no references in the pool, the union is the pool, and steps 3 and 5 do
nothing, so the stream is unchanged. When a reference is drawn, one extra
draw is consumed, which is the intended change to that seed. A forced
override for the table still performs the parent draw and discards it, as
today, and never triggers step 5. A forced value that is itself a reference
is refused with the table named, since a reference is not a value.

The four other draw sites (Pronouns, Theme, Stance, the `nogear` Gear
re-draw) and the legacy no-`_raw` re-roll path do not resolve references.
`check_group_references()` refuses a reference in every table one of them
reads, each with its own message naming the site: `Pronouns`, `Theme` and
`Stance` because those three are drawn outside the loop; `Gear` because a
Backdrop flagged `nogear` re-draws it after the loop from a pool it has
narrowed by hand; and every table in `REROLLABLE_TRAITS` because
`reroll_trait()` rebuilds the draw by hand for an entry written before `_raw`
existed. Refused rather than resolved - see §8 - because a reference in one of
those tables would resolve on most rolls and paste `=> Name` into the dossier
and the prompt on the rest.

### 4.4 What is recorded

`npc["_raw"][name]` is the member's line, verbatim from the group table. So:

- Re-rolls pin the member and reproduce the loop exactly. Same-seed regen is
  exact.
- Downstream reads of the slot's flags (the `notac` rule that shapes Weapon
  and Gear, the `dressy` policy, `outfit_notac` for hardtech) see the member's
  flags, which is where the flags live.
- `_raw`'s key set is still exactly `REQUIRED_TABLES`. Group tables are not
  required tables.

`heading_for(tables, name, subject, bullet)` learns to answer a group's
heading: after the existing variant checks, if the bullet is in a group table
referenced from `name` or its variants, return that group's heading.

### 4.5 Odds

`trait_odds()` counts a resolved member under its group heading and also
increments the reference row under the parent, so the parent's rows still sum
to one and the group's rows show each member's overall probability. Finding
the reference row is exact because one family - a table and its variants
together - references a group at most once.
The output filter admits group tables (and their variants) alongside required
tables. `test_trait_odds` gains: a group's rows sum to the reference row's
figure; every member is reported even at zero; the family-sums-to-one test
still holds for required tables.

### 4.6 Choices and set

`trait_choices()` builds its candidate list from the deduplicated variant
table today. It now expands each reference into the target's deduplicated
members, each with `heading` set to the group heading, and never offers the
reference itself. `allowed` for a member is "the reference survived in the
parent probe and the member survived in the group probe". `--set-trait`
therefore accepts a member and refuses a reference, with the same "not one of
the values this trait can take" message it gives any unknown value.

### 4.7 The ship generator

`generate-spaceship.py` shares `parse_tables`, `variant_table`,
`heading_for` and the filters but has its own roller. Its `check_tables()`
refuses any reference bullet with a message saying groups are not supported
for ships yet. Nothing else changes there.

### 4.8 Determinism gates

`test/fixtures/roll-snapshot.json` pins the roll of `test/fixtures/tables-minimal.md`,
not of the live tables file, and that fixture is not regrouped.

- Gate 1: mechanism landed, tables files unchanged. `roll-snapshot.json`
  must pass untouched, and `ProbeIsInert` must hold. A separate fixture
  `test/fixtures/tables-groups.md` exercises resolution.
- Gate 2: the Outfit first pass landed in the live file. The snapshot is
  still untouched; the gate is the full suite plus a `--trait-odds` readout
  showing Flight suits at one slot's share of Outfit, recorded in the commit
  message.

## 5. The import GUI

Nothing in the GUI breaks on a reference bullet today; it would be quietly
wrong in five places.

- **Tables tab layout.** `parseTableFile()` records, per table, the group
  headings it references. `groupTables()` nests a group table under the table
  that references it, and the existing `Name (x)` rule nests a themed group
  under its neutral sibling. A reference row is rendered as written with a
  "group" marker and a link that scrolls to the group's table. It gets no flag
  checkboxes and no weight input beyond the `xN` it already supports; its
  theme tag shows as text the way tags show today.
- **Flag checkboxes.** `flagsFor(tableName)` takes the parse result's
  reference map and falls back to the vocabulary of the table that references
  a group, so members get Outfit's civ, mil, notac and dressy boxes and
  `setBulletFlag` accepts them. The live-file drift test uses the same
  lookup.
- **Chances panel.** The generator's odds report now includes group tables,
  so settled percentages appear for members. The local estimate shown while a
  sample is pending becomes the member's share within its group multiplied by
  the reference's share of the parent, so estimate and settled figure are on
  one scale. `renderChanceNote` says for a group table: "Rolled only when
  <parent> draws this group."
- **Presets.** `diffPresetAgainstTables()` leaves a reference bullet alone
  when the preset has no key for the group it points at: a preset saved
  before the group existed says nothing about entering it, and the current
  whitelist rule would otherwise switch the whole group off. The preview
  lists, as it already does, any parent entries the preset names that are no
  longer in the parent. Presets saved after the change record group tables as
  ordinary tables.
- **Create-form overrides.** `lib/traitOptions.js` expands each reference
  into the target's members under a group heading in the dropdown and never
  offers the reference as a value. Set… needs no change because its values
  come from `--trait-choices` (section 4.6).
- **Trait Imports.** `insertBulletIntoTables` already appends under any
  existing heading, so a candidate may target a group table. No change.

The GUI README's Tables tab section documents groups, and `known-issues.md`
records that a preset predating a group cannot express "group off".

## 6. The trait-import skill and its tests

- `SKILL.md` gains, in the shape section: a group table takes the shape line
  of the table that references it; a run never authors a reference bullet;
  a candidate targets the group by its exact heading when the trait is a
  variant of an existing family.
- `test_import_skill_shape.py`: the set of known tables widens to include
  group tables (with their variants) for the reverse check, and a group table
  needs no shape line of its own.
- `test_import_skill_flags.py`: `flags_used()` follows references so flags on
  members are covered by the documented flag table.
- `test/helpers.py` `table_keys(name)` / `bullets_for(name)` follow
  references, so the theme visibility and live-pool measurements see members.
- `test_theme_tag_placement.py`: a tag on a reference is allowed only when
  the parent is a `THEMED_TABLES` table; a tag on a member of a themed group
  is refused (mirrors `check_tables`).

## 7. First pass over Outfit

Line numbers refer to `prompts/npc-generator-tables.md` at commit `a4e9b39`.
"Base" members come from `## Outfit` and go in `## <Group>`; "she" members
come from `## Outfit (she) +` and go in `## <Group> (she) +`. The reference
replaces the moved bullets in the parent at the position of the first moved
bullet. A women-only group is referenced from `## Outfit (she) +` and its
table has no variant suffix.

Decisions taken in discussion:

- Themed members stay as tagged bullets in the parent unless two or more of
  one theme share a family: only the two cyberpunk bodysuits form a themed
  sibling group. The gundam flight suits (1823, 1928), the gundam armor
  (1827), the scav tank top (1818) and the scav jacket (1825) stay in place.
- Existing `x2` weights on members (1860, 1871) are kept; they become
  within-group weights.
- The corporate blazer (1931) keeps its tag inside its pair, the one tagged
  member in a neutral group in this pass. It forgoes the parent-level theme
  boost, which was accepted.
- One cross-group near-duplicate is left as is: 1826 (flight suit) and 1835
  (work coveralls) both render as an orange jumpsuit under a grey scarf.

| Group | Base members (lines) | She members (lines) |
|---|---|---|
| Flight suits | 1732, 1766, 1767, 1769, 1793, 1794, 1798, 1826, 1829, 1842 | 1860 (x2), 1867, 1877, 1891, 1909 |
| Combat uniforms and plate carriers | 1743, 1744, 1745, 1749, 1750, 1752, 1753, 1756 | 1869 |
| Field jackets | 1759, 1762, 1763, 1779, 1805, 1828, 1830 | 1879 |
| Open jackets over plated or glowing bodysuits | 1758, 1781 | 1872, 1873, 1874, 1887, 1888, 1889 |
| Glowing-seam bodysuits | 1770 | 1875, 1876, 1882, 1892, 1907, 1908 |
| Glowing-seam bodysuits (cyberpunk), referenced from `Outfit (she) +` with `@cyberpunk` | | 1930, 1932 |
| Unlit tactical bodysuits | 1764, 1797, 1806 | 1870, 1916, 1926 |
| Hardsuits and segmented armor | 1746, 1751, 1755, 1780, 1791, 1792, 1799, 1802, 1803, 1844 | 1871 (x2), 1915 |
| Caped armor suits | 1772, 1775, 1800, 1807 | |
| Plain traditional robes | 1785, 1786, 1787, 1811, 1812, 1813 | |
| Kimonos and fine robes | 1810, 1815, 1816 | 1898, 1899, 1922 |
| Lacquered samurai armor | 1788, 1801, 1808, 1809 | 1912, 1919, 1920, 1921 |
| Work coveralls | 1733, 1822, 1832, 1835, 1843 | 1864 |
| Dress uniforms | 1747, 1771 | 1868, 1894, 1895 |
| Long coats over fatigues | 1734, 1748, 1768, 1838, 1845 | |
| Leather jackets | 1742, 1795, 1833, 1836 | 1933 |
| Tank tops | 1737 | 1880, 1884, 1902, 1911, 1913 |
| Bomber and flight jackets | 1778, 1782, 1804 | 1896, 1914 |
| Open jackets over crop tops, referenced from `Outfit (she) +` | | 1881, 1883, 1900, 1903, 1906 |
| Cheap suits | 1839, 1847 | |
| Corporate skirt suits, referenced from `Outfit (she) +` | | 1866, 1931 (keeps `@corporate`) |

Every reference is weight 1. After the move, `## Outfit` holds 37 ungrouped
bullets (33 distinct looks plus the four tagged bullets that stay) and 18
references, and `## Outfit (she) +` holds 23 ungrouped bullets (22 plus the
tagged gundam flight suit) and 3 references. The three-member candidates the clustering flagged
(corset coats, tactical vest over a shirt) are left alone.

## 8. Out of scope

- Groups in the ship generator's tables (refused by its check for now).
- Nesting a group inside a group.
- A share boost for a neutral group that happens to contain tagged members.
- Pruning duplicates within a group; grouping makes them visible, and that is
  a content pass for later.
- Any table other than Outfit. The mechanism is generic; applying it
  elsewhere is a curation decision per table.
- `Gear`, and every table in `REROLLABLE_TRAITS` (`Callsigns`, `Build`,
  `Height`, `Skin`, `Hair`, `Eyes`, `Feature`, `Demeanor`, `Headgear`,
  `Glow colour`, `Glow placement`). Each of those has a second draw site that
  does not resolve references - the `nogear` Gear re-draw and the legacy
  no-`_raw` re-roll - so `check_tables()` refuses them by name until those two
  sites resolve as well. Teaching them to is its own change, with its own
  filter questions: the `nogear` re-draw has already narrowed its pool by hand
  by the time it draws.

## 9. Acceptance

- `python -m unittest discover test` passes in the generator at both gates,
  with the snapshot untouched at both.
- A tables fixture with a neutral group, a themed group and a women-only group
  rolls: the reference is one slot, an empty member pool drops the reference,
  a themed reference obeys the theme filter and share, `_raw` holds the
  member, same-seed regen reproduces it, `--trait-choices` offers members and
  never the reference, `--set-trait` accepts a member and refuses a reference,
  `--trait-odds` reports group tables with rows summing to the reference row.
- `check_tables()` refuses each rule violation in section 3 with the heading
  and line named, and the ship check refuses any reference.
- `node --test` passes in the GUI with new tests for nesting, inherited
  flags, the chances estimate and note, the preset rule, and the override
  dropdown expansion.
- Both READMEs and the tables file preamble describe the syntax and rules.
- `generate-npc.py --trait-odds` on the regrouped live file shows Flight suits
  at roughly one slot's share of Outfit rather than eleven.
