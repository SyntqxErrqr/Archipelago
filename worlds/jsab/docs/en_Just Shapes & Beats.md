# Just Shapes & Beats

## Where is the options page?

The [player options page for this game](../player-options) contains all the options you need to configure and export
a config file.

## What does randomization do to this game?

The randomizer runs in one of two modes, picked with the **Mode** option.

### Story mode

You play Story mode as usual, but each chapter stays closed until the multiworld opens it. The chapters open in the
game's own order, one **Progressive Chapter** at a time:

1. Tutorial (open from the start)
2. Paradise
3. Island
4. Volcano
5. Industry
6. Tower

When you reach a level in a chapter you haven't opened yet, the game won't let you in and tells you so. You can go
back to the chapter select and replay earlier chapters while you wait. Because chapters always open in order, you never
hold a chapter you can't reach.

The **Lost Chapter** ("Anachronic Order") is left out by default. With the Lost Chapter option on Include or Require, it
is opened by its own item, the **Lost Chapter Key**.

Songs you clear in Story mode open in Playlist mode as they normally do, which is where S Rank checks are earned.

### Dash

You start able to dash. Turn off **Start With Dash** to shuffle **Dash** into the multiworld instead: you can't dash
until someone sends it. Only the first six tutorial checkpoints can be reached without it, so in a single-player game
this only works in Story mode with Tutorial Checkpoints on; otherwise the option is turned back on.

### Playlist mode

You start with a few songs on the Playlist screen and every other song is an item. Somewhere in the multiworld are
**Beat Shards**; once you have enough of them, the goal song opens.

## What is the goal?

- Story mode: beat **Till It's Over**, the end of the story. With the Lost Chapter option on Require, you also have
  to beat **Spider Dance**, the Lost Chapter's boss.
- Playlist mode: collect the required Beat Shards, then clear the goal song.

## Which items can be in another player's world?

- Story mode: five Progressive Chapters, and the Lost Chapter Key when the Lost Chapter is included.
- Dash, when Start With Dash is off.
- Playlist mode: one item per song (other than your starting songs and the goal song), and the Beat Shards.
- Beat Points, the game's own currency, as filler. Each one gives you 100 Beat Points.

## What counts as a location check?

- Story mode: each of the 9 triangles you collect in the tutorial level, Corrupted (Tutorial Checkpoints, on by
  default). The tenth triangle ends the level and counts as its clear.
- Clearing a song. In Story mode that means clearing the level in Story mode; in Playlist mode it means clearing the
  song on the Playlist screen.
- Getting an S Rank on a song in Playlist mode, which means finishing it without taking any damage (on by default).
  In Story mode, this works for every story song you have cleared, since those open in Playlist mode.

Clears and S Ranks only count on your **Minimum Difficulty** or a harder one. The tutorial is always played on
Normal, so its checks always count. The Playlist's Party Mode difficulty records no ranks, so it never counts.

## Does this touch my save file?

No. While connected, the mod keeps a separate save for each multiworld slot in the game's `BepInEx` folder and never
writes to the game's own save. Your settings carry over. Restart the game without connecting (or remove the mod) to
play your normal save again.

## What does another world's item look like in Just Shapes & Beats?

Items are not shown inside the levels. The mod shows a message on screen whenever you send or receive an item. In
Playlist mode, the game's own "Song unlocked" banner also appears for each song you receive.
