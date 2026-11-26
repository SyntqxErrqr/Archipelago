from __future__ import annotations

from BaseClasses import Location

from .data import (
    CHAPTERS,
    FINALE,
    GAME_NAME,
    PLAYLIST_SONGS,
    SONG_GROUPS,
    SONGS,
    TUTORIAL_CHECKPOINT_NAMES,
    chapter_songs,
    clear_location_name,
    s_rank_location_name,
)


class JSABLocation(Location):
    game = GAME_NAME


LOCATION_GROUPS: dict[str, set[str]] = {
    "Tutorial Checkpoints": set(TUTORIAL_CHECKPOINT_NAMES),
    "Clears": {clear_location_name(song) for song in SONGS if song is not FINALE},
    "S Ranks": {s_rank_location_name(song) for song in PLAYLIST_SONGS},
    **{
        chapter.name: {
            name
            for song in chapter_songs(chapter) if song is not FINALE
            for name in [clear_location_name(song)] + ([s_rank_location_name(song)] if song.in_playlist else [])
        }
        for chapter in CHAPTERS
    },
    **{
        group: {name for song in PLAYLIST_SONGS if song.name in names
                for name in (clear_location_name(song), s_rank_location_name(song))}
        for group, names in SONG_GROUPS.items()
    },
}
