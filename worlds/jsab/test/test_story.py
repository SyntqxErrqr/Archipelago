from ..data import (
    BEAT_SHARD,
    LOST_CHAPTER_KEY,
    PLAYLIST_SONGS,
    PROGRESSIVE_CHAPTER,
    SONG_BY_GAME_ID,
    clear_location_name,
    s_rank_location_name,
)
from . import JSABTestBase


class TestStoryDefaults(JSABTestBase):
    options = {"mode": "story"}

    def test_location_count(self) -> None:
        # 30 story clears (Till It's Over is the goal event) and 29 Playlist S Ranks, Lost Chapter included.
        self.assertEqual(len(self.location_names()), 30 + 29)

    def test_items(self) -> None:
        names = self.world_item_names()
        self.assertEqual(names.count(PROGRESSIVE_CHAPTER), 5)
        self.assertEqual(names.count(LOST_CHAPTER_KEY), 1)
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

    def test_lost_chapter_needs_key(self) -> None:
        spider_dance = clear_location_name(SONG_BY_GAME_ID["lost_chapter_boss"])
        self.assertFalse(self.can_reach_location(spider_dance))
        self.collect_by_name(LOST_CHAPTER_KEY)
        self.assertTrue(self.can_reach_location(spider_dance))

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(slot_data["mode"], "story")
        self.assertEqual(slot_data["finale"], "towerBoss_3")
        self.assertEqual(slot_data["lost_chapter_boss"], "lost_chapter_boss")
        self.assertEqual(len(slot_data["chapters"]), 7)


class TestStoryLostChapterRequired(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "require"}

    def test_goal_needs_lost_chapter(self) -> None:
        self.collect_by_name(PROGRESSIVE_CHAPTER)
        self.assertBeatable(False)
        self.collect_by_name(LOST_CHAPTER_KEY)
        self.assertBeatable(True)


class TestStoryNoLostChapterNoRanks(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "exclude", "s_rank_checks": False}

    def test_only_main_story_clears(self) -> None:
        self.assertEqual(len(self.location_names()), 25)
        self.assertNotIn(LOST_CHAPTER_KEY, self.world_item_names())
        self.assertNotIn(clear_location_name(SONG_BY_GAME_ID["lost_chapter_1"]), self.location_names())
