from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld

from .options import option_groups, option_presets


class JSABWebWorld(WebWorld):
    game = "Just Shapes & Beats"
    theme = "partyTime"
    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up Just Shapes & Beats for Archipelago.",
        "English",
        "setup_en.md",
        "setup/en",
        ["SyntqxErrqr"],
    )
    tutorials = [setup_en]
    option_groups = option_groups
    options_presets = option_presets
