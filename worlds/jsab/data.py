"""
Static game data for Just Shapes & Beats.

Song ids, names and chapter layout come from the game itself (Steam build v1.6.50), dumped by the JSABDataDump tool in
the mod repository. This module must not import anything from Archipelago core, so tests and tools can use it freely.
"""
from __future__ import annotations

from typing import NamedTuple

GAME_NAME = "Just Shapes & Beats"


class Chapter(NamedTuple):
    index: int
    name: str
    nodes: tuple[str, ...]
    """
    Every story map node in the chapter, in play order, by the game's checkpoint id. Includes cutscene and
    traversal nodes that have no song (the game calls them "fake songs"), since the mod has to block those too.
    """


# Story chapters in the order the game plays them, grouped the way the game's chapter select groups them.
# The Lost Chapter ("Anachronic Order") is separate: the game opens it from the chapter select, not from the main story.
CHAPTERS: tuple[Chapter, ...] = (
    Chapter(0, "Tutorial", (
        "tuto_0", "tuto_1", "tuto_2", "tuto_3", "tuto_boss", "fakeSong1stTriangleCutscene",
    )),
    Chapter(1, "Paradise", (
        "fakeSongParadiseCredits", "paradise_Boss",
    )),
    Chapter(2, "Island", (
        "volcanEntry_1", "volcanEntry_2", "volcanEntry_3", "volcanEntry_4", "fakeSongVolcanChapterBoat",
        "fakeSongVolcanChapterBarracuda", "volcanEntryBoss", "fakeSongLevelVolcanBoatOut",
    )),
    Chapter(3, "Volcano", (
        "volcanPart1_1", "volcanPart1_2", "volcanPart2_entry", "volcanPart2_1", "fakeSongLevelVolcanElevator",
        "fakeSongLevelVolcanElevatorOut", "volcanPart2_2", "fakeSongTriangleSaved",
    )),
    Chapter(4, "Industry", (
        "industryEntry_1", "industryPart1_1", "industryPart1_2", "industryPart1_3", "fakeIndustryGameplayIntense",
        "fakeIndustryGameplayHelico", "industryPart3_2", "fakeIndustryTriangle",
    )),
    Chapter(5, "Tower", (
        "industryPart4_1", "industryPart4_2", "industryPart4_3", "towerBoss_1", "towerBoss_2", "towerBoss_3",
    )),
    Chapter(6, "Lost Chapter", (
        "lost_chapter_1", "lost_chapter_2", "lost_chapter_3", "fakeSong_lost_chapter_Elevator",
        "fakeSong_lost_chapter_ElevatorOut", "lost_chapter_4", "lost_chapter_boss", "paradiseEntry_end",
    )),
)
MAIN_CHAPTERS = CHAPTERS[:6]
"""The main story, which Progressive Chapter items open one at a time."""
LOST_CHAPTER = CHAPTERS[6]


class Song(NamedTuple):
    number: int
    """Stable number used to build item and location ids. Never renumber a song."""
    game_id: str
    """The game's checkpoint id (ModelStoryCheckpoint.id)."""
    name: str
    artist: str
    chapter: int | None
    """Index into CHAPTERS for songs played in Story mode, None for Playlist-only extras."""
    boss: bool = False
    in_playlist: bool = True
    """False for the two songs that only exist in Story mode: the tutorial and the finale."""
    shovel_knight: bool = False

    @property
    def in_story(self) -> bool:
        return self.chapter is not None


