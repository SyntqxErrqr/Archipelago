# Just Shapes & Beats Setup Guide

## Required Software

- [Just Shapes & Beats](https://store.steampowered.com/app/531510/) on Steam, on Windows.
- [BepInEx 6](https://builds.bepinex.dev/projects/bepinex_be) (bleeding edge build, the `BepInEx-Unity.IL2CPP-win-x64`
  download). BepInEx 5 does not work with this game.
- The JSAB Archipelago mod, from the
  [JSAB-Archipelago releases page](https://github.com/SyntqxErrqr/JSAB-Archipelago/releases).
- The latest release of [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases), to generate games.
- The `jsab.apworld` file, placed in your Archipelago `custom_worlds` folder (skip this if your Archipelago install
  already includes Just Shapes & Beats).

## Installing the mod

1. In Steam, right-click Just Shapes & Beats, then **Manage > Browse local files**.
2. Extract the BepInEx zip into that folder, so `winhttp.dll` and the `BepInEx` folder sit next to `JSB.exe`.
3. Start the game once and wait for the title screen. The first start takes a minute or two while BepInEx sets itself
   up. Then close the game.
4. Extract the mod zip into the same folder, so the mod ends up in `BepInEx\plugins\JSABArchipelago`.

## Creating a config file

Visit the [player options page](/games/Just%20Shapes%20%26%20Beats/player-options) to build a YAML, or generate a
template from the Archipelago Launcher with "Generate Template Options".

## Joining a multiworld game

1. Start Just Shapes & Beats.
2. On the title screen, fill in the Archipelago panel in the top-left corner: server address (for example
   `archipelago.gg:38281`), slot name and password. Click a box to type in it; Tab moves to the next box and Ctrl+V
   pastes. Click **Connect** or press Enter.
3. Once it says "Connected", press any button to start. The title screen waits until you have connected, or until you
   click **Play without Archipelago**.

The mod remembers the last server and slot you used. Press **F1** at any time to show or hide the panel. To connect
without touching the panel, set `AutoConnect = true` in `BepInEx\config\com.syntqxerrqr.jsab.archipelago.cfg`.

A new slot starts from a fresh save, so the game shows its "It's not over" bonus challenge screen once. Press any
button to close it.

In Playlist mode, the **Party Mode** difficulty on the song start screen doesn't record ranks, so it doesn't count for
checks. Play on Normal or Hardcore.

## Troubleshooting

- **The panel doesn't appear.** Check `BepInEx\LogOutput.log` for errors. The mod needs the BepInEx 6 IL2CPP build;
  BepInEx 5 and the Mono builds don't load it.
- **My normal save is gone.** It isn't. While connected, the game plays on the slot's own save. Restart the game and
  click **Play without Archipelago** to play your normal save.
- **A chapter is locked in Story mode.** You need another Progressive Chapter (or the Lost Chapter Key). The panel shows
  how many chapters you have opened. Cutscenes on the story map still play; only the levels themselves are locked.
- **A console window opens with the game.** That is BepInEx's log window. Set `Enabled = false` under
  `[Logging.Console]` in `BepInEx\config\BepInEx.cfg` to hide it; the log is still written to `BepInEx\LogOutput.log`.
