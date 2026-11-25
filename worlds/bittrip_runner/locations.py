from __future__ import annotations

from BaseClasses import Location

from .data import (
    GAME_NAME,
    LEVELS,
    STAGE_LEVELS,
    UNLOCKABLE_LEVELS,
    bonus_location_name,
    clear_location_name,
    perfect_location_name,
)


class BitTripRunnerLocation(Location):
    game = GAME_NAME


LOCATION_GROUPS: dict[str, set[str]] = {
    "Clears": {clear_location_name(level) for level in UNLOCKABLE_LEVELS},
    "Perfects": {perfect_location_name(level) for level in STAGE_LEVELS},
    "Bonus Stages": {bonus_location_name(level) for level in STAGE_LEVELS},
    "Bosses": {clear_location_name(level) for level in UNLOCKABLE_LEVELS if level.is_boss},
    **{
        zone_name: {
            name
            for level in LEVELS if level.zone_name == zone_name and not level.is_final_boss
            for name in (
                [clear_location_name(level)]
                + ([] if level.is_boss else [perfect_location_name(level), bonus_location_name(level)])
            )
        }
        for zone_name in {level.zone_name for level in LEVELS}
    },
}
