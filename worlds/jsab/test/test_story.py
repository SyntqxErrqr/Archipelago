from ..data import (
    BEAT_SHARD,
    DASH,
    FINALE,
    LOST_CHAPTER_SPOTS,
    MAIN_STORY_SPOTS,
    PLAYLIST_SONGS,
    PROGRESSIVE_LEVEL,
    PROGRESSIVE_LOST_LEVEL,
    SONG_BY_GAME_ID,
    TUTORIAL_CHECKPOINT_NAMES,
    TUTORIAL_SONG,
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
        # One per level spot after the tutorial.
        self.assertEqual(names.count(PROGRESSIVE_LEVEL), 25)
        self.assertNotIn(PROGRESSIVE_LOST_LEVEL, names)
        self.assertNotIn(PROGRESSIVE_LEVEL, self.precollected_names())
        self.assertNotIn(DASH, names)
        self.assertIn(DASH, self.precollected_names())
        self.assertNotIn(BEAT_SHARD, names)
        for song in PLAYLIST_SONGS:
            self.assertNotIn(song.name, names)

    def test_only_the_tutorial_is_open_from_the_start(self) -> None:
        self.assertTrue(self.can_reach_location(clear_location_name(TUTORIAL_SONG)))
        self.assertTrue(self.can_reach_location(TUTORIAL_CHECKPOINT_NAMES[-1]))
        chronos = SONG_BY_GAME_ID["tuto_1"]
        self.assertFalse(self.can_reach_location(clear_location_name(chronos)))
        self.assertFalse(self.can_reach_location(s_rank_location_name(chronos)))

    def test_levels_open_one_at_a_time_in_order(self) -> None:
        # collect_by_name would take every copy at once, so collect them one at a time.
        levels = self.get_items_by_name(PROGRESSIVE_LEVEL)
        for count, spot in enumerate(MAIN_STORY_SPOTS[1:-1], start=1):
            name = clear_location_name(spot)
            self.assertFalse(self.can_reach_location(name), name)
            self.collect(levels[count - 1])
            self.assertTrue(self.can_reach_location(name), name)
            if spot.in_playlist:
                self.assertTrue(self.can_reach_location(s_rank_location_name(spot)), spot.name)

    def test_goal_needs_every_level(self) -> None:
        levels = self.get_items_by_name(PROGRESSIVE_LEVEL)
        self.collect(levels[:-1])
        self.assertBeatable(False)
        self.collect(levels[-1])
        self.assertBeatable(True)

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(slot_data["mode"], "story")
        self.assertEqual(slot_data["finale"], "towerBoss_3")
        self.assertEqual(slot_data["lost_chapter_boss"], "lost_chapter_boss")
        self.assertEqual(len(slot_data["chapters"]), 7)
        self.assertEqual(slot_data["tutorial_checkpoints"], 9)
        self.assertTrue(slot_data["start_with_dash"])
        self.assertEqual(slot_data["main_story_spots"], [spot.game_id for spot in MAIN_STORY_SPOTS])
        self.assertEqual(slot_data["lost_chapter_spots"], [spot.game_id for spot in LOST_CHAPTER_SPOTS])
        self.assertEqual(slot_data["spot_songs"], {spot.game_id: spot.game_id for spot in MAIN_STORY_SPOTS})
        self.assertEqual(slot_data["item_ids"]["progressive_level"], 6)
        self.assertEqual(slot_data["item_ids"]["progressive_lost_level"], 7)


class TestStoryLostChapterIncluded(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "include"}

    def test_lost_chapter_locations_and_items(self) -> None:
        self.assertEqual(len(self.location_names()), 30 + 29 + 9)
        self.assertEqual(self.world_item_names().count(PROGRESSIVE_LOST_LEVEL), 5)
        self.assertEqual(self.world.fill_slot_data()["spot_songs"]["lost_chapter_1"], "lost_chapter_1")

    def test_lost_chapter_levels_open_in_order(self) -> None:
        lost_levels = self.get_items_by_name(PROGRESSIVE_LOST_LEVEL)
        first = clear_location_name(LOST_CHAPTER_SPOTS[0])
        spider_dance = clear_location_name(LOST_CHAPTER_SPOTS[-1])
        self.assertFalse(self.can_reach_location(first))
        self.collect(lost_levels[0])
        self.assertTrue(self.can_reach_location(first))
        self.assertFalse(self.can_reach_location(spider_dance))
        self.collect(lost_levels[1:])
        self.assertTrue(self.can_reach_location(spider_dance))

    def test_lost_chapter_not_needed_to_win(self) -> None:
        self.collect_by_name(PROGRESSIVE_LEVEL)
        self.assertBeatable(True)


class TestStoryLostChapterRequired(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "require"}

    def test_goal_needs_lost_chapter(self) -> None:
        self.collect_by_name(PROGRESSIVE_LEVEL)
        self.assertBeatable(False)
        self.collect_by_name(PROGRESSIVE_LOST_LEVEL)
        self.assertBeatable(True)


class TestStoryNoLostChapterNoRanks(JSABTestBase):
    options = {"mode": "story", "lost_chapter": "exclude", "s_rank_checks": False, "tutorial_checkpoints": False}

    def test_only_main_story_clears(self) -> None:
        self.assertEqual(len(self.location_names()), 25)
        self.assertNotIn(PROGRESSIVE_LOST_LEVEL, self.world_item_names())
        self.assertNotIn(clear_location_name(LOST_CHAPTER_SPOTS[0]), self.location_names())
        # One location per level and one Progressive Level per level after the tutorial: it just fits.
        self.assertEqual(self.world_item_names().count(PROGRESSIVE_LEVEL), 25)


class TestStoryNoRoomForDash(JSABTestBase):
    options = {"mode": "story", "s_rank_checks": False, "tutorial_checkpoints": False, "start_with_dash": False}
    # Dash can only be shuffled in a multiworld here, and someone else has to have a place for it.
    players = 2
    other_player_options = {"mode": "story"}
    # The built-in fill tests assume a single player who can check something before receiving any items.
    run_default_tests = False

    def test_starts_with_a_level_open_to_make_room(self) -> None:
        self.assertEqual(len(self.location_names()), 25)
        self.assertIn(DASH, self.world_item_names())
        self.assertEqual(self.world_item_names().count(PROGRESSIVE_LEVEL), 24)
        self.assertEqual(self.precollected_names().count(PROGRESSIVE_LEVEL), 1)


class TestStoryShuffledSongs(JSABTestBase):
    options = {"mode": "story", "shuffle_story_songs": True, "lost_chapter": "include"}

    def test_every_song_plays_exactly_once(self) -> None:
        spot_songs = self.world.spot_songs
        spots = MAIN_STORY_SPOTS + LOST_CHAPTER_SPOTS
        self.assertEqual(set(spot_songs), set(spots))
        self.assertEqual(sorted(spot_songs.values()), sorted(spots))
        self.assertIs(spot_songs[TUTORIAL_SONG], TUTORIAL_SONG)
        self.assertIs(spot_songs[FINALE], FINALE)
        self.assertTrue(any(spot is not song for spot, song in spot_songs.items()), "nothing was shuffled")

    def test_clear_follows_the_song_played_at_the_spot(self) -> None:
        levels = self.get_items_by_name(PROGRESSIVE_LEVEL)
        for count, spot in enumerate(MAIN_STORY_SPOTS[1:-1], start=1):
            song = self.world.spot_songs[spot]
            name = clear_location_name(song)
            self.assertFalse(self.can_reach_location(name), f"{spot.name} plays {song.name}")
            self.collect(levels[count - 1])
            self.assertTrue(self.can_reach_location(name), f"{spot.name} plays {song.name}")

    def test_slot_data_lists_the_shuffle(self) -> None:
        slot_data = self.world.fill_slot_data()
        expected = {spot.game_id: song.game_id for spot, song in self.world.spot_songs.items()}
        self.assertEqual(slot_data["spot_songs"], expected)


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
        corrupted = clear_location_name(TUTORIAL_SONG)
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
