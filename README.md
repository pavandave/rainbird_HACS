# Rainbird Custom

A copy of the built-in Home Assistant [Rain Bird](https://www.home-assistant.io/integrations/rainbird)
integration (from Home Assistant 2026.9.3) with these additions:

- **Run program buttons**: one button per program on the controller (A, B, C, ...). Pressing
  it starts that program, using `pyrainbird`'s `set_program`.
- **Program next run sensors**: a timestamp sensor per program showing when it next starts.
  It moves on to the following run as soon as a run starts.
- **Zone run time sensors**: on each zone's device, a `Program A run time` sensor (in minutes)
  for every program that waters that zone. Handy as secondary info on a zone's dashboard card.
  If a zone is later removed from a program, its sensor shows 0.
- **Zone run times in the calendar**: each program event in the Rain Bird calendar lists the
  zones it waters and for how long, e.g. `Zone 1: 10 min`. The calendar entity is now disabled
  by default; enable it in the entity's settings if you want it.
- **Diagnostics**: **Download diagnostics** in the integration entry's ⋮ menu gives a JSON file with the full
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

The schedule loads in the background shortly after startup, even if the calendar entity is
disabled, and refreshes every 15 minutes. The schedule sensors and calendar can be empty for a
moment after a restart, and zone run time sensors appear once the schedule has loaded. To reload
the schedule straight away, run the `homeassistant.update_entity` action on any `Program A next
run` sensor or the Rain Bird calendar.

## Uninstall

Remove it in HACS and restart. Home Assistant goes back to the built-in integration, and the
added button and sensor entities become unavailable, so you can delete them.

## License

This is a modified copy of code from [Home Assistant Core](https://github.com/home-assistant/core),
licensed under the Apache License 2.0 (see [LICENSE](LICENSE)). The modifications are the new
`button.py` and `diagnostics.py` files, the next run sensors in `sensor.py`, zone run times in
`calendar.py`, and the related platform, icon and translation entries.
