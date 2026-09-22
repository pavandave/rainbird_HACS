# Rain Bird (program buttons)

A copy of the built-in Home Assistant [Rain Bird](https://www.home-assistant.io/integrations/rainbird)
integration (from Home Assistant 2026.9.3) with one addition: a **Run program** button for
each program configured on the controller (A, B, C, ...). Pressing a button starts that
program, using `pyrainbird`'s `set_program`.

This is for testing a change before it's proposed upstream to Home Assistant core. Because it
uses the same `rainbird` domain, it replaces the built-in integration. Your existing Rain Bird
config entry, entities and automations keep working.

## Install

1. In HACS, open the menu → **Custom repositories**, add this repository's URL, category **Integration**.
2. Download **Rain Bird (program buttons)**, then restart Home Assistant.
3. Open the Rain Bird controller device. You'll see `Run program A`, `Run program B`, and so on.
   The number of buttons comes from the controller model's program limit.

Use the buttons in automations with the `button.press` action.

## Uninstall

Remove it in HACS and restart. Home Assistant goes back to the built-in integration, and the
program button entities become unavailable, so you can delete them.
