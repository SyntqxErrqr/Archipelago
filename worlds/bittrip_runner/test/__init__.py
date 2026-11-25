from test.bases import WorldTestBase

from ..world import BitTripRunnerWorld


class BitTripRunnerTestBase(WorldTestBase):
    game = "BIT.TRIP RUNNER"
    world: BitTripRunnerWorld
