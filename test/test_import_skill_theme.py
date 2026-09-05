"""The npc-trait-import skill's Theme rules match the live Theme table.

The skill stages candidate bullets from reference images, and it may now stage
a `## Theme` entry of its own - a genuinely new visual world that none of the
live themes covers. That is a sharper edge than any other table it writes to,
because a theme name is not prose: it is the literal string every `@` tag is
matched against. A tag naming a theme that does not exist belongs to no theme
and is not untagged either, so the bullet carrying it is excluded from every
roll, silently, forever. The skill's own §0 has said so since the tag landed.

Two directions of drift, both silent, both guarded here:

  - **The skill's example themes go stale.** Its prose names real themes
    throughout - `@neosamurai`, `@cyberpunk`, `@gundam` - to show what a tag
    looks like and where the boundaries fall. Rename or drop one in the tables
    file and every one of those examples teaches a staging run to emit a dead
    tag. This is the same class `test_import_skill_flags.py` exists for, one
    column over.

  - **The threshold drifts between the two places that state it.** §4.8 sets
    the bar for proposing a theme at all and §7 rechecks it before handoff.
    That file already learned this lesson the expensive way: its flag table
    and its per-table shape lines stated overlapping rules, drifted apart, and
    `armed` went missing from the shape line a staging run actually copies.

Checked against the live tables file rather than a fixture, because staleness
is the property under test and a fixture cannot go stale.
"""
import re
import unittest

from test.helpers import REPO, load_generator

gen = load_generator()
LIVE = gen.parse_tables(REPO / "prompts" / "npc-generator-tables.md")
SKILL_PATH = REPO / ".claude" / "skills" / "npc-trait-import" / "SKILL.md"
SKILL = SKILL_PATH.read_text(encoding="utf-8") if SKILL_PATH.exists() else ""

# parse_tables() expands 'x6 gundam' into six entries and strips the weight, so
# the set of its Theme values is exactly the set of theme names.
LIVE_THEMES = set(LIVE["Theme"])

# Every '@name' the skill writes. Deliberately matches the tag syntax rather
# than a list the skill maintains: the point is to catch a name in running
# prose, which is where the stale ones hide.
NAMED_IN_SKILL = set(re.findall(r"@([a-z][a-z0-9]*)", SKILL))

# '@' strings that are not meant to name a live theme. Each needs a reason, and
# each is checked below to still not be one - an exemption that quietly becomes
# real is an exemption that will one day excuse the wrong thing.
NOT_A_THEME = {
    "theme": "the metasyntactic '@theme' / '@<theme>' the skill writes "
             "wherever it means 'any theme name goes here'",
    "kitbash": "§4.8's worked example of a theme that does NOT exist yet. "
               "That section is entirely about naming a world the table has "
               "not got, so its example must not be a real one - if 'kitbash' "
               "is ever authored for real, pick another example rather than "
               "deleting this entry",
}

# The count word for the seven tables a rolled Theme gates, wherever the skill
# says it in prose. Read off the generator so an eighth themed table makes
# every one of those sentences fail rather than one of them.
COUNT_WORDS = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
COUNT_PATTERNS = (
    r"([a-z]+) themed tables",
    r"read on ([a-z]+) tables",
)

# '4 candidates across 2 of the seven themed tables' - §4.8's gate for
# proposing a theme, restated in §7's checklist. Both must say the same thing.
THRESHOLDS = re.findall(
    r"(\d+) candidates across (\d+) of the seven themed tables", SKILL)

# §4.8's parenthesised roll-call of the live themes, the one place the skill
# spells them all out. Everywhere else it sends the reader to §0's one-liner
# instead, which is why only this list needs guarding.
_NAMING = re.search(
    r"matching the form\s+of the live entries \(([^)]*)\)", SKILL)
NAMING_EXAMPLES = set(re.findall(r"`([a-z]+)`", _NAMING.group(1))) if _NAMING \
    else set()


class TestTheSkillIsPresent(unittest.TestCase):
    def test_the_skill_file_is_where_this_test_expects_it(self):
        self.assertTrue(
            SKILL_PATH.exists(),
            "%s is missing. If the skill moved, move this test with it; if it "
            "was deleted, delete this test too." % SKILL_PATH)

    def test_the_live_themes_parsed(self):
        """A Theme table this could not read would make the checks below pass
        on nothing at all."""
        self.assertGreaterEqual(len(LIVE_THEMES), 8)
        self.assertIn("gundam", LIVE_THEMES)

    def test_the_skill_names_themes_at_all(self):
        """Same guard one column over: a skill whose '@' examples this regex
        stopped matching would silence the staleness check entirely."""
        self.assertGreaterEqual(
            len(NAMED_IN_SKILL - set(NOT_A_THEME)), 3,
            "found no real theme names in the skill's prose - the '@name' tag "
            "syntax this file greps for probably changed")


