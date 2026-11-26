from ..data import (
    BEAT_SHARD,
    DASH,
    LOST_CHAPTER_KEY,
    PLAYLIST_SONGS,
    PROGRESSIVE_CHAPTER,
    SONG_BY_GAME_ID,
    TUTORIAL_CHECKPOINT_NAMES,
    clear_location_name,
    s_rank_location_name,
)
from . import JSABTestBase


class TestStoryDefaults(JSABTestBase):
    options = {"mode": "story"}

    def test_location_count(self) -> None:
        # 25 main-story clears (Till It's Over is the goal event), 24 Playlist S Ranks and 9 tutorial checkpoints.
        # The Lost Chapter is left out by default.
        self.assertEqual(len(self.location_names()), 25 + 24 + 9)
        for name in TUTORIAL_CHECKPOINT_NAMES:
            self.assertIn(name, self.location_names())

    def test_items(self) -> None:
        names = self.world_item_names()
        self.assertEqual(names.count(PROGRESSIVE_CHAPTER), 5)
        self.assertNotIn(LOST_CHAPTER_KEY, names)
        self.assertNotIn(DASH, names)
        self.assertIn(DASH, self.precollected_names())
        self.assertNotIn(BEAT_SHARD, names)
        for song in PLAYLIST_SONGS:
            self.assertNotIn(song.name, names)

    def test_tutorial_open_from_the_start(self) -> None:
        self.assertTrue(self.can_reach_location(clear_location_name(SONG_BY_GAME_ID["tuto_0"])))
        self.assertTrue(self.can_reach_location(s_rank_location_name(SONG_BY_GAME_ID["tuto_boss"])))

    def test_chapters_open_in_order(self) -> None:
        # collect_by_name would take all five copies at once, so collect them one at a time.
        chapters = self.get_items_by_name(PROGRESSIVE_CHAPTER)
        new_game = clear_location_name(SONG_BY_GAME_ID["paradise_Boss"])
        barracuda = clear_location_name(SONG_BY_GAME_ID["volcanEntryBoss"])
        self.assertFalse(self.can_reach_location(new_game))
        self.collect(chapters[0])
        self.assertTrue(self.can_reach_location(new_game))
        self.assertFalse(self.can_reach_location(barracuda))
        self.collect(chapters[1])
        self.assertTrue(self.can_reach_location(barracuda))

    def test_goal_needs_every_chapter(self) -> None:
        chapters = self.get_items_by_name(PROGRESSIVE_CHAPTER)
        self.collect(chapters[:4])
        self.assertBeatable(False)
        self.collect(chapters[4])
        self.assertBeatable(True)

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(slot_data["mode"], "story")
        self.assertEqual(slot_data["finale"], "towerBoss_3")
        self.assertEqual(slot_data["lost_chapter_boss"], "lost_chapter_boss")
        self.assertEqual(len(slot_data["chapters"]), 7)
        self.assertEqual(slot_data["tutorial_checkpoints"], 9)
        self.assertTrue(slot_data["start_with_dash"])


class TestStoryLostChapterIncluded(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "include"}

    def test_lost_chapter_locations_and_key(self) -> None:
        self.assertEqual(len(self.location_names()), 30 + 29 + 9)
        self.assertEqual(self.world_item_names().count(LOST_CHAPTER_KEY), 1)

    def test_lost_chapter_needs_key(self) -> None:
        spider_dance = clear_location_name(SONG_BY_GAME_ID["lost_chapter_boss"])
        self.assertFalse(self.can_reach_location(spider_dance))
        self.collect_by_name(LOST_CHAPTER_KEY)
        self.assertTrue(self.can_reach_location(spider_dance))


class TestStoryLostChapterRequired(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "require"}

    def test_goal_needs_lost_chapter(self) -> None:
        self.collect_by_name(PROGRESSIVE_CHAPTER)
        self.assertBeatable(False)
        self.collect_by_name(LOST_CHAPTER_KEY)
        self.assertBeatable(True)


class TestStoryNoLostChapterNoRanks(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "exclude", "s_rank_checks": False, "tutorial_checkpoints": False}

    def test_only_main_story_clears(self) -> None:
        self.assertEqual(len(self.location_names()), 25)
        self.assertNotIn(LOST_CHAPTER_KEY, self.world_item_names())
        self.assertNotIn(clear_location_name(SONG_BY_GAME_ID["lost_chapter_1"]), self.location_names())


class TestStoryDashShuffled(JSABTestBase):
    options = {"mode": "story", "start_with_dash": False}

    def test_dash_in_pool(self) -> None:
        self.assertEqual(self.world_item_names().count(DASH), 1)
        self.assertNotIn(DASH, self.precollected_names())

    def test_dash_gates_all_but_first_six_checkpoints(self) -> None:
        for name in TUTORIAL_CHECKPOINT_NAMES[:6]:
            self.assertTrue(self.can_reach_location(name), name)
        for name in TUTORIAL_CHECKPOINT_NAMES[6:]:
            self.assertFalse(self.can_reach_location(name), name)
        corrupted = clear_location_name(SONG_BY_GAME_ID["tuto_0"])
        self.assertFalse(self.can_reach_location(corrupted))
        self.collect_by_name(DASH)
        self.assertTrue(self.can_reach_location(corrupted))
        self.assertTrue(self.can_reach_location(TUTORIAL_CHECKPOINT_NAMES[8]))
        self.assertFalse(self.world.fill_slot_data()["start_with_dash"])


class TestStoryDashShuffledNoCheckpointsSolo(JSABTestBase):
    options = {"mode": "story", "start_with_dash": False, "tutorial_checkpoints": False}

    def test_falls_back_to_starting_with_dash(self) -> None:
        # Nothing can be checked without Dash, so a single-player game has nowhere to put it.
        self.assertTrue(self.world.options.start_with_dash)
        self.assertIn(DASH, self.precollected_names())
