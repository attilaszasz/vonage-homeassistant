"""Support for Vonage SMS notifications."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.notify import (
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import VonageApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up Vonage notify platform."""
    api_client = hass.data[DOMAIN][config_entry.entry_id]
    
    # Register the notification service directly
    notify_service = VonageSmsNotificationService(api_client)
    
    # Register with notify component
    await hass.components.notify.async_register_services({
        "vonage_sms": notify_service
    })


class VonageSmsNotificationService(BaseNotificationService):
    """Implementation of a notification service for Vonage SMS."""

    def __init__(self, api_client: VonageApiClient) -> None:
        """Initialize the service."""
        self.api_client = api_client

    async def async_send_message(
        self, message: str = "", **kwargs: Any
    ) -> None:
        """Send a message to specified targets via SMS."""
        targets = kwargs.get(ATTR_TARGET, [])
        
        # Ensure targets is a list
        if isinstance(targets, str):
            targets = [targets]
        
        if not targets:
            _LOGGER.error("No targets specified for SMS notification")
            raise HomeAssistantError("No targets specified for SMS notification")
        
        if not message:
            _LOGGER.error("Empty message not allowed for SMS notification")
            raise HomeAssistantError("Empty message not allowed for SMS notification")

        # Send SMS to each target
        for target in targets:
            try:
                await self.api_client.send_sms(to=target, text=message)
                _LOGGER.debug("SMS sent successfully to %s", target)
            except Exception as err:
                _LOGGER.error("Failed to send SMS to %s: %s", target, err)
                raise HomeAssistantError(f"Failed to send SMS to {target}: {err}")