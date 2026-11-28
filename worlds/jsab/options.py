from dataclasses import dataclass

from Options import (
    Choice,
    DefaultOnToggle,
    OptionGroup,
    OptionSet,
    PerGameCommonOptions,
    Range,
    StartInventoryPool,
    Toggle,
)

from .data import PLAYLIST_SONGS, SONG_GROUPS

_SONG_KEYS = frozenset(song.name for song in PLAYLIST_SONGS) | frozenset(SONG_GROUPS)


class Mode(Choice):
    """
    Which part of the game the randomizer runs in.

    Story: play through Story mode. Every level on the story map is locked until a Progressive Level item opens it,
    one level at a time in story order, and clearing story levels sends checks. Songs you clear in the story also open
    in Playlist mode for S Rank checks. Beat Till It's Over to win.

    Playlist: play songs from the Playlist screen. You start with a few songs and the rest are items. Collect
    Beat Shards to open the goal song, then clear it to win.
    """
    display_name = "Mode"
    option_story = 0
    option_playlist = 1
    default = option_playlist


class SRankChecks(DefaultOnToggle):
    """
    Getting an S Rank on a song in Playlist mode is a check. An S Rank means finishing the song without taking any
    damage, so these are the hardest checks in the game.
    Adds one location per Playlist song.
    """
    display_name = "S Rank Checks"


class MinimumDifficulty(Choice):
    """
    The lowest difficulty that counts for checks. Clears and S Ranks on this difficulty or a harder one count.
    The game calls Hard "Hardcore".
    """
    display_name = "Minimum Difficulty"
    option_normal = 1
    option_hard = 2
    option_expert = 3
    default = option_normal


class LostChapter(Choice):
    """
    Story mode only. What to do with the Lost Chapter ("Anachronic Order").

    Exclude: leave it out.
    Include: its levels are checks, opened one at a time by Progressive Lost Chapter Level items.
    Require: as Include, and you also have to clear its last level to win.
    """
    display_name = "Lost Chapter"
    option_exclude = 0
    option_include = 1
    option_require = 2
    default = option_exclude


class TutorialCheckpoints(DefaultOnToggle):
    """
    Story mode only. Each of the 9 triangles you collect in the tutorial level, Corrupted, is a check.
    The first six can be reached without dashing; the seventh is behind a wall you have to dash through.
    """
    display_name = "Tutorial Checkpoints"


class ShuffleStorySongs(Toggle):
    """
    Story mode only. Each level on the story map plays a random story song instead of its own, so the story's songs come
    in a new order. The tutorial (Corrupted) and the finale (Till It's Over) stay where they are. With the Lost Chapter
    included, its songs are shuffled in with the rest.
    The levels still open in map order; only the song each one plays changes.
    """
    display_name = "Shuffle Story Songs"


class StartWithDash(DefaultOnToggle):
    """
    Start the game able to dash. Turn this off to shuffle Dash into the multiworld: you can't dash until someone sends
    it to you.
    Every level except the start of the tutorial needs Dash, so turning this off only works in a multiworld, or in
    Story mode with Tutorial Checkpoints on. Otherwise this option is turned back on.
    """
    display_name = "Start With Dash"


class StartingSongs(Range):
    """
    Playlist mode only. How many songs you can play from the start. They are picked at random from the song pool.
    If the pool would hold more items than there are locations, more songs are opened from the start.
    """
    display_name = "Starting Songs"
    range_start = 1
    range_end = 10
    default = 3


class BeatShards(Range):
    """
    Playlist mode only. How many Beat Shards are shuffled into the item pool. The goal song opens once you have enough
    of them. If there aren't enough locations for this many (for example with S Rank Checks turned off), fewer are
    placed.
    """
    display_name = "Beat Shards"
    range_start = 1
    range_end = 50
    default = 20


class BeatShardsRequired(Range):
    """Playlist mode only. The percentage of Beat Shards in the pool that you need to open the goal song."""
    display_name = "Beat Shards Required (%)"
    range_start = 1
    range_end = 100
    default = 75


class GoalSong(OptionSet):
    """
    Playlist mode only. The goal song is picked at random from these songs. Leave empty to pick from every song in the
    pool. Song groups work too: Story Songs, Lost Chapter Songs, Extra Songs, Shovel Knight Songs, Boss Songs.
    """
    display_name = "Goal Song"
    valid_keys = _SONG_KEYS


class ExcludeSongs(OptionSet):
    """
    Playlist mode only. Songs to leave out of the randomizer entirely. Song groups work too: Story Songs,
    Lost Chapter Songs, Extra Songs, Shovel Knight Songs, Boss Songs.
    At least a dozen songs are always kept so the seed can be filled.
    """
    display_name = "Exclude Songs"
    valid_keys = _SONG_KEYS


@dataclass
class JSABOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    mode: Mode
    s_rank_checks: SRankChecks
    minimum_difficulty: MinimumDifficulty
    start_with_dash: StartWithDash
    lost_chapter: LostChapter
    tutorial_checkpoints: TutorialCheckpoints
    shuffle_story_songs: ShuffleStorySongs
    starting_songs: StartingSongs
    beat_shards: BeatShards
    beat_shards_required: BeatShardsRequired
    goal_song: GoalSong
    exclude_songs: ExcludeSongs


option_groups = [
    OptionGroup("General", [Mode, SRankChecks, MinimumDifficulty, StartWithDash]),
    OptionGroup("Story Mode", [LostChapter, TutorialCheckpoints, ShuffleStorySongs]),
    OptionGroup("Playlist Mode", [StartingSongs, BeatShards, BeatShardsRequired, GoalSong, ExcludeSongs]),
]

option_presets = {
    "story": {
        "mode": Mode.option_story,
        "lost_chapter": LostChapter.option_include,
    },
    "story, dash shuffled": {
        "mode": Mode.option_story,
        "start_with_dash": False,
        "tutorial_checkpoints": True,
    },
    "story, songs shuffled": {
        "mode": Mode.option_story,
        "lost_chapter": LostChapter.option_include,
        "shuffle_story_songs": True,
    },
    "playlist sprint": {
        "mode": Mode.option_playlist,
        "s_rank_checks": False,
        "starting_songs": 5,
        "beat_shards": 10,
        "beat_shards_required": 50,
    },
    "hardcore playlist": {
        "mode": Mode.option_playlist,
        "minimum_difficulty": MinimumDifficulty.option_hard,
        "beat_shards": 30,
        "beat_shards_required": 100,
    },
}
