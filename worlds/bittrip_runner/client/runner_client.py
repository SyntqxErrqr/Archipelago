from __future__ import annotations

import asyncio
import hashlib
import sys
from argparse import Namespace
from typing import TYPE_CHECKING, Any

from CommonClient import ClientCommandProcessor, CommonContext, logger, server_loop
from NetUtils import ClientStatus
from Utils import gui_enabled

from ..data import (
    ABILITIES,
    FINAL_LEVEL_INDEX,
    GAME_NAME,
    ITEM_ID_RAINBOW_FRAGMENT,
    LEVELS,
    LOCATION_ID_BONUS_BASE,
    LOCATION_ID_CLEAR_BASE,
    LOCATION_ID_PERFECT_BASE,
    abilities_required,
    checked_level_flags,
    next_level_table,
    received_ability_numbers,
    unlocked_level_indices,
)
from . import game_memory
from .game_memory import GameMemoryError, RunnerProcess, UnsupportedGameVersion

if TYPE_CHECKING:
    import kvui

DIFFICULTY_NAMES = ("Easy", "Normal", "Hard")
POLL_SECONDS = 0.25


def window_icon_path() -> str | None:
    """
    A file path for the client window's icon.

    Kivy hands the window icon to SDL as a file path, which can't point inside a zipped .apworld, so the icon is
    copied out of the package into Archipelago's cache folder first. Returns None if that fails; the default
    Archipelago icon is used then.
    """
    import os
    import pkgutil

    from Utils import cache_path

    from ..components import ICON_RESOURCE

    try:
        data = pkgutil.get_data(__package__.rsplit(".", 1)[0], ICON_RESOURCE)
        if not data:
            return None
        path = cache_path("bittrip_runner", "icon.png")
        if os.path.exists(path):
            with open(path, "rb") as icon_file:
                if icon_file.read() == data:
                    return path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as icon_file:
            icon_file.write(data)
        return path
    except OSError:
        return None


class BitTripRunnerCommandProcessor(ClientCommandProcessor):
    ctx: BitTripRunnerContext

    def _cmd_levels(self) -> bool:
        """List every level and whether it is unlocked and cleared."""
        if not self.ctx.slot_data:
            logger.info("Connect to a BIT.TRIP RUNNER slot first.")
            return False
        self._cmd_abilities()
        unlocked = self.ctx.unlocked_levels()
        abilities = self.ctx.abilities()
        checked = self.ctx.checked_locations | self.ctx.locations_checked
        for level in LEVELS:
            state = "unlocked" if level.index in unlocked else "locked"
            parts = [f"{level.full_name}: {state}"]
            missing = [name for name in abilities_required(level) if ABILITIES.index(name) not in abilities]
            if missing:
                parts.append(f"needs {', '.join(missing)}")
            if level.index == FINAL_LEVEL_INDEX:
                fragments = self.ctx.received_ids().count(ITEM_ID_RAINBOW_FRAGMENT)
                parts.append(f"{fragments}/{self.ctx.slot_data['rainbow_fragments_required']} Rainbow Fragments")
            else:
                if LOCATION_ID_CLEAR_BASE + level.index in checked:
                    parts.append("cleared")
                if LOCATION_ID_PERFECT_BASE + level.index in checked:
                    parts.append("perfect")
                if LOCATION_ID_BONUS_BASE + level.index in checked:
                    parts.append("bonus perfect")
            logger.info(", ".join(parts))
        return True

    def _cmd_abilities(self) -> bool:
        """List which of CommanderVideo's moves you have."""
        if not self.ctx.slot_data:
            logger.info("Connect to a BIT.TRIP RUNNER slot first.")
            return False
        abilities = self.ctx.abilities()
        have = [name for number, name in enumerate(ABILITIES) if number in abilities]
        missing = [name for number, name in enumerate(ABILITIES) if number not in abilities]
        logger.info(f"Moves: {', '.join(have) or 'none'}" + (f" (missing {', '.join(missing)})" if missing else ""))
        return True

    def _cmd_game(self) -> bool:
        """Show whether the client is hooked into the game."""
        logger.info(self.ctx.game_status)
        return True


