# Role and dress register: gating Outfit and Faction on what the job is

> **Status:** implemented 2026-09-04, on branch `dress-register`.
> One correction was made while building to it: §3.2 originally said a `dressy`
> bullet "is dropped for a `plain` Role" for *both* tables, which contradicted
> §3.3's Faction design. §3.3 won — Faction keeps its place in the pool and
> loses only its visual — and §3.2 and §6 now say so. Independent of the
> [themed-NPC parent spec](2026-09-03-themed-npc-generation-design.md) and of
> its unshipped Phases 3 and 4 — see §2, which is the part of this document
> most worth reading if you already know that spec.

## 1. Problem

A rolled dockworker came out wearing *"a dark robe traced with gold embroidered
trim, a purple sash knotted at the waist and small tassels hanging loose"*,
with the Faction clause adding *"heavy brocade and gold braid, an heraldic
crest at the shoulder, in deep crimson"* on top of it. The figure reads as
minor nobility; the Role line two clauses earlier says dockworker. Nothing in
the generator prevents this, and two independent gaps produced it.

**Outfit has no register axis.** The only Role→Outfit gate is the `civ`/`mil`
split. `a dockworker` is an unflagged (civilian) Role and the gold-trimmed robe
is flagged `civ`, so it is fully reachable — as are the kimono, the lacquered
samurai armour and the swagged chain-loop mantle. `civ` distinguishes *not a
uniform* from *a uniform*. It says nothing about whether a garment is workaday
or ceremonial, which is the distinction that failed here.

**Faction has no gate at all.** `Karrakin Trade Baronies || heavy brocade and
gold braid, an heraldic crest at the shoulder, in deep crimson || palette`
carries neither `civ` nor `mil`, so every Role reaches it. Fixing Outfit alone
would leave the same dockworker in baronial heraldry.

### Goals

- A Role whose work is manual or dirty never rolls ceremonial or finely-made
  dress, from either table.
- Roles for whom fine dress is *right* — a corporate liaison, a colonial
  administrator — keep it, at unchanged odds.
- Adding a Role later needs no edit here.
- No pool is ever filtered to empty.

### Non-goals

- Theme tagging (parent spec Phase 4). See §2.
- The parent spec's other Phase 3 items: `bulk`/`enclosed`, `sealed`/`vacuum`,
  Backdrop `civ`/`mil`, `MECH_ACCESS`, the roll reorder.
- Retiring or absorbing `notac`. It stays, and §4.1 explains why it is not the
  flag this needs.

## 2. Why Phase 4 is not this

The Theme mechanism is built, tested and documented, and **no bullet in
`npc-generator-tables.md` carries a theme tag** — every `@` in the file is
prose inside a comment. `filter_by_theme()` and `apply_theme_share()` therefore
do nothing today; `test/theme_visibility.py` says as much in its own docstring:
*"with no bullet tagged the answer is 0% everywhere."* That is a deliberate
deferral, not a defect.

It is worth being explicit that landing Phase 4 would **not** fix the reported
bug, because the two are easy to conflate. The parent spec's answer to
traditional dress is Theme: *"13 of 87 Outfit bullets are traditional dress, so
14% of civilian NPCs arrive in it purely because that many got written,"* and
tagging them `@neosamurai` converts frequency-by-bullet-count into a single
Theme weight. But a rolled `@neosamurai` **dockworker** still reaches the
gold-trimmed robe — and reaches it *more* often than today, because
`apply_theme_share()` weights a theme's own tagged bullets up within its pool.
The parent spec makes this explicit and intends it: *"Theme is deliberately
independent of Role: a pirate is as likely to look neosamurai as cyberpunk. Do
not gate one on the other."*

So this is a third axis, orthogonal to both `civ`/`mil` and Theme, and it lands
independently of Phase 4 in either order.

## 3. Approach

Two flags and one policy table, following the shape `WEAPON_POLICY` already
established rather than inventing a new one.

### 3.1 `DRESS_POLICY`, keyed on `ROLE_CATEGORIES`

```python
DRESS_POLICY = {
    "Laborers":    "plain",   # dockworker, freelance salvager
    "Technicians": "plain",   # chief mechanic, maintenance technician
}

# What every other category gets. A default rather than six more entries, so a
# Role category added later is covered without a second edit here - the same
# reasoning DEFAULT_WEAPON_POLICY carries.
DEFAULT_DRESS_POLICY = "any"
```

