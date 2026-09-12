"""The npc-trait-import skill's per-table SHAPE lines match the real tables.

test_import_skill_flags.py holds the skill's three flag mirrors against the
tables file, and it works: it caught 'crown' and 'blade' the moment they
shipped. But it checks flags and only flags, per shape line it FINDS - its own
docstring says coverage is "asserted per shape line found rather than per table
in REQUIRED_TABLES". Two ways the skill can go stale slip straight through it:

  1. A NEW TABLE. Add one to the generator and no shape line mentions it, so
     there is nothing for the flag test to iterate and it passes. A staging run
     then has no format to copy for that table and invents one.
  2. A CHANGED SEGMENT COUNT. A shape line says how many '||' segments a bullet
     has. Backdrop, Hair colour and Faction carry two segments of PROSE and
     keep flags in a third; every other table keeps flags in the second. If a
     table changed shape - or a shape line was simply written wrong - a run
     would stage bullets whose flags land in a segment the generator reads as
     prose, which is the failure mode that reaches the image model as literal
     '|| crown' text in a prompt.

Both are the same class of bug as the flag drift: the skill is documentation
that the generator silently depends on, so it needs a test rather than a habit.

Checked against the generator's own splitters, not a regex over the file, for
the reason the flags test gives - this cannot disagree with the generator about
what a segment is.
"""
import re
import unittest

from test.helpers import REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
SKILL_PATH = REPO / ".claude" / "skills" / "npc-trait-import" / "SKILL.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8") if SKILL_PATH.exists() else ""

# '- **Stance**: `<participial phrase> || [hands] [armed] [gun]`' -> the
# backticked shape. Only the first backticked run on the line is the shape;
# prose after it may quote other things.
SHAPE_LINES = {}
for _table, _body in re.findall(r"^- \*\*([A-Za-z ]+)\*\*: (.*)$", SKILL, re.M):
    _m = re.search(r"`([^`]*)`", _body)
    if _m:
        SHAPE_LINES[_table.strip()] = _m.group(1)


# Tables the skill deliberately does not stage from a reference image, each
# with the reason. A run reads an image of a PERSON, so a table describing
# something else has no shape line and should not grow one.
NOT_STAGED = {
    "Given names": "a name is not a thing a reference image shows",
    "Family names": "as above",
    "Callsigns": "as above",
    "Pronouns": "a closed set the generator ships - the bullets the whole "
                "pronoun system is built on, not content to add to",
    "Height": "a small closed phrase set the roll pairs with Build; a new "
              "one would need a matching Build register rather than a bullet",
    "Age": "a closed set carrying the 'young' flag that gates Build; adding "
           "one is a change to that pairing, not a staged observation",
    "Build": "same pairing from the other side, and 'Build (she)' replaces "
             "rather than extends it - a bullet added blind lands in the "
             "wrong one half the time",
    "Skin": "a closed phrase set, and one an image reads unreliably under "
            "the coloured lighting most references have",
    "Eyes": "as Skin, and shorter still",
    "Role": "an occupation needs a matching ROLE_CATEGORIES entry in "
            "generate-npc.py or it falls to UNCATEGORIZED_ROLE and silently "
            "escapes the dress and weapon policies - see test_role_lock.py",
    "Weather": "a small closed set belonging to Backdrop, not to a subject",
}

# The generator's own three-segment tables. Asserted against split_* below
# rather than trusted, so this list cannot quietly disagree with the code.
THREE_SEGMENT = ("Backdrop", "Hair colour", "Faction")


def segments_in(shape):
    """How many '||'-separated segments a shape line describes."""
    return len([p for p in shape.split("||")])


def live_segments(table):
    """The segment count a shape line for this table should describe.

    Derived from the generator's own reading rather than by counting '||' in
    the file, because a raw count overstates it: a THEME tag also lives in the
    flag segment, so '## Feature', whose bullets carry no behavioural flag at
    all, still shows two segments wherever one is tagged '@cyberpunk'.

    The skill's shape lines deliberately describe behavioural flags only - a
    theme tag is appended on top and is documented in its own section, and
    guarded by test_import_skill_theme.py. So this counts what those lines are
    actually claiming:

        3   Backdrop, Hair colour, Faction - two prose segments, flags third
        2   any other table with a behavioural flag in use
        1   a table with none, whose text reaches the prompt verbatim
    """
    if table in THREE_SEGMENT:
        return 3
    for bullet in bullets_for(LIVE, table):
        if any(not f.startswith("@") for f in gen.flags_for(table, bullet)):
            return 2
    return 1


class TestTheShapeLinesParsed(unittest.TestCase):
    def test_the_skill_file_is_where_this_test_expects_it(self):
        self.assertTrue(
            SKILL_PATH.exists(),
            "%s is missing. If the skill moved, move this test with it; if it "
            "was deleted, delete this test too." % SKILL_PATH)

    def test_the_measurement_is_not_vacuous(self):
        """A changed '- **Table**: `shape`' format would empty SHAPE_LINES and
        make every assertion below pass on nothing."""
        self.assertGreaterEqual(
            len(SHAPE_LINES), 12,
            "only parsed %d shape lines - the '- **Table**: `<shape>`' format "
            "in the skill probably changed" % len(SHAPE_LINES))
        self.assertIn("Hair", SHAPE_LINES)


