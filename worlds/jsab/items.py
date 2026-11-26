from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .data import (
    BEAT_POINTS,
    BEAT_SHARD,
    DASH,
    GAME_NAME,
    ITEM_NAME_TO_ID,
    LOST_CHAPTER_KEY,
    MAIN_CHAPTERS,
    PROGRESSIVE_CHAPTER,
    SONG_GROUPS,
)

if TYPE_CHECKING:
    from .world import JSABWorld


class JSABItem(Item):
    game = GAME_NAME


ITEM_GROUPS: dict[str, set[str]] = {
    "Songs": {name for group in SONG_GROUPS.values() for name in group},
    **{name: set(group) for name, group in SONG_GROUPS.items()},
    "Chapters": {PROGRESSIVE_CHAPTER, LOST_CHAPTER_KEY},
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

    if world.is_story:
        itempool = [world.create_item(PROGRESSIVE_CHAPTER) for _ in MAIN_CHAPTERS[1:]]
        if world.options.lost_chapter:
            itempool.append(world.create_item(LOST_CHAPTER_KEY))
    else:
        for song in world.starting_songs:
            world.push_precollected(world.create_item(song.name))
        itempool = [world.create_item(song.name) for song in world.song_items()]
        itempool += [world.create_item(BEAT_SHARD) for _ in range(world.beat_shards_placed)]

    unfilled = len(world.multiworld.get_unfilled_locations(world.player))
    in_pool = len(itempool) + (0 if world.options.start_with_dash else 1)
    itempool += [world.create_filler() for _ in range(unfilled - in_pool)]
    world.multiworld.itempool += itempool
