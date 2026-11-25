import unittest

from ..client import game_memory
from ..data import (
    ENDING_WORLD,
    FINAL_LEVEL_INDEX,
    ITEM_ID_GOLD_BAR,
    ITEM_ID_LEVEL_BASE,
    ITEM_ID_RAINBOW_FRAGMENT,
    LEVELS,
    next_level_table,
    unlocked_level_indices,
)


class TestUnlocks(unittest.TestCase):
    def test_level_items_unlock_levels(self) -> None:
        received = [ITEM_ID_LEVEL_BASE + 0, ITEM_ID_LEVEL_BASE + 13, ITEM_ID_GOLD_BAR]
        self.assertEqual(unlocked_level_indices(received, fragments_required=3), {0, 13})

    def test_fragments_unlock_final_boss(self) -> None:
        received = [ITEM_ID_RAINBOW_FRAGMENT] * 2
        self.assertNotIn(FINAL_LEVEL_INDEX, unlocked_level_indices(received, fragments_required=3))
        received.append(ITEM_ID_RAINBOW_FRAGMENT)
        self.assertIn(FINAL_LEVEL_INDEX, unlocked_level_indices(received, fragments_required=3))


class TestNextLevelTable(unittest.TestCase):
    def test_vanilla_order_when_everything_is_open(self) -> None:
        table = next_level_table(set(range(len(LEVELS))))
        self.assertEqual(table[0], (0, 1))
        self.assertEqual(table[11], (1, 0))  # 1-12 leads into 2-1
        self.assertEqual(table[23], (2, 0))
        self.assertEqual(table[FINAL_LEVEL_INDEX], (ENDING_WORLD, 0))

    def test_skips_locked_levels_and_wraps(self) -> None:
        table = next_level_table({2, 16, 30})
        self.assertEqual(table[2], (1, 4))  # 1-3 -> 2-5
        self.assertEqual(table[16], (2, 6))  # 2-5 -> 3-7
        self.assertEqual(table[30], (0, 2))  # 3-7 wraps back to 1-3
        self.assertEqual(table[0], (0, 2))

    def test_replays_when_nothing_else_is_open(self) -> None:
        table = next_level_table({5})
        self.assertEqual(table[5], (0, 5))


class TestPatchTable(unittest.TestCase):
    def test_patches_keep_flag_layout(self) -> None:
        # The level-complete code writes "perfect" one byte after "cleared", and the level select reads "bonus"
        # two bytes after it. The AP table offsets have to match that.
        self.assertEqual(game_memory.K_PERFECT, game_memory.K_CLEARED + 1)
        self.assertEqual(game_memory.K_BONUS, game_memory.K_CLEARED + 2)

    def test_original_displacements_point_into_the_save(self) -> None:
        save_end = game_memory.SAVE_RECORDS_ADDRESS + game_memory.RECORD_COUNT * game_memory.RECORD_SIZE
        for patch in game_memory.DISPLACEMENT_PATCHES:
            start = patch.displacement_offset
            target = int.from_bytes(patch.original[start:start + 4], "little")
            # Some reads index from the record *before* the one they mean, so allow one record of slack.
            lowest = game_memory.SAVE_RECORDS_ADDRESS - game_memory.RECORD_SIZE
            self.assertGreaterEqual(target, lowest, hex(patch.address))
            self.assertLess(target, save_end, hex(patch.address))

    def test_table_fits_in_block(self) -> None:
        size = game_memory.AP_HEADER_SIZE + game_memory.RECORD_COUNT * game_memory.RECORD_SIZE
        self.assertLessEqual(size, game_memory.AP_BLOCK_SIZE)
