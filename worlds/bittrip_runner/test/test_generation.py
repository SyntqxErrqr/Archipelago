from ..data import (
    ABILITIES,
    FINAL_LEVEL,
    JUMP,
    JUMP_ONLY_LEVELS,
    LEVELS,
    RAINBOW_FRAGMENT,
    STAGE_LEVELS,
    UNLOCKABLE_LEVELS,
    abilities_required,
    clear_location_name,
    level_item_name,
    perfect_location_name,
)
from . import BitTripRunnerLogicTestBase, BitTripRunnerTestBase


class TestDefaults(BitTripRunnerTestBase):
    def precollected_names(self) -> list[str]:
        return [item.name for item in self.multiworld.precollected_items[self.player]]

    def test_location_count(self) -> None:
        locations = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locations), len(UNLOCKABLE_LEVELS) + len(STAGE_LEVELS))

    def test_starting_levels(self) -> None:
        self.assertEqual(len(self.world.starting_levels), self.world.options.starting_levels.value)
        for level in JUMP_ONLY_LEVELS:
            self.assertIn(level, self.world.starting_levels)
        # The third pick waits for Slide: 1-3 or 1-4.
        self.assertIn(self.world.starting_levels[2].code, ("1-3", "1-4"))
        for level in self.world.starting_levels:
            self.assertEqual(level.zone, 1)
            self.assertFalse(level.is_boss)
            self.assertIn(level_item_name(level), self.precollected_names())
            self.assertNotIn(level_item_name(level), self.world_item_names())

    def test_every_other_level_in_pool_once(self) -> None:
        starting = set(self.world.starting_levels)
        for level in UNLOCKABLE_LEVELS:
            if level not in starting:
                self.assertEqual(self.world_item_names().count(level_item_name(level)), 1, level.full_name)
        self.assertNotIn(level_item_name(FINAL_LEVEL), self.world_item_names())

    def test_starts_with_jump_and_shuffles_other_moves(self) -> None:
        self.assertIn(JUMP, self.precollected_names())
        self.assertNotIn(JUMP, self.world_item_names())
        for ability in ABILITIES[1:]:
            self.assertEqual(self.world_item_names().count(ability), 1, ability)

    def test_fragment_count(self) -> None:
        self.assertEqual(self.world_item_names().count(RAINBOW_FRAGMENT), self.world.rainbow_fragments_placed)
        self.assertEqual(self.world.rainbow_fragments_placed, self.world.options.rainbow_fragments.value)
        self.assertLessEqual(self.world.rainbow_fragments_required, self.world.rainbow_fragments_placed)

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(sorted(slot_data["starting_levels"]),
                         sorted(level.index for level in self.world.starting_levels))
        self.assertEqual(slot_data["rainbow_fragments_required"], self.world.rainbow_fragments_required)
        self.assertTrue(slot_data["start_with_jump"])


class TestLogic(BitTripRunnerLogicTestBase):
    def test_jump_only_levels_open_from_the_start(self) -> None:
        for level in JUMP_ONLY_LEVELS:
            self.assertTrue(self.can_reach_location(clear_location_name(level)), level.full_name)

    def test_levels_need_their_unlock_and_moves(self) -> None:
        # 2-5 needs its unlock plus Slide, Kick and Spring.
        level = LEVELS[16]
        self.assertEqual(abilities_required(level), (JUMP, "Slide", "Kick", "Spring"))
        self.collect_by_name(level_item_name(level))
        self.assertFalse(self.can_reach_location(clear_location_name(level)))
        self.collect_by_name(["Slide", "Kick"])
        self.assertFalse(self.can_reach_location(perfect_location_name(level)))
        self.collect_by_name("Spring")
        self.assertTrue(self.can_reach_location(clear_location_name(level)))
        self.assertTrue(self.can_reach_location(perfect_location_name(level)))

    def test_triumph_needs_block(self) -> None:
        level = LEVELS[24]
        self.collect_by_name([level_item_name(level), "Slide", "Kick", "Spring"])
        self.assertFalse(self.can_reach_location(clear_location_name(level)))
        self.collect_by_name("Block")
        self.assertTrue(self.can_reach_location(clear_location_name(level)))

    def test_goal_needs_every_move(self) -> None:
        fragments = self.get_items_by_name(RAINBOW_FRAGMENT)
        self.collect(fragments[:self.world.rainbow_fragments_required])
        self.collect_by_name(list(ABILITIES[1:4]))
        self.assertBeatable(False)
        self.collect_by_name("Block")
        self.assertBeatable(True)

    def test_goal_needs_fragments(self) -> None:
        fragments = self.get_items_by_name(RAINBOW_FRAGMENT)
        needed = self.world.rainbow_fragments_required
        self.collect_by_name(list(ABILITIES[1:]))
        self.collect(fragments[:needed - 1])
        self.assertBeatable(False)
        self.collect(fragments[needed - 1])
        self.assertBeatable(True)


class TestOneStartingLevel(BitTripRunnerTestBase):
    options = {"starting_levels": 1}

    def test_starts_on_first_contact(self) -> None:
        self.assertEqual(self.world.starting_levels, [LEVELS[0]])


class TestSoloWithoutJump(BitTripRunnerTestBase):
    options = {"start_with_jump": False}

    def test_falls_back_to_starting_with_jump(self) -> None:
        # Nothing can be cleared without Jump, so a single-player game has nowhere to put it.
        self.assertTrue(self.world.options.start_with_jump)
        self.assertIn(JUMP, [item.name for item in self.multiworld.precollected_items[self.player]])


class TestNoPerfects(BitTripRunnerTestBase):
    options = {"perfect_checks": False, "rainbow_fragments": 50, "starting_levels": 1}

    def test_items_fit(self) -> None:
        locations = [loc for loc in self.multiworld.get_locations(self.player) if loc.address is not None]
        self.assertEqual(len(locations), len(UNLOCKABLE_LEVELS))
        # 35 clears can't hold 34 level unlocks, 4 moves and a fragment, so extra levels start open:
        # 1-1, 1-2, one that needs Slide, one that needs Kick, then a random one.
        self.assertEqual(len(self.world.starting_levels), 5)
        codes = [level.code for level in self.world.starting_levels]
        self.assertEqual(codes[:2], ["1-1", "1-2"])
        self.assertTrue({"1-3", "1-4"} & set(codes))
        self.assertTrue({"1-5", "1-6"} & set(codes))
        self.assertEqual(self.world.rainbow_fragments_placed, 1)
        self.assertEqual(self.world.rainbow_fragments_required, 1)
        self.assertEqual(len(self.world_item_names()), len(locations))


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
