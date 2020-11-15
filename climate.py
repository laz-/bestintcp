"""Platform for Bestin TCP climate integration."""

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (HVAC_MODE_OFF,
        HVAC_MODE_HEAT, SUPPORT_TARGET_TEMPERATURE)

from homeassistant import const

from datetime import timedelta
import logging
import sys
import async_timeout

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import DOMAIN


# async component so that calls can better be done by room instead of by switch entity.
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    rooms = discovery_info

    _LOGGER.info("setup_platform called")

    async def async_update_data():
        """Fetch lighting data"""
        async with async_timeout.timeout(10):
            def fetch_thermo_status():
                for room in rooms:
                    room.fetchTemperStatus()
            await hass.async_add_executor_job(fetch_thermo_status)
            # XXX should maybe attempt error catching here?
            return True

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="bestintcp_switch",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=60),
    )

    thermostats = []
    for room in discovery_info:
        _LOGGER.info(f"climate config for {room}")
        # if the room has a temperature, it has a thermostat
        if room.temperature:
            thermostats.append(BestinTCPThermostat(room, 'thermostat', coordinator))

    _LOGGER.info(f"adding {thermostats}")
    async_add_entities(thermostats)


class BestinTCPThermostat(ClimateEntity):
    temperature_unit = const.TEMP_CELSIUS
    target_temperature_step = const.PRECISION_HALVES
    target_temperature_high = 40.0
    target_temperature_low = 5.0

    def __init__(self, room, name, coordinator):
        self.room = room
        self._name = name
        self.coordinator = coordinator

    @property
    def name(self):
        """Return the display name of this thermostat."""
        return f'bestin_r{self.room.name}_{self._name}'

    @property
    def unique_id(self):
        return f'{self.room.tcp.host}:{self.room.tcp.port}_{self.name}'

#    @property
#    def entity_id(self):
#        return self.name

    @property
    def current_temperature(self):
        return float(self.room.temperature)

    @property
    def target_temperature(self):
        return float(self.room.heat_target_temp)

    @property
    def hvac_mode(self):
        modes = {
            'off': HVAC_MODE_OFF,
            'on': HVAC_MODE_HEAT,
        }
        return modes[self.room.heat_status]

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_HEAT]

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        modes = {
            HVAC_MODE_OFF: 'off',
            HVAC_MODE_HEAT: 'on',
        }
        self.room.setTemperStatus(modes[hvac_mode])

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(const.ATTR_TEMPERATURE)
        self.room.setTemperStatus(self.room.heat_status, target_temp)

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    def should_poll(self):
        return True

    def update(self):
        self.room.fetchTemperStatus()

    async def async_update(self):
        """Update the thermostat."""
        return await self.coordinator.async_request_refresh()
