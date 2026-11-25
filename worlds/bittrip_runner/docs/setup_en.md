# BIT.TRIP RUNNER Setup Guide

## Required Software

- [BIT.TRIP RUNNER](https://store.steampowered.com/app/63710/) on Steam, on Windows.
- The latest release of [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases).
- The `bittrip_runner.apworld` file, placed in your Archipelago `custom_worlds` folder (skip this if your Archipelago
  install already includes BIT.TRIP RUNNER).

The client hooks into the running game, so only the Windows Steam version is supported. Other versions (DRM-free, macOS,
Linux) are detected and refused instead of being patched.

## Creating a config file

Visit the [player options page](/games/BIT.TRIP%20RUNNER/player-options) to build a YAML, or generate a template from
the Archipelago Launcher with "Generate Template Options".

## Joining a multiworld game

1. Start BIT.TRIP RUNNER from Steam and press a button on the title screen.
2. Open the Archipelago Launcher and click **BIT.TRIP RUNNER Client**.
3. Connect to the server with your slot name. You can also click your slot name on the room page and pick the
   BIT.TRIP RUNNER Client to connect automatically.
4. The client log says "Hooked into BIT.TRIP RUNNER" once it has taken over the level select. Pick a zone from the
   main menu; levels you have unlocked are shown in color and locked ones are grayed out.

You can start the game and the client in either order, and restart either of them at any time. Keep the client
running while you play: it is what notices that you cleared a level and sends the check.

## Client commands

- `/levels` lists every level with whether it is unlocked, cleared, PERFECT and bonus PERFECT.
- `/game` shows whether the client is hooked into the game.

## Troubleshooting

- **Every level is locked.** Make sure the client is connected to the server. Also check the difficulty shown on the
  main menu: levels only unlock on your minimum difficulty from the YAML and above.
- **"Only the current Windows Steam build of BIT.TRIP RUNNER is supported."** The client found code it does not
  recognize, so it left the game alone. Verify the game files in Steam and try again.
- **Levels are back to normal after restarting the game.** The client has to be running to lock levels. Start the
  client and connect again.