SONGS: tuple[Song, ...] = (
    # Story, in play order.
    Song(1, "tuto_0", "Corrupted", "Danimal Cannon & Zef", 0, in_playlist=False),
    Song(2, "tuto_1", "Chronos", "Danimal Cannon & Zef", 0),
    Song(3, "tuto_2", "Milky Ways", "Bossfight", 0),
    Song(4, "tuto_3", "Logic Gatekeeper", "Danimal Cannon & Zef", 0),
    Song(5, "tuto_boss", "Long Live the New Fresh", "Danimal Cannon", 0, boss=True),
    Song(6, "paradise_Boss", "New Game", "Nitro Fun", 1, boss=True),
    Song(7, "volcanEntry_1", "The Art of War", "Chipzel", 2),
    Song(8, "volcanEntry_2", "Termination Shock", "Sabrepulse", 2),
    Song(9, "volcanEntry_3", "Sevcon", "Big Giant Circles", 2),
    Song(10, "volcanEntry_4", "Cascade", "Kubbi", 2),
    Song(11, "volcanEntryBoss", "Barracuda", "Noisestorm", 2, boss=True),
    Song(12, "volcanPart1_1", "Dubwoofer Substep", "Omnitica", 3),
    Song(13, "volcanPart1_2", "Cheat Codes", "Nitro Fun", 3),
    Song(14, "volcanPart2_1", "Clash", "Trip40", 3),
    Song(15, "volcanPart2_2", "Lycanthropy", "Cardi", 3, boss=True),
    Song(16, "industryEntry_1", "Cool Friends", "Silva Hound (Murtagh & Veschell Remix)", 4),
    Song(17, "industryPart1_1", "The Lunar Whale", "Danimal Cannon", 4),
    Song(18, "industryPart1_2", "Spectra", "Chipzel", 4),
    Song(19, "industryPart1_3", "Unlocked", "Plesco", 4),
    Song(20, "industryPart3_2", "Close to Me", "Sabrepulse", 4, boss=True),
    Song(21, "industryPart4_1", "Into the Zone", "Shirobon", 5),
    Song(22, "industryPart4_2", "Vindicate Me", "Big Giant Circles", 5),
    Song(23, "industryPart4_3", "Try This", "Pegboard Nerds", 5),
    Song(24, "towerBoss_1", "Final Boss", "Nitro Fun", 5, boss=True),
    Song(25, "towerBoss_2", "Annihilate", "Destroid", 5, boss=True),
    Song(26, "towerBoss_3", "Till It's Over", "Tristam", 5, boss=True, in_playlist=False),
    Song(27, "lost_chapter_1", "Airborne Robots", "F-777", 6),
    Song(28, "lost_chapter_2", "Interlaced", "MDK", 6),
    Song(29, "lost_chapter_3", "Last Tile", "Kommisar", 6),
    Song(30, "lost_chapter_4", "Born Survivor", "Shirobon", 6),
    Song(31, "lost_chapter_boss", "Spider Dance", "Shirobon", 6, boss=True),
    # Playlist-only extras. The vanilla game unlocks these with Beat Points and challenge milestones.
    Song(32, "extra1", "Legacy", "Danimal Cannon & Zef", None),
    Song(33, "extra2", "Wicked", "Avenza", None),
    Song(34, "extra3", "First Crush", "Sabrepulse", None),
    Song(35, "extra4", "YokuMan Stage", "Kevin Phetsomphou", None),
    Song(36, "extra5", "Paper Dolls", "Shawn Daley", None),
    Song(37, "extra6", "Commando Steve", "Bossfight", None),
    Song(38, "extra7", "Houston", "Big Giant Circles", None),
    Song(39, "extra8", "Hype", "Tokyo Machine", None),
    Song(40, "extra9", "Tokyo Skies", "Chipzel", None),
    Song(41, "extraUpdate_1_1_1", "Dance of the Incognizant", "FantomenK", None),
    Song(42, "extraUpdate_1_1_2", "Fox", "Shirobon", None),
    Song(43, "extraUpdate_1_1_3", "Core", "Zef", None),
    Song(44, "extraUpdate_1_1_4", "Crystal Tokyo", "FantomenK & Meganeko", None),
    Song(45, "extraUpdate_1_1_5", "On the Run", "Shirobon", None),
    Song(46, "extra10", "Mortal Kombat", "The Immortals", None),
    Song(47, "extraUpdate_1_4_1", "Creatures Ov Deception", "Rainbowdragoneyes", None),
    Song(48, "extraUpdate_1_4_2", "Deadlocked", "F-777", None),
    Song(49, "extraUpdate_1_4_3", "Granite", "Shirobon", None),
    Song(50, "extraUpdate_1_4_4", "Lightspeed", "MDK & Sterrezo", None),
    Song(51, "extraUpdate_1_4_5", "Katana Blaster", "Big Giant Circles", None),
    Song(52, "extraSKUpdate_1", "Strike the Earth!", "Danimal Cannon", None, shovel_knight=True),
    Song(53, "extraSKUpdate_2", "Flowers of Antimony", "Rainbowdragoneyes", None, shovel_knight=True),
    Song(54, "extraSKUpdate_3", "La Danse Macabre", "Shirobon", None, boss=True, shovel_knight=True),
    Song(55, "extraSKUpdate_4", "In the Halls of the Usurper", "Kubbi", None, shovel_knight=True),
)

SONG_BY_NAME: dict[str, Song] = {song.name: song for song in SONGS}
SONG_BY_GAME_ID: dict[str, Song] = {song.game_id: song for song in SONGS}
PLAYLIST_SONGS = tuple(song for song in SONGS if song.in_playlist)
"""The 53 songs on the game's Playlist screen."""
FINALE = SONG_BY_GAME_ID["towerBoss_3"]
"""Till It's Over, the end of the main story."""
LOST_CHAPTER_BOSS = SONG_BY_GAME_ID["lost_chapter_boss"]
TUTORIAL_SONG = SONG_BY_GAME_ID["tuto_0"]
"""Corrupted, the tutorial level. The game always plays it on Normal, so the minimum difficulty doesn't apply to it."""

