from ..data import (
    FINAL_LEVEL,
    LEVELS,
    RAINBOW_FRAGMENT,
    STAGE_LEVELS,
    UNLOCKABLE_LEVELS,
    clear_location_name,
    level_item_name,
    perfect_location_name,
)
from . import BitTripRunnerTestBase


class TestDefaults(BitTripRunnerTestBase):
    def test_location_count(self) -> None:
        locations = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locations), len(UNLOCKABLE_LEVELS) + len(STAGE_LEVELS))

    def test_starting_levels_are_impetus_stages(self) -> None:
        self.assertEqual(len(self.world.starting_levels), self.world.options.starting_levels.value)
        for level in self.world.starting_levels:
            self.assertEqual(level.zone, 1)
            self.assertFalse(level.is_boss)
            precollected = [item.name for item in self.multiworld.precollected_items[self.player]]
            self.assertIn(level_item_name(level), precollected)

    def test_starting_levels_not_in_pool(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool if item.player == self.player]
        for level in self.world.starting_levels:
            self.assertNotIn(level_item_name(level), pool_names)

    def test_every_other_level_in_pool_once(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool if item.player == self.player]
        starting = set(self.world.starting_levels)
        for level in UNLOCKABLE_LEVELS:
            if level not in starting:
                self.assertEqual(pool_names.count(level_item_name(level)), 1, level.full_name)
        self.assertNotIn(level_item_name(FINAL_LEVEL), pool_names)

    def test_fragment_count(self) -> None:
        pool_names = [item.name for item in self.multiworld.itempool if item.player == self.player]
        self.assertEqual(pool_names.count(RAINBOW_FRAGMENT), self.world.rainbow_fragments_placed)
        self.assertEqual(self.world.rainbow_fragments_placed, self.world.options.rainbow_fragments.value)
        self.assertLessEqual(self.world.rainbow_fragments_required, self.world.rainbow_fragments_placed)

    def test_level_locations_need_their_level(self) -> None:
        stage = next(level for level in STAGE_LEVELS if level not in self.world.starting_levels)
        self.assertFalse(self.can_reach_location(clear_location_name(stage)))
        self.assertFalse(self.can_reach_location(perfect_location_name(stage)))
        self.collect_by_name(level_item_name(stage))
        self.assertTrue(self.can_reach_location(clear_location_name(stage)))
        self.assertTrue(self.can_reach_location(perfect_location_name(stage)))

    def test_goal_needs_fragments(self) -> None:
        self.assertBeatable(False)
        fragments = self.get_items_by_name(RAINBOW_FRAGMENT)
        needed = self.world.rainbow_fragments_required
        self.collect(fragments[:needed - 1])
        self.assertBeatable(False)
        self.collect(fragments[needed - 1])
        self.assertBeatable(True)

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(sorted(slot_data["starting_levels"]),
                         sorted(level.index for level in self.world.starting_levels))
        self.assertEqual(slot_data["rainbow_fragments_required"], self.world.rainbow_fragments_required)


class TestNoPerfects(BitTripRunnerTestBase):
    options = {"perfect_checks": False, "rainbow_fragments": 50, "starting_levels": 1}

    def test_fragments_shrink_to_fit(self) -> None:
        locations = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locations), len(UNLOCKABLE_LEVELS))
        # 35 clears, 34 level items in the pool, one slot left over for a fragment.
        self.assertEqual(self.world.rainbow_fragments_placed, 1)
        self.assertEqual(self.world.rainbow_fragments_required, 1)


class TestEverything(BitTripRunnerTestBase):
    options = {
        "perfect_checks": True,
        "bonus_checks": True,
        "rainbow_fragments": 50,
        "rainbow_fragments_required": 100,
        "starting_levels": 11,
        "minimum_difficulty": "hard",
    }

    def test_location_count(self) -> None:
        locations = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locations), len(UNLOCKABLE_LEVELS) + 2 * len(STAGE_LEVELS))

    def test_all_impetus_stages_start_open(self) -> None:
        self.assertEqual({level.index for level in self.world.starting_levels},
                         {level.index for level in LEVELS if level.zone == 1 and not level.is_boss})

    def test_required_is_all(self) -> None:
        self.assertEqual(self.world.rainbow_fragments_required, self.world.rainbow_fragments_placed)
        self.assertEqual(self.world.fill_slot_data()["minimum_difficulty"], 2)
