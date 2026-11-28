from __future__ import annotations

import logging
import math
from collections.abc import Iterable, Mapping
from typing import Any, ClassVar, TextIO

from BaseClasses import Region
from rule_builder.rules import Has
from worlds.AutoWorld import World

from . import items, locations
from .data import (
    BEAT_POINTS,
    BEAT_POINTS_PER_ITEM,
    BEAT_SHARD,
    CHAPTERS,
    DASH,
    DIFFICULTY_NAMES,
    FINALE,
    FIXED_SPOTS,
    GAME_NAME,
    ITEM_ID_BEAT_POINTS,
    ITEM_ID_BEAT_SHARD,
    ITEM_ID_DASH,
    ITEM_ID_PROGRESSIVE_LEVEL,
    ITEM_ID_PROGRESSIVE_LOST_LEVEL,
    ITEM_ID_SONG_BASE,
    ITEM_NAME_TO_ID,
    LOCATION_ID_CLEAR_BASE,
    LOCATION_ID_S_RANK_BASE,
    LOCATION_ID_TUTORIAL_CHECKPOINT_BASE,
    LOCATION_NAME_TO_ID,
    LOST_CHAPTER,
    LOST_CHAPTER_SPOTS,
    MAIN_STORY_SPOTS,
    PLAYLIST_SONGS,
    PROGRESSIVE_LEVEL,
    PROGRESSIVE_LOST_LEVEL,
    SONG_BY_GAME_ID,
    SONG_GROUPS,
    SONGS,
    TUTORIAL_CHECKPOINT_NAMES,
    TUTORIAL_CHECKPOINTS_WITHOUT_DASH,
    TUTORIAL_SONG,
    VICTORY,
    Song,
    clear_location_name,
    s_rank_location_name,
)
from .options import JSABOptions, LostChapter, Mode
from .web_world import JSABWebWorld

STORY_COMPLETE = "Story Complete"
LOST_CHAPTER_COMPLETE = "Lost Chapter Complete"


def expand_song_names(names: Iterable[str]) -> set[str]:
    """Song names from an option, with group names ("Extra Songs", ...) replaced by their songs."""
    result: set[str] = set()
    for name in names:
        result |= SONG_GROUPS.get(name, {name})
    return result


