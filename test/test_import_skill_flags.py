"""The npc-trait-import skill's flag documentation matches the tables file.

The skill stages candidate bullets for `npc-generator-tables.md` from reference
images, and its own pre-handoff checklist says "Every flag is in §0's table.
Unknown flags fail quietly forever." That makes the skill's flag table
load-bearing rather than decorative: a flag the tables file uses but the skill
does not document is one a staging run cannot look up and its own validation
step will reject.

It drifted for months without anyone noticing, which is the argument for this
file. At the point it was written the skill documented 13 flags and the tables
file used 18 - `dressy` had shipped on Outfit and Faction with the dress
register, `armed` on Stance, `scene` on Glow placement, `none` on Weapon. The
`armed` gap was the damaging one: the Stance shape line read `|| [hands]
[gun]`, so a pose staged from a reference of someone with a blade raised would
have landed untagged, stayed reachable by an NPC who rolled no weapon, and put
a sword in a prompt for someone holding nothing.

Checked in one direction only. A flag the tables use and the skill omits is a
silent failure; a flag the skill documents ahead of the table that will use it
is a reasonable order to work in, and failing on it would just punish writing
the documentation first.

The flags are read through the generator's own flags_for(), not a regex over
the file, so this cannot disagree with the generator about what a flag is -
Backdrop, Hair colour and Faction keep theirs in a third segment and the other
tables in a second. The table list comes from REQUIRED_TABLES for the same
reason: a table added next month is covered here with no edit, and the two
prose sections that parse_tables also returns ('How the script reads this
file', 'Prompt templates') are excluded by construction rather than by name.
"""
import re
import unittest

from test.helpers import REPO, bullets_for, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
SKILL_PATH = REPO / ".claude" / "skills" / "npc-trait-import" / "SKILL.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8") if SKILL_PATH.exists() else ""

# A row of the skill's §0 flag table: '| `notac` | Outfit | ... |'. The
# '@<theme>' row is deliberately not matched - theme tags are excluded below.
DOCUMENTED = set(re.findall(r"^\| `([a-z]+)` \|", SKILL, re.M))

# A per-table shape line: '- **Stance**: `<phrase> || [hands] [armed] [gun]`'.
# Only the tables the skill actually stages have one, which is why coverage is
# asserted per shape line found rather than per table in REQUIRED_TABLES.
SHAPES = {
    table: set(re.findall(r"\[([a-z]+)\]", body))
    for table, body in re.findall(
        r"^- \*\*([A-Za-z ]+)\*\*: (.*)$", SKILL, re.M)
}

# A row of the §3 routing table: '| what you see | **Table** (or ...) | how to
# tag it |'. This is the THIRD place the skill names flags, and until this file
# grew a check for it, the only one with no test - which is exactly the one
# that drifted. It was found claiming Hair took "no flags" a commit after
# `updo` shipped, describing Headgear with no mention of `helmet`, and listing
# "`hands`/`mil` only" for Gear when `helmet` and `admin` both reach it. §0 and
# §4 were correct throughout, because the assertions below covered them.
#
# It is the worst of the three to leave stale: §0 is a lookup table and §4 is a
# shape to copy, but §3 is the column a run reads while *deciding* what to tag,
# so a flag missing here is one that never gets considered at all.
ROUTES = {}
for _line in SKILL.split("\n"):
    if not _line.startswith("| "):
        continue
    _cells = [c.strip() for c in _line.strip().strip("|").split(" | ")]
    if len(_cells) != 3:
        continue
    _m = re.match(r"\*\*([A-Za-z ]+)\*\*", _cells[1])
    if _m:
        ROUTES[_m.group(1).strip()] = set(re.findall(r"`([a-z]+)`", _cells[2]))

# Flags a staging run must never author, so they are documented in the flag
# table but deliberately absent from the shape line. Each needs a reason.
NEVER_STAGED = {
    ("Weapon", "none"): "the single empty bullet, which is how an NPC rolls "
                        "unarmed - it is not a thing a reference image shows",
    ("Headgear", "bare"): "the single bare-headed bullet, marked so the "
                          "'covered' filter can name it. Same reason as "
                          "Weapon/none: an image cannot show an absence",
}


