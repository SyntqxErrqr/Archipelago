from collections.abc import Iterable
from unittest import mock

from BaseClasses import Item
from test.bases import WorldTestBase

from ..world import BitTripRunnerWorld


class BitTripRunnerTestBase(WorldTestBase):
    game = "BIT.TRIP RUNNER"
    world: BitTripRunnerWorld

    def get_items_by_name(self, item_names: str | Iterable[str]) -> list[Item]:
        """
        Items from the pool *or already placed*. In a single-player test, pre_fill has already put the moves and level
        unlocks into locations, so the default (pool only) would not find them.
        """
        if isinstance(item_names, str):
            item_names = (item_names,)
        return [item for item in self.multiworld.get_items()
                if item.player == self.player and item.name in item_names and item.code is not None]

    def world_item_names(self) -> list[str]:
        """Names of every non-event item this world put into the multiworld, placed or not."""
        return [item.name for item in self.multiworld.get_items()
                if item.player == self.player and item.code is not None]


class BitTripRunnerLogicTestBase(BitTripRunnerTestBase):
    """
    Stops generation before pre_fill. A solo game pre-places its moves and level unlocks, and state sweeps would then
    pick them up from reachable locations, so "this needs X" checks only make sense with everything still in the pool.
    """
    run_default_tests = False

    def world_setup(self, seed: int | None = None) -> None:
        with mock.patch.object(BitTripRunnerWorld, "pre_fill", lambda world: None):
            super().world_setup(seed)
