from dataclasses import dataclass

from Options import Choice, DefaultOnToggle, OptionGroup, PerGameCommonOptions, Range, StartInventoryPool, Toggle


class StartingLevels(Range):
    """
    How many random Impetus (zone 1) levels you can play from the start.
    The boss level, Mingrawn Timbletot, is never picked.
    """
    display_name = "Starting Levels"
    range_start = 1
    range_end = 11
    default = 3


class PerfectChecks(DefaultOnToggle):
    """
    Collecting every gold bar in a level (a "PERFECT") is a check.
    Adds 33 locations, one for every non-boss level.
    """
    display_name = "Perfect Checks"


class BonusChecks(Toggle):
    """
    Collecting every gold bar in a level's bonus stage is a check.
    The bonus stage only appears right after you PERFECT its level, so these are the hardest checks in the game.
    Adds 33 locations, one for every non-boss level.
    """
    display_name = "Bonus Stage Checks"


class RainbowFragments(Range):
    """
    How many Rainbow Fragments are shuffled into the item pool. The final boss, The Source, opens once you have
    enough of them.
    If there aren't enough locations for this many (for example with Perfect Checks turned off), fewer are placed.
    """
    display_name = "Rainbow Fragments"
    range_start = 1
    range_end = 50
    default = 20


class RainbowFragmentsRequired(Range):
    """
    The percentage of Rainbow Fragments in the pool that you need before you can face The Source (3-12).
    """
    display_name = "Rainbow Fragments Required (%)"
    range_start = 1
    range_end = 100
    default = 75


class MinimumDifficulty(Choice):
    """
    The lowest difficulty that counts. Levels are only unlocked on this difficulty and the ones above it,
    so you can still switch difficulty in the game's options menu whenever you like.
    """
    display_name = "Minimum Difficulty"
    option_easy = 0
    option_normal = 1
    option_hard = 2
    default = option_easy


@dataclass
class BitTripRunnerOptions(PerGameCommonOptions):
    start_inventory_from_pool: StartInventoryPool
    starting_levels: StartingLevels
    perfect_checks: PerfectChecks
    bonus_checks: BonusChecks
    rainbow_fragments: RainbowFragments
    rainbow_fragments_required: RainbowFragmentsRequired
    minimum_difficulty: MinimumDifficulty


option_groups = [
    OptionGroup("Goal", [RainbowFragments, RainbowFragmentsRequired]),
    OptionGroup("Locations", [PerfectChecks, BonusChecks]),
    OptionGroup("Gameplay", [StartingLevels, MinimumDifficulty]),
]

option_presets = {
    "quick run": {
        "starting_levels": 5,
        "perfect_checks": False,
        "bonus_checks": False,
        "rainbow_fragments_required": 50,
    },
    "completionist": {
        "perfect_checks": True,
        "bonus_checks": True,
        "rainbow_fragments": 40,
        "rainbow_fragments_required": 100,
        "minimum_difficulty": MinimumDifficulty.option_hard,
    },
}
