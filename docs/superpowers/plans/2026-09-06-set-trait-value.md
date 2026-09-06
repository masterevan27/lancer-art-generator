# Setting a trait to a chosen value — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an already-rolled NPC have one trait pinned to a chosen value and re-rendered, and let a caller ask which values that trait could legally take.

**Architecture:** Two additions, both leaning on machinery that already exists. `roll_npc()` gains an optional `probe` dict that records the fully-gated pool it computes for each table — that is the legality answer, produced by the one filter chain rather than a copy of it. `reroll_from_raw()`'s existing `pinned` argument, with `free=set()`, is "keep every other trait, change this one".

**Tech Stack:** Python 3, standard library only. Tests are `unittest`, run with `python -m unittest discover test`.

**Spec:** `docs/superpowers/specs/2026-09-06-set-trait-value-design.md`

## Global Constraints

- **No second filter chain.** Legality is whatever `roll_npc()`'s pool says. Never re-derive a filter outside that function.
- **The probe must be inert.** Recording pools consumes no randomness and changes no value: a probed roll and an unprobed roll at the same seed produce identical NPCs. Task 1 tests this and every later task depends on it.
- **Raw bullets only.** Both new commands refuse an entry whose `rawTraits` is missing or empty, reusing `reroll_trait()`'s existing wording. `hasRawTraits`-style emptiness checks, never key matching.
- **Values are raw bullets, verbatim, flags included.** That is what `--set-trait` consumes and what the downstream filters read. Never strip flags before storing or emitting a candidate.
- **`--release` expands to the cascade closure** via `trait_cascade()`, never the bare name.
- **Weather is exempt** from the downstream conflict check. Nothing narrows its pool; the Backdrop's `weather` flag only decides at prompt-build time whether it is rendered.
- Python files in this repo carry long explanatory comments stating *why*. Match that register; a one-line comment where the surrounding code writes ten reads as unfinished.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `generate-npc.py` | everything | modified in five places (below) |
| `test/test_set_trait_value.py` | the new behaviour | created |
| `README.md` | test count | modified |
| `docs/generate-npc.md` | the two new flags | modified |

`generate-npc.py` is one large module by long-standing convention in this repo; the new code goes in it rather than into a new module, next to the functions it extends:

- `roll_npc()` (line 1136) — the `probe` parameter and its four record points.
- `trait_choices()` — new, placed immediately after `reroll_trait()` (ends line ~2792), because it is the query half of the same idea.
- `npc_from_entry()` — new, extracted from `regenerate_one()`, placed immediately before it.
- `print_trait_choices()` — new, placed after `trait_choices()`.
- `parse_args()` (line 2278) and `main()` (line 3009) — wiring.

---

## Task 1: The probe

**Files:**
- Modify: `generate-npc.py:1136` (signature), `:1207` (Theme), `:1392` (loop), `:1520` (Stance), `:1558` (Gear correction)
- Test: `test/test_set_trait_value.py` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: `roll_npc(tables, rng, overrides=None, unarmed=False, probe=None)`. When `probe` is a dict, it is filled with `{table_name: [bullet, ...]}` for all of `REQUIRED_TABLES` except `Pronouns`. Bullets are raw, flags included. Every later task reads this.

- [ ] **Step 1: Write the failing test**

Create `test/test_set_trait_value.py`:

```python
"""Pinning one trait of an already-rolled NPC to a chosen value.

The question this file is really about is "which values could this trait
take", and the answer has to come from roll_npc()'s own pool or it is not an
answer at all - a second filter chain written out here would agree with the
roller on the day it was written and drift from it silently afterwards. So
roll_npc() records the pool it already computes, and everything below reads
that recording.

The recording has to be inert, which is the first class here and the one the
rest depends on: a probed roll and an unprobed roll at the same seed are the
same NPC. If that ever stops being true, every legality answer in this file is
being computed against a roll that never happened.
"""
import random
import unittest

from test.helpers import FIXTURE_TABLES, REPO, load_generator

gen = load_generator()

TABLES = gen.parse_tables(FIXTURE_TABLES)
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")


class ProbeIsInert(unittest.TestCase):
    def test_a_probed_roll_is_the_same_npc_as_an_unprobed_one(self):
        for seed in range(25):
            with self.subTest(seed=seed):
                plain = gen.roll_npc(LIVE, random.Random(seed), None)
                probed = gen.roll_npc(LIVE, random.Random(seed), None, probe={})
                self.assertEqual(plain, probed)

    def test_the_probe_is_untouched_when_none_is_passed(self):
        # The default has to stay None rather than {}, or every caller shares
        # one dict and the pools accumulate across rolls.
        self.assertIsNone(
            gen.roll_npc.__defaults__[-1],
            "roll_npc's probe default must be None, not a shared dict")


class ProbeCoversTheTables(unittest.TestCase):
    def test_every_required_table_but_pronouns_is_recorded(self):
        probe = {}
        gen.roll_npc(LIVE, random.Random(3), None, probe=probe)
        missing = [t for t in gen.REQUIRED_TABLES
                   if t != "Pronouns" and t not in probe]
        self.assertEqual(missing, [], "unrecorded tables have no legal values")

    def test_every_recorded_pool_is_non_empty(self):
        probe = {}
        gen.roll_npc(LIVE, random.Random(4), None, probe=probe)
        empty = sorted(t for t, pool in probe.items() if not pool)
        self.assertEqual(empty, [])

    def test_the_rolled_value_is_in_its_own_recorded_pool(self):
        # The pool is what the draw came from, so this is the tightest
        # statement that the record is of the right list.
        for seed in range(10):
            probe = {}
            npc = gen.roll_npc(LIVE, random.Random(seed), None, probe=probe)
            for table, pool in probe.items():
                with self.subTest(seed=seed, table=table):
                    self.assertIn(npc["_raw"][table], pool)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and watch it fail**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: FAIL — `roll_npc() got an unexpected keyword argument 'probe'`.

- [ ] **Step 3: Add the parameter**

`generate-npc.py:1136` — change the signature:

```python
def roll_npc(tables, rng, overrides=None, unarmed=False, probe=None):
```

Add to that function's docstring, after the existing text:

```
    `probe`, when a dict is passed, is filled with the fully-filtered pool
    this function computed for each table, keyed by table name. It is a
    read-out of work already being done rather than a second computation:
    every filter below narrows `options` and the draw comes off the end of
    it, so the list recorded here is by construction the set of bullets this
    table could have produced given the traits above it. That is the whole
    reason the query in trait_choices() can promise not to drift - there is
    nothing to drift from.

    Recording consumes no randomness and changes no value, so a probed roll
    and an unprobed roll at the same seed are the same NPC. test_set_trait_
    value.ProbeIsInert holds that, and every legality answer depends on it.

    Pronouns is the one table with no entry: it is drawn before the loop from
    an unfiltered list and is refused by both re-roll paths anyway, so there
    is no question to answer about it.