class TestEveryThemeTheSkillNamesIsReal(unittest.TestCase):
    def test_no_stale_theme_name_survives_in_the_skill(self):
        for name in sorted(NAMED_IN_SKILL):
            if name in NOT_A_THEME:
                continue
            self.assertIn(
                name, LIVE_THEMES,
                "the import skill writes '@%s', which the live Theme table "
                "does not have. A staging run copying that example emits a "
                "tag matched literally against nothing: the bullet belongs to "
                "no theme, is not untagged either, and is excluded from every "
                "roll. Update the skill's example, or add the exemption with "
                "a reason if it is deliberately not real." % name)

    def test_every_exemption_is_still_not_a_theme(self):
        for name, reason in sorted(NOT_A_THEME.items()):
            self.assertNotIn(
                name, LIVE_THEMES,
                "NOT_A_THEME exempts '@%s' as %s - but the tables file now has "
                "a theme by that name, so the exemption is excusing a real "
                "tag and would hide a genuinely stale one behind it."
                % (name, reason))


class TestTheNamingRuleTheSkillTeaches(unittest.TestCase):
    def test_every_live_theme_is_one_lowercase_word(self):
        """§4.8 tells a staging run to name a new theme the way the live ones
        are named - one lowercase word, no spaces or hyphens - because the name
        is the literal string after every '@' and flags are matched literally.
        A live theme in any other form makes that instruction a lie, and a
        space in one would split the flag segment besides.
        """
        for name in sorted(LIVE_THEMES):
            self.assertRegex(
                name, r"^[a-z]+$",
                "%r is not one lowercase word. The import skill teaches new "
                "theme names by pointing at this table, so a name in another "
                "form either breaks that instruction or, if it contains a "
                "space, cannot survive the flag segment at all." % name)

    def test_the_naming_roll_call_is_the_live_set(self):
        """§4.8 spells out every live theme once, to show a staging run what
        shape a name is. That is the skill's only enumeration of them - every
        other mention sends the reader to §0's one-liner - so it is the only
        one that can go stale, and a stale roll-call here teaches the wrong
        form to exactly the run that is inventing a name.
        """
        self.assertTrue(
            _NAMING,
            "§4.8's 'matching the form of the live entries (...)' list is gone "
            "or reworded; this file reads that wording. Restore it or move "
            "this test to wherever the roll-call now lives.")
        self.assertEqual(
            NAMING_EXAMPLES, LIVE_THEMES,
            "§4.8's roll-call of the live themes disagrees with the table. "
            "Missing from the skill: %s. In the skill but not the table: %s."
            % (sorted(LIVE_THEMES - NAMING_EXAMPLES) or "none",
               sorted(NAMING_EXAMPLES - LIVE_THEMES) or "none"))

    def test_the_skill_counts_the_themed_tables_correctly(self):
        expected = COUNT_WORDS[len(gen.THEMED_TABLES)]
        found = [word for pattern in COUNT_PATTERNS
                 for word in re.findall(pattern, SKILL)]
        self.assertTrue(
            found, "no themed-table count sentence found in the skill - the "
                   "wording this file greps for probably changed")
        for word in found:
            self.assertEqual(
                word, expected,
                "the skill says %r where the generator gates %d tables (%s). "
                "A staging run trusting the wrong list either skips a table "
                "that reads tags or tags one that does not."
                % (word, len(gen.THEMED_TABLES),
                   ", ".join(sorted(gen.THEMED_TABLES))))


class TestTheGateIsStatedOnce(unittest.TestCase):
    def test_the_threshold_is_stated_in_both_places(self):
        """§4.8 sets the bar and §7 rechecks it before handoff. One of them
        alone is a rule with no check, or a check with no rule."""
        self.assertGreaterEqual(
            len(THRESHOLDS), 2,
            "the new-theme threshold appears %d time(s) in the skill; §4.8 "
            "should state it and §7's checklist should recheck it, in the "
            "same '<n> candidates across <n> of the seven themed tables' "
            "wording this file reads." % len(THRESHOLDS))

    def test_both_statements_of_it_agree(self):
        self.assertEqual(
            len(set(THRESHOLDS)), 1,
            "the skill states the new-theme threshold more than one way: %s. "
            "The checklist is what a run is graded against and §4.8 is what it "
            "works from; they have to be the same number."
            % ", ".join("%s across %s" % t for t in sorted(set(THRESHOLDS))))
