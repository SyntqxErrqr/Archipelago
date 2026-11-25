from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, ClassVar, TextIO

from BaseClasses import Region
from rule_builder.rules import Has
from worlds.AutoWorld import World

from . import items, locations
from .data import (
    FINAL_LEVEL,
    GAME_NAME,
    GOLD_BAR,
    ITEM_NAME_TO_ID,
    LEVELS,
    LOCATION_NAME_TO_ID,
    RAINBOW_FRAGMENT,
    STAGE_LEVELS,
    UNLOCKABLE_LEVELS,
    VICTORY,
    ZONE_NAMES,
    Level,
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
    unlock arrives from the multiworld, and clearing or PERFECTing levels sends items back out.
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
            return

        impetus_levels = [level for level in UNLOCKABLE_LEVELS if level.zone == 1 and not level.is_boss]
        self.starting_levels = sorted(self.random.sample(impetus_levels, self.options.starting_levels.value))

        level_items = len(UNLOCKABLE_LEVELS) - len(self.starting_levels)
        free_slots = self.location_count() - level_items
        self.rainbow_fragments_placed = max(1, min(self.options.rainbow_fragments.value, free_slots))
        self.rainbow_fragments_required = max(
            1, math.ceil(self.rainbow_fragments_placed * self.options.rainbow_fragments_required.value / 100)
        )

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
            if level.is_final_boss:
                self.create_entrance(zone, region, Has(RAINBOW_FRAGMENT, count=self.rainbow_fragments_required))
                region.add_event(
                    clear_location_name(level), VICTORY,
                    location_type=locations.BitTripRunnerLocation, item_type=items.BitTripRunnerItem,
                )
                continue

            self.create_entrance(zone, region, Has(level_item_name(level)))
            names = [clear_location_name(level)]
            if not level.is_boss:
                if self.options.perfect_checks:
                    names.append(perfect_location_name(level))
                if self.options.bonus_checks:
                    names.append(bonus_location_name(level))
            region.add_locations({name: LOCATION_NAME_TO_ID[name] for name in names}, locations.BitTripRunnerLocation)

    def create_items(self) -> None:
        items.create_all_items(self)

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
        }

    @staticmethod
    def interpret_slot_data(slot_data: dict[str, Any]) -> dict[str, Any]:
        """Universal Tracker hook: hand slot data back to generate_early as re_gen_passthrough."""
        return slot_data

    def write_spoiler_header(self, spoiler_handle: TextIO) -> None:
        player_name = self.multiworld.get_player_name(self.player)
        spoiler_handle.write(f"\n{player_name}'s starting levels: "
                             f"{', '.join(level.full_name for level in self.starting_levels)}\n")
        spoiler_handle.write(f"{player_name}'s Rainbow Fragments needed for {FINAL_LEVEL.full_name}: "
                             f"{self.rainbow_fragments_required} of {self.rainbow_fragments_placed}\n")