TUTORIAL_CHECKPOINTS = 9
"""
Triangles collected in the tutorial before its last one, which ends the level. The game plays the tutorial as nine
scenes (LogicMusicTutorial.startLoops); collecting the Nth triangle starts scene N-1
(ActorTutorialLevelLogic.playScene).
"""
TUTORIAL_CHECKPOINTS_WITHOUT_DASH = 6
"""
The sixth triangle starts scene 5, a wall of spikes you can only get past by dashing
(LogicTriangleToCollectTutorial.isStuckedScene), so checkpoints after the sixth need Dash.
"""


def chapter_songs(chapter: Chapter) -> tuple[Song, ...]:
    return tuple(song for song in SONGS if song.chapter == chapter.index)


SONG_GROUPS: dict[str, frozenset[str]] = {
    "Story Songs": frozenset(
        song.name for song in PLAYLIST_SONGS if song.in_story and song.chapter != LOST_CHAPTER.index
    ),
    "Lost Chapter Songs": frozenset(song.name for song in chapter_songs(LOST_CHAPTER)),
    "Extra Songs": frozenset(song.name for song in PLAYLIST_SONGS if not song.in_story),
    "Shovel Knight Songs": frozenset(song.name for song in SONGS if song.shovel_knight),
    "Boss Songs": frozenset(song.name for song in PLAYLIST_SONGS if song.boss),
}

# ---- items -----------------------------------------------------------------------------------------------------------

PROGRESSIVE_CHAPTER = "Progressive Chapter"
LOST_CHAPTER_KEY = "Lost Chapter Key"
BEAT_SHARD = "Beat Shard"
BEAT_POINTS = "Beat Points"
DASH = "Dash"
VICTORY = "Victory"

BEAT_POINTS_PER_ITEM = 100
"""How many Beat Points (the game's own currency) one Beat Points filler item gives."""

ITEM_ID_PROGRESSIVE_CHAPTER = 1
ITEM_ID_LOST_CHAPTER_KEY = 2
ITEM_ID_BEAT_SHARD = 3
ITEM_ID_BEAT_POINTS = 4
ITEM_ID_DASH = 5
ITEM_ID_SONG_BASE = 100

ITEM_NAME_TO_ID: dict[str, int] = {
    PROGRESSIVE_CHAPTER: ITEM_ID_PROGRESSIVE_CHAPTER,
    LOST_CHAPTER_KEY: ITEM_ID_LOST_CHAPTER_KEY,
    BEAT_SHARD: ITEM_ID_BEAT_SHARD,
    BEAT_POINTS: ITEM_ID_BEAT_POINTS,
    DASH: ITEM_ID_DASH,
    **{song.name: ITEM_ID_SONG_BASE + song.number for song in PLAYLIST_SONGS},
}

# ---- locations -------------------------------------------------------------------------------------------------------

LOCATION_ID_CLEAR_BASE = 1000
LOCATION_ID_S_RANK_BASE = 2000
LOCATION_ID_TUTORIAL_CHECKPOINT_BASE = 3000


def tutorial_checkpoint_name(number: int) -> str:
    """Number is 1-based."""
    return f"{TUTORIAL_SONG.name} - Checkpoint {number}"


TUTORIAL_CHECKPOINT_NAMES = tuple(tutorial_checkpoint_name(n) for n in range(1, TUTORIAL_CHECKPOINTS + 1))


def clear_location_name(song: Song) -> str:
    return f"{song.name} - Clear"


def s_rank_location_name(song: Song) -> str:
    return f"{song.name} - S Rank"


def clear_location_id(song: Song) -> int:
    return LOCATION_ID_CLEAR_BASE + song.number


def s_rank_location_id(song: Song) -> int:
    return LOCATION_ID_S_RANK_BASE + song.number


LOCATION_NAME_TO_ID: dict[str, int] = {
    # Every song can be cleared. Till It's Over is the story goal, so it is an event instead.
    **{clear_location_name(song): clear_location_id(song) for song in SONGS if song is not FINALE},
    # Ranks only exist in Playlist mode.
    **{s_rank_location_name(song): s_rank_location_id(song) for song in PLAYLIST_SONGS},
    **{name: LOCATION_ID_TUTORIAL_CHECKPOINT_BASE + n for n, name in enumerate(TUTORIAL_CHECKPOINT_NAMES, start=1)},
}

# ---- difficulties ----------------------------------------------------------------------------------------------------

DIFFICULTY_NAMES = ("Normal", "Hard", "Expert")
"""The game numbers these 1, 2 and 3 (ModelGameDifficulty.difficultyValue)."""