class JSABWorld(World):
    """
    Just Shapes & Beats is a musical bullet hell: dodge pink shapes that move to the beat across a story of 30-odd
    songs. In this randomizer, Story mode levels or Playlist songs are locked until the multiworld sends them,
    and clearing songs or S-ranking them sends items back out.
    """

    game = GAME_NAME
    web = JSABWebWorld()
    options_dataclass = JSABOptions
    options: JSABOptions
    item_name_to_id: ClassVar[dict[str, int]] = ITEM_NAME_TO_ID
    location_name_to_id: ClassVar[dict[str, int]] = LOCATION_NAME_TO_ID
    item_name_groups = items.ITEM_GROUPS
    location_name_groups = locations.LOCATION_GROUPS
    origin_region_name = "Menu"

    MINIMUM_SONG_POOL = 10
    """Exclude Songs never shrinks the Playlist pool below this many songs."""

    song_pool: list[Song]
    starting_songs: list[Song]
    goal_song: Song | None
    beat_shards_placed: int
    beat_shards_required: int
    spot_songs: dict[Song, Song]
    """Story mode: the song each level spot in this seed plays. Every spot plays its own song unless shuffled."""

    @property
    def is_story(self) -> bool:
        return self.options.mode == Mode.option_story

    def generate_early(self) -> None:
        self.song_pool = []
        self.starting_songs = []
        self.goal_song = None
        self.beat_shards_placed = 0
        self.beat_shards_required = 0
        self.spot_songs = {}

        passthrough = getattr(self.multiworld, "re_gen_passthrough", {}).get(self.game)
        if passthrough:
            self.apply_passthrough(passthrough)
            return

        if not self.options.start_with_dash and not self.has_locations_without_dash():
            if self.multiworld.players == 1:
                # Nothing can be checked without Dash, so a single-player game has nowhere to put it.
                logging.warning(f"{self.player_name}: Start With Dash can only be turned off in a multiworld or in "
                                f"Story mode with Tutorial Checkpoints on. Turning it back on.")
                self.options.start_with_dash.value = 1
            else:
                self.multiworld.early_items[self.player][DASH] = 1

        if self.is_story:
            self.pick_spot_songs()
        else:
            self.pick_playlist()

    def story_spots(self) -> tuple[Song, ...]:
        """The level spots in this seed: the main story, then the Lost Chapter if it's included."""
        return MAIN_STORY_SPOTS + (LOST_CHAPTER_SPOTS if self.options.lost_chapter else ())

    def pick_spot_songs(self) -> None:
        spots = self.story_spots()
        self.spot_songs = {spot: spot for spot in spots}
        if self.options.shuffle_story_songs:
            movable = [spot for spot in spots if spot not in FIXED_SPOTS]
            songs = movable.copy()
            self.random.shuffle(songs)
            self.spot_songs.update(zip(movable, songs))

    def has_locations_without_dash(self) -> bool:
        """Only the start of the tutorial can be checked without dashing."""
        return self.is_story and bool(self.options.tutorial_checkpoints)

    def dash_free_location_names(self) -> set[str]:
        return set(TUTORIAL_CHECKPOINT_NAMES[:TUTORIAL_CHECKPOINTS_WITHOUT_DASH]) if self.has_locations_without_dash() \
            else set()

    def apply_passthrough(self, slot_data: Mapping[str, Any]) -> None:
        """Universal Tracker regenerates the world from slot data; reuse what the real generation picked."""
        self.options.mode.value = Mode.option_story if slot_data["mode"] == "story" else Mode.option_playlist
        self.options.s_rank_checks.value = int(slot_data["s_rank_checks"])
        self.options.minimum_difficulty.value = slot_data["minimum_difficulty"]
        self.options.lost_chapter.value = slot_data["lost_chapter"]
        self.options.start_with_dash.value = int(slot_data.get("start_with_dash", True))
        self.options.tutorial_checkpoints.value = int(slot_data.get("tutorial_checkpoints", 0) > 0)
        if self.is_story:
            spot_songs: dict[str, str] = slot_data["spot_songs"]
            self.options.shuffle_story_songs.value = int(any(spot != song for spot, song in spot_songs.items()))
            self.spot_songs = {SONG_BY_GAME_ID[spot]: SONG_BY_GAME_ID[song] for spot, song in spot_songs.items()}
            return
        self.song_pool = [SONG_BY_GAME_ID[game_id] for game_id in slot_data["song_pool"]]
        self.starting_songs = [SONG_BY_GAME_ID[game_id] for game_id in slot_data["starting_songs"]]
        self.goal_song = SONG_BY_GAME_ID[slot_data["goal_song"]]
        self.beat_shards_placed = slot_data["beat_shards_placed"]
        self.beat_shards_required = slot_data["beat_shards_required"]

    def pick_playlist(self) -> None:
        excluded = expand_song_names(self.options.exclude_songs.value)
        pool = [song for song in PLAYLIST_SONGS if song.name not in excluded]
        if len(pool) < self.MINIMUM_SONG_POOL:
            put_back = [song for song in PLAYLIST_SONGS if song not in pool]
            self.random.shuffle(put_back)
            pool += put_back[:self.MINIMUM_SONG_POOL - len(pool)]
            logging.warning(f"{self.player_name}: Exclude Songs left fewer than {self.MINIMUM_SONG_POOL} songs, "
                            f"so some excluded songs were put back.")
        self.song_pool = sorted(pool)

        wanted = expand_song_names(self.options.goal_song.value)
        candidates = [song for song in self.song_pool if song.name in wanted] or self.song_pool
        self.goal_song = self.random.choice(candidates)

        others = [song for song in self.song_pool if song is not self.goal_song]
        self.random.shuffle(others)
        count = self.options.starting_songs.value
        # Every song you don't start with is an item, as is Dash when it's shuffled, and at least one Beat Shard has
        # to fit as well. With S Rank Checks off there is one location per song, so start with more songs if needed.
        extra_items = 1 + (0 if self.options.start_with_dash else 1)
        while count < len(others) and len(others) - count + extra_items > self.location_count():
            count += 1
        if count > self.options.starting_songs.value:
            logging.info(f"{self.player_name}: not enough locations for every song, "
                         f"starting with {count} songs instead of {self.options.starting_songs.value}.")
        self.starting_songs = sorted(others[:count])

        free_slots = self.location_count() - len(self.song_items()) - (extra_items - 1)
        self.beat_shards_placed = max(1, min(self.options.beat_shards.value, free_slots))
        self.beat_shards_required = max(
            1, math.ceil(self.beat_shards_placed * self.options.beat_shards_required.value / 100)
        )

    def song_items(self) -> list[Song]:
        """Playlist songs that are shuffled into the item pool."""
        return [song for song in self.song_pool if song is not self.goal_song and song not in self.starting_songs]

    def checked_songs(self) -> list[Song]:
        """Songs that have locations in this seed."""
        if self.is_story:
            return list(self.story_spots())
        return [song for song in self.song_pool if song is not self.goal_song]

    def location_names_for(self, song: Song) -> list[str]:
        names = [] if song is FINALE else [clear_location_name(song)]
        if self.options.s_rank_checks and song.in_playlist:
            names.append(s_rank_location_name(song))
        return names

    def tutorial_checkpoint_names(self) -> tuple[str, ...]:
        return TUTORIAL_CHECKPOINT_NAMES if self.is_story and self.options.tutorial_checkpoints else ()

    def location_count(self) -> int:
        return (sum(len(self.location_names_for(song)) for song in self.checked_songs())
                + len(self.tutorial_checkpoint_names()))

    def create_regions(self) -> None:
        menu = Region(self.origin_region_name, self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        if self.is_story:
            self.create_story_regions(menu)
        else:
            self.create_playlist_regions(menu)

    def add_song_locations(self, region: Region, song: Song) -> None:
        names = self.location_names_for(song)
        region.add_locations({name: LOCATION_NAME_TO_ID[name] for name in names}, locations.JSABLocation)

    def create_story_regions(self, menu: Region) -> None:
        # The story map is a single path, so reaching a level spot means clearing every spot before it. Opening a spot
        # takes one Progressive Level per spot before it, which opens those earlier spots too.
        for index, spot in enumerate(MAIN_STORY_SPOTS):
            self.create_spot_region(menu, spot, Has(PROGRESSIVE_LEVEL, count=index) if index else None)
        if self.options.lost_chapter:
            region = None
            for index, spot in enumerate(LOST_CHAPTER_SPOTS):
                region = self.create_spot_region(menu, spot, Has(PROGRESSIVE_LOST_LEVEL, count=index + 1))
            assert region is not None
            region.add_event(LOST_CHAPTER_COMPLETE, LOST_CHAPTER_COMPLETE,
                             location_type=locations.JSABLocation, item_type=items.JSABItem)

    def create_spot_region(self, menu: Region, spot: Song, rule: Has | None) -> Region:
        assert spot.chapter is not None
        region = Region(f"{CHAPTERS[spot.chapter].name}: {spot.name}", self.player, self.multiworld)
        self.multiworld.regions.append(region)
        self.create_entrance(menu, region, rule)
        if spot is TUTORIAL_SONG:
            region.add_locations({name: LOCATION_NAME_TO_ID[name] for name in self.tutorial_checkpoint_names()},
                                 locations.JSABLocation)
        song = self.spot_songs[spot]
        if song is FINALE:
            region.add_event(clear_location_name(FINALE), STORY_COMPLETE,
                             location_type=locations.JSABLocation, item_type=items.JSABItem)
        else:
            self.add_song_locations(region, song)
        return region

    def create_playlist_regions(self, menu: Region) -> None:
        for song in self.checked_songs():
            region = Region(song.name, self.player, self.multiworld)
            self.multiworld.regions.append(region)
            self.create_entrance(menu, region, Has(song.name))
            self.add_song_locations(region, song)

        assert self.goal_song is not None
        goal = Region(f"Goal: {self.goal_song.name}", self.player, self.multiworld)
        self.multiworld.regions.append(goal)
        self.create_entrance(menu, goal, Has(BEAT_SHARD, count=self.beat_shards_required))
        goal.add_event(f"Goal: {self.goal_song.name}", VICTORY,
                       location_type=locations.JSABLocation, item_type=items.JSABItem)

    def create_items(self) -> None:
        items.create_all_items(self)

    def create_item(self, name: str) -> items.JSABItem:
        return items.create_item(self, name)

    def get_filler_item_name(self) -> str:
        return BEAT_POINTS

    def set_rules(self) -> None:
        # Dash is needed everywhere except the start of the tutorial. When you start with it, it is precollected, so
        # these rules always pass.
        dash_free = self.dash_free_location_names()
        for location in self.multiworld.get_locations(self.player):
            if location.name not in dash_free:
                self.set_rule(location, Has(DASH))

        if not self.is_story:
            self.set_completion_rule(Has(VICTORY))
        elif self.options.lost_chapter == LostChapter.option_require:
            self.set_completion_rule(Has(STORY_COMPLETE) & Has(LOST_CHAPTER_COMPLETE))
        else:
            self.set_completion_rule(Has(STORY_COMPLETE))

    def fill_slot_data(self) -> Mapping[str, Any]:
        """Everything the mod needs; it carries no song table of its own."""
        return {
            "mode": "story" if self.is_story else "playlist",
            "s_rank_checks": bool(self.options.s_rank_checks),
            "minimum_difficulty": self.options.minimum_difficulty.value,
            "lost_chapter": self.options.lost_chapter.value,
            "chapters": [list(chapter.nodes) for chapter in CHAPTERS],
            "chapter_names": [chapter.name for chapter in CHAPTERS],
            "lost_chapter_index": LOST_CHAPTER.index,
            "finale": FINALE.game_id,
            "lost_chapter_boss": LOST_CHAPTER_SPOTS[-1].game_id,
            # Story level spots in map order, and the song each spot in this seed plays (by game id).
            "main_story_spots": [spot.game_id for spot in MAIN_STORY_SPOTS],
            "lost_chapter_spots": [spot.game_id for spot in LOST_CHAPTER_SPOTS],
            "spot_songs": {spot.game_id: song.game_id for spot, song in self.spot_songs.items()},
            "song_pool": [song.game_id for song in self.song_pool],
            "starting_songs": [song.game_id for song in self.starting_songs],
            "goal_song": self.goal_song.game_id if self.goal_song else None,
            "beat_shards_placed": self.beat_shards_placed,
            "beat_shards_required": self.beat_shards_required,
            "songs": {song.game_id: song.number for song in SONGS},
            "location_id_bases": {"clear": LOCATION_ID_CLEAR_BASE, "s_rank": LOCATION_ID_S_RANK_BASE},
            "item_ids": {
                "progressive_level": ITEM_ID_PROGRESSIVE_LEVEL,
                "progressive_lost_level": ITEM_ID_PROGRESSIVE_LOST_LEVEL,
                "beat_shard": ITEM_ID_BEAT_SHARD,
                "beat_points": ITEM_ID_BEAT_POINTS,
                "dash": ITEM_ID_DASH,
                "song_base": ITEM_ID_SONG_BASE,
            },
            "beat_points_per_item": BEAT_POINTS_PER_ITEM,
            "start_with_dash": bool(self.options.start_with_dash),
            "tutorial_checkpoints": len(self.tutorial_checkpoint_names()),
            "tutorial_checkpoint_location_base": LOCATION_ID_TUTORIAL_CHECKPOINT_BASE,
            "tutorial_song": TUTORIAL_SONG.game_id,
            "difficulty_exempt": [TUTORIAL_SONG.game_id],
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        """Universal Tracker hook: hand slot data back to generate_early as re_gen_passthrough."""
        return slot_data

    def write_spoiler_header(self, spoiler_handle: TextIO) -> None:
        player_name = self.multiworld.get_player_name(self.player)
        spoiler_handle.write(f"\n{player_name}'s mode: {'Story' if self.is_story else 'Playlist'}, "
                             f"minimum difficulty {DIFFICULTY_NAMES[self.options.minimum_difficulty.value - 1]}, "
                             f"{'starts with Dash' if self.options.start_with_dash else 'Dash shuffled'}\n")
        if self.is_story:
            moved = [(spot, song) for spot, song in self.spot_songs.items() if spot is not song]
            if moved:
                spoiler_handle.write(f"{player_name}'s shuffled story songs (level spot: song played there):\n")
                for spot, song in moved:
                    spoiler_handle.write(f"    {spot.name}: {song.name}\n")
            return
        assert self.goal_song is not None
        spoiler_handle.write(f"{player_name}'s starting songs: "
                             f"{', '.join(song.name for song in self.starting_songs)}\n")
        spoiler_handle.write(f"{player_name}'s goal song: {self.goal_song.name}, opened by "
                             f"{self.beat_shards_required} of {self.beat_shards_placed} Beat Shards\n")
