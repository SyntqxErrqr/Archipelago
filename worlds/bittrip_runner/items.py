from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Item, ItemClassification

from .data import GAME_NAME, GOLD_BAR, ITEM_NAME_TO_ID, LEVELS, RAINBOW_FRAGMENT, UNLOCKABLE_LEVELS, level_item_name

if TYPE_CHECKING:
    from .world import BitTripRunnerWorld


class BitTripRunnerItem(Item):
    game = GAME_NAME


ITEM_GROUPS: dict[str, set[str]] = {
    "Levels": {level_item_name(level) for level in UNLOCKABLE_LEVELS},
    "Bosses": {level_item_name(level) for level in UNLOCKABLE_LEVELS if level.is_boss},
    **{
        f"{zone_name} Levels": {level_item_name(level) for level in UNLOCKABLE_LEVELS if level.zone_name == zone_name}
        for zone_name in {level.zone_name for level in LEVELS}
    },
}


def item_classification(name: str) -> ItemClassification:
    if name == GOLD_BAR:
        return ItemClassification.filler
    if name == RAINBOW_FRAGMENT:
        return ItemClassification.progression_skip_balancing
    return ItemClassification.progression


def create_item(world: BitTripRunnerWorld, name: str) -> BitTripRunnerItem:
    return BitTripRunnerItem(name, item_classification(name), ITEM_NAME_TO_ID[name], world.player)


def create_all_items(world: BitTripRunnerWorld) -> None:
    starting_names = {level_item_name(level) for level in world.starting_levels}
    for name in sorted(starting_names):
        world.push_precollected(world.create_item(name))

    itempool = [world.create_item(level_item_name(level)) for level in UNLOCKABLE_LEVELS
                if level_item_name(level) not in starting_names]
    itempool += [world.create_item(RAINBOW_FRAGMENT) for _ in range(world.rainbow_fragments_placed)]

    unfilled = len(world.multiworld.get_unfilled_locations(world.player))
    itempool += [world.create_filler() for _ in range(unfilled - len(itempool))]
    world.multiworld.itempool += itempool