def flags_used():
    """{table: {flag}} over every table the generator actually rolls."""
    used = {}
    for name in gen.REQUIRED_TABLES:
        found = set()
        for bullet in bullets_for(LIVE, name):
            found |= {f for f in gen.flags_for(name, bullet)
                      if not f.startswith("@")}
        if found:
            used[name] = found
    return used


class TestTheSkillIsPresent(unittest.TestCase):
    def test_the_skill_file_is_where_this_test_expects_it(self):
        self.assertTrue(
            SKILL_PATH.exists(),
            "%s is missing. If the skill moved, move this test with it; if it "
            "was deleted, delete this test too." % SKILL_PATH)

    def test_the_flag_table_parsed(self):
        """A reformatted markdown table would make DOCUMENTED empty, and every
        assertion below would then fail with a confusing 'undocumented flag'
        rather than the real cause."""
        self.assertGreaterEqual(
            len(DOCUMENTED), 15,
            "only parsed %d flag rows out of the skill's §0 table - the row "
            "format probably changed; the regex in this file expects "
            "'| `flag` | Tables | Meaning |'" % len(DOCUMENTED))

    def test_the_shape_lines_parsed(self):
        self.assertIn("Stance", SHAPES,
                      "no per-table shape lines found - the '- **Table**: ...' "
                      "format in the skill probably changed")


class TestEveryLiveFlagIsDocumented(unittest.TestCase):
    def test_the_measurement_is_not_vacuous(self):
        """A flags_for() that returned nothing would make this file pass on
        nothing at all."""
        used = flags_used()
        self.assertGreaterEqual(len(used), 10)
        self.assertIn("notac", used.get("Outfit", set()))

    def test_the_flag_table_covers_every_flag_in_use(self):
        for table, flags in sorted(flags_used().items()):
            for flag in sorted(flags):
                self.assertIn(
                    flag, DOCUMENTED,
                    "%r is used on the %s table but is not in the import "
                    "skill's flag table. A staged bullet carrying it would "
                    "fail that skill's own check that every flag is "
                    "documented." % (flag, table))

    def test_each_shape_line_covers_its_own_tables_flags(self):
        """The flag table and the shape lines drift separately, and it is the
        shape line a staging run copies. `armed` was in neither, but the case
        worth guarding is `dressy`, which reached the flag table first."""
        used = flags_used()
        for table, shape_flags in sorted(SHAPES.items()):
            for flag in sorted(used.get(table, set())):
                if (table, flag) in NEVER_STAGED:
                    continue
                self.assertIn(
                    flag, shape_flags,
                    "the import skill's shape line for %s omits %r, which the "
                    "table uses. A bullet staged from that line would be "
                    "silently untagged. If it is deliberately never authored "
                    "from a reference image, add it to NEVER_STAGED with a "
                    "reason." % (table, flag))

    def test_each_routing_row_covers_its_own_tables_flags(self):
        """The third mirror, and the one with the worst record.

        Same exemptions as the shape lines: a flag a run must never author
        does not need to appear in the column telling it what to author.
        """
        used = flags_used()
        for table, route_flags in sorted(ROUTES.items()):
            for flag in sorted(used.get(table, set())):
                if (table, flag) in NEVER_STAGED:
                    continue
                with self.subTest(table=table, flag=flag):
                    self.assertIn(
                        flag, route_flags,
                        "the import skill's §3 routing row for %s does not "
                        "mention %r, which the table uses. That row is what a "
                        "staging run reads while deciding what to tag, so a "
                        "flag missing from it is never considered at all."
                        % (table, flag))

    def test_the_routing_table_parsed(self):
        """A reformatted routing table would make every assertion above pass
        vacuously rather than fail."""
        self.assertGreaterEqual(
            len(ROUTES), 8,
            "only parsed %d routing rows out of the skill's §3 table - the "
            "row format probably changed; this file expects "
            "'| seen | **Table** | how to tag |'" % len(ROUTES))
        self.assertIn("Hair", ROUTES)

    def test_every_never_staged_flag_is_still_real(self):
        """An exemption for a flag that no longer exists is an exemption that
        will one day excuse the wrong thing."""
        used = flags_used()
        for (table, flag), reason in NEVER_STAGED.items():
            self.assertIn(flag, used.get(table, set()),
                          "NEVER_STAGED exempts %s/%r, which the tables file "
                          "no longer uses - drop the exemption. (%s)"
                          % (table, flag, reason))


if __name__ == "__main__":
    unittest.main()
