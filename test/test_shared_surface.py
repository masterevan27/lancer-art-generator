"""What generate-spaceship.py borrows off its two siblings, written down.

The ship generator changes zero lines of generate-npc.py and generate-art.py
and loads both by path instead. That is only safe while somebody can see what
it depends on, so this file is the list: an NPC-side rename fails here, at test
time, rather than three hundred lines into a render - for most of the names
below, which generate-spaceship.py actually reads. A handful are pinned but
never read anywhere in generate-spaceship.py today (NPC_SURFACE's
THEME_SHARE, flags_for, themes_of, glow_hue_families, CHARS_PER_TOKEN;
ART_SURFACE's Comfy, Entry, WORKFLOW_DIR), so "rather than at render time" is
not literally true of those - there is no render for a rename to break yet.
They stay pinned anyway: Comfy and Entry are the return-type contracts of
find_server()/entry_for() even though nothing names the type directly, and
the rest are a forward-looking churn guard - documented reliance that turns
into a real test failure the day one of them IS used without this list being
updated, rather than a silent gap.

It is also the input to the deferred lancerlib extraction (design 1, phase 2) -
the empirical surface rather than the guessed one.
"""
import unittest

from test.helpers import load_ship_generator

ship = load_ship_generator()

NPC_SURFACE = ("parse_tables", "reference_target", "variant_table", "heading_for",
               "split_flags", "split_backdrop", "split_faction", "flags_for",
               "themes_of", "filter_by_theme", "apply_theme_share", "filter_by_mil",
               "THEME_SHARE", "has_light_source", "light_hues",
               "glow_hue_families", "filter_by_hue", "estimate_tokens",
               "TOKEN_LIMIT", "CHARS_PER_TOKEN", "Knobs", "entry_for",
               "fetch", "_safe", "next_run_folder", "npc_folder")

ART_SURFACE = ("WORKFLOW_DIR", "DEFAULT_WORKFLOW", "POST_ALIASES", "Entry",
               "_slug", "parse_set", "locate_slots", "locate_post_slots",
               "image_ref", "build_post_job", "build_job", "Comfy",
               "find_server", "load_api_workflow", "load_manifest",
               "save_manifest", "WorkflowError")


class TestBorrowedSurface(unittest.TestCase):
    def test_every_npc_name_still_exists(self):
        for name in NPC_SURFACE:
            with self.subTest(name=name):
                self.assertTrue(hasattr(ship.npc, name),
                                "generate-npc.py no longer has %r" % name)

    def test_every_art_name_still_exists(self):
        for name in ART_SURFACE:
            with self.subTest(name=name):
                self.assertTrue(hasattr(ship.art, name),
                                "generate-art.py no longer has %r" % name)

    def test_flags_for_still_returns_the_third_segment(self):
        bullet = "a name || a visual || mil palette"
        self.assertIn("mil", ship.flags_for("Faction", bullet))
        self.assertIn("mil", ship.flags_for("Backdrop", bullet))

    def test_knobs_still_takes_a_size(self):
        args = ship.parse_args(["--dry-run"])
        knobs = ship.Knobs(args, (1536, 768), ship.COMFY_PREFIX)
        self.assertEqual((knobs.width, knobs.height), (1536, 768))

    def test_the_art_module_is_the_one_generate_npc_is_holding(self):
        """The guarded loader's whole reason: one art module, not two.

        generate-npc.py runs its own by-path load of generate-art.py under the
        same sys.modules name. Load art first and unguarded and ship.art and
        ship.npc.art become two module objects with the same name - nothing
        crashes, but an isinstance between their Entry classes starts quietly
        answering False.
        """
        self.assertIs(ship.art, ship.npc.art)