class TestEveryTableHasAShape(unittest.TestCase):
    """The gap the flags test leaves: a table nothing mentions at all.

    A staging run copies a shape line to write a bullet. A table with no line
    leaves it to invent a format, and the generator will read whatever it
    invents as prose - flags included.
    """

    def test_every_rolled_table_is_either_shaped_or_exempt(self):
        for table in gen.REQUIRED_TABLES:
            if table in NOT_STAGED:
                continue
            with self.subTest(table=table):
                self.assertIn(
                    table, SHAPE_LINES,
                    "the import skill has no shape line for %s. Add one to §4, "
                    "or add the table to NOT_STAGED in this file with the "
                    "reason a run should never author it." % table)

    def test_every_exemption_names_a_real_table(self):
        """A table renamed in the generator must not leave a dangling
        exemption here, silently switching the check off for its replacement."""
        for table in NOT_STAGED:
            with self.subTest(table=table):
                self.assertIn(
                    table, gen.REQUIRED_TABLES,
                    "NOT_STAGED names %r, which the generator no longer "
                    "rolls" % table)

    def test_every_exemption_carries_a_reason(self):
        for table, reason in NOT_STAGED.items():
            with self.subTest(table=table):
                self.assertTrue(reason.strip(), table)

    def test_no_shape_line_names_a_table_that_does_not_exist(self):
        """The other direction. A shape line for a table the generator dropped
        tells a run to stage bullets nothing will ever read."""
        known = set(gen.REQUIRED_TABLES) | {k.partition(" (")[0] for k in gen.group_tables(LIVE)}
        # Variants are legitimate targets and are named in the skill's routing
        # prose ('Headgear (she) +'), so compare on the base name.
        for table in SHAPE_LINES:
            base = table.split(" (")[0]
            with self.subTest(table=table):
                self.assertIn(
                    base, known,
                    "the import skill has a shape line for %r, which is not a "
                    "table the generator rolls" % table)

    def test_a_group_table_takes_the_shape_of_the_table_that_references_it(self):
        """A '## Flight suits' that Outfit enters through '- => Flight suits'
        holds Outfit-shaped bullets, so it needs no shape line of its own and
        must not have one that disagrees."""
        for name in gen.REQUIRED_TABLES:
            for group, reference in gen.references_in(LIVE, name).items():
                with self.subTest(group=group):
                    self.assertNotIn(group, SHAPE_LINES,
                                     "%s is a group of %s and takes its shape line" % (group, name))
                    self.assertTrue(name in SHAPE_LINES or name in NOT_STAGED,
                                    "%s references %s but has no shape line" % (name, group))


class TestTheSegmentCountsAgree(unittest.TestCase):
    """The second gap: a shape line that describes the wrong number of '||'.

    This is the one that reaches a prompt. Flags live in the LAST segment for
    two-segment tables and the THIRD for Backdrop, Hair colour and Faction; a
    bullet staged against a wrong count puts its flags where the generator
    reads prose, and the literal text '|| crown' ships to the image model.
    """

    def test_the_generator_still_has_exactly_three_three_segment_tables(self):
        """THREE_SEGMENT is asserted, not assumed. flags_for() branches on
        exactly these three names, so a fourth added there without a change
        here would leave this suite checking the wrong arity for it."""
        source = (REPO / "generate-npc.py").read_text(encoding="utf-8")
        body = source.split("def flags_for(")[1].split("\ndef ")[0]
        named = set(re.findall(r'name == "([^"]+)"', body))
        self.assertEqual(
            named, set(THREE_SEGMENT),
            "flags_for() now branches on %s - update THREE_SEGMENT here, and "
            "check the import skill's shape lines for those tables" % sorted(named))

    def test_a_three_segment_table_is_shaped_with_three(self):
        for table in THREE_SEGMENT:
            if table not in SHAPE_LINES:
                continue
            with self.subTest(table=table):
                self.assertEqual(
                    segments_in(SHAPE_LINES[table]), 3,
                    "the import skill shapes %s with %d segments, but it "
                    "carries two of prose and keeps flags in a third. A bullet "
                    "staged from that line would put its flags where the "
                    "generator reads prose."
                    % (table, segments_in(SHAPE_LINES[table])))

    def test_every_other_shaped_table_matches_what_its_bullets_carry(self):
        for table, shape in sorted(SHAPE_LINES.items()):
            base = table.split(" (")[0]
            if base in THREE_SEGMENT or base not in gen.REQUIRED_TABLES:
                continue
            with self.subTest(table=table):
                self.assertEqual(
                    segments_in(shape), live_segments(base),
                    "the import skill shapes %s with %d '||' segments but its "
                    "live bullets carry %d"
                    % (table, segments_in(shape), live_segments(base)))


if __name__ == "__main__":
    unittest.main()
