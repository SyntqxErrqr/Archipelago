from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld

from .options import option_groups, option_presets


class BitTripRunnerWebWorld(WebWorld):
    game = "BIT.TRIP RUNNER"
    theme = "partyTime"
    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up BIT.TRIP RUNNER for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["SyntqxErrqr"],
    )
    tutorials = [setup_en]
    option_groups = option_groups
    options_presets = option_presets