```

- [ ] **Step 4: Record the four pools**

`generate-npc.py:1207` — after the Theme draw:

```python
    theme = (overrides or {}).get("Theme") or rng.choice(tables["Theme"])
    # No filter runs on Theme - it is the thing the others are filtered by -
    # so its pool is the whole table. Recorded anyway, so a caller asking
    # "what could Theme be" gets a list rather than a KeyError, and so the
    # probe's coverage test can name every table uniformly.
    if probe is not None:
        probe["Theme"] = list(tables["Theme"])
```

`generate-npc.py:1392` — immediately before the draw:

```python
        # After the last filter and before the draw: this is the only line in
        # the function where `options` is exactly what the roller is about to
        # choose from.
        if probe is not None:
            probe[name] = list(options)
        value = rng.choice(options)
```

`generate-npc.py:1520` — immediately before the Stance draw:

```python
        # `stances` is (bullet, flags) pairs so the raw line survives the
        # filters; the probe wants the bullets, to match every other entry.
        if probe is not None:
            probe["Stance"] = [x[0] for x in stances]
        raw["Stance"] = npc["Stance"] = rng.choice(stances)[0]
```

`generate-npc.py:1558` — inside the `if free:` of the nogear correction, before the draw:

```python
        if free:
            # Replaces the loop's own Gear entry on purpose. A 'nogear'
            # backdrop has already filled the subject's hands, so THIS is the
            # pool the NPC's Gear actually comes from, and the loop's wider
            # one is a list the roller has just finished overruling. Recording
            # the wider one would tell a caller that a 'hands' Gear is fine
            # under a scene that is about to take it away - which is the
            # clash a pinned Gear survives today (23 in 400, per the
            # Backdrop -> Gear note in TRAIT_DEPENDENTS), reported as if it
            # were not there.
            if probe is not None:
                probe["Gear"] = list(free)
            raw["Gear"] = rng.choice(free)
```

- [ ] **Step 5: Run the new tests**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: PASS, 5 tests.

- [ ] **Step 6: Run the whole suite**

Run: `python -m unittest discover test`
Expected: PASS, no regressions. The probe is additive and defaults to `None`.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py test/test_set_trait_value.py
git commit -m "feat: let roll_npc read out the pool it filtered for each table"
```

---

## Task 2: `trait_choices()` — the legality answer

**Files:**
- Modify: `generate-npc.py` — add `trait_choices()` immediately after `reroll_trait()` (ends ~line 2792)
- Test: `test/test_set_trait_value.py`

**Interfaces:**
- Consumes: `roll_npc(..., probe=)` from Task 1.
- Produces: `trait_choices(tables, npc, name) -> list[dict]`, each dict `{"value": str, "heading": str, "allowed": bool, "current": bool, "conflicts": list[str], "releases": list[str]}`, in table order. `npc` must carry `_raw` and `_pronouns`. Tasks 4 and 5 consume it.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_set_trait_value.py`:

```python
def raw_npc(tables=LIVE, seed=0):
    """A freshly rolled NPC, which by construction has its raw bullets."""
    return gen.roll_npc(tables, random.Random(seed), None)


