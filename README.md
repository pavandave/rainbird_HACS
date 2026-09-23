# Rainbird Custom

A copy of the built-in Home Assistant [Rain Bird](https://www.home-assistant.io/integrations/rainbird)
integration (from Home Assistant 2026.9.3) with these additions:

- **Run program buttons**: one button per program on the controller (A, B, C, ...). Pressing
  it starts that program, using `pyrainbird`'s `set_program`.
- **Program next run sensors**: a timestamp sensor per program showing when it next starts.
  It moves on to the following run as soon as a run starts.
- **Zone run times in the calendar**: each program event in the Rain Bird calendar lists the
  zones it waters and for how long, e.g. `Zone 1: 10 min`.
- **Diagnostics**: **Download diagnostics** on the device page gives a JSON file with the full
  schedule (frequency, days, start times, zone run times), the model and the current state.
  The host, password, MAC address and serial number are redacted.

This is for testing changes before they're proposed upstream to Home Assistant core. Because it
uses the same `rainbird` domain, it replaces the built-in integration. Your existing Rain Bird
config entry, entities and automations keep working.

## Install

1. In HACS, open the menu → **Custom repositories**, add
   `https://github.com/pavandave/rainbird_HACS` with category **Integration**.
2. Download **Rainbird Custom**, then restart Home Assistant.
3. Open the Rain Bird controller device. You'll see `Run program A`, `Program A next run`, and
   so on. The number of programs comes from the controller model's program limit.

Use the buttons in automations with the `button.press` action.

The schedule loads in the background shortly after startup and refreshes every 15 minutes, so
the next run sensors and calendar can be empty for a moment after a restart. To reload it
straight away, run the `homeassistant.update_entity` action on the Rain Bird calendar entity.

## Uninstall

Remove it in HACS and restart. Home Assistant goes back to the built-in integration, and the
added button and sensor entities become unavailable, so you can delete them.

## License

This is a modified copy of code from [Home Assistant Core](https://github.com/home-assistant/core),
licensed under the Apache License 2.0 (see [LICENSE](LICENSE)). The modifications are the new
`button.py` and `diagnostics.py` files, the next run sensors in `sensor.py`, zone run times in
`calendar.py`, and the related platform, icon and translation entries.
