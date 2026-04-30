"""Vonage sensor platform."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_AUTO_RELOAD, ATTR_LAST_UPDATED, DOMAIN
from .coordinator import VonageBalanceCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Vonage sensor entities for a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: VonageBalanceCoordinator = entry_data["balance_coordinator"]
    async_add_entities([VonageAccountBalanceSensor(coordinator, entry)])


class VonageAccountBalanceSensor(
    CoordinatorEntity[VonageBalanceCoordinator], SensorEntity
):
    """Sensor exposing the current Vonage account balance."""

    _attr_has_entity_name = True
    _attr_translation_key = "account_balance"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash"

    def __init__(
        self,
        coordinator: VonageBalanceCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the balance sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_account_balance"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Vonage",
            manufacturer="Vonage",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | None:
        """Return the numeric balance."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the account currency as the unit of measurement."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.currency

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Return extra state attributes (last_updated, auto_reload when present)."""
        data = self.coordinator.data
        if data is None:
            return None
        attrs: dict[str, object] = {
            ATTR_LAST_UPDATED: data.fetched_at.isoformat(),
        }
        if data.auto_reload is not None:
            attrs[ATTR_AUTO_RELOAD] = data.auto_reload
        return attrs