class ChoicesDescribeTheCurrentNpc(unittest.TestCase):
    def test_the_value_the_npc_is_wearing_is_always_allowed(self):
        # The tightest invariant in the file. Whatever it has on was legal
        # when it was rolled and nothing has changed since, so a pin that
        # reports it as ruled out is reporting on the wrong NPC.
        for seed in range(8):
            npc = raw_npc(seed=seed)
            for trait in gen.RAW_REROLLABLE_TRAITS:
                with self.subTest(seed=seed, trait=trait):
                    choices = gen.trait_choices(LIVE, npc, trait)
                    current = [c for c in choices if c["current"]]
                    self.assertEqual(len(current), 1, "exactly one current value")
                    self.assertTrue(current[0]["allowed"])
                    self.assertEqual(current[0]["conflicts"], [])

    def test_current_marks_the_stored_raw_bullet(self):
        npc = raw_npc(seed=1)
        choices = gen.trait_choices(LIVE, npc, "Outfit")
        current = next(c for c in choices if c["current"])
        self.assertEqual(current["value"], npc["_raw"]["Outfit"])

    def test_every_bullet_in_the_table_is_offered(self):
        npc = raw_npc(seed=2)
        subject = npc["Pronouns"].split("/")[0].strip().lower()
        expected = gen.variant_table(LIVE, "Outfit", subject)
        got = [c["value"] for c in gen.trait_choices(LIVE, npc, "Outfit")]
        self.assertEqual(got, list(expected))

    def test_nothing_is_dropped_for_being_illegal(self):
        # The picker greys ruled-out values rather than hiding them, so this
        # function must report them rather than filter them.
        npc = raw_npc(seed=3)
        choices = gen.trait_choices(LIVE, npc, "Headgear")
        self.assertTrue(any(not c["allowed"] for c in choices),
                        "live Headgear has bullets some NPC cannot wear")


class ConflictsNameTheTraitThatWouldBreak(unittest.TestCase):
    def test_a_backdrop_that_forbids_gear_conflicts_with_a_hands_gear(self):
        # The correction the probe exists to expose: roll_npc() re-rolls a
        # 'hands' Gear under a 'nogear' scene, but a PINNED Gear is pasted
        # back over that correction, so the clash survives into the render.
        npc = next(n for n in (raw_npc(seed=s) for s in range(60))
                   if "hands" in gen.split_flags(n["_raw"]["Gear"])[1])
        choices = gen.trait_choices(LIVE, npc, "Backdrop")
        nogear = [c for c in choices
                  if "nogear" in gen.split_backdrop(c["value"])[2]]
        self.assertTrue(nogear, "the live tables have 'nogear' backdrops")
        for c in nogear:
            with self.subTest(value=c["value"][:40]):
                self.assertIn("Gear", c["conflicts"])

    def test_backdrop_never_reports_a_weather_conflict(self):
        # Backdrop -> Weather is a freshness edge, not a filter one: nothing
        # narrows the Weather pool, so a kept Weather is never illegal, only
        # newly hidden or newly shown.
        for seed in range(6):
            npc = raw_npc(seed=seed)
            for c in gen.trait_choices(LIVE, npc, "Backdrop"):
                with self.subTest(seed=seed):
                    self.assertNotIn("Weather", c["conflicts"])

    def test_a_trait_with_no_dependents_reports_no_conflicts(self):
        npc = raw_npc(seed=4)
        for trait in ("Faction", "Glow colour", "Demeanor"):
            with self.subTest(trait=trait):
                self.assertTrue(
                    all(c["conflicts"] == []
                        for c in gen.trait_choices(LIVE, npc, trait)))

    def test_conflicts_only_ever_name_direct_dependents(self):
        npc = raw_npc(seed=5)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            allowed = set(gen.TRAIT_DEPENDENTS.get(trait, ()))
            for c in gen.trait_choices(LIVE, npc, trait):
                with self.subTest(trait=trait):
                    self.assertTrue(set(c["conflicts"]) <= allowed)


class ReleasesIsTheCascadeClosure(unittest.TestCase):
    def test_releases_covers_every_conflict(self):
        npc = raw_npc(seed=6)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                with self.subTest(trait=trait):
                    self.assertTrue(set(c["conflicts"]) <= set(c["releases"]))

    def test_releases_is_the_closure_of_the_conflicts(self):
        # Freeing a conflicting trait re-rolls it, and anything gated by it
        # then has to move too - otherwise the contradiction reappears one
        # level down, which is the whole reason the flag expands.
        npc = raw_npc(seed=7)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                expected = set()
                for d in c["conflicts"]:
                    expected |= set(gen.trait_cascade(d))
                expected -= {trait}
                with self.subTest(trait=trait, value=c["value"][:30]):
                    self.assertEqual(set(c["releases"]), expected)

    def test_releases_is_empty_when_conflicts_is(self):
        npc = raw_npc(seed=8)
        for trait in gen.RAW_REROLLABLE_TRAITS:
            for c in gen.trait_choices(LIVE, npc, trait):
                if not c["conflicts"]:
                    with self.subTest(trait=trait):
                        self.assertEqual(c["releases"], [])
