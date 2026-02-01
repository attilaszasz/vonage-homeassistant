"""Vonage sensor platform.

Author: Attila Szasz
"""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VonageApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vonage sensors."""
    api_client: VonageApiClient = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = [VonageAccountBalanceSensor(api_client)]
    async_add_entities(entities)


class VonageAccountBalanceSensor(SensorEntity):
    """Sensor for Vonage account balance."""

    def __init__(self, api_client: VonageApiClient) -> None:
        """Initialize the sensor."""
        self._api_client = api_client
        self._attr_name = "Vonage Account Balance"
        self._attr_unique_id = f"{DOMAIN}_account_balance"
        self._attr_native_unit_of_measurement = "EUR"
        self._attr_icon = "mdi:currency-eur"
        self._attr_native_value: Optional[float] = None

    @property
    def native_value(self) -> Optional[float]:
        """Return the balance value."""
        return self._attr_native_value

    async def async_update(self) -> None:
        """Update the sensor."""
        try:
            # Test the credentials to get account info (which includes balance)
            success = await self._api_client.test_sms_credentials()
            if success:
                # For now, we don't have a direct balance endpoint implemented
                # Set a placeholder value to indicate the sensor is working
                self._attr_native_value = 0.0
                self._attr_available = True
            else:
                self._attr_native_value = None
                self._attr_available = False
        except Exception as err:
            _LOGGER.error("Failed to update Vonage account balance: %s", err)
            self._attr_native_value = None
            self._attr_available = False