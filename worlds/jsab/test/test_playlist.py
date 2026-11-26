from ..data import (
    BEAT_SHARD,
    PLAYLIST_SONGS,
    PROGRESSIVE_CHAPTER,
    SONG_BY_NAME,
    SONG_GROUPS,
    clear_location_name,
    s_rank_location_name,
)
from . import JSABTestBase


class TestPlaylistDefaults(JSABTestBase):
    options = {"mode": "playlist"}

    def test_location_count(self) -> None:
        # A clear and an S Rank for every song but the goal.
        self.assertEqual(len(self.location_names()), 2 * (len(PLAYLIST_SONGS) - 1))
        goal = self.world.goal_song
        assert goal is not None
        self.assertNotIn(clear_location_name(goal), self.location_names())

    def test_starting_songs(self) -> None:
        self.assertEqual(len(self.world.starting_songs), 3)
        self.assertNotIn(self.world.goal_song, self.world.starting_songs)
        for song in self.world.starting_songs:
            self.assertIn(song.name, self.precollected_names())
            self.assertNotIn(song.name, self.world_item_names())
            self.assertTrue(self.can_reach_location(clear_location_name(song)))

    def test_every_other_song_is_an_item_once(self) -> None:
        names = self.world_item_names()
        for song in self.world.song_items():
            self.assertEqual(names.count(song.name), 1, song.name)
        assert self.world.goal_song is not None
        self.assertNotIn(self.world.goal_song.name, names)
        self.assertNotIn(PROGRESSIVE_CHAPTER, names)

    def test_shards(self) -> None:
        self.assertEqual(self.world_item_names().count(BEAT_SHARD), 20)
        self.assertEqual(self.world.beat_shards_required, 15)

    def test_song_needs_its_item(self) -> None:
        song = self.world.song_items()[0]
        self.assertFalse(self.can_reach_location(s_rank_location_name(song)))
        self.collect_by_name(song.name)
        self.assertTrue(self.can_reach_location(s_rank_location_name(song)))

    def test_goal_needs_shards(self) -> None:
        shards = self.get_items_by_name(BEAT_SHARD)
        self.collect(shards[:14])
        self.assertBeatable(False)
        self.collect(shards[14])
        self.assertBeatable(True)

    def test_slot_data(self) -> None:
        slot_data = self.world.fill_slot_data()
        self.assertEqual(slot_data["mode"], "playlist")
        assert self.world.goal_song is not None
        self.assertEqual(slot_data["goal_song"], self.world.goal_song.game_id)
        self.assertEqual(len(slot_data["song_pool"]), len(PLAYLIST_SONGS))
        self.assertEqual(slot_data["beat_shards_required"], 15)


class TestPlaylistNoRanks(JSABTestBase):
    options = {"mode": "playlist", "s_rank_checks": False, "starting_songs": 1, "beat_shards": 50}

    def test_shards_capped_to_free_locations(self) -> None:
        # 52 clears hold 51 song items, which leaves room for a single Beat Shard.
        self.assertEqual(len(self.location_names()), len(PLAYLIST_SONGS) - 1)
        self.assertEqual(self.world.beat_shards_placed, 1)
        self.assertEqual(self.world.beat_shards_required, 1)


class TestPlaylistGoalAndExcludes(JSABTestBase):
    options = {
        "mode": "playlist",
        "goal_song": ["Annihilate"],
        "exclude_songs": ["Extra Songs"],
        "minimum_difficulty": "expert",
    }

    def test_goal_song(self) -> None:
        self.assertIs(self.world.goal_song, SONG_BY_NAME["Annihilate"])

    def test_extras_left_out(self) -> None:
        pool_names = {song.name for song in self.world.song_pool}
        self.assertFalse(pool_names & SONG_GROUPS["Extra Songs"])
        self.assertEqual(len(self.location_names()), 2 * (len(pool_names) - 1))
        self.assertEqual(self.world.fill_slot_data()["minimum_difficulty"], 3)


class TestPlaylistExcludeTooMuch(JSABTestBase):
    options = {"mode": "playlist", "exclude_songs": ["Story Songs", "Extra Songs"]}

    def test_pool_kept_at_minimum(self) -> None:
        self.assertGreaterEqual(len(self.world.song_pool), self.world.MINIMUM_SONG_POOL)
