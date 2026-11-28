import random
from argparse import Namespace
from typing import ClassVar

from BaseClasses import CollectionState, MultiWorld
from Generate import get_seed_name
from test.bases import WorldTestBase
from test.general import gen_steps
from worlds import AutoWorld
from worlds.AutoWorld import call_all

from ..world import JSABWorld


class JSABTestBase(WorldTestBase):
    game = "Just Shapes & Beats"
    world: JSABWorld
    players: ClassVar[int] = 1
    """More than 1 generates that many copies of this world, as Player 1 (the one tested), Player 2 and so on."""
    other_player_options: ClassVar[dict[str, object]] = {}
    """Options for Player 2 onwards."""

    def world_setup(self, seed: int | None = None) -> None:
        if self.players == 1:
            super().world_setup(seed)
            return
        # WorldTestBase only builds single-player games. Some options behave differently in a multiworld.
        self.multiworld = MultiWorld(self.players)
        players = range(1, self.players + 1)
        for player in players:
            self.multiworld.game[player] = self.game
        self.multiworld.player_name = {player: f"Tester{player}" for player in players}
        self.multiworld.set_seed(seed)
        random.seed(self.multiworld.seed)
        self.multiworld.seed_name = get_seed_name(random)
        args = Namespace()
        for name, option in AutoWorld.AutoWorldRegister.world_types[self.game].options_dataclass.type_hints.items():
            setattr(args, name, {
                player: option.from_any((self.options if player == self.player else self.other_player_options)
                                        .get(name, option.default))
                for player in players
            })
        self.multiworld.set_options(args)
        self.multiworld.state = CollectionState(self.multiworld)
        self.world = self.multiworld.worlds[self.player]
        for step in gen_steps:
            call_all(self.multiworld, step)

    def location_names(self) -> set[str]:
        return {location.name for location in self.multiworld.get_locations(self.player)
                if location.address is not None}

    def world_item_names(self) -> list[str]:
        """Names of every non-event item this world put into the multiworld, placed or not."""
        return [item.name for item in self.multiworld.get_items()
                if item.player == self.player and item.code is not None]

    def precollected_names(self) -> list[str]:
        return [item.name for item in self.multiworld.precollected_items[self.player]]
