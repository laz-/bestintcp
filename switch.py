"""Platform for Bestin TCP switch integration."""

# async component so that calls can better be done by room instead of by switch entity.
#
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.switch import SwitchEntity

from homeassistant import const

from datetime import timedelta
import logging
import sys
import async_timeout

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers import entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    rooms = discovery_info
    async def async_update_data():
        """Fetch lighting data"""
        async with async_timeout.timeout(10):
            def fetch_light_status():
                for room in rooms:
                    room.fetchOutletsStatus()
            await hass.async_add_executor_job(fetch_light_status)
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

    outlets = []
    for room in discovery_info:
        _LOGGER.info(f"{room}")
        for name in room.outlets:
            outlet = BestinTCPOutlet(room, name, coordinator)
            outlets.append(outlet)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async_add_entities(outlets)


class BestinTCPOutlet(SwitchEntity):
    def __init__(self, room, name, coordinator):
        self.room = room
        self._name = name
        self.coordinator = coordinator

    @property
    def name(self):
        """Return the display name of this switch."""
        return f'bestin_r{self.room.name}_{self._name}'

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self.room.isOutletOn(self._name)

    @property
    def available(self):
        return self.coordinator.last_update_success

    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self.room.setOutletStatus(self._name, 'on')

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self.room.setOutletStatus(self._name, 'off')

    async def async_update(self):
        """Update the light."""
        return await self.coordinator.async_request_refresh()

