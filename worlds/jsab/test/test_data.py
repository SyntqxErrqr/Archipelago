import unittest

from ..data import (
    CHAPTERS,
    ITEM_NAME_TO_ID,
    LOCATION_NAME_TO_ID,
    PLAYLIST_SONGS,
    SONG_BY_GAME_ID,
    SONGS,
    chapter_songs,
)


class TestSongTable(unittest.TestCase):
    def test_numbers_and_names_unique(self) -> None:
        self.assertEqual(len({song.number for song in SONGS}), len(SONGS))
        self.assertEqual(len({song.name for song in SONGS}), len(SONGS))
        self.assertEqual(len({song.game_id for song in SONGS}), len(SONGS))

    def test_playlist_has_53_songs(self) -> None:
        # The game's Playlist screen (MetaArcadeGroupSongProgress) lists exactly these.
        self.assertEqual(len(PLAYLIST_SONGS), 53)
        self.assertNotIn(SONG_BY_GAME_ID["tuto_0"], PLAYLIST_SONGS)
        self.assertNotIn(SONG_BY_GAME_ID["towerBoss_3"], PLAYLIST_SONGS)

    def test_story_songs_are_chapter_nodes_in_order(self) -> None:
        for chapter in CHAPTERS:
            songs = [song.game_id for song in chapter_songs(chapter)]
            nodes = [node for node in chapter.nodes if node in SONG_BY_GAME_ID]
            self.assertEqual(songs, nodes, chapter.name)

    def test_ids_do_not_collide(self) -> None:
        self.assertEqual(len(set(ITEM_NAME_TO_ID.values())), len(ITEM_NAME_TO_ID))
        self.assertEqual(len(set(LOCATION_NAME_TO_ID.values())), len(LOCATION_NAME_TO_ID))