```

- [ ] **Step 2: Run them and watch them fail**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: FAIL — `module 'gennpc' has no attribute 'trait_choices'`.

- [ ] **Step 3: Implement `trait_choices()`**

Insert immediately after `reroll_trait()` in `generate-npc.py`:

```python
def trait_choices(tables, npc, name):
    """Which bullets `name` could take on this NPC, and what each would cost.

    Two questions per bullet, and they run in opposite directions.

    Upstream: could the roller have produced this bullet for this table, given
    the traits above it? That is `probe[name]` from a roll with the whole NPC
    pinned - the pool roll_npc() filtered, read back rather than recomputed.
    One roll answers it for the entire table at once, because a table's pool
    is built from the traits ABOVE it and those are pinned to this NPC's own
    bullets regardless of which candidate we are asking about.

    Downstream: if this bullet replaced the current one, would any trait BELOW
    it be left holding a value the roller would no longer offer? Pinning
    filters one way only - a pinned trait is never re-drawn, so nothing
    re-checks it against a gate that has just changed - which is exactly the
    contradiction class reroll_from_raw()'s cascade exists to prevent. Here
    the cascade is not run, because keeping the dependents is the point, so
    the contradiction is reported instead of avoided.

    The downstream pass runs over every edge in TRAIT_DEPENDENTS bar Weather,
    including the pairs roll_npc() already filters both ways (Headgear/Gear,
    Age/Build). For those it is redundant and simply agrees with the upstream
    pool. Redundant beats an exception list that has to be re-derived every
    time an edge is added: a stale exception reports a conflict that is not
    real, but a missed edge hides one that is.

    Weather is exempt because its edge is not a filter. Nothing narrows the
    Weather pool - the Backdrop's 'weather' flag is read at prompt-build time
    by weather_sentence() and decides only whether the rolled Weather is
    RENDERED. A kept Weather is therefore never illegal, only newly hidden or
    newly shown, and checking it would report every Backdrop in the table as
    conflicting.

    Nothing is dropped. Both answers ride on the entry and the caller decides:
    the picker this feeds greys ruled-out values and still lets them be
    chosen, which mirrors --set-trait's own long-standing behaviour of
    bypassing the roll pool. This function describes the pool; it does not
    enforce it.

    The rng is fixed rather than passed in. Every roll here is fully pinned,
    so nothing is actually drawn and the seed cannot reach the result - but a
    caller handing in a live rng would have its stream silently consumed by a
    query, which is a bug that would only ever show up as an unrelated NPC
    changing.
    """
    subject = npc["Pronouns"].split("/")[0].strip().lower()
    raw = dict(npc["_raw"])

    baseline = {}
    roll_npc(tables, random.Random(0), raw, probe=baseline)
    pool = set(baseline.get(name, ()))

    dependents = [d for d in TRAIT_DEPENDENTS.get(name, ()) if d != "Weather"]

    out = []
    for bullet in variant_table(tables, name, subject):
        current = bullet == raw.get(name)
        # The value it already has cannot contradict what it is already
        # wearing, and skipping it here is not an optimisation - running the
        # check would compare the NPC against itself and could only ever
        # report a conflict that predates this feature.
        if dependents and not current:
            after = {}
            roll_npc(tables, random.Random(0), dict(raw, **{name: bullet}),
                     probe=after)
            conflicts = [d for d in dependents
                         if d in raw and raw[d] not in after.get(d, ())]
        else:
            conflicts = []

        # What --release <conflicts> would actually free. Reported rather than
        # left to the caller to derive, so the picker can name what moves
        # without a copy of trait_cascade() in JavaScript.
        releases = set()
        for d in conflicts:
            releases |= set(trait_cascade(d))
        releases -= {name}

        out.append({
            "value": bullet,
            "heading": heading_for(tables, name, subject, bullet),
            "allowed": bullet in pool,
            "current": current,
            "conflicts": conflicts,
            "releases": sorted(releases),
        })
    return out
```

- [ ] **Step 4: Run the tests**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: PASS.

If `test_a_backdrop_that_forbids_gear_conflicts_with_a_hands_gear` cannot find an NPC in 60 seeds, widen the range rather than weakening the assertion — a 'hands' Gear is common on the live tables.

- [ ] **Step 5: Run the whole suite**

Run: `python -m unittest discover test`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add generate-npc.py test/test_set_trait_value.py
git commit -m "feat: answer which values a trait could take on one NPC"
```

---

## Task 3: Extract `npc_from_entry()`

A pure refactor with no behaviour change, so that Task 4's query and `regenerate_one()` rebuild the NPC dict the same way instead of two ways that drift.

**Files:**
- Modify: `generate-npc.py:2794-2847` — lift the entry→npc reconstruction out of `regenerate_one()`

**Interfaces:**
- Consumes: nothing new.
- Produces: `find_regen_entry(manifest, regen_id) -> (folder_path, entry)` and `npc_from_entry(entry, regen_id, warn=True) -> dict`. Tasks 4 and 5 consume both.

- [ ] **Step 1: Extract, without changing behaviour**

Insert immediately before `regenerate_one()`:

