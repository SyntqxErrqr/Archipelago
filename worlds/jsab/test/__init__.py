from test.bases import WorldTestBase

from ..world import JSABWorld


class JSABTestBase(WorldTestBase):
    game = "Just Shapes & Beats"
    world: JSABWorld

    def location_names(self) -> set[str]:
        return {location.name for location in self.multiworld.get_locations(self.player)
                if location.address is not None}

    def world_item_names(self) -> list[str]:
        """Names of every non-event item this world put into the multiworld, placed or not."""
        return [item.name for item in self.multiworld.get_items()
                if item.player == self.player and item.code is not None]

    def precollected_names(self) -> list[str]:
        return [item.name for item in self.multiworld.precollected_items[self.player]]
