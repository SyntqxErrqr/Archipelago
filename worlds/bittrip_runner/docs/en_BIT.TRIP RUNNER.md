# BIT.TRIP RUNNER

## Where is the options page?

The [player options page for this game](../player-options) contains all the options you need to configure and export
a config file.

## What does randomization do to this game?

Every level in the game is locked until its unlock item is found somewhere in the multiworld. Instead of opening the
next level by clearing the one before it, you open levels by receiving them, in any order and across all three zones.
You start with a few levels from Impetus (zone 1) already open: always 1-1 and 1-2, then one level that needs Slide
and one that needs Kick, then random ones.

CommanderVideo's moves are items too. In the vanilla game you learn Slide at 1-3, Kick at 1-5, Spring at 1-7 and Block
at 3-1; here you can't use a move until you receive it, and pressing its button does nothing until then. You start with
Jump unless you turn off **Start With Jump**, in which case Jump is somewhere in the multiworld as well. Turn on
**Start With All Moves** to skip move shuffling entirely and start with all five.

A level counts as beatable once you have its unlock and every move the vanilla game had taught by that level, so 1-1 and
1-2 only need Jump, Tenacity levels need everything but Block, and Triumph levels need all five moves.

The final boss, **3-12 The Source**, is not unlocked by an item of its own. It opens once you have collected enough
**Rainbow Fragments**.

After you finish a level, the game moves on to the next level you have unlocked instead of the next one in order.

## What is the goal?

Collect the required number of Rainbow Fragments, then beat 3-12 The Source.

## Which items can be in another player's world?

- One unlock for each level, from 1-1 First Contact to 3-11 Rusty Warren, including the bosses of Impetus and Tenacity.
- Slide, Kick, Spring and Block (and Jump, with Start With Jump turned off), unless Start With All Moves is on.
- Rainbow Fragments, which open the final boss.
- Gold Bars, which are filler and do nothing in the game.

## What counts as a location check?

- Clearing a level.
- Getting a PERFECT on a level by collecting every gold bar (on by default).
- Collecting every gold bar in a level's bonus stage. The bonus stage only appears after a PERFECT, so these are
  optional and off by default.

Clears and PERFECTs count on the minimum difficulty from your options or any harder one. You can change difficulty at any
time from the game's options menu; levels are only shown as unlocked on difficulties that count.

## Does this touch my save file?

No. The client keeps the randomizer's progress inside the running game only, and the game's own save (your vanilla
level progress) is never written by the client. Your high scores are still saved as usual. The PERFECT markers on the
level select show your progress in the current seed while the client is hooked in; if you restart the game, the client
puts them back from the server as soon as it hooks in again. Without the client, the game goes back to normal.

## What does another world's item look like in BIT.TRIP RUNNER?

Items are not shown in the game. The client's window lists everything you send and receive.
