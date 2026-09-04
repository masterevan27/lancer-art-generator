# Glow placement filtered against the source that licensed it

> **Status:** design, not started 2026-09-04. Follow-up to `Glow placement`,
> which shipped as a free roll; this is what makes the rolled light land
> somewhere a rolled source could actually have cast it.

## 1. Problem

The portrait asserts a coloured light and then says where it falls. The two
halves are rolled independently, and nothing checks that they agree.

`has_light_source()` already gates *whether* the glow sentence appears at all:
it fires only when some rolled bullet describes something that emits. That gate
works. The failure is one step further along — **the placement is rolled blind
to the source that licensed it.**

A generated NPC rolled these three emitters:

| Source | Table | Where it sits |
| --- | --- | --- |
| `…gauntlet on one forearm with a small glowing sensor ring` | `Feature` | forearm |
| `…a small status indicator lit at the collar` | `Outfit` | throat |
| a glowing ring structure and street running-lights | `Backdrop` | behind |

and then rolled the placement `rakes across {possessive} chest and shoulder`.
No pinhead indicator on a forearm or a collar can rake a whole chest, and the
backdrop is behind the figure so it cannot light the chest front either. The
prompt asserted a broadly lit surface with nothing in frame capable of lighting
it. The model resolved the contradiction the only way left to it: it painted
the light onto the armour as a hard-edged emissive band, reading as a decal
rather than as illumination.

This is the same class of failure the `Glow colour` table's own comment
records — "electric blue" came out as arcing electricity — one slot further
along. A prompt that names a lighting effect without a plausible cause gets the
effect drawn as an object.

### Goals

- A rolled placement is only reachable when some rolled source could physically
  have cast light there.
- The rarity of broad torso lighting falls out of the tables rather than being
  hand-tuned: it becomes uncommon because few sources can produce it.
- `Glow placement` stays in `REROLLABLE_TRAITS`.

### Non-goals

- Naming the source in the prompt sentence. Considered and rejected in §6: it
  spends prompt budget that §7 shows is not available, and needs a tiebreak
  rule when several sources roll, as they did above.
- Changing the `scene` flag. It answers a different question and already works.
- Tagging the `Backdrop` table's 144 emitting bullets individually. Backdrop
  light is behind the subject by definition; one blanket rule covers it.
- Any change to `Weather`. Lightning is not currently a light source and this
  spec does not make it one.

## 2. The zone vocabulary

One axis, four values, assigned by where the emitter sits on or around the
figure. A source carries the zones it can light; a placement carries the zones
it will accept; a placement is reachable when the two sets intersect.

`LIGHT_SOURCE_WORDS` matches 37 bullets outside `Backdrop`. Two of them are
false positives that §9 removes, leaving **35 genuine emitters**, which
classify cleanly:

| Zone | Count | What is in it |
| --- | --- | --- |
| `face` | 18 | 12 `Headgear` (every one is a visor, lens, HUD or accent light at the head), 2 `Eyes`, the 3 `Outfit` collar indicators, the throat pendant |
| `hands` | 10 | all 4 `Weapon` (glowing blade edges, palm sensor nodes), held `Gear` (lantern, holo sphere, data-sheet, wrist interface), the `Feature` forearm gauntlet ring and arm-joint glow |
| `torso` | 5 | `Outfit` jacket linings and cable tubing down the front, the exo-frame hip strip, the `Feature` thigh panel |
| `behind` | 2 | the `Gear` thruster-pack vents and shoulder wing lenses |

The four counts sum to 35. A bullet may carry more than one zone; none of
these does.

`Backdrop` light contributes `behind` without per-bullet tagging.

Placements take a **set**, because a source lights more than one zone: a
lantern carried low is a `hands` source that also lights a face from below, so
`catches {possessive} jaw and one shoulder from below` accepts `face hands`.
Flags are space-separated, exactly like the existing `|| hands mil weapon`.