Keyed on the category, not on a per-Role flag, for the reason the parent spec
gives for `MECH_ACCESS`: `ROLE_CATEGORIES` already encodes this knowledge, and
a second per-bullet flag on `## Role` would duplicate it and then drift from
it. It also means the 22 Role bullets need no edit at all.

**Only two categories are `plain`, and that is not an oversight.** The other
six are either already handled or genuinely entitled:

| Category | Why not `plain` |
|---|---|
| Pilots, Soldiers, Support | Every Role in them is flagged `mil`, and `filter_by_mil()` already drops every `civ` bullet — which is every ceremonial outfit in the table. Already barred. |
| Officials | Fine dress is *correct* for a corporate liaison or a colonial administrator. This is the case the gate must not break. |
| Criminals | A pirate in finery is a genre staple, not a mismatch. |
| Civilians | Contains `a scavenger-priest of a local machine cult`, for whom robes are the point. |
| Other | Unknown Roles stay unconstrained, matching how every other filter treats them. |

### 3.2 `dressy` on Outfit and Faction

A bullet flagged `dressy` reads as ceremonial, formal or finely made — gold
thread, lacquer, brocade, tailoring, ornament. An unflagged bullet is neutral
and reachable by everyone, which is what the overwhelming majority stay,
exactly as with `civ`/`mil`.

**The two tables consume the flag differently, and this is deliberate.** On
Outfit a `dressy` bullet is dropped from the pool for a `plain` Role. On
Faction it is *not* — the bullet stays reachable and only its visual segment
is suppressed, for the reason §3.3 gives. Dropping a Faction outright would
throw away an affiliation to fix a garment.

On Outfit the flag joins the existing second segment (`|| civ notac dressy`).
On Faction it joins the third (`|| mil palette dressy`), since the two tables
carry different numbers of prose segments — the same asymmetry the file already
documents for `civ`/`mil`.

### 3.3 Faction keeps its name and loses its visual

A dockworker *employed by* the Karrakin Trade Baronies is good flavour. A
dockworker *dressed as a baron* is the bug. Barring the whole faction would
throw away the first to fix the second.

So for a `plain` Role, a `dressy` Faction contributes its **name** to the
dossier and byline as normal, and its **visual segment is dropped** — the
clothing sentence simply does not get the brocade clause.

Two Faction bullets take the flag. `Karrakin Trade Baronies || heavy brocade
and gold braid, an heraldic crest at the shoulder, in deep crimson` is the
reported one. `Smith-Shimano Corpro || precisely tailored with fine seam
piping, in white and pale pastels` is the same failure in a quieter register:
precisely tailored white and pastels is not what someone spends a shift in a
cargo hold wearing. The other six leave the flag off — issued and worn thin,
riveted and salt-stained, mismatched surplus and taped-over insignia all read
correctly on a dockworker, and the two non-affiliations have no visual at all.

This needs no new machinery. `split_faction()` already returns an empty visual
for the two non-affiliations, and `build_prompts()` already drops the clause
entirely rather than leaving a doubled comma:

```python
fields["faction_line"] = "%s, " % faction_visual if faction_visual else ""
```

Suppressing the visual for a `plain` Role reuses that path exactly.

## 4. What this is not

### 4.1 `dressy` is not `notac`

The overlap is tempting and wrong. `notac` means *do not pair this with
tactical gear*; `dressy` means *this is too fine for manual work*. Twenty
bullets carry `notac` — 13 in `## Outfit` and 7 in `## Outfit (she) +` — and
the two flags disagree on seven of them.

The disagreement is entirely in the base table, where `notac` covers both
finery and rags. Every one of these is `notac`; only the first group is
`dressy`:

| `## Outfit` bullet | `dressy`? |
|---|---|
| a dark robe traced with gold embroidered trim, a purple sash… | yes |
| a dark kimono cinched with a wide white sash tied in a full bow | yes |
| full lacquered samurai armor in dark green and black, ornamental tassels | yes |
| dark samurai robes with a long crimson cloak | yes |
| segmented crimson-lacquered armor plates over a floral-patterned quilted robe | yes |
| a fringed pleated mantle swagged with hanging chain loops | yes |
| a dark travel-worn robe with a crimson underlayer | **no** |
| layered white pilgrim's robes gone travel-stained at the hem | **no** |
| a weathered haori-style jacket, sleeves bound back with cord | **no** |
| a tattered dark robe hanging open at the chest, hems torn | **no** |
| ragged wrapped cloth bindings over bare limbs, feet bare | **no** |
| a dark robe with a pale patterned collar, red fingerless gloves | **no** |
| a dark patterned robe with a bright orange underlining, prayer beads | **no** |