```python
def find_regen_entry(manifest, regen_id):
    """The (folder path, entry) pair for one id, or a refusal naming it."""
    folder_path, entry = next(
        ((k, v) for k, v in manifest.items()
         if isinstance(v, dict) and v.get("id") == regen_id),
        (None, None),
    )
    if entry is None:
        raise SystemExit("--regen-id %r: no such entry" % regen_id)
    return folder_path, entry


def npc_from_entry(entry, regen_id, warn=True):
    """A manifest entry rebuilt into the dict roll_npc() would have produced.

    Lifted out of regenerate_one() so that --trait-choices reads an entry the
    same way a regen does. Two reconstructions would drift, and the direction
    they would drift in is the worst one available: a query answering about a
    slightly different NPC than the one the regen is about to render.

    `warn` is off for the query, which is a read-only question asked possibly
    many times by a GUI - the migration notices belong on the run that
    actually writes something, and printing them to stdout would corrupt the
    JSON besides.
    """
    npc = migrate_traits(entry["traits"])
    npc["_pronouns"] = pronoun_fields(npc["Pronouns"])
    if warn and "young" not in entry:
        print("! %s has no recorded 'young' flag (written by an older version "
              "of this script) - assuming not young; the maturity/face wording "
              "may drift slightly from the original render." % regen_id,
              file=sys.stderr)
    npc["_young"] = entry.get("young", False)
    npc["_outfit_notac"] = entry.get("outfit_notac")
    npc["_gear_helmet"] = entry.get("gear_helmet")
    if entry.get("rawTraits"):
        npc["_raw"] = rename_legacy_traits(entry["rawTraits"])
    if "Height" not in npc:
        if warn:
            print("! %s has no recorded Height trait (written before the "
                  "Height table existed) - regenerating without one; re-roll "
                  "instead of regenerating to pick one up." % regen_id,
                  file=sys.stderr)
        npc["Height"] = "of average height"
    return npc
```

Then replace the corresponding block inside `regenerate_one()` with:

```python
    manifest = art.load_manifest(args.regen_manifest)
    folder_path, entry = find_regen_entry(manifest, args.regen_id)
    npc = npc_from_entry(entry, args.regen_id)
```

**Careful:** the original `--regen-id` refusal names the manifest path (`"no such entry in %s"`). `find_regen_entry` does not have it. Keep the message identical by passing it, or by catching and re-raising in `regenerate_one`. Preserve the existing wording exactly — a test may assert on it.

Preserve every comment from the original block; they explain why `_outfit_notac` and `_gear_helmet` have no default, and losing them loses the reason.

- [ ] **Step 2: Run the whole suite**

Run: `python -m unittest discover test`
Expected: PASS, unchanged count. A refactor that changes a test is not a refactor.

- [ ] **Step 3: Commit**

```bash
git add generate-npc.py
git commit -m "refactor: read a manifest entry back into an npc in one place"
```

---

## Task 4: `--trait-choices`

**Files:**
- Modify: `generate-npc.py` — `parse_args()` (~2236 for the regen group, ~2278 for validation), `main()` (~3012), plus a new `print_trait_choices()`
- Test: `test/test_set_trait_value.py`

**Interfaces:**
- Consumes: `trait_choices()` (Task 2), `find_regen_entry()` / `npc_from_entry()` (Task 3).
- Produces: CLI `--trait-choices TABLE`, printing one JSON object to stdout: `{"trait", "current", "dependents", "choices"}`. Task 5 shares its refusals. The GUI plan's `lib/traitChoices.js` parses exactly this.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_set_trait_value.py` (add `import io`, `import json`, `import contextlib`, `import tempfile`, `from pathlib import Path` to the imports):

```python
def manifest_with(npc, seed=0, path=None, drop_raw=False):
    """A one-entry manifest file on disk, as regenerate_one() reads it."""
    entry = {
        "id": "npc-test-%d" % seed,
        "kind": "npc",
        "name": npc["name"],
        "seed": seed,
        "traits": {k: v for k, v in npc.items() if not k.startswith("_")},
        "young": npc["_young"],
        "outfit_notac": npc["_outfit_notac"],
        "gear_helmet": npc["_gear_helmet"],
        "rawTraits": {} if drop_raw else npc["_raw"],
    }
    path.write_text(json.dumps({"npcs/test": entry}), encoding="utf-8")
    return path


class TraitChoicesCommand(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = raw_npc(seed=0)
        self.manifest = manifest_with(
            self.npc, path=Path(self.dir.name) / "m.json")

    def run_cli(self, *extra):
        # --tables explicitly: the NPC in the manifest was rolled from LIVE,
        # so the query has to read the same file, and leaning on the default
        # would make this test depend on the working directory.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            gen.main(["--regen-manifest", str(self.manifest),
                      "--regen-id", "npc-test-0",
                      "--tables", str(REPO / "prompts" / "npc-generator-tables.md"),
                      *extra])
        return json.loads(out.getvalue())

    def test_it_prints_json_and_renders_nothing(self):
        got = self.run_cli("--trait-choices", "Outfit")
        self.assertEqual(got["trait"], "Outfit")
        self.assertEqual(got["current"], self.npc["_raw"]["Outfit"])
        self.assertEqual(got["dependents"], ["Headgear", "Weapon", "Gear"])
        self.assertTrue(got["choices"])

    def test_every_choice_carries_the_documented_keys(self):
        got = self.run_cli("--trait-choices", "Outfit")
        for c in got["choices"]:
            self.assertEqual(
                sorted(c),
                ["allowed", "conflicts", "current", "heading", "releases", "value"])

    def test_stdout_is_json_and_nothing_else(self):
        # The GUI parses stdout whole, so one stray banner line breaks it -
        # the same constraint --trait-odds already documents.
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            gen.main(["--regen-manifest", str(self.manifest),
                      "--regen-id", "npc-test-0", "--trait-choices", "Hair"])
        json.loads(out.getvalue())  # raises if anything else was printed

    def test_an_unrerollable_trait_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--trait-choices", "Pronouns")
        self.assertIn("Pronouns", str(caught.exception))

    def test_an_entry_without_raw_bullets_is_refused(self):
        manifest = manifest_with(
            self.npc, path=Path(self.dir.name) / "legacy.json", drop_raw=True)
        with self.assertRaises(SystemExit) as caught:
            gen.main(["--regen-manifest", str(manifest),
                      "--regen-id", "npc-test-0", "--trait-choices", "Outfit"])
        self.assertIn("re-roll", str(caught.exception).lower())

    def test_it_refuses_to_run_alongside_a_reroll(self):
        with self.assertRaises(SystemExit):
            self.run_cli("--trait-choices", "Hair", "--reroll-trait", "Hair")
```