Sources that distribute over the whole figure — `a long dark coat lined with
thin glowing cabling` — take several zones rather than motivating a fifth
value.

### Why this fixes the reported render

`rakes across {possessive} chest and shoulder` requires `torso`. The NPC in §1
rolled `hands`, `face` and `behind`. The placement is filtered out before the
roll, and the prompt never claims a lit chest.

`torso` is the rarest zone by a wide margin — five bullets out of 35. Broad
chest lighting becomes genuinely uncommon rather than as likely as any other
placement. That is the intended outcome, not a side effect.

## 3. `scene` stays as it is

`scene` marks a placement that puts light out in the environment: on a wall, on
the ground, hanging in the air. That requires the **backdrop** to be the
emitter, because a worn visor cannot stripe a wall behind its wearer.

`behind` marks a placement lit from behind the figure. A thruster pack can rim
your shoulders from behind; it cannot stripe a wall.

Two different questions, so two flags. `scene` is already implemented and
tested and this spec does not touch it. A placement may carry both.

## 4. Where the filter goes

The hook exists. `roll_npc()` already filters this exact table:

```python
if name == "Glow placement" and not has_light_source(
        split_backdrop(npc["Backdrop"])[1]):
    on_figure = [x for x in options if "scene" not in split_flags(x)[1]]
    options = on_figure or options   # never filter the pool down to nothing
```

`REQUIRED_TABLES` already orders every source table before the consumer —
`Eyes` and `Feature` at 12–13, `Outfit`, `Headgear`, `Weapon`, `Gear` at
17–20, `Backdrop` at 22, `Glow placement` at 23. That ordering is already
load-bearing and already commented as such. No reordering is needed.

The change is:

1. In the roll loop, when a bullet from one of the six source tables is chosen,
   test it with `LIGHT_SOURCE_WORDS`; if it matches, union its zone flags into
   a `light_zones` set.
2. If the rolled `Backdrop` scene emits, add `behind`.
3. At the filter site above, additionally keep only placements whose zone set
   intersects `light_zones`.

The existing `or options` guard is kept and generalised: **the pool is never
filtered to nothing.** §5 makes that guard unreachable in practice.

## 5. Fallback and coverage

When no placement is compatible, fall back to the unplaced wording the token
prompt already uses — `LEGACY_GLOW_PLACEMENT`'s shape, a glow with no asserted
location. It is safe against any source because it claims nothing.

That fallback should never fire, and a test asserts it: **every zone has at
least one compatible placement.**

Zone-tagging the existing ten exposes two thin spots:

| Zone | Placements today |
| --- | --- |
| `face` | 3, including the x2-weighted original |
| `behind` | 3 on-figure, plus 4 `scene` |
| `hands` | **1** |
| `torso` | **1** |

`hands` and `torso` each collapse to a single deterministic sentence once
filtering is on — every lantern-carrying NPC would get identical wording. So
the table grows from 10 to ~13, adding at least one more `hands` and one more
`torso` placement.

The `rakes across` bullet is reworded in the same pass. `rake` reads as an
object when its subject is a *glow*: everywhere the word succeeds in this repo
its subject is a light source — "Dramatic side lighting rakes across
{possessive} face", "Hard directional light rakes across the mechs' armor". A
placement should name an incoming direction and a falloff rather than a path to
trace across a flat plane.

## 6. Rejected: naming the source in the sentence

Tag each source with an origin phrase and cite it: *"A faint cyan glow from the
sensor ring at his forearm picks out…"*. This is the most explicit possible fix
and diffusion models render origin-plus-falloff well when told.

Rejected on budget. §7 measures the worst-case token prompt at ~500 tokens
against a 512-token ceiling. An origin clause costs 8–12 tokens on the
portrait, and the portrait is the shot that carries the placement. It also
needs a rule for choosing between sources when several roll — three did in §1 —
and any such rule is arbitrary in a way the zone intersection is not.

Zone filtering costs zero prompt tokens: it changes which bullet is chosen, not
what the sentence contains.

