# Storing raw bullets in the manifest, so any trait can be re-rolled

> **Status:** design, not started 2026-09-04. Follow-up to `--reroll-trait`,
> which shipped covering 11 of 24 traits; this is what the other 13 need.

## 1. Problem

`--reroll-trait` re-rolls one trait of a stored NPC and keeps the rest. It
refuses 13 of the 24 rolled traits, and the refusal is honest rather than
conservative: **the manifest is a lossy record of the roll.**

`roll_npc()` strips a bullet's flag segment before storing it, for the nine
tables in its strip list. A live roll stores:

```
Role     -> 'a colonial administrator'          the '|| mil' is gone
Outfit   -> 'a tailored jacket cut close…'      flags gone
Weapon   -> ''                                  flags gone
Backdrop -> 'A half-body portrait || Behind him…'   flag segment gone
Faction  -> 'IPS-Northstar || riveted… || civ palette'   intact
```

So re-rolling `Outfit` cannot know whether the Role was `mil`, and would offer
a civilian a service uniform. Re-rolling `Stance` cannot know whether the
Weapon occupied a hand, and would put hands in pockets around a rifle. These
are precisely the contradictions the flags exist to prevent, so producing them
in a "reroll" feature would be a regression dressed as a feature.

The repo has met this before and solved it one flag at a time: `young` is a
manifest key of its own, written alongside the traits, because the Age bullet's
flag was gone by the time the entry was saved. That is the pattern this
generalises.

It has since met it a second time. The [headgear/outfit register
spec](2026-09-04-headgear-outfit-register-design.md) gates `Headgear` on the
Outfit's `notac` flag, which would have pushed `Headgear` out of
`REROLLABLE_TRAITS` — so it records `outfit_notac` as a second key of exactly
this kind. When this spec lands, `outfit_notac` and `young` are both subsumed:
§2.1 deletes the hand-written filter rebuilds in `reroll_trait()`, and the
`Headgear` branch goes with the other eleven. The two keys stay written for the
benefit of entries and readers that predate `rawTraits`.

### Goals

- Every rolled trait becomes re-rollable, under the same filters a fresh roll
  applies.
- Entries written before the change keep working, at today's reduced coverage.
- No change to what the image prompts or dossiers contain.

### Non-goals

- Changing what `--regen-manifest` reproduces. A plain regen already works from
  the stripped traits and must keep producing byte-identical prompts.
- Re-rolling `Given names` / `Family names`. Those stay refused for an
  unrelated reason: the folder and manifest id derive from the name, so
  changing one is not a change in place.
- Re-rolling `Pronouns` or `Theme`, which gate whole groups of tables and would
  require re-rolling those too. Those are a "re-roll the NPC" feature, not a
  per-trait one.

## 2. Approach

Store the raw bullets beside the rendered traits.

```json
{
  "id": "npc-Nadia-Okonkwo-1234",
  "traits":    { "Role": "a colonial administrator", "...": "..." },
  "rawTraits": { "Role": "a colonial administrator || mil", "...": "..." }
}
```

`roll_npc()` already has each raw bullet in hand at the moment it strips it, so
collecting them is a dict assignment in the loop it already runs, exposed as
`npc["_raw"]` next to the `npc["_young"]` it already sets. The manifest writer
excludes `_`-prefixed keys by construction (`{k: v for k, v in npc.items() if
not k.startswith("_")}`), so this is written explicitly, like `young` is.

### 2.1 Re-rolling with them

With raw bullets available, a re-roll stops needing bespoke per-trait filter
logic. It becomes a full `roll_npc()` with every trait except the target pinned
as an override:

```python
overrides = {name: raw for name, raw in entry["rawTraits"].items()
             if name != target}
npc = roll_npc(tables, rng, overrides)
```

This is the *designed* use of the override path, not a trick: `--set-trait` is
documented as taking a bullet verbatim with its flags, and the script's own
help shows `--set-trait Outfit="an elaborate floral kimono … || civ notac"`.
Every filter then runs exactly as it does for a fresh roll, because it *is* a
fresh roll with one free variable — which also means the 11 hand-written filter
rebuilds in `reroll_trait()` are deleted rather than extended.

### 2.2 Entries without them

An entry written before this change has no `rawTraits`. It falls back to
today's behaviour: `REROLLABLE_TRAITS` and its hand-rebuilt filters, with a
message saying that re-rolling the rest needs a re-roll of the NPC. So the
fallback path is the code that exists now, kept rather than replaced, and the
new path is additive.

## 3. Risks

**The Foundry importer contract.** `docs/foundry-importer-contract.md` governs
the manifest as a cross-repo interface — the client ships inside a released
`module.zip`. Adding a key should be additive and safe, but that document is
the authority and must be read and updated before this lands. This is the one
item that could change the shape of the design.

**Manifest size.** Raw bullets roughly double the stored trait text per NPC.
On a local single-user tool with a few hundred entries this is not a concern;
it is recorded so nobody is surprised by the diff.

**Two records of one thing.** `traits` and `rawTraits` can disagree if a future
edit updates one and not the other. `--reroll-trait` already rewrites `traits`
on a successful re-roll and would have to rewrite both. A test that every
`rawTraits` value strips to its `traits` value is cheap and worth having.

## 4. Verification

1. A fresh roll writes `rawTraits` for every trait in `traits`, and each raw
   value strips to exactly its rendered counterpart.
2. Re-rolling `Outfit` on a `mil` Role never yields a `civ` bullet, and vice
   versa, over a few thousand entries.
3. Re-rolling `Stance` never yields a two-hands-free pose on an NPC whose
   Weapon or Gear occupies a hand.
4. Re-rolling any trait leaves every other trait byte-identical.
5. An entry with no `rawTraits` still re-rolls the 11 traits it can, and
   refuses the rest with the current message.
6. A plain `--regen-manifest` regen of a pre-change entry produces a prompt
   byte-identical to the one it produced before.
7. The importer contract's tests still pass unchanged.