- [ ] **Step 2: Run and watch them fail**

Run: `python -m unittest test.test_set_trait_value.TraitChoicesCommand -v`
Expected: FAIL — `unrecognized arguments: --trait-choices`.

- [ ] **Step 3: Add the argument**

In `parse_args()`, in the `regen` group next to `--reroll-trait` (~line 2236):

```python
    regen.add_argument("--trait-choices", metavar="TABLE",
                       help="print, as JSON on stdout, which values TABLE "
                            "could take on this NPC given its other traits - "
                            "each with whether the roller would have offered "
                            "it and which kept traits it would contradict. "
                            "Renders nothing and contacts no server. "
                            "Requires --regen-id; needs the entry's raw "
                            "bullets.")
```

In the `--regen-manifest` validation block (~2278), after the existing `conflicting` check:

```python
    if args.trait_choices:
        if not args.regen_manifest:
            p.error("--trait-choices needs --regen-manifest and --regen-id")
        if args.reroll_trait:
            p.error("--trait-choices only reports; drop --reroll-trait")
```

Note `--set-trait` is still in the `conflicting` list at this point; Task 5 removes it and must then also refuse `--trait-choices` with `--set-trait`.

- [ ] **Step 4: Add the printer and wire `main()`**

Insert after `trait_choices()`:

```python
def print_trait_choices(args):
    """--trait-choices: which values one trait could take, as JSON.

    Prints to stdout and nothing else, because the caller parses stdout whole
    - the same contract --trait-odds already keeps, and the reason
    npc_from_entry() is asked not to warn here. Every diagnostic that does
    escape goes to stderr.
    """
    manifest = art.load_manifest(args.regen_manifest)
    _, entry = find_regen_entry(manifest, args.regen_id)
    npc = npc_from_entry(entry, args.regen_id, warn=False)

    # The same refusal reroll_trait() gives, from the same two lists, so a
    # trait the GUI is told it cannot choose is a trait it is also told it
    # cannot re-roll. Offering one without the other would be worse than
    # offering neither.
    raw = npc.get("_raw")
    rerollable = RAW_REROLLABLE_TRAITS if raw else REROLLABLE_TRAITS
    if not raw:
        raise SystemExit(
            "--trait-choices %s: this entry recorded no raw bullets, so there "
            "is nothing to pin the rest of the NPC to. Re-roll the NPC to "
            "record them." % args.trait_choices)
    if args.trait_choices not in rerollable:
        reason = UNREROLLABLE_REASONS.get(
            args.trait_choices, "it is not a trait this script rolls")
        raise SystemExit(
            "--trait-choices %s: cannot choose that one, because %s.\n"
            "Choosable: %s"
            % (args.trait_choices, reason, ", ".join(rerollable)))

    if not args.tables.exists():
        raise SystemExit("--trait-choices needs the tables file: %s" % args.tables)
    tables = parse_tables(args.tables)
    check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))

    json.dump({
        "trait": args.trait_choices,
        "current": npc["_raw"].get(args.trait_choices),
        "dependents": list(TRAIT_DEPENDENTS.get(args.trait_choices, ())),
        "choices": trait_choices(tables, npc, args.trait_choices),
    }, sys.stdout)
    return 0
```

In `main()`, immediately before `if args.regen_manifest: return regenerate_one(args)` (~3012):

```python
    # Before regenerate_one(), which renders. This mode only reports.
    if args.trait_choices:
        return print_trait_choices(args)
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `python -m unittest discover test`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py test/test_set_trait_value.py
git commit -m "feat: --trait-choices reports what one trait could be"
```

---

## Task 5: `--set-trait` on a regen, and `--release`

**Files:**
- Modify: `generate-npc.py` — `parse_args()` (~2279 conflict list, plus `--release`), `regenerate_one()` (~2853, beside the `--reroll-trait` branch)
- Test: `test/test_set_trait_value.py`

**Interfaces:**
- Consumes: `reroll_from_raw()` (existing), `trait_cascade()` (existing), Task 3's helpers.
- Produces: CLI `--set-trait Table=value` valid with `--regen-manifest`, and `--release A,B`. The GUI plan's `startRegenJob` emits exactly these.

- [ ] **Step 1: Write the failing tests**

Append to `test/test_set_trait_value.py`:

```python
class SetTraitOnARegen(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.npc = raw_npc(seed=0)
        self.manifest = manifest_with(
            self.npc, path=Path(self.dir.name) / "m.json")

    def pinned(self, table, value, release=None):
        """regenerate_one()'s roll half, without the render half."""
        npc = gen.npc_from_entry(
            json.loads(self.manifest.read_text())["npcs/test"],
            "npc-test-0", warn=False)
        free = set()
        for name in (release or ()):
            free |= set(gen.trait_cascade(name))
        gen.reroll_from_raw(LIVE, npc, free, random.Random(1),
                            {table: value})
        return npc

    def other_value_for(self, trait):
        choices = gen.trait_choices(LIVE, self.npc, trait)
        return next(c for c in choices
                    if c["allowed"] and not c["current"] and not c["conflicts"])

    def test_only_the_named_trait_moves(self):
        pick = self.other_value_for("Demeanor")
        after = self.pinned("Demeanor", pick["value"])
        moved = [t for t in gen.REQUIRED_TABLES
                 if self.npc["_raw"].get(t) != after["_raw"].get(t)]
        self.assertEqual(moved, ["Demeanor"])

    def test_the_named_trait_actually_takes_the_value(self):
        pick = self.other_value_for("Demeanor")
        after = self.pinned("Demeanor", pick["value"])
        self.assertEqual(after["_raw"]["Demeanor"], pick["value"])

    def test_raw_and_rendered_traits_agree_afterwards(self):
        # The one risk both specs single out: rawTraits describing bullets the
        # NPC no longer carries.
        pick = self.other_value_for("Outfit")
        after = self.pinned("Outfit", pick["value"])
        for trait in gen.REQUIRED_TABLES:
            if trait in ("Hair", "Hair colour", "Backdrop", "Faction"):
                continue  # these are re-split downstream; see roll_npc()
            with self.subTest(trait=trait):
                self.assertEqual(
                    gen.split_flags(after["_raw"][trait])[0], after[trait])

    def test_releasing_a_trait_frees_its_whole_cascade(self):
        # Freeing Outfit alone would redraw it while Headgear, Weapon and Gear
        # stayed pinned to bullets chosen for the outfit that is now gone.
        pick = next(c for c in gen.trait_choices(LIVE, self.npc, "Theme")
                    if c["conflicts"])
        after = self.pinned("Theme", pick["value"], release=pick["conflicts"])
        for trait in pick["releases"]:
            self.assertIn(trait, gen.REQUIRED_TABLES)
        untouched = [t for t in gen.REQUIRED_TABLES
                     if t not in pick["releases"] and t != "Theme"]
        for trait in untouched:
            with self.subTest(trait=trait):
                self.assertEqual(self.npc["_raw"].get(trait),
                                 after["_raw"].get(trait))


class SetTraitArgumentRules(unittest.TestCase):
    def parse(self, *argv):
        return gen.parse_args(list(argv))

    def test_set_trait_is_allowed_with_regen(self):
        args = self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                          "--set-trait", "Hair=a bob")
        self.assertEqual(args.overrides, {"Hair": "a bob"})

    def test_set_trait_and_reroll_trait_together_are_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--set-trait", "Hair=a bob", "--reroll-trait", "Hair")

    def test_release_without_set_trait_is_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--release", "Headgear")

    def test_release_of_a_non_dependent_is_refused(self):
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--set-trait", "Demeanor=a scowl",
                       "--release", "Backdrop")

    def test_release_of_a_real_dependent_is_accepted(self):
        args = self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                          "--set-trait", "Outfit=a kimono",
                          "--release", "Headgear,Gear")
        self.assertEqual(args.release, ["Headgear", "Gear"])

    def test_count_and_name_are_still_refused_with_regen(self):
        # --set-trait leaving the conflict list must not take the rest with it.
        with self.assertRaises(SystemExit):
            self.parse("--regen-manifest", "m.json", "--regen-id", "x",
                       "--name", "Someone")
```

- [ ] **Step 2: Run and watch them fail**

Run: `python -m unittest test.test_set_trait_value.SetTraitArgumentRules -v`
Expected: FAIL — the parser still refuses `--set-trait` with `--regen-manifest`.

- [ ] **Step 3: Loosen the parser and add `--release`**

In `parse_args()`, remove the `--set-trait` line from the `conflicting` list (~2283), leaving `--count`, `--seed`, `--name`, `--pronouns` and `--unarmed`. Add above it a comment:

```python
        # --set-trait is deliberately NOT here any more. "Replaces the roll
        # entirely" is still true of every other flag in this list, but a
        # pinned regen is exactly the case where naming one trait's value and
        # reproducing the rest is the request rather than a contradiction -
        # see reroll_from_raw()'s `pinned`, which has existed for it since
        # Theme's cascade.
```

Add the flag to the `regen` group:

```python
    regen.add_argument("--release", metavar="A,B",
                       help="with --set-trait, traits to re-roll instead of "
                            "keeping - use for the ones --trait-choices "
                            "reports as conflicting. Each name expands to its "
                            "whole cascade, so releasing Outfit also re-rolls "
                            "the Headgear, Weapon and Gear it gates.")
```

And validate, after the `--trait-choices` block from Task 4:

