# Rainbird Custom

A modified copy of the built-in Home Assistant [Rain Bird](https://www.home-assistant.io/integrations/rainbird)
integration, based on the version in Home Assistant **2026.9.3**. It adds ways to start and inspect
the programs stored on your Rain Bird controller.

This is a test bed for changes that are meant to be proposed upstream to Home Assistant core. It
uses the same `rainbird` domain, so installing it replaces the built-in integration. Your existing
Rain Bird config entry, entities and automations keep working.

## What's different from the built-in integration

### New entities

| Entity | Where | What it does |
|---|---|---|
| **Run program A / B / C…** (button) | Controller device | Starts that program on the controller right away, the same as starting it manually at the controller. One button per program the controller model supports. |
| **Program A / B / C… next run** (timestamp sensor) | Controller device | When the program next starts, taking the rain delay into account. Moves on to the following run as soon as a run starts. Empty if the program has no start times or no zones. |
| **Program A / B / C… run time** (duration sensor, minutes) | Each zone's device | How long a program waters that zone. A zone only gets a sensor for the programs that water it. If a zone is later removed from a program, its sensor shows 0. |

The run time sensors are created once the schedule has loaded, and new ones appear at the next
schedule refresh when you add a zone to a program on the controller. They need the zones to
have their own devices, which is the case for all but very old Rain Bird setups.

### Changed behavior

- **Calendar events list their zones.** Each program event in the Rain Bird calendar has a
  description with the zones it waters and for how long, e.g. `Zone 1: 10 min`. It shows when
  you click an event, in the calendar entity's `description` attribute, and in calendar
  triggers as `trigger.calendar_event.description`.
- **The schedule loads at startup without the calendar.** The built-in integration only fetches
  the schedule while the calendar entity is enabled. Here it loads in the background shortly
  after startup and refreshes every 15 minutes, whether or not the calendar is enabled, so you
  can disable the calendar entity and keep the other schedule features.
- **Diagnostics.** **Settings → Devices & services → Rainbird Custom → ⋮ → Download diagnostics**
  gives a JSON file with the full schedule (frequency, days, start times and minutes per zone for
  each program), the controller model, firmware and limits, and the current state. The host,
  password, MAC address and serial number are redacted.
- **Name and icon.** The integration shows as **Rainbird Custom**, and the Rain Bird icon and
  logo are included in the integration.

### Unchanged

Setup, zone switches, the `rainbird.start_irrigation` action, the rain delay number and
sensor, the rain sensor, the default irrigation time option, and the `pyrainbird` version
(6.5.0) are the same as the built-in integration.

## Install

1. In HACS, open the menu → **Custom repositories**, add
   `https://github.com/pavandave/rainbird_HACS` with category **Integration**.
2. Download **Rainbird Custom**, then restart Home Assistant. A restart is required; reloading
   the integration isn't enough.
3. Open the Rain Bird controller device. You'll see `Run program A`, `Program A next run`, and
   so on. The zone devices get their `Program A run time` sensors a few seconds after startup.

Requires Home Assistant 2026.9 or later.

## Usage

- **Start a program from an automation:** use the `button.press` action on a `Run program`
  button.
- **Reload the schedule right away:** run `homeassistant.update_entity` on any
  `Program A next run` sensor (or the calendar, if enabled). Otherwise it refreshes every 15
  minutes, so changes made on the controller or in the Rain Bird app can take that long to show.
- **Show run times on a dashboard:** the built-in entities card can't show another entity as a
  row's secondary info. With [multiple-entity-row](https://github.com/benct/lovelace-multiple-entity-row)
  from HACS:

  ```yaml
  type: entities
  entities:
    - entity: switch.rain_bird_sprinkler_1
      type: custom:multiple-entity-row
      toggle: true
      secondary_info:
        entity: sensor.rain_bird_sprinkler_1_program_b_run_time
        name: "Program B:"
    # A zone in two programs: show both as columns
    - entity: switch.rain_bird_sprinkler_2
      type: custom:multiple-entity-row
      toggle: true
      entities:
        - entity: sensor.rain_bird_sprinkler_2_program_a_run_time
          name: Prog A
        - entity: sensor.rain_bird_sprinkler_2_program_b_run_time
          name: Prog B
  ```

  Entity IDs depend on your device names, so check them on each zone's device page.

## Uninstall

Remove it in HACS and restart. Home Assistant goes back to the built-in integration. The added
button and sensor entities become unavailable, so you can delete them.

## License

This is a modified copy of code from [Home Assistant Core](https://github.com/home-assistant/core),
licensed under the Apache License 2.0 (see [LICENSE](LICENSE)). The modifications are:

- new `button.py` and `diagnostics.py`;
- next run and zone run time sensors in `sensor.py`;
- zone run times in event descriptions in `calendar.py`;
- the schedule loading at startup in `__init__.py`;
- the related icon, translation and manifest entries, and the `brand/` images.
