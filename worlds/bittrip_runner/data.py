"""
Static game data shared by the world and the client.

This module must not import anything from Archipelago core, so the client and the tests can use it freely.
"""
from __future__ import annotations

from typing import NamedTuple

GAME_NAME = "BIT.TRIP RUNNER"

ZONE_NAMES = ("Impetus", "Tenacity", "Triumph")
LEVELS_PER_ZONE = 12
BOSS_LEVEL_NUMBER = 12


class Level(NamedTuple):
    index: int
    """0-35, the order the game stores levels in (zone * 12 + level in zone)."""
    zone: int
    """1-3"""
    number: int
    """1-12 inside the zone. 12 is the zone's boss."""
    name: str

    @property
    def code(self) -> str:
        return f"{self.zone}-{self.number}"

    @property
    def full_name(self) -> str:
        return f"{self.code} {self.name}"

    @property
    def is_boss(self) -> bool:
        return self.number == BOSS_LEVEL_NUMBER

    @property
    def is_final_boss(self) -> bool:
        return self.index == FINAL_LEVEL_INDEX

    @property
    def zone_name(self) -> str:
        return ZONE_NAMES[self.zone - 1]


# Level titles, in the order RUNNER.exe stores them.
_LEVEL_TITLES = (
    # Zone 1: Impetus
    "First Contact", "A Wake of Dust", "Gestersmek", "Crater Raider", "Unstoppable Mr. Video", "Junior Melchkin",
    "Jabol Smabbler", "Smabbler's Groan", "Beat Deposits", "End of the Beginning", "Odyssey", "Mingrawn Timbletot",
    # Zone 2: Tenacity
    "Lesser Timbletot", "Hairy Knorkwhisp", "Flyss Whizzle", "Wizened Elderbend", "Pandinkoris Plains", "Moint Moint",
    "Radbot", "Slobbering Falls", "Beat Mines", "Middle of the Middle", "Watcher's Watch", "Non Trotski",
    # Zone 3: Triumph
    "Paradise Lost", "Leaky Krinkston", "Withering Moint", "Sewer Snark", "Congestion", "Tubular Unders",
    "Gall Blaster", "Ginger Pit", "The Gauntlet", "Beginning of the End", "Rusty Warren", "The Source",
)

LEVELS: tuple[Level, ...] = tuple(
    Level(index, index // LEVELS_PER_ZONE + 1, index % LEVELS_PER_ZONE + 1, title)
    for index, title in enumerate(_LEVEL_TITLES)
)
FINAL_LEVEL_INDEX = len(LEVELS) - 1
FINAL_LEVEL = LEVELS[FINAL_LEVEL_INDEX]

UNLOCKABLE_LEVELS = tuple(level for level in LEVELS if not level.is_final_boss)
"""Every level that has its own unlock item. The final boss is opened by Rainbow Fragments instead."""
STAGE_LEVELS = tuple(level for level in LEVELS if not level.is_boss)
"""Levels with gold bars, which means they can be perfected and have a bonus stage."""

RAINBOW_FRAGMENT = "Rainbow Fragment"
GOLD_BAR = "Gold Bar"
VICTORY = "Victory"

# ---- ids -------------------------------------------------------------------------------------------------------------

ITEM_ID_RAINBOW_FRAGMENT = 1
ITEM_ID_GOLD_BAR = 2
ITEM_ID_LEVEL_BASE = 100

LOCATION_ID_CLEAR_BASE = 100
LOCATION_ID_PERFECT_BASE = 200
LOCATION_ID_BONUS_BASE = 300


def level_item_name(level: Level) -> str:
    return level.full_name


def clear_location_name(level: Level) -> str:
    return f"{level.full_name} - Clear"


def perfect_location_name(level: Level) -> str:
    return f"{level.full_name} - Perfect"


def bonus_location_name(level: Level) -> str:
    return f"{level.full_name} - Bonus Perfect"


ITEM_NAME_TO_ID: dict[str, int] = {
    RAINBOW_FRAGMENT: ITEM_ID_RAINBOW_FRAGMENT,
    GOLD_BAR: ITEM_ID_GOLD_BAR,
    **{level_item_name(level): ITEM_ID_LEVEL_BASE + level.index for level in UNLOCKABLE_LEVELS},
}

LOCATION_NAME_TO_ID: dict[str, int] = {
    **{clear_location_name(level): LOCATION_ID_CLEAR_BASE + level.index for level in UNLOCKABLE_LEVELS},
    **{perfect_location_name(level): LOCATION_ID_PERFECT_BASE + level.index for level in STAGE_LEVELS},
    **{bonus_location_name(level): LOCATION_ID_BONUS_BASE + level.index for level in STAGE_LEVELS},
}

LEVEL_BY_ITEM_ID: dict[int, Level] = {ITEM_ID_LEVEL_BASE + level.index: level for level in UNLOCKABLE_LEVELS}


# ---- client helpers --------------------------------------------------------------------------------------------------

def unlocked_level_indices(received_item_ids: list[int], fragments_required: int) -> set[int]:
    """Which levels (by index) the player can enter, given every item id received so far."""
    unlocked = {LEVEL_BY_ITEM_ID[item].index for item in received_item_ids if item in LEVEL_BY_ITEM_ID}
    if received_item_ids.count(ITEM_ID_RAINBOW_FRAGMENT) >= fragments_required:
        unlocked.add(FINAL_LEVEL_INDEX)
    return unlocked


ENDING_WORLD = 6
"""World index the vanilla next-level table sends the player to after the final boss (the ending cutscene)."""


def next_level_table(unlocked: set[int]) -> list[tuple[int, int]]:
    """
    Build the game's "what plays after this level" table: one (world, level in zone) pair per level.

    The vanilla game moves on to the next level in order. Here it moves on to the next *unlocked* level in order,
    wrapping around to the start, and replays the same level if nothing else is open.
    The final boss keeps leading into the ending.
    """
    table: list[tuple[int, int]] = []
    total = len(LEVELS)
    for index in range(total):
        if index == FINAL_LEVEL_INDEX:
            table.append((ENDING_WORLD, 0))
            continue
        following = index
        for step in range(1, total):
            candidate = (index + step) % total
            if candidate in unlocked:
                following = candidate
                break
        table.append(divmod(following, LEVELS_PER_ZONE))
    return table