A dockworker in ragged cloth bindings, a travel-worn robe or a weathered haori
is entirely plausible — several read as *poorer* than the default coveralls.
A dockworker in gold thread is not. Reusing `notac` would bar that whole second
group for no reason, and, being a preference rather than a rule on the Weapon
side, would carry semantics this gate does not want.

All 7 of the `## Outfit (she) +` `notac` bullets are `dressy` — the elaborate
floral kimono, the shrine robes, the plum-blossom kimono and the four lacquered
armour pieces are ceremonial without exception. That variant simply has no
ragged entries, which is why the flags coincide there and not below.

**13 Outfit bullets take `dressy` in total**, 6 of them reachable by any
pronoun set and 7 only by a woman.

### 4.2 It is not a weighting

Per the decision taken when this was scoped, the gate is a **hard bar with a
starvation guard**: a `plain` Role cannot roll a `dressy` bullet, but if the
filter would empty a pool the unfiltered pool is used instead. That guard is
the idiom already in the file — `options = grown or options  # never filter the
pool down to nothing`. It cannot trigger on today's content — a `plain` male
Role loses 6 of 87 Outfit bullets, a `plain` female Role 13 of 150 — but will
matter once Phase 4's theme filter narrows the same pool first. A thin theme
whose only tagged outfits happen to be ceremonial ones is exactly the shape
that would otherwise deal an empty pool.

## 5. Forcing a contradiction

Role is rolled before Faction and Outfit, so the ordinary case needs nothing
special. `--set-trait` can invert it, and the file already has a precedent for
exactly this shape in the Age/Build `young`/`figure` pairing, which this
follows rather than reinventing:

- **Outfit forced `dressy`, Role rolled** → drop `plain` categories from the
  Role pool. An explicit choice of outfit should not collide with a randomly
  rolled dockworker and abort the run.
- **Role forced `plain`, Outfit rolled** → the normal filter; `dressy` bullets
  are out of the pool.
- **Both forced, contradictory** → `SystemExit` naming both, the same as
  `--set-trait Age` and `--set-trait Build` disagreeing today. Two explicit
  choices that contradict each other are a mistake worth reporting rather than
  silently resolving.

## 6. Changes

| Where | What |
|---|---|
| `generate-npc.py` | `DRESS_POLICY`, `DEFAULT_DRESS_POLICY`, `dress_policy_for()`, a `filter_by_dress()` applied to **Outfit only** after `filter_by_mil()`, the Faction visual suppression in `build_prompts()`, and the forced-contradiction check |
| `npc-generator-tables.md` | `dressy` on 13 Outfit bullets (6 base, 7 in the `(she) +` variant) and on 2 Faction bullets; the flag documented in the segment-conventions section, the Outfit table comment and the Faction table comment |
| `docs/generate-npc.md` | A section on register, alongside "Name the number" and "Period vocabulary matters" |
| `test/test_dress_register.py` | New |

The Import GUI needs no change: it derives its override list from
`REQUIRED_TABLES`, which gains no entry, and its new trait-value dropdown reads
bullet text verbatim, so `dressy` shows up in the label like any other flag.

## 7. Verification

1. A rolled `Laborers` or `Technicians` Role never carries a `dressy` Outfit,
   over a few thousand seeds.
2. An `Officials` Role still reaches `dressy` outfits, at a rate
   indistinguishable from today's — the gate must not quietly narrow the roles
   it does not target.
3. A `plain` Role rolling Karrakin gets the name in its dossier and **no**
   brocade clause in either prompt, with no doubled comma where the clause was.
4. A non-`plain` Role rolling Karrakin is unchanged.
5. Every `dressy` bullet is also reachable by someone — a flag that bars a
   bullet from everyone is a typo, and the same vacuity check the Faction and
   Stance tests already carry catches it.
6. The starvation guard returns the unfiltered pool rather than an empty one
   when every candidate is filtered out.
7. Forcing a contradiction exits with a message naming both traits; forcing
   only one of the pair does not.
8. Prompt budget does not regress — `dressy` removes clauses from some prompts
   and adds none, so p99 should hold or improve.
