"""The token's canvas, its grid footprint, and the one number Foundry reads.

Two numbers are easy to confuse and the manifest carries both: gridWidth is a
HEX COUNT and tokenWidth is PIXELS. A 1728 in Foundry's token.width would draw
a cruiser across a map the size of a continent, so the distinction is asserted
here rather than trusted - the GUI's importer reads these fields.
"""
import unittest

from test.helpers import load_ship_generator

ship = load_ship_generator()
sp = ship.sp


class TestTokenGrid(unittest.TestCase):
    def test_width_is_read_off_ship_policy_not_typed_twice(self):
        for band in sp.SIZE_ORDER:
            with self.subTest(band=band):
                self.assertEqual(ship.TOKEN_GRID[band][0], sp.hexes_for(band))

    def test_every_band_is_covered_exactly_once(self):
        self.assertEqual(set(ship.TOKEN_GRID), set(sp.SIZE_ORDER))
        self.assertEqual(set(ship.TOKEN_PX_PER_HEX), set(sp.SIZE_ORDER))
        self.assertEqual(set(ship.PLAN_FRAMING), set(sp.SIZE_ORDER))

    def test_grid_widths_are_one_two_three_five_and_increasing(self):
        self.assertEqual([ship.TOKEN_GRID[b][0] for b in sp.SIZE_ORDER],
                         [1, 2, 3, 5])

    def test_every_plan_phrase_is_non_empty(self):
        for band, phrase in ship.PLAN_FRAMING.items():
            with self.subTest(band=band):
                self.assertTrue(phrase.strip())


class TestTokenCanvas(unittest.TestCase):
    def test_both_dimensions_are_multiples_of_64(self):
        for band in sp.SIZE_ORDER:
            w, h = ship.token_size(band)
            with self.subTest(band=band):
                self.assertEqual((w % 64, h % 64), (0, 0))

    def test_area_is_within_the_budget(self):
        for band in sp.SIZE_ORDER:
            w, h = ship.token_size(band)
            with self.subTest(band=band):
                self.assertLessEqual(w * h, ship.MAX_TOKEN_PX)

    def test_canvas_aspect_equals_grid_aspect(self):
        for band in sp.SIZE_ORDER:
            gw, gh = ship.TOKEN_GRID[band]
            w, h = ship.token_size(band)
            with self.subTest(band=band):
                self.assertAlmostEqual(w / h, gw / gh, places=2)

    def test_a_tighter_budget_preserves_aspect_and_the_64_floor(self):
        for band in sp.SIZE_ORDER:
            gw, gh = ship.TOKEN_GRID[band]
            w, h = ship.token_size(band, max_px=1_000_000)
            with self.subTest(band=band):
                self.assertLessEqual(w * h, 1_000_000)
                self.assertGreaterEqual(min(w, h), 64)
                self.assertEqual((w % 64, h % 64), (0, 0))
                self.assertAlmostEqual(w / h, gw / gh, delta=0.02 * gw / gh)


class TestTokenMetadata(unittest.TestCase):
    def test_grid_fields_are_hexes_and_token_fields_are_pixels(self):
        meta = ship.token_metadata("large")
        self.assertEqual(meta["gridWidth"], 3)
        self.assertEqual(meta["gridHeight"], 2)
        self.assertEqual((meta["tokenWidth"], meta["tokenHeight"]),
                         ship.token_size("large"))
        self.assertGreater(
            meta["tokenWidth"], 100,
            "tokenWidth is PIXELS; a hex count here would be a cross-repo "
            "contract break - see the GUI plan's F1")

    def test_every_numeric_field_is_an_int(self):
        for band in sp.SIZE_ORDER:
            for key, value in ship.token_metadata(band).items():
                if key == "sizeBand":
                    continue
                with self.subTest(band=band, key=key):
                    self.assertIsInstance(value, int)


class TestTokenCanvasBelowTheUnitCell(unittest.TestCase):
    """--max-token-px carries no enforced minimum, and a value below one
    64px-per-hex unit cell (4096px for 'small' up to 61440px for 'huge') is a
    real, reachable call - a fix-round regression this pins directly: the
    m-based clamp above once forced m=1 regardless of the budget, so
    --max-token-px 20000 on a huge hull came back 61440px, three times over
    what was asked for. Below the unit, aspect gives way instead of the
    budget; below the absolute 64x64 floor there is no legal answer left at
    all, and 64x64 - never a smaller or negative dimension - is what wins.
    """

    def test_a_budget_below_the_unit_cell_is_pinned_per_band(self):
        for band in sp.SIZE_ORDER:
            gw, gh = ship.TOKEN_GRID[band]
            unit = 64 * 64 * gw * gh
            max_px = unit - 1
            w, h = ship.token_size(band, max_px=max_px)
            with self.subTest(band=band, max_px=max_px):
                self.assertEqual((w % 64, h % 64), (0, 0))
                if max_px >= 64 * 64:
                    self.assertLessEqual(
                        w * h, max_px,
                        "a budget between the 64x64 floor and this band's "
                        "own unit cell must still be honoured")
                else:
                    self.assertEqual(
                        (w, h), (64, 64),
                        "below the absolute floor, 64x64 is the only legal "
                        "answer - never a smaller or negative dimension")
