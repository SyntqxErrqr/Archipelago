from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .data import (
    BEAT_POINTS,
    BEAT_SHARD,
    DASH,
    GAME_NAME,
    ITEM_NAME_TO_ID,
    LOST_CHAPTER_SPOTS,
    MAIN_STORY_SPOTS,
    PROGRESSIVE_LEVEL,
    PROGRESSIVE_LOST_LEVEL,
    SONG_GROUPS,
)

if TYPE_CHECKING:
    from .world import JSABWorld


class JSABItem(Item):
    game = GAME_NAME


ITEM_GROUPS: dict[str, set[str]] = {
    "Songs": {name for group in SONG_GROUPS.values() for name in group},
    **{name: set(group) for name, group in SONG_GROUPS.items()},
    "Story Levels": {PROGRESSIVE_LEVEL, PROGRESSIVE_LOST_LEVEL},
    "Abilities": {DASH},
}


def item_classification(name: str) -> ItemClassification:
    if name == BEAT_POINTS:
        return ItemClassification.filler
    if name == BEAT_SHARD:
        return ItemClassification.progression_skip_balancing
    return ItemClassification.progression


def create_item(world: JSABWorld, name: str) -> JSABItem:
    return JSABItem(name, item_classification(name), ITEM_NAME_TO_ID[name], world.player)


def create_all_items(world: JSABWorld) -> None:
    dash = world.create_item(DASH)
    if world.options.start_with_dash:
        world.push_precollected(dash)
    else:
        world.multiworld.itempool.append(dash)

    unfilled = len(world.multiworld.get_unfilled_locations(world.player))
    dash_in_pool = 0 if world.options.start_with_dash else 1
    if world.is_story:
        # The first spot, the tutorial, is open from the start; every later one takes one more Progressive Level.
        itempool = [world.create_item(PROGRESSIVE_LEVEL) for _ in MAIN_STORY_SPOTS[1:]]
        if world.options.lost_chapter:
            itempool += [world.create_item(PROGRESSIVE_LOST_LEVEL) for _ in LOST_CHAPTER_SPOTS]
        # With S Ranks and Tutorial Checkpoints off there is one location per level, which leaves no room for a
        # shuffled Dash. Start with the first levels open instead.
        overflow = len(itempool) + dash_in_pool - unfilled
        if overflow > 0:
            logging.info(f"{world.player_name}: not enough locations for every Progressive Level, "
                         f"starting with {overflow} of them.")
            for _ in range(overflow):
                world.push_precollected(itempool.pop(0))
    else:
        for song in world.starting_songs:
            world.push_precollected(world.create_item(song.name))
        itempool = [world.create_item(song.name) for song in world.song_items()]
        itempool += [world.create_item(BEAT_SHARD) for _ in range(world.beat_shards_placed)]

    itempool += [world.create_filler() for _ in range(unfilled - len(itempool) - dash_in_pool)]
    world.multiworld.itempool += itempool
