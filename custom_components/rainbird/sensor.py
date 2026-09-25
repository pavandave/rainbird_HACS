"""Support for Rain Bird Irrigation system LNK Wi-Fi Module."""

from datetime import datetime
import logging
from typing import override

from pyrainbird.timeline import ProgramId

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import RainbirdScheduleUpdateCoordinator, RainbirdUpdateCoordinator
from .types import RainbirdConfigEntry

_LOGGER = logging.getLogger(__name__)


RAIN_DELAY_ENTITY_DESCRIPTION = SensorEntityDescription(
    key="raindelay",
    translation_key="raindelay",
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RainbirdConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up entry for a Rain Bird sensor."""
    data = config_entry.runtime_data
    async_add_entities(
        [
            RainBirdSensor(
                data.coordinator,
                RAIN_DELAY_ENTITY_DESCRIPTION,
            ),
            *(
                RainBirdProgramNextRunSensor(
                    data.schedule_coordinator, data.coordinator, program
                )
                for program in range(data.model_info.model_info.max_programs)
            ),
        ]
    )

    # Zone run time sensors live on the zone devices, which need a unique id.
    if (unique_id := data.coordinator.unique_id) is None:
        return
    added: set[tuple[int, int]] = set()

    @callback
    def _async_add_zone_run_time_sensors() -> None:
        """Add a sensor for each zone that a program waters."""
        if (schedule := data.schedule_coordinator.data) is None:
            return
        new = [
            (program.program, zone.zone)
            for program in schedule.programs
            for zone in program.durations
            if zone.zone in data.coordinator.data.zones
            and (program.program, zone.zone) not in added
        ]
        added.update(new)
        async_add_entities(
            RainBirdZoneRunTimeSensor(data.schedule_coordinator, unique_id, *pair)
            for pair in new
        )

    _async_add_zone_run_time_sensors()
    config_entry.async_on_unload(
        data.schedule_coordinator.async_add_listener(_async_add_zone_run_time_sensors)
    )


class RainBirdSensor(CoordinatorEntity[RainbirdUpdateCoordinator], SensorEntity):
    """A sensor implementation for Rain Bird device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: RainbirdUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the Rain Bird sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        if coordinator.unique_id is not None:
            self._attr_unique_id = f"{coordinator.unique_id}-{description.key}"
            self._attr_device_info = coordinator.device_info
        else:
            self._attr_name = (
                f"{coordinator.device_name} {description.key.capitalize()}"
            )

    @property
    @override
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.rain_delay


class RainBirdProgramNextRunSensor(
    CoordinatorEntity[RainbirdScheduleUpdateCoordinator], SensorEntity
):
    """The next time a program is scheduled to start."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_translation_key = "program_next_run"

    def __init__(
        self,
        coordinator: RainbirdScheduleUpdateCoordinator,
        device_coordinator: RainbirdUpdateCoordinator,
        program: int,
    ) -> None:
        """Initialize the Rain Bird program next run sensor."""
        super().__init__(coordinator)
        self._program = program
        self._unsub_run_started: CALLBACK_TYPE | None = None
        program_name = ProgramId(program).name
        self._attr_translation_placeholders = {"program": program_name}
        if (unique_id := device_coordinator.unique_id) is not None:
            self._attr_unique_id = f"{unique_id}-program-{program}-next-run"
            self._attr_device_info = device_coordinator.device_info
        else:
            self._attr_name = (
                f"{device_coordinator.device_name} {program_name} next run"
            )

    @override
    async def async_added_to_hass(self) -> None:
        """Compute the next run from any schedule already loaded."""
        await super().async_added_to_hass()
        self.async_on_remove(self._cancel_run_started)
        self._update_next_run()

    @override
    @callback
    def _handle_coordinator_update(self) -> None:
        """Recompute the next run when the schedule changes."""
        self._update_next_run()
        super()._handle_coordinator_update()

    @callback
    def _handle_run_started(self, _now: datetime) -> None:
        """Move on to the following run once the current one has started."""
        self._unsub_run_started = None
        self._update_next_run()
        self.async_write_ha_state()

    @callback
    def _cancel_run_started(self) -> None:
        if self._unsub_run_started is not None:
            self._unsub_run_started()
            self._unsub_run_started = None

    @callback
    def _update_next_run(self) -> None:
        self._cancel_run_started()
        self._attr_native_value = self._next_run()
        if self._attr_native_value is not None:
            # The schedule only refreshes every 15 minutes, so advance the
            # value ourselves when a run starts.
            self._unsub_run_started = async_track_point_in_utc_time(
                self.hass, self._handle_run_started, self._attr_native_value
            )

    def _next_run(self) -> datetime | None:
        if (schedule := self.coordinator.data) is None:
            return None
        program = next(
            (p for p in schedule.programs if p.program == self._program), None
        )
        # A program without zones never waters, even if it has start times.
        if program is None or not program.durations:
            return None
        timeline = program.timeline_tz(dt_util.get_default_time_zone())
        if (event := next(timeline.start_after(dt_util.now()), None)) is None:
            return None
        return dt_util.as_local(event.start)


class RainBirdZoneRunTimeSensor(
    CoordinatorEntity[RainbirdScheduleUpdateCoordinator], SensorEntity
):
    """How long a program waters a zone."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_translation_key = "zone_run_time"

    def __init__(
        self,
        coordinator: RainbirdScheduleUpdateCoordinator,
        unique_id: str,
        program: int,
        zone: int,
    ) -> None:
        """Initialize the Rain Bird zone run time sensor."""
        super().__init__(coordinator)
        self._program = program
        self._zone = zone
        self._attr_translation_placeholders = {"program": ProgramId(program).name}
        self._attr_unique_id = f"{unique_id}-{zone}-program-{program}-run-time"
        # The zone device is created by the switch platform.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{unique_id}-{zone}")}
        )

    @property
    @override
    def native_value(self) -> int | None:
        """Return the minutes the program waters the zone, or 0 if it no longer does."""
        if (schedule := self.coordinator.data) is None:
            return None
        program = next(
            (p for p in schedule.programs if p.program == self._program), None
        )
        if program is None:
            return 0
        return next(
            (
                int(zone.duration.total_seconds() // 60)
                for zone in program.durations
                if zone.zone == self._zone
            ),
            0,
        )