## 7. Prompt budget

Measured over the 34 generated NPCs in `output/LancerNPCs`:

| | portrait | token |
| --- | --- | --- |
| median | ~422 | ~445 |
| worst case | — | ~500 |

Against `TOKEN_LIMIT = 512`. This spec is budget-neutral by construction.

## 8. Re-roll, and the relationship to `rawTraits`

`reroll_trait()` mirrors the §4 filter. It cannot see zone flags for the same
reason `UNREROLLABLE_REASONS` gives five times over: **the manifest stores
these traits with their flags already stripped.**

The repo's answer to this so far is a hand-written manifest key per flag —
`young` for the Age bullet's flag, `outfit_notac` for the Outfit's. This spec
adds a third, `light_zones`, holding the derived set rather than the raw flags.
That keeps `Glow placement` rerollable instead of adding a sixth entry to the
refusal list.

**`light_zones` is written as debt, knowingly.** The [raw-bullets
spec](2026-09-04-raw-bullets-in-the-manifest-design.md) exists to delete keys
of exactly this kind; its §2.1 already subsumes `young` and `outfit_notac`.
When it lands, `light_zones` goes with them — zones are re-derived from the raw
bullets and the key is kept only for entries written before that change. That
spec's subsumed-keys list must name `light_zones`, or this key outlives its
reason.

If `rawTraits` is implemented first, this section is deleted rather than
implemented.

### Orphaned placements on re-roll

`Eyes`, `Feature` and `Headgear` are all rerollable and all carry `face`
sources. Re-rolling `Headgear` can delete the only `face` source out from under
a face placement, leaving the stored NPC asserting light from an emitter that
is gone — the same breakage `Backdrop` is refused outright to prevent.

Those three re-rolls recompute `light_zones` and re-roll `Glow placement` when
the stored one is orphaned. Recomputing rather than refusing, because all three
are traits a user re-rolls often.

## 9. The gate's two false positives

Found while classifying. `LIGHT_SOURCE_WORDS` matches the bare word `light`,
so two reflective bullets currently license a glow with nothing that emits:

- `amber-brown eyes catching the light` (`Eyes`)
- `a horned kabuto-style helmet with a trailing neck guard, its crest catching the last light.` (`Headgear`)

Both *reflect*. The second reflects daylight, which the regex's own comment
excludes explicitly: "Deliberately excludes plain daylight/dusk words like
'sun' or 'sunlit' - natural light doesn't motivate an arbitrary saturated glow
color either."

Either bullet alone is currently enough to switch the whole glow sentence on.
That is this spec's problem one layer lower — a glow asserted with no emitter —
so it is fixed here: the regex requires an emitting construction, and a test
pins both bullets as non-emitting.

## 10. Blast radius

| File | Change |
| --- | --- |
| `prompts/npc-generator-tables.md` | zone flags on 35 source bullets; placement table 10 → ~13 with zone flags; `rakes across` reworded |
| `generate-npc.py` | zone accumulation in `roll_npc()`; intersection at both filter sites; `light_zones` manifest key; `LIGHT_SOURCE_WORDS` false-positive fix |
| `docs/generate-npc.md` | the `## Glow placement` section documents the zone axis alongside `scene` |
| `test/test_glow_placement.py` | zone coverage per §5; intersection behaviour; the §9 non-emitters |
| `test/fixtures/tables-minimal.md`, `tables-themed.md` | fixture placements need zone flags to exercise the filter |
| `.claude/skills/npc-trait-import/` | the skill emits zone flags for new source bullets — `test_import_skill_flags.py` fails when it falls behind the tables |
| `2026-09-04-raw-bullets-in-the-manifest-design.md` | its subsumed-keys list gains `light_zones` |

`lancer-npc-import-gui` reads headings generically and derives its re-roll
buttons from `REROLLABLE_TRAITS`, which is unchanged — **expected to need no
change, to be verified rather than assumed**, per the standing note in the
Phase 2 and themed-generation specs.