```python
    if args.reroll_trait and args.overrides:
        p.error("--reroll-trait draws a new value and --set-trait names one; "
                "use one")
    if args.trait_choices and args.overrides:
        p.error("--trait-choices only reports; drop --set-trait")

    args.release = [n.strip() for n in (args.release or "").split(",") if n.strip()]
    if args.release:
        if not args.overrides:
            p.error("--release only makes sense with --set-trait")
        allowed = set()
        for table in args.overrides:
            allowed |= set(TRAIT_DEPENDENTS.get(table, ()))
        stray = [n for n in args.release if n not in allowed]
        if stray:
            p.error(
                "--release %s: not gated by %s. Releasing a trait the set one "
                "does not gate is a re-roll wearing a disguise; --reroll-trait "
                "is the flag for that. Releasable here: %s"
                % (", ".join(stray), ", ".join(args.overrides),
                   ", ".join(sorted(allowed)) or "nothing"))
```

**Careful:** `args.overrides` is built later in `parse_args` (~2301). Move these checks below that point, or they will read an attribute that does not exist yet. Verify by running the argument tests.

- [ ] **Step 4: Add the regen branch**

In `regenerate_one()`, immediately after the `if args.reroll_trait:` block (~ends line 2886):

```python
    # One trait pinned to a chosen value, everything else reproduced - the
    # mirror of the block above, which draws instead of choosing.
    if args.overrides:
        if not args.tables.exists():
            raise SystemExit("--set-trait needs the tables file: %s" % args.tables)
        tables = parse_tables(args.tables)
        check_tables(tables, args.tables, getattr(parse_tables, "repeated", ()))
        if not npc.get("_raw"):
            raise SystemExit(
                "--set-trait on a regen needs the entry's raw bullets, so the "
                "rest of the NPC has something to be pinned to. Re-roll the "
                "NPC to record them.")

        # free=set() pins every stored bullet; `pinned` swaps the named ones.
        # Re-running roll_npc() rather than poking npc[table] directly is the
        # point: _young, _outfit_notac, _gear_helmet, the '{colour}' fill and
        # the flag stripping all recompute, and _raw ends up describing the
        # NPC being rendered rather than the one it replaced.
        free = set()
        for name in args.release:
            free |= set(trait_cascade(name))
        before = {k: v for k, v in npc.items() if not k.startswith("_")}
        reroll_from_raw(
            tables, npc, free,
            random.Random(args.new_seed if args.new_seed is not None else entry["seed"]),
            dict(args.overrides))
        for table in args.overrides:
            print("set %s: %r -> %r" % (table, before.get(table), npc.get(table)))
        # Named rather than summarised, for the same reason the re-roll
        # cascade above names its own: a release reaches further than the
        # trait the user typed, and finding that out from the render is the
        # failure this report exists to prevent.
        for trait in sorted(free):
            if trait not in args.overrides:
                print("  with %s: %r -> %r"
                      % (trait, before.get(trait), npc.get(trait)))
```

- [ ] **Step 5: Run the tests**

Run: `python -m unittest test.test_set_trait_value -v`
Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `python -m unittest discover test`
Expected: PASS. Pay attention to `test_reroll_trait.py` and any test asserting on `parse_args` refusals — the conflict-list change is the one edit here that can break an existing expectation.

- [ ] **Step 7: Commit**

```bash
git add generate-npc.py test/test_set_trait_value.py
git commit -m "feat: pin one trait to a chosen value and re-render from it"
```

---

## Task 6: Documentation

**Files:**
- Modify: `README.md` (test count), `docs/generate-npc.md` (the two flags), `generate-npc.py:43-48` (the usage epilog)

- [ ] **Step 1: Count the tests**

Run: `python -m unittest discover test 2>&1 | tail -3`
Note the new total.

- [ ] **Step 2: Update `README.md`**

Replace the stated test count with the number just measured. Do not guess it.

- [ ] **Step 3: Add the epilog examples**

In `generate-npc.py`'s usage epilog (~line 43-48), beside the existing `--regen-manifest` examples:

```
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234 \\
      --trait-choices Outfit
  python generate-npc.py --regen-manifest .generated-npcs.json --regen-id npc-Nadia-Okonkwo-1234 \\
      --set-trait Outfit="an elaborate floral kimono ... || civ notac" --release Headgear
```

- [ ] **Step 4: Document both flags in `docs/generate-npc.md`**

Add a section beside the existing `--reroll-trait` documentation covering: what `--trait-choices` prints and that stdout is JSON only; that `allowed` and `conflicts` are different questions; that `--release` expands to the cascade; and that both need raw bullets. Cross-reference the spec.

- [ ] **Step 5: Verify the docs match the code**

Run: `python generate-npc.py --help`
Confirm both flags appear with the help text as written.

- [ ] **Step 6: Commit**

```bash
git add README.md docs/generate-npc.md generate-npc.py
git commit -m "docs: describe choosing a trait's value on a stored NPC"
```

---

## Done when

- `python -m unittest discover test` passes.
- `--trait-choices Outfit` on a real manifest entry prints JSON whose `current` entry is `allowed` with no conflicts.
- `--set-trait` on a regen changes the named trait and nothing else; adding `--release` moves exactly the traits the query listed under `releases`.
- The GUI plan (`lancer-npc-import-gui/docs/superpowers/plans/2026-09-06-set-trait-value-picker.md`) can start.