class BitTripRunnerContext(CommonContext):
    game = GAME_NAME
    items_handling = 0b111
    command_processor = BitTripRunnerCommandProcessor

    def __init__(self, server_address: str | None, password: str | None) -> None:
        super().__init__(server_address, password)
        self.slot_data: dict[str, Any] | None = None
        self.runner: RunnerProcess | None = None
        self.runner_ready = False
        self.game_status = "Waiting for BIT.TRIP RUNNER to start."
        self._last_logged_status = ""
        self.game_task: asyncio.Task[None] | None = None

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict[str, Any]) -> None:
        if cmd == "Connected":
            self.slot_data = args.get("slot_data") or {}
            # A different slot may own the patches in an already-running game; re-claim on the next tick.
            self.runner_ready = False

    async def disconnect(self, allow_autoreconnect: bool = False) -> None:
        self.slot_data = None
        await super().disconnect(allow_autoreconnect)

    def make_gui(self) -> type[kvui.GameManager]:
        base = super().make_gui()

        class BitTripRunnerManager(base):  # type: ignore[valid-type, misc]
            base_title = "Archipelago BIT.TRIP RUNNER Client"

            def __init__(self, ctx: BitTripRunnerContext) -> None:
                super().__init__(ctx)
                icon = window_icon_path()
                if icon:
                    self.icon = icon

        return BitTripRunnerManager

    # ---- state ------------------------------------------------------------------------------------------------------

    def received_ids(self) -> list[int]:
        return [item.item for item in self.items_received]

    def unlocked_levels(self) -> set[int]:
        assert self.slot_data is not None
        return unlocked_level_indices(self.received_ids(), self.slot_data["rainbow_fragments_required"])

    def abilities(self) -> set[int]:
        assert self.slot_data is not None
        if "start_with_jump" not in self.slot_data:
            # Seed from before moves were shuffled: every move is available.
            return set(range(len(ABILITIES)))
        return received_ability_numbers(self.received_ids())

    def allowed_difficulties(self) -> set[int]:
        assert self.slot_data is not None
        return set(range(self.slot_data.get("minimum_difficulty", 0), game_memory.DIFFICULTIES))

    def slot_identity(self) -> bytes:
        return hashlib.sha256(f"{self.seed_name}|{self.slot}".encode()).digest()

    def set_status(self, status: str) -> None:
        self.game_status = status
        if status != self._last_logged_status:
            logger.info(status)
            self._last_logged_status = status

    # ---- game loop --------------------------------------------------------------------------------------------------

    def drop_game(self) -> None:
        if self.runner:
            self.runner.close()
        self.runner = None
        self.runner_ready = False

    async def tick(self) -> None:
        if self.runner is None or not self.runner.is_alive():
            self.drop_game()
            self.runner = RunnerProcess.attach()
            if self.runner is None:
                self.set_status("Waiting for BIT.TRIP RUNNER to start.")
                return

        if not self.slot_data or self.slot is None:
            self.set_status("Found BIT.TRIP RUNNER. Connect to the Archipelago server to start.")
            return

        if not self.runner_ready:
            if not self.runner.code_is_decrypted():
                self.set_status("BIT.TRIP RUNNER is still starting up...")
                return
            self.runner.install()
            if self.runner.claim_for_slot(self.slot_identity()):
                logger.debug("Started a fresh progress table for this slot.")
            self.runner_ready = True
            self.set_status("Hooked into BIT.TRIP RUNNER. Levels you have unlocked are open in the level select.")

        difficulties = self.allowed_difficulties()
        unlocked = self.unlocked_levels()
        self.runner.write_unlocks(unlocked, difficulties)
        self.runner.write_abilities(self.abilities(), difficulties)
        self.runner.write_next_levels(next_level_table(unlocked))
        # The table starts empty in a freshly started game; put back the markers for checks the server already has.
        self.runner.restore_progress(*checked_level_flags(self.checked_locations), difficulties)
        await self.report_progress()

    async def report_progress(self) -> None:
        assert self.runner is not None and self.slot_data is not None
        allowed = self.allowed_difficulties()
        found: set[int] = set()
        goal = False
        for (difficulty, level_index), flags in self.runner.read_level_flags().items():
            if difficulty not in allowed:
                continue
            if flags.cleared:
                if level_index == FINAL_LEVEL_INDEX:
                    goal = True
                else:
                    found.add(LOCATION_ID_CLEAR_BASE + level_index)
            if flags.perfect and self.slot_data.get("perfect_checks"):
                found.add(LOCATION_ID_PERFECT_BASE + level_index)
            if flags.bonus and self.slot_data.get("bonus_checks"):
                found.add(LOCATION_ID_BONUS_BASE + level_index)

        # check_locations only sends what the server still lists as missing, so calling it every tick is cheap and
        # also covers anything found while the connection was down.
        self.locations_checked |= found
        if found:
            await self.check_locations(found)

        if goal and not self.finished_game:
            self.finished_game = True
            await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
            logger.info("The Source has fallen. Goal complete!")


async def game_loop(ctx: BitTripRunnerContext) -> None:
    if sys.platform != "win32":
        logger.error("The BIT.TRIP RUNNER client only works on Windows.")
        return
    while not ctx.exit_event.is_set():
        try:
            await ctx.tick()
        except UnsupportedGameVersion as error:
            ctx.set_status(str(error))
            ctx.drop_game()
            await asyncio.sleep(10)
        except GameMemoryError as error:
            # Usually the game closing between two reads; try again from scratch.
            logger.debug(f"Lost track of BIT.TRIP RUNNER: {error}")
            ctx.drop_game()
            await asyncio.sleep(1)
        await asyncio.sleep(POLL_SECONDS)


async def main(args: Namespace) -> None:
    ctx = BitTripRunnerContext(args.connect, args.password)
    ctx.auth = args.name
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="ServerLoop")
    ctx.game_task = asyncio.create_task(game_loop(ctx), name="GameLoop")

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()
    if ctx.game_task:
        ctx.game_task.cancel()
    ctx.drop_game()
