"""Support for Rain Bird Irrigation system LNK Wi-Fi Module."""

from datetime import datetime
import logging
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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
        letter = chr(ord("A") + program)
        self._attr_translation_placeholders = {"program": letter}
        if (unique_id := device_coordinator.unique_id) is not None:
            self._attr_unique_id = f"{unique_id}-program-{program}-next-run"
            self._attr_device_info = device_coordinator.device_info
        else:
            self._attr_name = (
                f"{device_coordinator.device_name} Program {letter} next run"
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
