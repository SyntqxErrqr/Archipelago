from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from typing import Any, ClassVar, TextIO

from BaseClasses import Region
from Fill import fill_restrictive
from rule_builder.rules import Has, HasAll
from worlds.AutoWorld import World

from . import items, locations
from .data import (
    ABILITIES,
    FINAL_LEVEL,
    GAME_NAME,
    GOLD_BAR,
    ITEM_NAME_TO_ID,
    JUMP,
    JUMP_ONLY_LEVELS,
    LEVEL_ITEM_NAMES,
    LEVELS,
    LOCATION_NAME_TO_ID,
    RAINBOW_FRAGMENT,
    STAGE_LEVELS,
    UNLOCKABLE_LEVELS,
    VICTORY,
    ZONE_NAMES,
    Level,
    abilities_required,
    bonus_location_name,
    clear_location_name,
    level_item_name,
    perfect_location_name,
)
from .options import BitTripRunnerOptions
from .web_world import BitTripRunnerWebWorld


class BitTripRunnerWorld(World):
    """
    BIT.TRIP RUNNER is a rhythm platformer. CommanderVideo runs on his own; you jump, slide, kick and block in time
    with the music across three zones of levels and bosses. In this randomizer, every level is locked until its
    unlock arrives from the multiworld, so are CommanderVideo's moves, and clearing or PERFECTing levels sends items
    back out.
    """

    game = GAME_NAME
    web = BitTripRunnerWebWorld()
    options_dataclass = BitTripRunnerOptions
    options: BitTripRunnerOptions
    item_name_to_id: ClassVar[dict[str, int]] = ITEM_NAME_TO_ID
    location_name_to_id: ClassVar[dict[str, int]] = LOCATION_NAME_TO_ID
    item_name_groups = items.ITEM_GROUPS
    location_name_groups = locations.LOCATION_GROUPS
    origin_region_name = "Level Select"

    starting_levels: list[Level]
    rainbow_fragments_placed: int
    rainbow_fragments_required: int

    def generate_early(self) -> None:
        passthrough = getattr(self.multiworld, "re_gen_passthrough", {}).get(self.game)
        if passthrough:
            # Universal Tracker regenerates the world from slot data; reuse what the real generation picked.
            self.starting_levels = [LEVELS[index] for index in passthrough["starting_levels"]]
            self.rainbow_fragments_placed = passthrough["rainbow_fragments_placed"]
            self.rainbow_fragments_required = passthrough["rainbow_fragments_required"]
            self.options.start_with_jump.value = int(passthrough.get("start_with_jump", True))
            self.options.perfect_checks.value = int(passthrough["perfect_checks"])
            self.options.bonus_checks.value = int(passthrough["bonus_checks"])
            return

        if not self.options.start_with_jump:
            if self.multiworld.players == 1:
                # Every level needs Jump, so a solo game would have nowhere to put it.
                logging.warning(f"{self.player_name}: Start With Jump can only be turned off in a multiworld. "
                                f"Turning it back on.")
                self.options.start_with_jump.value = 1
            else:
                self.multiworld.early_items[self.player][JUMP] = 1

        self.starting_levels = self.pick_starting_levels()

        free_slots = self.location_count() - self.level_items_in_pool() - len(self.abilities_in_pool())
        self.rainbow_fragments_placed = max(1, min(self.options.rainbow_fragments.value, free_slots))
        self.rainbow_fragments_required = max(
            1, math.ceil(self.rainbow_fragments_placed * self.options.rainbow_fragments_required.value / 100)
        )

    def pick_starting_levels(self) -> list[Level]:
        """
        1-1 and 1-2 first, since nothing else can be cleared with only Jump. Then one level that needs Slide and one
        that needs Kick, so each new move has a level waiting for it; without those, the first moves and level unlocks
        have too few locations to go in and some seeds can't be filled. Then random Impetus levels.
        If the pool would hold more items than there are locations, more levels are opened from the start.
        """
        tiers = [
            [level for level in UNLOCKABLE_LEVELS if abilities_required(level)[-1] == move and level.zone == 1]
            for move in ("Slide", "Kick")
        ]
        order = [*JUMP_ONLY_LEVELS, *(self.random.choice(tier) for tier in tiers)]
        impetus = [level for level in UNLOCKABLE_LEVELS
                   if level.zone == 1 and not level.is_boss and level not in order]
        rest = [level for level in UNLOCKABLE_LEVELS if level not in order and level not in impetus]
        self.random.shuffle(impetus)
        self.random.shuffle(rest)
        order += [*impetus, *rest]

        count = self.options.starting_levels.value
        # Every level not started with, every shuffled move and at least one Rainbow Fragment need a location.
        needed = len(UNLOCKABLE_LEVELS) - count + len(self.abilities_in_pool()) + 1
        overflow = needed - self.location_count()
        if overflow > 0:
            logging.info(f"{self.player_name}: not enough locations for every level unlock, "
                         f"starting with {overflow} extra level(s).")
            count += overflow
        return sorted(order[:count])

    def abilities_in_pool(self) -> list[str]:
        return [ability for ability in ABILITIES if not (ability == JUMP and self.options.start_with_jump)]

    def level_items_in_pool(self) -> int:
        return len(UNLOCKABLE_LEVELS) - len(self.starting_levels)

    def location_count(self) -> int:
        count = len(UNLOCKABLE_LEVELS)
        if self.options.perfect_checks:
            count += len(STAGE_LEVELS)
        if self.options.bonus_checks:
            count += len(STAGE_LEVELS)
        return count

    def create_regions(self) -> None:
        level_select = Region(self.origin_region_name, self.player, self.multiworld)
        self.multiworld.regions.append(level_select)

        zones: dict[int, Region] = {}
        for zone_number, zone_name in enumerate(ZONE_NAMES, start=1):
            zone = Region(zone_name, self.player, self.multiworld)
            self.multiworld.regions.append(zone)
            level_select.connect(zone)
            zones[zone_number] = zone

        for level in LEVELS:
            region = Region(level.full_name, self.player, self.multiworld)
            self.multiworld.regions.append(region)
            zone = zones[level.zone]
            moves = HasAll(*abilities_required(level))
            if level.is_final_boss:
                self.create_entrance(zone, region,
                                     Has(RAINBOW_FRAGMENT, count=self.rainbow_fragments_required) & moves)
                region.add_event(
                    clear_location_name(level), VICTORY,
                    location_type=locations.BitTripRunnerLocation, item_type=items.BitTripRunnerItem,
                )
                continue

            self.create_entrance(zone, region, Has(level_item_name(level)) & moves)
            names = [clear_location_name(level)]
            if not level.is_boss:
                if self.options.perfect_checks:
                    names.append(perfect_location_name(level))
                if self.options.bonus_checks:
                    names.append(bonus_location_name(level))
            region.add_locations({name: LOCATION_NAME_TO_ID[name] for name in names}, locations.BitTripRunnerLocation)

    def create_items(self) -> None:
        items.create_all_items(self)

    PRE_FILL_ATTEMPTS = 25

    def pre_fill(self) -> None:
        """
        In a single-player game, place the moves and level unlocks before anything else, retrying unlucky draws.

        Only 1-1 and 1-2 can be cleared with Jump alone and each later move opens a large block of levels, so a solo
        seed starts with just two to four locations to hold whatever opens the rest. A random fill dead-ends there
        often enough (about one seed in four with a single starting level) that it is worth retrying here, where a
        failed attempt can be undone, instead of failing the whole generation. Fragments and filler are left to the
        main fill; once every level is placed they can go anywhere. In a multiworld, the other games provide plenty of
        early locations and the normal fill is used.
        """
        if self.multiworld.players > 1:
            return
        key_names = self.item_name_groups["Abilities"] | LEVEL_ITEM_NAMES
        keys = [item for item in self.multiworld.itempool if item.player == self.player and item.name in key_names]
        for item in keys:
            self.multiworld.itempool.remove(item)
        # Every item still in the pool counts as found; the moves and levels don't, since they were just taken out.
        state = self.multiworld.get_all_state()
        all_locations = self.multiworld.get_unfilled_locations(self.player)

        for _ in range(self.PRE_FILL_ATTEMPTS):
            locations = list(all_locations)
            pool = list(keys)
            self.random.shuffle(locations)
            self.random.shuffle(pool)
            fill_restrictive(self.multiworld, state, locations, pool, single_player_placement=True, lock=True,
                             allow_partial=True, name="BIT.TRIP RUNNER moves and levels")
            if not pool:
                return
            # Dead end: take this attempt's items back out and draw again.
            for location in all_locations:
                if location.item is not None and location.item in keys:
                    location.item.location = None
                    location.item = None
                    location.locked = False

        logging.warning(f"{self.player_name}: could not pre-place moves and levels, leaving them to the main fill.")
        self.multiworld.itempool += keys

    def create_item(self, name: str) -> items.BitTripRunnerItem:
        return items.create_item(self, name)

    def get_filler_item_name(self) -> str:
        return GOLD_BAR

    def set_rules(self) -> None:
        self.set_completion_rule(Has(VICTORY))

    def fill_slot_data(self) -> Mapping[str, Any]:
        return {
            "starting_levels": [level.index for level in self.starting_levels],
            "rainbow_fragments_placed": self.rainbow_fragments_placed,
            "rainbow_fragments_required": self.rainbow_fragments_required,
            "perfect_checks": bool(self.options.perfect_checks),
            "bonus_checks": bool(self.options.bonus_checks),
            "minimum_difficulty": self.options.minimum_difficulty.value,
            "start_with_jump": bool(self.options.start_with_jump),
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        """Universal Tracker hook: hand slot data back to generate_early as re_gen_passthrough."""
        return slot_data

    def write_spoiler_header(self, spoiler_handle: TextIO) -> None:
        player_name = self.multiworld.get_player_name(self.player)
        if self.options.start_with_jump:
            spoiler_handle.write(f"\n{player_name} starts with Jump")
        spoiler_handle.write(f"\n{player_name}'s starting levels: "
                             f"{', '.join(level.full_name for level in self.starting_levels)}\n")
        spoiler_handle.write(f"{player_name}'s Rainbow Fragments needed for {FINAL_LEVEL.full_name}: "
                             f"{self.rainbow_fragments_required} of {self.rainbow_fragments_placed}\n")
